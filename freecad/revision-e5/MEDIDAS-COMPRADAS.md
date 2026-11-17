# Medidas usadas por el modelo E.5

El gabinete se regeneró sin suponer recortes: T1, T2, T3 y T5 usan placas
compradas de 90 × 70 × 1,6 mm, y T4 usa la placa de 120 × 80 × 1,6 mm. La
quinta placa de 90 × 70 queda como repuesto. Esto explica el aumento del tamaño
del gabinete frente a la primera vista E.5.

El piezo comprado se corrigió a cuerpo circular de **44 mm de diámetro por
14 mm de alto**. El ZMPT101B se reserva a 51,7 × 21,6 mm y permanece en el
compartimento de red, detrás del tabique. La pantalla se reserva a
51,2 × 27,3 mm.

`medidas-componentes.json` registra la fuente y la calidad de cada cota. Antes de
imprimir definitivamente hay que medir las piezas marcadas `por_medir`, en
especial el ESP32 definitivo, los dos EC11, la altura del ZMPT101B y el ancho
real de la cinta IP65. Esas cotas no están publicadas de forma suficiente para
crear agujeros de ajuste exacto.
