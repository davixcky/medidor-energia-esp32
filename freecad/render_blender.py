"""Vistas del medidor con Blender (Cycles por CPU), con los colores de cada componente de la PCB.

Se ejecuta en dos pasos (los llama generar.sh):
    freecadcmd render_blender.py                      exporta las mallas del ensamble a .render/
    blender --background --python render_blender.py -- .render/ensamble.json
Conserva los nombres de las ilustraciones: ../img/3d-medidor-{cerrado,abierto,planta}.png.
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
TEMP = os.path.join(AQUI, ".render")


def exportar():
    import FreeCAD as App
    import Part
    import Import

    os.makedirs(TEMP, exist_ok=True)
    doc = App.openDocument(os.path.join(AQUI, "medidor.FCStd"))
    piezas = [o for o in doc.Objects if hasattr(o, "ColorRGB")]
    Import.export(piezas, os.path.join(AQUI, "medidor.step"))
    datos = []

    def agregar(nombre, forma, color, grupo, abierta=None):
        vertices, caras = forma.tessellate(0.12)
        datos.append(dict(nombre=nombre, vertices=[tuple(v) for v in vertices], caras=caras,
                          color=color, grupo=grupo, abierta=abierta))

    for o in piezas:
        if o.Name == "Placa_KiCad":
            antes = set(x.Name for x in doc.Objects)
            Import.insert(os.path.join(AQUI, o.ArchivoSTEP), doc.Name)
            for componente in doc.Objects:
                if componente.Name in antes or componente.TypeId != "Part::Feature":
                    continue
                forma = componente.Shape.copy()
                if forma.isNull() or forma.Volume <= 0:
                    continue
                forma.translate(o.Traslado)
                etiqueta = componente.Label
                color = (0.14, 0.14, 0.15)
                if "PCB" in etiqueta:
                    color = (0.14, 0.38, 0.24)
                elif "TerminalBlock" in etiqueta:
                    color = (0.15, 0.48, 0.29)
                elif "ESP32" in etiqueta or ("devkit" in etiqueta.lower() and
                        (forma.BoundBox.XLength < 1 or
                         (7 < forma.BoundBox.XLength < 9 and 5 < forma.BoundBox.YLength < 6))):
                    color = (0.65, 0.68, 0.71)
                elif "R_Axial" in etiqueta:
                    color = (0.72, 0.65, 0.48)
                elif "C_Disc" in etiqueta:
                    color = (0.65, 0.35, 0.15)
                agregar(componente.Name, forma, color, "interior")
            continue
        color = tuple(float(c) for c in o.ColorRGB.split(","))
        agregar(o.Name, o.Shape, color, o.Grupo)
        if hasattr(o, "FormaAbierta"):
            datos[-1]["abierta"] = o.Name + "_abierta"
            agregar(o.Name + "_abierta", o.FormaAbierta, color, "servicio")
    ruta = os.path.join(TEMP, "ensamble.json")
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo)
    print("Mallas del medidor exportadas:", ruta)


def renderizar():
    import bpy
    from mathutils import Vector

    with open(sys.argv[-1], encoding="utf-8") as archivo:
        datos = json.load(archivo)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    escena = bpy.context.scene
    escena.render.engine = "CYCLES"
    escena.cycles.device = "CPU"
    escena.cycles.samples = 32
    escena.cycles.use_denoising = True
    escena.render.resolution_x = 2000
    escena.render.resolution_y = 1250
    escena.render.resolution_percentage = 100
    escena.world.use_nodes = True
    escena.world.node_tree.nodes.get("Background").inputs[0].default_value = (1, 1, 1, 1)
    escena.world.node_tree.nodes.get("Background").inputs[1].default_value = 1
    mundo = escena.world.node_tree
    ambiente = mundo.nodes.get("Background")
    ambiente.inputs[1].default_value = 0.3
    blanco = mundo.nodes.new("ShaderNodeBackground")
    blanco.inputs[0].default_value = (1, 1, 1, 1)
    rayos = mundo.nodes.new("ShaderNodeLightPath")
    mezcla = mundo.nodes.new("ShaderNodeMixShader")
    mundo.links.new(rayos.outputs["Is Camera Ray"], mezcla.inputs[0])
    mundo.links.new(ambiente.outputs[0], mezcla.inputs[1])
    mundo.links.new(blanco.outputs[0], mezcla.inputs[2])
    mundo.links.new(mezcla.outputs[0], mundo.nodes.get("World Output").inputs[0])
    escena.view_settings.view_transform = "Standard"
    objetos = {}
    for dato in datos:
        malla = bpy.data.meshes.new(dato["nombre"])
        malla.from_pydata(dato["vertices"], [], dato["caras"])
        malla.update()
        objeto = bpy.data.objects.new(dato["nombre"], malla)
        escena.collection.objects.link(objeto)
        material = bpy.data.materials.new(dato["nombre"])
        material.diffuse_color = (*dato["color"], 1)
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = (*dato["color"], 1)
        shader.inputs["Roughness"].default_value = 0.65
        objeto.data.materials.append(material)
        objetos[dato["nombre"]] = objeto
    for posicion, potencia, tam in (((-100, -150, 450), 180000, 350), ((350, 100, 350), 120000, 300)):
        luz = bpy.data.lights.new("Luz", "AREA")
        luz.energy, luz.shape, luz.size = potencia, "DISK", tam
        objeto = bpy.data.objects.new("Luz", luz)
        escena.collection.objects.link(objeto)
        objeto.location = posicion
        objeto.rotation_euler = (Vector((150, 70, 0)) - objeto.location).to_track_quat('-Z', 'Y').to_euler()
    camara = bpy.data.cameras.new("Cámara")
    camara.type = "ORTHO"
    objeto = bpy.data.objects.new("Cámara", camara)
    escena.collection.objects.link(objeto)
    escena.camera = objeto
    for vista, centro, direccion, escala in (
        ("cerrado", (100, 75, 35), (-0.75, -1, 0.95), 370),
        ("abierto", (220, 75, 20), (-0.25, -0.65, 1.5), 520),
        ("planta", (100, 75, 20), (0, -0.18, 1), 310),
    ):
        if vista not in os.environ.get("VISTAS", "cerrado,abierto,planta").split(","):
            continue
        for dato in datos:
            pieza = objetos[dato["nombre"]]
            grupo = dato["grupo"]
            pieza.location = (240, 0, -72) if grupo == "tapa" and vista == "abierto" else (0, 0, 0)
            pieza.hide_render = ((grupo == "servicio" and vista != "abierto") or
                                 (grupo == "tapa" and vista == "planta") or
                                 (bool(dato["abierta"]) and vista != "cerrado"))
        objetivo = Vector(centro)
        objeto.location = objetivo + Vector(direccion).normalized() * 700
        objeto.rotation_euler = (objetivo - objeto.location).to_track_quat('-Z', 'Y').to_euler()
        camara.ortho_scale = escala
        escena.render.filepath = os.path.join(AQUI, "..", "img", f"3d-medidor-{vista}.png")
        bpy.ops.render.render(write_still=True)


if "--" in sys.argv:
    renderizar()
else:
    exportar()
