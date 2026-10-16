#!/usr/bin/env python3
"""Genera la placa de KiCad del medidor (../hardware/medidor-energia.kicad_pcb) a partir de:

- la netlist que KiCad exporta del esquemático (../hardware/medidor-energia.net), y
- la distribución en placa perforada de placa_perforada.py (columna, fila de cada pin, pistas
  de estaño y puentes), ya verificada contra esa misma netlist.

La placa reproduce la placa perforada real de 150 × 90 mm (59 × 35 agujeros, paso 2,54 mm):

- cada componente es la huella de la biblioteca oficial de KiCad, con su modelo 3D, colocada
  de modo que cada pin cae en su agujero;
- los agujeros libres son pads sin red de una huella «solo de placa» (la rejilla perforada);
- las pistas de estaño son pistas de cobre en la cara inferior (B.Cu);
- los puentes de cable aislado son huellas «solo de placa» con dos pads unidos como puente
  (jumper pad group), dibujados en la serigrafía superior.

Se ejecuta con el Python de KiCad (módulo pcbnew):

    python3 generar_pcb.py
    kicad-cli pcb drc --schematic-parity -o ../hardware/drc.rpt ../hardware/medidor-energia.kicad_pcb
"""
import json
import os
import sys

import pcbnew

import placa_perforada as pp
from sexpr import Sym, dump, find, find1, parse

AQUI = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(AQUI, "..", "hardware"))
NET = os.path.join(HW, "medidor-energia.net")
SALIDA = os.path.join(HW, "medidor-energia.kicad_pcb")
FP = "/usr/share/kicad/footprints"
M3D = "${KICAD10_3DMODEL_DIR}"

# Placa de 150 × 90 mm con la rejilla centrada
X0, Y0, ANCHO, ALTO = 100.0, 100.0, 150.0, 90.0
PASO = 2.54
MX = (ANCHO - (pp.COLS - 1) * PASO) / 2
MY = (ALTO - (pp.FILAS - 1) * PASO) / 2
PAD_PERF, TALADRO_PERF = 1.7, 1.0      # pad y taladro de la placa perforada comercial


def mm(v):
    return pcbnew.FromMM(v)


def agujero(c, f):
    return X0 + MX + c * PASO, Y0 + MY + f * PASO


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


