#!/usr/bin/env python3
"""Validate that the current E.9 still images exist, decode and are fresh."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageStat

HERE = Path(__file__).resolve().parent
EXPECTED = {
    "medidor-E7-cerrado.png": (2100, 1350),
    "medidor-E7-abierto.png": (2100, 1350),
    "medidor-E7-planta.png": (2100, 1350),
    "medidor-E7-trasera.png": (2100, 1350),
    "medidor-E7-tapa-interior.png": (2100, 1350),
    "medidor-E7-difusor.png": (2100, 1350),
    "medidor-E7-cierre-magnetico.png": (2100, 1350),
    "medidor-E9-entradas-SCT.png": (2100, 1350),
    "medidor-E9-alimentacion-12V.png": (2100, 1350),
    "medidor-E9-ruta-alimentacion-interior.png": (2100, 1350),
    "medidor-E8-pantalla-soporte-explotado.png": (1800, 1350),
}
SOURCES = [HERE / ".render/ensamble.json", HERE / "render_modelo.py", HERE / "escena_blender.py", HERE / "tft-render-horizontal.png"]
fresh_after = max(p.stat().st_mtime for p in SOURCES)
issues, files = [], []
for name, expected_size in EXPECTED.items():
    path = HERE / name
    row = {"file": name, "expected_pixels": list(expected_size)}
    if not path.exists():
        issues.append(f"falta {name}")
        files.append(row)
        continue
    try:
        with Image.open(path) as im:
            im.load()
            actual = im.size
            deviation = round(ImageStat.Stat(im.convert("L").resize((256, 256))).stddev[0], 2)
        row.update({"pixels": list(actual), "bytes": path.stat().st_size,
                    "grayscale_stddev": deviation,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "fresh": path.stat().st_mtime >= fresh_after})
        if actual != expected_size: issues.append(f"{name}: resolución {actual}, esperada {expected_size}")
        if path.stat().st_size < 50_000: issues.append(f"{name}: archivo demasiado pequeño")
        if deviation < 8: issues.append(f"{name}: imagen posiblemente vacía")
        if not row["fresh"]: issues.append(f"{name}: anterior a sus fuentes")
    except Exception as exc:
        issues.append(f"{name}: no decodifica: {exc}")
    files.append(row)

report = {
    "revision": "E.9", "valid": not issues, "issues": issues, "files": files,
    "scope": "Integridad, resolución, contenido no vacío y vigencia de renders fijos.",
    "does_not_prove": "Encaje físico, seguridad eléctrica, imprimibilidad ni fidelidad óptica.",
}
(HERE / "validacion-renders.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print("RENDERS_E9_OK" if not issues else "RENDERS_E9_ERROR")
for issue in issues: print("-", issue)
raise SystemExit(bool(issues))
