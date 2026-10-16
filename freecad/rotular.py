"""Rotula la vista superior del banco renderizada por FreeCAD y la guarda en ../img/3d-banco-planta.png."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, "..", "img")

img = mpimg.imread(os.path.join(AQUI, "planta-banco-base.png"))   # vista sin rótulos de render.py
x0, x1, y0, y1 = 280, 1780, 200, 1030           # recorte alrededor del banco (píxeles)
img = img[y0:y1, x0:x1]
fig, ax = plt.subplots(figsize=(14, 7.8))
ax.imshow(img)
ax.axis("off")

# (texto, punto señalado en píxeles del render, posición del texto)
rotulos = [
    ("P1: clavija NEMA 5-15P\n(se enchufa a la pared)", (490, 790), (470, 600)),
    ("Cordón SJT 3 × 14 AWG\ny prensaestopas PG11", (1075, 790), (820, 960)),
    ("Neutro (blanco): directo al\ntornillo plateado de X1", (1300, 866), (1180, 1000)),
    ("Tierra (verde): directo al\ntornillo verde de X1", (1575, 830), (1640, 960)),
    ("Fase (negro): sale por\nel primer PG7", (1335, 640), (1040, 640)),
    ("Lazo de fase exterior\n(THHN 14 AWG aislado)", (1390, 290), (1640, 300)),
    ("CT1: pinza SCT-013-000\n(translúcida) cerrada sobre\nuna sola pata del lazo", (1337, 470), (1660, 480)),
    ("Cable de la pinza: plug de\n3,5 mm a J2 del medidor", (900, 413), (760, 280)),
    ("X1: tomacorriente doble\ndonde se conecta el equipo", (1475, 760), (1700, 720)),
    ("La fase vuelve por el segundo\nPG7 al tornillo de bronce de X1", (1390, 698), (1680, 600)),
]
for texto, (px, py), (tx, ty) in rotulos:
    ax.annotate(texto, (px - x0, py - y0), (tx - x0, ty - y0), fontsize=8.5, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#455a64", lw=0.8),
                arrowprops=dict(arrowstyle="->", color="#c62828", lw=1.3))
ax.set_xlim(0, x1 - x0)
ax.set_ylim(y1 - y0 + 20, -60)
ax.set_title("Banco de medición sin tapa (vista superior). Negro: fase · blanco: neutro · verde: tierra · gris: cable de pinza",
             fontsize=10, weight="bold")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "3d-banco-planta.png"), dpi=150)
print("Rótulos agregados a 3d-banco-planta.png")
