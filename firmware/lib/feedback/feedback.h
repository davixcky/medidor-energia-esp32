#pragma once
#include <stdint.h>
// Pure timing logic: no delays, rollover-safe elapsed times.
namespace feedback {
struct Sound {
  bool muted = false, previousAlert = false;
  uint32_t started = 0;
  uint8_t pattern = 0;
  void stop() { pattern = 0; }
  void click(uint32_t now) { if (!muted && pattern != 2) { started = now; pattern = 1; } }
  void toggle() { muted = !muted; stop(); }
  bool tick(uint32_t now, bool alert) {
    if (alert && !previousAlert && !muted) { started = now; pattern = 2; }
    if (!alert && previousAlert && pattern == 2) stop();
    previousAlert = alert;
    if (muted) { stop(); return false; }
    const uint32_t age = now - started;
    if (pattern == 1) { if (age < 30) return true; stop(); }
    if (pattern == 2) {
      if (age >= 240) { stop(); return false; }
      return age < 80 || age >= 160;
    }
    return false;
  }
};
}
