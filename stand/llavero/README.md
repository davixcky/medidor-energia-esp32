# Llavero de la pinza

Llaveros de dos colores. Once chistes del proyecto con forma de pinza **SCT-013** (la argolla pasa por
el hueco de la pinza, como el conductor de fase) y un llavero QR para regalar en el stand.

| Archivo | Chiste |
|---|---|
| `llavero-fase` | **SOLO ABRAZO LA FASE** · fase + neutro = 0,0 A *(si la pinza abraza el cable completo de un equipo, fase y neutro se cancelan y mide cero)* |
| `llavero-hardexplosion` | **HARDEXPLOSION: PENDIENTE** *(la tabla de la prueba de resistencia, toda en "Pendiente")* |
| `llavero-revision` | **REVISIÓN E.9 · ESTA SÍ ES** la final (dijimos igual en la E.5) |
| `llavero-factura` | **MI FACTURA: 30 DÍAS** · yo: cada segundo |
| `llavero-ads1015` | **3.300 < 24.000 · ADIÓS ADS1015** *(el ADC externo que no alcanzaba)* |
| `llavero-puentes` | **10 PUENTES · CERO VÍAS** · PCB de una cara, hecha con tóner |
| `llavero-arranque` | **MI FIRMWARE NO ARRANCABA** · esperaba en el núcleo equivocado |
| `llavero-francia` | **MI IA APRENDIÓ EN FRANCIA** · una casa en Sceaux, datos de la UCI |
| `llavero-muestras` | **8.000 MUESTRAS POR SEGUNDO** · y aún no sé cuánto gasta la nevera |
| `llavero-mcp6004` | **¿MCP6004? NO HAY AQUÍ** · en Barranquilla no se consigue |
| `llavero-equipo` | **DAVID, JOSE Y LEO** · Sistemas Embebidos 1 · CUC 2026-2 |

## Llavero QR (`llavero-qr`)

42 × 63,5 × 3,6 mm. Abre `https://davixcky.github.io/medidor-energia-esp32/` (la misma página del
stand). Aquí los colores van al revés: la parte `base` (`llavero-qr-claro.stl`) debe ser **blanca o
clara** y `color` (`llavero-qr-oscuro.stl`) **negra**, porque los lectores de QR necesitan módulos
oscuros sobre fondo claro. Cada módulo mide 1,1 mm. La vista previa se probó con un lector de QR;
probar la primera pieza impresa con el celular antes de imprimir varias.

![Llavero QR](vista-qr.png)

![Vistas](vista-fase.png)

## Imprimir

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

## Cambiar el chiste

Editar `CHISTES` en `generar_llavero.py` y ejecutar:

```sh
pip install trimesh shapely mapbox_earcut manifold3d fonttools pillow
python3 stand/llavero/generar_llavero.py
```
