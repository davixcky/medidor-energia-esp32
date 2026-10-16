/**
 * Lógica del servidor: almacenamiento, energía por hora, umbral P95, alertas y pronóstico.
 * Los tiempos de referencia salen de los propios registros (no del reloj del servidor), así
 * el histórico cargado por el simulador se procesa igual que el de un nodo real.
 */
import { EventEmitter } from 'node:events'
import type { Registro } from './adr001'
import { base } from './db'
import { VENTANA, aKwh, recursivo, rmsePorHorizonte, variables } from './lstm'

export const ZONA = -5 * 3600 // Colombia, UTC−5 sin horario de verano
export const DIA = 86400
const BRECHA_MAX = 60 // s: más separación entre registros no se integra como energía
const ALERTA_MIN = 300 // s sostenidos sobre el umbral
const CANALES = [1, 2] as const

export const eventos = new EventEmitter()
eventos.setMaxListeners(100)

interface EstadoCanal { inicio: number | null; pico: number; alertaId: number | null; ultimo: number }
const ultimoT = new Map<string, number>()
const estadoAlerta = new Map<string, EstadoCanal>()
const umbralCache = new Map<string, { valor: number; calculado: number }>()

export function reiniciarEstado() {
  ultimoT.clear()
  estadoAlerta.clear()
  umbralCache.clear()
}

// ---------------------------------------------------------------- umbral P95
function percentil95(nodo: string, canal: number, hasta: number): number | null {
  const db = base()
  const desde = hasta - 21 * DIA
  const col = `p${canal}`
  const { n, t0 } = db.prepare(`SELECT COUNT(*) AS n, MIN(t) AS t0 FROM registros WHERE nodo = ? AND t BETWEEN ? AND ?`)
    .get(nodo, desde, hasta) as { n: number; t0: number | null }
  if (!n || t0 === null || hasta - t0 < DIA) return null // se necesita al menos un día de datos
  const fila = db.prepare(`SELECT ${col} AS p FROM registros WHERE nodo = ? AND t BETWEEN ? AND ? ORDER BY ${col} LIMIT 1 OFFSET ?`)
    .get(nodo, desde, hasta, Math.floor(0.95 * (n - 1))) as { p: number }
  return fila.p
}

function umbral(nodo: string, canal: number, t: number): number | null {
  const k = `${nodo}:${canal}`
  let u = umbralCache.get(k)
  if (!u) {
    const fila = base().prepare('SELECT valor, calculado FROM umbrales WHERE nodo = ? AND canal = ?').get(nodo, canal) as
      | { valor: number; calculado: number } | undefined
    if (fila) umbralCache.set(k, (u = fila))
  }
  if (!u || t - u.calculado >= 7 * DIA) {
    const v = percentil95(nodo, canal, t)
    if (v === null) return u?.valor ?? null
    base().prepare('INSERT OR REPLACE INTO umbrales (nodo, canal, valor, calculado) VALUES (?, ?, ?, ?)').run(nodo, canal, v, t)
    umbralCache.set(k, (u = { valor: v, calculado: t }))
  }
  return u.valor
}

// ---------------------------------------------------------------- alertas
function revisarAlerta(nodo: string, canal: number, t: number, p: number) {
  const k = `${nodo}:${canal}`
  const e = estadoAlerta.get(k) ?? { inicio: null, pico: 0, alertaId: null, ultimo: t }
  const db = base()
  const u = umbral(nodo, canal, t)
  const cortar = () => {
    if (e.alertaId !== null) db.prepare('UPDATE alertas SET fin = ?, pico = ? WHERE id = ?').run(e.ultimo, e.pico, e.alertaId)
    e.inicio = null
    e.alertaId = null
    e.pico = 0
  }
  if (t - e.ultimo > BRECHA_MAX) cortar()
  if (u !== null && p > u) {
    if (e.inicio === null) { e.inicio = t; e.pico = p }
    e.pico = Math.max(e.pico, p)
    if (e.alertaId === null && t - e.inicio >= ALERTA_MIN) {
      const r = db.prepare('INSERT INTO alertas (nodo, canal, inicio, pico, umbral) VALUES (?, ?, ?, ?, ?)').run(nodo, canal, e.inicio, e.pico, u)
      e.alertaId = Number(r.lastInsertRowid)
      eventos.emit('alerta', { nodo, canal })
    }
  } else cortar()
  e.ultimo = t
  estadoAlerta.set(k, e)
}

