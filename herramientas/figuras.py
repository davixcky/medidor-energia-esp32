#!/usr/bin/env python3
"""Diagrama de bloques (Graphviz), planos del gabinete y cronograma (Matplotlib)."""
import os
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Rectangle

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, "..", "img")

BLOQUES = r'''
digraph G {
  graph [rankdir=LR, fontname="DejaVu Sans", fontsize=11, nodesep=0.35, ranksep=0.55, bgcolor="white"];
  node  [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=10, fillcolor="#f5f5f5", color="#555555"];
  edge  [fontname="DejaVu Sans", fontsize=9, color="#444444"];

  subgraph cluster_red {
    label="Zona de red 120 V CA (compartimento aislado)"; color="#c62828"; fontcolor="#c62828"; style="dashed,rounded";
    red  [label="Tablero eléctrico\nfase + neutro", fillcolor="#ffebee"];
    fus  [label="F1\nfusible T 500 mA", fillcolor="#ffebee"];
    zmpt [label="U2  módulo ZMPT101B\ntransformador aislado\n+ LM358", fillcolor="#ffebee"];
  }
  subgraph cluster_mbt {
    label="Muy baja tensión (≤ 5 V CC) — placa perforada"; color="#1565c0"; fontcolor="#1565c0"; style="dashed,rounded";
    ct1  [label="Pinza SCT-013-000 CH1\n(total, 0–60 A)", fillcolor="#fff8e1"];
    ct2  [label="Pinza SCT-013-000 CH2\n(subcircuito, 0–30 A)", fillcolor="#fff8e1"];
    b1   [label="Burden 22 Ω\n+ RC 3,3 kΩ / 47 nF\n+ recorte BAT85", fillcolor="#fff8e1"];
    b2   [label="Burden 47 Ω\n+ RC 3,3 kΩ / 47 nF\n+ recorte BAT85", fillcolor="#fff8e1"];
    bias [label="VBIAS 1,32 V\ndivisor 15k/10k", fillcolor="#f3e5f5"];
    div  [label="Divisor 11k/13k\n+ C 27 nF\n+ recorte BAT85", fillcolor="#e8f5e9"];
    esp  [label="U1  ESP32-DevKitC V4\nADC1 12 bit · Wi-Fi\nGPIO36 / 39 / 35", fillcolor="#e3f2fd", penwidth=2];
    oled [label="OLED SSD1306\nI2C 0x3C", fillcolor="#e3f2fd"];
    hmi  [label="LED de estado\nSW1, SW2", fillcolor="#e3f2fd"];
    res  [label="J7 reserva\nGPIO34 / 32 / 33", fillcolor="#eeeeee"];
    pwr  [label="Adaptador 5 V 2 A\n→ PTC → 1N5819", fillcolor="#ffebee"];
  }
  nube [label="Broker MQTT / TLS\nbase de series de tiempo\ntablero web", shape=cylinder, fillcolor="#ede7f6"];

  red -> fus -> zmpt;
  zmpt -> div [label="0–3,5 V\nreposo 2,5 V", color="#2e7d32"];
  red -> ct1 [style=dotted, label="acople\nmagnético", arrowhead=none];
  red -> ct2 [style=dotted, arrowhead=none];
  ct1 -> b1 [label="0–30 mA", color="#b8860b"];
  ct2 -> b2 [label="0–15 mA", color="#b8860b"];
  bias -> b1 [color="#8e24aa"]; bias -> b2 [color="#8e24aa"];
  b1 -> esp [label="CH1_ADC\nGPIO36", color="#b8860b"];
  b2 -> esp [label="CH2_ADC\nGPIO39", color="#b8860b"];
  div -> esp [label="V_ADC\nGPIO35", color="#2e7d32"];
  esp -> oled [dir=both, color="#1565c0", label="GPIO21/22"];
  esp -> hmi [dir=both, label="GPIO25/26/27"];
  esp -> res [style=dashed];
  pwr -> esp [label="+5 V", color="#c62828"];
  pwr -> zmpt [label="+5 V", color="#c62828"];
  esp -> nube [label="Wi-Fi\n40 B/s", style=bold];
}
'''


