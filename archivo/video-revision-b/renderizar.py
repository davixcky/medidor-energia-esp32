import bpy,json,os
from pathlib import Path
p=Path(__file__).resolve().parent;s=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
s.render.use_persistent_data=True
s.cycles.device='GPU';s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=95
node=bpy.data.objects['Difusor_NeoPixel'].active_material.node_tree.nodes['Principled BSDF']
tim=json.loads((p/'tiempos.json').read_text());change=tim['segments'][3]['start'];end=tim['segments'][4]['start']
screen=bpy.data.objects['LCD_pantalla'].active_material.node_tree.nodes.get('Image Texture')
summary=screen.image
config=bpy.data.images.load(str(p/'assets/lcd-configuracion.png'),check_existing=False)
config.use_fake_user=True;config.pack()
for frame in range(int(os.environ.get("FRAME_START",s.frame_start)),int(os.environ.get("FRAME_END",s.frame_end))+1):
 path=p/'frames'/f'frame-{frame:04d}.jpg'
 if path.exists() and not os.environ.get("FORCE_RENDER"):continue
 s.frame_set(frame);t=(frame-1)/s.render.fps
 screen.image=config if tim['segments'][2]['start']+1<=t<tim['segments'][3]['start'] else summary
 color=(.03,.5,.22,1)
 if change+3<=t<change+5:color=(.75,.23,.01,1)
 elif change+5<=t<end:color=(.7,.02,.01,1)
 node.inputs['Base Color'].default_value=color;node.inputs['Emission Color'].default_value=color
 s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
