#!/usr/bin/env python3
"""Genera el esquemático KiCad del medidor de energía (ESP32 + 2 canales de corriente
+ 1 canal de tensión) en ../hardware/medidor-energia.kicad_sch.

Cada coordenada está en milímetros sobre la grilla de 1,27 mm de KiCad. Las conexiones
se dibujan con cables entre pines y con etiquetas locales entre bloques. Después de
generar el archivo se verifica con:

    kicad-cli sch erc ../hardware/medidor-energia.kicad_sch
"""
import math
import os
import uuid as _uuid
from collections import Counter

from sexpr import Sym, dump, find, find1, parse

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "..", "hardware", "medidor-energia.kicad_sch")
LIBS = "/usr/share/kicad/symbols/"
PROYECTO = "medidor-energia"

# Identificadores deterministas: el archivo no cambia si el script se vuelve a correr.
_ns = _uuid.UUID("6f1d2c3e-0000-4000-8000-000000000000")
_cont = Counter()


def uid(tag="x"):
    _cont[tag] += 1
    return str(_uuid.uuid5(_ns, f"{tag}-{_cont[tag]}"))


RAIZ = uid("raiz")
S = Sym

# Huellas reales de la placa de KiCad (generar_pcb.py las escribe al ubicar cada pieza en su
# agujero) y piezas que no van en la placa perforada: R1 y R2 se sueldan en los jacks del
# panel; U2, J4 y F1 están en el compartimento de red.
_RUTA_HUELLAS = os.path.join(AQUI, "..", "hardware", "3d", "huellas.json")
HUELLAS = {}
if os.path.exists(_RUTA_HUELLAS):
    import json
    HUELLAS = json.load(open(_RUTA_HUELLAS, encoding="utf-8"))["huellas"]
FUERA_DE_PLACA = {"R1", "R2", "U2", "J4", "F1"}


def r(v):
    return round(v, 4)


# ---------------------------------------------------------------- símbolos de biblioteca
def cargar(lib, nombre):
    arbol = parse(open(LIBS + lib + ".kicad_sym", encoding="utf-8").read())[0]
    for s in find(arbol, "symbol"):
        if s[1] == nombre:
            if find1(s, "extends"):
                raise SystemExit(f"{lib}:{nombre} usa extends; no soportado")
            s = list(s)
            s[1] = f"{lib}:{nombre}"
            return s
    raise SystemExit(f"No existe {lib}:{nombre}")


def pines_de(simbolo):
    pines = {}

    def recorrer(n):
        for x in n:
            if isinstance(x, list) and x:
                if x[0] == "pin":
                    at = find1(x, "at")
                    num = find1(x, "number")[1]
                    pines[num] = (float(at[1]), float(at[2]))
                else:
                    recorrer(x)

    recorrer(simbolo)
    return pines


def efectos(tam=1.27, oculto=False, just=None):
    e = [S("effects"), [S("font"), [S("size"), tam, tam]]]
    if just:
        e.append([S("justify")] + [S(j) for j in just.split()])
    if oculto:
        e.append([S("hide"), S("yes")])
    return e


def pin_def(tipo, x, y, ang, nombre, numero, largo=5.08):
    return [S("pin"), S(tipo), S("line"), [S("at"), x, y, ang], [S("length"), largo],
            [S("name"), nombre, efectos()], [S("number"), numero, efectos()]]


def prop(nombre, valor, x, y, ang=0, oculto=False, just=None):
    return [S("property"), nombre, valor, [S("at"), r(x), r(y), ang], efectos(oculto=oculto, just=just)]


