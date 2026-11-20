from pathlib import Path
import json, math
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

p=Path(__file__).resolve().parent
k=Kokoro(str(Path.home()/'.cache/hyperframes/tts/models/kokoro-v1.0.onnx'),
         str(Path.home()/'.cache/hyperframes/tts/voices/voices-v1.0.bin'))
segments=[];at=1.0;sr=24000
for i,line in enumerate(p.joinpath('narracion.txt').read_text().splitlines()):
    if not line.strip(): continue
    audio,sr=k.create(line,voice='ef_dora',lang='es',speed=1.03)
    sf.write(p/f'voz-{i+1}.wav',audio,sr)
    duration=len(audio)/sr
    segments.append(dict(id=i+1,start=round(at,3),end=round(at+duration,3),text=line))
    at+=duration+.85
length=math.ceil(at+1.0);mix=np.zeros((length*sr,2),dtype=np.float32)
for seg in segments:
    audio,_=sf.read(p/f"voz-{seg['id']}.wav");start=round(seg['start']*sr)
    mix[start:start+len(audio)]+=audio[:,None]*.80
# Cama original tenue, conservada como parte del flujo reproducible del proyecto.
t=np.arange(length*sr)/sr;bed=np.zeros_like(t)
chords=[(110,146.83,196),(98,130.81,174.61),(87.31,130.81,164.81),(98,146.83,196)]
for beat in np.arange(0,length,3.0):
    for f in chords[int(beat//6)%4]:
        dt=t-beat;env=np.where(dt>=0,(1-np.exp(-np.maximum(dt,0)*3))*np.exp(-np.maximum(dt,0)/3.2),0)
        bed+=.007*env*(np.sin(2*np.pi*f*dt)+.16*np.sin(2*np.pi*2*f*dt))
bed*=np.minimum(t/2,1)*np.minimum((length-t)/2,1);mix+=bed[:,None]
# Piezo solamente cuando aparece el estado de alerta.
alert=segments[2]['start']+4.5
for offset in (0,.18):
    start=round((alert+offset)*sr);n=round(.085*sr);bt=np.arange(n)/sr
    tone=.05*np.sin(2*np.pi*2400*bt)*np.minimum(bt/.006,1)*np.minimum((.085-bt)/.006,1)
    mix[start:start+n]+=tone[:,None]
sf.write(p/'mezcla.wav',mix,sr)
(p.parent/'tiempos.json').write_text(json.dumps(dict(duration=length,fps=24,segments=segments),ensure_ascii=False,indent=2))
print(length,segments)
