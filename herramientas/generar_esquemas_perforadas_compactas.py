#!/usr/bin/env python3
"""Genera esquemas legibles, uno por tarjeta perforada compacta del medidor."""
from pathlib import Path
import json
import math

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, Polygon, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "perforadas-modulares" / "esquemas"
COMBINED = ROOT / "hardware" / "perforadas-modulares" / "esquemas-tarjetas-compactas.pdf"

BLUE = "#143d73"
GREEN = "#167447"
RED = "#b4232d"
BLACK = "#15191e"
GRAY = "#5e6872"
LIGHT = "#f5f7f8"

CARDS = {
    "T1": {"title": "Alimentación protegida", "size_mm": [50, 40],
           "refs": ["J1", "F2", "D1", "C1", "C2", "TP1", "TP8"],
           "connectors": {"C_PWR3": ["+5V_PROT", "GND"], "C_PWR4": ["+5V_PROT", "GND"], "C_PWR5": ["+5V_PROT", "GND"]}},
    "T2": {"title": "Corriente CH1/CH2 y VBIAS", "size_mm": [70, 55],
           "refs": ["J2", "J3", "R1", "R2", "R3", "R4", "R5", "R6", "C5", "C6", "C7", "C8", "D2", "D3", "D4", "D5", "TP3", "TP4", "TP5"],
           "connectors": {"C_ADC_I": ["+3V3", "GND", "CH1_ADC", "CH2_ADC"]}},
    "T3": {"title": "Tensión de muy baja tensión", "size_mm": [55, 45],
           "refs": ["J5", "R7", "R8", "C9", "D6", "D7", "TP6", "TP7", "TP9"],
           "connectors": {"C_PWR3": ["+5V_PROT", "GND"], "C_ZMPT": ["+5V_PROT", "ZMPT_OUT", "GND"], "C_ADC_V": ["+3V3", "GND", "V_ADC"]}},
    "T4": {"title": "ESP32S V1.1 USB-C y control", "size_mm": [80, 65],
           "refs": ["U1", "J6", "R11", "R12", "R13", "R14", "R15", "C10", "C11", "D8", "D9", "D10", "SW1", "SW2", "TP2", "J_RES34"],
           "connectors": {"C_PWR4": ["+5V_PROT", "GND"], "C_ADC_I": ["+3V3", "GND", "CH1_ADC", "CH2_ADC"], "C_ADC_V": ["+3V3", "GND", "V_ADC"], "C_UI_D": ["GND", "LED_DATA", "BUZZ"], "C_UI_E": ["+3V3", "GND", "ENC_A", "ENC_B", "ENC_SW"], "C_LCD": ["VCC", "GND", "DIN", "CS", "DC", "BL", "CLK", "RST"]}},
    "T5": {"title": "Encoder, NeoPixel y piezo", "size_mm": [65, 50],
           "refs": ["U3", "Q1", "R16", "R17", "R18", "R19", "R20", "R21", "R22", "R23", "C12", "C13", "C14", "C15", "C16", "ENC1", "BZ1", "LED1", "PIX1-PIX4"],
           "connectors": {"C_PWR5": ["+5V_PROT", "GND"], "C_UI_D": ["GND", "LED_DATA", "BUZZ"], "C_UI_E": ["+3V3", "GND", "ENC_A", "ENC_B", "ENC_SW"], "C_PIX": ["+5V_PROT", "DIN_5V", "GND"]}},
}


