"""Record the completed dance worker's explicit visual review and measured placement."""
import argparse
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
NOTES={
 'happy3_loop':['20 source-index slots retain full spin and curtsy','True front-left3q-leftprofile-leftback3q-back-rightback3q-rightprofile-right3q-front views','Deep curtsy uses visibly flexed knees, close crossed feet and365px height against451px standing','Hands pinch actual skirt rather than coat; finalarms at sides; ImageGen sparkle donor restored'],
 'dance1_loop':['16 source-index slots retain alternating left/high-right/low then opposite fistpump','Feet close underhips; low-to-high442-454px bounce','Hairclip/identity never mirrored during hand-side swap','Peak low arm retains relaxed source hip-level fist'],
 'yaho1_loop':['14 slots retain handrise, puffedcheek inhale, megaphone shout, tiptoe peak, V transition, gyaru pose, loweringhands, neutral return','Wrong-side upright source V corrected: frames7-11 upside-down V on imageRIGHT and imageLEFT hip hand','Frame10 briefly blinks other eye while holding same V/hip pose','Frame13 copies exact canonical idle pixels; ImageGen sparkle donor restored'],
 'parapara1_loop':['All24 slots retain left45-degree straightarm, right45-degree straightarm, T, X, overhead highV, lowV and gather-return','ImageGen correction restored flat innerhand frame10 and raised frame18/19 hands above crown','Footcenter registration prevents translation from one-sided arm extension'],
 'dance2_loop':['All16 slots retain left sway, center, opposite sway, center, two forwardpaw pushes and return','Puppypaw fists and curled wrists preserved, feet hipwidth','Frame14 generated separate stars retained via keep-components'],
 'dance3_loop':['All16 slots retain left fingerpoint sway, center, opposite sway, center, two uppoints and return','Wide stance and index-only pointing gestures retained','Frame14 ImageGen sparkle donor restored'],
}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    a=p.parse_args()
    d=json.loads(a.manifest.read_text(encoding='utf-8'))
    result=[]
    for c in d['clips']:
        if c['clip'] not in NOTES:
            continue
        c['review'].update(style=True,motion=True,alpha=True,seams=False)
        c['method']='ImageGen full-resolution action batches with explicit corrections; uniform shoe-band placement; original source order, holds/repeats, rate and duration retained'
        c['motionReview']=NOTES[c['clip']]
        measurements=[]
        for i in range(c['count']):
            path=ROOT/'sprites/rebuilt/frames'/c['clip']/f"{c['clip']}_{i:02d}.png"
            im=Image.open(path)
            alpha=im.getchannel('A').point(lambda x:255 if x>10 else 0)
            box=alpha.getbbox()
            band=max(12,round(c['placement']['frames'][i]['height']*0.065))
            foot=alpha.crop((0,box[3]-band,512,box[3])).getbbox()
            measurements.append({'frame':i,'footCenterX':(foot[0]+foot[2])/2,'floorY':box[3],'band':band})
        c['evidence']['footRegistrationMeasurement']=measurements
        result.append({'clip':c['clip'],'count':c['count'],'floorRange':[min(m['floorY'] for m in measurements),max(m['floorY'] for m in measurements)],'footCenterRange':[min(m['footCenterX'] for m in measurements),max(m['footCenterX'] for m in measurements)]})
    a.manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':
    main()
