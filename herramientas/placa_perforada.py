#!/usr/bin/env python3
"""Distribución del medidor en placa perforada de 9 × 15 cm (59 × 35 agujeros, paso 2,54 mm).

1. Describe cada componente, pista inferior y puente por coordenadas de agujero (columna, fila).
2. Verifica la conectividad contra la netlist que exporta KiCad del esquemático:
   cada red del esquemático debe quedar en un solo grupo de agujeros y dos redes distintas
   nunca pueden compartir agujero.
3. Dibuja la cara de componentes y la cara de soldadura (vista espejo).

Uso:  python3 placa_perforada.py ../hardware/medidor-energia.net
"""
import os
import sys
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

from sexpr import find, find1, parse

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, "..", "img")
COLS, FILAS = 59, 35

# ------------------------------------------------------------------ código de colores
COLOR = {
    "5V": "#d62728",      # rojo
    "3V3": "#ff7f0e",     # naranja
    "GND": "#111111",     # negro
    "VBIAS": "#8e44ad",   # violeta
    "CORR": "#e6c200",    # amarillo
    "TENS": "#2ca02c",    # verde
    "LCD": "#1f5fbf",     # azul
    "DIG": "#bdbdbd",     # blanco (gris claro para que se vea sobre el fondo)
    "RES": "#7f7f7f",     # gris
    "PRE": "#d62728",     # entrada de 5 V antes del diodo (rojo)
}


def clase_de_red(red):
    if red in ("+5V",) or red.startswith("Net-(J1") or red.startswith("Net-(D1"):
        return "5V"
    if red == "+3V3":
        return "3V3"
    if red == "GND":
        return "GND"
    if red == "VBIAS":
        return "VBIAS"
    if red.startswith(("CH1", "CH2", "Net-(J2", "Net-(J3")):
        return "CORR"
    if red in ("ZMPT_OUT", "V_ADC"):
        return "TENS"
    if red.startswith("LCD"):
        return "LCD"
    if red.startswith("RES_"):
        return "RES"
    return "DIG"


# ------------------------------------------------------------------ descripción de la placa
PIEZAS = []    # (ref, tipo, {pin: (c, f)}, texto)
PISTAS = []    # ((c1, f1), (c2, f2))  pista de estaño por la cara inferior
PUENTES = []   # ((c1, f1), (c2, f2), clase)  cable aislado por la cara superior
PADS = []      # ((c, f), texto)  punto de soldadura para un cable que sale de la placa


def pieza(ref, tipo, pines, texto=""):
    PIEZAS.append((ref, tipo, pines, texto))


def pista(*pts):
    for a, b in zip(pts, pts[1:]):
        assert a[0] == b[0] or a[1] == b[1], f"pista no ortogonal {a} {b}"
        PISTAS.append((a, b))


def puente(a, b, clase):
    PUENTES.append((a, b, clase))


def pad(p, texto):
    PADS.append((p, texto))


def esp32(c_izq=36, c_der=46, f0=14):
    pines = {}
    for k in range(19):
        pines[str(k + 1)] = (c_izq, f0 + k)
        pines[str(k + 20)] = (c_der, f0 + k)
    pieza("U1", "esp32", pines, "ESP32-DevKitC V4")


