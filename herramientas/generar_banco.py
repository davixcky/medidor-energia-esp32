#!/usr/bin/env python3
"""Genera el esquemático KiCad del banco de medición en ../hardware/banco-pruebas.kicad_sch.

El banco es una caja con una clavija de entrada y un tomacorriente de salida. La fase sale de
la caja en un lazo aislado donde se coloca la pinza, de modo que cualquier equipo se mide con
solo enchufarlo, sin cortar ni pelar su cable. Reutiliza la clase
Esquematico de generar_esquematico.py. Se verifica con:

    kicad-cli sch erc ../hardware/banco-pruebas.kicad_sch
"""
import os
import uuid as _uuid

import generar_esquematico as g
from generar_esquematico import S, efectos, pin_def, polilinea, rect, simbolo_propio, texto_sim

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "..", "hardware", "banco-pruebas.kicad_sch")

# Identificadores propios: no se mezclan con los del esquemático del medidor.
g._ns = _uuid.UUID("6f1d2c3e-0000-4000-8000-0000000000b1")
g._cont.clear()
g.RAIZ = g.uid("raiz")
g.PROYECTO = "banco-pruebas"

# ---------------------------------------------------------------- símbolos propios
def circulo(cx, cy, radio, ancho=0.254, relleno="none"):
    return [S("circle"), [S("center"), cx, cy], [S("radius"), radio],
            [S("stroke"), [S("width"), ancho], [S("type"), S("default")]], [S("fill"), [S("type"), S(relleno)]]]


def sim_clavija():
    pines = [pin_def("passive", 7.62, 2.54, 180, "L", "1"),
             pin_def("passive", 7.62, 0, 180, "N", "2"),
             pin_def("passive", 7.62, -2.54, 180, "PE", "3")]
    graf = [rect(-5.08, 5.08, 2.54, -5.08),
            polilinea([(-8.89, 0), (-5.08, 0)], 0.6),
            texto_sim("5-15P", -1.27, -6.6, 1.0)]
    return simbolo_propio("Medidor:Clavija_NEMA_5-15P", "P", "Clavija 5-15P", graf, pines, 7.62, -7.62,
                          "Clavija de 3 patas NEMA 5-15P, 125 V 15 A, con cable")


def sim_toma():
    pines = [pin_def("passive", -7.62, 2.54, 0, "L", "1"),
             pin_def("passive", -7.62, 0, 0, "N", "2"),
             pin_def("passive", -7.62, -2.54, 0, "PE", "3")]
    graf = [rect(-2.54, 5.08, 7.62, -5.08)]
    for cy in (2.54, -2.54):  # dos tomas del aparato doble
        graf += [polilinea([(0.9, cy + 0.9), (0.9, cy - 0.3)], 0.3),
                 polilinea([(3.0, cy + 0.9), (3.0, cy - 0.3)], 0.3),
                 circulo(1.95, cy - 1.2, 0.35)]
    graf.append(texto_sim("5-15R", 2.54, -6.6, 1.0))
    return simbolo_propio("Medidor:Tomacorriente_NEMA_5-15R", "X", "Tomacorriente doble 5-15R", graf, pines,
                          7.62, -7.62, "Tomacorriente doble polarizado con polo a tierra, 125 V 15 A")


def sim_pinza():
    # Primario: el conductor de fase atraviesa el núcleo (P1 entra, P2 sale).
    # Secundario: los dos hilos del cable de la pinza (punta T y manga S del plug).
    pines = [pin_def("passive", -10.16, 0, 0, "P1", "1"),
             pin_def("passive", 10.16, 0, 180, "P2", "2"),
             pin_def("passive", -2.54, -10.16, 90, "S", "3"),
             pin_def("passive", 2.54, -10.16, 90, "T", "4")]
    graf = [circulo(0, 0, 4.2, 0.6), circulo(0, 0, 2.6, 0.254),
            polilinea([(-5.08, 0), (5.08, 0)], 0.254),
            polilinea([(-2.54, -5.08), (-2.54, -3.6)], 0.254),
            polilinea([(2.54, -5.08), (2.54, -3.6)], 0.254),
            texto_sim("100 A : 50 mA", 0, 5.6, 1.0)]
    return simbolo_propio("Medidor:Pinza_SCT-013-000", "CT", "SCT-013-000", graf, pines, 8.89, -8.89,
                          "Pinza de corriente de núcleo partido 100 A : 50 mA, sin resistencia de carga")


def sim_plug():
    pines = [pin_def("passive", -2.54, 5.08, 270, "S", "1", 2.54),
             pin_def("passive", 2.54, 5.08, 270, "T", "2", 2.54)]
    graf = [rect(-4.445, 2.54, 4.445, -2.54),
            polilinea([(0, -2.54), (0, -5.08)], 0.6),
            texto_sim("3,5 mm", 0, -6.4, 1.0)]
    return simbolo_propio("Medidor:Plug_3.5mm", "PL", "Plug 3,5 mm", graf, pines, 0, 0,
                          "Plug macho de 3,5 mm del cable de la pinza (punta = T, manga = S)")