def simbolo_propio(nombre, ref, valor, graficos, pines, y_ref, y_val, desc=""):
    corto = nombre.split(":")[1]
    return [S("symbol"), nombre, [S("pin_names"), [S("offset"), 1.016]],
            [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
            prop("Reference", ref, 0, y_ref), prop("Value", valor, 0, y_val),
            prop("Footprint", "", 0, 0, oculto=True), prop("Datasheet", "", 0, 0, oculto=True),
            prop("Description", desc, 0, 0, oculto=True),
            [S("symbol"), f"{corto}_0_1"] + graficos,
            [S("symbol"), f"{corto}_1_1"] + pines]


def rect(x1, y1, x2, y2, ancho=0.254, tipo="default", relleno="background"):
    return [S("rectangle"), [S("start"), x1, y1], [S("end"), x2, y2],
            [S("stroke"), [S("width"), ancho], [S("type"), S(tipo)]], [S("fill"), [S("type"), S(relleno)]]]


def polilinea(puntos, ancho=0.254, tipo="default"):
    return [S("polyline"), [S("pts")] + [[S("xy"), x, y] for x, y in puntos],
            [S("stroke"), [S("width"), ancho], [S("type"), S(tipo)]], [S("fill"), [S("type"), S("none")]]]


def texto_sim(t, x, y, tam=1.27):
    return [S("text"), t, [S("at"), x, y, 0], efectos(tam)]


# ESP32-DevKitC V4 de 38 pines: orden físico de los dos cabezales vistos desde arriba.
IZQ = ["3V3", "EN", "VP/IO36", "VN/IO39", "IO34", "IO35", "IO32", "IO33", "IO25",
       "IO26", "IO27", "IO14", "IO12", "GND", "IO13", "SD2/IO9", "SD3/IO10", "CMD/IO11", "5V"]
DER = ["GND", "IO23", "IO22", "TXD0/IO1", "RXD0/IO3", "IO21", "GND", "IO19", "IO18", "IO5",
       "IO17", "IO16", "IO4", "IO0", "IO2", "IO15", "SD1/IO8", "SD0/IO7", "CLK/IO6"]


def tipo_pin_esp(nombre):
    if nombre == "3V3":
        return "power_out"
    if nombre in ("5V", "GND"):
        return "power_in"
    if nombre in ("VP/IO36", "VN/IO39", "IO34", "IO35", "EN"):
        return "input"
    return "bidirectional"


def sim_esp32():
    pines = []
    for k, n in enumerate(IZQ):
        pines.append(pin_def(tipo_pin_esp(n), -17.78, r(22.86 - 2.54 * k), 0, n, str(k + 1)))
    for k, n in enumerate(DER):
        pines.append(pin_def(tipo_pin_esp(n), 17.78, r(22.86 - 2.54 * k), 180, n, str(k + 20)))
    graf = [rect(-12.7, 25.4, 12.7, -25.4), texto_sim("USB", 0, -23.5)]
    return simbolo_propio("Medidor:ESP32-DevKitC-38", "U", "ESP32-DevKitC-38", graf, pines,
                          27.94, -27.94, "Tarjeta ESP32-DevKitC V4 (ESP32-WROOM-32), 38 pines")


def sim_zmpt():
    pines = [pin_def("passive", -12.7, 2.54, 0, "L", "1"),
             pin_def("passive", -12.7, -2.54, 0, "N", "2"),
             pin_def("power_in", 12.7, 2.54, 180, "VCC", "3"),
             pin_def("output", 12.7, 0, 180, "OUT", "4"),
             pin_def("power_in", 12.7, -2.54, 180, "GND", "5")]
    graf = [rect(-7.62, 7.62, 7.62, -7.62),
            polilinea([(0, 7.62), (0, -7.62)], 0.254, "dash"),
            texto_sim("RED", -3.81, 5.6, 1.0), texto_sim("MBT", 3.81, 5.6, 1.0),
            texto_sim("aislado", 0, -6.2, 0.9)]
    return simbolo_propio("Medidor:ZMPT101B_Modulo", "U", "ZMPT101B", graf, pines, 10.16, -10.16,
                          "Módulo sensor de tensión con transformador ZMPT101B y amplificador LM358")


# ---------------------------------------------------------------- el esquemático
class Esquematico:
    def __init__(self):
        self.lib = {}
        self.pines_lib = {}
        self.items = []
        self.cables = []
        self.puntos_pin = []
        self.pwr_n = 0
        self.flg_n = 0

    def usar(self, lib_id, definicion=None):
        if lib_id not in self.lib:
            d = definicion or cargar(*lib_id.split(":"))
            self.lib[lib_id] = d
            self.pines_lib[lib_id] = pines_de(d)
        return self.pines_lib[lib_id]

    def colocar(self, lib_id, ref, valor, x, y, rot=0, espejo=False, huella="",
                ref_at=None, val_at=None, ocultar_valor=False, nc=()):
        pines = self.usar(lib_id)
        huella = HUELLAS.get(ref, huella)
        pos = {}
        for num, (px, py) in pines.items():
            if espejo:
                px = -px
            a = math.radians(rot)
            rx = px * math.cos(a) - py * math.sin(a)
            ry = px * math.sin(a) + py * math.cos(a)
            pos[num] = (r(x + rx), r(y - ry))
        es_power = lib_id.startswith("power:")
        ra = ref_at or (x + 3, y - 2)
        va = val_at or (x + 3, y + 2)
        just = None if es_power else ("right" if (espejo or rot in (180, 270)) else "left")
        ang_campo = 0 if es_power else (rot if rot in (90, 270) else 0)
        nodo = [S("symbol"), [S("lib_id"), lib_id], [S("at"), r(x), r(y), rot]]
        if espejo:
            nodo.append([S("mirror"), S("y")])
        nodo += [[S("unit"), 1], [S("exclude_from_sim"), S("no")], [S("in_bom"), S("no" if es_power else "yes")],
                 [S("on_board"), S("no" if ref in FUERA_DE_PLACA else "yes")], [S("dnp"), S("no")],
                 [S("uuid"), uid("sym")],
                 prop("Reference", ref, ra[0], ra[1], ang_campo, oculto=es_power, just=just),
                 prop("Value", valor, va[0], va[1], ang_campo, oculto=ocultar_valor, just=just),
                 prop("Footprint", huella, x, y, 0, oculto=True),
                 prop("Datasheet", "", x, y, 0, oculto=True)]
        for num in pines:
            nodo.append([S("pin"), num, [S("uuid"), uid("pin")]])
        nodo.append([S("instances"), [S("project"), PROYECTO,
                                      [S("path"), f"/{RAIZ}", [S("reference"), ref], [S("unit"), 1]]]])
        self.items.append(nodo)
        for num, p in pos.items():
            self.puntos_pin.append(p)
            if num in nc:
                self.no_conectar(p)
        return pos

    def power(self, nombre, x, y, rot=0):
        self.pwr_n += 1
        dy = {0: -1, 180: 1}.get(rot, 0)
        dx = {90: -1, 270: 1}.get(rot, 0)
        if nombre == "GND":
            dy, dx = -dy * 1, -dx
        ta = (x + dx * 5.2, y + dy * 3.4)
        return self.colocar(f"power:{nombre}", f"#PWR{self.pwr_n:03d}", nombre, x, y, rot,
                            ref_at=(x, y), val_at=ta)

    def bandera(self, x, y, rot=0):
        self.flg_n += 1
        return self.colocar("power:PWR_FLAG", f"#FLG{self.flg_n:02d}", "PWR_FLAG", x, y, rot,
                            ref_at=(x, y), val_at=(x, y - 4.5 if rot == 0 else y + 4.5))

    def cable(self, *puntos):
        for a, b in zip(puntos, puntos[1:]):
            a = (r(a[0]), r(a[1]))
            b = (r(b[0]), r(b[1]))
            if a != b:
                self.cables.append((a, b))

    def etiqueta(self, nombre, x, y, lado="der"):
        ang, just = (0, "left bottom") if lado == "der" else (180, "right bottom")
        self.items.append([S("label"), nombre, [S("at"), r(x), r(y), ang],
                           efectos(just=just), [S("uuid"), uid("lbl")]])

    def no_conectar(self, p):
        self.items.append([S("no_connect"), [S("at"), p[0], p[1]], [S("uuid"), uid("nc")]])

    def texto(self, t, x, y, tam=1.27, negrita=False, color=None):
        e = [S("effects"), [S("font"), [S("size"), tam, tam]] + ([[S("bold"), S("yes")]] if negrita else [])
             + ([[S("color")] + list(color) + [1]] if color else []), [S("justify"), S("left"), S("bottom")]]
        self.items.append([S("text"), t, [S("exclude_from_sim"), S("no")], [S("at"), r(x), r(y), 0], e,
                           [S("uuid"), uid("txt")]])

    def caja(self, x1, y1, x2, y2, color=(90, 90, 90), tipo="dash", ancho=0.3):
        self.items.append([S("rectangle"), [S("start"), r(x1), r(y1)], [S("end"), r(x2), r(y2)],
                           [S("stroke"), [S("width"), ancho], [S("type"), S(tipo)],
                            [S("color")] + list(color) + [1]],
                           [S("fill"), [S("type"), S("none")]], [S("uuid"), uid("rect")]])

    def _uniones(self):
        cuenta = Counter()
        for a, b in self.cables:
            cuenta[a] += 1
            cuenta[b] += 1
        for p in self.puntos_pin:
            if p in cuenta:
                cuenta[p] += 1
        uniones = {p for p, n in cuenta.items() if n >= 3}
        # extremo de cable que cae en el interior de otro cable
        for a, b in self.cables:
            for p in (a, b):
                for c, d in self.cables:
                    if p in (c, d):
                        continue
                    if c[0] == d[0] == p[0] and min(c[1], d[1]) < p[1] < max(c[1], d[1]):
                        uniones.add(p)
                    if c[1] == d[1] == p[1] and min(c[0], d[0]) < p[0] < max(c[0], d[0]):
                        uniones.add(p)
        return sorted(uniones)

    def guardar(self, ruta, titulo, papel="A3"):
        cab = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "eeschema"],
               [S("generator_version"), "9.0"], [S("uuid"), RAIZ], [S("paper"), papel],
               [S("title_block"), [S("title"), titulo[0]], [S("date"), titulo[1]], [S("rev"), titulo[2]],
                [S("company"), titulo[3]]] + [[S("comment"), i + 1, c] for i, c in enumerate(titulo[4:])],
               [S("lib_symbols")] + list(self.lib.values())]
        cuerpo = []
        for p in self._uniones():
            cuerpo.append([S("junction"), [S("at"), p[0], p[1]], [S("diameter"), 0],
                           [S("color"), 0, 0, 0, 0], [S("uuid"), uid("jn")]])
        for a, b in self.cables:
            cuerpo.append([S("wire"), [S("pts"), [S("xy"), a[0], a[1]], [S("xy"), b[0], b[1]]],
                           [S("stroke"), [S("width"), 0], [S("type"), S("default")]], [S("uuid"), uid("w")]])
        doc = cab + cuerpo + self.items + [[S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]],
                                           [S("embedded_fonts"), S("no")]]
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        # Biblioteca propia y tabla de bibliotecas para poder editar el esquemático en KiCad.
        # La biblioteca es compartida por el medidor y el banco: se conservan los símbolos
        # que ya estaban y se reemplazan los que este esquemático vuelve a definir.
        carpeta = os.path.dirname(ruta)
        ruta_lib = os.path.join(carpeta, "Medidor.kicad_sym")
        propios = {}
        if os.path.exists(ruta_lib):
            for v in find(parse(open(ruta_lib, encoding="utf-8").read())[0], "symbol"):
                propios[v[1]] = v
        for k, v in self.lib.items():
            if k.startswith("Medidor:"):
                v = list(v)
                v[1] = k.split(":")[1]
                propios[v[1]] = v
        propios = [propios[k] for k in sorted(propios)]
        with open(ruta_lib, "w", encoding="utf-8") as f:
            f.write(dump([S("kicad_symbol_lib"), [S("version"), 20241209], [S("generator"), "kicad_symbol_editor"],
                          [S("generator_version"), "9.0"]] + propios) + "\n")
        with open(os.path.join(carpeta, "sym-lib-table"), "w", encoding="utf-8") as f:
            f.write('(sym_lib_table\n  (version 7)\n  (lib (name "Medidor")(type "KiCad")'
                    '(uri "${KIPRJMOD}/Medidor.kicad_sym")(options "")(descr "Símbolos propios del medidor"))\n)\n')
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(dump(doc) + "\n")


