# Archivo — revisiones superadas

Nada de esta carpeta forma parte del diseño vigente. Se conserva porque documenta el camino del
proyecto y porque algunos entregables (fichas, guías de impresión, videos) se citan en los avances
ya entregados.

**El diseño vigente es la revisión E.9.** Ver el [índice del repositorio](../README.md).

| Carpeta | Qué fue | Reemplazada por |
|---|---|---|
| [`revision-b/`](revision-b/) | Primer gabinete PETG con tapa magnética, LCD Waveshare a color, 4 NeoPixels, piezo y encoder. Incluye ficha del dispositivo, guía de impresión, STL, cupones de ajuste y los perfiles P2S. | `3d/revision-e7/` (E.9) |
| [`revision-e5/`](revision-e5/) | Primer gabinete para el medidor en placas perforadas modulares. | `3d/revision-e7/` (E.9) |
| [`video-revision-b/`](video-revision-b/) | Video de producto de la revisión B: animación en Blender, narración sintética, subtítulos y verificación. | `docs/video/revision-e7/` |
| `medidor-energia-E7-hardware.zip` | Paquete de hardware de la revisión E.7, publicado en su momento como archivo de release. | `hardware/perforadas-modulares/` |

## Reproducibilidad

Los scripts archivados siguen funcionando desde la raíz del repositorio:

```bash
freecadcmd archivo/revision-b/medidor_profesional.py   # toma medidor.py y comun.py de 3d/
python3  archivo/revision-b/empaquetar.py              # rearma el zip de fabricación de la revisión B
```

El generador de la revisión B no tiene copia propia de la geometría base: importa `medidor.py` y
`comun.py` de [`../freecad/`](../3d/README.md), que son los modelos vivos. Si esa geometría
cambia, la revisión B se regenera con la geometría nueva; los archivos ya guardados aquí son la
versión tal como se entregó.

Los entregables grandes que se pueden regenerar (renders, `.step`, `.mp4`, `.blend`, g-code y los
zips que arman los scripts) no están en Git: se publican como archivos de las releases.

La excepción es `medidor-energia-E7-hardware.zip`, que sí está versionado: es el paquete tal como se
entregó en su momento y no hay un script que lo reconstruya byte a byte.
