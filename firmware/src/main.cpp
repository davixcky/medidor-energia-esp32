// Firmware del medidor de energía de dos canales (ESP32-DevKitC V4).
//
// Núcleo 1: tarea de adquisición. Muestrea V, I1 e I2 a 8 kS/s por canal y calcula una
// ventana de 60 ciclos (≈ 1 s). Solo entrega resultados por cola: nunca toca la red.
// Núcleo 0: red (Wi-Fi, NTP, POST de registros ADR-001 en lotes), pantalla OLED, pulsadores
// y LED de estado.
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <WiFi.h>
#include <Wire.h>
#include <esp_adc_cal.h>
#include <esp_timer.h>
#include <time.h>

#include "adr001.h"
#include "config.h"
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
static int dia_actual = -1;
static uint32_t inicio_alerta = 0;
static bool alerta_activa = false, alerta_reconocida = false;
static uint32_t ultimo_envio_ok = 0;
static int rssi = 0;

// Búfer circular de registros codificados, para no perder datos sin red.
static uint8_t bufer[BUFER_REGISTROS][adr001::TAMANO];
static size_t cabeza = 0, cantidad = 0;

Adafruit_SSD1306 oled(128, 64, &Wire, -1);
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
  }
  energia_hoy_wh += r.p[0] * (r.muestras / (float)FS_HZ) / 3600.0;
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
enum Pantalla { RESUMEN, CH1, CH2, ENERGIA, N_CICLO, ALERTA, TARA };
static Pantalla pantalla = RESUMEN;
static uint32_t ultima_pulsacion = 0;

static void encabezado(const char* titulo, int pagina) {
  oled.fillRect(0, 0, 128, 10, SSD1306_WHITE);
  oled.setTextColor(SSD1306_BLACK);
  oled.setTextSize(1);
  oled.setCursor(2, 1);
  oled.print(titulo);
  if (pagina > 0) {
    oled.setCursor(104, 1);
    oled.printf("%d/4", pagina);
  }
  oled.setTextColor(SSD1306_WHITE);
}

