"""Modelo paramétrico del banco de medición (FreeCAD 1.1, freecadcmd).

El banco es lo mínimo para medir cualquier equipo sin cortar su cable: una clavija que se
enchufa a la pared, el cordón, un tomacorriente donde se conecta el equipo y, entre los dos,
la fase sacada fuera de la caja en un lazo aislado donde se cierra la pinza SCT-013-000.
El neutro y la tierra van directo al tomacorriente y nunca pasan por la pinza.

Caja de 130 × 90 × 65 mm (cuerpo de 62 mm y tapa de 3 mm). Origen en la esquina frontal
izquierda inferior: X a la derecha, Y hacia el fondo, Z hacia arriba.
"""
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import Part

from comun import V, Modelo, caja_redondeada, cilindro, orientar, prensaestopas, ranura, texto, tubo

W, D, H_CUERPO, E_TAPA = 130.0, 90.0, 62.0, 3.0
PARED, R_ESQ, TORNILLO = 3.0, 5.0, 6.0
ZT = H_CUERPO                          # cara inferior de la tapa
TOMA = (65.0, 45.0)                    # centro del tomacorriente doble X1 (eje del aparato en X)
SEP_CARAS, SEP_TORN = 38.8, 83.3       # separación de las dos caras y de los tornillos del aparato
D_HILO = 3.0                           # THHN 14 AWG con aislamiento
Z_ENTRADA = 30.0                       # altura del cordón (PG11, pared izquierda)
Z_LAZO = 40.0                          # altura del lazo exterior (PG7, pared del fondo)
X_LAZO = (52.5, 77.5)                  # las dos patas del lazo, separadas 25 mm
L_LAZO = 70.0                          # largo de cada pata fuera de la caja
Y_PINZA = D + 38.0                     # la pinza abraza la pata izquierda a esta distancia
Z_BORNE = ZT - 14                      # altura de los tornillos del tomacorriente


def cuerpo():
    ext = caja_redondeada(W, D, H_CUERPO, R_ESQ)
    c = ext.cut(caja_redondeada(W - 2 * PARED, D - 2 * PARED, H_CUERPO, R_ESQ - PARED, PARED, PARED, PARED))
    for x, y in ((TORNILLO, TORNILLO), (W - TORNILLO, TORNILLO), (TORNILLO, D - TORNILLO), (W - TORNILLO, D - TORNILLO)):
        c = c.fuse(cilindro(8, H_CUERPO - PARED, x, y, PARED)).cut(cilindro(3.4, 12, x, y, H_CUERPO - 12))
    c = c.cut(cilindro(18.8, 10, -2, TOMA[1], Z_ENTRADA, "x"))           # PG11 del cordón
    for x in X_LAZO:                                                     # dos PG7 del lazo
        c = c.cut(cilindro(12.7, 10, x, D - 5, Z_LAZO, "y"))
    for x, y in ((15, 15), (W - 15, 15), (15, D - 15), (W - 15, D - 15)):   # patas
        c = c.fuse(cilindro(12, 3, x, y, -3))
    return c.removeSplitter()


def tapa():
    x, y = TOMA
    t = caja_redondeada(W, D, E_TAPA, R_ESQ, 0, 0, ZT)
    labio = caja_redondeada(W - 2 * PARED - 0.8, D - 2 * PARED - 0.8, 4, R_ESQ - PARED, PARED + 0.4, PARED + 0.4, ZT - 4)
    labio = labio.cut(caja_redondeada(W - 2 * PARED - 4.8, D - 2 * PARED - 4.8, 4, 1, PARED + 2.4, PARED + 2.4, ZT - 4))
    t = t.fuse(labio)
    for xt, yt in ((TORNILLO, TORNILLO), (W - TORNILLO, TORNILLO), (TORNILLO, D - TORNILLO), (W - TORNILLO, D - TORNILLO)):
        t = t.cut(cilindro(3.4, 10, xt, yt, ZT - 5)).cut(cilindro(7, 3.5, xt, yt, ZT + E_TAPA - 3.5))
    for dx in (-SEP_CARAS / 2, SEP_CARAS / 2):              # dos caras de 30 × 35 mm
        t = t.cut(ranura(30.0, 35.0, 12, x + dx, y, ZT - 5))
    for dx in (-SEP_TORN / 2, SEP_TORN / 2):
        t = t.cut(cilindro(3.6, 12, x + dx, y, ZT - 5))
    for s, tam, xs, ys in (("BANCO DE MEDICION  120 V  15 A", 5, W / 2, 9),
                           ("X1", 5, x, 21),
                           ("LAZO DE MEDICION: PINZA AQUI", 4.2, W / 2, D - 15)):
        t = t.cut(texto(s, tam, xs, ys, ZT + E_TAPA - 0.6, 1))
    return t.removeSplitter()