# Huella de biblioteca según el tipo de pieza y la separación entre pines (en pasos de 2,54 mm).
def huella_para(tipo, pasos):
    tabla = {
        ("res", 4): "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
        ("res_v", 2): "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical",
        ("res_v", 3): "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
        ("disco", 1): "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm",
        ("disco", 2): "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
        ("disco", 3): "Capacitor_THT:C_Disc_D7.5mm_W5.0mm_P7.50mm",
        ("electro8", 2): "Capacitor_THT:CP_Radial_D8.0mm_P5.00mm",
        ("electro5", 2): "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm",
        ("diodo35", 2): "Diode_THT:D_DO-35_SOD27_P5.08mm_Vertical_AnodeUp",
        ("diodo35", 3): "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
        ("diodo41", 4): "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
        ("ptc", 2): "Fuse:Fuse_BelFuse_0ZRE0040FF_L11.5mm_W3.8mm",   # PTC radial con modelo 3D
        ("borne2", 2): "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
        ("borne3", 2): "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal",
        ("hembra4v", 1): "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
        ("macho2v", 1): "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    }
    return tabla[(tipo, pasos)]


def leer_netlist():
    t = parse(open(NET, encoding="utf-8").read())[0]
    comps = {}
    for c in find(find1(t, "components"), "comp"):
        comps[find1(c, "ref")[1]] = {"valor": find1(c, "value")[1], "uuid": find1(c, "tstamps")[1]}
    red_de_pin = {}
    redes = []
    for n in find(find1(t, "nets"), "net"):
        nombre = find1(n, "name")[1]
        redes.append(nombre)
        for x in find(n, "node"):
            red_de_pin[(find1(x, "ref")[1], find1(x, "pin")[1])] = nombre
    return comps, redes, red_de_pin


class Placa:
    def __init__(self):
        self.b = pcbnew.NewBoard(SALIDA)
        self.redes = {}

    def red(self, nombre):
        if nombre is None:
            return None
        if nombre not in self.redes:
            n = pcbnew.NETINFO_ITEM(self.b, nombre)
            self.b.Add(n)
            self.redes[nombre] = n
        return self.redes[nombre]

    def contorno(self):
        s = pcbnew.PCB_SHAPE(self.b)
        s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetStart(vec(X0, Y0))
        s.SetEnd(vec(X0 + ANCHO, Y0 + ALTO))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        self.b.Add(s)

    def pista(self, a, b, nombre, ancho=1.0):
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(vec(*a))
        t.SetEnd(vec(*b))
        t.SetWidth(mm(ancho))
        t.SetLayer(pcbnew.B_Cu)
        t.SetNet(self.red(nombre))
        self.b.Add(t)
        # Sin máscara encima: en la placa perforada la pista es estaño a la vista.
        m = pcbnew.PCB_SHAPE(self.b)
        m.SetShape(pcbnew.SHAPE_T_SEGMENT)
        m.SetStart(vec(*a))
        m.SetEnd(vec(*b))
        m.SetLayer(pcbnew.B_Mask)
        m.SetWidth(mm(ancho + 0.2))
        self.b.Add(m)

    def texto_fp(self, fp, ref, valor, uuid, lib_id):
        fp.SetReference(ref)
        fp.SetValue(valor)
        lib, nombre = lib_id.split(":")
        fp.SetFPID(pcbnew.LIB_ID(lib, nombre))
        if uuid:
            fp.SetPath(pcbnew.KIID_PATH(f"/{uuid}"))
            fp.SetSheetname("")
            fp.SetSheetfile("medidor-energia.kicad_sch")


def pad_tht(fp, numero, x, y, diam=PAD_PERF, taladro=TALADRO_PERF, cuadrado=False):
    p = pcbnew.PAD(fp)
    p.SetNumber(numero)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetShape(pcbnew.PAD_SHAPE_RECT if cuadrado else pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(vec(diam, diam))
    p.SetDrillSize(vec(taladro, taladro))
    p.SetLayerSet(pcbnew.PAD.PTHMask())
    fp.Add(p)
    p.SetPosition(vec(x, y))
    return p


def modelo(fp, ruta, dx=0.0, dy=0.0, dz=0.0, rz=0.0):
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = ruta
    m.m_Offset = pcbnew.VECTOR3D(dx, dy, dz)
    m.m_Rotation = pcbnew.VECTOR3D(0, 0, rz)
    m.m_Scale = pcbnew.VECTOR3D(1, 1, 1)
    fp.Add3DModel(m)


def colocar_biblioteca(placa, ref, lib_id, pines, comps, red_de_pin):
    """Carga la huella y la gira y traslada para que cada pad caiga en su agujero."""
    lib, nombre = lib_id.split(":")
    destino = {n: agujero(*cf) for n, cf in pines.items()}
    mejor = None
    for ang in (0, 90, 180, 270):
        fp = pcbnew.FootprintLoad(os.path.join(FP, lib + ".pretty"), nombre)
        fp.SetOrientationDegrees(ang)
        p1 = [p for p in fp.Pads() if p.GetNumber() == "1" or p.GetNumber() in destino][0]
        n1 = p1.GetNumber()
        ax, ay = destino[n1]
        pos = p1.GetPosition()
        fp.SetPosition(vec(ax - pcbnew.ToMM(pos.x), ay - pcbnew.ToMM(pos.y)))
        err = 0.0
        for p in fp.Pads():
            if p.GetNumber() in destino:
                q = p.GetPosition()
                tx, ty = destino[p.GetNumber()]
                err += abs(pcbnew.ToMM(q.x) - tx) + abs(pcbnew.ToMM(q.y) - ty)
        if mejor is None or err < mejor[0]:
            mejor = (err, ang, fp)
    err, ang, fp = mejor
    placa.b.Add(fp)
    # Ajuste fino: en la placa perforada las patas se doblan al paso de 2,54 mm.
    desplaz = []
    for p in fp.Pads():
        n = p.GetNumber()
        if n in destino:
            antes = p.GetFPRelativePosition()
            p.SetPosition(vec(*destino[n]))
            despues = p.GetFPRelativePosition()
            desplaz.append((pcbnew.ToMM(despues.x - antes.x), pcbnew.ToMM(despues.y - antes.y)))
        p.SetNet(placa.red(red_de_pin.get((ref, n))))
    if desplaz:
        dx = sum(d[0] for d in desplaz) / len(desplaz)
        dy = sum(d[1] for d in desplaz) / len(desplaz)
        for m in fp.Models():
            # El desplazamiento del modelo usa Y hacia arriba.
            m.m_Offset = pcbnew.VECTOR3D(m.m_Offset.x + dx, m.m_Offset.y - dy, m.m_Offset.z)
    c = comps[ref]
    placa.texto_fp(fp, ref, c["valor"], c["uuid"], lib_id)
    return fp, max((abs(d[0]) + abs(d[1]) for d in desplaz), default=0)


def huella_esp32(placa, pines, comps, red_de_pin):
    fp = pcbnew.FOOTPRINT(placa.b)
    x1, y1 = agujero(*pines["1"])
    fp.SetPosition(vec(x1, y1))
    placa.b.Add(fp)
    for n, cf in pines.items():
        x, y = agujero(*cf)
        p = pad_tht(fp, n, x, y, 1.7, 1.0, cuadrado=(n == "1"))
        p.SetNet(placa.red(red_de_pin.get(("U1", n))))
    # Los tres GND de la tarjeta están unidos por su plano de tierra.
    # (el grupo de puente se agrega al guardar: ver PUENTES_INTERNOS)
    fp.SetAttributes(pcbnew.FP_THROUGH_HOLE)
    sock = f"{M3D}/Connector_PinSocket_2.54mm.3dshapes/PinSocket_1x19_P2.54mm_Vertical.step"
    modelo(fp, sock)
    modelo(fp, sock, dx=10 * PASO)
    modelo(fp, "${KIPRJMOD}/3d/esp32-devkitc-v4.wrl")
    # Módulo ESP32-WROOM-32 oficial sobre la tarjeta (su borde de antena 4,3 mm antes del pin 1).
    modelo(fp, f"{M3D}/RF_Module.3dshapes/ESP32-WROOM-32.step", dx=5 * PASO, dy=-(15.86 - 4.3),
           dz=8.5 + 2.5 + 1.6)
    # Contorno de la tarjeta en la serigrafía y en el patio
    for capa, ancho in ((pcbnew.F_SilkS, 0.15), (pcbnew.F_CrtYd, 0.05)):
        s = pcbnew.PCB_SHAPE(fp)
        s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetStart(vec(x1 - 1.3, y1 - 4.28))
        s.SetEnd(vec(x1 + 26.7, y1 + 18 * PASO + 4.28 + 1.0))
        s.SetLayer(capa)
        s.SetWidth(mm(ancho))
        fp.Add(s)
    c = comps["U1"]
    placa.texto_fp(fp, "U1", c["valor"], c["uuid"], "Medidor:ESP32-DevKitC-38_Zocalo")
    fp.Reference().SetPosition(vec(x1 + 12.7, y1 + 9))
    fp.Value().SetPosition(vec(x1 + 12.7, y1 + 30))
    fp.Value().SetVisible(False)
    return fp


def huella_cables_jack(placa, ref, pines, comps, red_de_pin):
    """J2 y J3: puntos de soldadura del cable que va al jack de panel (la resistencia de carga
    va soldada en el propio jack)."""
    fp = pcbnew.FOOTPRINT(placa.b)
    x, y = agujero(*pines["T"])
    fp.SetPosition(vec(x, y))
    placa.b.Add(fp)
    # El anillo (R) del jack no se usa: su hilo se suelda en el agujero entre T y S para que
    # no quede suelto dentro del gabinete.
    pines = dict(pines, R=(pines["T"][0], pines["T"][1] + 1))
    for n, cf in pines.items():
        p = pad_tht(fp, n, *agujero(*cf))
        p.SetNet(placa.red(red_de_pin.get((ref, n))))
    c = comps[ref]
    placa.texto_fp(fp, ref, c["valor"], c["uuid"], "Medidor:Cable_Jack_Panel")
    fp.Reference().SetPosition(vec(x + 3.5, y + 1.27))
    fp.Value().SetVisible(False)
    fp.SetAttributes(pcbnew.FP_THROUGH_HOLE)
    return fp


# Reglas del proyecto. Las que se relajan son propias de una placa perforada y se explican
# en el documento: la rejilla tiene agujeros bajo todos los componentes, la serigrafía cae
# sobre pads de la rejilla, y las patas se doblan al paso de 2,54 mm (la huella difiere de la
# de biblioteca solo en la posición del segundo pad).
SEVERIDADES = {
    "pth_inside_courtyard": "ignore",
    "silk_over_copper": "ignore",
    "silk_overlap": "ignore",
    "lib_footprint_mismatch": "ignore",
}


def escribir_proyecto():
    ruta = os.path.join(HW, "medidor-energia.kicad_pro")
    try:
        pro = json.load(open(ruta, encoding="utf-8"))
    except (OSError, ValueError):
        pro = {}
    ds = pro.setdefault("board", {}).setdefault("design_settings", {})
    ds.setdefault("rule_severities", {}).update(SEVERIDADES)
    ds.setdefault("rules", {}).update({"min_copper_edge_clearance": 0.3, "min_track_width": 0.5,
                                        "min_clearance": 0.2})
    pro.setdefault("meta", {"filename": "medidor-energia.kicad_pro", "version": 3})
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(pro, f, indent=2, ensure_ascii=False)
    with open(os.path.join(HW, "fp-lib-table"), "w", encoding="utf-8") as f:
        f.write('(fp_lib_table\n  (version 7)\n  (lib (name "Medidor")(type "KiCad")'
                '(uri "${KIPRJMOD}/Medidor.pretty")(options "")(descr "Huellas propias del medidor"))\n)\n')


def guardar_biblioteca(placa):
    """Guarda las huellas propias en Medidor.pretty para que el proyecto sea editable en KiCad."""
    lib = os.path.join(HW, "Medidor.pretty")
    os.makedirs(lib, exist_ok=True)
    hechas = set()
    for fp in placa.b.GetFootprints():
        fpid = fp.GetFPID()
        if str(fpid.GetLibNickname()) != "Medidor" or str(fpid.GetLibItemName()) in hechas:
            continue
        copia = fp.Duplicate(False) if hasattr(fp, "Duplicate") else fp
        copia = pcbnew.Cast_to_FOOTPRINT(copia) if not isinstance(copia, pcbnew.FOOTPRINT) else copia
        copia.SetOrientationDegrees(0)
        copia.SetPosition(pcbnew.VECTOR2I(0, 0))
        for p in copia.Pads():
            p.SetNetCode(0)
        copia.SetReference(copia.GetReference().rstrip("0123456789") or "REF")
        pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave(lib, copia)
        hechas.add(str(fpid.GetLibItemName()))


def agregar_grupos_de_puente():
    """La API de Python no expone los grupos de pads puente; se escriben en el archivo.

    U1 une sus tres GND por el plano de tierra de la tarjeta y cada puente de cable une sus
    dos extremos. KiCad los trata como conectados al calcular la conectividad.
    """
    texto = open(SALIDA, encoding="utf-8").read()
    arbol = parse(texto)[0]
    for fp in find(arbol, "footprint"):
        ref = next((x[2] for x in find(fp, "property") if x[1] == "Reference"), "")
        if ref == "U1":
            fp.append([Sym("jumper_pad_groups"), ["14", "20", "26"]])
        elif ref.startswith("W") and ref[1:].isdigit():
            fp.append([Sym("jumper_pad_groups"), ["1", "2"]])
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(dump(arbol) + "\n")


def main():
    pp.definir()
    errores, grupo_de_red, uf, n_redes = pp.verificar(NET)
    if errores:
        raise SystemExit("La placa perforada no coincide con la netlist:\n" + "\n".join(errores))
    comps, redes, red_de_pin = leer_netlist()
    placa = Placa()
    for r in redes:
        placa.red(r)
    placa.contorno()

    ocupados = set()
    estiradas = {}
    huellas = {}
    for ref, tipo, pines, _ in pp.PIEZAS:
        ocupados |= set(pines.values())
        if tipo == "panel":
            ocupados.add((pines["T"][0], pines["T"][1] + 1))
        if tipo == "esp32":
            huella_esp32(placa, pines, comps, red_de_pin)
            huellas[ref] = "Medidor:ESP32-DevKitC-38_Zocalo"
            continue
        if tipo == "panel":
            huella_cables_jack(placa, ref, pines, comps, red_de_pin)
            huellas[ref] = "Medidor:Cable_Jack_Panel"
            continue
        pts = sorted(pines.values())
        pasos = max(abs(pts[-1][0] - pts[0][0]), abs(pts[-1][1] - pts[0][1])) // (len(pts) - 1)
        lib_id = huella_para(tipo, pasos)
        _, d = colocar_biblioteca(placa, ref, lib_id, pines, comps, red_de_pin)
        huellas[ref] = lib_id
        if d > 0.01:
            estiradas[ref] = round(d, 2)

    # Red de cada agujero usado por una pista o un puente
    def red_de(xy):
        nombre = grupo_de_red.get(uf.f(xy))
        if nombre is None:
            return None
        return next((r for r in redes if r.lstrip("/") == nombre), nombre)

    usados = {x for a, b in pp.PISTAS for x in pp.agujeros_de_pista(a, b)}
    usados |= {x for a, b, _ in pp.PUENTES for x in (a, b)}

    # Rejilla de la placa perforada: un pad por cada agujero que no ocupa un componente
    perf = pcbnew.FOOTPRINT(placa.b)
    perf.SetPosition(vec(*agujero(0, 0)))
    placa.b.Add(perf)
    for c in range(pp.COLS):
        for f in range(pp.FILAS):
            if (c, f) in ocupados:
                continue
            p = pad_tht(perf, "", *agujero(c, f))
            if (c, f) in usados:
                p.SetNet(placa.red(red_de((c, f))))
    perf.SetReference("PERF1")
    perf.SetValue("Placa perforada 9 × 15 cm, 59 × 35 agujeros")
    perf.Reference().SetVisible(False)
    perf.Value().SetVisible(False)
    perf.SetFPID(pcbnew.LIB_ID("Medidor", "Placa_Perforada_59x35"))
    perf.SetBoardOnly(True)
    perf.SetExcludedFromBOM(True)
    perf.SetExcludedFromPosFiles(True)

    # Pistas de estaño (cara inferior)
    for a, b in pp.PISTAS:
        placa.pista(agujero(*a), agujero(*b), red_de(a))

    # Puentes de cable aislado (cara superior): dos pads unidos como puente
    for k, (a, b, clase) in enumerate(pp.PUENTES, 1):
        fp = pcbnew.FOOTPRINT(placa.b)
        fp.SetPosition(vec(*agujero(*a)))
        placa.b.Add(fp)
        for n, cf in (("1", a), ("2", b)):
            p = pcbnew.PAD(fp)
            p.SetNumber(n)
            p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            p.SetSize(vec(0.9, 0.9))
            ls = pcbnew.LSET()
            ls.AddLayer(pcbnew.F_Cu)
            p.SetLayerSet(ls)
            fp.Add(p)
            p.SetPosition(vec(*agujero(*cf)))
            p.SetNet(placa.red(red_de(a)))
        s = pcbnew.PCB_SHAPE(fp)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(vec(*agujero(*a)))
        s.SetEnd(vec(*agujero(*b)))
        s.SetLayer(pcbnew.F_SilkS)
        s.SetWidth(mm(0.5))
        fp.Add(s)
        fp.SetReference(f"W{k}")
        fp.SetValue(f"Puente {clase}")
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetFPID(pcbnew.LIB_ID("", f"Puente_Cable_{k}"))
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_SMD)

    ds = placa.b.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.5)
    ds.m_MinClearance = mm(0.2)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.SetBoardThickness(mm(1.6))
    guardar_biblioteca(placa)
    pcbnew.SaveBoard(SALIDA, placa.b)
    agregar_grupos_de_puente()
    escribir_proyecto()
    with open(os.path.join(HW, "3d", "huellas.json"), "w") as f:
        json.dump({"huellas": huellas, "patas_ajustadas_mm": estiradas}, f, indent=1, ensure_ascii=False)
    print(f"Placa escrita en {SALIDA}: {len(huellas)} componentes, {len(pp.PISTAS)} pistas, "
          f"{len(pp.PUENTES)} puentes, {sum(1 for _ in perf.Pads())} agujeros libres de la rejilla")


if __name__ == "__main__":
    main()
