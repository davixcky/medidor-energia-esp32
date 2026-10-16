#!/usr/bin/env bash
# Regenera los modelos de FreeCAD, las piezas STL, los STEP y las ilustraciones 3D.
# Requiere FreeCAD 1.1 y xvfb-run (las vistas se guardan con la interfaz gráfica sin pantalla).
set -euo pipefail
cd "$(dirname "$0")"
freecadcmd medidor.py
freecadcmd banco.py
QT_QPA_PLATFORM=xcb WAYLAND_DISPLAY= xvfb-run -a -s "-screen 0 1920x1200x24" freecad render.py
python3 rotular.py
echo "Listo: *.FCStd, *.step, stl/*.stl y ../img/3d-{medidor,banco}-{cerrado,abierto,planta}.png"
