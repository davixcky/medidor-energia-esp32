# Carritos — Medidor de energía E.5 perforadas modulares

Fecha: 2026-11-16. Fuente: `BOM-precision.csv` (columna "Cantidad a comprar").
Carritos de sesión en Chrome (sin login). **Las cuatro tiendas comparten el carrito
con el ecualizador E.5**; aquí solo se listan y suman las líneas o cantidades que
corresponden al medidor. Reporte del ecualizador:
`ecualizador-esp32/hardware/E5-perforadas/carritos-ecualizador-E5-perforadas.md`.

Precios en COP, IVA incluido, sin envío.

## 0. Reconstrucción (2026-11-16, después del reinicio de carritos)

- **Electronilab:** carrito verificado vacío y reconstruido desde cero con 25 líneas, $241.584.
  La resistencia de 330 Ω pasa a **1 paquete compartido** (10 piezas = 5 ecualizador + 5 medidor);
  antes había 2. El subtotal del medidor en Electronilab baja de $174.884 a **$173.984**.
- **Sigma y Didácticas** también estaban vacíos y **CVR** había perdido las 2 pantallas.
  Se reconstruyeron con las mismas cantidades: Sigma $43.852, Didácticas $350.418,11 (28 líneas),
  CVR $82.698.

### Tira NeoPixel (PIX1-PIX4) — revisión específica

