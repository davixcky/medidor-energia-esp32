# Medidor de energía E.7 — modelo de producto

Modelo mecánico editable del medidor modular T1–T5. Las tarjetas se recortan de
las perforadas compradas y conservan las dimensiones indicadas por los
esquemáticos KiCad. El gabinete mide 280 × 180 × 70 mm.

El modelo abierto incluye ESP32S V1.1 USB-C, borneras, JST, jacks SCT,
potenciómetros de MT3608 y ZMPT101B, capacitores, 74HCT245N, LED de estado,
arneses, fusible, guarda de red y las cinco perforadas. La tapa incluye LCD,
encoder con perilla, dos pulsadores, LED de estado, piezo 44 × 14 mm empotrado
y la barra BTF FCOB WS2811 de 200 × 12 mm bajo difusor.

Archivos principales:

- `medidor-E7-perforadas.FCStd`: modelo nativo FreeCAD.
- `medidor-E7-perforadas.step`: ensamble intercambiable.
- `medidor-E7-{cerrado,abierto,planta}.png`: renders de revisión.
- `stl/`: cuerpo, tapa, guarda de 120 V y soporte de la barra.
- `medidas-componentes.json`: origen y certeza de cada cota.
- `validacion-3d.json`: envolvente, ubicación de placas y solapes.

El MT3608 todavía debe comprarse o medirse; su espacio reservado de
36 × 17 × 14 mm es conservador. No fabricar la tapa final sin verificar con
calibre los elementos marcados `por_medir`.
