#!/usr/bin/env python3
"""Exporta el FCStd E.5 a JSON y crea las vistas con Blender."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent; TEMP=HERE/".render"


def exportar():
    import FreeCAD as App
    TEMP.mkdir(exist_ok=True); doc=App.openDocument(str(HERE/"medidor-E5-perforadas.FCStd")); data=[]
    for o in doc.Objects:
        if not hasattr(o,"Shape") or o.Shape.isNull(): continue
        vertices,faces=o.Shape.tessellate(.18)
        data.append({"name":o.Name,"vertices":[tuple(v) for v in vertices],"faces":faces,
                     "color":[float(v) for v in o.ColorRGB.split(",")],"group":o.AssemblyGroup})
    path=TEMP/"ensamble.json"; path.write_text(json.dumps(data),encoding="utf-8"); print(path)


def renderizar(path):
    import bpy
    from mathutils import Vector
    data=json.loads(Path(path).read_text()); bpy.ops.wm.read_factory_settings(use_empty=True); s=bpy.context.scene
    s.render.engine="BLENDER_EEVEE"; s.render.resolution_x,s.render.resolution_y=2100,1350
    s.render.resolution_percentage=100; s.render.image_settings.file_format="PNG"
    s.world=bpy.data.worlds.new("World"); s.world.use_nodes=True
    bg=s.world.node_tree.nodes.get("Background"); bg.inputs["Color"].default_value=(.72,.74,.78,1); bg.inputs["Strength"].default_value=.75
    s.view_settings.look="AgX - Medium High Contrast"; objects={}; groups={}
    for d in data:
        me=bpy.data.meshes.new(d["name"]); me.from_pydata(d["vertices"],[],d["faces"]); me.update()
        o=bpy.data.objects.new(d["name"],me); s.collection.objects.link(o)
        m=bpy.data.materials.new(d["name"]); m.diffuse_color=(*d["color"],1); m.use_nodes=True
        sh=m.node_tree.nodes.get("Principled BSDF"); sh.inputs["Base Color"].default_value=(*d["color"],1); sh.inputs["Roughness"].default_value=.62
        if "NeoPixels" in d["name"]: sh.inputs["Emission Color"].default_value=(*d["color"],1); sh.inputs["Emission Strength"].default_value=2
        o.data.materials.append(m); objects[d["name"]]=o; groups[d["name"]]=d["group"]
    for pos,energy,size in (((-180,-250,380),1400,240),((420,80,300),1000,200)):
        ld=bpy.data.lights.new("Area","AREA"); ld.energy=energy; ld.size=size
        lo=bpy.data.objects.new("Area",ld); s.collection.objects.link(lo); lo.location=pos
        lo.rotation_euler=(Vector((170,120,20))-lo.location).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new("Camera"); cd.type="ORTHO"; cam=bpy.data.objects.new("Camera",cd); s.collection.objects.link(cam); s.camera=cam
    def shot(name,target,direction,scale):
        target=Vector(target); cam.location=target+Vector(direction).normalized()*700
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); cd.ortho_scale=scale
        s.render.filepath=str(HERE/name); bpy.ops.render.render(write_still=True)
    for n,o in objects.items(): o.location=(0,0,0); o.hide_render=False
    shot("medidor-E5-cerrado.png",(170,120,32),(-.65,-.9,1),420)
    for n,o in objects.items():
        o.location=(365,0,-67) if groups[n]=="lid" else ((0,260,-46) if groups[n]=="guard" else (0,0,0)); o.hide_render=False
    shot("medidor-E5-abierto.png",(265,120,22),(-.5,-.9,1.2),610)
    for n,o in objects.items(): o.location=(0,0,0); o.hide_render=groups[n] in ("lid","guard")
    shot("medidor-E5-planta.png",(170,120,13),(0,-.05,1),380)


if "--" in sys.argv: renderizar(sys.argv[-1])
else: exportar()
