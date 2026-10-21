#!/usr/bin/env python3
"""Figuras que explican el LSTM (para el documento y la presentación).

    .venv/bin/python figuras_lstm.py

Escribe en ../img:
- lstm-ventanas.png   de la serie horaria a ejemplos de 24 h → hora siguiente, y la partición
- lstm-celda.png      esquema de la celda LSTM
- lstm-ecuaciones.png ecuaciones de la celda tal como están en modelo.py
- lstm-dia-real.png   compuertas y estado de la red entrenada sobre un día real del conjunto de prueba
- lstm-horizonte.png  error medio por horizonte del pronóstico recursivo frente a las referencias
y en horizonte.json los valores de la última figura.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

from modelo import AQUI, FIN_ENTRENA, FIN_VALIDA, VENTANA, Normalizador, Pronosticador, cargar_serie, recursivo, ventanas

IMG = os.path.join(AQUI, "..", "img")
ROJO, GRIS, TINTA, AMBAR, AZUL = "#a3161a", "#6b5f61", "#1d1517", "#e8a33d", "#1565c0"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})


def guardar(fig, nombre):
    fig.savefig(os.path.join(IMG, nombre), dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("escrita", nombre)


# ------------------------------------------------------------------ datos y modelo
serie = cargar_serie()
norm = Normalizador(d=json.load(open(os.path.join(AQUI, "normalizacion.json"))))
X = norm.variables(serie)
kwh = serie["kwh"].values
valida = serie["valida"].values
i_ent = serie.index.get_loc(serie.loc[:FIN_ENTRENA].index[-1]) + 1
i_val = serie.index.get_loc(serie.loc[:FIN_VALIDA].index[-1]) + 1
n = len(serie)
modelo = Pronosticador()
modelo.load_state_dict(torch.load(os.path.join(AQUI, "lstm.pt")))
modelo.eval()
n_ej = [len(ventanas(X, valida, a, b)[2]) for a, b in ((0, i_ent), (i_ent, i_val), (i_val, n))]


# ------------------------------------------------------------------ 1. ventanas
def figura_ventanas():
    t0 = serie.index.get_loc(serie.loc["2008-01-14 00:00":].index[0])  # una semana de enero de 2008
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(11, 5.4), gridspec_kw={"height_ratios": [3, 1.1]})
    h = np.arange(7 * 24)
    sem = kwh[t0:t0 + 7 * 24]
    tope = sem.max()
    ax.plot(h, sem, color=TINTA, lw=1.2)
    for k, (ini, col, et) in enumerate(((50, ROJO, "ejemplo 1"), (51, AMBAR, "ejemplo 2"))):
        ax.axvspan(ini, ini + VENTANA, color=col, alpha=0.13 if k == 0 else 0.0, lw=0)
        y = tope * (1.1 + 0.12 * k)
        ax.plot([ini, ini + VENTANA], [y] * 2, color=col, lw=3, solid_capstyle="butt")
        ax.plot(ini + VENTANA, kwh[t0 + ini + VENTANA], "o", color=col, ms=8, zorder=5)
        ax.text(ini + VENTANA + 1.5, y, f"{et}: 24 h de entrada → hora siguiente", color=col, va="center", fontsize=9)
    ax.annotate("hora que se predice", xy=(74, kwh[t0 + 74]), xytext=(84, tope * 0.75), fontsize=9, color=ROJO,
                arrowprops=dict(arrowstyle="->", color=ROJO))
    ax.set_xlim(0, 7 * 24)
    ax.set_ylim(0, tope * 1.32)
    ax.set_xticks(np.arange(0, 7 * 24 + 1, 24))
    ax.set_xticklabels(["lun", "mar", "mié", "jue", "vie", "sáb", "dom", ""])
    ax.set_ylabel("kWh por hora")
    ax.set_title("Cada ventana de 24 horas es un ejemplo; la ventana avanza de a una hora", loc="left", weight="bold")
    # partición cronológica
    tramos = [(serie.index[0], serie.index[i_ent - 1], ROJO, f"Entrenamiento\n{n_ej[0]:,} ejemplos".replace(",", ".")),
              (serie.index[i_ent], serie.index[i_val - 1], AMBAR, f"Validación\n{n_ej[1]:,}".replace(",", ".")),
              (serie.index[i_val], serie.index[-1], GRIS, f"Prueba\n{n_ej[2]:,} ejemplos".replace(",", "."))]
    for a, b, col, et in tramos:
        bx.barh(0, (b - a).days, left=(a - serie.index[0]).days, color=col, height=0.6)
        bx.text((a - serie.index[0]).days + (b - a).days / 2, 0, et, ha="center", va="center", color="white",
                fontsize=9, weight="bold")
    total = (serie.index[-1] - serie.index[0]).days
    bx.set_xlim(0, total)
    bx.set_yticks([])
    marcas = ["2007-01-01", "2008-01-01", "2009-01-01", "2009-07-01", "2010-01-01", "2010-11-26"]
    bx.set_xticks([(np.datetime64(m) - np.datetime64(serie.index[0].date())).astype(int) for m in marcas])
    bx.set_xticklabels(["ene 2007", "ene 2008", "ene 2009", "jul 2009", "ene 2010", "nov 2010"], fontsize=9)
    bx.spines["left"].set_visible(False)
    bx.set_title("Partición en el tiempo: el modelo nunca ve datos posteriores a los que usa para aprender",
                 loc="left", fontsize=10)
    fig.tight_layout()
    guardar(fig, "lstm-ventanas.png")


# ------------------------------------------------------------------ 2. celda
def figura_celda():
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.9, 0.9), 8.0, 4.3, boxstyle="round,pad=0.05,rounding_size=0.3",
                                fc="#f6f1ee", ec=GRIS, lw=1.2))

    def flecha(a, b, col=TINTA, lw=1.6):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=col, lw=lw, shrinkA=0, shrinkB=0))

    def linea(pts, col=TINTA, lw=1.6):
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=col, lw=lw, solid_capstyle="round")

    def op(x, y, s):
        ax.add_patch(Circle((x, y), 0.25, fc="white", ec=TINTA, lw=1.4, zorder=4))
        ax.text(x, y, s, ha="center", va="center", fontsize=13, zorder=5)

    def caja(x, s, col):
        ax.add_patch(FancyBboxPatch((x - 0.38, 1.85), 0.76, 0.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                                    fc=col, ec="none", zorder=4))
        ax.text(x, 2.15, s, ha="center", va="center", color="white", fontsize=12, zorder=5)

    # estado de la celda (línea superior)
    linea([(0.2, 4.6), (2.75, 4.6)], ROJO, 2.4)
    op(3.0, 4.6, "×")
    linea([(3.25, 4.6), (5.05, 4.6)], ROJO, 2.4)
    op(5.3, 4.6, "+")
    flecha((5.55, 4.6), (9.8, 4.6), ROJO, 2.4)
    ax.text(0.2, 4.85, r"$c_{t-1}$", fontsize=13, color=ROJO)
    ax.text(9.35, 4.85, r"$c_t$", fontsize=13, color=ROJO)
    # entrada: [h_{t-1}, x_t]
    linea([(0.2, 1.3), (6.95, 1.3)])
    flecha((1.6, 0.2), (1.6, 1.3))
    ax.text(0.2, 1.45, r"$h_{t-1}$", fontsize=13)
    ax.text(1.75, 0.25, r"$x_t$  (4 variables de la hora)", fontsize=11)
    xs = {"f": 3.0, "i": 4.4, "g": 5.3, "o": 6.95}
    for k, x in xs.items():
        linea([(x, 1.3), (x, 1.85)])
    caja(xs["f"], r"$\sigma$", ROJO)
    caja(xs["i"], r"$\sigma$", ROJO)
    caja(xs["g"], "tanh", GRIS)
    caja(xs["o"], r"$\sigma$", ROJO)
    ax.text(xs["f"] - 0.75, 2.15, r"$f_t$", fontsize=13, ha="center")
    ax.text(xs["i"] - 0.7, 2.15, r"$i_t$", fontsize=13, ha="center")
    ax.text(xs["g"] + 0.55, 2.75, r"$\tilde c_t$", fontsize=13, ha="center")
    ax.text(xs["o"] - 0.7, 2.15, r"$o_t$", fontsize=13, ha="center")
    flecha((xs["f"], 2.45), (xs["f"], 4.35))
    op(4.85, 3.4, "×")
    linea([(xs["i"], 2.45), (xs["i"], 3.4), (4.6, 3.4)])
    linea([(xs["g"], 2.45), (xs["g"], 3.4), (5.1, 3.4)])
    flecha((4.85, 3.65), (5.12, 4.37))
    # salida
    ax.add_patch(FancyBboxPatch((7.55, 3.85), 0.8, 0.45, boxstyle="round,pad=0.02,rounding_size=0.1",
                                fc=GRIS, ec="none", zorder=4))
    ax.text(7.95, 4.07, "tanh", color="white", ha="center", va="center", fontsize=11, zorder=5)
    linea([(7.95, 4.6), (7.95, 4.3)], ROJO, 1.6)
    op(7.95, 3.2, "×")
    linea([(7.95, 3.85), (7.95, 3.45)])
    linea([(xs["o"], 2.45), (xs["o"], 3.2), (7.7, 3.2)])
    linea([(7.95, 2.95), (7.95, 1.3)])
    flecha((7.95, 1.3), (9.8, 1.3))
    flecha((8.6, 1.3), (8.6, 0.2))
    ax.text(9.35, 1.45, r"$h_t$", fontsize=13)
    ax.text(8.75, 0.25, "a la hora siguiente", fontsize=10, color=GRIS)
    # rótulos de las compuertas
    for x, s in ((3.0, "olvido"), (4.85, "entrada"), (6.95, "salida")):
        ax.text(x, 5.45, s, ha="center", fontsize=10, color=GRIS)
    guardar(fig, "lstm-celda.png")


# ------------------------------------------------------------------ 3. ecuaciones
def figura_ecuaciones():
    fig = plt.figure(figsize=(6.6, 4.6))
    lineas = [
        (r"$f_t = \sigma\left(W_f\,[h_{t-1},\,x_t] + b_f\right)$", "compuerta de olvido"),
        (r"$i_t = \sigma\left(W_i\,[h_{t-1},\,x_t] + b_i\right)$", "compuerta de entrada"),
        (r"$\tilde c_t = \tanh\left(W_c\,[h_{t-1},\,x_t] + b_c\right)$", "candidato a memoria"),
        (r"$o_t = \sigma\left(W_o\,[h_{t-1},\,x_t] + b_o\right)$", "compuerta de salida"),
        (r"$c_t = f_t \odot c_{t-1} + i_t \odot \tilde c_t$", "estado de la celda"),
        (r"$h_t = o_t \odot \tanh(c_t)$", "salida de la hora $t$"),
    ]
    for k, (eq, et) in enumerate(lineas):
        y = 0.92 - k * 0.15
        fig.text(0.02, y, eq, fontsize=19, color=TINTA if k < 4 else ROJO, va="center")
        fig.text(0.69, y, et, fontsize=14, color=GRIS, va="center")
    fig.text(0.02, 0.0, r"$\sigma(z) = 1/(1+e^{-z})\in(0,1)$;  $\odot$: producto elemento a elemento;  "
             r"$h, c \in \mathbb{R}^{32}$,  $x_t \in \mathbb{R}^{4}$", fontsize=13, color=GRIS)
    guardar(fig, "lstm-ecuaciones.png")


# ------------------------------------------------------------------ 4. día real
@torch.no_grad()
def compuertas(ventana):
    """Ejecuta la celda paso a paso y devuelve f, i, o, c, h de cada hora (24 × 32)."""
    lin = modelo.lstm.lin
    h = torch.zeros(1, 32)
    c = torch.zeros(1, 32)
    reg = {k: [] for k in "fioch"}
    for x in torch.from_numpy(ventana):
        f, i, g, o = lin(torch.cat([h, x[None]], 1)).chunk(4, 1)
        f, i, o = torch.sigmoid(f), torch.sigmoid(i), torch.sigmoid(o)
        c = f * c + i * torch.tanh(g)
        h = o * torch.tanh(c)
        for k, v in zip("fioch", (f, i, o, c, h)):
            reg[k].append(v[0].numpy())
    return {k: np.array(v) for k, v in reg.items()}


def dia_tipico():
    """Medianoche del conjunto de prueba cuyo error a 1 h es la mediana: un ejemplo representativo."""
    ts = [t for t in range(i_val + VENTANA, n) if serie.index[t].hour == 0 and valida[t - VENTANA:t + 1].all()]
    with torch.no_grad():
        z = modelo(torch.from_numpy(np.stack([X[t - VENTANA:t] for t in ts])))[:, 0].numpy()
    err = np.abs(norm.a_kwh(z) - kwh[ts])
    return ts[int(np.argsort(err)[len(err) // 2])], float(np.median(err))


def figura_dia_real():
    t, err_mediana = dia_tipico()
    ventana = X[t - VENTANA:t]
    g = compuertas(ventana)
    with torch.no_grad():
        pred = norm.a_kwh(modelo(torch.from_numpy(ventana[None]))[0, 0].item())
    horas = serie.index[t - VENTANA:t]
    et = [f"{x.hour:02d}" for x in horas]
    fig, axs = plt.subplots(3, 1, figsize=(10.5, 7.6), sharex=True, gridspec_kw={"height_ratios": [1.1, 1.1, 1.4]})
    a0, a1, a2 = axs
    a0.bar(range(VENTANA), kwh[t - VENTANA:t], color=TINTA, width=0.75)
    a0.bar(VENTANA, pred, color=ROJO, width=0.75, label=f"predicción: {pred:.2f} kWh")
    a0.bar(VENTANA, kwh[t], color="none", edgecolor=TINTA, ls="--", width=0.75, label=f"medido: {kwh[t]:.2f} kWh")
    a0.set_ylabel("kWh")
    a0.legend(loc="upper left", fontsize=9, frameon=False)
    a0.set_title(f"Entrada: consumo del {horas[0]:%d/%m/%Y} (conjunto de prueba, error típico) y hora que se predice",
                 loc="left", weight="bold", fontsize=11)
    corr = [float(np.corrcoef(g["c"][:, u], kwh[t - VENTANA:t])[0, 1]) for u in range(32)]
    u = int(np.argmax(np.abs(corr)))
    a1.plot(range(VENTANA), g["f"][:, u], "o-", color=ROJO, ms=3.5, lw=1.6, label="olvido $f_t$")
    a1.plot(range(VENTANA), g["i"][:, u], "o-", color=AMBAR, ms=3.5, lw=1.6, label="entrada $i_t$")
    a1.set_ylim(0, 1)
    a1.set_ylabel("compuerta")
    b1 = a1.twinx()
    b1.plot(range(VENTANA), g["c"][:, u], color=TINTA, lw=2.2, label=f"estado $c_t$")
    b1.set_ylabel(f"$c_t$ de la unidad {u + 1}")
    b1.spines["right"].set_visible(True)
    l1, n1 = a1.get_legend_handles_labels()
    l2, n2 = b1.get_legend_handles_labels()
    a1.legend(l1 + l2, n1 + n2, loc="upper left", fontsize=9, ncol=3, frameon=False)
    a1.set_title(f"Unidad {u + 1} de 32: su estado sigue el consumo (correlación {corr[u]:.2f})".replace(".", ","),
                 loc="left", fontsize=10)
    lim = np.abs(g["c"]).max()
    im = a2.imshow(g["c"].T, aspect="auto", cmap="RdBu_r", vmin=-lim, vmax=lim, extent=(-0.5, VENTANA - 0.5, 32.5, 0.5))
    a2.set_ylabel("unidad")
    a2.set_title("Estado $c_t$ de las 32 unidades (cada fila es una memoria)", loc="left", fontsize=10)
    fig.colorbar(im, cax=a2.inset_axes([1.01, 0, 0.012, 1]))
    a2.set_xticks(range(0, VENTANA + 1, 2))
    a2.set_xticklabels([et[k] if k < VENTANA else "00\n(pred.)" for k in range(0, VENTANA + 1, 2)])
    a2.set_xlim(-0.6, VENTANA + 0.6)
    a2.set_xlabel("hora del día")
    fig.tight_layout()
    guardar(fig, "lstm-dia-real.png")
    # números que se citan en la presentación
    return {"error_mediana_1h": err_mediana, "fecha": f"{horas[0]:%Y-%m-%d}", "pred": pred, "real": float(kwh[t]),
            "f_medio": float(g["f"].mean()), "i_medio": float(g["i"].mean()), "o_medio": float(g["o"].mean()),
            "unidad": u + 1, "correlacion": corr[u]}


# ------------------------------------------------------------------ 5. error por horizonte
def figura_horizonte():
    H = 48
    E = {k: [] for k in ("LSTM", "Persistencia", "Ingenuo 24 h", "Ingenuo 168 h")}
    for t in range(i_val, n - H):
        if serie.index[t].hour != 0 or not valida[t - 168:t + H].all():
            continue
        r = kwh[t:t + H]
        h = np.arange(H)
        E["LSTM"].append(np.abs(norm.a_kwh(recursivo(modelo, X, t, H)) - r))
        E["Persistencia"].append(np.abs(kwh[t - 1] - r))
        E["Ingenuo 24 h"].append(np.abs(kwh[t - 24 + (h % 24)] - r))
        E["Ingenuo 168 h"].append(np.abs(kwh[t - 168 + h] - r))
    mae = {k: np.mean(v, axis=0) for k, v in E.items()}
    fig, ax = plt.subplots(figsize=(9, 4.2))
    estilos = {"LSTM": (ROJO, "-", 2.4), "Persistencia": (GRIS, "--", 1.4), "Ingenuo 24 h": (AMBAR, "-", 1.4),
               "Ingenuo 168 h": (AZUL, ":", 1.6)}
    for k, v in mae.items():
        c, ls, lw = estilos[k]
        ax.plot(np.arange(1, H + 1), v, ls, color=c, lw=lw, label=k)
    ax.set_xlabel("horizonte (horas después del inicio, a medianoche)")
    ax.set_ylabel("error absoluto medio (kWh)")
    ax.set_xticks([1, 6, 12, 18, 24, 30, 36, 42, 48])
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, frameon=False, ncol=2)
    ax.set_title(f"Error por horizonte del pronóstico recursivo ({len(E['LSTM'])} inicios en el conjunto de prueba)",
                 loc="left", weight="bold", fontsize=11)
    fig.tight_layout()
    guardar(fig, "lstm-horizonte.png")
    return {"inicios": len(E["LSTM"]), "mae": {k: [round(float(x), 4) for x in v] for k, v in mae.items()}}


if __name__ == "__main__":
    figura_ventanas()
    figura_celda()
    figura_ecuaciones()
    dia = figura_dia_real()
    hz = figura_horizonte()
    json.dump({"ejemplos": n_ej, "dia_real": dia, "horizonte": hz}, open(os.path.join(AQUI, "horizonte.json"), "w"),
              indent=1, ensure_ascii=False)
    print(json.dumps(dia, indent=1))
