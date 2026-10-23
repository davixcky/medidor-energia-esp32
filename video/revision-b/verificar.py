from pathlib import Path
from PIL import Image
import subprocess,json
p=Path(__file__).resolve().parent;movie=p/'medidor-revB-audio.mp4'
tim=json.loads((p/'tiempos.json').read_text());sheet=Image.new('RGB',(1440,1215))
for i,seg in enumerate(tim['segments']):
 out=p/f'final-{i+1}.png';t=(seg['start']+seg['end'])/2
 subprocess.run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(movie),'-frames:v','1',str(out)],check=True)
 sheet.paste(Image.open(out).resize((720,405)),((i%2)*720,(i//2)*405))
sheet.save(p/'contacto-final.png')
with (p/'verificacion-decodificacion.log').open('w') as f:
 subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-map','0:v','-map','0:a','-f','null','-'],stdout=f,stderr=subprocess.STDOUT,check=True)
with (p/'verificacion-audio.log').open('w') as f:
 subprocess.run(['ffmpeg','-hide_banner','-i',str(movie),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],stdout=f,stderr=subprocess.STDOUT,check=True)
print('Final contact sheet and decode/audio checks complete')