# ---------------------------------------------------------------- huellas (placa perforada)
H_R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
H_C = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
H_CP = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
H_D = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
H_BORNE2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
H_BORNE3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal"
H_JACK = "Connector_Audio:Jack_3.5mm_CUI_SJ1-3523N_Horizontal"
H_PH4 = "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical"
H_PH8 = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
H_TP = "TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm"
H_LED3 = "LED_THT:LED_D3.0mm"


def canal_corriente(sch, n, y0, r_burden, nota_burden):
    """Canal de corriente: jack, burden, antialias RC y diodos de recorte."""
    x0 = 40.64
    jack = f"J{n + 1}"
    rb = f"R{n}"
    raa = f"R{n + 4}"
    caa = f"C{n + 4}"
    da, db = f"D{2 * n}", f"D{2 * n + 1}"
    adc = f"CH{n}_ADC"
    sch.texto(f"CANAL DE CORRIENTE CH{n}", 22.86, y0 - 13.97, 1.8, True)
    sch.texto(nota_burden, 22.86, y0 - 10.8, 1.2)
    p = sch.colocar("Connector_Audio:AudioJack3", jack, f"Jack 3,5 mm de panel (pinza SCT-013-000 CH{n})", x0, y0,
                    huella="", ref_at=(x0 - 7.62, y0 - 6.35), val_at=(x0 - 17.78, y0 + 15.24), nc=("R",))
    s, t = p["S"], p["T"]
    xb = 55.88
    pr = sch.colocar("Device:R", rb, f"{r_burden} 1% 1/4 W (burden)", xb, y0, huella="",
                     ref_at=(xb + 2.54, y0 - 0.5), val_at=(xb + 2.54, y0 + 1.8))
    yv = y0 - 6.35
    sch.cable(s, (48.26, s[1]), (48.26, yv), (xb, yv), pr["1"])
    sch.cable((xb, yv), (60.96, yv))
    sch.etiqueta("VBIAS", 60.96, yv)
    yr = y0 + 6.35
    sch.cable(t, (50.8, t[1]), (50.8, yr), (xb, yr))
    sch.cable(pr["2"], (xb, yr))
    pa = sch.colocar("Device:R", raa, "3,3k 1%", 67.31, yr, rot=90, huella=H_R,
                     ref_at=(65.4, yr - 2.0), val_at=(64.5, yr + 3.6))
    sch.cable((xb, yr), pa["1"])
    xc, xd, xf = 81.28, 96.52, 106.68
    pc = sch.colocar("Device:C", caa, "47n C0G", xc, yr + 3.81, huella=H_C,
                     ref_at=(xc + 2.54, yr + 2.54), val_at=(xc + 2.54, yr + 5.08))
    pd1 = sch.colocar("Device:D_Schottky", da, "BAT85", xd, yr - 3.81, rot=270, huella=H_D,
                      ref_at=(xd + 2.54, yr - 4.6), val_at=(xd + 2.54, yr - 2.4))
    pd2 = sch.colocar("Device:D_Schottky", db, "BAT85", xd, yr + 3.81, rot=270, huella=H_D,
                      ref_at=(xd + 2.54, yr + 3.2), val_at=(xd + 2.54, yr + 5.4))
    sch.cable(pa["2"], (xc, yr), (xd, yr), (xf, yr))
    sch.etiqueta(adc, xf, yr)
    sch.power("+3V3", xd, pd1["1"][1])
    sch.power("GND", xc, pc["2"][1])
    sch.power("GND", xd, pd2["2"][1])


