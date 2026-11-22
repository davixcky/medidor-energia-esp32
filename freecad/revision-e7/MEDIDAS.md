# Medidas del modelo E.7

Revisión `E.8-serviciable-2026-11-21`, en milímetros. Generado por `informe_medidas.py`; no editar a mano.

**Ninguna cota está confirmada con calibre sobre la pieza recibida.** «Publicada» significa que la da la tienda o el fabricante; «nominal», que sale de la norma o serie del componente; «conservadora», que el CAD reserva espacio de más hasta medir. La columna de compra sigue `hardware/COMPONENTES-COMPRADOS-VERIFICADOS.md`.

## Publicadas

| Componente | Cota usada en el CAD | Compra | Nota |
|---|---|---|---|
| `PCB-FV-7X9-HQ` | 90 × 70 × 1.6 | planificada | Stock 90x70; recortar para T1 50x40, T2 70x55, T3 55x45 y T5 65x50; paso 2.54, perforacion 1.0; queda una de repuesto |
| `PCB-FV-8X12-HQ` | 120 × 80 × 1.6 | planificada | Stock 120x80; recortar T4 a 80x65 mm |
| `GEP0008-piezo-pasivo` | diametro 44.0; altura 14.0 | planificada |  |
| `BTF-FCOB-WS2811-12V-720L-IP30` | 200 × 12 × 2 | planificada | Modelo FCOB-12V-720L-W-IP30-SPI; 720 LED/m, 20 IC/m, ancho 12 mm, max. 10 W/m |

## Nominales

| Componente | Cota usada en el CAD | Compra | Nota |
|---|---|---|---|
| `1N5819-DO41` | cuerpo diametro 2.7; cuerpo largo 5.2; paso 10.16 | verificada | D1 comprado. El esquemático y el BOM piden 1N5822 DO-201AD de 3 A: discrepancia eléctrica abierta. |
| `REGLETA-HEMBRA-1x40-2.54` | paso 2.54; altura 8.5 | verificada |  |
| `LED-5-VE-D` | diametro 5.0; altura 8.6; agujero panel 5.1 | verificada | D8. El archivo de compras llama indicador de panel al LED verde de 3 mm; el BOM y el esquemático dicen 5 mm. Sin resolver. |
| `JST-XH-2.5` | paso 2.5; ancho 2,5 x (vías - 1) + 4,9; fondo 5.75; altura 7.0 | planificada | Cotas de la serie XH tomadas de memoria de la hoja del fabricante; verificar con la pieza. |
| `PRENSAESTOPA-PG7` | agujero panel 12.5 | planificada |  |
| `SEPARADOR-M3-NYLON` | altura 6.0; entre caras 5.5; cabeza tornillo 5.5 | planificada |  |
| `IMAN-NEODIMIO-6x2` | diametro 6.0; altura 2.0 | planificada | Disco de neodimio 6 x 2 mm, imantado axialmente; cuatro en el gabinete y cuatro en la tapa. No figura en COMPONENTES-COMPRADOS-VERIFICADOS.md. Fuerza de retención y polaridad sin comprobar. |
| `GABINETE-E7-IMPRESO` | 280 × 180 × 70 | no aplica | Pared 2,5; piso 3; tapa y guarda 3. Pide una cama de impresión de 280 mm o partir la pieza. |

## Conservadoras o mixtas

| Componente | Cota usada en el CAD | Compra | Nota |
|---|---|---|---|
| `ESP32S-V1.1-USB-C-38P` | 58 × 28 × 13 | planificada |  |
| `LilyGO-T4-S3-AMOLED-2.41` | 56 × 44 × 13 | planificada |  |
| `ZMPT101B-SNC0015` | 51.7 × 21.6 × 17 | planificada |  |
| `SW12BP` | cuerpo diametro 12.0; largo posterior 18.0; brida diametro 14.4; tuerca entre caras 14.0 | verificada | Metálico, momentáneo, sin iluminación. Agujero de 12 mm publicado; largo posterior y tuerca reservados. |
| `EC11-BOT0011` | cuerpo [12.0, 12.0, 6.5]; casquillo diametro 7.0; eje diametro 6.0; eje largo sobre cuerpo 15.0; perilla {'diametro': 18.0, 'altura': 12.0} | planificada |  |
| `MT3608-MODULO-BOOST` | 36 × 17 × 14 | planificada |  |
| `74HCT245N-con-zocalo-DIP20` | 25.8 × 10.1 × 8.1 | verificada |  |
| `CON-156A-jack-DC-5.5x2.5` | agujero panel 8.2; cuerpo diametro 10.0; largo interior 12.5 | verificada |  |
| `CE470UF35V` | diametro 10.0; altura 17.0 | verificada |  |
| `CE680UF16V` | diametro 10.0; altura 17.0 | verificada | C16 y C17 usan las dos unidades compradas; no queda repuesto. Low-ESR no verificado. |
| `CC0.1UF50V` | 6 × 2.6 × 6 | verificada |  |
| `BORNERA-5.08` | ancho 5,08 x polos + 0,6; fondo 8.0; altura 10.0 | planificada | El esquemático asigna huella JST-XH a J1 y J5; el BOM pide bornera. Unificar antes de soldar. |
| `PTC-2A` | 12.5 × 3.5 × 15 | planificada |  |
| `JACK-3.5-PANEL` | agujero panel 6.2; cuerpo diametro 8.0; largo interior 13.5 | planificada |  |
| `PORTAFUSIBLE-5x20-CERRADO` | diametro 12.5; largo 42.0 | planificada | F1 es T500 mA lento. El CON-183AC y los FC-3A rápidos comprados no se asignan al medidor. |
| `J4-BORNERA-PROTEGIDA-2P` | 22 × 16 × 14 | planificada |  |