def definir():
    # ---- ESP32 sobre dos tiras de espadín hembra 1×19, separadas 10 pasos (25,4 mm)
    esp32()

    # ---- buses
    pista((1, 8), (1, 27))                 # GND analógico vertical
    pista((1, 27), (36, 27))               # GND analógico -> pin 14 (GND) del DevKitC
    pista((1, 20), (30, 20))               # GND de los canales de corriente
    pista((1, 9), (18, 9))                 # GND del canal de tensión
    pista((5, 14), (36, 14))               # +3V3 principal (pin 1 del DevKitC)
    pista((5, 25), (23, 25))               # +3V3 del canal CH2
    pista((12, 3), (20, 3))                # +3V3 del canal de tensión
    puente((23, 14), (23, 25), "3V3")
    puente((24, 14), (20, 3), "3V3")
    pista((36, 14), (36, 12), (57, 12), (57, 33))   # +3V3 lado derecho
    pista((46, 20), (48, 20))              # GND pin 26 -> bus derecho
    pista((48, 14), (48, 33))              # GND digital (lado derecho)
    pista((46, 14), (48, 14))              # GND pin 20 -> bus derecho
    pista((2, 32), (19, 32), (19, 33), (48, 33))    # GND de alimentación

    # ---- alimentación
    pieza("J1", "borne2", {"1": (2, 30), "2": (2, 32)}, "J1 5 V")
    pieza("F2", "ptc", {"1": (5, 30), "2": (7, 30)}, "F2")
    pieza("D1", "diodo41", {"2": (9, 30), "1": (13, 30)}, "D1")
    pieza("C1", "electro8", {"1": (15, 30), "2": (15, 32)}, "C1")
    pieza("C2", "disco", {"1": (18, 30), "2": (18, 32)}, "C2")
    pista((2, 30), (5, 30))
    pista((7, 30), (9, 30))
    pista((13, 30), (18, 30))
    puente((18, 30), (36, 32), "5V")       # +5V -> pin 19 (5V) del DevKitC
    puente((13, 30), (4, 4), "5V")         # +5V -> J5 (módulo ZMPT101B)

    # ---- polarización VBIAS (compartida por los dos canales)
    pieza("R3", "res", {"1": (5, 14), "2": (5, 18)}, "R3")
    pieza("R4", "res_v", {"1": (7, 18), "2": (7, 20)}, "R4")
    pieza("C7", "electro5", {"1": (9, 18), "2": (9, 20)}, "C7")
    pieza("C8", "disco", {"1": (12, 18), "2": (12, 20)}, "C8")
    pista((3, 18), (12, 18))

    # ---- canal CH1
    pad((3, 16), "CH1 T")
    pad((3, 18), "CH1 S")
    pieza("J2", "panel", {"T": (3, 16), "S": (3, 18)}, "")
    pista((3, 16), (10, 16))
    pieza("R5", "res", {"1": (10, 16), "2": (14, 16)}, "R5")
    pista((14, 16), (36, 16))              # CH1_ADC -> GPIO36
    pieza("C5", "disco", {"1": (16, 16), "2": (16, 18)}, "C5")
    pista((13, 18), (16, 18))              # C5 vuelve a VBIAS, donde cierra la pinza
    pieza("D2", "diodo35", {"2": (18, 16), "1": (18, 14)}, "D2")
    pieza("D3", "diodo35", {"1": (20, 16), "2": (20, 18)}, "D3")
    pista((20, 18), (20, 20))

    # ---- canal CH2
    pad((3, 22), "CH2 T")
    pad((3, 24), "CH2 S")
    pieza("J3", "panel", {"T": (3, 22), "S": (3, 24)}, "")
    puente((3, 24), (4, 18), "VBIAS")
    pista((3, 22), (10, 22))
    pieza("R6", "res", {"1": (10, 22), "2": (14, 22)}, "R6")
    pista((14, 22), (22, 22))
    pieza("C6", "disco", {"1": (17, 22), "2": (17, 24)}, "C6")
    pista((3, 24), (17, 24))               # C6 vuelve a VBIAS por el punto S de CH2
    pieza("D4", "diodo35", {"2": (18, 22), "1": (18, 25)}, "D4")
    pieza("D5", "diodo35", {"1": (21, 22), "2": (21, 20)}, "D5")
    puente((22, 22), (36, 17), "CORR")     # CH2_ADC -> GPIO39

    # ---- canal de tensión
    pieza("J5", "borne3", {"1": (2, 4), "2": (2, 6), "3": (2, 8)}, "J5 ZMPT")
    pista((2, 4), (4, 4))
    pista((1, 8), (2, 8))
    pista((2, 6), (5, 6))
    pieza("R7", "res", {"1": (5, 6), "2": (9, 6)}, "R7")
    pista((9, 6), (18, 6))
    pieza("R8", "res_v", {"1": (11, 6), "2": (11, 9)}, "R8")
    pieza("C9", "disco", {"1": (13, 6), "2": (13, 9)}, "C9")
    pieza("D6", "diodo35", {"2": (15, 6), "1": (15, 3)}, "D6")
    pieza("D7", "diodo35", {"1": (17, 6), "2": (17, 9)}, "D7")
    puente((18, 6), (36, 19), "TENS")      # V_ADC -> GPIO35

    # ---- reserva J7
    pieza("J7", "hembra4v", {"1": (32, 18), "2": (32, 19), "3": (32, 20), "4": (32, 21)}, "J7")
    pista((32, 18), (36, 18))
    puente((32, 19), (36, 20), "RES")
    puente((32, 20), (36, 21), "RES")
    pista((32, 21), (30, 21), (30, 20))

    # ---- pantalla LCD J6 (espadín macho 1×8; el cable del módulo termina en Dupont hembra)
    # J6: 1 VCC, 2 GND, 3 DIN, 4 CS, 5 DC, 6 BL, 7 CLK, 8 RST. El pin 1 cae sobre el bus de +3V3.
    pieza("J6", "macho8v", {str(k + 1): (54, 12 + k) for k in range(8)}, "J6 LCD")
    pista((48, 14), (48, 13), (54, 13))    # GND
    for pin_esp, pin_j6 in ((21, 3), (22, 4), (25, 5), (27, 6), (28, 7), (32, 8)):
        puente((46, 14 + pin_esp - 20), (54, 11 + pin_j6), "LCD")

    # ---- puntos de prueba (lazo de alambre en un agujero de la red) y LED de alimentación
    pista((18, 30), (21, 30))
    pieza("TP1", "tp", {"1": (20, 30)}, "+5V")
    pieza("TP2", "tp", {"1": (57, 18)}, "+3V3")
    pista((12, 18), (13, 18))
    pieza("TP3", "tp", {"1": (13, 18)}, "VBIAS")
    pieza("TP4", "tp", {"1": (28, 16)}, "CH1_ADC")
    pieza("TP5", "tp", {"1": (15, 22)}, "CH2_ADC")
    pieza("TP6", "tp", {"1": (4, 6)}, "ZMPT_OUT")
    pista((18, 6), (19, 6))
    pieza("TP7", "tp", {"1": (19, 6)}, "V_ADC")
    pieza("TP8", "tp", {"1": (30, 27)}, "GND")
    pieza("TP9", "tp", {"1": (48, 29)}, "GND")
    pieza("R14", "res_v", {"1": (21, 30), "2": (21, 28)}, "R14")
    pista((21, 28), (26, 28))
    pieza("D9", "led3", {"2": (26, 28), "1": (26, 27)}, "D9 +5V")      # cátodo sobre el bus de GND
    pieza("R15", "res", {"1": (57, 24), "2": (53, 24)}, "R15")
    pista((53, 24), (52, 24))
    pieza("D10", "led3", {"2": (52, 24), "1": (51, 24)}, "D10 +3V3")
    pista((51, 24), (48, 24))

    # ---- LED de estado (LED en el panel, cable a un espadín de 2 pines)
    puente((36, 22), (50, 22), "DIG")
    pieza("R11", "res", {"1": (50, 22), "2": (54, 22)}, "R11")
    pieza("D8", "macho2v", {"2": (55, 22), "1": (55, 23)}, "LED")
    pista((54, 22), (55, 22))
    pista((48, 23), (55, 23))

    # ---- pulsadores (en el panel, cable a espadín de 2 pines)
    for nombre, f, rr, cc, gp in (("SW1", 26, "R12", "C10", 23), ("SW2", 30, "R13", "C11", 24)):
        puente((36, gp), (50, f), "DIG")
        pieza(cc, "disco", {"1": (50, f), "2": (50, f + 1)}, cc)
        pieza(nombre, "macho2v", {"1": (51, f), "2": (51, f + 1)}, nombre)
        pieza(rr, "res", {"2": (53, f), "1": (57, f)}, rr)
        pista((50, f), (53, f))
        pista((48, f + 1), (51, f + 1))


