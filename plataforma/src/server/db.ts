/**
 * Conexión a la base de datos en Supabase (Postgres) con postgres.js.
 *
 * DATABASE_URL es la cadena de conexión del proyecto de Supabase (Project Settings → Database).
 * Con el pooler en modo transacción (puerto 6543) las sentencias preparadas no se pueden reutilizar,
 * por eso van desactivadas. Para las pruebas sirve cualquier Postgres local. Con DEMO=1 la conexión
 * va a un Postgres en memoria (demo.ts) y DATABASE_URL no se usa.
 */
import { readFileSync } from 'node:fs'
import postgres from 'postgres'
import * as demo from './demo.ts'

export type Sql = postgres.Sql
/** Conexión dentro de una transacción (sql().begin). */
export type Tx = postgres.TransactionSql

let cliente: Sql | null = null

// bigint (t, hora, conteos) como número de JS: los valores caben de sobra en 2^53
const tipos = { bigint: { to: 20, from: [20], serialize: (x: number) => String(x), parse: (x: string) => Number(x) } }

/** Cliente al Postgres en memoria. PGlite atiende una sesión a la vez: una sola conexión. */
export function clienteDemo(esperarCarga = false): Sql {
  // `socket` existe en postgres.js aunque sus tipos no lo declaran.
  const opciones = { socket: () => demo.socket(esperarCarga), max: 1, prepare: false, onnotice: () => {}, types: tipos }
  return postgres(opciones as postgres.Options<typeof tipos>)
}

export function sql(): Sql {
  if (demo.activo()) {
    const enCarga = demo.cargador.getStore() as Sql | undefined
    if (enCarga) return enCarga
    if (!cliente) {
      console.log('[demo] DEMO=1: datos simulados en memoria, sin Supabase')
      cliente = clienteDemo(true)
    }
    return cliente
  }
  if (!cliente) {
    const url = process.env.DATABASE_URL
    if (!url) throw new Error('falta DATABASE_URL (cadena de conexión de Supabase); DEMO=1 corre sin base de datos')
    const local = /@(localhost|127\.0\.0\.1)[:/]/.test(url)
    cliente = postgres(url, {
      prepare: false,
      ssl: local ? false : 'require',
      max: Number(process.env.DB_CONEXIONES ?? 5),
      onnotice: () => {},
      types: tipos,
    })
  }
  return cliente
}

/** Aplica el esquema de supabase/migrations (idempotente). */
export async function migrar(): Promise<void> {
  const ruta = new URL('../../supabase/migrations/20261021000000_medidor.sql', import.meta.url)
  await sql().unsafe(readFileSync(ruta, 'utf8'))
}

export async function cerrar(): Promise<void> {
  await cliente?.end({ timeout: 5 })
  cliente = null
}
