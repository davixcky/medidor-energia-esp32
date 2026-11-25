"""Línea de tiempo del video E.7, derivada de tiempos.json (narración) y del firmware.

Estados (firmware/src/main.cpp):
  FCOB  pixels.fill(): verde (0,18,10) en línea, ámbar (24,9,0) sin envío reciente, rojo (32,0,0) en alerta.
  LED D8 (verde, un solo color): fijo en línea; (m/500)%2 sin conexión = 1 Hz; (m/100)%2 en alerta = 5 Hz.
"""
from pathlib import Path
import json

P = Path(__file__).resolve().parent
TIEMPOS = json.loads((P / 'tiempos.json').read_text(encoding='utf-8'))
FPS, DUR = TIEMPOS['fps'], TIEMPOS['duration']
FRAMES = FPS * DUR
S = [seg['start'] for seg in TIEMPOS['segments']]

T = {
    'panel': S[1], 'verde': S[2], 'ambar': S[3], 'rojo': S[4], 'normal': S[5],
    'abre': (S[5] + .35, S[5] + 2.35), 'interior': S[6], 'detalle': S[6] + 3.3, 'red': S[7],
    'cierra': (DUR - 3.5, DUR - 1.7),
}
COLORES_FW = {'verde': (0, 18, 10), 'ambar': (24, 9, 0), 'rojo': (32, 0, 0)}


def tiempo(frame):
    return (frame - 1) / FPS


def frame_de(t):
    return int(round(t * FPS)) + 1


def estado(t):
    return 'ambar' if T['ambar'] <= t < T['rojo'] else 'rojo' if T['rojo'] <= t < T['normal'] else 'verde'


def led_encendido(t):
    """Mismo cálculo que el firmware, con m en milisegundos desde que empezó el estado."""
    e = estado(t)
    if e == 'verde':
        return True
    m = int(round((t - T[e]) * 1000))
    return bool((m // (500 if e == 'ambar' else 100)) % 2)


def apertura(t, maximo):
    def suave(u):
        u = min(max(u, 0.0), 1.0)
        return u * u * u * (u * (6 * u - 15) + 10)
    a0, a1 = T['abre']
    c0, c1 = T['cierra']
    if t < a0 or t >= c1:
        return 0.0
    if t < a1:
        return maximo * suave((t - a0) / (a1 - a0))
    if t < c0:
        return maximo
    return maximo * (1 - suave((t - c0) / (c1 - c0)))
