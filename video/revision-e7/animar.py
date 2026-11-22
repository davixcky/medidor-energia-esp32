#!/usr/bin/env python3
"""Construye y renderiza el video E.7 desde el ensamble FreeCAD.

    blender -b --python video/revision-e7/animar.py            # 912 fotogramas a frames/
    PREVIEW=1 blender -b --python video/revision-e7/animar.py  # una imagen por plano
    BUILD_ONLY=1 ...                                           # solo .blend y seguimiento.json
"""
from pathlib import Path
import json
import os
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

p = Path(__file__).resolve().parent
root = p.parents[1]
sys.path[:0] = [str(p), str(root / 'freecad/revision-e7')]
import linea_tiempo as lt
from escena_blender import Escena

e = Escena(fondo=(.030, .038, .050), fuerza=1.0)
s, meta = e.s, e.meta
T, fps, fr = lt.T, lt.FPS, lt.frame_de
ABIERTA = 1.0      # fracción de la trayectoria de servicio: 0 cerrada, 1 estacionada de pie
s.render.fps = fps
s.frame_start, s.frame_end = 1, lt.FRAMES
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1920, 1080, 100
s.render.image_settings.file_format = 'JPEG'
s.render.image_settings.quality = 95
s.render.filepath = str(p / 'frames/frame-')
try:
    s.eevee.taa_render_samples = 32
except AttributeError:
    pass

# ---------------------------------------------------------------- estudio
e.fondo_camara(color=(.030, .038, .050), ambiente=(.50, .56, .66), fuerza=.30)
e.suelo(color=(.030, .035, .043), rug=.5)
e.sol('Principal', (-150, -330, 430), 2.1, (1, .92, .84))
e.sol('Contra', (470, 330, 360), 1.5, (.70, .84, 1))
e.sol('Cenital', (160, 60, 520), .9, (1, 1, 1), angulo=40)

