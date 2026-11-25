#!/usr/bin/env python3
"""Modelo E.9 del medidor: terminal LilyGO tactil, entrada 12 V y montaje sin tornillos.

Se ejecuta con FreeCAD en modo consola (ver README.md).  Genera el FCStd, el
STEP, los STL de las piezas impresas, `metadatos-ensamble.json` (lo consume el
video) y `validacion-3d.json`.  Las cotas de piezas compradas salen de
`medidas-componentes.json`; nada de lo marcado allí como conservador o por
medir debe leerse como medida confirmada.
"""
from pathlib import Path
import csv
import json
import math
import re

import FreeCAD as App
import Import
import MeshPart
import Part

V = App.Vector
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HW = ROOT / "hardware/perforadas-modulares"
STL = HERE / "stl"
FIT = HERE / "pruebas-de-ajuste"
MED = json.loads((HERE / "medidas-componentes.json").read_text(encoding="utf-8"))["componentes"]

# ------------------------------------------------------------------ cotas globales
W, D, HB, LID = 280.0, 180.0, 67.0, 3.0      # el cuerpo llega a z=67; tapa y guarda a z=70
H = HB + LID
WALL, FLOOR, RC = 2.5, 3.0, 8.0
Z_PCB = 9.0                                   # cara inferior de las perforadas (separador de 6 mm)
ZT = Z_PCB + 1.6                              # cara superior de las perforadas
PART_Y0, PART_Y1 = 136.0, 140.0               # tabique entre MBT y la zona de red Z1
LID_Y1, GUARD_Y0 = 137.6, 138.4               # junta visible de 0,8 mm sobre el tabique
PIVOT_Y, PIVOT_Z = 0.0, HB                    # arista frontal inferior de la tapa: sobre ella bascula al levantarla
# Tapa suelta con imanes. Trayectoria de servicio: (fracción, giro en grados, avance en Y, elevación en Z).
# Bascula sobre la arista frontal, se levanta, avanza y baja con sus dos lengüetas a los bolsillos de estacionamiento.
LID_PATH = [(0.0, 0.0, 0.0, 0.0), (0.62, 90.0, 0.0, 9.0), (0.80, 90.0, 6.3, 9.0), (1.0, 90.0, 6.3, 0.0)]
# E.9 uses the same clean lid edge as the equalizer. The lid lifts from its rear underside;
# no service tongues project beyond the front face.
TAB_X, TAB_W, TAB_L = (), 14.0, 8.0
FINGER_SCALLOP_X, FINGER_SCALLOP_R = W / 2, 10.0  # recess under the front lid edge
MAG_D, MAG_T = MED["IMAN-NEODIMIO-6x2"]["envolvente"]["diametro"], MED["IMAN-NEODIMIO-6x2"]["envolvente"]["altura"]
MAGNETS = [(10.0, 7.0), (270.0, 7.0), (12.0, 131.5), (268.0, 131.5)]
MAG_MIN_ZMPT = 60.0                           # criterio de diseño: separación mínima imán–transformador del ZMPT101B
HEX_R, HEX_GROOVE, HEX_RIM = 12.5 / 3, 0.6, 0.8        # celdas hexagonales: el dibujo se repite cada 12,5 mm
HEX_AF = math.sqrt(3) * HEX_R
HEX_T = (0.3, 0.5, 1.1)                       # espesor en surco, interior de celda y aro
ROW_Y = 52.0                                  # fila de controles de la tapa

BOARDS = {  # x, y, ancho, fondo, rótulo
    "T1": (214.0, 8.0, 50.0, 40.0, "ALIMENTACIÓN"),
    "T2": (6.0, 77.0, 70.0, 55.0, "CORRIENTE + VBIAS"),
    "T3": (94.0, 62.0, 55.0, 45.0, "TENSIÓN MBT"),
    "T4": (6.0, 8.0, 80.0, 65.0, "CONTROL ESP32S"),
    "T5": (94.0, 8.0, 65.0, 50.0, "INTERFAZ + ALERTAS"),
}

ESP_L, ESP_W, ESP_H = MED["ESP32S-V1.1-USB-C-38P"]["envolvente"]
ESP_ROWS = MED["ESP32S-V1.1-USB-C-38P"]["separacion_centros_hileras"]
LCD_L, LCD_W, LCD_T = MED["LilyGO-T4-S3-AMOLED-2.41"]["envolvente"]
LCD_ACTIVE = MED["LilyGO-T4-S3-AMOLED-2.41"]["area_activa"]
PIEZO_D = MED["GEP0008-piezo-pasivo"]["envolvente"]["diametro"]
PIEZO_H = MED["GEP0008-piezo-pasivo"]["envolvente"]["altura"]
ZMPT_L, ZMPT_W, ZMPT_H = MED["ZMPT101B-SNC0015"]["envolvente"]
FCOB_L, FCOB_W, FCOB_T = MED["BTF-FCOB-WS2811-12V-720L-IP30"]["envolvente_usada"]
FCOB_SEG = MED["BTF-FCOB-WS2811-12V-720L-IP30"]["segmento_corte"]
LM_L, LM_W, LM_H = MED["LM2596-MODULO-BUCK"]["envolvente_reservada"]

COLORS = {
    "body": (.10, .12, .15), "lid": (.20, .22, .25), "guard": (.20, .22, .25), "warning": (1.0, .48, .24),
    "perf": (.70, .56, .34), "pad": (.80, .80, .76), "nylon": (.86, .86, .82),
    "screw": (.30, .31, .33), "metal": (.74, .75, .77), "gold": (.85, .65, .25),
    "ic": (.03, .03, .035), "jst": (.90, .87, .78), "plug": (.97, .96, .93),
    "hdr": (.05, .05, .055), "tb": (.12, .50, .22), "resistor": (.35, .62, .80),
    "lead": (.70, .70, .72), "diode": (.85, .35, .12), "capc": (.80, .55, .18),
    "cape": (.07, .09, .16), "ptc": (.90, .72, .10), "pcb_blue": (.05, .20, .50),
    "pcb_dark": (.04, .05, .06), "trimmer": (.10, .30, .75), "brass": (.80, .62, .25),
    "coil": (.30, .30, .32), "magnet": (.78, .79, .80), "w_power": (.80, .07, .05), "w_analog": (.92, .72, .10),
    "w_digital": (.12, .42, .88), "w_lid": (.62, .66, .72), "w_L": (.04, .04, .04),
    "w_N": (.93, .93, .93), "rubber": (.03, .03, .03), "strip": (.93, .93, .90),
    "seg": (.10, .78, .40), "diffuser": (.90, .92, .92), "glass": (.02, .03, .04),
    "led": (.10, .85, .30), "knob": (.05, .055, .06), "piezo": (.04, .04, .045),
}

OBJECTS = []      # (nombre, forma, material, grupo)
FOOTPRINTS = {}   # tarjeta -> [(ref, x0, y0, x1, y1, permite_voladizo)]
PINS = {}         # (tarjeta, ref) -> vías del conector modelado
CENTER = {}       # (tarjeta, ref) -> (x, y, z_superior) en coordenadas globales
HARNESS = []      # registros de arneses para el informe de radios
HEX_CENTERS = []  # centros de las celdas del difusor


def box(w, d, h, x=0, y=0, z=0):
    return Part.makeBox(w, d, h, V(x, y, z))


def cyl(r, h, x, y, z, axis=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(x, y, z), V(*axis))


def hexprism(af, h, x, y, z, axis="z"):
    r = af / math.sqrt(3)
    pts = [V(r * math.cos(math.radians(60 * i)), r * math.sin(math.radians(60 * i)), 0) for i in range(7)]
    s = Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, h))
    if axis == "x":
        s.rotate(V(0, 0, 0), V(0, 1, 0), 90)
    elif axis == "y":
        s.rotate(V(0, 0, 0), V(1, 0, 0), -90)
    s.translate(V(x, y, z))
    return s


def rbox(w, d, h, x, y, z, r):
    b = box(w, d, h, x, y, z)
    edges = [e for e in b.Edges if abs(e.Vertexes[0].X - e.Vertexes[1].X) < 1e-6
             and abs(e.Vertexes[0].Y - e.Vertexes[1].Y) < 1e-6]
    return b.makeFillet(r, edges)


def comp(shapes):
    return Part.makeCompound(list(shapes))


def fuse(base, others):
    return base.fuse(list(others)).removeSplitter()


def magnet_ribs(x, y, z, h):
    """Cuatro nervios de apriete: retienen un imán de 6 mm sin adhesivo y permiten extraerlo."""
    return [box(.45, .8, h, x + 2.75, y - .4, z), box(.45, .8, h, x - 3.20, y - .4, z),
            box(.8, .45, h, x - .4, y + 2.75, z), box(.8, .45, h, x - .4, y - 3.20, z)]


def add(name, shape, mat, group="interior"):
    OBJECTS.append((name, shape, mat, group))
    return shape


def tube(points, r, t0=None, t1=None):
    """Tubo por B-spline interpolada; devuelve (sólido, radio mínimo de curvatura, longitud)."""
    pts = [V(*p) for p in points]
    bs = Part.BSplineCurve()
    kw = {}
    if t0 is not None:
        kw["InitialTangent"] = V(*t0)
    if t1 is not None:
        kw["FinalTangent"] = V(*t1)
    bs.interpolate(Points=pts, **kw)
    u0, u1 = bs.FirstParameter, bs.LastParameter
    kmax = max(bs.curvature(u0 + (u1 - u0) * i / 200.0) for i in range(201))
    wire = Part.Wire([bs.toShape()])
    profile = Part.Wire([Part.makeCircle(r, pts[0], bs.tangent(u0)[0])])
    solid = wire.makePipeShell([profile], True, True)
    if solid.isNull() or not solid.isValid():
        raise RuntimeError("tubo inválido")
    return solid, (1.0 / kmax if kmax > 1e-9 else float("inf")), bs.length()


def routed(points, r, bend=None):
    """Tubo por tramos rectos y codos circulares; devuelve (sólido, radio mínimo real, longitud)."""
    pts = [V(*p) for p in points]
    bend = bend or 3.0 * 2 * r
    edges, cur, rmin = [], pts[0], float("inf")
    for i in range(1, len(pts) - 1):
        a, b = (pts[i] - pts[i - 1]), (pts[i + 1] - pts[i])
        la, lb = a.Length, b.Length
        a.normalize(); b.normalize()
        ang = a.getAngle(b)
        if ang < 1e-3:
            continue
        t = min(bend * math.tan(ang / 2), .48 * la, .48 * lb)
        rr = t / math.tan(ang / 2)
        rmin = min(rmin, rr)
        p1, p2 = pts[i] - a * t, pts[i] + b * t
        bis = b - a
        bis.normalize()
        center = pts[i] + bis * (rr / math.cos(ang / 2))
        mid = center - bis * rr
        if (p1 - cur).Length > 1e-6:
            edges.append(Part.makeLine(cur, p1))
        edges.append(Part.Arc(p1, mid, p2).toShape())
        cur = p2
    edges.append(Part.makeLine(cur, pts[-1]))
    wire = Part.Wire(edges)
    d0 = pts[1] - pts[0]
    profile = Part.Wire([Part.makeCircle(r, pts[0], d0)])
    solid = wire.makePipeShell([profile], True, True)
    if solid.isNull() or not solid.isValid() or solid.Volume < .5 * math.pi * r * r * wire.Length:
        raise RuntimeError("tubo inválido")
    return solid, rmin, wire.Length


