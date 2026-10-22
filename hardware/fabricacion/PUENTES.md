# Puentes de alambre (lado de componentes)

La PCB es de **una sola cara** (cobre abajo). Las conexiones que no caben en el cobre se hacen
con alambre aislado (por ejemplo, hilo de cable UTP) del lado de los componentes. Cada puente
está dibujado en la serigrafía como una línea recta con su nombre `JPn`.

- Instalar todos los puentes **antes** que los componentes: algunos pasan por debajo del ESP32.
- Cortar el alambre unos 6 mm más largo que la medida, doblar las puntas y soldar por el cobre.
- Si un puente tiene más de dos agujeros, se hace con varios tramos (todos son la misma red).

Coordenadas en mm desde la esquina superior izquierda de la placa, vista desde los componentes.

Total: **10 puentes, 13 alambres**.

| Puente | Red | Alambres | Largo aprox. | Agujeros |
|---|---|---|---|---|
| JP1 | `Net-(J1-Pin_1)` | 1 | 8 mm | (9.5, 73.3) junto a J1.2<br>(10.4, 80.9) junto a J1.1 |
| JP2 | `+5V` | 1 | 26 mm | (15.3, 42.6) junto a R6.1<br>(16.0, 68.9) junto a R4.1 |
| JP3 | `CH1_ADC` | 1 | 28 mm | (47.1, 40.2) junto a D4.2<br>(74.7, 35.6) junto a U1.3 |
| JP4 | `CH2_ADC` | 1 | 27 mm | (52.0, 48.9) junto a TP5.1<br>(76.8, 37.8) junto a U1.4 |
| JP5 | `+3V3` | 4 | 40 mm | (61.5, 9.6) junto a D7.1<br>(64.8, 18.7) junto a D7.1<br>(70.5, 24.8) junto a J7.1<br>(72.1, 15.7) junto a TP2.1<br>(85.6, 16.4) junto a J7.4 |
| JP6 | `+5V` | 1 | 16 mm | (62.7, 78.5) junto a R14.2<br>(78.5, 76.7) junto a SW2.2 |
| JP7 | `Net-(D8-A)` | 1 | 11 mm | (63.1, 58.5) junto a R13.1<br>(66.2, 69.1) junto a D8.2 |
| JP8 | `SW1` | 1 | 8 mm | (64.6, 62.4) junto a C10.2<br>(69.8, 68.0) junto a C11.1 |
| JP9 | `RES_IO34` | 1 | 21 mm | (69.0, 22.0) junto a J7.1<br>(81.4, 39.4) junto a U1.5 |
| JP10 | `V_ADC` | 1 | 21 mm | (83.9, 31.3) junto a U1.2<br>(85.3, 10.7) junto a TP2.1 |
