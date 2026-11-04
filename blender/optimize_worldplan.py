"""Optimize the authored WorldPlan non-destructively to a staged sibling file.

Run Blender -b exports/WorldPlan.blend --python optimize_worldplan.py.
The original is backed up once; validation promotes WorldPlan.optimized.blend.
"""
import bpy, numpy as np, json, hashlib, shutil, sys, math
from pathlib import Path
from mathutils import Matrix

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
OUT = BASE / 'exports' / 'WorldPlan_Optimization'
OUT.mkdir(exist_ok=True)
TEXTURES = OUT / 'textures'
TEXTURES.mkdir(exist_ok=True)

def log(message): print('[OPTIMIZE]', message, flush=True)

def triangles(mesh):
    lengths=np.empty(len(mesh.polygons),np.int32)
    mesh.polygons.foreach_get('loop_total',lengths)
    return int(np.maximum(lengths-2,0).sum())

def metrics():
    return dict(objects=len(bpy.data.objects), mesh_datablocks=len(bpy.data.meshes),
                stored_triangles=sum(triangles(m) for m in bpy.data.meshes),
                materials=len(bpy.data.materials), images=sum(i.source!='VIEWER' for i in bpy.data.images),
                rgba8_texture_bytes=sum(i.size[0]*i.size[1]*4 for i in bpy.data.images if i.source!='VIEWER'),
                collection_instances=sum(o.instance_type=='COLLECTION' for o in bpy.data.objects))

def geometry_fingerprint(mesh):
    h=hashlib.sha256()
    for items,prop,count,dtype in [(mesh.vertices,'co',3,np.float32),(mesh.loops,'vertex_index',1,np.int32),(mesh.polygons,'loop_total',1,np.int32),(mesh.polygons,'material_index',1,np.int32),(mesh.polygons,'use_smooth',1,np.bool_)]:
        a=np.empty(len(items)*count,dtype);items.foreach_get(prop,a);h.update(a.tobytes())
    for layer in mesh.uv_layers:
        a=np.empty(len(layer.data)*2,np.float32);layer.data.foreach_get('uv',a);h.update(layer.name.encode());h.update(a.tobytes())
    for a in mesh.color_attributes:
        vals=np.empty(len(a.data)*4,np.float32);a.data.foreach_get('color',vals);h.update(a.name.encode());h.update(vals.tobytes())
    return h.hexdigest()

def protected_snapshot():
    # Everything outside the explicit optimized mesh allowlist must preserve its geometry and transforms.
    changed=lambda n:n.startswith('Ashlar facade blocks') or n in {'Individual mixed meadow grass blades','Common garden | Layered perennial groundcover'}
    return {o.name:dict(matrix=[v for row in o.matrix_world for v in row],geometry=geometry_fingerprint(o.data) if o.type=='MESH' else None,
                         type=o.type,instance_collection=o.instance_collection.name if o.instance_collection else None)
            for o in bpy.data.objects if not changed(o.name)}

def deduplicate_images():
    seen={};merged=[]
    for im in list(bpy.data.images):
        if im.source!='FILE' or not im.packed_file:continue
        key=(tuple(im.size),im.colorspace_settings.name,im.alpha_mode,hashlib.sha256(im.packed_file.data).hexdigest())
        if key in seen:
            master=seen[key];merged.append([im.name,master.name]);im.user_remap(master);bpy.data.images.remove(im)
        else:seen[key]=im
    return merged

def serial(value):
    if isinstance(value,(str,bool,int,float)):return value
    try:return [serial(x) for x in value]
    except TypeError:return str(value)

