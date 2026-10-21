/**
 * Conexión a la base de datos en Supabase (Postgres) con postgres.js.
 *
 * DATABASE_URL es la cadena de conexión del proyecto de Supabase (Project Settings → Database).
 * Con el pooler en modo transacción (puerto 6543) las sentencias preparadas no se pueden reutilizar,
 * por eso van desactivadas. Para las pruebas sirve cualquier Postgres local.
 */
import { readFileSync } from 'node:fs'
import postgres from 'postgres'

export type Sql = postgres.Sql
/** Conexión dentro de una transacción (sql().begin). */
export type Tx = postgres.TransactionSql

let cliente: Sql | null = null

export function sql(): Sql {
  if (!cliente) {
    const url = process.env.DATABASE_URL
    if (!url) throw new Error('falta DATABASE_URL (cadena de conexión de Supabase)')
    const local = /@(localhost|127\.0\.0\.1)[:/]/.test(url)
    cliente = postgres(url, {
      prepare: false,
      ssl: local ? false : 'require',
      max: Number(process.env.DB_CONEXIONES ?? 5),
      onnotice: () => {},
      // bigint (t, hora, conteos) como número de JS: los valores caben de sobra en 2^53
      types: { bigint: { to: 20, from: [20], serialize: (x: number) => String(x), parse: (x: string) => Number(x) } },
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
