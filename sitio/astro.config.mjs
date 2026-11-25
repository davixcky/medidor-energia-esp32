// @ts-check
import { defineConfig } from 'astro/config';

// El sitio se publica en GitHub Pages bajo el nombre del repositorio.
// Los QR impresos (llaveros y stand/img/qr.svg) apuntan exactamente a esta URL.
export default defineConfig({
  site: 'https://davixcky.github.io',
  base: '/medidor-energia-esp32',
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
