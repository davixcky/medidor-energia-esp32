#pragma once

#include <stdint.h>

// Paquete binario compacto: ESP-NOW v1 admite como maximo 250 bytes.
// Los dos firmwares validan magic/version/size antes de usarlo.
struct __attribute__((packed)) TelemetryPacket {
  uint32_t magic = 0x4D454E45;  // "ENEM" little-endian
  uint16_t version = 1;
  uint16_t size = sizeof(TelemetryPacket);
  uint32_t seq = 0;
  float vrms = 0;
  float i1 = 0;
  float i2 = 0;
  float p1 = 0;
  float p2 = 0;
  float today_wh = 0;
  float temp_c = 0;
  float wind_kmh = 0;
  float frequency_hz = 60;
  int16_t rssi_dbm = -100;
  int16_t humidity = 0;
  int16_t weather_code = -1;
  uint8_t local_hour = 0;
  uint8_t local_minute = 0;
  uint8_t alert = 0;
  uint8_t internet = 0;
  char city[24] = {};
};

static_assert(sizeof(TelemetryPacket) < 250, "ESP-NOW payload too large");

