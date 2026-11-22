# E.9 BOM by board

Generated from `herramientas/generar_kicad_perforadas.py`.
Quantities are mounted quantities, not spare-purchase quantities. `verified` refers only to documented purchase evidence.

## T1

| References | Qty | Description | Purchase status | Mounting / verification |
|---|---:|---|---|---|
| J1 | 1 | 2-way 5.08 mm terminal block | planned | 12 V input from panel CON-156A |
| F2 | 1 | Resettable PTC, 2.0 A hold, rated >=16 V | planned | Series input protection |
| D1 | 1 | 1N5822 Schottky, 3 A, DO-201AD | planned | Do not substitute the purchased 1N5819 without current/thermal review |
| C1 | 1 | 470 uF 35 V electrolytic | verified purchase | At protected 12 V input; measure body before final placement |
| C2 | 1 | 100 nF 50 V ceramic THT | verified shared stock | At protected 12 V input |
| C17 | 1 | 680 uF 16 V electrolytic | verified purchase | At returned 5 V rail; low-ESR not verified |
| C_BUCK_IN C_BUCK_OUT C_PWR3 C_PWR4 | 4 | JST-XH 2-way vertical header | planned | Key every harness; BUCK IN and OUT must not be interchangeable |
| C_PWR5 | 1 | JST-XH 3-way vertical header | planned | +5V_PROT / +12V_PROT / GND |
| BOARD | 1 | FR4 perfboard, 2.54 mm pitch, cut to 50 x 40 mm from user's 60 x 40 mm board | declared on hand; dimensions unverified | Test against the printed supports, mark, then remove 10 mm from the long side and deburr all copper edges |

## T2

| References | Qty | Description | Purchase status | Mounting / verification |
|---|---:|---|---|---|
| J2 J3 | 2 | JST-XH 2-way vertical header | planned | Short harnesses to panel SCT jacks |
| R3 | 1 | 15 kohm metal-film resistor, 1%, 0.25 W | planned | VBIAS upper divider |
| R4 | 1 | 10 kohm metal-film resistor, 1%, 0.25 W | planned | VBIAS lower divider |
| R5 R6 | 2 | 3.3 kohm metal-film resistor, 1%, 0.25 W | planned | ADC series filters |
| C5 C6 | 2 | 47 nF film or C0G THT, 5% | planned | Return to VBIAS, not GND |
| C7 | 1 | 10 uF >=16 V electrolytic | planned | VBIAS reservoir |
| C8 | 1 | 100 nF 50 V ceramic THT | verified shared stock | VBIAS bypass |
| D2 D3 D4 D5 | 4 | BAT85 Schottky DO-35 | planned | ADC clamps |
| C_ADC_I | 1 | JST-XH 4-way vertical header | planned | +3V3 / GND / CH1_ADC / CH2_ADC |
| BOARD | 1 | FR4 perfboard, 2.54 mm pitch, cut to 70 x 55 mm | planned | Keep SCT traces away from digital/power wiring |

## T3

| References | Qty | Description | Purchase status | Mounting / verification |
|---|---:|---|---|---|
| J5 | 1 | 3-way 5.08 mm terminal block | planned | Only ZMPT low-voltage side enters this board |
| R7 | 1 | 11 kohm metal-film resistor, 1%, 0.25 W | planned | Voltage-channel divider/filter |
| R8 | 1 | 13 kohm metal-film resistor, 1%, 0.25 W | planned | Do not replace with 12 kohm |
| C9 | 1 | 27 nF film or C0G THT, 5% | planned | Voltage-channel filter |
| D6 D7 | 2 | BAT85 Schottky DO-35 | planned | ADC clamps |
| C_PWR3 | 1 | JST-XH 2-way vertical header | planned | +5V_PROT / GND |
| C_ADC_V | 1 | JST-XH 3-way vertical header | planned | +3V3 / GND / V_ADC |
| BOARD | 1 | FR4 perfboard, 2.54 mm pitch, cut to 55 x 45 mm | planned | No mains-voltage component is allowed on T3 |

## T4

