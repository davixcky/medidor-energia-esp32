from pathlib import Path
from PIL import Image
import subprocess,json
p=Path(__file__).resolve().parent
duration=json.loads((p/'tiempos.json').read_text())['duration']
assert all((p/'frames'/f'frame-{i:04d}.jpg').is_file() for i in range(1,duration*24+1)), 'Render incompleto'
# Fade the top behind labels for readable contrast during closeups.
im=Image.new('RGBA',(1920,1080),(0,0,0,0))
for y in range(240):
 alpha=round(150*max(0,1-y/240))
 im.paste((7,13,18,alpha),(0,y,1920,y+1))
im.save(p/'sombra-titulos.png')
ff=['ffmpeg','-y','-hide_banner','-framerate','24','-i',str(p/'frames/frame-%04d.jpg'),'-i',str(p/'audio/mezcla.wav'),'-loop','1','-i',str(p/'sombra-titulos.png'),'-i',str(p/'subtitulos-es.srt'),'-filter_complex',f"[0:v][2:v]overlay=0:0:shortest=1,ass='{p}/graficos.ass',fade=t=in:st=0:d=0.5,fade=t=out:st={duration-1}:d=1[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={duration-2}:d=2[a]",'-map','[v]','-map','[a]','-map','3:s','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-c:s','mov_text','-metadata:s:s:0','language=spa','-metadata:s:a:0','language=spa','-metadata','title=Medidor de energía ESP32 — Revisión B','-movflags','+faststart','-t',str(duration),str(p/'medidor-revB-audio.mp4')]
subprocess.run(ff,check=True)
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p/'medidor-revB-audio.mp4')]))
(p/'verificacion.json').write_text(json.dumps(info,indent=2))
assert any(s['codec_type']=='audio' for s in info['streams'])
v=next(s for s in info['streams'] if s['codec_type']=='video');assert (v['width'],v['height'])==(1920,1080)
assert abs(float(info['format']['duration'])-duration)<.1
