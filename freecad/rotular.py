"""Rotula la vista superior del banco renderizada por FreeCAD y la guarda en ../img/3d-banco-planta.png."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, "..", "img")

img = mpimg.imread(os.path.join(AQUI, "planta-banco-base.png"))   # vista sin rótulos de render.py
x0, x1, y0, y1 = 300, 1720, 280, 960            # recorte alrededor de la caja (píxeles)
img = img[y0:y1, x0:x1]
fig, ax = plt.subplots(figsize=(14, 8.6))
ax.imshow(img)
ax.axis("off")

# (texto, punto señalado en píxeles del render, posición del texto)
rotulos = [
    ("Cable de red (entrada)\ny prensaestopas PG11", (470, 490), (330, 300)),
    ("H1: piloto neón", (735, 430), (600, 300)),
    ("W1 neutro y W2 tierra\n(conectores de palanca)", (785, 440), (840, 300)),
    ("Q1: breaker 15 A", (860, 470), (1060, 300)),
    ("CT1: pinza de CH1\n(translúcida; la fase de X1\npasa por su ventana)", (950, 520), (1250, 300)),
    ("CT2: pinza de CH2\n(la fase de X2 pasa\npor su ventana)", (1310, 520), (1500, 300)),
    ("Cables de las pinzas\nhacia J2 y J3 del medidor\n(prensaestopas PG9)", (1590, 430), (1590, 560)),
    ("W3: empalme de fase\ndespués de Q1", (795, 672), (560, 900)),
    ("X0: toma auxiliar\n(sin medir)", (705, 760), (730, 940)),
    ("X1: salida CH1", (1030, 760), (1010, 940)),
    ("Fase (negro) al tornillo\nde bronce de X1", (1105, 600), (1200, 860)),
    ("X2: salida CH2", (1357, 760), (1400, 940)),
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
