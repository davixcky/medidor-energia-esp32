#pragma once
#include <stdint.h>
namespace ajustes_ui {
// Gray-code quadrature: reject two-bit jumps; four valid edges make one detent.
inline __attribute__((always_inline)) int transition(uint8_t before, uint8_t after) {
  const int a = before ^ (before >> 1), b = after ^ (after >> 1);
  const int d = (b - a + 4) % 4;
  return d == 1 ? 1 : d == 3 ? -1 : 0;
}
struct Values {
  int brightness; bool muted; int threshold;
  Values(int b = 200, bool m = false, int t = 2000) : brightness(b), muted(m), threshold(t) {}
};
inline int clamp(int x, int lo, int hi) { return x < lo ? lo : x > hi ? hi : x; }
struct Menu {
  Values values, draft;
  bool active = false, editing = false;
  int row = 0;
  void turn(int delta) {
    if (!active) return;
    if (!editing) { row = ((row + delta) % 4 + 4) % 4; return; }
    if (row == 0) draft.brightness = clamp(draft.brightness + delta * 8, 32, 255);
    if (row == 1 && delta % 2) draft.muted = !draft.muted;
    if (row == 2) draft.threshold = clamp(draft.threshold + delta * 100, 100, 10000);
  }
  // True only when an edit is committed; caller persists to NVS once.
  bool press() {
    if (!active) { active = true; row = 0; editing = false; return false; }
    if (row == 3) { active = false; return false; }
    if (!editing) { draft = values; editing = true; return false; }
    values = draft; editing = false; return true;
  }
  void cancel() { if (editing) { editing = false; draft = values; } else active = false; }
};
}