static void dibujar(const medicion::Resultado& r) {
  oled.clearDisplay();
  char b[24];
  switch (pantalla) {
    case RESUMEN:
      encabezado("RESUMEN", 1);
      oled.setTextSize(2);
      snprintf(b, sizeof b, "%.0f W", r.p[0]);
      oled.setCursor((128 - strlen(b) * 12) / 2, 14);
      oled.print(b);
      oled.setTextSize(1);
      oled.setCursor(0, 34);
      oled.printf("V %.1fV  I %.2fA", r.v_rms, r.i_rms[0]);
      oled.setCursor(0, 44);
      oled.printf("FP %.2f  f %.2fHz", r.fp[0], r.f_hz);
      oled.setCursor(0, 54);
      oled.printf("CH2 %.0fW RES %.0fW", r.p[1], r.p[0] - r.p[1]);
      break;
    case CH1:
    case CH2: {
      int c = pantalla == CH1 ? 0 : 1;
      encabezado(c == 0 ? "CH1 TOTAL" : "CH2 SUBCIRC.", c + 2);
      oled.setTextSize(2);
      snprintf(b, sizeof b, "%.2f A", r.i_rms[c]);
      oled.setCursor((128 - strlen(b) * 12) / 2, 14);
      oled.print(b);
      oled.setTextSize(1);
      oled.setCursor(0, 32);
      oled.printf("P  %6.0f W", r.p[c]);
      oled.setCursor(0, 41);
      oled.printf("S  %6.0f VA", r.s[c]);
      oled.setCursor(0, 50);
      if (c == 0) oled.printf("FP %.2f THD %.1f%%", r.fp[c], r.thd_i1);
      else oled.printf("FP %.2f", r.fp[c]);
      float escala = c == 0 ? 60.0f : 30.0f;
      oled.drawRect(26, 58, 100, 6, SSD1306_WHITE);
      oled.fillRect(26, 58, (int)constrain(r.i_rms[c] / escala * 100, 0, 100), 6, SSD1306_WHITE);
      oled.setCursor(0, 58);
      oled.printf("%.0fA", escala);
      break;
    }
    case ENERGIA: {
      encabezado("ENERGIA HOY", 4);
      oled.setTextSize(2);
      snprintf(b, sizeof b, "%.2fkWh", energia_hoy_wh / 1000.0);
      oled.setCursor((128 - strlen(b) * 12) / 2, 14);
      oled.print(b);
      oled.setTextSize(1);
      oled.setCursor(0, 34);
      if (WiFi.status() == WL_CONNECTED) oled.printf("WIFI %ddBm OK", rssi);
      else oled.print("WIFI SIN RED");
      oled.setCursor(0, 44);
      oled.print(millis() - ultimo_envio_ok < 15000 ? "SERVIDOR OK" : "SERVIDOR SIN ENVIO");
      oled.setCursor(0, 54);
      oled.printf("BUFER %u REG", (unsigned)cantidad);
      break;
    }
    case ALERTA:
      encabezado("! ALERTA CH1", 0);
      oled.setTextSize(2);
      snprintf(b, sizeof b, "%.0f W", r.p[0]);
      oled.setCursor((128 - strlen(b) * 12) / 2, 14);
      oled.print(b);
      oled.setTextSize(1);
      oled.setCursor(0, 34);
      oled.printf("SOBRE UMBRAL %.0fW", UMBRAL_ALERTA_W);
      oled.setCursor(0, 44);
      oled.printf("DURANTE %lu min", (unsigned long)((millis() - inicio_alerta) / 60000));
      oled.fillRect(0, 54, 128, 10, SSD1306_WHITE);
      oled.setTextColor(SSD1306_BLACK);
      oled.setCursor(2, 55);
      oled.print("SW2: RECONOCER");
      oled.setTextColor(SSD1306_WHITE);
      break;
    case TARA:
      encabezado(canal_tara == 0 ? "TARA CH1" : "TARA CH2", 0);
      oled.setCursor(0, 14);
      oled.print("RETIRE LA CARGA");
      oled.setCursor(0, 24);
      oled.print("RUIDO ACTUAL");
      oled.setTextSize(2);
      oled.setCursor(10, 34);
      oled.printf("%.2f A", cal.ruido_i[canal_tara]);
      oled.setTextSize(1);
      oled.setCursor(0, 56);
      oled.print("SW2 2s:OK SW1:SALIR");
      break;
    default:
      break;
  }
  oled.display();
}

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
  Boton sw1(PIN_SW1), sw2(PIN_SW2);
  bool apagada = false;
  uint32_t ultimo_dibujo = 0;
  for (;;) {
    int e1 = leer(sw1), e2 = leer(sw2);
    if (e1 || e2) {
      ultima_pulsacion = millis();
      if (apagada) {
        apagada = false;
        oled.ssd1306_command(SSD1306_DISPLAYON);
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
      oled.ssd1306_command(SSD1306_DISPLAYOFF);
    }
    // LED: fijo = servidor al día, 1 Hz = sin red, 5 Hz = alerta sin reconocer.
    uint32_t m = millis();
    bool led;
    if (alerta_activa && !alerta_reconocida) led = (m / 100) % 2;
    else if (m - ultimo_envio_ok < 15000) led = true;
    else led = (m / 500) % 2;
    digitalWrite(PIN_LED, led);
    if (!apagada && m - ultimo_dibujo > 250) {
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

  Wire.begin(PIN_SDA, PIN_SCL);
  if (!oled.begin(SSD1306_SWITCHCAPVCC, OLED_DIR)) Serial.println("OLED no encontrada");
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setCursor(0, 0);
  oled.printf("Medidor de energia\n%s\nIniciando...", FW_VERSION);
  oled.display();

  cola_resultados = xQueueCreate(8, sizeof(medicion::Resultado));
  xTaskCreatePinnedToCore(tarea_adquisicion, "adquisicion", 6144, nullptr, 20, nullptr, 1);
  xTaskCreatePinnedToCore(tarea_red, "red", 8192, nullptr, 5, nullptr, 0);
  xTaskCreatePinnedToCore(tarea_interfaz, "interfaz", 4096, nullptr, 3, nullptr, 0);
}

void loop() {
  vTaskDelete(nullptr);   // todo corre en tareas; el lazo de Arduino no se usa
}
