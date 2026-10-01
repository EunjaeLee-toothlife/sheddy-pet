"""ImageGen 반응 시트를 비율 유지 PNG와 투명 VP9 영상으로 조립한다."""
import hashlib
import argparse
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageOps
from slice_and_key import chroma_key, body_box, match_to

ROOT = Path(__file__).resolve().parent.parent


def prepare_frames(sheet, config, reference):
    columns, rows = config.get('grid', [4, 2])
    transparent = sheet.mode == 'RGBA' and sheet.getchannel('A').getextrema()[0] < 255
    sheet = sheet.convert('RGBA' if transparent else 'RGB')
    frames = []
    row_offset = config.get('row_offset', 0)
    for i in range(columns * rows):
        x, y = i % columns, i // columns
        tile = sheet.crop((round(x * sheet.width / columns), round(y * sheet.height / rows) + row_offset,
                           round((x + 1) * sheet.width / columns), round((y + 1) * sheet.height / rows) + row_offset))
        tile = ImageOps.contain(tile, (512, 512), Image.Resampling.LANCZOS)
        canvas = Image.new(sheet.mode, (512, 512), (0, 0, 0, 0) if transparent else (0, 255, 0))
        canvas.paste(tile, ((512 - tile.width) // 2, (512 - tile.height) // 2))
        if transparent:
            # 생성 시트의 거의 투명한 배경 잡점만 제거하고 실제 가장자리 알파는 보존한다.
            canvas.putalpha(canvas.getchannel('A').point(lambda a: 0 if a < 8 else a))
            frames.append(canvas)
        else:
            frames.append(chroma_key(canvas))
    if config.get('preserve_motion', False):
        # 춤의 이동·점프는 정렬하지 않는다. 전체 포즈에 같은 배율·이동만 적용한다.
        rt, rb, rc = body_box(Image.open(reference).convert('RGBA'))
        top, bottom, center = body_box(frames[0])
        boxes = [f.getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox() for f in frames]
        left, upper = min(b[0] for b in boxes), min(b[1] for b in boxes)
        right, lower = max(b[2] for b in boxes), max(b[3] for b in boxes)
        scale = min((rb - rt) / (bottom - top), 480 / (right - left), 480 / (lower - upper))
        tx = min(max(rc - scale * center, 16 - scale * left), 496 - scale * right)
        ty = min(max(rb - scale * bottom, 16 - scale * upper), 496 - scale * lower)
        frames = [f.transform(f.size, Image.Transform.AFFINE,
                             (1 / scale, 0, -tx / scale, 0, 1 / scale, -ty / scale),
                             resample=Image.Resampling.BICUBIC) for f in frames]
    else:
        # 발을 딛는 반응 모션은 기존대로 셀별 배치 오차를 보정한다.
        _, bottom, center = body_box(frames[0])
        for i, frame in enumerate(frames):
            _, b, c = body_box(frame)
            frames[i] = frame.transform(frame.size, Image.Transform.AFFINE,
                                       (1, 0, c - center, 0, 1, b - bottom),
                                       resample=Image.Resampling.BICUBIC)
        frames = match_to(frames, reference)
    frames[-1] = frames[0].copy()
    return frames


def main():
    configs = json.loads((ROOT / 'anims/obs_reactions.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('states', nargs='*', help='지정한 모션만 재생성')
    args = parser.parse_args()
    if any(state not in configs for state in args.states):
        parser.error('등록되지 않은 모션: ' + ' ,'.join(s for s in args.states if s not in configs))
    for state, config in configs.items():
        if args.states and state not in args.states:
            continue
        source = ROOT / config['sheet']
        if hashlib.sha256(source.read_bytes()).hexdigest() != config['sha256']:
            raise ValueError(f'원본 시트 해시 불일치: {source}')
        frames = prepare_frames(Image.open(source), config,
                                ROOT / 'sprites/rebuilt/frames/idle1_loop/idle1_loop_00.png')
        dest = ROOT / 'sprites' / config['name']
        dest.mkdir(exist_ok=True)
        for i, frame in enumerate(frames):
            frame.save(dest / f'{config["name"]}_{i:02d}.png')
        timing = ROOT / 'anims' / f'{config["name"]}.json'
        timing.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
        subprocess.run([sys.executable, str(ROOT / 'tools/encode_holds.py'), str(timing),
                        '--fps', str(config.get('fps', 10))],
                       cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
