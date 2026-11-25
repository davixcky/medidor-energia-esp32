#!/usr/bin/env python3
"""Comprueba que todos los enlaces relativos de los .md del repositorio existan.

    python3 herramientas/verificar_enlaces.py

Sale con código 1 si algún enlace apunta a un archivo que no está. Ignora los enlaces
http(s)/mailto y las anclas puras (#seccion). De los enlaces con ancla comprueba el archivo.
"""
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

RAIZ = Path(__file__).resolve().parents[1]
ENLACE = re.compile(r"\]\(\s*<?([^)<>\s]+)>?\s*(?:\"[^\"]*\")?\)")
EXTERNO = re.compile(r"^(https?:|mailto:|tel:|data:|#|//)")


def archivos_md():
    salida = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=RAIZ, capture_output=True, text=True, check=True
    ).stdout.split("\n")
    return [RAIZ / linea for linea in salida if linea.strip()]


def ignorado_por_git(rutas):
    """Devuelve el subconjunto que .gitignore excluye: archivos regenerables, no enlaces rotos."""
    if not rutas:
        return set()
    r = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        cwd=RAIZ, input="\n".join(rutas), capture_output=True, text=True,
    )
    return {linea.strip() for linea in r.stdout.split("\n") if linea.strip()}


def main():
    roto = []
    revisados = 0
    for md in archivos_md():
        texto = md.read_text(encoding="utf-8", errors="replace")
        # Fuera los bloques de código: sus "árboles" de carpetas no son enlaces.
        sin_codigo = re.sub(r"```.*?```", "", texto, flags=re.S)
        for linea_n, linea in enumerate(sin_codigo.split("\n"), 1):
            for destino in ENLACE.findall(linea):
                if EXTERNO.match(destino):
                    continue
                ruta = unquote(destino.split("#", 1)[0])
                if not ruta:
                    continue
                revisados += 1
                if not (md.parent / ruta).exists():
                    rel = (md.parent / ruta).resolve()
                    try:
                        rel = str(rel.relative_to(RAIZ))
                    except ValueError:
                        rel = str(rel)
                    roto.append((f"{md.relative_to(RAIZ)}: {destino}", rel))

    total_md = len(archivos_md())
    ignorados = ignorado_por_git([rel for _, rel in roto])
    generados = [d for d, rel in roto if rel in ignorados]
    rotos = [d for d, rel in roto if rel not in ignorados]

    print(f"{revisados} enlaces relativos revisados en {total_md} archivos .md")
    if generados:
        print(f"\n{len(generados)} apuntan a archivos regenerables (en .gitignore), no es un error:")
        for d in generados:
            print(f"  · {d}")
    if rotos:
        print(f"\n{len(rotos)} enlaces rotos:")
        for d in rotos:
            print(f"  ✗ {d}")
        return 1
    print("Todos los enlaces relativos resuelven.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
