import { describe, expect, it } from 'vitest'
import caso from '../src/server/lstm-caso-prueba.json'
import { recursivo, unPaso } from '../src/server/lstm'

describe('LSTM en TypeScript frente a PyTorch', () => {
  it('un paso coincide con PyTorch (tolerancia 1e-4)', () => {
    expect(Math.abs(unPaso(caso.entrada.slice(0, 24)) - caso.un_paso)).toBeLessThan(1e-4)
  })
  it('el pronóstico recursivo de 48 h coincide con PyTorch (tolerancia 1e-4)', () => {
    const ts = recursivo(caso.entrada, 48)
    const peor = Math.max(...ts.map((z, k) => Math.abs(z - caso.recursivo[k])))
    expect(peor).toBeLessThan(1e-4)
  })
})
