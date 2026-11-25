#!/usr/bin/env python3
"""Exporta el FCStd E.7 a JSON (con FreeCAD) y crea las vistas de revisión (con Blender).

    freecadcmd  -> escribe .render/ensamble.json
    blender -b --python render_modelo.py -- vistas
"""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
TEMP = HERE / ".render"


def exportar():
    import FreeCAD as App
    TEMP.mkdir(exist_ok=True)
    doc = App.openDocument(str(HERE / "medidor-E7-perforadas.FCStd"))
    data = []
    for o in doc.Objects:
        if not hasattr(o, "Shape") or o.Shape.isNull():
            continue
        vertices, faces = o.Shape.tessellate(.12)
        data.append({"name": o.Name, "vertices": [tuple(round(c, 4) for c in v) for v in vertices], "faces": faces,
                     "color": [float(v) for v in o.ColorRGB.split(",")], "material": o.Material, "group": o.AssemblyGroup})
    path = TEMP / "ensamble.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    print(path, len(data), "objetos")


def renderizar():
    sys.path.insert(0, str(HERE))
    import bpy
    from escena_blender import Escena

    e = Escena()
    s = e.s
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 2100, 1350, 100
    e.suelo((.045, .055, .07), .55)
    # Dark visible background, with a separate neutral environment fill so the dark enclosure
    # retains the same readable product contrast as the equalizer renders.
    e.fondo_camara((.035, .045, .06), (.55, .57, .60), .9)
    e.luz("Principal", (-160, -260, 420), 52000, 260)
    e.luz("Relleno", (480, 60, 330), 32000, 240)
    e.luz("Trasera", (140, 480, 300), 28000, 240)
    cam = e.camara(50)
    e.luces_fcob(fuerza=.9)
    e.color_fcob((0, 1.0, 10 / 18))      # estado normal del firmware: verde (0,18,10) en los cuatro segmentos

    def toma(nombre, f, pos, hacia, lente=50, orto=None):
        e.abrir(f)
        cam.data.type = "ORTHO" if orto else "PERSP"
        if orto:
            cam.data.ortho_scale = orto
        cam.data.lens = lente
        e.apuntar(cam, pos, hacia)
        s.render.filepath = str(HERE / nombre)
        bpy.ops.render.render(write_still=True)

    abierta = 1.0      # tapa de pie en los bolsillos de estacionamiento
    toma("medidor-E7-cerrado.png", 0, (-150, -400, 330), (140, 84, 28))
    toma("medidor-E7-abierto.png", abierta, (470, 330, 420), (140, 70, 45))
    toma("medidor-E7-planta.png", abierta, (140, 89, 700), (140, 90, 0), orto=330)
    toma("medidor-E7-trasera.png", 0, (-190, 500, 300), (140, 96, 28))
    toma("medidor-E7-tapa-interior.png", abierta, (150, 330, 250), (140, 5, 130), lente=42)
    toma("medidor-E7-difusor.png", 0, (118, 30, 215), (128, 100, 68), lente=70)
    toma("medidor-E7-cierre-magnetico.png", .45, (430, -250, 250), (140, 70, 70), lente=50)
    toma("medidor-E9-entradas-SCT.png", 0, (-145, 76, 105), (0, 106, 38), lente=72)
    toma("medidor-E9-alimentacion-12V.png", 0, (425, -55, 115), (280, 36, 40), lente=72)
    toma("medidor-E9-ruta-alimentacion-interior.png", abierta, (88, 112, 185), (226, 29, 27), lente=50)

    # Vista didáctica del soporte de pantalla. La tapa, la pantalla y la placa trasera de
    # deslizamiento se separan solo para mostrar el orden de montaje sin tornillos.
    e.abrir(0)
    bpy.ops.wm.stl_import(filepath=str(HERE / "pruebas-de-ajuste/tapa_pantalla_T4S3.stl"))
    front = bpy.context.object
    front.name = "Frente_prueba_pantalla_T4S3"
    front.data.materials.append(e.material("frente_pantalla", "lid", (.68, .70, .73)))
    keep = {front.name, "LilyGO_T4S3_PCB_51p56x38p72", "LilyGO_T4S3_AMOLED_vidrio_56x44",
            "LilyGO_VBUS_GND_2vias", "Placa_trasera_desmontable_LCD"}
    for obj in s.objects:
        if obj.type in {"MESH", "CURVE"}:
            obj.hide_render = obj.name not in keep
    for name in ("LilyGO_T4S3_PCB_51p56x38p72", "LilyGO_T4S3_AMOLED_vidrio_56x44", "LilyGO_VBUS_GND_2vias"):
        e.objetos[name].location.z -= 8
    pcb = e.objetos["LilyGO_T4S3_PCB_51p56x38p72"]
    pcb.data.materials.clear()
    pcb.data.materials.append(e.material("pcb_pantalla_acento", "pcb_dark", (.035, .24, .13)))
    back = e.objetos["Placa_trasera_desmontable_LCD"]
    back.location.z -= 18
    # Color propio para distinguir la pieza impresa desmontable de la tapa fija.
    accent = e.material("placa_trasera_acento", "nylon", (.20, .48, .78))
    back.data.materials.clear()
    back.data.materials.append(accent)
    s.render.resolution_x, s.render.resolution_y = 1800, 1350
    cam.data.type = "PERSP"
    cam.data.lens = 62
    e.apuntar(cam, (190, -170, -50), (56, 52, 48))
    s.render.filepath = str(HERE / "medidor-E8-pantalla-soporte-explotado.png")
    bpy.ops.render.render(write_still=True)


if "--" in sys.argv:
    renderizar()
else:
    exportar()
