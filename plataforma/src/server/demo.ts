/**
 * Modo de demostración (DEMO=1): el servidor corre sin Supabase. Levanta un Postgres en memoria
 * (PGlite) detrás de un socket local, aplica la misma migración, carga 21 días del simulador por la
 * misma función de ingesta que usa el ESP32 y sigue agregando un registro por segundo, de modo que
 * energía, umbrales, alertas y pronóstico salen del código real. Todo se pierde al reiniciar.
 */
import { AsyncLocalStorage } from 'node:async_hooks'
import { type Socket, connect } from 'node:net'
import type { Registro } from './adr001'
import { registro } from './simulador.ts'

const NODO = 'nodo01'
const FW = 'fw-v1.0.0-sim'
const DIAS = 21
const PASO = 30 // s entre registros del histórico (el simulador usa 10; con 30 cabe en 512 MB de memoria)
const RETENCION = 22 * 86400 // los registros más viejos se borran para no crecer sin límite

export const activo = () => process.env.DEMO === '1'

/** Cliente que usa la carga inicial mientras las demás conexiones esperan a que termine. */
export const cargador = new AsyncLocalStorage<unknown>()

let servidor: Promise<{ host: string; port: number }> | null = null
let listo: Promise<void> | null = null

async function arrancarBase() {
  const { PGlite } = await import('@electric-sql/pglite')
  const { PGLiteSocketServer } = await import('@electric-sql/pglite-socket')
  // El esquema va dentro del paquete del servidor (?raw), así no depende de archivos sueltos.
  const { default: esquema } = await import('../../supabase/migrations/20261021000000_medidor.sql?raw')
  // Búferes mínimos: con los valores por defecto el proceso pasa de 512 MB (plan gratuito de Render).
  const db = await PGlite.create({ postgresqlconf: ['shared_buffers=8MB', 'work_mem=1MB', 'wal_buffers=256kB', 'maintenance_work_mem=1MB'] })
  await db.exec(esquema)
  const srv = new PGLiteSocketServer({ db, host: '127.0.0.1', port: 0 })
  await srv.start()
  const [host, port] = srv.getServerConn().split(':')
  return { host, port: Number(port) }
}

/** Abre un socket ya conectado al Postgres en memoria (opción `socket` de postgres.js). */
export async function socket(esperarCarga: boolean): Promise<Socket> {
  servidor ??= arrancarBase()
  const { host, port } = await servidor
  if (esperarCarga) await iniciar()
  return new Promise((ok, mal) => {
    const s = connect(port, host, () => ok(s))
    s.once('error', mal)
  })
}

/** Carga el histórico (una sola vez) y arranca el registro en vivo. */
export function iniciar(): Promise<void> {
  listo ??= (async () => {
    const { ingerir } = await import('./servicio')
    const { clienteDemo } = await import('./db')
    const db = clienteDemo()
    const t0 = Date.now()
    const ahora = Math.floor(Date.now() / 1000)
    await cargador.run(db, async () => {
      let lote: Registro[] = []
      for (let t = ahora - DIAS * 86400; t < ahora; t += PASO) {
        lote.push(registro(t))
        if (lote.length === 1000) { await ingerir(NODO, FW, lote); lote = [] }
      }
      if (lote.length) await ingerir(NODO, FW, lote)
    })
    await db.end({ timeout: 5 })
    console.log(`[demo] ${DIAS} días simulados cargados en ${((Date.now() - t0) / 1000).toFixed(1)} s; sigue un registro por segundo`)
    setInterval(() => {
      ingerir(NODO, FW, [registro(Math.floor(Date.now() / 1000))]).catch((e) => console.error('[demo]', e))
    }, 1000).unref()
    setInterval(async () => {
      const { sql } = await import('./db')
      await sql()`DELETE FROM registros WHERE t < ${Math.floor(Date.now() / 1000) - RETENCION}`
    }, 3600_000).unref()
  })()
  return listo
}
