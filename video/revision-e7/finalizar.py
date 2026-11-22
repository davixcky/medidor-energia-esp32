"""Une fotogramas, gráficos, audio y subtítulos en medidor-E7-producto.mp4 (H.264 + AAC + mov_text)."""
from pathlib import Path
import subprocess
import linea_tiempo as lt

p = Path(__file__).resolve().parent
dur, fps = lt.DUR, lt.FPS
assert all((p / 'frames' / f'frame-{i:04d}.jpg').is_file() for i in range(1, lt.FRAMES + 1)), 'Render incompleto'
out = p / 'medidor-E7-producto.mp4'
video = (f"[0:v]scale=in_range=full:out_range=tv,format=yuv420p,drawbox=x=0:y=0:w=iw:h=155:color=0x081018@0.55:t=fill,"
         f"ass='{p}/graficos.ass',fade=t=in:st=0:d=0.4,fade=t=out:st={dur - .5}:d=0.5[v]")
audio = f"[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={dur - 1.5}:d=1.5[a]"
subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-framerate', str(fps), '-i', str(p / 'frames/frame-%04d.jpg'),
                '-i', str(p / 'audio/mezcla.wav'), '-i', str(p / 'subtitulos-es.srt'), '-filter_complex', video + ';' + audio,
                '-map', '[v]', '-map', '[a]', '-map', '2:s', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                '-color_range', 'tv', '-frames:v', str(lt.FRAMES), '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-c:s', 'mov_text',
                '-metadata:s:s:0', 'language=spa', '-metadata:s:a:0', 'language=spa', '-metadata', 'title=Medidor de energía ESP32 — E.7',
                '-movflags', '+faststart', '-t', str(dur), str(out)], check=True)
print(out)
