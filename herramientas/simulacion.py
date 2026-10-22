#!/usr/bin/env python3
"""Simulación SPICE (ngspice) de las entradas analógicas y de la alimentación del medidor.

Cada caso escribe una netlist, la ejecuta con `ngspice -b`, lee los datos con `wrdata` y
compara el resultado con el límite de diseño. Las netlists quedan en ../simulacion/ para
poder abrirlas y repetirlas a mano. El resumen se imprime como tabla en Markdown y las
gráficas se escriben en ../img/sim-*.png.

Supuestos del modelo (los mismos del documento, sección 7.4):
- La pinza SCT-013-000 es una fuente de corriente ideal de relación 2000:1. No modela la
  saturación del núcleo ni el error de fase propio del transformador.
- El módulo ZMPT101B se modela por su salida: 2,5 V de reposo más una senoide cuya
  amplitud fija el potenciómetro del módulo.
- BAT85 y 1N5819 usan parámetros ajustados a los puntos de la hoja de datos (abajo).
- La entrada del ADC del ESP32 se modela como 10 MΩ; su capacitor de muestreo no se modela.
"""
import math
import os
import re
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(AQUI, "..", "simulacion")
IMG = os.path.join(AQUI, "..", "img")

# BAT85 (hoja de datos: VF ≤ 240 mV a 0,1 mA, 320 mV a 1 mA, 400 mV a 10 mA, 800 mV a 100 mA)
# 1N5819 (hoja de datos: VF típica ≈ 0,45 V a 1 A)
MODELOS = """
.model BAT85 D(IS=1.3e-8 N=1.1 RS=2 CJO=10p BV=30 IBV=2u)
.model D1N5819 D(IS=31.7u N=1.373 RS=0.051 CJO=110p M=0.35 EG=0.69 XTI=2 BV=40 IBV=1m)
"""

LIN_MIN, LIN_MAX = 0.15, 2.45      # zona lineal del ADC con atenuación de 11 dB
ABS_MAX = 3.3 + 0.3                # máximo absoluto de un pin del ESP32 (VDD + 0,3 V)


