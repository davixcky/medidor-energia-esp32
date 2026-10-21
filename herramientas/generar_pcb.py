#!/usr/bin/env python3
"""Genera la PCB de una sola cara del medidor (../hardware/medidor-energia.kicad_pcb).

Pensada para fabricarse en el laboratorio o en casa, por transferencia de tóner o fresado CNC:

- cobre solo abajo (B.Cu) y componentes arriba; lo que no cabe en una cara se resuelve con
  puentes de alambre (JPn) del lado de los componentes, dibujados en la serigrafía;
- pistas de 0,8 mm (1,2 mm en alimentación), separación de 0,5 mm y pads de al menos 2 mm;
- relleno de GND en toda la cara libre y cuatro agujeros M3 a 4 mm de las esquinas;
- contorno de 150 × 90 mm (cabe en una baquelita de 10 × 15 cm), el mismo del gabinete.

El ruteo lo hace Freerouting 2.5 con la cara de arriba como «capa de puentes»: cada tramo que
Freerouting pone arriba se convierte en un alambre recto. La sesión elegida se guarda en
../hardware/ruteo-freerouting.ses para que el resultado sea reproducible.

Se ejecuta con el Python de KiCad (módulo pcbnew), después de exportar la netlist:

    python3 generar_pcb.py importar   # coloca y aplica el ruteo guardado (por omisión)
    python3 generar_pcb.py rutear     # coloca y rutea de nuevo (java + freerouting.jar)
    python3 generar_pcb.py colocar    # solo coloca los componentes
"""
import json
import os
import re
import subprocess
import sys

import pcbnew
from pcbnew import FromMM as MM, ToMM, VECTOR2I

from sexpr import find, find1, parse

AQUI = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(AQUI, "..", "hardware"))
NET = os.path.join(HW, "medidor-energia.net")
SALIDA = os.path.join(HW, "medidor-energia.kicad_pcb")
SES = os.path.join(HW, "ruteo-freerouting.ses")
TRABAJO = os.path.join(HW, "fabricacion", "ruteo")
CONECTORES = os.path.join(HW, "3d", "conectores.json")
FREEROUTING = os.environ.get("FREEROUTING_JAR", os.path.expanduser("~/.local/share/freerouting/freerouting.jar"))
LIBS = {"Medidor": os.path.join(HW, "Medidor.pretty")}
FP_SIS = "/usr/share/kicad/footprints"

W, H = 150.0, 90.0
PISTA, PISTA_ALIM, SEP = 0.8, 1.2, 0.5
REDES_ALIM = {"GND", "+5V", "+3V3", "Net-(J1-Pin_1)", "Net-(D1-A)"}
COSTO_VIA = int(os.environ.get("VIA_COST", 400))        # cada vía es un puente: se encarecen
COSTO_PUENTE = float(os.environ.get("JUMPER_COST", 20))
BORDE = 1.5                                            # el ruteo se queda a 1,5 mm del borde
# La placa se dibuja a 25 mm de la esquina de la hoja: la impresora no imprime en el margen.
OX, OY = 25.0, 25.0
AGUJEROS = [(4.0, 4.0), (W - 4.0, 4.0), (4.0, H - 4.0), (W - 4.0, H - 4.0)]

