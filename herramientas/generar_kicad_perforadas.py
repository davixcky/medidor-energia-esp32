#!/usr/bin/env python3
"""Genera esquemáticos KiCad nativos para T1–T5 del medidor modular.

Estos archivos, no las láminas ilustrativas antiguas, son la fuente eléctrica.
La tira real es BTF FCOB WS2811, 12 V, 720 LED/m, 20 segmentos/m.
"""
from pathlib import Path
import csv
import json
import os
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "hardware" / "perforadas-modulares" / "kicad"
sys.path.insert(0, str(HERE))
import generar_esquematico as g

# Construction sheets use KiCad's 1.27 mm connection grid.  Keeping this at
# the generator boundary lets the visual layout use readable spacing without
# ever producing off-grid symbol pins or wire endpoints.
def grid(v):
    return round(round(float(v) / 1.27) * 1.27, 4)

g.r = grid

H_R = g.H_R
H_C = g.H_C
H_D = g.H_D
H_CP5 = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
H_CP10 = "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"
H_CONN2 = "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
H_CONN3 = "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical"
H_CONN4 = "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"
H_CONN5 = "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical"
H_CONN8 = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
H_TERM2 = "TerminalBlock_CUI:TerminalBlock_CUI_TB007-508-02_1x02_P5.08mm_Horizontal"
H_TERM3 = "TerminalBlock_RND:TerminalBlock_RND_205-00288_1x03_P5.08mm_Horizontal"
H_DIP20 = "Package_DIP:DIP-20_W7.62mm"

PINOUTS = {
    "C_BUCK_IN": ["+12V_PROT", "GND"],
    "C_BUCK_OUT": ["+5V_PROT", "GND"],
    "C_PWR3": ["+5V_PROT", "GND"],
    "C_PWR4": ["+5V_PROT", "GND"],
    "C_PWR5": ["+5V_PROT", "+12V_PROT", "GND"],
    "C_ADC_I": ["+3V3", "GND", "CH1_ADC", "CH2_ADC"],
    "C_ADC_V": ["+3V3", "GND", "V_ADC"],
    "C_UI_D": ["GND", "LED_DATA", "BUZZ"],
    "C_PIX": ["+12V_PROT", "DIN_5V", "GND"],
    "C_LILY": ["+5V_PROT", "GND"],
    "C_LED": ["LED_A", "GND"],
    "C_BZ": ["+5V_PROT", "BZ_SW"],
}


def reset(card):
    g._ns = uuid.uuid5(uuid.NAMESPACE_URL, f"medidor-energia-perforada-{card}-e7")
    g._cont.clear()
    g.RAIZ = g.uid("raiz")
    g.PROYECTO = f"medidor-perforada-{card.lower()}"
    # No heredar las asignaciones por referencia del esquemático monolítico.
    g.HUELLAS = {}
    # These sheets describe complete electrical assemblies, including R1/R2
    # mounted directly on the panel jacks.  Keep them in exported netlists so
    # connectivity checks cannot silently omit the two SCT burden resistors.
    g.FUERA_DE_PLACA = {"U2", "J4", "F1"}


def own_symbol(name, ref, value, pins, width=15.24, height=12.7, description=""):
    """Símbolo rectangular simple; pins=(tipo,x,y,ang,nombre,numero)."""
    p = [g.pin_def(*x) for x in pins]
    graphics = [g.rect(-width/2, height/2, width/2, -height/2)]
    return g.simbolo_propio(f"Medidor:{name}", ref, value, graphics, p,
                            height/2+2.54, -height/2-2.54, description)


def connector(s, ref, n, x, y, value, mirror=False, footprint=None):
    fp = footprint or {2:H_CONN2, 3:H_CONN3, 4:H_CONN4, 5:H_CONN5, 8:H_CONN8}[n]
    # Los nombres eléctricos se dibujan junto a cada pin. Ocultar el valor largo
    # evita que KiCad lo superponga al conector y deja la hoja legible impresa.
    return s.colocar(f"Connector_Generic:Conn_01x{n:02d}", ref, value, x, y,
                     espejo=mirror, huella=fp, ocultar_valor=True,
                     ref_at=(x, y - n*1.27 - 3.0))


def label_connector(s, p, names, x_label, side):
    for i, name in enumerate(names, 1):
        q=p[str(i)]; s.cable(q,(x_label,q[1])); s.etiqueta(name,x_label,q[1],side)


def add_note(s, card, title, size):
    s.texto(f"{card} · {title}", 20.32, 25.4, 2.2, True)
    s.texto(f"Perfboard cut size: {size[0]} × {size[1]} mm · 2.54 mm pitch", 20.32, 30.48, 1.1)
    s.texto(f"Component values and purchasing status: bom-por-tarjeta/BOM-{card}.csv", 20.32, 34.0, 1.15, True)


def power_input(s, name, x, y):
    """Declara una alimentación que entra por arnés, lejos del conector impreso."""
    if name in ("+5V", "+3V3", "GND"):
        s.power(name, x, y, 180)
    else:
        s.etiqueta(name, x, y, "der")
    s.bandera(x, y)


