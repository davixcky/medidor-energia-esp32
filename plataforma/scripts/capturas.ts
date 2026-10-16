/**
 * Capturas del tablero con Chrome sin interfaz (playwright-core, sin descargar navegadores).
 * Requiere el servidor en marcha (pnpm start) con datos (pnpm simular --dias 21).
 *   node scripts/capturas.ts            # escribe en ../img/
 * CHROME=/ruta/al/navegador y URL=http://… cambian los valores por defecto.
 */
import { execFileSync } from 'node:child_process'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { chromium } from 'playwright-core'

const URL_BASE = process.env.URL ?? 'http://localhost:3000/'
const IMG = new URL('../../img/', import.meta.url).pathname
const navegador = await chromium.launch({ executablePath: process.env.CHROME ?? '/usr/bin/google-chrome-stable' })

async function captura(ruta: string, opc: { ancho: number; alto: number; tema: 'light' | 'dark'; escala?: number; seccion?: string; movil?: boolean }) {
  const ctx = await navegador.newContext({
    viewport: { width: opc.ancho, height: opc.alto }, deviceScaleFactor: opc.escala ?? 1, colorScheme: opc.tema,
    isMobile: opc.movil ?? false, hasTouch: opc.movil ?? false, locale: 'es-CO', timezoneId: 'America/Bogota',
  })
  const p = await ctx.newPage()
  await p.goto(`${URL_BASE}?tema=${opc.tema}`, { waitUntil: 'load' })
  await p.waitForSelector('.g24 .recharts-surface', { timeout: 15000 })
  if (opc.seccion) await p.locator(`#${opc.seccion}`).evaluate((e) => e.scrollIntoView({ block: 'start' }))
  await p.waitForTimeout(800)
  await p.screenshot({ path: ruta })
  await ctx.close()
}

await captura(join(IMG, 'ui-tablero-escritorio.png'), { ancho: 1440, alto: 900, tema: 'light' })
await captura(join(IMG, 'ui-tablero-oscuro.png'), { ancho: 1440, alto: 1240, tema: 'dark' })
const tmp = mkdtempSync(join(tmpdir(), 'capturas-'))
const secciones = ['', 'dia', 'alertas']
for (const [k, s] of secciones.entries()) {
  await captura(join(tmp, `m${k}.png`), { ancho: 390, alto: 844, tema: 'light', escala: 2, seccion: s || undefined, movil: true })
}
await navegador.close()
// Composición de las tres vistas móviles en marcos de teléfono (Pillow).
execFileSync('python3', ['-c', `
import sys
from PIL import Image, ImageDraw
tmp, salida = sys.argv[1], sys.argv[2]
ims = [Image.open(f"{tmp}/m{k}.png").convert("RGB") for k in range(3)]
w, h = ims[0].size
b, gap = 20, 56
lienzo = Image.new("RGB", (3 * (w + 2 * b) + 4 * gap, h + 2 * b + 2 * gap), "#dfe3e8")
d = ImageDraw.Draw(lienzo)
for k, im in enumerate(ims):
    x, y = gap + k * (w + 2 * b + gap), gap
    d.rounded_rectangle((x, y, x + w + 2 * b, y + h + 2 * b), radius=72, fill="#111")
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), radius=54, fill=255)
    lienzo.paste(im, (x + b, y + b), m)
lienzo.save(salida)
`, tmp, join(IMG, 'ui-tablero-movil.png')])
rmSync(tmp, { recursive: true })
console.log('capturas escritas en', IMG)
