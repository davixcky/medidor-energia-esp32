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
import { registro } from '../src/server/simulador.ts'

const arg = (n: string, d?: string) => {
  const i = process.argv.indexOf(`--${n}`)
  return i >= 0 ? (process.argv[i + 1] ?? '') : d
}
const URL_BASE = arg('url', 'http://localhost:3000')!
const NODO = arg('nodo', 'nodo01')!
const DIAS = Number(arg('dias', '0'))
const PASO = Number(arg('paso', '10'))
const SOLO_HISTORICO = process.argv.includes('--solo-historico')

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