def t1():
    reset("T1"); s=g.Esquematico(); add_note(s,"T1","12 V INPUT + LM2596 BUCK + STAR DISTRIBUTION",(50,40))
    buck=own_symbol("LM2596_Module","U","LM2596 adjusted to 5.0 V",[
        ("power_in",-10.16,2.54,0,"VIN+","1"),("power_in",-10.16,-2.54,0,"VIN-","2"),
        ("power_out",10.16,2.54,180,"VOUT+","3"),("power_out",10.16,-2.54,180,"VOUT-","4")],20.32,10.16,
        "Off-board LM2596 buck; adjust to 5.0 V before connecting any load")
    s.usar("Medidor:LM2596_Module",buck)
    j=connector(s,"J1",2,30.0,55.0,"12 V DC FROM CON-156A · CENTER POSITIVE",True,H_TERM2)
    f=s.colocar("Device:Polyfuse","F2","PTC hold 2.0 A · rated >=16 V",70.0,53.73,rot=90,huella="Fuse:Fuse_Littelfuse-LVR200")
    d=s.colocar("Device:D_Schottky","D1","1N5822 3 A",105.0,53.73,rot=180,huella="Diode_THT:D_DO-201AD_P15.24mm_Horizontal")
    s.cable(j["1"],f["1"]); s.cable(f["2"],d["2"]); s.cable(d["1"],(125.0,53.73)); s.etiqueta("+12V_PROT",125.0,53.73)
    s.bandera(125.0,53.73)
    s.cable(j["2"],(45.0,j["2"][1]),(45.0,70.0)); s.power("GND",45.0,70.0)
    c1=s.colocar("Device:C_Polarized","C1","470u 35V",150.0,60.08,huella=g.H_CP)
    c2=s.colocar("Device:C","C2","100n",180.0,60.08,huella=H_C)
    for c in (c1,c2): s.cable(c["1"],(c["1"][0],53.73)); s.cable((125.0,53.73),(c["1"][0],53.73)); s.power("GND",c["2"][0],c["2"][1])

    bi=connector(s,"C_BUCK_IN",2,30.0,95.0,"TO LM2596 IN: +12V_PROT / GND",True)
    label_connector(s,bi,PINOUTS["C_BUCK_IN"],52.0,"der")
    u=s.colocar("Medidor:LM2596_Module","U4","LM2596 OFF-BOARD 12→5 V",120.0,95.0,huella="")
    s.cable(u["1"],(90.0,u["1"][1])); s.etiqueta("+12V_PROT",90.0,u["1"][1],"izq")
    s.cable(u["2"],(90.0,u["2"][1])); s.power("GND",90.0,u["2"][1],270)
    s.cable(u["3"],(150.0,u["3"][1])); s.etiqueta("+5V_PROT",150.0,u["3"][1])
    s.cable(u["4"],(150.0,u["4"][1])); s.power("GND",150.0,u["4"][1],90)
    bo=connector(s,"C_BUCK_OUT",2,210.0,95.0,"FROM LM2596 OUT: +5V_PROT / GND")
    label_connector(s,bo,PINOUTS["C_BUCK_OUT"],185.0,"izq")
    c17=s.colocar("Device:C_Polarized","C17","680u 16V",245.0,95.0,huella=H_CP10)
    s.cable(c17["1"],(245.0,86.0)); s.etiqueta("+5V_PROT",245.0,86.0); s.power("GND",245.0,c17["2"][1])

    for ref,names,x,y,xlab in (("C_PWR3",PINOUTS["C_PWR3"],230.0,125.0,200.0),
                               ("C_PWR4",PINOUTS["C_PWR4"],230.0,150.0,200.0),
                               ("C_PWR5",PINOUTS["C_PWR5"],150.0,175.0,115.0)):
        p=connector(s,ref,len(names),x,y," / ".join(names)); label_connector(s,p,names,xlab,"izq")
    s.texto("MANDATORY: disconnect all loads and adjust U4 to 5.0 V before plugging C_BUCK_OUT.\n"
            "The FCOB branch uses +12V_PROT directly; logic and analog boards use +5V_PROT.\n"
            "C_BUCK_IN and C_BUCK_OUT are separate keyed 2-way harnesses; never interchange them.",20.32,180.34,1.15)
    return s