def construir():
    sch = Esquematico()
    sch.usar("Medidor:ESP32-DevKitC-38", sim_esp32())
    sch.usar("Medidor:ZMPT101B_Modulo", sim_zmpt())

    # ---------------- alimentación
    sch.texto("ALIMENTACIÓN 5 V (adaptador externo aislado 100–240 V CA / 5 V 2 A)", 22.86, 38.1, 1.8, True)
    j1 = sch.colocar("Connector:Screw_Terminal_01x02", "J1", "Bornera 5 V", 30.48, 50.8, espejo=True,
                     huella=H_BORNE2, ref_at=(25.4, 46.99), val_at=(22.86, 64.77))
    f2 = sch.colocar("Device:Polyfuse", "F2", "PTC 1,1 A (MF-R110)", 45.72, 50.8, rot=90,
                     huella="Fuse:Fuse_Bourns_MF-RG1100", ref_at=(44.0, 47.5), val_at=(40.0, 45.0))
    d1 = sch.colocar("Device:D_Schottky", "D1", "1N5819", 60.96, 50.8, rot=180,
                     huella="Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", ref_at=(58.42, 46.99),
                     val_at=(57.15, 55.88))
    sch.cable(j1["1"], f2["1"])
    sch.cable(f2["2"], d1["2"])
    c1 = sch.colocar("Device:C_Polarized", "C1", "470u 10V", 74.93, 55.88, huella=H_CP,
                     ref_at=(77.47, 54.61), val_at=(77.47, 57.15))
    c2 = sch.colocar("Device:C", "C2", "100n", 87.63, 55.88, huella=H_C,
                     ref_at=(90.17, 54.61), val_at=(90.17, 57.15))
    sch.cable(d1["1"], (69.85, 50.8), (74.93, 50.8), (87.63, 50.8), (97.79, 50.8))
    sch.cable((74.93, 50.8), c1["1"])
    sch.cable((87.63, 50.8), c2["1"])
    sch.bandera(69.85, 50.8)
    sch.power("+5V", 97.79, 50.8)
    sch.power("GND", 74.93, c1["2"][1])
    sch.power("GND", 87.63, c2["2"][1])
    sch.cable(j1["2"], (38.1, j1["2"][1]), (38.1, 55.88), (38.1, 60.96))
    sch.power("GND", 38.1, 60.96)
    sch.bandera(38.1, 55.88, rot=270)
    sch.items[-1][[i for i, x in enumerate(sch.items[-1]) if isinstance(x, list) and x[:2] == [S("property"), "Value"]][0]][3] = [S("at"), 41.5, 56.6, 0]
    sch.texto("D1 bloquea polaridad invertida y evita que el USB del\nDevKitC alimente hacia atrás el adaptador.",
              22.86, 69.85, 1.1)

    # ---------------- canales de corriente
    canal_corriente(sch, 1, 101.6, "22", "total del tablero, 0–60 A, burden 22 Ω")
    canal_corriente(sch, 2, 147.32, "47", "subcircuito, 0–30 A, burden 47 Ω")

    # ---------------- polarización
    sch.texto("POLARIZACIÓN VBIAS = 1,32 V", 139.7, 87.63, 1.8, True)
    xr = 149.86
    sch.power("+3V3", xr, 95.25)
    r3 = sch.colocar("Device:R", "R3", "15k 1%", xr, 101.6, huella=H_R,
                     ref_at=(xr + 2.54, 100.33), val_at=(xr + 2.54, 102.87))
    r4 = sch.colocar("Device:R", "R4", "10k 1%", xr, 111.76, huella=H_R,
                     ref_at=(xr + 2.54, 110.49), val_at=(xr + 2.54, 113.03))
    sch.cable((xr, 95.25), r3["1"])
    sch.cable(r3["2"], (xr, 107.95), r4["1"])
    sch.power("GND", xr, r4["2"][1])
    c7 = sch.colocar("Device:C_Polarized", "C7", "10u 16V", xr + 12.7, 111.76, huella="Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
                     ref_at=(xr + 15.24, 110.49), val_at=(xr + 15.24, 113.03))
    c8 = sch.colocar("Device:C", "C8", "100n", xr + 27.94, 111.76, huella=H_C,
                     ref_at=(xr + 30.48, 110.49), val_at=(xr + 30.48, 113.03))
    sch.cable((xr - 7.62, 107.95), (xr, 107.95), (xr + 12.7, 107.95), (xr + 27.94, 107.95))
    sch.cable((xr + 12.7, 107.95), c7["1"])
    sch.cable((xr + 27.94, 107.95), c8["1"])
    sch.etiqueta("VBIAS", xr - 7.62, 107.95, "izq")
    sch.power("GND", xr + 12.7, c7["2"][1])
    sch.power("GND", xr + 27.94, c8["2"][1])
    sch.texto("La corriente de la pinza circula solo por el burden;\nVBIAS solo ve la corriente de entrada del ADC,\npor eso un divisor sirve a los dos canales.",
              139.7, 127.0, 1.1)

    # ---------------- canal de tensión
    sch.texto("CANAL DE TENSIÓN", 22.86, 190.5, 1.8, True)
    sch.caja(17.78, 194.31, 73.66, 233.68, color=(200, 0, 0))
    sch.texto("ZONA DE RED 120 V CA — fuera de la placa perforada\n(compartimento aislado del gabinete)", 19.05, 199.39, 1.1,
              color=(200, 0, 0))
    j4 = sch.colocar("Connector:Screw_Terminal_01x02", "J4", "Bornera red L/N", 30.48, 210.82, espejo=True,
                     huella=H_BORNE2, ref_at=(25.4, 207.01), val_at=(20.32, 222.25))
    sch.texto("L", 36.6, 209.8, 1.1)
    sch.texto("N", 36.6, 212.3, 1.1)
    f1 = sch.colocar("Device:Fuse", "F1", "T 500 mA 250 V", 45.72, 210.82, rot=90,
                     huella="Fuse:Fuseholder_Clip-5x20mm_Keystone_3517_Inline_P23.11x6.76mm_D1.70mm_Horizontal",
                     ref_at=(44.0, 207.5), val_at=(40.0, 205.0))
    u2 = sch.colocar("Medidor:ZMPT101B_Modulo", "U2", "Módulo ZMPT101B", 73.66, 213.36,
                     ref_at=(76.2, 203.2), val_at=(60.96, 226.06))
    sch.cable(j4["1"], f1["1"])
    sch.cable(f1["2"], u2["1"])
    sch.cable(j4["2"], (55.88, j4["2"][1]), (55.88, u2["2"][1]), u2["2"])
    sch.cable(u2["3"], (91.44, u2["3"][1]))
    sch.power("+5V", 91.44, u2["3"][1])
    sch.cable(u2["4"], (93.98, u2["4"][1]))
    sch.etiqueta("ZMPT_OUT", 93.98, u2["4"][1])
    sch.cable(u2["5"], (88.9, u2["5"][1]), (88.9, 220.98))
    sch.power("GND", 88.9, 220.98)
    sch.texto("Cable de 3 hilos U2 → J5:\nrojo +5 V, verde OUT, negro GND", 78.74, 236.22, 1.1)

    xj5 = 116.84
    j5 = sch.colocar("Connector:Screw_Terminal_01x03", "J5", "Bornera ZMPT", xj5, 213.36, espejo=True,
                     huella=H_BORNE3, ref_at=(xj5 - 5.08, 206.0), val_at=(xj5 - 8.89, 223.52))
    p1, p2, p3 = j5["1"], j5["2"], j5["3"]
    sch.cable(p1, (p1[0] + 5.08, p1[1]))
    sch.power("+5V", p1[0] + 5.08, p1[1])
    sch.cable(p3, (p3[0] + 2.54, p3[1]), (p3[0] + 2.54, 223.52))
    sch.power("GND", p3[0] + 2.54, 223.52)
    xa = p2[0] + 17.78
    sch.cable(p2, (p2[0] + 3.81, p2[1]), (xa, p2[1]))
    sch.etiqueta("ZMPT_OUT", p2[0] + 3.81, p2[1])
    r7 = sch.colocar("Device:R", "R7", "11k 1%", xa + 8.89, 213.36, rot=90, huella=H_R,
                     ref_at=(xa + 7.6, 211.6), val_at=(xa + 6.6, 217.0))
    sch.cable((xa, p2[1]), r7["1"])
    xv = xa + 20.32
    r8 = sch.colocar("Device:R", "R8", "13k 1%", xv, 217.17, huella=H_R,
                     ref_at=(xv + 2.54, 215.9), val_at=(xv + 2.54, 218.44))
    xc9 = xv + 12.7
    c9 = sch.colocar("Device:C", "C9", "27n C0G", xc9, 217.17, huella=H_C,
                     ref_at=(xc9 + 2.54, 215.9), val_at=(xc9 + 2.54, 218.44))
    xdv = xc9 + 15.24
    d6 = sch.colocar("Device:D_Schottky", "D6", "BAT85", xdv, 209.55, rot=270, huella=H_D,
                     ref_at=(xdv + 2.54, 208.28), val_at=(xdv + 2.54, 210.82))
    d7 = sch.colocar("Device:D_Schottky", "D7", "BAT85", xdv, 217.17, rot=270, huella=H_D,
                     ref_at=(xdv + 2.54, 215.9), val_at=(xdv + 2.54, 218.44))
    xfin = xdv + 10.16
    sch.cable(r7["2"], (xv, 213.36), (xc9, 213.36), (xdv, 213.36), (xfin, 213.36))
    sch.cable((xv, 213.36), r8["1"])
    sch.cable((xc9, 213.36), c9["1"])
    sch.etiqueta("V_ADC", xfin, 213.36)
    sch.power("GND", xv, r8["2"][1])
    sch.power("GND", xc9, c9["2"][1])
    sch.power("GND", xdv, d7["2"][1])
    sch.power("+3V3", xdv, d6["1"][1])
    sch.texto("R7–R8 llevan el reposo de 2,5 V del módulo a 1,35 V.\nR7‖R8 = 5,96 kΩ con C9 = 27 nF da τ = 161 µs, frente a 156 y 157 µs\nen CH1 y CH2: desfase relativo ≤ 0,1° a 60 Hz (se corrige en firmware).",
              xa - 2.54, 236.22, 1.1)

    # ---------------- ESP32
    ux, uy = 254.0, 152.4
    sch.texto("MICROCONTROLADOR", 236.22, 116.84, 1.8, True)
    usados_izq = {1: ("pwr", "+3V3"), 3: ("lbl", "CH1_ADC"), 4: ("lbl", "CH2_ADC"), 5: ("lbl", "RES_IO34"),
                  6: ("lbl", "V_ADC"), 7: ("lbl", "RES_IO32"), 8: ("lbl", "RES_IO33"), 9: ("lbl", "LED_EST"),
                  10: ("lbl", "SW1"), 11: ("lbl", "SW2"), 14: ("gnd", None), 19: ("pwr", "+5V")}
    usados_der = {20: ("gnd", None), 21: ("lbl", "LCD_DIN"), 22: ("lbl", "LCD_CS"), 25: ("lbl", "LCD_DC"),
                  26: ("gnd", None), 27: ("lbl", "LCD_BL"), 28: ("lbl", "LCD_CLK"), 32: ("lbl", "LCD_RST")}
    u1 = sch.colocar("Medidor:ESP32-DevKitC-38", "U1", "ESP32-DevKitC V4 (38 pines)", ux, uy,
                     ref_at=(ux - 2.54, uy - 27.94), val_at=(ux - 15.24, uy + 29.21),
                     nc=[str(k) for k in range(1, 39) if k not in usados_izq and k not in usados_der])
    for k, (tipo, nombre) in usados_izq.items():
        p = u1[str(k)]
        xe = p[0] - 10.16
        sch.cable(p, (xe, p[1]))
        if tipo == "lbl":
            sch.etiqueta(nombre, xe, p[1], "izq")
        elif tipo == "pwr":
            sch.power(nombre, xe, p[1], rot=90)
        else:
            sch.power("GND", xe, p[1], rot=270)
    for k, (tipo, nombre) in usados_der.items():
        p = u1[str(k)]
        # GND más cerca del pin para que su texto no tape las etiquetas de los pines vecinos.
        xe = p[0] + (12.7 if tipo == "lbl" else 5.08)
        sch.cable(p, (xe, p[1]))
        if tipo == "lbl":
            sch.etiqueta(nombre, xe, p[1])
        else:
            sch.power("GND", xe, p[1], rot=90)
    sch.texto("Analógicas solo en ADC1 (GPIO32–39):\nel ADC2 no funciona con Wi-Fi activo.\nGPIO6–11 = flash interna: no se usan.",
              236.22, 190.5, 1.1)

    # ---------------- pantalla LCD
    sch.texto("PANTALLA LCD 1,9\" ST7789V2 170×320 (SPI)", 299.72, 83.82, 1.8, True)
    # Orden de pines igual al del lado derecho del ESP32, para que las pistas de la placa de una cara
    # salgan rectas; el cable del módulo termina en conectores Dupont sueltos y se conecta hilo a hilo.
    j6 = sch.colocar("Connector_Generic:Conn_01x08", "J6", "LCD (VCC GND DIN CS DC BL CLK RST)", 342.9, 104.14,
                     huella=H_PH8, ref_at=(347.98, 101.6), val_at=(347.98, 106.68))
    v, g = j6["1"], j6["2"]
    sch.cable(v, (330.2, v[1]), (330.2, 91.44))
    sch.power("+3V3", 330.2, 91.44)
    sch.cable(g, (325.12, g[1]), (325.12, 91.44))
    sch.power("GND", 325.12, 91.44, rot=180)
    for k, nombre in enumerate(("LCD_DIN", "LCD_CS", "LCD_DC", "LCD_BL", "LCD_CLK", "LCD_RST")):
        p = j6[str(k + 3)]
        sch.cable(p, (320.04, p[1]))
        sch.etiqueta(nombre, 320.04, p[1], "izq")

    # ---------------- puntos de prueba e indicadores de alimentación
    sch.texto("PUNTOS DE PRUEBA E INDICADORES DE ALIMENTACIÓN", 139.7, 40.64, 1.8, True)
    sch.texto("Lazos de alambre para el gancho de la punta del osciloscopio o del multímetro;\n"
              "TP8 y TP9 reciben el caimán de tierra de la punta.", 139.7, 45.72, 1.1)
    for k, (red, nombre) in enumerate((("+5V", "+5V"), ("+3V3", "+3V3"), ("VBIAS", "VBIAS"),
                                       ("CH1_ADC", "CH1_ADC"), ("CH2_ADC", "CH2_ADC"), ("ZMPT_OUT", "ZMPT_OUT"),
                                       ("V_ADC", "V_ADC"), ("GND", "GND"), ("GND", "GND"))):
        xt = 142.24 + k * 17.78
        tp = sch.colocar("Connector:TestPoint", f"TP{k + 1}", nombre, xt, 58.42, huella=H_TP,
                         ref_at=(xt + 1.27, 53.34), val_at=(xt + 1.27, 50.8))
        fin = (xt, 63.5)
        sch.cable(tp["1"], fin)
        if red == "GND":
            sch.power("GND", xt, fin[1])
        elif red.startswith("+"):
            sch.power(red, xt, fin[1], rot=180)
        else:
            sch.etiqueta(red, xt, fin[1])
    for k, (red, r, valor, d, color) in enumerate((("+5V", "R14", "1k", "D9", "LED rojo 3 mm"),
                                                   ("+3V3", "R15", "470", "D10", "LED verde 3 mm"))):
        yl = 73.66
        x0 = 142.24 + k * 55.88
        sch.power(red, x0, yl, rot=90)
        rr = sch.colocar("Device:R", r, valor, x0 + 7.62, yl, rot=90, huella=H_R,
                         ref_at=(x0 + 5.74, yl - 2.0), val_at=(x0 + 5.74, yl + 3.6))
        dd = sch.colocar("Device:LED", d, color, x0 + 19.05, yl, rot=180, huella=H_LED3,
                         ref_at=(x0 + 21.59, yl - 6.0), val_at=(x0 + 27.94, yl - 3.3))
        sch.cable((x0, yl), rr["1"])
        sch.cable(rr["2"], dd["2"])
        sch.cable(dd["1"], (x0 + 27.94, yl), (x0 + 27.94, yl + 2.54))
        sch.power("GND", x0 + 27.94, yl + 2.54)
    sch.texto("D9: (5 − 2) V / 1 kΩ = 3 mA, llega el adaptador.\n"
              "D10: (3,3 − 2) V / 470 Ω = 2,8 mA, funciona el\nregulador del DevKitC.", 233.68, 71.12, 1.1)

    # ---------------- LED de estado
    sch.texto("LED DE ESTADO", 299.72, 125.73, 1.8, True)
    yl = 134.62
    sch.etiqueta("LED_EST", 302.26, yl, "izq")
    r11 = sch.colocar("Device:R", "R11", "330", 309.88, yl, rot=90, huella=H_R,
                      ref_at=(308.0, yl - 2.0), val_at=(308.0, yl + 3.6))
    d8 = sch.colocar("Device:LED", "D8", "LED verde 5 mm (panel)", 321.31, yl, rot=180,
                     huella="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", ref_at=(323.85, yl - 6.0), val_at=(330.2, yl - 3.3))
    sch.cable((302.26, yl), r11["1"])
    sch.cable(r11["2"], d8["2"])
    sch.cable(d8["1"], (330.2, yl), (330.2, yl + 2.54))
    sch.power("GND", 330.2, yl + 2.54)

    # ---------------- pulsadores
    for i, (nombre, y) in enumerate((("SW1", 157.48), ("SW2", 185.42))):
        sch.texto(f"PULSADOR {nombre} ({'menú / canal' if i == 0 else 'confirmar / tara'})", 299.72, y - 11.43, 1.8, True)
        rpu, cdb = f"R{12 + i}", f"C{10 + i}"
        rr = sch.colocar("Device:R", rpu, "10k", 309.88, y - 3.81, huella=H_R,
                         ref_at=(312.42, y - 5.08), val_at=(312.42, y - 2.54))
        sw = sch.colocar("Switch:SW_Push", nombre, "Pulsador de panel 12 mm NA", 330.2, y,
                         huella="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", ref_at=(327.66, y - 5.08), val_at=(343.5, y + 0.6))
        cc = sch.colocar("Device:C", cdb, "100n", 317.5, y + 3.81, huella=H_C,
                         ref_at=(320.04, y + 5.08), val_at=(320.04, y + 7.62))
        sch.etiqueta(nombre, 302.26, y, "izq")
        sch.cable((302.26, y), (309.88, y), (317.5, y), sw["1"])
        sch.cable(rr["2"], (309.88, y))
        sch.cable(cc["1"], (317.5, y))
        sch.power("+3V3", 309.88, rr["1"][1])
        sch.power("GND", 317.5, cc["2"][1])
        sch.cable(sw["2"], (340.36, y), (340.36, y + 2.54))
        sch.power("GND", 340.36, y + 2.54)

    # ---------------- reserva
    sch.texto("RESERVA DE ESCALABILIDAD (CH3, CH4, CH5)", 299.72, 207.01, 1.8, True)
    j7 = sch.colocar("Connector_Generic:Conn_01x04", "J7", "Reserva ADC1", 342.9, 218.44,
                     huella=H_PH4, ref_at=(345.44, 213.36), val_at=(345.44, 226.06))
    for k, nombre in ((1, "RES_IO34"), (2, "RES_IO32"), (3, "RES_IO33")):
        p = j7[str(k)]
        sch.cable((317.5, p[1]), p)
        sch.etiqueta(nombre, 317.5, p[1], "izq")
    p = j7["4"]
    sch.cable(p, (330.2, p[1]), (330.2, p[1] + 2.54))
    sch.power("GND", 330.2, p[1] + 2.54)

    # ---------------- notas
    notas = ("NOTAS\n"
             "1. Todo lo que está fuera del recuadro rojo es muy baja tensión (MBT, ≤ 5 V CC). J2, J3, D8, SW1 y SW2 van en el panel del gabinete.\n"
             "2. Los burden R1 y R2 se sueldan directamente en los terminales T y S del jack de panel, nunca en el cable.\n"
             "3. Nunca desenchufar una pinza mientras abraza un conductor energizado (secundario abierto).\n"
             "4. Las pinzas abrazan solo el conductor de fase; jamás fase y neutro juntos.\n"
             "5. Tierra en estrella: el GND analógico llega solo al pin 14 del DevKitC; alimentación y parte digital retornan por los pines 20 y 26.\n"
             "6. ADC con atenuación de 11 dB: zona lineal 0,15–2,45 V; la señal queda en 0,32–2,32 V.")
    sch.texto(notas, 22.86, 250.19, 1.3)
    return sch


if __name__ == "__main__":
    e = construir()
    e.guardar(SALIDA, ["Medidor de energía de dos canales con ESP32", "2026-10-21", "B",
                       "", "", "PCB de una cara (ver medidor-energia.kicad_pcb)"])
    print("Esquemático escrito en", os.path.normpath(SALIDA))
