"""Datos y modelo del pronóstico horario de consumo (LSTM pequeño del informe, sección 9).

Entrada: ventana de 24 h × 4 variables (consumo kWh, hora del día, día de la semana, temperatura °C).
Red: LSTM 32 → Dropout 0,2 → Densa 16 (ReLU) → Densa 1 = 5.281 parámetros.
"""
import json
import os

import numpy as np
import pandas as pd
import torch
from torch import nn

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "datos")
UCI = os.path.join(DATOS, "uci", "household_power_consumption.txt")
CLIMA = os.path.join(DATOS, "clima", "sceaux.json")
VENTANA = 24

# Partición cronológica: entrenamiento, validación y prueba nunca se mezclan en el tiempo.
FIN_ENTRENA = "2009-06-30 23:00"
FIN_VALIDA = "2009-12-31 23:00"


def cargar_serie():
    """Serie horaria con columnas kwh, temp, valida (hora con al menos 30 min medidos)."""
    df = pd.read_csv(UCI, sep=";", usecols=["Date", "Time", "Global_active_power"], na_values="?",
                     dtype={"Global_active_power": "float64"}, low_memory=False)
    t = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S")
    p = pd.Series(df["Global_active_power"].values, index=t)  # kW, promedio de cada minuto
    g = p.resample("1h")
    horas = pd.DataFrame({"kwh": g.mean(), "n": g.count()})  # kW medio × 1 h = kWh
    horas["valida"] = horas["n"] >= 30
    horas.loc[~horas["valida"], "kwh"] = np.nan
    # Huecos: se interpolan solo para dar continuidad; las ventanas que los tocan no se usan.
    horas["kwh"] = horas["kwh"].interpolate(limit_direction="both")

    c = json.load(open(CLIMA, encoding="utf-8"))["hourly"]
    temp = pd.Series(c["temperature_2m"], index=pd.to_datetime(c["time"]), dtype="float64")
    temp = temp[~temp.index.duplicated()]
    horas["temp"] = temp.reindex(horas.index).interpolate(limit_direction="both")
    return horas[["kwh", "temp", "valida"]]


class Normalizador:
    def __init__(self, serie=None, d=None):
        if d is None:
            ent = serie.loc[:FIN_ENTRENA]  # solo con datos de entrenamiento
            d = {"kwh_m": float(ent["kwh"].mean()), "kwh_s": float(ent["kwh"].std()),
                 "temp_m": float(ent["temp"].mean()), "temp_s": float(ent["temp"].std())}
        self.d = d

    def variables(self, serie):
        """Matriz (T, 4): kWh y temperatura estandarizados, hora y día en [0, 1]."""
        d = self.d
        return np.stack([(serie["kwh"].values - d["kwh_m"]) / d["kwh_s"],
                         serie.index.hour.values / 23.0,
                         serie.index.dayofweek.values / 6.0,
                         (serie["temp"].values - d["temp_m"]) / d["temp_s"]], axis=1).astype("float32")

    def a_kwh(self, z):
        return z * self.d["kwh_s"] + self.d["kwh_m"]


def ventanas(X, valida, desde, hasta):
    """Ejemplos (24 h de entrada → hora siguiente) con objetivo en [desde, hasta)."""
    idx = [t for t in range(max(desde, VENTANA), hasta) if valida[t - VENTANA:t + 1].all()]
    idx = np.array(idx)
    xs = np.stack([X[t - VENTANA:t] for t in idx])
    ys = X[idx, 0:1]
    return torch.from_numpy(xs), torch.from_numpy(ys), idx


class LSTMUnaCompuerta(nn.Module):
    """LSTM con un solo vector de sesgo por compuerta, como en las ecuaciones del informe:
    4 × ((4 + 32) × 32 + 32) = 4.736 parámetros (nn.LSTM de PyTorch usa dos sesgos)."""

    def __init__(self, entradas, unidades):
        super().__init__()
        self.u = unidades
        self.lin = nn.Linear(entradas + unidades, 4 * unidades)

    def forward(self, x):
        b, T, _ = x.shape
        h = x.new_zeros(b, self.u)
        c = x.new_zeros(b, self.u)
        for t in range(T):
            f, i, g, o = self.lin(torch.cat([h, x[:, t]], 1)).chunk(4, 1)
            c = torch.sigmoid(f) * c + torch.sigmoid(i) * torch.tanh(g)
            h = torch.sigmoid(o) * torch.tanh(c)
        return h


class Pronosticador(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = LSTMUnaCompuerta(4, 32)
        self.red = nn.Sequential(nn.Dropout(0.2), nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1))

    def forward(self, x):
        return self.red(self.lstm(x))


@torch.no_grad()
def recursivo(modelo, X, t0, H):
    """Pronostica t0 … t0+H−1 alimentando cada predicción como consumo de la hora siguiente.
    Hora, día y temperatura de las horas futuras se toman de los datos (temperatura observada)."""
    v = X[t0 - VENTANA:t0 + H].copy()
    salida = []
    for k in range(H):
        z = modelo(torch.from_numpy(v[k:k + VENTANA][None]))[0, 0].item()
        v[VENTANA + k, 0] = z
        salida.append(z)
    return np.array(salida)
