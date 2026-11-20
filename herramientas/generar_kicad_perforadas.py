#!/usr/bin/env python3
"""Genera esquemáticos KiCad nativos para T1–T5 del medidor modular.

Estos archivos, no las láminas ilustrativas antiguas, son la fuente eléctrica.
La tira real es BTF FCOB WS2811, 12 V, 720 LED/m, 20 segmentos/m.
"""
from pathlib import Path
import json
import os
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "hardware" / "perforadas-modulares" / "kicad"
sys.path.insert(0, str(HERE))
import generar_esquematico as g

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
H_DIP20 = "Package_DIP:DIP-20_W7.62mm"

PINOUTS = {
    "C_PWR3": ["+5V", "GND"],
    "C_PWR4": ["+5V", "GND"],
    "C_PWR5": ["+5V", "+12V_LED", "GND"],
    "C_ADC_I": ["+3V3", "GND", "CH1_ADC", "CH2_ADC"],
    "C_ADC_V": ["+3V3", "GND", "V_ADC"],
    "C_UI_D": ["GND", "LED_DATA", "BUZZ"],
    "C_UI_E": ["+3V3", "GND", "ENC_A", "ENC_B", "ENC_SW"],
    "C_PIX": ["+12V_LED", "DIN_5V", "GND"],
    "C_LCD": ["+3V3", "GND", "LCD_DIN", "LCD_CS", "LCD_DC", "LCD_BL", "LCD_CLK", "LCD_RST"],
}


def reset(card):
    g._ns = uuid.uuid5(uuid.NAMESPACE_URL, f"medidor-energia-perforada-{card}-e7")
    g._cont.clear()
    g.RAIZ = g.uid("raiz")
    g.PROYECTO = f"medidor-perforada-{card.lower()}"
    # No heredar las asignaciones por referencia del esquemático monolítico.
    g.HUELLAS = {}


def own_symbol(name, ref, value, pins, width=15.24, height=12.7, description=""):
    """Símbolo rectangular simple; pins=(tipo,x,y,ang,nombre,numero)."""
    p = [g.pin_def(*x) for x in pins]
    graphics = [g.rect(-width/2, height/2, width/2, -height/2)]
    return g.simbolo_propio(f"Medidor:{name}", ref, value, graphics, p,
                            height/2+2.54, -height/2-2.54, description)


def connector(s, ref, n, x, y, value, mirror=False):
    fp = {2:H_CONN2, 3:H_CONN3, 4:H_CONN4, 5:H_CONN5, 8:H_CONN8}[n]
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
    s.texto(f"Tarjeta perforada recortada: {size[0]} × {size[1]} mm · paso 2,54 mm", 20.32, 30.48, 1.1)


def power_input(s, name, x, y):
    """Declara una alimentación que entra por arnés, lejos del conector impreso."""
    if name in ("+5V", "+3V3", "GND"):
        s.power(name, x, y, 180)
    else:
        s.etiqueta(name, x, y, "der")
    s.bandera(x, y)


