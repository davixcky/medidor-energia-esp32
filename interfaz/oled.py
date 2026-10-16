#!/usr/bin/env python3
"""Dibuja las pantallas de la OLED SSD1306 (128 × 64, monocromática) píxel por píxel.

Usa una fuente de 5 × 7 en celdas de 6 × 8, igual a la fuente clásica de Adafruit GFX que
usará el firmware (setTextSize(1) = 6 × 8, setTextSize(2) = 12 × 16). Por eso los textos van
sin tildes: esa fuente no las tiene. Genera:

    ../img/ui-oled-pantallas.png   las seis pantallas ampliadas
    ../img/ui-oled-navegacion.png  diagrama de navegación con los pulsadores (Graphviz)
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, "..", "img")
W, H = 128, 64

# Cada glifo: 7 filas de 5 bits (el bit 4 es la columna izquierda).
FUENTE = {
    "0": "0E 11 13 15 19 11 0E", "1": "04 0C 04 04 04 04 0E", "2": "0E 11 01 02 04 08 1F",
    "3": "1F 02 04 02 01 11 0E", "4": "02 06 0A 12 1F 02 02", "5": "1F 10 1E 01 01 11 0E",
    "6": "06 08 10 1E 11 11 0E", "7": "1F 01 02 04 08 08 08", "8": "0E 11 11 0E 11 11 0E",
    "9": "0E 11 11 0F 01 02 0C",
    "A": "0E 11 11 1F 11 11 11", "B": "1E 11 11 1E 11 11 1E", "C": "0E 11 10 10 10 11 0E",
    "D": "1C 12 11 11 11 12 1C", "E": "1F 10 10 1E 10 10 1F", "F": "1F 10 10 1E 10 10 10",
    "G": "0E 11 10 17 11 11 0F", "H": "11 11 11 1F 11 11 11", "I": "0E 04 04 04 04 04 0E",
    "J": "07 02 02 02 02 12 0C", "K": "11 12 14 18 14 12 11", "L": "10 10 10 10 10 10 1F",
    "M": "11 1B 15 15 11 11 11", "N": "11 11 19 15 13 11 11", "O": "0E 11 11 11 11 11 0E",
    "P": "1E 11 11 1E 10 10 10", "Q": "0E 11 11 11 15 12 0D", "R": "1E 11 11 1E 14 12 11",
    "S": "0F 10 10 0E 01 01 1E", "T": "1F 04 04 04 04 04 04", "U": "11 11 11 11 11 11 0E",
    "V": "11 11 11 11 11 0A 04", "W": "11 11 11 15 15 15 0A", "X": "11 11 0A 04 0A 11 11",
    "Y": "11 11 11 0A 04 04 04", "Z": "1F 01 02 04 08 10 1F",
    "a": "00 00 0E 01 0F 11 0F", "b": "10 10 16 19 11 11 1E", "c": "00 00 0E 10 10 11 0E",
    "d": "01 01 0D 13 11 11 0F", "e": "00 00 0E 11 1F 10 0E", "f": "06 08 08 1C 08 08 08", "h": "10 10 16 19 11 11 11",
    "i": "04 00 0C 04 04 04 0E", "k": "10 10 12 14 18 14 12", "l": "0C 04 04 04 04 04 0E",
    "m": "00 00 1A 15 15 11 11", "n": "00 00 16 19 11 11 11", "o": "00 00 0E 11 11 11 0E",
    "r": "00 00 16 19 10 10 10", "s": "00 00 0E 10 0E 01 1E", "t": "08 08 1C 08 08 09 06",
    "u": "00 00 11 11 11 13 0D", "v": "00 00 11 11 11 0A 04", "z": "00 00 1F 02 04 08 1F",
    " ": "00 00 00 00 00 00 00", ".": "00 00 00 00 00 0C 0C", ",": "00 00 00 00 0C 04 08",
    ":": "00 0C 0C 00 0C 0C 00", "-": "00 00 00 1F 00 00 00", "/": "00 01 02 04 08 10 00",
    "%": "18 19 02 04 08 13 03", "!": "04 04 04 04 04 00 04", ">": "08 04 02 01 02 04 08",
    "<": "02 04 08 10 08 04 02", "=": "00 00 1F 00 1F 00 00", "(": "02 04 08 08 08 04 02",
    ")": "08 04 02 02 02 04 08", "+": "00 04 04 1F 04 04 00",
}


class Oled:
    def __init__(self):
        self.px = [[0] * W for _ in range(H)]

    def punto(self, x, y, c=1):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = c

    def caja(self, x, y, w, h, relleno=True, c=1):
        for j in range(y, y + h):
            for i in range(x, x + w):
                if relleno or j in (y, y + h - 1) or i in (x, x + w - 1):
                    self.punto(i, j, c)

    def texto(self, x, y, t, tam=1, c=1):
        for ch in t:
            filas = [int(v, 16) for v in FUENTE[ch].split()]
            for fy, fila in enumerate(filas):
                for fx in range(5):
                    if fila & (1 << (4 - fx)):
                        self.caja(x + fx * tam, y + fy * tam, tam, tam, True, c)
            x += 6 * tam
        return x

    def ancho(self, t, tam=1):
        return len(t) * 6 * tam - tam

    def centrado(self, y, t, tam=1):
        self.texto((W - self.ancho(t, tam)) // 2, y, t, tam)

    def cabecera(self, titulo, pagina=None, wifi=True):
        self.caja(0, 0, W, 10)
        self.texto(2, 1, titulo, 1, 0)
        x = W - 2
        if pagina:
            x -= self.ancho(pagina)
            self.texto(x, 1, pagina, 1, 0)
            x -= 4
        if wifi:  # tres barras de intensidad de señal
            for k, h in enumerate((3, 5, 7)):
                self.caja(x - 12 + k * 4, 8 - h, 3, h, True, 0)

    def barra(self, y, frac, etiqueta):
        self.texto(0, y, etiqueta)
        x0 = self.ancho(etiqueta) + 4
        self.caja(x0, y, W - x0, 7, relleno=False)
        self.caja(x0 + 2, y + 2, int((W - x0 - 4) * min(1, frac)), 3)


def pantallas():
    p = []
    s = Oled()  # 1. resumen
    s.cabecera("RESUMEN", "1/4")
    s.centrado(14, "1362 W", 2)
    s.texto(0, 34, "V 120,4V  I 12,76A")
    s.texto(0, 44, "FP 0,90   f 60,00Hz")
    s.texto(0, 55, "CH2 1154W  RES 208W")
    p.append(("1. Resumen (pantalla de inicio)", s))

    s = Oled()  # 2. CH1
    s.cabecera("CH1 TOTAL", "2/4")
    s.centrado(13, "12,76 A", 2)
    s.texto(0, 31, "P    1362 W")
    s.texto(0, 40, "S    1517 VA")
    s.texto(0, 49, "FP   0,90  THD 7,8%")
    s.barra(57, 12.76 / 60, "60A")
    p.append(("2. Detalle CH1 (total, escala 60 A)", s))

    s = Oled()  # 3. CH2
    s.cabecera("CH2 SUBCIRC.", "3/4")
    s.centrado(13, "11,04 A", 2)
    s.texto(0, 31, "P    1154 W")
    s.texto(0, 40, "S    1311 VA")
    s.texto(0, 49, "FP   0,88  85% TOT")
    s.barra(57, 11.04 / 30, "30A")
    p.append(("3. Detalle CH2 (subcircuito, escala 30 A)", s))

    s = Oled()  # 4. energía y red
    s.cabecera("ENERGIA HOY", "4/4")
    s.centrado(13, "13,72kWh", 2)
    s.texto(0, 31, "WIFI   -61dBm  OK")
    s.texto(0, 40, "SERVIDOR OK")
    s.texto(0, 49, "NTP    15:46:10")
    s.texto(0, 57, "BUFER  0 REG")
    p.append(("4. Energía del día y estado de la red", s))

    s = Oled()  # 5. alerta
    s.caja(0, 0, W, 10)
    s.texto(2, 1, "! ALERTA CH1", 1, 0)
    s.centrado(14, "2480 W", 2)
    s.texto(0, 33, "SOBRE UMBRAL 2050W")
    s.texto(0, 42, "DURANTE 9 min")
    s.caja(0, 53, W, 11)
    s.texto(4, 55, "SW2: RECONOCER", 1, 0)
    p.append(("5. Alerta (aparece sola, el LED parpadea rápido)", s))

    s = Oled()  # 6. tara
    s.cabecera("TARA CH1", None, wifi=False)
    s.texto(0, 14, "RETIRE LA CARGA")
    s.texto(0, 23, "OFFSET ACTUAL")
    s.centrado(33, "+0,07 A", 2)
    s.texto(0, 56, "SW2 2s:OK SW1:SALIR")
    p.append(("6. Tara de un canal (SW2 sostenido en 2 o 3)", s))
    return p


def ampliar(s, k=4, on=(140, 225, 255), off=(10, 14, 20)):
    im = Image.new("RGB", (W * k, H * k), off)
    d = ImageDraw.Draw(im)
    for y in range(H):
        for x in range(W):
            if s.px[y][x]:
                d.rectangle([x * k, y * k, x * k + k - 2, y * k + k - 2], fill=on)
            else:
                d.rectangle([x * k, y * k, x * k + k - 2, y * k + k - 2], fill=(18, 23, 31))
    return im


def fuente(tam, negrita=False):
    for nombre in ("/usr/share/fonts/TTF/JetBrainsMono-Bold.ttf" if negrita else "/usr/share/fonts/TTF/JetBrainsMono-Regular.ttf",
                   "/usr/share/fonts/TTF/JetBrainsMono-Regular.ttf"):
        if os.path.exists(nombre):
            return ImageFont.truetype(nombre, tam)
    return ImageFont.load_default()


def lamina():
    ps = pantallas()
    k, borde, rot = 4, 26, 46
    cw, ch = W * k + 2 * borde, H * k + 2 * borde + rot
    cols, filas = 3, 2
    hoja = Image.new("RGB", (cols * cw + (cols + 1) * 24, filas * ch + (filas + 1) * 24 + 40), (245, 246, 248))
    d = ImageDraw.Draw(hoja)
    d.text((24, 16), "Pantallas de la OLED SSD1306 128 × 64 (cada cuadro es un píxel)", fill=(22, 25, 31), font=fuente(24, True))
    for i, (nombre, s) in enumerate(ps):
        cx = 24 + (i % cols) * (cw + 24)
        cy = 64 + (i // cols) * (ch + 24)
        d.rounded_rectangle([cx, cy, cx + cw, cy + ch - rot], radius=14, fill=(32, 36, 44))
        hoja.paste(ampliar(s, k), (cx + borde, cy + borde))
        d.text((cx + 4, cy + ch - rot + 10), nombre, fill=(22, 25, 31), font=fuente(19))
    hoja.save(os.path.join(IMG, "ui-oled-pantallas.png"))


NAVEGACION = r'''
digraph N {
  graph [rankdir=LR, fontname="DejaVu Sans", fontsize=11, nodesep=0.4, ranksep=0.6, bgcolor="white"];
  node  [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=10, fillcolor="#eef3fb", color="#4a5568"];
  edge  [fontname="DejaVu Sans", fontsize=9, color="#4a5568"];
  arranque [label="Arranque\n(descarta 500 ms,\nconecta Wi-Fi)", fillcolor="#f5f5f5"];
  r  [label="1. Resumen"];
  c1 [label="2. CH1"];
  c2 [label="3. CH2"];
  e  [label="4. Energía y red"];
  al [label="5. Alerta", fillcolor="#fdecea", color="#c62828"];
  ta [label="6. Tara del canal", fillcolor="#fff8e1", color="#b35900"];
  ap [label="Pantalla apagada\n(ahorro)", fillcolor="#f5f5f5"];
  arranque -> r;
  r -> c1 [label="SW1"]; c1 -> c2 [label="SW1"]; c2 -> e [label="SW1"]; e -> r [label="SW1"];
  c1 -> ta [label="SW2 sostenido 2 s"]; c2 -> ta [label="SW2 sostenido 2 s"];
  ta -> r [label="SW2 2 s: guarda offset\nSW1: cancela"];
  r -> al [label="desde cualquier pantalla:\npico ≥ 5 min o saturación", style=dashed, color="#c62828", fontcolor="#c62828"];
  al -> r [label="SW2: reconoce", color="#c62828", fontcolor="#c62828"];
  e -> ap [label="60 s sin pulsar\n(cualquier pantalla)", style=dashed];
  ap -> r [label="SW1 o SW2"];
  subgraph cluster_led { label="LED de estado (D8)"; fontsize=10; color="#9aa4b2"; style="dashed,rounded";
    led [shape=plaintext, fillcolor="white", label=<
      <TABLE BORDER="0" CELLSPACING="2" CELLPADDING="2">
      <TR><TD ALIGN="LEFT"><B>Fijo</B></TD><TD ALIGN="LEFT">Servidor al día</TD></TR>
      <TR><TD ALIGN="LEFT"><B>1 Hz</B></TD><TD ALIGN="LEFT">sin red: guarda en LittleFS</TD></TR>
      <TR><TD ALIGN="LEFT"><B>5 Hz</B></TD><TD ALIGN="LEFT">alerta sin reconocer</TD></TR>
      <TR><TD ALIGN="LEFT"><B>Apagado</B></TD><TD ALIGN="LEFT">sin alimentación o falla</TD></TR>
      </TABLE>>];
  }
}
'''


def navegacion():
    subprocess.run(["dot", "-Tpng", "-Gdpi=150", "-o", os.path.join(IMG, "ui-oled-navegacion.png")],
                   input=NAVEGACION.encode(), check=True)


if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    lamina()
    navegacion()
    print("Pantallas escritas en", os.path.normpath(IMG))