def current_channel(s, n, y, burden):
    j=connector(s,f"J{n+1}",2,30.0,y,f"SCT-013-000 CH{n} · T/S",True)
    rb=s.colocar("Device:R",f"R{n}",f"{burden}Ω 1% burden",70.0,y,rot=90,huella=H_R)
    s.cable(j["1"],rb["1"]); s.cable(rb["2"],(88.0,rb["2"][1])); s.etiqueta("VBIAS",88.0,rb["2"][1])
    rs=s.colocar("Device:R",f"R{n+4}","3.3k 1%",115.0,j["1"][1],rot=90,huella=H_R)
    # Branch R5/R6 from the SCT tip side of the burden.  Route above R1/R2 so
    # the wire cannot pass through the burden symbol and accidentally join its
    # VBIAS side when KiCad constructs the electrical graph.
    lane_y = j["1"][1] - 10.16
    s.cable(j["1"],(50.8,j["1"][1]),(50.8,lane_y),(rs["1"][0],lane_y),rs["1"])
    out=f"CH{n}_ADC"; s.cable(rs["2"],(140.0,rs["2"][1])); s.etiqueta(out,140.0,rs["2"][1])
    c=s.colocar("Device:C",f"C{n+4}","47n 5%",155.0,y+8.0,huella=H_C)
    s.cable((140.0,rs["2"][1]),c["1"]); s.cable(c["2"],(155.0,y+16.0)); s.etiqueta("VBIAS",155.0,y+16.0)
    dl=s.colocar("Device:D_Schottky",f"D{2*n+1}","BAT85",185.0,y+10.0,rot=270,huella=H_D)
    dh=s.colocar("Device:D_Schottky",f"D{2*n}","BAT85",185.0,y-10.0,rot=270,huella=H_D)
    # The midpoint of each rail-clamp pair is the ADC node.  Starting this
    # wire at R5/R6 is intentional: the previous generator began at x=185 mm,
    # leaving the diode pair electrically floating despite looking nearby.
    s.cable(rs["2"],(185.0,rs["2"][1]),dl["1"],dh["2"]); s.power("GND",185.0,dl["2"][1]); s.power("+3V3",185.0,dh["1"][1],180)
    s.cable(j["2"],(48.0,j["2"][1])); s.etiqueta("VBIAS",48.0,j["2"][1])


def t2():
    reset("T2"); s=g.Esquematico(); add_note(s,"T2","TWO SCT CHANNELS + VBIAS",(70,55))
    current_channel(s,1,65.0,22); current_channel(s,2,125.0,47)
    r3=s.colocar("Device:R","R3","15k 1%",220.0,62.0,huella=H_R); r4=s.colocar("Device:R","R4","10k 1%",220.0,82.0,huella=H_R)
    s.power("+3V3",220.0,r3["1"][1]); s.cable(r3["2"],(220.0,72.0),r4["1"]); s.etiqueta("VBIAS",220.0,72.0); s.power("GND",220.0,r4["2"][1])
    c7=s.colocar("Device:C_Polarized","C7","10u 16V",245.0,77.0,huella=H_CP5); c8=s.colocar("Device:C","C8","100n",265.0,77.0,huella=H_C)
    for c in (c7,c8): s.cable(c["1"],(c["1"][0],72.0)); s.cable((220.0,72.0),(c["1"][0],72.0)); s.power("GND",c["2"][0],c["2"][1])
    p=connector(s,"C_ADC_I",4,250.0,130.0,"+3V3 / GND / CH1 / CH2"); label_connector(s,p,PINOUTS["C_ADC_I"],220.0,"izq")
    power_input(s,"+3V3",240.0,45.0); power_input(s,"GND",265.0,45.0)
    s.texto("R1 and R2 mount directly across the panel-jack terminals: never leave an energized SCT secondary open.\nC5/C6 return to VBIAS, not GND.",20.32,165.0,1.3)
    return s


def t3():
    reset("T3"); s=g.Esquematico(); add_note(s,"T3","VOLTAGE CONDITIONING · ELV ONLY",(55,45))
    p=connector(s,"J5",3,30.0,70.0,"ZMPT ELV: +5V_PROT / OUT / GND",True,H_TERM3); label_connector(s,p,["+5V_PROT","ZMPT_OUT","GND"],55.0,"der")
    r7=s.colocar("Device:R","R7","11k 1%",100.0,p["2"][1],rot=90,huella=H_R); s.cable((55.0,p["2"][1]),r7["1"])
    x=130.0; s.cable(r7["2"],(x,r7["2"][1])); s.etiqueta("V_ADC",x,r7["2"][1])
    r8=s.colocar("Device:R","R8","13k 1%",145.0,90.0,huella=H_R); c9=s.colocar("Device:C","C9","27n 5%",170.0,90.0,huella=H_C)
    for q in (r8,c9):
        s.cable(q["1"],(q["1"][0],r7["2"][1]),(x,r7["2"][1]))
        s.cable(q["2"],(q["2"][0],q["2"][1]+2.54)); s.power("GND",q["2"][0],q["2"][1]+2.54)
    d6=s.colocar("Device:D_Schottky","D6","BAT85",200.0,60.0,rot=270,huella=H_D); d7=s.colocar("Device:D_Schottky","D7","BAT85",200.0,80.0,rot=270,huella=H_D)
    # Join the D6/D7 midpoint to V_ADC.  As on T2, starting at x=200 mm left
    # the clamp pair floating in the native KiCad netlist.
    s.cable(r7["2"],(200.0,r7["2"][1]),d6["2"],d7["1"]); s.power("+3V3",200.0,d6["1"][1],180); s.power("GND",200.0,d7["2"][1])
    a=connector(s,"C_ADC_V",3,255.0,70.0,"+3V3 / GND / V_ADC"); label_connector(s,a,PINOUTS["C_ADC_V"],225.0,"izq")
    w=connector(s,"C_PWR3",2,255.0,120.0,"+5V / GND"); label_connector(s,w,PINOUTS["C_PWR3"],225.0,"izq")
    power_input(s,"+3V3",235.0,45.0); power_input(s,"GND",260.0,45.0)
    s.texto("J4, F1 and the ZMPT101B primary are NOT on this board.\nThe full module remains inside Z1; T3 receives only +5 V, OUT and GND.",20.32,155.0,1.3)
    return s


