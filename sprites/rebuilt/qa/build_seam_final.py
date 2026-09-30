from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
import numpy as np
r=Path(__file__).resolve().parents[3];q=r/'sprites/rebuilt/qa/seam_final';q.mkdir(exist_ok=True)
raw=(r/'anims/rebuild_manifest.json').read_bytes();d=json.loads(raw);cs={c['clip']:c for c in d['clips']};h={'manifestSHA256':hashlib.sha256(raw).hexdigest(),'clips':{}}
def path(n,i,source=False):return r/cs[n]['frames'][i] if source else r/f'sprites/rebuilt/frames/{n}/{n}_{i:02}.png'
def drawcell(sh,dr,n,i,x,y,source):
 im=Image.open(path(n,i,source)).convert('RGBA').resize((160,160));sh.paste(im,(x,y+26),im);dr.text((x+3,y+3),f'{"O" if source else "F"} {n} {i:02}',fill='white')
loops=[n for n,c in cs.items() if c['part']=='loop']
for k in range(0,len(loops),5):
 ns=loops[k:k+5];sh=Image.new('RGB',(1920,len(ns)*200),(53,53,53));dr=ImageDraw.Draw(sh)
 for row,n in enumerate(ns):
  count=cs[n]['count'];inds=list(range(count-3,count))+[0,1,2]
  for j,i in enumerate(inds):
   for source in [True,False]:drawcell(sh,dr,n,i,(j+(0 if source else 6))*160,row*200,source)
 sh.save(q/f'loops_{k//5:02}.png')
edges=[('idle1_loop','happy1_start'),('happy1_start','happy1_loop'),('happy1_loop','happy1_end'),('happy1_end','idle1_loop'),('idle1_loop','pastry1_start'),('pastry1_start','pastry1_loop'),('pastry1_outro','idle1_loop'),('idle1_loop','chem1_start'),('chem1_start','chem1_loop')]
for i in range(1,11):edges.extend([('pastry1_loop',f'pastry1_end{i}'),(f'pastry1_end{i}','pastry1_outro')])
for i in range(1,4):edges.extend([('chem1_loop',f'chem1_end{i}'),(f'chem1_end{i}','idle1_loop')])
for n in loops:
 if n not in ['idle1_loop','happy1_loop','pastry1_loop','chem1_loop']:edges.extend([('idle1_loop',n),(n,'idle1_loop')])
for k in range(0,len(edges),8):
 es=edges[k:k+8];sh=Image.new('RGB',(1280,len(es)*205),(53,53,53));dr=ImageDraw.Draw(sh)
 for row,(a,b) in enumerate(es):
  frames=[(a,cs[a]['count']-2),(a,cs[a]['count']-1),(b,0),(b,1)]
  for j,(n,i) in enumerate(frames):
   for source in [True,False]:drawcell(sh,dr,n,i,(j+(0 if source else 4))*160,row*205,source)
 sh.save(q/f'edges_{k//8:02}.png')
for n,c in cs.items():
 h['clips'][n]={'candidateFrames':[hashlib.sha256(path(n,i).read_bytes()).hexdigest() for i in range(c['count'])],'sourceFrames':[hashlib.sha256(path(n,i,True).read_bytes()).hexdigest() for i in range(c['count'])],'sourceHashesMatchLedger':all(hashlib.sha256(path(n,i,True).read_bytes()).hexdigest()==c['sourceFrameHashes'][i] for i in range(c['count'])),'candidateVideoSHA256':hashlib.sha256((r/c['candidate']).read_bytes()).hexdigest()}
for a,b in edges:
 aa=np.array(Image.open(path(a,cs[a]['count']-1)).convert('RGBA')).astype(float);bb=np.array(Image.open(path(b,0)).convert('RGBA')).astype(float)
 mask=np.any(np.abs(aa[:,:,:3]*aa[:,:,3:4]/255-bb[:,:,:3]*bb[:,:,3:4]/255)>.01,axis=2)|(aa[:,:,3]!=bb[:,:,3])
 h.setdefault('boundaries',[]).append({'from':a,'to':b,'visibleChangedPixels':int(mask.sum())})
(q/'hash_binding.json').write_text(json.dumps(h,indent=2),encoding='utf-8')
print('clips',len(cs),'loops',len(loops),'edges',len(edges));print('exactEdges',[(e['from'],e['to']) for e in h['boundaries'] if not e['visibleChangedPixels']])
