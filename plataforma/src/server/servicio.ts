/**
 * Lógica del servidor: almacenamiento, energía por hora, umbral P95, alertas y pronóstico.
 * Los tiempos de referencia salen de los propios registros (no del reloj del servidor), así
 * el histórico cargado por el simulador se procesa igual que el de un nodo real.
 */
import { EventEmitter } from 'node:events'
import type { Registro } from './adr001'
import { type Tx, sql } from './db'
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
// reintento: cuándo volver a calcular el P95 (7 días después, o cuando ya haya un día de datos)
const umbralCache = new Map<string, { valor: number | null; reintento: number }>()

export function reiniciarEstado() {
  ultimoT.clear()
  estadoAlerta.clear()
  umbralCache.clear()
}

// ---------------------------------------------------------------- umbral P95
/** P95 de la potencia del canal en los 21 días previos; null y el primer registro si falta un día de datos. */
async function percentil95(db: Tx, nodo: string, canal: number, hasta: number) {
  const desde = hasta - 21 * DIA
  const col = db(`p${canal}`)
  const [{ n, t0 }] = await db<{ n: number; t0: number | null }[]>`
    SELECT COUNT(*)::bigint AS n, MIN(t) AS t0 FROM registros WHERE nodo = ${nodo} AND t BETWEEN ${desde} AND ${hasta}`
  if (!n || t0 === null || hasta - t0 < DIA) return { p: null, t0: t0 ?? hasta }
  const [fila] = await db<{ p: number }[]>`
    SELECT ${col} AS p FROM registros WHERE nodo = ${nodo} AND t BETWEEN ${desde} AND ${hasta}
    ORDER BY ${col} LIMIT 1 OFFSET ${Math.floor(0.95 * (n - 1))}`
  return { p: fila.p, t0 }
}

async function umbral(db: Tx, nodo: string, canal: number, t: number): Promise<number | null> {
  const k = `${nodo}:${canal}`
  let u = umbralCache.get(k)
  if (!u) {
    const [fila] = await db<{ valor: number; calculado: number }[]>`
      SELECT valor, calculado FROM umbrales WHERE nodo = ${nodo} AND canal = ${canal}`
    if (fila) umbralCache.set(k, (u = { valor: fila.valor, reintento: fila.calculado + 7 * DIA }))
  }
  if (!u || t >= u.reintento) {
    const { p, t0 } = await percentil95(db, nodo, canal, t)
    if (p === null) {
      // Sin un día de datos todavía: se espera a tenerlo en vez de consultar en cada registro.
      umbralCache.set(k, (u = { valor: u?.valor ?? null, reintento: t0 + DIA }))
      return u.valor
    }
    await db`INSERT INTO umbrales (nodo, canal, valor, calculado) VALUES (${nodo}, ${canal}, ${p}, ${t})
      ON CONFLICT (nodo, canal) DO UPDATE SET valor = excluded.valor, calculado = excluded.calculado`
    umbralCache.set(k, (u = { valor: p, reintento: t + 7 * DIA }))
  }
  return u.valor
}

// ---------------------------------------------------------------- alertas
async function revisarAlerta(db: Tx, nodo: string, canal: number, t: number, p: number, abiertas: { nodo: string; canal: number }[]) {
  const k = `${nodo}:${canal}`
  const e = estadoAlerta.get(k) ?? { inicio: null, pico: 0, alertaId: null, ultimo: t }
  const u = await umbral(db, nodo, canal, t)
  const cortar = async () => {
    if (e.alertaId !== null) await db`UPDATE alertas SET fin = ${e.ultimo}, pico = ${e.pico} WHERE id = ${e.alertaId}`
    e.inicio = null
    e.alertaId = null
    e.pico = 0
  }
  if (t - e.ultimo > BRECHA_MAX) await cortar()
  if (u !== null && p > u) {
    if (e.inicio === null) { e.inicio = t; e.pico = p }
    e.pico = Math.max(e.pico, p)
    if (e.alertaId === null && t - e.inicio >= ALERTA_MIN) {
      const [r] = await db<{ id: number }[]>`INSERT INTO alertas (nodo, canal, inicio, pico, umbral)
        VALUES (${nodo}, ${canal}, ${e.inicio}, ${e.pico}, ${u}) RETURNING id`
      e.alertaId = r.id
      abiertas.push({ nodo, canal })
    }
  } else await cortar()
  e.ultimo = t
  estadoAlerta.set(k, e)
}

