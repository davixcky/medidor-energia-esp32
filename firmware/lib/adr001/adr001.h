// Contrato de datos ADR-001: registro de 40 bytes, little-endian, sin relleno.
// Es la única interfaz entre el medidor y la plataforma (POST /api/ingesta).
//
//  offset  tipo      campo        escala
//   0      uint32    t            s (tiempo Unix UTC)
//   4      int16     v_rms        0,01 V
//   6      int16[3]  i_rms        0,01 A     (CH1, CH2, CH3 de reserva)
//  12      int16[3]  p            1 W
//  18      int16[3]  q            1 var
//  24      int16[3]  s            1 VA
//  30      int16[3]  fp           0,0001
//  36      int16     f            0,01 Hz
//  38      int16     thd          0,01 %     (corriente de CH1)
#pragma once
#include <cmath>
#include <cstdint>
#include <cstring>

namespace adr001 {

constexpr size_t TAMANO = 40;

struct Registro {
  uint32_t t;
  float v_rms;
  float i_rms[3];
  float p[3], q[3], s[3], fp[3];
  float f_hz;
  float thd;
};

inline int16_t a16(float x, float escala) {
  float y = std::round(x / escala);
  if (y > 32767.0f) y = 32767.0f;
  if (y < -32768.0f) y = -32768.0f;
  return (int16_t)y;
}

inline void poner16(uint8_t* b, size_t off, int16_t v) {
  b[off] = (uint8_t)(v & 0xFF);
  b[off + 1] = (uint8_t)((uint16_t)v >> 8);
}

inline void codificar(const Registro& r, uint8_t* b) {
  b[0] = r.t & 0xFF;
  b[1] = (r.t >> 8) & 0xFF;
  b[2] = (r.t >> 16) & 0xFF;
  b[3] = (r.t >> 24) & 0xFF;
  poner16(b, 4, a16(r.v_rms, 0.01f));
  for (int c = 0; c < 3; ++c) {
    poner16(b, 6 + 2 * c, a16(r.i_rms[c], 0.01f));
    poner16(b, 12 + 2 * c, a16(r.p[c], 1.0f));
    poner16(b, 18 + 2 * c, a16(r.q[c], 1.0f));
    poner16(b, 24 + 2 * c, a16(r.s[c], 1.0f));
    poner16(b, 30 + 2 * c, a16(r.fp[c], 0.0001f));
  }
  poner16(b, 36, a16(r.f_hz, 0.01f));
  poner16(b, 38, a16(r.thd, 0.01f));
}

}  // namespace adr001
