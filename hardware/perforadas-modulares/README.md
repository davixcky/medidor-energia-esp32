# Medidor E.9 touch-first with 12 V input

The current source of truth is the five E.9 KiCad sheets in `kicad/`, the generated
per-board BOMs in `bom-por-tarjeta/`, and `conexiones-entre-tarjetas.csv`.
They match the current CAD: horizontal touch LilyGO, 12 V input, separate LM2596
buck and no physical user buttons or encoder.

Esta era la fuente de verdad E.7 para montar el medidor en tarjetas
perforadas pequeñas. Conserva el circuito analógico validado del esquemático
los cinco esquemáticos KiCad nativos de `kicad/`; solamente cambia su partición
física e incorpora la interfaz local y el ESP32S V1.1 USB-C de 38 pines.

## Arquitectura: cinco tarjetas y una zona de red separada

| Tarjeta | Tamaño orientativo | Contenido | Conectores principales |
|---|---:|---|---|
| T1 Power | 50 x 40 mm | J1, F2, D1, C1, C2 and +5V/+12V/GND distribution | Cut 10 mm from the user's 60 x 40 mm board; 12 V input; outputs to T3, T4 and T5 |
| T2 Corriente y VBIAS | 70 x 55 mm | R1-R6, C5-C8, D2-D5, entradas de las dos SCT | jacks CH1/CH2; bus ADC de 4 vías a T4 |
| T3 Tensión MBT | 55 x 45 mm | J5, R7-R8, C9, D6-D7 y filtro `V_ADC` | alimentación desde T1; ZMPT MBT; bus ADC de 3 vías a T4 |
| T4 Control | 80 x 65 mm | ESP32S V1.1 USB-C in sockets, ESP-NOW, LilyGO power and status LED | power, ADC-I, ADC-V, LilyGO power, status LED and T5 |
| T5 Interface/alerts | 65 x 50 mm | 74HCT245, 12 V WS2811 FCOB output and piezo driver | power, digital signals from T4, FCOB and piezo |
| U4 Buck separado | 43 x 21 x 14 mm reservados | LM2596 en cuna impresa sin tornillos | 12 V a 5 V |
| Z1 zona de red | no es perforada | J4, F1 y primario del ZMPT101B, dentro de guarda aislante | L/N de 120 V; cable MBT de 3 vías hacia T3 |

No se monta red de 120 V en una tarjeta perforada. Z1 debe estar encerrada,
separada y sin cobre expuesto accesible. El montaje y prueba de esa zona deben
hacerlos personas calificadas, con el equipo desconectado.

## Decisiones importantes

- T2 reúne las dos pinzas y VBIAS. Así las señales de microvoltios/milivoltios
  no comparten recorridos largos con NeoPixels, LCD o Wi-Fi.
- R1 y R2 se sueldan **directamente sobre las terminales de los jacks de panel**.
  El secundario de una SCT-013-000 nunca debe quedar abierto con corriente en el
  primario. No se ponen estas resistencias después de un conector removible.
- T3 solo recibe el lado de muy baja tensión del módulo ZMPT. J4 y F1 permanecen
  en Z1.
- T1 distribuye +5 V y GND en estrella. Cada tarjeta tiene su propio par de
  alimentación; no se encadenan T2/T3/T4/T5.
- Las uniones analógicas llevan señal y GND en el mismo cable, son cortas y se
  mantienen lejos de LCD, Wi-Fi, piezo y la FCOB.
- GPIO32 and GPIO33 are not assigned to panel controls. E.9 has no SW1, SW2 or ENC1 components.
- Se documenta 74HCT245N DIP-20 como reemplazo local del 74AHCT125. A 5 V, una
  entrada HCT reconoce 3,3 V del ESP32; el firmware no cambia. No usar módulos
  I2C bidireccionales con BSS138 para la línea WS2811.
- The purchased FCOB is 12 V. It uses the protected 12 V branch; the LM2596 produces 5 V for logic and analog electronics.
- Todos los conectores entre tarjetas son JST-XH de 2,50 mm, polarizados. Puede
  emplearse un sistema equivalente de 2,54 mm, pero no deben mezclarse familias.

## Orden de montaje

1. Construir T1 y comprobar polaridad, continuidad y +5 V protegido sin carga.
2. Construir T2; comprobar VBIAS = 1,32 V aproximadamente y los burdens antes
   de conectar las pinzas.
3. Construir T3 sin conectar 120 V; probar su entrada con generador de baja
   tensión o con la salida MBT del ZMPT ya verificada.
