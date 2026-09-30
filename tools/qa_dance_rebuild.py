"""Decode VP9 alpha and save a per-frame review sheet for the dance worker."""
import argparse
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('clip')
    p.add_argument('--manifest',type=Path,required=True)
    a=p.parse_args()
    d=json.loads(a.manifest.read_text(encoding='utf-8'))
    c=next(c for c in d['clips'] if c['clip']==a.clip)
    video=ROOT/c['candidate']
    raw=subprocess.run(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(video),'-f','rawvideo','-pix_fmt','rgba','pipe:1'],capture_output=True,check=True).stdout
    frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,512,512,4)
    alpha=frames[:,:,:,3]
    corners=alpha[:,[0,0,511,511],[0,511,0,511]]
    if np.any(corners) or np.any(alpha.max(axis=(1,2))<240):
        raise ValueError('decoded alpha invalid')
    cols=5; rows=(c['count']+cols-1)//cols
    sheet=Image.new('RGB',(cols*256,rows*278),(35,40,49))
    draw=ImageDraw.Draw(sheet)
    for i in range(c['count']):
        im=Image.open(ROOT/'sprites/rebuilt/frames'/a.clip/f'{a.clip}_{i:02d}.png').convert('RGBA')
        xy=((i%cols)*256,(i//cols)*278)
        sheet.paste(im.resize((256,256)),xy,im.resize((256,256)))
        draw.text((xy[0]+5,xy[1]+258),str(i),fill='white')
    target=ROOT/'sprites/rebuilt/qa'/f'{a.clip}_contact.png'
    target.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(target)
    c.setdefault('evidence',{})['decodedAlpha']={'decoder':'libvpx-vp9','frameCount':len(frames),'cornersAllZero':True,'everyFrameHasOpaqueForeground':True}
    c['review']['alpha']=True
    c['qaContact']=target.relative_to(ROOT).as_posix()
    a.manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{a.clip}: decoded {len(frames)} transparent VP9 frames; contact {target}')

if __name__=='__main__':
    main()