class Schematic:
    def __init__(self, key):
        self.key = key
        self.fig, self.ax = plt.subplots(figsize=(16, 10), constrained_layout=True)
        self.ax.set_xlim(0, 100); self.ax.set_ylim(0, 70); self.ax.axis("off")
        card = CARDS[key]
        self.ax.text(2, 68, f"{key} · {card['title']}", fontsize=21, weight="bold", color=BLUE, va="top")
        self.ax.text(98, 68, f"PERFORADA {card['size_mm'][0]} × {card['size_mm'][1]} mm · paso 2,54 mm",
                     fontsize=10, color=GRAY, ha="right", va="top")
        self.ax.plot([2, 98], [64.8, 64.8], color=BLUE, lw=1.3)
        self.ax.text(2, 1.1, "Conectar por nombre de red y número de pin; comprobar continuidad antes de insertar módulos.",
                     fontsize=8.5, color=GRAY)

    def wire(self, pts, color=BLACK, lw=1.45):
        xs, ys = zip(*pts); self.ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="round", zorder=1)

    def node(self, x, y): self.ax.add_patch(Circle((x, y), .32, color=BLACK, zorder=5))

    def text(self, x, y, text, **kw):
        defaults = {"fontsize": 8.5, "color": BLACK, "ha": "center", "va": "center"}; defaults.update(kw)
        self.ax.text(x, y, text, **defaults)

    def net(self, x, y, text, color=GREEN, ha="left"):
        self.ax.text(x, y, text, fontsize=8.5, color=color, weight="bold", ha=ha, va="bottom")

    def resistor(self, x1, y, x2, ref, value):
        lead=1.7; self.wire([(x1,y),(x1+lead,y)]); self.wire([(x2-lead,y),(x2,y)])
        n=8; span=x2-x1-2*lead; pts=[]
        for i in range(n+1): pts.append((x1+lead+span*i/n, y+(1.0 if i%2 else -1.0)))
        self.wire(pts); self.text((x1+x2)/2,y+2.6,f"{ref}  {value}",fontsize=8)

    def resistor_v(self, x, y1, y2, ref, value):
        lead=1.7; self.wire([(x,y1),(x,y1+lead)]); self.wire([(x,y2-lead),(x,y2)])
        n=8; span=y2-y1-2*lead; pts=[]
        for i in range(n+1): pts.append((x+(1.0 if i%2 else -1.0), y1+lead+span*i/n))
        self.wire(pts); self.text(x+2.0,(y1+y2)/2,f"{ref}\n{value}",ha="left",fontsize=7.6)

    def capacitor_v(self, x, y_top, y_bottom, ref, value, polarized=False):
        ym=(y_top+y_bottom)/2; self.wire([(x,y_top),(x,ym+1.0)]); self.wire([(x,ym-1.0),(x,y_bottom)])
        self.ax.plot([x-1.5,x+1.5],[ym+1,ym+1],color=BLACK,lw=1.5)
        self.ax.plot([x-1.5,x+1.5],[ym-1,ym-1],color=BLACK,lw=1.5)
        if polarized:self.text(x+1.9,ym+1.8,"+",fontsize=10)
        self.text(x+2.0,ym,f"{ref}\n{value}",ha="left",fontsize=7.5)

    def diode(self, x1, y, x2, ref, value, cathode_right=True):
        mid=(x1+x2)/2; self.wire([(x1,y),(mid-2,y)]); self.wire([(mid+2,y),(x2,y)])
        if cathode_right:
            tri=[(mid-2,y-1.5),(mid-2,y+1.5),(mid+1,y)] ; bar=mid+1.4
        else:
            tri=[(mid+2,y-1.5),(mid+2,y+1.5),(mid-1,y)] ; bar=mid-1.4
        self.ax.add_patch(Polygon(tri, closed=True, fill=False, edgecolor=BLACK, lw=1.35)); self.ax.plot([bar,bar],[y-1.6,y+1.6],color=BLACK,lw=1.5)
        self.text(mid,y+2.8,f"{ref}  {value}",fontsize=7.8)

    def diode_v(self, x, y1, y2, ref, value, cathode_top=True):
        """Diodo vertical. y1 es el nodo inferior y y2 el superior."""
        mid=(y1+y2)/2
        self.wire([(x,y1),(x,mid-2)]); self.wire([(x,mid+2),(x,y2)])
        if cathode_top:
            tri=[(x-1.5,mid-2),(x+1.5,mid-2),(x,mid+1)]; bar=mid+1.4
        else:
            tri=[(x-1.5,mid+2),(x+1.5,mid+2),(x,mid-1)]; bar=mid-1.4
        self.ax.add_patch(Polygon(tri,closed=True,fill=False,edgecolor=BLACK,lw=1.35))
        self.ax.plot([x-1.6,x+1.6],[bar,bar],color=BLACK,lw=1.5)
        self.text(x+2.0,mid,f"{ref}\n{value}",ha="left",fontsize=7.2)

    def clamp(self, x, y, top_ref, bottom_ref):
        self.wire([(x,y),(x+4,y)]); self.node(x+4,y)
        self.diode(x+4,y,x+4,top_ref,"BAT85")

    def connector(self, x, y, name, pins, width=12, pin_pitch=3.3):
        h=max(7,len(pins)*pin_pitch+2); self.ax.add_patch(Rectangle((x,y-h/2),width,h,facecolor=LIGHT,edgecolor=BLUE,lw=1.1))
        self.text(x+width/2,y+h/2-1.3,name,color=BLUE,weight="bold",fontsize=8)
        coords=[]
        for i,p in enumerate(pins,1):
            py=y+h/2-3.3-(i-1)*pin_pitch; self.node(x,py); self.text(x+1.2,py,f"{i}  {p}",ha="left",fontsize=7.2); coords.append((x,py))
        return coords

    def ic(self,x,y,w,h,ref,value,pins_left=(),pins_right=()):
        self.ax.add_patch(Rectangle((x,y),w,h,facecolor=LIGHT,edgecolor=BLUE,lw=1.2)); self.text(x+w/2,y+h/2+1,ref,weight="bold",color=BLUE)
        self.text(x+w/2,y+h/2-1,value,fontsize=7.5,color=GRAY)
        left={};right={}
        for i,(p,n) in enumerate(pins_left):
            py=y+h-(i+1)*h/(len(pins_left)+1); self.node(x,py); self.text(x+1,py,f"{p} {n}",ha="left",fontsize=6.8);left[n]=(x,py)
        for i,(p,n) in enumerate(pins_right):
            py=y+h-(i+1)*h/(len(pins_right)+1); self.node(x+w,py); self.text(x+w-1,py,f"{n} {p}",ha="right",fontsize=6.8);right[n]=(x+w,py)
        return left,right

    def ground(self,x,y):
        self.wire([(x,y),(x,y-1.4)]); self.ax.plot([x-1.4,x+1.4],[y-1.4,y-1.4],color=BLACK,lw=1.3); self.ax.plot([x-.8,x+.8],[y-2.0,y-2.0],color=BLACK,lw=1.2)

    def notes(self, lines, title="MONTAJE Y PRUEBA"):
        x,y,w,h=78,6,20,56; self.ax.add_patch(Rectangle((x,y),w,h,facecolor="#fbfcfd",edgecolor=BLUE,lw=1))
        self.text(x+1,y+h-2,title,ha="left",weight="bold",color=BLUE,fontsize=9)
        yy=y+h-5
        for line in lines:
            self.ax.text(x+1.2,yy,"• "+line,fontsize=7.3,color=BLACK,ha="left",va="top",wrap=True)
            yy-=5.0 if len(line)<55 else 7.0


