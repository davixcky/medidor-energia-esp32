#!/usr/bin/env python3
"""Pronostica las próximas 48 h con el LSTM entrenado.

    .venv/bin/python predict.py                       # demostración con datos de prueba UCI
    .venv/bin/python predict.py medidas.csv           # CSV con columnas tiempo,kwh,temp (≥ 24 filas horarias)

En el CSV propio, las horas futuras necesitan temperatura: se repite la del mismo horario del último día.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import torch

from modelo import AQUI, VENTANA, Normalizador, Pronosticador, cargar_serie, recursivo

H = 48


def main():
    modelo = Pronosticador()
    modelo.load_state_dict(torch.load(os.path.join(AQUI, "lstm.pt")))
    modelo.eval()
    norm = Normalizador(d=json.load(open(os.path.join(AQUI, "normalizacion.json"))))
    if len(sys.argv) > 1:
        m = pd.read_csv(sys.argv[1], parse_dates=["tiempo"]).set_index("tiempo").sort_index().iloc[-VENTANA:]
        futuro = pd.date_range(m.index[-1] + pd.Timedelta(hours=1), periods=H, freq="1h")
        temp = np.resize(m["temp"].values[-24:], H)
        serie = pd.concat([m[["kwh", "temp"]], pd.DataFrame({"kwh": 0.0, "temp": temp}, index=futuro)])
        t0 = VENTANA
    else:
        serie = cargar_serie()
        t0 = serie.index.get_loc(serie.loc["2010-03-10 00:00":].index[0])
    pred = norm.a_kwh(recursivo(modelo, norm.variables(serie), t0, H))
    for t, v in zip(serie.index[t0:t0 + H], pred):
        print(f"{t:%Y-%m-%d %H:%M}  {v:6.3f} kWh")
    print(f"Total pronosticado en 48 h: {pred.sum():.2f} kWh")


if __name__ == "__main__":
    main()