def bloques():
    ruta = os.path.join(IMG, "diagrama-de-bloques.png")
    subprocess.run(["dot", "-Tpng", "-Gdpi=150", "-o", ruta], input=BLOQUES.encode(), check=True)


def cota(ax, x1, y1, x2, y2, texto, off=6, vertical=False):
    if vertical:
        ax.annotate("", (x1 - off, y1), (x2 - off, y2), arrowprops=dict(arrowstyle="<->", lw=0.9))
        ax.text(x1 - off - 2, (y1 + y2) / 2, texto, rotation=90, ha="right", va="center", fontsize=8)
    else:
        ax.annotate("", (x1, y1 - off), (x2, y2 - off), arrowprops=dict(arrowstyle="<->", lw=0.9))
        ax.text((x1 + x2) / 2, y1 - off - 2, texto, ha="center", va="top", fontsize=8)


def gabinete():
    fig, (a, b) = plt.subplots(1, 2, figsize=(15, 6.6))
    # ---------------- vista superior sin tapa
    W, D, t = 200, 150, 2.5
    a.add_patch(Rectangle((0, 0), W, D, fc="#eceff1", ec="black", lw=2))
    a.add_patch(Rectangle((t, t), W - 2 * t, D - 2 * t, fc="white", ec="#607d8b", lw=1))
    yp = 108
    a.add_patch(Rectangle((t, yp), W - 2 * t, 3, fc="#c62828", ec="#7f0000"))
    a.text(W / 2, yp + 1.5, "tabique de 3 mm", ha="center", va="center", fontsize=7, color="white")
    a.add_patch(Rectangle((t, yp + 3), W - 2 * t, D - yp - 3 - t, fc="#ffebee", ec="none", alpha=0.7))
    a.text(8, D - 9, "ZONA DE RED 120 V CA", color="#c62828", fontsize=9, weight="bold")
    a.add_patch(Rectangle((70, 118), 49, 19, fc="#1565c0", ec="black"))
    a.text(94.5, 127.5, "U2 ZMPT101B\n(separadores M3)", ha="center", va="center", fontsize=7, color="white")
    a.add_patch(Rectangle((35, 120), 25, 9, fc="#424242", ec="black"))
    a.text(47.5, 124.5, "F1 portafusible", ha="center", va="center", fontsize=6.5, color="white")
    a.add_patch(Rectangle((135, 119), 18, 10, fc="#2e7d32", ec="black"))
    a.text(144, 124, "J4 L/N", ha="center", va="center", fontsize=6.5, color="white")
    a.add_patch(Circle((180, D), 6, fc="#9e9e9e", ec="black"))
    a.text(180, D - 10, "PG7\n(cable de red)", ha="center", va="top", fontsize=7)
    a.annotate("", (25, 106), (25, 116), arrowprops=dict(arrowstyle="-", lw=2.5, color="#2e7d32"))
    a.text(27, 112, "paso con collarín:\ncable de 3 hilos a J5", fontsize=6.5, va="center")
    # placa
    bx, by = 25, 10
    a.add_patch(Rectangle((bx, by), 150, 90, fc="#e9d8a6", ec="#8a6d1e", lw=1.5))
    a.text(bx + 75, by + 82, "Placa perforada 150 × 90 mm\n(4 separadores M3 de 10 mm)", ha="center", fontsize=8)
    for cx, cy in ((bx + 4, by + 4), (bx + 146, by + 4), (bx + 4, by + 86), (bx + 146, by + 86)):
        a.add_patch(Circle((cx, cy), 1.6, fc="white", ec="black"))
    a.add_patch(Rectangle((bx + 89, by + 2), 28, 54, fc="#263238", ec="black", alpha=0.85))
    a.text(bx + 103, by + 32, "ESP32\nDevKitC", ha="center", va="center", color="white", fontsize=8)
    a.add_patch(Rectangle((bx + 98, 0), 10, t + 1, fc="#ffca28", ec="black"))
    a.text(bx + 103, -3, "ventana USB 10 × 6 mm", ha="center", va="top", fontsize=7)
    for y, n in ((by + 47, "J2 CH1"), (by + 33, "J3 CH2"), (by + 9, "jack CC 5,5 × 2,1")):
        a.add_patch(Rectangle((-3, y - 3), 6, 6, fc="#ffca28", ec="black"))
        a.text(-5, y, n, ha="right", va="center", fontsize=7.5)
    a.text(10, by + 61, "Pinzas: el cable\nentra por el jack", fontsize=6.5)
    cota(a, 0, 0, W, 0, "200 mm", off=12)
    cota(a, 0, 0, 0, D, "150 mm", off=26, vertical=True)
    a.set_xlim(-45, W + 10)
    a.set_ylim(-25, D + 12)
    a.set_aspect("equal")
    a.axis("off")
    a.set_title("Vista superior sin tapa (frente abajo)", weight="bold")

    # ---------------- tapa
    b.add_patch(Rectangle((0, 0), W, D, fc="#eceff1", ec="black", lw=2))
    b.add_patch(Rectangle((0, yp), W, D - yp, fc="#ffcdd2", ec="none", alpha=0.6))
    b.text(W / 2, D - 20, "⚠ RIESGO ELÉCTRICO 120 V — NO ABRIR ENERGIZADO", ha="center", color="#b71c1c",
           fontsize=9, weight="bold")
    b.add_patch(Rectangle((40, 55), 26.5, 15, fc="#0d1b2a", ec="black", lw=1.5))
    b.text(53.25, 62.5, "OLED", color="#80deea", ha="center", va="center", fontsize=8)
    b.text(53.25, 50, "ventana 26,5 × 15 mm\n(pantalla rehundida 1,5 mm)", ha="center", va="top", fontsize=7)
    b.add_patch(Circle((95, 62.5), 4, fc="#66bb6a", ec="black"))
    b.text(95, 54, "D8 LED 5 mm", ha="center", va="top", fontsize=7)
    for x, n in ((125, "SW1\nmenú / canal"), (155, "SW2\nconfirmar / tara")):
        b.add_patch(Circle((x, 62.5), 6, fc="#455a64", ec="black"))
        b.add_patch(Circle((x, 62.5), 4.2, fc="#b0bec5", ec="black"))
        b.text(x, 52, n, ha="center", va="top", fontsize=7)
    b.text(W / 2, 20, "MEDIDOR DE ENERGÍA · CH1 total · CH2 subcircuito\nCUC · Sistemas Embebidos 1", ha="center",
           fontsize=8.5)
    for cx, cy in ((7, 7), (W - 7, 7), (7, D - 7), (W - 7, D - 7)):
        b.add_patch(Circle((cx, cy), 1.7, fc="white", ec="black"))
    b.text(9, 11, "4 × M3", fontsize=7)
    cota(b, 40, 55, 66.5, 55, "26,5", off=-20)
    b.set_xlim(-10, W + 10)
    b.set_ylim(-25, D + 12)
    b.set_aspect("equal")
    b.axis("off")
    b.set_title("Tapa (vista exterior)", weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "gabinete.png"), dpi=150)
    plt.close(fig)


