#include "interfaz.h"

#include <Fonts/FreeSans9pt7b.h>
#include <Fonts/FreeSansBold12pt7b.h>
#include <Fonts/FreeSansBold24pt7b.h>
#include <Fonts/FreeSansBold9pt7b.h>
#include <stdio.h>
#include <string.h>

namespace interfaz {

// ---------------------------------------------------------------- colores (RGB565)
static constexpr uint16_t rgb(uint8_t r, uint8_t g, uint8_t b) {
  return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
}
static constexpr uint16_t FONDO = rgb(0x14, 0x10, 0x12);
static constexpr uint16_t PANEL = rgb(0x2A, 0x22, 0x25);
static constexpr uint16_t TEXTO = rgb(0xF6, 0xF1, 0xEE);
static constexpr uint16_t TENUE = rgb(0x9A, 0x8E, 0x90);
static constexpr uint16_t ROJO = rgb(0xE0, 0x3A, 0x2E);
static constexpr uint16_t AMBAR = rgb(0xE8, 0xA3, 0x3D);
static constexpr uint16_t AZUL = rgb(0x5B, 0x9B, 0xD5);
static constexpr uint16_t VERDE = rgb(0x5C, 0xB8, 0x72);
static constexpr uint16_t NEGRO = rgb(0x00, 0x00, 0x00);
static constexpr uint16_t GRIS = rgb(0x4A, 0x40, 0x43);

enum Alineacion { IZQ, CENTRO, DER };

// ---------------------------------------------------------------- piezas de dibujo
// Escribe `s` con la línea base en y. Devuelve la x donde termina el texto.
static int16_t texto(Adafruit_GFX& g, const GFXfont* f, uint16_t color, int16_t x, int16_t y,
                     const char* s, Alineacion a = IZQ) {
  g.setFont(f);
  g.setTextSize(1);
  g.setTextColor(color);
  int16_t x1, y1;
  uint16_t w, h;
  g.getTextBounds(s, 0, y, &x1, &y1, &w, &h);
  if (a == CENTRO) x -= (int16_t)(w / 2) + x1;
  else if (a == DER) x -= (int16_t)w + x1;
  g.setCursor(x, y);
  g.print(s);
  return g.getCursorX();
}

// Etiqueta pequeña en mayúsculas (fuente de 5 × 7 del GFX), con la esquina superior en (x, y).
static void etiqueta(Adafruit_GFX& g, int16_t x, int16_t y, const char* s, uint16_t color = TENUE) {
  g.setFont(nullptr);
  g.setTextSize(1);
  g.setTextColor(color);
  g.setCursor(x, y);
  g.print(s);
}

static void intensidad_wifi(Adafruit_GFX& g, int16_t x, int16_t base, const Datos& d) {
  int barras = !d.wifi ? 0 : d.rssi > -55 ? 4 : d.rssi > -65 ? 3 : d.rssi > -75 ? 2 : 1;
  for (int k = 0; k < 4; ++k) {
    int16_t h = 4 + 3 * k;
    g.fillRect(x + 5 * k, base - h, 3, h, k < barras ? TEXTO : GRIS);
  }
  if (!d.wifi) {
    g.drawLine(x - 1, base - 13, x + 18, base, ROJO);
    g.drawLine(x - 1, base - 12, x + 18, base + 1, ROJO);
  }
}

// Barra superior: marca de color, título, puntos de página y señal Wi-Fi.
static void encabezado(Adafruit_GFX& g, const char* titulo, uint16_t acento, int pagina,
                       const Datos& d, uint16_t fondo = PANEL, uint16_t color = TEXTO) {
  g.fillRect(0, 0, ANCHO, 26, fondo);
  g.fillRect(0, 0, 4, 26, acento);
  texto(g, &FreeSansBold9pt7b, color, 12, 19, titulo);
  if (pagina > 0) {
    for (int k = 0; k < 4; ++k) {
      int16_t cx = 246 + 9 * k;
      if (k + 1 == pagina) g.fillCircle(cx, 13, 3, TEXTO);
      else g.drawCircle(cx, 13, 2, TENUE);
    }
  }
  intensidad_wifi(g, 292, 20, d);
}

// Valor principal: número grande y unidad a continuación, con la línea base en y.
static void valor_grande(Adafruit_GFX& g, int16_t x, int16_t y, const char* numero,
                         const char* unidad, uint16_t color = TEXTO) {
  int16_t fin = texto(g, &FreeSansBold24pt7b, color, x, y, numero);
  texto(g, &FreeSansBold12pt7b, TENUE, fin + 6, y, unidad);
}

// Celda de la rejilla inferior: etiqueta arriba y valor debajo.
static void celda(Adafruit_GFX& g, int16_t x, int16_t y, const char* nombre, const char* valor,
                  uint16_t color = TEXTO) {
  etiqueta(g, x, y, nombre);
  texto(g, &FreeSansBold9pt7b, color, x, y + 22, valor);
}

static void barra(Adafruit_GFX& g, int16_t x, int16_t y, int16_t w, int16_t h, float fraccion,
                  uint16_t color) {
  if (fraccion < 0) fraccion = 0;
  if (fraccion > 1) fraccion = 1;
  g.fillRect(x, y, w, h, PANEL);
  g.fillRect(x, y, (int16_t)(w * fraccion + 0.5f), h, color);
}

// ---------------------------------------------------------------- pantallas
static void resumen(Adafruit_GFX& g, const Datos& d) {
  const medicion::Resultado& r = d.r;
  char b[24], u[24];
  encabezado(g, "RESUMEN", ROJO, 1, d);
  etiqueta(g, 12, 36, "POTENCIA TOTAL (CH1)");
  snprintf(b, sizeof b, "%.0f", r.p[0]);
  valor_grande(g, 10, 82, b, "W");
  barra(g, 12, 90, 296, 6, r.p[0] / 7200.0f, ROJO);
  snprintf(b, sizeof b, "%.1f V", r.v_rms);
  celda(g, 12, 106, "TENSION", b);
  snprintf(b, sizeof b, "%.2f A", r.i_rms[0]);
  celda(g, 116, 106, "CORRIENTE", b);
  snprintf(b, sizeof b, "%.2f", r.fp[0]);
  celda(g, 220, 106, "FACTOR POT.", b);
  snprintf(b, sizeof b, "%.2f Hz", r.f_hz);
  celda(g, 12, 138, "FRECUENCIA", b);
  snprintf(b, sizeof b, "%.0f W", r.p[1]);
  celda(g, 116, 138, "CH2", b, AZUL);
  snprintf(u, sizeof u, "%.0f W", r.p[0] - r.p[1]);
  celda(g, 220, 138, "RESTO", u);
}

static void canal(Adafruit_GFX& g, const Datos& d, int c) {
  const medicion::Resultado& r = d.r;
  char b[24];
  uint16_t acento = c == 0 ? ROJO : AZUL;
  float escala = c == 0 ? 60.0f : 30.0f;
  encabezado(g, c == 0 ? "CH1  TOTAL" : "CH2  SUBCIRCUITO", acento, c + 2, d);
  etiqueta(g, 12, 36, "CORRIENTE EFICAZ");
  snprintf(b, sizeof b, "%.2f", r.i_rms[c]);
  valor_grande(g, 10, 82, b, "A");
  barra(g, 12, 90, 296, 6, r.i_rms[c] / escala, acento);
  snprintf(b, sizeof b, "%.0f A", escala);
  etiqueta(g, 308 - 6 * (int16_t)strlen(b), 36, b);
  snprintf(b, sizeof b, "%.0f W", r.p[c]);
  celda(g, 12, 106, "POTENCIA", b);
  snprintf(b, sizeof b, "%.0f VA", r.s[c]);
  celda(g, 116, 106, "APARENTE", b);
  snprintf(b, sizeof b, "%.2f", r.fp[c]);
  celda(g, 220, 106, "FACTOR POT.", b);
  snprintf(b, sizeof b, "%.0f var", r.q[c]);
  celda(g, 12, 138, "REACTIVA", b);
  if (c == 0) snprintf(b, sizeof b, "%.1f %%", r.thd_i1);
  else snprintf(b, sizeof b, "-");
  celda(g, 116, 138, "THD CORRIENTE", b);
  snprintf(b, sizeof b, "%.1f V", r.v_rms);
  celda(g, 220, 138, "TENSION", b);
}

static void energia(Adafruit_GFX& g, const Datos& d) {
  char b[24];
  encabezado(g, "ENERGIA HOY", AMBAR, 4, d);
  etiqueta(g, 12, 36, "CONSUMO DEL DIA (CH1)");
  snprintf(b, sizeof b, "%.2f", d.energia_hoy_kwh);
  valor_grande(g, 10, 82, b, "kWh");

  // Estado de la conexión, a la derecha del valor principal.
  g.fillCircle(222, 43, 3, d.wifi ? VERDE : ROJO);
  if (d.wifi) snprintf(b, sizeof b, "WIFI %d dBm", d.rssi);
  else snprintf(b, sizeof b, "WIFI SIN RED");
  etiqueta(g, 230, 40, b, TEXTO);
  g.fillCircle(222, 58, 3, d.servidor_ok ? VERDE : AMBAR);
  etiqueta(g, 230, 55, d.servidor_ok ? "SERVIDOR OK" : "SIN ENVIO", TEXTO);
  g.fillCircle(222, 73, 3, d.bufer < 60 ? VERDE : AMBAR);
  snprintf(b, sizeof b, "BUFER %u", d.bufer);
  etiqueta(g, 230, 70, b, TEXTO);

  // Energía por hora del día en curso; la hora actual va en ámbar.
  etiqueta(g, 12, 94, "kWh POR HORA");
  const int16_t x0 = 12, y_base = 150, alto = 44;
  float maximo = 0.5f;
  for (float e : d.energia_hora_kwh) maximo = e > maximo ? e : maximo;
  for (int h = 0; h < 24; ++h) {
    int16_t x = x0 + (int16_t)(h * 12.4f);
    if (d.hora >= 0 && h > d.hora) {
      g.drawFastHLine(x, y_base - 1, 9, PANEL);
      continue;
    }
    int16_t hb = (int16_t)(d.energia_hora_kwh[h] / maximo * alto + 0.5f);
    if (hb < 1) hb = 1;
    g.fillRect(x, y_base - hb, 9, hb, h == d.hora ? AMBAR : ROJO);
  }
  g.drawFastHLine(x0, y_base, 296, TENUE);
  for (int h = 0; h <= 24; h += 6) {
    snprintf(b, sizeof b, "%d", h);
    int16_t x = x0 + (int16_t)(h * 12.4f) - (h == 24 ? 10 : 0);
    etiqueta(g, x, y_base + 6, b);
  }
}

static void alerta(Adafruit_GFX& g, const Datos& d) {
  char b[40];
  encabezado(g, "! ALERTA  CH1", TEXTO, 0, d, ROJO, TEXTO);
  etiqueta(g, 12, 36, "POTENCIA SOSTENIDA");
  snprintf(b, sizeof b, "%.0f", d.r.p[0]);
  valor_grande(g, 10, 82, b, "W", ROJO);
  snprintf(b, sizeof b, "Sobre el umbral de %.0f W", d.umbral_w);
  texto(g, &FreeSans9pt7b, TEXTO, 12, 112, b);
  snprintf(b, sizeof b, "Durante %u min", d.alerta_min);
  texto(g, &FreeSans9pt7b, TEXTO, 12, 134, b);
  g.fillRect(0, 146, ANCHO, 24, AMBAR);
  texto(g, &FreeSansBold9pt7b, NEGRO, ANCHO / 2, 163, "SW2: RECONOCER", CENTRO);
}

static void tara(Adafruit_GFX& g, const Datos& d) {
  char b[24];
  encabezado(g, d.canal_tara == 0 ? "TARA  CH1" : "TARA  CH2", AMBAR, 0, d);
  texto(g, &FreeSans9pt7b, TEXTO, 12, 50, "Retire la carga del canal.");
  etiqueta(g, 12, 64, "RUIDO MEDIDO SIN CARGA");
  snprintf(b, sizeof b, "%.2f", d.ruido_tara);
  valor_grande(g, 10, 112, b, "A", AMBAR);
  g.fillRect(0, 146, ANCHO, 24, PANEL);
  etiqueta(g, 12, 154, "SW2 2 s: GUARDAR", TEXTO);
  etiqueta(g, 214, 154, "SW1: SALIR", TEXTO);
}

static void arranque(Adafruit_GFX& g, const Datos& d) {
  g.fillRect(140, 52, 40, 4, ROJO);
  texto(g, &FreeSansBold12pt7b, TEXTO, ANCHO / 2, 92, "MEDIDOR DE ENERGIA", CENTRO);
  etiqueta(g, ANCHO / 2 - 3 * (int16_t)strlen(d.version), 108, d.version);
  texto(g, &FreeSans9pt7b, TENUE, ANCHO / 2, 140, "Iniciando...", CENTRO);
}

void dibujar(Adafruit_GFX& g, Pantalla p, const Datos& d) {
  g.fillScreen(FONDO);
  switch (p) {
    case RESUMEN: resumen(g, d); break;
    case CH1: canal(g, d, 0); break;
    case CH2: canal(g, d, 1); break;
    case ENERGIA: energia(g, d); break;
    case ALERTA: alerta(g, d); break;
    case TARA: tara(g, d); break;
    case ARRANQUE: arranque(g, d); break;
    default: break;
  }
}

// ---------------------------------------------------------------- franja
// Coordenadas de pantalla completa; se recorta a las filas que cubre la franja.
void Franja::drawPixel(int16_t x, int16_t y, uint16_t color) {
  y -= y0_;
  if (x < 0 || x >= WIDTH || y < 0 || y >= HEIGHT) return;
  buffer[x + y * WIDTH] = color;
}

void Franja::drawFastHLine(int16_t x, int16_t y, int16_t w, uint16_t color) {
  fillRect(x, y, w, 1, color);
}

void Franja::drawFastVLine(int16_t x, int16_t y, int16_t h, uint16_t color) {
  fillRect(x, y, 1, h, color);
}

void Franja::fillRect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color) {
  y -= y0_;
  int16_t x1 = x + w, y1 = y + h;
  if (x < 0) x = 0;
  if (y < 0) y = 0;
  if (x1 > WIDTH) x1 = WIDTH;
  if (y1 > HEIGHT) y1 = HEIGHT;
  for (int16_t j = y; j < y1; ++j)
    for (int16_t i = x; i < x1; ++i) buffer[i + j * WIDTH] = color;
}

}  // namespace interfaz
