// Dibuja las pantallas de la LCD en el PC con el mismo código del firmware (lib/interfaz) y las
// guarda como PPM de 320 × 170. Comprueba además que dibujar por franjas da la misma imagen que
// dibujar sobre un lienzo completo.
//   make pantallas        # escribe salida/*.ppm y ../../img/ui-lcd-*.png
#include <stdio.h>

#include "interfaz.h"

using namespace interfaz;

static Datos ejemplo() {
  Datos d{};
  medicion::Resultado& r = d.r;
  r.v_rms = 121.3f;
  r.f_hz = 60.01f;
  r.i_rms[0] = 12.64f; r.p[0] = 1438; r.s[0] = 1533; r.q[0] = 531; r.fp[0] = 0.94f;
  r.i_rms[1] = 4.08f;  r.p[1] = 482;  r.s[1] = 495;  r.q[1] = 113; r.fp[1] = 0.97f;
  r.thd_i1 = 6.8f;
  r.valido = true;
  const float perfil[24] = {0.31f, 0.27f, 0.26f, 0.25f, 0.26f, 0.33f, 0.52f, 0.71f, 0.48f, 0.36f,
                            0.34f, 0.39f, 0.58f, 0.49f, 0.37f, 0.35f, 0.41f, 0.62f, 0.88f, 0.54f,
                            0, 0, 0, 0};
  d.hora = 19;
  for (int h = 0; h < 24; ++h) {
    d.energia_hora_kwh[h] = perfil[h];
    d.energia_hoy_kwh += perfil[h];
  }
  d.wifi = true;
  d.rssi = -61;
  d.servidor_ok = true;
  d.bufer = 3;
  d.umbral_w = 2000;
  d.alerta_min = 7;
  d.canal_tara = 0;
  d.ruido_tara = 0.06f;
  d.version = "fw-v1.3.0";
  return d;
}

static bool guardar(const char* ruta, const uint16_t* px) {
  FILE* f = fopen(ruta, "wb");
  if (!f) return false;
  fprintf(f, "P6\n%d %d\n255\n", ANCHO, ALTO);
  for (int k = 0; k < ANCHO * ALTO; ++k) {
    uint16_t c = px[k];
    uint8_t rgb[3] = {(uint8_t)((c >> 11) * 255 / 31), (uint8_t)(((c >> 5) & 63) * 255 / 63),
                      (uint8_t)((c & 31) * 255 / 31)};
    fwrite(rgb, 1, 3, f);
  }
  fclose(f);
  return true;
}

int main(int argc, char** argv) {
  const char* dir = argc > 1 ? argv[1] : "salida";
  struct { Pantalla p; const char* nombre; } lista[] = {
      {RESUMEN, "resumen"}, {CH1, "ch1"}, {CH2, "ch2"}, {ENERGIA, "energia"},
      {ALERTA, "alerta"}, {TARA, "tara"}, {ARRANQUE, "arranque"},
  };
  Datos d = ejemplo();
  GFXcanvas16 completo(ANCHO, ALTO);
  const int alto_franja = 34;
  Franja franja(alto_franja);
  static uint16_t compuesta[ANCHO * ALTO];
  int fallos = 0;
  for (auto& e : lista) {
    // En la alerta, CH1 está sobre el umbral.
    d.r.p[0] = e.p == ALERTA ? 2310 : 1438;
    dibujar(completo, e.p, d);
    for (int y0 = 0; y0 < ALTO; y0 += alto_franja) {
      franja.origen(y0);
      dibujar(franja, e.p, d);
      memcpy(compuesta + y0 * ANCHO, franja.getBuffer(), sizeof(uint16_t) * ANCHO * alto_franja);
    }
    bool igual = memcmp(compuesta, completo.getBuffer(), sizeof compuesta) == 0;
    fallos += !igual;
    char ruta[256];
    snprintf(ruta, sizeof ruta, "%s/%s.ppm", dir, e.nombre);
    if (!guardar(ruta, completo.getBuffer())) {
      fprintf(stderr, "No se pudo escribir %s\n", ruta);
      return 1;
    }
    printf("%-9s franjas %s  %s\n", e.nombre, igual ? "iguales" : "DISTINTAS", ruta);
  }
  dibujar_ajustes(completo, 0, true, 200, false, 2000);
  for(int y0=0;y0<ALTO;y0+=alto_franja) {
    franja.origen(y0);dibujar_ajustes(franja,0,true,200,false,2000);
    memcpy(compuesta+y0*ANCHO,franja.getBuffer(),sizeof(uint16_t)*ANCHO*alto_franja);
  }
  bool same=memcmp(compuesta,completo.getBuffer(),sizeof compuesta)==0;
  fallos+=!same;
  char config_path[256];snprintf(config_path,sizeof config_path,"%s/configuracion.ppm",dir);
  if(!guardar(config_path,completo.getBuffer()))return 1;
  printf("Configuracion: franjas %s\n",same ? "iguales" : "DISTINTAS");
  return fallos ? 1 : 0;
}
