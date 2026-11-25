from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
p=Path(__file__).resolve().parent
with ZipFile(p/'medidor-revB-video-fuentes.zip','w',ZIP_DEFLATED) as z:
 for f in p.rglob('*'):
  if not f.is_file() or 'frames' in f.parts:continue
  if f.name in ('base.blend','narracion.wav','contacto.png') or f.suffix in ('.zip','.mp4','.blend1'):continue
  if f.name.startswith(('preview-','final-')):continue
  z.write(f,'video-revision-b/'+str(f.relative_to(p)))
print('Video source archive created')
