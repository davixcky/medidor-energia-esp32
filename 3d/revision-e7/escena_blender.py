"""Escena Blender del medidor E.7 a partir del ensamble exportado por FreeCAD.

La usan `render_modelo.py` (vistas fijas) y `docs/video/revision-e7/animar.py`.
La tapa es suelta (cierre magnético): cuelga de un vacío que sigue la misma
trayectoria de servicio que valida el CAD, y los tres puentes de arnés se
recalculan con la misma fórmula de coca en U.
"""
from pathlib import Path
import json
import math

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent

# rugosidad, metal, emisión, alfa
MATERIALES = {
    "body": (.55, 0, 0, 1), "lid": (.48, 0, 0, 1), "guard": (.58, 0, 0, 1), "perf": (.75, 0, 0, 1),
    "pad": (.35, .9, 0, 1), "nylon": (.5, 0, 0, 1), "screw": (.35, .9, 0, 1), "metal": (.28, 1, 0, 1),
    "gold": (.3, 1, 0, 1), "ic": (.5, 0, 0, 1), "jst": (.5, 0, 0, 1), "plug": (.5, 0, 0, 1), "hdr": (.45, 0, 0, 1),
    "tb": (.45, 0, 0, 1), "resistor": (.4, 0, 0, 1), "lead": (.3, 1, 0, 1), "diode": (.2, 0, 0, 1),
    "capc": (.5, 0, 0, 1), "cape": (.35, 0, 0, 1), "ptc": (.5, 0, 0, 1), "pcb_blue": (.4, 0, 0, 1),
    "pcb_dark": (.4, 0, 0, 1), "trimmer": (.4, 0, 0, 1), "brass": (.3, 1, 0, 1), "coil": (.5, .3, 0, 1), "magnet": (.25, 1, 0, 1),
    "w_power": (.5, 0, 0, 1), "w_analog": (.5, 0, 0, 1), "w_digital": (.5, 0, 0, 1), "w_lid": (.5, 0, 0, 1),
    "w_L": (.5, 0, 0, 1), "w_N": (.5, 0, 0, 1), "rubber": (.8, 0, 0, 1), "strip": (.6, 0, 0, 1),
    "seg": (.4, 0, 1.5, 1), "diffuser": (.35, 0, 0, 1), "glass": (.08, 0, 0, 1), "led": (.3, 0, 2.0, 1),
    "knob": (.42, 0, 0, 1), "piezo": (.5, 0, 0, 1), "warning": (.38, 0, .15, 1),
}


