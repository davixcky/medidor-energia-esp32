#!/usr/bin/env python3
"""Modelo E.7 compacto y montable, basado en componentes comprados/reales."""
from pathlib import Path
import json
import sys

import FreeCAD as App
import Import
import MeshPart
import Part

HERE = Path(__file__).resolve().parent
STL = HERE / "stl"; STL.mkdir(parents=True, exist_ok=True)
W, D, H, LID = 280.0, 180.0, 67.0, 3.0
WALL, FLOOR, Z_BOARD = 2.5, 3.0, 9.0
NETWORK_Y = 132.0
STRIP_W = 12.0
BOARDS = {
    "T1": (222.0, 8.0, 50.0, 40.0, "POTENCIA"),
    "T2": (92.0, 8.0, 70.0, 55.0, "CORRIENTE + VBIAS"),
    "T3": (168.0, 70.0, 55.0, 45.0, "TENSION MBT"),
    "T4": (6.0, 8.0, 80.0, 65.0, "ESP32 + LCD"),
    "T5": (92.0, 70.0, 65.0, 50.0, "INTERFAZ + ALERTAS"),
}
COLORS = {
    "body": (.11,.14,.17), "lid": (.32,.35,.39), "guard": (.82,.12,.08),
    "perf": (.45,.25,.08), "pad": (.86,.62,.15), "chip": (.035,.04,.045),
    "connector": (.85,.88,.90), "esp": (.05,.25,.20), "wire": (.08,.45,.92),
    "power": (.88,.08,.05), "ground": (.04,.04,.04), "support": (.16,.18,.20),
    "strip": (.96,.96,.96), "led": (.10,.78,.92), "screen": (.02,.17,.28),
    "network": (.22,.38,.18), "knob": (.06,.07,.08), "diffuser": (.82,.88,.90),
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
    for ix in range(int((w-8)//2.54)+1):
        for iy in range(int((d-8)//2.54)+1):
            px,py=x+4+ix*2.54,y+4+iy*2.54
            r=Part.makeCylinder(1.15,.12,v((px,py,Z_BOARD+1.6))).cut(Part.makeCylinder(.45,.2,v((px,py,Z_BOARD+1.55))))
            rings.append(r)
    return Part.makeCompound(rings)


def dip(x,y,length=20):
    return box(length,10,4,x,y,Z_BOARD+2).cut(Part.makeCylinder(1.4,2,v((x+3,y+5,Z_BOARD+5))))


def conn(x,y,pins,vertical=False):
    w,d=(6,pins*2.54+2) if vertical else (pins*2.54+2,6)
    return box(w,d,7,x,y,Z_BOARD+1.6)


def terminal(x,y,pins):
    """Bornera verde de 5,08 mm con bocas de tornillo visibles."""
    body=box(pins*5.08+2,8.2,10,x,y,Z_BOARD+1.6)
    ports=[Part.makeCylinder(1.35,2.2,v((x+3.54+i*5.08,y+4.1,Z_BOARD+10.0))) for i in range(pins)]
    return Part.makeCompound([body]+ports)


def trimmer(x,y):
    return Part.makeCompound([box(9.5,9.5,6,x,y,Z_BOARD+3.2),Part.makeCylinder(2.8,1.2,v((x+4.75,y+4.75,Z_BOARD+9.2)))])


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
    add(doc,"Gabinete_E7",bottom.fuse(walls+[barrier]),"body","body")
    lid=box(W,D,LID,0,0,H)
    lid=lid.cut(box(47,23,LID+2,14,16,H-1))
    lid=lid.cut(box(204,14,LID+2,38,94,H-1))
    for x in (105,130): lid=lid.cut(Part.makeCylinder(6.2,LID+2,v((x,28,H-1))))
    lid=lid.cut(Part.makeCylinder(3.8,LID+2,v((162,28,H-1))))
    lid=lid.cut(Part.makeCylinder(2.7,LID+2,v((190,28,H-1))))
    # Rejilla acústica del piezo comprado, cuerpo circular de 44 x 14 mm.
    for ix in range(-2,3):
        for iy in range(-2,3):
            if ix*ix+iy*iy <= 5:
                lid=lid.cut(Part.makeCylinder(1.4,LID+2,v((232+ix*6,28+iy*6,H-1))))
    add(doc,"Tapa_E7",lid,"lid","lid")
    # Guarda independiente y desmontable de la zona de red.
    guard=box(W-10,D-NETWORK_Y-7,2,5,NETWORK_Y+4,42)
    guard=guard.fuse(box(W-10,2,39,5,NETWORK_Y+4,FLOOR))
    add(doc,"Guarda_120V_E7",guard,"guard","guard")


def populate(doc):
    mounting=[]
    for ref,(x,y,w,d,label) in BOARDS.items():
        board,holes=perfboard(x,y,w,d); mounting += holes
        add(doc,f"{ref}_Perforada_{int(w)}x{int(d)}",board,"perf")
        add(doc,f"{ref}_Donas",pads(x,y,w,d),"pad")
        if ref=="T1":
            add(doc,"T1_J1_Entrada_5V_bornera",terminal(x+2,y+2,2),"network")
            add(doc,"T1_PTC_2A_y_1N5822",box(22,5,5,x+16,y+3,Z_BOARD+1.6),"connector")
            add(doc,"T1_C1_470u_35V",Part.makeCylinder(5,12,v((x+43,y+7,Z_BOARD+1.6))),"chip")
            add(doc,"T1_MT3608_36x17",box(36,17,2,x+3,y+18,Z_BOARD+1.6),"esp")
            add(doc,"T1_MT3608_potenciometro_ajuste",trimmer(x+23,y+21),"connector")
            add(doc,"T1_C17_680u_16V",Part.makeCylinder(5,12,v((x+42,y+27,Z_BOARD+1.6))),"chip")
            add(doc,"T1_C_PWR3_JST2",conn(x+2,y+d-7,2),"connector")
            add(doc,"T1_C_PWR4_JST2",conn(x+12,y+d-7,2),"connector")
            add(doc,"T1_C_PWR5_JST3",conn(x+22,y+d-7,3),"connector")
        elif ref=="T2":
            add(doc,"T2_Jacks_SCT_3p5mm",Part.makeCompound([box(11,12,8,x+4+i*17,y+4,Z_BOARD+1.6) for i in range(2)]),"knob")
            add(doc,"T2_Burdens_precision_1pct",Part.makeCompound([box(9,3,3,x+7+i*17,y+20,Z_BOARD+2) for i in range(2)]),"connector")
            add(doc,"T2_Pasivos_CH1_CH2",Part.makeCompound([box(8,3,3,x+7+i*10,y+30,Z_BOARD+2) for i in range(6)]),"connector")
            add(doc,"T2_C7_VBIAS",Part.makeCylinder(4,9,v((x+25,y+42,Z_BOARD+1.6))),"chip")
            add(doc,"T2_C_ADC_I_JST4",conn(x+w-17,y+d-9,4),"connector")
        elif ref=="T3":
            add(doc,"T3_Filtro_V_precision",Part.makeCompound([box(9,3,3,x+5+i*11,y+17,Z_BOARD+2) for i in range(4)]),"connector")
            add(doc,"T3_J5_ZMPT_MBT_bornera3",terminal(x+3,y+3,3),"network")
            add(doc,"T3_C_ADC_V_JST3",conn(x+w-16,y+d-9,3),"connector")
            add(doc,"T3_C_PWR3_JST2",conn(x+3,y+d-9,2),"connector")
        elif ref=="T4":
            esp32s_v11_usbc(doc,x+6,y+3)
            add(doc,"T4_C_LCD_JST8",conn(x+40,y+5,8),"connector")
            add(doc,"T4_C_ADC_I_JST4",conn(x+w-9,y+5,4,True),"connector")
            add(doc,"T4_C_ADC_V_JST3",conn(x+w-9,y+20,3,True),"connector")
            add(doc,"T4_C_UI_D_JST3",conn(x+w-9,y+34,3,True),"connector")
            add(doc,"T4_C_UI_E_JST5",conn(x+w-9,y+46,5,True),"connector")
            add(doc,"T4_LED_estado_D8",Part.makeCylinder(2.5,8,v((x+51,y+44,Z_BOARD+1.6))),"led")
        else:
            add(doc,"T5_U3_74HCT245N_DIP20",dip(x+5,y+18,26),"chip")
            add(doc,"T5_Encoder_Filtros",Part.makeCompound([box(7,3,3,x+5+i*10,y+6,Z_BOARD+2) for i in range(5)]),"connector")
            add(doc,"T5_Q1_Piezo_Driver",box(18,10,7,x+39,y+31,Z_BOARD+1.6),"chip")
            add(doc,"T5_C_UI_E_JST5",conn(x+w-9,y+4,5,True),"connector")
            add(doc,"T5_C_UI_D_JST3",conn(x+w-9,y+21,3,True),"connector")
            add(doc,"T5_C_PIX_JST3",conn(x+5,y+d-8,3),"connector")
    add(doc,"Postes_M3",Part.makeCompound([Part.makeCylinder(3.2,Z_BOARD-FLOOR,v((x,y,FLOOR))) for x,y in mounting]),"support")

    # Arnés en estrella y señales con retorno, por corredores libres.
    signal_paths=[[(84,31,16),(89,31,16),(89,42,16),(92,42,16)],
                  [(84,55,17),(162,55,17),(162,92,17),(168,92,17)],
                  [(86,64,18),(88,64,18),(88,94,18),(92,94,18)]]
    add(doc,"Arneses_Senal_E7",Part.makeCompound([tube(p,.75) for p in signal_paths]),"wire")
    add(doc,"Bus_5V_GND_Estrella",tube([(225,44,18),(218,62,18),(86,62,18)],1.2),"power")

    # Barra real de 4 píxeles, claramente visible y con soporte adaptable 10-12,5 mm.
    sx,sy,sz=40.0,95.0,H-4.2
    add(doc,"Soporte_FCOB_12p6mm",box(202,STRIP_W+.6,1.8,sx-1,sy-.3,sz-1.2),"support","lid")
    add(doc,"BTF_FCOB_WS2811_12V_4segmentos_200mm",box(200,STRIP_W,1.2,sx,sy,sz),"strip","lid")
    add(doc,"Segmentos_WS2811_4",Part.makeCompound([box(48,8,1.1,sx+1+i*50,sy+2,sz+1.2) for i in range(4)]),"led","lid")
    add(doc,"Difusor_FCOB_204x14",box(204,14,2.0,sx-2,sy-1,H+1.2),"diffuser","lid")

    # Elementos de panel/tapa: LCD, encoder, botones y piezo.
    add(doc,"LCD_1p9_ST7789_51p2x27p3",box(51.2,27.3,3.0,11.9,13.8,H-5),"screen","lid")
    add(doc,"Encoder_EC11_cuerpo",Part.makeCylinder(6,13,v((162,28,H-10))),"connector","lid")
    add(doc,"Perilla_EC11_eje6mm",Part.makeCylinder(9,10,v((162,28,H+1))),"knob","lid")
    add(doc,"SW12BP_12mm",Part.makeCompound([Part.makeCylinder(6,12,v((x,28,H-10))) for x in (105,130)]),"connector","lid")
    add(doc,"LED_estado_panel_5mm",Part.makeCylinder(2.5,7,v((190,28,H-4))),"led","lid")
    add(doc,"Piezo_pasivo_empotrado_44x14",Part.makeCylinder(22,14,v((232,28,H-17))),"chip","lid")

    # Zona de red: ZMPT, fusible y bornera, siempre detrás del tabique.
    add(doc,"ZMPT101B_Z1_51p7x21p6",box(51.7,21.6,17,118,145,FLOOR+4),"network","network")
    add(doc,"ZMPT101B_potenciometro_calibracion",Part.makeCompound([box(10,10,7,154,150,FLOOR+21),Part.makeCylinder(3,1.5,v((159,155,FLOOR+28)))]),"connector","network")
    add(doc,"Fusible_T500mA_Z1",box(30,10,10,48,148,FLOOR+4),"chip","network")
    add(doc,"Bornera_LN_Z1",terminal(225,146,2),"network","network")
    add(doc,"Cableado_Red_Z1",Part.makeCompound([
        tube([(247,151,12),(190,151,12),(170,155,12)],1.2),
        tube([(225,156,12),(95,156,12),(78,153,12),(48,153,12)],1.2)]),"power","network")


def validate():
    issues=[]; rects=[]
    for ref,(x,y,w,d,_) in BOARDS.items():
        if x<WALL+2 or y<WALL+2 or x+w>W-WALL-1 or y+d>NETWORK_Y-5: issues.append(f"{ref} fuera de MBT")
        for other,ox,oy,ow,od in rects:
            if x<ox+ow and x+w>ox and y<oy+od and y+d>oy: issues.append(f"solape {ref}/{other}")
        rects.append((ref,x,y,w,d))
    report={"revision":"E.7","enclosure_mm":[W,D,H+LID],"network_partition_y_mm":NETWORK_Y,
            "boards":{k:list(v[:4]) for k,v in BOARDS.items()},"fcob_strip_mm":[200.0,STRIP_W],
            "fcob_support_clearance_mm":12.6,"issues":issues,"valid":not issues,
            "dimension_basis":"medidas-componentes.json",
            "note":"Placas compradas recortadas a T1-T5; envolventes reales o conservadoras identificadas en medidas-componentes.json."}
    (HERE/"validacion-3d.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    if issues: raise RuntimeError(issues)


def main():
    validate(); doc=App.newDocument("Medidor_E7_Perforadas")
    enclosure(doc); populate(doc); doc.recompute(); doc.saveAs(str(HERE/"medidor-E7-perforadas.FCStd"))
    objects=[o for o in doc.Objects if hasattr(o,"Shape") and not o.Shape.isNull()]
    Import.export(objects,str(HERE/"medidor-E7-perforadas.step"))
    for name in ("Gabinete_E7","Tapa_E7","Guarda_120V_E7","Soporte_FCOB_12p6mm"):
        obj=doc.getObject(name); mesh=MeshPart.meshFromShape(Shape=obj.Shape,LinearDeflection=.12,AngularDeflection=.35)
        mesh.write(str(STL/f"{name.lower()}.stl"))
    print(f"Medidor E.7 CAD: {len(objects)} objetos; {W} x {D} x {H+LID} mm")


if __name__=="__main__": main()
