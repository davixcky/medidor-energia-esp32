"""Guarda una vista visible al abrir los FCStd. Ejecutar con FreeCAD (interfaz gráfica)."""
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
import Part  # Carga los tipos geométricos antes de restaurar los documentos.
from PySide import QtCore


def guardar_vistas():
    carpeta = Path(__file__).resolve().parent
    Gui.activateWorkbench("PartWorkbench")
    for ruta in (
        carpeta / "medidor.FCStd",
        carpeta / "banco.FCStd",
        carpeta / "revision-b" / "medidor-revB.FCStd",
    ):
        doc = App.openDocument(str(ruta))
        for pieza in doc.Objects:
            if pieza.ViewObject is None:
                continue
            vista = pieza.ViewObject
            vista.Visibility = True
            if hasattr(pieza, "ColorRGB"):
                vista.ShapeColor = tuple(float(c) for c in pieza.ColorRGB.split(","))
            vista.DisplayMode = "Flat Lines"
            vista.LineColor = (0.15, 0.15, 0.15)
            vista.Deviation = 0.05
        doc.recompute()
        vista = Gui.activeDocument().activeView()
        vista.viewAxonometric()
        vista.fitAll()
        Gui.updateGui()
        doc.save()
        App.closeDocument(doc.Name)
    Gui.getMainWindow().close()


QtCore.QTimer.singleShot(0, guardar_vistas)
