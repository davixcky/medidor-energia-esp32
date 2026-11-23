#!/usr/bin/env python3
"""Llaveros compactos, sin texto y de dos colores con forma de pinza SCT-013.

El aro de la llavero pasa por el hueco de la pinza, como el conductor de fase.
Genera, por cada icono: STL de la base, STL del color, un 3MF de dos partes
(Bambu Studio / OrcaSlicer asignan el filamento 1 y 2), una vista previa PNG
y cuatro placas 3MF listas para acomodar en una cama de 256 x 256 mm.

Uso:  pip install trimesh shapely manifold3d pillow qrcode
      python3 stand/llavero/generar_llavero.py
"""
import math
from pathlib import Path
import zipfile

import trimesh
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

AQUI = Path(__file__).resolve().parent

# --- medidas (mm) ---
R_EXT, R_HUECO = 10.0, 4.5          # aro compacto; hueco de 9 mm para la argolla
CUERPO = (7.0, -10.0, 44.0, 10.0)   # 54 mm de ancho total
R_ESQ = 4.0
ALTO, INCRUSTE = 3.2, 0.6           # espesor total y segundo color (3 capas de 0,2)
MARGEN = 1.2

# Cada variante usa solamente un pictograma relacionado con el proyecto.
ICONOS = ("energia", "wifi", "onda", "canales", "pronostico", "seguridad")

# Llavero QR para regalar en el stand: abre la página del proyecto.
URL_QR = "https://davixcky.github.io/medidor-energia-esp32/"

# Los iconos usan base oscura + detalle verde. El QR queda separado
# porque necesita base clara + detalle oscuro. La placa QR lleva seis copias:
# es la pieza pensada para regalar en el stand.
PLACAS = (
    ("placa-01-iconos", ICONOS, 1),
    ("placa-04-qr-x6", ("qr",), 6),
)


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


def trazo(puntos, ancho=1.5):
    return LineString(puntos).buffer(ancho / 2, cap_style="round", join_style="round")


def pictograma(clave):
    """Pictogramas gruesos para que sobrevivan bien a una boquilla de 0,4 mm."""
    if clave == "energia":
        return Polygon([(29, 8), (22, -1), (27, -1), (24, -8),
                        (37, 3), (31, 3), (35, 8)])
    if clave == "wifi":
        centro = (29, -6)
        arcos = []
        for radio in (5, 9):
            puntos = [(centro[0] + radio * math.cos(math.radians(a)),
                       centro[1] + radio * math.sin(math.radians(a)))
                      for a in range(28, 153, 4)]
            arcos.append(trazo(puntos, 1.6))
        return unary_union(arcos + [Point(*centro).buffer(1.6, 32)])
    if clave == "onda":
        puntos = [(18 + i * 0.8, 5.5 * math.sin(i * 0.8 * math.pi / 7)) for i in range(29)]
        return trazo(puntos, 1.8)
    if clave == "canales":
        canal_1 = box(20, -7, 27, 5).buffer(1.2, 16)
        canal_2 = box(32, -3, 39, 7).buffer(1.2, 16)
        return unary_union([canal_1, canal_2])
    if clave == "pronostico":
        curva = trazo([(18, -6), (24, -2), (29, -4), (36, 5)], 1.7)
        punta = Polygon([(36, 5), (31.5, 4.5), (35, 0.5)])
        return unary_union([curva, punta, Point(18, -6).buffer(1.4, 24)])
    if clave == "seguridad":
        exterior = Polygon([(29, 8), (39, 4), (37, -4), (29, -9), (21, -4), (19, 4)])
        interior = Polygon([(29, 5.5), (36, 2.8), (34.8, -2.5), (29, -6), (23.2, -2.5), (22, 2.8)])
        escudo = exterior.difference(interior)
        visto = trazo([(24.5, -0.5), (28, -4), (34.5, 3.5)], 1.7)
        return unary_union([escudo, visto])
    raise ValueError(f"Icono desconocido: {clave}")


def color(clave):
    # núcleo de la pinza: arco con la ranura de apertura arriba
    nucleo = arco(R_HUECO + 1.6, R_HUECO + 2.8, 105, 435)
    verde = unary_union([nucleo, pictograma(clave)])
    seguro = contorno().buffer(-MARGEN)
    return verde.intersection(seguro)