// ---------------------------------------------------------------- ingesta
const COLUMNAS = ['nodo', 't', 'fw', 'v', 'i1', 'i2', 'i3', 'p1', 'p2', 'p3', 'q1', 'q2', 'q3',
  's1', 's2', 's3', 'fp1', 'fp2', 'fp3', 'f', 'thd'] as const

/**
 * Guarda un lote de registros en una transacción. Los registros se insertan de una vez y la
 * energía por hora se acumula en memoria antes de escribirla: con la base en Supabase cada viaje
 * de ida y vuelta cuesta decenas de milisegundos.
 */
export async function ingerir(nodo: string, fw: string | null, registros: Registro[]): Promise<number> {
  const orden = [...registros].sort((a, b) => a.t - b.t)
  if (!orden.length) return 0
  const abiertas: { nodo: string; canal: number }[] = []
  const aceptados = await sql().begin(async (db) => {
    if (!ultimoT.has(nodo)) {
      const [f] = await db<{ t: number | null }[]>`SELECT MAX(t) AS t FROM registros WHERE nodo = ${nodo}`
      if (f.t !== null) ultimoT.set(nodo, f.t)
    }
    // Duplicados (el firmware reenvía lo que no confirmó): ON CONFLICT los descarta y RETURNING
    // dice cuáles entraron.
    const nuevos = new Set<number>()
    for (let k = 0; k < orden.length; k += 1000) {
      const filas = orden.slice(k, k + 1000).map((r) => ({
        nodo, t: r.t, fw, v: r.v_rms, i1: r.i_rms[0], i2: r.i_rms[1], i3: r.i_rms[2],
        p1: r.p[0], p2: r.p[1], p3: r.p[2], q1: r.q[0], q2: r.q[1], q3: r.q[2],
        s1: r.s[0], s2: r.s[1], s3: r.s[2], fp1: r.fp[0], fp2: r.fp[1], fp3: r.fp[2], f: r.f, thd: r.thd,
      }))
      const res = await db<{ t: number }[]>`INSERT INTO registros ${db(filas, ...COLUMNAS)}
        ON CONFLICT (nodo, t) DO NOTHING RETURNING t`
      for (const x of res) nuevos.add(x.t)
    }
    // Energía: potencia × tiempo hasta el registro anterior; brechas largas no se integran.
    const horas = new Map<number, { kwh1: number; kwh2: number; kwh3: number; segundos: number }>()
    let n = 0
    for (const r of orden) {
      if (!nuevos.delete(r.t)) continue
      n++
      const prev = ultimoT.get(nodo)
      const dt = prev !== undefined && r.t > prev && r.t - prev <= BRECHA_MAX ? r.t - prev : 1
      if (prev === undefined || r.t > prev) ultimoT.set(nodo, r.t)
      const h = Math.floor(r.t / 3600) * 3600
      const acc = horas.get(h) ?? { kwh1: 0, kwh2: 0, kwh3: 0, segundos: 0 }
      acc.kwh1 += (r.p[0] * dt) / 3.6e6
      acc.kwh2 += (r.p[1] * dt) / 3.6e6
      acc.kwh3 += (r.p[2] * dt) / 3.6e6
      acc.segundos += dt
      horas.set(h, acc)
      for (const c of CANALES) await revisarAlerta(db, nodo, c, r.t, r.p[c - 1], abiertas)
    }
    if (horas.size) {
      const filas = [...horas].map(([hora, a]) => ({ nodo, hora, ...a }))
      await db`INSERT INTO horas ${db(filas, 'nodo', 'hora', 'kwh1', 'kwh2', 'kwh3', 'segundos')}
        ON CONFLICT (nodo, hora) DO UPDATE SET kwh1 = horas.kwh1 + excluded.kwh1, kwh2 = horas.kwh2 + excluded.kwh2,
        kwh3 = horas.kwh3 + excluded.kwh3, segundos = horas.segundos + excluded.segundos`
    }
    return n
  })
  for (const a of abiertas) eventos.emit('alerta', a)
  if (aceptados) eventos.emit('registro', { nodo, registro: orden[orden.length - 1] })
  return aceptados
}

// ---------------------------------------------------------------- lecturas
export async function nodos(): Promise<string[]> {
  return (await sql()<{ nodo: string }[]>`SELECT DISTINCT nodo FROM horas ORDER BY nodo`).map((x) => x.nodo)
}

export async function ultimo(nodo: string) {
  const [fila] = await sql()<Record<string, number | string>[]>`
    SELECT * FROM registros WHERE nodo = ${nodo} ORDER BY t DESC LIMIT 1`
  return fila
}

