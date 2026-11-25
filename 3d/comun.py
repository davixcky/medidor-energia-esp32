"""Piezas y utilidades comunes para los modelos de FreeCAD del medidor y del banco.

Todas las cotas están en milímetros. El origen de cada caja es la esquina frontal izquierda
inferior: X hacia la derecha, Y hacia el fondo y Z hacia arriba.
"""
import math
import os

import FreeCAD as App
import Part

V = App.Vector
FUENTE = "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"

# Colores (R, G, B) de 0 a 1
COLOR = {
    "abs": (0.86, 0.87, 0.88),
    "tapa": (0.80, 0.82, 0.84),
    "caja_gris": (0.42, 0.45, 0.48),
    "tapa_gris": (0.50, 0.53, 0.56),
    "fase": (0.08, 0.08, 0.08),
    "neutro": (0.96, 0.96, 0.96),
    "tierra": (0.10, 0.62, 0.20),
    "pinza": (0.17, 0.22, 0.25),
    "cable_pinza": (0.30, 0.30, 0.32),
    "metal": (0.70, 0.72, 0.75),
    "laton": (0.80, 0.65, 0.30),
    "naranja": (1.00, 0.55, 0.05),
    "blanco": (0.97, 0.97, 0.95),
    "gris": (0.55, 0.57, 0.60),
    "negro": (0.12, 0.12, 0.13),
    "verde_pcb": (0.10, 0.45, 0.20),
    "azul": (0.10, 0.30, 0.75),
    "rojo": (0.85, 0.15, 0.10),
    "rojo_texto": (0.75, 0.05, 0.05),
    "verde_led": (0.15, 0.85, 0.25),
    "oled": (0.05, 0.10, 0.18),
    "placa": (0.82, 0.68, 0.42),
}


def caja_redondeada(lx, ly, lz, r, x=0, y=0, z=0):
    """Prisma con aristas verticales redondeadas."""
    s = Part.makeBox(lx, ly, lz, V(x, y, z))
    if r > 0:
        aristas = [e for e in s.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
        s = s.makeFillet(r, aristas)
    return s


def cilindro(d, h, x, y, z, eje="z"):
    direc = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}[eje]
    return Part.makeCylinder(d / 2, h, V(x, y, z), direc)


def ranura(lx, ly, h, x, y, z):
    """Abertura rectangular de extremos redondeados (ly = ancho), centrada en (x, y)."""
    r = min(lx, ly) / 2
    s = Part.makeBox(lx - 2 * r if lx > ly else lx, ly - 2 * r if ly >= lx else ly, h,
                     V(x - (lx / 2 - r if lx > ly else lx / 2), y - (ly / 2 - r if ly >= lx else ly / 2), z))
    if lx > ly:
        s = s.fuse([cilindro(ly, h, x - lx / 2 + r, y, z), cilindro(ly, h, x + lx / 2 - r, y, z)])
    else:
        s = s.fuse([cilindro(lx, h, x, y - ly / 2 + r, z), cilindro(lx, h, x, y + ly / 2 - r, z)])
    return s.removeSplitter()


def texto(t, tam, x, y, z, prof):
    """Texto extruido (para grabar o resaltar en la tapa)."""
    hilos = Part.makeWireString(t, FUENTE, tam, 0)
    caras = []
    for letra in hilos:
        if not letra:
            continue
        # Conserva contornos separados (tildes, puntos) y huecos interiores.
        f = Part.makeFace(letra, "Part::FaceMakerBullseye")
        caras.append(f)
    sol = Part.makeCompound([c.extrude(V(0, 0, prof)) for c in caras])
    bb = sol.BoundBox
    sol.translate(V(x - bb.XLength / 2 - bb.XMin, y - bb.YMin, z))
    return sol


def tubo(puntos, d):
    """Conductor como tubo: cilindros por tramo y esferas en los codos."""
    partes = []
    for a, b in zip(puntos, puntos[1:]):
        a, b = V(*a), V(*b)
        L = (b - a).Length
        if L < 1e-6:
            continue
        partes.append(Part.makeCylinder(d / 2, L, a, b - a))
    for p in puntos[1:-1]:
        partes.append(Part.makeSphere(d / 2, V(*p)))
    s = partes[0]
    if len(partes) > 1:
        s = Part.makeCompound(partes)
    return s


def prensaestopas(rosca_d, pared_x=None, pared_y=None, y=0, z=0, x=0, hacia=1, color_cuerpo="negro"):
    """Prensaestopas: tuerca hexagonal interior, cuerpo y domo exterior. Eje en X o en Y."""
    hexa = Part.makePolygon([V(rosca_d * 0.8 * math.cos(math.radians(a)), rosca_d * 0.8 * math.sin(math.radians(a)), 0)
                             for a in range(0, 361, 60)])
    tuerca = Part.Face(hexa).extrude(V(0, 0, 4))
    cuerpo = Part.makeCylinder(rosca_d / 2, 8, V(0, 0, 4))
    domo = Part.makeCone(rosca_d * 0.75, rosca_d * 0.45, rosca_d * 0.9, V(0, 0, 12))
    hexa2 = Part.Face(Part.makePolygon([V(rosca_d * 0.85 * math.cos(math.radians(a)), rosca_d * 0.85 * math.sin(math.radians(a)), 0)
                                        for a in range(0, 361, 60)])).extrude(V(0, 0, 5))
    hexa2.translate(V(0, 0, 4))
    s = Part.makeCompound([tuerca, cuerpo, hexa2, domo])
    return s


def orientar(s, eje, signo, x, y, z):
    """Gira una pieza modelada a lo largo de +Z para que apunte en ±X o ±Y y la coloca."""
    s = s.copy()
    if eje == "x":
        s.rotate(V(0, 0, 0), V(0, 1, 0), 90 * signo)
    elif eje == "y":
        s.rotate(V(0, 0, 0), V(1, 0, 0), -90 * signo)
    elif eje == "z" and signo < 0:
        s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    s.translate(V(x, y, z))
    return s


class Modelo:
    """Documento de FreeCAD con piezas nombradas, color y grupo (cuerpo, tapa o interior)."""

    def __init__(self, nombre):
        self.doc = App.newDocument(nombre)
        self.nombre = nombre

    def agregar(self, nombre, forma, color, grupo="interior"):
        o = self.doc.addObject("Part::Feature", nombre)
        o.Shape = forma
        o.addProperty("App::PropertyString", "ColorRGB", "Render")
        o.ColorRGB = ",".join(f"{c:.3f}" for c in COLOR[color])
        o.addProperty("App::PropertyString", "Grupo", "Render")
        o.Grupo = grupo
        return o

    def guardar(self, carpeta, imprimibles):
        self.doc.recompute()
        os.makedirs(os.path.join(carpeta, "stl"), exist_ok=True)
        self.doc.saveAs(os.path.join(carpeta, f"{self.nombre}.FCStd"))
        import MeshPart
        for nombre, archivo, voltear in imprimibles:
            s = self.doc.getObject(nombre).Shape.copy()
            if voltear:  # la tapa se imprime boca abajo
                bb = s.BoundBox
                s.rotate(V(bb.Center.x, bb.Center.y, bb.Center.z), V(1, 0, 0), 180)
            bb = s.BoundBox
            s.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
            m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.08, AngularDeflection=0.35)
            m.write(os.path.join(carpeta, "stl", archivo))
