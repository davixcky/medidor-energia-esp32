# Pronóstico de consumo con LSTM

Modelo inicial del medidor de energía, entrenado con la serie pública *Individual Household Electric
Power Consumption* de la UCI y la temperatura horaria de Open-Meteo. La descripción, los resultados y
las limitaciones están en la sección 7.15 del [documento del avance](../README.md).

## Cómo regenerar

```bash
cd pronostico
python3 -m venv .venv
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install pandas matplotlib
mkdir -p datos/uci datos/clima
curl -L -o datos/uci/uci.zip "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
(cd datos/uci && unzip uci.zip)
curl -o datos/clima/sceaux.json "https://archive-api.open-meteo.com/v1/archive?latitude=48.78&longitude=2.29&start_date=2006-12-16&end_date=2010-11-26&hourly=temperature_2m&timezone=Europe%2FParis"
.venv/bin/python train.py      # entrena, evalúa y dibuja ../img/lstm-*.png
.venv/bin/python predict.py    # pronóstico de 48 h (demostración o CSV tiempo,kwh,temp)
.venv/bin/python figuras_lstm.py   # celda, ecuaciones, día real y error por horizonte en ../img/lstm-*.png
```

`datos/` y `.venv/` no se suben al repositorio (ver `.gitignore`).
