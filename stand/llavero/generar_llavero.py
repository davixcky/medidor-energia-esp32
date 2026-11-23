#!/usr/bin/env python3
"""Llavero de dos colores con forma de pinza SCT-013.

El aro de la llavero pasa por el hueco de la pinza, como el conductor de fase.
Genera, por cada chiste: STL de la base, STL del color, un 3MF de dos partes
(Bambu Studio / OrcaSlicer asignan el filamento 1 y 2) y una vista previa PNG.

Uso:  pip install trimesh shapely mapbox_earcut manifold3d fonttools pillow
      python3 stand/llavero/generar_llavero.py
"""
from pathlib import Path
import math
import zipfile

import trimesh
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

AQUI = Path(__file__).resolve().parent
FUENTE = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FUENTE_PEQ = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

# --- medidas (mm) ---
R_EXT, R_HUECO = 13.0, 6.0          # aro de la pinza; hueco de 12 mm para la argolla
CUERPO = (9.0, -13.0, 66.0, 13.0)   # cuerpo rectangular de la pinza
R_ESQ = 5.0
ALTO, INCRUSTE = 3.6, 0.6           # espesor total y profundidad del segundo color (3 capas de 0,2)
MARGEN = 1.6                        # borde de la base alrededor del color
TEXTO_X = (19.0, CUERPO[2] - 3.2)   # zona útil para texto

CHISTES = {
    "fase": (["SOLO ABRAZO", "LA FASE"], "fase + neutro = 0,0 A"),
    "hardexplosion": (["HARDEXPLOSION:", "PENDIENTE"], "prueba de resistencia · CUC"),
    "revision": (["REVISIÓN E.9", "ESTA SÍ ES"], "la final (dijimos igual en la E.5)"),
}


# ---------- texto a polígonos ----------
class Contornos(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.contornos, self.actual = [], []

    def _moveTo(self, p):
        self.actual = [p]

    def _lineTo(self, p):
        self.actual.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.actual[-1]
        for k in range(1, 9):
            t = k / 8
            self.actual.append(tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d
                                     for a, b, c, d in zip(p0, p1, p2, p3)))

    def _qCurveToOne(self, p1, p2):
        p0 = self.actual[-1]
        for k in range(1, 7):
            t = k / 6
            self.actual.append(tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t ** 2 * c for a, b, c in zip(p0, p1, p2)))

    def _closePath(self):
        if len(self.actual) > 2:
            self.contornos.append(self.actual)
        self.actual = []

    _endPath = _closePath


def texto(cadena, ruta_fuente):
    """Polígono del texto en unidades de la fuente, con la línea base en y=0."""
    f = TTFont(ruta_fuente)
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    x, partes = 0, []
    for ch in cadena:
        nombre = cmap.get(ord(ch))
        if nombre is None:
            continue
        pen = Contornos(gs)
        gs[nombre].draw(pen)
        letra = None
        for c in pen.contornos:  # par/impar: los contornos internos abren huecos
            p = Polygon(c).buffer(0)
            letra = p if letra is None else letra.symmetric_difference(p)
        if letra is not None:
            partes.append(affinity.translate(letra, x, 0))
        x += hmtx[nombre][0]
    cap = f["OS/2"].sCapHeight
    return unary_union(partes), cap


def linea(cadena, fuente, alto_cap, ancho_max, x0, y_base):
    g, cap = texto(cadena, fuente)
    s = alto_cap / cap
    minx, _, maxx, _ = g.bounds
    if (maxx - minx) * s > ancho_max:
        s = ancho_max / (maxx - minx)
    g = affinity.scale(g, s, s, origin=(0, 0))
    minx = g.bounds[0]
    return affinity.translate(g, x0 - minx, y_base)


# ---------- geometría ----------
def contorno():
    aro = Point(0, 0).buffer(R_EXT, 128)
    x0, y0, x1, y1 = CUERPO
    cuerpo = box(x0 + R_ESQ, y0 + R_ESQ, x1 - R_ESQ, y1 - R_ESQ).buffer(R_ESQ, 32)
    union = unary_union([aro, cuerpo])
    # transición suave entre aro y cuerpo
    union = union.buffer(-2.0, 32).buffer(2.0, 32)
    return union.difference(Point(0, 0).buffer(R_HUECO, 96))