# Referencia -> (x, y, rotación) del origen de la huella, en mm desde la esquina superior
# izquierda de la placa vista desde los componentes. El borde superior da al tabique (bornera
# del ZMPT101B), el izquierdo a los jacks del panel y el inferior al frente (USB del ESP32).
U1X, U1Y = 87.5, 30.0     # pin 1 (3V3) del ESP32; la fila derecha queda 25,4 mm a la derecha
COLOCACION = {
    "U1": (U1X, U1Y, 0),
    # entrada de 5 V: bornera en el borde izquierdo, PTC, diodo y condensadores abajo
    "J1": (6.5, 76.0, 90),
    "F2": (16.0, 84.5, 0),
    "D1": (31.0, 84.5, 0),
    "C1": (48.0, 82.0, 0),
    "C2": (56.0, 84.5, 0),
    # pinzas: puntos de soldadura del cable de cada jack (T, R, S) en el borde izquierdo
    "J2": (5.0, 30.0, 0),
    "J3": (5.0, 48.0, 0),
    # CH1: resistencia serie, condensador del filtro y diodos de recorte
    "R5": (12.0, 30.0, 0),
    "C5": (27.0, 30.0, 0),
    "D2": (36.0, 26.5, 0),
    "D3": (36.0, 33.5, 0),
    # CH2
    "R6": (12.0, 48.0, 0),
    "C6": (27.0, 48.0, 0),
    "D4": (36.0, 44.5, 0),
    "D5": (36.0, 51.5, 0),
    # polarización VBIAS (1,32 V) junto al retorno S de los jacks
    "R3": (12.0, 60.0, 0),
    "R4": (12.0, 65.0, 0),
    "C7": (28.0, 62.5, 0),
    "C8": (35.0, 62.5, 0),
    # tensión: bornera del ZMPT101B en el borde superior, divisor 11k/13k, filtro y recorte
    "J5": (14.0, 8.0, 0),
    "R7": (36.0, 7.0, 0),
    "R8": (36.0, 12.0, 0),
    "C9": (52.0, 9.5, 0),
    "D6": (61.0, 6.0, 0),
    "D7": (61.0, 13.0, 0),
    # reserva ADC1 (IO34, IO32, IO33) arriba a la izquierda del ESP32
    "J7": (72.0, 21.0, 90),
    # LED y pulsadores del panel: resistencias, antirrebote y conectores
    "R11": (60.0, 50.0, 0),
    "R12": (60.0, 54.5, 0),
    "R13": (60.0, 59.0, 0),
    "C10": (62.0, 64.5, 0),
    "C11": (70.0, 64.5, 0),
    "D8": (62.0, 72.0, 90),
    "SW1": (69.0, 72.0, 90),
    "SW2": (76.0, 72.0, 90),
    # OLED (I2C) a la derecha del ESP32 con sus resistencias de pull-up
    "J6": (128.0, 34.0, 0),
    "R9": (122.0, 52.0, 0),
    "R10": (122.0, 57.0, 0),
}
# referencias que quedarían fuera del borde: desplazamiento (mm) desde el origen de la huella
REF_POS = {"J1": (6.5, -1.0)}
# Reglas que se relajan en el proyecto, a propósito:
# - lib_footprint_mismatch: los pads se agrandan (≥ 2 mm) para la transferencia de tóner;
# - silk_over_copper: la serigrafía de biblioteca queda recortada por esos pads más grandes;
# - pth_inside_courtyard: los extremos de algunos puentes caen bajo el ESP32 (va en zócalo).
SEVERIDADES = {"lib_footprint_mismatch": "ignore", "silk_over_copper": "ignore",
               "pth_inside_courtyard": "warning"}
TEXTO_COBRE = [("MEDIDOR DE ENERGÍA ESP32\nREV. B", 1.5),
               ("MEDIDOR DE ENERGÍA ESP32", 1.5), ("MEDIDOR ESP32", 1.3)]


def leer_netlist():
    t = parse(open(NET, encoding="utf-8").read())[0]
    comps = {}
    for c in find(find1(t, "components"), "comp"):
        comps[find1(c, "ref")[1]] = (find1(c, "value")[1], find1(c, "footprint")[1], find1(c, "tstamps")[1])
    red_de_pin = {}
    for n in find(find1(t, "nets"), "net"):
        for x in find(n, "node"):
            red_de_pin[(find1(x, "ref")[1], find1(x, "pin")[1])] = find1(n, "name")[1]
    return comps, red_de_pin


def cargar_huella(fpid):
    lib, nombre = fpid.split(":")
    fp = pcbnew.FootprintLoad(LIBS.get(lib, os.path.join(FP_SIS, lib + ".pretty")), nombre)
    if fp is None:
        raise SystemExit("no encuentro la huella " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, nombre))
    return fp


