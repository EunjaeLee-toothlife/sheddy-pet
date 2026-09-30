"""Reproduce food-matte repair candidates without changing production assets."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'sprites/rebuilt/repairs/pastry_macaron_matte'
OUT.mkdir(parents=True, exist_ok=True)
config = json.loads((ROOT / 'sprites/rebuilt/configs/pastry1_end3_camera.json').read_text())
regions = {3:(226,255,277,279),4:(232,232,279,259),5:(227,43,280,67),6:(227,43,279,67),7:(235,223,280,249)}
records=[]
for index, region in regions.items():
    sheetname = 'pastry1_end3_00-01-02-03.png' if index == 3 else 'pastry1_end3_04-05-06-07.png'
    cell = 3 if index == 3 else index-4
    sheet = Image.open(ROOT/'sprites/rebuilt/sheets'/sheetname).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
    tile = sheet.crop(((cell%2)*512,(cell//2)*512,(cell%2+1)*512,(cell//2+1)*512))
    raw = np.array(tile).astype(int)
    r,g,b=raw[:,:,0],raw[:,:,1],raw[:,:,2]
    # Reviewed pastel green (R/B both high) is distinct from saturated chroma.
    # Tight food-only ROI prevents restoring stray chroma elsewhere.
    bounded=np.zeros((512,512),bool)
    x0,y0,x1,y1=region
    bounded[y0:y1,x0:x1]=True
    protect=bounded&(g-r>10)&(g-b>10)&(r>60)&(b>60)
    # The preserved pre-repair source is immutable after production adoption.
    # Prefer it so repeated repair runs never use already-restored alpha.
    sourcepath=OUT/f'pastry1_end3_{index:02d}_source_before.png'
    if not sourcepath.exists():
        sourcepath=ROOT/'sprites/rebuilt/poses/pastry_camera_source/pastry1_end3'/f'pastry1_end3_{index:02d}.png'
    source=Image.open(sourcepath).convert('RGBA')
    restored=np.array(source)
    assert protect.any()
    changed=protect&(restored[:,:,3]<255)
    restored[protect,:3]=raw[protect]
    restored[protect,3]=255
    revised=Image.fromarray(restored)
    # Replay unchanged original camera, using the ORIGINAL bbox and placement.
    rec=config[index];box=source.getbbox();factor=rec['uniformScale']
    size=(round((box[2]-box[0])*factor),round((box[3]-box[1])*factor))
    def camera(im):
        out=Image.new('RGBA',(512,512));out.alpha_composite(im.crop(box).resize(size,Image.Resampling.LANCZOS),tuple(rec['placement']));return out
    oldcam=np.array(camera(source));newcam=np.array(camera(revised))
    finalpath=ROOT/'sprites/rebuilt/frames/pastry1_end3'/f'pastry1_end3_{index:02d}.png'
    final=np.array(Image.open(finalpath).convert('RGBA'))
    assert np.array_equal(oldcam,final) or np.array_equal(newcam,final),f'Camera changed since analysis: {index}'
    # Evidence always compares the immutable before image with the repair,
    # independently of whether production has already adopted the candidate.
    difference=np.any(oldcam!=newcam,axis=2)
    ys,xs=np.where(difference)
    assert len(xs)>0
    revised.save(OUT/f'pastry1_end3_{index:02d}_source.png')
    Image.fromarray(newcam).save(OUT/f'pastry1_end3_{index:02d}.png')
    records.append({'index':index,'rawSheet':sheetname,'rawTileProtectedROI':region,'restoredSourcePixels':int(changed.sum()),'finalChangedPixels':len(xs),'finalChangedBBox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'outsideFinalChangedBBoxIdentical':True,'cameraUnchanged':True})
    print(index,records[-1])
evidence=json.loads((OUT/'repair_spec.json').read_text()) if (OUT/'repair_spec.json').exists() else {}
evidence.update({'method':'Bounded raw pastel green protection before unchanged camera replay; saturation/background exclusion r>60,b>60,g-r>10,g-b>10. No generated art, source geometry, common donors, final files or ledgers changed.','records':records,'reproductionBaseline':'*_source_before.png preferred; production final may equal original or repaired camera output'})
(OUT/'repair_spec.json').write_text(json.dumps(evidence,indent=2)+'\n')
