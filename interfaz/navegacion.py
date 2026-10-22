#!/usr/bin/env python3
"""Diagrama de navegación de la LCD con los pulsadores (Graphviz).

Cada nodo muestra la pantalla real, dibujada por el código del firmware en el PC
(`make -C ../firmware/test pantallas`, que escribe ../img/ui-lcd-*.png). Genera:

    ../img/ui-lcd-navegacion.png
"""
import os
import subprocess
import tempfile

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.normpath(os.path.join(AQUI, "..", "img"))
PANTALLAS = {"arranque": "Arranque", "resumen": "1. Resumen", "ch1": "2. CH1", "ch2": "3. CH2",
             "energia": "4. Energía hoy", "alerta": "Alerta", "tara": "Tara del canal"}
COLOR = {"alerta": "#c62828", "tara": "#b35900"}


def nodo(clave, tmp):
    ruta = os.path.join(tmp, clave + ".png")
    Image.open(os.path.join(IMG, f"ui-lcd-{clave}.png")).resize((240, 128), Image.LANCZOS).save(ruta)
    color = COLOR.get(clave, "#1D1517")
    return (f'  {clave} [label=<<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="3">'
            f'<TR><TD><IMG SRC="{ruta}"/></TD></TR>'
            f'<TR><TD><FONT COLOR="{color}"><B>{PANTALLAS[clave]}</B></FONT></TD></TR></TABLE>>];')


def main():
    with tempfile.TemporaryDirectory() as tmp:
        nodos = "\n".join(nodo(k, tmp) for k in PANTALLAS)
        dot = r'''
digraph N {
  graph [rankdir=LR, fontname="DejaVu Sans", fontsize=11, nodesep=0.35, ranksep=0.55, bgcolor="white"];
  node  [shape=plain, fontname="DejaVu Sans", fontsize=11];
  edge  [fontname="DejaVu Sans", fontsize=9, color="#4a5568"];
%s
  apagada [shape=box, style="rounded,filled", fillcolor="#f5f5f5", color="#4a5568",
           label="Luz de fondo apagada\n(60 s sin pulsar)"];
  arranque -> resumen;
  resumen -> ch1 [label="SW1"]; ch1 -> ch2 [label="SW1"]; ch2 -> energia [label="SW1"];
  energia -> resumen [label="SW1"];
  ch1 -> tara [label="SW2 sostenido 2 s"]; ch2 -> tara [label="SW2 sostenido 2 s"];
  tara -> ch1 [label="SW1: vuelve al canal"];
  tara -> tara [label="SW2 2 s: mide y guarda el ruido"];
  resumen -> alerta [label="CH1 > 2000 W durante 5 min\n(desde cualquier pantalla)", style=dashed,
                     color="#c62828", fontcolor="#c62828"];
  alerta -> resumen [label="SW2: reconoce", color="#c62828", fontcolor="#c62828"];
  energia -> apagada [style=dashed]; apagada -> resumen [label="SW1 o SW2: enciende la luz\n(vuelve a la misma pantalla)", style=dashed];
  subgraph cluster_led { label="LED de estado (D8)"; fontsize=10; color="#9aa4b2"; style="dashed,rounded";
    led [shape=plaintext, label=<
      <TABLE BORDER="0" CELLSPACING="2" CELLPADDING="2">
      <TR><TD ALIGN="LEFT"><B>Fijo</B></TD><TD ALIGN="LEFT">servidor al día</TD></TR>
      <TR><TD ALIGN="LEFT"><B>1 Hz</B></TD><TD ALIGN="LEFT">sin envío: guarda en RAM (20 min)</TD></TR>
      <TR><TD ALIGN="LEFT"><B>5 Hz</B></TD><TD ALIGN="LEFT">alerta sin reconocer</TD></TR>
      </TABLE>>];
  }
}
''' % nodos
        subprocess.run(["dot", "-Tpng", "-Gdpi=130", "-o", os.path.join(IMG, "ui-lcd-navegacion.png")],
                       input=dot.encode(), check=True)
    print("Diagrama escrito en", os.path.join(IMG, "ui-lcd-navegacion.png"))


if __name__ == "__main__":
    main()
