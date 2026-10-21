import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest'
import type { Registro } from '../src/server/adr001'
import { cerrar, migrar, sql } from '../src/server/db'
import { alertas, cambiarEstado, energia, ingerir, pronostico, reiniciarEstado, umbrales } from '../src/server/servicio'

const reg = (t: number, p1: number, p2 = 0): Registro => ({
  t, v_rms: 120, i_rms: [p1 / 120, p2 / 120, 0], p: [p1, p2, 0], q: [0, 0, 0], s: [p1, p2, 0], fp: [1, 1, 0], f: 60, thd: 5,
})
const T0 = 1_790_000_000 - (1_790_000_000 % 86400) + 5 * 3600 // medianoche en Colombia

// Necesitan un Postgres: DATABASE_URL de un proyecto de Supabase de pruebas o un Postgres local
// (ver README). Sin DATABASE_URL se omiten.
const conBase = describe.skipIf(!process.env.DATABASE_URL)
async function vaciar() {
  await sql()`TRUNCATE registros, horas, umbrales, alertas RESTART IDENTITY`
  reiniciarEstado()
}
beforeAll(async () => { if (process.env.DATABASE_URL) await migrar() })
afterAll(async () => { if (process.env.DATABASE_URL) await cerrar() })

conBase('servicio', () => {
  beforeEach(vaciar)

  it('integra la energía: 1000 W durante una hora = 1 kWh', async () => {
    const rs = Array.from({ length: 3601 }, (_, k) => reg(T0 + k, 1000, 500))
    expect(await ingerir('n', 'fw', rs)).toBe(3601)
    const e = (await energia('n'))!
    expect(e.hoy.kwh1).toBeCloseTo(1, 2)
    expect(e.hoy.kwh2).toBeCloseTo(0.5, 2)
  })

  it('ignora registros repetidos (reenvíos del firmware)', async () => {
    await ingerir('n', 'fw', [reg(T0, 100), reg(T0 + 1, 100)])
    expect(await ingerir('n', 'fw', [reg(T0 + 1, 100), reg(T0 + 2, 100)])).toBe(1)
  })

  it('calcula el P95 y abre una alerta tras 5 min sostenidos sobre el umbral', async () => {
    // Dos días a 500 W con 10 s entre registros, luego 10 min a 3000 W.
    const rs: Registro[] = []
    for (let t = T0; t < T0 + 2 * 86400; t += 10) rs.push(reg(t, 500))
    for (let t = T0 + 2 * 86400; t < T0 + 2 * 86400 + 600; t += 10) rs.push(reg(t, 3000))
    rs.push(reg(T0 + 2 * 86400 + 610, 500))
    await ingerir('n', 'fw', rs)
    expect((await umbrales('n'))[0].valor).toBe(500)
    const a = await alertas('n')
    expect(a).toHaveLength(1)
    expect(a[0]).toMatchObject({ canal: 1, pico: 3000, estado: 'notificada', inicio: T0 + 2 * 86400, fin: T0 + 2 * 86400 + 590 })
    expect(await cambiarEstado(a[0].id, 'revisada')).toBe(true)
    await expect(cambiarEstado(a[0].id, 'otra')).rejects.toThrow()
  })

  it('pronostica 48 h cuando hay 24 horas completas', async () => {
    const rs: Registro[] = []
    for (let t = T0; t < T0 + 26 * 3600; t += 10) rs.push(reg(t, 800 + 400 * Math.sin(t / 7200)))
    await ingerir('n', 'fw', rs)
    const p = (await pronostico('n')) as { disponible: boolean; horas: { kwh: number; min: number; max: number }[] }
    expect(p.disponible).toBe(true)
    expect(p.horas).toHaveLength(48)
    for (const h of p.horas) { expect(h.kwh).toBeGreaterThanOrEqual(0); expect(h.max).toBeGreaterThan(h.min) }
  })
})

conBase('agrupaciones', () => {
  beforeEach(vaciar)
  it('agrupa la serie en intervalos de 5 min y la energía por día local', async () => {
    const { serie } = await import('../src/server/servicio')
    const rs: Registro[] = []
    for (let t = T0; t < T0 + 2 * 86400; t += 10) rs.push(reg(t, 1000))
    await ingerir('n', 'fw', rs)
    expect(await serie('n', 24, 300)).toHaveLength(288)
    const e = (await energia('n'))!
    const dias = e.mes.dias.map((x) => x.dia)
    expect(new Set(dias).size).toBe(dias.length) // un elemento por día
    expect(e.mes.dias.at(-2)!.kwh1).toBeCloseTo(24, 1) // día completo a 1 kW
  })
})
