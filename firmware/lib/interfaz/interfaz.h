// Pantallas de la interfaz local para la LCD Waveshare de 1,9" (ST7789V2, 170 × 320, en
// horizontal: 320 × 170). Solo dibuja sobre un Adafruit_GFX, así que el mismo código corre en el
// ESP32 y en el PC (test/pantallas.cpp genera las imágenes del documento con él).
#pragma once
#include <Adafruit_GFX.h>
#include <stdint.h>

#include "medicion.h"

namespace interfaz {

constexpr int ANCHO = 320;
constexpr int ALTO = 170;

enum Pantalla { RESUMEN, CH1, CH2, ENERGIA, N_CICLO, ALERTA, TARA, ARRANQUE };

// Todo lo que muestra la pantalla. El firmware lo llena desde sus variables de estado.
struct Datos {
  medicion::Resultado r;
  float energia_hoy_kwh;
  float energia_hora_kwh[24];     // energía de CH1 en cada hora del día en curso
  int hora;                       // hora local (0 a 23), −1 sin hora de NTP
  bool wifi;
  int rssi;                       // dBm
  bool servidor_ok;               // último lote aceptado hace menos de 15 s
  unsigned bufer;                 // registros pendientes de envío
  float umbral_w;
  unsigned alerta_min;            // minutos sobre el umbral
  int canal_tara;
  float ruido_tara;               // A, piso de ruido guardado del canal en tara
  const char* version;
};

// Dibuja la pantalla completa. `g` puede ser la LCD, un lienzo completo o una franja.
void dibujar(Adafruit_GFX& g, Pantalla p, const Datos& d);
void dibujar_ajustes(Adafruit_GFX& g, int selected, bool editing, int brightness, bool muted, int threshold);

// Lienzo de 16 bits que cubre solo las filas [y0, y0 + alto) de la pantalla. Dibujar la pantalla
// por franjas y enviar cada una evita el parpadeo sin reservar los 109 kB de un lienzo completo.
class Franja : public GFXcanvas16 {
 public:
  Franja(int16_t alto) : GFXcanvas16(ANCHO, alto) { _height = ALTO; }
  void origen(int16_t y0) { y0_ = y0; }
  int16_t origen() const { return y0_; }
  void drawPixel(int16_t x, int16_t y, uint16_t color) override;
  void drawFastHLine(int16_t x, int16_t y, int16_t w, uint16_t color) override;
  void drawFastVLine(int16_t x, int16_t y, int16_t h, uint16_t color) override;
  void fillRect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color) override;

 private:
  int16_t y0_ = 0;
};

}  // namespace interfaz