def harness(name, points, r, mat, group="interior", kind="lógico", bend=None):
    solid, rmin, length = routed(points, r, bend)
    add(name, solid, mat, group)
    HARNESS.append({"nombre": name, "tipo": kind, "diametro_mm": round(2 * r, 2),
                    "radio_minimo_mm": round(rmin, 1), "longitud_mm": round(length, 1)})


# ------------------------------------------------------------------ huellas THT
def jst_size(n):
    return 2.5 * (n - 1) + 4.9, 5.75


def part_shapes(kind, n=0, plug=True):
    """Devuelve (ancho, fondo, altura, [(material, forma)]) con origen en la esquina mínima, z=0 sobre la tarjeta."""
    if kind == "R":
        return 12.2, 2.6, 2.8, [("resistor", cyl(1.25, 6.3, 2.95, 1.3, 1.5, (1, 0, 0))),
                                ("lead", comp([cyl(.3, 12.2, 0, 1.3, 1.5, (1, 0, 0)), cyl(.3, 1.5, .3, 1.3, 0), cyl(.3, 1.5, 11.9, 1.3, 0)]))]
    if kind == "D35":
        return 9.6, 2.2, 2.2, [("diode", cyl(.95, 4.0, 2.8, 1.1, 1.2, (1, 0, 0))),
                               ("lead", comp([cyl(.28, 9.6, 0, 1.1, 1.2, (1, 0, 0)), cyl(.28, 1.2, .3, 1.1, 0), cyl(.28, 1.2, 9.3, 1.1, 0)]))]
    if kind == "D41":   # 1N5819 comprado, DO-41
        return 12.2, 2.8, 2.9, [("ic", cyl(1.35, 5.2, 3.5, 1.4, 1.5, (1, 0, 0))),
                                ("lead", comp([cyl(.4, 12.2, 0, 1.4, 1.5, (1, 0, 0)), cyl(.4, 1.5, .4, 1.4, 0), cyl(.4, 1.5, 11.8, 1.4, 0)]))]
    if kind == "D201":
        return 17.5, 5.4, 5.6, [("ic", cyl(2.65, 9.5, 4.0, 2.7, 2.9, (1, 0, 0))),
                                ("lead", comp([cyl(.6, 17.5, 0, 2.7, 2.9, (1, 0, 0)), cyl(.6, 2.9, .6, 2.7, 0), cyl(.6, 2.9, 16.9, 2.7, 0)]))]
    if kind == "CD":
        return 6.0, 2.6, 6.0, [("capc", box(5.4, 2.4, 4.6, .3, .1, 1.4)),
                               ("lead", comp([cyl(.28, 1.6, .8, 1.3, 0), cyl(.28, 1.6, 5.2, 1.3, 0)]))]
    if kind in ("CP5", "CP10"):
        d, h = (5.0, 11.0) if kind == "CP5" else (10.0, 17.0)
        return d, d, h, [("cape", cyl(d / 2, h - .4, d / 2, d / 2, 0)), ("metal", cyl(d / 2 - .6, .4, d / 2, d / 2, h - .4))]
    if kind == "PTC":
        return 12.5, 3.5, 15.0, [("ptc", cyl(6.0, 3.0, 6.25, .25, 9.0, (0, 1, 0))),
                                 ("lead", comp([cyl(.4, 6.0, 3.7, 1.75, 0), cyl(.4, 6.0, 8.8, 1.75, 0)]))]
    if kind == "JST":
        w, d = jst_size(n)
        body = box(w, d, 7.0).cut(box(w - 1.2, d - 1.4, 5.6, .6, .7, 1.4))
        pins = comp([box(.64, .64, 6.2, 2.45 - .32 + 2.5 * i, d / 2 - .32, 0) for i in range(n)])
        out = [("jst", body), ("gold", pins)]
        if plug:
            out.append(("plug", box(w - 1.6, d - 1.8, 8.2, .8, .9, 1.4)))
        return w, d, 9.6 if plug else 7.0, out
    if kind == "HDR":
        w = 2.54 * n
        out = [("hdr", box(w, 2.54, 2.5)), ("gold", comp([box(.64, .64, 8.5, 1.27 - .32 + 2.54 * i, .95, 0) for i in range(n)]))]
        if plug:
            out.append(("hdr", box(w, 2.6, 14.0, 0, -.03, 2.5)))
        return w, 2.54, 16.5 if plug else 8.5, out
    if kind == "TB":   # bornera de 5,08 mm; bocas de cable en la cara -Y local
        w, d, h = 5.08 * n + .6, 8.0, 10.0
        body = box(w, d, h)
        for i in range(n):
            cx = .3 + 2.54 + 5.08 * i
            body = body.cut(box(3.4, 3.0, 3.6, cx - 1.7, -.1, 1.6)).cut(cyl(1.9, 1.2, cx, 4.6, h - 1.0))
        screws = comp([cyl(1.7, .6, .3 + 2.54 + 5.08 * i, 4.6, h - 1.2) for i in range(n)])
        clamps = comp([box(2.8, 2.2, 2.6, .3 + 2.54 + 5.08 * i - 1.4, .8, 2.0) for i in range(n)])
        return w, d, h, [("tb", body), ("metal", comp([screws, clamps]))]
    if kind == "DIP20":
        zs = 4.2   # zócalo DIP-20 comprado: el 74HCT245N queda removible
        sock = box(25.8, 10.1, zs, .1, 0, 0).cut(box(22.0, 4.6, zs + 1, 2.0, 2.75, 1.2))
        body = box(25.4, 6.6, 3.4, .3, 1.75, zs + .5).cut(cyl(1.0, 1.0, .3, 5.05, zs + 3.2))
        pins = comp([box(.5, 1.0, 2.6, 1.3 + 2.54 * i - .25, yy, zs - .2) for i in range(10) for yy in (.75, 8.35)])
        return 26.0, 10.1, zs + 3.9, [("hdr", sock), ("ic", body), ("lead", pins)]
    if kind == "TO92":
        body = cyl(2.3, 4.6, 2.4, 2.1, 2.6).cut(box(4.8, 1.2, 5, 0, -.1, 2.5))
        return 4.8, 3.8, 7.2, [("ic", body), ("lead", comp([cyl(.25, 2.8, 1.13 + 1.27 * i, 2.1, 0) for i in range(3)]))]
    if kind == "LM2596":
        zp = 2.5
        posts = comp([box(2.5, 2.5, zp, x, y, 0) for x in (.4, LM_L - 2.9) for y in (.4, LM_W - 2.9)])
        trim = box(9.5, 4.8, LM_H - zp - 1.6 - .9, 27.0, 1.2, zp + 1.6)
        return LM_L, LM_W, LM_H, [
            ("hdr", posts), ("pcb_blue", box(LM_L, LM_W, 1.6, 0, 0, zp)),
            ("coil", box(12.0, 12.0, 5.2, 12.0, 5.0, zp + 1.6)), ("ic", box(6.0, 6.0, 2.0, 4.0, 7.5, zp + 1.6)),
            ("trimmer", trim), ("brass", cyl(1.15, .9, 28.4, 3.6, LM_H - .9)),
            ("tb", comp([box(7.5, 10.0, 8.0, x, 5.5, zp + 1.6) for x in (0.0, LM_L - 7.5)]))]
    if kind == "ESP":  # USB-C en -X; zócalos hembra 1x19 sobre la tarjeta
        zs, row = 8.5, (ESP_W - ESP_ROWS) / 2
        x0 = 1.0   # el conector USB-C sobresale 1 mm del borde de su PCB
        socks = comp([box(48.26, 2.54, zs, x0 + 4.87, row - 1.27 + k * ESP_ROWS, 0) for k in (0, 1)])
        pins = comp([cyl(.45, .5, x0 + 4.87 + 1.27 + 2.54 * i, row + k * ESP_ROWS, zs + 1.6) for i in range(19) for k in (0, 1)])
        return ESP_L + x0, ESP_W, ESP_H, [
            ("hdr", socks), ("pcb_dark", box(ESP_L, ESP_W, 1.6, x0, 0, zs)), ("gold", pins),
            ("coil", box(6.2, 18.0, .5, x0 + 51.6, 5.0, zs + 1.6)),                      # antena impresa: mantener libre
            ("metal", comp([box(15.8, 17.6, 3.1, x0 + 34.5, 5.2, zs + 1.6),            # blindaje WROOM-32
                            box(7.4, 8.94, 3.2, 0, ESP_W / 2 - 4.47, zs + 1.6)])),      # USB-C
                        ("ic", comp([box(5.0, 5.0, .9, x0 + 12.0, ESP_W / 2 - 2.5, zs + 1.6), box(6.5, 3.5, 1.6, x0 + 20.0, 6.0, zs + 1.6),
                         box(3.2, 4.2, 1.8, x0 + 3.2, 3.6, zs + 1.6), box(3.2, 4.2, 1.8, x0 + 3.2, ESP_W - 7.8, zs + 1.6)]))]
    raise ValueError(kind)


def place(board, ref, kind, lx, ly, rot=0, n=0, plug=True, overhang=False):
    """Coloca una huella; (lx, ly) es la esquina mínima ya rotada, relativa a la tarjeta."""
    bx, by = BOARDS[board][:2]
    w, d, h, shapes = part_shapes(kind, n, plug)
    rw, rd = (w, d) if rot % 180 == 0 else (d, w)
    for mat, s in shapes:
        s = s.copy()
        s.translate(V(-w / 2, -d / 2, 0))
        s.rotate(V(0, 0, 0), V(0, 0, 1), rot)
        s.translate(V(bx + lx + rw / 2, by + ly + rd / 2, ZT))
        add(f"{board}_{ref}_{kind}_{mat}", s, mat)
    FOOTPRINTS.setdefault(board, []).append((ref, lx, ly, lx + rw, ly + rd, overhang))
    CENTER[(board, ref)] = (bx + lx + rw / 2, by + ly + rd / 2, ZT + h)
    if kind in ("JST", "HDR", "TB"):
        PINS[(board, ref)] = n


