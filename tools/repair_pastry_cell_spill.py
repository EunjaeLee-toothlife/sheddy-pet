"""Remove the confirmed neighboring-cell spill from the ice-cream donor matte.

This corrects sprite-sheet extraction, preserving every character/effect pixel
above the real shoes. The immutable pre-repair tile is kept for reproduction.
"""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from slice_and_key import largest_component

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / 'sprites/rebuilt/poses/pastry_camera_source/pastry1_end8/pastry1_end8_04.png'
FROZEN = ROOT / 'sprites/rebuilt/poses/pastry1_end8_04_before_cell_spill.png'
if not FROZEN.exists():
    shutil.copyfile(TARGET, FROZEN)
source = np.array(Image.open(FROZEN).convert('RGBA'))
body = largest_component(source[:, :, 3] > 13)
body_bottom = int(np.where(body)[0].max())
spill = (np.indices(body.shape)[0] > body_bottom + 2) & (source[:, :, 3] > 0)
assert 0 < np.count_nonzero(spill) < 100, 'Unexpected spill extent; inspect the input'
assert not np.any(spill & body), 'Spill cleanup must not remove body pixels'
cleaned = source.copy()
cleaned[spill] = 0
assert np.array_equal(cleaned[~spill], source[~spill])
Image.fromarray(cleaned).save(TARGET)
record = {
    'reason': 'Bottom-left cherry stem crossed the raw sheet quadrant into frame04; foreign pixels below the real shoes skewed foot registration.',
    'frozenInput': FROZEN.relative_to(ROOT).as_posix(),
    'output': TARGET.relative_to(ROOT).as_posix(),
    'frozenSHA256': hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
    'outputSHA256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    'mainBodyBottom': body_bottom,
    'removedSpillPixels': int(np.count_nonzero(spill)),
    'removedOpaqueSpillPixels': int(np.count_nonzero(spill & (source[:, :, 3] > 100))),
    'allNonSpillPixelsExact': True,
}
(ROOT / 'sprites/rebuilt/configs/pastry1_end8_cell_spill_repair.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
