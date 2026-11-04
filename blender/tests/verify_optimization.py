import bpy,sys,json,numpy as np
from pathlib import Path
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base))
from optimize_worldplan import geometry_fingerprint,metrics
out=base/'exports/WorldPlan_Optimization'
before=json.loads((out/'protected_before.json').read_text())
errors=[]
for name,record in before.items():
    o=bpy.data.objects.get(name)
    if not o:errors.append('Missing protected object: '+name);continue
    if record['matrix']!=[v for row in o.matrix_world for v in row]:errors.append('Changed transform: '+name)
    if o.type=='MESH' and record['geometry']!=geometry_fingerprint(o.data):errors.append('Changed protected geometry: '+name)
    if record['instance_collection']!=(o.instance_collection.name if o.instance_collection else None):errors.append('Changed collection instance: '+name)
report=json.loads((out/'report.json').read_text())
assert metrics()['collection_instances']==report['before']['collection_instances']
counts={}
for o in list(bpy.data.objects):
    if not (o.get('wp_grass_cards') or o.get('wp_instance_geometry')):continue
    # Realize export copies to verify saved node dependencies and UV/material channels.
    tmp=o.copy();bpy.context.scene.collection.objects.link(tmp)
    ng=bpy.data.node_groups.new('Validation realize','GeometryNodeTree')
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    i=ng.nodes.new('NodeGroupInput');r=ng.nodes.new('GeometryNodeRealizeInstances');e=ng.nodes.new('NodeGroupOutput')
    ng.links.new(i.outputs[0],r.inputs[0]);ng.links.new(r.outputs[0],e.inputs[0])
    tmp.modifiers.new('Validation only','NODES').node_group=ng
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=tmp.evaluated_get(deps);mesh=ev.to_mesh()
    tris=sum(len(p.vertices)-2 for p in mesh.polygons)
    counts[o.name]=dict(vertices=len(mesh.vertices),triangles=tris,uv_layers=len(mesh.uv_layers),materials=len(mesh.materials))
    if o.get('wp_grass_cards'):
        if tris!=o['wp_grass_realized_triangles']:errors.append('Grass instance realization mismatch')
        if not mesh.uv_layers:errors.append('Grass UV missing')
    if o.get('wp_instance_geometry') and tris!=report['groundcover']['realized_triangles']:errors.append('Groundcover instance realization mismatch')
    ev.to_mesh_clear();bpy.data.objects.remove(tmp,do_unlink=True);bpy.data.node_groups.remove(ng)
for item in report['trims']['objects']:
    o=bpy.data.objects[item['name']]
    if len(o.data.materials)!=1 or len(o.data.uv_layers)!=1:errors.append('Trim material/UV mismatch: '+o.name)
    if sum(len(p.vertices)-2 for p in o.data.polygons)!=item['triangles_after']:errors.append('Trim triangle mismatch: '+o.name)
images=[]
for im in bpy.data.images:
    if im.source=='VIEWER':continue
    if not im.packed_file:errors.append('Unpacked image: '+im.name)
    if not im.size[0] or not im.size[1]:errors.append('Empty image: '+im.name)
    images.append(dict(name=im.name,size=list(im.size),packed=bool(im.packed_file)))
result=dict(ok=not errors,errors=errors,protected_objects_checked=len(before),realization=counts,images=images,metrics=metrics())
(out/'validation.json').write_text(json.dumps(result,indent=2))
print('OPTIMIZATION_VALIDATION',json.dumps(result),flush=True)
assert not errors, errors
