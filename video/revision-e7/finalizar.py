from pathlib import Path
from PIL import Image
import subprocess,json
p=Path(__file__).resolve().parent;tim=json.loads((p/'tiempos.json').read_text());duration=tim['duration'];fps=tim['fps']
assert all((p/'frames'/f'frame-{i:04d}.jpg').is_file() for i in range(1,duration*fps+1)), 'Render incompleto'
out=p/'medidor-E7-producto.mp4'
ff=['ffmpeg','-y','-hide_banner','-framerate',str(fps),'-i',str(p/'frames/frame-%04d.jpg'),'-i',str(p/'audio/mezcla.wav'),'-i',str(p/'subtitulos-es.srt'),
    '-filter_complex',f"[0:v]drawbox=x=0:y=0:w=iw:h=155:color=0x081018@0.50:t=fill,ass='{p}/graficos.ass',fade=t=in:st=0:d=0.4,fade=t=out:st={duration-1}:d=1[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={duration-2}:d=2[a]",
    '-map','[v]','-map','[a]','-map','2:s','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-c:s','mov_text','-metadata:s:s:0','language=spa','-metadata:s:a:0','language=spa','-metadata','title=Medidor de energía ESP32 — E.7','-movflags','+faststart','-t',str(duration),str(out)]
subprocess.run(ff,check=True)
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]))
(p/'verificacion.json').write_text(json.dumps(info,indent=2))
v=next(s for s in info['streams'] if s['codec_type']=='video');assert (v['width'],v['height'])==(1920,1080)
assert any(s['codec_type']=='audio' for s in info['streams']);assert abs(float(info['format']['duration'])-duration)<.1
print(out)
