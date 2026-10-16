#include "medicion.h"

namespace medicion {

namespace {
constexpr float PI_F = 3.14159265358979f;
constexpr int HISTERESIS = 40;      // códigos (≈ 32 mV en el pin)
}  // namespace

Ventana::Ventana(const Calibracion& cal, int ciclos, float fs_hz)
    : cal_(cal), ciclos_(ciclos), fs_(fs_hz), v_media_(1640.0f) {
  reiniciar_sumas();
}

void Ventana::reiniciar_sumas() {
  n_ = sv_ = svv_ = 0;
  for (int c = 0; c < N_CANALES; ++c) si_[c] = sii_[c] = svi_[c] = sva_[c] = 0;
  for (int h = 0; h < N_ARMONICOS; ++h) {
    float w = 2.0f * PI_F * (h + 1) * f_red_ / fs_;
    coef_[h] = 2.0f * std::cos(w);
    s1_[h] = s2_[h] = 0.0f;
  }
}

bool Ventana::muestra(int v, int i1, int i2) {
  if (!hay_prev_) {
    v_prev_ = v;
    i_prev_[0] = i1;
    i_prev_[1] = i2;
    hay_prev_ = true;
    return false;
  }
  // Cruce por cero ascendente con histéresis.
  bool cruce = false;
  float x = v - v_media_;
  if (!positivo_ && x > HISTERESIS) {
    positivo_ = true;
    cruce = true;
  } else if (positivo_ && x < -HISTERESIS) {
    positivo_ = false;
  }

  bool lista = false;
  if (cruce) {
    if (!sincronizada_) {
      sincronizada_ = true;
      cruces_ = 0;
      reiniciar_sumas();
    } else if (++cruces_ >= ciclos_) {
      // La ventana termina justo antes de esta muestra, que abre la siguiente.
      calcular();
      cruces_ = 0;
      reiniciar_sumas();
      lista = true;
    }
  }

  if (sincronizada_) {
    ++n_;
    sv_ += v;
    svv_ += (int64_t)v * v;
    // Orden de conversión: V(t), I1(t + δ1), I2(t + δ2). La corriente del instante anterior
    // cae entre v_prev_ y v, así que se empareja con la tensión interpolada en
    // t − Ts + δ, es decir, con alfa = δ / Ts (punto fijo de 8 bits).
    const int ii[N_CANALES] = {i_prev_[0], i_prev_[1]};
    for (int c = 0; c < N_CANALES; ++c) {
      int a = (int)std::lround(cal_.alfa[c] * 256.0f);
      int va = (v_prev_ * (256 - a) + v * a) >> 8;
      si_[c] += ii[c];
      sii_[c] += (int64_t)ii[c] * ii[c];
      svi_[c] += (int64_t)va * ii[c];
      sva_[c] += va;
    }
    // Sin la componente continua: con el reposo de 1,32 V el Goertzel en float pierde
    // precisión y aparece un THD falso del orden del 1 %.
    float xi = (float)ii[0] - i_media_;
    for (int h = 0; h < N_ARMONICOS; ++h) {
      float s0 = xi + coef_[h] * s1_[h] - s2_[h];
      s2_[h] = s1_[h];
      s1_[h] = s0;
    }
  }
  v_prev_ = v;
  i_prev_[0] = i1;
  i_prev_[1] = i2;
  return lista;
}

void Ventana::calcular() {
  Resultado r{};
  r.muestras = (uint32_t)n_;
  if (n_ < 100) {
    res_ = r;
    return;
  }
  const double n = (double)n_;
  const double q = cal_.voltios_por_codigo;
  const double mv = sv_ / n;
  const double var_v = svv_ / n - mv * mv;
  v_media_ = (float)mv;  // la siguiente ventana detecta cruces sobre el reposo actualizado
  r.v_rms = (float)(std::sqrt(var_v > 0 ? var_v : 0) * q * cal_.k_v);

  i_media_ = (float)(si_[0] / n);
  for (int c = 0; c < N_CANALES; ++c) {
    const double mi = si_[c] / n;
    const double ma = sva_[c] / n;
    double var_i = sii_[c] / n - mi * mi;
    double i_rms = std::sqrt(var_i > 0 ? var_i : 0) * q * cal_.k_i[c];
    // Tara: el piso de ruido se resta en cuadratura.
    double ruido = cal_.ruido_i[c];
    i_rms = i_rms > ruido ? std::sqrt(i_rms * i_rms - ruido * ruido) : 0.0;
    double p = (svi_[c] / n - ma * mi) * q * q * cal_.k_v * cal_.k_i[c];
    double s = r.v_rms * i_rms;
    if (i_rms == 0.0) p = 0.0;
    if (std::fabs(p) > s) p = (p > 0 ? s : -s);
    r.i_rms[c] = (float)i_rms;
    r.p[c] = (float)p;
    r.s[c] = (float)s;
    r.q[c] = (float)std::sqrt(s * s - p * p);
    r.fp[c] = s > 0 ? (float)(p / s) : 1.0f;
  }

  // Frecuencia de red: ciclos completos sobre la duración de la ventana.
  r.f_hz = (float)(ciclos_ * fs_ / n);
  if (r.f_hz > 45.0f && r.f_hz < 65.0f) f_red_ = r.f_hz;

  // THD de la corriente de CH1, compensando la atenuación del filtro antialias.
  double a1 = 0, suma = 0;
  for (int h = 0; h < N_ARMONICOS; ++h) {
    float w = 2.0f * PI_F * (h + 1) * f_red_ / fs_;
    double re = s1_[h] - s2_[h] * std::cos(w);
    double im = s2_[h] * std::sin(w);
    double mag = std::sqrt(re * re + im * im);
    double wt = 2.0 * PI_F * (h + 1) * f_red_ * cal_.tau_filtro_s;
    mag *= std::sqrt(1.0 + wt * wt);
    if (h == 0) a1 = mag; else suma += mag * mag;
  }
  r.thd_i1 = (a1 > 0 && r.i_rms[0] > 0.2f) ? (float)(100.0 * std::sqrt(suma) / a1) : 0.0f;
  r.valido = true;
  res_ = r;
}

}  // namespace medicion