def agrandar_pads(fp):
    """Pads de al menos 2 mm (ovalados en filas de 2,54 mm) sin romper la separación."""
    pads = list(fp.Pads())
    pos = [(ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)) for p in pads]
    for p, (x, y) in zip(pads, pos):
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
            continue
        dx = min([abs(x - a) for a, b in pos if abs(y - b) < 0.1 and abs(x - a) > 0.1] or [99])
        dy = min([abs(y - b) for a, b in pos if abs(x - a) < 0.1 and abs(y - b) > 0.1] or [99])
        s = p.GetSize(pcbnew.F_Cu)
        sx, sy = ToMM(s.x), ToMM(s.y)
        tx = min(max(sx, 2.0), dx - SEP - 0.04)
        ty = min(max(sy, 2.0), dy - SEP - 0.04)
        if dy < 3 and dx >= 5:
            tx = max(tx, 2.4)
        if dx < 3 and dy >= 5:
            ty = max(ty, 2.4)
        tx, ty = max(tx, sx), max(ty, sy)
        if abs(tx - ty) > 0.01 and p.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
            p.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_OVAL)
        p.SetSize(pcbnew.F_Cu, VECTOR2I(MM(tx), MM(ty)))


def construir():
    comps, red_de_pin = leer_netlist()
    b = pcbnew.BOARD()
    b.SetCopperLayerCount(2)
    ds = b.GetDesignSettings()
    ds.m_TrackMinWidth = MM(0.6)
    ds.m_MinClearance = MM(SEP)
    ds.m_CopperEdgeClearance = MM(0.5)
    ds.m_ViasMinSize = MM(1.8)
    ds.m_MinThroughDrill = MM(0.8)
    ds.SetBoardThickness(MM(1.6))
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetTrackWidth(MM(PISTA))
    nc.SetClearance(MM(SEP))
    nc.SetViaDiameter(MM(2.0))
    nc.SetViaDrill(MM(0.8))
    alim = pcbnew.NETCLASS("Alimentacion")
    alim.SetTrackWidth(MM(PISTA_ALIM))
    alim.SetClearance(MM(SEP))
    alim.SetViaDiameter(MM(2.0))
    alim.SetViaDrill(MM(0.8))
    ds.m_NetSettings.SetNetclass("Alimentacion", alim)
    for n in sorted(REDES_ALIM):
        ds.m_NetSettings.SetNetclassPatternAssignment(n, "Alimentacion")

    redes = {}
    for nombre in sorted(set(red_de_pin.values())):
        ni = pcbnew.NETINFO_ITEM(b, nombre)
        b.Add(ni)
        redes[nombre] = ni

    for ref, (valor, fpid, uuid) in sorted(comps.items()):
        if ref not in COLOCACION:
            raise SystemExit("falta la posición de " + ref)
        fp = cargar_huella(fpid)
        fp.SetReference(ref)
        fp.SetValue(valor)
        fp.SetPath(pcbnew.KIID_PATH("/" + uuid))
        fp.SetSheetname("")
        fp.SetSheetfile("medidor-energia.kicad_sch")
        agrandar_pads(fp)
        for p in fp.Pads():
            red = red_de_pin.get((ref, p.GetNumber()))
            if red in redes:
                p.SetNet(redes[red])
        x, y, rot = COLOCACION[ref]
        b.Add(fp)
        fp.SetPosition(VECTOR2I(MM(x), MM(y)))
        fp.SetOrientationDegrees(rot)
        fp.Reference().SetVisible(True)
        fp.Value().SetVisible(False)
        if ref in REF_POS:
            fp.Reference().SetPosition(VECTOR2I(MM(x + REF_POS[ref][0]), MM(y + REF_POS[ref][1])))

    for i, (x, y) in enumerate(AGUJEROS, 1):
        fp = cargar_huella("MountingHole:MountingHole_3.2mm_M3")
        fp.SetReference(f"H{i}")
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        b.Add(fp)
        fp.SetPosition(VECTOR2I(MM(x), MM(y)))

    r = pcbnew.PCB_SHAPE(b)
    r.SetShape(pcbnew.SHAPE_T_RECT)
    r.SetStart(VECTOR2I(0, 0))
    r.SetEnd(VECTOR2I(MM(W), MM(H)))
    r.SetLayer(pcbnew.Edge_Cuts)
    r.SetWidth(MM(0.15))
    b.Add(r)
    return b


