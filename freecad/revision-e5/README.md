# Modelo 3D del medidor E.5 modular

El gabinete ampliado coloca T1–T5 en una sola capa y reserva una zona posterior
independiente para J4, F1 y ZMPT101B. La guarda de 120 V es una pieza desmontable
separada de la tapa general. La barra WS2812B tiene cuatro píxeles y una cuna de
13,2 mm para una tira nominal de 10–12,5 mm.

Fuentes reproducibles: `generar_modelo.py` y `render_modelo.py`. Entregables:
FCStd, STEP, STL, tres vistas PNG y `validacion-3d.json`.

El modelo valida las envolventes y la segregación geométrica básica. Antes de
imprimir hay que confirmar dimensiones del ESP32, pantalla, encoder, piezo,
conectores y ancho real de la tira recibida.
