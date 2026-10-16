"""Modelo paramétrico del banco de medición (FreeCAD 1.1, freecadcmd).

Caja de 300 × 180 × 100 mm. Cada salida medida tiene su propia pinza SCT-013-000 y el
conductor de fase la atraviesa una sola vez (sección 7.11 del documento).
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import Part

from comun import V, Modelo, caja_redondeada, cilindro, orientar, prensaestopas, ranura, texto, tubo

W, D, H_CUERPO, E_TAPA = 300.0, 180.0, 97.0, 3.0
PARED, R_ESQ, TORNILLO = 3.0, 6.0, 7.0
ZT = H_CUERPO                         # cara inferior de la tapa
# tomacorrientes dobles NEMA 5-15R: centro (x, y), eje del aparato a lo largo de Y
TOMAS = {"X0": (45.0, 60.0), "X1": (150.0, 60.0), "X2": (255.0, 60.0)}
SEP_CARAS, SEP_TORN = 38.8, 83.3      # separación de las dos caras y de los tornillos del aparato
Q1 = (95.0, 115.0)                    # centro del breaker visto desde arriba
H1 = (55.0, 140.0)
Z_HILO = 62.0                         # altura del conductor de fase que atraviesa las pinzas
PINZAS = {"CT1": (125.0, 124.0), "CT2": (240.0, 124.0)}
D_HILO = 3.0                          # THHN 14 AWG


def cuerpo():
    ext = caja_redondeada(W, D, H_CUERPO, R_ESQ)
    c = ext.cut(caja_redondeada(W - 2 * PARED, D - 2 * PARED, H_CUERPO, R_ESQ - PARED, PARED, PARED, PARED))
    for x, y in ((TORNILLO, TORNILLO), (W - TORNILLO, TORNILLO), (TORNILLO, D - TORNILLO), (W - TORNILLO, D - TORNILLO)):
        c = c.fuse(cilindro(9, H_CUERPO - PARED, x, y, PARED)).cut(cilindro(4.0, 12, x, y, H_CUERPO - 12))
    # base elevada del riel DIN (15 mm) con dos tornillos
    c = c.fuse(Part.makeBox(130, 20, 15, V(10, Q1[1] - 10, PARED)))
    # prensaestopas: PG11 (18,6 mm) en la pared izquierda y PG9 (15,2 mm) en la derecha
    c = c.cut(cilindro(18.8, 10, -2, 140, 40, "x"))
    c = c.cut(cilindro(15.4, 10, W - 5, 160, 40, "x"))
    # patas
    for x, y in ((25, 25), (W - 25, 25), (25, D - 25), (W - 25, D - 25)):
        c = c.fuse(cilindro(16, 3, x, y, -3))
    return c.removeSplitter()


def tapa():
    t = caja_redondeada(W, D, E_TAPA, R_ESQ, 0, 0, ZT)
    labio = caja_redondeada(W - 2 * PARED - 0.8, D - 2 * PARED - 0.8, 4, R_ESQ - PARED, PARED + 0.4, PARED + 0.4, ZT - 4)
    labio = labio.cut(caja_redondeada(W - 2 * PARED - 4.8, D - 2 * PARED - 4.8, 4, 1, PARED + 2.4, PARED + 2.4, ZT - 4))
    t = t.fuse(labio)
    for x, y in ((TORNILLO, TORNILLO), (W - TORNILLO, TORNILLO), (TORNILLO, D - TORNILLO), (W - TORNILLO, D - TORNILLO)):
        t = t.cut(cilindro(3.4, 10, x, y, ZT - 5)).cut(cilindro(11, 4.5, x, y, ZT - 4.5))
    for nombre, (x, y) in TOMAS.items():
        for dy in (-SEP_CARAS / 2, SEP_CARAS / 2):          # dos caras de 35 × 30 mm
            t = t.cut(ranura(35.0, 30.0, 12, x, y + dy, ZT - 5))
        for dy in (-SEP_TORN / 2, SEP_TORN / 2):
            t = t.cut(cilindro(3.6, 12, x, y + dy, ZT - 5))
    t = t.cut(Part.makeBox(19, 46, 12, V(Q1[0] - 9.5, Q1[1] - 23, ZT - 5)))     # ventana del breaker
    t = t.cut(cilindro(12.4, 12, H1[0], H1[1], ZT - 5))                         # piloto neón
    for s, tam, x, y in (("AUXILIAR", 5, 45, 108), ("SALIDA CH1", 5, 150, 108), ("SALIDA CH2", 5, 255, 108),
                         ("Q1 15 A", 4, Q1[0], 145), ("H1", 4, H1[0], 150),
                         ("BANCO DE MEDICION  120 V  15 A", 6.5, 200, 160)):
        t = t.cut(texto(s, tam, x, y, ZT + E_TAPA - 0.6, 1))
    return t.removeSplitter()


def toma(m, nombre, x, y):
    """Tomacorriente doble: cuerpo bajo la tapa, caras que asoman, yugo metálico y bornes."""
    cuerpo_t = Part.makeBox(33, 75, 28, V(x - 16.5, y - 37.5, ZT - 28))
    caras = [ranura(34.2, 29.2, 3, x, y + dy, ZT) for dy in (-SEP_CARAS / 2, SEP_CARAS / 2)]
    for cara in caras:
        cuerpo_t = cuerpo_t.fuse(cara)
    # ranuras de las clavijas (corta = fase, larga = neutro) y agujero de tierra
    for dy in (-SEP_CARAS / 2, SEP_CARAS / 2):
        cuerpo_t = cuerpo_t.cut(Part.makeBox(1.8, 7.0, 6, V(x + 5.5, y + dy - 1, ZT - 2)))
        cuerpo_t = cuerpo_t.cut(Part.makeBox(1.8, 8.5, 6, V(x - 7.3, y + dy - 1, ZT - 2)))
        cuerpo_t = cuerpo_t.cut(cilindro(4.5, 6, x, y + dy - 6.5, ZT - 2))
    m.agregar(f"{nombre}_cuerpo", cuerpo_t, "blanco", "montado")
    yugo = Part.makeBox(18, 107, 1.2, V(x - 9, y - 53.5, ZT - 1.4))
    m.agregar(f"{nombre}_yugo", yugo, "metal", "montado")
    # bornes: fase (latón) a la derecha, neutro (plateado) a la izquierda, tierra (verde) abajo
    m.agregar(f"{nombre}_borne_fase", cilindro(6, 3, x + 16.5, y, ZT - 14, "x"), "laton", "montado")
    m.agregar(f"{nombre}_borne_neutro", cilindro(6, 3, x - 19.5, y, ZT - 14, "x"), "metal", "montado")
    m.agregar(f"{nombre}_borne_tierra", cilindro(6, 3, x, y + 37.5, ZT - 10, "y"), "tierra", "montado")


def pinza(m, nombre, x, y):
    """SCT-013-000: cuerpo de 31 × 56 × 25 mm (eje de la ventana en X), ventana de 13 mm."""
    zc = Z_HILO
    cuerpo_p = caja_redondeada(25, 31, 56, 0, x - 12.5, y - 15.5, zc - 40)
    cuerpo_p = cuerpo_p.cut(cilindro(13, 30, x - 15, y, zc, "x"))
    try:
        cuerpo_p = cuerpo_p.makeFillet(3, cuerpo_p.Edges[:12])
    except Exception:
        pass
    m.agregar(f"{nombre}_pinza", cuerpo_p, "pinza")
    m.agregar(f"{nombre}_cierre", Part.makeBox(25.4, 4, 6, V(x - 12.7, y - 2, zc + 14)), "negro")
    m.agregar(f"{nombre}_salida", cilindro(6, 6, x, y, zc - 46), "negro")


def construir():
    m = Modelo("banco")
    m.agregar("Cuerpo", cuerpo(), "caja_gris", "cuerpo")
    m.agregar("Tapa", tapa(), "tapa_gris", "tapa")
    for n, (x, y) in TOMAS.items():
        toma(m, n, x, y)
    # piloto neón con lente roja
    m.agregar("H1_piloto", cilindro(12, 25, H1[0], H1[1], ZT - 22).fuse(cilindro(15, 2, H1[0], H1[1], ZT + E_TAPA)),
              "negro", "montado")
    m.agregar("H1_lente", Part.makeSphere(6, V(H1[0], H1[1], ZT + E_TAPA + 2)).common(
        cilindro(14, 8, H1[0], H1[1], ZT + E_TAPA + 2)), "rojo", "montado")
    # riel DIN y breaker 1P de 15 A (18 × 85 mm, frente de 45 mm que asoma por la tapa)
    m.agregar("Riel_DIN", Part.makeBox(130, 35, 7.5, V(10, Q1[1] - 17.5, PARED + 15)), "metal")
    zb = PARED + 15 + 7.5
    q = Part.makeBox(18, 85, 60, V(Q1[0] - 9, Q1[1] - 42.5, zb))
    q = q.fuse(Part.makeBox(18, 45, ZT - zb - 60 + 0.5, V(Q1[0] - 9, Q1[1] - 22.5, zb + 60)))
    m.agregar("Q1_breaker", q, "blanco")
    m.agregar("Q1_palanca", Part.makeBox(8, 12, 9, V(Q1[0] - 4, Q1[1] - 2, ZT + 0.5)), "negro")
    # conectores de palanca sobre el piso: W1 neutro, W2 tierra, W3 fase (L_SW)
    for nombre, (x, y), vias in (("W1", (60, 152), 5), ("W2", (60, 166), 5), ("W3", (75, 82), 5)):
        b = Part.makeBox(6.2 * vias, 18.7, 8.5, V(x - 3.1 * vias, y - 9.35, PARED))
        m.agregar(f"{nombre}_conector", b, "gris")
        for k in range(vias):
            m.agregar(f"{nombre}_palanca_{k}", Part.makeBox(4.8, 9, 3, V(x - 3.1 * vias + 0.7 + 6.2 * k, y - 1, PARED + 8.5)),
                      "naranja")
    for n, (x, y) in PINZAS.items():
        pinza(m, n, x, y)
    # prensaestopas
    m.agregar("PG11", orientar(prensaestopas(18.6), "x", -1, PARED + 4, 140, 40), "negro")
    m.agregar("PG9", orientar(prensaestopas(15.2), "x", 1, W - PARED - 4, 160, 40), "negro")
    m.agregar("Cable_entrada", tubo([(-80, 140, 40), (-20, 140, 40), (PARED + 20, 140, 40)], 9.5), "negro")

    zb_w = PARED + 4      # altura de entrada a los conectores
    zt_b = ZT - 14        # altura de los bornes de las tomas
    d = D_HILO
    # entrada: fase a Q1, neutro a W1, tierra a W2
    m.agregar("L_red", tubo([(PARED + 20, 141.5, 41.5), (Q1[0], 141.5, 41.5), (Q1[0], Q1[1] + 42.5, 41.5)], d), "fase")
    m.agregar("N_red", tubo([(PARED + 20, 139, 38), (30, 139, 38), (30, 152, zb_w), (45, 152, zb_w)], d), "neutro")
    m.agregar("PE_red", tubo([(PARED + 20, 137, 41), (22, 137, 41), (22, 166, zb_w), (45, 166, zb_w)], d), "tierra")
    # L_SW: Q1 → W3 → X0, H1 y una rama por pinza
    m.agregar("L_SW", tubo([(Q1[0], Q1[1] - 42.5, 41.5), (Q1[0], 82, zb_w), (90, 82, zb_w)], d), "fase")
    x0b = (TOMAS["X0"][0] + 16.5, TOMAS["X0"][1])
    m.agregar("L_X0", tubo([(60, 82, zb_w), (x0b[0] + 8, 82, zb_w), (x0b[0] + 8, x0b[1], zt_b), (x0b[0] + 3, x0b[1], zt_b)], d),
              "fase")
    m.agregar("L_H1", tubo([(66, 86, zb_w), (66, H1[1] - 8, 30), (H1[0], H1[1] - 3, ZT - 22)], 1.6), "fase")
    for n, salida, yr in (("CT1", "X1", 124.0), ("CT2", "X2", 128.0)):
        xp, yp = PINZAS[n]
        xb, yb = TOMAS[salida][0] + 16.5, TOMAS[salida][1]
        inicio = (84, 82, zb_w) if n == "CT1" else (78, 82, zb_w)
        ruta = [inicio, (inicio[0], yp, zb_w + (0 if n == "CT1" else 4)), (xp - 30, yp, Z_HILO), (xp + 30, yp, Z_HILO),
                (xb + 8, yp, Z_HILO), (xb + 8, yb, zt_b), (xb + 3, yb, zt_b)]
        if n == "CT2":   # pasa por detrás de CT1 para no cruzar su ventana
            ruta = [inicio, (inicio[0], 160, zb_w + 4), (xp - 40, 160, zb_w + 4), (xp - 30, yp, Z_HILO), (xp + 30, yp, Z_HILO),
                    (xb + 8, yp, Z_HILO), (xb + 8, yb, zt_b), (xb + 3, yb, zt_b)]
        m.agregar(f"L_{salida}_{n}", tubo(ruta, d), "fase")
    # neutros y tierras a cada toma
    for k, (nombre, (x, y)) in enumerate(TOMAS.items()):
        m.agregar(f"N_{nombre}", tubo([(75, 150 + k, zb_w), (x - 25, 150 + k, zb_w), (x - 25, y, zt_b), (x - 21, y, zt_b)], d),
                  "neutro")
        m.agregar(f"PE_{nombre}", tubo([(75, 166 + k, zb_w), (x + 4 * (k - 1), 166 + k, zb_w),
                                        (x + 4 * (k - 1), y + 39, ZT - 10), (x, y + 39, ZT - 10)], d), "tierra")
    m.agregar("N_H1", tubo([(48, 152, zb_w), (48, H1[1], 30), (H1[0] - 3, H1[1], ZT - 22)], 1.6), "neutro")
    # cables de las pinzas hacia el PG9
    for n, (xp, yp) in PINZAS.items():
        m.agregar(f"Cable_{n}", tubo([(xp, yp, Z_HILO - 46), (xp, yp, 10), (xp, 160 + (2 if n == "CT2" else -2), 10),
                                      (W - 30, 160 + (2 if n == "CT2" else -2), 40), (W + 60, 160, 40)], 3.5), "cable_pinza")
    m.guardar(AQUI, [("Cuerpo", "banco-cuerpo.stl", False), ("Tapa", "banco-tapa.stl", True)])
    print("Banco guardado")


construir()