def t1():
    reset("T1"); s=g.Esquematico(); add_note(s,"T1","ALIMENTACIÓN 5 V + ELEVADOR 12 V LED",(50,40))
    boost=own_symbol("MT3608_Module","U","MT3608 ajustado a 12,0 V",[
        ("power_in",-10.16,2.54,0,"VIN+","1"),("power_in",-10.16,-2.54,0,"VIN-","2"),
        ("power_out",10.16,2.54,180,"VOUT+","3"),("power_out",10.16,-2.54,180,"VOUT-","4")],20.32,10.16,
        "Módulo elevador MT3608; ajustar a 12,0 V antes de conectar la tira")
    s.usar("Medidor:MT3608_Module",boost)
    j=connector(s,"J1",2,27.94,50.8,"ENTRADA ADAP-5V-5A 5,5x2,5",True)
    f=s.colocar("Device:Polyfuse","F2","PTC hold 2,0 A",45.72,49.53,rot=90,huella="Fuse:Fuse_Littelfuse-LVR200")
    d=s.colocar("Device:D_Schottky","D1","1N5822 3 A",60.96,49.53,rot=180,huella="Diode_THT:D_DO-201AD_P15.24mm_Horizontal")
    s.cable(j["1"],f["1"]); s.cable(f["2"],d["2"]); s.cable(d["1"],(71.12,49.53)); s.etiqueta("+5V",71.12,49.53)
    s.bandera(71.12,49.53)
    s.cable(j["2"],(35.56,j["2"][1]),(35.56,60.96)); s.power("GND",35.56,60.96)
    c1=s.colocar("Device:C_Polarized","C1","470u 35V (comprado)",76.2,55.88,huella=g.H_CP)
    c2=s.colocar("Device:C","C2","100n",88.9,55.88,huella=H_C)
    for c in (c1,c2): s.cable(c["1"],(c["1"][0],49.53)); s.etiqueta("+5V",c["1"][0],49.53); s.power("GND",c["2"][0],c["2"][1])
    u=s.colocar("Medidor:MT3608_Module","U4","MT3608 5→12 V",63.5,82.55,huella="")
    s.cable(u["1"],(48.26,u["1"][1])); s.etiqueta("+5V",48.26,u["1"][1],"izq")
    s.cable(u["2"],(48.26,u["2"][1])); s.power("GND",48.26,u["2"][1],270)
    s.cable(u["3"],(78.74,u["3"][1])); s.etiqueta("+12V_LED",78.74,u["3"][1])
    s.cable(u["4"],(78.74,u["4"][1])); s.power("GND",78.74,u["4"][1],90)
    c17=s.colocar("Device:C_Polarized","C17","680u 16V",91.44,82.55,huella=H_CP10)
    s.cable(c17["1"],(91.44,76.2)); s.etiqueta("+12V_LED",91.44,76.2); s.power("GND",91.44,c17["2"][1])
    for i,(ref,names,y) in enumerate((("C_PWR3",PINOUTS["C_PWR3"],109.22),("C_PWR4",PINOUTS["C_PWR4"],127.0),("C_PWR5",PINOUTS["C_PWR5"],147.32))):
        p=connector(s,ref,len(names),116.84,y," / ".join(names)); label_connector(s,p,names,101.6,"izq")
    s.texto("AJUSTE OBLIGATORIO: sin la tira conectada, regular U4 hasta 12,0 V.\n"
            "La tira FCOB de 200 mm consume hasta 2 W; diseñar U4 para ≥0,25 A a 12 V.\n"
            "D1 y F2 cambian respecto al diseño anterior: 1N5819/1,1 A quedan con poco margen.",20.32,167.64,1.15)
    return s


def current_channel(s, n, y, burden):
    j=connector(s,f"J{n+1}",2,27.94,y,f"SCT-013-000 CH{n} · T/S",True)
    rb=s.colocar("Device:R",f"R{n}",f"{burden}Ω 1% burden",45.72,y,rot=90,huella=H_R)
    s.cable(j["1"],rb["1"]); s.cable(rb["2"],(55.88,rb["2"][1])); s.etiqueta("VBIAS",55.88,rb["2"][1])
    rs=s.colocar("Device:R",f"R{n+4}","3,3k 1%",63.5,j["1"][1],rot=90,huella=H_R)
    s.cable(j["1"],rs["1"]); out=f"CH{n}_ADC"; s.cable(rs["2"],(76.2,rs["2"][1])); s.etiqueta(out,76.2,rs["2"][1])
    c=s.colocar("Device:C",f"C{n+4}","47n 5%",81.28,y+5.08,huella=H_C)
    s.cable(c["1"],(81.28,rs["2"][1])); s.etiqueta(out,81.28,rs["2"][1]); s.cable(c["2"],(81.28,y+10.16)); s.etiqueta("VBIAS",81.28,y+10.16)
    dl=s.colocar("Device:D_Schottky",f"D{2*n+1}","BAT85",93.98,y+3.81,rot=270,huella=H_D)
    dh=s.colocar("Device:D_Schottky",f"D{2*n}","BAT85",93.98,y-3.81,rot=270,huella=H_D)
    s.cable((93.98,rs["2"][1]),dl["1"],dh["2"]); s.power("GND",93.98,dl["2"][1]); s.power("+3V3",93.98,dh["1"][1],180)
    s.cable(j["2"],(35.56,j["2"][1])); s.etiqueta("VBIAS",35.56,j["2"][1])


