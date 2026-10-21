#!/usr/bin/env bash
# Exporta lo necesario para fabricar la PCB de una cara del medidor (../hardware/fabricacion):
#   toner/  PDF a escala 1:1 para imprimir en láser (transferencia de tóner)
#   cnc/    Gerber y taladros Excellon (FlatCAM, Candle, bCNC) y el zip para un fabricante
#   guia-montaje.pdf, vista-cobre-desde-abajo.pdf, vista-toner.png y DRC
# Las vistas 3D para el documento van a ../img/3d-placa-{arriba,abajo,iso}.png.
set -euo pipefail
cd "$(dirname "$0")/../hardware"
PCB=medidor-energia.kicad_pcb
OUT=fabricacion
IMG=../img
q() { grep -v -e assert -e '^Plotted' -e '^Done' -e '^$' -e Debug || true; }

rm -rf "$OUT/toner" "$OUT/cnc"
mkdir -p "$OUT/toner" "$OUT/cnc"

# Cobre (B.Cu) sin espejo: el papel va boca abajo sobre el cobre. El texto de cobre se lee al
# revés en el papel y al derecho en la placa.
kicad-cli pcb export pdf --mode-single --black-and-white --drill-shape-opt 1 \
  --layers B.Cu,Edge.Cuts -o "$OUT/toner/1-cobre-B_Cu-1a1.pdf" "$PCB" 2>&1 | q
# Serigrafía del lado de componentes (opcional), en espejo para transferirla arriba
kicad-cli pcb export pdf --mode-single --black-and-white --mirror --drill-shape-opt 0 \
  --layers F.Silkscreen,Edge.Cuts -o "$OUT/toner/2-serigrafia-F_SilkS-espejo-1a1.pdf" "$PCB" 2>&1 | q
# Guía de montaje en color: componentes, puentes y pistas vistas desde arriba
kicad-cli pcb export pdf --mode-single --drill-shape-opt 2 \
  --layers B.Cu,F.Silkscreen,F.Fab,Edge.Cuts -o "$OUT/guia-montaje.pdf" "$PCB" 2>&1 | q
# El cobre como se ve al soldar (desde abajo)
kicad-cli pcb export pdf --mode-single --mirror --drill-shape-opt 2 \
  --layers B.Cu,Edge.Cuts -o "$OUT/vista-cobre-desde-abajo.pdf" "$PCB" 2>&1 | q

# CNC: Gerber y taladros con origen en la esquina de la placa
kicad-cli pcb export gerbers --layers B.Cu,F.Silkscreen,B.Mask,Edge.Cuts \
  --use-drill-file-origin --no-protel-ext -o "$OUT/cnc/" "$PCB" 2>&1 | q
kicad-cli pcb export drill --format excellon --excellon-units mm --drill-origin plot \
  --excellon-separate-th -o "$OUT/cnc/" "$PCB" 2>&1 | q
( cd "$OUT/cnc" && zip -q gerbers-medidor.zip ./* )

# Vista previa del cobre para el documento (recortada al borde de la placa)
pdftoppm -r 200 -png -singlefile "$OUT/toner/1-cobre-B_Cu-1a1.pdf" "$OUT/vista-toner"
magick "$OUT/vista-toner.png" -trim +repage -bordercolor white -border 20 "$OUT/vista-toner.png"
cp "$OUT/vista-toner.png" "$IMG/pcb-cobre-toner.png"

# Vistas 3D
kicad-cli pcb render --side top --quality high --width 2000 --height 1300 --background opaque \
  -o "$IMG/3d-placa-arriba.png" "$PCB" 2>&1 | q
kicad-cli pcb render --side bottom --quality high --width 2000 --height 1300 --background opaque \
  -o "$IMG/3d-placa-abajo.png" "$PCB" 2>&1 | q
kicad-cli pcb render --quality high --width 2000 --height 1300 --background opaque --rotate '-50,0,35' \
  --zoom 0.9 -o "$IMG/3d-placa-iso.png" "$PCB" 2>&1 | q
kicad-cli pcb export step --subst-models --force -o 3d/medidor-placa.step "$PCB" 2>&1 | q

# DRC con paridad contra el esquemático
kicad-cli pcb drc --schematic-parity -o drc.rpt "$PCB" 2>&1 | q
grep -E "Found|\*\* " drc.rpt || true
echo "listo: hardware/$OUT/"
