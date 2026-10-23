from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
p=Path(__file__).resolve().parent;root=p.parent.parent
with ZipFile(p/'medidor-revB-fabricacion.zip','w',ZIP_DEFLATED) as z:
 for f in p.rglob('*'):
  if not f.is_file() or 'render' in f.parts or f.suffix in ('.zip','.FCBak','.gcode') or f.name=='slicer.log':continue
  z.write(f,f.relative_to(p))
 for folder,patterns in [('freecad',['*.py']),('hardware/3d',['*.step','*.json']),('hardware',['encoder-conexiones.csv','revision-b-bom.csv']),('firmware',['platformio.ini','README.md']),('firmware/src',['*.cpp']),('firmware/include',['config.h','secretos.h.ejemplo']),('firmware/lib',['**/*.h','**/*.cpp']),('firmware/test',['*.cpp','*.py','Makefile','arduino/*.h'])]:
  for pattern in patterns:
   for f in (root/folder).glob(pattern):z.write(f,'fuentes/'+str(f.relative_to(root)))
print('Paquete actualizado:',p/'medidor-revB-fabricacion.zip')