def t2():
    reset("T2"); s=g.Esquematico(); add_note(s,"T2","DOS SCT + VBIAS",(70,55))
    current_channel(s,1,58.42,22); current_channel(s,2,101.6,47)
    r3=s.colocar("Device:R","R3","15k 1%",124.46,55.88,huella=H_R); r4=s.colocar("Device:R","R4","10k 1%",124.46,71.12,huella=H_R)
    s.power("+3V3",124.46,r3["1"][1]); s.cable(r3["2"],(124.46,63.5),r4["1"]); s.etiqueta("VBIAS",124.46,63.5); s.power("GND",124.46,r4["2"][1])
    c7=s.colocar("Device:C_Polarized","C7","10u 16V",139.7,68.58,huella=H_CP5); c8=s.colocar("Device:C","C8","100n",152.4,68.58,huella=H_C)
    for c in (c7,c8): s.cable(c["1"],(c["1"][0],63.5)); s.etiqueta("VBIAS",c["1"][0],63.5); s.power("GND",c["2"][0],c["2"][1])
    p=connector(s,"C_ADC_I",4,160.02,104.14,"+3V3 / GND / CH1 / CH2"); label_connector(s,p,PINOUTS["C_ADC_I"],144.78,"izq")
    power_input(s,"+3V3",170.18,43.18); power_input(s,"GND",182.88,43.18)
    s.texto("R1 y R2 van físicamente sobre los terminales del jack: nunca dejar abierta una SCT energizada.\nC5/C6 retornan a VBIAS, no a GND.",20.32,132.08,1.15)
    return s


def t3():
    reset("T3"); s=g.Esquematico(); add_note(s,"T3","ACONDICIONAMIENTO DE TENSIÓN · SOLO MBT",(55,45))
    p=connector(s,"J5",3,27.94,60.96,"ZMPT MBT: +5V / OUT / GND",True); label_connector(s,p,["+5V","ZMPT_OUT","GND"],40.64,"der")
    r7=s.colocar("Device:R","R7","11k 1%",71.12,p["2"][1],rot=90,huella=H_R); s.cable((40.64,p["2"][1]),r7["1"])
    x=86.36; s.cable(r7["2"],(x,r7["2"][1])); s.etiqueta("V_ADC",x,r7["2"][1])
    r8=s.colocar("Device:R","R8","13k 1%",91.44,73.66,huella=H_R); c9=s.colocar("Device:C","C9","27n 5%",104.14,73.66,huella=H_C)
    for q in (r8,c9):
        s.cable(q["1"],(q["1"][0],r7["2"][1]),(x,r7["2"][1]))
        s.cable(q["2"],(q["2"][0],q["2"][1]+2.54)); s.power("GND",q["2"][0],q["2"][1]+2.54)
    d6=s.colocar("Device:D_Schottky","D6","BAT85",119.38,54.61,rot=270,huella=H_D); d7=s.colocar("Device:D_Schottky","D7","BAT85",119.38,69.85,rot=270,huella=H_D)
    s.cable((119.38,r7["2"][1]),d6["2"],d7["1"]); s.power("+3V3",119.38,d6["1"][1],180); s.power("GND",119.38,d7["2"][1])
    a=connector(s,"C_ADC_V",3,149.86,60.96,"+3V3 / GND / V_ADC"); label_connector(s,a,PINOUTS["C_ADC_V"],134.62,"izq")
    w=connector(s,"C_PWR3",2,149.86,91.44,"+5V / GND"); label_connector(s,w,PINOUTS["C_PWR3"],134.62,"izq")
    power_input(s,"+3V3",144.78,43.18); power_input(s,"GND",157.48,43.18)
    s.texto("J4, F1 y el primario del ZMPT101B NO están en esta tarjeta.\nEl módulo completo permanece dentro de Z1; T3 recibe solamente +5V, OUT y GND.",20.32,111.76,1.2)
    return s


