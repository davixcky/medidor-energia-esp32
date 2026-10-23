"""Revisión B: gabinete PETG con tapa magnética y guarda interior atornillada.
freecadcmd freecad/medidor_profesional.py
No cambia la PCB ni sobrescribe la revisión anterior.
"""
import sys,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import FreeCAD as App
import Part,MeshPart,Import
import medidor as base
from comun import V,Modelo,caja_redondeada,cilindro,texto,tubo,COLOR
OUT=HERE/'revision-b';OUT.mkdir(exist_ok=True)
base.R_ESQ=10.0
TOP=76.6;ZLID=72.;MAG_D=8.2;MAG_DEPTH=3.2
# Provisional cable overmold envelope, not a claim about an unmeasured USB-C board.
USB_CLEAR_W=18.;USB_CLEAR_H=10.;USB_CORNER_R=2.
def usb_cut(depth=6):
 p=caja_redondeada(USB_CLEAR_W,USB_CLEAR_H,depth,USB_CORNER_R)
 p.rotate(V(0,0,0),V(1,0,0),90)
 p.translate(V(base.X_USB-USB_CLEAR_W/2,4,base.Z_USB-USB_CLEAR_H/2))
 return p

def usb_coupon():
 p=caja_redondeada(40,25,2.5,3)
 p=p.cut(caja_redondeada(USB_CLEAR_W,USB_CLEAR_H,4,USB_CORNER_R,11,7.5,-.5))
 return p

CORNERS=[(7,7),(193,7),(7,143),(193,143)]
COLOR.update(grafito=(.12,.15,.18),panel=(.035,.045,.055),cubierta=(.31,.35,.39),tinta=(.86,.9,.91),ambar=(.95,.46,.07),difusor=(.86,.9,.91))

def soft(shape,radius,levels):
 edges=[e for e in shape.Edges if e.BoundBox.ZLength<1e-5 and any(abs(e.BoundBox.ZMin-z)<1e-4 for z in levels)]
 try:return shape.makeFillet(radius,edges)
 except Exception:return shape

def body():
 c=base.cuerpo()
 c=c.cut(usb_cut())
 for x,y in CORNERS:
  c=c.fuse(cilindro(12,base.H_CUERPO-base.PISO,x,y,base.PISO))
  c=c.cut(cilindro(MAG_D,MAG_DEPTH+.1,x,y,ZLID-MAG_DEPTH))
 # Posts and ribs for the independently fastened mains guard.
 for x in (20,160):
  c=c.fuse(cilindro(8,57.5,x,116,2.5))
  c=c.fuse(Part.makeBox(4,8,57.5,V(x-2,108,2.5)))
  c=c.cut(cilindro(2.7,10,x,116,50.5))
 # Rear seating ledge; no through-holes added to the mains compartment.
 c=c.fuse(Part.makeBox(180,3,3,V(10,144.5,57)))
 # Finger recess on the low-voltage front, below the lid edge.
 notch=Part.makeCylinder(10,3,V(100,-.4,77),V(0,1,0))
 c=c.cut(notch)
 return soft(c.removeSplitter(),.6,[72])

