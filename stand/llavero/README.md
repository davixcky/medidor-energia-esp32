# Llavero de la pinza

Llaveros compactos de dos colores, sin texto, con forma de pinza **SCT-013**. La argolla pasa por el
hueco de la pinza, como el conductor de fase. Los pictogramas son grandes y simples para que se lean
bien impresos con boquilla de 0,4 mm.

| Archivo | Pictograma |
|---|---|
| `llavero-energia` | Rayo: medición de energía |
| `llavero-wifi` | Señal inalámbrica: telemetría ESP32 |
| `llavero-onda` | Onda senoidal: tensión y corriente de CA |
| `llavero-canales` | Dos barras: canales CH1 y CH2 |
| `llavero-pronostico` | Gráfica ascendente: pronóstico de consumo |
| `llavero-seguridad` | Escudo: aislamiento y protección |

## Llavero QR (`llavero-qr`)

40 × 47,5 × 3,2 mm, sin texto. Abre `https://davixcky.github.io/medidor-energia-esp32/` (la misma página del
stand). Aquí los colores van al revés: la parte `base` (`llavero-qr-claro.stl`) debe ser **blanca o
clara** y `color` (`llavero-qr-oscuro.stl`) **negra**, porque los lectores de QR necesitan módulos
oscuros sobre fondo claro. Cada módulo mide 1,1 mm. La vista previa se probó con un lector de QR;
probar la primera pieza impresa con el celular antes de imprimir varias.

![Llavero QR](vista-qr.png)

![Vistas](vista-energia.png)

## Imprimir

### Placas listas

La carpeta `placas/` contiene dos archivos 3MF ya acomodados para una cama de **220 × 220 mm**.
Cada llavero sigue siendo un objeto de dos partes, por lo que se puede mover o borrar sin separar sus
colores.

| Placa | Contenido | Filamento 1 | Filamento 2 |
|---|---|---|---|
| `placa-01-iconos.3mf` | los 6 pictogramas | oscuro | verde |
| `placa-04-qr-x6.3mf` | 6 llaveros QR | blanco o claro | negro |

Abrir una placa en Bambu Studio u OrcaSlicer, confirmar los dos filamentos y laminar con capa de
0,2 mm. Las placas contienen geometría y posiciones, no un perfil de impresora: así se pueden usar
con cualquier Bambu de cama completa o con otra impresora de al menos 220 × 220 mm. Si la cama es
más pequeña, usar los 3MF individuales de `3mf/`.

Imprimir primero una sola copia de `llavero-qr.3mf` y comprobarla con varios celulares antes de
lanzar `placa-04-qr-x6.3mf`.

### Archivos individuales

- Medidas: 54 × 20 × 3,2 mm. Hueco de 9 mm para la argolla.
- Abrir `3mf/llavero-<icono>.3mf` en Bambu Studio u OrcaSlicer: es **un objeto con dos partes**.
  La parte `base` va con el filamento 1 (gris oscuro o negro) y `color` con el filamento 2 (verde).
  Si el programa no las asigna solo, cambiar el filamento de la parte `color` en la lista de objetos.
- Sin 3MF: importar juntos `stl/llavero-<icono>-base.stl` y `-color.stl` y responder **Sí** a
  "¿cargar como un solo objeto con varias partes?".
- Capa de 0,2 mm, boquilla de 0,4 mm, cara plana sobre la cama (el color queda arriba, al ras).
  El verde ocupa solo las 3 últimas capas, así que el cambio de filamento es corto.
- Sin AMS: pausar en la capa de 2,6 mm, cambiar a verde y continuar. Así todo lo que está a esa
  altura sale verde, que es justo el dibujo.

## Cambiar un pictograma

Editar `pictograma()` o `ICONOS` en `generar_llavero.py` y ejecutar:

```sh
pip install trimesh shapely manifold3d pillow qrcode
python3 stand/llavero/generar_llavero.py
```