| Tienda | Artículo | Estado |
|---|---|---|
| Electronilab | Cinta Pixel WS2812B 60 LED/m, 5 V | ❌ **FALTANTE en formato adecuado.** Las versiones de 1 m (id 115863 IP65, id 2988 IP67) están agotadas. Solo hay rollos de **5 m** (id 119893 IP20, 1 unidad, $164.900; id 115877 IP65 e id 115853 IP67, $186.900), y su ficha dice **12,5 mm de ancho**, no ~10 mm. No se añadió |
| Didácticas | Cinta LED RGB WS2812B 5 V 60 LED IP65, 1 m (SKU CINTALED-WS2812B) — [enlace](https://www.didacticaselectronicas.com/shop/cintaled-ws2812b-cinta-led-rgb-ws2812b-5v-60-leds-ip65-1-metro-16610) | ✅ **En carrito ×1, $28.483,84.** Direccionable WS2812B, 5 V, 60 LED/m (4 píxeles ≈ 66,7 mm), se puede cortar entre LED, conector JST de 3 pines. ⚠️ **La ficha no publica el ancho**; las IP65 con silicona suelen medir 10–12 mm. Medirla al recibirla o confirmarlo con la tienda |
| CVR | — | No vende tira; solo anillos y LEDs WS2812 sueltos |

No es una tira RGB analógica ni un módulo BSS138/I2C.

## 1. Artículos agregados para el medidor

### Electronilab (electronilab.co/carrito/) — subtotal medidor **$173.984** (reconstruido)

| Ref. BOM | Producto (SKU/ID tienda) | Cant. | P. unit. | Subtotal | Nota |
|---|---|---:|---:|---:|---|
| CH1/CH2 | Sensor SCT-013-000 100A/50mA (id 5619) | 2 | $39.900 | $79.800 | Salida 0–50 mA, sin burden interno ✓ |
| U2 | ZMPT101B módulo (id 404402) | 1 | $16.900 | $16.900 | Con potenciómetro y offset VCC/2 (op-amp). Zona de red |
| ENC1 | Encoder rotativo EC11 con pulsador (id 89970) | 2 | $3.900 | $7.800 | Eje no indicado en la ficha; verificar 6 mm |
| Q1 | 2N2222 / PN2222 TO-92 (id 74487) | 3 | $108 | $324 | Ficha no dice sufijo A; confirmar patillaje |
| BZ1 | Buzzer **pasivo** piezoeléctrico (id 278806) | 2 | $9.900 | $19.800 | ⚠️ Medida 44×14 mm aprox., BOM pide ~12 mm |
| R1 | Resistencia 22 Ω metal film 1 % ×10 (id 83219) | 1 paq. | $900 | $900 | |
| R2 | Resistencia 47 Ω metal film 1 % ×10 (id 83220) | 1 paq. | $900 | $900 | |
| R5-R6 | Resistencia 3,3 kΩ metal film 1 % ×10 (id 83233) | 1 paq. | $900 | $900 | |
| R15 | Resistencia 470 Ω metal film 1 % ×10 (id 83227) | 1 paq. | $900 | $900 | |
| R11/R16 | Resistencia 330 Ω metal film 1 % ×10 (id 83226) | 0 (compartido) | $900 | $0 | 1 paquete total para ambos proyectos; se cuenta en el ecualizador |
| J1 | Bornera 2P 5,08 mm (id 18868) | +2 | $500 | $1.000 | Línea total ×4 (2 + 2) |
| J5 | Bornera 3P 5,08 mm (id 18877) | 2 | $780 | $1.560 | |
| Mecánico | Kit 160 separadores nylon M3 M-H (id 6862) | 1 | $36.300 | $36.300 | Verificar si trae tornillos y tuercas |
| JST-XH 5P | Conector macho XH2.54 5P (id 91799) | 5 | $380 | $1.900 | Completa los 5P que faltaban en Didácticas |
| JST-XH 5P | Cable conector XH2.54 5P para soldar (id 91808) | 5 | $1.000 | $5.000 | Pigtail con carcasa XH 5P (misma familia) |

### Didácticas Electrónicas (didacticaselectronicas.com/shop/cart) — subtotal medidor **$194.116,37**

| Ref. BOM | Producto (SKU) | Cant. | P. unit. | Subtotal | Nota |
|---|---|---:|---:|---:|---|
| T1-T5 + repuesto | Placa perforada FR4 7×9 cm, pads individuales (PCB-FV-7X9-HQ) | 5 | $2.541,84 | $12.709,20 | T1, T2, T3, T5 y repuesto; recortar |
| T4 | Placa perforada FR4 8×12 cm (PCB-FV-8X12-HQ) | 1 | $3.647,35 | $3.647,35 | ≥100×80 mm |
| D1 | 1N5819 DO-41 (1N5819) | 3 | $240,38 | $721,14 | |
| D8 | LED 5 mm difuso verde (LED-5-VE-D) | 2 | $59,50 | $119,00 | |
| D9 | LED 3 mm difuso rojo (LED-3-RO-D) | 1 | $120,19 | $120,19 | |
| D10 | LED 3 mm verde alta intensidad (LED-3-VE-C) | 1 | $120,19 | $120,19 | El difuso verde está agotado |
| SW1/SW2 | Pulsador metálico momentáneo 12 mm panel (SW12BP) | 3 | $7.225,68 | $21.677,04 | |
| Alimentación | Fuente/adaptador 5 V 5 A, plug 5,5×2,5 (ADAP-5V-5A) | 1 | $41.364,40 | $41.364,40 | ⚠️ Plug interior 2,5 mm → por eso se eligió el jack de 2,5 mm |
| Jack DC | Jack DC metálico chasis 5,5×2,5 mm (CON-156A) | 2 | $1.884,96 | $3.769,92 | ⚠️ BOM decía 5,5×2,1; se igualó al plug del adaptador |
| Cable 22 AWG | Cable siliconado 22 AWG rojo, por metro (UL3239-22AWG-RO) | +2 m | $1.760,01 | $3.520,02 | Línea total 5 m (3 ecualizador + 2 medidor) |
| Cable 22 AWG | Cable siliconado 22 AWG negro (UL3239-22AWG-NE) | +2 m | $1.760,01 | $3.520,02 | Línea total 5 m |
| Cable 24 AWG | Dispensador de 5 colores 24 AWG (KIT-CAB-SILIC-24AWG) | 1 | $41.000,26 | $41.000,26 | Metros por rollo no indicados |
| Cable 18 AWG | Silicona 18 AWG negro, 3000 V (UL3239-18AWG-NE) | 1 m | $4.048,38 | $4.048,38 | Fase |
| Cable 18 AWG | Silicona 18 AWG blanco (UL3239-18AWG-BL) | 1 m | $4.048,38 | $4.048,38 | Neutro. No hay verde para tierra |
| C2/C8/C10… | Cerámico 100 nF 50 V THT (CC0.1UF50V) | +10 | $72,59 | $725,90 | Línea total 20 (10 + 10); dieléctrico no indicado |
| C16 | Electrolítico 680 µF 16 V (CE680UF16V) | 2 | $273,70 | $547,40 | Low-ESR no indicado |
| C1 | Electrolítico 470 µF 35 V (CE470UF35V) | 2 | $452,20 | $904,40 | Low-ESR no indicado; no hay 10/16 V THT |
| PIX1-PIX4 | Cinta WS2812B 5 V 60 LED/m IP65, 1 m (CINTALED-WS2812B) | 1 | $28.483,84 | $28.483,84 | Cortar un tramo de 4 píxeles; sobra |
| JST-XH 2P | Kit XH 2P: macho recto PCB + carcasa hembra con cable 26 AWG 20 cm (K-JST-XH2.54-2P) | +14 | $649,74 | $9.096,36 | 8 entre tarjetas + 6 para arneses de panel. Línea total ×16 |
| JST-XH 3P | Kit XH 3P (K-JST-XH2.54-3P) | 9 | $849,66 | $7.646,94 | 6 entre tarjetas + 3 para panel |
| JST-XH 4P | Kit XH 4P (K-JST-XH2.54-4P) | +4 | $1.256,64 | $5.026,56 | Línea total ×14 (10 + 4) |
| JST-XH 5P | Kit XH 5P (K-JST-XH2.54-5P) | +1 | $1.299,48 | $1.299,48 | Última unidad; los otros 5 van en Electronilab |

**JST-XH sin crimpadora:** cada kit trae un header macho para PCB y una carcasa hembra
ya cableada. Dos kits empalmados con termorretráctil forman un arnés de 2 extremos; los
42 contactos de crimp de la BOM ya no son necesarios. Todo es de la misma familia XH
de 2,54 mm. El termorretráctil está en la línea KIT-TE del carrito, comprada para el
ecualizador y compartida.

### Sigma Electrónica (sigmaelectronica.net/carrito/) — subtotal medidor **$14.280**

| Ref. BOM | Producto (SKU) | Cant. | P. unit. | Subtotal | Nota |
|---|---|---:|---:|---:|---|
| U3 | 74HCT245 DIP-20, "Empaque 20-DIP" (74HCT245) | +2 | $4.998 | $9.996 | Línea total ×4 (2 + 2). HCT ✓ |
| ESP32 1×19 + LCD 1×8 | Regleta hembra 1×40 2,54 mm (REG-40 X 1-H) | +3 | $1.428 | $4.284 | 4 × 1×19 + 2 × 1×8 cortadas. Línea total ×4 |

### CVR Electrónica (cvrelectronica.com/shopping_cart/) — subtotal medidor **$33.462**

| Ref. BOM | Producto | Cant. | P. unit. | Subtotal | Nota |
|---|---|---:|---:|---:|---|
| LCD | TFT IPS 1,9" 170×320 SPI ST7789 (product_id 1602) | +1 | $32.412 | $32.412 | Línea total ×2. Pines GND,VCC,SCL,SDA,RES,DC,CS,BLK |
| C7 | Electrolítico 10 µF 16 V | +3 | $350 | $1.050 | Línea total ×8 (5 + 3) |

## 2. Ya estaban en el carrito y no se duplicaron

- **Termorretráctil KIT-TE, cinta 26 AWG, portafusible y fusibles de 3 A en Didácticas:** son
  del ecualizador; los auxiliares se pueden compartir.
- **Fuente 5 V 5 A abierta de Electronilab (ecualizador):** el medidor usa su propio
  adaptador cerrado, como pide la BOM.

## 3. Faltantes reales y alternativas

| Ref. BOM | Necesario | Estado | Alternativas |
|---|---|---|---|
| U1 ESP32 DevKitC 38 pines | 1 | El único WROOM-32D de 38 pines de Didácticas (última unidad) está en el carrito del ecualizador. Electronilab: CH9102F de 38 pines agotado | (a) Didácticas D-ESP32S-38P-C "DevKit32 ESP32S 38 pines", 111 unidades, unos $21.700: módulo ESP-32S, confirmar ancho y pinout. (b) Asignar el WROOM-32D al medidor y la (a) al ecualizador. **Pendiente de aprobación** |
| D2-D7 BAT85 | 10 | Sin existencia en las 4 tiendas | BAT43 o BAT42 (DO-35): revisar Vf y fuga antes de usar. Pendiente |
| F2 PTC MF-R110 | 2 | No encontrado | MF-R110 equivalente de 1,1 A hold, de otro fabricante. Pendiente |
| F1 fusible T500mA 5×20 + portafusible cerrado | 3 + 1 | No encontrado | Portafusible aéreo 5×20 de Didácticas (CON-183AC); fusible lento de 500 mA en tienda eléctrica local. Pendiente (zona de red) |
| Prensaestopa PG7 | 2 | No encontrado | Tienda eléctrica local |
| R3 15k, R4 10k (12), R7 11k, R8 13k, R14 1k — película metálica 1 % | 3/12/3/3/5 | Electronilab: 10k y 1k agotados; 11k, 13k y 15k no existen. Didácticas: solo carbón. CVR: tolerancia no indicada | Kit de resistencias 1 % E24 en otra tienda; o pedir los valores sueltos en Sigma por WhatsApp. **No se añadió carbón** |
| C5-C6 47 nF, C9 27 nF, C12-C13 10 nF película/C0G 5 % | 4/3/4 | El poliéster de Didácticas y CVR no indica tolerancia; 27 nF solo existe en SMD 0805 | Poliéster de 47 nF/250 V (Didácticas) o 10 nF/250 V (CVR) si se acepta tolerancia no garantizada; medir y seleccionar con LCR. Pendiente |
| LED1 ámbar 5 mm | 2 | No encontrado | LED amarillo de 5 mm (cambia el color). Pendiente |
| J2/J3 jack 3,5 mm estéreo de panel | 3 | Didácticas solo tiene mono de chasis; el PJ313D de Electronilab es de PCB | PJ313D en la tarjeta con soporte, o jack estéreo de chasis en tienda de audio. Pendiente |
| J4 bornera protegida de red + guarda | 1 | No buscada en detalle (zona de red) | Bornera con tapa en tienda eléctrica. Pendiente |
| Cable 18 AWG verde (tierra) | 1 m | No hay verde | Verde/amarillo en tienda eléctrica |
| TP1-TP9 lazos de prueba | 12 | No encontrado | Cortar pines de las regletas macho o usar alambre estañado |
| Perilla eje 6 mm | 1 | No confirmada | Perilla de aluminio de 15×17 mm en Electronilab ($2.800): confirmar el eje del EC11 |

## 4. Incompatibilidades o publicaciones ambiguas

- **Piezo de Electronilab:** es pasivo ✓, pero mide unos 44×14 mm frente a ~12 mm de la BOM.
  Revisar el espacio en el panel.
- **Adaptador ADAP-5V-5A:** el plug es de 5,5×2,5 mm. Se cambió el jack de panel a 2,5 mm
  (CON-156A) para que encajen. Si prefieres el jack de 5,5×2,1, cambia también el adaptador.
- **Electrolíticos de 470 µF y 680 µF:** ninguna tienda indica low-ESR; el de 470 µF es de 35 V
  (la BOM acepta 10 V o más).
- **Encoder EC11:** la ficha no indica el diámetro del eje.
- **2N2222:** la ficha no dice si es la versión A; confirmar el orden EBC del fabricante.
- **Cerámicos de 100 nF:** el dieléctrico no está indicado.
- **ZMPT101B:** no montar el primario de J4/F1 en la perforada de baja tensión, como indica la BOM.

## 5. Totales del medidor (sin envío)

| Tienda | Subtotal medidor |
|---|---:|
| Sigma Electrónica | $14.280 |
| Electronilab | $173.984 |
| Didácticas Electrónicas | $194.116,37 |
| CVR Electrónica | $33.462 |
| **Total medidor** | **$415.842,37** |

Totales de cada carrito con ambos proyectos (reconstruidos): Sigma $43.852; Electronilab
$241.584; Didácticas $350.418,11; CVR $82.698. Total general: **$718.552,11**.

NO SE REALIZÓ NINGUNA COMPRA
