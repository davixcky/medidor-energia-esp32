import { describe, expect, it } from 'vitest'
import { type Registro, TAMANO_REGISTRO, codificarLote, decodificarLote, validar } from '../src/server/adr001'

const ejemplo: Registro = {
  t: 1_792_000_000, v_rms: 120.37, i_rms: [12.76, 11.04, 0], p: [1362, 1154, 0], q: [658, 593, 0],
  s: [1517, 1311, 0], fp: [0.8978, -0.8803, 0], f: 60.01, thd: 7.82,
}

describe('ADR-001', () => {
  it('ocupa 40 B con los desplazamientos del firmware', () => {
    const u8 = codificarLote([ejemplo])
    expect(u8.byteLength).toBe(TAMANO_REGISTRO)
    const dv = new DataView(u8.buffer)
    expect(dv.getUint32(0, true)).toBe(1_792_000_000)
    expect(dv.getInt16(4, true)).toBe(12037) // 0,01 V
    expect(dv.getInt16(6, true)).toBe(1276) // i_rms[0], 0,01 A
    expect(dv.getInt16(12, true)).toBe(1362) // p[0], W
    expect(dv.getInt16(18, true)).toBe(658) // q[0], var
    expect(dv.getInt16(24, true)).toBe(1517) // s[0], VA
    expect(dv.getInt16(30, true)).toBe(8978) // fp[0], 0,0001
    expect(dv.getInt16(32, true)).toBe(-8803) // fp[1] con signo
    expect(dv.getInt16(36, true)).toBe(6001) // f, 0,01 Hz
    expect(dv.getInt16(38, true)).toBe(782) // thd, 0,01 %
  })

  it('decodifica varios registros concatenados', () => {
    const u8 = codificarLote([ejemplo, { ...ejemplo, t: ejemplo.t + 1 }, { ...ejemplo, t: ejemplo.t + 2 }])
    const rs = decodificarLote(u8)
    expect(rs).toHaveLength(3)
    expect(rs[2].t).toBe(ejemplo.t + 2)
    expect(rs[1].v_rms).toBeCloseTo(120.37, 2)
    expect(rs[1].fp[1]).toBeCloseTo(-0.8803, 4)
    expect(rs[0].thd).toBeCloseTo(7.82, 2)
  })

  it('rechaza cuerpos que no son múltiplo de 40 B y valores imposibles', () => {
    expect(() => decodificarLote(new Uint8Array(41))).toThrow()
    expect(validar(ejemplo)).toBeNull()
    expect(validar({ ...ejemplo, f: 90 })).toMatch(/f fuera/)
    expect(validar({ ...ejemplo, t: 5 })).toMatch(/NTP/)
  })
})