def extruir(geom, z0, z1):
    """Extruye con manifold3d (robusto ante letras con huecos que tocan el borde)."""
    import manifold3d as mf
    import numpy as np
    geoms = [geom] if geom.geom_type == "Polygon" else [g for g in geom.geoms if g.geom_type == "Polygon"]
    anillos = []
    for g in geoms:
        if g.area < 1e-3:
            continue
        g = orient(g)
        anillos.append(np.array(g.exterior.coords[:-1]))
        anillos += [np.array(i.coords[:-1]) for i in g.interiors]
    sec = mf.CrossSection(anillos, mf.FillRule.EvenOdd)
    malla = sec.extrude(z1 - z0).translate((0, 0, z0)).to_mesh()
    m = trimesh.Trimesh(vertices=malla.vert_properties[:, :3], faces=malla.tri_verts, process=True)
    assert m.is_volume, geom.bounds
    return m


def mallas(clave):
    forma, verde = contorno(), color(clave)
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


def escribir_placa_3mf(ruta, nombre, claves, copias, mallas_por_clave):
    """Escribe una placa con objetos de dos partes, ya espaciados para 256 mm."""
    # Seis llaveros compactos en dos filas. El QR también admite 3 x 2.
    posiciones = ([(35, 78), (105, 78), (175, 78), (35, 148), (105, 148), (175, 148)] if copias == 1 else
                  [(43, 69), (112, 69), (181, 69), (43, 157), (112, 157), (181, 157)])
    recursos, objetos_config, items = [], [], []
    id_por_clave = {}
    siguiente_id = 1

    for clave in claves:
        base, capa = mallas_por_clave[clave]
        base_id, color_id, conjunto_id = siguiente_id, siguiente_id + 1, siguiente_id + 2
        siguiente_id += 3
        id_por_clave[clave] = conjunto_id
        etiqueta = "QR" if clave == "qr" else clave
        recursos.extend((
            f'<object id="{base_id}" type="model" name="{etiqueta} base">{malla_xml(base)}</object>',
            f'<object id="{color_id}" type="model" name="{etiqueta} color">{malla_xml(capa)}</object>',
            f'<object id="{conjunto_id}" type="model" name="Llavero {etiqueta}"><components>'
            f'<component objectid="{base_id}"/><component objectid="{color_id}"/>'
            '</components></object>',
        ))
        objetos_config.append(
            f'<object id="{conjunto_id}"><metadata key="name" value="Llavero {etiqueta}"/>'
            '<metadata key="extruder" value="1"/>'
            f'<part id="{base_id}" subtype="normal_part"><metadata key="name" value="base"/>'
            '<metadata key="extruder" value="1"/></part>'
            f'<part id="{color_id}" subtype="normal_part"><metadata key="name" value="color"/>'
            '<metadata key="extruder" value="2"/></part></object>'
        )

    instancias = list(claves) if copias == 1 else [claves[0]] * copias
    assert len(instancias) <= len(posiciones)
    for clave, (x, y) in zip(instancias, posiciones):
        items.append(f'<item objectid="{id_por_clave[clave]}" '
                     f'transform="1 0 0 0 1 0 0 0 1 {x} {y} 0"/>')

    modelo = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<model unit="millimeter" xml:lang="es" '
              'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
              f'<metadata name="Title">{nombre}</metadata><resources>{"".join(recursos)}</resources>'
              f'<build>{"".join(items)}</build></model>')
    ajustes = f'<?xml version="1.0" encoding="UTF-8"?>\n<config>{"".join(objetos_config)}</config>'
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="text/xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", modelo)
        z.writestr("Metadata/model_settings.config", ajustes)


# ---------- vista previa ----------
def vista(ruta, forma, verde, escala=14, claro=False):
    minx, miny, maxx, maxy = forma.bounds
    W, H = int((maxx - minx + 8) * escala), int((maxy - miny + 8) * escala)
    img = Image.new("RGB", (W, H), "#e9edf1")
    d = ImageDraw.Draw(img)
    a = lambda x, y: ((x - minx + 4) * escala, (maxy - y + 4) * escala)

    def pinta(g, col, dx=0, dy=0):
        # cada polígono en su propia máscara, para que sus huecos no borren otras piezas
        for p in ([g] if g.geom_type == "Polygon" else g.geoms):
            capa = Image.new("L", img.size, 0)
            dc = ImageDraw.Draw(capa)
            dc.polygon([a(x + dx, y + dy) for x, y in p.exterior.coords], fill=255)
            for i in p.interiors:
                dc.polygon([a(x + dx, y + dy) for x, y in i.coords], fill=0)
            img.paste(col, mask=capa)

    pinta(forma, "#c5ccd3", .5, -.6)   # sombra
    pinta(forma, "#f4f6f8" if claro else "#2f3740")
    pinta(verde, "#1b2128" if claro else "#3ddc97")
    img.save(ruta)