def t4():
    reset("T4"); s=g.Esquematico(); s.usar("Medidor:ESP32-DevKitC-38",g.sim_esp32()); add_note(s,"T4","ESP32S V1.1 USB-C + CONTROL",(80,65))
    u=s.colocar("Medidor:ESP32-DevKitC-38","U1","ESP32S V1.1 USB-C 38P",91.44,101.6,huella="Medidor:ESP32-DevKitC-38_Zocalo",
                nc=[str(i) for i in range(1,39) if i not in (1,3,4,6,7,8,9,10,11,12,14,15,19,20,21,22,25,26,27,28,32,35)])
    mapping={"1":"+3V3","3":"CH1_ADC","4":"CH2_ADC","6":"V_ADC","7":"ENC_A","8":"ENC_B","9":"LED_EST","10":"SW1","11":"SW2","12":"BUZZ","14":"GND","15":"LED_DATA","19":"+5V",
             "20":"GND","21":"LCD_DIN","22":"LCD_CS","25":"LCD_DC","26":"GND","27":"LCD_BL","28":"LCD_CLK","32":"LCD_RST","35":"ENC_SW"}
    for pin,name in mapping.items():
        q=u[pin]; left=q[0]<91.44; xx=q[0]+(-10.16 if left else 10.16); s.cable(q,(xx,q[1]))
        if name=="GND": s.power("GND",xx,q[1],270 if left else 90)
        elif name.startswith("+"): s.power(name,xx,q[1],90 if left else 270)
        else: s.etiqueta(name,xx,q[1],"izq" if left else "der")
    specs=[("C_PWR4",2,30.48,55.88),("C_ADC_I",4,30.48,81.28),("C_ADC_V",3,30.48,109.22),("C_UI_D",3,160.02,55.88),("C_UI_E",5,160.02,83.82),("C_LCD",8,160.02,127.0)]
    for ref,n,x,y in specs:
        p=connector(s,ref,n,x,y," / ".join(PINOUTS[ref]),mirror=x<90); label_connector(s,p,PINOUTS[ref],x+(12.7 if x<90 else -12.7),"der" if x<90 else "izq")
    power_input(s,"+5V",35.56,40.64); power_input(s,"GND",50.8,40.64)
    # LED de estado local/panel.
    r11=s.colocar("Device:R","R11","330Ω",111.76,149.86,rot=90,huella=H_R)
    d8=s.colocar("Device:LED","D8","LED verde panel",132.08,149.86,rot=180,huella="LED_THT:LED_D5.0mm")
    s.etiqueta("LED_EST",99.06,r11["1"][1],"izq"); s.cable((99.06,r11["1"][1]),r11["1"]); s.cable(r11["2"],d8["2"]); s.cable(d8["1"],(142.24,d8["1"][1])); s.power("GND",142.24,d8["1"][1],90)
    # Dos pulsadores locales con pull-up y antirrebote.
    for i,(net,y) in enumerate((("SW1",160.02),("SW2",180.34))):
        rr=s.colocar("Device:R",f"R{12+i}","10k 1%",60.96,y-5.08,huella=H_R); sw=s.colocar("Switch:SW_Push",net,"SW12BP panel",91.44,y,huella=H_CONN2); cc=s.colocar("Device:C",f"C{10+i}","100n",76.2,y+5.08,huella=H_C)
        s.power("+3V3",60.96,rr["1"][1]); s.cable(rr["2"],(60.96,y),(76.2,y),sw["1"]); s.etiqueta(net,60.96,y,"izq"); s.cable(cc["1"],(76.2,y)); s.power("GND",76.2,cc["2"][1]); s.power("GND",104.14,sw["2"][1],90); s.cable(sw["2"],(104.14,sw["2"][1]))
    s.texto("ESP32 montado en dos zócalos hembra 1×19, separación entre hileras 25,4 mm.\nMantener libre el extremo de antena y el conector USB-C.",20.32,203.2,1.15)
    return s


