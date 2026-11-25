// Escribe en la salida estándar registros ADR-001 codificados con el mismo código del
// firmware, para comprobar que el servidor los acepta:
//   ./trama | curl --data-binary @- -H 'Content-Type: application/octet-stream' URL/api/ingesta
#include <cstdio>
#include <ctime>

#include "../lib/adr001/adr001.h"

int main() {
  uint32_t ahora = (uint32_t)time(nullptr);
  for (int k = 0; k < 3; ++k) {
    adr001::Registro r{ahora - 2 + k, 120.4f, {12.76f, 3.05f, 0}, {1371, 335, 0}, {664, 110, 0},
                       {1536, 367, 0}, {0.8926f, 0.9128f, 1.0f}, 60.01f, 7.8f};
    uint8_t b[adr001::TAMANO];
    adr001::codificar(r, b);
    fwrite(b, 1, sizeof b, stdout);
  }
  return 0;
}