def lid():
 t=caja_redondeada(200,150,4.6,10,0,0,72)
 t=soft(t,.8,[TOP])
 # Locating lip, 0.4 mm nominal clearance from the shell interior.
 lip=caja_redondeada(194.2,144.2,3.5,7.1,2.9,2.9,68.5)
 lip=lip.cut(caja_redondeada(191.2,141.2,4,5.6,4.4,4.4,68.3))
 for x,y in CORNERS:lip=lip.cut(cilindro(13,5,x,y,68))
 t=t.fuse(lip)
 for x,y in CORNERS:t=t.cut(cilindro(MAG_D,MAG_DEPTH,x,y,72))
 t=t.cut(cilindro(7.2,9,164,26,71)) # encoder roscado M7, verificar pieza real
 t=t.cut(Part.makeBox(44,24,8,V(33,50.5,71)))
 # Raised LCD PCB nests into underside; active glass is 1.3 mm below lid top.
 t=t.cut(Part.makeBox(51.8,27.9,2.3,V(29.1,48.55,71.9)))
 # Shallow seat for optional 0.8-mm transparent protective window.
 t=t.cut(Part.makeBox(50,30,1.5,V(30,47.5,TOP-1.5)))
 for x in (125,155):t=t.cut(cilindro(12.2,8,x,62.5,71))
 for y in (55,75):t=t.cut(caja_redondeada(6,10,8,1,92,y-5,71))
 # Diffused NeoPixel bar, with removable strip carrier below it.
 t=t.cut(caja_redondeada(80,6,8,2.9,60,26,71))
 for x in (54,146):
  t=t.fuse(cilindro(7,7,x,29,65))
  t=t.cut(cilindro(2.7,6.5,x,29,64.5))
 # Passive piezo pocket, 12 mm nominal diameter / 7 mm high; friction-free fit.
 ring=cilindro(16,8,165,97,64).cut(cilindro(12.6,9,165,97,63.5))
 t=t.fuse(ring)
 for x in (162,165,168):
  t=t.cut(caja_redondeada(1.4,7,6,.6,x-.7,93.5,71))
 # LCD retainers: M3 nuts accessible from below, not heat-set inserts.
 for x in (23.5,86.5):
  for y in (43,82):
   t=t.fuse(cilindro(8,1.6,x,y,70.4))
   t=t.cut(cilindro(3.4,5.2,x,y,70))
   radius=5.7/math.sqrt(3)
   pts=[V(x+radius*math.cos(k*math.pi/3),y+radius*math.sin(k*math.pi/3),70.4) for k in range(7)]
   t=t.cut(Part.Face(Part.makePolygon(pts)).extrude(V(0,0,2.6)))
 return t.removeSplitter()

def fascia():
 p=caja_redondeada(154,51,.8,5,23,37,TOP)
 p=p.cut(Part.makeBox(44,24,2,V(33,50.5,TOP-.2)))
 for x in (125,155):p=p.cut(cilindro(12.2,2,x,62.5,TOP-.2))
 for y in (55,75):p=p.cut(caja_redondeada(6,10,2,1,92,y-5,TOP-.2))
 return p.removeSplitter()

def guard():
 p=caja_redondeada(194.2,35.9,2.4,6,2.9,111.2,60)
 for x,y in CORNERS:p=p.cut(cilindro(13,4,x,y,59))
 for x in (20,160):p=p.cut(cilindro(3.4,4,x,116,59))
 return p.removeSplitter()

def retainer(left):
 x=19 if left else 82
 p=Part.makeBox(12,47,2,V(x,39,63.5))
 for y in (43,82):p=p.cut(cilindro(3.4,4,x+4.5,y,63))
 sx=29.4 if left else 78.8
 p=p.fuse(Part.makeBox(1.8,25,1.9,V(sx,50,65.5)))
 if not left:p=p.fuse(Part.makeBox(3.2,25,2,V(78.8,50,63.5)))
 return p.removeSplitter()

def diffuser(y):
 # Rear flange locates the part; the neck rises through lid and fascia.
 a=caja_redondeada(8,12,1,1,91,y-6,71)
 a=a.fuse(caja_redondeada(5.7,9.7,5.6,.8,92.15,y-4.85,72))
 a=a.cut(cilindro(5.2,1.5,95,y,70.5))
 return a.removeSplitter()

def light_diffuser():
 p=caja_redondeada(84,10,1,3,58,24,71)
 return p.fuse(caja_redondeada(79.6,5.6,4.8,2.7,60.2,26.2,72)).removeSplitter()

def light_carrier():
 p=caja_redondeada(100,14,1.6,3,50,22,63.4)
 for x in (54,146):p=p.cut(cilindro(3.4,3,x,29,63))
 # Strip rests on this shelf, emitters face the diffuser.
 for y in (22,34):p=p.fuse(Part.makeBox(74,2,2,V(63,y,65)))
 return p.removeSplitter()

