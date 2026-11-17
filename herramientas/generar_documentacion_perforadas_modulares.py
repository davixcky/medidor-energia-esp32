#!/usr/bin/env python3
"""Genera el plano PDF de la partición E.5 para tarjetas perforadas."""
from pathlib import Path

import pymupdf as fitz


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "hardware" / "medidor-energia.pdf"
OUT = ROOT / "hardware" / "perforadas-modulares" / "esquema-modular-perforadas.pdf"
A4L = (842, 595)
M = 30
BLUE = (0.04, 0.18, 0.48)
GREEN = (0.02, 0.43, 0.24)
RED = (0.75, 0.08, 0.08)
GRAY = (0.35, 0.35, 0.35)


def mmrect(src, x1, y1, x2, y2):
    return fitz.Rect(
        x1 * src.rect.width / 420,
        y1 * src.rect.height / 297,
        x2 * src.rect.width / 420,
        y2 * src.rect.height / 297,
    )


def page(doc, title, subtitle=""):
    p = doc.new_page(width=A4L[0], height=A4L[1])
    p.insert_text((M, 28), title, fontsize=17, fontname="hebo", color=BLUE)
    p.insert_text((M, 45), subtitle, fontsize=8.5, color=GRAY)
    p.draw_line((M, 52), (A4L[0] - M, 52), color=BLUE, width=0.8)
    p.insert_text((A4L[0] - 190, A4L[1] - 14), "Medidor E.5 · perforadas modulares", fontsize=7, color=GRAY)
    return p


def box(p, rect, title, lines, color=BLUE, size=8.2):
    p.draw_rect(rect, color=color, fill=(0.98, 0.98, 0.98), width=0.7)
    p.insert_text((rect.x0 + 8, rect.y0 + 16), title, fontsize=10, fontname="hebo", color=color)
    p.insert_textbox(
        fitz.Rect(rect.x0 + 8, rect.y0 + 29, rect.x1 - 8, rect.y1 - 7),
        "\n\n".join(lines), fontsize=size, lineheight=1.14, color=(0.08, 0.08, 0.08)
    )


def clip(p, master, src, target, coords, caption):
    p.insert_text((target.x0, target.y0 - 5), caption, fontsize=9, fontname="hebo", color=GREEN)
    body = fitz.Rect(target.x0, target.y0 + 2, target.x1, target.y1)
    p.show_pdf_page(body, master, 0, clip=mmrect(src, *coords), keep_proportion=True)
    p.draw_rect(body, color=(0.7, 0.7, 0.7), width=0.4)


