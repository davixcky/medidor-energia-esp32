# Sitio del proyecto (Astro)

Sitio público del medidor, publicado en GitHub Pages:
<https://davixcky.github.io/medidor-energia-esp32/>

```bash
cd sitio
pnpm install
pnpm dev        # http://localhost:4321/medidor-energia-esp32
pnpm build      # genera dist/
pnpm preview    # sirve dist/ como lo verá GitHub Pages
```

## Páginas

| Ruta | Contenido |
|---|---|
| `/` | Portada: el problema, la cadena de medición, el equipo y el tablero |
| `/hardware` | Arquitectura E.9, esquemáticos T1–T5, PCB, BOM y verificaciones |
| `/firmware` | Reparto por núcleos, el cálculo, el contrato ADR-001 y las tres placas |
| `/modelos-3d` | Gabinete E.9, once vistas, orden de impresión y banco de pruebas |
| `/plataforma` | Arquitectura, tablero, API y cómo levantarla |
| `/pronostico` | La LSTM, resultados frente a métodos simples y limitaciones |
| `/informe` | [`docs/informe.md`](../docs/informe.md) renderizado, con índice lateral |

## De dónde salen las imágenes

No hay imágenes propias: `scripts/preparar-assets.mjs` copia a `public/` lo que ya
existe en el repositorio, y **falla si falta alguna**. Se ejecuta solo, antes de
`dev` y de `build`.

| Origen | Destino |
|---|---|
| `img/` y `sitio/stand/img/` | `public/img/` |
| `3d/revision-e7/*.png` (renders E.9) | `public/render/` |
| `hardware/perforadas-modulares/schematic-previews/` | `public/esquematicos/` |

`public/` está en `.gitignore`: es caché de construcción, no fuente. Si se agrega un
render nuevo al sitio, hay que añadirlo a la lista `RENDERS` del script.

La página del informe lee `../docs/informe.md` en tiempo de construcción y traduce sus
rutas: las imágenes apuntan a `public/` (con la misma traducción de carpetas que hace el
script) y cualquier otro archivo del repositorio —PDF, KiCad, scripts— se enlaza a GitHub.

## Publicación

Lo hace [`.github/workflows/pages.yml`](../.github/workflows/pages.yml) en un solo
despliegue de Pages, que además superpone las páginas del stand:

| URL | Qué es |
|---|---|
| `/` | este sitio |
| `/kiosko.html` | presentación del iPad (URL sin cambios) |
| `/pantalla.html` | segunda pantalla HDMI (URL sin cambios) |
| `/stand/` | página anterior del QR, como respaldo |

> **La raíz no se puede mover.** Los llaveros impresos y `sitio/stand/img/qr.svg` codifican
> exactamente `https://davixcky.github.io/medidor-energia-esp32/`. Cambiar la URL obliga a
> regenerar el QR (`python3 sitio/stand/generar_qr.py <url>`) y a volver a imprimir los llaveros.

El flujo comprueba, antes de publicar, que `kiosko.html`, `pantalla.html`, `sw.js`,
`manifest.webmanifest`, `img/qr.svg` y `sitio/stand/index.html` estén en su sitio y que la raíz
sea este sitio y no la página antigua.

## Diseño

La paleta es la misma del kiosco (`sitio/stand/index.html`), para que el QR lleve a algo que se
ve como la presentación física. Tokens en [`src/styles/global.css`](src/styles/global.css);
tema oscuro único y deliberado. Las cifras de la portada y de la página del pronóstico se
leen de `pronostico/metricas.json` en tiempo de construcción, así que no se desactualizan
respecto al modelo entrenado.
