"""Reproduce reviewed per-pose placement without fitting away crouches or raised arms."""
import argparse
import json
import shutil
from pathlib import Path

from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('clip')
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    data = json.loads(args.plan.read_text(encoding='utf-8'))
    destination = ROOT / 'sprites/rebuilt/frames' / args.clip
    destination.mkdir(parents=True, exist_ok=True)
    for record in data['frames']:
        sprite = Image.open(ROOT / record['donor']).convert('RGBA')
        scale = record['scale']
        sprite = sprite.resize((round(sprite.width * scale), round(sprite.height * scale)),
                               Image.Resampling.LANCZOS)
        x, y = record['dx'], record['dy']
        box = sprite.getbbox()
        placed = (box[0] + x, box[1] + y, box[2] + x, box[3] + y)
        if min(placed[:2]) < 1 or max(placed[2:]) > 511:
            raise ValueError(f'pose would clip: {record["frame"]} {placed}')
        frame = Image.new('RGBA', (512, 512))
        frame.alpha_composite(sprite, (x, y))
        if data.get('despillAfterResize'):
            # Lanczos' negative lobes can reintroduce green in faint contour
            # pixels even when the keyed donor was already despilled. Opaque
            # green liquid and all opaque illustration pixels stay untouched.
            rgba = np.asarray(frame).copy()
            limit = np.maximum(rgba[..., 0], rgba[..., 2])
            spill = ((rgba[..., 3] > 0) & (rgba[..., 3] < 128)
                     & (rgba[..., 1].astype(int) - limit.astype(int) > 20))
            rgba[..., 1] = np.where(spill, limit, rgba[..., 1])
            frame = Image.fromarray(rgba, 'RGBA')
        frame.save(destination / f'{args.clip}_{record["frame"]:02d}.png')
    for key, index in [('exactEntry', 0), ('exactExit', len(data['frames']))]:
        if data.get(key):
            shutil.copyfile(ROOT / data[key], destination / f'{args.clip}_{index:02d}.png')


if __name__ == '__main__':
    main()