// ---------------------------------------------------------------- ingesta
export function ingerir(nodo: string, fw: string | null, registros: Registro[]): number {
  const db = base()
  const ins = db.prepare(`INSERT OR IGNORE INTO registros VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
  const hora = db.prepare(`INSERT INTO horas (nodo, hora, kwh1, kwh2, kwh3, segundos) VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT (nodo, hora) DO UPDATE SET kwh1 = kwh1 + excluded.kwh1, kwh2 = kwh2 + excluded.kwh2,
    kwh3 = kwh3 + excluded.kwh3, segundos = segundos + excluded.segundos`)
  if (!ultimoT.has(nodo)) {
    const f = db.prepare('SELECT MAX(t) AS t FROM registros WHERE nodo = ?').get(nodo) as { t: number | null }
    if (f.t !== null) ultimoT.set(nodo, f.t)
  }
  const orden = [...registros].sort((a, b) => a.t - b.t)
  let aceptados = 0
  db.exec('BEGIN')
  try {
    for (const r of orden) {
      const res = ins.run(nodo, r.t, fw, r.v_rms, ...r.i_rms, ...r.p, ...r.q, ...r.s, ...r.fp, r.f, r.thd)
      if (!res.changes) continue // duplicado (el firmware reenvía lo que no confirmó)
      aceptados++
      // Energía: potencia × tiempo hasta el registro anterior; brechas largas no se integran.
      const prev = ultimoT.get(nodo)
      const dt = prev !== undefined && r.t > prev && r.t - prev <= BRECHA_MAX ? r.t - prev : 1
      if (prev === undefined || r.t > prev) ultimoT.set(nodo, r.t)
      const h = Math.floor(r.t / 3600) * 3600
      hora.run(nodo, h, (r.p[0] * dt) / 3.6e6, (r.p[1] * dt) / 3.6e6, (r.p[2] * dt) / 3.6e6, dt)
      for (const c of CANALES) revisarAlerta(nodo, c, r.t, r.p[c - 1])
    }
    db.exec('COMMIT')
  } catch (e) {
    db.exec('ROLLBACK')
    throw e
  }
  if (aceptados) eventos.emit('registro', { nodo, registro: orden[orden.length - 1] })
  return aceptados
}

// ---------------------------------------------------------------- lecturas
export function nodos(): string[] {
  return (base().prepare('SELECT DISTINCT nodo FROM horas ORDER BY nodo').all() as { nodo: string }[]).map((x) => x.nodo)
}

export function ultimo(nodo: string) {
  return base().prepare('SELECT * FROM registros WHERE nodo = ? ORDER BY t DESC LIMIT 1').get(nodo) as
    | Record<string, number | string> | undefined
}

/** Promedios por intervalo de las últimas `horas` (referidas al último registro). */
export function serie(nodo: string, horas = 24, paso = 300) {
  const u = ultimo(nodo)
  if (!u) return []
  const hasta = u.t as number
  // CAST: node:sqlite enlaza los números de JS como REAL y la división dejaría de ser entera.
  return base().prepare(`SELECT (t / CAST(?1 AS INTEGER)) * CAST(?1 AS INTEGER) AS t, AVG(p1) AS p1, AVG(p2) AS p2,
    AVG(v) AS v, AVG(fp1) AS fp1 FROM registros WHERE nodo = ?2 AND t > ?3 GROUP BY 1 ORDER BY 1`)
    .all(Math.round(paso), nodo, hasta - horas * 3600)
}

const diaLocal = (t: number) => Math.floor((t + ZONA) / DIA)

export function energia(nodo: string) {
  const u = ultimo(nodo)
  if (!u) return null
  const ahora = u.t as number
  const hoy = diaLocal(ahora)
  const fechaHoy = new Date((hoy * DIA) * 1000)
  const inicioMes = Date.UTC(fechaHoy.getUTCFullYear(), fechaHoy.getUTCMonth(), 1) / 1000 - ZONA
  const diasMes = new Date(Date.UTC(fechaHoy.getUTCFullYear(), fechaHoy.getUTCMonth() + 1, 0)).getUTCDate()
  const dias = base().prepare(`SELECT (hora + CAST(? AS INTEGER)) / ${DIA} AS dia, SUM(kwh1) AS kwh1, SUM(kwh2) AS kwh2, SUM(segundos) AS seg
    FROM horas WHERE nodo = ? AND hora >= ? GROUP BY 1 ORDER BY 1`).all(ZONA, nodo, inicioMes - 40 * DIA) as
    { dia: number; kwh1: number; kwh2: number; seg: number }[]
  const delMes = dias.filter((d) => d.dia * DIA >= inicioMes + ZONA)
  const hoyFila = dias.find((d) => d.dia === hoy)
  const ayer = dias.find((d) => d.dia === hoy - 1)
  // Proyección del mes: lo medido + promedio de los últimos 7 días completos × días que faltan.
  const completos = dias.filter((d) => d.dia < hoy && d.seg > 0.9 * DIA).slice(-7).map((d) => d.kwh1)
  const media = completos.length ? completos.reduce((a, b) => a + b, 0) / completos.length : null
  const desv = completos.length > 1 ? Math.sqrt(completos.reduce((a, b) => a + (b - media!) ** 2, 0) / (completos.length - 1)) : 0
  const medidoMes = delMes.reduce((a, d) => a + d.kwh1, 0)
  const fraccionHoy = ((ahora + ZONA) % DIA) / DIA
  const faltan = diasMes - (hoy - (inicioMes + ZONA) / DIA) - fraccionHoy
  const proyeccion = media === null ? null : {
    kwh: medidoMes + media * faltan,
    min: medidoMes + Math.max(0, media * faltan - 1.645 * desv * Math.sqrt(faltan)),
    max: medidoMes + media * faltan + 1.645 * desv * Math.sqrt(faltan),
    dias_base: completos.length,
  }
  return {
    hoy: { kwh1: hoyFila?.kwh1 ?? 0, kwh2: hoyFila?.kwh2 ?? 0 },
    ayer_misma_hora: ayer ? horaParcial(nodo, (hoy - 1) * DIA - ZONA, ahora - DIA) : null,
    mes: { kwh: medidoMes, dias: delMes.map((d) => ({ dia: new Date(d.dia * DIA * 1000).toISOString().slice(0, 10), kwh1: d.kwh1, kwh2: d.kwh2 })), dias_mes: diasMes },
    proyeccion,
  }
}

function horaParcial(nodo: string, desde: number, hasta: number) {
  const f = base().prepare('SELECT SUM(kwh1) AS k FROM horas WHERE nodo = ? AND hora >= ? AND hora < ?').get(nodo, desde, hasta) as { k: number | null }
  return f.k ?? 0
}

export function alertas(nodo: string, limite = 50) {
  return base().prepare('SELECT * FROM alertas WHERE nodo = ? ORDER BY inicio DESC LIMIT ?').all(nodo, limite)
}

export function cambiarEstado(id: number, estado: string): boolean {
  if (!['notificada', 'revisada', 'descartada'].includes(estado)) throw new Error('estado inválido')
  return base().prepare('UPDATE alertas SET estado = ? WHERE id = ?').run(estado, id).changes > 0
}

export function umbrales(nodo: string) {
  return base().prepare('SELECT canal, valor, calculado FROM umbrales WHERE nodo = ?').all(nodo)
}

// ---------------------------------------------------------------- pronóstico
/**
 * Temperatura que recibe el LSTM para cada hora local. Por defecto, un perfil diario típico de
 * Barranquilla (25 °C a las 5 h, 32 °C a las 14 h). TEMP_CONSTANTE=<°C> fija un valor único.
 */
export function temperatura(horaLocal: number): number {
  const c = process.env.TEMP_CONSTANTE
  if (c !== undefined && c !== '') return Number(c)
  return 28.5 + 3.5 * Math.cos((2 * Math.PI * (horaLocal - 14)) / 24)
}

function rasgos(hora: number) {
  const loc = new Date((hora + ZONA) * 1000)
  return { h: loc.getUTCHours(), d: (loc.getUTCDay() + 6) % 7 }
}

export function pronostico(nodo: string, H = 48) {
  const u = ultimo(nodo)
  if (!u) return { disponible: false, motivo: 'sin datos' }
  const horaActual = Math.floor((u.t as number) / 3600) * 3600
  const filas = base().prepare('SELECT hora, kwh1, segundos FROM horas WHERE nodo = ? AND hora >= ? AND hora < ? ORDER BY hora')
    .all(nodo, horaActual - VENTANA * 3600, horaActual) as { hora: number; kwh1: number; segundos: number }[]
  const completas = filas.filter((f) => f.segundos >= 0.9 * 3600)
  if (completas.length < VENTANA) {
    return { disponible: false, motivo: `se necesitan ${VENTANA} horas completas; hay ${completas.length}` }
  }
  const v = completas.map((f) => { const r = rasgos(f.hora); return variables(f.kwh1, r.h, r.d, temperatura(r.h)) })
  const futuras: number[] = []
  for (let k = 0; k < H; k++) {
    const hora = horaActual + k * 3600
    futuras.push(hora)
    const r = rasgos(hora)
    v.push(variables(0, r.h, r.d, temperatura(r.h)))
  }
  const z = recursivo(v, H)
  return {
    disponible: true,
    modelo: 'LSTM 24×4 → 32 → 16 → 1 (5.281 parámetros), entrenado con UCI',
    temperatura: process.env.TEMP_CONSTANTE ? `constante ${process.env.TEMP_CONSTANTE} °C` : 'perfil diario típico de Barranquilla (25–32 °C)',
    horas: futuras.map((hora, k) => {
      const kwh = Math.max(0, aKwh(z[k]))
      const e = 1.645 * rmsePorHorizonte(k + 1)
      return { hora, kwh, min: Math.max(0, kwh - e), max: kwh + e }
    }),
  }
}

/** Todo lo que necesita el tablero, en una sola lectura. */
export function tablero(nodoPedido?: string) {
  const lista = nodos()
  const nodo = nodoPedido || lista[0] || 'nodo01'
  return {
    nodos: lista, nodo, ultimo: ultimo(nodo) ?? null, serie: serie(nodo, 24, 300), energia: energia(nodo),
    alertas: alertas(nodo, 20), umbrales: umbrales(nodo), pronostico: pronostico(nodo, 48),
  }
}
export type Tablero = ReturnType<typeof tablero>
