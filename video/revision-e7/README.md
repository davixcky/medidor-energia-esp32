# Video del medidor E.7

Video reproducible desde el ensamble FreeCAD E.7. Muestra el gabinete cerrado,
la interfaz de tapa, los estados reales de iluminación, la apertura del conjunto,
T1–T5 y la guarda independiente de red.

Los cuatro segmentos FCOB siempre comparten color porque el firmware usa
`pixels.fill()`: verde conectado, ámbar sin red/servidor y rojo en alerta. El
LED pequeño queda fijo en estado normal, parpadea a 1 Hz sin red y a 5 Hz en
alerta.

Regeneración desde la raíz del repositorio:

```sh
freecadcmd -c "p='freecad/revision-e7/render_modelo.py'; exec(compile(open(p).read(),p,'exec'),{'__file__':p,'__name__':'__main__'})"
python video/revision-e7/audio/generar.py
python video/revision-e7/graficos.py
PREVIEW=1 blender -b --python video/revision-e7/animar.py
blender -b --python video/revision-e7/animar.py
python video/revision-e7/finalizar.py
```

Es una visualización de diseño; no sustituye prueba eléctrica, calibración ni
verificación de aislamiento sobre el prototipo físico.
