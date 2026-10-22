# Puentes de alambre (lado de componentes)

La PCB es de **una sola cara** (cobre abajo). Las conexiones que no caben en el cobre se hacen
con alambre aislado (por ejemplo, hilo de cable UTP) del lado de los componentes. Cada puente
está dibujado en la serigrafía como una línea recta con su nombre `JPn`.

- Instalar todos los puentes **antes** que los componentes: algunos pasan por debajo del ESP32.
- Cortar el alambre unos 6 mm más largo que la medida, doblar las puntas y soldar por el cobre.
- Si un puente tiene más de dos agujeros, se hace con varios tramos (todos son la misma red).

Coordenadas en mm desde la esquina superior izquierda de la placa, vista desde los componentes.

Total: **3 puentes, 3 alambres**.

| Puente | Red | Alambres | Largo aprox. | Agujeros |
|---|---|---|---|---|
| JP1 | `CH2_ADC` | 1 | 17 mm | (43.6, 47.1) junto a D4.2<br>(60.9, 47.1) junto a R11.1 |
| JP2 | `CH1_ADC` | 1 | 6 mm | (65.2, 38.6) junto a R11.2<br>(71.3, 38.6) junto a R11.2 |
| JP3 | `V_ADC` | 1 | 24 mm | (78.6, 16.5) junto a J7.4<br>(81.8, 40.8) junto a U1.5 |
