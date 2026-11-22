#include <Arduino.h>
#include <LilyGo_AMOLED.h>
#include <SD.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <telemetry_packet.h>
#include "cuc_logo.h"

namespace {
constexpr char LINK_AP[] = "Medidor-Energy-Link";
constexpr uint32_t OFFLINE_MS = 10000;
constexpr uint32_t DRAW_MS = 90;
constexpr float COST_COP_KWH = 850.0f;
constexpr int SCREEN_COUNT = 4;

enum DetailView {
  DETAIL_NONE,
  DETAIL_TOTAL,
  DETAIL_WEATHER,
  DETAIL_VOLTAGE,
  DETAIL_FREQUENCY,
  DETAIL_ENERGY,
  DETAIL_CHANNEL_1,
  DETAIL_CHANNEL_2,
  DETAIL_ESPNOW,
  DETAIL_SD
};

constexpr uint16_t BG = TFT_BLACK;
constexpr uint16_t PANEL = 0x10A2;
constexpr uint16_t PANEL_2 = 0x0841;
constexpr uint16_t LINE = 0x31A6;
constexpr uint16_t MUTED = 0x9CF3;
constexpr uint16_t DIM = 0x632C;
constexpr uint16_t CYAN = 0x5DFF;
constexpr uint16_t GREEN = 0x4EAA;
constexpr uint16_t YELLOW = 0xFDC0;
constexpr uint16_t ORANGE = 0xFD20;
constexpr uint16_t RED = 0xF986;

LilyGo_Class amoled;
TFT_eSPI tft;
TFT_eSprite frame(&tft);

struct View {
  String city = "Esperando datos";
  float vrms = 0, i1 = 0, i2 = 0, p1 = 0, p2 = 0, wh = 0;
  float temp_c = 0, wind_kmh = 0, frequency_hz = 60;
  int humidity = 0, weather_code = -1, rssi_dbm = -100;
  int hour = 0, minute = 0;
  bool alert = false, internet = false;
} target, shown;

TelemetryPacket pending_packet;
volatile bool packet_ready = false;
portMUX_TYPE packet_mux = portMUX_INITIALIZER_UNLOCKED;
uint32_t last_packet_ms = 0, last_draw_ms = 0, last_screen_ms = 0, last_seq = 0;
int active_screen = 0;
DetailView active_detail = DETAIL_NONE;
bool have_data = false, sd_ready = false;
bool touch_dragging = false;
int touch_drag_dx = 0;
uint32_t swipe_flash_until = 0;
int swipe_flash_direction = 0;
bool double_tap_waiting = false;
uint32_t double_tap_deadline = 0;
int double_tap_x = 0, double_tap_y = 0, double_tap_screen = 0;
uint32_t sd_capacity_mb = 0;
float power_history[64] = {};
int history_head = 0, history_count = 0;

float powerFactor(float p, float v, float i);
float reactivePower(float p, float v, float i);
void handleTap(int x, int y);

bool mountSd() {
  if (SD.cardType() == CARD_NONE && !SD.begin(1, SPI, 4000000U, "/fs")) return false;
  if (SD.cardType() == CARD_NONE) return false;
  sd_capacity_mb = SD.cardSize() / (1024ULL * 1024ULL);
  sd_ready = true;
  if (!SD.exists("/telemetry.csv")) {
    File file = SD.open("/telemetry.csv", FILE_WRITE);
    if (file) {
      file.println("seq,hour,minute,vrms,hz,i1,p1,pf1,var1,i2,p2,pf2,var2,today_wh,temp_c,humidity,rssi");
      file.close();
    }
  }
  Serial.printf("SD MOUNTED: %lu MB, logging /telemetry.csv\n",
                static_cast<unsigned long>(sd_capacity_mb));
  return true;
}

void logPacket(const TelemetryPacket& packet) {
  if (!sd_ready) return;
  File file = SD.open("/telemetry.csv", FILE_APPEND);
  if (!file) {
    Serial.println("SD WRITE FAILED");
    sd_ready = false;
    return;
  }
  file.printf("%lu,%u,%u,%.2f,%.3f,%.3f,%.2f,%.4f,%.2f,%.3f,%.2f,%.4f,%.2f,%.2f,%.1f,%d,%d\n",
              static_cast<unsigned long>(packet.seq), packet.local_hour, packet.local_minute,
              packet.vrms, packet.frequency_hz, packet.i1, packet.p1,
              powerFactor(packet.p1, packet.vrms, packet.i1),
              reactivePower(packet.p1, packet.vrms, packet.i1),
              packet.i2, packet.p2, powerFactor(packet.p2, packet.vrms, packet.i2),
              reactivePower(packet.p2, packet.vrms, packet.i2), packet.today_wh,
              packet.temp_c, packet.humidity, packet.rssi_dbm);
  file.close();
}

float approach(float current, float desired, float amount = 0.18f) {
  return current + (desired - current) * amount;
}

float powerFactor(float p, float v, float i) {
  const float apparent = v * i;
  return apparent > 0.1f ? constrain(fabsf(p) / apparent, 0.0f, 1.0f) : 0.0f;
}

float reactivePower(float p, float v, float i) {
  const float s = v * i;
  return sqrtf(max(0.0f, s * s - p * p));
}

void card(int x, int y, int w, int h, uint16_t color = PANEL) {
  frame.fillRoundRect(x, y, w, h, 18, color);
}

void text(const String& value, int x, int y, int font, uint16_t color,
          uint16_t background = BG) {
  frame.setTextDatum(TL_DATUM);
  frame.setTextColor(color, background);
  frame.drawString(value, x, y, font);
}

void rightText(const String& value, int x, int y, int font, uint16_t color,
               uint16_t background = BG) {
  frame.setTextDatum(TR_DATUM);
  frame.setTextColor(color, background);
  frame.drawString(value, x, y, font);
  frame.setTextDatum(TL_DATUM);
}

void progressBar(int x, int y, int w, int h, float ratio, uint16_t color) {
  ratio = constrain(ratio, 0.0f, 1.0f);
  frame.fillRoundRect(x, y, w, h, h / 2, 0x2124);
  if (ratio > 0.01f) frame.fillRoundRect(x, y, max(h, int(w * ratio)), h, h / 2, color);
}

void tapHint(int x, int y, uint16_t background = PANEL) {
  text("TOCAR  >", x, y, 1, DIM, background);
}

void statusBadge(const char* label, int x, bool good) {
  const uint16_t color = good ? GREEN : ORANGE;
  frame.fillRoundRect(x, 25, 58, 24, 12, 0x2124);
  frame.fillCircle(x + 12, 37, 4, color);
  text(label, x + 21, 31, 1, TFT_WHITE, 0x2124);
}

void header(const char* title, const char* subtitle) {
  card(16, 10, 568, 74);
  frame.fillRoundRect(25, 20, 76, 36, 9, TFT_BLACK);
  frame.pushImage(30, 23, CUC_LOGO_W, CUC_LOGO_H, CUC_LOGO);
  const int logo_pulse = 2 + int((sinf(millis() / 260.0f) + 1.0f) * 1.5f);
  frame.fillCircle(103, 38, logo_pulse, 0xB800);
  text(title, 112, 25, 4, TFT_WHITE, PANEL);
  const bool esp_link = have_data && millis() - last_packet_ms <= OFFLINE_MS;
  statusBadge("ESP", 382, esp_link);
  statusBadge("SD", 446, sd_ready);
  const String clock = String(shown.hour < 10 ? "0" : "") + shown.hour + ":" +
                       String(shown.minute < 10 ? "0" : "") + shown.minute;
  rightText(clock, 566, 29, 2, TFT_WHITE, PANEL);

  const char* tabs[] = {"RESUMEN", "CANALES", "ENERGIA", "FLUJO"};
  for (int i = 0; i < SCREEN_COUNT; ++i) {
    const int x = 25 + i * 85;
    const bool selected = i == active_screen && active_detail == DETAIL_NONE;
    frame.fillRoundRect(x, 59, 79, 19, 8, selected ? CYAN : PANEL_2);
    frame.setTextDatum(MC_DATUM);
    frame.setTextColor(selected ? BG : MUTED, selected ? CYAN : PANEL_2);
    frame.drawString(tabs[i], x + 39, 68, 1);
  }
  frame.setTextDatum(TR_DATUM);
  frame.setTextColor(MUTED, PANEL);
  frame.drawString(subtitle, 566, 63, 1);
  frame.setTextDatum(TL_DATUM);
}

const char* weatherLabel(int code) {
  if (code == 0) return "DESPEJADO";
  if (code <= 3) return "PARCIALMENTE NUBLADO";
  if (code == 45 || code == 48) return "NIEBLA";
  if (code <= 67 || (code >= 80 && code <= 82)) return "LLUVIA";
  if (code >= 95) return "TORMENTA";
  return "SIN CLIMA";
}

void weatherIcon(int cx, int cy, int code) {
  if (code <= 3) {
    frame.fillCircle(cx - 13, cy - 9, 18, YELLOW);
    for (int a = 0; a < 360; a += 45) {
      const float r = a * PI / 180.0f;
      frame.drawLine(cx - 13 + cosf(r) * 23, cy - 9 + sinf(r) * 23,
                     cx - 13 + cosf(r) * 30, cy - 9 + sinf(r) * 30, YELLOW);
    }
  }
  if (code != 0) {
    frame.fillCircle(cx, cy, 20, 0xBDF7);
    frame.fillCircle(cx + 23, cy + 5, 16, 0xBDF7);
    frame.fillRoundRect(cx - 25, cy, 65, 23, 11, 0xBDF7);
  }
  if (code >= 51)
    for (int dx = -12; dx <= 22; dx += 17)
      frame.drawLine(cx + dx, cy + 31, cx + dx - 5, cy + 43, CYAN);
}

void renderOverview() {
  header("RESUMEN", "POTENCIA TOTAL Y CONDICIONES");
  const float total = shown.p1 + shown.p2;
  card(16, 88, 350, 218);
  text("CONSUMO AHORA", 34, 108, 2, MUTED, PANEL);
  text(String(total, 0), 34, 139, 8, TFT_WHITE, PANEL);
  text("W", 242, 188, 4, CYAN, PANEL);
  const float load = total / 3000.0f;
  progressBar(34, 241, 314, 15, load, load > 0.8f ? RED : CYAN);
  const int shimmer_x = 34 + int(fmodf(millis() / 3.5f, max(15.0f, 314.0f * load)));
  frame.fillCircle(shimmer_x, 248, 3, TFT_WHITE);
  const int pulse_radius = 17 + int((sinf(millis() / 240.0f) + 1.0f) * 5.0f);
  frame.drawCircle(316, 185, pulse_radius, CYAN);
  frame.fillCircle(316, 185, 5, CYAN);
  text(String(load * 100.0f, 0) + "% DE 3 kW", 34, 269, 2, MUTED, PANEL);
  tapHint(286, 111);

  card(380, 88, 204, 218, PANEL_2);
  text(shown.city.substring(0, 18), 398, 108, 2, MUTED, PANEL_2);
  weatherIcon(474, 169, shown.weather_code);
  text(String(shown.temp_c, 1) + " C", 401, 218, 6, TFT_WHITE, PANEL_2);
  text(weatherLabel(shown.weather_code), 400, 263, 1, CYAN, PANEL_2);
  text(String(shown.humidity) + "% HUM  " + String(shown.wind_kmh, 0) + " km/h",
       400, 283, 1, MUTED, PANEL_2);
  tapHint(518, 109, PANEL_2);

  card(16, 320, 178, 112);
  text("TENSION", 32, 339, 2, MUTED, PANEL);
  text(String(shown.vrms, 1) + " V", 32, 369, 4, CYAN, PANEL);
  tapHint(122, 342);
  card(210, 320, 178, 112);
  text("FRECUENCIA", 226, 339, 2, MUTED, PANEL);
  text(String(shown.frequency_hz, 2) + " Hz", 226, 369, 4, GREEN, PANEL);
  tapHint(316, 342);
  card(404, 320, 180, 112);
  text("ENERGIA HOY", 420, 339, 2, MUTED, PANEL);
  text(String(shown.wh / 1000.0f, 2) + " kWh", 420, 369, 4, YELLOW, PANEL);
  tapHint(512, 342);
}

void channelCard(int channel, int y, float p, float current, uint16_t accent) {
  const float pf = powerFactor(p, shown.vrms, current);
  const float va = shown.vrms * current;
  const float var = reactivePower(p, shown.vrms, current);
  card(16, y, 568, 142);
  text("CANAL " + String(channel), 34, y + 18, 4, TFT_WHITE, PANEL);
  text(String(p, 0) + " W", 34, y + 58, 6, accent, PANEL);
  text("CORRIENTE", 242, y + 20, 1, MUTED, PANEL);
  text(String(current, 2) + " A", 242, y + 40, 4, TFT_WHITE, PANEL);
  text("FP", 390, y + 20, 1, MUTED, PANEL);
  text(String(pf, 3), 390, y + 40, 4, pf < 0.9f ? ORANGE : GREEN, PANEL);
  text("APARENTE " + String(va, 0) + " VA", 242, y + 83, 1, MUTED, PANEL);
  text("REACTIVA " + String(var, 0) + " var", 390, y + 83, 1, MUTED, PANEL);
  progressBar(242, y + 110, 314, 11, p / 2000.0f, accent);
  tapHint(500, y + 20);
}

void renderChannels() {
  header("CANALES", "CALCULOS DERIVADOS EN LA LILYGO");
  channelCard(1, 90, shown.p1, shown.i1, CYAN);
  channelCard(2, 248, shown.p2, shown.i2, YELLOW);
  text("FP = W / (V x A)   |   var = sqrt(VA^2 - W^2)", 24, 411, 1, DIM);
}

void sparkline(int x, int y, int w, int h) {
  frame.drawRoundRect(x, y, w, h, 14, LINE);
  if (history_count < 2) return;
  float low = power_history[0], high = low;
  for (int i = 0; i < history_count; ++i) {
    const float v = power_history[(history_head - history_count + i + 64) % 64];
    low = min(low, v); high = max(high, v);
  }
  if (high - low < 100) high = low + 100;
  int px = x + 8, py = y + h - 8;
  for (int i = 0; i < history_count; ++i) {
    const float v = power_history[(history_head - history_count + i + 64) % 64];
    const int nx = x + 8 + i * (w - 16) / max(1, history_count - 1);
    const int ny = y + h - 8 - int((v - low) * (h - 16) / (high - low));
    if (i) frame.drawLine(px, py, nx, ny, CYAN);
    frame.fillCircle(nx, ny, i == history_count - 1 ? 3 : 1, CYAN);
    px = nx; py = ny;
  }
}

void renderEnergy() {
  header("ENERGIA", "PROYECCION Y COSTO ESTIMADO");
  const float total = shown.p1 + shown.p2;
  const float elapsed_h = shown.hour + shown.minute / 60.0f;
  const float remaining_h = max(0.0f, 24.0f - elapsed_h);
  const float projection = shown.wh / 1000.0f + total * remaining_h / 1000.0f;
  const float cost = shown.wh / 1000.0f * COST_COP_KWH;
  const float projected_cost = projection * COST_COP_KWH;

  card(16, 90, 270, 156);
  text("ACUMULADO HOY", 34, 110, 2, MUTED, PANEL);
  text(String(shown.wh / 1000.0f, 3), 34, 143, 6, TFT_WHITE, PANEL);
  text("kWh", 200, 171, 2, CYAN, PANEL);
  text("$ " + String(cost, 0) + " COP", 34, 211, 2, GREEN, PANEL);

  card(302, 90, 282, 156, PANEL_2);
  text("PROYECCION 24 H", 320, 110, 2, MUTED, PANEL_2);
  text(String(projection, 2), 320, 143, 6, YELLOW, PANEL_2);
  text("kWh", 485, 171, 2, YELLOW, PANEL_2);
  text("$ " + String(projected_cost, 0) + " COP", 320, 211, 2, GREEN, PANEL_2);

  text("POTENCIA TOTAL - ULTIMAS MUESTRAS ESP-NOW", 24, 266, 1, MUTED);
  sparkline(16, 286, 568, 132);
  rightText(String(total, 0) + " W", 566, 266, 2, CYAN);
}

void animatedWire(int x1, int y1, int x2, int y2, uint16_t color, int phase) {
  frame.drawLine(x1, y1, x2, y2, LINE);
  const int steps = 6;
  for (int i = 0; i < steps; ++i) {
    const float t = fmodf((i / float(steps)) + phase / 100.0f, 1.0f);
    frame.fillCircle(x1 + int((x2 - x1) * t), y1 + int((y2 - y1) * t), 4, color);
  }
}

void renderFlow() {
  header("FLUJO", "RED -> MEDIDOR -> CARGAS");
  const float total = shown.p1 + shown.p2;
  const int phase = (millis() / 18) % 100;

  card(24, 151, 126, 126, PANEL_2);
  text("RED", 62, 169, 4, TFT_WHITE, PANEL_2);
  text(String(shown.vrms, 1) + " V", 47, 211, 2, CYAN, PANEL_2);
  text(String(shown.frequency_hz, 2) + " Hz", 42, 241, 2, MUTED, PANEL_2);

  animatedWire(150, 214, 252, 214, CYAN, phase);
  frame.fillCircle(284, 214, 42, CYAN);
  frame.fillCircle(284, 214, 34, BG);
  frame.setTextDatum(MC_DATUM);
  frame.setTextColor(TFT_WHITE, BG);
  frame.drawString(String(total, 0), 284, 205, 4);
  frame.drawString("W", 284, 231, 2);
  frame.setTextDatum(TL_DATUM);
  animatedWire(326, 214, 405, 150, CYAN, phase + 25);
  animatedWire(326, 214, 405, 281, YELLOW, phase + 55);

  card(405, 94, 171, 112);
  text("CANAL 1", 423, 112, 2, MUTED, PANEL);
  text(String(shown.p1, 0) + " W", 423, 144, 4, CYAN, PANEL);
  progressBar(423, 181, 133, 9, shown.p1 / max(1.0f, total), CYAN);
  card(405, 238, 171, 112);
  text("CANAL 2", 423, 256, 2, MUTED, PANEL);
  text(String(shown.p2, 0) + " W", 423, 288, 4, YELLOW, PANEL);
  progressBar(423, 325, 133, 9, shown.p2 / max(1.0f, total), YELLOW);

  card(24, 372, 552, 60);
  text("ESP-NOW " + String(shown.rssi_dbm) + " dBm", 42, 392, 2,
       shown.rssi_dbm > -75 ? GREEN : ORANGE, PANEL);
  text(sd_ready ? "SD " + String(sd_capacity_mb) + " MB" : "SD NO DETECTADA",
       246, 392, 2, sd_ready ? GREEN : ORANGE, PANEL);
  rightText(shown.alert ? "ALERTA" : "SISTEMA OK", 558, 392, 2,
            shown.alert ? RED : GREEN, PANEL);
}

void detailShell(const char* title, const char* subtitle) {
  header(title, subtitle);
  frame.fillRoundRect(16, 89, 132, 44, 14, CYAN);
  text("<  VOLVER", 34, 103, 2, BG, CYAN);
}

void detailMetric(const String& label, const String& value, int x, int y,
                  int w, uint16_t accent = TFT_WHITE) {
  card(x, y, w, 92);
  text(label, x + 16, y + 15, 1, MUTED, PANEL);
  text(value, x + 16, y + 42, 4, accent, PANEL);
}

void renderChannelDetail(int channel, float watts, float amps, uint16_t accent) {
  detailShell(channel == 1 ? "DETALLE CANAL 1" : "DETALLE CANAL 2",
              "CALCULADO CON LOS DATOS RECIBIDOS");
  const float va = shown.vrms * amps;
  const float pf = powerFactor(watts, shown.vrms, amps);
  const float vars = reactivePower(watts, shown.vrms, amps);
  const float total = max(1.0f, shown.p1 + shown.p2);
  detailMetric("POTENCIA ACTIVA", String(watts, 0) + " W", 16, 150, 178, accent);
  detailMetric("CORRIENTE", String(amps, 2) + " A", 210, 150, 178);
  detailMetric("FACTOR POTENCIA", String(pf, 3), 404, 150, 180,
               pf < 0.9f ? ORANGE : GREEN);
  detailMetric("POTENCIA APARENTE", String(va, 0) + " VA", 16, 258, 178);
  detailMetric("POTENCIA REACTIVA", String(vars, 0) + " var", 210, 258, 178);
  detailMetric("PARTE DEL TOTAL", String(watts * 100.0f / total, 1) + "%",
               404, 258, 180, accent);
  text("FP = W / (V x A)    |    var = sqrt(VA^2 - W^2)", 24, 385, 2, DIM);
}

void renderDetail() {
  const float total = shown.p1 + shown.p2;
  const float total_va = shown.vrms * (shown.i1 + shown.i2);
  const float elapsed_h = shown.hour + shown.minute / 60.0f;
  const float projection = shown.wh / 1000.0f +
                           total * max(0.0f, 24.0f - elapsed_h) / 1000.0f;

  if (active_detail == DETAIL_CHANNEL_1) {
    renderChannelDetail(1, shown.p1, shown.i1, CYAN);
    return;
  }
  if (active_detail == DETAIL_CHANNEL_2) {
    renderChannelDetail(2, shown.p2, shown.i2, YELLOW);
    return;
  }

  if (active_detail == DETAIL_TOTAL) {
    detailShell("CONSUMO TOTAL", "RESUMEN ELECTRICO CALCULADO");
    detailMetric("POTENCIA ACTIVA", String(total, 0) + " W", 16, 150, 178, CYAN);
    detailMetric("POTENCIA APARENTE", String(total_va, 0) + " VA", 210, 150, 178);
    detailMetric("FACTOR POTENCIA", String(total_va > 0.1f ? total / total_va : 0, 3),
                 404, 150, 180, GREEN);
    detailMetric("CARGA SOBRE 3 kW", String(total / 30.0f, 1) + "%", 16, 258, 178);
    detailMetric("COSTO POR HORA", "$" + String(total / 1000.0f * COST_COP_KWH, 0),
                 210, 258, 178, GREEN);
    detailMetric("REACTIVA TOTAL",
                 String(reactivePower(total, shown.vrms, shown.i1 + shown.i2), 0) + " var",
                 404, 258, 180, ORANGE);
  } else if (active_detail == DETAIL_WEATHER) {
    detailShell("CLIMA", shown.city.c_str());
    weatherIcon(94, 231, shown.weather_code);
    detailMetric("TEMPERATURA", String(shown.temp_c, 1) + " C", 184, 150, 190, YELLOW);
    detailMetric("HUMEDAD", String(shown.humidity) + "%", 390, 150, 194, CYAN);
    detailMetric("VIENTO", String(shown.wind_kmh, 1) + " km/h", 184, 258, 190);
    detailMetric("CONDICION", weatherLabel(shown.weather_code), 390, 258, 194, GREEN);
  } else if (active_detail == DETAIL_VOLTAGE) {
    detailShell("TENSION", "CALIDAD DE LA RED");
    detailMetric("VALOR RMS", String(shown.vrms, 2) + " V", 16, 150, 276, CYAN);
    detailMetric("DESVIACION DE 120 V", String(shown.vrms - 120.0f, 2) + " V",
                 308, 150, 276, shown.vrms < 108 || shown.vrms > 132 ? ORANGE : GREEN);
    detailMetric("ESTADO", shown.vrms >= 108 && shown.vrms <= 132 ? "NORMAL" : "REVISAR",
                 16, 258, 568, shown.vrms >= 108 && shown.vrms <= 132 ? GREEN : RED);
  } else if (active_detail == DETAIL_FREQUENCY) {
    detailShell("FRECUENCIA", "ESTABILIDAD DE LA RED");
    detailMetric("FRECUENCIA", String(shown.frequency_hz, 3) + " Hz", 16, 150, 276, GREEN);
    detailMetric("DESVIACION DE 60 Hz", String(shown.frequency_hz - 60.0f, 3) + " Hz",
                 308, 150, 276, CYAN);
    detailMetric("ESTADO", fabsf(shown.frequency_hz - 60.0f) <= 0.5f ? "ESTABLE" : "REVISAR",
                 16, 258, 568, fabsf(shown.frequency_hz - 60.0f) <= 0.5f ? GREEN : ORANGE);
  } else if (active_detail == DETAIL_ENERGY) {
    detailShell("ENERGIA Y COSTO", "ESTIMACION A 850 COP / kWh");
    detailMetric("ACUMULADO HOY", String(shown.wh / 1000.0f, 3) + " kWh", 16, 150, 276, CYAN);
    detailMetric("COSTO HOY", "$" + String(shown.wh / 1000.0f * COST_COP_KWH, 0) + " COP",
                 308, 150, 276, GREEN);
    detailMetric("PROYECCION 24 H", String(projection, 2) + " kWh", 16, 258, 276, YELLOW);
    detailMetric("COSTO PROYECTADO", "$" + String(projection * COST_COP_KWH, 0) + " COP",
                 308, 258, 276, GREEN);
  } else if (active_detail == DETAIL_ESPNOW) {
    detailShell("ENLACE ESP-NOW", "RADIO ENTRE LOS DOS ESP32");
    uint8_t primary = 0; wifi_second_chan_t secondary;
    esp_wifi_get_channel(&primary, &secondary);
    const bool online = have_data && millis() - last_packet_ms <= OFFLINE_MS;
    detailMetric("ESTADO", online ? "CONECTADO" : "SIN ENLACE", 16, 150, 178,
                 online ? GREEN : RED);
    detailMetric("SENAL WIFI", String(shown.rssi_dbm) + " dBm", 210, 150, 178, CYAN);
    detailMetric("CANAL RADIO", String(primary), 404, 150, 180, YELLOW);
    detailMetric("ULTIMO PAQUETE", have_data ? String(millis() - last_packet_ms) + " ms" : "NUNCA",
                 16, 258, 276);
    detailMetric("SECUENCIA", String(last_seq), 308, 258, 276);
  } else if (active_detail == DETAIL_SD) {
    detailShell("TARJETA MICROSD", "REGISTRO LOCAL DE TELEMETRIA");
    detailMetric("ESTADO", sd_ready ? "LISTA" : "NO DETECTADA", 16, 150, 276,
                 sd_ready ? GREEN : ORANGE);
    detailMetric("CAPACIDAD", sd_ready ? String(sd_capacity_mb) + " MB" : "--",
                 308, 150, 276, CYAN);
    detailMetric("ARCHIVO", sd_ready ? "/telemetry.csv" : "INSERTE FAT32", 16, 258, 276);
    detailMetric("REGISTRO", sd_ready ? "ACTIVO" : "REINTENTO 15 s", 308, 258, 276,
                 sd_ready ? GREEN : YELLOW);
  }
}

const char* screenName(int screen) {
  const char* names[] = {"RESUMEN", "CANALES", "ENERGIA", "FLUJO"};
  return names[constrain(screen, 0, SCREEN_COUNT - 1)];
}

void renderGestureFeedback() {
  if (touch_dragging && abs(touch_drag_dx) >= 8) {
    const bool next = touch_drag_dx < 0;
    const int destination = (active_screen + (next ? 1 : SCREEN_COUNT - 1)) % SCREEN_COUNT;
    const int strength = constrain(abs(touch_drag_dx), 0, 42);
    frame.fillRoundRect(184, 397, 232, 37, 18, 0x2124);
    frame.setTextDatum(MC_DATUM);
    frame.setTextColor(strength >= 34 ? TFT_WHITE : MUTED, 0x2124);
    frame.drawString(String(next ? "<  " : ">  ") + screenName(destination), 300, 415, 2);
    frame.fillRect(next ? 0 : 594, 100, 6, 250,
                   strength >= 34 ? CYAN : DIM);
    frame.setTextDatum(TL_DATUM);
  } else if (millis() < swipe_flash_until) {
    const int x = swipe_flash_direction < 0 ? 0 : 592;
    frame.fillRect(x, 92, 8, 266, CYAN);
  } else if (double_tap_waiting && millis() <= double_tap_deadline) {
    frame.fillRoundRect(158, 395, 284, 39, 19, 0x4208);
    frame.setTextDatum(MC_DATUM);
    frame.setTextColor(YELLOW, 0x4208);
    frame.drawString("TOCA OTRA VEZ PARA ABRIR", 300, 414, 2);
    frame.setTextDatum(TL_DATUM);
  }
}

void render() {
  frame.fillSprite(BG);
  if (active_detail != DETAIL_NONE) renderDetail();
  else if (active_screen == 0) renderOverview();
  else if (active_screen == 1) renderChannels();
  else if (active_screen == 2) renderEnergy();
  else renderFlow();

  renderGestureFeedback();

  if (!have_data || millis() - last_packet_ms > OFFLINE_MS) {
    frame.fillRoundRect(158, 180, 284, 82, 18, 0x7800);
    frame.setTextDatum(MC_DATUM);
    frame.setTextColor(TFT_WHITE, 0x7800);
    frame.drawString(have_data ? "ENLACE PERDIDO" : "ESPERANDO ESP-NOW", 300, 221, 4);
    frame.setTextDatum(TL_DATUM);
  }
  amoled.pushColors(0, 0, amoled.width(), amoled.height(),
                    reinterpret_cast<uint16_t*>(frame.getPointer()));
}

bool inRect(int x, int y, int left, int top, int width, int height) {
  return x >= left && x < left + width && y >= top && y < top + height;
}

void openDetail(DetailView detail) {
  active_detail = detail;
  last_screen_ms = millis();
  Serial.printf("UI detail -> %d\n", static_cast<int>(detail));
}

void changeScreenBySwipe(int dx) {
  const int direction = dx < 0 ? 1 : SCREEN_COUNT - 1;
  active_detail = DETAIL_NONE;
  active_screen = (active_screen + direction) % SCREEN_COUNT;
  last_screen_ms = millis();
  swipe_flash_direction = dx < 0 ? -1 : 1;
  swipe_flash_until = millis() + 320;
  double_tap_waiting = false;
  Serial.printf("TOUCH swipe dx=%d -> %s\n", dx, screenName(active_screen));
}

void dispatchTap(int x, int y) {
  // Only data cards use double-tap. Navigation and detail controls stay quick.
  const bool card_tap = active_detail == DETAIL_NONE && y >= 84;
  if (!card_tap) {
    double_tap_waiting = false;
    handleTap(x, y);
    return;
  }

  const uint32_t now = millis();
  const bool same_card_area = double_tap_waiting && now <= double_tap_deadline &&
                              double_tap_screen == active_screen &&
                              abs(x - double_tap_x) <= 90 &&
                              abs(y - double_tap_y) <= 90;
  if (same_card_area) {
    double_tap_waiting = false;
    handleTap(x, y);
    Serial.printf("TOUCH double tap x=%d y=%d\n", x, y);
  } else {
    double_tap_waiting = true;
    double_tap_deadline = now + 850;
    double_tap_x = x;
    double_tap_y = y;
    double_tap_screen = active_screen;
    Serial.printf("TOUCH first tap x=%d y=%d\n", x, y);
  }
}

void handleTap(int x, int y) {
  // Navigation is always available in the header, including from detail pages.
  if (inRect(x, y, 20, 53, 350, 34)) {
    active_screen = constrain((x - 25) / 85, 0, SCREEN_COUNT - 1);
    active_detail = DETAIL_NONE;
    last_screen_ms = millis();
    Serial.printf("UI page -> %d\n", active_screen);
    return;
  }
  if (inRect(x, y, 375, 10, 68, 50)) return openDetail(DETAIL_ESPNOW);
  if (inRect(x, y, 443, 10, 65, 50)) return openDetail(DETAIL_SD);

  // A large back target makes the detail pages usable without precise tapping.
  if (active_detail != DETAIL_NONE) {
    if (inRect(x, y, 0, 84, 180, 76)) {
      active_detail = DETAIL_NONE;
      last_screen_ms = millis();
      Serial.println("UI detail -> back");
    }
    return;
  }

  if (active_screen == 0) {
    if (inRect(x, y, 16, 88, 350, 218)) return openDetail(DETAIL_TOTAL);
    if (inRect(x, y, 380, 88, 204, 218)) return openDetail(DETAIL_WEATHER);
    if (inRect(x, y, 16, 320, 178, 112)) return openDetail(DETAIL_VOLTAGE);
    if (inRect(x, y, 210, 320, 178, 112)) return openDetail(DETAIL_FREQUENCY);
    if (inRect(x, y, 404, 320, 180, 112)) return openDetail(DETAIL_ENERGY);
  } else if (active_screen == 1) {
    if (inRect(x, y, 16, 90, 568, 142)) return openDetail(DETAIL_CHANNEL_1);
    if (inRect(x, y, 16, 248, 568, 142)) return openDetail(DETAIL_CHANNEL_2);
  } else if (active_screen == 2) {
    if (inRect(x, y, 16, 90, 568, 328)) return openDetail(DETAIL_ENERGY);
  } else {
    if (inRect(x, y, 405, 94, 171, 112)) return openDetail(DETAIL_CHANNEL_1);
    if (inRect(x, y, 405, 238, 171, 112)) return openDetail(DETAIL_CHANNEL_2);
    if (inRect(x, y, 24, 372, 220, 60)) return openDetail(DETAIL_ESPNOW);
    if (inRect(x, y, 244, 372, 190, 60)) return openDetail(DETAIL_SD);
    if (inRect(x, y, 24, 130, 350, 180)) return openDetail(DETAIL_TOTAL);
  }
}

void updateShown() {
  shown.vrms = approach(shown.vrms, target.vrms);
  shown.i1 = approach(shown.i1, target.i1);
  shown.i2 = approach(shown.i2, target.i2);
  shown.p1 = approach(shown.p1, target.p1);
  shown.p2 = approach(shown.p2, target.p2);
  shown.wh = approach(shown.wh, target.wh, 0.25f);
  shown.temp_c = approach(shown.temp_c, target.temp_c, 0.12f);
  shown.wind_kmh = approach(shown.wind_kmh, target.wind_kmh, 0.12f);
  shown.frequency_hz = approach(shown.frequency_hz, target.frequency_hz, 0.12f);
  shown.city = target.city;
  shown.humidity = target.humidity;
  shown.weather_code = target.weather_code;
  shown.rssi_dbm = target.rssi_dbm;
  shown.hour = target.hour;
  shown.minute = target.minute;
  shown.alert = target.alert;
  shown.internet = target.internet;
}

void acceptPacket(const TelemetryPacket& packet) {
  if (packet.magic != 0x4D454E45 || packet.version != 1 ||
      packet.size != sizeof(TelemetryPacket)) return;
  last_seq = packet.seq;
  target.vrms = packet.vrms; target.i1 = packet.i1; target.i2 = packet.i2;
  target.p1 = packet.p1; target.p2 = packet.p2; target.wh = packet.today_wh;
  target.temp_c = packet.temp_c; target.wind_kmh = packet.wind_kmh;
  target.frequency_hz = packet.frequency_hz; target.rssi_dbm = packet.rssi_dbm;
  target.humidity = packet.humidity; target.weather_code = packet.weather_code;
  target.hour = packet.local_hour; target.minute = packet.local_minute;
  target.alert = packet.alert; target.internet = packet.internet;
  target.city = packet.city;
  if (!have_data) shown = target;
  have_data = true;
  last_packet_ms = millis();
  power_history[history_head] = packet.p1 + packet.p2;
  history_head = (history_head + 1) % 64;
  history_count = min(64, history_count + 1);
  logPacket(packet);
  Serial.printf("ESP-NOW FRAME %lu: %.0f W, FP1 %.3f, %s %.1f C\n",
                static_cast<unsigned long>(last_seq), packet.p1 + packet.p2,
                powerFactor(packet.p1, packet.vrms, packet.i1), packet.city, packet.temp_c);
}

void onEspNowReceive(const esp_now_recv_info_t*, const uint8_t* data, int len) {
  if (len != sizeof(TelemetryPacket)) return;
  portENTER_CRITICAL(&packet_mux);
  memcpy(&pending_packet, data, sizeof(pending_packet));
  packet_ready = true;
  portEXIT_CRITICAL(&packet_mux);
}

void bootAnimation() {
  const uint32_t start = millis();
  while (millis() - start < 1800) {
    const float progress = (millis() - start) / 1800.0f;
    frame.fillSprite(BG);
    frame.fillRoundRect(255, 62, 90, 44, 12, TFT_BLACK);
    frame.pushImage(267, 69, CUC_LOGO_W, CUC_LOGO_H, CUC_LOGO);
    frame.setTextDatum(MC_DATUM);
    frame.setTextColor(TFT_WHITE, BG);
    frame.drawString("MEDIDOR DE ENERGIA", 300, 151, 6);
    frame.setTextColor(MUTED, BG);
    frame.drawString("PROYECTO CUC  |  ESP-NOW + LILYGO", 300, 194, 2);

    frame.drawLine(100, 284, 500, 284, LINE);
    const int nodes[] = {100, 300, 500};
    const char* labels[] = {"CAPTURA", "CALCULA", "VISUALIZA"};
    for (int i = 0; i < 3; ++i) {
      const float wave = sinf(millis() / 170.0f + i * 1.8f);
      frame.fillCircle(nodes[i], 284, 22 + int((wave + 1) * 3), PANEL);
      frame.drawCircle(nodes[i], 284, 23 + int((wave + 1) * 3), i == 1 ? YELLOW : CYAN);
      frame.fillCircle(nodes[i], 284, 7, i == 1 ? YELLOW : CYAN);
      frame.drawString(labels[i], nodes[i], 330, 2);
    }
    for (int i = 0; i < 5; ++i) {
      const float t = fmodf(progress * 3.0f + i / 5.0f, 1.0f);
      frame.fillCircle(100 + int(t * 400), 284, 4, i % 2 ? CYAN : YELLOW);
    }
    frame.fillRoundRect(100, 385, 400, 7, 3, PANEL_2);
    frame.fillRoundRect(100, 385, max(7, int(400 * progress)), 7, 3, CYAN);
    frame.setTextColor(DIM, BG);
    frame.drawString("INICIANDO TELEMETRIA", 300, 414, 1);
    frame.setTextDatum(TL_DATUM);
    amoled.pushColors(0, 0, amoled.width(), amoled.height(),
                      reinterpret_cast<uint16_t*>(frame.getPointer()));
    delay(35);
  }
}
}  // namespace

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  if (esp_now_init() == ESP_OK) esp_now_register_recv_cb(onEspNowReceive);
  else Serial.println("ESP-NOW INIT FAILED");

  // false habilita la microSD; la pantalla sigue arrancando aunque no haya tarjeta.
  if (!amoled.beginAMOLED_241(false, true)) while (true) delay(1000);
  amoled.setRotation(0);
  amoled.enableTouch();
  amoled.setBrightness(180);
  frame.createSprite(amoled.width(), amoled.height());
  frame.setSwapBytes(true);

  bootAnimation();

  sd_ready = mountSd();
  Serial.printf("LILYGO READY: %ux%u, MAC=%s, TOUCH=%s, SD=%s %lu MB\n",
                amoled.width(), amoled.height(), WiFi.macAddress().c_str(),
                amoled.hasTouch() ? "OK" : "NOT FOUND",
                sd_ready ? "OK" : "NOT FOUND", static_cast<unsigned long>(sd_capacity_mb));
  render();
}