def toma(m):
    """Tomacorriente doble NEMA 5-15R con su eje a lo largo de X (la caja mide 84 mm por dentro en Y)."""
    x, y = TOMA
    c = Part.makeBox(75, 33, 28, V(x - 37.5, y - 16.5, ZT - 28))
    for dx in (-SEP_CARAS / 2, SEP_CARAS / 2):
        c = c.fuse(ranura(29.2, 34.2, 3, x + dx, y, ZT))
    for dx in (-SEP_CARAS / 2, SEP_CARAS / 2):
        # ranura corta = fase (lado del fondo), larga = neutro (lado del frente), agujero de tierra
        c = c.cut(Part.makeBox(7.0, 1.8, 6, V(x + dx - 1, y + 5.5, ZT - 2)))
        c = c.cut(Part.makeBox(8.5, 1.8, 6, V(x + dx - 1, y - 7.3, ZT - 2)))
        c = c.cut(cilindro(4.5, 6, x + dx - 6.5, y, ZT - 2))
    m.agregar("X1_cuerpo", c, "blanco", "montado")
    m.agregar("X1_yugo", Part.makeBox(107, 18, 1.2, V(x - 53.5, y - 9, ZT - 1.4)), "metal", "montado")
    # tornillos: fase (latón) al fondo, neutro (plateado) al frente, tierra (verde) en el extremo derecho
    m.agregar("X1_borne_fase", cilindro(6, 3, x, y + 16.5, Z_BORNE, "y"), "laton", "montado")
    m.agregar("X1_borne_neutro", cilindro(6, 3, x, y - 19.5, Z_BORNE, "y"), "metal", "montado")
    m.agregar("X1_borne_tierra", cilindro(6, 3, x + 37.5, y, Z_BORNE - 6, "x"), "tierra", "montado")


def clavija(m, x):
    """Clavija NEMA 5-15P al final del cordón: cuerpo moldeado, dos patas planas y la de tierra."""
    y, z = TOMA[1], Z_ENTRADA
    cuerpo_c = Part.makeBox(32, 38, 22, V(x - 32, y - 19, z - 11))
    cuerpo_c = cuerpo_c.fuse(Part.makeCone(9, 6, 14, V(x, y, z), V(1, 0, 0)))
    try:
        cuerpo_c = cuerpo_c.makeFillet(3, [e for e in cuerpo_c.Edges if e.Length > 20][:8])
    except Exception:
        pass
    m.agregar("P1_clavija", cuerpo_c, "negro")
    for dy in (-6.35, 6.35):
        m.agregar(f"P1_pata_{'n' if dy < 0 else 'f'}", Part.makeBox(16, 1.5, 6.3, V(x - 48, y + dy - 0.75, z - 3.15)), "metal")
    m.agregar("P1_pata_t", cilindro(4.8, 19, x - 51, y, z - 7, "x"), "metal")


