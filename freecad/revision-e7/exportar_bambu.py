#!/usr/bin/env python3
"""Generate named E.9 3MF projects from the current STL files.

Ejecutar después de ``regenerar.sh cad``. La cama predeterminada es 256 x 256 mm;
puede cambiarse con ``CAMA=350x320``. No lamina: conserva en Bambu Studio el perfil
de impresora, proceso y filamento que tenga abierto el usuario.
"""
from pathlib import Path
import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
STL, FIT, OUT = HERE / "stl", HERE / "pruebas-de-ajuste", HERE / "bambu"
BED = tuple(float(v) for v in os.environ.get("CAMA", "256x256").lower().split("x"))
MARGIN = 7.0


def read_stl(path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + 50 * count, f"{path.name}: se esperaba STL binario"
    index, vertices, triangles = {}, [], []
    for i in range(count):
        row = struct.unpack_from("<12f", data, 84 + 50 * i)
        tri = []
        for k in (3, 6, 9):
            key = tuple(round(row[k + j], 4) for j in range(3))
            if key not in index:
                index[key] = len(vertices)
                vertices.append(key)
            tri.append(index[key])
        if len(set(tri)) == 3:
            triangles.append(tuple(tri))
    return vertices, triangles


def bbox(vertices):
    return ([min(v[i] for v in vertices) for i in range(3)],
            [max(v[i] for v in vertices) for i in range(3)])


def open_edges(triangles):
    edges = {}
    for a, b, c in triangles:
        for x, y in ((a, b), (b, c), (c, a)):
            key = min(x, y), max(x, y)
            edges[key] = edges.get(key, 0) + 1
    return sum(n != 2 for n in edges.values())


def rotate_z(vertices, degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return [(c * x - s * y, s * x + c * y, z) for x, y, z in vertices]


def on_rear_edge(vertices):
    """Apoya la pared trasera: X queda horizontal, Z en la cama e Y pasa a altura."""
    ymax = max(v[1] for v in vertices)
    return [(x, z, ymax - y) for x, y, z in vertices]


def flip(vertices):
    return [(x, -y, -z) for x, y, z in vertices]


def place(vertices, cx, cy):
    lo, hi = bbox(vertices)
    dx, dy = cx - (lo[0] + hi[0]) / 2, cy - (lo[1] + hi[1]) / 2
    return [(x + dx, y + dy, z - lo[2]) for x, y, z in vertices]


def pack(rows):
    objects, x, y, row_h = [], MARGIN, MARGIN, 0.0
    for path, name, upside in rows:
        vertices, triangles = read_stl(path)
        if upside:
            vertices = flip(vertices)
        lo, hi = bbox(vertices)
        dx, dy = hi[0] - lo[0], hi[1] - lo[1]
        if x + dx > BED[0] - MARGIN:
            x, y, row_h = MARGIN, y + row_h + 6.0, 0.0
        objects.append((name, place(vertices, x + dx / 2, y + dy / 2), triangles))
        x, row_h = x + dx + 6.0, max(row_h, dy)
    return objects


def diagonal(path, name):
    vertices, triangles = read_stl(path)
    vertices = rotate_z(on_rear_edge(vertices), 45)
    return [(name, place(vertices, BED[0] / 2, BED[1] / 2), triangles)]


def flat_diagonal(path, name):
    vertices, triangles = read_stl(path)
    vertices = rotate_z(vertices, 45)
    return [(name, place(vertices, BED[0] / 2, BED[1] / 2), triangles)]


def write_3mf(path, objects, title):
    resources, build = [], []
    for oid, (name, vertices, triangles) in enumerate(objects, 1):
        vv = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in vertices)
        tt = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles)
        resources.append(f'<object id="{oid}" type="model" name="{name}"><mesh><vertices>{vv}</vertices><triangles>{tt}</triangles></mesh></object>')
        build.append(f'<item objectid="{oid}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="es" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">{title}</metadata><resources>{"".join(resources)}</resources>'
             f'<build>{"".join(build)}</build></model>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        archive.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        archive.writestr("3D/3dmodel.model", model)


def native_3mf(dest, objects):
    exe = shutil.which("bambu-studio")
    if not exe:
        write_3mf(dest, objects, dest.stem)
        return "3MF genérico; importar los STL si el laminador no lo abre"
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "source.3mf"
        write_3mf(source, objects, dest.stem)
        run = subprocess.run([exe, "--arrange", "0", "--outputdir", tmp, "--export-3mf", "native.3mf", str(source)],
                             capture_output=True, text=True)
        native = Path(tmp) / "native.3mf"
        assert native.exists(), run.stdout[-1000:] + run.stderr[-1000:]
        with zipfile.ZipFile(native) as zin, zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                if info.filename != "Metadata/project_settings.config":
                    zout.writestr(info, zin.read(info.filename))
    return "proyecto nativo; usa los ajustes abiertos en Bambu Studio"


def plates_config(config, groups, names):
    """Assign each object group to its own named Bambu Studio plate."""
    ids = {}
    for oid, body in re.findall(r'<object id="(\d+)">(.*?)</object>', config, re.S):
        match = re.search(r'key="name" value="([^"]*)"', body)
        if match:
            ids[match.group(1)] = oid
    blocks = []
    for number, (group, label) in enumerate(zip(groups, names), 1):
        instances = "".join(
            f'    <model_instance>\n      <metadata key="object_id" value="{ids[name]}"/>\n'
            f'      <metadata key="instance_id" value="0"/>\n'
            f'      <metadata key="identify_id" value="{100 + int(ids[name])}"/>\n    </model_instance>\n'
            for name, _, _ in group
        )
        blocks.append(
            f'  <plate>\n    <metadata key="plater_id" value="{number}"/>\n'
            f'    <metadata key="plater_name" value="{label}"/>\n'
            f'    <metadata key="locked" value="false"/>\n'
            f'    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
            f'    <metadata key="gcode_file" value=""/>\n{instances}  </plate>\n'
        )
    return re.sub(r'  <plate>.*?</plate>\n', lambda _: "".join(blocks), config, count=1, flags=re.S)


def plate_origin(index, count):
    cols = math.ceil(math.sqrt(count))
    return (index % cols) * BED[0] * 1.2, -(index // cols) * BED[1] * 1.2


PRESETS = (
    ("machine", os.environ.get("IMPRESORA", "Bambu Lab P2S 0.2 nozzle")),
    ("process", os.environ.get("PROCESO", "0.10mm Standard @BBL P2S 0.2 nozzle")),
    ("filament", os.environ.get("FILAMENTO", "Bambu PLA Basic @BBL P2S 0.2 nozzle")),
)


def flat_preset(root, kind, name):
    data = json.loads((root / kind / f"{name}.json").read_text(encoding="utf-8"))
    result = flat_preset(root, kind, data["inherits"]) if data.get("inherits") else {}
    for include in data.get("include", []):
        result.update({k: v for k, v in flat_preset(root, kind, include).items()
                       if k not in ("name", "type", "from", "instantiation", "setting_id", "filament_id")})
    result.update(data)
    result.pop("include", None)
    return result


def preset_args(exe, tmp):
    root = Path(exe).resolve()
    if root.stat().st_size < 4096:
        root = Path(re.search(r'"(/[^"]+)/AppRun"', root.read_text()).group(1)) / "bin/x"
    root = root.parents[1] / "resources/profiles/BBL"
    paths = {}
    for kind, name in PRESETS:
        data = dict(flat_preset(root, kind, name), inherits="", name=name, **{"from": "system"})
        paths[kind] = Path(tmp) / f"{kind}.json"
        paths[kind].write_text(json.dumps(data), encoding="utf-8")
    return ["--load-settings", f"{paths['machine']};{paths['process']}",
            "--load-filaments", str(paths["filament"])]


def native_multiplate(dest, groups, names):
    """Create the generated, multi-plate project without overwriting user projects."""
    exe = shutil.which("bambu-studio")
    if not exe:
        return None, "Bambu Studio is required for the multi-plate project"
    moved = []
    for index, group in enumerate(groups):
        ox, oy = plate_origin(index, len(groups))
        moved += [(name, [(x + ox, y + oy, z) for x, y, z in vertices], triangles)
                  for name, vertices, triangles in group]
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "source.3mf"
        write_3mf(source, moved, dest.stem)
        run = subprocess.run([exe, "--arrange", "0", *preset_args(exe, tmp), "--outputdir", tmp,
                              "--export-3mf", "native.3mf", str(source)], capture_output=True, text=True)
        native = Path(tmp) / "native.3mf"
        assert native.exists(), run.stdout[-2000:] + run.stderr[-2000:]
        with zipfile.ZipFile(native) as zin, zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename == "Metadata/model_settings.config":
                    text = plates_config(data.decode("utf-8"), groups, names)
                    support = ('<metadata key="enable_support" value="1"/>\n    '
                               '<metadata key="support_type" value="tree(auto)"/>\n    '
                               '<metadata key="support_style" value="tree_hybrid"/>\n    '
                               '<metadata key="support_threshold_angle" value="20"/>\n    '
                               '<metadata key="support_on_build_plate_only" value="0"/>\n    '
                               '<metadata key="support_critical_regions_only" value="0"/>\n    '
                               '<metadata key="support_remove_small_overhang" value="0"/>\n    '
                               '<metadata key="support_interface_top_layers" value="3"/>\n    '
                               '<metadata key="support_interface_spacing" value="0.25"/>\n    '
                               '<metadata key="support_top_z_distance" value="0.1"/>\n    '
                               '<metadata key="support_bottom_z_distance" value="0.2"/>\n    '
                               '<metadata key="support_object_xy_distance" value="0.25"/>\n    '
                               '<metadata key="tree_support_wall_count" value="1"/>\n    '
                               '<metadata key="brim_type" value="outer_only"/>\n    '
                               '<metadata key="brim_width" value="12"/>\n    ')
                    text = re.sub(r'(<metadata key="name" value="[^"]*_de_canto"/>\s*)'
                                  r'(<metadata key="extruder")', r'\g<1>' + support + r'\g<2>', text)
                    data = text.encode("utf-8")
                elif info.filename == "Metadata/project_settings.config":
                    settings = json.loads(data)
                    settings.update({
                        "support_type": "tree(auto)", "support_style": "tree_hybrid",
                        "support_threshold_angle": "20", "support_on_build_plate_only": "0",
                        "support_critical_regions_only": "0", "support_remove_small_overhang": "0",
                        "support_interface_top_layers": "3", "support_interface_spacing": "0.25",
                        "support_top_z_distance": "0.1", "support_bottom_z_distance": "0.2",
                        "support_object_xy_distance": "0.25", "tree_support_wall_count": "1",
                        "brim_type": "outer_only", "brim_width": "12", "brim_object_gap": "0",
                    })
                    data = json.dumps(settings, indent=4).encode("utf-8")
                elif info.filename == "Metadata/filament_sequence.json":
                    data = json.dumps({f"plate_{n}": {"sequence": []}
                                       for n in range(1, len(groups) + 1)}).encode()
                zout.writestr(info, data)
    return dest, "multi-plate Bambu project with P2S profile; tree supports and 8 mm brim on edge-printed body/lid"


def summarize(objects):
    pieces, all_vertices = [], []
    for name, vertices, triangles in objects:
        lo, hi = bbox(vertices)
        opened = open_edges(triangles)
        assert opened == 0, f"{name}: {opened} aristas abiertas"
        pieces.append({"nombre": name, "triangulos": len(triangles), "tamano_mm": [round(hi[i] - lo[i], 1) for i in range(3)]})
        all_vertices += vertices
    lo, hi = bbox(all_vertices)
    occupied = [round(hi[i] - lo[i], 1) for i in range(3)]
    assert occupied[0] <= BED[0] + .1 and occupied[1] <= BED[1] + .1, (occupied, BED)
    return {"piezas": pieces, "ocupa_mm": occupied, "cabe_en_cama": True}


def main():
    OUT.mkdir(exist_ok=True)
    plates = {
        "E9-pruebas-de-ajuste.3mf": pack([(p, "Prueba_" + p.stem, False) for p in sorted(FIT.glob("*.stl"))]),
        "E9-piezas-pequenas.3mf": pack([
            (STL / "soporte_fcob.stl", "Soporte_FCOB", True),
            (STL / "difusor_fcob_hex.stl", "Difusor_FCOB_hex", False),
            (STL / "placa_trasera_desmontable_lcd.stl", "Placa_trasera_desmontable_LCD", False),
            (STL / "aro_reten_piezo_bayoneta.stl", "Aro_reten_piezo_bayoneta", False),
        ]),
        "E9-guarda-120V.3mf": flat_diagonal(STL / "guarda_120v_e7.stl", "Guarda_120V_E9"),
        "E9-gabinete.3mf": diagonal(STL / "gabinete_e7.stl", "Gabinete_E9_de_canto"),
        "E9-tapa.3mf": diagonal(STL / "tapa_e7.stl", "Tapa_E9_de_canto"),
    }
    report = {"cama_mm": list(BED), "archivos": {}}
    for filename, objects in plates.items():
        data = summarize(objects)
        data["formato"] = native_3mf(OUT / filename, objects)
        report["archivos"][filename] = data
    generated = OUT / "E9-completo-generado.3mf"
    groups = list(plates.values())
    names = ["1 - FIT TESTS - PRINT FIRST", "2 - Small parts", "3 - 120 V guard",
             "4 - Enclosure body - supports", "5 - Lid - supports"]
    path, fmt = native_multiplate(generated, groups, names)
    if path:
        report["archivos"][generated.name] = {"camas": names,
                                                "piezas": sum(len(g) for g in groups), "formato": fmt}
    (OUT / "contenido.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
