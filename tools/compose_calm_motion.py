"""복장별 원본 몸체를 고정하고 작은 눈·입 영역과 미세 호흡만 합성한다."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'anims/calm_faces.json'
BREATH = [0, .25, .7, 1.2, 1.7, 2, 1.7, 1.2, .7, .25, 0, -.25, -.35, -.2, 0, 0]
SPEECH = ['base', 'ah', 'ah', 'o', 'o', 'closed', 'closed', 'ah',
          'ah', 'o', 'closed', 'ah', 'ah', 'o', 'closed', 'base']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def align(image, source, target):
    """두 눈의 기준점으로 배율·회전·이동을 정해 얼굴 기울기를 보존한다."""
    p, q = [complex(*point) for point in source]
    a, b = [complex(*point) for point in target]
    scale = (q - p) / (b - a)
    shift = p - scale * a
    return image.transform((720, 720), Image.Transform.AFFINE,
                           (scale.real, -scale.imag, shift.real,
                            scale.imag, scale.real, shift.imag), Image.Resampling.BICUBIC)


def transplant(base, donor, rectangles):
    """경계의 피부색을 맞추고 지정 영역 밖 픽셀과 알파는 그대로 둔다."""
    result = np.array(base)
    for x0, y0, x1, y1 in rectangles:
        original = np.asarray(base)[y0:y1, x0:x1, :3].astype(float)
        patch = np.asarray(donor)[y0:y1, x0:x1, :3].astype(float)
        ring = np.zeros(original.shape[:2], bool)
        ring[:3] = ring[-3:] = True
        ring[:, :3] = ring[:, -3:] = True
        offset = np.median(original[ring] - patch[ring], axis=0)
        patch = np.clip(patch + offset, 0, 255)
        mask = Image.new('L', (x1 - x0, y1 - y0))
        ImageDraw.Draw(mask).rectangle((3, 3, mask.width - 4, mask.height - 4), fill=255)
        mask = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.2)), dtype=float)[..., None] / 255
        result[y0:y1, x0:x1, :3] = np.rint(original * (1 - mask) + patch * mask).astype(np.uint8)
    return Image.fromarray(result)


def variants(config):
    base = Image.open(ROOT / config['base']).convert('RGBA')
    sheet = Image.open(ROOT / config['sheet']).convert('RGBA')
    width = sheet.width // 3
    result = {'base': base}
    for i, name in enumerate(['blink', 'ah', 'o']):
        donor = sheet.crop((i * width, 0, (i + 1) * width, sheet.height))
        points = config['closedEyes'] if name == 'blink' else config['eyes']
        aligned = align(donor, config['donorEyes'][i], points)
        boxes = config['eyeRects'] if name == 'blink' else [config['mouthRect']]
        result[name] = transplant(base, aligned, boxes)
        if name == 'blink':
            mouth_transform = config.get('closedMouthTransform')
            if mouth_transform:
                # 열린 입이 기본인 복장은 입을 닫는다. 원본 턱선은 패치 밖에 둔다.
                scale, offset = mouth_transform
                aligned = aligned.transform((720, 720), Image.Transform.AFFINE,
                                            (1, 0, 0, 0, scale, offset), Image.Resampling.BICUBIC)
            result['closed'] = transplant(base, aligned, [config['mouthRect']]) if mouth_transform else base
    return result


def breathe(image, offset):
    if not offset:
        return image.copy()
    # 발과 하단 의상은 고정하고 위쪽으로 갈수록 최대 2px만 움직인다.
    mesh = []
    for y in range(0, 720, 8):
        bottom = min(y + 8, 720)
        dy0 = offset * max(0, min(1, (560 - y) / 400))
        dy1 = offset * max(0, min(1, (560 - bottom) / 400))
        mesh.append(((0, y, 720, bottom), (0, y + dy0, 0, bottom + dy1,
                                          720, bottom + dy1, 720, y + dy0)))
    result = image.transform((720, 720), Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)
    result.paste(image.crop((0, 560, 720, 720)), (0, 560))
    return result


def frames(config, role):
    poses = variants(config)
    if role == 'talk':
        return [poses[key].copy() for key in SPEECH]
    return [breathe(poses['blink' if i in (6, 7) else 'base'], dy) for i, dy in enumerate(BREATH)]


def build(state):
    config = json.loads((ROOT / f'anims/{state}_loop.json').read_text())
    face = json.loads(CONFIG.read_text())[config['faceMode']]
    for field in ['base', 'sheet']:
        assert sha(ROOT / face[field]) == face[field + 'Sha256'], f'표정 원본 변경: {field}'
    ordered = frames(face, config['faceRole'])
    name = config['name']
    for size, folder, video in [
        (720, ROOT / 'sprites/hd720/frames' / name, ROOT / f'sprites/hd720/videos/anim_{name}.webm'),
        (512, ROOT / 'sprites' / name, ROOT / f'sprites/anim_{name}.webm'),
    ]:
        folder.mkdir(parents=True, exist_ok=True)
        for i, frame in enumerate(ordered):
            frame.resize((size, size), Image.Resampling.LANCZOS).save(folder / f'{name}_{i:02d}.png')
        subprocess.run([sys.executable, str(ROOT / 'tools/encode_holds.py'),
                        str(ROOT / f'anims/{name}.json'), '--fps', str(config['fps']),
                        '--frames-dir', str(folder), '--out', str(video)], check=True)


def verify_sources(config):
    face = json.loads(CONFIG.read_text())[config['faceMode']]
    for field in ['base', 'sheet']:
        assert sha(ROOT / face[field]) == face[field + 'Sha256'], f'표정 원본 해시: {field}'
    expected = frames(face, config['faceRole'])
    for i, image in enumerate(expected):
        path = ROOT / f'sprites/hd720/frames/{config["name"]}/{config["name"]}_{i:02d}.png'
        assert Image.open(path).tobytes() == image.tobytes(), f'표정 합성 재현성: {path}'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('states', nargs='+')
    args = parser.parse_args()
    for state in args.states:
        build(state)