# ---------- llavero QR ----------
def llavero_qr():
    import qrcode
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, border=0)
    q.add_data(URL_QR)
    q.make(fit=True)
    mat = q.get_matrix()
    n = len(mat)
    lado_qr = 32.0
    m = lado_qr / n                       # tamaño de módulo
    W, H, r = 40.0, 40.0, 4.0             # placa clara compacta, sin texto
    placa = box(-W / 2 + r, -H / 2 + r, W / 2 - r, H / 2 - r).buffer(r, 32)
    oreja = Point(0, H / 2 + 1.5).buffer(6.0, 64)
    forma = unary_union([placa, oreja]).buffer(-1.5, 32).buffer(1.5, 32).difference(Point(0, H / 2 + 2.0).buffer(3.0, 64))
    x0, y0 = -lado_qr / 2, H / 2 - 4.0    # esquina superior izquierda del QR (zona de silencio = borde claro)
    filas = []
    for i, fila in enumerate(mat):
        j = 0
        while j < n:
            if fila[j]:
                k = j
                while k < n and fila[k]:
                    k += 1
                filas.append(box(x0 + j * m, y0 - (i + 1) * m, x0 + k * m, y0 - i * m))
                j = k
            else:
                j += 1
    # una dilatación mínima une los módulos que solo se tocan en una esquina
    oscuro = unary_union(filas).buffer(0.01, join_style=2)
    oscuro = oscuro.intersection(forma.buffer(-MARGEN))
    base = trimesh.boolean.union([extruir(forma, 0, ALTO - INCRUSTE),
                                  extruir(forma.difference(oscuro), ALTO - INCRUSTE - 0.01, ALTO)], engine="manifold")
    capa = trimesh.boolean.union([extruir(oscuro, ALTO - INCRUSTE, ALTO)], engine="manifold")
    return forma, oscuro, base, capa, n, m


def main():
    (AQUI / "stl").mkdir(exist_ok=True)
    (AQUI / "3mf").mkdir(exist_ok=True)
    (AQUI / "placas").mkdir(exist_ok=True)
    mallas_por_clave = {}
    for clave in ICONOS:
        forma, verde, base, capa = mallas(clave)
        assert base.is_watertight and capa.is_watertight, clave
        base.export(AQUI / "stl" / f"llavero-{clave}-base.stl")
        capa.export(AQUI / "stl" / f"llavero-{clave}-color.stl")
        escribir_3mf(AQUI / "3mf" / f"llavero-{clave}.3mf", f"Llavero {clave}", base, capa)
        mallas_por_clave[clave] = (base, capa)
        vista(AQUI / f"vista-{clave}.png", forma, verde)
        x0, y0, x1, y1 = forma.bounds
        print(f"{clave}: {x1 - x0:.1f} × {y1 - y0:.1f} × {ALTO} mm · base {base.volume / 1000:.2f} cm³ · color {capa.volume / 1000:.2f} cm³")
    forma, oscuro, base, capa, n, m = llavero_qr()
    assert base.is_watertight and capa.is_watertight, "qr"
    base.export(AQUI / "stl" / "llavero-qr-claro.stl")
    capa.export(AQUI / "stl" / "llavero-qr-oscuro.stl")
    escribir_3mf(AQUI / "3mf" / "llavero-qr.3mf", "Llavero QR", base, capa)
    mallas_por_clave["qr"] = (base, capa)
    vista(AQUI / "vista-qr.png", forma, oscuro, claro=True)
    x0, y0, x1, y1 = forma.bounds
    print(f"qr: {x1 - x0:.1f} × {y1 - y0:.1f} × {ALTO} mm · {n}×{n} módulos de {m:.2f} mm")

    for nombre, claves, copias in PLACAS:
        escribir_placa_3mf(AQUI / "placas" / f"{nombre}.3mf", nombre, claves, copias, mallas_por_clave)
        cantidad = len(claves) if copias == 1 else copias
        print(f"{nombre}: {cantidad} llaveros")


if __name__ == "__main__":
    main()