def rails(s, x1=3, x2=75, top=59, bottom=8, top_name="+3V3"):
    s.wire([(x1,top),(x2,top)],GREEN,1.7);s.net(x1,top+.8,top_name)
    s.wire([(x1,bottom),(x2,bottom)],BLACK,1.7);s.net(x1,bottom+.8,"GND",BLACK)


def draw_t1():
    s=Schematic("T1"); rails(s,4,74,top=55,bottom=12,top_name="+5V_PROT")
    p=s.connector(4,35,"J1 · ENTRADA 5 V",["VIN_5V","GND"],15)
    s.wire([(p[0][0],p[0][1]),(20,p[0][1])]); s.resistor(20,p[0][1],29,"F2","PTC 1,1 A")
    s.diode(29,p[0][1],39,"D1","1N5819");s.wire([(39,p[0][1]),(43,p[0][1]),(43,55)]);s.node(43,p[0][1])
    s.wire([(p[1][0],p[1][1]),(4,12)])
    s.capacitor_v(49,55,12,"C1","470 µF",True);s.capacitor_v(56,55,12,"C2","100 nF")
    for x,name in ((61,"C_PWR3"),(66,"C_PWR4"),(71,"C_PWR5")):
        s.wire([(x,55),(x,45)]);s.wire([(x,25),(x,12)]);s.ax.add_patch(Rectangle((x-2.1,25),4.2,20,facecolor=LIGHT,edgecolor=BLUE));s.text(x,42,name,fontsize=6.5,color=BLUE,weight="bold");s.text(x,36,"1 +5V",fontsize=6.2);s.text(x,30,"2 GND",fontsize=6.2)
    s.text(45,57,"TP1",ha="left",fontsize=7);s.text(45,10,"TP8",ha="left",fontsize=7)
    s.notes(["Usar cable 22 AWG para +5 V y GND.","Las tres salidas son ramas estrella independientes.","Primera prueba: fuente limitada a 100 mA.","Aceptar 5,0–5,25 V en cada salida.","No conectar aún T2–T5."])
    return s


