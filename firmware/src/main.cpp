// Firmware del medidor de energía de dos canales (ESP32-DevKitC V4).
//
// Núcleo 1: tarea de adquisición. Muestrea V, I1 e I2 a 8 kS/s por canal y calcula una
// ventana de 60 ciclos (≈ 1 s). Solo entrega resultados por cola: nunca toca la red.
// Núcleo 0: red (Wi-Fi, NTP, POST de registros ADR-001 en lotes), pantalla LCD, pulsadores
// y LED de estado.
#include <Adafruit_ST7789.h>
#include <Arduino.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <WiFi.h>
#include <SPI.h>
#include <esp_adc_cal.h>
#include <esp_timer.h>
#include <time.h>

#include "adr001.h"
#include "config.h"
#include "interfaz.h"
#include "medicion.h"
#include "secretos.h"

#ifndef FW_VERSION
#define FW_VERSION "fw-v1.0.0"
#endif

// ---------------------------------------------------------------- estado compartido
static QueueHandle_t cola_resultados;            // adquisición → red
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
static medicion::Resultado ultimo{};             // copia para la pantalla
static medicion::Calibracion cal{};
static volatile bool pedir_tara = false;
static volatile int canal_tara = 0;

static double energia_hoy_wh = 0;
static float energia_hora_wh[24] = {};
static int hora_actual = -1;
static int dia_actual = -1;
static uint32_t inicio_alerta = 0;
static bool alerta_activa = false, alerta_reconocida = false;
static uint32_t ultimo_envio_ok = 0;
static int rssi = 0;

// Búfer circular de registros codificados, para no perder datos sin red.
static uint8_t bufer[BUFER_REGISTROS][adr001::TAMANO];
static size_t cabeza = 0, cantidad = 0;

Adafruit_ST7789 lcd(PIN_LCD_CS, PIN_LCD_DC, PIN_LCD_RST);
constexpr int16_t ALTO_FRANJA = 34;   // 5 franjas de 34 filas = 170 filas; 21,8 kB de RAM
static interfaz::Franja franja(ALTO_FRANJA);
Preferences prefs;

// ---------------------------------------------------------------- adquisición (núcleo 1)
static void tarea_adquisicion(void*) {
  medicion::Ventana ventana(cal, CICLOS_VENTANA, (float)FS_HZ);
  const int64_t periodo = 1000000LL / FS_HZ;
  int64_t proximo = esp_timer_get_time();
  int64_t t_ventana = proximo;
  uint32_t n_ventana = 0;
  const int64_t arranque = proximo + DESCARTE_MS * 1000LL;
  for (;;) {
    proximo += periodo;
    int64_t ahora;
    while ((ahora = esp_timer_get_time()) < proximo) {
    }
    if (ahora - proximo > 1000) proximo = ahora;   // se perdió el ritmo: resincroniza
    int v = adc1_get_raw(ADC_V);
    int i1 = adc1_get_raw(ADC_CH1);
    int i2 = adc1_get_raw(ADC_CH2);
    ++n_ventana;
    if (ahora < arranque) continue;
    if (ventana.muestra(v, i1, i2)) {
      // Frecuencia de muestreo real de la ventana que terminó (corrige la frecuencia de red).
      float fs_real = n_ventana * 1e6f / (float)(ahora - t_ventana);
      ventana.fs_real(fs_real);
      t_ventana = ahora;
      n_ventana = 0;
      medicion::Resultado r = ventana.resultado();
      xQueueSend(cola_resultados, &r, 0);
      if (pedir_tara) {   // el piso de ruido es la corriente medida sin carga
        cal.ruido_i[canal_tara] = sqrtf(r.i_rms[canal_tara] * r.i_rms[canal_tara] +
                                        cal.ruido_i[canal_tara] * cal.ruido_i[canal_tara]);
        ventana.calibracion(cal);
        pedir_tara = false;
      }
    }
  }
}

