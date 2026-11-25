#!/bin/sh
# Regenerate the current E.9 CAD and outputs. Usage: sh 3d/revision-e7/regenerar.sh [cad|bambu|json|vistas|validar-renders]
set -e
cd "$(dirname "$0")/../.."
run() {
  output=$(freecadcmd -c "p='3d/revision-e7/$1'; exec(compile(open(p).read(),p,'exec'),{'__file__':p,'__name__':'__main__'})" 2>&1) || {
    status=$?
    printf '%s\n' "$output" | grep -v -e 'saving' -e '%)' -e '^\s*$' -e '\*\*\*' -e 'Transfer' -e 'WorkSession' || true
    return "$status"
  }
  printf '%s\n' "$output" | grep -v -e 'saving' -e '%)' -e '^\s*$' -e '\*\*\*' -e 'Transfer' -e 'WorkSession' || true
}
case "${1:-todo}" in
  cad) run generar_modelo.py ;;
  bambu) python 3d/revision-e7/exportar_bambu.py ;;
  json) run render_modelo.py ;;
  vistas) blender -b --python 3d/revision-e7/render_modelo.py -- vistas >/dev/null ;;
  validar-renders) python 3d/revision-e7/validar_renders.py ;;
  todo) run generar_modelo.py; python 3d/revision-e7/exportar_bambu.py; run render_modelo.py; blender -b --python 3d/revision-e7/render_modelo.py -- vistas >/dev/null; python 3d/revision-e7/validar_renders.py ;;
esac
