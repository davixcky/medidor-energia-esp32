from pathlib import Path
import json
p=Path(__file__).resolve().parent;tim=json.loads((p/'tiempos.json').read_text());segs=tim['segments']
titles=[('MEDIDOR E.7','CINCO TARJETAS MODULARES'),('INTERFAZ EMPOTRADA','LCD · ENCODER · PIEZO 44 mm · FCOB 12 V'),('ESTADOS REALES','VERDE CONECTADO · ÁMBAR SIN RED · ROJO ALERTA'),('INTERIOR ACCESIBLE','BORNERAS · JST · POTENCIÓMETROS · ESP32S USB-C'),('RED SEGREGADA','GUARDA INDEPENDIENTE · VALIDACIÓN CON GABINETE CERRADO')]
def ts(t,ass=False):
    h=int(t//3600);m=int(t%3600//60);s=t%60
    return f'{h}:{m:02d}:{s:05.2f}' if ass else f'{h:02d}:{m:02d}:{s:06.3f}'.replace('.',',')
ass=['[Script Info]','ScriptType: v4.00+','PlayResX: 1920','PlayResY: 1080','[V4+ Styles]',
'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
'Style: Title,DejaVu Sans,44,&H00FFFFFF,&H00FFFFFF,&H00101820,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,7,72,72,42,1',
'Style: Sub,DejaVu Sans,25,&H00BFD0DA,&H00FFFFFF,&H00101820,&H00000000,0,0,0,0,100,100,0,0,1,1,0,7,72,72,98,1','[Events]',
'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
srt=[]
for i,(seg,(title,sub)) in enumerate(zip(segs,titles),1):
    ass.append(f"Dialogue: 0,{ts(seg['start'],1)},{ts(seg['end'],1)},Title,,0,0,0,,{title}")
    ass.append(f"Dialogue: 0,{ts(seg['start'],1)},{ts(seg['end'],1)},Sub,,0,0,0,,{sub}")
    srt += [str(i),f"{ts(seg['start'])} --> {ts(seg['end'])}",seg['text'],'']
(p/'graficos.ass').write_text('\n'.join(ass)+'\n')
(p/'subtitulos-es.srt').write_text('\n'.join(srt))