def _hilo(ax, pts, tipo):
    xs, ys = zip(*pts)
    if tipo == "N":
        ax.plot(xs, ys, color="#616161", lw=4.2, solid_capstyle="round", zorder=3)
        ax.plot(xs, ys, color="white", lw=2.6, solid_capstyle="round", zorder=3)
    else:
        ax.plot(xs, ys, color={"L": "black", "PE": "#2e7d32", "S": "#9e9e9e"}[tipo], lw=2.6 if tipo != "S" else 1.6,
                solid_capstyle="round", zorder=3)


def _pinza(ax, cx, cy, nombre):
    """Pinza vista desde arriba: el núcleo queda de canto y el conductor de fase lo atraviesa."""
    yf = cy + 4                                   # altura del conductor de fase
    ax.add_patch(FancyBboxPatch((cx - 9, yf - 17), 18, 34, boxstyle="round,pad=1,rounding_size=4",
                                fc="#37474f", ec="black", alpha=0.9, zorder=4))
    # Ventana del núcleo (13 mm) vista de canto y el conductor que pasa por ella.
    ax.add_patch(Rectangle((cx - 10.5, yf - 6.5), 21, 13, fc="#eceff1", ec="black", lw=0.8, zorder=5))
    ax.plot([cx - 24, cx + 24], [yf, yf], color="black", lw=2.6, zorder=6, solid_capstyle="round")
    ax.annotate("", (cx + 22, yf - 9), (cx - 22, yf - 9),
                arrowprops=dict(arrowstyle="->", lw=0.9, color="#c62828"), zorder=7)
    ax.text(cx, yf - 21, f"{nombre}: la fase cruza\nla ventana una vez", ha="center", va="top",
            fontsize=6.5, color="#263238", weight="bold", zorder=7)