def t4():
    reset("T4"); s=g.Esquematico(); s.usar("Medidor:ESP32-DevKitC-38",g.sim_esp32()); add_note(s,"T4","MAIN ESP32 · ADC · ESP-NOW · LILYGO POWER",(80,65))
    u=s.colocar("Medidor:ESP32-DevKitC-38","U1","ESP32S V1.1 USB-C 38P",135.0,105.0,huella="Medidor:ESP32-DevKitC-38_Zocalo",
                nc=[str(i) for i in range(1,39) if i not in (1,3,4,6,9,12,14,15,19,20,26)])
    mapping={"1":"+3V3","3":"CH1_ADC","4":"CH2_ADC","6":"V_ADC","9":"LED_EST",
             "12":"BUZZ","14":"GND","15":"LED_DATA","19":"+5V_PROT","20":"GND","26":"GND"}
    for pin,name in mapping.items():
        q=u[pin]; left=q[0]<135.0; xx=q[0]+(-18.0 if left else 18.0); s.cable(q,(xx,q[1]))
        if name=="GND": s.power("GND",xx,q[1],270 if left else 90)
        elif name=="+3V3": s.power(name,xx,q[1],90 if left else 270)
        else: s.etiqueta(name,xx,q[1],"izq" if left else "der")
    specs=[("C_PWR4",2,30.0,60.0),("C_ADC_I",4,30.0,100.0),("C_ADC_V",3,30.0,140.0),
           ("C_UI_D",3,250.0,60.0),("C_LILY",2,250.0,105.0),("C_LED",2,250.0,145.0)]
    for ref,n,x,y in specs:
        p=connector(s,ref,n,x,y," / ".join(PINOUTS[ref]),mirror=x<90); label_connector(s,p,PINOUTS[ref],x+(25.0 if x<90 else -25.0),"der" if x<90 else "izq")
    power_input(s,"+5V_PROT",35.0,43.0); power_input(s,"GND",60.0,43.0)
    r11=s.colocar("Device:R","R11","330Ω 1%",135.0,165.0,rot=90,huella=H_R)
    s.etiqueta("LED_EST",110.0,r11["1"][1],"izq"); s.cable((110.0,r11["1"][1]),r11["1"])
    s.cable(r11["2"],(160.0,r11["2"][1])); s.etiqueta("LED_A",160.0,r11["2"][1])
    s.texto("The LilyGO is an independent ESP-NOW terminal: C_LILY carries only +5V_PROT and GND.\n"
            "There is no wired LCD bus, UART, encoder or push-button input in E.9.\n"
            "Disconnect C_LILY before powering or programming the LilyGO through USB-C.",20.32,175.26,1.15)
    return s


