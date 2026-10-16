/**
 * Simulador del nodo ESP32: genera mediciones de una vivienda de la costa Caribe y las envía a
 * POST /api/ingesta exactamente como lo hará el firmware: registros ADR-001 de 40 B en binario,
 * concatenados, con las cabeceras X-Nodo y X-Firmware.
 *
 *   node scripts/simular.ts                    # en vivo, un registro por segundo
 *   node scripts/simular.ts --dias 21          # primero carga 21 días de histórico y luego sigue en vivo
 *   node scripts/simular.ts --dias 21 --solo-historico
 *
 * Opciones: --url (http://localhost:3000), --nodo (nodo01), --paso (s entre registros del histórico, 10).
 */
import { type Registro, codificarLote } from '../src/server/adr001.ts'

const arg = (n: string, d?: string) => {
  const i = process.argv.indexOf(`--${n}`)
  return i >= 0 ? (process.argv[i + 1] ?? '') : d
}
const URL_BASE = arg('url', 'http://localhost:3000')!
const NODO = arg('nodo', 'nodo01')!
const DIAS = Number(arg('dias', '0'))
const PASO = Number(arg('paso', '10'))
const SOLO_HISTORICO = process.argv.includes('--solo-historico')
const ZONA = -5 * 3600

// Generador pseudoaleatorio con semilla: el mismo día produce siempre el mismo perfil.
function aleatorio(semilla: number) {
  let s = semilla >>> 0
  return () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296)
}
const ruido = aleatorio(20261016)

interface Dia { factor: number; aireDesde: number; aireHasta: number; aireNoche: boolean; cocina: number[] }
const dias = new Map<number, Dia>()
function dia(n: number): Dia {
  let d = dias.get(n)
  if (!d) {
    const r = aleatorio(n * 7919)
    const finde = [5, 6].includes((new Date(n * 86400000).getUTCDay() + 6) % 7)
    d = {
      factor: 0.85 + 0.3 * r() + (finde ? 0.1 : 0),
      aireDesde: 12.5 + 2 * r(),
      aireHasta: 22 + 1.5 * r(),
      aireNoche: r() < 0.7,
      cocina: [6.2 + 0.6 * r(), 11.6 + 0.6 * r(), 18.4 + 0.8 * r()],
    }
    dias.set(n, d)
  }
  return d
}

/** Potencias de CH1 (total) y CH2 (aire acondicionado) para un instante. */
function potencias(t: number) {
  const loc = t + ZONA
  const d = dia(Math.floor(loc / 86400))
  const h = (loc % 86400) / 3600
  const base = 190 + 30 * Math.sin(h * 0.7)
  const nevera = Math.floor(t / 1200) % 2 === 0 ? 150 : 12 // ciclo del compresor de 20 min
  let aire = 0
  if (h >= d.aireDesde && h < d.aireHasta) aire = 980 + 280 * Math.sin(((h - d.aireDesde) / (d.aireHasta - d.aireDesde)) * Math.PI)
  else if (d.aireNoche && (h >= 23 || h < 5)) aire = 640
  if (aire && Math.floor(t / 900) % 4 === 3) aire *= 0.35 // el compresor del aire también cicla
  const cocina = d.cocina.some((c) => h > c && h < c + 0.9) ? 1350 : 0
  const tv = h > 19 && h < 23 ? 120 : 0
  const ch2 = aire * d.factor * (0.97 + 0.06 * ruido())
  const ch1 = Math.max(80, (base + nevera + tv + cocina) * d.factor + ch2 + (ruido() - 0.5) * 60)
  return { ch1, ch2 }
}

function registro(t: number): Registro {
  const { ch1, ch2 } = potencias(t)
  const h = ((t + ZONA) % 86400) / 3600
  const v = 120.3 + 1.8 * Math.sin(h / 3.5) + (ruido() - 0.5) * 0.6
  const fp1 = 0.88 + 0.05 * Math.sin(h / 2) + 0.01 * ruido()
  const fp2 = ch2 > 0 ? 0.86 + 0.02 * ruido() : 1
  const s1 = ch1 / fp1, s2 = ch2 / fp2
  return {
    t, v_rms: v,
    i_rms: [s1 / v, s2 / v, 0],
    p: [ch1, ch2, 0],
    q: [Math.sqrt(Math.max(0, s1 * s1 - ch1 * ch1)), Math.sqrt(Math.max(0, s2 * s2 - ch2 * ch2)), 0],
    s: [s1, s2, 0],
    fp: [fp1, fp2, 0],
    f: 60 + (ruido() - 0.5) * 0.04,
    thd: 6 + 4 * ruido() + (ch2 > 0 ? 2 : 0),
  }
}

async function enviar(rs: Registro[]) {
  const r = await fetch(`${URL_BASE}/api/ingesta`, {
    method: 'POST',
    headers: { 'content-type': 'application/octet-stream', 'x-nodo': NODO, 'x-firmware': 'fw-v1.0.0-sim' },
    body: codificarLote(rs) as Uint8Array<ArrayBuffer>,
  })
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`)
  return ((await r.json()) as { aceptados: number }).aceptados
}

async function main() {
  const ahora = Math.floor(Date.now() / 1000)
  if (DIAS > 0) {
    const desde = ahora - DIAS * 86400
    let lote: Registro[] = []
    let total = 0
    for (let t = desde; t < ahora; t += PASO) {
      lote.push(registro(t))
      if (lote.length === 1000) { total += await enviar(lote); lote = [] }
      if ((t - desde) % 86400 < PASO) process.stdout.write(`\rhistórico: día ${Math.floor((t - desde) / 86400) + 1}/${DIAS}`)
    }
    if (lote.length) total += await enviar(lote)
    console.log(`\nhistórico cargado: ${total} registros (uno cada ${PASO} s)`)
  }
  if (SOLO_HISTORICO) return
  console.log(`en vivo: un registro por segundo a ${URL_BASE}/api/ingesta como ${NODO} (Ctrl+C para salir)`)
  for (;;) {
    const t = Math.floor(Date.now() / 1000)
    try { await enviar([registro(t)]) } catch (e) { console.error((e as Error).message) }
    await new Promise((r) => setTimeout(r, 1000 - (Date.now() % 1000)))
  }
}

main().catch((e) => { console.error(e); process.exit(1) })
