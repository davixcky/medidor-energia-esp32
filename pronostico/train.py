#!/usr/bin/env python3
"""Entrena el LSTM, lo compara con las líneas base ingenuas y genera las gráficas.

    .venv/bin/python train.py
"""
import json
import os
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import torch

from modelo import AQUI, FIN_ENTRENA, FIN_VALIDA, VENTANA, Normalizador, Pronosticador, cargar_serie, recursivo, ventanas

IMG = os.path.join(AQUI, "..", "img")
torch.manual_seed(0)
np.random.seed(0)


def metricas(real, pred):
    e = pred - real
    return {"MAE": float(np.mean(np.abs(e))), "RMSE": float(np.sqrt(np.mean(e ** 2))),
            "MAPE": float(100 * np.mean(np.abs(e) / real))}


def main():
    serie = cargar_serie()
    norm = Normalizador(serie)
    X = norm.variables(serie)
    valida = serie["valida"].values
    kwh = serie["kwh"].values
    i_ent = serie.index.get_loc(serie.loc[:FIN_ENTRENA].index[-1]) + 1
    i_val = serie.index.get_loc(serie.loc[:FIN_VALIDA].index[-1]) + 1
    n = len(serie)
    xe, ye, _ = ventanas(X, valida, 0, i_ent)
    xv, yv, _ = ventanas(X, valida, i_ent, i_val)
    xp, yp, ip = ventanas(X, valida, i_val, n)
    print(f"horas: {n}  ejemplos entrenamiento/validación/prueba: {len(xe)}/{len(xv)}/{len(xp)}")

    modelo = Pronosticador()
    n_par = sum(p.numel() for p in modelo.parameters())
    print("parámetros:", n_par)
    opt = torch.optim.Adam(modelo.parameters(), lr=2e-3)
    perdida = torch.nn.MSELoss()
    hist = {"entrenamiento": [], "validacion": []}
    mejor, paciencia, estado = 1e9, 0, None
    t0 = time.time()
    for ep in range(60):
        modelo.train()
        orden = torch.randperm(len(xe))  # se barajan ventanas ya cortadas, nunca el eje del tiempo
        acum = 0.0
        for k in range(0, len(xe), 256):
            b = orden[k:k + 256]
            opt.zero_grad()
            l = perdida(modelo(xe[b]), ye[b])
            l.backward()
            opt.step()
            acum += l.item() * len(b)
        modelo.eval()
        with torch.no_grad():
            lv = perdida(modelo(xv), yv).item()
        hist["entrenamiento"].append(acum / len(xe))
        hist["validacion"].append(lv)
        print(f"época {ep + 1:2d}  MSE entrenamiento {acum / len(xe):.4f}  validación {lv:.4f}")
        if lv < mejor - 1e-4:
            mejor, paciencia = lv, 0
            estado = {k: v.clone() for k, v in modelo.state_dict().items()}
        else:
            paciencia += 1
            if paciencia >= 6:
                break
    modelo.load_state_dict(estado)
    modelo.eval()
    print(f"entrenamiento: {time.time() - t0:.0f} s")
    torch.save(estado, os.path.join(AQUI, "lstm.pt"))
    json.dump(norm.d, open(os.path.join(AQUI, "normalizacion.json"), "w"), indent=2)

    # ---------------- prueba a 1 h
    with torch.no_grad():
        pred1 = norm.a_kwh(modelo(xp).numpy()[:, 0])
    real1 = kwh[ip]
    res = {"1 h": {"LSTM": metricas(real1, pred1),
                   "Persistencia": metricas(real1, kwh[ip - 1]),
                   "Ingenuo 24 h": metricas(real1, kwh[ip - 24]),
                   "Ingenuo 168 h": metricas(real1, kwh[ip - 168])}}

    # ---------------- prueba recursiva desde cada medianoche del periodo de prueba
    for H in (24, 48):
        R, L, N24, N168, P = [], [], [], [], []
        for t in range(i_val, n - H):
            if serie.index[t].hour != 0 or not valida[t - 168:t + H].all():
                continue
            R.append(kwh[t:t + H])
            L.append(norm.a_kwh(recursivo(modelo, X, t, H)))
            h = np.arange(H)
            N24.append(kwh[t - 24 + (h % 24)])        # repite el último día medido
            N168.append(kwh[t - 168 + h])             # misma hora de la semana anterior
            P.append(np.full(H, kwh[t - 1]))          # última hora medida
        R, L, N24, N168, P = map(np.concatenate, (R, L, N24, N168, P))
        res[f"{H} h recursivo"] = {"LSTM": metricas(R, L), "Persistencia": metricas(R, P),
                                   "Ingenuo 24 h": metricas(R, N24),
                                   "Ingenuo 168 h": metricas(R, N168), "origenes": len(R) // H}
    json.dump({"parametros": n_par, "epocas": len(hist["validacion"]), "ejemplos":
               {"entrenamiento": len(xe), "validacion": len(xv), "prueba": len(xp)}, "resultados": res},
              open(os.path.join(AQUI, "metricas.json"), "w"), indent=2, ensure_ascii=False)
    for h, r in res.items():
        print(h)
        for m, v in r.items():
            if isinstance(v, dict):
                print(f"   {m:14s} MAE {v['MAE']:.3f}  RMSE {v['RMSE']:.3f}  MAPE {v['MAPE']:.1f} %")

    # ---------------- gráficas
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(range(1, len(hist["entrenamiento"]) + 1), hist["entrenamiento"], "o-", label="Entrenamiento")
    ax.plot(range(1, len(hist["validacion"]) + 1), hist["validacion"], "s-", label="Validación")
    ax.set_xlabel("Época")
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.set_ylabel("Error cuadrático medio (datos estandarizados)")
    ax.set_title("Curvas de aprendizaje del LSTM (5.281 parámetros)", weight="bold")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "lstm-entrenamiento.png"), dpi=150)
    plt.close(fig)

    t = serie.index.get_loc(serie.loc["2010-03-10 00:00":].index[0])  # miércoles de la prueba
    H = 48
    lstm = norm.a_kwh(recursivo(modelo, X, t, H))
    eje = serie.index[t - 72:t + H]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(eje, kwh[t - 72:t + H], color="black", lw=1.4, label="Consumo real")
    ax.plot(serie.index[t:t + H], lstm, color="#1565c0", lw=2, label="LSTM (recursivo, 48 h)")
    ax.plot(serie.index[t:t + H], kwh[t - 168:t - 168 + H], color="#ef6c00", lw=1.4, ls="--",
            label="Ingenuo: semana anterior")
    ax.axvline(serie.index[t], color="gray", ls=":")
    ax.text(serie.index[t], ax.get_ylim()[1] * 0.95, "  inicio del pronóstico", fontsize=8, va="top")
    ax.set_ylabel("Consumo (kWh por hora)")
    ax.set_title("72 h medidas y 48 h pronosticadas — conjunto de prueba (10 al 12 de marzo de 2010)",
                 weight="bold")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "lstm-pronostico.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
