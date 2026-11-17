#!/usr/bin/env python3
"""Modelo E.5 del medidor: cinco perforadas y zona de red segregada."""
from pathlib import Path
import json
import sys

import FreeCAD as App
import Import
import MeshPart
import Part

HERE = Path(__file__).resolve().parent
STL = HERE / "stl"; STL.mkdir(parents=True, exist_ok=True)
W, D, H, LID = 276.0, 210.0, 64.0, 3.0
WALL, FLOOR, Z_BOARD = 2.5, 3.0, 9.0
NETWORK_Y = 165.0
STRIP_W = 12.5
BOARDS = {
    "T1": (212.0, 8.0, 60.0, 50.0, "POTENCIA"),
    "T2": (118.0, 8.0, 90.0, 70.0, "CORRIENTE + VBIAS"),
    "T3": (8.0, 100.0, 70.0, 50.0, "TENSION MBT"),
    "T4": (8.0, 8.0, 100.0, 80.0, "ESP32 + LCD"),
    "T5": (90.0, 95.0, 80.0, 60.0, "INTERFAZ + ALERTAS"),
}
COLORS = {
    "body": (.11,.14,.17), "lid": (.32,.35,.39), "guard": (.82,.12,.08),
    "perf": (.45,.25,.08), "pad": (.86,.62,.15), "chip": (.035,.04,.045),
    "connector": (.85,.88,.90), "esp": (.05,.25,.20), "wire": (.08,.45,.92),
    "power": (.88,.08,.05), "ground": (.04,.04,.04), "support": (.16,.18,.20),
    "strip": (.96,.96,.96), "led": (.10,.78,.92), "screen": (.02,.17,.28),
    "network": (.22,.38,.18),
}


def v(p): return App.Vector(*p)
def box(w,d,h,x=0,y=0,z=0): return Part.makeBox(w,d,h,v((x,y,z)))


def tube(points, r=.7):
    shapes=[]
    for a,b in zip(points,points[1:]):
        av,bv=v(a),v(b); dv=bv.sub(av)
        if dv.Length>.01: shapes.append(Part.makeCylinder(r,dv.Length,av,dv))
    return Part.makeCompound(shapes)


def add(doc,name,shape,color,group="interior"):
    obj=doc.addObject("PartDesign::Feature",name); obj.Label=name.replace("_"," "); obj.Shape=shape
    obj.addProperty("App::PropertyString","ColorRGB","Render"); obj.ColorRGB=",".join(map(str,COLORS[color]))
    obj.addProperty("App::PropertyString","AssemblyGroup","Render"); obj.AssemblyGroup=group
    return obj


def perfboard(x,y,w,d):
    s=box(w,d,1.6,x,y,Z_BOARD); holes=[]
    for hx,hy in ((x+4,y+4),(x+w-4,y+4),(x+4,y+d-4),(x+w-4,y+d-4)):
        holes.append((hx,hy)); s=s.cut(Part.makeCylinder(1.6,3,v((hx,hy,Z_BOARD-.5))))
    return s,holes


