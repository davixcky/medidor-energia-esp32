# Encargo para Claude: carritos del medidor E.5 modular

Trabaja sobre el proyecto `medidor-energia-esp32`. La lista de compra completa
está en:

`/home/davixcky/dev/.personal/electronica/medidor-energia-esp32/hardware/perforadas-modulares/BOM-precision.csv`

La arquitectura y los conectores están en el mismo directorio. Debes preparar
carritos en tiendas colombianas, priorizando Sigma Electrónica, Electronilab,
Didácticas Electrónicas y CVR Electrónica. No uses Mouser, DigiKey ni vendedores
internacionales si no entregan dentro del plazo en Colombia.

Instrucciones obligatorias:

1. Revisa los carritos existentes antes de agregar artículos y evita duplicados.
2. **Agrega al carrito los componentes que falten y estén disponibles**, con la
   cantidad "a comprar" de la BOM. No te limites a informar qué falta.
3. No compres, no pagues, no confirmes pedido y no ingreses datos de pago.
4. No sustituyas silenciosamente. Si una referencia exacta no existe, busca dos
   alternativas locales técnicamente compatibles, explica la diferencia y deja
   el artículo pendiente de aprobación.
5. Prioriza resistencias de película metálica de 1 %. Los capacitores de 47 nF,
   27 nF y 10 nF deben ser película o C0G de 5 % cuando sea posible.
6. Para el level shifter compra `74HCT245N` DIP-20 (HCT, no HC). El diseño ya
   documenta su pinout. No comprar módulos I2C BSS138 para la línea WS2812.
7. Los piezos deben ser pasivos, no buzzers activos. Las pinzas deben decir
   `SCT-013-000 100A:50mA`, sin burden interno. El ESP32 debe ser DevKitC de 38
   pines. Confirma físicamente estas tres condiciones en cada publicación.
8. Incluye toda la conectividad: headers/carcazas/contactos JST-XH, zócalos 1x19,
   arneses de panel, borneras, jacks, cable, separadores, fusibles y portafusible.
9. Si JST-XH no está disponible como conjunto compatible, propone una única
   familia polarizada equivalente y reemplaza ambos lados; no mezcles pasos.
10. Mantén separada la zona de 120 V. No propongas montar J4/F1/primario ZMPT en
    perforada de baja tensión.

Entrega un reporte Markdown con:

- artículos agregados por tienda, enlace, SKU, cantidad y subtotal;
- artículos que ya estaban y no se duplicaron;
- faltantes reales y dos alternativas compatibles cuando existan;
- incompatibilidades o publicaciones ambiguas;
- total por tienda y total general, sin envío;
- confirmación textual: `NO SE REALIZÓ NINGUNA COMPRA`.

Guarda el reporte como `carritos-medidor-E5-perforadas.md` y no cierres la tarea
hasta revisar la BOM completa, incluidos conectores y componentes auxiliares.