# ---------------------------------------------------------------- el esquemático
def toma(sch, ref, valor, xr, yr, y_n, y_pe, x_fila, y_fila):
    """Coloca un tomacorriente con L arriba; baja N y PE a sus barras y sube L a la fila de fase."""
    p = sch.colocar("Medidor:Tomacorriente_NEMA_5-15R", ref, valor, xr, yr,
                    ref_at=(xr - 1.27, yr - 7.0), val_at=(xr - 3.81, yr + 9.5))
    sch.cable(p["1"], (x_fila, p["1"][1]), (x_fila, y_fila))
    sch.cable(p["2"], (xr - 12.7, p["2"][1]), (xr - 12.7, y_n))
    sch.cable(p["3"], (xr - 10.16, p["3"][1]), (xr - 10.16, y_pe))
    return p


def pinza(sch, ref, pl, x, y, canal, jack):
    p = sch.colocar("Medidor:Pinza_SCT-013-000", ref, f"SCT-013-000 ({canal})", x, y,
                    ref_at=(x + 5.6, y - 8.6), val_at=(x + 5.6, y - 6.2))
    q = sch.colocar("Medidor:Plug_3.5mm", pl, f"Plug 3,5 mm → {jack} del medidor", x, y + 17.78,
                    ref_at=(x + 5.6, y + 16.5), val_at=(x + 5.6, y + 19.0))
    sch.cable(p["3"], q["1"])
    sch.cable(p["4"], q["2"])
    return p


def construir():
    sch = g.Esquematico()
    for d in (sim_clavija(), sim_toma(), sim_pinza(), sim_plug()):
        sch.usar(d[1], d)

    yf, y_n, y_pe = 60.96, 101.6, 109.22     # fila de fase, neutro y tierra
    sch.texto("BANCO DE MEDICIÓN — 120 V CA, 60 Hz, 15 A máx.", 20.32, 30.48, 2.0, True)
    sch.texto("Se enchufa a un tomacorriente de pared; el equipo a medir se enchufa en X1. La fase sale de la caja\n"
              "en un lazo aislado donde se coloca la pinza; el neutro y la tierra van directo a X1.",
              20.32, 36.83, 1.27)
    sch.caja(11.43, 41.91, 182.88, 118.11, color=(200, 0, 0))

    # Entrada: clavija con cable de 3 hilos
    p1 = sch.colocar("Medidor:Clavija_NEMA_5-15P", "P1", "Clavija 5-15P, cable SJT 3×14 AWG 1,8 m", 22.86, yf + 2.54,
                     ref_at=(19.05, yf - 4.5), val_at=(17.78, yf + 12.7))
    sch.cable(p1["2"], (35.56, p1["2"][1]), (35.56, y_n))
    sch.cable(p1["3"], (33.02, p1["3"][1]), (33.02, y_pe))

    # Lazo de medición: la fase atraviesa una vez la pinza CT1
    ct1 = pinza(sch, "CT1", "PL1", 71.12, yf, "CH1", "J2")
    sch.cable(p1["1"], ct1["1"])
    sch.etiqueta("L_ENT", 40.64, yf)
    sch.texto("Lazo de medición (fuera de la caja)", 55.88, yf - 13.97, 1.27, True)

    # Salida
    x1 = toma(sch, "X1", "Tomacorriente doble 5-15R (equipo a medir)", 127.0, 81.28, y_n, y_pe, 111.76, yf)
    sch.cable(ct1["2"], (111.76, yf))
    sch.etiqueta("L_X1", 93.98, yf)

    sch.cable((35.56, y_n), (114.3, y_n))
    sch.cable((33.02, y_pe), (116.84, y_pe))
    sch.etiqueta("N", 40.64, y_n)
    sch.etiqueta("PE", 40.64, y_pe)

    notas = ("NOTAS\n"
             "1. Solo la fase pasa por la pinza, una sola vez: el lazo exterior es un tramo de THHN 14 AWG negro que sale y vuelve a entrar\n"
             "    a la caja por dos prensaestopas PG7. El neutro y la tierra nunca pasan por la pinza (las corrientes se cancelarían).\n"
             "2. La pinza se conecta a J2 (CH1) del medidor; la calibración es la misma que en un tablero (una pasada).\n"
             "3. Conductores 14 AWG: fase negro, neutro blanco, tierra verde. Tomacorriente polarizado: fase al tornillo de bronce\n"
             "    (ranura corta), neutro al plateado (ranura larga), tierra al verde.\n"
             "4. La protección es el breaker del circuito de pared (15 A). El medidor se alimenta de otro tomacorriente de pared.\n"
             "5. El lazo también admite una pinza amperimétrica comercial, útil para calibrar el canal.")
    sch.texto(notas, 20.32, 152.4, 1.27)
    return sch


if __name__ == "__main__":
    e = construir()
    e.guardar(SALIDA, ["Banco de medición con tomacorriente de entrada y salida", "2026-10-21", "B",
                       "", "", "Complemento del medidor de energía de dos canales"], papel="A4")
    with open(os.path.join(os.path.dirname(SALIDA), "banco-pruebas.kicad_pro"), "w") as f:
        f.write("{}\n")
    print("Esquemático escrito en", os.path.normpath(SALIDA))
