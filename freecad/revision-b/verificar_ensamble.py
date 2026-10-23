"""freecadcmd freecad/revision-b/verificar_ensamble.py"""
import FreeCAD as App,json
from pathlib import Path
p=Path(__file__).resolve().parent;d=App.openDocument(str(p/'medidor-revB.FCStd'))
structural=['Cuerpo','Tapa','Guarda_120V','Porta_NeoPixel','Retenedor_LCD_I','Retenedor_LCD_D']
items=[o for o in d.Objects if hasattr(o,'ColorRGB') and o.Name.startswith(('LCD','Placa','Piezo','Tira_NeoPixel','Pixel_','SW1','SW2','Encoder_'))]
issues=[]
for name in structural:
 for o in items:
  volume=d.getObject(name).Shape.common(o.Shape).Volume
  if volume>.05:issues.append([name,o.Name,round(volume,3)])
(p/'holgura-electronica.json').write_text(json.dumps(issues,indent=2))
assert not issues,issues
print('Sin interferencias entre piezas estructurales y electrónica comprobada')
