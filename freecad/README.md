# Modelos 3D en FreeCAD

Gabinetes y ensambles del medidor y del banco de medición, construidos con scripts de Python para
FreeCAD 1.1 (módulo Part: sólidos, operaciones booleanas y redondeos). Cada cota es un parámetro al
principio del script.

| Archivo | Contenido |
|---|---|
| `comun.py` | Utilidades: caja redondeada, ranuras, textos grabados, conductores, prensaestopas, colores |
| `medidor.py` | Gabinete de 200 × 150 × 75 mm con tabique, tapa y ensamble con la placa de KiCad |
| `banco.py` | Caja de 300 × 180 × 100 mm, tapa con tres tomacorrientes, *breaker*, pinzas y cableado |
| `render.py` | Aplica los colores, exporta los STEP y guarda las vistas en `../img/3d-*.png` |
| `medidor.FCStd`, `banco.FCStd` | Documentos de FreeCAD (abrir con FreeCAD 1.1) |
| `medidor.step`, `banco.step` | Ensambles en STEP con colores |
| `stl/` | Cuerpos y tapas para impresión 3D (las tapas van boca abajo) |

La placa perforada del medidor no se modela aquí: se importa el STEP que exporta KiCad
(`../hardware/3d/medidor-placa.step`), de modo que cada componente queda donde está en la placa real.

Para regenerar todo:

```bash
./generar.sh
```
