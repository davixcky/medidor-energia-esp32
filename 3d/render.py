"""Renderiza los modelos de FreeCAD (se ejecuta con la interfaz gráfica, p. ej. bajo xvfb-run).

Para cada modelo (medidor, banco): abre el .FCStd, aplica el color guardado en cada pieza,
exporta el ensamble a STEP con colores y guarda dos vistas isométricas en ../img:
3d-<modelo>-abierto.png (tapa a un lado, interior visible) y 3d-<modelo>-cerrado.png.
"""
import os

import FreeCAD as App
import FreeCADGui as Gui
import Import
from pivy import coin  # necesario para getCameraNode()

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, "..", "img")
MODELOS = os.environ.get("MODELOS", "medidor,banco").split(",")


def vista(nombre_png, gdoc, direccion, zoom=0.62, seleccion=None):
    """Vista ortográfica desde la dirección dada (vector de la cámara hacia el modelo)."""
    Gui.updateGui()
    v = gdoc.ActiveView or gdoc.mdiViewsOfType("Gui::View3DInventor")[0]
    v.setAxisCross(False)
    v.setCameraType("Orthographic")
    # orientación de la cámara: mira a lo largo de "direccion" con el eje Z del modelo hacia arriba
    d = App.Vector(*direccion).normalize()
    zc = d * -1
    xc = App.Vector(0, 0, 1).cross(zc).normalize()
    yc = zc.cross(xc)
    m = App.Matrix(xc.x, yc.x, zc.x, 0, xc.y, yc.y, zc.y, 0, xc.z, yc.z, zc.z, 0, 0, 0, 0, 1)
    v.setCameraOrientation(App.Rotation(m).Q)
    for _ in range(3):
        Gui.updateGui()
        if seleccion:
            Gui.Selection.clearSelection()
            for o in seleccion:
                Gui.Selection.addSelection(o)
            Gui.SendMsgToActiveView("ViewSelection")
            Gui.Selection.clearSelection()
        else:
            v.fitAll()
    cam = v.getCameraNode()
    cam.height.setValue(cam.height.getValue() * zoom)
    Gui.updateGui()
    ruta = nombre_png if os.path.isabs(nombre_png) else os.path.join(IMG, nombre_png)
    v.saveImage(ruta, 2000, 1250, "White")


Gui.getMainWindow().showMaximized()
Gui.updateGui()

for nombre in MODELOS:
    doc = App.openDocument(os.path.join(AQUI, f"{nombre}.FCStd"))
    App.setActiveDocument(doc.Name)
    gdoc = Gui.getDocument(doc.Name)
    Gui.updateGui()
    piezas = [o for o in doc.Objects if hasattr(o, "ColorRGB")]
    for o in piezas:
        c = tuple(float(x) for x in o.ColorRGB.split(","))
        o.ViewObject.ShapeColor = c
        o.ViewObject.LineColor = (0.15, 0.15, 0.15)
        o.ViewObject.LineWidth = 1.0
        o.ViewObject.DisplayMode = "Flat Lines"
        if o.Name.startswith("Placa_KiCad"):
            o.ViewObject.DisplayMode = "Shaded"
        o.ViewObject.Deviation = 0.05
        o.ViewObject.Visibility = True
    doc.recompute()
    Import.export(piezas, os.path.join(AQUI, f"{nombre}.step"))
    # placa de KiCad: se vuelve a importar en modo gráfico para conservar los colores de cada componente
    pk = doc.getObject("Placa_KiCad")
    if pk is not None:
        antes = set(o.Name for o in doc.Objects)
        Import.insert(os.path.join(AQUI, pk.ArchivoSTEP), doc.Name)
        nuevos = [o for o in doc.Objects if o.Name not in antes]
        raices = [o for o in nuevos if not any(o in p.OutList for p in nuevos)]
        for o in raices:
            o.Placement = App.Placement(pk.Traslado, App.Rotation()).multiply(o.Placement)
        pk.ViewObject.Visibility = False
        doc.recompute()

    W = max(o.Shape.BoundBox.XMax for o in piezas if o.Grupo == "cuerpo")
    H = max(o.Shape.BoundBox.ZMax for o in piezas if o.Grupo == "cuerpo")
    # cerrado
    vista(f"3d-{nombre}-cerrado.png", gdoc, (0.75, 1.0, -0.85))
    # abierto: la tapa y lo que va montado en ella se dejan a un lado, a la altura del piso
    mov = App.Placement(App.Vector(W + 40, 0, -H), App.Rotation())
    for o in piezas:
        if hasattr(o, "FormaAbierta"):
            o.Shape = o.FormaAbierta
        if o.Grupo == "tapa":
            o.Placement = mov.multiply(o.Placement)
        elif o.Grupo == "montado":   # aparatos de la tapa: quedan en su sitio, translúcidos
            o.ViewObject.Transparency = 60
        if o.Name.endswith("_pinza"):  # pinzas translúcidas: se ve la fase dentro de la ventana
            o.ViewObject.Transparency = 55
    doc.recompute()
    vista(f"3d-{nombre}-abierto.png", gdoc, (0.45, 1.0, -2.6), 0.56)
    # planta: interior visto desde arriba, sin la tapa
    for o in piezas:
        if o.Grupo == "tapa" or hasattr(o, "FormaAbierta"):
            o.ViewObject.Visibility = False
    # la planta del banco se guarda sin rótulos; rotular.py la rotula en ../img
    planta = os.path.join(AQUI, "planta-banco-base.png") if nombre == "banco" else f"3d-{nombre}-planta.png"
    vista(planta, gdoc, (0.0, 0.3, -1.0), 0.5)
    App.closeDocument(doc.Name)

Gui.getMainWindow().close()
os._exit(0)
