from pathlib import Path
import json
import hashlib
import numpy as np
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[4]
out=Path(__file__).resolve().parent
d=json.loads((root/'anims/rebuild_manifest.json').read_text(encoding='utf-8'))
names=json.loads((out/'geometry.json').read_text())
stats={}
original_donors={}
for n in ['basic1','basic2','basic3','happy2','excited1','sad1','sad2']:
 p=json.loads((root/f'anims/{n}_plan.json').read_text())
 original_donors[n]=list(dict.fromkeys([p['base']]+list(p['poses'].values())))
original_donors.update(idle1=['sprites/idle1_donor/donor_00.png','sprites/idle1_donor/donor_01.png'],happy1=['sprites/idle1_loop/idle1_loop_00.png','sprites/happy1_poses/happy1_pose_00.png','sprites/happy1_poses/happy1_pose_01.png'],talk=['sprites/idle1_donor/donor_00.png','sprites/talk_poses/talk_pose_00.png','sprites/talk_poses/talk_pose_01.png'])
for n,ps in original_donors.items():
 sh=Image.new('RGB',(512*len(ps),552),(53,53,53)); dr=ImageDraw.Draw(sh)
 for j,p in enumerate(ps):
  im=Image.open(root/p).convert('RGBA');sh.paste(im,(512*j,40),im);dr.text((512*j+4,8),p,fill='white')
 sh.save(out/f'{n}_original_donors.png')
idle=Image.open(root/'sprites/rebuilt/frames/idle1_loop/idle1_loop_00.png').convert('RGBA')
for c in d['clips']:
 if c['clip'] not in names: continue
 n=c['clip']; imgs=[Image.open(root/f'sprites/rebuilt/frames/{n}/{n}_{i:02}.png').convert('RGBA') for i in range(c['count'])]
 def diff(a,b):
  aa=np.asarray(a).astype(np.float32);bb=np.asarray(b).astype(np.float32)
  # Ignore arbitrary hidden RGB under alpha zero; compare premultiplied visible color and alpha.
  mask=(np.any(np.abs(aa[:,:,:3]*aa[:,:,3:4]/255-bb[:,:,:3]*bb[:,:,3:4]/255)>0.01,axis=2)) | (aa[:,:,3]!=bb[:,:,3]);ys,xs=np.where(mask)
  return {'pixels':int(mask.sum()),'bbox':None if not len(xs) else [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]}
 expected=c['sourceFrameHashes'];actual=[hashlib.sha256((root/p).read_bytes()).hexdigest() for p in c['frames']]
 stats[n]={'seam':diff(imgs[-1],imgs[0]),'idleEntry':diff(imgs[0],idle),'idleExit':diff(imgs[-1],idle),'sourceDuration':c['sourceDuration'],'fps':c.get('fps'),'rate':c['rate'],'holds':c['holds'],'repeats':c['repeats'],'originalHashesMatch':actual==expected}
 selected=[0,len(imgs)-1]
 if n=='happy1_loop': selected=[0,17]
 if n=='basic2_loop': selected=[0,2,4,17]
 if n=='boxing1_loop': selected=[0,1,2,4,5,6]
 if n=='excited1_loop': selected=[0,2,6,11,12,17]
 sheet=Image.new('RGB',(512*len(selected),552),(255,255,255));dr=ImageDraw.Draw(sheet)
 for j,i in enumerate(selected):
  sheet.paste(imgs[i],(j*512,40),imgs[i]);dr.text((j*512+10,8),f'{n} PNG {i:02}',fill=(0,0,0))
 sheet.save(out/f'{n}_details_white.png')
 # Face and coat enlargement on neutral poses, natural RGBA resampling retained.
 donor_paths=list(dict.fromkeys((c.get('donors') or {}).values()))
 if donor_paths:
  ds=Image.new('RGB',(512*len(donor_paths),552),(53,53,53)); dd=ImageDraw.Draw(ds)
  for j,p in enumerate(donor_paths):
   im=Image.open(root/p).convert('RGBA'); ds.paste(im,(j*512,40),im);dd.text((j*512+4,8),Path(p).name,fill='white')
  ds.save(out/f'{n}_donors.png')
(out/'seam_stats.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
anchors={}
for a,ai,b,bi in [('happy1_start',5,'happy1_loop',0),('happy1_loop',0,'happy1_end',0),('happy1_loop',17,'happy1_end',0)]:
 anchors[f'{a}_{ai:02} -> {b}_{bi:02}']=diff(Image.open(root/f'sprites/rebuilt/frames/{a}/{a}_{ai:02}.png').convert('RGBA'),Image.open(root/f'sprites/rebuilt/frames/{b}/{b}_{bi:02}.png').convert('RGBA'))
(out/'happy_anchors.json').write_text(json.dumps(anchors,indent=2),encoding='utf-8')
print(json.dumps(stats,indent=2))