// Mide cuánto tarda una conversión para interpolar la tensión al instante de cada corriente.
static void medir_retardo_multiplexado() {
  const int N = 2000;
  int64_t t0 = esp_timer_get_time();
  for (int k = 0; k < N; ++k) adc1_get_raw(ADC_CH1);
  float t_conv = (esp_timer_get_time() - t0) / (float)N * 1e-6f;
  float ts = 1.0f / FS_HZ;
  float grados_a_fraccion = 1.0f / 360.0f / 60.0f / ts;   // grados a 60 Hz → fracción de Ts
  cal.alfa[0] = t_conv / ts + FASE_CT1_GRADOS * grados_a_fraccion;
  cal.alfa[1] = 2 * t_conv / ts + FASE_CT2_GRADOS * grados_a_fraccion;
  for (float& a : cal.alfa) a = constrain(a, 0.0f, 1.0f);
  Serial.printf("Conversión ADC: %.1f us; alfa CH1 %.3f, CH2 %.3f\n", t_conv * 1e6f, cal.alfa[0], cal.alfa[1]);
}

// ---------------------------------------------------------------- red (núcleo 0)
static void guardar_registro(const medicion::Resultado& r) {
  adr001::Registro reg{};
  reg.t = (uint32_t)time(nullptr);
  reg.v_rms = r.v_rms;
  for (int c = 0; c < 2; ++c) {
    reg.i_rms[c] = r.i_rms[c];
    reg.p[c] = r.p[c];
    reg.q[c] = r.q[c];
    reg.s[c] = r.s[c];
    reg.fp[c] = r.fp[c];
  }
  reg.fp[2] = 1.0f;
  reg.f_hz = r.f_hz;
  reg.thd = r.thd_i1;
  size_t pos = (cabeza + cantidad) % BUFER_REGISTROS;
  if (cantidad == BUFER_REGISTROS) cabeza = (cabeza + 1) % BUFER_REGISTROS;   // descarta el más viejo
  else ++cantidad;
  adr001::codificar(reg, bufer[pos]);
}

static void enviar_lote() {
  if (WiFi.status() != WL_CONNECTED || cantidad == 0 || time(nullptr) < 1700000000) return;
  const size_t max_lote = 60;
  size_t n = cantidad < max_lote ? cantidad : max_lote;
  static uint8_t cuerpo[max_lote * adr001::TAMANO];
  for (size_t k = 0; k < n; ++k)
    memcpy(cuerpo + k * adr001::TAMANO, bufer[(cabeza + k) % BUFER_REGISTROS], adr001::TAMANO);
  HTTPClient http;
  http.setTimeout(4000);
  http.begin(SERVIDOR_URL);
  http.addHeader("Content-Type", "application/octet-stream");
  http.addHeader("X-Nodo", NODO_ID);
  http.addHeader("X-Firmware", FW_VERSION);
  int codigo = http.POST(cuerpo, n * adr001::TAMANO);
  http.end();
  if (codigo == 200) {
    cabeza = (cabeza + n) % BUFER_REGISTROS;
    cantidad -= n;
    ultimo_envio_ok = millis();
  } else {
    Serial.printf("POST falló: %d\n", codigo);
  }
}

static void actualizar_energia_y_alerta(const medicion::Resultado& r) {
  time_t t = time(nullptr);
  struct tm local;
  localtime_r(&t, &local);
  if (t > 1700000000 && local.tm_yday != dia_actual) {
    dia_actual = local.tm_yday;
    energia_hoy_wh = 0;
    for (float& e : energia_hora_wh) e = 0;
  }
  double wh = r.p[0] * (r.muestras / (float)FS_HZ) / 3600.0;
  energia_hoy_wh += wh;
  if (t > 1700000000) {
    hora_actual = local.tm_hour;
    energia_hora_wh[hora_actual] += wh;
  }
  if (r.p[0] > UMBRAL_ALERTA_W) {
    if (inicio_alerta == 0) inicio_alerta = millis();
    if (!alerta_activa && millis() - inicio_alerta >= ALERTA_SOSTENIDA_S * 1000UL) {
      alerta_activa = true;
      alerta_reconocida = false;
    }
  } else {
    inicio_alerta = 0;
    alerta_activa = false;
  }
}