def reportar_solapes(b):
    cajas = {}
    for f in b.GetFootprints():
        ref = f.GetReference()
        c = f.GetCourtyard(pcbnew.F_CrtYd)
        bb = c.BBox() if c.OutlineCount() else f.GetBoundingBox(False)
        cajas[ref] = (ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()))
    malos = 0
    refs = sorted(cajas)
    for i, a in enumerate(refs):
        ax0, ay0, ax1, ay1 = cajas[a]
        if ax0 < -0.01 or ay0 < -0.01 or ax1 > W + 0.01 or ay1 > H + 0.01:
            print("FUERA DE LA PLACA:", a, [round(v, 1) for v in cajas[a]])
            malos += 1
        for c in refs[i + 1:]:
            bx0, by0, bx1, by1 = cajas[c]
            if ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1:
                print("SE SOLAPAN:", a, c)
                malos += 1
    print("solapes:", malos)
    return malos


def bloques(texto, cabeza):
    """(inicio, fin) de cada bloque «(cabeza ...» con paréntesis balanceados."""
    out, i = [], 0
    while True:
        i = texto.find("(" + cabeza, i)
        if i < 0:
            return out
        prof, j = 0, i
        while True:
            if texto[j] == "(":
                prof += 1
            elif texto[j] == ")":
                prof -= 1
                if prof == 0:
                    break
            j += 1
        out.append((i, j + 1))
        i = j + 1


def preparar_dsn(texto):
    """Una sola cara: los pads existen solo en B.Cu; F.Cu queda como capa de puentes."""
    piezas, ult = [], 0
    for a, z in bloques(texto, "padstack "):
        bloque = texto[a:z]
        if "Via[" not in bloque:
            for sa, sz in reversed(bloques(bloque, "shape (")):
                if "F.Cu" in bloque[sa:sz]:
                    bloque = bloque[:sa] + bloque[sz:]
        piezas += [texto[ult:a], bloque]
        ult = z
    piezas.append(texto[ult:])
    texto = "".join(piezas)
    e = BORDE * 1000
    caja = "(path pcb 0  %d %d  %d %d  %d %d  %d %d  %d %d)" % (
        W * 1000 - e, -H * 1000 + e, e, -H * 1000 + e, e, -e, W * 1000 - e, -e, W * 1000 - e, -H * 1000 + e)
    texto = re.sub(r"\(boundary\s*\(path pcb 0[^)]*\)", "(boundary\n      " + caja, texto, count=1)
    ajustes = """    (autoroute_settings
      (fanout off) (autoroute on) (postroute on) (vias on)
      (via_costs %d) (plane_via_costs 5) (start_ripup_costs 100)
      (layer_rule F.Cu (active on) (preferred_direction horizontal)
        (preferred_direction_trace_costs %g) (against_preferred_direction_trace_costs %g))
      (layer_rule B.Cu (active on) (preferred_direction vertical)
        (preferred_direction_trace_costs 1) (against_preferred_direction_trace_costs 1))
    )
""" % (COSTO_VIA, COSTO_PUENTE, COSTO_PUENTE)
    a, z = bloques(texto, "structure")[0]
    return texto[:z - 1] + ajustes + "  " + texto[z - 1:]


