"""Render isolated before/after review views without modifying the saved world."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
label=sys.argv[-1]
out=Path(__file__).resolve().parents[1]/'exports/WorldPlan_Optimization'
scene=bpy.data.scenes.new('Optimization review')
bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.cycles.max_bounces=4;scene.cycles.transparent_max_bounces=8
scene.render.threads_mode='FIXED';scene.render.threads=6
scene.render.resolution_x=960;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.world=bpy.data.worlds.new('Review daylight');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.55,.65,.8,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
scene.view_settings.view_transform='AgX'
light=bpy.data.lights.new('Review sun','SUN');light.energy=2.3;light.angle=.12
sun=bpy.data.objects.new('Review sun',light);scene.collection.objects.link(sun);sun.rotation_euler=(.5,-.4,-.5)
camera=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',camera);scene.collection.objects.link(cam);scene.camera=cam
def view(position,target,lens=45):
    cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camera.lens=lens
def render(name):
    scene.render.filepath=str(out/(label+'_'+name+'.png'));print('REVIEW_RENDER',scene.render.filepath,flush=True);bpy.ops.render.render(write_still=True)
house=bpy.data.collections['EMBERCLAW HOUSE']
for o in house.all_objects:
    if o.type=='MESH':scene.collection.objects.link(o)
bounds=[o.matrix_world@Vector(p) for o in house.all_objects if o.type=='MESH' for p in o.bound_box]
lo=Vector(tuple(min(v[k] for v in bounds) for k in range(3)));hi=Vector(tuple(max(v[k] for v in bounds) for k in range(3)));center=(lo+hi)/2
view((center.x-55,lo.y-115,lo.z+47),(center.x,center.y,lo.z+27),43)
render('house')
for o in list(scene.collection.objects):
    if o.type=='MESH':scene.collection.objects.unlink(o)
grass=bpy.data.objects['Individual mixed meadow grass blades'];scene.collection.objects.link(grass)
if grass.get('wp_grass_cards'):
    co=grass.data.vertices[120].co.copy()
else:
    verts=[grass.data.vertices[120*25+j].co for j in range(25)]
    co=Vector(tuple((min(v[k] for v in verts)+max(v[k] for v in verts))*.5 for k in range(3)))
    co.z=sum(verts[j*5+k].z for j in range(5) for k in (0,1))/10
co=grass.matrix_world@co
# A neutral ground provides the same reference under original blades and alpha cards.
mesh=bpy.data.meshes.new('Review soil');mesh.from_pydata([(-300,-300,0),(300,-300,0),(300,300,0),(-300,300,0)],[],[(0,1,2,3)])
ground=bpy.data.objects.new('Review soil',mesh);scene.collection.objects.link(ground);ground.location=(co.x,co.y,co.z-.04)
mat=bpy.data.materials.new('Review earth');mat.diffuse_color=(.10,.125,.045,1);mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.10,.125,.045,1);mesh.materials.append(mat)
view((co.x+3.8,co.y-5.2,co.z+2.0),(co.x,co.y,co.z+.5),48)
render('grass')
