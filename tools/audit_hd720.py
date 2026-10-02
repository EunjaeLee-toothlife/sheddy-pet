"""전체 런타임의 720px 영상·프레임·타이밍·알파와 기존 리소스 보존을 검증한다."""
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'stream=width,height,codec_name:stream_tags=alpha_mode:format=duration', '-of', 'json', str(path)]))


def registry():
    widget = (ROOT / 'widget.html').read_text(encoding='utf-8')
    script = 'const ANIMS =' + widget.split('const ANIMS =', 1)[1].split('const THEME_STATES', 1)[0]
    code = "const fs=require('fs'),vm=require('vm');let s=fs.readFileSync(0,'utf8');process.stdout.write(JSON.stringify(vm.runInNewContext(s+';ANIMS')));"
    return json.loads(subprocess.check_output(['node', '-e', code], input=script, text=True, encoding='utf-8'))


def main():
    snapshot = json.loads((ROOT / 'sprites/hd720/configs/source_snapshot.json').read_text())
    for path, expected in snapshot.items():
        if sha(ROOT / path) != expected:
            raise ValueError('기존 리소스 변경: ' + path)
    previous = json.loads((ROOT / 'anims/rebuild_manifest.json').read_text(encoding='utf-8'))
    old = {c['clip']: c for c in previous['clips']}
    report = {'resolution': 720, 'codec': 'vp9', 'crf': 24, 'clips': [], 'sourcePreservation': True}
    seen = set()
    for state, animation in registry().items():
        for part in ('start', 'loop', 'end', 'outro'):
            files = animation.get(part, [])
            files = files if isinstance(files, list) else [files]
            for filename in files:
                name = filename.removeprefix('anim_').removesuffix('.webm')
                if name in seen:
                    raise ValueError('중복 런타임 영상: ' + name)
                seen.add(name)
                if name in old:
                    source = ROOT / old[name]['candidate']
                    source_frames = sorted((ROOT / 'sprites/rebuilt/frames' / name).glob('*.png'))
                    timing = old[name]
                else:
                    source = ROOT / 'sprites' / filename
                    source_frames = sorted((ROOT / 'sprites' / name).glob('*.png'))
                    timing = json.loads((ROOT / 'anims' / f'{name}.json').read_text(encoding='utf-8'))
                candidate = ROOT / 'sprites/hd720/videos' / filename
                frames = sorted((ROOT / 'sprites/hd720/frames' / name).glob('*.png'))
                if len(frames) != len(source_frames) or not frames:
                    raise ValueError(f'프레임 수 불일치: {name} {len(frames)}/{len(source_frames)}')
                hashes = []
                for i, frame in enumerate(frames):
                    if frame.name != f'{name}_{i:02d}.png':
                        raise ValueError('프레임 순서 불일치: ' + str(frame))
                    im = Image.open(frame)
                    alpha = np.asarray(im.getchannel('A'))
                    if im.mode != 'RGBA' or im.size != (720, 720):
                        raise ValueError('720RGBA 규격 오류: ' + str(frame))
                    if any(np.any(edge) for edge in (alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1])):
                        raise ValueError('캔버스 가장자리 접촉: ' + str(frame))
                    hashes.append(sha(frame))
                before, after = probe(source), probe(candidate)
                stream = after['streams'][0]
                if (stream['width'], stream['height']) != (720, 720) or stream.get('tags', {}).get('alpha_mode') != '1':
                    raise ValueError('영상 규격 또는 알파 오류: ' + name)
                if abs(float(before['format']['duration']) - float(after['format']['duration'])) > .001:
                    raise ValueError('영상 길이 변경: ' + name)
                raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9', '-i', str(candidate), '-f', 'rawvideo', '-pix_fmt', 'rgba', 'pipe:1'])
                decoded = np.frombuffer(raw, np.uint8).reshape(-1, 720, 720, 4)
                holds = {int(k): int(v) for k, v in timing.get('holds', {}).items()}
                repeats = {r['frames'][0]: (r['frames'][1], r['times']) for r in timing.get('repeats', [])}
                ticks, index = 0, 0
                while index < len(frames):
                    if index in repeats:
                        end, times = repeats[index]
                        ticks += sum(max(1, holds.get(i, 1)) for i in range(index, end + 1)) * max(1, times)
                        index = end + 1
                    else:
                        ticks += max(1, holds.get(index, 1))
                        index += 1
                if len(decoded) != ticks:
                    raise ValueError(f'hold/repeat tick 변경: {name} {len(decoded)}/{ticks}')
                if np.any(decoded[:, [0, 0, -1, -1], [0, -1, 0, -1], 3]) or np.any(np.sum(decoded[:, :, :, 3] > 240, axis=(1, 2)) == 0):
                    raise ValueError('디코딩 알파 오류: ' + name)
                record = {'clip': name, 'state': state, 'part': part, 'rate': animation.get('rate', 1),
                    'sourceVideo': source.relative_to(ROOT).as_posix(), 'sourceVideoSha256': sha(source),
                    'sourceFrames': [p.relative_to(ROOT).as_posix() for p in source_frames],
                    'sourceFrameHashes': [sha(p) for p in source_frames],
                    'frames': [p.relative_to(ROOT).as_posix() for p in frames], 'frameHashes': hashes,
                    'candidate': candidate.relative_to(ROOT).as_posix(), 'videoSha256': sha(candidate),
                    'frameCount': len(frames), 'duration': float(after['format']['duration']), 'decodedTicks': len(decoded),
                    'fps': timing.get('fps', 10), 'holds': timing.get('holds', {}), 'repeats': timing.get('repeats', []),
                    'sourceBytes': source.stat().st_size, 'candidateBytes': candidate.stat().st_size,
                    'technicalReview': {'dimensions': True, 'alpha': True, 'duration': True,
                                        'pngFrameOrder': True, 'decodedTickCount': True},
                    'status': 'audited'}
                report['clips'].append(record)
                print('Audited', name, len(frames), 'slots /', len(decoded), 'ticks', flush=True)
    report['clipCount'] = len(report['clips'])
    report['frameCount'] = sum(c['frameCount'] for c in report['clips'])
    report['sourceVideoBytes'] = sum(c['sourceBytes'] for c in report['clips'])
    report['candidateVideoBytes'] = sum(c['candidateBytes'] for c in report['clips'])
    report['workers'] = [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / 'anims').glob('hd720_*.json')) if p.name != 'hd720_manifest.json']
    (ROOT / 'anims/hd720_manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Complete', report['clipCount'], 'videos,', report['frameCount'], 'slots', flush=True)


if __name__ == '__main__':
    main()
