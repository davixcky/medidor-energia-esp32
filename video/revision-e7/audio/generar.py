"""Narración (Kokoro), cama tonal y pitidos del piezo.  Escribe mezcla.wav y ../tiempos.json.

    uv run --python 3.12 --with kokoro-onnx==0.6.1 --with soundfile python video/revision-e7/audio/generar.py
"""
from pathlib import Path
import json
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

DURACION, INICIO, COLA = 38, 0.8, 3.4   # la cola deja el cierre de tapa y el plano final sin voz
p = Path(__file__).resolve().parent
k = Kokoro(str(Path.home() / '.cache/hyperframes/tts/models/kokoro-v1.0.onnx'),
           str(Path.home() / '.cache/hyperframes/tts/voices/voices-v1.0.bin'))
lineas = [l.strip() for l in p.joinpath('narracion.txt').read_text(encoding='utf-8').splitlines() if l.strip()]
for old in p.glob('voz-*.wav'):
    old.unlink()
voces, sr = [], 24000
for i, linea in enumerate(lineas, 1):
    audio, sr = k.create(linea, voice='ef_dora', lang='es', speed=1.06)
    nz = np.flatnonzero(np.abs(audio) > 1e-3)          # sin silencios de cabecera ni de cola
    audio = audio[max(nz[0] - 480, 0):nz[-1] + 1200]
    sf.write(p / f'voz-{i}.wav', audio, sr)
    voces.append(audio)
habla = sum(len(a) for a in voces) / sr
pausa = (DURACION - INICIO - COLA - habla) / (len(voces) - 1)
assert pausa >= .30, f'La narración ({habla:.1f} s) no cabe en {DURACION} s'
segmentos, at = [], INICIO
mix = np.zeros((DURACION * sr, 2), dtype=np.float32)
for i, (linea, audio) in enumerate(zip(lineas, voces), 1):
    ini = round(at * sr)
    mix[ini:ini + len(audio)] += audio[:, None] * .80
    segmentos.append(dict(id=i, start=round(at, 3), end=round(at + len(audio) / sr, 3), text=linea))
    at += len(audio) / sr + pausa
# Cama tonal tenue.
t = np.arange(DURACION * sr) / sr
bed = np.zeros_like(t)
acordes = [(110, 146.83, 196), (98, 130.81, 174.61), (87.31, 130.81, 164.81), (98, 146.83, 196)]
for beat in np.arange(0, DURACION, 3.0):
    for f in acordes[int(beat // 6) % 4]:
        dt = t - beat
        env = np.where(dt >= 0, (1 - np.exp(-np.maximum(dt, 0) * 3)) * np.exp(-np.maximum(dt, 0) / 3.2), 0)
        bed += .007 * env * (np.sin(2 * np.pi * f * dt) + .16 * np.sin(2 * np.pi * 2 * f * dt))
bed *= np.minimum(t / 2, 1) * np.minimum((DURACION - t) / 2, 1)
mix += bed[:, None]
# Piezo: patrón de alerta del firmware (feedback::Sound): 80 ms sí, 80 ms no, 80 ms sí, a 2400 Hz.
alerta = segmentos[4]['start']
for offset in (0, .16):
    ini = round((alerta + offset) * sr)
    n = round(.08 * sr)
    bt = np.arange(n) / sr
    mix[ini:ini + n] += (.05 * np.sin(2 * np.pi * 2400 * bt) * np.minimum(bt / .004, 1) * np.minimum((.08 - bt) / .004, 1))[:, None]
sf.write(p / 'mezcla.wav', mix, sr)
(p.parent / 'tiempos.json').write_text(json.dumps(dict(duration=DURACION, fps=24, pausa=round(pausa, 3), segments=segmentos), ensure_ascii=False, indent=2), encoding='utf-8')
print(f'habla {habla:.2f} s, pausa {pausa:.2f} s')
for s_ in segmentos:
    print(s_)
