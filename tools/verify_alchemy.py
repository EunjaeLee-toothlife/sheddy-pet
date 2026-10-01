"""연금술 프레임의 잘림·접합점과 실제 VP9 디코딩의 알파·타이밍을 검증한다."""
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PARTS = ('start', 'loop', 'end1', 'end2', 'end3', 'outro')


def verify():
    frames = {}
    for part in PARTS:
        name = f'alchemy1_{part}'
        config = json.loads((ROOT / f'anims/{name}.json').read_text())
        assert hashlib.sha256((ROOT / config['sheet']).read_bytes()).hexdigest() == config['sha256'], name
        files = sorted((ROOT / 'sprites' / name).glob('*.png'))
        assert len(files) == 16, (name, len(files))
        frames[part] = [Image.open(p).convert('RGBA') for p in files]
        for frame in frames[part]:
            assert frame.size == (512, 512), name
            alpha = frame.getchannel('A')
            box = alpha.getbbox()
            assert box and min(box[:2]) > 0 and max(box[2:]) < 512, (name, box)
            assert alpha.getextrema() == (0, 255), name

        video = ROOT / f'sprites/anim_{name}.webm'
        decoded = subprocess.run(['ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9', '-i', str(video),
                                  '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
                                 check=True, capture_output=True).stdout
        size = 512 * 512 * 4
        ticks = sum(config['holds'].values())
        assert len(decoded) == size * ticks, (name, len(decoded) / size, ticks)
        for index in range(ticks):
            frame = Image.frombytes('RGBA', (512, 512), decoded[index * size:(index + 1) * size])
            assert frame.getpixel((0, 0))[3] == 0, (name, index, '배경')
            assert frame.getchannel('A').getextrema()[1] >= 250, (name, index, '본체')
        metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format',
                                                       '-of', 'json', str(video)]))
        duration = float(metadata['format']['duration'])
        assert abs(duration - ticks / config['fps']) < 0.02, (name, duration)
        print(f'{name}: 16 PNG, {ticks} VP9 frames, {duration:.3f}s, alpha OK')

    anchor = frames['loop'][0].tobytes()
    for part, index in [('start', -1), ('loop', -1), ('outro', 0),
                        *[(p, i) for p in ('end1', 'end2', 'end3') for i in (0, -1)]]:
        assert frames[part][index].tobytes() == anchor, (part, index, '접합점')
    idle = Image.open(ROOT / 'sprites/rebuilt/frames/idle1_loop/idle1_loop_00.png').convert('RGBA').tobytes()
    assert frames['start'][0].tobytes() == frames['outro'][-1].tobytes() == idle
    print('96 PNG, 모든 장면 접합점과 idle 원복 일치')


if __name__ == '__main__':
    verify()
