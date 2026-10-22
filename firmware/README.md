# Firmware del medidor de energía (ESP32-DevKitC V4)

PlatformIO con el *framework* Arduino para ESP32 (núcleo 2.0.17, ESP-IDF 4.4).

| Núcleo | Tarea | Qué hace |
|---|---|---|
| 1 | `adquisicion` | Muestrea V (GPIO35), CH1 (GPIO36) y CH2 (GPIO39) a 8.000 muestras/s por canal y cierra una ventana cada 60 ciclos de red (≈ 1 s). Solo entrega resultados por cola. |
| 0 | `red` | Wi-Fi, hora por NTP (UTC−5), registro ADR-001 de 40 B por ventana, búfer de 1.200 registros (20 min sin red) y envío en lotes cada 5 s a `POST /api/ingesta`. |
| 0 | `interfaz` | LCD Waveshare de 1,9" por SPI (resumen, CH1, CH2, energía hoy, alerta, tara), pulsadores SW1/SW2 y LED de estado. |

El cálculo (`lib/medicion/`) no depende de Arduino:

- Ventana sincronizada por cruce por cero, sobre ciclos enteros.
- Valores eficaces y potencia activa con sumas enteras exactas, quitando la componente continua de la propia ventana (no hace falta conocer VBIAS).
- La tensión se interpola al instante de cada corriente para corregir el retardo del multiplexado; el retardo se mide al arrancar.
- S = V·I, Q = √(S² − P²), FP = P/S.
- Frecuencia por ciclos sobre la duración real de la ventana.
- THD de la corriente de CH1 hasta el armónico 40 con Goertzel, compensando la atenuación del filtro antialias.
- La tara guarda el piso de ruido de cada canal en NVS y lo resta en cuadratura.

## Compilar, cargar y probar

```bash
cp include/secretos.h.ejemplo include/secretos.h   # red Wi-Fi y URL del servidor
pio run                  # compila
pio run -t upload        # carga en el ESP32
pio device monitor       # consola serie a 115200 baudios
make -C test             # prueba del cálculo en el PC con señales sintéticas
make -C test pantallas   # dibuja las pantallas de la LCD en el PC (después de pio pkg install)
```

La prueba en el PC genera señales con la misma cadena del *hardware* (pinza, resistencia de carga,
VBIAS, ADC de 12 bits con ruido y retardo de multiplexado) y compara V, I, P, frecuencia y THD con los
valores exactos.

## Pantalla

Las pantallas están en `lib/interfaz/` y solo dibujan sobre un `Adafruit_GFX`. En el ESP32 se dibujan
en cinco franjas de 320 × 34 píxeles (21,8 kB) que se envían una tras otra por SPI a 40 MHz, sin
parpadeo y sin reservar los 109 kB de un lienzo completo. En el PC, `test/pantallas.cpp` compila el
mismo código con un sustituto mínimo de Arduino (`test/arduino/`), comprueba que el dibujo por franjas
da la misma imagen que el lienzo completo y escribe `../img/ui-lcd-*.png`.

Conexión de J6 (en el orden de los pines del DevKitC): VCC → 3V3, GND, DIN → GPIO23, CS → GPIO22,
DC → GPIO21, BL → GPIO19, CLK → GPIO18, RST → GPIO4.

## Calibración

Las constantes nominales están en `include/config.h` (`K_V`, `K_I1`, `K_I2`, `FASE_CT1_GRADOS`,
`FASE_CT2_GRADOS`). Se ajustan en el banco de medición con una carga resistiva conocida (FP ≈ 1),
comparando contra una pinza amperimétrica o el PZEM-004T.