def material_key(m):
    if not m.use_nodes or not m.node_tree:return None
    if m.animation_data or m.node_tree.animation_data:return None
    nodes=list(m.node_tree.nodes); node_ids={n:i for i,n in enumerate(nodes)};records=[]
    for n in nodes:
        # Fingerprint rendering-relevant RNA, excluding editor/name fields.
        if n.type=='GROUP':return None
        r={'type':n.bl_idname,'inputs':[(s.identifier,serial(s.default_value)) for s in n.inputs if hasattr(s,'default_value')]}
        for p in n.bl_rna.properties:
            if p.identifier in {'rna_type','name','label','location','width','height','dimensions','select','show_options','show_preview','show_texture','hide','parent','color','use_custom_color','inputs','outputs','internal_links'} or p.is_readonly:continue
            if p.type in {'BOOLEAN','INT','FLOAT','STRING','ENUM'}:
                try:r[p.identifier]=serial(getattr(n,p.identifier))
                except Exception:pass
        if n.type=='TEX_IMAGE':r['image']=n.image.name if n.image else None
        if hasattr(n,'color_ramp'):
            cr=n.color_ramp;r['ramp']=[cr.interpolation,cr.color_mode,cr.hue_interpolation,[(e.position,list(e.color)) for e in cr.elements]]
        if n.type=='TEX_COORD' and n.object:r['object']=n.object.name
        if n.type in {'CURVE_RGB','CURVE_VEC','CURVE_FLOAT'}:return None
        records.append(r)
    links=[(node_ids[l.from_node],l.from_socket.identifier,node_ids[l.to_node],l.to_socket.identifier) for l in m.node_tree.links]
    settings={p:serial(getattr(m,p)) for p in ('diffuse_color','metallic','roughness','surface_render_method','use_backface_culling','displacement_method') if hasattr(m,p)}
    return json.dumps([records,links,settings],sort_keys=True)

def deduplicate_materials():
    seen={};merged=[]
    for m in list(bpy.data.materials):
        key=material_key(m)
        if key is None:continue
        if key in seen:
            master=seen[key];merged.append([m.name,master.name]);m.user_remap(master);bpy.data.materials.remove(m)
        else:seen[key]=m
    return merged

def deduplicate_meshes():
    seen={};merged=[]
    for o in list(bpy.data.objects):
        if o.type!='MESH' or o.data.shape_keys or o.vertex_groups or o.data.has_custom_normals:continue
        # Only standard attributes covered by the full fingerprint are eligible.
        if any(a.name not in {'position','.edge_verts','.corner_vert','.corner_edge','material_index','sharp_face','sharp_edge'} and a.name not in {u.name for u in o.data.uv_layers} and a.name not in {c.name for c in o.data.color_attributes} for a in o.data.attributes):continue
        key=(geometry_fingerprint(o.data),tuple(m.name if m else '' for m in o.data.materials))
        if key in seen and seen[key]!=o.data:
            old=o.data;master=seen[key];merged.append([o.name,old.name,master.name]);o.data=master
            if old.users==0:bpy.data.meshes.remove(old)
        else:seen[key]=o.data
    return merged

