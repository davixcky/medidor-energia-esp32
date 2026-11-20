# BOM de precisión — Medidor E.7 perforadas

La lista de compra fila por fila y las cantidades con repuesto están en
[`BOM-precision.csv`](BOM-precision.csv). Contiene 62 líneas e incluye electrónica,
sensores, conectores, arneses, cableado, alimentación y montaje.

## Componentes críticos

| Grupo | Requisito |
|---|---|
| ESP32 | ESP32S V1.1 USB-C de 38 pines, ESP32-WROOM-32; verificar 25,4 mm entre hileras; no versión de 30 pines |
| Corriente | 2 × SCT-013-000, 100 A : 50 mA, **sin** burden interno |
| Tensión | 1 × ZMPT101B; su primario queda en la zona Z1 cerrada |
| Burdens | 22 ohm y 47 ohm, película metálica, 1 %, soldadas en los jacks |
| Filtros | resistencias 1 %; 47 nF, 27 nF y 10 nF de película/C0G, idealmente 5 % |
| Level shifter | 74HCT245N DIP-20; HCT, no HC y no módulo I2C BSS138 |
| Sonido | piezo pasivo comprado GEP0008, 44 × 14 mm, más NPN; no buzzer activo |
| Iluminación | BTF FCOB WS2811 12 V, 720 LED/m, 20 segmentos/m; usar 4 segmentos = 200 mm |
| Alimentación | adaptador comprado 5 V/5 A y jack 5,5 × 2,5 mm; MT3608 ajustado a 12,0 V para la FCOB |

## Conectividad incluida

Los siete arneses entre tarjetas requieren en total:

- 6 headers y 6 carcasas de 2 vías.
- 4 headers y 4 carcasas de 3 vías.
- 2 headers y 2 carcasas de 4 vías.
- 2 headers y 2 carcasas de 5 vías.
- 42 contactos crimp; comprar 60 por pérdidas y repuestos.

Estos conteos no incluyen LCD, ZMPT, encoder, piezo, LEDs ni pulsadores de panel;
sus arneses aparecen como líneas independientes en el CSV.

## Sustituciones

No sustituir valores críticos por el más cercano sin recalcular. En especial:

- 11 kOhm no se reemplaza por 10 kOhm y 13 kOhm no se reemplaza por 12 kOhm.
- BAT85 no se reemplaza automáticamente por un diodo de silicio común.
- 74HC245 no equivale al 74HCT245 para una entrada de 3,3 V alimentada a 5 V.
- Un SCT-013 con salida de tensión o burden interno no equivale al SCT-013-000.
- La FCOB de 12 V no puede conectarse al antiguo riel de 5 V ni reemplazarse en
  el esquema por una WS2812B sin eliminar/recalcular el elevador.
- 1N5819 y PTC de 1,1 A se retiraron de T1; usar 1N5822 de 3 A y PTC hold 2 A.

Si una familia JST-XH completa no está disponible, puede elegirse otra familia
polarizada, pero deben cambiarse ambos extremos y mantenerse un solo paso.