/** Promedios por intervalo de las últimas `horas` (referidas al último registro). */
export async function serie(nodo: string, horas = 24, paso = 300) {
  const u = await ultimo(nodo)
  if (!u) return []
  const hasta = u.t as number
  const p = Math.round(paso)
  return sql()<{ t: number; p1: number; p2: number; v: number; fp1: number }[]>`
    SELECT (t / ${p}::bigint) * ${p}::bigint AS t, AVG(p1) AS p1, AVG(p2) AS p2, AVG(v) AS v, AVG(fp1) AS fp1
    FROM registros WHERE nodo = ${nodo} AND t > ${hasta - horas * 3600} GROUP BY 1 ORDER BY 1`
}

const diaLocal = (t: number) => Math.floor((t + ZONA) / DIA)

export async function energia(nodo: string) {
  const u = await ultimo(nodo)
  if (!u) return null
  const ahora = u.t as number
  const hoy = diaLocal(ahora)
  const fechaHoy = new Date((hoy * DIA) * 1000)
  const inicioMes = Date.UTC(fechaHoy.getUTCFullYear(), fechaHoy.getUTCMonth(), 1) / 1000 - ZONA
  const diasMes = new Date(Date.UTC(fechaHoy.getUTCFullYear(), fechaHoy.getUTCMonth() + 1, 0)).getUTCDate()
  const dias = await sql()<{ dia: number; kwh1: number; kwh2: number; seg: number }[]>`
    SELECT (hora + ${ZONA}::bigint) / ${DIA}::bigint AS dia, SUM(kwh1) AS kwh1, SUM(kwh2) AS kwh2, SUM(segundos) AS seg
    FROM horas WHERE nodo = ${nodo} AND hora >= ${inicioMes - 40 * DIA} GROUP BY 1 ORDER BY 1`
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
    ayer_misma_hora: ayer ? await horaParcial(nodo, (hoy - 1) * DIA - ZONA, ahora - DIA) : null,
    mes: { kwh: medidoMes, dias: delMes.map((d) => ({ dia: new Date(d.dia * DIA * 1000).toISOString().slice(0, 10), kwh1: d.kwh1, kwh2: d.kwh2 })), dias_mes: diasMes },
    proyeccion,
  }
}

async function horaParcial(nodo: string, desde: number, hasta: number) {
  const [f] = await sql()<{ k: number | null }[]>`
    SELECT SUM(kwh1) AS k FROM horas WHERE nodo = ${nodo} AND hora >= ${desde} AND hora < ${hasta}`
  return f.k ?? 0
}

export async function alertas(nodo: string, limite = 50) {
  return sql()<{ id: number; nodo: string; canal: number; inicio: number; fin: number | null; pico: number; umbral: number; estado: string }[]>`
    SELECT * FROM alertas WHERE nodo = ${nodo} ORDER BY inicio DESC LIMIT ${limite}`
}

export async function cambiarEstado(id: number, estado: string): Promise<boolean> {
  if (!['notificada', 'revisada', 'descartada'].includes(estado)) throw new Error('estado inválido')
  const r = await sql()`UPDATE alertas SET estado = ${estado} WHERE id = ${id}`
  return r.count > 0
}

export async function umbrales(nodo: string) {
  return sql()<{ canal: number; valor: number; calculado: number }[]>`
    SELECT canal, valor, calculado FROM umbrales WHERE nodo = ${nodo}`
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

export async function pronostico(nodo: string, H = 48) {
  const u = await ultimo(nodo)
  if (!u) return { disponible: false, motivo: 'sin datos' }
  const horaActual = Math.floor((u.t as number) / 3600) * 3600
  const filas = await sql()<{ hora: number; kwh1: number; segundos: number }[]>`
    SELECT hora, kwh1, segundos FROM horas WHERE nodo = ${nodo} AND hora >= ${horaActual - VENTANA * 3600}
    AND hora < ${horaActual} ORDER BY hora`
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
export async function tablero(nodoPedido?: string) {
  const lista = await nodos()
  const nodo = nodoPedido || lista[0] || 'nodo01'
  const [u, s, e, a, um, p] = await Promise.all([ultimo(nodo), serie(nodo, 24, 300), energia(nodo),
    alertas(nodo, 20), umbrales(nodo), pronostico(nodo, 48)])
  return { nodos: lista, nodo, ultimo: u ?? null, serie: [...s], energia: e, alertas: [...a], umbrales: [...um], pronostico: p }
}
export type Tablero = Awaited<ReturnType<typeof tablero>>
