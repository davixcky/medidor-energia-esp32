# Stand CUC — presentación en iPad

Dos páginas estáticas, sin dependencias externas:

| Archivo | Para qué |
|---|---|
| `kiosko.html` | Presentación animada para el iPad en horizontal. 10 escenas que avanzan solas (≈ 3 min por vuelta) con un QR fijo en la esquina. |
| `index.html` | Página que abre el QR en el celular del visitante: explicación completa, renders, video, tablas y enlace al repositorio. |

## Escenas del kiosco

1. Portada con valores animados y ondas de V/I.
2. El problema: la factura llega 30 días tarde (calendario animado).
3. Medición no invasiva: pinza SCT-013 con campo magnético animado.
4. Cadena de medición: sensores → acondicionamiento → ADC → cálculo → Wi-Fi → plataforma.
5. Cálculo: muestreo de v(t)·i(t) y potencia activa en vivo.
6. Video del producto (sin audio).
7. Por dentro: render abierto con puntos señalados.
8. Pronóstico LSTM: curva y error frente a métodos ingenuos.
9. Comparación con medidores comerciales.
10. Cierre con QR grande y equipo.

Controles: tocar a la derecha/izquierda avanza/retrocede; dos dedos pausa; en un teclado,
flechas y barra espaciadora. Después de tocar, sigue avanzando sola.

## Publicar (una vez)

1. En GitHub: **Settings → Pages → Source: GitHub Actions**.
2. Hacer *merge* a `main`. El flujo `.github/workflows/stand-pages.yml` publica `stand/` en
   `https://davixcky.github.io/medidor-energia-esp32/`.
3. El repositorio debe ser público (o tener un plan que permita Pages privadas).

Si se usa otra URL, regenerar el QR: `pip install qrcode && python3 stand/generar_qr.py https://otra-url/`.

## Preparar el iPad

1. Abrir `https://davixcky.github.io/medidor-energia-esp32/kiosko.html` en Safari.
2. **Compartir → Agregar a inicio**. Se abre a pantalla completa, sin barra de Safari.
3. Abrirla una vez con Wi-Fi y dejar pasar una vuelta completa: queda guardada y funciona sin internet.
4. **Ajustes → Pantalla y brillo → Bloqueo automático: Nunca**, brillo alto, modo No molestar.
5. **Ajustes → Accesibilidad → Acceso guiado** activado. En la app, triple clic al botón lateral
   para bloquearla y que nadie salga de la presentación.
6. Mantener el iPad conectado al cargador durante la exposición.

Prueba local: `cd stand && python3 -m http.server 8000` y abrir `http://<ip-del-computador>:8000/kiosko.html`
desde el iPad en la misma red. Agregar `?auto` a la URL omite la pantalla de inicio.

## Fuentes

Los textos y cifras salen del documento principal (`README.md`) y de `pronostico/metricas.json`.
Las imágenes son copias reducidas de `freecad/revision-e7/` e `img/`; el video es
`video/revision-e7/medidor-E7-producto.mp4` re-codificado a 720p sin audio. Los valores de la portada
y la curva del pronóstico del kiosco son ilustrativos y así se indica en pantalla.
