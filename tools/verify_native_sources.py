"""실제 사용한 원본 크기·해시·축소 비율과 720 프레임 재현성을 검사한다."""
from PIL import Image

from build_halloween import ROOT, sha
from build_native_motion import bounds, foot_center


def verify_sources(config):
    sources = config['nativeSources']
    frames = list((ROOT / f'sprites/hd720/frames/{config["name"]}').glob('*.png'))
    assert len(sources) == len(frames), '원본 증빙 프레임 수'
    for i, source in enumerate(sources):
        path = ROOT / source.get('anchor', source.get('source', ''))
        assert sha(path) == source['sourceSha256'], f'원본 해시: {path}'
        image = Image.open(path)
        assert image.mode == 'RGBA', f'원본 알파: {path}'
        if 'anchor' in source:
            expected = image
        else:
            cell = source['cell']
            assert len(cell) == 4 and 0 <= cell[0] < cell[2] <= image.width and 0 <= cell[1] < cell[3] <= image.height
            tile = image.crop(cell)
            assert min(tile.size) >= 720 and list(tile.size) == source['nativeSize'], f'원본 셀 규격: {path}'
            tile.putalpha(tile.getchannel('A').point(lambda a: 0 if a < 8 else a))
            solid = bounds(tile)
            assert list(solid) == source['nativeBounds'], f'원본 경계: {path}'
            assert solid[0] > 0 and solid[1] > 0 and solid[2] < tile.width and solid[3] < tile.height, f'원본 잘림: {path}'
            target = source['target']
            scale = target['height'] / (solid[3] - solid[1])
            assert 0 < scale <= 1 and abs(scale - source['scale']) < 1e-9, f'원본 확대: {path}'
            resized = tile.resize((round(tile.width * scale), round(tile.height * scale)), Image.Resampling.LANCZOS)
            box = bounds(resized)
            center = (box[0] + box[2]) / 2 if target.get('alignment') == 'bounds' else foot_center(resized, box)
            position = [round(target['x'] - center), round(target['bottom'] - box[3])]
            full = resized.getchannel('A').getbbox()
            assert full[2] - full[0] <= 704 and full[3] - full[1] <= 704, f'출력 크기 초과: {path}'
            position[0] = min(max(position[0], 8 - full[0]), 712 - full[2])
            position[1] = min(max(position[1], 8 - full[1]), 712 - full[3])
            assert position == source['position'], f'정렬 설정: {path}'
            expected = Image.new('RGBA', (720, 720))
            expected.alpha_composite(resized, tuple(position))
        output = Image.open(ROOT / f'sprites/hd720/frames/{config["name"]}/{config["name"]}_{i:02}.png')
        assert expected.size == output.size == (720, 720) and expected.tobytes() == output.tobytes(), f'원본 재현 불일치: {config["name"]} {i}'