# ------------------------------------------------------------------ verificación
class UF:
    def __init__(self):
        self.p = {}

    def f(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def u(self, a, b):
        self.p[self.f(a)] = self.f(b)


def agujeros_de_pista(a, b):
    if a[0] == b[0]:
        return [(a[0], f) for f in range(min(a[1], b[1]), max(a[1], b[1]) + 1)]
    return [(c, a[1]) for c in range(min(a[0], b[0]), max(a[0], b[0]) + 1)]


def leer_netlist(ruta):
    t = parse(open(ruta, encoding="utf-8").read())[0]
    redes = {}
    for n in find(find1(t, "nets"), "net"):
        nombre = find1(n, "name")[1].lstrip("/")
        redes[nombre] = [(find1(x, "ref")[1], find1(x, "pin")[1]) for x in find(n, "node")]
    return redes


FUERA_DE_PLACA = {"U2", "J4", "F1", "R1", "R2"}   # zona de red y burden en el jack de panel


def verificar(ruta_net):
    redes = leer_netlist(ruta_net)
    uf = UF()
    for a, b in PISTAS:
        h = agujeros_de_pista(a, b)
        for x in h:
            uf.u(h[0], x)
    for a, b, _ in PUENTES:
        uf.u(a, b)
    # El DevKitC une internamente sus tres pines GND (plano de tierra del módulo).
    u1 = dict((p, xy) for ref, _, pines, _ in PIEZAS if ref == "U1" for p, xy in pines.items())
    uf.u(u1["14"], u1["20"])
    uf.u(u1["14"], u1["26"])

    pos = {(ref, p): xy for ref, _, pines, _ in PIEZAS for p, xy in pines.items()}
    ocupado = defaultdict(set)
    for (ref, p), xy in pos.items():
        if ref != "U1" or True:
            ocupado[xy].add((ref, p))

    errores = []
    grupo_de_red = {}
    for red, nodos in redes.items():
        grupos = set()
        for ref, p in nodos:
            if ref in FUERA_DE_PLACA:
                continue
            if (ref, p) not in pos:
                if red.startswith("unconnected"):
                    continue
                errores.append(f"falta en la placa: {ref}.{p} (red {red})")
                continue
            grupos.add(uf.f(pos[(ref, p)]))
        if red.startswith("unconnected"):
            continue
        if len(grupos) > 1:
            errores.append(f"red {red} partida en {len(grupos)} grupos")
        for g in grupos:
            if g in grupo_de_red and grupo_de_red[g] != red:
                errores.append(f"cortocircuito entre {red} y {grupo_de_red[g]}")
            grupo_de_red[g] = red
    # Agujeros usados por pistas o puentes que tocan un pin sin conexión.
    sin_conexion = {pos[n] for red, nodos in redes.items() if red.startswith("unconnected")
                    for n in nodos if n in pos}
    usados = {x for a, b in PISTAS for x in agujeros_de_pista(a, b)} | {x for a, b, _ in PUENTES for x in (a, b)}
    for xy in sin_conexion & usados:
        errores.append(f"pista o puente sobre un pin sin conexión en {xy}")
    for xy, quien in ocupado.items():
        if len(quien) > 1:
            errores.append(f"agujero {xy} con dos terminales: {sorted(quien)}")
    for xy in list(pos.values()) + list(usados):
        if not (0 <= xy[0] < COLS and 0 <= xy[1] < FILAS):
            errores.append(f"fuera de la placa: {xy}")
    red_de_agujero = {}
    for (ref, p), xy in pos.items():
        g = uf.f(xy)
        if g in grupo_de_red:
            red_de_agujero[xy] = grupo_de_red[g]
    return errores, grupo_de_red, uf, len([r for r in redes if not r.startswith("unconnected")])


# ------------------------------------------------------------------ dibujo
def dibujar(grupo_de_red, uf, ruta, espejo=False):
    paso = 1.0
    fig, ax = plt.subplots(figsize=(15, 9.6))
    X = (lambda c: (COLS - 1 - c)) if espejo else (lambda c: c)
    Y = lambda f: FILAS - 1 - f

    ax.add_patch(FancyBboxPatch((-1.4, -1.4), COLS + 1.8, FILAS + 1.8, boxstyle="round,pad=0,rounding_size=1.2",
                                fc="#e9d8a6" if not espejo else "#d9c48c", ec="#8a6d1e", lw=2))
    for c in range(COLS):
        for f in range(FILAS):
            ax.add_patch(Circle((X(c), Y(f)), 0.17, fc="#f6edd3" if not espejo else "#c9a227",
                                ec="#a68a3a", lw=0.4, zorder=1))
    for c, f in ((1, 1), (COLS - 2, 1), (1, FILAS - 2), (COLS - 2, FILAS - 2)):
        pass

    def color_red(xy):
        red = grupo_de_red.get(uf.f(xy))
        return COLOR[clase_de_red(red)] if red else "#9e9e9e"

    # pistas inferiores
    alfa_pista = 1.0 if espejo else 0.35
    for a, b in PISTAS:
        col = color_red(a)
        ax.plot([X(a[0]), X(b[0])], [Y(a[1]), Y(b[1])], color="#9aa0a6", lw=7, solid_capstyle="round",
                alpha=alfa_pista, zorder=2)
        ax.plot([X(a[0]), X(b[0])], [Y(a[1]), Y(b[1])], color=col, lw=2.6, solid_capstyle="round",
                alpha=alfa_pista, zorder=3)

    if not espejo:
        dibujar_piezas(ax, X, Y)
        for a, b, clase in PUENTES:
            col = COLOR[clase]
            ax.plot([X(a[0]), X(b[0])], [Y(a[1]), Y(b[1])], color="black", lw=4.6, alpha=0.9, zorder=8,
                    solid_capstyle="round")
            ax.plot([X(a[0]), X(b[0])], [Y(a[1]), Y(b[1])], color=col, lw=3.0, zorder=9, solid_capstyle="round")
        for (c, f), t in PADS:
            ax.add_patch(Circle((X(c), Y(f)), 0.42, fc="white", ec="#c62828", lw=1.6, zorder=10))
            ax.text(X(c) + 0.6, Y(f) + 0.45, t, fontsize=7.5, color="#c62828", zorder=11, weight="bold")
    else:
        # puntos de soldadura de cada terminal
        for ref, tipo, pines, _ in PIEZAS:
            for p, (c, f) in pines.items():
                if tipo == "panel":
                    continue
                ax.add_patch(Circle((X(c), Y(f)), 0.32, fc="#cfd8dc", ec="#455a64", lw=1.0, zorder=6))
        for a, b, clase in PUENTES:
            for c, f in (a, b):
                ax.add_patch(Circle((X(c), Y(f)), 0.32, fc=COLOR[clase], ec="black", lw=0.8, zorder=7))

    # numeración de columnas y filas
    for c in range(0, COLS, 5):
        ax.text(X(c), FILAS + 0.15, str(c), ha="center", fontsize=7, color="#5d4a12")
    for f in range(0, FILAS, 5):
        ax.text(-2.2 if not espejo else COLS + 0.4, Y(f), str(f), va="center", fontsize=7, color="#5d4a12")

    ax.set_xlim(-3, COLS + 1.5)
    ax.set_ylim(-3.2, FILAS + 1.2)
    ax.set_aspect("equal")
    ax.axis("off")
    titulo = ("Cara de soldadura (vista espejo: la placa volteada sobre su eje vertical)" if espejo
              else "Cara de componentes — placa perforada 9 × 15 cm, paso 2,54 mm")
    ax.set_title(titulo, fontsize=12, weight="bold")
    leyenda = [("+5 V", "5V"), ("+3,3 V", "3V3"), ("GND", "GND"), ("VBIAS 1,32 V", "VBIAS"),
               ("Señal de corriente", "CORR"), ("Señal de tensión", "TENS"), ("LCD (SPI)", "LCD"),
               ("LED y pulsadores", "DIG"), ("Reserva ADC1", "RES")]
    for i, (t, k) in enumerate(leyenda):
        x0 = 1 + i * 6.3
        ax.plot([x0, x0 + 1.4], [-2.3, -2.3], color="black", lw=4.6)
        ax.plot([x0, x0 + 1.4], [-2.3, -2.3], color=COLOR[k], lw=3)
        ax.text(x0 + 1.8, -2.3, t, va="center", fontsize=7.5)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def dibujar_piezas(ax, X, Y):
    def lead(a, b):
        ax.plot([X(a[0]), X(b[0])], [Y(a[1]), Y(b[1])], color="#8d8d8d", lw=1.4, zorder=4)

    for ref, tipo, pines, texto in PIEZAS:
        pts = list(pines.values())
        xs = [X(c) for c, _ in pts]
        ys = [Y(f) for _, f in pts]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        if tipo == "esp32":
            x0, x1 = min(xs), max(xs)
            y0, y1 = min(ys), max(ys)
            ax.add_patch(Rectangle((x0 - 1.0, y0 - 2.6), (x1 - x0) + 2.0, (y1 - y0) + 6.6, fc="#263238",
                                   ec="black", lw=1.2, alpha=0.88, zorder=5))
            ax.add_patch(Rectangle((x0 + 1.4, y1 + 0.6), (x1 - x0) - 2.8, 3.0, fc="#b0bec5", ec="#37474f",
                                   zorder=6))
            ax.add_patch(Rectangle((cx - 1.3, y0 - 3.0), 2.6, 1.8, fc="#cfd8dc", ec="#37474f", zorder=6))
            ax.text(cx, y1 + 2.1, "ESP32-WROOM-32", ha="center", va="center", fontsize=7, zorder=7)
            ax.text(cx, y0 - 2.1, "USB", ha="center", va="center", fontsize=6.5, zorder=7)
            ax.text(cx, cy + 3, "U1\nESP32-DevKitC V4\n(38 pines)", ha="center", va="center", color="white",
                    fontsize=9, weight="bold", zorder=7)
            nombres_i = ["3V3", "EN", "VP", "VN", "34", "35", "32", "33", "25", "26", "27", "14", "12", "GND",
                         "13", "D2", "D3", "CMD", "5V"]
            nombres_d = ["GND", "23", "22", "TX", "RX", "21", "GND", "19", "18", "5", "17", "16", "4", "0",
                         "2", "15", "D1", "D0", "CLK"]
            for k in range(19):
                c_i, f_i = pines[str(k + 1)]
                c_d, f_d = pines[str(k + 20)]
                for (c, f), n, dx, ha in (((c_i, f_i), nombres_i[k], 0.55, "left"),
                                          ((c_d, f_d), nombres_d[k], -0.55, "right")):
                    ax.add_patch(Rectangle((X(c) - 0.45, Y(f) - 0.45), 0.9, 0.9, fc="#111", ec="#555", zorder=6))
                    ax.text(X(c) + dx, Y(f), n, fontsize=5.6, color="white", va="center", ha=ha, zorder=7)
            continue
        if tipo == "panel":
            continue
        if tipo in ("res", "res_v"):
            a, b = pts
            lead(a, b)
            if a[1] == b[1]:
                ax.add_patch(FancyBboxPatch((cx - 1.15, cy - 0.38), 2.3, 0.76, boxstyle="round,pad=0.05",
                                            fc="#7fb3d5", ec="#1b4f72", lw=1, zorder=5))
                ax.text(cx, cy, ref, ha="center", va="center", fontsize=6.5, zorder=6)
            else:
                h = min(2.3, abs(ys[0] - ys[1]) - 0.5)
                ax.add_patch(FancyBboxPatch((cx - 0.38, cy - h / 2), 0.76, h, boxstyle="round,pad=0.05",
                                            fc="#7fb3d5", ec="#1b4f72", lw=1, zorder=5))
                ax.text(cx + 0.55, cy, ref, ha="left", va="center", fontsize=6.5, zorder=6)
        elif tipo == "disco":
            a, b = pts
            lead(a, b)
            ax.add_patch(Circle((cx, cy), 0.62, fc="#e67e22", ec="#873600", lw=1, zorder=5))
            ax.text(cx, cy + 0.95, ref, ha="center", va="center", fontsize=6.5, zorder=6)
        elif tipo in ("electro8", "electro5"):
            a, b = pts
            lead(a, b)
            r = 1.45 if tipo == "electro8" else 0.95
            ax.add_patch(Circle((cx, cy), r, fc="#1a5276", ec="black", lw=1, zorder=5))
            ax.text(X(pines["1"][0]), Y(pines["1"][1]), "+", ha="center", va="center", color="white",
                    fontsize=8, weight="bold", zorder=6)
            ax.text(cx + r + 0.2, cy, ref, ha="left", va="center", fontsize=6.5, zorder=6)
        elif tipo in ("diodo35", "diodo41"):
            a, k = pines["2"], pines["1"]
            lead(a, k)
            ax_ = (X(k[0]) - X(a[0]), Y(k[1]) - Y(a[1]))
            L = max(abs(ax_[0]), abs(ax_[1]))
            ux, uy = ax_[0] / L, ax_[1] / L
            largo = 1.3 if tipo == "diodo35" else 2.0
            ancho = 0.55 if tipo == "diodo35" else 0.8
            w, h = (largo, ancho) if uy == 0 else (ancho, largo)
            ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h,
                                   fc="#c0392b" if tipo == "diodo35" else "#212121", ec="black", lw=0.8, zorder=5))
            bx, by = cx + ux * (largo / 2 - 0.22), cy + uy * (largo / 2 - 0.22)
            bw, bh = (0.22, ancho) if uy == 0 else (ancho, 0.22)
            ax.add_patch(Rectangle((bx - bw / 2, by - bh / 2), bw, bh, fc="#eeeeee", ec="none", zorder=6))
            ax.text(cx + (0.6 if uy != 0 else 0), cy + (0.65 if uy == 0 else 0), ref,
                    ha="left" if uy != 0 else "center", va="center", fontsize=6.5, zorder=6)
        elif tipo == "ptc":
            a, b = pts
            lead(a, b)
            ax.add_patch(Circle((cx, cy), 0.85, fc="#f1c40f", ec="#7d6608", lw=1, zorder=5))
            ax.text(cx, cy + 1.2, ref, ha="center", fontsize=6.5, zorder=6)
        elif tipo in ("borne2", "borne3"):
            y0, y1 = min(ys), max(ys)
            ax.add_patch(Rectangle((min(xs) - 1.9, y0 - 1.1), 2.6, (y1 - y0) + 2.2, fc="#27ae60", ec="#145a32",
                                   lw=1.2, zorder=5))
            for x, y in zip(xs, ys):
                ax.add_patch(Circle((x - 0.6, y), 0.5, fc="#bdc3c7", ec="#555", zorder=6))
                ax.plot([x - 0.9, x - 0.3], [y, y], color="#555", lw=1, zorder=7)
            ax.text(min(xs) + 1.0, y1 + 0.9, texto, fontsize=7, weight="bold", zorder=6)
        elif tipo == "tp":
            ax.add_patch(Circle((cx, cy), 0.55, fc="none", ec="#b0b0b0", lw=2.2, zorder=6))
            ax.text(cx + 0.7, cy + 0.7, texto, fontsize=6.2, weight="bold", zorder=6)
        elif tipo == "led3":
            ax.add_patch(Circle((cx, cy), 0.75, fc="#e74c3c" if "5V" in texto else "#2ecc71", ec="black",
                                lw=0.8, alpha=0.9, zorder=5))
            ax.text(cx + 0.9, cy, texto, va="center", fontsize=6.2, zorder=6)
        elif tipo in ("hembra4v", "macho2v", "macho8v"):
            y0, y1 = min(ys), max(ys)
            ax.add_patch(Rectangle((xs[0] - 0.5, y0 - 0.5), 1.0, (y1 - y0) + 1.0,
                                   fc="#212121" if tipo == "hembra4v" else "#424242", ec="black", zorder=5))
            for x, y in zip(xs, ys):
                ax.add_patch(Rectangle((x - 0.18, y - 0.18), 0.36, 0.36,
                                       fc="#000" if tipo == "hembra4v" else "#d4ac0d", zorder=6))
            ax.text(xs[0] + 0.8, y1 + 0.2, texto, fontsize=6.8, weight="bold", zorder=6)


def main():
    definir()
    ruta_net = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "..", "hardware", "medidor-energia.net")
    errores, grupo_de_red, uf, n = verificar(ruta_net)
    if errores:
        print("ERRORES DE CONECTIVIDAD:")
        for e in errores:
            print("  -", e)
        sys.exit(1)
    print(f"Conectividad verificada: {n} redes del esquemático coinciden con la placa perforada.")
    print(f"{len(PIEZAS)} piezas, {len(PISTAS)} pistas, {len(PUENTES)} puentes.")
    os.makedirs(IMG, exist_ok=True)
    dibujar(grupo_de_red, uf, os.path.join(IMG, "placa-perforada-componentes.png"))
    dibujar(grupo_de_red, uf, os.path.join(IMG, "placa-perforada-soldadura.png"), espejo=True)


if __name__ == "__main__":
    main()