def arco(r1, r2, a0, a1, n=96):
    ext = [(r2 * math.cos(math.radians(a0 + (a1 - a0) * k / n)), r2 * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    inn = [(r1 * math.cos(math.radians(a1 - (a1 - a0) * k / n)), r1 * math.sin(math.radians(a1 - (a1 - a0) * k / n))) for k in range(n + 1)]
    return Polygon(ext + inn)


def color(lineas, pie):
    # núcleo de la pinza: arco con la ranura de apertura arriba
    nucleo = arco(R_HUECO + 2.2, R_HUECO + 3.6, 105, 435)
    ancho = TEXTO_X[1] - TEXTO_X[0]
    t1 = linea(lineas[0], FUENTE, 5.2, ancho, TEXTO_X[0], 4.0)
    t2 = linea(lineas[1], FUENTE, 5.2, ancho, TEXTO_X[0], -3.2)
    t3 = linea(pie, FUENTE_PEQ, 2.9, ancho, TEXTO_X[0], -9.0)
    # rayo pequeño a la izquierda del texto
    rayo = Polygon([(13.6, 6.5), (11.0, 0.4), (13.0, 0.4), (11.6, -5.5), (16.2, 1.6), (14.0, 1.6), (15.8, 6.5)])
    verde = unary_union([nucleo, t1, t2, t3, rayo])
    seguro = contorno().buffer(-MARGEN)
    return verde.intersection(seguro)


def extruir(geom, z0, z1):
    geoms = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    mallas = [trimesh.creation.extrude_polygon(g, z1 - z0) for g in geoms if g.area > 1e-3]
    m = trimesh.util.concatenate(mallas)
    m.apply_translation((0, 0, z0))
    return m


def mallas(lineas, pie):
    forma, verde = contorno(), color(lineas, pie)
    base = trimesh.boolean.union([extruir(forma, 0, ALTO - INCRUSTE),
                                  extruir(forma.difference(verde), ALTO - INCRUSTE - 0.01, ALTO)], engine="manifold")
    capa = extruir(verde, ALTO - INCRUSTE, ALTO)
    capa = trimesh.boolean.union([capa], engine="manifold")
    return forma, verde, base, capa


# ---------- 3MF de dos partes ----------
def malla_xml(m):
    vv = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in m.vertices)
    tt = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
    return f"<mesh><vertices>{vv}</vertices><triangles>{tt}</triangles></mesh>"


def escribir_3mf(ruta, nombre, base, capa):
    modelo = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<model unit="millimeter" xml:lang="es" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
              f'<metadata name="Title">{nombre}</metadata><resources>'
              f'<object id="1" type="model" name="base">{malla_xml(base)}</object>'
              f'<object id="2" type="model" name="color">{malla_xml(capa)}</object>'
              f'<object id="3" type="model" name="{nombre}"><components><component objectid="1"/><component objectid="2"/></components></object>'
              '</resources><build><item objectid="3" transform="1 0 0 0 1 0 0 0 1 128 128 0"/></build></model>')
    ajustes = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>'
               f'<object id="3"><metadata key="name" value="{nombre}"/><metadata key="extruder" value="1"/>'
               '<part id="1" subtype="normal_part"><metadata key="name" value="base"/><metadata key="extruder" value="1"/></part>'
               '<part id="2" subtype="normal_part"><metadata key="name" value="color"/><metadata key="extruder" value="2"/></part>'
               '</object></config>')
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="text/xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", modelo)
        z.writestr("Metadata/model_settings.config", ajustes)


# ---------- vista previa ----------
def vista(ruta, forma, verde, escala=14):
    minx, miny, maxx, maxy = forma.bounds
    W, H = int((maxx - minx + 8) * escala), int((maxy - miny + 8) * escala)
    img = Image.new("RGB", (W, H), "#e9edf1")
    d = ImageDraw.Draw(img)
    a = lambda x, y: ((x - minx + 4) * escala, (maxy - y + 4) * escala)

    def pinta(g, col, dx=0, dy=0):
        for p in ([g] if g.geom_type == "Polygon" else g.geoms):
            d.polygon([a(x + dx, y + dy) for x, y in p.exterior.coords], fill=col)
            for i in p.interiors:
                d.polygon([a(x + dx, y + dy) for x, y in i.coords], fill="#e9edf1" if col != "#3ddc97" else "#2f3740")

    pinta(forma, "#c5ccd3", .5, -.6)   # sombra
    pinta(forma, "#2f3740")
    pinta(verde, "#3ddc97")
    img.save(ruta)


def main():
    (AQUI / "stl").mkdir(exist_ok=True)
    (AQUI / "3mf").mkdir(exist_ok=True)
    for clave, (lineas, pie) in CHISTES.items():
        forma, verde, base, capa = mallas(lineas, pie)
        assert base.is_watertight and capa.is_watertight, clave
        base.export(AQUI / "stl" / f"llavero-{clave}-base.stl")
        capa.export(AQUI / "stl" / f"llavero-{clave}-color.stl")
        escribir_3mf(AQUI / "3mf" / f"llavero-{clave}.3mf", f"Llavero {clave}", base, capa)
        vista(AQUI / f"vista-{clave}.png", forma, verde)
        x0, y0, x1, y1 = forma.bounds
        print(f"{clave}: {x1 - x0:.1f} × {y1 - y0:.1f} × {ALTO} mm · base {base.volume / 1000:.2f} cm³ · color {capa.volume / 1000:.2f} cm³")


if __name__ == "__main__":
    main()
