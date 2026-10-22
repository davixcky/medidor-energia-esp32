// Prueba en el PC del cálculo de magnitudes: señales sintéticas con la misma cadena del
// hardware (pinza → burden → VBIAS → ADC de 12 bits) y comparación con los valores exactos.
//   make -C test
#include <cassert>
#include <cmath>
#include <cstdio>
#include <random>

#include "../lib/adr001/adr001.h"
#include "../lib/medicion/medicion.h"

using namespace medicion;
constexpr double PI = 3.14159265358979;

struct Caso {
  const char* nombre;
  double f, v_rms, v_h3;           // tensión y tercer armónico relativo
  double i1_rms, fp1, i1_h3;       // CH1: corriente fundamental, FP de desplazamiento, h3 relativo
  double i2_rms, fp2;
  bool compensar_multiplexado;
  double v_adelanto_grados = 0;    // fase propia del canal de tensión (ZMPT101B), se compensa
  bool sin_tension = false;        // ZMPT101B desconectado: el pin queda en 0 V
};

int fallas = 0;
void comprobar(const char* que, double medido, double esperado, double tol_rel, double tol_abs = 0) {
  double err = std::fabs(medido - esperado);
  bool ok = err <= std::max(tol_rel * std::fabs(esperado), tol_abs);
  std::printf("  %-26s medido %10.4f  esperado %10.4f  %s\n", que, medido, esperado, ok ? "OK" : "FALLA");
  if (!ok) ++fallas;
}

Resultado correr(const Caso& k, double* p1_exacta, double* p2_exacta, double* thd_exacto) {
  const double fs = 8000, q = 3.3 / 4095;      // escala del ADC usada en la prueba
  const double d1 = 12e-6, d2 = 24e-6;         // retardo de conversión de I1 e I2 tras V
  Calibracion cal{};
  cal.voltios_por_codigo = (float)q;
  cal.k_v = 482.0f;
  cal.k_i[0] = 2000.0f / 22;
  cal.k_i[1] = 2000.0f / 47;
  // Retardo en muestras: multiplexado (δ·fs) menos el adelanto del canal de tensión.
  const double adelanto_muestras = k.v_adelanto_grados / 360.0 / k.f * fs;
  cal.retardo[0] = k.compensar_multiplexado ? (float)(d1 * fs - adelanto_muestras) : 0.0f;
  cal.retardo[1] = k.compensar_multiplexado ? (float)(d2 * fs - adelanto_muestras) : 0.0f;
  cal.tau_filtro_s = 0.0f;                     // las señales sintéticas no pasan por el filtro
  Ventana w(cal, 60, (float)fs);

  std::mt19937 rng(1);
  std::normal_distribution<double> ruido(0.0, 0.7);   // ruido del ADC, 0,7 códigos eficaces
  auto adc = [&](double volt) {
    long c = std::lround(volt / q + ruido(rng));
    return (int)std::min(4095L, std::max(0L, c));
  };
  const double vpk = k.v_rms * std::sqrt(2.0), w0 = 2 * PI * k.f;
  const double ph1 = std::acos(k.fp1), ph2 = std::acos(k.fp2);
  auto v_de = [&](double t) { return vpk * (std::sin(w0 * t) + k.v_h3 * std::sin(3 * w0 * t)); };
  auto i1_de = [&](double t) {
    return k.i1_rms * std::sqrt(2.0) * (std::sin(w0 * t - ph1) + k.i1_h3 * std::sin(3 * w0 * t - 3 * ph1));
  };
  auto i2_de = [&](double t) { return k.i2_rms * std::sqrt(2.0) * std::sin(w0 * t - ph2); };
  // Potencias exactas: P = V1·I1·cos φ1 + V3·I3·cos φ3 (la tensión también tiene h3).
  *p1_exacta = k.v_rms * k.i1_rms * (k.fp1 + k.v_h3 * k.i1_h3 * std::cos(3 * ph1));
  *p2_exacta = k.v_rms * k.i2_rms * k.fp2;
  *thd_exacto = 100 * k.i1_h3;

  Resultado ultimo{};
  int ventanas = 0;
  for (long n = 0; n < (long)(fs * 4); ++n) {
    double t = n / fs;
    // El canal de tensión adelanta: el pin muestra la tensión de un instante posterior.
    const double t_v = t + k.v_adelanto_grados / 360.0 / k.f;
    int v = k.sin_tension ? adc(0.0) : adc(1.35 + v_de(t_v) / cal.k_v);
    int i1 = adc(1.32 + i1_de(t + d1) / cal.k_i[0]);
    int i2 = adc(1.32 + i2_de(t + d2) / cal.k_i[1]);
    if (w.muestra(v, i1, i2) && ++ventanas >= 2) ultimo = w.resultado();  // la primera estima el reposo
  }
  return ultimo;
}