def t5():
    reset("T5"); s=g.Esquematico(); add_note(s,"T5","FCOB LEVEL SHIFTER + PIEZO DRIVER",(65,50))
    u=s.colocar("74xx:74LS245","U3","74HCT245N",110.0,80.0,huella=H_DIP20,nc=[str(i) for i in range(11,18)])
    q=u["20"]; s.cable(q,(q[0],q[1]-12.0)); s.etiqueta("+5V_PROT",q[0],q[1]-12.0)
    q=u["1"]; s.cable(q,(q[0]-18.0,q[1])); s.etiqueta("+5V_PROT",q[0]-18.0,q[1],"izq")
    q=u["19"]; s.cable(q,(q[0]-18.0,q[1])); s.power("GND",q[0]-18.0,q[1],90)
    q=u["10"]; s.cable(q,(q[0],q[1]+5.08)); s.power("GND",q[0],q[1]+5.08)
    bus_x=72.0
    for pin in range(3,10):
        q=u[str(pin)]; s.cable(q,(bus_x,q[1]))
    s.cable((bus_x,u["3"][1]),(bus_x,u["9"][1]))
    ru=s.colocar("Device:R","R23","10k 1%",bus_x,100.0,huella=H_R)
    s.cable((bus_x,u["9"][1]),ru["1"]); s.power("GND",bus_x,ru["2"][1])
    s.cable(u["2"],(55.0,u["2"][1])); s.etiqueta("LED_DATA",55.0,u["2"][1],"izq")
    r16=s.colocar("Device:R","R16","330Ω 1%",160.0,u["18"][1],rot=90,huella=H_R); s.cable(u["18"],r16["1"]); s.cable(r16["2"],(190.0,r16["2"][1])); s.etiqueta("DIN_5V",190.0,r16["2"][1])
    c14=s.colocar("Device:C","C14","100n 50V",170.0,50.0,huella=H_C); s.etiqueta("+5V_PROT",170.0,c14["1"][1]); s.power("GND",170.0,c14["2"][1])
    r17=s.colocar("Device:R","R17","10k 1%",45.0,82.0,huella=H_R)
    s.cable(r17["1"],(25.0,r17["1"][1])); s.etiqueta("LED_DATA",25.0,r17["1"][1],"izq"); s.power("GND",45.0,r17["2"][1])
    pix=connector(s,"C_PIX",3,250.0,75.0,"FCOB: +12V_PROT / DIN / GND"); label_connector(s,pix,PINOUTS["C_PIX"],215.0,"izq")
    c16=s.colocar("Device:C_Polarized","C16","680u 16V",205.0,50.0,huella=H_CP10)
    s.cable(c16["1"],(c16["1"][0],c16["1"][1]-6.35)); s.etiqueta("+12V_PROT",c16["1"][0],c16["1"][1]-6.35)
    s.power("GND",c16["2"][0],c16["2"][1])
    r18=s.colocar("Device:R","R18","1k 1%",110.0,140.0,rot=90,huella=H_R)
    q=s.colocar("Transistor_BJT:Q_NPN_EBC","Q1","PN2222A",155.0,140.0,huella="Package_TO_SOT_THT:TO-92_Inline")
    s.etiqueta("BUZZ",75.0,r18["1"][1],"izq"); s.cable((75.0,r18["1"][1]),r18["1"]); s.cable(r18["2"],q["2"])
    s.cable(q["1"],(q["1"][0],q["1"][1]+3.81)); s.power("GND",q["1"][0],q["1"][1]+3.81)
    s.cable(q["3"],(190.0,q["3"][1])); s.etiqueta("BZ_SW",190.0,q["3"][1])
    bz=connector(s,"C_BZ",2,250.0,140.0,"PANEL PIEZO: +5V_PROT / BZ_SW"); label_connector(s,bz,PINOUTS["C_BZ"],215.0,"izq")
    p5=connector(s,"C_PWR5",3,30.0,175.0,"+5V_PROT / +12V_PROT / GND",True); label_connector(s,p5,PINOUTS["C_PWR5"],60.0,"der")
    pd=connector(s,"C_UI_D",3,130.0,175.0,"GND / DATA / BUZZ",True); label_connector(s,pd,PINOUTS["C_UI_D"],160.0,"der")
    power_input(s,"+5V_PROT",30.48,43.18); power_input(s,"+12V_PROT",76.2,43.18); power_input(s,"GND",119.38,43.18)
    s.texto("Real strip: BTF FCOB WS2811 12 V, 720 LED/m, 20 pixels/m.\n"
            "Four 50 mm pixels = 200 mm; design maximum is 2 W.\n"
            "ENC1 and its R/C network are removed in E.9; all user input is touch.\n"
            "Verify Q1 E/B/C against the exact manufacturer's datasheet before soldering.",20.32,198.12,1.15)
    return s


BUILD={"T1":t1,"T2":t2,"T3":t3,"T4":t4,"T5":t5}


def item(refs, description, qty, status, mounting):
    return {"References": refs, "Description": description, "Quantity": qty,
            "Purchase status": status, "Mounting / verification": mounting}


