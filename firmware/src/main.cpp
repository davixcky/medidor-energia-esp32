// Firmware del medidor de energía de dos canales (ESP32-DevKitC V4).
//
// Núcleo 1: tarea de adquisición. Muestrea V, I1 e I2 a 8 kS/s por canal y calcula una
// ventana de 60 ciclos (≈ 1 s). Solo entrega resultados por cola: nunca toca la red.
// Núcleo 0: red (Wi-Fi, NTP, POST de registros ADR-001 en lotes), pantalla LCD, pulsadores
// y LED de estado.
#include <Adafruit_ST7789.h>
#include <Adafruit_NeoPixel.h>
#include "feedback.h"
#include "ajustes.h"
#include <atomic>
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
#define FW_VERSION "fw-v1.3.0"
#endif

// ---------------------------------------------------------------- estado compartido
static QueueHandle_t cola_resultados;            // adquisición → red
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
static medicion::Resultado ultimo{};             // copia para la pantalla
static medicion::Calibracion cal{};
static volatile bool pedir_tara = false;
static volatile int canal_tara = 0;
static volatile bool cal_nueva = false;          // la consola cambió la calibración
static float t_conv_s = 0;                       // duración de una conversión del ADC

// Constantes de calibración ajustables en el banco (se guardan en NVS).
struct Ajustes {
  float k_v, k_i1, k_i2;
  float fase_v, fase_ct1, fase_ct2;              // grados a 60 Hz
};
static Ajustes ajustes{K_V, K_I1, K_I2, FASE_V_GRADOS, FASE_CT1_GRADOS, FASE_CT2_GRADOS};
static TaskHandle_t h_adquisicion = nullptr;
static hw_timer_t* temporizador = nullptr;

static double energia_hoy_wh = 0;
static float energia_hora_wh[24] = {};
static int hora_actual = -1;
static int dia_actual = -1;
static uint32_t inicio_alerta = 0;
static std::atomic<uint32_t> umbral_local{static_cast<uint32_t>(UMBRAL_ALERTA_W)};
static int brillo_lcd = 200;
static ajustes_ui::Menu menu;
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
// El temporizador de hardware despierta la tarea cada 125 µs. Entre muestras la tarea queda
// bloqueada, así que el núcleo 1 también atiende a las demás tareas que viven en él.
static void IRAM_ATTR al_muestrear() {
  BaseType_t despertar = pdFALSE;
  vTaskNotifyGiveFromISR(h_adquisicion, &despertar);
  if (despertar) portYIELD_FROM_ISR();
}

static void tarea_adquisicion(void*) {
  portENTER_CRITICAL(&mux);
  medicion::Calibracion c = cal;
  portEXIT_CRITICAL(&mux);
  medicion::Ventana ventana(c, CICLOS_VENTANA, (float)FS_HZ);
  // El temporizador se arranca desde esta tarea para que su interrupción quede en el núcleo 1.
  temporizador = timerBegin(0, 80, true);                 // 80 MHz / 80 = 1 µs por cuenta
  timerAttachInterrupt(temporizador, &al_muestrear, true);
  timerAlarmWrite(temporizador, 1000000 / FS_HZ, true);
  timerAlarmEnable(temporizador);
  int64_t t_ventana = esp_timer_get_time();
  uint32_t n_ventana = 0;
  const int64_t arranque = t_ventana + DESCARTE_MS * 1000LL;
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    int v = adc1_get_raw(ADC_V);
    int i1 = adc1_get_raw(ADC_CH1);
    int i2 = adc1_get_raw(ADC_CH2);
    int64_t ahora = esp_timer_get_time();
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
        portENTER_CRITICAL(&mux);
        cal.ruido_i[canal_tara] = sqrtf(r.i_rms[canal_tara] * r.i_rms[canal_tara] +
                                        cal.ruido_i[canal_tara] * cal.ruido_i[canal_tara]);
        portEXIT_CRITICAL(&mux);
        cal_nueva = true;
        pedir_tara = false;
      }
      if (cal_nueva) {    // los cambios entran al empezar la ventana siguiente
        portENTER_CRITICAL(&mux);
        c = cal;
        portEXIT_CRITICAL(&mux);
        ventana.calibracion(c);
        cal_nueva = false;
      }
    }
  }
}

