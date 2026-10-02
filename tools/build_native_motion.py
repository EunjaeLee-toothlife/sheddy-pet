"""2포즈 고해상도 원본을 확대 없이 기존 타이밍의 720/512 모션으로 조립한다."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image

from build_halloween import ROOT, sha, write_json


def bounds(image):
    return image.getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox()


def foot_center(image, box):
    alpha = np.asarray(image.getchannel('A')) > 128
    strip = alpha[max(box[1], box[3] - max(4, round((box[3] - box[1]) * .03))):box[3]]
    xs = np.nonzero(strip)[1]
    return float(np.median(xs))


def build(state):
    geometry = json.loads((ROOT / 'anims/native/geometry.json').read_text())[state]
    source_dir = ROOT / f'sprites/raw/native/{geometry["theme"]}/{state}'
    frames, evidence = [], []
    for i, target in enumerate(geometry['poses']):
        first = i // 2 * 2
        path = source_dir / f'{first:02}-{first + 1:02}.png'
        sheet = Image.open(path)
        assert sheet.mode == 'RGBA' and sheet.getchannel('A').getextrema()[0] == 0, path
        w, h = sheet.size
        assert w >= 1440 and h >= 720, f'원본 셀 규격 미달: {path} {sheet.size}'
        box = (i % 2 * w // 2, 0, (i % 2 + 1) * w // 2, h)
        tile = sheet.crop(box)
        tile.putalpha(tile.getchannel('A').point(lambda a: 0 if a < 8 else a))
        solid = bounds(tile)
        assert solid and solid[0] > 0 and solid[1] > 0 and solid[2] < tile.width and solid[3] < tile.height, f'원본 잘림: {path} {i}'
        scale = target['height'] / (solid[3] - solid[1])
        assert scale <= 1, f'원본 확대 금지: {state} {i} {scale:.3f}'
        resized = tile.resize((round(tile.width * scale), round(tile.height * scale)), Image.Resampling.LANCZOS)
        rb = bounds(resized)
        px = round(target['x'] - foot_center(resized, rb))
        py = round(target['bottom'] - rb[3])
        full = resized.getchannel('A').getbbox()
        assert px + full[0] >= 8 and py + full[1] >= 8 and px + full[2] <= 712 and py + full[3] <= 712, f'출력 잘림: {state} {i} {(px,py,full)}'
        frame = Image.new('RGBA', (720, 720))
        frame.alpha_composite(resized, (px, py))
        frames.append(frame)
        evidence.append({'source': path.relative_to(ROOT).as_posix(), 'sourceSha256': sha(path), 'cell': box,
                         'nativeSize': tile.size, 'nativeBounds': solid, 'scale': scale,
                         'position': [px, py], 'target': target})
    mode = geometry['mode']
    if geometry['theme'] == 'seasonal':
        if state.endswith('_breathe1'):
            frames[-1] = frames[0].copy()
            evidence[-1] = dict(evidence[0])
        else:
            anchor_path = ROOT / f'sprites/hd720/frames/{mode}_breathe1_loop/{mode}_breathe1_loop_00.png'
            anchor = Image.open(anchor_path).convert('RGBA')
            frames[0] = anchor.copy()
            frames[-1] = anchor.copy()
            evidence[0] = evidence[-1] = {'anchor': anchor_path.relative_to(ROOT).as_posix(), 'sourceSha256': sha(anchor_path)}
        parts = [('loop', frames)]
    else:
        anchor = Image.open(ROOT / geometry['anchor']).convert('RGBA')
        frames[0] = anchor.copy()
        evidence[0] = {'anchor': geometry['anchor'], 'sourceSha256': sha(ROOT / geometry['anchor'])}
        if mode != 'normal':
            cocoon_path = ROOT / 'sprites/hd720/frames/transform_normal_start/transform_normal_start_15.png'
            frames[-1] = Image.open(cocoon_path).convert('RGBA')
            evidence[-1] = {'anchor': cocoon_path.relative_to(ROOT).as_posix(), 'sourceSha256': sha(cocoon_path)}
        parts = [('start', frames), ('loop', list(reversed(frames)))]
    for part, ordered in parts:
        name = state + '_' + part
        cfg_path = ROOT / f'anims/{name}.json'
        cfg = json.loads(cfg_path.read_text())
        for obsolete in ('sheet', 'sha256', 'cellBoxes'):
            cfg.pop(obsolete, None)
        cfg['nativeSources'] = evidence if part != 'loop' or geometry['theme'] == 'seasonal' else list(reversed(evidence))
        cfg['sourcePipeline'] = 'native-pairs-v1'
        cfg['anchor'] = geometry['anchor']
        write_json(cfg_path, cfg)
        for size, directory, out in [(720, ROOT / 'sprites/hd720/frames' / name, ROOT / f'sprites/hd720/videos/anim_{name}.webm'),
                                     (512, ROOT / 'sprites' / name, ROOT / f'sprites/anim_{name}.webm')]:
            directory.mkdir(parents=True, exist_ok=True)
            for i, frame in enumerate(ordered):
                frame.resize((size, size), Image.Resampling.LANCZOS).save(directory / f'{name}_{i:02}.png')
            subprocess.run([sys.executable, str(ROOT / 'tools/encode_holds.py'), str(cfg_path), '--fps', str(cfg['fps']), '--frames-dir', str(directory), '--out', str(out)], check=True)
        qa = ROOT / 'sprites/hd720/qa/native'
        qa.mkdir(parents=True, exist_ok=True)
        contact = Image.new('RGB', (1440, 1440), '#48444e')
        for i, frame in enumerate(ordered):
            thumb = frame.resize((360, 360))
            contact.paste(thumb, ((i % 4) * 360, (i // 4) * 360), thumb)
        contact.save(qa / f'{name}.jpg')
    print('PASS native', state, 'max scale', max(e.get('scale', 0) for e in evidence), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('states', nargs='+')
    args = parser.parse_args()
    for state in args.states:
        build(state)
