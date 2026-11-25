from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
import json
p=Path(__file__).resolve().parent
w,h=A4;c=canvas.Canvas(str(p/'medidor-revB.pdf'),pagesize=A4)
c.setTitle('Medidor de energía — revisión B')
def text(x,y,s,size=10,color='#303b42'):
 c.setFillColor(HexColor(color));c.setFont('Helvetica',size);c.drawString(x,y,s)
def head(sub):
 text(36,h-40,'MEDIDOR DE ENERGÍA',21);text(36,h-61,sub,10)
 c.setStrokeColor(HexColor('#ccd3d6'));c.line(36,h-76,w-36,h-76)
def lines(y,rows):
 for row in rows:text(36,y,row);y-=17
 return y
head('Revisión B  /  PETG  /  Bambu Lab P2S')
c.drawImage(str(p/'3d-medidor-cerrado.png'),20,375,width=w-40,height=340,preserveAspectRatio=True,anchor='c',mask='auto')
y=lines(355,[
 'Tapa magnética · ocho imanes de 8 × 3 mm · esquinas de radio 10 mm.',
 'Encoder: pulsar para configurar brillo, sonido y umbral local.',
 'Barra difusa con cuatro NeoPixels y soporte desmontable.',
 'Piezo oculto: pulsaciones breves y dos tonos por alerta nueva.',
 'Mantener VISTA dos segundos activa o desactiva el sonido.',
 'Guarda de red atornillada, independiente de la tapa magnética.',
 '',
 'Color de la barra',
 'Verde: envío reciente. Ámbar: sin envío confirmado. Rojo: alerta.',
 '',
 'Antes de imprimir el gabinete',
 'Imprimir el cupón y medir imanes, pulsadores y piezo reales.',
 'Cupón: aproximadamente 37 minutos y 22 g de PETG.',
 'Perfil: boquilla 0,4 mm, capa 0,20 mm, cuatro paredes, PEI texturizado.',
 '',
 'Validado: compilación, pruebas de lógica, mallas y laminado.',
 'Pendiente: montaje físico, alimentación, ruido ADC y prueba térmica.'
])
text(36,30,'Vista CAD con pantalla de prueba; cifras ilustrativas, no mediciones físicas.',8)
c.showPage();head('Conexiones auxiliares  /  montaje en baja tensión')
lines(h-105,[
 'NeoPixels: GPIO13 a 74AHCT125; salida a DIN mediante 330 ohm.',
 'Alimentación: TP1 (+5 V protegido) y TP9 (GND). No usar 3,3 V.',
 '680 uF / 10 V junto a la tira y 100 nF junto al 74AHCT125.',
 '74AHCT125: 14 = +5 V, 7 = GND, 1 = GND, 2 = GPIO13, 3 = salida.',
 'Entradas 5/9/12 a GND; habilitaciones 4/10/13 a +5 V.',
 'Salidas 6/8/11 sin conectar; resistencia de 10 kohm GPIO13-GND.',
 'Comprobar 4,5–5,5 V en el integrado durante transmisión Wi-Fi.',
 '',
 'Piezo pasivo: GPIO14 a base de NPN mediante 1 kohm.',
 '10 kohm base-emisor. Emisor a GND, colector al negativo del piezo.',
 'Positivo del piezo a +5 V protegido. Confirmar el patillaje del NPN.',
 'Asiento nominal para piezo de diámetro 12 mm y altura 7 mm.',
 '',
 'La PCB principal no incluye estos drivers: requieren placa auxiliar.',
 'Fijar esa placa y aislar sus soldaduras; definir soporte según su tamaño.',
 'Primera prueba con fuente aislada, sin conectar 120 V.',
 'Comprobar caída de tensión, interferencia en ADC y temperatura.',
 '',
 'Archivos de fabricación',
 'USB-C: abertura 18 × 10 mm; confirmar placa y cable antes del cuerpo.',
 'El STEP aún usa DevKitC Micro-USB: centro de conexión provisional.',
 'stl/ : diez piezas y cupones de ajuste, USB-C y encoder.',
 'p2s-petg/ : proyectos 3MF separados y resultados del laminado.',
 'medidor-revB.FCStd / .step : ensamble editable e intercambio CAD.',
 'LEER-ANTES-DE-IMPRIMIR.txt : materiales y detalles de conexión.'
])
text(36,230,'Referencias del circuito',11)
for label,url,y in [('Adafruit: NeoPixel Best Practices','https://learn.adafruit.com/adafruit-neopixel-uberguide/best-practices',209),('Texas Instruments: SN74AHCT125','https://www.ti.com/product/SN74AHCT125',188)]:
 text(36,y,label,10,'#176b69');c.linkURL(url,(36,y-2,400,y+12),relative=0)
text(36,30,'No cargar a la impresora sin revisar el cupón y el material real.',8)
c.save()
