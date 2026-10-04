"""ImageGen 할로윈 시트를 검수 가능한 720/512 PNG와 투명 VP9로 조립한다."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
MOTIONS = ROOT / 'anims/halloween/motions.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def boxes_for(sheet):
    """분할선 근처의 투명한 틈을 찾아 옆 포즈의 모자·신발을 자르지 않는다."""
    alpha = np.asarray(sheet.getchannel('A'))
    h, w = alpha.shape

    def gap(values, target, radius):
        positions = range(max(1, target - radius), min(len(values) - 1, target + radius + 1))
        return min(positions, key=lambda pos: (values[pos - 1] + values[pos] + values[pos + 1]) * 1000 + abs(pos - target))

    xs = [0] + [gap((alpha > 64).sum(axis=0), round(w * c / 4), round(w / 40)) for c in range(1, 4)] + [w]
    boxes = [None] * 16
    for col in range(4):
        strip = alpha[:, xs[col]:xs[col + 1]]
        ys = [0] + [gap((strip > 64).sum(axis=1), round(h * r / 4), round(h / 20)) for r in range(1, 4)] + [h]
        for row in range(4):
            boxes[row * 4 + col] = [xs[col], ys[row], xs[col + 1], ys[row + 1]]
    return boxes


def prepare(sheet, config, close_loop=True):
    tiles = []
    mask = np.asarray(sheet.getchannel('A')) > 128
    for i, box in enumerate(config['cellBoxes']):
        tile = sheet.crop(box).convert('RGBA')
        # 투명 배경에 남은 1~7/255 알파 잡점만 정리한다.
        tile.putalpha(tile.getchannel('A').point(lambda a: 0 if a < 8 else a))
        solid = tile.getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox()
        if not solid:
            raise ValueError(f'빈 포즈: {config["name"]} {i}')
        left, top, right, bottom = box
        # 한 픽셀 투명 틈도 유효하다. 분할선 양쪽에 연결된 불투명 픽셀이 있을 때만 잘림이다.
        cuts = [mask[top, left:right] & mask[top - 1, left:right] if top else mask[0, left:right],
                mask[bottom - 1, left:right] & mask[bottom, left:right] if bottom < sheet.height else mask[-1, left:right],
                mask[top:bottom, left] & mask[top:bottom, left - 1] if left else mask[top:bottom, 0],
                mask[top:bottom, right - 1] & mask[top:bottom, right] if right < sheet.width else mask[top:bottom, -1]]
        if max(np.count_nonzero(edge) for edge in cuts) > 3:
            raise ValueError(f'분할선이 포즈를 자름: {config["name"]} {i}')
        tiles.append((tile, solid))
    first = tiles[0][1]
    full = [tile.getchannel('A').getbbox() for tile, _ in tiles]
    scale = min(560 / (first[3] - first[1]),
                660 / max(b[2] - b[0] for b in full),
                650 / max(b[3] - b[1] for b in full))
    frames = []
    for i, (tile, box) in enumerate(tiles):
        # 이동·점프는 생성된 포즈의 상대 위치를 보존하고, 서 있는 동작은 바닥만 정렬한다.
        airborne = config['state'] in ('broom1', 'moon1', 'witchdance1')
        local_bottom = first[3] + config['cellBoxes'][0][1] if airborne else box[3] + config['cellBoxes'][i][1] - (i // 4) * sheet.height / 4
        x = config['cellBoxes'][i][0] - (i % 4) * sheet.width / 4
        y = config['cellBoxes'][i][1] - (i // 4) * sheet.height / 4
        resized = tile.resize((round(tile.width * scale), round(tile.height * scale)), Image.Resampling.LANCZOS)
        bounds = resized.getchannel('A').getbbox()
        px = round(360 + (x - sheet.width / 8) * scale)
        py = round(680 + (y - local_bottom) * scale)
        # 옆으로 날아가는 박쥐나 별빛 꼬리까지 화면 안에 들어오도록 최소한만 이동한다.
        px = min(max(px, 12 - bounds[0]), 708 - bounds[2])
        py = min(max(py, 12 - bounds[1]), 708 - bounds[3])
        frame = Image.new('RGBA', (720, 720))
        frame.alpha_composite(resized, (px, py))
        bounds = frame.getchannel('A').getbbox()
        if not bounds or min(bounds[:2]) < 8 or max(bounds[2:]) > 712:
            raise ValueError(f'출력 여백 부족: {config["name"]} {i} {bounds}')
        frames.append(frame)
    if close_loop:
        frames[-1] = frames[0].copy()
    return frames


def build(motion, theme='halloween', anchor_state='witchidle1'):
    state = motion['id']
    name = state + '_loop'
    existing = ROOT / f'anims/{name}.json'
    if existing.exists() and json.loads(existing.read_text()).get('sourcePipeline') == 'calm-face-v1':
        from compose_calm_motion import build as build_calm
        return build_calm(state)
    raw = ROOT / f'sprites/raw/{theme}/{state}.png'
    sheet = Image.open(raw)
    if sheet.mode != 'RGBA' or sheet.getchannel('A').getextrema()[0] != 0:
        raise ValueError('투명 원본이 아님: ' + str(raw))
    path = ROOT / f'anims/{name}.json'
    config = json.loads(path.read_text()) if path.exists() else {
        'name': name, 'state': state, 'sheet': raw.relative_to(ROOT).as_posix(),
        'sha256': sha(raw), 'cellBoxes': boxes_for(sheet), 'fps': motion['fps'], 'holds': motion['holds'],
    }
    if config['sha256'] != sha(raw):
        raise ValueError('원본 변경: ' + str(raw))
    frames = prepare(sheet, config)
    if state != anchor_state:
        anchor = Image.open(ROOT / f'sprites/hd720/frames/{anchor_state}_loop/{anchor_state}_loop_00.png').convert('RGBA')
        if state in ('witchlook1', 'witchtidy1'):
            # 서 있는 잔동작의 시트 배치 오차를 제거한다. 모자와 팔의 의도된 움직임은 보존한다.
            def foot_x(image):
                alpha = np.asarray(image.getchannel('A')) > 128
                bottom = np.nonzero(alpha)[0].max() + 1
                return round(float(np.median(np.nonzero(alpha[bottom - 17:bottom])[1])))
            center = foot_x(anchor)
            stable = []
            for frame in frames:
                aligned = Image.new('RGBA', frame.size)
                aligned.paste(frame, (center - foot_x(frame), 0))
                stable.append(aligned)
            frames = stable
        frames[0] = anchor.copy()
        frames[-1] = anchor.copy()
    write_json(path, config)
    for size, directory, output in [
        (720, ROOT / 'sprites/hd720/frames' / name, ROOT / f'sprites/hd720/videos/anim_{name}.webm'),
        (512, ROOT / 'sprites' / name, ROOT / f'sprites/anim_{name}.webm'),
    ]:
        directory.mkdir(parents=True, exist_ok=True)
        for i, frame in enumerate(frames):
            frame.resize((size, size), Image.Resampling.LANCZOS).save(directory / f'{name}_{i:02d}.png')
        subprocess.run([sys.executable, str(ROOT / 'tools/encode_holds.py'), str(path), '--fps', str(config['fps']),
                        '--frames-dir', str(directory), '--out', str(output)], cwd=ROOT, check=True)
    qa = ROOT / f'sprites/hd720/qa/{theme}'
    qa.mkdir(parents=True, exist_ok=True)
    contact = Image.new('RGB', (960, 1040), '#e7e5ee')
    draw = ImageDraw.Draw(contact)
    for i, frame in enumerate(frames):
        thumb = frame.resize((240, 240), Image.Resampling.LANCZOS)
        x, y = (i % 4) * 240, (i // 4) * 260
        contact.paste(thumb, (x, y), thumb)
        draw.text((x + 5, y + 242), f'{state} {i:02d}', fill='black')
    contact.save(qa / f'{state}.jpg')
    print('Built', state, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('states', nargs='*')
    args = parser.parse_args()
    motions = json.loads(MOTIONS.read_text())
    known = {m['id'] for m in motions}
    if set(args.states) - known:
        parser.error('알 수 없는 모션: ' + ', '.join(sorted(set(args.states) - known)))
    for motion in motions:
        if not args.states or motion['id'] in args.states:
            build(motion)