BOARD_BOM = {
    "T1": [
        item("J1", "2-way 5.08 mm terminal block", 1, "planned", "12 V input from panel CON-156A"),
        item("F2", "Resettable PTC, 2.0 A hold, rated >=16 V", 1, "planned", "Series input protection"),
        item("D1", "1N5822 Schottky, 3 A, DO-201AD", 1, "planned", "Do not substitute the purchased 1N5819 without current/thermal review"),
        item("C1", "470 uF 35 V electrolytic", 1, "verified purchase", "At protected 12 V input; measure body before final placement"),
        item("C2", "100 nF 50 V ceramic THT", 1, "verified shared stock", "At protected 12 V input"),
        item("C17", "680 uF 16 V electrolytic", 1, "verified purchase", "At returned 5 V rail; low-ESR not verified"),
        item("C_BUCK_IN C_BUCK_OUT C_PWR3 C_PWR4", "JST-XH 2-way vertical header", 4, "planned", "Key every harness; BUCK IN and OUT must not be interchangeable"),
        item("C_PWR5", "JST-XH 3-way vertical header", 1, "planned", "+5V_PROT / +12V_PROT / GND"),
        item("BOARD", "FR4 perfboard, 2.54 mm pitch, cut to 50 x 40 mm from user's 60 x 40 mm board", 1, "declared on hand; dimensions unverified", "Test against the printed supports, mark, then remove 10 mm from the long side and deburr all copper edges"),
    ],
    "T2": [
        item("J2 J3", "JST-XH 2-way vertical header", 2, "planned", "Short harnesses to panel SCT jacks"),
        item("R3", "15 kohm metal-film resistor, 1%, 0.25 W", 1, "planned", "VBIAS upper divider"),
        item("R4", "10 kohm metal-film resistor, 1%, 0.25 W", 1, "planned", "VBIAS lower divider"),
        item("R5 R6", "3.3 kohm metal-film resistor, 1%, 0.25 W", 2, "planned", "ADC series filters"),
        item("C5 C6", "47 nF film or C0G THT, 5%", 2, "planned", "Return to VBIAS, not GND"),
        item("C7", "10 uF >=16 V electrolytic", 1, "planned", "VBIAS reservoir"),
        item("C8", "100 nF 50 V ceramic THT", 1, "verified shared stock", "VBIAS bypass"),
        item("D2 D3 D4 D5", "BAT85 Schottky DO-35", 4, "planned", "ADC clamps"),
        item("C_ADC_I", "JST-XH 4-way vertical header", 1, "planned", "+3V3 / GND / CH1_ADC / CH2_ADC"),
        item("BOARD", "FR4 perfboard, 2.54 mm pitch, cut to 70 x 55 mm", 1, "planned", "Keep SCT traces away from digital/power wiring"),
    ],
    "T3": [
        item("J5", "3-way 5.08 mm terminal block", 1, "planned", "Only ZMPT low-voltage side enters this board"),
        item("R7", "11 kohm metal-film resistor, 1%, 0.25 W", 1, "planned", "Voltage-channel divider/filter"),
        item("R8", "13 kohm metal-film resistor, 1%, 0.25 W", 1, "planned", "Do not replace with 12 kohm"),
        item("C9", "27 nF film or C0G THT, 5%", 1, "planned", "Voltage-channel filter"),
        item("D6 D7", "BAT85 Schottky DO-35", 2, "planned", "ADC clamps"),
        item("C_PWR3", "JST-XH 2-way vertical header", 1, "planned", "+5V_PROT / GND"),
        item("C_ADC_V", "JST-XH 3-way vertical header", 1, "planned", "+3V3 / GND / V_ADC"),
        item("BOARD", "FR4 perfboard, 2.54 mm pitch, cut to 55 x 45 mm", 1, "planned", "No mains-voltage component is allowed on T3"),
    ],
    "T4": [
        item("U1", "ESP32S V1.1 USB-C, 38 pins, ESP32-WROOM-32", 1, "planned", "ADC1 pins only; keep antenna and USB-C clear"),
        item("U1 sockets", "Female header strip 1x19, 2.54 mm", 2, "verified shared stock", "Cut from verified 1x40 strips; confirm 25.4 mm row spacing"),
        item("R11", "330 ohm metal-film resistor, 1%, 0.25 W", 1, "planned", "Panel status LED series resistor"),
        item("C_PWR4 C_LILY C_LED", "JST-XH 2-way vertical header", 3, "planned", "LilyGO connector carries power only"),
        item("C_ADC_V C_UI_D", "JST-XH 3-way vertical header", 2, "planned", "Voltage ADC and digital-output harnesses"),
        item("C_ADC_I", "JST-XH 4-way vertical header", 1, "planned", "Two current ADC channels"),
        item("BOARD", "FR4 perfboard, 2.54 mm pitch, cut to 80 x 65 mm", 1, "planned", "No SW1, SW2, ENC1 or wired LCD bus in E.9"),
    ],
    "T5": [
        item("U3", "74HCT245N DIP-20", 1, "verified shared purchase", "HCT required; do not use 74HC245"),
        item("U3 socket", "DIP-20 socket, 7.62 mm", 1, "verified shared purchase", "Install before U3"),
        item("Q1", "2N2222A or PN2222A THT", 1, "planned", "Verify E/B/C for the exact manufacturer"),
        item("R16", "330 ohm metal-film resistor, 1%, 0.25 W", 1, "planned", "Series resistor on FCOB data"),
        item("R17 R23", "10 kohm metal-film resistor, 1%, 0.25 W", 2, "planned", "Input and unused-channel pulldowns"),
        item("R18", "1 kohm metal-film resistor, 1%, 0.25 W", 1, "planned", "Piezo transistor base"),
        item("C14", "100 nF 50 V ceramic THT", 1, "verified shared stock", "Directly beside U3 pins 20/10"),
        item("C16", "680 uF 16 V electrolytic", 1, "verified purchase", "Beside C_PIX; low-ESR not verified"),
        item("C_PWR5 C_UI_D C_PIX", "JST-XH 3-way vertical header", 3, "planned", "Power, control and FCOB"),
        item("C_BZ", "JST-XH 2-way vertical header", 1, "planned", "Panel passive piezo"),
        item("BOARD", "FR4 perfboard, 2.54 mm pitch, cut to 65 x 50 mm", 1, "planned", "Encoder and its RC network are absent in E.9"),
    ],
    "OFFBOARD": [
        item("U4", "LM2596 adjustable buck module, reserved 43 x 21 x 14 mm", 1, "planned / exact model unverified", "Adjust to 5.0 V unloaded, then verify under current-limited load"),
        item("LCD1", "LilyGO T4-S3 AMOLED 2.41 in, 450 x 600", 1, "planned", "ESP-NOW terminal; VBUS/GND only; disconnect harness before USB"),
        item("JDC", "CON-156A panel jack, 5.5 x 2.5 mm, center positive", 1, "verified purchase", "12 V input"),
        item("J2P J3P", "3.5 mm female panel jack", 2, "planned", "For SCT-013-000 plugs"),
        item("R1", "22 ohm metal-film resistor, 1%, 0.25 W", 1, "planned", "Solder directly across CH1 panel jack"),
        item("R2", "47 ohm metal-film resistor, 1%, 0.25 W", 1, "planned", "Solder directly across CH2 panel jack"),
        item("D8", "Green diffused panel LED, 5 mm", 1, "verified purchase", "Connected through C_LED; R11 is on T4"),
        item("BZ1", "GEP0008 passive piezo, 44 x 14 mm", 1, "declared purchased; document pending", "Not an active buzzer"),
        item("FCOB", "BTF FCOB WS2811, 12 V, 12 mm, 200 mm used", 1, "planned", "Four 50 mm addressable pixels; <=2 W design load"),
        item("SCT1 SCT2", "SCT-013-000, 100 A : 50 mA, no internal burden", 2, "planned", "Never leave secondary open while clamped around energized conductor"),
        item("Z1-U2", "ZMPT101B module", 1, "planned", "Primary remains inside guarded Z1 compartment"),
        item("Z1-F1", "T500 mA 250 V slow-blow fuse + enclosed holder", 1, "planned", "Phase conductor only; qualified mains work"),
        item("Z1-J4", "Guarded 2-way mains terminal + PG7 gland", 1, "planned", "Inside opaque segregated guard"),
        item("SUPPLY", "Isolated regulated 12 V DC adapter, center-positive", 1, "planned", "Final current rating after measured load test; 2 A provisional minimum"),
    ],
}


