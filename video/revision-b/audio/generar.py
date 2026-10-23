from pathlib import Path
import json,math
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
p=Path(__file__).resolve().parent
k=Kokoro(str(Path.home()/'.cache/hyperframes/tts/models/kokoro-v1.0.onnx'),str(Path.home()/'.cache/hyperframes/tts/voices/voices-v1.0.bin'))
segments=[];at=1.2;sr=24000
for i,line in enumerate(p.joinpath('narracion.txt').read_text().splitlines()):
 if not line.strip():continue
 audio,sr=k.create(line,voice='ef_dora',lang='es',speed=1.03)
 sf.write(p/f'voz-{i+1}.wav',audio,sr)
 duration=len(audio)/sr;segments.append(dict(id=i+1,start=round(at,3),end=round(at+duration,3),text=line));at+=duration+1.0
length=math.ceil(at+1);mix=np.zeros((length*sr,2),dtype=np.float32)
for seg in segments:
 audio,_=sf.read(p/f"voz-{seg['id']}.wav");start=round(seg['start']*sr)
 mix[start:start+len(audio)]+=audio[:,None]*.80
# Original quiet tonal bed, no licensed recording; soft partials and long release.
t=np.arange(length*sr)/sr;bed=np.zeros_like(t)
for beat in np.arange(0,length,2.5):
 for f in [(130.8128,164.8138,195.9977),(110,130.8128,164.8138),(87.3071,130.8128,174.6141),(97.9989,146.8324,195.9977)][int(beat//5)%4]:
  dt=t-beat;env=np.where(dt>=0,(1-np.exp(-np.maximum(dt,0)*3))*np.exp(-np.maximum(dt,0)/2.7),0)
  bed+=.008*env*(np.sin(2*np.pi*f*dt)+.2*np.sin(2*np.pi*2*f*dt))
for beat,note in enumerate([261.63,329.63,392,329.63,293.66,392,329.63,261.63]*5):
 dt=t-beat*1.25
 env=np.where(dt>=0,(1-np.exp(-np.maximum(dt,0)*25))*np.exp(-np.maximum(dt,0)*2),0)
 bed+=.009*env*np.sin(2*np.pi*note*dt)
bed*=np.minimum(t/2,1)*np.minimum((length-t)/2,1)
mix+=bed[:,None]
# Two quiet piezo demonstration tones near the end of the feedback scene.
beep_start=segments[3]['end']+.1
for offset in [0,.16]:
 start=round((beep_start+offset)*sr);n=round(.08*sr);bt=np.arange(n)/sr
 tone=.055*np.sin(2*np.pi*2400*bt)*np.minimum(bt/.006,1)*np.minimum((.08-bt)/.006,1)
 mix[start:start+n]+=tone[:,None]
# Tiny soft clicks on chapter changes.
for seg in segments[1:]:
 start=round((seg['start']-.15)*sr);ct=np.arange(round(.045*sr))/sr
 click=.025*np.sin(2*np.pi*800*ct)*np.exp(-ct*110)
 mix[start:start+len(ct)]+=click[:,None]
sf.write(p/'mezcla.wav',mix,sr)
(p.parent/'tiempos.json').write_text(json.dumps(dict(duration=length,fps=24,segments=segments),ensure_ascii=False,indent=2))
print(length,segments,flush=True)
