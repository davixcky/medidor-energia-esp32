#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WiFiManager.h>
#include <esp_now.h>
#include <telemetry_packet.h>
#include <time.h>

namespace {
constexpr uint8_t LILYGO_MAC[6] = {0xF0, 0xF5, 0xBD, 0x43, 0x1A, 0x9C};
constexpr char LINK_AP[] = "Medidor-Energy-Link";
constexpr char WEATHER_URL[] =
    "https://api.open-meteo.com/v1/forecast?latitude=10.9685&longitude=-74.7813"
    "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
    "&timezone=America%2FBogota";
constexpr uint32_t SEND_MS = 2000;
constexpr uint32_t WEATHER_MS = 10UL * 60UL * 1000UL;
constexpr char SETUP_AP[] = "MedidorEnergia-Setup";
constexpr char SETUP_PASSWORD[] = "medidor123";

const char PORTAL_HEAD[] PROGMEM = R"HTML(
<meta name="theme-color" content="#0b0e11">
<meta name="color-scheme" content="dark">
<style>
:root{--bg:#0b0e11;--panel:#151a20;--line:#2b333c;--ink:#f4f6f8;--muted:#929daa;--hot:#ffb547;--ok:#4bd3a5}
*{box-sizing:border-box}body{background:var(--bg)!important;color:var(--ink)!important;font-family:Inter,ui-sans-serif,system-ui,sans-serif!important;margin:0}
.wrap{max-width:520px!important;padding:24px 18px 40px!important}.wrap:before{content:'MEDIDOR / SETUP';display:block;color:var(--hot);font-size:12px;font-weight:800;letter-spacing:.18em;margin:10px 0 18px}
h1{font-size:30px!important;line-height:1.05!important;letter-spacing:-.04em;margin:0 0 12px!important}h2,h3{letter-spacing:-.02em}
form,.msg,.q{background:var(--panel)!important;border:1px solid var(--line)!important;border-radius:18px!important;padding:18px!important;box-shadow:none!important}
label{color:var(--muted)!important;font-size:13px!important;font-weight:700!important}input,select{background:#0e1216!important;border:1px solid var(--line)!important;border-radius:12px!important;color:var(--ink)!important;min-height:48px!important}
button,.btn,input[type=submit]{background:var(--hot)!important;border:0!important;border-radius:12px!important;color:#19130a!important;font-weight:800!important;min-height:48px!important;box-shadow:none!important}
button:hover,.btn:hover{filter:brightness(1.08)}a{color:var(--ok)!important}.s{color:var(--muted)!important}.medidor-note{background:#10151a;border-left:3px solid var(--ok);border-radius:8px;color:var(--muted);font-size:13px;line-height:1.5;margin:14px 0 20px;padding:12px 14px}.medidor-note b{color:var(--ink)}
</style>
)HTML";

uint32_t sequence = 0;
uint32_t last_send = 0;
uint32_t last_weather = 0;
float today_wh = 3250.0f;
TelemetryPacket climate;

bool addDisplayPeer() {
  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, LILYGO_MAC, sizeof(LILYGO_MAC));
  peer.channel = 0;
  peer.encrypt = false;
  return esp_now_add_peer(&peer) == ESP_OK;
}

void onEspNowSent(const esp_now_send_info_t*, esp_now_send_status_t status) {
  Serial.printf("ESP-NOW delivery=%s\n",
                status == ESP_NOW_SEND_SUCCESS ? "confirmed" : "failed");
}

void sendPacket(TelemetryPacket& packet) {
  packet.seq = ++sequence;
  const esp_err_t result = esp_now_send(
      LILYGO_MAC, reinterpret_cast<const uint8_t*>(&packet), sizeof(packet));
  Serial.printf("ESP-NOW seq=%lu channel=%d result=%s\n",
                static_cast<unsigned long>(packet.seq), WiFi.channel(),
                result == ESP_OK ? "queued" : esp_err_to_name(result));
}

bool fetchWeather(TelemetryPacket& packet) {
  WiFiClientSecure client;
  client.setInsecure();  // Demo: fijar la CA antes de produccion.
  HTTPClient http;
  http.useHTTP10(true);  // Evita respuestas chunked en el parser embebido.
  http.setTimeout(8000);
  if (!http.begin(client, WEATHER_URL)) return false;
  const int status = http.GET();
  if (status != HTTP_CODE_OK) {
    Serial.printf("WEATHER HTTP %d\n", status);
    http.end();
    return false;
  }
  const String payload = http.getString();
  http.end();
  JsonDocument doc;
  const DeserializationError error = deserializeJson(doc, payload);
  if (error) {
    Serial.printf("WEATHER JSON: %s, bytes=%u, prefix=%.48s\n",
                  error.c_str(), payload.length(), payload.c_str());
    return false;
  }
  packet.temp_c = doc["current"]["temperature_2m"] | 0.0f;
  packet.humidity = doc["current"]["relative_humidity_2m"] | 0;
  packet.weather_code = doc["current"]["weather_code"] | -1;
  packet.wind_kmh = doc["current"]["wind_speed_10m"] | 0.0f;
  strlcpy(packet.city, "Barranquilla", sizeof(packet.city));
  packet.internet = 1;
  return true;
}

TelemetryPacket makeTelemetry() {
  TelemetryPacket packet;
  const float phase = millis() / 9000.0f;
  packet.vrms = 120.1f + 0.8f * sinf(phase * 0.37f);
  packet.p1 = 760.0f + 280.0f * (0.5f + 0.5f * sinf(phase));
  packet.p2 = 210.0f + 190.0f * (0.5f + 0.5f * sinf(phase * 0.63f + 1.4f));
  const float pf1 = 0.94f + 0.035f * sinf(phase * 0.41f);
  const float pf2 = 0.87f + 0.055f * sinf(phase * 0.29f + 0.8f);
  packet.i1 = packet.p1 / (packet.vrms * pf1);
  packet.i2 = packet.p2 / (packet.vrms * pf2);
  packet.frequency_hz = 59.96f + 0.035f * sinf(phase * 0.21f);
  packet.rssi_dbm = WiFi.RSSI();
  today_wh += (packet.p1 + packet.p2) * (SEND_MS / 3600000.0f);
  packet.today_wh = today_wh;
  packet.temp_c = climate.temp_c;
  packet.humidity = climate.humidity;
  packet.weather_code = climate.weather_code;
  packet.wind_kmh = climate.wind_kmh;
  packet.internet = climate.internet;
  strlcpy(packet.city, climate.city[0] ? climate.city : "Sin clima", sizeof(packet.city));
  struct tm local_time {};
  if (getLocalTime(&local_time, 10)) {
    packet.local_hour = local_time.tm_hour;
    packet.local_minute = local_time.tm_min;
  }
  return packet;
}
}  // namespace

void setup() {
  Serial.begin(115200);
  delay(300);
  WiFi.mode(WIFI_STA);

  WiFiManager manager;
  manager.setHostname("medidor-energia");
  manager.setTitle("Configurar medidor de energia");
  manager.setDarkMode(true);
  manager.setCaptivePortalEnable(true);
  manager.setCustomHeadElement(PORTAL_HEAD);
  manager.setClass("invert");
  manager.setConnectTimeout(20);
  manager.setSaveConnectTimeout(25);
  manager.setBreakAfterConfig(true);
  manager.setShowInfoUpdate(false);
  manager.setShowInfoErase(false);
  const char* menu[] = {"wifi", "info", "sep", "restart", "exit"};
  manager.setMenu(menu, 5);
  WiFiManagerParameter intro(
      "<div class='medidor-note'><b>Conecta el medidor a tu Wi-Fi.</b><br>"
      "El ESP32 principal obtiene clima y mediciones; la LilyGO se enlaza sola por ESP-NOW.</div>");
  manager.addParameter(&intro);
  manager.setAPCallback([](WiFiManager* portal) {
    Serial.printf("CAPTIVE PORTAL READY: ssid=%s ip=%s\n",
                  portal->getConfigPortalSSID().c_str(), WiFi.softAPIP().toString().c_str());
  });
  manager.setSaveConfigCallback([]() {
    Serial.println("CAPTIVE PORTAL: credentials validated and saved");
  });
  Serial.printf("WIFI: captive setup %s (password %s)\n", SETUP_AP, SETUP_PASSWORD);
  if (!manager.autoConnect(SETUP_AP, SETUP_PASSWORD)) {
    Serial.println("WIFI SETUP CLOSED; restarting");
    delay(1000);
    ESP.restart();
  }

  // Beacon protegido: LilyGO descubre el canal sin unirse ni acceder a Internet.
  const uint8_t station_channel = WiFi.channel();
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(LINK_AP, "display-only", station_channel, false, 1);
  if (esp_now_init() != ESP_OK || !addDisplayPeer()) {
    Serial.println("ESP-NOW INIT FAILED");
    while (true) delay(1000);
  }
  esp_now_register_send_cb(onEspNowSent);
  Serial.printf("MAIN READY mac=%s ip=%s channel=%u\n",
                WiFi.macAddress().c_str(), WiFi.localIP().toString().c_str(),
                station_channel);
  configTzTime("COT5", "pool.ntp.org", "time.google.com");
  strlcpy(climate.city, "Sin clima", sizeof(climate.city));
  last_weather = millis() - WEATHER_MS;
  last_send = millis() - SEND_MS;
}

void loop() {
  if (Serial.available()) {
    const String command = Serial.readStringUntil('\n');
    if (command == "portal" || command == "portal\r") {
      Serial.println("Erasing Wi-Fi credentials and reopening captive portal...");
      WiFiManager manager;
      manager.resetSettings();
      delay(500);
      ESP.restart();
    }
  }
  const uint32_t now = millis();
  if (now - last_weather >= WEATHER_MS) {
    last_weather = now;
    const bool live = fetchWeather(climate);
    Serial.printf("WEATHER %s: %s %.1f C, mock %.0f W\n",
                  live ? "LIVE" : "OFFLINE", climate.city, climate.temp_c, 0.0f);
  }
  if (now - last_send >= SEND_MS) {
    last_send = now;
    TelemetryPacket packet = makeTelemetry();
    sendPacket(packet);
  }
  delay(10);
}