def rutear(b):
    os.makedirs(TRABAJO, exist_ok=True)
    dsn = os.path.join(TRABAJO, "medidor.dsn")
    ses = os.path.join(TRABAJO, "medidor.ses")
    log = os.path.join(TRABAJO, "freerouting.log")
    pcbnew.ExportSpecctraDSN(b, dsn)
    texto = preparar_dsn(open(dsn).read())
    open(dsn, "w").write(texto)
    if os.path.exists(ses):
        os.remove(ses)
    cmd = ["java", "-jar", FREEROUTING, "-de", dsn, "-do", ses, "-mp", os.environ.get("FR_PASES", "200"),
           "-mt", os.environ.get("FR_HILOS", "4"), "--gui.enabled=false"]
    subprocess.run(cmd, check=True, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    res = re.findall(r"incomplete connections: (\d+)", open(log).read())
    print("freerouting: conexiones sin rutear =", res[-1] if res else "?")
    # Freerouting no da siempre el mismo resultado: si este ruteo es el bueno, se copia
    # fabricacion/ruteo/medidor.ses a ../hardware/ruteo-freerouting.ses.
    if not pcbnew.ImportSpecctraSES(b, ses):
        raise SystemExit("no pude importar " + ses)


def hacer_puentes(b):
    """Cada grupo de tramos de F.Cu entre vías se convierte en un puente de alambre JPn."""
    vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    tramos = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.F_Cu]
    clave = lambda p: (round(ToMM(p.x), 2), round(ToMM(p.y), 2))
    padre = {}

    def raiz(k):
        while padre.setdefault(k, k) != k:
            k = padre[k]
        return k
    for s in tramos:
        padre[raiz(clave(s.GetStart()))] = raiz(clave(s.GetEnd()))
    grupos = {}
    for v in vias:
        grupos.setdefault(raiz(clave(v.GetPosition())), {})[clave(v.GetPosition())] = v
    n = alambres = 0
    lista = []
    for vs in sorted(grupos.values(), key=lambda g: sorted(g)[0]):
        pts = sorted(vs)
        if len(pts) < 2:
            continue
        red = next(iter(vs.values())).GetNet()
        hechos, aristas = [0], []
        while len(hechos) < len(pts):
            _, i, j = min(((pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2, i, j)
                          for i in hechos for j in range(len(pts)) if j not in hechos)
            hechos.append(j)
            aristas.append((pts[i], pts[j]))
        n += 1
        alambres += len(aristas)
        agregar_puente(b, f"JP{n}", red, pts, aristas)
        lista.append((f"JP{n}", red.GetNetname(), pts, aristas))
    for t in vias + tramos:
        b.Remove(t)
    print(f"puentes: {n} ({alambres} alambres)")
    return lista


def agregar_puente(b, ref, red, pts, aristas):
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference(ref)
    fp.SetValue("puente")
    fp.SetAttributes(pcbnew.FP_THROUGH_HOLE | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
    fp.SetDuplicatePadNumbersAreJumpers(True)
    fp.SetFPID(pcbnew.LIB_ID("Medidor", "Puente_alambre"))
    b.Add(fp)
    fp.SetPosition(VECTOR2I(MM(pts[0][0]), MM(pts[0][1])))
    for x, y in pts:
        p = pcbnew.PAD(fp)
        p.SetNumber("1")
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_CIRCLE)
        p.SetSize(pcbnew.F_Cu, VECTOR2I(MM(2.0), MM(2.0)))
        p.SetDrillSize(VECTOR2I(MM(0.8), MM(0.8)))
        p.SetLayerSet(pcbnew.PAD.PTHMask())
        fp.Add(p)
        p.SetPosition(VECTOR2I(MM(x), MM(y)))
        p.SetNet(red)
    for p1, p2 in aristas:
        s = pcbnew.PCB_SHAPE(fp)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(VECTOR2I(MM(p1[0]), MM(p1[1])))
        s.SetEnd(VECTOR2I(MM(p2[0]), MM(p2[1])))
        s.SetLayer(pcbnew.F_SilkS)
        s.SetWidth(MM(0.4))
        fp.Add(s)
    (x1, y1), (x2, y2) = aristas[0]
    fp.Reference().SetPosition(VECTOR2I(MM((x1 + x2) / 2), MM((y1 + y2) / 2 - 1.2)))
    fp.Reference().SetTextSize(VECTOR2I(MM(0.9), MM(0.9)))
    fp.Reference().SetTextThickness(MM(0.15))
    fp.Value().SetVisible(False)


def escribir_puentes(lista):
    """Tabla de puentes para el montaje: red, largo y agujeros (mm desde la esquina superior izquierda)."""
    b = pcbnew.LoadBoard(SALIDA)
    pads = [(ToMM(p.GetPosition().x) - OX, ToMM(p.GetPosition().y) - OY, f"{f.GetReference()}.{p.GetNumber()}")
            for f in b.GetFootprints() if not f.GetReference().startswith(("JP", "H")) for p in f.Pads()]

    def junto_a(x, y):
        return min(pads, key=lambda q: (q[0] - x) ** 2 + (q[1] - y) ** 2)[2]
    filas, total = [], 0
    for ref, red, pts, aristas in lista:
        largo = sum(((a[0] - c[0]) ** 2 + (a[1] - c[1]) ** 2) ** 0.5 for a, c in aristas)
        total += len(aristas)
        aguj = "<br>".join(f"({x:.1f}, {y:.1f}) junto a {junto_a(x, y)}" for x, y in pts)
        filas.append(f"| {ref} | `{red.lstrip('/')}` | {len(aristas)} | {largo:.0f} mm | {aguj} |")
    texto = ["# Puentes de alambre (lado de componentes)", "",
             "La PCB es de **una sola cara** (cobre abajo). Las conexiones que no caben en el cobre se hacen",
             "con alambre aislado (por ejemplo, hilo de cable UTP) del lado de los componentes. Cada puente",
             "está dibujado en la serigrafía como una línea recta con su nombre `JPn`.", "",
             "- Instalar todos los puentes **antes** que los componentes: algunos pasan por debajo del ESP32.",
             "- Cortar el alambre unos 6 mm más largo que la medida, doblar las puntas y soldar por el cobre.",
             "- Si un puente tiene más de dos agujeros, se hace con varios tramos (todos son la misma red).", "",
             "Coordenadas en mm desde la esquina superior izquierda de la placa, vista desde los componentes.", "",
             f"Total: **{len(lista)} puentes, {total} alambres**.", "",
             "| Puente | Red | Alambres | Largo aprox. | Agujeros |", "|---|---|---|---|---|"] + filas
    os.makedirs(os.path.join(HW, "fabricacion"), exist_ok=True)
    open(os.path.join(HW, "fabricacion", "PUENTES.md"), "w", encoding="utf-8").write("\n".join(texto) + "\n")


def lugar_libre(b, w, h, margen=1.0):
    """Rectángulo de w × h mm sin cobre en B.Cu, lo más centrado posible (para el texto)."""
    obst = []
    for t in b.GetTracks():
        a, z, r = t.GetStart(), t.GetEnd(), ToMM(t.GetWidth()) / 2 + margen
        (x1, y1), (x2, y2) = (ToMM(a.x), ToMM(a.y)), (ToMM(z.x), ToMM(z.y))
        pasos = max(1, int(max(abs(x2 - x1), abs(y2 - y1)) / 0.3))
        for k in range(pasos + 1):
            x, y = x1 + (x2 - x1) * k / pasos, y1 + (y2 - y1) * k / pasos
            obst.append((x - r, y - r, x + r, y + r))
    for f in b.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox()
            obst.append((ToMM(bb.GetLeft()) - margen, ToMM(bb.GetTop()) - margen,
                         ToMM(bb.GetRight()) + margen, ToMM(bb.GetBottom()) + margen))
    mejor = None
    for yi in range(int((H - h - 8) / 0.5)):
        for xi in range(int((W - w - 8) / 0.5)):
            x0, y0 = 4 + xi * 0.5, 4 + yi * 0.5
            x1, y1 = x0 + w, y0 + h
            if not any(a < x1 and x0 < c and q < y1 and y0 < d for a, q, c, d in obst):
                cx, cy = x0 + w / 2, y0 + h / 2
                puntaje = (cx - W / 2) ** 2 + (cy - H / 2) ** 2
                if mejor is None or puntaje < mejor[0]:
                    mejor = (puntaje, cx, cy)
    return None if mejor is None else mejor[1:]


def texto_cobre(b):
    """Texto en espejo en B.Cu: en el papel de tóner se lee al revés y en la placa al derecho."""
    for msg, tam in TEXTO_COBRE:
        lineas = msg.split("\n")
        lugar = lugar_libre(b, max(len(l) for l in lineas) * tam * 0.95, len(lineas) * tam * 1.7, 0.7)
        if lugar:
            break
    else:
        print("AVISO: no hay espacio para el texto de cobre")
        return
    t = pcbnew.PCB_TEXT(b)
    t.SetText(msg)
    t.SetLayer(pcbnew.B_Cu)
    t.SetMirrored(True)
    t.SetTextSize(VECTOR2I(MM(tam), MM(tam)))
    t.SetTextThickness(MM(tam * 0.18))
    t.SetPosition(VECTOR2I(MM(lugar[0]), MM(lugar[1])))
    b.Add(t)


def relleno_gnd(b):
    z = pcbnew.ZONE(b)
    z.SetLayer(pcbnew.B_Cu)
    z.SetNet(b.FindNet("GND"))
    o = z.Outline()
    o.NewOutline()
    for x, y in ((1, 1), (W - 1, 1), (W - 1, H - 1), (1, H - 1)):
        o.Append(MM(OX + x), MM(OY + y))
    z.SetLocalClearance(MM(0.8))
    z.SetMinThickness(MM(0.6))
    z.SetThermalReliefGap(MM(0.6))
    z.SetThermalReliefSpokeWidth(MM(1.0))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z)
    # sin cobre de relleno bajo la antena del módulo ESP32-WROOM (el extremo de arriba del DevKitC)
    k = pcbnew.ZONE(b)
    k.SetIsRuleArea(True)
    k.SetDoNotAllowZoneFills(True)
    k.SetDoNotAllowTracks(False)
    k.SetDoNotAllowVias(False)
    k.SetDoNotAllowPads(False)
    k.SetDoNotAllowFootprints(False)
    k.SetLayer(pcbnew.B_Cu)
    o = k.Outline()
    o.NewOutline()
    for x, y in ((U1X - 1.5, U1Y - 12), (U1X + 26.9, U1Y - 12), (U1X + 26.9, U1Y + 3), (U1X - 1.5, U1Y + 3)):
        o.Append(MM(OX + x), MM(OY + y))
    b.Add(k)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def exportar_conectores(b):
    """Posición de los conectores y agujeros (mm, origen en la esquina superior izquierda, vista
    desde los componentes, y hacia abajo) para que el modelo de FreeCAD lleve los cables a su sitio."""
    out = {"placa": {"ancho": W, "alto": H, "espesor": 1.6},
           "agujeros_m3": [[x, y] for x, y in AGUJEROS], "conectores": {}}
    for f in b.GetFootprints():
        ref = f.GetReference()
        if ref.startswith(("J", "SW", "D8")) or ref == "U1":
            pads = {p.GetNumber(): [round(ToMM(p.GetPosition().x) - OX, 2), round(ToMM(p.GetPosition().y) - OY, 2)]
                    for p in f.Pads()}
            out["conectores"][ref] = {"valor": f.GetValue(), "pads": pads}
    json.dump(out, open(CONECTORES, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def terminar(b):
    texto_cobre(b)
    desp = VECTOR2I(MM(OX), MM(OY))
    for it in list(b.GetFootprints()) + list(b.GetTracks()) + list(b.GetDrawings()):
        it.Move(desp)
    ds = b.GetDesignSettings()
    # reglas finales (Freerouting deja algunos pasos a 0,45–0,5 mm)
    ds.m_MinClearance = MM(0.45)
    ds.m_TrackMinWidth = MM(0.45)
    ds.m_CopperEdgeClearance = MM(0.4)
    for nc in (ds.m_NetSettings.GetDefaultNetclass(), ds.m_NetSettings.GetNetClassByName("Alimentacion")):
        nc.SetClearance(MM(0.45))
    ds.SetAuxOrigin(desp)
    ds.SetGridOrigin(desp)
    relleno_gnd(b)
    exportar_conectores(b)


def escribir_proyecto():
    ruta = os.path.join(HW, "medidor-energia.kicad_pro")
    pro = json.load(open(ruta, encoding="utf-8"))
    pro.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rule_severities", {}).update(SEVERIDADES)
    json.dump(pro, open(ruta, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "importar"
    b = construir()
    reportar_solapes(b)
    puentes = []
    if modo == "rutear":
        rutear(b)
    elif modo == "importar":
        if not pcbnew.ImportSpecctraSES(b, SES):
            raise SystemExit("no hay sesión de Freerouting guardada; usar «rutear»")
    if modo in ("rutear", "importar"):
        puentes = hacer_puentes(b)
    b.Save(SALIDA)
    # el relleno falla sobre una placa recién creada en memoria: se recarga desde el archivo
    b = pcbnew.LoadBoard(SALIDA)
    terminar(b)
    b.Save(SALIDA)
    escribir_proyecto()
    if puentes:
        escribir_puentes(puentes)
    print("PCB guardada:", SALIDA)


if __name__ == "__main__":
    main()
