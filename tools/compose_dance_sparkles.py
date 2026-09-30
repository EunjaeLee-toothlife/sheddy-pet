"""Composite only the ImageGen sparkle donor at the original described effect beats."""
import argparse
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
PLAN={
    'happy3_loop': {i:[(90,75,12+(i%3)*2),(416,112,10+(i%2)*3)] for i in range(11)},
    'yaho1_loop': {4:[(122,85,17),(396,115,13)],9:[(119,77,17),(390,112,12)],10:[(119,79,12),(390,114,8)],11:[(119,77,8)]},
    'dance3_loop': {14:[(115,77,14),(400,113,11)]},
}
PLAN['happy3_loop'].update({14:[(113,130,10)],15:[(107,128,15),(402,160,10)],18:[(112,70,12),(390,110,8)],19:[(112,70,6)]})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('clip',choices=list(PLAN))
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--refresh',action='store_true',help='refresh clean inputs after pose placement changes')
    a=p.parse_args()
    d=json.loads(a.manifest.read_text(encoding='utf-8'))
    c=next(c for c in d['clips'] if c['clip']==a.clip)
    donor=Image.open(ROOT/'sprites/rebuilt/poses/dance_sparkle_00.png').convert('RGBA')
    donor=donor.crop(donor.getbbox())
    stash=ROOT/'sprites/rebuilt/poses/pre_effects'/a.clip
    stash.mkdir(parents=True,exist_ok=True)
    for i,stars in PLAN[a.clip].items():
        frame=ROOT/'sprites/rebuilt/frames'/a.clip/f'{a.clip}_{i:02d}.png'
        clean=stash/frame.name
        if a.refresh or not clean.exists():
            clean.write_bytes(frame.read_bytes())
        im=Image.open(clean).convert('RGBA')
        for x,y,h in stars:
            star=donor.resize((max(3,round(donor.width*h/donor.height)),h),Image.Resampling.LANCZOS)
            im.alpha_composite(star,(x-star.width//2,y-star.height//2))
        im.save(frame)
    c['effectDonor']='sprites/rebuilt/poses/dance_sparkle_00.png'
    c['effectPlan']={str(k):v for k,v in PLAN[a.clip].items()}
    a.manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
