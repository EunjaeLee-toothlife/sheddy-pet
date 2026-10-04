"""기존 키 포즈를 보존하면서 검수한 ImageGen 중간 포즈를 사이에 넣는다."""
import hashlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def insert_inbetweens(frames, config):
    additions = {}
    for item in config.get('inbetweens', []):
        index = item['after']
        if index < 0 or index >= len(frames) - 1 or index in additions:
            raise ValueError('중간 포즈의 연결 구간이 잘못됨')
        path = ROOT / item['source']
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('중간 포즈 원본 변경: ' + str(path))
        tile = Image.open(path).convert('RGBA')
        if 'box' in item:
            tile = tile.crop(item['box'])
        tile.putalpha(tile.getchannel('A').point(lambda a: 0 if a < 8 else a))
        solid = tile.getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox()
        if not solid:
            raise ValueError('빈 중간 포즈')
        first = frames[index].getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox()
        last = frames[index + 1].getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox()
        target = [(a + b) / 2 for a, b in zip(first, last)]
        # 회전·점프 위치를 두 키 포즈 사이에 두고 종횡비는 그대로 유지한다.
        scale = (target[3] - target[1]) / (solid[3] - solid[1])
        resized = tile.resize((round(tile.width * scale), round(tile.height * scale)), Image.Resampling.LANCZOS)
        x = round((target[0] + target[2] - (solid[0] + solid[2]) * scale) / 2)
        y = round(target[3] - solid[3] * scale)
        frame = Image.new('RGBA', frames[index].size)
        frame.alpha_composite(resized, (x, y))
        bounds = frame.getchannel('A').getbbox()
        if not bounds or min(bounds[:2]) < 3 or bounds[2] > frame.width - 3 or bounds[3] > frame.height - 3:
            raise ValueError('중간 포즈가 캔버스 가장자리에 닿음')
        additions[index] = frame
    result = []
    for i, frame in enumerate(frames):
        result.append(frame)
        if i in additions:
            result.append(additions[i])
    return result
