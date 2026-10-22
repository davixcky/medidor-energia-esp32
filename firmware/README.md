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

Las constantes de partida están en `include/config.h` (`K_V`, `K_I1`, `K_I2`, `FASE_V_GRADOS`,
`FASE_CT1_GRADOS`, `FASE_CT2_GRADOS`). Los valores medidos en el banco se guardan en la memoria no
volátil del ESP32 desde la consola serie (115200 baudios), sin recompilar:

```
cal                 muestra los valores actuales y el retardo en muestras de cada canal
cal kv 482.5        V de red por voltio en el pin (contra un multímetro)
cal ki1 91.2        A por voltio de CH1 (contra una pinza amperimétrica o el PZEM-004T)
cal ki2 42.4        A por voltio de CH2
cal fv 4.5          fase del ZMPT101B en grados (positivo = la tensión adelanta)
cal f1 0.3          fase de la pinza de CH1 (positivo = la corriente adelanta)
cal f2 0.3          fase de la pinza de CH2
cal borrar          vuelve a los valores de config.h
```

Las ganancias se ajustan con una carga resistiva conocida (FP ≈ 1). La fase no se ve con carga
resistiva: se ajusta con una carga inductiva (ventilador o motor) comparando la potencia activa con el
PZEM-004T. El *firmware* acepta un retardo total de −3 a +4 muestras (−8° a +11° a 60 Hz); si un ajuste
lo saca de ese rango, lo avisa por la consola y lo recorta.

## Muestreo

Un temporizador de hardware interrumpe cada 125 µs y despierta la tarea de adquisición (núcleo 1,
prioridad 20), que lee V, I1 e I2 y vuelve a bloquearse. Así el núcleo 1 queda libre entre muestras.
Los eventos de Wi-Fi corren en el núcleo 0 (`-DARDUINO_EVENT_RUNNING_CORE=0` en `platformio.ini`).
Si la tensión no cruza por cero durante 0,5 s, las ventanas se cierran por cantidad de muestras y se
sigue midiendo la corriente.