CABLES = [
    ("C_DC_IN","Panel JDC",1,"+12V_IN","T1 J1",1,"22 AWG red","Center positive"),
    ("C_DC_IN","Panel JDC",2,"GND","T1 J1",2,"22 AWG black","Return"),
    ("C_BUCK_IN","T1",1,"+12V_PROT","U4 LM2596 IN",1,"22 AWG red","Key separately from BUCK_OUT"),
    ("C_BUCK_IN","T1",2,"GND","U4 LM2596 IN",2,"22 AWG black",""),
    ("C_BUCK_OUT","U4 LM2596 OUT",1,"+5V_PROT","T1",1,"22 AWG red","Adjust to 5.0 V before connecting"),
    ("C_BUCK_OUT","U4 LM2596 OUT",2,"GND","T1",2,"22 AWG black",""),
    ("C_PWR3","T1",1,"+5V_PROT","T3",1,"22 AWG red","Dedicated star pair"),
    ("C_PWR3","T1",2,"GND","T3",2,"22 AWG black",""),
    ("C_PWR4","T1",1,"+5V_PROT","T4",1,"22 AWG red","Dedicated star pair"),
    ("C_PWR4","T1",2,"GND","T4",2,"22 AWG black",""),
    ("C_PWR5","T1",1,"+5V_PROT","T5",1,"22 AWG red","Dedicated harness"),
    ("C_PWR5","T1",2,"+12V_PROT","T5",2,"22 AWG yellow","FCOB branch"),
    ("C_PWR5","T1",3,"GND","T5",3,"22 AWG black",""),
    ("C_ADC_I","T4",1,"+3V3","T2",1,"24 AWG red","Short; away from digital wiring"),
    ("C_ADC_I","T4",2,"GND","T2",2,"24 AWG black","Twist/route with signals"),
    ("C_ADC_I","T4",3,"CH1_ADC","T2",3,"24 AWG yellow","GPIO36 / ADC1"),
    ("C_ADC_I","T4",4,"CH2_ADC","T2",4,"24 AWG blue","GPIO39 / ADC1"),
    ("C_ADC_V","T4",1,"+3V3","T3",1,"24 AWG red","Clamp reference"),
    ("C_ADC_V","T4",2,"GND","T3",2,"24 AWG black",""),
    ("C_ADC_V","T4",3,"V_ADC","T3",3,"24 AWG white","GPIO35 / ADC1"),
    ("C_UI_D","T4",1,"GND","T5",1,"24 AWG black","Digital reference"),
    ("C_UI_D","T4",2,"LED_DATA GPIO13","T5",2,"24 AWG green","To HCT input"),
    ("C_UI_D","T4",3,"BUZZ GPIO14","T5",3,"24 AWG orange","To R18"),
    ("C_LILY","T4",1,"+5V_PROT","Panel LCD1",1,"22 AWG red","VBUS; disconnect before USB-C"),
    ("C_LILY","T4",2,"GND","Panel LCD1",2,"22 AWG black","No UART/SPI/I2C"),
    ("C_LED","T4",1,"LED_A","Panel D8",1,"24 AWG green","R11 remains on T4"),
    ("C_LED","T4",2,"GND","Panel D8",2,"24 AWG black",""),
    ("C_BZ","T5",1,"+5V_PROT","Panel BZ1",1,"24 AWG red","Passive piezo"),
    ("C_BZ","T5",2,"BZ_SW","Panel BZ1",2,"24 AWG black","Switched by Q1"),
    ("C_PIX","T5",1,"+12V_PROT","Panel FCOB",1,"22 AWG yellow","Never connect to +5 V"),
    ("C_PIX","T5",2,"DIN_5V","Panel FCOB",2,"24 AWG green","Follow data arrow"),
    ("C_PIX","T5",3,"GND","Panel FCOB",3,"22 AWG black",""),
    ("C_ZMPT","T3",1,"+5V_PROT","Z1 U2 LV",1,"22 AWG red","Low-voltage side only"),
    ("C_ZMPT","T3",2,"ZMPT_OUT","Z1 U2 LV",2,"24 AWG yellow","Verify module pin order"),
    ("C_ZMPT","T3",3,"GND","Z1 U2 LV",3,"22 AWG black",""),
]


