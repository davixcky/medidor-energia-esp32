"""Modelo 3D de la tarjeta ESP32-DevKitC V4 (38 pines) para la huella de la placa perforada.

Se ejecuta con FreeCAD en modo consola:

    freecadcmd modelo_devkitc.py

Escribe ../hardware/3d/esp32-devkitc-v4.step (geometría, para la exportación STEP de KiCad) y
../hardware/3d/esp32-devkitc-v4.wrl (la misma geometría con colores, para la vista 3D de KiCad,
que usa unidades de 0,1 in). El módulo ESP32-WROOM-32 no se modela aquí: la huella usa el modelo
oficial de la biblioteca de KiCad.

Coordenadas del modelo (las de KiCad): origen en el pin 1 (3V3), X hacia la columna derecha
(25,4 mm), Y hacia arriba en la vista de la placa (los pines avanzan en −Y), Z desde la cara
superior de la placa perforada. La tarjeta queda montada sobre dos zócalos hembra de 8,5 mm.
"""
import os

import FreeCAD as App
import Part

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "..", "hardware", "3d")
PASO = 2.54
N = 19
H_ZOCALO = 8.5          # altura del zócalo PinSocket_1x19 de la biblioteca
H_ESPADIN = 2.5         # plástico del espadín macho de la tarjeta
E_PCB = 1.6
Z_PCB = H_ZOCALO + H_ESPADIN
Y_FIN = -(N - 1) * PASO


def caja(x0, y0, z0, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, App.Vector(x0, y0, z0))


piezas = []   # (nombre, forma, color RGB 0–1)

# Tarjeta: 28 × 54 mm, la antena sobresale del lado del pin 1 y el USB del lado del pin 19.
piezas.append(("pcb", caja(-1.3, Y_FIN - 4.28, Z_PCB, 28.0, 54.0, E_PCB), (0.08, 0.08, 0.09)))
for x in (0.0, 10 * PASO):
    piezas.append(("espadin", caja(x - 1.27, Y_FIN - 1.27, H_ZOCALO, PASO, (N - 1) * PASO + PASO, H_ESPADIN),
                   (0.05, 0.05, 0.05)))
    for k in range(N):
        y = -k * PASO
        piezas.append(("pin", caja(x - 0.32, y - 0.32, 3.0, 0.64, 0.64, Z_PCB + E_PCB + 1.0 - 3.0),
                       (0.85, 0.7, 0.25)))
# Conector micro-USB, pulsadores EN y BOOT, regulador AMS1117 y puente USB-serie CP2102.
piezas.append(("usb", caja(12.7 - 3.9, Y_FIN - 4.9, Z_PCB + E_PCB, 7.8, 5.5, 2.7), (0.78, 0.78, 0.8)))
for x in (3.0, 22.4 - 3.5):
    piezas.append(("pulsador", caja(x, Y_FIN - 3.6, Z_PCB + E_PCB, 3.5, 4.5, 1.6), (0.75, 0.75, 0.77)))
    piezas.append(("tecla", Part.makeCylinder(0.9, 0.6, App.Vector(x + 1.75, Y_FIN - 1.35, Z_PCB + E_PCB + 1.6)),
                   (0.1, 0.1, 0.1)))
piezas.append(("ams1117", caja(3.0, Y_FIN + 4.5, Z_PCB + E_PCB, 6.5, 3.5, 1.6), (0.12, 0.12, 0.12)))
piezas.append(("cp2102", caja(15.5, Y_FIN + 3.5, Z_PCB + E_PCB, 5.0, 5.0, 0.9), (0.12, 0.12, 0.12)))
for x, c in ((10.0, (0.9, 0.1, 0.1)), (15.4, (0.1, 0.8, 0.2))):
    piezas.append(("led", caja(x, Y_FIN + 9.0, Z_PCB + E_PCB, 1.6, 0.8, 0.6), c))


def escribir_wrl(ruta):
    """VRML 2.0 con un IndexedFaceSet por pieza; KiCad usa 1 unidad = 2,54 mm."""
    k = 1 / 2.54
    with open(ruta, "w") as f:
        f.write("#VRML V2.0 utf8\n# ESP32-DevKitC V4, generado con FreeCAD (modelo_devkitc.py)\n")
        for nombre, forma, (r, g, b) in piezas:
            verts, caras = forma.tessellate(0.05)
            f.write(f"Shape {{ appearance Appearance {{ material Material {{ diffuseColor {r} {g} {b} "
                    f"specularColor 0.2 0.2 0.2 shininess 0.3 }} }}\n")
            f.write("geometry IndexedFaceSet { creaseAngle 0.5 coord Coordinate { point [\n")
            f.write(",\n".join(f"{v.x * k:.5f} {v.y * k:.5f} {v.z * k:.5f}" for v in verts))
            f.write("] }\ncoordIndex [\n")
            f.write(",\n".join(f"{a},{b_},{c},-1" for a, b_, c in caras))
            f.write("] } }\n")


os.makedirs(SALIDA, exist_ok=True)
compuesto = Part.makeCompound([p[1] for p in piezas])
compuesto.exportStep(os.path.join(SALIDA, "esp32-devkitc-v4.step"))
escribir_wrl(os.path.join(SALIDA, "esp32-devkitc-v4.wrl"))
print("Modelo de la DevKitC escrito en", os.path.normpath(SALIDA))
