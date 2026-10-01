"""ImageGen 연금술 시트를 분리·정렬하고 공통 이음새와 투명 VP9를 재현한다."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PARTS = ('start', 'loop', 'end1', 'end2', 'end3', 'outro')
IDLE = ROOT / 'sprites/rebuilt/frames/idle1_loop/idle1_loop_00.png'


def solid_box(frame):
    return frame.getchannel('A').point(lambda a: 255 if a > 200 else 0).getbbox()


def build():
    configs, cells = {}, {}
    for part in PARTS:
        config = json.loads((ROOT / f'anims/alchemy1_{part}.json').read_text())
        source = ROOT / config['sheet']
        if hashlib.sha256(source.read_bytes()).hexdigest() != config['sha256']:
            raise ValueError(f'생성 원본 해시 불일치: {source}')
        sheet = Image.open(source)
        if sheet.mode != 'RGBA' or sheet.getchannel('A').getextrema()[0] != 0:
            raise ValueError(f'투명 ImageGen 시트가 아님: {source}')
        configs[part] = config
        cells[part] = []
        # 동일 간격으로 잘라 모자·신발이 잘리지 않도록 검수한 셀 경계를 사용한다.
        for box in config['cellBoxes']:
            tile = sheet.crop(box)
            tile.putalpha(tile.getchannel('A').point(lambda a: 0 if a < 8 else a))
            cells[part].append(tile)

    idle = Image.open(IDLE).convert('RGBA')
    ref = solid_box(idle)
    first = solid_box(cells['start'][0])
    boxes = [solid_box(f) for frames in cells.values() for f in frames]
    scale = min((ref[3] - ref[1]) / (first[3] - first[1]),
                480 / max(b[2] - b[0] for b in boxes),
                480 / max(b[3] - b[1] for b in boxes))
    frames = {}
    for part, tiles in cells.items():
        frames[part] = []
        for tile in tiles:
            box = solid_box(tile)
            resized = tile.resize((round(tile.width * scale), round(tile.height * scale)),
                                  Image.Resampling.LANCZOS)
            frame = Image.new('RGBA', (512, 512))
            frame.alpha_composite(resized, (round(256 - resized.width / 2),
                                           round(496 - box[3] * scale)))
            bounds = frame.getchannel('A').getbbox()
            if not bounds or min(bounds[:2]) <= 0 or max(bounds[2:]) >= 512:
                raise ValueError(f'프레임 가장자리 잘림: {part}')
            frames[part].append(frame)

    # 접합점은 같은 PNG를 공유한다. 결과 중간의 포즈는 생성 원본을 그대로 보존한다.
    anchor = frames['loop'][0]
    frames['start'][0] = idle.copy()
    frames['start'][-1] = anchor.copy()
    frames['loop'][-1] = anchor.copy()
    frames['outro'][0] = anchor.copy()
    frames['outro'][-1] = idle.copy()
    for part in ('end1', 'end2', 'end3'):
        frames[part][0] = anchor.copy()
        frames[part][-1] = anchor.copy()

    for part in PARTS:
        name = f'alchemy1_{part}'
        dest = ROOT / 'sprites' / name
        dest.mkdir(exist_ok=True)
        for i, frame in enumerate(frames[part]):
            frame.save(dest / f'{name}_{i:02d}.png')
        subprocess.run([sys.executable, str(ROOT / 'tools/encode_holds.py'),
                        str(ROOT / f'anims/{name}.json'), '--fps', str(configs[part]['fps'])],
                       cwd=ROOT, check=True)
    return frames


if __name__ == '__main__':
    build()
