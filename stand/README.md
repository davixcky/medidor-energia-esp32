# Stand CUC — presentación en iPad

Dos páginas estáticas, sin dependencias externas:

| Archivo | Para qué |
|---|---|
| `kiosko.html` | Presentación animada para el iPad en horizontal. 12 escenas que avanzan solas (≈ 4 min por vuelta) con un QR fijo en la esquina. |
| `pantalla.html` | Segunda pantalla HDMI (pantalla de gabinete de PC). Alterna un letrero (nombre, frase, QR) y un medidor en vivo de demostración. Se ajusta a barra, pantalla normal o vertical. |
| `index.html` | Página que abre el QR en el celular del visitante: explicación completa, renders, video, la LSTM explicada en lenguaje sencillo, preguntas frecuentes y enlace al repositorio. |

## Escenas del kiosco

1. Portada con valores animados y ondas de V/I.
2. El problema: la factura llega 30 días tarde (calendario animado).
3. Medición no invasiva: pinza SCT-013 con campo magnético animado.
4. Cadena de medición: sensores → acondicionamiento → ADC → cálculo → Wi-Fi → plataforma.
5. Cálculo: muestreo de v(t)·i(t) y potencia activa en vivo.
6. Video del producto (sin audio).
7. Por dentro: render abierto con puntos señalados.
8. ¿Cómo piensa la IA?: la LSTM lee 24 horas y sus tres puertas (olvido, entrada, salida) animadas.
9. Pronóstico LSTM: curva y error frente a métodos simples (−17 % frente al mejor, a 24 h).
10. Comparación con medidores comerciales.
11. Preguntas frecuentes: tablero y equipos, cables, Wi-Fi, precisión.
12. Cierre con QR grande y equipo.

Controles: tocar a la derecha/izquierda avanza/retrocede; dos dedos pausa; en un teclado,
flechas y barra espaciadora. Después de tocar, sigue avanzando sola.

## Publicar (una vez)

1. En GitHub: **Settings → Pages → Source: GitHub Actions**.
2. Hacer *merge* a `main`. El flujo [`.github/workflows/pages.yml`](../.github/workflows/pages.yml)
   publica, en un solo despliegue, el sitio del proyecto y estas páginas:

   | URL | Qué queda ahí |
   |---|---|
   | `/` | El [sitio del proyecto en Astro](../sitio/README.md) — **es a donde apuntan los QR** |
   | `/kiosko.html` | La presentación del iPad (URL sin cambios) |
   | `/pantalla.html` | La segunda pantalla HDMI (URL sin cambios) |
   | `/img/*` | Las imágenes de esta carpeta (sin cambios) |
   | `/stand/` | `index.html` de esta carpeta, conservada como respaldo |

3. El repositorio debe ser público (o tener un plan que permita Pages privadas).

> **La raíz la ocupa el sitio del proyecto, no `index.html` de esta carpeta.** El QR impreso
> sigue funcionando porque la URL no cambió: lleva a una página mejor. La versión anterior
> queda disponible en `/stand/`.

Si se usa otra URL hay que regenerar el QR **y volver a imprimir los llaveros**:
`pip install qrcode && python3 stand/generar_qr.py https://otra-url/`.

## Preparar el iPad

1. Abrir `https://davixcky.github.io/medidor-energia-esp32/kiosko.html` en Safari.
2. **Compartir → Agregar a inicio**. Se abre a pantalla completa, sin barra de Safari.
3. Abrirla una vez con Wi-Fi (y de nuevo tras cada actualización) y dejar pasar una vuelta completa: queda guardada y funciona sin internet.
4. **Ajustes → Pantalla y brillo → Bloqueo automático: Nunca**, brillo alto, modo No molestar.
5. **Ajustes → Accesibilidad → Acceso guiado** activado. En la app, triple clic al botón lateral
   para bloquearla y que nadie salga de la presentación.
6. Mantener el iPad conectado al cargador durante la exposición.

Prueba local: `cd stand && python3 -m http.server 8000` y abrir `http://<ip-del-computador>:8000/kiosko.html`
desde el iPad en la misma red. Agregar `?auto` a la URL omite la pantalla de inicio.

## Segunda pantalla HDMI (`pantalla.html`)

Funciona sin internet y se adapta sola a la forma de la pantalla: barra (p. ej. 1920×480),
normal (800×480, 1024×600, 1920×1080) o vertical. El QR queda visible todo el tiempo.

Opciones en la URL:

| Parámetro | Efecto |
|---|---|
| `?girar=90` (o 180, 270) | Gira el contenido. Muchas barras de 8,8" llegan como 480×1920 vertical. |
| `?modo=letrero` / `?modo=medidor` | Muestra solo una vista. Por defecto alterna. |
| `?seg=12` | Segundos por vista. |

**Con Raspberry Pi** (recomendada la Zero 2 W; la Zero W original es demasiado lenta para Chromium):

1. Grabar **Raspberry Pi OS con escritorio** con Raspberry Pi Imager (configurar Wi-Fi y SSH ahí).
2. Conectar la pantalla por mini-HDMI y encender.
3. En la Pi:
   ```sh
   git clone https://github.com/davixcky/medidor-energia-esp32.git
   cd medidor-energia-esp32 && bash stand/pi/instalar.sh
   sudo reboot
   ```
4. Si la imagen sale de lado, repetir con `GIRAR=90 bash stand/pi/instalar.sh` (o 270).

Al encender abre la página a pantalla completa, sin cursor, sin apagar la pantalla y la reabre si
se cierra. No necesita internet en el stand.

Si la pantalla no muestra imagen o la resolución es incorrecta, agregar al final de la línea de
`/boot/firmware/cmdline.txt` la resolución de la pantalla, por ejemplo `video=HDMI-A-1:1920x480@60`
(o `480x1920@60`), y reiniciar.

**Con el Mac:** conectar la pantalla, en **Ajustes → Pantallas** usarla como pantalla extendida
(no duplicada), hacer doble clic en `stand/mac/abrir-pantalla.command`, arrastrar la ventana a la
pantalla pequeña y pulsar **Control + Command + F**.

## Fuentes

Los textos y cifras salen del [informe](../docs/informe.md) y de `pronostico/metricas.json`.
Las imágenes son copias reducidas de `freecad/revision-e7/` e `img/`; el video es
`video/revision-e7/medidor-E7-producto.mp4` re-codificado a 720p sin audio. Los valores de la portada
y la curva del pronóstico del kiosco son ilustrativos y así se indica en pantalla.
