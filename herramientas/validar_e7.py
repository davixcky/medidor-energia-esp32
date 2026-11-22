#!/usr/bin/env python3
"""Validación cruzada de la entrega vigente E.9.

El nombre del archivo se conserva por compatibilidad con los comandos y enlaces
históricos de la revisión E.7. Esta validación no sustituye pruebas físicas.
"""
from pathlib import Path
import json
import re
import subprocess
import sys

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
    assert contracts["revision"] == "E.9-TOUCH-12V-LM2596"
    assert contracts["pinouts"]["C_BUCK_IN"] == ["+12V_PROT", "GND"]
    assert contracts["pinouts"]["C_BUCK_OUT"] == ["+5V_PROT", "GND"]
    assert contracts["pinouts"]["C_PWR5"] == ["+5V_PROT", "+12V_PROT", "GND"]
    assert contracts["pinouts"]["C_PIX"] == ["+12V_PROT", "DIN_5V", "GND"]
    checks["contratos"] = {"ok": True, "revision": contracts["revision"]}

    topology = subprocess.run(
        [sys.executable, str(ROOT / "herramientas/validar_esquematicos_e9.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    checks["schematic_topology"] = {
        "ok": topology.returncode == 0,
        "result": topology.stdout.strip(),
        "error": topology.stderr.strip(),
    }

    cad = json.loads((CAD / "validacion-3d.json").read_text())
    checks["cad"] = {"ok": cad["valid"], "issues": cad["issues"],
                     "enclosure_mm": cad["enclosure_mm"]}

    # La tira se alimenta directamente desde +12V_PROT; no hay elevador MT3608.
    p_out = float(strip["max_power_w"])
    i_out = p_out / float(strip["voltage_v"])
    checks["fcob_power_budget"] = {
        "ok": i_out < 0.25,
        "max_output_w": p_out,
        "max_output_a_at_12v": round(i_out, 4),
        "required_12v_branch": ">=0.25 A continuos medidos",
        "note": "La FCOB usa +12V_PROT directo; el LM2596 genera solo +5V_PROT."
    }

    ok = (all(v["ok"] for v in erc.values())
          and checks["schematic_topology"]["ok"]
          and checks["cad"]["ok"]
          and checks["fcob_power_budget"]["ok"])
    result = {"revision": contracts["revision"], "valid": ok, "checks": checks,
              "limits": "No valida soldadura manual, aislamiento de red, LM2596 real ni tolerancias de impresión."}
    (HW / "validacion-e7.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
