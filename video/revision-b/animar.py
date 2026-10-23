import bpy,json,math,os
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent;root=p.parents[1]
s=bpy.context.scene;tim=json.loads((p/'tiempos.json').read_text());segments=tim['segments'];fps=24
def fr(t):return round(t*fps)+1
s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True;s.cycles.denoiser='OPTIX'
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.render.fps=fps;s.frame_start=1;s.frame_end=tim['duration']*fps
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.threads_mode='FIXED';s.render.threads=6
# An actual CAD turntable/exploded view. The mains guard stays screwed in place.
data=json.loads((root/'freecad/revision-b/render/ensamble.json').read_text())
opening=segments[1]['start'];closing=segments[2]['start']
for row in data:
 o=bpy.data.objects.get(row['nombre'])
 if not o:continue
 if row['grupo']=='servicio':o.hide_render=True
 if row['grupo']=='tapa':
  for t,xyz in [(0,(0,0,0)),(opening-.35,(0,0,0)),(opening+1.5,(205,0,55)),(closing-1.5,(205,0,55)),(closing,(0,0,0))]:
   o.location=xyz;o.keyframe_insert('location',frame=fr(t))
# Soft graphite studio. Lighting is shared with the checked still renders.
world=s.world.node_tree
for node in world.nodes:
 if node.type=='BACKGROUND':node.inputs[0].default_value=(.025,.035,.045,1)
s.view_settings.view_transform='AgX'
bpy.ops.mesh.primitive_plane_add(size=20000,location=(100,75,-1));floor=bpy.context.object
mat=bpy.data.materials.new('Suelo');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.025,.035,.045,1);bs.inputs['Roughness'].default_value=.6;floor.data.materials.append(mat)
for o in bpy.data.objects:
 if o.type=='LIGHT':o.data.energy*=3
cam=s.camera;cam.data.type='ORTHO'
shots=[(0,(-.75,-1,.95),(100,75,40),390),
 (opening-.4,(-.6,-1,1.1),(100,75,40),390),
 (opening+1.5,(-.15,-.65,1.5),(205,75,55),590),
 (closing-1.5,(-.1,-.5,1.6),(205,75,55),590),
 (closing+.8,(-.25,-.7,1.5),(95,62,70),240),
 (segments[3]['start'],(-.2,-.7,1.4),(105,52,70),245),
 (segments[4]['start'],(-.35,-1,.5),(115,30,37),265),
 (segments[5]['start'],(-.6,-1,1),(100,75,40),390),
 (tim['duration'],(-.75,-1,1),(100,75,40),400)]
for t,dir,target,scale in shots:
 cam.location=Vector(target)+Vector(dir).normalized()*700;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 cam.keyframe_insert('location',frame=fr(t));cam.keyframe_insert('rotation_euler',frame=fr(t));cam.data.keyframe_insert('ortho_scale',frame=fr(t))
# Illustrative state sequence: connected, offline, alert; not measured device footage.
node=bpy.data.objects['Difusor_NeoPixel'].active_material.node_tree.nodes['Principled BSDF']
colors=[(0,(.03,.5,.22,1)),(segments[3]['start']+2,(.03,.5,.22,1)),(segments[3]['start']+3,(.75,.23,.01,1)),(segments[3]['start']+5,(.7,.02,.01,1)),(segments[4]['start'],(.03,.5,.22,1))]
node.inputs['Emission Strength'].default_value=1.4
for t,c in colors:
 for socket in ['Base Color','Emission Color']:node.inputs[socket].default_value=c;node.inputs[socket].keyframe_insert('default_value',frame=fr(t))
config_image=bpy.data.images.load(str(p/'assets/lcd-configuracion.png'))
config_image.use_fake_user=True
config_image.pack()
s.frame_set(1);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(p/'medidor-revB.blend'))
for i,seg in enumerate(segments):
 s.frame_set(fr((seg['start']+seg['end'])/2));s.render.filepath=str(p/f'preview-{i+1}.png');bpy.ops.render.render(write_still=True)
