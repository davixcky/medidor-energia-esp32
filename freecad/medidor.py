"""Modelo paramétrico del gabinete y el ensamble del medidor (FreeCAD 1.1, freecadcmd).

Cotas tomadas de la sección 7.8 del documento y de herramientas/figuras.py (gabinete()).
La placa perforada es el STEP exportado por KiCad (../hardware/3d/medidor-placa.step); si no
existe, se usa una placa de reemplazo del mismo tamaño y el script lo avisa.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import FreeCAD as App
import Part

from comun import V, Modelo, caja_redondeada, cilindro, orientar, prensaestopas, ranura, texto, tubo

# ---------------------------------------------------------------- parámetros
W, D, H_CUERPO, E_TAPA = 200.0, 150.0, 72.0, 3.0
PARED, PISO, R_ESQ = 2.5, 2.5, 5.0
Y_TABIQUE, E_TABIQUE = 108.0, 3.0
TORNILLO = 7.0                    # distancia de los tornillos de la tapa a los bordes
PLACA_X, PLACA_Y, PLACA_W, PLACA_D = 25.0, 10.0, 150.0, 90.0
SEPARADOR = 10.0
Z_PLACA = PISO + SEPARADOR
Z_JACKS = 26.0
STEP_PLACA = os.path.join(AQUI, "..", "hardware", "3d", "medidor-placa.step")


def cuerpo():
    ext = caja_redondeada(W, D, H_CUERPO, R_ESQ)
    inte = caja_redondeada(W - 2 * PARED, D - 2 * PARED, H_CUERPO, R_ESQ - PARED, PARED, PARED, PISO)
    c = ext.cut(inte)
    # tabique de 3 mm que separa la zona de red, con collarín para el cable de 3 hilos
    tab = Part.makeBox(W - 2 * PARED, E_TABIQUE, H_CUERPO - PISO - 4, V(PARED, Y_TABIQUE, PISO))
    collar = cilindro(12, 10, 25, Y_TABIQUE - 3.5, 30, "y")
    tab = tab.fuse(collar).cut(cilindro(6.5, 12, 25, Y_TABIQUE - 4.5, 30, "y"))
    c = c.fuse(tab)
    # postes de la tapa (M3 con inserto) en las cuatro esquinas
    for x, y in ((TORNILLO, TORNILLO), (W - TORNILLO, TORNILLO), (TORNILLO, D - TORNILLO), (W - TORNILLO, D - TORNILLO)):
        c = c.fuse(cilindro(8, H_CUERPO - PISO, x, y, PISO)).cut(cilindro(4.0, 12, x, y, H_CUERPO - 12))
    # separadores de la placa perforada (los cuatro agujeros a 4 mm de las esquinas)
    for x, y in ((4, 4), (PLACA_W - 4, 4), (4, PLACA_D - 4), (PLACA_W - 4, PLACA_D - 4)):
        px, py = PLACA_X + x, PLACA_Y + y
        c = c.fuse(cilindro(6, SEPARADOR, px, py, PISO)).cut(cilindro(2.5, SEPARADOR, px, py, PISO + 2))
    # postes del módulo ZMPT101B (49 × 19 mm) en la zona de red
    for x, y in ((73, 121), (116, 121), (73, 134), (116, 134)):
        c = c.fuse(cilindro(5, 8, x, y, PISO)).cut(cilindro(2.5, 8, x, y, PISO + 1))
    # pared izquierda: jacks J2 (CH1) y J3 (CH2) de 3,5 mm y jack de alimentación
    for y, d in ((PLACA_Y + 47, 6.2), (PLACA_Y + 33, 6.2), (PLACA_Y + 9, 8.2)):
        c = c.cut(cilindro(d, 10, -1, y, Z_JACKS, "x"))
    # pared frontal: ventana del USB del DevKitC (10 × 6 mm)
    c = c.cut(Part.makeBox(10, 10, 6, V(PLACA_X + 98, -2, Z_PLACA + 9)))
    # pared posterior: prensaestopas PG7 (rosca de 12,5 mm)
    c = c.cut(cilindro(12.7, 10, 180, D - 4, 40, "y"))
    # ranuras de ventilación en la pared derecha (zona de MBT)
    for k in range(6):
        c = c.cut(ranura(10, 3, 1, 0, 0, 0).rotated(V(0, 0, 0), V(0, 1, 0), 90).translated(V(W + 1, 25 + 10 * k, 45)))
    return c.removeSplitter()


def tapa():
    t = caja_redondeada(W, D, E_TAPA, R_ESQ, 0, 0, H_CUERPO)
    holg = 0.4
    labio = caja_redondeada(W - 2 * PARED - 2 * holg, D - 2 * PARED - 2 * holg, 4, R_ESQ - PARED,
                            PARED + holg, PARED + holg, H_CUERPO - 4)
    labio = labio.cut(caja_redondeada(W - 2 * PARED - 2 * holg - 3, D - 2 * PARED - 2 * holg - 3, 4, 1,
                                      PARED + holg + 1.5, PARED + holg + 1.5, H_CUERPO - 4))
    t = t.fuse(labio)
    for x, y in ((TORNILLO, TORNILLO), (W - TORNILLO, TORNILLO), (TORNILLO, D - TORNILLO), (W - TORNILLO, D - TORNILLO)):
        t = t.cut(cilindro(3.4, 10, x, y, H_CUERPO - 5)).cut(Part.makeCone(1.7, 3.3, 1.6, V(x, y, H_CUERPO + E_TAPA - 1.6)))
        # el labio se recorta alrededor de los postes
        t = t.cut(cilindro(10, 4.5, x, y, H_CUERPO - 4.5))
    # ventana OLED 26,5 × 15 con rebaje de 1,5 mm
    t = t.cut(Part.makeBox(26.5, 15, 10, V(40, 55, H_CUERPO - 1)))
    t = t.cut(Part.makeBox(32.5, 21, 1.5, V(37, 52, H_CUERPO + E_TAPA - 1.5)))
    t = t.cut(cilindro(5.2, 10, 95, 62.5, H_CUERPO - 1))          # LED de estado
    for x in (125, 155):                                          # pulsadores de 12 mm
        t = t.cut(cilindro(12.2, 10, x, 62.5, H_CUERPO - 1))
    # rótulos grabados 0,6 mm
    for s, tam, x, y in (("OLED", 4, 53.25, 47), ("ESTADO", 3.5, 95, 52), ("SW1", 3.5, 125, 52), ("SW2", 3.5, 155, 52),
                         ("MEDIDOR DE ENERGIA", 6, 100, 22), ("CH1 TOTAL  -  CH2 SUBCIRCUITO", 3.5, 100, 14)):
        t = t.cut(texto(s, tam, x, y, H_CUERPO + E_TAPA - 0.6, 1))
    return t.removeSplitter()


def placa(m):
    if os.path.exists(STEP_PLACA):
        import Import
        antes = set(o.Name for o in m.doc.Objects)
        Import.insert(STEP_PLACA, m.doc.Name)
        nuevos = [o for o in m.doc.Objects if o.Name not in antes]
        nombres = [o.Name for o in nuevos]
        formas = [o.Shape for o in nuevos if hasattr(o, "Shape") and not o.Shape.isNull() and o.Shape.Volume > 0
                  and o.TypeId == "Part::Feature"]
        if not formas:
            formas = [o.Shape for o in nuevos if hasattr(o, "Shape") and not o.Shape.isNull()]
        comp = Part.makeCompound(formas)
        bb = comp.BoundBox
        for n in nombres:
            if m.doc.getObject(n) is not None:
                m.doc.removeObject(n)
        # el sustrato es la pieza más grande y plana: se alinea su esquina con la posición de la placa
        sust = max(formas, key=lambda f: f.BoundBox.XLength * f.BoundBox.YLength)
        sb = sust.BoundBox
        comp.translate(V(PLACA_X - sb.XMin, PLACA_Y - sb.YMin, Z_PLACA - sb.ZMin))
        print(f"Placa de KiCad importada: {bb.XLength:.1f} × {bb.YLength:.1f} × {bb.ZLength:.1f} mm")
        o = m.agregar("Placa_KiCad", comp, "placa", "interior")
        # traslado aplicado, para que render.py vuelva a importar el STEP con sus colores
        o.addProperty("App::PropertyVector", "Traslado", "Render")
        o.Traslado = V(PLACA_X - sb.XMin, PLACA_Y - sb.YMin, Z_PLACA - sb.ZMin)
        o.addProperty("App::PropertyString", "ArchivoSTEP", "Render")
        o.ArchivoSTEP = os.path.relpath(STEP_PLACA, AQUI)
        return True
    print("AVISO: no existe", STEP_PLACA, "— se usa una placa de reemplazo")
    p = Part.makeBox(PLACA_W, PLACA_D, 1.6, V(PLACA_X, PLACA_Y, Z_PLACA))
    for x, y in ((4, 4), (PLACA_W - 4, 4), (4, PLACA_D - 4), (PLACA_W - 4, PLACA_D - 4)):
        p = p.cut(cilindro(3.2, 3, PLACA_X + x, PLACA_Y + y, Z_PLACA - 1))
    m.agregar("Placa_reemplazo", p, "placa", "interior")
    esp = Part.makeBox(28, 54, 12, V(PLACA_X + 89, PLACA_Y + 2, Z_PLACA + 1.6))
    m.agregar("ESP32_reemplazo", esp, "negro", "interior")
    return False


def interior(m):
    # zona de red: módulo ZMPT101B, portafusible F1 y bornera J4
    zm = Part.makeBox(49, 19, 1.6, V(70, 118, PISO + 8))
    m.agregar("ZMPT101B_PCB", zm, "azul")
    m.agregar("ZMPT101B_trafo", Part.makeBox(19, 17, 17, V(73, 119, PISO + 9.6)), "azul")
    m.agregar("ZMPT101B_bornes", Part.makeBox(7, 10, 10, V(112, 122, PISO + 9.6)), "verde_pcb")
    m.agregar("ZMPT101B_pot", cilindro(6, 5, 100, 127, PISO + 9.6), "azul")
    f1 = Part.makeBox(25, 9, 10, V(35, 120, PISO)).fuse(cilindro(5, 20, 37.5, 124.5, PISO + 7, "x"))
    m.agregar("F1_portafusible", f1, "negro")
    m.agregar("J4_bornera", Part.makeBox(18, 10, 12, V(135, 119, PISO)), "verde_pcb")
    m.agregar("PG7", orientar(prensaestopas(12.5), "y", 1, 180, D - PARED - 4, 40), "negro")
    # cableado de red: fase negro, neutro blanco, tierra verde (18 AWG)
    m.agregar("Red_fase", tubo([(178, D - 6, 40), (178, 135, 40), (160, 135, 14), (153, 125, 8)], 2.4), "fase")
    m.agregar("Red_neutro", tubo([(182, D - 6, 40), (182, 132, 40), (162, 132, 14), (153, 122, 8)], 2.4), "neutro")
    m.agregar("Red_fase_F1", tubo([(135, 125, 9), (62, 125, 9), (60, 124.5, 12)], 2.0), "fase")
    m.agregar("Red_F1_ZMPT", tubo([(35, 124.5, 12), (31, 124.5, 12), (31, 140, 12), (115, 140, 14), (115, 131, 16)], 2.0), "fase")
    m.agregar("Red_N_ZMPT", tubo([(135, 121, 9), (118, 121, 9), (115, 125, 16)], 2.0), "neutro")
    # cable de 3 hilos ZMPT101B → J5 a través del collarín del tabique
    for k, col in enumerate(("rojo", "verde_led", "negro")):
        dx = (k - 1) * 1.8
        m.agregar(f"ZMPT_J5_{k}", tubo([(70, 126 + dx, 14), (25 + dx, 126, 30), (25 + dx, 100, 30),
                                       (30 + dx, PLACA_Y + 80, Z_PLACA + 6)], 1.4), col)
    # pared izquierda: jacks de 3,5 mm y jack de alimentación con su tuerca
    for nombre, y, d in (("J2_CH1", PLACA_Y + 47, 6), ("J3_CH2", PLACA_Y + 33, 6), ("Jack_5V", PLACA_Y + 9, 8)):
        cuerpo_j = cilindro(d + 4, 14, PARED, y, Z_JACKS, "x")
        tuerca = cilindro(d + 3, 2, -2, y, Z_JACKS, "x").cut(cilindro(d, 3, -2.5, y, Z_JACKS, "x"))
        m.agregar(nombre, cuerpo_j.fuse(tuerca), "negro")
    # cables de los jacks a la placa (amarillo = señal, violeta = VBIAS, rojo/negro = 5 V)
    for y, cols in ((PLACA_Y + 47, ("naranja", "azul")), (PLACA_Y + 33, ("naranja", "azul")), (PLACA_Y + 9, ("rojo", "negro"))):
        for k, col in enumerate(cols):
            dy = (k - 0.5) * 2.2
            m.agregar(f"Cable_jack_{int(y)}_{k}", tubo([(PARED + 14, y + dy, Z_JACKS), (22, y + dy, Z_JACKS),
                                                       (PLACA_X + 3, y + dy, Z_PLACA + 5)], 1.2), col)
    # bajo la tapa: OLED, LED y pulsadores
    zt = H_CUERPO
    m.agregar("OLED_modulo", Part.makeBox(27.3, 27.8, 1.6, V(39.6, 49.6, zt - 4.6)), "azul", "tapa")
    m.agregar("OLED_pantalla", Part.makeBox(26.5, 15, 1.4, V(40, 55, zt - 3.0)), "oled", "tapa")
    m.agregar("D8_LED", cilindro(5, 8, 95, 62.5, zt - 5).fuse(Part.makeSphere(2.5, V(95, 62.5, zt + 3))), "verde_led", "tapa")
    for nombre, x in (("SW1", 125), ("SW2", 155)):
        cu = cilindro(12, 12, x, 62.5, zt - 12)
        ta = cilindro(9, 4, x, 62.5, zt + 1)
        tu = cilindro(16, 2, x, 62.5, zt - 2.5).cut(cilindro(12, 3, x, 62.5, zt - 3))
        m.agregar(nombre, cu.fuse([ta, tu]), "gris", "tapa")
    # rótulo de advertencia sobre la zona de red (relieve rojo de 0,4 mm)
    m.agregar("Rotulo_peligro", texto("PELIGRO 120 V - NO ABRIR ENERGIZADO", 5, 100, 128, zt + E_TAPA, 0.4),
              "rojo_texto", "tapa")


def construir():
    m = Modelo("medidor")
    m.agregar("Cuerpo", cuerpo(), "abs", "cuerpo")
    m.agregar("Tapa", tapa(), "tapa", "tapa")
    integrada = placa(m)
    interior(m)
    m.guardar(AQUI, [("Cuerpo", "medidor-cuerpo.stl", False), ("Tapa", "medidor-tapa.stl", True)])
    print("Medidor guardado. Placa de KiCad integrada:", integrada)


construir()
