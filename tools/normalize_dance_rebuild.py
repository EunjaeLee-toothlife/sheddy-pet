"""Place dance-worker generated poses on a stable floor without deforming anatomy."""
import argparse
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('clip')
    parser.add_argument('--heights', type=int, nargs='+', required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding='utf-8'))
    clip = next(c for c in data['clips'] if c['clip'] == args.clip)
    if len(args.heights) != clip['count']:
        raise ValueError('one anatomical height per original frame required')
    raw = ROOT / 'sprites/rebuilt/poses/normalized_inputs' / args.clip
    raw.mkdir(parents=True, exist_ok=True)
    evidence = []
    for i, height in enumerate(args.heights):
        target = ROOT / 'sprites/rebuilt/frames' / args.clip / f'{args.clip}_{i:02d}.png'
        donor = raw / target.name
        if not donor.exists():
            donor.write_bytes(target.read_bytes())
        im = Image.open(donor).convert('RGBA')
        box = im.getchannel('A').point(lambda a: 255 if a > 10 else 0).getbbox()
        if box is None:
            raise ValueError('empty generated pose')
        tight = im.crop(box)
        width = round(tight.width * height / tight.height)
        if width > 480 or height > 480:
            raise ValueError('normalization would clip a limb')
        scaled = tight.resize((width, height), Image.Resampling.LANCZOS)
        # Register the shoes, not the complete silhouette: a side-pointing arm
        # or flowing hair must not translate planted feet sideways.
        band=max(12,round(tight.height*0.065))
        foot=tight.getchannel('A').crop((0,tight.height-band,tight.width,tight.height))
        foot_box=foot.point(lambda a: 255 if a>10 else 0).getbbox()
        foot_center=(foot_box[0]+foot_box[2])/2
        x=round(256-foot_center*width/tight.width)
        if x<0 or x+width>512:
            raise ValueError('foot registration would clip a limb')
        out = Image.new('RGBA', (512, 512))
        out.alpha_composite(scaled, (x, 498-height))
        out.save(target)
        evidence.append({'frame': i, 'donorBBox': list(box), 'height': height, 'floor':498, 'footCenter':256, 'scaleIsUniform':True})
    clip['placement'] = {'method':'uniform pose scaling plus shoe-band registration to floor498px and foot-center256px; no squash or gesture modification', 'frames': evidence}
    args.manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__ == '__main__':
    main()