def correr(nombre, cuerpo, columnas):
    """Escribe la netlist, la corre y devuelve un arreglo con las columnas pedidas."""
    os.makedirs(SIM, exist_ok=True)
    datos = os.path.join(SIM, f"{nombre}.dat")
    ruta = os.path.join(SIM, f"{nombre}.cir")
    with open(ruta, "w") as f:
        f.write(f"* {nombre}\n{cuerpo}\n{MODELOS}\n.control\nset wr_singlescale\nset wr_vecnames\n"
                f"run\nwrdata {datos} {' '.join(columnas)}\n.endc\n.end\n")
    r = subprocess.run(["ngspice", "-b", ruta], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(datos):
        raise SystemExit(f"ngspice falló en {nombre}:\n{r.stdout}\n{r.stderr}")
    return np.loadtxt(datos, skiprows=1)


# ---------------------------------------------------------------- canales de corriente
def canal_corriente(nombre, rb, i_rms, armonico3=0.0):
    """Transitorio de un canal: pinza → burden → RC 3,3 kΩ / 47 nF (a VBIAS) → BAT85 → ADC."""
    ipk = i_rms * math.sqrt(2) / 2000
    fuente = f"SIN(0 {ipk} 60)"
    extra = f"Ih3 vb t SIN(0 {ipk * armonico3} 180)\n" if armonico3 else ""
    cuerpo = f"""
V33 v33 0 3.3
R3 v33 vb 15k
R4 vb 0 10k
C7 vb 0 10u
C8 vb 0 100n
Ict vb t {fuente}
{extra}Rb t vb {rb}
R5 t a 3.3k
C5 a vb 47n
Dsup a v33 BAT85
Dinf 0 a BAT85
Radc a 0 10Meg
.ic v(vb)=1.32 v(a)=1.32 v(t)=1.32
.tran 5u 120m 70m uic
"""
    d = correr(nombre, cuerpo, ["v(a)", "v(vb)", "i(V33)"])
    return d[:, 0], d[:, 1], d[:, 2]


def ac_corriente(nombre, rb):
    cuerpo = f"""
Vb vb 0 1.32
Ict vb t AC 1
Rb t vb {rb}
R5 t a 3.3k
C5 a vb 47n
.ac dec 200 10 20k
"""
    d = correr(nombre, cuerpo, ["vm(a)", "vp(a)"])
    return d[:, 0], d[:, 1], d[:, 2]


# ---------------------------------------------------------------- canal de tensión
def canal_tension(nombre, amp):
    cuerpo = f"""
V33 v33 0 3.3
Vz z 0 SIN(2.5 {amp} 60)
R7 z v 11k
R8 v 0 13k
C9 v 0 27n
Dsup v v33 BAT85
Dinf 0 v BAT85
Radc v 0 10Meg
.tran 5u 60m 20m
"""
    d = correr(nombre, cuerpo, ["v(v)"])
    return d[:, 0], d[:, 1]


def ac_tension(nombre):
    cuerpo = """
Vz z 0 AC 1
R7 z v 11k
R8 v 0 13k
C9 v 0 27n
.ac dec 200 10 20k
"""
    d = correr(nombre, cuerpo, ["vm(v)", "vp(v)"])
    return d[:, 0], d[:, 1], d[:, 2]


# ---------------------------------------------------------------- alimentación
def alimentacion(nombre, v_adaptador):
    """Barrido de la corriente de carga: adaptador → PTC (0,15 Ω) → 1N5819 → entrada del LDO."""
    cuerpo = f"""
Vad in 0 {v_adaptador}
Rptc in p 0.15
D1 p v5 D1N5819
C1 v5 0 470u
Iload v5 0 0
.dc Iload 0 0.8 0.01
"""
    d = correr(nombre, cuerpo, ["v(v5)"])
    return d[:, 0], d[:, 1]


def interp(f, y, f0):
    return float(np.interp(f0, f, y))


def main():
    os.makedirs(IMG, exist_ok=True)
    filas = []

    def fila(caso, resultado, criterio, ok):
        filas.append((caso, resultado, criterio, ok if isinstance(ok, str) else ("Cumple" if ok else "**No cumple**")))

    # 1. Excursión de los canales de corriente en su corriente nominal y en el límite lineal
    trans = {}
    for canal, rb, nominal, limite in (("CH1", 22, 60, 72.6), ("CH2", 47, 30, 34.0)):
        for etiqueta, i in (("nominal", nominal), ("límite", limite)):
            t, va, vb = canal_corriente(f"{canal.lower()}_{int(i)}A", rb, i)
            lo, hi = va.min(), va.max()
            trans[(canal, etiqueta)] = (t, va)
            fila(f"{canal}, {i:g} A eficaces ({etiqueta})", f"{lo:.3f} V a {hi:.3f} V",
                 f"dentro de {LIN_MIN}–{LIN_MAX} V" if etiqueta == "nominal" else f"máximo ≤ {LIN_MAX} V + 0,01",
                 LIN_MIN <= lo and hi <= (LIN_MAX if etiqueta == "nominal" else LIN_MAX + 0.01))
    # 2. Sobrecorriente: los BAT85 deben mantener el pin bajo el máximo absoluto
    for canal, rb, i in (("CH1", 22, 150), ("CH1", 22, 200), ("CH2", 47, 80), ("CH2", 47, 100)):
        t, va, _ = canal_corriente(f"{canal.lower()}_sobre_{i}A", rb, i)
        if i in (150, 80):
            trans[(canal, "sobrecorriente")] = (t, va)
        fila(f"{canal}, sobrecorriente de {i} A", f"{va.min():.3f} V a {va.max():.3f} V",
             f"entre −0,3 V y {ABS_MAX:.1f} V (máximo absoluto)", va.min() >= -0.3 and va.max() <= ABS_MAX)
    # 3. Carga no lineal: tercer armónico del 60 % (fuente conmutada) en CH2 a 20 A
    t, va, _ = canal_corriente("ch2_armonico", 47, 20, armonico3=0.6)
    fila("CH2, 20 A con 60 % de tercer armónico", f"{va.min():.3f} V a {va.max():.3f} V",
         f"dentro de {LIN_MIN}–{LIN_MAX} V", LIN_MIN <= va.min() and va.max() <= LIN_MAX)
    # 4. Polarización: valor en reposo
    _, _, vb = canal_corriente("ch1_reposo", 22, 0.0001)
    fila("VBIAS en reposo", f"{vb.mean():.4f} V", "1,32 V ± 1 %", abs(vb.mean() - 1.32) < 0.0132)

    # 5. Respuesta en frecuencia y desfase entre canales
    f1, m1, p1 = ac_corriente("ac_ch1", 22)
    f2, m2, p2 = ac_corriente("ac_ch2", 47)
    fv, mv, pv = ac_tension("ac_v")
    g1_60, g1_3k = interp(f1, m1, 60), interp(f1, m1, 3000)
    fila("CH1, ganancia a 60 Hz", f"{g1_60:.3f} V/A en el secundario ({g1_60 / 2000 * 1000:.2f} mV por A de primario)",
         "22 Ω (sin pérdida en el filtro)", abs(g1_60 - 22) < 0.1)
    fila("CH1, atenuación en el armónico 50 (3 kHz)", f"{20 * math.log10(g1_3k / g1_60):.2f} dB",
         "atenuación conocida: el *firmware* la compensa", "Informativo")
    g1_4k = interp(f1, m1, 4000)
    fila("CH1, atenuación en la frecuencia de Nyquist (4 kHz)", f"{20 * math.log10(g1_4k / g1_60):.2f} dB",
         "filtro de primer orden: lo que pase de 4 kHz se pliega atenuado", "Informativo")
    fc1 = float(f1[np.argmin(abs(m1 - m1[0] / math.sqrt(2)))])
    fcv = float(fv[np.argmin(abs(mv - mv[0] / math.sqrt(2)))])
    fila("Frecuencia de corte, CH1 y tensión", f"{fc1:.0f} Hz y {fcv:.0f} Hz", "≈ 1 kHz (τ ≈ 156–161 µs)",
         900 < fc1 < 1100 and 900 < fcv < 1100)
    fase = lambda f, p: math.degrees(interp(f, p, 60))
    d1, d2, dv = fase(f1, p1), fase(f2, p2), fase(fv, pv)
    peor = max(abs(d1 - dv), abs(d2 - dv))
    fila("Desfase a 60 Hz entre corriente y tensión",
         f"CH1 {d1:.2f}°, CH2 {d2:.2f}°, V {dv:.2f}° → diferencia máx. {peor:.2f}°",
         "≤ 0,2° (error en P ≤ 0,3 % con FP = 0,5)", peor <= 0.2)

    # 6. Canal de tensión
    for amp in (1.0, 1.4):
        t, vv = canal_tension(f"v_{amp}".replace(".", "_"), amp)
        trans[("V", amp)] = (t, vv)
        fila(f"Tensión, salida del módulo 2,5 V ± {amp:g} V", f"{vv.min():.3f} V a {vv.max():.3f} V",
             f"dentro de {LIN_MIN}–{LIN_MAX} V", LIN_MIN <= vv.min() and vv.max() <= LIN_MAX)

    # 7. Alimentación: tensión a la entrada del regulador AMS1117 del DevKitC
    alim = {}
    for vad in (4.75, 5.0, 5.25):
        i, v5 = alimentacion(f"alim_{vad}".replace(".", "_"), vad)
        alim[vad] = (i, v5)
        v_05 = interp(i, v5, 0.5)
        # AMS1117: caída típica 1,1 V a 0,8 A; el ESP32 funciona desde 3,0 V
        fila(f"Entrada del regulador con adaptador de {vad:g} V y 500 mA", f"{v_05:.3f} V",
             "≥ 4,4 V (3,3 V regulados) · ≥ 4,1 V (ESP32 aún funciona a 3,0 V)",
             v_05 >= 4.4)

    # ---------------- gráficas
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    for (canal, etq), (t, va) in trans.items():
        if canal in ("CH1", "CH2") and etq in ("nominal", "límite", "sobrecorriente"):
            a = ax[0, 0] if canal == "CH1" else ax[0, 1]
            a.plot((t - t[0]) * 1000, va, label=etq)
    for a, canal in ((ax[0, 0], "CH1 (burden 22 Ω)"), (ax[0, 1], "CH2 (burden 47 Ω)")):
        a.axhspan(LIN_MIN, LIN_MAX, color="#c8e6c9", alpha=0.5, label="zona lineal del ADC")
        a.axhline(ABS_MAX, color="#c62828", ls="--", lw=1, label="máximo absoluto 3,6 V")
        a.set_title(f"Tensión en el pin del ADC — {canal}")
        a.set_xlabel("tiempo (ms)")
        a.set_ylabel("V")
        a.set_xlim(0, 50)
        a.legend(fontsize=8, loc="lower right")
        a.grid(alpha=0.3)
    a = ax[1, 0]
    a.semilogx(f1, 20 * np.log10(m1 / m1[0]), label="CH1")
    a.semilogx(f2, 20 * np.log10(m2 / m2[0]), label="CH2")
    a.semilogx(fv, 20 * np.log10(mv / mv[0]), "--", label="tensión")
    for x, n in ((60, "60 Hz"), (3000, "h50"), (4000, "Nyquist")):
        a.axvline(x, color="gray", lw=0.8, ls=":")
        a.text(x, -17, n, rotation=90, fontsize=8, va="bottom")
    a.set_ylim(-20, 1)
    a.set_title("Respuesta en frecuencia de los filtros antialias")
    a.set_xlabel("frecuencia (Hz)")
    a.set_ylabel("dB")
    a.legend(fontsize=8)
    a.grid(alpha=0.3, which="both")
    a = ax[1, 1]
    for vad, (i, v5) in alim.items():
        a.plot(i * 1000, v5, label=f"adaptador {vad:g} V".replace(".", ","))
    a.axhline(4.4, color="#ef6c00", ls="--", lw=1, label="4,4 V: AMS1117 aún regula 3,3 V")
    a.axhline(4.1, color="#c62828", ls="--", lw=1, label="4,1 V: ESP32 a 3,0 V (mínimo)")
    a.axvspan(380, 520, color="#e3f2fd", label="picos de Wi-Fi")
    a.set_title("Tensión a la entrada del regulador del DevKitC")
    a.set_xlabel("corriente de carga (mA)")
    a.set_ylabel("V")
    a.set_ylim(3.9, 5.3)
    a.legend(fontsize=8, loc="lower left")
    a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "sim-resultados.png"), dpi=140)
    plt.close(fig)

    print("| # | Caso | Resultado de la simulación | Criterio | Estado |")
    print("|---:|---|---|---|---|")
    coma = lambda x: re.sub(r"(?<=\d)\.(?=\d)", ",", x)  # decimales con coma, como el documento
    for k, (c, r, cr, ok) in enumerate(filas, 1):
        print(coma(f"| {k} | {c} | {r} | {cr} | {ok} |"))


if __name__ == "__main__":
    main()
