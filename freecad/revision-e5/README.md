# Modelo 3D del medidor E.5 modular

El gabinete ampliado coloca T1–T5 en una sola capa y reserva una zona posterior
independiente para J4, F1 y ZMPT101B. La guarda de 120 V es una pieza desmontable
separada de la tapa general. La barra WS2812B tiene cuatro píxeles y una cuna de
13,2 mm para una tira nominal de 10–12,5 mm.

La envolvente resultante mide 340 × 240 × 70 mm. Usa completas cuatro placas
de 90 × 70 × 1,6 mm y una de 120 × 80 × 1,6 mm; la quinta placa 90 × 70
comprada queda como repuesto. El piezo se corrigió a Ø44 × 14 mm y el módulo
ZMPT101B a 51,7 × 21,6 mm.

Fuentes reproducibles: `generar_modelo.py` y `render_modelo.py`. Entregables:
FCStd, STEP, STL, tres vistas PNG, `validacion-3d.json` y
`medidas-componentes.json`.

El modelo valida las envolventes y la segregación geométrica básica. Antes de
imprimir hay que confirmar las cotas marcadas `por_medir`, sobre todo el ESP32,
los ejes EC11, la altura del ZMPT101B y el ancho real de la tira recibida.