static void tarea_red(void*) {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_CLAVE);
  configTzTime("COT5", "pool.ntp.org", "time.google.com");   // Colombia, UTC−5
  uint32_t ultimo_lote = 0;
  for (;;) {
    medicion::Resultado r;
    while (xQueueReceive(cola_resultados, &r, pdMS_TO_TICKS(100)) == pdTRUE) {
      if (!r.valido) continue;
      portENTER_CRITICAL(&mux);
      ultimo = r;
      portEXIT_CRITICAL(&mux);
      actualizar_energia_y_alerta(r);
      guardar_registro(r);
    }
    if (WiFi.status() != WL_CONNECTED) {
      static uint32_t ultimo_intento = 0;
      if (millis() - ultimo_intento > 10000) {
        ultimo_intento = millis();
        WiFi.reconnect();
      }
    } else {
      rssi = WiFi.RSSI();
    }
    if (millis() - ultimo_lote >= ENVIO_CADA_MS) {
      ultimo_lote = millis();
      enviar_lote();
    }
  }
}

// ---------------------------------------------------------------- interfaz local (núcleo 0)
using interfaz::Pantalla;
static Pantalla pantalla = interfaz::RESUMEN;
static uint32_t ultima_pulsacion = 0;

static void dibujar(const medicion::Resultado& r) {
  interfaz::Datos d{};
  d.r = r;
  d.energia_hoy_kwh = energia_hoy_wh / 1000.0;
  for (int h = 0; h < 24; ++h) d.energia_hora_kwh[h] = energia_hora_wh[h] / 1000.0f;
  d.hora = hora_actual;
  d.wifi = WiFi.status() == WL_CONNECTED;
  d.rssi = rssi;
  d.servidor_ok = millis() - ultimo_envio_ok < 15000;
  d.bufer = cantidad;
  d.umbral_w = UMBRAL_ALERTA_W;
  d.alerta_min = inicio_alerta ? (millis() - inicio_alerta) / 60000 : 0;
  d.canal_tara = canal_tara;
  d.ruido_tara = cal.ruido_i[canal_tara];
  d.version = FW_VERSION;
  // Se dibuja la pantalla completa en cada franja y se envía solo la parte que le toca.
  for (int16_t y0 = 0; y0 < interfaz::ALTO; y0 += ALTO_FRANJA) {
    franja.origen(y0);
    interfaz::dibujar(franja, pantalla, d);
    lcd.drawRGBBitmap(0, y0, franja.getBuffer(), interfaz::ANCHO, ALTO_FRANJA);
  }
}

static void luz_fondo(bool encendida) { ledcWrite(0, encendida ? 200 : 0); }

struct Boton {
  explicit Boton(int p) : pin(p) {}
  int pin;
  bool antes = true;
  uint32_t desde = 0;
  bool largo_emitido = false;
};

// Devuelve 1 en pulsación corta (al soltar), 2 al cumplir 2 s sostenido, 0 si nada.
static int leer(Boton& b) {
  bool ahora = digitalRead(b.pin);   // activo en bajo; el RC de 100 nF filtra el rebote
  int evento = 0;
  if (b.antes && !ahora) {
    b.desde = millis();
    b.largo_emitido = false;
  } else if (!b.antes && !ahora && !b.largo_emitido && millis() - b.desde >= 2000) {
    b.largo_emitido = true;
    evento = 2;
  } else if (!b.antes && ahora && !b.largo_emitido && millis() - b.desde > 30) {
    evento = 1;
  }
  b.antes = ahora;
  return evento;
}

