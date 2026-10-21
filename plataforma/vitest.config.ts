import { defineConfig } from 'vitest/config'

// Las pruebas del servicio comparten una base de datos: se ejecutan en un solo proceso.
export default defineConfig({ test: { include: ['tests/**/*.test.ts'], environment: 'node', fileParallelism: false, testTimeout: 30000 } })
