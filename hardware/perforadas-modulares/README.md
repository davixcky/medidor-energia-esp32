# Medidor E.5 en tarjetas perforadas modulares

Esta es la fuente de verdad para montar la revisión B del medidor en tarjetas
perforadas pequeñas. Conserva el circuito analógico validado del esquemático
`hardware/medidor-energia.kicad_sch`; solamente cambia su partición física y se
incorpora la interfaz local de la revisión B.

## Arquitectura: cinco tarjetas y una zona de red separada

| Tarjeta | Tamaño orientativo | Contenido | Conectores principales |
|---|---:|---|---|
| T1 Alimentación | 60 x 50 mm | J1, F2, D1, C1, C2 y distribución en estrella de +5V/GND | entrada 5 V; salidas a T3, T4 y T5 |
| T2 Corriente y VBIAS | 90 x 70 mm | R1-R6, C5-C8, D2-D5, entradas de las dos SCT | jacks CH1/CH2; bus ADC de 4 vías a T4 |
| T3 Tensión MBT | 70 x 50 mm | J5, R7-R8, C9, D6-D7 y filtro `V_ADC` | alimentación desde T1; ZMPT MBT; bus ADC de 3 vías a T4 |
| T4 Control | 100 x 80 mm | ESP32 en zócalos, LCD, pulsadores, LED de estado e indicadores | alimentación, ADC-I, ADC-V, LCD, panel y T5 |
| T5 Interfaz/alertas | 80 x 60 mm | encoder, 74HCT245, cuatro WS2812B y driver del piezo | alimentación, señales desde T4, encoder, LEDs y piezo |
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
  mantienen lejos de LCD, Wi-Fi, piezo y NeoPixels.
- GPIO32 y GPIO33 ya no son reserva: la revisión B los usa para el encoder. Solo
  GPIO34 queda como reserva real.
- Se documenta 74HCT245N DIP-20 como reemplazo local del 74AHCT125. A 5 V, una
  entrada HCT reconoce 3,3 V del ESP32; el firmware no cambia. No usar módulos
  I2C bidireccionales con BSS138 para WS2812.
- Todos los conectores entre tarjetas son JST-XH de 2,50 mm, polarizados. Puede
  emplearse un sistema equivalente de 2,54 mm, pero no deben mezclarse familias.

## Orden de montaje

1. Construir T1 y comprobar polaridad, continuidad y +5 V protegido sin carga.
2. Construir T2; comprobar VBIAS = 1,32 V aproximadamente y los burdens antes
   de conectar las pinzas.
3. Construir T3 sin conectar 120 V; probar su entrada con generador de baja
   tensión o con la salida MBT del ZMPT ya verificada.
4. Construir T4, alimentar el ESP32 y probar botones/LCD sin T2, T3 ni T5.
5. Construir T5 y probar encoder, piezo y un solo pixel antes de colocar cuatro.
6. Unir tarjetas de una en una. La prueba de red se hace al final, dentro de la
   guarda, con fusible y protocolo de aislamiento.

## Archivos

- `esquema-modular-perforadas.pdf`: plano legible de las cinco tarjetas,
  circuitos conservados, T5, arneses y secuencia de integración.
- `BOM-precision.csv`: compra completa y cantidades recomendadas.
- `BOM-precision.md`: resumen humano y criterios de sustitución.
- `lista-por-tarjeta.csv`: ubicación de cada componente.
- `conexiones-entre-tarjetas.csv`: pinout inequívoco de cada arnés.
- `SEGURIDAD-Y-PRUEBAS.md`: criterios de construcción y aceptación.
- `PROMPT-CLAUDE-CARRITOS.md`: solicitud para preparar carritos en Colombia,
  sin efectuar compras.
- `../../freecad/revision-e5/medidor-E5-perforadas.FCStd` y `.step`: gabinete
  ampliado con T1–T5 en una sola capa, zona Z1 segregada y barra NeoPixel visible.
- `../../freecad/revision-e5/medidor-E5-{cerrado,abierto,planta}.png`: vistas actualizadas
- `../../freecad/revision-e5/medidas-componentes.json`: cotas de los artículos
  comprados, su fuente y las dimensiones que todavía deben medirse con calibre.

## Validación que sí aplica

La división no cambia los valores ni las redes del acondicionamiento analógico.
El generador de la perforada monolítica verificó 27/27 redes contra la netlist y
`herramientas/simulacion.py` aprobó los márgenes de los tres ADC, las frecuencias
de corte y el desfase. El caso de 4,75 V/500 mA no cumple; se exige adaptador
regulado de 5,1 V y 2 A como mínimo (3 A recomendado).

Esta documentación todavía requiere continuidad, medición y calibración sobre
el prototipo físico; una simulación no valida errores de cableado manual.
