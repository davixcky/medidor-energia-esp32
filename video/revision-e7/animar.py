#!/usr/bin/env python3
"""Construye y renderiza el video E.7 desde el ensamble FreeCAD real."""
from pathlib import Path
import bpy, json, os
from mathutils import Vector

p=Path(__file__).resolve().parent; root=p.parents[1]
tim=json.loads((p/'tiempos.json').read_text());segments=tim['segments'];fps=24
data=json.loads((root/'freecad/revision-e7/.render/ensamble.json').read_text())
def fr(t): return round(t*fps)+1

bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.fps=fps
s.frame_start=1;s.frame_end=tim['duration']*fps
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=94
s.render.filepath=str(p/'frames/frame-')
s.view_settings.look='AgX - Medium High Contrast'

objects={};groups={};materials={}
for d in data:
    me=bpy.data.meshes.new(d['name']);me.from_pydata(d['vertices'],[],d['faces']);me.update()
    o=bpy.data.objects.new(d['name'],me);s.collection.objects.link(o)
    m=bpy.data.materials.new(d['name']);m.diffuse_color=(*d['color'],1);m.use_nodes=True
    bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*d['color'],1);bs.inputs['Roughness'].default_value=.58
    o.data.materials.append(m);objects[d['name']]=o;groups[d['name']]=d['group'];materials[d['name']]=m

# LCD real del firmware sobre el área activa del módulo comprado.
bpy.ops.mesh.primitive_plane_add(size=1,location=(37.5,27.5,67.15));lcd=bpy.context.active_object;lcd.name='LCD_interfaz_firmware';lcd.scale=(23.2,11.3,1)
mat=bpy.data.materials.new('LCD_emision');mat.use_nodes=True;nt=mat.node_tree
tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'assets/lcd-resumen.png'));tex.interpolation='Closest'
emi=nt.nodes.new('ShaderNodeEmission');emi.inputs['Strength'].default_value=1.25
nt.links.new(tex.outputs['Color'],emi.inputs['Color']);nt.links.new(emi.outputs['Emission'],nt.nodes['Material Output'].inputs['Surface']);lcd.data.materials.append(mat)
objects[lcd.name]=lcd;groups[lcd.name]='lid'

# Estudio sobrio con contacto.
world=bpy.data.worlds.new('World');world.use_nodes=True;s.world=world
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.18,.20,.23,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.68
bpy.ops.mesh.primitive_plane_add(size=2000,location=(140,90,-.5));floor=bpy.context.active_object
fm=bpy.data.materials.new('Suelo');fm.use_nodes=True;fb=fm.node_tree.nodes['Principled BSDF'];fb.inputs['Base Color'].default_value=(.105,.12,.14,1);fb.inputs['Roughness'].default_value=.72;floor.data.materials.append(fm)
for name,pos,energy,size,color in (
    ('Key',(-190,-250,370),3600,240,(1,.83,.68)),('Rim',(430,120,310),2800,210,(.58,.78,1)),('Fill',(120,360,220),1900,180,(.8,.88,1))):
    ld=bpy.data.lights.new(name,'AREA');ld.energy=energy;ld.shape='DISK';ld.size=size
    lo=bpy.data.objects.new(name,ld);s.collection.objects.link(lo);lo.location=pos;ld.color=color
    lo.rotation_euler=(Vector((140,90,25))-lo.location).to_track_quat('-Z','Y').to_euler()

camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd);s.collection.objects.link(cam);s.camera=cam;camd.lens=52
def camera_key(t,pos,target,lens=52):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camd.lens=lens
    cam.keyframe_insert('location',frame=fr(t));cam.keyframe_insert('rotation_euler',frame=fr(t));camd.keyframe_insert('lens',frame=fr(t))

