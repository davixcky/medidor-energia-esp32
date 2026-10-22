import { defineConfig } from 'vite'

import { tanstackStart } from '@tanstack/react-start/plugin/vite'

import viteReact from '@vitejs/plugin-react'
import { nitro } from 'nitro/vite'

const config = defineConfig({
  resolve: { tsconfigPaths: true },
  plugins: [
    // PGlite (modo DEMO) carga su .wasm y .data junto al paquete: se copia entero a .output.
    nitro({ traceDeps: ['@electric-sql/pglite*', '@electric-sql/pglite-socket'] }),
    tanstackStart(),
    viteReact(),
  ],
})

export default config