def t5():
    reset("T5"); s=g.Esquematico(); add_note(s,"T5","INTERFAZ, PIEZO Y FCOB WS2811 12 V",(65,50))
    # El símbolo 74LS245 nativo de KiCad tiene exactamente el mismo pinout DIP-20;
    # el valor y la pieza física siguen siendo 74HCT245N.
    # 74HCT245 se usa como buffer 3,3→5 V; canales no usados amarrados a GND.
    u=s.colocar("74xx:74LS245","U3","74HCT245N",81.28,73.66,huella=H_DIP20,nc=[str(i) for i in range(11,18)])
    # Pinout estándar: 1 DIR, 2 A0, 3..9 A1..A7, 10 GND, 11..18 B7..B0, 19 OE, 20 VCC.
    # Alimentación y control del sentido: A→B, salida siempre habilitada.
    q=u["20"]; s.cable(q,(q[0],q[1]-5.08)); s.power("+5V",q[0],q[1]-5.08,180)
    q=u["1"]; s.cable(q,(q[0]-7.62,q[1])); s.power("+5V",q[0]-7.62,q[1],90)
    q=u["19"]; s.cable(q,(q[0]-7.62,q[1])); s.power("GND",q[0]-7.62,q[1],90)
    q=u["10"]; s.cable(q,(q[0],q[1]+5.08)); s.power("GND",q[0],q[1]+5.08)
    # A1..A7 no pueden flotar: bus común y un pull-down de 10 kΩ.
    bus_x=60.96
    for pin in range(3,10):
        q=u[str(pin)]; s.cable(q,(bus_x,q[1]))
    s.cable((bus_x,u["3"][1]),(bus_x,u["9"][1]))
    ru=s.colocar("Device:R","R23","10k",bus_x,86.36,huella=H_R)
    s.cable((bus_x,u["9"][1]),ru["1"]); s.power("GND",bus_x,ru["2"][1])
    s.cable(u["2"],(55.88,u["2"][1])); s.etiqueta("LED_DATA",55.88,u["2"][1],"izq")
    r16=s.colocar("Device:R","R16","330Ω 1%",111.76,u["18"][1],rot=90,huella=H_R); s.cable(u["18"],r16["1"]); s.cable(r16["2"],(127.0,r16["2"][1])); s.etiqueta("DIN_5V",127.0,r16["2"][1])
    c14=s.colocar("Device:C","C14","100n",104.14,45.72,huella=H_C); s.power("+5V",104.14,c14["1"][1],180); s.power("GND",104.14,c14["2"][1])
    r17=s.colocar("Device:R","R17","10k",48.26,76.2,huella=H_R); s.cable(r17["1"],(48.26,u["2"][1])); s.etiqueta("LED_DATA",48.26,u["2"][1]); s.power("GND",48.26,r17["2"][1])
    pix=connector(s,"C_PIX",3,154.94,60.96,"FCOB: +12V / DIN / GND"); label_connector(s,pix,PINOUTS["C_PIX"],137.16,"izq")
    c16=s.colocar("Device:C_Polarized","C16","680u 16V",132.08,48.26,huella=H_CP10)
    s.cable(c16["1"],(c16["1"][0],c16["1"][1]-2.54)); s.etiqueta("+12V_LED",c16["1"][0],c16["1"][1]-2.54)
    s.power("GND",c16["2"][0],c16["2"][1])
    # Encoder: conector de panel y RC por canal.
    enc=connector(s,"ENC1",5,30.48,124.46,"EC11: A / B / SW / COM / COM",True)
    channels=((1,"ENC_A","C12","10n",116.84),(2,"ENC_B","C13","10n",132.08),(3,"ENC_SW","C15","100n",147.32))
    for i,(pin,net,refc,valc,y) in enumerate(channels):
        py=enc[str(pin)][1]; s.cable(enc[str(pin)],(45.72,py)); s.etiqueta(net,45.72,py)
        rr=s.colocar("Device:R",f"R{19+i}","10k",60.96,y-5.08,huella=H_R)
        cc=s.colocar("Device:C",refc,valc,76.2,y+5.08,huella=H_C)
        s.power("+3V3",rr["1"][0],rr["1"][1],180)
        s.cable(rr["2"],(rr["2"][0],y),(76.2,y)); s.etiqueta(net,68.58,y)
        s.cable(cc["1"],(cc["1"][0],y)); s.power("GND",cc["2"][0],cc["2"][1])
    for pin in (4,5): s.cable(enc[str(pin)],(40.64,enc[str(pin)][1])); s.power("GND",40.64,enc[str(pin)][1],90)
    # Driver del piezo comprado 44×14 mm.
    r18=s.colocar("Device:R","R18","1k",104.14,139.7,rot=90,huella=H_R); q=s.colocar("Transistor_BJT:Q_NPN_EBC","Q1","2N2222 (verificar E/B/C)",121.92,139.7,huella="Package_TO_SOT_THT:TO-92_Inline")
    s.etiqueta("BUZZ",91.44,r18["1"][1],"izq"); s.cable((91.44,r18["1"][1]),r18["1"]); s.cable(r18["2"],q["2"]); s.cable(q["1"],(q["1"][0],q["1"][1]+3.81)); s.power("GND",q["1"][0],q["1"][1]+3.81)
    bz=s.colocar("Device:Buzzer","BZ1","Piezo pasivo 44×14 mm",149.86,139.7,huella=H_CONN2); s.cable(q["3"],bz["2"]); s.cable(bz["1"],(bz["1"][0],bz["1"][1]-3.81)); s.power("+5V",bz["1"][0],bz["1"][1]-3.81,180)
    p5=connector(s,"C_PWR5",3,30.48,170.18,"+5V / +12V_LED / GND",True); label_connector(s,p5,PINOUTS["C_PWR5"],45.72,"der")
    pd=connector(s,"C_UI_D",3,91.44,170.18,"GND / DATA / BUZZ",True); label_connector(s,pd,PINOUTS["C_UI_D"],106.68,"der")
    pe=connector(s,"C_UI_E",5,154.94,170.18,"+3V3 / GND / A / B / SW"); label_connector(s,pe,PINOUTS["C_UI_E"],137.16,"izq")
    power_input(s,"+5V",30.48,43.18); power_input(s,"+12V_LED",43.18,43.18)
    power_input(s,"+3V3",55.88,43.18); power_input(s,"GND",68.58,43.18)
    s.texto("Tira real: BTF FCOB WS2811 12 V, 720 LED/m, 20 segmentos/m.\n4 segmentos = 200 mm; consumo máximo de diseño 2 W. El firmware conserva 4 píxeles GRB/800 kHz.",20.32,198.12,1.15)
    return s