def validate_pinouts():
    endpoints={"C_PWR3":["T1","T3"],"C_PWR4":["T1","T4"],"C_PWR5":["T1","T5"],
               "C_ADC_I":["T2","T4"],"C_ADC_V":["T3","T4"],"C_UI_D":["T4","T5"],
               "C_BUCK_IN":["T1","U4"],"C_BUCK_OUT":["U4","T1"],
               "C_LILY":["T4","Panel"],"C_LED":["T4","Panel"],
               "C_BZ":["T5","Panel"],"C_PIX":["T5","Panel"]}
    return {"valid":True,"revision":"E.9-TOUCH-12V-LM2596","pinouts":PINOUTS,"endpoints":endpoints,
            "strip":{"asin":"B0BW5T6HW4","model":"FCOB-12V-720L-W-IP30-SPI","voltage_v":12,
                     "width_mm":12,"cut_mm":50,"pixels_per_m":20,"used_pixels":4,"used_length_mm":200,"max_power_w":2.0}}


def write_boms():
    root = OUT.parent
    bom_dir = root / "bom-por-tarjeta"
    bom_dir.mkdir(exist_ok=True)
    fields = ["Assembly", "References", "Description", "Quantity", "Purchase status", "Mounting / verification"]
    all_rows = []
    for assembly, rows in BOARD_BOM.items():
        cooked = [dict(Assembly=assembly, **row) for row in rows]
        all_rows.extend(cooked)
        with (bom_dir / f"BOM-{assembly}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(cooked)
    for csv_name in ("BOM-E9-by-board.csv", "BOM-precision.csv"):
        with (root / csv_name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(all_rows)
    lines = ["# E.9 BOM by board", "", "Generated from `herramientas/generar_kicad_perforadas.py`.",
             "Quantities are mounted quantities, not spare-purchase quantities. `verified` refers only to documented purchase evidence.", ""]
    for assembly, rows in BOARD_BOM.items():
        title = assembly if assembly != "OFFBOARD" else "Off-board, panel and guarded Z1"
        lines += [f"## {title}", "", "| References | Qty | Description | Purchase status | Mounting / verification |",
                  "|---|---:|---|---|---|"]
        for row in rows:
            vals = [str(row[k]).replace("|", "\\|") for k in ("References","Quantity","Description","Purchase status","Mounting / verification")]
            lines.append("| " + " | ".join(vals) + " |")
        lines.append("")
    rendered_bom = "\n".join(lines)
    (root / "BOM-E9-by-board.md").write_text(rendered_bom, encoding="utf-8")
    (root / "BOM-precision.md").write_text(rendered_bom, encoding="utf-8")

    # Keep the legacy Spanish column names because the CAD electrical validator
    # consumes this file directly.
    list_fields = ["Tarjeta", "Referencias", "Descripción", "Regla de montaje"]
    with (root / "lista-por-tarjeta.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list_fields); w.writeheader()
        for assembly, rows in BOARD_BOM.items():
            w.writerow({"Tarjeta": assembly, "Referencias": " ".join(r["References"] for r in rows),
                        "Descripción": "; ".join(r["Description"] for r in rows),
                        "Regla de montaje": "; ".join(r["Mounting / verification"] for r in rows)})

    cable_fields = ["Cable","Desde","Pin","Señal","Hacia","Pin destino","Calibre/color recomendado","Nota"]
    with (root / "conexiones-entre-tarjetas.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cable_fields); w.writerows(CABLES)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for card,fn in BUILD.items():
        sch=fn(); path=OUT/f"medidor-{card.lower()}.kicad_sch"
        sch.guardar(str(path),[f"Energy meter · {card}","2026-11-22","E.9","","Modular perfboard","Touch LilyGO · 12 V input · LM2596 to 5 V"], papel="A4")
        (OUT/f"medidor-{card.lower()}.kicad_pro").write_text("{}\n",encoding="utf-8")
    (OUT/"fp-lib-table").write_text('(fp_lib_table\n  (version 7)\n  (lib (name "Medidor")(type "KiCad")(uri "${KIPRJMOD}/../../Medidor.pretty")(options "")(descr "Huellas propias"))\n)\n',encoding="utf-8")
    (OUT/"contratos.json").write_text(json.dumps(validate_pinouts(),indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    write_boms()
    print(OUT)


if __name__=="__main__": main()