def coupon():
 p=caja_redondeada(106,52,6.6,3)
 for x,d in zip((14,37,60),(8.1,8.2,8.3)):
  p=p.cut(cilindro(d,3.2,x,15,3.4))
  p=p.cut(texto(str(d),3,x,25,6.1,.7))
 for x,d in ((14,2.7),(37,3.4),(60,12.2)):
  p=p.cut(cilindro(d,8,x,40,-1))
 # Diffuser rectangular seat and a 5.4-mm panel-stack test area.
 p=p.cut(caja_redondeada(6,10,8,1,79,10,-1))
 p=p.cut(Part.makeBox(22,23,1.2,V(78,27,5.4)))
 p=p.cut(cilindro(12.2,7,89,39,-1))
 return p

m=Modelo('medidor-revB');base.placa(m);base.interior(m)
for o in list(m.doc.Objects):
 if o.Name.startswith(('Tinta_grabado','Rotulo_peligro','Soporte_LCD','Mazo_D8')) or o.Name=='D8_LED':m.doc.removeObject(o.Name)
for o in m.doc.Objects:
 if o.Name in ('LCD_modulo','LCD_pantalla'):o.Shape=o.Shape.translated(V(0,0,4.9))
 if o.Name.startswith(('SW1','SW2')) and hasattr(o,'Grupo') and o.Grupo=='tapa':
  x=125 if o.Name=='SW1' else 155
  # Panel-mount switch envelope: threaded barrel crosses the 5.4-mm stack;
  # the retaining nut must remain entirely below the lid.
  barrel=cilindro(12,18,x,62.5,60)
  cap=cilindro(9,4,x,62.5,77.4)
  nut=cilindro(16,2,x,62.5,69.8).cut(cilindro(12,3,x,62.5,69.3))
  o.Shape=barrel.fuse([cap,nut])
m.agregar('Cuerpo',body(),'grafito','cuerpo')
m.agregar('Tapa',lid(),'cubierta','tapa')
m.agregar('Panel',fascia(),'panel','tapa')
m.agregar('Encoder_cuerpo',Part.makeBox(12,12,12,V(158,20,59.8)),'metal','tapa')
m.agregar('Encoder_rosca',cilindro(7,7,164,26,71.8),'metal','tapa')
m.agregar('Encoder_eje',cilindro(6,12,164,26,78),'metal','tapa')
m.agregar('Encoder_tuerca',cilindro(10,2,164,26,76.7).cut(cilindro(7,3,164,26,76.2)),'metal','tapa')
m.agregar('Encoder_perilla',cilindro(20,12,164,26,80),'panel','tapa')
m.agregar('Leyenda_encoder',texto('AJUSTES',2.8,164,10,TOP+.03,.05),'tinta','tapa')

m.agregar('Difusor_NeoPixel',light_diffuser(),'difusor','tapa')
m.agregar('Porta_NeoPixel',light_carrier(),'grafito','tapa')
m.agregar('Tira_NeoPixel',Part.makeBox(66.7,10,.5,V(66.65,24,65)),'panel','tapa')
for k in range(4):
 m.agregar(f'Pixel_{k}',Part.makeBox(5,5,1.6,V(72.5+k*16.67,26.5,65.5)),'verde_led','tapa')
m.agregar('Piezo_12mm',cilindro(12,7,165,97,64.5),'negro','tapa')
m.agregar('Guarda_120V',guard(),'ambar','guarda')
m.agregar('Retenedor_LCD_I',retainer(True).translated(V(0,0,4.9)),'grafito','tapa')
m.agregar('Retenedor_LCD_D',retainer(False).translated(V(0,0,4.9)),'grafito','tapa')
for y,name,color in ((55,'Estado','verde_led'),(75,'Alimentacion','ambar')):
 m.agregar('Difusor_'+name,diffuser(y),'difusor','tapa')
 m.agregar('LED_'+name,cilindro(5,6,95,y,65.5),color,'tapa')
for k,(x,y) in enumerate(CORNERS):
 m.agregar(f'Iman_base_{k}',cilindro(8,3,x,y,68.9),'metal','cuerpo')
 m.agregar(f'Iman_tapa_{k}',cilindro(8,3,x,y,72.1),'metal','tapa')
