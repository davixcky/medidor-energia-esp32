| # | Caso | Resultado de la simulación | Criterio | Estado |
|---:|---|---|---|---|
| 1 | CH1, 60 A eficaces (nominal) | 0,387 V a 2,250 V | dentro de 0,15–2,45 V | Cumple |
| 2 | CH1, 72,6 A eficaces (límite) | 0,192 V a 2,446 V | máximo ≤ 2,45 V + 0,01 | Cumple |
| 3 | CH2, 30 A eficaces (nominal) | 0,324 V a 2,314 V | dentro de 0,15–2,45 V | Cumple |
| 4 | CH2, 34 A eficaces (límite) | 0,191 V a 2,447 V | máximo ≤ 2,45 V + 0,01 | Cumple |
| 5 | CH1, sobrecorriente de 150 A | -0,273 V a 3,544 V | entre −0,3 V y 3,6 V (máximo absoluto) | Cumple |
| 6 | CH1, sobrecorriente de 200 A | -0,295 V a 3,586 V | entre −0,3 V y 3,6 V (máximo absoluto) | Cumple |
| 7 | CH2, sobrecorriente de 80 A | -0,284 V a 3,569 V | entre −0,3 V y 3,6 V (máximo absoluto) | Cumple |
| 8 | CH2, sobrecorriente de 100 A | -0,299 V a 3,592 V | entre −0,3 V y 3,6 V (máximo absoluto) | Cumple |
| 9 | CH2, 20 A con 60 % de tercer armónico | 0,551 V a 2,086 V | dentro de 0,15–2,45 V | Cumple |
| 10 | VBIAS en reposo | 1,3194 V | 1,32 V ± 1 % | Cumple |
| 11 | CH1, ganancia a 60 Hz | 21,962 V/A en el secundario (10,98 mV por A de primario) | 22 Ω (sin pérdida en el filtro) | Cumple |
| 12 | CH1, atenuación en el armónico 50 (3 kHz) | -9,84 dB | atenuación conocida: el *firmware* la compensa | Informativo |
| 13 | CH1, atenuación en la frecuencia de Nyquist (4 kHz) | -12,13 dB | filtro de primer orden: lo que pase de 4 kHz se pliega atenuado | Informativo |
| 14 | Frecuencia de corte, CH1 y tensión | 1025 Hz y 990 Hz | ≈ 1 kHz (τ ≈ 156–161 µs) | Cumple |
| 15 | Desfase a 60 Hz entre corriente y tensión | CH1 -3,37°, CH2 -3,39°, V -3,47° → diferencia máx. 0,10° | ≤ 0,2° (error en P ≤ 0,3 % con FP = 0,5) | Cumple |
| 16 | Tensión, salida del módulo 2,5 V ± 1 V | 0,813 V a 1,894 V | dentro de 0,15–2,45 V | Cumple |
| 17 | Tensión, salida del módulo 2,5 V ± 1,4 V | 0,597 V a 2,110 V | dentro de 0,15–2,45 V | Cumple |
| 18 | Entrada del regulador con adaptador de 4,75 V y 500 mA | 4,306 V | ≥ 4,4 V (3,3 V regulados) · ≥ 4,1 V (ESP32 aún funciona a 3,0 V) | **No cumple** |
| 19 | Entrada del regulador con adaptador de 5 V y 500 mA | 4,556 V | ≥ 4,4 V (3,3 V regulados) · ≥ 4,1 V (ESP32 aún funciona a 3,0 V) | Cumple |
| 20 | Entrada del regulador con adaptador de 5,25 V y 500 mA | 4,806 V | ≥ 4,4 V (3,3 V regulados) · ≥ 4,1 V (ESP32 aún funciona a 3,0 V) | Cumple |