def draw_t2():
    s=Schematic("T2"); rails(s,3,75,59,8)
    # VBIAS
    s.resistor_v(8,40,59,"R3","15 kΩ 1%") ; s.resistor_v(8,8,34,"R4","10 kΩ 1%")
    s.wire([(8,34),(8,40)]);s.node(8,37);s.net(9,37.5,"VBIAS")
    s.capacitor_v(13,37,8,"C7","10 µF",True);s.capacitor_v(17,37,8,"C8","100 nF");s.wire([(8,37),(17,37)])
    def channel(y,j,rbur,rbur_value,rser,cf,dlow,dhigh,out):
        pins=s.connector(20,y,j,["CT","NC","VBIAS"],10,2.8); ct=pins[0]; vb=pins[2]
        s.wire([(vb[0],vb[1]),(17,vb[1])]); s.net(17,vb[1]+.7,"VBIAS",ha="right")
        s.wire([(ct[0],ct[1]),(27,ct[1])]); s.node(27,ct[1])
        s.resistor(27,ct[1],37,rbur,rbur_value)
        s.wire([(37,ct[1]),(37,37),(17,37)])
        s.resistor(39,ct[1],50,rser,"3,3 kΩ 1%")
        s.wire([(27,ct[1]),(39,ct[1])]); s.node(50,ct[1]); s.net(51,ct[1]+.8,out)
        bias_y=37
        s.capacitor_v(54,max(ct[1],bias_y),min(ct[1],bias_y),cf,"47 nF 5%")
        s.wire([(50,ct[1]),(66,ct[1])]); s.wire([(54,bias_y),(17,bias_y)])
        s.diode_v(60,ct[1]-8,ct[1],dlow,"BAT85",cathode_top=True)
        s.net(60,ct[1]-8.8,"GND",BLACK,ha="center")
        s.diode_v(65,ct[1],ct[1]+8,dhigh,"BAT85",cathode_top=True)
        s.net(65,ct[1]+8.5,"+3V3",ha="center")
    channel(49,"J2 · SCT CH1","R1","22 Ω 1%","R5","C5","D3","D2","CH1_ADC")
    channel(24,"J3 · SCT CH2","R2","47 Ω 1%","R6","C6","D5","D4","CH2_ADC")
    cp=s.connector(69,34,"C_ADC_I",["+3V3","GND","CH1_ADC","CH2_ADC"],8.5,3.0)
    s.wire([(cp[0][0],cp[0][1]),(67,cp[0][1]),(67,59)])
    s.wire([(cp[1][0],cp[1][1]),(68,cp[1][1]),(68,8)])
    s.notes(["R1 y R2 se sueldan directamente en los jacks.","Nunca dejar una SCT-013-000 sin burden.","Sin pinzas: medir VBIAS = 1,32 V ±1 %.","Probar CH1 y CH2 por separado.","Mantener esta tarjeta lejos de Wi-Fi y NeoPixel."])
    return s


