"""Register generated doze poses using shoes, preserving nod height and head sway."""
from pathlib import Path
import numpy as np
import sys
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
def footprint(im):
    a=np.asarray(im).astype(float)
    y=np.indices(a.shape[:2])[0]
    mask=(a[:,:,3]>200)&(y>420)&(a[:,:,0]>a[:,:,1]*1.18)&(a[:,:,1]>a[:,:,2]*1.05)&(a[:,:,0]<190)
    ys,xs=np.where(mask)
    return int(xs.min()),int(xs.max())+1
base=Image.open(ROOT/'sprites/rebuilt/poses/idle_open_00.png').convert('RGBA')
bl,br=footprint(base)
target_bottom=base.getbbox()[3]
records=[]
clip=sys.argv[1] if len(sys.argv)>1 else 'doze1_loop'
assert clip in ('doze1_loop','lemon1_loop','chem1_loop','chem1_start','chem1_end1')
count={'doze1_loop':14,'lemon1_loop':16,'chem1_loop':19,'chem1_start':12,'chem1_end1':20}[clip]
for index in range(count):
    source=index if clip!='doze1_loop' or index<12 else 0
    group=source//4
    batch=clip+'_'+ '-'.join(f'{j:02d}' for j in range(group*4,min(group*4+4,count)))
    donor=ROOT/'sprites/rebuilt/poses/batches'/batch/f'cell_{source%4:02d}.png'
    overrides={('chem1_loop',10):'chem1_opposite_00.png',
               ('chem1_loop',13):'chem1_swirl_opposite_00.png',
               ('chem1_end1',15):'chem1_crosswipe_00.png',
               ('chem1_end1',18):'chem1_finalhide_00.png'}
    if (clip,index) in overrides:
        donor=ROOT/'sprites/rebuilt/poses'/overrides[(clip,index)]
    im=Image.open(donor).convert('RGBA')
    left,right=footprint(im)
    scale=(br-bl)/(right-left)
    if clip!='doze1_loop':
        # These standing gestures never nod or crouch; use body height to
        # preserve canonical proportions despite generated shoe separation.
        a=np.asarray(im)
        yy,xx=np.indices(a.shape[:2])
        center=(left+right)/2
        hair=(a[:,:,3]>220)&(yy<180)&(abs(xx-center)<72)&(a[:,:,0]>200)&(a[:,:,1]>140)&(a[:,:,2]<175)
        crown=np.where(hair)[0].min()
        if clip=='chem1_end1' and index==3:
            # Poof hides the crown; adjacent frame has the same anatomy.
            previous=Image.open(ROOT/'sprites/rebuilt/poses/batches'/batch/'cell_02.png').convert('RGBA')
            pa=np.asarray(previous)
            pm=(pa[:,:,3]>220)&(yy<180)&(abs(xx-center)<72)&(pa[:,:,0]>200)&(pa[:,:,1]>140)&(pa[:,:,2]<175)
            crown=np.where(pm)[0].min()
        scale=(target_bottom-47)/(im.getbbox()[3]-crown+2)
        if clip=='chem1_end1':
            # Retain smoke and detached puffs while keeping a 15px canvas margin.
            bbox=im.getbbox()
            scale=min(scale,483/(bbox[3]-bbox[1]))
    scaled=im.resize((round(512*scale),round(512*scale)),Image.Resampling.LANCZOS)
    dx=round((bl+br)/2-(left+right)*scale/2)
    dy=target_bottom-scaled.getbbox()[3]
    out=Image.new('RGBA',(512,512))
    out.alpha_composite(scaled,(dx,dy))
    if clip=='lemon1_loop' and index in (0,15):
        out=base.copy()
    if clip=='chem1_start' and index==0:
        out=base.copy()
    if clip=='chem1_start' and index==11:
        out=Image.open(ROOT/'sprites/rebuilt/poses/chem1_base_00.png').convert('RGBA')
    if clip=='chem1_end1' and index==0:
        out=Image.open(ROOT/'sprites/rebuilt/poses/chem1_base_00.png').convert('RGBA')
    if clip=='chem1_end1' and index==19:
        out=base.copy()
    path=ROOT/'sprites/rebuilt/frames'/clip/f'{clip}_{index:02d}.png'
    out.save(path)
    records.append({'frame':index,'sourceCell':source,'donor':donor.relative_to(ROOT).as_posix(),'scale':scale,'dx':dx,'dy':dy,'bbox':list(out.getbbox())})
if clip=='chem1_loop':
    from shutil import copyfile
    folder=ROOT/'sprites/rebuilt/frames'/clip
    copyfile(folder/'chem1_loop_00.png',folder/'chem1_loop_18.png')
    records[-1]['sourceCell']=0
    records[-1]['bbox']=records[0]['bbox']
    records[-1]['exactLoopCloser']=True
import json
method='canonical shoe width, foot center and baseline; head height is not used for scaling' if clip=='doze1_loop' else 'canonical standing body height from hair crown, foot center and baseline; explicit shared entry/exit donors'
if clip=='chem1_end1':
    method+='; poof crown inferred from adjacent frame; smoke fit constrained to 15px margin; entry is chem mixing base and exit is neutral idle'
(ROOT/'sprites/rebuilt/configs'/f'{clip}_registration.json').write_text(json.dumps({'method':method,'frames':records},indent=2)+'\n',encoding='utf-8')
print(f'Registered {count} poses to canonical frame anchors')
