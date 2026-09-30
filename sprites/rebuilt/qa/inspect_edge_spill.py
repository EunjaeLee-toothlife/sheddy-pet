"""Read-only candidate PNG edge-spill measurements and QA composites."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label, binary_dilation

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'sprites/rebuilt/qa/edge_spill'
OUT.mkdir(exist_ok=True)
raw=(ROOT/'anims/rebuild_manifest.json').read_bytes()
data=json.loads(raw)
records=[]
for c in data['clips']:
    if c['clip']=='chem1_end3':continue
    for p in sorted((ROOT/'sprites/rebuilt/frames'/c['clip']).glob('*.png')):
        im=Image.open(p).convert('RGBA');a=np.array(im).astype(np.int16)
        alpha=a[:,:,3];excess=a[:,:,1]-np.maximum(a[:,:,0],a[:,:,2])
        mask=(alpha>0)&(alpha<100)&(excess>20)
        visible=excess*alpha/255
        strong=mask&(visible>8)
        # Exterior contour vs enclosed green objects: explicit counts only,
        # classification still requires viewing the native image.
        void,number=label(alpha==0)
        border_ids=np.unique(np.concatenate([void[0],void[-1],void[:,0],void[:,-1]]))
        exterior=np.isin(void,border_ids[border_ids!=0])
        external=mask&binary_dilation(exterior,iterations=2)
        yy,xx=np.where(mask)
        records.append({'clip':c['clip'],'frame':p.name,'file':p.relative_to(ROOT).as_posix(),
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'count':int(mask.sum()),
            'externalCount':int(external.sum()),'weightedAbove3':int((mask&(visible>3)).sum()),
            'weightedAbove8':int(strong.sum()),'maxWeightedGreenExcess':round(float(visible[mask].max()),3) if mask.any() else 0,
            'bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)] if len(xx) else None})
summary=[]
for c in data['clips']:
    rows=[r for r in records if r['clip']==c['clip']]
    if not rows:continue
    worst=max(rows,key=lambda r:(r['weightedAbove8'],r['count']))
    summary.append({'clip':c['clip'],'frames':len(rows),'affectedFrames':sum(r['count']>0 for r in rows),
        'minCount':min(r['count'] for r in rows),'maxCount':max(r['count'] for r in rows),
        'totalCount':sum(r['count'] for r in rows),'maxAbove8':max(r['weightedAbove8'] for r in rows),
        'worst':worst['frame'],'worstFile':worst['file']})
result={'manifestSha256':hashlib.sha256(raw).hexdigest(),'criterion':'0 < alpha < 100 and G - max(R,B) > 20; RGB excess weighted by alpha/255 approximates actual composite green contribution.','clips':summary,'frames':records}
(OUT/'measurements.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
worst_clips=sorted(summary,key=lambda r:(r['maxAbove8'],r['maxCount']),reverse=True)[:12]
for offset in range(0,len(worst_clips),4):
    group=worst_clips[offset:offset+4]
    sheet=Image.new('RGB',(1024,len(group)*540),(128,128,128));draw=ImageDraw.Draw(sheet)
    for row,r in enumerate(group):
        im=Image.open(ROOT/r['worstFile']).convert('RGBA')
        for col,bg in enumerate([(255,255,255,255),(24,29,38,255)]):
            comp=Image.alpha_composite(Image.new('RGBA',(512,512),bg),im).convert('RGB')
            sheet.paste(comp,(col*512,row*540))
        draw.text((8,row*540+515),r['clip']+'/'+r['worst']+' count='+str(r['maxCount'])+' above8='+str(r['maxAbove8']),fill=(0,0,0))
    sheet.save(OUT/f'native_white_dark_{offset//4+1}.png')
print(json.dumps(summary,indent=2))
