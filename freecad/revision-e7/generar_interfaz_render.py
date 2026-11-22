#!/usr/bin/env python3
"""Genera la interfaz táctil horizontal estática usada por los renders E.8."""
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H = 600, 450


def font(bold, size):
    family = "DejaVu Sans:bold" if bold else "DejaVu Sans"
    path = subprocess.check_output(["fc-match", "-f", "%{file}", family], text=True)
    return ImageFont.truetype(path, size)


im = Image.new("RGB", (W, H), (3, 7, 10))
d = ImageDraw.Draw(im)
fg, muted, green, blue = (238, 244, 246), (115, 132, 142), (61, 214, 133), (66, 166, 255)
d.text((28, 22), "ENERGÍA · E.8", font=font(False, 18), fill=muted)
d.text((572, 22), "Wi-Fi  ●", font=font(False, 18), fill=green, anchor="ra")
d.text((28, 52), "Consumo ahora", font=font(True, 31), fill=fg)
d.text((28, 104), "1.84", font=font(True, 73), fill=fg)
d.text((190, 151), "kW", font=font(True, 27), fill=muted)
cards = (("RED", "121.2 V", green), ("TOTAL", "15.3 A", blue), ("A/C", "8.7 A", (255, 166, 65)))
for i, (label, value, color) in enumerate(cards):
    x = 28 + i * 184
    d.rounded_rectangle((x, 215, x + 168, 335), 12, fill=(15, 23, 28), outline=tuple(int(c * .55) for c in color), width=2)
    d.text((x + 15, 233), label, font=font(False, 16), fill=color)
    d.text((x + 15, 273), value, font=font(True, 28), fill=fg)
d.rounded_rectangle((28, 364, 572, 418), 12, fill=(12, 29, 23))
d.text((48, 391), "Estado normal · toque para ver detalles", font=font(True, 20), fill=green, anchor="lm")
im.save(HERE / "tft-render-horizontal.png")