// Retardo de la tensión que se empareja con cada corriente, en muestras: multiplexado del ADC
// (I1 se convierte una conversión después de V, I2 dos) más la fase de la pinza menos la del ZMPT.
static void aplicar_ajustes() {
  const float ts = 1.0f / FS_HZ;
  const float grados_a_muestras = 1.0f / 360.0f / 60.0f / ts;
  portENTER_CRITICAL(&mux);
  cal.k_v = ajustes.k_v;
  cal.k_i[0] = ajustes.k_i1;
  cal.k_i[1] = ajustes.k_i2;
  cal.retardo[0] = t_conv_s / ts + (ajustes.fase_ct1 - ajustes.fase_v) * grados_a_muestras;
  cal.retardo[1] = 2 * t_conv_s / ts + (ajustes.fase_ct2 - ajustes.fase_v) * grados_a_muestras;
  portEXIT_CRITICAL(&mux);
  for (float r : cal.retardo)
    if (r < medicion::RETARDO_MIN || r > medicion::RETARDO_MAX)
      Serial.printf("Aviso: retardo de %.2f muestras fuera de rango; se recorta\n", r);
  cal_nueva = true;
}

// Mide cuánto tarda una conversión para interpolar la tensión al instante de cada corriente.
static void medir_retardo_multiplexado() {
  const int N = 2000;
  int64_t t0 = esp_timer_get_time();
  for (int k = 0; k < N; ++k) adc1_get_raw(ADC_CH1);
  t_conv_s = (esp_timer_get_time() - t0) / (float)N * 1e-6f;
  Serial.printf("Conversión ADC: %.1f us\n", t_conv_s * 1e6f);
}

static void cargar_ajustes() {
  ajustes.k_v = prefs.getFloat("kv", K_V);
  ajustes.k_i1 = prefs.getFloat("ki1", K_I1);
  ajustes.k_i2 = prefs.getFloat("ki2", K_I2);
  ajustes.fase_v = prefs.getFloat("fv", FASE_V_GRADOS);
  ajustes.fase_ct1 = prefs.getFloat("f1", FASE_CT1_GRADOS);
  ajustes.fase_ct2 = prefs.getFloat("f2", FASE_CT2_GRADOS);
}

static void mostrar_ajustes() {
  Serial.printf("kv %.3f  ki1 %.4f  ki2 %.4f  fv %.2f  f1 %.2f  f2 %.2f  (retardo %.3f / %.3f muestras)\n",
                ajustes.k_v, ajustes.k_i1, ajustes.k_i2, ajustes.fase_v, ajustes.fase_ct1, ajustes.fase_ct2,
                cal.retardo[0], cal.retardo[1]);
}

