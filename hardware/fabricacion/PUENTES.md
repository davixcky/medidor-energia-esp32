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
| JP1 | `+5V` | 1 | 14 mm | (9.2, 59.4) junto a R3.1<br>(9.2, 73.2) junto a J1.2 |
| JP2 | `CH2_ADC` | 1 | 4 mm | (55.7, 44.7) junto a R11.1<br>(60.0, 44.7) junto a R11.1 |
| JP3 | `V_ADC` | 1 | 21 mm | (83.0, 18.8) junto a J7.4<br>(83.0, 39.6) junto a U1.5 |