t2=segments[1]['start'];t3=segments[2]['start'];t4=segments[3]['start'];t5=segments[4]['start'];end=tim['duration']
camera_key(0,(-185,-275,245),(140,82,30),54)
camera_key(t2,(115,-250,335),(120,70,55),58)
camera_key(t3,(140,-195,225),(140,92,62),62)
camera_key(t4+.8,(365,-285,295),(220,90,32),52)
camera_key(t5,(165,-230,430),(140,102,18),55)
camera_key(end,(350,-290,270),(205,88,30),54)

# La tapa abre como un conjunto; la guarda de red permanece atornillada.
opening=t4+.15;opened=t4+1.65;closing=end-2.0
for n,o in objects.items():
    if groups[n]!='lid': continue
    base=o.location.copy()
    for t,offset in ((0,(0,0,0)),(opening,(0,0,0)),(opened,(170,0,48)),(closing,(170,0,48)),(end,(0,0,0))):
        o.location=base+Vector(offset);o.keyframe_insert('location',frame=fr(t))

# Estados implementados por firmware: todos los segmentos FCOB comparten color.
state_colors={'green':(0,.55,.26,1),'amber':(.9,.26,0,1),'red':(.8,.015,.01,1)}
led_names=('Segmentos_WS2811_4','Difusor_FCOB_204x14','LED_estado_panel_5mm')
def led_color(name,t,color,strength):
    bs=materials[name].node_tree.nodes['Principled BSDF']
    for socket in ('Base Color','Emission Color'):
        bs.inputs[socket].default_value=color;bs.inputs[socket].keyframe_insert('default_value',frame=fr(t))
    bs.inputs['Emission Strength'].default_value=strength;bs.inputs['Emission Strength'].keyframe_insert('default_value',frame=fr(t))

amber=t3+1.8;red=t3+4.6;normal=t4-.2
for name in led_names:
    led_color(name,0,state_colors['green'],1.8 if 'Segmentos' in name else 1.0)
    led_color(name,amber,state_colors['amber'],1.8 if 'Segmentos' in name else 1.0)
    led_color(name,red,state_colors['red'],2.1 if 'Segmentos' in name else 1.3)
    led_color(name,normal,state_colors['green'],1.8 if 'Segmentos' in name else 1.0)
# El LED pequeño parpadea: 1 Hz ámbar y 5 Hz rojo. La FCOB queda fija.
panel='LED_estado_panel_5mm';bs=materials[panel].node_tree.nodes['Principled BSDF']
for t0,t1,hz,on in ((amber,red,1,1.0),(red,normal,5,1.3)):
    step=.5/hz;t=t0
    while t<t1:
        for dt,val in ((0,on),(step,0.03)):
            bs.inputs['Emission Strength'].default_value=val;bs.inputs['Emission Strength'].keyframe_insert('default_value',frame=fr(min(t+dt,t1)))
        t+=2*step

# Composición: halo solo en emisores, moderado para conservar el detalle.
s.use_nodes=True;nt=s.compositing_node_group
if nt is None: nt=bpy.data.node_groups.new('Composición','CompositorNodeTree');s.compositing_node_group=nt
nt.nodes.clear();nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.inputs['Type'].default_value='Fog Glow';gl.inputs['Quality'].default_value='Medium';gl.inputs['Threshold'].default_value=2.2
out=nt.nodes.new('NodeGroupOutput');nt.links.new(rl.outputs['Image'],gl.inputs['Image']);nt.links.new(gl.outputs['Image'],out.inputs[0])

(p/'frames').mkdir(exist_ok=True);s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(p/'medidor-E7.blend'))
if os.environ.get('PREVIEW'):
    for i,t in enumerate((1,(t3+amber)/2,red+.5,opened+1,t5+1,end-.5),1):
        s.frame_set(fr(t));s.render.filepath=str(p/f'preview-{i}.jpg');bpy.ops.render.render(write_still=True)
elif not os.environ.get('BUILD_ONLY'):
    bpy.ops.render.render(animation=True)
