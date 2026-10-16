#!/usr/bin/env python3
"""Exporta los pesos del LSTM (../pronostico/lstm.pt) a JSON para la inferencia en TypeScript,
junto con un caso de prueba calculado con PyTorch (una ventana y un pronóstico recursivo de 48 h).

    ../pronostico/.venv/bin/python scripts/exportar_lstm.py
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PRON = os.path.join(AQUI, "..", "..", "pronostico")
sys.path.insert(0, PRON)

import numpy as np  # noqa: E402
import torch  # noqa: E402

from modelo import Pronosticador  # noqa: E402

m = Pronosticador()
m.load_state_dict(torch.load(os.path.join(PRON, "lstm.pt")))
m.eval()
sd = {k: v.tolist() for k, v in m.state_dict().items()}
norm = json.load(open(os.path.join(PRON, "normalizacion.json")))
metr = json.load(open(os.path.join(PRON, "metricas.json")))
pesos = {"normalizacion": norm, "estado": sd, "metricas": metr}
salida = os.path.join(AQUI, "..", "src", "server", "lstm-pesos.json")
json.dump(pesos, open(salida, "w"))

# Caso de prueba: ventana determinista de 24 + 48 h (consumo, hora/23, día/6, temperatura).
rng = np.random.default_rng(7)
T = 72
horas = np.arange(T) % 24
v = np.stack([rng.normal(0, 1, T), horas / 23.0, ((np.arange(T) // 24) % 7) / 6.0,
              rng.normal(0, 1, T)], axis=1).astype("float32")
with torch.no_grad():
    uno = m(torch.from_numpy(v[:24][None]))[0, 0].item()
    w = v.copy()
    rec = []
    for k in range(48):
        z = m(torch.from_numpy(w[k:k + 24][None]))[0, 0].item()
        w[24 + k, 0] = z
        rec.append(z)
json.dump({"entrada": v.tolist(), "un_paso": uno, "recursivo": rec},
          open(os.path.join(AQUI, "..", "src", "server", "lstm-caso-prueba.json"), "w"))
print("pesos:", {k: list(np.array(x).shape) for k, x in sd.items()}, "un paso:", uno)