def draw_t3():
    s=Schematic("T3");rails(s,3,75,59,8)
    p=s.connector(4,39,"C_ZMPT / J5",["+5V_PROT","ZMPT_OUT","GND"],15)
    s.net(20,47,"Solo lado MBT del módulo",RED)
    s.wire([(p[1][0],p[1][1]),(27,p[1][1])]);s.resistor(27,p[1][1],39,"R7","11 kΩ 1%")
    y=p[1][1];s.wire([(39,y),(66,y)]);s.node(42,y);s.net(42,y+1,"V_ADC")
    s.resistor_v(47,8,y,"R8","13 kΩ 1%");s.capacitor_v(53,y,8,"C9","27 nF 5%")
    s.diode_v(59,8,y,"D7","BAT85",cathode_top=True)
    s.diode_v(64,y,59,"D6","BAT85",cathode_top=True)
    ca=s.connector(68,25,"C_ADC_V",["+3V3","GND","V_ADC"],9,3.1)
    pw=s.connector(68,50,"C_PWR3",["+5V_PROT","GND"],9,3.1)
    s.wire([(ca[0][0],ca[0][1]),(66,ca[0][1]),(66,59)])
    s.wire([(ca[1][0],ca[1][1]),(67,ca[1][1]),(67,8)])
    s.net(67,ca[2][1]+.7,"V_ADC",ha="right")
    s.notes(["J4, F1 y 120 V nunca van en esta perforada.","El ZMPT queda dentro de la guarda Z1.","Primero inyectar señal aislada alrededor de 2,5 V.","Verificar V_ADC dentro de 0,15–2,45 V.","Llevar V_ADC junto con su retorno GND."])
    return s


def draw_t4():
    s=Schematic("T4")
    s.ax.add_patch(Rectangle((1.5,65.2),56,3.1,facecolor="white",edgecolor="none",zorder=3))
    s.ax.text(2,68,"T4 · ESP32S USB-C y control",fontsize=21,weight="bold",color=BLUE,va="top",zorder=4)
    left,right=s.ic(29,15,22,43,"U1","ESP32S V1.1 USB-C · 38P",
        [("VIN","+5V"),("36","CH1_ADC"),("39","CH2_ADC"),("35","V_ADC"),("32","ENC_A"),("33","ENC_B"),("16","ENC_SW"),("26","SW1"),("27","SW2")],
        [("23","DIN"),("22","CS"),("21","DC"),("19","BL"),("18","CLK"),("4","RST"),("13","LED_DATA"),("14","BUZZ"),("25","LED_EST")])
    s.connector(4,52,"C_PWR4",["+5V_PROT","GND"],13)
    s.connector(4,35,"C_ADC_I",["+3V3","GND","CH1_ADC","CH2_ADC"],13,2.8)
    s.connector(4,18,"C_ADC_V",["+3V3","GND","V_ADC"],13,2.8)
    s.connector(58,50,"C_LCD",["VCC","GND","DIN","CS","DC","BL","CLK","RST"],17,2.7)
    s.connector(58,28,"C_UI_E",["+3V3","GND","ENC_A","ENC_B","ENC_SW"],17,2.7)
    s.connector(58,12,"C_UI_D",["GND","LED_DATA","BUZZ"],17,2.7)
    # clean labelled fanout rather than crossing wires
    for name,pt in {**left,**right}.items(): s.net(pt[0]+(-1 if pt[0]>50 else 1),pt[1]+.45,name,ha="right" if pt[0]>50 else "left")
    # buttons and indicators shown as local subcircuits
    s.ax.add_patch(Rectangle((17,6),38,7,facecolor="#fff",edgecolor=GRAY,lw=.8));s.text(18,11.3,"Panel local",ha="left",color=GRAY,fontsize=7.5)
    s.text(25,8.5,"SW1: GPIO26 · R12 10k ↑3V3 · C10 100n/GND",fontsize=6.7)
    s.text(45,8.5,"SW2: GPIO27 · R13 10k ↑3V3 · C11 100n/GND",fontsize=6.7)
    s.text(36,6.8,"D8 GPIO25/R11 330Ω · D9 +5V/R14 1k · D10 +3V3/R15 470Ω",fontsize=6.5)
    s.notes(["Usar dos zócalos hembra 1×19; no soldar el ESP32.","Confirmar 25,4 mm entre hileras antes de soldar.","Mantener libre el extremo de antena y el acceso USB-C.","Probar LCD y botones antes de conectar ADC.","GPIO34 queda como única reserva ADC."])
    return s