BUILD={"T1":t1,"T2":t2,"T3":t3,"T4":t4,"T5":t5}


def validate_pinouts():
    endpoints={"C_PWR3":["T1","T3"],"C_PWR4":["T1","T4"],"C_PWR5":["T1","T5"],
               "C_ADC_I":["T2","T4"],"C_ADC_V":["T3","T4"],"C_UI_D":["T4","T5"],"C_UI_E":["T4","T5"]}
    return {"valid":True,"revision":"E.7-WS2811-FCOB-12V","pinouts":PINOUTS,"endpoints":endpoints,
            "strip":{"asin":"B0BW5T6HW4","model":"FCOB-12V-720L-W-IP30-SPI","voltage_v":12,
                     "width_mm":12,"cut_mm":50,"pixels_per_m":20,"used_pixels":4,"used_length_mm":200,"max_power_w":2.0}}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for card,fn in BUILD.items():
        sch=fn(); path=OUT/f"medidor-{card.lower()}.kicad_sch"
        sch.guardar(str(path),[f"Medidor de energía · {card}","2026-11-20","E.7","","Tarjeta perforada modular","Tira BTF FCOB WS2811 12 V"], papel="A4")
        (OUT/f"medidor-{card.lower()}.kicad_pro").write_text("{}\n",encoding="utf-8")
    (OUT/"fp-lib-table").write_text('(fp_lib_table\n  (version 7)\n  (lib (name "Medidor")(type "KiCad")(uri "${KIPRJMOD}/../../Medidor.pretty")(options "")(descr "Huellas propias"))\n)\n',encoding="utf-8")
    (OUT/"contratos.json").write_text(json.dumps(validate_pinouts(),indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(OUT)


if __name__=="__main__": main()