// Consola serie para calibrar en el banco sin recompilar:
//   cal                    muestra los valores
//   cal kv|ki1|ki2|fv|f1|f2 <valor>   cambia uno y lo guarda en NVS
//   cal borrar             vuelve a los valores de config.h
static void atender_consola() {
  static char linea[48];
  static size_t largo = 0;
  while (Serial.available()) {
    char ch = (char)Serial.read();
    if (ch != '\n' && ch != '\r') {
      if (largo < sizeof linea - 1) linea[largo++] = ch;
      continue;
    }
    if (largo == 0) continue;
    linea[largo] = 0;
    largo = 0;
    char clave[8] = "";
    float valor = 0;
    int n = sscanf(linea, "cal %7s %f", clave, &valor);
    if (strncmp(linea, "cal", 3) != 0) {
      Serial.println("Comandos: cal | cal kv|ki1|ki2|fv|f1|f2 <valor> | cal borrar");
      continue;
    }
    if (n == 1 && strcmp(clave, "borrar") == 0) {
      for (const char* k : {"kv", "ki1", "ki2", "fv", "f1", "f2"}) prefs.remove(k);
      cargar_ajustes();
    } else if (n == 2) {
      float* destino = strcmp(clave, "kv") == 0    ? &ajustes.k_v
                       : strcmp(clave, "ki1") == 0 ? &ajustes.k_i1
                       : strcmp(clave, "ki2") == 0 ? &ajustes.k_i2
                       : strcmp(clave, "fv") == 0  ? &ajustes.fase_v
                       : strcmp(clave, "f1") == 0  ? &ajustes.fase_ct1
                       : strcmp(clave, "f2") == 0  ? &ajustes.fase_ct2
                                                   : nullptr;
      if (!destino) {
        Serial.printf("Clave desconocida: %s\n", clave);
        continue;
      }
      *destino = valor;
      prefs.putFloat(clave, valor);
    }
    aplicar_ajustes();
    mostrar_ajustes();
  }
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
  const uint32_t threshold = umbral_local.load();
  static uint32_t previous_threshold = threshold;
  if (previous_threshold != threshold) {
    inicio_alerta = 0; alerta_activa = false; alerta_reconocida = false;
    previous_threshold = threshold;
  }
  if (r.p[0] > threshold) {
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
  d.umbral_w = umbral_local.load();
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

static void luz_fondo(bool encendida) { ledcWrite(0, encendida ? brillo_lcd : 0); }

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

static Adafruit_NeoPixel pixels(4, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
static feedback::Sound sound;
static void feedback_tick() {
  const uint32_t now = millis();
  const bool alert = alerta_activa && !alerta_reconocida;
  ledcWrite(2, sound.tick(now, alert) ? 128 : 0);
  // Restrained fixed colors; only transmit when the state changes.
  const bool online = ultimo_envio_ok != 0 && now - ultimo_envio_ok < 15000;
  const uint32_t color = alert ? pixels.Color(32, 0, 0) :
      online ? pixels.Color(0, 18, 10) : pixels.Color(24, 9, 0);
  static uint32_t previous = 0xffffffff;
  if (color != previous) { pixels.fill(color); pixels.show(); previous = color; }
}

static portMUX_TYPE enc_mux = portMUX_INITIALIZER_UNLOCKED;
static volatile int enc_edges = 0;
static volatile uint8_t enc_before = 0;
static void IRAM_ATTR encoder_edge() {
  const uint8_t now = (digitalRead(PIN_ENC_A) << 1) | digitalRead(PIN_ENC_B);
  portENTER_CRITICAL_ISR(&enc_mux);
  // A two-bit jump loses synchronization; don't turn an invalid edge into motion.
  if ((enc_before ^ now) == 3) enc_edges = 0;
  else enc_edges += ajustes_ui::transition(enc_before, now);
  enc_before = now;
  portEXIT_CRITICAL_ISR(&enc_mux);
}
static int encoder_turn() {
  portENTER_CRITICAL(&enc_mux);
  const int detents = enc_edges / ENCODER_EDGES_PER_DETENT;
  enc_edges %= ENCODER_EDGES_PER_DETENT;
  portEXIT_CRITICAL(&enc_mux);
  return detents;
}
static void dibujar_ajustes() {
  const auto& v = menu.editing ? menu.draft : menu.values;
  for (int y = 0; y < interfaz::ALTO; y += ALTO_FRANJA) {
    franja.origen(y);
    interfaz::dibujar_ajustes(franja,menu.row,menu.editing,v.brightness,v.muted,v.threshold);
    lcd.drawRGBBitmap(0,y,franja.getBuffer(),interfaz::ANCHO,ALTO_FRANJA);
  }
}

static void tarea_interfaz(void*) {
  using namespace interfaz;
  Boton sw1(PIN_SW1), sw2(PIN_SW2), encoder_button(PIN_ENC_SW);
  bool apagada = false;
  uint32_t ultimo_dibujo = 0;
  for (;;) {
    atender_consola();
    int e1 = leer(sw1), e2 = leer(sw2);
    int enc_press = leer(encoder_button), turn = encoder_turn();
    if (e1 || e2 || enc_press || turn) {
      ultima_pulsacion = millis();
      if (apagada) {
        apagada = false;
        luz_fondo(true);
        e1 = e2 = enc_press = turn = 0;
      }
    }
    const bool alert = alerta_activa && !alerta_reconocida;
    if (alert) { menu.active = false; menu.editing = false; pantalla = ALERTA; }
    if (!alert && pantalla != TARA) {
      if (enc_press == 2) menu.cancel();
      if (enc_press == 1) {
        if (!menu.active) menu.values = {brillo_lcd, sound.muted, static_cast<int>(umbral_local.load())};
        if (menu.press()) {
          brillo_lcd = menu.values.brightness;
          sound.muted = menu.values.muted; sound.stop();
          umbral_local.store(menu.values.threshold);
          prefs.putInt("brillo", brillo_lcd); prefs.putBool("silencio", sound.muted);
          prefs.putUInt("umbral", menu.values.threshold);
          luz_fondo(true);
        }
        sound.click(millis());
      }
      menu.turn(turn);
    }
    if (menu.active) e1 = e2 = 0;
    if (enc_press || turn) ultimo_dibujo = millis() - 501;
    if (e1 == 2) {
      sound.toggle();
      prefs.putBool("silencio", sound.muted);
      Serial.printf("Sonido: %s\n", sound.muted ? "silenciado" : "activo");
    } else if (e1 || e2) sound.click(millis());
    feedback_tick();
    if (menu.active) {
      // Configuration consumes encoder input; measurement and network tasks continue.
    } else if (pantalla == ALERTA) {
      if (e2 == 1) {
        alerta_reconocida = true;
        pantalla = RESUMEN;
      }
    } else if (pantalla == TARA) {
      if (e1 == 1) pantalla = canal_tara == 0 ? CH1 : CH2;
      if (e2 == 2) {
        pedir_tara = true;
        while (pedir_tara) { feedback_tick(); vTaskDelay(pdMS_TO_TICKS(10)); }
        portENTER_CRITICAL(&mux);
        float ruido = cal.ruido_i[canal_tara];
        portEXIT_CRITICAL(&mux);
        prefs.putFloat(canal_tara == 0 ? "ruido1" : "ruido2", ruido);
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
      if (menu.active) dibujar_ajustes(); else dibujar(r);
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
  pinMode(PIN_ENC_A, INPUT_PULLUP); pinMode(PIN_ENC_B, INPUT_PULLUP);
  pinMode(PIN_ENC_SW, INPUT_PULLUP);
  enc_before = (digitalRead(PIN_ENC_A) << 1) | digitalRead(PIN_ENC_B);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_A), encoder_edge, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_B), encoder_edge, CHANGE);

  adc1_config_width(ADC_WIDTH_BIT_12);
  for (adc1_channel_t ch : {ADC_CH1, ADC_CH2, ADC_V}) adc1_config_channel_atten(ch, ADC_ATTEN_DB_12);
  esp_adc_cal_characteristics_t car;
  esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN_DB_12, ADC_WIDTH_BIT_12, 1100, &car);
  // Pendiente de la recta de calibración del eFuse (mV por código, escalada por 65536).
  cal.voltios_por_codigo = car.coeff_a / 65536.0f / 1000.0f;
  cal.tau_filtro_s = TAU_FILTRO_S;
  prefs.begin("medidor", false);
  sound.muted = prefs.getBool("silencio", false);
  brillo_lcd = ajustes_ui::clamp(prefs.getInt("brillo", 200), 32, 255);
  umbral_local.store(ajustes_ui::clamp(prefs.getUInt("umbral", static_cast<uint32_t>(UMBRAL_ALERTA_W)), 100, 10000));
  ledcSetup(2, 2400, 8); // independent timer from LCD channel 0
  ledcAttachPin(PIN_BUZZER, 2);
  ledcWrite(2, 0);
  pixels.begin();
  pixels.clear();
  pixels.show();
  cal.ruido_i[0] = prefs.getFloat("ruido1", 0.0f);
  cal.ruido_i[1] = prefs.getFloat("ruido2", 0.0f);
  medir_retardo_multiplexado();
  cargar_ajustes();
  aplicar_ajustes();
  mostrar_ajustes();

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
  xTaskCreatePinnedToCore(tarea_red, "red", 8192, nullptr, 5, nullptr, 0);
  xTaskCreatePinnedToCore(tarea_interfaz, "interfaz", 6144, nullptr, 3, nullptr, 0);
  // La adquisición se crea al final: tiene la prioridad más alta del núcleo 1.
  xTaskCreatePinnedToCore(tarea_adquisicion, "adquisicion", 6144, nullptr, 20, &h_adquisicion, 1);
}

void loop() {
  vTaskDelete(nullptr);   // todo corre en tareas; el lazo de Arduino no se usa
}