4. Build T4, power the main ESP32 and verify ADC pins, ESP-NOW, LilyGO power and the status LED without T2, T3 or T5.
5. Build T5 and test the passive piezo and one FCOB segment at limited brightness.
6. Unir tarjetas de una en una. La prueba de red se hace al final, dentro de la
   guarda, con fusible y protocolo de aislamiento.

## Archivos

- `kicad/medidor-t1.kicad_sch` … `medidor-t5.kicad_sch`: **única fuente de
  verdad eléctrica**, editable en KiCad.
- `kicad/medidor-t1.pdf` … `medidor-t5.pdf`: exportaciones A4 de esos mismos
  archivos; los reportes `*-erc.rpt` deben indicar cero violaciones.
- `schematic-previews/medidor-t1.png` … `medidor-t5.png`: 200 DPI previews for
  reading on screen without opening KiCad. The sheets prioritize large reference
  and net labels; exact component values and purchase status are in the matching
  `bom-por-tarjeta/BOM-T*.csv` file.
- `medidor-E9-esquematicos-T1-T5.pdf`: the five native schematic PDFs combined, without
  redibujar ni alterar el circuito.
- `medidor-E9-construction-pack.pdf`: recommended workshop file. It contains
  T1 schematic, T1 component table, T2 schematic, T2 component table, and so
  on; the final page contains the off-board/panel/Z1 components.
- `construction-packets/T1-schematic-and-BOM.pdf` …
  `T5-schematic-and-BOM.pdf`: two-page packets for building one board at a time.
- `kicad/contratos.json`: pinout validado de arneses y datos de la tira real.
- `esquema-modular-perforadas.pdf`: plano legible de las cinco tarjetas,
  arneses y secuencia de integración; se conserva como vista general.
- `BOM-E9-by-board.csv` and `.md`: combined mounted-quantity BOM, grouped by board.
- `bom-por-tarjeta/BOM-T1.csv` … `BOM-T5.csv`: one construction BOM per perfboard.
- `bom-por-tarjeta/BOM-OFFBOARD.csv`: LM2596, LilyGO, panel parts, sensors and guarded Z1 parts.
- `BOM-precision.csv` and `.md`: compatibility copies generated from the same E.9 BOM source.
- `lista-por-tarjeta.csv`: ubicación de cada componente.
- `conexiones-entre-tarjetas.csv`: pinout inequívoco de cada arnés.
- `SEGURIDAD-Y-PRUEBAS.md`: criterios de construcción y aceptación.
- `PROMPT-CLAUDE-CARRITOS.md`: solicitud para preparar carritos en Colombia,
  sin efectuar compras.
- `../../freecad/revision-e7/medidor-E7-perforadas.FCStd` y `.step`: gabinete
  con tapa de cierre magnético, T1–T5, arneses y zona Z1 bajo guarda independiente.
- `../../freecad/revision-e7/medidor-E7-{cerrado,abierto,planta,trasera,tapa-interior,difusor,cierre-magnetico}.png`:
  vistas actualizadas.
- `../../freecad/revision-e7/MEDIDAS.md`: cotas publicadas, conservadoras y
  pendientes de medir; `validacion-3d.json` compara T1–T5 con los esquemáticos.
- `../COMPONENTES-COMPRADOS-VERIFICADOS.md`: compras con evidencia.

## Validación que sí aplica

La división no cambia los valores ni las redes del acondicionamiento analógico.
El generador de los cinco esquemas comprueba que cada arnés tenga exactamente el
mismo orden de pines en ambos extremos. KiCad ERC reporta 0 errores y 0
advertencias en T1–T5. Ninguna red de 120 V aparece en una perforada.
The CAD electrical cross-check reports no layout errors. E.9 uses an isolated
12 V supply through CON-156A; the FCOB uses protected 12 V and U4 generates
regulated 5 V. U4 must be adjusted and verified under a current-limited load
before C_BUCK_OUT or any electronics are connected.

`python3 herramientas/validar_esquematicos_e9.py` exports the native KiCad
netlists and verifies the critical topology that passive-pin ERC cannot detect:
the SCT tip side feeds R5/R6, both burden resistors return to VBIAS, and the
midpoints of D2-D7 are joined to their corresponding ADC nodes.

Las láminas dibujadas antiguas se retiraron para evitar dos fuentes de verdad.
Para cablear siempre manda el `.kicad_sch` de `kicad/` y su PDF exportado.

Esta documentación todavía requiere continuidad, medición y calibración sobre
el prototipo físico; una simulación no valida errores de cableado manual.
