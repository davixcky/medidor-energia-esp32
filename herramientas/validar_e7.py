#!/usr/bin/env python3
"""Validación cruzada de la revisión E.7 (sin sustituir pruebas físicas)."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware/perforadas-modulares"
KICAD = HW / "kicad"
CAD = ROOT / "freecad/revision-e7"


def main():
    checks = {}
    erc = {}
    for n in range(1, 6):
        report = (KICAD / f"medidor-t{n}-erc.rpt").read_text(encoding="utf-8")
        match = re.search(r"ERC messages:\s*(\d+)\s+Errors\s+(\d+)\s+Warnings\s+(\d+)", report)
        ok = bool(match) and all(int(v) == 0 for v in match.groups())
        erc[f"T{n}"] = {"ok": ok, "report": f"kicad/medidor-t{n}-erc.rpt"}
    checks["kicad_erc"] = erc

    contracts = json.loads((KICAD / "contratos.json").read_text())
    strip = contracts["strip"]
    assert strip["voltage_v"] == 12 and strip["used_length_mm"] == 200
    assert contracts["pinouts"]["C_PWR5"] == ["+5V", "+12V_LED", "GND"]
    assert contracts["pinouts"]["C_PIX"] == ["+12V_LED", "DIN_5V", "GND"]
    checks["contratos"] = {"ok": True, "revision": contracts["revision"]}

    cad = json.loads((CAD / "validacion-3d.json").read_text())
    checks["cad"] = {"ok": cad["valid"], "issues": cad["issues"],
                     "enclosure_mm": cad["enclosure_mm"]}

    # Peor caso publicado: 10 W/m, tramo de 0,2 m.
    p_out = 10.0 * 0.2
    i_out = p_out / 12.0
    efficiency_floor = 0.80
    i_in_5v = p_out / (5.0 * efficiency_floor)
    checks["fcob_power_budget"] = {
        "ok": i_out < 0.25 and i_in_5v < 0.60,
        "max_output_w": p_out,
        "max_output_a_at_12v": round(i_out, 4),
        "estimated_input_a_at_5v_80pct": round(i_in_5v, 4),
        "required_boost": "12.0 V regulados, >=0.25 A continuos medidos",
        "note": "Cálculo conservador; validar temperatura y tensión del MT3608 real."
    }

    ok = all(v["ok"] for v in erc.values()) and checks["cad"]["ok"] and checks["fcob_power_budget"]["ok"]
    result = {"revision": "E.7", "valid": ok, "checks": checks,
              "limits": "No valida soldadura manual, aislamiento de red ni módulo MT3608 real."}
    (HW / "validacion-e7.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