void loop() {
  if (packet_ready) {
    TelemetryPacket packet;
    portENTER_CRITICAL(&packet_mux);
    memcpy(&packet, &pending_packet, sizeof(packet));
    packet_ready = false;
    portEXIT_CRITICAL(&packet_mux);
    acceptPacket(packet);
  }

  const uint32_t now = millis();
  static uint32_t last_sd_retry = 0;
  if (!sd_ready && now - last_sd_retry > 15000) {
    last_sd_retry = now;
    mountSd();
  }
  static uint32_t last_scan = 0;
  if ((!have_data || now - last_packet_ms > OFFLINE_MS) && now - last_scan > 5000) {
    last_scan = now;
    const int count = WiFi.scanNetworks(false, true);
    bool found = false;
    for (int i = 0; i < count; ++i) {
      if (WiFi.SSID(i) == LINK_AP) {
        esp_wifi_set_channel(WiFi.channel(i), WIFI_SECOND_CHAN_NONE);
        Serial.printf("ESP-NOW channel: %d\n", WiFi.channel(i));
        found = true;
        break;
      }
    }
    if (!found) Serial.printf("ESP-NOW beacon not found (%d networks)\n", count);
    WiFi.scanDelete();
  }

  // Lock and trigger a horizontal swipe while the finger is moving. Peak travel
  // is retained because this controller can briefly jump back before release.
  static bool touching = false;
  static bool gesture_consumed = false;
  static bool tap_fired = false;
  static int16_t touch_start_x = 0, touch_start_y = 0, touch_x = 0, touch_y = 0;
  static int best_dx = 0;
  static uint32_t touch_start_ms = 0;
  int16_t x = 0, y = 0;
  const bool touched = amoled.getPoint(&x, &y) > 0;
  if (touched) {
    touch_x = x; touch_y = y;
    if (!touching) {
      touching = true;
      gesture_consumed = false;
      tap_fired = false;
      touch_start_x = x; touch_start_y = y;
      best_dx = 0;
      touch_start_ms = now;
      touch_dragging = true;
      touch_drag_dx = 0;
      Serial.printf("TOUCH down x=%d y=%d\n", x, y);
      if (x < 0 || x >= amoled.width() || y < 0 || y >= amoled.height()) {
        Serial.printf("TOUCH coordinate outside %ux%u\n", amoled.width(), amoled.height());
      }
    } else if (!gesture_consumed) {
      const int current_dx = x - touch_start_x;
      const int current_dy = y - touch_start_y;
      if (abs(current_dx) > abs(best_dx)) best_dx = current_dx;
      touch_drag_dx = best_dx;
      const bool horizontal = abs(best_dx) >= 14 && abs(best_dx) * 4 >= abs(current_dy) * 3;
      if (horizontal && abs(best_dx) >= 34) {
        changeScreenBySwipe(best_dx);
        gesture_consumed = true;
        touch_dragging = false;
      } else if (!tap_fired && now - touch_start_ms >= 90 &&
                 abs(best_dx) <= 12 && abs(current_dy) <= 18 &&
                 touch_start_x >= 0 && touch_start_x < amoled.width() &&
                 touch_start_y >= 0 && touch_start_y < amoled.height()) {
        dispatchTap(touch_start_x, touch_start_y);
        tap_fired = true;
        Serial.printf("TOUCH stable tap x=%d y=%d\n", touch_start_x, touch_start_y);
      }
    }
  } else if (touching) {
    touching = false;
    touch_dragging = false;
    const int endpoint_dx = touch_x - touch_start_x;
    const int dy = touch_y - touch_start_y;
    if (abs(endpoint_dx) > abs(best_dx)) best_dx = endpoint_dx;
    Serial.printf("TOUCH up x=%d y=%d peak_dx=%d dy=%d\n", touch_x, touch_y, best_dx, dy);
    const bool horizontal = abs(best_dx) >= 12 && abs(best_dx) * 4 >= abs(dy) * 3;
    if (!gesture_consumed && horizontal && abs(best_dx) >= 26) {
      changeScreenBySwipe(best_dx);
    } else if (!gesture_consumed && !tap_fired &&
               touch_start_x >= 0 && touch_start_x < amoled.width() &&
               touch_start_y >= 0 && touch_start_y < amoled.height()) {
      dispatchTap(touch_start_x, touch_start_y);
      Serial.printf("TOUCH tap x=%d y=%d\n", touch_start_x, touch_start_y);
    } else if (!gesture_consumed) {
      Serial.println("TOUCH gesture ignored");
    }
  }
  if (double_tap_waiting && now > double_tap_deadline) {
    double_tap_waiting = false;
    Serial.println("TOUCH double tap expired");
  }
  if (now - last_draw_ms >= DRAW_MS) {
    last_draw_ms = now;
    updateShown();
    render();
  }
  delay(2);
}
