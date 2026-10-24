# Modelos 3D en FreeCAD

Gabinetes y ensambles del medidor y del banco de medición, construidos con scripts de Python para
FreeCAD 1.1 (módulo Part: sólidos, operaciones booleanas y redondeos). Cada cota es un parámetro al
principio del script.

| Archivo | Contenido |
|---|---|
| `comun.py` | Utilidades: caja redondeada, ranuras, textos grabados, conductores, prensaestopas, colores |
| `medidor.py` | Gabinete de 200 × 150 × 75 mm con tabique, tapa y ensamble con la placa de KiCad |
| `banco.py` | Caja de 130 × 90 × 65 mm: clavija y cordón, tomacorriente doble X1 y lazo exterior de fase con la pinza CT1 |
| `rotular.py` | Rótulos de la vista superior del banco (`../img/3d-banco-planta.png`) |
| `render.py` | Aplica los colores, exporta el STEP del banco y guarda sus vistas en `../img/3d-banco-*.png` |
| `guardar_vistas.py` | Guarda los tres documentos FCStd con las piezas visibles, sus colores y una vista isométrica ajustada |
| `render_blender.py` | Exporta las mallas del medidor (con cada componente de la PCB) y las renderiza en Blender: `../img/3d-medidor-*.png` |
| `medidor.FCStd`, `banco.FCStd` | Documentos de FreeCAD (abrir con FreeCAD 1.1) |
| `medidor.step`, `banco.step` | Ensambles en STEP con colores |
| `stl/` | Cuerpos y tapas para impresión 3D (las tapas van boca abajo) |

La PCB del medidor no se modela aquí: se importa el STEP que exporta KiCad
(`../hardware/3d/medidor-placa.step`), de modo que cada componente queda donde está en la placa real.
Los cables internos terminan en los pads de cada conector según `../hardware/3d/conectores.json`, que
escribe `../herramientas/generar_pcb.py`.

Para regenerar todo:

```bash
./generar.sh
```

Si se regeneran los modelos por separado con `freecadcmd` (incluida la revisión B), ejecutar
después `freecad guardar_vistas.py` desde esta carpeta. Este paso usa la interfaz gráfica para
guardar la presentación de los documentos: al abrirlos, el modelo debe aparecer sin activar
manualmente la visibilidad de las piezas.
