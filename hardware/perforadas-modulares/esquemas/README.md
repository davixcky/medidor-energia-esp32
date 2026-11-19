# Esquemas por tarjeta — Medidor de energía E.6

Cada PDF corresponde a una tarjeta perforada que se puede construir y probar
sin las demás. El documento combinado está un nivel arriba en
`esquemas-tarjetas-compactas.pdf`.

| Tarjeta | PDF | Prueba aislada mínima |
|---|---|---|
| T1 | `T1-alimentación-protegida.pdf` | +5 V protegido y polaridad en las tres salidas |
| T2 | `T2-corriente-ch1-ch2-y-vbias.pdf` | VBIAS 1,32 V; burden presente; cada ADC centrado |
| T3 | `T3-tensión-de-muy-baja-tensión.pdf` | Inyección aislada; V_ADC entre 0,15 y 2,45 V |
| T4 | `T4-esp32s-v1.1-usb-c-y-control.pdf` | Arranque, LCD, botones e indicadores sin conectar ADC |
| T5 | `T5-encoder,-neopixel-y-piezo.pdf` | Encoder, piezo y un solo NeoPixel con brillo limitado |

Los nombres y números de pin de los conectores son parte del diseño. No se debe
invertir un arnés porque físicamente “parece encajar”. T2 y T3 deben mantenerse
lejos de la antena Wi-Fi, el piezo, el LCD y los NeoPixels.

`netlist-por-tarjeta.json` es generado junto con los PDFs y comprueba los
contratos de conectores. J4, F1 y el primario de 120 V del ZMPT101B pertenecen a
la guarda Z1: no forman una sexta tarjeta perforada.
