# Seguridad y aceptación

## Antes de soldar

- Confirmar con multímetro el pinout de ESP32, transistor, encoder, jacks SCT,
  módulo ZMPT y pantalla reales. El encapsulado no garantiza el orden de pines.
- Etiquetar ambos extremos de cada arnés con el nombre de cable y pin 1.
- Reservar una barra de GND y una de alimentación por tarjeta. Ninguna unión de
  GND debe depender de tornillos del gabinete.
- Mantener al menos una fila perforada libre entre analógico y digital. No pasar
  cables de NeoPixel, LCD o piezo sobre T2/T3.

## 74HCT245 en T5

Uso de un solo canal, con alimentación de 5 V:

| Pin | Conexión |
|---:|---|
| 1 DIR | +5V |
| 2 A0 | GPIO13 desde T4 |
| 18 B0 | R16 de 330 ohm y luego DIN del primer WS2812B |
| 19 /OE | GND |
| 20 VCC | +5V |
| 10 GND | GND |
| 3-9 A1-A7 | GND, nunca flotantes |
| 11-17 B1-B7 | sin conectar |

C14 de 100 nF debe quedar directamente entre pines 20 y 10. R17 de 10 kOhm
mantiene GPIO13 a GND durante el arranque. C16 de 680 uF queda entre +5 V y GND
junto al conector de los pixels.

## Pruebas sin red

1. Sin integrados ni ESP32: resistencia entre +5 V y GND mayor de 1 kOhm después
   de cargar los electrolíticos; comprobar que no hay inversión de D1.
2. T1 con fuente limitada a 100 mA: medir entre 5,0 y 5,25 V en cada salida.
3. T2 alimentada desde 3,3 V: VBIAS = 1,32 V ±1 %. Medir R1=22 Ohm y R2=47
   Ohm directamente en los jacks con las pinzas desconectadas.
4. T3: inyectar una senoide pequeña alrededor de 2,5 V por ZMPT_OUT y comprobar
   que V_ADC permanece entre 0,15 y 2,45 V.
5. T4: instalar ESP32; probar LCD, SW1, SW2 y LEDs. GPIO32/33 deben quedar para
   el encoder, no para una expansión ADC.
6. T5: confirmar +5 V en pin 20 y GND en pin 10 del HCT245. Verificar salida B0
   con un pixel y brillo limitado antes de instalar cuatro. Confirmar patillaje
   E/B/C de Q1 y probar el piezo con corriente limitada.
7. Integración: conectar un arnés cada vez, comprobando consumo y temperatura.

## Prueba de red

La prueba de 120 V no se realiza sobre la mesa con Z1 abierta. Requiere guarda
cerrada, fusible T500 mA en la fase, prensaestopa, alivio de tensión, continuidad
de protección y revisión por dos personas. No conectar USB ni instrumentos sin
aislamiento mientras la zona de red esté energizada.

## Criterios finales

- Ningún secundario SCT puede quedar sin burden.
- Ningún conductor de 120 V comparte tarjeta o conector con MBT.
- +5 V en carga permanece entre 5,0 y 5,25 V.
- VBIAS = 1,32 V ±1 %.
- Entradas ADC permanecen dentro de 0,15-2,45 V en operación nominal.
- La calibración final se hace contra una carga resistiva conocida y un medidor
  patrón; el firmware guarda las constantes medidas, no solo las nominales.
