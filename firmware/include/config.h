// Configuración del hardware y constantes de calibración.
// Los pines coinciden con la Tabla 3 del documento y con el esquemático.
#pragma once
#include <driver/adc.h>

// ---- Entradas analógicas (solo ADC1: el ADC2 no funciona con Wi-Fi)
constexpr adc1_channel_t ADC_CH1 = ADC1_CHANNEL_0;  // GPIO36, pinza CH1 (total)
constexpr adc1_channel_t ADC_CH2 = ADC1_CHANNEL_3;  // GPIO39, pinza CH2 (subcircuito)
constexpr adc1_channel_t ADC_V   = ADC1_CHANNEL_7;  // GPIO35, ZMPT101B

// ---- Interfaz local
constexpr int PIN_LED = 25;
constexpr int PIN_SW1 = 26;   // menú / canal (activo en bajo, pull-up externo de 10 kΩ)
constexpr int PIN_SW2 = 27;   // confirmar / tara
// LCD Waveshare de 1,9" (ST7789V2, 170 × 320) por SPI. Todos los pines están en el mismo lado
// de la tarjeta (J3 del DevKitC); se evitan GPIO5 y GPIO15, que son pines de arranque.
constexpr int PIN_LCD_CLK = 18;   // SCK del VSPI
constexpr int PIN_LCD_DIN = 23;   // MOSI del VSPI
constexpr int PIN_LCD_CS = 22;
constexpr int PIN_LCD_DC = 21;
constexpr int PIN_LCD_RST = 4;
constexpr int PIN_LCD_BL = 19;    // luz de fondo, con PWM
constexpr uint32_t LCD_SPI_HZ = 40000000;

// ---- Muestreo
constexpr uint32_t FS_HZ = 8000;        // muestras por segundo y por canal
constexpr int CICLOS_VENTANA = 60;      // ventana de 60 ciclos enteros (1 s a 60 Hz)
constexpr uint32_t DESCARTE_MS = 500;   // espera a que se estabilice VBIAS al encender

// ---- Calibración nominal (se ajusta en banco contra una carga resistiva conocida)
// Corriente: A de primario por voltio en el pin = relación 2000 / resistencia de carga.
constexpr float K_I1 = 2000.0f / 22.0f;   // CH1, burden 22 Ω
constexpr float K_I2 = 2000.0f / 47.0f;   // CH2, burden 47 Ω
// Tensión: V de red por voltio en el pin. 120 V eficaces → 0,352 V pico en el pin
// (potenciómetro del módulo en 0,65 V pico y divisor 13/24): 169,7 / 0,352 = 482.
constexpr float K_V = 482.0f;
// Corrección de fase de cada pinza, en grados a 60 Hz (positivo = la corriente adelanta).
constexpr float FASE_CT1_GRADOS = 0.0f;
constexpr float FASE_CT2_GRADOS = 0.0f;
// Constante de tiempo de los filtros antialias (para compensar armónicos en el THD).
constexpr float TAU_FILTRO_S = 156e-6f;

// ---- Alerta local (el servidor calcula el umbral P95; esto es el respaldo sin red)
constexpr float UMBRAL_ALERTA_W = 2000.0f;
constexpr uint32_t ALERTA_SOSTENIDA_S = 300;

// ---- Red
constexpr uint32_t ENVIO_CADA_MS = 5000;    // lote de registros cada 5 s
constexpr size_t BUFER_REGISTROS = 1200;    // 20 min sin red en RAM (48 kB)