def banco():
    fig, (a, b) = plt.subplots(1, 2, figsize=(16, 6.4))
    W, D, t = 300, 180, 3
    # ---------------- interior, vista superior sin tapa
    a.add_patch(Rectangle((0, 0), W, D, fc="#eceff1", ec="black", lw=2))
    a.add_patch(Rectangle((t, t), W - 2 * t, D - 2 * t, fc="#ffebee", ec="#607d8b", lw=1))
    a.text(150, 8, "TODA LA CAJA ES ZONA DE RED 120 V CA", color="#c62828", fontsize=9, weight="bold", ha="center")
    a.add_patch(Rectangle((t, 112), 110, 7, fc="#b0bec5", ec="black"))
    a.text(60, 115.5, "riel DIN 35 mm", ha="center", va="center", fontsize=6.5)
    a.add_patch(Rectangle((22, 92), 18, 47, fc="white", ec="black", lw=1.2, zorder=4))
    a.text(31, 115.5, "Q1\n15 A", ha="center", va="center", fontsize=7, weight="bold", zorder=5)
    # salidas montadas en la tapa (contorno punteado)
    for x, n in ((40, "X0"), (150, "X1"), (255, "X2")):
        a.add_patch(Rectangle((x - 17, 18), 34, 52, fill=False, ec="#455a64", ls="--", lw=1.2))
        a.text(x, 44, f"{n}\n(en la tapa)", ha="center", va="center", fontsize=7, color="#455a64")
    a.add_patch(Circle((95, 44), 5, fill=False, ec="#455a64", ls="--"))
    a.text(95, 33, "H1", ha="center", fontsize=7, color="#455a64")
    # conectores de palanca
    for x, y, w, n in ((60, 150, 30, "W1 neutro (5)"), (60, 165, 30, "W2 tierra (5)"),
                       (75, 84, 22, "W3 L_SW (5)")):
        a.add_patch(Rectangle((x - w / 2, y - 4), w, 8, fc="#ff9800", ec="black", zorder=4))
        a.text(x, y + 6, n, ha="center", fontsize=6.5, zorder=5)
    # entrada: la fase va al breaker; neutro y tierra a sus conectores de palanca
    a.add_patch(Circle((0, 140), 7, fc="#9e9e9e", ec="black", zorder=5))
    a.text(-10, 140, "PG11\ncable de red\nSJT 3×14 AWG", ha="right", va="center", fontsize=7)
    _hilo(a, [(0, 141), (31, 141), (31, 139)], "L")
    _hilo(a, [(0, 139), (12, 139), (12, 150), (45, 150)], "N")
    _hilo(a, [(0, 137), (8, 137), (8, 165), (45, 165)], "PE")
    for y in (150, 165):
        a.annotate("", (110, y), (76, y), arrowprops=dict(arrowstyle="->", lw=1.0, color="#455a64"))
    a.text(112, 157.5, "a X0, X1, X2 y H1\n(Tabla 9)", va="center", fontsize=7, color="#455a64")
    # recorrido de la fase: Q1 → W3 → (CT1 → X1) y (CT2 → X2); la fase cruza cada ventana una vez
    _hilo(a, [(31, 92), (31, 84), (64, 84)], "L")
    _hilo(a, [(68, 80), (68, 76), (46, 76), (46, 70)], "L")
    _hilo(a, [(76, 80), (76, 62), (95, 62), (95, 49)], "L")
    _hilo(a, [(86, 84), (92, 84), (92, 124), (160, 124), (160, 70)], "L")
    _hilo(a, [(84, 88), (84, 144), (214, 144), (214, 124), (270, 124), (270, 76), (262, 76), (262, 70)], "L")
    _pinza(a, 125, 120, "CT1")
    _pinza(a, 240, 120, "CT2")
    # cables de las pinzas (MBT aislada) hacia el prensaestopas
    a.add_patch(Circle((W, 172), 5, fc="#9e9e9e", ec="black", zorder=5))
    _hilo(a, [(125, 141), (125, 170), (W, 170)], "S")
    _hilo(a, [(240, 141), (240, 174), (W, 174)], "S")
    a.text(W + 8, 172, "PG9: cables de las pinzas\n→ plugs a J2 y J3\ndel medidor", va="center", fontsize=7)
    cota(a, 0, 0, W, 0, "300 mm", off=10)
    cota(a, 0, 0, 0, D, "180 mm", off=40, vertical=True)
    a.set_xlim(-75, W + 70)
    a.set_ylim(-22, D + 8)
    a.set_aspect("equal")
    a.axis("off")
    a.set_title("Interior sin tapa (frente abajo): recorrido de la fase por las pinzas\nnegro: fase · blanco: neutro · verde: tierra · gris: cable de pinza",
                weight="bold", fontsize=9)

    # ---------------- tapa
    b.add_patch(Rectangle((0, 0), W, D, fc="#eceff1", ec="black", lw=2))
    for x, n, d in ((40, "X0", "AUXILIAR\nsin medir"), (150, "X1", "SALIDA CH1\nmedida"),
                    (255, "X2", "SALIDA CH2\nmedida")):
        b.add_patch(FancyBboxPatch((x - 17, 18), 34, 52, boxstyle="round,pad=0.5,rounding_size=3", fc="white",
                                   ec="black"))
        for yy in (32, 56):
            b.add_patch(Rectangle((x - 5, yy), 1.6, 6, fc="black"))
            b.add_patch(Rectangle((x + 3.6, yy), 1.6, 7.5, fc="black"))
            b.add_patch(Circle((x, yy - 3.5), 1.6, fc="black"))
        b.text(x, 80, f"{n}  {d}", ha="center", va="bottom", fontsize=7.5, weight="bold")
    b.add_patch(Rectangle((86, 120), 18, 24, fc="#263238", ec="black"))
    b.text(95, 132, "Q1", color="white", ha="center", va="center", fontsize=8)
    b.text(95, 117, "ventana del breaker", ha="center", va="top", fontsize=7)
    b.add_patch(Circle((55, 140), 5, fc="#ff7043", ec="black"))
    b.text(55, 132, "H1 piloto", ha="center", va="top", fontsize=7)
    b.text(205, 140, "BANCO DE MEDICIÓN · 120 V 15 A máx.\nCH1 = X1 · CH2 = X2", ha="center", fontsize=9,
           weight="bold")
    b.text(205, 118, "⚠ NO ABRIR ENERGIZADO", ha="center", fontsize=8.5, color="#b71c1c", weight="bold")
    for cx, cy in ((6, 6), (W - 6, 6), (6, D - 6), (W - 6, D - 6)):
        b.add_patch(Circle((cx, cy), 1.7, fc="white", ec="black"))
    b.set_xlim(-10, W + 10)
    b.set_ylim(-22, D + 8)
    b.set_aspect("equal")
    b.axis("off")
    b.set_title("Tapa (vista exterior)", weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "banco-pruebas.png"), dpi=150)
    plt.close(fig)


