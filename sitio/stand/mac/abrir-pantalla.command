#!/bin/bash
# Doble clic en el Mac: abre la segunda pantalla del stand en una ventana sin barras.
# Luego arrástrala a la pantalla pequeña y pulsa Control + Command + F para pantalla completa.
# Para girar el contenido: GIRAR=90 (edita la línea de abajo).
GIRAR=0
DIR="$(cd "$(dirname "$0")/.." && pwd)"
URL="file://$DIR/pantalla.html?girar=$GIRAR"
if [ -d "/Applications/Google Chrome.app" ]; then
  open -na "Google Chrome" --args --app="$URL" --user-data-dir="$HOME/.stand-medidor-chrome" --no-first-run
else
  open -a Safari "$URL"
fi