int main() {
  const Caso casos[] = {
      {"Carga resistiva, 60 Hz", 60.0, 120, 0.0, 10.0, 1.0, 0.0, 3.0, 1.0, true},
      {"Motor FP 0,8 + armónicos", 60.0, 121, 0.025, 20.0, 0.8, 0.30, 5.0, 0.6, true},
      {"Red a 59,8 Hz, carga baja", 59.8, 118, 0.0, 1.0, 0.95, 0.0, 0.5, 1.0, true},
      {"Sin compensar multiplexado", 60.0, 120, 0.0, 20.0, 0.5, 0.0, 5.0, 0.5, false},
      {"ZMPT adelanta 6°, compensado", 60.0, 120, 0.0, 15.0, 0.8, 0.0, 5.0, 0.6, true, 6.0},
      {"ZMPT desconectado", 60.0, 0, 0.0, 10.0, 1.0, 0.0, 3.0, 1.0, true, 0.0, true},
  };
  for (const auto& k : casos) {
    double p1, p2, thd;
    Resultado r = correr(k, &p1, &p2, &thd);
    std::printf("%s (%u muestras por ventana)\n", k.nombre, r.muestras);
    double v_esp = k.v_rms * std::sqrt(1 + k.v_h3 * k.v_h3);
    double i1_esp = k.i1_rms * std::sqrt(1 + k.i1_h3 * k.i1_h3);
    comprobar("V eficaz (V)", r.v_rms, v_esp, 0.005);
    comprobar("I eficaz CH1 (A)", r.i_rms[0], i1_esp, 0.01, 0.05);
    comprobar("I eficaz CH2 (A)", r.i_rms[1], k.i2_rms, 0.01, 0.05);
    if (k.sin_tension) {
      // Sin tensión no hay cruces: ventanas de longitud fija, solo corriente.
      comprobar("Frecuencia (0 = sin red)", r.f_hz, 0.0, 0.0, 0.001);
      comprobar("P CH1 (W)", r.p[0], 0.0, 0.0, 0.001);
      continue;
    }
    if (k.compensar_multiplexado) {
      comprobar("P CH1 (W)", r.p[0], p1, 0.01, 6);
      comprobar("P CH2 (W)", r.p[1], p2, 0.01, 6);
    } else {
      double e = 100 * (r.p[0] - p1) / p1;
      std::printf("  error de P CH1 sin compensar: %.2f %% (se espera > 0,5 %% con FP 0,5)\n", e);
      if (std::fabs(e) < 0.5) ++fallas;
    }
    comprobar("Frecuencia (Hz)", r.f_hz, k.f, 0.0, 0.02);
    if (k.i1_rms > 5) comprobar("THD CH1 (%)", r.thd_i1, thd, 0.0, 0.5);
  }
  // Codificación ADR-001
  adr001::Registro reg{1760630400u, 120.37f, {12.76f, 3.01f, 0}, {1362, 330, 0}, {660, 0, 0},
                       {1513, 362, 0}, {0.9001f, 0.912f, 1.0f}, 60.01f, 7.8f};
  uint8_t b[adr001::TAMANO];
  adr001::codificar(reg, b);
  auto le16 = [&](int off) { return (int16_t)(b[off] | (b[off + 1] << 8)); };
  uint32_t t = b[0] | (b[1] << 8) | (b[2] << 16) | ((uint32_t)b[3] << 24);
  bool ok = t == 1760630400u && le16(4) == 12037 && le16(6) == 1276 && le16(12) == 1362 &&
            le16(30) == 9001 && le16(36) == 6001 && le16(38) == 780;
  std::printf("Codificación ADR-001 de 40 B: %s\n", ok ? "OK" : "FALLA");
  if (!ok) ++fallas;
  std::printf("\n%s (%d fallas)\n", fallas ? "HAY FALLAS" : "TODAS LAS PRUEBAS PASAN", fallas);
  return fallas ? 1 : 0;
}
