"""Títulos, rótulos T1–T5 (graficos.ass) y subtítulos (subtitulos-es.srt) desde la línea de tiempo."""
from pathlib import Path
import json
import linea_tiempo as lt

p = Path(__file__).resolve().parent
T, D = lt.T, lt.DUR
seg = json.loads((p / 'seguimiento.json').read_text(encoding='utf-8'))
TITULOS = [
    (0.3, T['panel'], 'MEDIDOR E.7', 'CINCO TARJETAS MODULARES · RED SEGREGADA BAJO GUARDA PROPIA'),
    (T['panel'], T['verde'], 'INTERFAZ EMPOTRADA', 'LCD · PULSADORES · ENCODER · LED · PIEZO 44 mm · FCOB 200 mm'),
    (T['verde'], T['ambar'], 'VERDE · CONECTADO', 'FCOB: 4 SEGMENTOS DE 50 mm, UN SOLO COLOR · LED DE PANEL FIJO'),
    (T['ambar'], T['rojo'], 'ÁMBAR · SIN CONEXIÓN', 'LED DE PANEL A 1 Hz · LA BARRA NO PARPADEA'),
    (T['rojo'], T['normal'], 'ROJO · ALERTA SIN RECONOCER', 'LED DE PANEL A 5 Hz · DOS PITIDOS DEL PIEZO'),
    (T['normal'], T['interior'], 'TAPA CON CIERRE MAGNÉTICO', 'SIN BISAGRA NI TORNILLOS · ARNESES CON COCA DE HOLGURA'),
    (T['interior'], T['detalle'], 'CINCO TARJETAS PERFORADAS', 'T1–T5 SOBRE SEPARADORES M3 · ALIMENTACIÓN EN ESTRELLA'),
    (T['detalle'], T['red'], 'CONEXIONES', 'ESP32S V1.1 USB-C · JST-XH · BORNERAS · POTENCIÓMETROS DE AJUSTE'),
    (T['red'], T['cierra'][0] - .25, 'ZONA DE RED 120 V', 'TABIQUE Y GUARDA INDEPENDIENTE · AQUÍ MOSTRADA TRANSLÚCIDA'),
    (T['cierra'][0] - .25, D - .3, 'MEDIDOR E.7', 'VISUALIZACIÓN DE DISEÑO · NO VALIDA AISLAMIENTO NI CALIBRACIÓN'),
]


def ts(t, ass=False):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f'{h}:{m:02d}:{s:05.2f}' if ass else f'{h:02d}:{m:02d}:{s:06.3f}'.replace('.', ',')


ass = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 1920', 'PlayResY: 1080', '', '[V4+ Styles]',
       'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
       'Style: Title,DejaVu Sans,44,&H00FFFFFF,&H00FFFFFF,&H00101820,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,7,72,72,42,1',
       'Style: Sub,DejaVu Sans,25,&H00BFD0DA,&H00FFFFFF,&H00101820,&H00000000,0,0,0,0,100,100,0,0,1,1,0,7,72,72,98,1',
       'Style: Rotulo,DejaVu Sans,23,&H00FFFFFF,&H00FFFFFF,&H50201810,&H50201810,-1,0,0,0,100,100,0,0,3,5,0,5,0,0,0,1',
       '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
for a, b, titulo, sub in TITULOS:
    ass.append(f'Dialogue: 0,{ts(a, 1)},{ts(b - .04, 1)},Title,,0,0,0,,{titulo}')
    ass.append(f'Dialogue: 0,{ts(a, 1)},{ts(b - .04, 1)},Sub,,0,0,0,,{sub}')
for ref, r in sorted(seg['rotulos'].items()):
    ass.append(f"Dialogue: 1,{ts(T['interior'] + .35, 1)},{ts(T['detalle'] - .08, 1)},Rotulo,,0,0,0,,{{\\pos({r['x']:.0f},{r['y']:.0f})\\fad(200,0)}}{ref} · {r['rotulo']}")
(p / 'graficos.ass').write_text('\n'.join(ass) + '\n', encoding='utf-8')
srt = []
for s_ in lt.TIEMPOS['segments']:
    srt += [str(s_['id']), f"{ts(s_['start'])} --> {ts(s_['end'])}", s_['text'], '']
(p / 'subtitulos-es.srt').write_text('\n'.join(srt), encoding='utf-8')
print(len(TITULOS), 'títulos;', len(seg['rotulos']), 'rótulos')
