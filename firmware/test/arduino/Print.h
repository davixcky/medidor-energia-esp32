#pragma once
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

class __FlashStringHelper;

// Cadena mínima: Adafruit GFX solo le pide length() y c_str().
class String {
 public:
  String(const char* s = "") : s_(s) {}
  unsigned length() const { return strlen(s_); }
  const char* c_str() const { return s_; }

 private:
  const char* s_;
};

class Print {
 public:
  virtual ~Print() {}
  virtual size_t write(uint8_t c) = 0;
  size_t write(const char* s) {
    size_t n = 0;
    while (*s) n += write((uint8_t)*s++);
    return n;
  }
  size_t print(const char* s) { return write(s); }
  size_t printf(const char* f, ...) {
    char b[128];
    va_list a;
    va_start(a, f);
    vsnprintf(b, sizeof b, f, a);
    va_end(a);
    return write(b);
  }
};