def pinza(m):
    """SCT-013-000 cerrada sobre la pata izquierda del lazo: cuerpo de 31 × 25 × 56 mm, ventana de 13 mm."""
    x, y, z = X_LAZO[0], Y_PINZA, Z_LAZO
    c = caja_redondeada(31, 25, 56, 0, x - 15.5, y - 12.5, z - 40)
    c = c.cut(cilindro(13, 30, x, y - 15, z, "y"))
    try:
        c = c.makeFillet(3, c.Edges[:12])
    except Exception:
        pass
    m.agregar("CT1_pinza", c, "pinza")
    m.agregar("CT1_cierre", Part.makeBox(6, 25.4, 4, V(x - 3, y - 12.7, z + 15)), "negro")
    # cable de la pinza: sale por el costado izquierdo y termina en el plug de 3,5 mm (va a J2 del medidor)
    cable = [(x - 15.5, y, z - 32), (x - 40, y, z - 32), (x - 70, y + 20, z - 32), (x - 95, y + 20, z - 32)]
    m.agregar("CT1_cable", tubo(cable, 3.5), "cable_pinza")
    xp = x - 95
    m.agregar("CT1_plug_cuerpo", cilindro(8, 18, xp - 18, y + 20, z - 32, "x"), "negro")
    m.agregar("CT1_plug_punta", cilindro(3.5, 14, xp - 32, y + 20, z - 32, "x"), "metal")


def construir():
    m = Modelo("banco")
    m.agregar("Cuerpo", cuerpo(), "caja_gris", "cuerpo")
    m.agregar("Tapa", tapa(), "tapa_gris", "tapa")
    toma(m)

    # prensaestopas: PG11 del cordón (izquierda) y dos PG7 del lazo (fondo)
    m.agregar("PG11", orientar(prensaestopas(18.6), "x", -1, PARED + 4, TOMA[1], Z_ENTRADA), "negro")
    for k, x in enumerate(X_LAZO):
        m.agregar(f"PG7_{k + 1}", orientar(prensaestopas(12.5), "y", 1, x, D - PARED - 4, Z_LAZO), "negro")

    # cordón SJT 3 × 14 AWG de entrada (tramo visible de 140 mm) y clavija
    x_clavija = -140.0
    m.agregar("Cordon", tubo([(x_clavija, TOMA[1], Z_ENTRADA), (PARED + 16, TOMA[1], Z_ENTRADA)], 9.5), "negro")
    clavija(m, x_clavija)

    x, y = TOMA
    e = PARED + 16                     # donde termina la chaqueta del cordón, dentro de la caja
    d = D_HILO
    # neutro (blanco) directo al tornillo plateado; tierra (verde) directo al tornillo verde
    m.agregar("N_X1", tubo([(e, y - 2, Z_ENTRADA), (e + 6, y - 2, Z_ENTRADA), (e + 6, y - 24, Z_BORNE),
                            (x, y - 24, Z_BORNE), (x, y - 21, Z_BORNE)], d), "neutro")
    m.agregar("PE_X1", tubo([(e, y, Z_ENTRADA - 2), (e + 4, y, 14), (x + 46, y - 6, 14), (x + 46, y, Z_BORNE - 6),
                             (x + 41, y, Z_BORNE - 6)], d), "tierra")
    # fase (negro): sale por el primer PG7, forma el lazo exterior y vuelve por el segundo al tornillo de latón
    xa, xb = X_LAZO
    yf = D + L_LAZO
    r = (xb - xa) / 2
    curva = [(xa + r - r * math.cos(math.radians(a)), yf + r * math.sin(math.radians(a)), Z_LAZO) for a in range(0, 181, 15)]
    lazo = ([(e, y + 2, Z_ENTRADA), (e + 8, y + 2, Z_ENTRADA), (e + 8, D - 18, Z_LAZO), (xa, D - 18, Z_LAZO)]
            + [(xa, yf, Z_LAZO)] + curva[1:-1] + [(xb, yf, Z_LAZO)]
            + [(xb, D - 18, Z_LAZO), (xb, y + 26, Z_BORNE), (x, y + 26, Z_BORNE), (x, y + 21, Z_BORNE)])
    m.agregar("L_lazo", tubo(lazo, d), "fase")
    pinza(m)

    m.guardar(AQUI, [("Cuerpo", "banco-cuerpo.stl", False), ("Tapa", "banco-tapa.stl", True)])
    print("Banco guardado")


construir()
