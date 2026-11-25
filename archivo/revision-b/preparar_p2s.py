"""Resolve installed P2S profiles and slice each part on its own plate. Never sends jobs."""
from pathlib import Path
import json,subprocess
here=Path(__file__).resolve().parent
root=Path('/opt/bambustudio-bin/resources/profiles/BBL')
out=here/'p2s-petg';out.mkdir(exist_ok=True)
def resolve(kind,name):
 d=json.loads((root/kind/(name+'.json')).read_text());parent=d.pop('inherits',None)
 if parent:
  p=resolve(kind,parent);p.update(d);d=p
 return d
for kind,name in [('machine','Bambu Lab P2S 0.4 nozzle'),('process','0.20mm Standard @BBL P2S'),('filament','Generic PETG @BBL P2S')]:
 d=resolve(kind,name)
 if kind=='process':d.update(wall_loops='4',sparse_infill_density='20%',enable_support='0',curr_bed_type='Textured PEI Plate')
 (out/(kind+'.json')).write_text(json.dumps(d,indent=2))
summary=[]
for stl in sorted((here/'stl').glob('*.stl')):
 dest=out/stl.stem;dest.mkdir(exist_ok=True)
 cmd=['bambu-studio','--load-settings',str(out/'machine.json')+';'+str(out/'process.json'),'--load-filaments',str(out/'filament.json'),'--arrange','1','--ensure-on-bed','--export-3mf',stl.stem+'-p2s-petg.3mf','--slice','0','--outputdir',str(dest),str(stl)]
 with (dest/'slicer.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 r=json.loads((dest/'result.json').read_text());assert r['return_code']==0,r
 plate=r['sliced_plates'][0]
 summary.append(dict(part=stl.stem,seconds=plate['total_predication'],grams=sum(f['total_used_g'] for f in plate['filaments']),warning=plate['warning_message']))
 print(summary[-1],flush=True)
(out/'resumen.json').write_text(json.dumps(summary,indent=2))