class Escena:
    def __init__(self, fondo=(.10, .12, .15), fuerza=.55):
        self.meta = json.loads((HERE / "metadatos-ensamble.json").read_text(encoding="utf-8"))
        data = json.loads((HERE / ".render/ensamble.json").read_text(encoding="utf-8"))
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.s = s = bpy.context.scene
        s.render.engine = "BLENDER_EEVEE"
        s.render.image_settings.file_format = "PNG"
        s.view_settings.look = "AgX - Medium High Contrast"
        try:
            s.eevee.use_raytracing = True
            s.eevee.taa_render_samples = 48
        except AttributeError:
            pass
        s.world = bpy.data.worlds.new("Mundo")
        s.world.use_nodes = True
        bg = s.world.node_tree.nodes["Background"]
        bg.inputs["Color"].default_value = (*fondo, 1)
        bg.inputs["Strength"].default_value = fuerza

        self.objetos, self.grupos, self.mats = {}, {}, {}
        py, pz = self.meta["tapa"]["pivote_yz"]
        self.pivote = Vector((0, py, pz))
        self.trayectoria = self.meta["tapa"]["trayectoria"]
        self.bisagra = bpy.data.objects.new("Tapa_trayectoria_servicio", None)
        self.bisagra.location = self.pivote
        self.bisagra.empty_display_size = 12
        s.collection.objects.link(self.bisagra)
        bpy.context.view_layer.update()
        for d in data:
            if d["group"] == "bridge":
                continue
            o = self._malla(d)
            if d["group"] == "lid":
                self.emparentar(o)
        self.puentes = [self._puente(b) for b in self.meta["puentes"]]
        self.abrir(0)
        self._pantalla_lilygo()

    # ---------------------------------------------------------------- construcción
    def material(self, nombre, clave, color):
        if nombre in self.mats:
            return self.mats[nombre]
        rug, metal, emis, alfa = MATERIALES[clave]
        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
        m.diffuse_color = (*color, alfa)
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = rug
        b.inputs["Metallic"].default_value = metal
        if emis:
            b.inputs["Emission Color"].default_value = (*color, 1)
            b.inputs["Emission Strength"].default_value = emis
        if alfa < 1:
            b.inputs["Alpha"].default_value = alfa
            m.surface_render_method = "BLENDED"
        self.mats[nombre] = m
        return m

    def _malla(self, d):
        me = bpy.data.meshes.new(d["name"])
        me.from_pydata(d["vertices"], [], d["faces"])
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=.002)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(38))
        me.update()
        o = bpy.data.objects.new(d["name"], me)
        self.s.collection.objects.link(o)
        # Los emisores animables llevan material propio; el resto comparte por tipo.
        propio = d["material"] in ("seg", "led", "diffuser")
        o.data.materials.append(self.material(d["name"] if propio else d["material"], d["material"], d["color"]))
        self.objetos[d["name"]] = o
        self.grupos[d["name"]] = d["group"]
        return o

    def _pantalla_lilygo(self):
        """Plano emisivo de la interfaz táctil horizontal sobre el vidrio del T4-S3."""
        p = self.meta["lcd_area_activa"]
        cx, cy, z = p["centro"]
        w, h = p["tamano"]
        me = bpy.data.meshes.new("LilyGO_interfaz_horizontal")
        me.from_pydata([(cx - w / 2, cy - h / 2, z + .04), (cx + w / 2, cy - h / 2, z + .04),
                        (cx + w / 2, cy + h / 2, z + .04), (cx - w / 2, cy + h / 2, z + .04)], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new(name="UV")
        for loop, co in zip(uv.data, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop.uv = co
        o = bpy.data.objects.new("LilyGO_T4S3_interfaz_tactil_600x450", me)
        self.s.collection.objects.link(o)
        m = bpy.data.materials.new("LilyGO_interfaz")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        tex = m.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(HERE / "tft-render-horizontal.png"))
        m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        m.node_tree.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 1.25
        b.inputs["Roughness"].default_value = .3
        me.materials.append(m)
        self.emparentar(o)
        self.objetos[o.name] = o
        self.grupos[o.name] = "lid"

    def emparentar(self, o):
        o.parent = self.bisagra
        o.matrix_parent_inverse = self.bisagra.matrix_world.inverted()

    def _puente(self, b):
        cu = bpy.data.curves.new("Puente_arnes_" + b["nombre"], "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = b["radio"]
        cu.bevel_resolution = 4
        cu.use_fill_caps = True
        sp = cu.splines.new("POLY")
        sp.points.add(22)
        o = bpy.data.objects.new(cu.name, cu)
        self.s.collection.objects.link(o)
        o.data.materials.append(self.material("w_lid", "w_lid", (.62, .66, .72)))
        self.objetos[o.name] = o
        self.grupos[o.name] = "bridge"
        return o, b

    # ---------------------------------------------------------------- cinemática
    def pose_tapa(self, f):
        """(giro en grados, avance Y, elevación Z) para la fracción f de la trayectoria; igual que lid_pose() del CAD."""
        f = min(max(f, 0.0), 1.0)
        for (f0, *a), (f1, *b) in zip(self.trayectoria, self.trayectoria[1:]):
            if f <= f1:
                u = (f - f0) / (f1 - f0)
                return tuple(a[k] + (b[k] - a[k]) * u for k in range(3))
        return tuple(self.trayectoria[-1][1:])

    def punto_tapa(self, p, f):
        grados, dy, dz = self.pose_tapa(f)
        a = math.radians(grados)
        y, z = p[1] - self.pivote.y, p[2] - self.pivote.z
        return (p[0], self.pivote.y + y * math.cos(a) - z * math.sin(a) + dy, self.pivote.z + y * math.sin(a) + z * math.cos(a) + dz)

    def puntos_puente(self, b, f, n=20):
        pl, pb, s, largo = self.punto_tapa(b["tapa"], f), b["base"], b["sentido"], b["longitud_mm"]
        c = math.dist(pl, pb)
        rad = c / 2
        tramo = (largo - math.pi * rad) / 2
        u = [(pl[k] - pb[k]) / c for k in range(3)]
        mid = [(pl[k] + pb[k]) / 2 for k in range(3)]
        pts = [tuple(pb)]
        for i in range(n + 1):
            f = math.pi * i / n
            pts.append(tuple(mid[k] + (s * (tramo + rad * math.sin(f)) if k == 0 else 0) - rad * math.cos(f) * u[k] for k in range(3)))
        pts.append(tuple(pl))
        return pts

    def abrir(self, f, frame=None):
        """Lleva la tapa a la fracción f (0 cerrada, 1 estacionada); con `frame` inserta fotogramas clave en tapa y puentes."""
        grados, dy, dz = self.pose_tapa(f)
        self.bisagra.rotation_euler = (math.radians(grados), 0, 0)
        self.bisagra.location = self.pivote + Vector((0, dy, dz))
        if frame is not None:
            self.bisagra.keyframe_insert("rotation_euler", frame=frame)
            self.bisagra.keyframe_insert("location", frame=frame)
        for o, b in self.puentes:
            sp = o.data.splines[0]
            for p, co in zip(sp.points, self.puntos_puente(b, f)):
                p.co = (*co, 1)
                if frame is not None:
                    p.keyframe_insert("co", frame=frame)

    # ---------------------------------------------------------------- luz de la FCOB tras el difusor hexagonal
    def _mapa_hex(self, px_mm=20):
        """Imagen de brillo de una zona de 50 mm: más clara donde el difusor es más fino.

        Es una ilustración (brillo = exp(-(espesor - 0,3 mm))), no una simulación óptica.
        """
        import numpy as np
        f, hx = self.meta["fcob"], self.meta["fcob"]["hex"]
        R, a, g, w = hx["radio"], hx["entre_caras"], hx["surco"], hx["aro"]
        t_s, t_c, t_r = hx["espesores_mm"]
        nx, ny = int(f["segmento"] * px_mm), int(2 * a * px_mm)
        x = (np.arange(nx) + .5) / px_mm
        y = (np.arange(ny) + .5) / px_mm - a
        X, Y = np.meshgrid(x, y)
        d = np.full(X.shape, 1e9)
        for i in range(int(f["segmento"] / (1.5 * R)) + 2):
            for j in range(-2, 3):
                dx, dy = np.abs(X - 1.5 * R * i), np.abs(Y - a * (j + (.5 if i % 2 else 0)))
                d = np.minimum(d, np.maximum(dy, dx * math.sqrt(3) / 2 + dy / 2))
        esp = np.where(d > (a - g) / 2, t_s, np.where(d > (a - g) / 2 - w, t_r, t_c))
        b = np.exp(-(esp - t_s))
        img = bpy.data.images.new("Difusor_hex_brillo", nx, ny, alpha=False, float_buffer=True)
        img.colorspace_settings.name = "Non-Color"
        img.pixels.foreach_set(np.dstack([b, b, b, np.ones_like(b)]).astype(np.float32).ravel())
        img.pack()
        return img

    def luces_fcob(self, fuerza=1.3):
        """Single capsule-shaped emitter with a repeated 50 mm hex map."""
        f = self.meta["fcob"]
        x0, x1, y0, y1 = f["ventana"]
        img = self._mapa_hex()
        yc, r, z = (y0 + y1) / 2, (y1 - y0) / 2, f["z_difusor"] + .03
        pts = []
        for i in range(13):
            a = math.radians(-90 + 180 * i / 12)
            pts.append((x1 - r + r * math.cos(a), yc + r * math.sin(a), z))
        for i in range(13):
            a = math.radians(90 + 180 * i / 12)
            pts.append((x0 + r + r * math.cos(a), yc + r * math.sin(a), z))
        me = bpy.data.meshes.new("FCOB_luz_capsula")
        me.from_pydata(pts, [], [tuple(range(len(pts)))])
        uv = me.uv_layers.new(name="UV")
        for i, loop in enumerate(uv.data):
            vx, vy, _ = pts[me.loops[i].vertex_index]
            loop.uv = ((vx - x0) / f["segmento"], (vy - y0) / (y1 - y0))
        o = bpy.data.objects.new("FCOB_luz_capsula_redondeada", me)
        self.s.collection.objects.link(o)
        m = bpy.data.materials.new(o.name)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image, tex.extension = img, "REPEAT"
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.name = "Color_estado"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        emi = nt.nodes.new("ShaderNodeEmission")
        emi.inputs["Strength"].default_value = fuerza
        nt.links.new(rgb.outputs["Color"], mix.inputs["A"])
        nt.links.new(tex.outputs["Color"], mix.inputs["B"])
        nt.links.new(mix.outputs["Result"], emi.inputs["Color"])
        nt.links.new(emi.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
        o.data.materials.append(m)
        self.emparentar(o)
        self.zonas = [m]
        centros = [(x0 + f["segmento"] * (i + .5), yc, z) for i in range(4)]
        return centros

    def color_fcob(self, color, frame=None):
        """pixels.fill(): las cuatro zonas reciben siempre el mismo color."""
        for m in self.zonas:
            salida = m.node_tree.nodes["Color_estado"].outputs["Color"]
            salida.default_value = (*color, 1)
            if frame is not None:
                salida.keyframe_insert("default_value", frame=frame)

    # ---------------------------------------------------------------- estudio
    def suelo(self, color=(.55, .57, .60), rug=.7):
        bpy.ops.mesh.primitive_plane_add(size=4000, location=(140, 90, -3.02))
        o = bpy.context.active_object
        o.name = "Suelo"
        m = bpy.data.materials.new("Suelo")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*color, 1)
        b.inputs["Roughness"].default_value = rug
        o.data.materials.append(m)
        return o

    def luz(self, nombre, pos, energia, tam, color=(1, 1, 1), hacia=(140, 90, 30)):
        ld = bpy.data.lights.new(nombre, "AREA")
        ld.energy, ld.shape, ld.size, ld.color = energia, "DISK", tam, color
        lo = bpy.data.objects.new(nombre, ld)
        self.s.collection.objects.link(lo)
        lo.location = pos
        lo.rotation_euler = (Vector(hacia) - lo.location).to_track_quat("-Z", "Y").to_euler()
        return lo

    def sol(self, nombre, desde, fuerza, color=(1, 1, 1), angulo=25, hacia=(140, 90, 30)):
        """Luz direccional: la escena está en milímetros y una luz de área se apagaría con la distancia."""
        ld = bpy.data.lights.new(nombre, "SUN")
        ld.energy, ld.color, ld.angle = fuerza, color, math.radians(angulo)
        lo = bpy.data.objects.new(nombre, ld)
        self.s.collection.objects.link(lo)
        lo.location = desde
        lo.rotation_euler = (Vector(hacia) - lo.location).to_track_quat("-Z", "Y").to_euler()
        return lo

    def fondo_camara(self, color, ambiente, fuerza):
        """La cámara ve `color`; la escena recibe `ambiente` como luz de relleno."""
        nt = self.s.world.node_tree
        bg = nt.nodes["Background"]
        lp = nt.nodes.new("ShaderNodeLightPath")
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["A"].default_value = (*[c * fuerza for c in ambiente], 1)
        mix.inputs["B"].default_value = (*color, 1)
        nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = 1.0

    def camara(self, lente=50):
        cd = bpy.data.cameras.new("Camara")
        cd.lens = lente
        cd.clip_start, cd.clip_end = 5, 6000
        cam = bpy.data.objects.new("Camara", cd)
        self.s.collection.objects.link(cam)
        self.s.camera = cam
        return cam

    @staticmethod
    def apuntar(cam, pos, hacia):
        cam.location = pos
        cam.rotation_euler = (Vector(hacia) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
