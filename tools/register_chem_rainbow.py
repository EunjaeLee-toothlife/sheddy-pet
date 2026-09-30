"""Register the rainbow ending with one camera scale per generated pose group.

Standing hair-to-sole measurements normalize generation layout, while crouches
and bent knees use the adjacent standing pose's scale rather than their height.
The flare masks a small camera pullback for the overhead flask; the proud exit
eases back toward the exact neutral pose. Original motion/timing stays intact.
"""
from pathlib import Path
import json
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def geometry(path):
    array = np.asarray(Image.open(path).convert('RGBA')).astype(int)
    red, green, blue, alpha = array.transpose(2, 0, 1)
    yy, xx = np.indices(alpha.shape)
    bottom = np.where(alpha > 100)[0].max()
    shoes = np.where((alpha > 100) & (yy > bottom - 15))[1]
    center = (shoes.min() + shoes.max()) / 2
    # A broad crown row excludes detached star points and yellow flask liquid.
    hair = ((red > 210) & (green > 145) & (blue > 65) & (blue < 185)
            & (alpha > 220) & (yy < 250) & (abs(xx - center) < 65))
    crown = np.where(hair.sum(axis=1) > 40)[0].min()
    return {'center': float(center), 'bottom': int(bottom),
            'crown': int(crown), 'bodyHeight': int(bottom - crown)}


def main():
    clip = 'chem1_end3'
    donors = []
    for index in range(16):
        first = index // 4 * 4
        batch = clip + '_' + '-'.join(f'{i:02d}' for i in range(first, first + 4))
        donors.append(ROOT / 'sprites/rebuilt/poses/batches' / batch / f'cell_{index % 4:02d}.png')
    donors.append(ROOT / 'sprites/rebuilt/poses/chem1_end3_proud_00.png')
    dimensions = [geometry(path) for path in donors]
    base = geometry(ROOT / 'sprites/rebuilt/frames/chem1_loop/chem1_loop_00.png')
    camera = .85
    scales = [camera * base['bodyHeight'] / item['bodyHeight'] for item in dimensions]
    scales[0] = scales[1] = base['bodyHeight'] / dimensions[0]['bodyHeight']
    scales[7] = sum(scales[4:7]) / 3
    group_scale = camera * base['bodyHeight'] / np.mean([dimensions[i]['bodyHeight'] for i in [10, 11]])
    for index in [8, 9, 10, 11]:
        scales[index] = float(group_scale)
    group_scale = camera * base['bodyHeight'] / np.mean([dimensions[i]['bodyHeight'] for i in [14, 15]])
    for index in [12, 13, 14, 15]:
        scales[index] = float(group_scale)
    scales[16] = .93 * base['bodyHeight'] / dimensions[16]['bodyHeight']
    records = []
    for index, (path, scale, item) in enumerate(zip(donors, scales, dimensions)):
        lift = {9: 7, 10: 5, 11: 5, 12: 2}.get(index, 0)
        records.append({'frame': index, 'donor': path.relative_to(ROOT).as_posix(),
                        'scale': scale, 'dx': round(base['center'] - item['center'] * scale),
                        'dy': round(498 - (item['bottom'] + 1) * scale - lift),
                        'jumpLift': lift, 'measuredGeometry': item})
    plan = {'method': __doc__, 'camera': camera, 'frames': records, 'despillAfterResize': True,
            'exactEntry': 'sprites/rebuilt/frames/chem1_loop/chem1_loop_00.png',
            'exactExit': 'sprites/rebuilt/poses/idle_open_00.png'}
    target = ROOT / 'sprites/rebuilt/configs/chem1_end3_registration.json'
    target.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    subprocess.run([sys.executable, str(ROOT / 'tools/render_registered_rebuild.py'),
                    clip, str(target)], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
