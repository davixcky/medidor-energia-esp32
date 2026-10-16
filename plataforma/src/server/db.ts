/** Base de datos SQLite con el módulo nativo node:sqlite (Node ≥ 22.13). */
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { DatabaseSync } from 'node:sqlite'

const ESQUEMA = `
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
-- Registros ADR-001 tal como llegan (1 Hz por nodo).
CREATE TABLE IF NOT EXISTS registros (
  nodo TEXT NOT NULL, t INTEGER NOT NULL, fw TEXT,
  v REAL, i1 REAL, i2 REAL, i3 REAL, p1 REAL, p2 REAL, p3 REAL,
  q1 REAL, q2 REAL, q3 REAL, s1 REAL, s2 REAL, s3 REAL,
  fp1 REAL, fp2 REAL, fp3 REAL, f REAL, thd REAL,
  PRIMARY KEY (nodo, t)
) WITHOUT ROWID;
-- Energía integrada por hora (inicio de la hora en época Unix UTC), en kWh por canal.
CREATE TABLE IF NOT EXISTS horas (
  nodo TEXT NOT NULL, hora INTEGER NOT NULL,
  kwh1 REAL NOT NULL DEFAULT 0, kwh2 REAL NOT NULL DEFAULT 0, kwh3 REAL NOT NULL DEFAULT 0,
  segundos REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (nodo, hora)
) WITHOUT ROWID;
-- Umbral de alerta por canal: percentil 95 de los últimos 21 días, recalculado cada semana.
CREATE TABLE IF NOT EXISTS umbrales (
  nodo TEXT NOT NULL, canal INTEGER NOT NULL, valor REAL NOT NULL, calculado INTEGER NOT NULL,
  PRIMARY KEY (nodo, canal)
);
CREATE TABLE IF NOT EXISTS alertas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nodo TEXT NOT NULL, canal INTEGER NOT NULL, inicio INTEGER NOT NULL, fin INTEGER,
  pico REAL NOT NULL, umbral REAL NOT NULL,
  estado TEXT NOT NULL DEFAULT 'notificada' CHECK (estado IN ('notificada', 'revisada', 'descartada'))
);
CREATE INDEX IF NOT EXISTS alertas_nodo ON alertas (nodo, inicio DESC);
`

let db: DatabaseSync | null = null

export function base(): DatabaseSync {
  if (!db) {
    const dir = process.env.DATOS_DIR ?? join(process.cwd(), 'datos')
    mkdirSync(dir, { recursive: true })
    db = new DatabaseSync(process.env.DATOS_DB ?? join(dir, 'medidor.db'))
    db.exec(ESQUEMA)
  }
  return db
}

/** Solo para pruebas: abre una base en memoria nueva. */
export function baseEnMemoria(): DatabaseSync {
  db = new DatabaseSync(':memory:')
  db.exec(ESQUEMA)
  return db
}
