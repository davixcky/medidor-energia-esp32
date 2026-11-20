# Medidor E.7 en tarjetas perforadas compactas

Esta es la fuente de verdad para montar el medidor en tarjetas
perforadas pequeñas. Conserva el circuito analógico validado del esquemático
los cinco esquemáticos KiCad nativos de `kicad/`; solamente cambia su partición
física e incorpora la interfaz local y el ESP32S V1.1 USB-C de 38 pines.

## Arquitectura: cinco tarjetas y una zona de red separada

| Tarjeta | Tamaño orientativo | Contenido | Conectores principales |
|---|---:|---|---|
| T1 Alimentación | 50 x 40 mm | J1, F2, D1, C1, C2, MT3608 y distribución +5V/+12V/GND | entrada 5 V; salidas a T3, T4 y T5 |
| T2 Corriente y VBIAS | 70 x 55 mm | R1-R6, C5-C8, D2-D5, entradas de las dos SCT | jacks CH1/CH2; bus ADC de 4 vías a T4 |
| T3 Tensión MBT | 55 x 45 mm | J5, R7-R8, C9, D6-D7 y filtro `V_ADC` | alimentación desde T1; ZMPT MBT; bus ADC de 3 vías a T4 |
| T4 Control | 80 x 65 mm | ESP32S V1.1 USB-C en zócalos, LCD, pulsadores e indicadores | alimentación, ADC-I, ADC-V, LCD, panel y T5 |
| T5 Interfaz/alertas | 65 x 50 mm | encoder, 74HCT245, conector FCOB WS2811 12 V y driver del piezo | alimentación, señales desde T4, encoder, LEDs y piezo |
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
- GPIO32 y GPIO33 ya no son reserva: la revisión B los usa para el encoder. Solo
  GPIO34 queda como reserva real.
- Se documenta 74HCT245N DIP-20 como reemplazo local del 74AHCT125. A 5 V, una
  entrada HCT reconoce 3,3 V del ESP32; el firmware no cambia. No usar módulos
  I2C bidireccionales con BSS138 para la línea WS2811.
- La barra comprada es BTF FCOB WS2811 de 12 V, 720 LED/m y 20 segmentos/m.
  Cuatro segmentos miden 200 mm y consumen hasta 2 W. T1 eleva 5 V a 12 V con
  un MT3608; se ajusta a 12,0 V sin carga antes de conectar la barra.
- Todos los conectores entre tarjetas son JST-XH de 2,50 mm, polarizados. Puede
  emplearse un sistema equivalente de 2,54 mm, pero no deben mezclarse familias.

## Orden de montaje

1. Construir T1 y comprobar polaridad, continuidad y +5 V protegido sin carga.
2. Construir T2; comprobar VBIAS = 1,32 V aproximadamente y los burdens antes
   de conectar las pinzas.
3. Construir T3 sin conectar 120 V; probar su entrada con generador de baja
   tensión o con la salida MBT del ZMPT ya verificada.
4. Construir T4, alimentar el ESP32 y probar botones/LCD sin T2, T3 ni T5.
5. Construir T5 y probar encoder, piezo y un segmento FCOB con brillo limitado.
6. Unir tarjetas de una en una. La prueba de red se hace al final, dentro de la
   guarda, con fusible y protocolo de aislamiento.

## Archivos

- `kicad/medidor-t1.kicad_sch` … `medidor-t5.kicad_sch`: **única fuente de
  verdad eléctrica**, editable en KiCad.
- `kicad/medidor-t1.pdf` … `medidor-t5.pdf`: exportaciones A4 de esos mismos
  archivos; los reportes `*-erc.rpt` deben indicar cero violaciones.
- `medidor-E7-esquematicos-T1-T5.pdf`: los cinco PDFs nativos reunidos, sin
  redibujar ni alterar el circuito.
- `kicad/contratos.json`: pinout validado de arneses y datos de la tira real.
- `esquema-modular-perforadas.pdf`: plano legible de las cinco tarjetas,
  arneses y secuencia de integración; se conserva como vista general.
- `BOM-precision.csv`: compra completa y cantidades recomendadas.
- `BOM-precision.md`: resumen humano y criterios de sustitución.
- `lista-por-tarjeta.csv`: ubicación de cada componente.
- `conexiones-entre-tarjetas.csv`: pinout inequívoco de cada arnés.
- `SEGURIDAD-Y-PRUEBAS.md`: criterios de construcción y aceptación.
- `PROMPT-CLAUDE-CARRITOS.md`: solicitud para preparar carritos en Colombia,
  sin efectuar compras.
- `../../freecad/revision-e7/medidor-E7-perforadas.FCStd` y `.step`: gabinete
  compacto con T1–T5, zona Z1 segregada y FCOB empotrada.
- `../../freecad/revision-e7/medidor-E7-{cerrado,abierto,planta}.png` y
  `medidor-E7-tapa-interior.png`: vistas actualizadas.
- `../../freecad/revision-e7/medidas-componentes.json`: cotas de los artículos
  comprados, su fuente y las dimensiones que todavía deben medirse con calibre.

## Validación que sí aplica

La división no cambia los valores ni las redes del acondicionamiento analógico.
El generador de los cinco esquemas comprueba que cada arnés tenga exactamente el
mismo orden de pines en ambos extremos. KiCad ERC reporta 0 errores y 0
advertencias en T1–T5. Ninguna red de 120 V aparece en una perforada.
El generador de la perforada monolítica verificó 27/27 redes contra la netlist y
`herramientas/simulacion.py` aprobó los márgenes de los tres ADC, las frecuencias
de corte y el desfase. El caso de 4,75 V/500 mA no cumple; se exige adaptador
regulado. La unidad comprada de 5 V/5 A alimenta T1; la FCOB recibe 12 V solo
desde el MT3608 y no directamente desde el adaptador.

Las láminas dibujadas antiguas se retiraron para evitar dos fuentes de verdad.
Para cablear siempre manda el `.kicad_sch` de `kicad/` y su PDF exportado.

Esta documentación todavía requiere continuidad, medición y calibración sobre
el prototipo físico; una simulación no valida errores de cableado manual.
