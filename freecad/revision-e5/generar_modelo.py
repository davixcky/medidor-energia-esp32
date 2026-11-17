#!/usr/bin/env python3
"""Modelo E.5 basado en las envolventes de los artículos comprados."""
from pathlib import Path
import json
import sys

import FreeCAD as App
import Import
import MeshPart
import Part

HERE = Path(__file__).resolve().parent
STL = HERE / "stl"; STL.mkdir(parents=True, exist_ok=True)
W, D, H, LID = 340.0, 240.0, 67.0, 3.0
WALL, FLOOR, Z_BOARD = 2.5, 3.0, 9.0
NETWORK_Y = 185.0
STRIP_W = 12.5
BOARDS = {
    "T1": (242.0, 8.0, 90.0, 70.0, "POTENCIA"),
    "T2": (140.0, 8.0, 90.0, 70.0, "CORRIENTE + VBIAS"),
    "T3": (8.0, 100.0, 90.0, 70.0, "TENSION MBT"),
    "T4": (8.0, 8.0, 120.0, 80.0, "ESP32 + LCD"),
    "T5": (110.0, 100.0, 90.0, 70.0, "INTERFAZ + ALERTAS"),
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


def esp32s_v11_usbc(doc,x,y,prefix="T4"):
    """ESP32S/ESP-WROOM-32 USB-C, 38 pines; filas separadas 25,4 mm."""
    z=Z_BOARD+1.6
    add(doc,f"{prefix}_ESP32S_V1p1_PCB_58x28",box(28,58,1.6,x,y,z),"esp")
    add(doc,f"{prefix}_ESP32S_Headers_38P",Part.makeCompound([
        box(2.54,48.26,8.5,x+.03,y+4.87,z-5.0),
        box(2.54,48.26,8.5,x+25.43,y+4.87,z-5.0)]),"chip")
    add(doc,f"{prefix}_ESP32S_RF_Shield",box(18,25,3.2,x+5,y+29,z+1.6),"connector")
    add(doc,f"{prefix}_ESP32S_USB_C",box(9,7.5,3.2,x+9.5,y-.8,z+1.6),"connector")
    add(doc,f"{prefix}_ESP32S_EN_BOOT",Part.makeCompound([
        box(4,3.5,2.2,x+3.5,y+5,z+1.6),box(4,3.5,2.2,x+20.5,y+5,z+1.6)]),"chip")


def enclosure(doc):
    bottom=box(W,D,FLOOR)
    walls=[box(W,WALL,H-FLOOR,0,0,FLOOR),box(W,WALL,H-FLOOR,0,D-WALL,FLOOR),
           box(WALL,D-2*WALL,H-FLOOR,0,WALL,FLOOR),box(WALL,D-2*WALL,H-FLOOR,W-WALL,WALL,FLOOR)]
    barrier=box(W-2*WALL,3,H-8,WALL,NETWORK_Y,FLOOR)
    add(doc,"Gabinete_E5",bottom.fuse(walls+[barrier]),"body","body")
    lid=box(W,D,LID,0,0,H)
    lid=lid.cut(box(47,23,LID+2,24,44,H-1))
    lid=lid.cut(box(70,6,LID+2,248,116,H-1))
    for x in (110,140): lid=lid.cut(Part.makeCylinder(6.2,LID+2,v((x,52,H-1))))
    for x in (170,200): lid=lid.cut(Part.makeCylinder(3.8,LID+2,v((x,52,H-1))))
    # Rejilla acústica del piezo comprado, cuerpo circular de 44 x 14 mm.
    for ix in range(-2,3):
        for iy in range(-2,3):
            if ix*ix+iy*iy <= 5:
                lid=lid.cut(Part.makeCylinder(1.4,LID+2,v((225+ix*6,52+iy*6,H-1))))
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
            esp32s_v11_usbc(doc,x+9,y+13)
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
    signal_paths=[[(128,44,16),(134,44,16),(134,58,16),(140,58,16)],
                  [(58,88,16),(58,94,16),(43,94,16),(43,100,16)],
                  [(128,70,16),(205,92,16),(205,135,16),(200,135,16)],
                  [(230,45,17),(236,45,17),(236,92,17),(70,92,17),(70,100,17)]]
    add(doc,"Arneses_Senal_E5",Part.makeCompound([tube(p,.75) for p in signal_paths]),"wire")
    add(doc,"Bus_5V_GND_Estrella",tube([(320,72,18),(320,92,18),(205,92,18),(205,165,18)],1.2),"power")

    # Barra real de 4 píxeles, claramente visible y con soporte adaptable 10-12,5 mm.
    sx,sy,sz=248.0,116.0,41.0
    add(doc,"Soporte_Barra_NeoPixel_13p2mm",box(71,STRIP_W+.7,2.2,sx-2,sy-.35,sz-1.5),"support")
    add(doc,"Barra_NeoPixel_WS2812B_4px",box(66.7,STRIP_W,1.2,sx,sy,sz),"strip")
    add(doc,"NeoPixels_4",Part.makeCompound([box(5,5,1.8,sx+6.3+i*16.67,sy+(STRIP_W-5)/2,sz+1.2) for i in range(4)]),"led")

    # Elementos de panel/tapa: LCD, encoder, botones y piezo.
    add(doc,"LCD_1p9_ST7789_51p2x27p3",box(51.2,27.3,3.0,21.9,41.8,H-5),"screen","lid")
    add(doc,"Encoders_EC11",Part.makeCompound([Part.makeCylinder(6,13,v((x,52,H-10))) for x in (170,200)]),"connector","lid")
    add(doc,"SW12BP_12mm",Part.makeCompound([Part.makeCylinder(6,12,v((x,52,H-10))) for x in (110,140)]),"connector","lid")
    add(doc,"Piezo_pasivo_44x14",Part.makeCylinder(22,14,v((225,52,H-17))),"chip","lid")

    # Zona de red: ZMPT, fusible y bornera, siempre detrás del tabique.
    add(doc,"ZMPT101B_Z1_51p7x21p6",box(51.7,21.6,17,142,200,FLOOR+4),"network","network")
    add(doc,"Fusible_T500mA_Z1",box(30,10,10,52,203,FLOOR+4),"chip","network")
    add(doc,"Bornera_LN_Z1",box(20,12,11,258,201,FLOOR+4),"connector","network")
    add(doc,"Cableado_Red_Z1",Part.makeCompound([
        tube([(278,207,12),(220,207,12),(194,211,12)],1.2),
        tube([(258,211,12),(95,211,12),(82,208,12),(52,208,12)],1.2)]),"power","network")


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
            "dimension_basis":"medidas-componentes.json",
            "note":"Placas compradas completas; componentes por envolvente. Ver estados fuente/conservadora/por_medir."}
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
