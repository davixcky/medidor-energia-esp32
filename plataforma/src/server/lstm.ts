/**
 * Inferencia del LSTM de C2-ABPR/pronostico en TypeScript, con los pesos exportados por
 * scripts/exportar_lstm.py. Reproduce modelo.py: LSTM 32 con un sesgo por compuerta
 * (orden f, i, g, o; entrada [h, x]) → Densa 16 ReLU → Densa 1. El dropout no actúa al inferir.
 */
import pesos from './lstm-pesos.json'

type Mat = number[][]
const E = pesos.estado as unknown as Record<string, Mat | number[]>
const W = E['lstm.lin.weight'] as Mat // 128 × 36
const B = E['lstm.lin.bias'] as number[]
const W1 = E['red.1.weight'] as Mat // 16 × 32
const B1 = E['red.1.bias'] as number[]
const W2 = E['red.3.weight'] as Mat // 1 × 16
const B2 = E['red.3.bias'] as number[]
const U = 32
export const VENTANA = 24
export const NORMALIZACION = pesos.normalizacion

const sig = (x: number) => 1 / (1 + Math.exp(-x))

/** Una ventana de 24 × 4 variables normalizadas → consumo normalizado de la hora siguiente. */
export function unPaso(ventana: number[][]): number {
  let h = new Array(U).fill(0)
  let c = new Array(U).fill(0)
  for (const x of ventana) {
    const z = h.concat(x)
    const a = new Array(4 * U)
    for (let r = 0; r < 4 * U; r++) {
      let s = B[r]
      const fila = W[r]
      for (let k = 0; k < z.length; k++) s += fila[k] * z[k]
      a[r] = s
    }
    const hn = new Array(U)
    const cn = new Array(U)
    for (let j = 0; j < U; j++) {
      const f = sig(a[j]), i = sig(a[U + j]), g = Math.tanh(a[2 * U + j]), o = sig(a[3 * U + j])
      cn[j] = f * c[j] + i * g
      hn[j] = o * Math.tanh(cn[j])
    }
    h = hn
    c = cn
  }
  const d = W1.map((fila, r) => Math.max(0, fila.reduce((s, w, k) => s + w * h[k], B1[r])))
  return W2[0].reduce((s, w, k) => s + w * d[k], B2[0])
}

/**
 * Pronóstico recursivo: `v` tiene 24 filas medidas seguidas de H filas futuras cuyas columnas
 * de hora, día y temperatura ya están llenas; cada predicción se escribe como consumo de su hora.
 */
export function recursivo(v: number[][], H: number): number[] {
  const w = v.map((f) => f.slice())
  const out: number[] = []
  for (let k = 0; k < H; k++) {
    const z = unPaso(w.slice(k, k + VENTANA))
    w[VENTANA + k][0] = z
    out.push(z)
  }
  return out
}

/** Variables de una hora: kWh y temperatura estandarizados, hora/23 y día/6 (lunes = 0, como pandas). */
export function variables(kwh: number, horaLocal: number, diaLunes0: number, temp: number): number[] {
  const n = NORMALIZACION
  return [(kwh - n.kwh_m) / n.kwh_s, horaLocal / 23, diaLunes0 / 6, (temp - n.temp_m) / n.temp_s]
}

export const aKwh = (z: number) => z * NORMALIZACION.kwh_s + NORMALIZACION.kwh_m

/** RMSE del LSTM en la prueba de UCI (kWh), para el intervalo del 90 %: 1 h, 24 h y 48 h. */
export function rmsePorHorizonte(k: number): number {
  const r = pesos.metricas.resultados as unknown as Record<string, Record<string, { RMSE: number }>>
  const r1 = r['1 h'].LSTM.RMSE, r24 = r['24 h recursivo'].LSTM.RMSE, r48 = r['48 h recursivo'].LSTM.RMSE
  if (k <= 1) return r1
  if (k <= 24) return r1 + ((r24 - r1) * (k - 1)) / 23
  return r24 + ((r48 - r24) * (k - 24)) / 24
}
