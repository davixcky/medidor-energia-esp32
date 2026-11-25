# Video del medidor E.7

Video de 38 s (912 fotogramas a 24 fps, Full HD) generado desde el ensamble
FreeCAD de `3d/revision-e7/`. Es una visualización de diseño: no
sustituye prueba eléctrica, calibración ni verificación de aislamiento.

## Estados que muestra

Salen de `firmware/src/main.cpp` y están codificados en `linea_tiempo.py`.

| Estado | FCOB (`pixels.fill`, cuatro segmentos iguales) | LED de panel D8 (verde) |
|---|---|---|
| Conectado | verde (0, 18, 10) | fijo |
| Sin conexión o servidor | ámbar (24, 9, 0) | 1 Hz, `(m / 500) % 2` |
| Alerta sin reconocer | rojo (32, 0, 0) | 5 Hz, `(m / 100) % 2` |

El LED D8 es de un solo color: solo cambia su parpadeo. La barra no parpadea
ni funciona como indicador de nivel.

## Regenerar

Desde la raíz del repositorio, con el CAD ya regenerado:

```sh
uv run --python 3.12 --with kokoro-onnx==0.6.1 --with soundfile python docs/video/revision-e7/audio/generar.py
python docs/video/revision-e7/pantallas.py
BUILD_ONLY=1 blender -b --python docs/video/revision-e7/animar.py
python docs/video/revision-e7/graficos.py
blender -b --python docs/video/revision-e7/animar.py
python docs/video/revision-e7/finalizar.py
python docs/video/revision-e7/verificar.py
```

La voz usa los modelos Kokoro de `~/.cache/hyperframes/tts/`. `PREVIEW=1` con
`animar.py` produce una imagen por plano.

## Archivos

- `linea_tiempo.py`: tiempos de cada plano, estados y apertura de tapa.
- `animar.py`: escena, cámara, luces, estados y render; escribe `medidor-E7.blend` y `seguimiento.json`.
- `graficos.py`: títulos, rótulos T1–T5 y subtítulos.
- `finalizar.py`: MP4 con H.264, AAC y subtítulos en español.
- `verificar.py`: `verificacion.json` y `contacto-final.png`.
- `pantallas.py`: pantallas LCD de «sin red» y «alerta», ilustrativas.
- `REVIEW.md`: revisión del resultado.