def main():
    master = fitz.open(SRC)
    src = master[0]
    doc = fitz.open()

    p = page(doc, "Arquitectura modular del medidor",
             "Cinco tarjetas de muy baja tensión; la red de 120 V permanece en una guarda independiente")
    cards = [
        (fitz.Rect(35, 82, 175, 205), "T1 · POTENCIA", ["5,1 V", "PTC + Schottky", "estrella +5V/GND"]),
        (fitz.Rect(195, 82, 335, 205), "T2 · CORRIENTE", ["CH1 + CH2", "burdens en jacks", "VBIAS 1,32 V"]),
        (fitz.Rect(355, 82, 495, 205), "T3 · TENSIÓN MBT", ["salida ZMPT", "filtro + clamps", "V_ADC"]),
        (fitz.Rect(515, 82, 655, 205), "T4 · CONTROL", ["ESP32 + LCD", "botones + LEDs", "ADC1"]),
        (fitz.Rect(675, 82, 815, 205), "T5 · INTERFAZ", ["encoder", "HCT245 + WS2812", "piezo NPN"]),
    ]
    for rect, title, lines in cards:
        box(p, rect, title, lines, size=8)
    for x1, x2, label in ((175, 515, "+5V/GND"), (335, 515, "ADC-I"), (495, 515, "ADC-V"), (655, 675, "UI")):
        y = 145 if label != "+5V/GND" else 188
        p.draw_line((x1, y), (x2, y), color=GREEN, width=1.1)
        p.insert_text(((x1 + x2) / 2 - 12, y - 5), label, fontsize=6.5, color=GREEN)
    box(p, fitz.Rect(35, 260, 395, 505), "DISTRIBUCIÓN Y RETORNOS", [
        "T1 entrega un par +5V/GND independiente a T3, T4 y T5. No encadenar tarjetas.",
        "T4 entrega +3V3 y GND a T2/T3. Cada arnés ADC lleva su propio retorno GND.",
        "T2 y T3 lejos de Wi-Fi, LCD, piezo y NeoPixels. Cables analógicos cortos y trenzados con GND.",
        "VBIAS no es tierra ni se distribuye a las demás tarjetas.",
    ], size=9)
    box(p, fitz.Rect(425, 260, 815, 505), "Z1 · ZONA DE RED (NO PERFORADA)", [
        "J4, F1 y el primario del ZMPT101B van dentro de una guarda aislante cerrada.",
        "Solo +5V, GND y ZMPT_OUT del lado MBT llegan a T3.",
        "R1=22 ohm y R2=47 ohm se sueldan directamente en los jacks SCT para que el secundario nunca quede abierto.",
        "No energizar 120 V con la guarda abierta ni con USB/instrumentos no aislados conectados.",
    ], color=RED, size=9)

    p = page(doc, "T1 · alimentación protegida", "Montar y verificar antes de conectar cualquier otra tarjeta")
    clip(p, master, src, fitz.Rect(35, 82, 560, 285), (12, 25, 135, 70), "Circuito conservado del esquemático validado")
    box(p, fitz.Rect(590, 82, 815, 285), "MONTAJE", [
        "60 x 50 mm orientativo", "J1, F2, D1, C1 y C2", "Tres salidas independientes: T3, T4 y T5",
        "5,0-5,25 V bajo carga; fuente 5,1 V / 2 A mínimo",
    ])
    box(p, fitz.Rect(35, 325, 815, 510), "PRUEBA", [
        "Sin cargas: continuidad y polaridad. Encender con límite de 100 mA. Medir +5V_PROT en las tres salidas.",
        "No usar una fuente de 4,75 V / 500 mA: el caso simulado no mantiene el margen del regulador del ESP32.",
    ], size=9)

    p = page(doc, "T2 · dos canales de corriente y VBIAS",
             "Los burdens permanecen físicamente en los jacks de panel aunque pertenezcan eléctricamente a T2")
    clip(p, master, src, fitz.Rect(30, 72, 530, 390), (12, 68, 210, 190), "CH1, CH2 y polarización conservados")
    box(p, fitz.Rect(560, 82, 815, 390), "CONECTOR C_ADC_I", [
        "1  +3V3", "2  GND", "3  CH1_ADC → GPIO36", "4  CH2_ADC → GPIO39",
        "R1 = 22 ohm 1% en J2", "R2 = 47 ohm 1% en J3", "VBIAS esperado: 1,32 V ±1%",
    ], size=8.7)
    box(p, fitz.Rect(30, 430, 815, 525), "REGLA DE SEGURIDAD SCT", [
        "No colocar R1/R2 después de un arnés desconectable. Soldarlas directamente entre las terminales activas de cada jack y comprobar su valor antes de conectar la pinza."], color=RED, size=9)

    p = page(doc, "T3 · canal de tensión de muy baja tensión",
             "La tarjeta recibe únicamente +5V, GND y ZMPT_OUT del lado aislado del módulo")
    clip(p, master, src, fitz.Rect(30, 75, 560, 350), (70, 188, 250, 260), "Acondicionamiento V_ADC; Z1 se muestra solo para contexto")
    box(p, fitz.Rect(590, 82, 815, 350), "CONECTORES", [
        "Potencia desde T1: +5V / GND", "C_ZMPT: +5V / OUT / GND", "C_ADC_V hacia T4: +3V3 / GND / V_ADC",
        "70 x 50 mm orientativo", "J4 y F1 NO se montan aquí",
    ])
    box(p, fitz.Rect(30, 400, 815, 520), "PRUEBA SIN RED", [
        "Inyectar señal pequeña alrededor de 2,5 V en ZMPT_OUT y confirmar que V_ADC queda entre 0,15 y 2,45 V. La primera prueba con 120 V solo se hace al final y con Z1 cerrada."], size=9)

    p = page(doc, "T4 · ESP32, LCD y panel", "Tarjeta central; recibe los tres ADC y distribuye +3V3")
    clip(p, master, src, fitz.Rect(30, 72, 610, 410), (220, 70, 410, 245), "Control conservado del esquemático")
    box(p, fitz.Rect(635, 82, 815, 410), "CAMBIOS E.5", [
        "100 x 80 mm", "ESP32 en 2 x zócalo 1x19", "GPIO32/33: encoder", "GPIO16: pulsador encoder",
        "GPIO34: única reserva ADC", "GPIO13: LED_DATA", "GPIO14: BUZZ",
    ], size=8.2)
    box(p, fitz.Rect(30, 455, 815, 525), "NO INSERTAR EL ESP32 HASTA MEDIR", [
        "+5V, +3V3, GND y ausencia de tensión fuera de rango en CH1_ADC, CH2_ADC y V_ADC."], size=9)

    p = page(doc, "T5 · encoder, NeoPixels y piezo", "Interfaz ruidosa separada de los tres canales analógicos")
    box(p, fitz.Rect(30, 72, 395, 275), "NEOPIXEL · 74HCT245N DIP-20", [
        "1 DIR → +5V; 19 /OE → GND; 20 VCC → +5V; 10 → GND.",
        "2 A0 ← GPIO13; 18 B0 → 330 ohm → DIN. A1-A7 (3-9) a GND; B1-B7 (11-17) NC.",
        "100 nF pegado a 20/10; 10k GPIO13-GND; 680 uF junto a los pixels.",
    ], size=8.4)
    box(p, fitz.Rect(425, 72, 812, 275), "PIEZO PASIVO", [
        "GPIO14 → 1k → base Q1.", "10k base-emisor; emisor a GND.",
        "Colector a piezo (-); piezo (+) a +5V.", "Confirmar E/B/C del transistor comprado.",
    ], size=8.7)
    box(p, fitz.Rect(30, 310, 395, 510), "ENCODER", [
        "A → GPIO32; B → GPIO33; pulsador → GPIO16; común a GND.",
        "Cada señal con pull-up de 10k a 3,3V. A/B: 10 nF a GND; pulsador: 100 nF a GND.",
        "Conector polarizado de 5 vías: +3V3, GND, A, B, SW.",
    ], size=8.7)
    box(p, fitz.Rect(425, 310, 812, 510), "PRUEBA", [
        "Comprobar 5 V en pin 20 y GND en pin 10. Probar un solo pixel con brillo limitado. Probar encoder y piezo antes de acercar T5 a T2/T3.",
        "El 74HCT245 acepta el nivel alto de 3,3 V; no usar 74HC245 ni módulo I2C BSS138.",
    ], size=8.7)

    p = page(doc, "Arneses y orden de integración", "Cablear por nombre de señal y pin; no por posición visual")
    box(p, fitz.Rect(30, 72, 400, 300), "ENTRE TARJETAS", [
        "C_PWR4  +5V / GND     T1 ↔ T4", "C_PWR3  +5V / GND     T1 ↔ T3", "C_PWR5  +5V / GND     T1 ↔ T5",
        "C_ADC_I  +3V3 / GND / CH1 / CH2     T4 ↔ T2",
        "C_ADC_V  +3V3 / GND / V_ADC     T4 ↔ T3",
        "C_UI_D  GND / LED_DATA / BUZZ     T4 ↔ T5",
        "C_UI_E  +3V3 / GND / ENC_A / ENC_B / ENC_SW     T4 ↔ T5",
    ], size=8.5)
    box(p, fitz.Rect(430, 72, 812, 300), "SECUENCIA", [
        "1. T1 sola", "2. T2 y VBIAS", "3. T3 sin red", "4. T4 sin ADC externos", "5. T5 con un pixel",
        "6. Integrar un arnés por vez", "7. Calibrar con carga patrón", "8. Probar 120 V con Z1 cerrada",
    ], size=8.5)
    box(p, fitz.Rect(30, 340, 812, 520), "DOCUMENTOS DE MONTAJE", [
        "Pinout completo: conexiones-entre-tarjetas.csv", "Compra: BOM-precision.csv", "Ubicación: lista-por-tarjeta.csv",
        "Seguridad y aceptación: SEGURIDAD-Y-PRUEBAS.md", "Este PDF define la partición eléctrica; no es una plantilla 1:1 de perforaciones.",
    ], size=9)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata({
        "title": "Medidor E.5 · esquema modular para tarjetas perforadas",
        "author": "Sistemas Embebidos 1 · Universidad de la Costa",
        "subject": "Partición comprobable del medidor ESP32",
    })
    doc.save(OUT, garbage=4, deflate=True)
    print(OUT)


if __name__ == "__main__":
    main()