def instance_groundcover():
    """Recover exact rigid transforms of the 10,400 repeated sculpted leaves."""
    o=bpy.data.objects.get('Common garden | Layered perennial groundcover')
    if not o or o.get('wp_instance_geometry'):return {'skipped':True}
    me=o.data
    count=len(me.vertices)//48
    assert len(me.vertices)==count*48 and len(me.polygons)==count*40, 'Unexpected groundcover topology'
    co=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',co);co=co.reshape(count,48,3).astype(np.float64)
    centers=co.mean(axis=1);centered=co-centers[:,None,:];template=centered[0]
    # Batched Kabsch alignment, with exact correspondence inherited from Batch.uvball.
    covariance=np.einsum('ji,njk->nik',template,centered)
    u,_,vt=np.linalg.svd(covariance);rot=u@vt
    assert np.all(np.linalg.det(rot)>.999), 'Mirrored leaf requires separate template'
    reconstructed=np.einsum('ij,njk->nik',template,rot)+centers[:,None,:]
    error=float(np.max(np.abs(co-reconstructed)))
    assert error<.0002, f'Groundcover transform reconstruction error {error}'
    face_template=[tuple(v for v in p.vertices) for p in me.polygons[:40]]
    mat_indices=np.empty(len(me.polygons),np.int32);me.polygons.foreach_get('material_index',mat_indices);mat_indices=mat_indices.reshape(count,40)
    assert np.all(mat_indices==mat_indices[:,:1]), 'Mixed leaf material'
    # Verify all repeated topology before replacing geometry.
    for i in range(count):
        if any(tuple(v-i*48 for v in p.vertices)!=face_template[j] for j,p in enumerate(me.polygons[i*40:(i+1)*40])):raise AssertionError('Leaf topology differs')
    ng=bpy.data.node_groups.new('WP | Shared groundcover leaf instances','GeometryNodeTree')
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes,links=ng.nodes,ng.links;join=nodes.new('GeometryNodeJoinGeometry');out=nodes.new('NodeGroupOutput');links.new(join.outputs['Geometry'],out.inputs['Geometry'])
    library=bpy.data.collections.get('WP | Optimization prototypes') or bpy.data.collections.new('WP | Optimization prototypes')
    # Deliberately unlinked library: Object Info references render prototypes only through instances.
    created=[]
    for mi in np.unique(mat_indices[:,0]):
        ids=np.where(mat_indices[:,0]==mi)[0];mat=me.materials[int(mi)]
        proto=bpy.data.meshes.new('WP | Groundcover leaf '+str(mi));proto.from_pydata(template.tolist(),[],face_template);proto.materials.append(mat)
        for p in proto.polygons:p.use_smooth=True
        po=bpy.data.objects.new(proto.name,proto);library.objects.link(po)
        points=bpy.data.meshes.new('WP | Groundcover placements '+str(mi));points.from_pydata(centers[ids].tolist(),[],[])
        rotations=points.attributes.new('wp_rotation','FLOAT_VECTOR','POINT')
        angles=[tuple(Matrix(rot[i].T.tolist()).to_euler()) for i in ids];rotations.data.foreach_set('vector',np.asarray(angles,np.float32).ravel())
        positions=bpy.data.objects.new(points.name,points);library.objects.link(positions)
        getpoints=nodes.new('GeometryNodeObjectInfo');getpoints.inputs['Object'].default_value=positions;getpoints.transform_space='ORIGINAL'
        getproto=nodes.new('GeometryNodeObjectInfo');getproto.inputs['Object'].default_value=po;getproto.inputs['As Instance'].default_value=True;getproto.transform_space='ORIGINAL'
        attr=nodes.new('GeometryNodeInputNamedAttribute');attr.data_type='FLOAT_VECTOR';attr.inputs['Name'].default_value='wp_rotation'
        inst=nodes.new('GeometryNodeInstanceOnPoints');links.new(getpoints.outputs['Geometry'],inst.inputs['Points']);links.new(getproto.outputs['Geometry'],inst.inputs['Instance']);links.new(attr.outputs['Attribute'],inst.inputs['Rotation']);links.new(inst.outputs['Instances'],join.inputs['Geometry'])
        created.append(dict(material=mat.name,instances=len(ids),triangles=triangles(proto)))
    old_tri=triangles(me);empty=bpy.data.meshes.new(o.name+' | instance carrier');o.data=empty
    mod=o.modifiers.new('Shared leaf geometry','NODES');mod.node_group=ng;o['wp_instance_geometry']=True;o['wp_instance_count']=count
    if me.users==0:bpy.data.meshes.remove(me)
    return dict(leaf_instances=count,stored_triangles_before=old_tri,stored_triangles_after=sum(p['triangles'] for p in created),realized_triangles=old_tri,max_vertex_error=error,prototypes=created)

def main():
    source=Path(bpy.data.filepath)
    assert source.name=='WorldPlan.blend'
    assert not bpy.context.scene.get('wp_optimized_version'), 'Already optimized; reopen backup to rebuild'
    backup=source.with_name('WorldPlan.before-optimization.blend')
    if not backup.exists():shutil.copy2(source,backup)
    report={'source':str(source),'backup':str(backup),'before':metrics()}
    log(report['before'])
    (OUT/'protected_before.json').write_text(json.dumps(protected_snapshot()))
    log('Deduplicating packed textures and equivalent node materials')
    report['images_merged']=deduplicate_images();report['materials_merged']=deduplicate_materials()
    report['meshes_linked']=deduplicate_meshes()
    log('Recovering shared groundcover prototypes')
    report['groundcover']=instance_groundcover()
    from optimization_grass import optimize_grass
    from optimization_trims import optimize_trims
    log('Replacing grass with shared textured cards');report['grass']=optimize_grass(OUT)
    log('Replacing shallow block geometry with normal-mapped trim skin');report['trims']=optimize_trims(TEXTURES)
    # Remove only truly unused data; hidden recovery collections remain intact.
    removed={}
    for label,blocks in [('meshes',bpy.data.meshes),('materials',bpy.data.materials),('images',bpy.data.images)]:
        unused=[x for x in blocks if x.users==0 and not x.use_fake_user];removed[label]=len(unused)
        for x in unused:blocks.remove(x)
    report['unused_removed']=removed
    report['after']=metrics()
    for scene in bpy.data.scenes:scene['wp_optimized_version']=1
    bpy.context.preferences.filepaths.file_preview_type='NONE';bpy.context.preferences.filepaths.save_version=0
    target=source.with_name('WorldPlan.optimized.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
    report['staged_file']=str(target);report['staged_bytes']=target.stat().st_size
    (OUT/'report.json').write_text(json.dumps(report,indent=2))
    log(json.dumps(report['after']));log('STAGED '+str(target))

if __name__=='__main__':main()