def draw_t5():
    s=Schematic("T5");rails(s,3,75,59,8,top_name="+5V_PROT")
    l,r=s.ic(27,29,22,25,"U3","74HCT245N DIP-20",
             [("1","DIR=+5V"),("2","A0 LED_DATA"),("3-9","A1-A7=GND"),("10","GND")],
             [("20","VCC +5V"),("19","/OE=GND"),("18","B0 DIN_5V"),("11-17","B1-B7 NC")])
    s.capacitor_v(53,59,8,"C14","100 nF");s.resistor_v(22,8,31,"R17","10 kΩ")
    s.resistor(49,r["B0 DIN_5V"][1],59,"R16","330 Ω");s.connector(63,45,"C_PIX",["+5V_PROT","DIN_5V","GND"],11,3.0)
    s.capacitor_v(59,59,8,"C16","680 µF",True)
    # Encoder box
    s.ax.add_patch(Rectangle((3,12),20,15,facecolor=LIGHT,edgecolor=BLUE));s.text(13,25,"ENC1 · EC11",weight="bold",color=BLUE)
    s.text(13,21.5,"A → GPIO32 · R19 10k ↑ · C12 10n ↓",fontsize=6.6);s.text(13,18.5,"B → GPIO33 · R20 10k ↑ · C13 10n ↓",fontsize=6.6);s.text(13,15.5,"SW → GPIO16 · R21 10k ↑ · C15 100n ↓",fontsize=6.6)
    # Piezo driver
    s.ax.add_patch(Rectangle((27,12),24,13,facecolor=LIGHT,edgecolor=BLUE));s.text(39,23,"DRIVER PIEZO",weight="bold",color=BLUE)
    s.text(39,19.2,"GPIO14 → R18 1k → base Q1",fontsize=7);s.text(39,16.5,"R22 10k base-GND · emisor GND",fontsize=7);s.text(39,13.8,"colector → BZ1(-); BZ1(+) → +5V",fontsize=7)
    s.connector(64,24,"C_UI_D",["GND","LED_DATA","BUZZ"],11,3.0)
    s.connector(64,12,"C_UI_E",["+3V3","GND","ENC_A","ENC_B","ENC_SW"],11,2.4)
    s.notes(["C14 debe quedar pegado a pines 20 y 10.","Probar primero un solo pixel con brillo limitado.","Confirmar el orden E/B/C del 2N2222 comprado.","C16 queda junto al conector de la tira.","No tender estos cables sobre T2 o T3."])
    return s


DRAW = {"T1":draw_t1,"T2":draw_t2,"T3":draw_t3,"T4":draw_t4,"T5":draw_t5}


def validate():
    issues=[]
    limits={"T1":[50,40],"T2":[70,55],"T3":[55,45],"T4":[80,65],"T5":[65,50]}
    for key,card in CARDS.items():
        if card["size_mm"]!=limits[key]:issues.append(f"tamaño inesperado {key}")
        for conn,pins in card["connectors"].items():
            if not pins or len(set(pins))!=len(pins):issues.append(f"pines inválidos {key}/{conn}")
        if any("120V" in p for pins in card["connectors"].values() for p in pins):issues.append(f"red en {key}")
    # Contratos entre tarjetas: mismo nombre y mismo orden en ambos extremos.
    for a,b,c in [("T1","T3","C_PWR3"),("T1","T4","C_PWR4"),("T1","T5","C_PWR5"),("T2","T4","C_ADC_I"),("T3","T4","C_ADC_V"),("T4","T5","C_UI_D"),("T4","T5","C_UI_E")]:
        if CARDS[a]["connectors"][c]!=CARDS[b]["connectors"][c]:issues.append(f"pinout distinto {c}: {a}/{b}")
    if issues:raise RuntimeError("; ".join(issues))
    return {"revision":"E.6-compacta","valid":True,"issues":[],"cards":CARDS,
            "safety":"J4, F1 y el primario del ZMPT101B permanecen en Z1; ninguna perforada lleva 120 V."}


def main():
    OUT.mkdir(parents=True,exist_ok=True); report=validate()
    with PdfPages(COMBINED) as combined:
        for key in CARDS:
            s=DRAW[key](); individual=OUT/f"{key}-{CARDS[key]['title'].lower().replace(' ','-').replace('/','-')}.pdf"
            s.fig.savefig(individual,bbox_inches="tight");s.fig.savefig(OUT/f"{key}.png",dpi=180,bbox_inches="tight")
            combined.savefig(s.fig,bbox_inches="tight");plt.close(s.fig)
    (OUT/"netlist-por-tarjeta.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(COMBINED)


if __name__=="__main__":main()