# Colored text is a paint/label representation; not a structural printed solid.
for k,(s,size,x,y) in enumerate([('MEDIDOR DE ENERGÍA',5,80,20),('ESP32  /  DOS CANALES',2.8,75,12),('VISTA',3,125,44),('ACCIÓN',3,155,44),('ESTADO',2.5,110,53),('5 V',2.5,106,74)]):
 m.agregar('Leyenda_'+str(k),texto(s,size,x,y,TOP+(.85 if k>=2 else .03),.05),'tinta','tapa')
m.agregar('Advertencia_tapa',texto('120 V  ·  DESCONECTAR ANTES DE ABRIR',3,100,128,TOP+.03,.05),'ambar','tapa')
m.agregar('Advertencia_guarda',texto('120 V  /  SOLO SERVICIO',3,100,128,62.41,.04),'negro','guarda')
# Power LED is an optional low-voltage harness: protected +5V -> 1k -> LED -> GND.
# Status LED continues to use the existing D8 circuit and its series resistor.
for k,(ref,pin,dest) in enumerate([('D8',2,(95,55,65.5)),('D8',1,(97,55,65.5)),('J5',1,(95,75,65.5)),('J5',3,(97,75,65.5))]):
 a=base.pad(ref,pin,7);m.agregar(f'Mazo_LED_{k}',tubo([a,(a[0],a[1],43),(170,90,48),(dest[0],90,55),dest],1.1),'rojo' if k%2==0 else 'negro')
m.doc.recompute()
parts=[('Cuerpo','cuerpo',False),('Tapa','tapa',True),('Panel','panel',False),('Guarda_120V','guarda-120v',False),('Retenedor_LCD_I','retenedor-lcd-i',False),('Retenedor_LCD_D','retenedor-lcd-d',False),('Difusor_Estado','difusor-estado',False),('Difusor_Alimentacion','difusor-alimentacion',False)]
parts += [('Difusor_NeoPixel','difusor-neopixel',False),('Porta_NeoPixel','porta-neopixel',False)]
reports=[]
(OUT/'stl').mkdir(exist_ok=True)
for name,file,flip in parts:
 o=m.doc.getObject(name);shape=o.Shape.copy()
 assert shape.isValid(),name
 assert len(shape.Solids)==1,(name,len(shape.Solids))
 if flip:shape.rotate(shape.BoundBox.Center,V(1,0,0),180)
 bb=shape.BoundBox;shape.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.08,AngularDeflection=.3)
 assert mesh.isSolid(),name
 mesh.write(str(OUT/'stl'/f'{file}.stl'))
 bb=shape.BoundBox;dims=[bb.XLength,bb.YLength,bb.ZLength]
 assert max(dims)<256,(name,dims)
 reports.append(dict(part=name,mm=dims,volume_mm3=shape.Volume,valid=True,closed_mesh=True,solids=len(shape.Solids)))
e=caja_redondeada(40,25,4.6,3).cut(cilindro(7.2,6,20,12.5,-.5));assert e.isValid();MeshPart.meshFromShape(Shape=e,LinearDeflection=.06,AngularDeflection=.3).write(str(OUT/'stl/cupon-encoder.stl'))
u=usb_coupon();assert u.isValid();MeshPart.meshFromShape(Shape=u,LinearDeflection=.06,AngularDeflection=.3).write(str(OUT/'stl/cupon-usbc.stl'))
c=coupon();assert c.isValid();MeshPart.meshFromShape(Shape=c,LinearDeflection=.06,AngularDeflection=.3).write(str(OUT/'stl/cupon-ajuste.stl'))
# Test real assembly positions, before export normalization.
collisions=[]
for i,(name,_,_) in enumerate(parts):
 for other,_,_ in parts[i+1:]:
  volume=m.doc.getObject(name).Shape.common(m.doc.getObject(other).Shape).Volume
  if volume>.01:collisions.append([name,other,round(volume,3)])
(OUT/'interferencias.json').write_text(json.dumps(collisions,indent=2))
assert not collisions,collisions
m.doc.saveAs(str(OUT/'medidor-revB.FCStd'))
Import.export([o for o in m.doc.Objects if hasattr(o,'ColorRGB')],str(OUT/'medidor-revB.step'))
(OUT/'validacion-cad.json').write_text(json.dumps(reports,indent=2))
print('REVISION B:',len(reports),'piezas verificadas; cupón de ajuste; CAD y STEP exportados')
