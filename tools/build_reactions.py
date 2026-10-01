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
        sheet = Image.open(source).convert('RGB')
        frames = []
        for i in range(8):
            x, y = i % 4, i // 4
            tile = sheet.crop((round(x * sheet.width / 4), round(y * sheet.height / 2),
                               round((x + 1) * sheet.width / 4), round((y + 1) * sheet.height / 2)))
            tile = ImageOps.contain(tile, (512, 512), Image.Resampling.LANCZOS)
            canvas = Image.new('RGB', (512, 512), (0, 255, 0))
            canvas.paste(tile, ((512 - tile.width) // 2, (512 - tile.height) // 2))
            frames.append(chroma_key(canvas))
        # 발을 딛는 모션이라 생성 시트의 셀별 배치 오차만 보정한다.
        _, bottom, center = body_box(frames[0])
        for i, frame in enumerate(frames):
            _, b, c = body_box(frame)
            frames[i] = frame.transform(frame.size, Image.Transform.AFFINE,
                                         (1, 0, c - center, 0, 1, b - bottom),
                                         resample=Image.Resampling.BICUBIC)
        frames = match_to(frames, ROOT / 'sprites/rebuilt/frames/idle1_loop/idle1_loop_00.png')
        frames[-1] = frames[0].copy()
        dest = ROOT / 'sprites' / config['name']
        dest.mkdir(exist_ok=True)
        for i, frame in enumerate(frames):
            frame.save(dest / f'{config["name"]}_{i:02d}.png')
        timing = ROOT / 'anims' / f'{config["name"]}.json'
        timing.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
        subprocess.run([sys.executable, str(ROOT / 'tools/encode_holds.py'), str(timing)],
                       cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
