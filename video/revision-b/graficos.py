from pathlib import Path
import json,textwrap
p=Path(__file__).resolve().parent;tim=json.loads((p/'tiempos.json').read_text());segments=tim['segments']
def stamp(t):
 cs=round(t*100);return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'
header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,DejaVu Sans,48,&H00F4F6F7,&H00FFFFFF,&H00121A20,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,72,72,50,1
Style: Detail,DejaVu Sans,27,&H00CBD1D5,&H00FFFFFF,&H00121A20,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,72,72,115,1
Style: Foot,DejaVu Sans,21,&H00AAB6BF,&H00FFFFFF,&H00121A20,&H00000000,0,0,0,0,100,100,0,0,1,0,0,1,72,72,42,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
rows=[('MEDIDOR DE ENERGÍA','ESP32 · Revisión B · Diseño para fabricación'),('TAPA MAGNÉTICA','PETG · Esquinas R10 · Guarda interior atornillada'),('AJUSTES AL GIRAR','Encoder con pulsador · Brillo · Sonido · Alerta local'),('LUZ Y SONIDO','4 NeoPixels · Avisos breves · VISTA 2 s para silenciar'),('ACCESO USB-C','Abertura 18 × 10 mm · Posición por verificar con la placa real'),('SIGUIENTE PASO','Cupones de ajuste → montaje → pruebas en banco')]
def event(start,end,style,body,layer=1):return f'Dialogue: {layer},{stamp(start)},{stamp(end)},{style},,0,0,0,,{body}\n'
ass=header
for i,((title,detail),seg) in enumerate(zip(rows,segments)):
 start=0 if i==0 else seg['start']-.4;end=segments[i+1]['start']-.4 if i<5 else tim['duration']
 ass+=event(start,end,'Title',r'{\fad(300,200)}'+title)
 ass+=event(start,end,'Detail',r'{\fad(350,200)}'+detail)
 ass+=event(start,end,'Detail',r'{\an9\pos(1848,60)\fs23\fad(300,200)}'+f'{i+1:02} / 06')
 ass+=event(start,end,'Detail',r'{\an7\pos(72,165)\p1\bord0\1c&H75B85C&\fad(300,200)}m 0 0 l 100 0 100 3 0 3'+r'{\p0}',0)
ass+=event(0,tim['duration'],'Foot','VISUALIZACIÓN CAD  /  Interfaz con datos de prueba')
# Color legend is tied to the same simulated states as the light bar animation.
for offset,end,label,color in [(0,3,'● CONECTADO','75B85C'),(3,5,'● SIN ENVÍO','3DA3E8'),(5,8.5,'● ALERTA','2E3AE0')]:
 st=segments[3]['start']+offset
 ass+=event(st,min(segments[3]['start']+end,segments[4]['start']-.4),'Detail',r'{\an3\pos(1848,1038)\fs25\1c&H'+color+r'&\fad(120,120)}'+label)
(p/'graficos.ass').write_text(ass)
def srtstamp(t):return (stamp(t).replace('.',',')+'0').zfill(12)
srt=[];n=1
for seg in segments:
 chunks=textwrap.wrap(seg['text'],width=100,break_long_words=False)
 total=sum(map(len,chunks));at=seg['start']
 for chunk in chunks:
  end=at+(seg['end']-seg['start'])*len(chunk)/total
  srt.append(f'{n}\n{srtstamp(at)} --> {srtstamp(end)}\n'+ '\n'.join(textwrap.wrap(chunk,width=52))+'\n');n+=1;at=end
(p/'subtitulos-es.srt').write_text('\n'.join(srt))