def pads(x,y,w,d):
    rings=[]
    for ix in range(int((w-8)//5.08)+1):
        for iy in range(int((d-8)//5.08)+1):
            px,py=x+4+ix*5.08,y+4+iy*5.08
            r=Part.makeCylinder(1.15,.12,v((px,py,Z_BOARD+1.6))).cut(Part.makeCylinder(.45,.2,v((px,py,Z_BOARD+1.55))))
            rings.append(r)
    return Part.makeCompound(rings)


def dip(x,y,length=20):
    return box(length,10,4,x,y,Z_BOARD+2).cut(Part.makeCylinder(1.4,2,v((x+3,y+5,Z_BOARD+5))))


def conn(x,y,pins,vertical=False):
    w,d=(6,pins*2.54+2) if vertical else (pins*2.54+2,6)
    return box(w,d,7,x,y,Z_BOARD+1.6)


def enclosure(doc):
    bottom=box(W,D,FLOOR)
    walls=[box(W,WALL,H-FLOOR,0,0,FLOOR),box(W,WALL,H-FLOOR,0,D-WALL,FLOOR),
           box(WALL,D-2*WALL,H-FLOOR,0,WALL,FLOOR),box(WALL,D-2*WALL,H-FLOOR,W-WALL,WALL,FLOOR)]
    barrier=box(W-2*WALL,3,H-8,WALL,NETWORK_Y,FLOOR)
    add(doc,"Gabinete_E5",bottom.fuse(walls+[barrier]),"body","body")
    lid=box(W,D,LID,0,0,H)
    lid=lid.cut(box(46,25,LID+2,22,42,H-1))
    lid=lid.cut(box(70,6,LID+2,188,116,H-1))
    for x in (98,128): lid=lid.cut(Part.makeCylinder(6.2,LID+2,v((x,52,H-1))))
    lid=lid.cut(Part.makeCylinder(3.8,LID+2,v((158,52,H-1))))
    add(doc,"Tapa_E5",lid,"lid","lid")
    # Guarda independiente y desmontable de la zona de red.
    guard=box(W-10,D-NETWORK_Y-7,2,5,NETWORK_Y+4,42)
    guard=guard.fuse(box(W-10,2,39,5,NETWORK_Y+4,FLOOR))
    add(doc,"Guarda_120V_E5",guard,"guard","guard")


def populate(doc):
    mounting=[]
    for ref,(x,y,w,d,label) in BOARDS.items():
        board,holes=perfboard(x,y,w,d); mounting += holes
        add(doc,f"{ref}_Perforada_{int(w)}x{int(d)}",board,"perf")
        add(doc,f"{ref}_Donas",pads(x,y,w,d),"pad")
        if ref=="T1":
            add(doc,"T1_PTC_Diodo",box(28,8,6,x+8,y+10,Z_BOARD+1.6),"connector")
            add(doc,"T1_C470u",Part.makeCylinder(5,12,v((x+43,y+18,Z_BOARD+1.6))),"chip")
            add(doc,"T1_Salidas_Estrella",conn(x+10,y+d-10,5),"connector")
        elif ref=="T2":
            add(doc,"T2_Pasivos_CH1_CH2",Part.makeCompound([box(8,3,3,x+9+i*12,y+16,Z_BOARD+2) for i in range(6)]),"connector")
            add(doc,"T2_C7_VBIAS",Part.makeCylinder(4,9,v((x+25,y+42,Z_BOARD+1.6))),"chip")
            add(doc,"T2_ADC_I",conn(x+w-17,y+d-9,4),"connector")
        elif ref=="T3":
            add(doc,"T3_Filtro_V",Part.makeCompound([box(9,3,3,x+10+i*13,y+18,Z_BOARD+2) for i in range(4)]),"connector")
            add(doc,"T3_ZMPT_LV",conn(x+8,y+d-9,3),"connector")
            add(doc,"T3_ADC_V",conn(x+w-16,y+d-9,3),"connector")
        elif ref=="T4":
            add(doc,"T4_ESP32",box(28,54,8,x+9,y+13,Z_BOARD+1.6),"esp")
            add(doc,"T4_LCD_Header",conn(x+50,y+12,8),"connector")
            add(doc,"T4_ADC_I",conn(x+w-12,y+8,4,True),"connector")
            add(doc,"T4_ADC_V",conn(x+w-12,y+34,3,True),"connector")
        else:
            add(doc,"T5_HCT245",dip(x+12,y+20,26),"chip")
            add(doc,"T5_Encoder_Filtros",Part.makeCompound([box(7,3,3,x+10+i*10,y+8,Z_BOARD+2) for i in range(5)]),"connector")
            add(doc,"T5_Piezo_Driver",box(18,10,7,x+50,y+39,Z_BOARD+1.6),"chip")
            add(doc,"T5_UI_Arneses",conn(x+w-10,y+8,5,True),"connector")
    add(doc,"Postes_M3",Part.makeCompound([Part.makeCylinder(3.2,Z_BOARD-FLOOR,v((x,y,FLOOR))) for x,y in mounting]),"support")

    # Arnés en estrella y señales con retorno, por corredores libres.
    signal_paths=[[(108,44,16),(113,44,16),(113,58,16),(118,58,16)],
                  [(58,88,16),(58,94,16),(43,94,16),(43,100,16)],
                  [(108,70,16),(180,86,16),(180,125,16),(170,125,16)],
                  [(208,45,17),(210,45,17),(210,70,17),(70,92,17),(70,100,17)]]
    add(doc,"Arneses_Senal_E5",Part.makeCompound([tube(p,.75) for p in signal_paths]),"wire")
    add(doc,"Bus_5V_GND_Estrella",tube([(242,58,18),(242,88,18),(175,88,18),(175,150,18)],1.2),"power")

    # Barra real de 4 píxeles, claramente visible y con soporte adaptable 10-12,5 mm.
    sx,sy,sz=188.0,116.0,38.0
    add(doc,"Soporte_Barra_NeoPixel_13p2mm",box(71,STRIP_W+.7,2.2,sx-2,sy-.35,sz-1.5),"support")
    add(doc,"Barra_NeoPixel_WS2812B_4px",box(66.7,STRIP_W,1.2,sx,sy,sz),"strip")
    add(doc,"NeoPixels_4",Part.makeCompound([box(5,5,1.8,sx+6.3+i*16.67,sy+(STRIP_W-5)/2,sz+1.2) for i in range(4)]),"led")

    # Elementos de panel/tapa: LCD, encoder, botones y piezo.
    add(doc,"LCD_1p9_ST7789",box(51.2,27.3,1.6,19.4,40.8,H-5),"screen","lid")
    add(doc,"Encoder",Part.makeCylinder(6,13,v((158,52,H-10))),"connector","lid")
    add(doc,"SW1_SW2",Part.makeCompound([Part.makeCylinder(6,12,v((x,52,H-10))) for x in (98,128)]),"connector","lid")
    add(doc,"Piezo_pasivo",Part.makeCylinder(7,7,v((184,83,18))),"chip")

    # Zona de red: ZMPT, fusible y bornera, siempre detrás del tabique.
    add(doc,"ZMPT101B_Z1",box(49,19,15,110,178,FLOOR+4),"network","network")
    add(doc,"Fusible_T500mA_Z1",box(30,10,10,45,181,FLOOR+4),"chip","network")
    add(doc,"Bornera_LN_Z1",box(20,12,11,205,180,FLOOR+4),"connector","network")
    add(doc,"Cableado_Red_Z1",Part.makeCompound([
        tube([(225,186,12),(180,186,12),(159,187,12)],1.2),
        tube([(205,190,12),(85,190,12),(75,186,12),(45,186,12)],1.2)]),"power","network")


def validate():
    issues=[]; rects=[]
    for ref,(x,y,w,d,_) in BOARDS.items():
        if x<WALL+2 or y<WALL+2 or x+w>W-WALL-1 or y+d>NETWORK_Y-5: issues.append(f"{ref} fuera de MBT")
        for other,ox,oy,ow,od in rects:
            if x<ox+ow and x+w>ox and y<oy+od and y+d>oy: issues.append(f"solape {ref}/{other}")
        rects.append((ref,x,y,w,d))
    report={"revision":"E.5","enclosure_mm":[W,D,H+LID],"network_partition_y_mm":NETWORK_Y,
            "boards":{k:list(v[:4]) for k,v in BOARDS.items()},"neopixel_strip_mm":[66.7,STRIP_W],
            "neopixel_support_clearance_mm":13.2,"issues":issues,"valid":not issues,
            "note":"Colocación por envolventes; confirmar medidas de componentes comprados antes de imprimir."}
    (HERE/"validacion-3d.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    if issues: raise RuntimeError(issues)


def main():
    validate(); doc=App.newDocument("Medidor_E5_Perforadas")
    enclosure(doc); populate(doc); doc.recompute(); doc.saveAs(str(HERE/"medidor-E5-perforadas.FCStd"))
    objects=[o for o in doc.Objects if hasattr(o,"Shape") and not o.Shape.isNull()]
    Import.export(objects,str(HERE/"medidor-E5-perforadas.step"))
    for name in ("Gabinete_E5","Tapa_E5","Guarda_120V_E5","Soporte_Barra_NeoPixel_13p2mm"):
        obj=doc.getObject(name); mesh=MeshPart.meshFromShape(Shape=obj.Shape,LinearDeflection=.12,AngularDeflection=.35)
        mesh.write(str(STL/f"{name.lower()}.stl"))
    print(f"Medidor E.5 CAD: {len(objects)} objetos; {W} x {D} x {H+LID} mm")


if __name__=="__main__": main()