# ---------------------------------------------------------------- LCD con las pantallas del firmware
lcd = meta['lcd_area_activa']
pantallas = {}
for clave, archivo in (('verde', 'lcd-resumen.png'), ('ambar', 'lcd-sin-red.png'), ('rojo', 'lcd-alerta.png')):
    bpy.ops.mesh.primitive_plane_add(size=1, location=lcd['centro'])
    o = bpy.context.active_object
    o.name = f'LCD_pantalla_{clave}'
    o.scale = (lcd['tamano'][0], lcd['tamano'][1], 1)
    m = bpy.data.materials.new(o.name)
    m.use_nodes = True
    nt = m.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(p / 'assets' / archivo))
    tex.interpolation = 'Closest'
    emi = nt.nodes.new('ShaderNodeEmission')
    emi.inputs['Strength'].default_value = 1.15
    nt.links.new(tex.outputs['Color'], emi.inputs['Color'])
    nt.links.new(emi.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
    o.data.materials.append(m)
    bpy.context.view_layer.update()
    e.emparentar(o)
    pantallas[clave] = o

# ---------------------------------------------------------------- luz de la FCOB: cuatro zonas de 50 mm tras el difusor hexagonal
centros_fcob = e.luces_fcob()
zonas = e.zonas
seg_mats = [e.mats[f'FCOB_segmento_{i + 1}_50mm'] for i in range(4)]
led_mat = e.mats['D8_LED_verde_5mm_panel']


def lineal(c):
    return tuple((v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4) for v in c)


# Mismas proporciones RGB que escribe el firmware, llevadas a brillo de pantalla.
COLOR = {k: tuple(v / max(rgb) for v in rgb) for k, rgb in lt.COLORES_FW.items()}   # PWM lineal del firmware
VERDE_LED = lineal((.10, 1.0, .25))


def clave(mat, color, fuerza, frame, base=.85):
    b = mat.node_tree.nodes['Principled BSDF']
    for nombre, valor in (('Base Color', (*[c * base for c in color], 1)), ('Emission Color', (*color, 1)), ('Emission Strength', fuerza)):
        b.inputs[nombre].default_value = valor
        b.inputs[nombre].keyframe_insert('default_value', frame=frame)


previo = None
for frame in range(1, lt.FRAMES + 1):
    t = lt.tiempo(frame)
    est, led = lt.estado(t), lt.led_encendido(t)
    if est != (previo or (None,))[0]:
        e.color_fcob(COLOR[est], frame)       # pixels.fill(): los cuatro segmentos reciben el mismo color
        for m in seg_mats:
            clave(m, COLOR[est], 1.5, frame)
        for k, o in pantallas.items():
            o.hide_render = o.hide_viewport = k != est
            o.keyframe_insert('hide_render', frame=frame)
            o.keyframe_insert('hide_viewport', frame=frame)
    if (est, led) != previo:
        clave(led_mat, VERDE_LED if led else tuple(c * .06 for c in VERDE_LED), 2.4 if led else 0.0, frame)
    previo = (est, led)

# ---------------------------------------------------------------- tapa (suelta, con imanes) y puentes de arnés
angulos = {}
for frame in range(1, lt.FRAMES + 1):
    angulos[frame] = lt.apertura(lt.tiempo(frame), ABIERTA)
    if frame in (1, lt.FRAMES) or angulos[frame] != angulos.get(frame - 1) or lt.apertura(lt.tiempo(frame + 1), ABIERTA) != angulos[frame]:
        e.abrir(angulos[frame], frame)

# La guarda no se retira: solo se aclara en el plano de la zona de red para ver su interior.
alfa = e.mats['guard'].node_tree.nodes['Principled BSDF'].inputs['Alpha']
for t, v in ((0, .24), (T['red'], .24), (T['red'] + .7, .07), (T['cierra'][0] - .3, .07), (T['cierra'][0] - .25, .24)):
    alfa.default_value = v
    alfa.keyframe_insert('default_value', frame=fr(t))

# ---------------------------------------------------------------- cámara: planos unidos por corte
cam = e.camara()
PT = meta['puntos']
PLANOS = [  # inicio, (pos, objetivo, lente) inicial y final
    (0.0, ((440, -300, 300), (140, 88, 30), 50), ((385, -335, 315), (140, 88, 30), 50)),
    (T['panel'], ((40, -170, 250), (70, 62, 66), 50), ((250, -170, 250), (215, 62, 66), 50)),
    (T['verde'], ((150, -190, 330), (150, 98, 68), 55), ((155, -170, 310), (155, 98, 68), 55)),
    (T['ambar'], ((158, -165, 305), (158, 98, 68), 55), ((178, -105, 240), (176, 100, 68), 58)),
    (T['rojo'], ((196, -95, 205), (186, 88, 68), 58), ((200, -80, 190), (188, 88, 68), 58)),
    (T['normal'], ((480, 320, 400), (140, 62, 60), 46), ((450, 350, 430), (140, 62, 60), 46)),
    (T['interior'], ((140, 96, 560), (140, 66, 0), 50), ((140, 96, 560), (140, 66, 0), 50)),
    (T['detalle'], ((-40, 210, 235), (62, 52, 12), 58), ((20, 235, 220), (88, 60, 12), 58)),
    (T['red'], ((250, 275, 400), (185, 142, 10), 50), ((215, 285, 390), (170, 142, 10), 50)),
    (T['cierra'][0] - .25, ((440, -300, 300), (140, 88, 30), 50), ((410, -318, 308), (140, 88, 30), 50)),
]


def pose(frame, pos, hacia, lente):
    e.apuntar(cam, pos, hacia)
    cam.data.lens = lente
    cam.keyframe_insert('location', frame=frame)
    cam.keyframe_insert('rotation_euler', frame=frame)
    cam.data.keyframe_insert('lens', frame=frame)


for i, (t0, a, b) in enumerate(PLANOS):
    f0 = fr(t0)
    f1 = fr(PLANOS[i + 1][0]) - 1 if i + 1 < len(PLANOS) else lt.FRAMES
    pose(f0, *a)
    pose(f1, *b)


def lineales(ad):
    if not ad or not ad.action:
        return
    act = ad.action
    curvas = list(getattr(act, 'fcurves', []) or [])
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                curvas += list(bag.fcurves)
    for fc in curvas:
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'


for mat in zonas + seg_mats + [led_mat]:
    ad = mat.node_tree.animation_data
    if ad and ad.action:
        act = ad.action
        curvas = list(getattr(act, 'fcurves', []) or [])
        for layer in getattr(act, 'layers', []):
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curvas += list(bag.fcurves)
        for fc in curvas:
            for k in fc.keyframe_points:
                k.interpolation = 'CONSTANT'
lineales(cam.animation_data)
lineales(cam.data.animation_data)
lineales(e.bisagra.animation_data)
for o, _ in e.puentes:
    lineales(o.data.animation_data)

# ---------------------------------------------------------------- composición: halo moderado en emisores
s.use_nodes = True
nt = s.compositing_node_group
if nt is None:
    nt = bpy.data.node_groups.new('Composicion', 'CompositorNodeTree')
    s.compositing_node_group = nt
nt.nodes.clear()
nt.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
rl = nt.nodes.new('CompositorNodeRLayers')
gl = nt.nodes.new('CompositorNodeGlare')
gl.inputs['Type'].default_value = 'Fog Glow'
gl.inputs['Quality'].default_value = 'Medium'
gl.inputs['Threshold'].default_value = .85
out = nt.nodes.new('NodeGroupOutput')
nt.links.new(rl.outputs['Image'], gl.inputs['Image'])
nt.links.new(gl.outputs['Image'], out.inputs[0])

# ---------------------------------------------------------------- seguimiento para rótulos y verificación
dg = bpy.context.evaluated_depsgraph_get()


def proyectar(punto, permitidos=()):
    v = Vector(punto)
    ndc = world_to_camera_view(s, cam, v)
    origen = cam.matrix_world.translation
    d = v - origen
    ok, loc, _, _, obj, _ = s.ray_cast(dg, origen, d.normalized())
    libre = (not ok) or (loc - origen).length >= d.length - 1.5 or (obj is not None and obj.name.startswith(tuple(permitidos)))
    dentro = 0 < ndc.x < 1 and 0 < ndc.y < 1 and ndc.z > 0
    return {'x': round(ndc.x * 1920, 1), 'y': round((1 - ndc.y) * 1080, 1), 'visible': bool(dentro and libre), 'tapa': obj.name if ok and obj else None}


seguimiento = {'frames': {}, 'rotulos': {}, 'apertura': {}}
for frame in range(1, lt.FRAMES + 1):
    s.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    ang = angulos[frame]
    seguimiento['apertura'][frame] = round(ang, 3)
    seguimiento['frames'][frame] = {
        'led': proyectar(e.punto_tapa(meta['led_panel'], ang), ('D8_',)),
        'fcob': [proyectar(e.punto_tapa(c, ang), ('FCOB_luz', 'Difusor')) for c in centros_fcob],
    }
f_planta = fr(T['interior'] + 1.5)
s.frame_set(f_planta)
dg = bpy.context.evaluated_depsgraph_get()
for ref, b in meta['tarjetas'].items():
    x, y, w, d = b['rect']
    seguimiento['rotulos'][ref] = dict(proyectar((x + w / 2, y + d / 2, b['z_superior'] + 1), (ref + '_',)), rotulo=b['rotulo'],
                                       esquina=proyectar((x + 6, y + d - 6, b['z_superior']), (ref + '_',)))
seguimiento['frame_planta'] = f_planta
(p / 'seguimiento.json').write_text(json.dumps(seguimiento), encoding='utf-8')

(p / 'frames').mkdir(exist_ok=True)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'medidor-E7.blend'))
if os.environ.get('PREVIEW'):
    s.render.resolution_percentage = 50
    tiempos = [1.0, T['panel'] + 2.5, T['verde'] + 1.5, T['ambar'] + 3.2, T['rojo'] + 2.75, T['abre'][0] + 1.0, T['normal'] + 3.3,
               T['interior'] + 1.5, T['detalle'] + 1.5, T['red'] + 1.5, T['cierra'][0] + .9, lt.DUR - 1.2]
    for i, t in enumerate(tiempos, 1):
        s.frame_set(fr(t))
        s.render.filepath = str(p / f'preview-{i:02d}.jpg')
        bpy.ops.render.render(write_still=True)
elif not os.environ.get('BUILD_ONLY'):
    bpy.ops.render.render(animation=True)
