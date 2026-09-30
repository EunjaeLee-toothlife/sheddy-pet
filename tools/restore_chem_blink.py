"""Restore the missing slow blink using only ImageGen-edited eye pixels."""
from pathlib import Path
import json
import shutil
import numpy as np
from PIL import Image
from compose_talk import rect_mask

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / 'sprites/rebuilt/frames/chem1_end2/chem1_end2_04.png'
BASE = ROOT / 'sprites/rebuilt/poses/chem1_end2_04_blink_base.png'
DONOR = ROOT / 'sprites/rebuilt/poses/chem1_end2_04_blink_special_native.png'


def main():
    if not BASE.exists():
        shutil.copyfile(TARGET, BASE)
    original = np.asarray(Image.open(BASE).convert('RGBA'))
    donor = np.asarray(Image.open(DONOR).convert('RGBA').resize((512, 512), Image.Resampling.LANCZOS))
    rectangle = [210, 128, 302, 162]
    mask = rect_mask(original.shape[:2], rectangle, 3)
    changed = np.rint(original.astype(float) * (1 - mask) + donor.astype(float) * mask).astype('uint8')
    changed[..., 3] = original[..., 3]
    assert np.array_equal(changed[mask[..., 0] == 0], original[mask[..., 0] == 0])
    Image.fromarray(changed, 'RGBA').save(TARGET)
    evidence = {'frame': 4, 'base': BASE.relative_to(ROOT).as_posix(),
                'donor': DONOR.relative_to(ROOT).as_posix(), 'rect': rectangle,
                'feather': 3, 'alphaUnchanged': True, 'outsideEyePixelsExact': True}
    (ROOT / 'sprites/rebuilt/configs/chem1_end2_blink_patch.json').write_text(
        json.dumps(evidence, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
