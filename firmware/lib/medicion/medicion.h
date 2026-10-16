// Cálculo de magnitudes eléctricas sobre una ventana de ciclos enteros.
//
// No depende de Arduino: se compila igual en el ESP32 y en el PC (test/prueba_medicion.cpp).
// Entradas: códigos crudos del ADC (0..4095) de tensión y de dos corrientes, tomados en
// secuencia V → I1 → I2 en cada instante de muestreo.
#pragma once
#include <cmath>
#include <cstdint>

namespace medicion {

constexpr int N_CANALES = 2;
constexpr int N_ARMONICOS = 40;   // THD hasta el armónico 40 (2,4 kHz)

struct Calibracion {
  float voltios_por_codigo;        // escala del ADC (de esp_adc_cal en el ESP32)
  float k_v;                       // V de red por voltio en el pin
  float k_i[N_CANALES];            // A de primario por voltio en el pin
  // Fracción de periodo de muestreo (0..1) en que la tensión se interpola hacia el
  // instante de cada corriente: compensa el retardo del multiplexado y la fase de la pinza.
  float alfa[N_CANALES];
  float tau_filtro_s;              // constante de tiempo del antialias (compensación de THD)
  float ruido_i[N_CANALES];        // piso de ruido medido con la tara (A eficaces)
};

struct Resultado {
  float v_rms;
  float i_rms[N_CANALES];
  float p[N_CANALES];
  float q[N_CANALES];
  float s[N_CANALES];
  float fp[N_CANALES];
  float f_hz;
  float thd_i1;                    // en por ciento
  uint32_t muestras;
  bool valido;
};

class Ventana {
 public:
  Ventana(const Calibracion& cal, int ciclos, float fs_hz);
  void calibracion(const Calibracion& cal) { cal_ = cal; }

  // Agrega un juego de muestras. Devuelve true cuando la ventana se completó y
  // resultado() tiene un valor nuevo.
  bool muestra(int v, int i1, int i2);
  const Resultado& resultado() const { return res_; }
  // Frecuencia de muestreo real medida por el llamador (para la frecuencia de red).
  void fs_real(float fs) { fs_ = fs; }

 private:
  void reiniciar_sumas();
  void calcular();

  Calibracion cal_;
  int ciclos_;
  float fs_;

  // Detección de cruces por cero con histéresis sobre la tensión sin componente continua.
  float v_media_;                  // nivel de reposo estimado (códigos)
  bool positivo_ = false;
  bool sincronizada_ = false;
  int cruces_ = 0;
  int v_prev_ = 0;
  int i_prev_[N_CANALES] = {};
  bool hay_prev_ = false;

  // Sumas exactas en enteros: rms y potencia se calculan quitando la media de la ventana.
  int64_t n_ = 0;
  int64_t sv_ = 0, svv_ = 0;
  int64_t si_[N_CANALES] = {}, sii_[N_CANALES] = {};
  int64_t svi_[N_CANALES] = {}, sva_[N_CANALES] = {};

  // Goertzel sobre la corriente de CH1 para el THD.
  float coef_[N_ARMONICOS] = {};
  float s1_[N_ARMONICOS] = {}, s2_[N_ARMONICOS] = {};
  float f_red_ = 60.0f;
  float i_media_ = 1638.0f;        // reposo de CH1 estimado en la ventana anterior

  Resultado res_{};
};

}  // namespace medicion