static void tarea_interfaz(void*) {
  using namespace interfaz;
  Boton sw1(PIN_SW1), sw2(PIN_SW2);
  bool apagada = false;
  uint32_t ultimo_dibujo = 0;
  for (;;) {
    int e1 = leer(sw1), e2 = leer(sw2);
    if (e1 || e2) {
      ultima_pulsacion = millis();
      if (apagada) {
        apagada = false;
        luz_fondo(true);
        e1 = e2 = 0;
      }
    }
    if (pantalla == ALERTA) {
      if (e2 == 1) {
        alerta_reconocida = true;
        pantalla = RESUMEN;
      }
    } else if (pantalla == TARA) {
      if (e1 == 1) pantalla = canal_tara == 0 ? CH1 : CH2;
      if (e2 == 2) {
        pedir_tara = true;
        while (pedir_tara) vTaskDelay(pdMS_TO_TICKS(50));
        prefs.putFloat(canal_tara == 0 ? "ruido1" : "ruido2", cal.ruido_i[canal_tara]);
      }
    } else {
      if (e1 == 1) pantalla = (Pantalla)((pantalla + 1) % N_CICLO);
      if (e2 == 2 && (pantalla == CH1 || pantalla == CH2)) {
        canal_tara = pantalla == CH1 ? 0 : 1;
        pantalla = TARA;
      }
      if (alerta_activa && !alerta_reconocida) pantalla = ALERTA;
    }
    if (!apagada && millis() - ultima_pulsacion > 60000 && pantalla != ALERTA) {
      apagada = true;
      luz_fondo(false);
    }
    // LED: fijo = servidor al día, 1 Hz = sin red, 5 Hz = alerta sin reconocer.
    uint32_t m = millis();
    bool led;
    if (alerta_activa && !alerta_reconocida) led = (m / 100) % 2;
    else if (m - ultimo_envio_ok < 15000) led = true;
    else led = (m / 500) % 2;
    digitalWrite(PIN_LED, led);
    if (!apagada && m - ultimo_dibujo > 500) {
      ultimo_dibujo = m;
      medicion::Resultado r;
      portENTER_CRITICAL(&mux);
      r = ultimo;
      portEXIT_CRITICAL(&mux);
      dibujar(r);
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

// ---------------------------------------------------------------- arranque
void setup() {
  Serial.begin(115200);
  Serial.printf("\nMedidor de energía %s\n", FW_VERSION);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_SW1, INPUT);   // pull-up externo de 10 kΩ
  pinMode(PIN_SW2, INPUT);

  adc1_config_width(ADC_WIDTH_BIT_12);
  for (adc1_channel_t ch : {ADC_CH1, ADC_CH2, ADC_V}) adc1_config_channel_atten(ch, ADC_ATTEN_DB_12);
  esp_adc_cal_characteristics_t car;
  esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN_DB_12, ADC_WIDTH_BIT_12, 1100, &car);
  // Pendiente de la recta de calibración del eFuse (mV por código, escalada por 65536).
  cal.voltios_por_codigo = car.coeff_a / 65536.0f / 1000.0f;
  cal.k_v = K_V;
  cal.k_i[0] = K_I1;
  cal.k_i[1] = K_I2;
  cal.tau_filtro_s = TAU_FILTRO_S;
  prefs.begin("medidor", false);
  cal.ruido_i[0] = prefs.getFloat("ruido1", 0.0f);
  cal.ruido_i[1] = prefs.getFloat("ruido2", 0.0f);
  medir_retardo_multiplexado();

  ledcSetup(0, 5000, 8);   // luz de fondo de la LCD
  ledcAttachPin(PIN_LCD_BL, 0);
  luz_fondo(true);
  SPI.begin(PIN_LCD_CLK, -1, PIN_LCD_DIN, PIN_LCD_CS);
  lcd.init(170, 320);
  lcd.setSPISpeed(LCD_SPI_HZ);
  lcd.setRotation(1);      // horizontal, 320 × 170, con el conector a la izquierda
  {
    interfaz::Datos d{};
    d.version = FW_VERSION;
    for (int16_t y0 = 0; y0 < interfaz::ALTO; y0 += ALTO_FRANJA) {
      franja.origen(y0);
      interfaz::dibujar(franja, interfaz::ARRANQUE, d);
      lcd.drawRGBBitmap(0, y0, franja.getBuffer(), interfaz::ANCHO, ALTO_FRANJA);
    }
  }

  cola_resultados = xQueueCreate(8, sizeof(medicion::Resultado));
  xTaskCreatePinnedToCore(tarea_adquisicion, "adquisicion", 6144, nullptr, 20, nullptr, 1);
  xTaskCreatePinnedToCore(tarea_red, "red", 8192, nullptr, 5, nullptr, 0);
  xTaskCreatePinnedToCore(tarea_interfaz, "interfaz", 6144, nullptr, 3, nullptr, 0);
}

void loop() {
  vTaskDelete(nullptr);   // todo corre en tareas; el lazo de Arduino no se usa
}