def perfboard(ref):
    x, y, w, d, _ = BOARDS[ref]
    holes = [(x + 4, y + 4), (x + w - 4, y + 4), (x + 4, y + d - 4), (x + w - 4, y + d - 4)]
    s = box(w, d, 1.6, x, y, Z_PCB)
    for hx, hy in holes:
        s = s.cut(cyl(1.6, 3, hx, hy, Z_PCB - .5))
    add(f"{ref}_Perforada_{int(w)}x{int(d)}", s, "perf")
    nx, ny = int((w - 3) // 2.54) + 1, int((d - 3) // 2.54) + 1
    mx, my = (w - (nx - 1) * 2.54) / 2, (d - (ny - 1) * 2.54) / 2
    pads = []
    for i in range(nx):
        for j in range(ny):
            px, py = x + mx + i * 2.54, y + my + j * 2.54
            if all(math.hypot(px - hx, py - hy) > 3.6 for hx, hy in holes):
                pads.append(cyl(.95, .04, px, py, ZT))
    add(f"{ref}_Donas", comp(pads), "pad")
    add(f"{ref}_Postes_encastre", comp([hexprism(5.5, Z_PCB - FLOOR, hx, hy, FLOOR) for hx, hy in holes]), "nylon")
    add(f"{ref}_Pines_elasticos", comp([cyl(1.35, 3.2, hx, hy, Z_PCB - .2).fuse(cyl(1.65, .8, hx, hy, ZT + .2)) for hx, hy in holes]), "nylon")


def top(board, ref):
    return CENTER[(board, ref)]


def arc(name, a, b, mat, r, kind):
    h = max(5.4 * 2 * r, 14.0)
    zt = max(a[2], b[2]) + h
    harness(name, [a, (a[0], a[1], zt), (b[0], b[1], zt), b], r, mat, kind=kind)


def clips(name, pts, group="lid"):
    """Clips impresos que sujetan el carril de cable a la cara interior de la tapa."""
    add(name, comp([box(4, 4, HB - z, x - 2, y - 2, z) for x, y, z in pts]), "nylon", group)


# ------------------------------------------------------------------ gabinete, tapa y guarda
def outline(z, h):
    return rbox(W, D, h, 0, 0, z, RC)


def lid_pose(f):
    """Giro, avance y elevación de la tapa para la fracción f de la trayectoria de servicio."""
    f = min(max(f, 0.0), 1.0)
    for (f0, *a), (f1, *b) in zip(LID_PATH, LID_PATH[1:]):
        if f <= f1:
            u = (f - f0) / (f1 - f0)
            return tuple(a[k] + (b[k] - a[k]) * u for k in range(3))
    return tuple(LID_PATH[-1][1:])


def lid_point(y, z, f):
    deg, dy, dz = lid_pose(f)
    a = math.radians(deg)
    ry, rz = y - PIVOT_Y, z - PIVOT_Z
    return PIVOT_Y + ry * math.cos(a) - rz * math.sin(a) + dy, PIVOT_Z + ry * math.sin(a) + rz * math.cos(a) + dz


def lid_moved(shape, f):
    deg, dy, dz = lid_pose(f)
    r = shape.copy()
    r.rotate(V(0, PIVOT_Y, PIVOT_Z), V(1, 0, 0), deg)
    r.translate(V(0, dy, dz))
    return r


def prism_yz(pts, x0, w):
    """Extruye en X un perfil dado en (y, z)."""
    return Part.Face(Part.makePolygon([V(x0, y, z) for y, z in pts + pts[:1]])).extrude(V(w, 0, 0))


def frustum(x0, x1, y0, y1, e):
    """Tronco de pirámide de z=HB a z=H; la boca superior es el rectángulo dado y la inferior crece e + LID por lado (45°)."""
    def wire(z, g):
        return Part.makePolygon([V(x0 - g, y0 - g, z), V(x1 + g, y0 - g, z), V(x1 + g, y1 + g, z), V(x0 - g, y1 + g, z), V(x0 - g, y0 - g, z)])
    return Part.makeLoft([wire(HB, e + LID), wire(H, e)], True)


def capsule_wire(x0, x1, y0, y1, z, grow=0.0, steps=12):
    """Closed polygonal wire for a horizontal capsule; sufficient facets for the printed diffuser."""
    xa, xb, ya, yb = x0 - grow, x1 + grow, y0 - grow, y1 + grow
    yc, r = (ya + yb) / 2, (yb - ya) / 2
    cr, cl = xb - r, xa + r
    pts = []
    for i in range(steps + 1):
        a = math.radians(-90 + 180 * i / steps)
        pts.append(V(cr + r * math.cos(a), yc + r * math.sin(a), z))
    for i in range(steps + 1):
        a = math.radians(90 + 180 * i / steps)
        pts.append(V(cl + r * math.cos(a), yc + r * math.sin(a), z))
    return Part.makePolygon(pts + [pts[0]])


def capsule_frustum(x0, x1, y0, y1, e):
    """45-degree rounded-end seat matching the equalizer's integrated light-bar language."""
    return Part.makeLoft([capsule_wire(x0, x1, y0, y1, HB, e + LID),
                          capsule_wire(x0, x1, y0, y1, H, e)], True)


def enclosure():
    shell = outline(0, HB).cut(rbox(W - 2 * WALL, D - 2 * WALL, HB, WALL, WALL, FLOOR, RC - WALL))
    extra = [box(W - 2 * WALL, PART_Y1 - PART_Y0, HB - FLOOR, WALL, PART_Y0, FLOOR)]
    # Cuna integrada para el LM2596: guías laterales, topes y labios elásticos; sin tornillos.
    lm_x, lm_y = 166.0, 18.0
    extra += [box(LM_L + 2.0, 1.8, 3.2, lm_x - 1.0, lm_y - 1.8, FLOOR),
              box(LM_L + 2.0, 1.8, 3.2, lm_x - 1.0, lm_y + LM_W, FLOOR),
              box(1.8, LM_W + 3.6, 3.2, lm_x - 1.8, lm_y - 1.8, FLOOR),
              box(1.8, LM_W + 3.6, 3.2, lm_x + LM_L, lm_y - 1.8, FLOOR),
              box(2.0, 5.0, 1.2, lm_x - 1.8, lm_y + 8.0, FLOOR + 3.0),
              box(2.0, 5.0, 1.2, lm_x + LM_L - .2, lm_y + 8.0, FLOOR + 3.0)]
    # Cuatro postes para la guarda de red.
    guard_posts = [(7.0, 144.5), (273.0, 144.5), (8.0, 172.0), (272.0, 172.0)]
    # Cartelas de los imanes de cierre: dos en la pared frontal y dos en el tabique, por encima de las tarjetas.
    for x, y in MAGNETS:
        prof = [(WALL, HB), (11.5, HB), (11.5, HB - 7), (WALL, HB - 16)] if y < 60 else [(PART_Y0, HB), (127.0, HB), (127.0, HB - 7), (PART_Y0, HB - 16)]
        extra.append(prism_yz(prof, x - 4.5, 9.0))
    # Bolsillos de estacionamiento: reciben las lengüetas de la tapa cuando queda de pie para servicio.
    for x in TAB_X:
        extra.append(prism_yz([(WALL, HB), (8.5, HB), (8.5, HB - 11), (WALL, HB - 17)], x - 1.0, TAB_W + 2.0))
    for x, y in guard_posts:
        # 4,7 mm solapa 0,2 mm con las paredes en los postes delanteros; una tangencia exacta
        # producía aristas no-manifold en el STL aunque el BREP fuese válido.
        extra.append(cyl(4.7, HB - FLOOR, x, y, FLOOR))
        extra.append(cyl(1.35, 2.0, x, y, HB).fuse(cyl(2.15, .8, x, y, HB + 1.2)))
    # Ménsulas con brida para el lado fijo de los tres puentes de arnés.
    for _, x, y, _, r, _, zb in BRIDGES:
        zt = zb - r
        extra.append(box(8, y + 3.5 - WALL, 2.5, x - 4, WALL, zt - 2.5))
        g = Part.Face(Part.makePolygon([V(0, WALL, zt - 2.5), V(0, WALL + 10, zt - 2.5), V(0, WALL, zt - 12.5), V(0, WALL, zt - 2.5)])).extrude(V(3, 0, 0))
        g.translate(V(x - 1.5, 0, 0))
        extra.append(g)
    # Zona de red: pedestal de J4, sillas del portafusible y cuna del ZMPT101B.
    extra.append(box(22, 16, 4, 222, 148, FLOOR))
    for x in (156.0, 180.0):
        extra.append(box(4, 14, 4.4, x, 153, FLOOR))
    for x in (ZMPT_X0 - 2, ZMPT_X0 + ZMPT_L - 1.2):
        extra.append(box(3.2, ZMPT_W + 2, Z_PCB - FLOOR, x, 147, FLOOR))
    for x in (ZMPT_X0 - 2, ZMPT_X0 + ZMPT_L + .5):
        extra.append(box(1.5, 6, ZT + 1.6 - FLOOR, x, 148.0, FLOOR))
    extra.append(box(2.5, 6, 1.6, ZMPT_X0 - 2, 148.0, ZT))
    extra.append(box(2.5, 6, 1.6, ZMPT_X0 + ZMPT_L - .5, 148.0, ZT))
    body = fuse(shell, extra)
    cuts = [cyl(MAG_D / 2 + .1, MAG_T + .2, x, y, HB - MAG_T - .2) for x, y in MAGNETS]
    cuts += [box(TAB_W + .6, LID + .4, TAB_L + 1.5, x - .3, 3.1, HB - TAB_L - .5) for x in TAB_X]
    # Smooth fingertip scallop in the front wall. The circle is centred above
    # the wall edge, leaving a shallow 19 mm-wide recess beneath the intact lid.
    # It is printable as part of the body and adds no loose part or fastener.
    cuts.append(cyl(FINGER_SCALLOP_R, WALL + 2.0, FINGER_SCALLOP_X, -1.0,
                    HB + 3.0, (0, 1, 0)))
    usb_y = BOARDS["T4"][1] + 28.0 + ESP_W / 2
    usb_z = ZT + 8.5 + 1.6 + 1.6
    # The ESP32 USB-C remains accessible with the magnetic lid removed. A direct wall tunnel
    # was eliminated because the board socket sits behind the wall and cannot form a gap-free panel port.
    for y in (95.0, 117.0):
        cuts.append(cyl(3.1, WALL + 2, -1, y, 38.0, (1, 0, 0)))                              # jacks SCT de 3,5 mm
    cuts.append(cyl(4.1, WALL + 2, W - WALL - 1, 36.0, 40.0, (1, 0, 0)))                    # jack DC 5,5 x 2,5
    cuts.append(cyl(6.25, WALL + 2, 258.0, D - WALL - 1, 30.0, (0, 1, 0)))                  # prensaestopa PG7
    cuts.append(cyl(4.0, PART_Y1 - PART_Y0 + 2, GROMMET[0], PART_Y0 - 1, GROMMET[1], (0, 1, 0)))       # pasamuros MBT del ZMPT
    body = body.cut(cuts)
    body = fuse(body, [r for x, y in MAGNETS for r in magnet_ribs(x, y, HB - MAG_T - .2, MAG_T + .2)])
    add("Gabinete_E7", body, "body", "body")
    add("Imanes_gabinete_6x2", comp([cyl(MAG_D / 2, MAG_T, x, y, HB - MAG_T) for x, y in MAGNETS]), "magnet", "body")
    add("Patas_goma", comp([cyl(7, 3, x, y, -3) for x in (20, W - 20) for y in (20, D - 20)]), "rubber", "body")
    return {"usb": (0.0, usb_y, usb_z), "guard_posts": guard_posts}


LCD_X0, LCD_Y0 = 111.0, ROW_Y - LCD_W / 2
LCD_C = (LCD_X0 + LCD_L / 2, ROW_Y)
LED_X, PIEZO_X = 188.0, 236.0
FCOB_X0, FCOB_Y0 = 40.0, 100.0
FCOB_YC = FCOB_Y0 + FCOB_W / 2
WIN = (FCOB_X0, FCOB_X0 + FCOB_L, FCOB_YC - HEX_AF, FCOB_YC + HEX_AF)   # ventana de luz: 200 x 14,4 mm, dos celdas de alto
BRIDGES = [  # nombre, x, y de carril, sentido de la coca (+1/-1 en X), radio del mazo, vías, z del anclaje fijo
    ("LCD", 58.0, 24.0, +1, 1.1, 2, 46.0),
    ("panel_T4", 44.0, 17.5, -1, 1.1, 2, 46.0),
    ("panel_T5", 96.0, 12.0, -1, 1.5, 5, 40.0),
]
LANE_Z = 62.0
ZMPT_X0, ZMPT_Y0 = 80.0, 148.0
GROMMET = (ZMPT_X0 + 1.87, 43.0)   # x, z del pasamuros MBT en el tabique


def lid(info):
    slab = box(W, LID_Y1, LID, 0, 0, HB).common(outline(HB, LID))
    plus, cuts = [], []
    # LilyGO T4-S3 horizontal: vidrio al ras, área activa táctil y cuatro setas de encastre.
    cx, cy = LCD_C
    cuts += [rbox(LCD_ACTIVE[0] + .4, LCD_ACTIVE[1] + .4, LID + 1,
                  cx - LCD_ACTIVE[0] / 2 - .2, cy - LCD_ACTIVE[1] / 2 - .2, HB, 3.0),
             rbox(LCD_L + .5, LCD_W + .5, 2.05,
                  cx - LCD_L / 2 - .25, cy - LCD_W / 2 - .25, H - 2.05, 4.25)]
    lcd_boss = [(x, y) for x in (cx - LCD_L / 2 - 4.0, cx + LCD_L / 2 + 4.0) for y in (LCD_Y0 + 4.0, LCD_Y0 + LCD_W - 4.0)]
    plus += [cyl(1.35, 4.2, x, y, HB - 4.2).fuse(cyl(2.25, 1.0, x, y, HB - 5.2)) for x, y in lcd_boss]
    # Toda interacción humana es táctil; solo permanecen un LED de estado y el piezo.
    cuts += [cyl(2.55, LID + 12, LED_X, ROW_Y, HB - 9)]
    plus.append(cyl(4.5, 5.0, LED_X, ROW_Y, HB - 5.0))
    # Narrow parallel slots reuse the equalizer's ventilation language instead of a round hole cluster.
    for ix in range(-5, 6):
        sx = PIEZO_X + ix * 3.8
        cuts.append(box(2.2, 21.8, LID + 2, sx - 1.1, ROW_Y - 10.9, HB - 1)
                    .fuse(cyl(1.1, LID + 2, sx, ROW_Y - 10.9, HB - 1))
                    .fuse(cyl(1.1, LID + 2, sx, ROW_Y + 10.9, HB - 1)))
    cup = cyl(PIEZO_D / 2 + 2.3, PIEZO_H, PIEZO_X, ROW_Y, HB - PIEZO_H).cut(cyl(PIEZO_D / 2 + .3, PIEZO_H + 1, PIEZO_X, ROW_Y, HB - PIEZO_H - .5))
    cup = cup.cut(box(8, 6, 7, PIEZO_X - 4, ROW_Y - PIEZO_D / 2 - 4, HB - PIEZO_H - .5))     # salida de cables
    plus.append(cup)
    ears = [(PIEZO_X + 27.5 * math.cos(math.radians(a)), ROW_Y + 27.5 * math.sin(math.radians(a))) for a in (90, 210, 330)]
    plus += [cyl(1.45, PIEZO_H, x, y, HB - PIEZO_H).fuse(cyl(2.5, 1.0, x, y, HB - PIEZO_H - 1.0)) for x, y in ears]
    # FCOB: ventana con asiento a 45° para el difusor y torretas del soporte.
    cuts.append(capsule_frustum(*WIN, 0))
    fcob_boss = [(FCOB_X0 - 7.5, FCOB_YC + 1), (FCOB_X0 + FCOB_L + 7.5, FCOB_YC + 1)]
    plus += [cyl(1.45, 8.0, x, y, HB - 8.0).fuse(cyl(2.5, 1.0, x, y, HB - 9.0)) for x, y in fcob_boss]
    # Sillas de brida para el lado móvil de los puentes de arnés.
    plus += [box(8, 6.4, HB - LANE_Z - r, x - 4, y - 3.2, LANE_Z + r) for _, x, y, _, r, _, _ in BRIDGES]
    # Lengüetas frontales: uñeros con la tapa cerrada y apoyo en los bolsillos con la tapa de pie.
    plus += [box(TAB_W, TAB_L, LID, x, -TAB_L, HB) for x in TAB_X]
    # Topes de centrado contra las cuatro caras interiores (la tapa no lleva tornillos ni bisagra).
    plus += [box(12, 2.0, 3.0, x, WALL + .2, HB - 3.0) for x in (120.0, 150.0)]
    plus += [box(12, 2.0, 3.0, x, PART_Y0 - 2.4, HB - 3.0) for x in (40.0, 228.0)]
    plus += [box(2.0, 12, 3.0, x, 60.0, HB - 3.0) for x in (WALL + .2, W - WALL - 2.2)]
    lid_s = fuse(slab, plus)
    cuts += [cyl(MAG_D / 2 + .1, MAG_T + .2, x, y, HB - .01) for x, y in MAGNETS]      # ciegos: quedan 0,8 mm de piel
    lid_s = lid_s.cut(cuts)
    lid_s = fuse(lid_s, [r for x, y in MAGNETS for r in magnet_ribs(x, y, HB - .01, MAG_T + .2)])
    add("Tapa_E7", lid_s, "lid", "lid")
    add("Imanes_tapa_6x2", comp([cyl(MAG_D / 2, MAG_T, x, y, HB) for x, y in MAGNETS]), "magnet", "lid")
    return {"lcd_boss": lcd_boss, "ears": ears, "fcob_boss": fcob_boss}


def guard(info):
    slab = box(W, D - GUARD_Y0, LID, 0, GUARD_Y0, HB).common(outline(HB, LID))
    skirt = box(W - 2 * WALL - 1, D - WALL - PART_Y1 - 1, 6, WALL + .5, PART_Y1 + .5, HB - 6)
    skirt = skirt.cut(box(W - 2 * WALL - 5, D - WALL - PART_Y1 - 5, 7, WALL + 2.5, PART_Y1 + 2.5, HB - 6.5))
    # El radio 5,2 atraviesa el borde del faldón. Con 5,0 era tangente y el STL quedaba no-manifold.
    skirt = skirt.cut(comp([cyl(5.2, 8, x, y, HB - 7) for x, y in info["guard_posts"]]))
    # Triángulo de advertencia en relieve (0,6 mm).
    tri = Part.Face(Part.makePolygon([V(26, 149, H), V(56, 149, H), V(41, 174, H), V(26, 149, H)])).extrude(V(0, 0, .6))
    tri = tri.cut(Part.Face(Part.makePolygon([V(31, 152, H), V(51, 152, H), V(41, 168.5, H), V(31, 152, H)])).extrude(V(0, 0, 1)))
    mark = [tri, box(2.2, 7, .6, 39.9, 157.5, H), cyl(1.2, .6, 41, 155, H)]
    # Cuatro alojamientos ciegos encajan sobre pines elásticos del cuerpo. La piel superior
    # permanece intacta: no hay cabezas visibles ni acceso casual a la zona de red.
    sockets = [cyl(2.25, 2.45, x, y, HB - .05) for x, y in info["guard_posts"]]
    # The warning is embossed into the same printable guard. The separate coincident overlay
    # only assigns the orange render/AMS paint cue; assembly still uses one solid and no glue.
    g = fuse(slab, [skirt] + mark).cut(sockets)
    add("Guarda_120V_E7", g, "guard", "guard")
    add("Advertencia_120V_color_render", comp(mark), "warning", "render")


# ------------------------------------------------------------------ tarjetas
def boards():
    for ref in BOARDS:
        perfboard(ref)
    # Buck separado de las perforadas, encajado en la cuna integrada del cuerpo.
    lm_x, lm_y, lm_z = 166.0, 18.0, FLOOR + 2.0
    _, _, _, lm_shapes = part_shapes("LM2596")
    for mat, s in lm_shapes:
        q = s.copy()
        q.translate(V(lm_x, lm_y, lm_z))
        add(f"U4_LM2596_{mat}", q, mat)
    # T1 — entrada protegida de 12 V, buck LM2596 a 5 V y estrella de alimentación.
    place("T1", "J1", "TB", 41.0, 7.5, rot=90, n=2)
    place("T1", "D1", "D41", 8.0, 2.6)
    place("T1", "F2", "PTC", 24.0, 2.2)
    place("T1", "C1", "CP10", 9.0, 7.5)
    place("T1", "C17", "CP10", 21.0, 7.5)
    place("T1", "C2", "CD", 33.0, 9.0)
    place("T1", "C_PWR3", "JST", .6, 7.0, rot=90, n=2)
    place("T1", "C_PWR4", "JST", .6, 15.0, rot=90, n=2)
    place("T1", "C_PWR5", "JST", .6, 23.0, rot=90, n=3)
    # Removable four-wire link to the separately cradled buck module. BUCK_IN
    # carries protected 12 V to the LM2596; BUCK_OUT returns regulated 5 V to
    # the distribution traces on T1. These connectors must be added to KiCad.
    place("T1", "C_BUCK_IN", "JST", 23.5, 25.0, n=2)
    place("T1", "C_BUCK_OUT", "JST", 34.5, 25.0, n=2)
    # T2 — dos canales SCT y VBIAS.  R1/R2 van soldadas en los jacks de panel.
    place("T2", "C_ADC_I", "JST", 50.0, 2.0, n=4)
    place("T2", "J2", "JST", 18.0, 14.0, rot=90, n=2)
    place("T2", "J3", "JST", 18.0, 36.0, rot=90, n=2)
    for k, y in ((0, 14.5), (1, 36.5)):
        place("T2", f"R{5 + k}", "R", 26.0, y + 2.0)
        place("T2", f"C{5 + k}", "CD", 40.0, y + 2.0)
        place("T2", f"D{2 + 2 * k}", "D35", 48.0, y)
        place("T2", f"D{3 + 2 * k}", "D35", 48.0, y + 4.0)
    place("T2", "R3", "R", 26.0, 25.0)
    place("T2", "R4", "R", 26.0, 29.5)
    place("T2", "C7", "CP5", 42.0, 25.0)
    place("T2", "C8", "CD", 50.0, 26.5)
    # T3 — acondicionamiento de tensión; solo el lado MBT del ZMPT.
    place("T3", "J5", "TB", 30.0, 34.0, rot=180, n=3)
    place("T3", "C_PWR3", "JST", 47.0, 12.0, rot=90, n=2)
    place("T3", "C_ADC_V", "JST", 2.5, 8.0, rot=90, n=3)
    place("T3", "R7", "R", 14.0, 24.0)
    place("T3", "R8", "R", 14.0, 29.0)
    place("T3", "C9", "CD", 16.0, 16.0)
    place("T3", "D6", "D35", 26.0, 12.0)
    place("T3", "D7", "D35", 26.0, 16.5)
    # T4 — ESP32S V1.1 USB-C sobre zócalos; USB-C hacia la pared izquierda.
    place("T4", "U1", "ESP", -1.0, 28.0, overhang=True)
    place("T4", "C_LILY", "JST", 22.0, 14.5, n=2)
    place("T4", "C_LED", "JST", 52.0, 8.0, n=2)
    place("T4", "R11", "R", 8.0, 19.5)
    place("T4", "C_PWR4", "JST", 56.0, 58.5, n=2)
    place("T4", "C_UI_D", "JST", 70.5, 19.0, rot=90, n=3)
    place("T4", "C_ADC_V", "JST", 70.5, 47.5, rot=90, n=3)
    place("T4", "C_ADC_I", "JST", 40.0, 58.5, n=4)
    # T5 — 74HCT245N, salida FCOB de 12 V y driver del piezo; interfaz solo tactil.
    place("T5", "C_BZ", "JST", 27.0, 2.0, n=2)
    place("T5", "C_PIX", "JST", 38.0, 2.0, n=3)
    place("T5", "C16", "CP10", 48.2, 8.5)
    place("T5", "C_PWR5", "JST", 56.5, 24.0, rot=90, n=3)
    place("T5", "C_UI_D", "JST", 2.5, 10.0, rot=90, n=3)
    place("T5", "U3", "DIP20", 14.0, 12.0)
    place("T5", "C14", "CD", 41.5, 13.0)
    place("T5", "R16", "R", 14.0, 24.0)
    place("T5", "R17", "R", 28.0, 24.0)
    place("T5", "R23", "R", 42.0, 24.0)
    place("T5", "R18", "R", 34.0, 31.0)
    place("T5", "Q1", "TO92", 38.0, 36.0)


OFFBOARD = {  # referencias del esquemático cuya pieza física no está sobre la tarjeta
    "T1": {"U4": "LM2596 en cuna impresa integrada al cuerpo; sustituye al MT3608 histórico"},
    "T2": {"R1": "soldada en el jack de panel J2", "R2": "soldada en el jack de panel J3"},
}

# Deliberate E.9 additions already present in the mechanical proposal but still
# blocked on the matching KiCad revision. They remain visible in validation as
# planned differences instead of being silently treated as schematic matches.
PLANNED_EXTRA = {}


def base_harnesses():
    # Señales entre tarjetas vecinas: arcos cortos sobre conectores verticales.
    arc("C_UI_D_T4_T5", top("T4", "C_UI_D"), top("T5", "C_UI_D"), "w_digital", 1.3, "digital")
    arc("C_ADC_I_T4_T2", top("T4", "C_ADC_I"), top("T2", "C_ADC_I"), "w_analog", 1.5, "analógico")
    arc("C_ADC_V_T4_T3", top("T4", "C_ADC_V"), top("T3", "C_ADC_V"), "w_analog", 1.3, "analógico")
    # Alimentación en estrella desde T1: un par dedicado por tarjeta, por el piso y corredores libres.
    zf, zh = FLOOR + 2.5, 37.5
    a, b = top("T1", "C_PWR5"), top("T5", "C_PWR5")
    harness("C_PWR5_T1_T5", [a, (a[0], a[1], zh), (b[0], b[1], zh), b], 1.5, "w_power", kind="potencia MBT")
    a, b = top("T1", "C_PWR3"), top("T3", "C_PWR3")
    harness("C_PWR3_T1_T3", [a, (a[0], a[1], zh), (199, a[1], zh), (199, a[1], zf), (199, b[1], zf), (162.5, b[1], zf), (162.5, b[1], zh), (b[0], b[1], zh), b],
            1.3, "w_power", kind="potencia MBT")
    a, b = top("T1", "C_PWR4"), top("T4", "C_PWR4")
    harness("C_PWR4_T1_T4", [a, (a[0], a[1], zh), (193, a[1], zh), (193, a[1], zf), (193, 60, zf), (90, 60, zf), (90, 60, 44), (b[0], b[1], 44), b],
            1.3, "w_power", kind="potencia MBT")
    # Entrada 12 V por jack de chasis CON-156A (5,5 x 2,5 mm) hacia J1.
    add("Jack_DC_CON156A_cuerpo_interior", cyl(5.0, 12.5, W - WALL - 12.5, 36, 40, (1, 0, 0)), "ic")
    add("Jack_DC_CON156A_anillo_panel", Part.makeTorus(5.35, .75, V(W - .55, 36, 40), V(1, 0, 0)), "metal")
    add("Jack_DC_CON156A_boca_5p5x2p5", cyl(4.8, 3.2, W, 36, 40, (1, 0, 0)).cut(
        cyl(2.55, 3.4, W - .1, 36, 40, (1, 0, 0))), "ic")
    add("Jack_DC_terminales", comp([box(2.5, .6, 3, W - WALL - 15, 36 + dy - .3, 38.5) for dy in (-1.9, 1.9)]), "metal")
    jx, jy, _ = top("T1", "J1")
    for name, mat, dy, y_in in (("pos", "w_power", -1.9, jy - 2.54), ("gnd", "w_L", 1.9, jy + 2.54)):
        # Keep the short red/black pair visible and serviceable above T1 instead of
        # hiding it behind the wall and beneath the perfboard. It starts on the two
        # rear solder lugs and terminates at the protected 12 V input J1.
        harness(f"Entrada_12V_{name}", [(W - WALL - 14, 36 + dy, 39.0),
                (W - WALL - 14, 36 + dy, 49.0), (275.0, 36 + dy, 49.0),
                (275.0, y_in, 49.0), (jx + 3.0, y_in, 49.0),
                (jx + 3.0, y_in, ZT + 3.4)],
                .9, mat, kind="potencia MBT")
    # Complete the power-conversion loop that was previously absent from the
    # assembly model: protected 12 V leaves T1 for the LM2596 and regulated
    # 5 V returns to T1 before the star-distribution connectors.
    lm_yc = 18.0 + 10.5
    lm_zterm = FLOOR + 2.0 + 2.5 + 1.6 + 8.0
    for ref, side_x, prefix in (("C_BUCK_IN", 166.0 + 3.75, "Buck_12V_IN"),
                                ("C_BUCK_OUT", 166.0 + LM_L - 3.75, "Buck_5V_OUT")):
        cx, cy, cz = top("T1", ref)
        for suffix, mat, off in (("pos", "w_power", -2.0), ("gnd", "w_L", 2.0)):
            arc(f"{prefix}_{suffix}", (cx, cy + off, cz),
                (side_x, lm_yc + off, lm_zterm), mat, .9, "potencia MBT")
    # Jacks SCT de panel con el burden soldado directamente en sus terminales.
    for y, ref, rr in ((95.0, "J2", "R1"), (117.0, "J3", "R2")):
        add(f"Jack_SCT_{ref}_cuerpo_interior", cyl(4.0, 13.5, WALL, y, 38, (1, 0, 0)), "ic")
        add(f"Jack_SCT_{ref}_anillo_panel", Part.makeTorus(4.35, .7, V(-.55, y, 38), V(1, 0, 0)), "metal")
        add(f"Jack_SCT_{ref}_boca_3p5mm", cyl(3.8, 3.5, -4.2, y, 38, (1, 0, 0)).cut(
            cyl(1.85, 3.7, -4.3, y, 38, (1, 0, 0))), "ic")
        add(f"Jack_SCT_{ref}_terminales", comp([box(6.5, .5, 2.2, WALL + 13.5, y + dy, 36.9) for dy in (-3.4, 2.9)]), "metal")
        add(f"T2_{rr}_burden_en_jack", cyl(1.25, 6.3, 22.0, y - 3.15, 38, (0, 1, 0)), "resistor")
        add(f"T2_{rr}_terminales", cyl(.3, 7.0, 22.0, y - 3.5, 38, (0, 1, 0)), "lead")
        b = top("T2", ref)
        harness(f"Par_SCT_{ref}", [(22.0, y, 37.5), (22.0, y, 31.0), (b[0], b[1], 26.5), b], 1.2, "w_analog", kind="analógico")


def bridge_points(pl, pb, s, length, n=20):
    """Coca en U entre el anclaje fijo pb y el móvil pl; misma fórmula que usa el video."""
    c = math.dist(pl, pb)
    rad = c / 2
    run = (length - math.pi * rad) / 2
    u = [(pl[k] - pb[k]) / c for k in range(3)]
    mid = [(pl[k] + pb[k]) / 2 for k in range(3)]
    pts = [tuple(pb)]
    for i in range(n + 1):
        f = math.pi * i / n
        pts.append(tuple(mid[k] + (s * (run + rad * math.sin(f)) if k == 0 else 0) - rad * math.cos(f) * u[k] for k in range(3)))
    pts.append(tuple(pl))
    return pts


def polylen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def hex_diffuser():
    """Difusor impreso tipo «3D hex»: cara exterior lisa y relieve de celdas hacia la FCOB.

    Piel de 0,3 mm, interior de celda de 0,5 mm y aro de 1,1 mm; marco a 45° que asienta en la tapa.
    Devuelve el sólido y los centros de celda.
    """
    x0, x1, y0, y1 = WIN
    t_s, t_c, t_r = HEX_T
    shell = capsule_frustum(*WIN, 0).cut(capsule_frustum(*WIN, -1.0).common(
        box(x1 - x0 + 20, y1 - y0 + 20, H - t_r - HB, x0 - 10, y0 - 10, HB)))
    cells, centers = [], []
    for i in range(int(round((x1 - x0) / (1.5 * HEX_R))) + 1):
        cx = x0 + 1.5 * HEX_R * i
        for j in range(-2, 3):
            cy = FCOB_YC + HEX_AF * (j + (.5 if i % 2 else 0))
            if abs(cy - FCOB_YC) > HEX_AF + .01:
                continue
            centers.append((round(cx, 4), round(cy, 4)))
            cell = hexprism(HEX_AF - HEX_GROOVE, t_r - t_s, cx, cy, H - t_r)
            cells.append(cell.cut(hexprism(HEX_AF - HEX_GROOVE - 2 * HEX_RIM, t_r - t_c, cx, cy, H - t_r - .01)))
    zone = rbox(x1 - x0, y1 - y0, t_r - t_s, x0, y0, H - t_r, (y1 - y0) / 2 - .05)
    return shell.cut(zone.cut(cells)).removeSplitter(), centers


def lid_parts(feat):
    cx, cy = LCD_C
    glass_z = H - 2.0
    pcb_top = glass_z - .8
    zb = pcb_top
    add("LilyGO_T4S3_AMOLED_vidrio_56x44", rbox(56, 44, 2.0, cx - 28, cy - 22, glass_z, 4.0), "glass", "lid")
    add("LilyGO_T4S3_AMOLED_panel_y_adhesivo", rbox(LCD_ACTIVE[0], LCD_ACTIVE[1], .8,
        cx - LCD_ACTIVE[0] / 2, cy - LCD_ACTIVE[1] / 2, pcb_top, 3.0), "ic", "lid")
    add("LilyGO_T4S3_PCB_51p56x38p72", box(51.56, 38.72, 1.6, cx - 25.78, cy - 19.36, zb - 1.6), "pcb_dark", "lid")
    add("LilyGO_VBUS_GND_2vias", box(5.08, 2.54, 8.5, cx - 2.54, LCD_Y0 + LCD_W - 2.54, zb - 10.1), "hdr", "lid")
    # Placa trasera abierta con cuatro ojos de cerradura. Baja sobre las cabezas impresas y se
    # desliza 4 mm: retiene las esquinas sin tornillos, adhesivo ni carga sobre los conectores.
    pz = zb - 4.0
    frame = [box(6, 50, 2.0, cx - 32, cy - 25, pz), box(6, 50, 2.0, cx + 26, cy - 25, pz),
             box(52, 3, 2.0, cx - 26, cy - 25, pz), box(52, 3, 2.0, cx - 26, cy + 22, pz)]
    # Los apoyos solapan 0,1 mm con marco y largueros: evita cinco shells apenas tangentes en el STL.
    frame += [box(6.2, 4, 2.1, x, y, zb - 2.1)
              for x in (cx - 26.1, cx + 19.9) for y in (cy - 19.36, cy + 15.36)]
    backplate = fuse(frame[0], frame[1:])
    keyholes = []
    for x, y in feat["lcd_boss"]:
        keyholes += [cyl(2.35, 3.0, x, y + 4.0, pz - .5), box(2.9, 4.1, 3.0, x - 1.45, y, pz - .5)]
    backplate = backplate.cut(keyholes).removeSplitter()
    add("Placa_trasera_desmontable_LCD", backplate, "lid", "lid")
    # LED D8 verde de 5 mm en su manguito impreso.
    led = cyl(2.5, 6.1, LED_X, ROW_Y, HB - 3.6).fuse(Part.makeSphere(2.5, V(LED_X, ROW_Y, HB + 2.5))).fuse(cyl(2.9, 1.0, LED_X, ROW_Y, HB - 6.0))
    led = led.fuse(cyl(2.5, 1.5, LED_X, ROW_Y, HB - 5.0))
    add("D8_LED_verde_5mm_panel", led, "led", "lid")
    add("D8_LED_terminales", comp([cyl(.3, 5.0, LED_X + dx, ROW_Y, HB - 11.0) for dx in (-1.27, 1.27)]), "lead", "lid")
    # Piezo GEP0008 dentro de su copa, con aro de retención por giro.
    add("BZ1_piezo_pasivo_44x14", cyl(PIEZO_D / 2, PIEZO_H, PIEZO_X, ROW_Y, HB - PIEZO_H), "piezo", "lid")
    ring = cyl(PIEZO_D / 2 + 2.3, 2.0, PIEZO_X, ROW_Y, HB - PIEZO_H - 2.0).cut(cyl(PIEZO_D / 2 - 5, 3, PIEZO_X, ROW_Y, HB - PIEZO_H - 2.5))
    arms = []
    for a in (90, 210, 330):
        arm = box(11.0, 7.0, 2.0, PIEZO_D / 2, -3.5, HB - PIEZO_H - 2.0)
        arm.rotate(V(0, 0, 0), V(0, 0, 1), a)
        arm.translate(V(PIEZO_X, ROW_Y, 0))
        arms.append(arm)
    ring = fuse(ring, arms)
    ring = ring.cut([cyl(2.6, 3, x, y, HB - PIEZO_H - 2.5) for x, y in feat["ears"]])
    add("Aro_reten_piezo_bayoneta", ring, "lid", "lid")
    # FCOB de 200 mm en cuatro segmentos lógicos de 50 mm, sobre soporte en U que además retiene el difusor.
    zt = HB - 10.0
    tray = [box(FCOB_L + 22, 2 * HEX_AF + 8.6, 2.0, FCOB_X0 - 11, FCOB_YC - HEX_AF - 4.3, zt),
            box(FCOB_L + 6, 1.7, 8.0, FCOB_X0 - 3, FCOB_YC - HEX_AF - 3.7, zt + 2.0), box(FCOB_L + 6, 1.7, 8.0, FCOB_X0 - 3, FCOB_YC + HEX_AF + 2.0, zt + 2.0)]
    add("Soporte_FCOB", fuse(tray[0], tray[1:]).cut([cyl(2.6, 4, x, y, zt - 1) for x, y in feat["fcob_boss"]]), "lid", "lid")
    add("BTF_FCOB_WS2811_12V_200mm", box(FCOB_L, FCOB_W, FCOB_T - .6, FCOB_X0, FCOB_Y0, zt + 2.0), "strip", "lid")
    for i in range(4):
        add(f"FCOB_segmento_{i + 1}_50mm", box(FCOB_SEG - 1.0, FCOB_W - 2.0, .6, FCOB_X0 + .5 + FCOB_SEG * i, FCOB_Y0 + 1.0, zt + 2.0 + FCOB_T - .6), "seg", "lid")
    dif, HEX_CENTERS[:] = hex_diffuser()
    add("Difusor_FCOB_hex", dif, "diffuser", "lid")
    add("FCOB_terminales_soldados", box(4, 10, 1.2, FCOB_X0 + FCOB_L - 4.5, FCOB_Y0 + 1.0, zt + 2.0 + FCOB_T - .6), "metal", "lid")

    # ---- arneses de la tapa: carriles junto al borde frontal, clips, bridas y puentes con coca.
    z = LANE_Z
    lanes = {n: (x, y, s, r, zb) for n, x, y, s, r, _, zb in BRIDGES}
    kw = dict(group="lid", kind="lógico tapa")
    x, y, s, r, zb = lanes["LCD"]
    hx, hy = x, LCD_Y0 + LCD_W - 1.27
    harness("Arnes_tapa_LCD", [(hx, hy, z - 8), (hx, y + 8, z - 8), (x, y, z)], r, "w_lid", **kw)
    x, y, s, r, zb = lanes["panel_T4"]
    harness("Arnes_tapa_LED", [(LED_X, ROW_Y, HB - 10.0), (LED_X, ROW_Y - 14, z), (LED_X, y, z), (x, y, z)], r, "w_lid", **kw)
    x, y, s, r, zb = lanes["panel_T5"]
    fx, fy = FCOB_X0 + FCOB_L - 1.0, FCOB_Y0 + 1.3
    harness("Arnes_tapa_T5_tronco", [(150, y, z), (x, y, z)], r, "w_lid", **kw)
    harness("Arnes_tapa_FCOB", [(fx, fy, zt + 4.3), (263, fy, z - 1), (263, y - 1.5, z - 1), (147, y - 1.5, z - .5)], 1.3, "w_lid", **kw)
    harness("Arnes_tapa_piezo", [(PIEZO_X, ROW_Y - PIEZO_D / 2 + .5, HB - PIEZO_H + 5), (PIEZO_X, y + 1.0, z - 2), (147, y + 1.0, z - .5)], 1.1, "w_lid", **kw)
    clips("Clips_impresos_tapa", [(LED_X, ROW_Y - 26, z + 1.6), (150, lanes["panel_T4"][1], z + 1.6), (75, lanes["panel_T4"][1], z + 1.6), (125, y, z + 2.2),
                                   (263, 80, z + .3), (263, 40, z + .3), (205, y - 1.5, z + .3), (hx, lanes["LCD"][1] + 8, z + .6)])

    # ---- puentes: coca en U (dos tramos rectos y media vuelta) paralela al borde frontal.
    meta = []
    for name, x, y, s, r, ways, zb in BRIDGES:
        pl, pb = (x, y, LANE_Z), (x, y, zb)
        path = [lid_point(y, LANE_Z, k / 100) for k in range(101)]
        chord_max = max(math.dist(q, (y, zb)) for q in path)
        oy, oz = path[-1]
        chord_open = math.dist((oy, oz), (y, zb))
        length = 1.6 * chord_max                        # la media vuelta pide pi/2 = 1,57 veces la cuerda mayor del recorrido
        pts = bridge_points(pl, pb, s, length)
        solid = Part.makePolygon([V(*q) for q in pts])
        solid = Part.Wire(solid.Edges).makePipeShell([Part.Wire([Part.makeCircle(r, V(*pb), V(s, 0, 0))])], True, True)
        add(f"Puente_arnes_{name}", solid, "w_lid", "bridge")
        rad = (LANE_Z - zb) / 2
        # Separación con la pared frontal de la parte del puente que queda por debajo del borde del gabinete.
        wall_gap = min(min(q[0] if q[1] <= HB else y + (HB - zb) / (q[1] - zb) * (q[0] - y) for q in path), y) - r - WALL
        HARNESS.append({"nombre": f"Puente_arnes_{name}", "tipo": "puente tapa", "diametro_mm": 2 * r, "radio_minimo_mm": round(rad, 1), "longitud_mm": round(length, 1)})
        meta.append({"nombre": name, "tapa": pl, "base": pb, "sentido": s, "radio": r, "vias": ways, "longitud_mm": round(length, 2),
                     "radio_coca_cerrada_mm": rad, "saliente_coca_cerrada_mm": round((length - math.pi * rad) / 2 + rad, 1),
                     "cuerda_cerrada_mm": round(LANE_Z - zb, 2), "cuerda_estacionada_mm": round(chord_open, 2), "cuerda_maxima_mm": round(chord_max, 2),
                     "holgura_minima_mm": round(length - chord_max, 2), "separacion_pared_frontal_mm": round(wall_gap, 2)})
        add(f"Brida_tapa_{name}", box(1.2, 6.4, r * 2 + 1.0, x - s * 2.5 - .6, y - 3.2, LANE_Z - r - .6), "nylon", "lid")
        add(f"Brida_base_{name}", box(1.2, 6.4, 2 * r + .9, x - s * 2.5 - .6, y - 3.2, zb - r - .5), "nylon")
    # ---- lado fijo: de cada ménsula a los conectores de T4 y T5.
    kw = dict(kind="lógico tapa")
    x, y, s, r, zb = lanes["LCD"]
    b = top("T4", "C_LILY")
    harness("Arnes_base_LCD", [(x, y, zb), (b[0], b[1], zb), b], r, "w_lid", **kw)
    for lane, board, refs, straight in (("panel_T4", "T4", ("C_LED",), "C_LED"), ("panel_T5", "T5", ("C_BZ", "C_PIX"), "C_BZ")):
        x, y, s, r, zb = lanes[lane]
        c = top(board, straight)
        tip = (c[0], c[1], 36.0)
        harness(f"Arnes_base_{lane}", [(x, y, zb), (x + 9, y, zb), tip], r, "w_lid", **kw)
        for ref in refs:
            b = top(board, ref)
            pts = [(tip[0], tip[1], tip[2] + .5), b] if ref == straight else [(tip[0], tip[1], tip[2] + .5), (b[0], b[1], 30.5), b]
            harness(f"Arnes_base_{ref}", pts, 1.1, "w_lid", **kw)
    return meta


def network_zone():
    """Z1: prensaestopa, bornera protegida J4, portafusible cerrado F1 y módulo ZMPT101B."""
    g = "network"
    x0, y0 = ZMPT_X0, ZMPT_Y0
    add("U2_ZMPT101B_PCB_51p7x21p6", box(ZMPT_L, ZMPT_W, 1.6, x0, y0, Z_PCB), "pcb_blue", g)
    add("U2_ZMPT101B_transformador", box(18.3, 17.0, ZMPT_H - 1.6, x0 + 23.5, y0 + 2.3, ZT), "cape", g)
    add("U2_ZMPT101B_borne_primario", box(8.0, 10.8, 8.5, x0 + 43.2, y0 + 5.4, ZT)
        .cut(comp([box(3.2, 3.2, 3.4, x0 + 48.2, y0 + 6.5 + 5.08 * i, ZT + 1.6) for i in range(2)])), "tb", g)
    add("U2_ZMPT101B_potenciometro", box(9.5, 4.8, 10.0, x0 + 11.0, y0 + 3.0, ZT), "trimmer", g)
    add("U2_ZMPT101B_potenciometro_tornillo", cyl(1.15, .9, x0 + 12.5, y0 + 5.4, ZT + 10.0), "brass", g)
    add("U2_ZMPT101B_LM358", box(5.0, 4.0, 1.6, x0 + 12.0, y0 + 12.5, ZT), "ic", g)
    add("U2_ZMPT101B_cabecera_MBT", box(2.54, 10.16, 16.5, x0 + .6, y0 + 5.7, ZT), "hdr", g)
    ze = FLOOR + 11.0
    add("J4_bornera_protegida_2P", box(22, 16, 14, 222, 148, FLOOR + 4).cut(comp([box(3, 4, 4, xx, 152 + 8 * i - 2, ze - 2) for xx in (221.5, 241.5) for i in range(2)])), "ic", g)
    add("J4_tornillos", comp([cyl(2.0, .8, 233, 152 + 8 * i, FLOOR + 17.6) for i in range(2)]), "metal", g)
    add("F1_portafusible_cerrado_5x20", comp([cyl(6.25, 42, 150, 160, 13.6, (1, 0, 0)), cyl(6.9, 9, 183, 160, 13.6, (1, 0, 0))]), "ic", g)
    add("F1_terminales", comp([cyl(1.4, 2.5, 147.5, 160, 13.6, (1, 0, 0)), cyl(1.4, 2.5, 192, 160, 13.6, (1, 0, 0))]), "metal", g)
    # Prensaestopa PG7 en la pared trasera y cable de red.
    add("Prensaestopa_PG7", comp([hexprism(15, 5, 258, D, 30, "y"), cyl(7.0, 9, 258, D + 5, 30, (0, 1, 0)), cyl(6.2, WALL + 1, 258, D - WALL - .5, 30, (0, 1, 0)),
                                 hexprism(15, 3, 258, D - WALL - 3, 30, "y")]), "ic", g)
    add("Cable_red_120V", cyl(3.0, 50, 258, 173.0, 30, (0, 1, 0)), "rubber", g)
    add("Pasamuros_MBT_goma", cyl(5.5, PART_Y1 - PART_Y0 + 3, GROMMET[0], PART_Y0 - 1.5, GROMMET[1], (0, 1, 0)).cut(cyl(1.6, 9, GROMMET[0], PART_Y0 - 2, GROMMET[1], (0, 1, 0))), "rubber", g)
    kw = dict(group=g, kind="red 120 V")
    harness("Red_L_entrada_J4", [(256.5, 173.5, 30.5), (256.5, 152, 30.5), (256.5, 152, ze), (243.0, 152, ze)], 1.1, "w_L", **kw)
    harness("Red_N_entrada_J4", [(259.8, 173.5, 29.5), (259.8, 160, 29.5), (259.8, 160, ze), (243.0, 160, ze)], 1.1, "w_N", **kw)
    harness("Red_L_J4_F1", [(223.5, 152, ze), (213, 152, ze), (204, 160, 13.6), (193.5, 160, 13.6)], 1.1, "w_L", **kw)
    harness("Red_L_F1_ZMPT", [(148.5, 160, 13.6), (142, 160, 13.6), (136, y0 + 8.1, ZT + 3.3), (x0 + 50.0, y0 + 8.1, ZT + 3.3)], 1.1, "w_L", **kw)
    harness("Red_N_J4_ZMPT", [(223.5, 160, ze), (215, 160, ze), (205, 171, 8), (152, 171, 8), (141, y0 + 13.2, ZT + 3.3), (x0 + 50.0, y0 + 13.2, ZT + 3.3)],
            1.1, "w_N", **kw)
    # Cable MBT de 3 vías: sale de la zona de red por el pasamuros hacia la bornera J5 de T3.
    j5 = top("T3", "J5")
    hx, hy, zc = GROMMET[0], y0 + 10.78, GROMMET[1]
    harness("C_ZMPT_MBT_a_T3_J5", [(hx, hy, ZT + 16.5), (hx, hy, zc), (hx, 120.0, zc), (j5[0], 120.0, zc), (j5[0], 120.0, ZT + 3.4), (j5[0], BOARDS["T3"][1] + 41.0, ZT + 3.4)],
            1.5, "w_analog", "interior", kind="MBT desde Z1")


# ------------------------------------------------------------------ validación
def schematic_parts():
    out = {}
    pat = re.compile(r'\(symbol\s+\(lib_id "([^"]+)"\)(.*?)\(property "Reference" "([^"]+)".*?\(property "Value" "([^"]*)".*?\(property "Footprint" "([^"]*)"', re.S)
    for t in range(1, 6):
        text = (HW / f"kicad/medidor-t{t}.kicad_sch").read_text(encoding="utf-8")
        out[f"T{t}"] = {m.group(3): (m.group(4), m.group(5).split(":")[-1]) for m in pat.finditer(text) if not m.group(3).startswith("#")}
    return out


def validate_electrical():
    issues, notes = [], []
    sch = schematic_parts()
    per_board = {}
    for board, parts in sch.items():
        modeled = {fp[0] for fp in FOOTPRINTS[board]} | set(OFFBOARD.get(board, {}))
        planned = set(PLANNED_EXTRA.get(board, {}))
        missing, extra = sorted(set(parts) - modeled), sorted(modeled - set(parts))
        extra = sorted(set(extra) - planned)
        if missing:
            issues.append(f"{board}: el CAD no modela {missing}")
        if extra:
            issues.append(f"{board}: el CAD tiene {extra} que no están en el esquemático")
        for ref, (value, fp) in parts.items():
            m = re.search(r"JST_XH_B(\d+)B|PinHeader_1x(\d+)", fp)
            if m and (board, ref) in PINS:
                n = int(m.group(1) or m.group(2))
                if PINS[(board, ref)] != n:
                    issues.append(f"{board} {ref}: {PINS[(board, ref)]} vías en CAD y {n} en el esquemático")
            if ref in ("J1", "J5") and "JST" in fp:
                notes.append(f"{board} {ref}: el esquemático asigna huella {fp}; el BOM y el CAD usan bornera de 5,08 mm de {PINS[(board, ref)]} polos. Unificar la huella.")
            if ref == "D8":
                notes.append("T4 D8: el esquemático usa huella LED_D5.0mm sobre la tarjeta; el LED va en la tapa y el CAD pone un conector de 2 vías para su arnés.")
        if planned:
            notes.append(f"{board}: conectores E.9 pendientes de incorporar al esquemático: {sorted(planned)}.")
        per_board[board] = {"esquematico": sorted(parts), "sobre_tarjeta": sorted(fp[0] for fp in FOOTPRINTS[board]),
                            "fuera_de_tarjeta": OFFBOARD.get(board, {}),
                            "extras_planificados": PLANNED_EXTRA.get(board, {}),
                            "coincide": not missing and not extra and not planned}
    # Lista por tarjeta frente al esquemático (documental).
    with (HW / "lista-por-tarjeta.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Tarjeta"] in sch:
                listed = set(row["Referencias"].split())
                documentary = {"BOARD", "socket", "sockets"}
                only_list = sorted(listed - set(sch[row["Tarjeta"]]) - documentary)
                offboard = set(OFFBOARD.get(row["Tarjeta"], {}))
                only_sch = sorted(r for r in set(sch[row["Tarjeta"]]) - listed - offboard if not r.startswith("C_"))
                if only_list or only_sch:
                    notes.append(f"{row['Tarjeta']}: lista-por-tarjeta.csv difiere del esquemático; solo en la lista {only_list}, solo en el esquemático {only_sch}.")
    # Arneses: mismo número de vías en cada extremo que conexiones-entre-tarjetas.csv.
    cables = {}
    with (HW / "conexiones-entre-tarjetas.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            c = cables.setdefault(row["Cable"], {"desde": row["Desde"], "hacia": row["Hacia"], "vias": 0})
            c["vias"] += 1
    alias = {("T3", "C_ZMPT"): "J5"}
    for name, c in cables.items():
        for end in (c["desde"], c["hacia"]):
            if end in BOARDS:
                ref = alias.get((end, name), name)
                if PINS.get((end, ref)) != c["vias"]:
                    issues.append(f"{name}: {end} tiene {PINS.get((end, ref))} vías y la tabla pide {c['vias']}")
    contracts = json.loads((HW / "kicad/contratos.json").read_text(encoding="utf-8"))
    for name, pins in contracts["pinouts"].items():
        if name in cables and cables[name]["vias"] != len(pins):
            issues.append(f"{name}: contratos.json y conexiones-entre-tarjetas.csv no coinciden")
    return {"tarjetas": per_board, "arneses": cables, "notas": sorted(set(notes))}, issues


def validate_layout():
    issues, rects = [], []
    for ref, (x, y, w, d, _) in BOARDS.items():
        if x < WALL + 2 or y < WALL + 2 or x + w > W - WALL - 2 or y + d > PART_Y0 - 3:
            issues.append(f"{ref} fuera de la zona MBT")
        for other, ox, oy, ow, od in rects:
            if x < ox + ow + 2 and x + w + 2 > ox and y < oy + od + 2 and y + d + 2 > oy:
                issues.append(f"solape o separación < 2 mm entre {ref} y {other}")
        rects.append((ref, x, y, w, d))
        fps = FOOTPRINTS[ref]
        holes = [(4, 4), (w - 4, 4), (4, d - 4), (w - 4, d - 4)]
        for i, (r1, ax0, ay0, ax1, ay1, over) in enumerate(fps):
            if not over and (ax0 < 0 or ay0 < 0 or ax1 > w or ay1 > d):
                issues.append(f"{ref} {r1} sobresale de la tarjeta")
            for hx, hy in holes:
                if r1 != "U1" and ax0 < hx + 2.75 and ax1 > hx - 2.75 and ay0 < hy + 2.75 and ay1 > hy - 2.75:
                    issues.append(f"{ref} {r1} invade un tornillo de montaje")
            for r2, bx0, by0, bx1, by1, _ in fps[i + 1:]:
                if ax0 < bx1 - .01 and ax1 > bx0 + .01 and ay0 < by1 - .01 and ay1 > by0 + .01:
                    issues.append(f"{ref}: {r1} se solapa con {r2}")
    return issues


def bbox_near(a, b, tol):
    return (a.XMin <= b.XMax + tol and a.XMax >= b.XMin - tol and a.YMin <= b.YMax + tol and a.YMax >= b.YMin - tol
            and a.ZMin <= b.ZMax + tol and a.ZMax >= b.ZMin - tol)


def validate_support():
    """Ninguna pieza flota: todo debe tocar, en cadena, al gabinete (ensamble cerrado)."""
    items = [(n, s, s.BoundBox) for n, s, _, _ in OBJECTS if not n.endswith("_Donas")]
    seen, todo = {"Gabinete_E7"}, ["Gabinete_E7"]
    byname = {n: (s, bb) for n, s, bb in items}
    while todo:
        s, bb = byname[todo.pop()]
        for n, s2, bb2 in items:
            if n not in seen and bbox_near(bb, bb2, .15) and s.distToShape(s2)[0] <= .15:
                seen.add(n)
                todo.append(n)
    return sorted(n for n, _, _ in items if n not in seen)


def validate_swing():
    """La tapa recorre LID_PATH hasta quedar estacionada sin interferir con el cuerpo ni con lo montado en él."""
    lid_items = [(n, s) for n, s, _, g in OBJECTS if g == "lid"]
    fixed = [(n, s, s.BoundBox) for n, s, _, g in OBJECTS if g in ("body", "interior", "network", "guard") and not n.endswith("_Donas")]
    hits = set()
    for f in (.04, .10, .18, .28, .40, .52, .62, .71, .80, .87, .94, 1.0):
        deg = "{:.0f}° +{:.1f}/{:.1f} mm".format(*lid_pose(f))
        for n, s in lid_items:
            r = lid_moved(s, f)
            bb = r.BoundBox
            for n2, s2, bb2 in fixed:
                if bbox_near(bb, bb2, 0) and r.common(s2).Volume > .05:
                    hits.add(f"{n} con {n2} a {deg}")
    return sorted(hits)


def fit_coupons(doc, info):
    """Recortes de la geometría final para probar piezas compradas antes de imprimir el gabinete."""
    FIT.mkdir(exist_ok=True)
    for old in FIT.glob("*.stl"):
        old.unlink()
    lid = doc.getObject("Tapa_E7").Shape
    body = doc.getObject("Gabinete_E7").Shape
    guard_shape = doc.getObject("Guarda_120V_E7").Shape
    cx, cy = LCD_C
    ux, uy, uz = info["usb"]
    mx, my = MAGNETS[0]
    clip = lambda shape, x0, y0, z0, x1, y1, z1: shape.common(box(x1 - x0, y1 - y0, z1 - z0, x0, y0, z0))
    pieces = {
        "tapa_pantalla_T4S3": clip(lid, cx - 38, cy - 30, HB - 6, cx + 38, cy + 30, H),
        # Dedicated coupon uses the exact panel thickness, bore and printed sleeve dimensions.
        "tapa_LED": box(30, 30, LID, 0, 0, 0).cut(cyl(2.55, LID + 2, 15, 15, -1))
                    .fuse(cyl(4.5, 5.0, 15, 15, -5.0).cut(cyl(2.55, 6.0, 15, 15, -5.5))),
        "pared_izq_jacks_SCT": clip(body, 0, 84, 27, 12, 128, 49),
        "pared_der_jack_DC": clip(body, W - 12, 24, 28, W, 48, 52),
        "pared_trasera_PG7": clip(body, 246, D - 12, 17, 267, D, 43),
        "cuerpo_alojamiento_iman": clip(body, mx - 8, 0, HB - 10, mx + 8, 16, HB),
        "tapa_alojamiento_iman": clip(lid, mx - 8, 0, HB - 6, mx + 8, 16, H),
        "cuerpo_cuna_LM2596": clip(body, 160, 12, 0, 215, 46, 12),
        "cuerpo_pin_guarda_120V": clip(body, 0, 138, HB - 8, 16, 153, HB + 3),
        "guarda_socket_ciego_120V": clip(guard_shape, 0, 138, HB - 7, 16, 153, H + 1),
    }
    for name, shape in pieces.items():
        assert shape.isValid() and len(shape.Solids) == 1 and shape.Volume > 20, (name, len(shape.Solids), shape.Volume)
        MeshPart.meshFromShape(Shape=shape, LinearDeflection=.1, AngularDeflection=.3).write(str(FIT / f"{name}.stl"))
    return sorted(f"pruebas-de-ajuste/{name}.stl" for name in pieces)


def main():
    info = enclosure()
    feat = lid(info)
    guard(info)
    boards()
    base_harnesses()
    bridges = lid_parts(feat)
    network_zone()

    electrical, issues = validate_electrical()
    issues += validate_layout()
    import os
    quick = bool(os.environ.get("E7_RAPIDO"))
    floating = validate_support()
    issues += [f"pieza sin apoyo: {n}" for n in floating]
    swing = [] if quick else validate_swing()
    issues += [f"interferencia al abrir: {h}" for h in swing]
    for h in HARNESS:
        h["relacion_radio_diametro"] = round(h["radio_minimo_mm"] / h["diametro_mm"], 2)
        if h["relacion_radio_diametro"] < 2.5:
            issues.append(f"radio de curvatura < 2,5 diámetros en {h['nombre']}")
    for b in bridges:
        if b["longitud_mm"] < 1.5708 * b["cuerda_maxima_mm"]:
            issues.append(f"puente {b['nombre']} sin holgura suficiente durante el recorrido de la tapa")
        if b["separacion_pared_frontal_mm"] < 1.0:
            issues.append(f"puente {b['nombre']} roza la pared frontal")
    zmpt_tr = box(18.3, 17.0, ZMPT_H - 1.6, ZMPT_X0 + 23.5, ZMPT_Y0 + 2.3, ZT)
    magnets = []
    for x, y in MAGNETS:
        d = zmpt_tr.distToShape(cyl(MAG_D / 2, 2 * MAG_T, x, y, HB - MAG_T))[0]
        magnets.append({"xy": [x, y], "distancia_a_transformador_ZMPT_mm": round(d, 1)})
        if d < MAG_MIN_ZMPT:
            issues.append(f"imán en ({x}, {y}) a menos de {MAG_MIN_ZMPT} mm del transformador del ZMPT101B")
    for name, s, _, g in OBJECTS:
        if g == "network" and s.BoundBox.YMin < PART_Y0 - .01 and "Pasamuros" not in name:
            issues.append(f"{name} sale de la zona de red")
        if g in ("interior", "lid") and s.BoundBox.YMax > (LID_Y1 if g == "lid" else PART_Y0) + .01 and name != "C_ZMPT_MBT_a_T3_J5":
            issues.append(f"{name} entra en la zona de red")

    if quick:
        print("MODO RÁPIDO (sin guardar):", *issues, sep="\n  ")
        for h in HARNESS:
            print(f"  {h['nombre']:28s} d={h['diametro_mm']} rmin={h['radio_minimo_mm']} L={h['longitud_mm']}")
        return
    doc = App.newDocument("Medidor_E7_Perforadas")
    for name, shape, mat, group in OBJECTS:
        o = doc.addObject("Part::Feature", name)
        o.Label = name.replace("_", " ")
        o.Shape = shape
        o.addProperty("App::PropertyString", "ColorRGB", "Render").ColorRGB = ",".join(map(str, COLORS[mat]))
        o.addProperty("App::PropertyString", "Material", "Render").Material = mat
        o.addProperty("App::PropertyString", "AssemblyGroup", "Render").AssemblyGroup = group
    doc.recompute()
    doc.saveAs(str(HERE / "medidor-E7-perforadas.FCStd"))
    Import.export(list(doc.Objects), str(HERE / "medidor-E7-perforadas.step"))
    STL.mkdir(exist_ok=True)
    for old in STL.glob("*.stl"):
        old.unlink()
    printed = ("Gabinete_E7", "Tapa_E7", "Guarda_120V_E7", "Soporte_FCOB", "Difusor_FCOB_hex", "Placa_trasera_desmontable_LCD", "Aro_reten_piezo_bayoneta")
    for name in printed:
        mesh = MeshPart.meshFromShape(Shape=doc.getObject(name).Shape, LinearDeflection=.1, AngularDeflection=.3)
        mesh.write(str(STL / f"{name.lower()}.stl"))
    coupons = fit_coupons(doc, info)

    usb = info["usb"]
    meta = {
        "revision": "E.9", "unidades": "mm", "envolvente": [W, D, H],
        "tapa": {"cierre": "4 pares de imanes 6x2", "pivote_yz": [PIVOT_Y, PIVOT_Z], "trayectoria": [list(k) for k in LID_PATH],
                 "imanes_xy": [list(m) for m in MAGNETS], "lenguetas_x": list(TAB_X)},
        "tarjetas": {k: {"rect": list(v[:4]), "rotulo": v[4], "z_superior": ZT} for k, v in BOARDS.items()},
        "puentes": bridges,
        "lcd_area_activa": {"centro": [LCD_C[0], LCD_C[1], H + .02], "tamano": LCD_ACTIVE, "modelo": "LilyGO T4-S3 AMOLED"},
        "led_panel": [LED_X, ROW_Y, HB + 5.0],
        "fcob": {"x0": FCOB_X0, "y0": FCOB_Y0, "largo": FCOB_L, "ancho": FCOB_W, "segmento": FCOB_SEG, "z_difusor": H,
                 "ventana": list(WIN), "hex": {"radio": HEX_R, "entre_caras": HEX_AF, "surco": HEX_GROOVE, "aro": HEX_RIM, "espesores_mm": list(HEX_T),
                                               "repeticion_mm": 3 * HEX_R, "centros": HEX_CENTERS}},
        "puntos": {"usb_c": list(usb), "esp32": list(top("T4", "U1")), "j1": list(top("T1", "J1")), "j5": list(top("T3", "J5")),
                   "zona_red": [165.0, 159.0, 15.0], "piezo": [PIEZO_X, ROW_Y, H], "lcd": [LCD_C[0], LCD_C[1], H],
                   "lm2596_pot": [166.0 + 28.4, 18.0 + 3.6, FLOOR + 2.0 + LM_H], "zmpt_pot": [ZMPT_X0 + 12.5, ZMPT_Y0 + 5.4, ZT + 10.9]},
        "tabique_y": [PART_Y0, PART_Y1], "junta_tapa_guarda_y": [LID_Y1, GUARD_Y0],
    }
    (HERE / "metadatos-ensamble.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    report = {
        "revision": "E.9", "valid": not issues, "issues": issues,
        "enclosure_mm": [W, D, H], "network_partition_y_mm": PART_Y0,
        "boards": {k: list(v[:4]) for k, v in BOARDS.items()},
        "fcob_strip_mm": [FCOB_L, FCOB_W], "fcob_ventana_mm": [WIN[1] - WIN[0], round(WIN[3] - WIN[2], 2)],
        "difusor_hex": {"espesores_mm": list(HEX_T), "repeticion_mm": 3 * HEX_R, "celdas": len(HEX_CENTERS), "distancia_fcob_a_piel_mm": round(H - HEX_T[2] - (HB - 8.0 + FCOB_T), 2)},
        "objetos": len(OBJECTS), "piezas_sin_apoyo": floating, "interferencias_al_abrir": swing,
        "tapa": {"cierre": "imanes", "trayectoria_servicio": [list(k) for k in LID_PATH], "imanes": magnets,
                 "unero_frontal_mm": {"centro_x": FINGER_SCALLOP_X, "radio": FINGER_SCALLOP_R, "profundidad_vertical": 7.0},
                 "separacion_minima_exigida_mm": MAG_MIN_ZMPT},
        "puentes_de_arnes": bridges, "arneses": HARNESS,
        "esquematicos": electrical, "piezas_impresas": [f"stl/{n.lower()}.stl" for n in printed],
        "probetas_ajuste": coupons,
        "dimension_basis": "medidas-componentes.json",
        "limits": "Comprobación geométrica del CAD. No valida aislamiento, distancias normativas, soldadura ni el prototipo físico.",
    }
    (HERE / "validacion-3d.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Medidor E.9 CAD: {len(OBJECTS)} objetos; {W} x {D} x {H} mm; válido={not issues}")
    for i in issues:
        print("  PROBLEMA:", i)
    for n in electrical["notas"]:
        print("  nota:", n)
    if issues:
        raise SystemExit(1)


main()
