// Lo mínimo del entorno Arduino para compilar Adafruit GFX y la interfaz en el PC.
#pragma once
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "Print.h"

#define PROGMEM
#define pgm_read_byte(a) (*(const uint8_t*)(a))
#define pgm_read_word(a) (*(const uint16_t*)(a))
#define pgm_read_dword(a) (*(const uint32_t*)(a))
#define pgm_read_pointer(a) (*(void* const*)(a))
#define radians(g) ((g) * M_PI / 180.0)
#define degrees(r) ((r) * 180.0 / M_PI)
typedef bool boolean;
typedef uint8_t byte;
