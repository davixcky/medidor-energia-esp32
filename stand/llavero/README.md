# Llavero de la pinza

Llaveros de dos colores. Once mensajes que explican el medidor con forma de pinza **SCT-013** (la
argolla pasa por el hueco de la pinza, como el conductor de fase) y un llavero QR para regalar en el
stand.

| Archivo | Mensaje del proyecto |
|---|---|
| `llavero-proyecto` | **MEDIDOR DE ENERGÍA ESP32** · no invasivo · 2 canales · Wi-Fi |
| `llavero-sct013` | **PINZA SCT-013 · SIN ABRIR CIRCUITO** · corriente no invasiva |
| `llavero-tiempo-real` | **CONSUMO EN TIEMPO REAL** · potencia · energía · costo |
| `llavero-muestreo` | **8.000 MUESTRAS POR SEGUNDO** · por canal · ADC1 del ESP32 |
| `llavero-canales` | **DOS CANALES · CH1 + CH2** · tablero total + subcircuito |
| `llavero-variables` | **V · I · P · Q · S Y FACTOR P.** · medición eléctrica completa |
| `llavero-wifi` | **ESP32 + Wi-Fi · DATOS CADA 1 s** · tablero web en tiempo real |
| `llavero-lstm` | **PRONÓSTICO LSTM · PRÓXIMAS 48 h** · energía con inteligencia artificial |
| `llavero-alertas` | **ALERTAS DE CONSUMO ALTO** · umbral P95 · detección 5 min |
| `llavero-seguridad` | **120 V AISLADOS · BAJA TENSIÓN** · ZMPT101B + barrera física |
| `llavero-equipo` | **CUC 2026-2 · SIST. EMBEBIDOS** · David · Jose · Leo |

## Llavero QR (`llavero-qr`)

42 × 63,5 × 3,6 mm. Abre `https://davixcky.github.io/medidor-energia-esp32/` (la misma página del
stand). Aquí los colores van al revés: la parte `base` (`llavero-qr-claro.stl`) debe ser **blanca o
clara** y `color` (`llavero-qr-oscuro.stl`) **negra**, porque los lectores de QR necesitan módulos
oscuros sobre fondo claro. Cada módulo mide 1,1 mm. La vista previa se probó con un lector de QR;
probar la primera pieza impresa con el celular antes de imprimir varias.

![Llavero QR](vista-qr.png)

![Vistas](vista-fase.png)

## Imprimir

### Placas listas

La carpeta `placas/` contiene cuatro archivos 3MF ya acomodados para una cama de **256 × 256 mm**.
Cada llavero sigue siendo un objeto de dos partes, por lo que se puede mover o borrar sin separar sus
colores.

| Placa | Contenido | Filamento 1 | Filamento 2 |
|---|---|---|---|
| `placa-01-medidor.3mf` | proyecto, SCT-013, tiempo real, muestreo | oscuro | verde |
| `placa-02-funciones.3mf` | canales, variables, Wi-Fi, LSTM | oscuro | verde |
| `placa-03-identidad.3mf` | alertas, seguridad, equipo | oscuro | verde |
| `placa-04-qr-x6.3mf` | 6 llaveros QR | blanco o claro | negro |

Abrir una placa en Bambu Studio u OrcaSlicer, confirmar los dos filamentos y laminar con capa de
0,2 mm. Las placas contienen geometría y posiciones, no un perfil de impresora: así se pueden usar
con cualquier Bambu de cama completa o con otra impresora de al menos 220 × 220 mm. Si la cama es
más pequeña, usar los 3MF individuales de `3mf/`.

Imprimir primero una sola copia de `llavero-qr.3mf` y comprobarla con varios celulares antes de
lanzar `placa-04-qr-x6.3mf`.

### Archivos individuales

- Medidas: 79 × 26 × 3,6 mm. Hueco de 12 mm para la argolla.
- Abrir `3mf/llavero-<chiste>.3mf` en Bambu Studio u OrcaSlicer: es **un objeto con dos partes**.
  La parte `base` va con el filamento 1 (gris oscuro o negro) y `color` con el filamento 2 (verde).
  Si el programa no las asigna solo, cambiar el filamento de la parte `color` en la lista de objetos.
- Sin 3MF: importar juntos `stl/llavero-<chiste>-base.stl` y `-color.stl` y responder **Sí** a
  "¿cargar como un solo objeto con varias partes?".
- Capa de 0,2 mm, boquilla de 0,4 mm, cara plana sobre la cama (el color queda arriba, al ras).
  El verde ocupa solo las 3 últimas capas, así que el cambio de filamento es corto.
- El texto pequeño mide 2,9 mm de alto; con el generador de perímetros Arachne (por defecto) sale bien.
- Sin AMS: pausar en la capa de 3,0 mm, cambiar a verde y continuar. Así todo lo que está a esa
  altura sale verde, que es justo el dibujo.

## Cambiar el mensaje

Editar `TEXTOS` en `generar_llavero.py` y ejecutar:

```sh
pip install trimesh shapely mapbox_earcut manifold3d fonttools pillow qrcode
python3 stand/llavero/generar_llavero.py
```
