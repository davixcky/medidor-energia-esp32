#!/usr/bin/env bash
# Regenera los modelos de FreeCAD, las piezas STL, los STEP y las ilustraciones 3D.
# Requiere FreeCAD 1.1, Blender (vistas del medidor) y xvfb-run (vistas del banco, que FreeCAD
# guarda con la interfaz gráfica sin pantalla).
set -euo pipefail
cd "$(dirname "$0")"
freecadcmd medidor.py
freecadcmd banco.py
# Medidor: Blender conserva los colores de cada componente de la PCB importada de KiCad
freecadcmd render_blender.py
blender --background --factory-startup --threads 6 --python render_blender.py -- .render/ensamble.json
# Banco: vistas de FreeCAD
MODELOS=banco QT_QPA_PLATFORM=xcb WAYLAND_DISPLAY= xvfb-run -a -s "-screen 0 1920x1200x24" freecad render.py
# Guarda también la visibilidad, los colores y la cámara de los documentos entregables.
QT_QPA_PLATFORM=xcb WAYLAND_DISPLAY= xvfb-run -a -s "-screen 0 1920x1200x24" freecad guardar_vistas.py
python3 rotular.py
echo "Listo: *.FCStd, *.step, stl/*.stl y ../img/3d-{medidor,banco}-{cerrado,abierto,planta}.png"