| References | Qty | Description | Purchase status | Mounting / verification |
|---|---:|---|---|---|
| U1 | 1 | ESP32S V1.1 USB-C, 38 pins, ESP32-WROOM-32 | planned | ADC1 pins only; keep antenna and USB-C clear |
| U1 sockets | 2 | Female header strip 1x19, 2.54 mm | verified shared stock | Cut from verified 1x40 strips; confirm 25.4 mm row spacing |
| R11 | 1 | 330 ohm metal-film resistor, 1%, 0.25 W | planned | Panel status LED series resistor |
| C_PWR4 C_LILY C_LED | 3 | JST-XH 2-way vertical header | planned | LilyGO connector carries power only |
| C_ADC_V C_UI_D | 2 | JST-XH 3-way vertical header | planned | Voltage ADC and digital-output harnesses |
| C_ADC_I | 1 | JST-XH 4-way vertical header | planned | Two current ADC channels |
| BOARD | 1 | FR4 perfboard, 2.54 mm pitch, cut to 80 x 65 mm | planned | No SW1, SW2, ENC1 or wired LCD bus in E.9 |

## T5

| References | Qty | Description | Purchase status | Mounting / verification |
|---|---:|---|---|---|
| U3 | 1 | 74HCT245N DIP-20 | verified shared purchase | HCT required; do not use 74HC245 |
| U3 socket | 1 | DIP-20 socket, 7.62 mm | verified shared purchase | Install before U3 |
| Q1 | 1 | 2N2222A or PN2222A THT | planned | Verify E/B/C for the exact manufacturer |
| R16 | 1 | 330 ohm metal-film resistor, 1%, 0.25 W | planned | Series resistor on FCOB data |
| R17 R23 | 2 | 10 kohm metal-film resistor, 1%, 0.25 W | planned | Input and unused-channel pulldowns |
| R18 | 1 | 1 kohm metal-film resistor, 1%, 0.25 W | planned | Piezo transistor base |
| C14 | 1 | 100 nF 50 V ceramic THT | verified shared stock | Directly beside U3 pins 20/10 |
| C16 | 1 | 680 uF 16 V electrolytic | verified purchase | Beside C_PIX; low-ESR not verified |
| C_PWR5 C_UI_D C_PIX | 3 | JST-XH 3-way vertical header | planned | Power, control and FCOB |
| C_BZ | 1 | JST-XH 2-way vertical header | planned | Panel passive piezo |
| BOARD | 1 | FR4 perfboard, 2.54 mm pitch, cut to 65 x 50 mm | planned | Encoder and its RC network are absent in E.9 |

## Off-board, panel and guarded Z1

| References | Qty | Description | Purchase status | Mounting / verification |
|---|---:|---|---|---|
| U4 | 1 | LM2596 adjustable buck module, reserved 43 x 21 x 14 mm | planned / exact model unverified | Adjust to 5.0 V unloaded, then verify under current-limited load |
| LCD1 | 1 | LilyGO T4-S3 AMOLED 2.41 in, 450 x 600 | planned | ESP-NOW terminal; VBUS/GND only; disconnect harness before USB |
| JDC | 1 | CON-156A panel jack, 5.5 x 2.5 mm, center positive | verified purchase | 12 V input |
| J2P J3P | 2 | 3.5 mm female panel jack | planned | For SCT-013-000 plugs |
| R1 | 1 | 22 ohm metal-film resistor, 1%, 0.25 W | planned | Solder directly across CH1 panel jack |
| R2 | 1 | 47 ohm metal-film resistor, 1%, 0.25 W | planned | Solder directly across CH2 panel jack |
| D8 | 1 | Green diffused panel LED, 5 mm | verified purchase | Connected through C_LED; R11 is on T4 |
| BZ1 | 1 | GEP0008 passive piezo, 44 x 14 mm | declared purchased; document pending | Not an active buzzer |
| FCOB | 1 | BTF FCOB WS2811, 12 V, 12 mm, 200 mm used | planned | Four 50 mm addressable pixels; <=2 W design load |
| SCT1 SCT2 | 2 | SCT-013-000, 100 A : 50 mA, no internal burden | planned | Never leave secondary open while clamped around energized conductor |
| Z1-U2 | 1 | ZMPT101B module | planned | Primary remains inside guarded Z1 compartment |
| Z1-F1 | 1 | T500 mA 250 V slow-blow fuse + enclosed holder | planned | Phase conductor only; qualified mains work |
| Z1-J4 | 1 | Guarded 2-way mains terminal + PG7 gland | planned | Inside opaque segregated guard |
| SUPPLY | 1 | Isolated regulated 12 V DC adapter, center-positive | planned | Final current rating after measured load test; 2 A provisional minimum |