## Pendientes de medir

- `ESP32S-V1.1-USB-C-38P`: largo y ancho exactos de la unidad recibida
- `ESP32S-V1.1-USB-C-38P`: altura total con headers
- `ESP32S-V1.1-USB-C-38P`: sobremoldeo del cable USB-C que se usará
- `ESP32S-V1.1-USB-C-38P`: altura del conector USB-C sobre el PCB
- `LilyGO-T4-S3-AMOLED-2.41`: espesor real del vidrio y del conjunto
- `LilyGO-T4-S3-AMOLED-2.41`: posición del área activa respecto al vidrio
- `LilyGO-T4-S3-AMOLED-2.41`: posición de la cabecera de alimentación VBUS/GND
- `ZMPT101B-SNC0015`: altura total real
- `SW12BP`: largo posterior
- `SW12BP`: diametro de tuerca
- `EC11-BOT0011`: diametro y largo del eje
- `EC11-BOT0011`: rosca
- `EC11-BOT0011`: cuerpo
- `EC11-BOT0011`: paso de terminales
- `MT3608-MODULO-BOOST`: envolvente exacta y posicion del potenciometro del modulo recibido
- `74HCT245N-con-zocalo-DIP20`: ancho entre hileras 7,62 mm del zócalo
- `74HCT245N-con-zocalo-DIP20`: altura del conjunto
- `REGLETA-HEMBRA-1x40-2.54`: altura real del aislante
- `CON-156A-jack-DC-5.5x2.5`: diámetro de rosca
- `CON-156A-jack-DC-5.5x2.5`: largo interior
- `CON-156A-jack-DC-5.5x2.5`: posición de terminales
- `CE470UF35V`: diámetro, altura y paso de la unidad recibida
- `CE680UF16V`: diámetro, altura y paso
- `JACK-3.5-PANEL`: rosca
- `JACK-3.5-PANEL`: largo
- `JACK-3.5-PANEL`: terminales
- `PRENSAESTOPA-PG7`: largo de rosca y tuerca

## Holguras comprobadas en el CAD

- Tapa suelta con imanes: recorre la trayectoria de servicio hasta quedar de pie en sus bolsillos sin interferencias (0 detectadas).
- Imanes: el más cercano al transformador del ZMPT101B queda a 98.5 mm (mínimo de diseño 60 mm; el efecto magnético no está medido).
- Difusor hexagonal: 83 celdas, espesores 0.3 / 0.5 / 1.1 mm, 7.9 mm entre la FCOB y la piel.
- Piezas sin apoyo: 0 de 296 objetos.

| Puente de arnés | Vías | Largo | Radio de coca cerrada | Cuerda con tapa de pie | Cuerda máxima del recorrido | Holgura mínima | Separación a la pared frontal |
|---|---:|---:|---:|---:|---:|---:|---:|
| LCD | 4 | 91.59 | 8 | 46.76 | 57.25 | 34.35 | 12.81 |
| panel_T4 | 6 | 78.59 | 8 | 39 | 49.12 | 29.47 | 7.87 |
| panel_T5 | 10 | 77.61 | 11 | 39.01 | 48.51 | 29.1 | 3.36 |

Radio de curvatura mínimo entre los 37 arneses: 8 mm en `Puente_arnes_panel_T4` (2.5 diámetros). El criterio de 2,5 diámetros es de este diseño, no de una norma.

Esto es una comprobación geométrica del modelo. No valida aislamiento, distancias normativas ni el prototipo físico.
