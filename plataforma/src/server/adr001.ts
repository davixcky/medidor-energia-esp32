/**
 * Contrato de datos ADR-001: un registro de 40 B, little-endian, sin relleno.
 * Es el mismo formato que publica el firmware del ESP32 (C2-ABPR/firmware/).
 *
 * offset  tipo      campo      escala
 *  0      uint32    t          1 s (época Unix, UTC)
 *  4      int16     v_rms      0,01 V
 *  6      int16[3]  i_rms      0,01 A   (0 = CH1, 1 = CH2, 2 = CH3 de reserva)
 * 12      int16[3]  p          1 W
 * 18      int16[3]  q          1 var
 * 24      int16[3]  s          1 VA
 * 30      int16[3]  fp         0,0001   (−1…1 → −10000…10000)
 * 36      int16     f          0,01 Hz
 * 38      int16     thd        0,01 %   (THD de corriente de CH1)
 */
export const TAMANO_REGISTRO = 40

export type Tripleta = [number, number, number]

export interface Registro {
  t: number
  v_rms: number
  i_rms: Tripleta
  p: Tripleta
  q: Tripleta
  s: Tripleta
  fp: Tripleta
  f: number
  thd: number
}

const ESCALA = { v_rms: 0.01, i_rms: 0.01, p: 1, q: 1, s: 1, fp: 0.0001, f: 0.01, thd: 0.01 }

function leer3(dv: DataView, o: number, escala: number): Tripleta {
  return [dv.getInt16(o, true) * escala, dv.getInt16(o + 2, true) * escala, dv.getInt16(o + 4, true) * escala]
}

export function decodificar(dv: DataView, o = 0): Registro {
  return {
    t: dv.getUint32(o, true),
    v_rms: dv.getInt16(o + 4, true) * ESCALA.v_rms,
    i_rms: leer3(dv, o + 6, ESCALA.i_rms),
    p: leer3(dv, o + 12, ESCALA.p),
    q: leer3(dv, o + 18, ESCALA.q),
    s: leer3(dv, o + 24, ESCALA.s),
    fp: leer3(dv, o + 30, ESCALA.fp),
    f: dv.getInt16(o + 36, true) * ESCALA.f,
    thd: dv.getInt16(o + 38, true) * ESCALA.thd,
  }
}

/** Decodifica un cuerpo con uno o más registros concatenados (el firmware agrupa los que guardó sin red). */
export function decodificarLote(buf: ArrayBuffer | Uint8Array): Registro[] {
  const u8 = buf instanceof Uint8Array ? buf : new Uint8Array(buf)
  if (u8.byteLength === 0 || u8.byteLength % TAMANO_REGISTRO !== 0) {
    throw new Error(`El cuerpo mide ${u8.byteLength} B; debe ser un múltiplo de ${TAMANO_REGISTRO} B`)
  }
  const dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength)
  const out: Registro[] = []
  for (let o = 0; o < u8.byteLength; o += TAMANO_REGISTRO) out.push(decodificar(dv, o))
  return out
}

function i16(x: number, escala: number): number {
  const v = Math.round(x / escala)
  return Math.max(-32768, Math.min(32767, v))
}

export function codificar(r: Registro, dv: DataView, o = 0): void {
  dv.setUint32(o, r.t >>> 0, true)
  dv.setInt16(o + 4, i16(r.v_rms, ESCALA.v_rms), true)
  const tri = (base: number, x: Tripleta, e: number) => x.forEach((v, k) => dv.setInt16(base + 2 * k, i16(v, e), true))
  tri(o + 6, r.i_rms, ESCALA.i_rms)
  tri(o + 12, r.p, ESCALA.p)
  tri(o + 18, r.q, ESCALA.q)
  tri(o + 24, r.s, ESCALA.s)
  tri(o + 30, r.fp, ESCALA.fp)
  dv.setInt16(o + 36, i16(r.f, ESCALA.f), true)
  dv.setInt16(o + 38, i16(r.thd, ESCALA.thd), true)
}

export function codificarLote(rs: Registro[]): Uint8Array {
  const u8 = new Uint8Array(rs.length * TAMANO_REGISTRO)
  const dv = new DataView(u8.buffer)
  rs.forEach((r, k) => codificar(r, dv, k * TAMANO_REGISTRO))
  return u8
}

/** Comprueba que los valores estén en rangos físicamente posibles; devuelve el motivo si no. */
export function validar(r: Registro): string | null {
  if (!Number.isFinite(r.t) || r.t < 1_600_000_000) return 't fuera de rango (¿reloj sin NTP?)'
  if (r.v_rms < 0 || r.v_rms > 300) return 'v_rms fuera de 0–300 V'
  if (r.f !== 0 && (r.f < 40 || r.f > 70)) return 'f fuera de 40–70 Hz'
  for (const x of r.fp) if (x < -1.0001 || x > 1.0001) return 'fp fuera de −1…1'
  for (const x of r.i_rms) if (x < 0 || x > 120) return 'i_rms fuera de 0–120 A'
  return null
}

/** Versión JSON del registro (misma forma que Registro), para clientes que no envían binario. */
export function desdeJson(o: unknown): Registro {
  const x = o as Record<string, unknown>
  const tri = (k: string): Tripleta => {
    const a = x[k]
    if (!Array.isArray(a) || a.length !== 3 || a.some((v) => typeof v !== 'number')) throw new Error(`${k} debe ser [n, n, n]`)
    return a as Tripleta
  }
  const num = (k: string): number => {
    if (typeof x[k] !== 'number') throw new Error(`${k} debe ser numérico`)
    return x[k] as number
  }
  return { t: num('t'), v_rms: num('v_rms'), i_rms: tri('i_rms'), p: tri('p'), q: tri('q'), s: tri('s'), fp: tri('fp'), f: num('f'), thd: num('thd') }
}