def cronograma():
    actividades = [
        ("Definición de la idea y requerimientos", 1, 3, "hecho"),
        ("Arquitectura y selección de componentes", 3, 5, "hecho"),
        ("Esquemático en KiCad y verificación ERC", 5, 8, "hecho"),
        ("Distribución en placa perforada", 7, 8, "hecho"),
        ("Banco de medición: diseño y esquemático", 8, 8, "hecho"),
        ("Simulación SPICE de las entradas y la alimentación", 8, 8, "hecho"),
        ("Modelos 3D del medidor y del banco", 8, 8, "hecho"),
        ("Diseño de la interfaz (tablero web y OLED)", 8, 8, "hecho"),
        ("LSTM inicial con datos públicos", 8, 8, "hecho"),
        ("Compra de componentes", 5, 9, "retraso"),
        ("Gabinete: diseño y fabricación", 7, 10, "curso"),
        ("Montaje y soldadura", 9, 10, "curso"),
        ("Pruebas eléctricas y HardExplosion", 10, 10, "pendiente"),
        ("Banco de medición: montaje y calibración", 10, 11, "pendiente"),
        ("Firmware: código y prueba del cálculo en el PC", 8, 8, "hecho"),
        ("Plataforma web (TanStack Start) con simulador", 8, 8, "hecho"),
        ("Firmware: prueba en el ESP32 y calibración", 10, 11, "pendiente"),
        ("Conexión del nodo real a la plataforma", 11, 13, "pendiente"),
        ("Validación contra referencia y entrega final", 14, 16, "pendiente"),
    ]
    colores = {"hecho": "#2e7d32", "curso": "#1565c0", "retraso": "#ef6c00", "pendiente": "#9e9e9e"}
    nombres = {"hecho": "Terminada", "curso": "En curso", "retraso": "En curso con retraso", "pendiente": "Pendiente"}
    fig, ax = plt.subplots(figsize=(12, 7.8))
    for i, (n, s, e, st) in enumerate(actividades):
        ax.barh(i, e - s + 1, left=s - 0.5, color=colores[st], edgecolor="black", height=0.6)
    ax.set_yticks(range(len(actividades)))
    ax.set_yticklabels([a[0] for a in actividades], fontsize=9)
    ax.invert_yaxis()
    ax.set_xticks(range(1, 17))
    ax.set_xlim(0.5, 16.5)
    ax.set_xlabel("Semana del periodo 2026-2")
    for x in (4, 10, 16):
        ax.axvline(x + 0.5, color="black", lw=1, ls=":")
        ax.text(x + 0.42, len(actividades) - 0.3, f"Corte {(x // 6) + 1 if x != 4 else 1}", ha="right", fontsize=8)
    ax.axvspan(8.5, 9.5, color="#fff3e0", zorder=0)
    ax.text(9, len(actividades) - 0.3, "receso", ha="center", fontsize=8, color="#e65100")
    ax.grid(axis="x", alpha=0.3)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=colores[k], ec="black", label=nombres[k]) for k in colores],
              loc="lower left", fontsize=8, ncol=4, bbox_to_anchor=(0, -0.28))
    ax.set_title("Cronograma de actividades y estado al 16 de octubre de 2026", weight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "cronograma.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    bloques()
    gabinete()
    banco()
    cronograma()
    print("Figuras escritas en", os.path.normpath(IMG))
