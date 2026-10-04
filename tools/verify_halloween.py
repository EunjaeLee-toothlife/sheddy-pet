"""신규 할로윈 모션의 원본·프레임·영상만 검증하고 기존 검수 기록을 보존한다."""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image

from audit_hd720 import probe, sha

ROOT = Path(__file__).resolve().parent.parent


def verify(motion, anchor_state='witchidle1', part='loop', transform=False):
    state = motion['id']
    name = state + '_' + part
    config = json.loads((ROOT / f'anims/{name}.json').read_text())
    calm = config.get('sourcePipeline') == 'calm-face-v1'
    if calm:
        from compose_calm_motion import verify_sources
        verify_sources(config)
    elif config.get('sourcePipeline') in ('native-pairs-v1', 'native-strips-v1'):
        from verify_native_sources import verify_sources
        verify_sources(config)
    else:
        assert sha(ROOT / config['sheet']) == config['sha256'], f'원본 해시: {state}'
    assert config['fps'] == motion['fps'] and config['holds'] == motion['holds'], f'타이밍 설정: {state}'
    ticks = sum(int(config['holds'].get(str(i), 1)) for i in range(16))
    assets = []
    for size, directory, video in [
        (512, ROOT / 'sprites' / name, ROOT / f'sprites/anim_{name}.webm'),
        (720, ROOT / 'sprites/hd720/frames' / name, ROOT / f'sprites/hd720/videos/anim_{name}.webm'),
    ]:
        frames = sorted(directory.glob('*.png'))
        assert len(frames) == 16, f'프레임 수: {state}'
        for i, path in enumerate(frames):
            im = Image.open(path)
            assert path.name == f'{name}_{i:02d}.png' and im.mode == 'RGBA' and im.size == (size, size), str(path)
            alpha = np.asarray(im.getchannel('A'))
            assert np.any(alpha > 240) and not any(np.any(edge) for edge in (alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1])), f'프레임 여백/알파: {path}'
        hashes = [sha(p) for p in frames]
        if transform:
            anchor = Image.open(ROOT / config['anchor']).convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
            cocoon = directory.parent / 'transform_normal_start/transform_normal_start_15.png'
            neutral = Image.open(frames[0 if part == 'start' else -1])
            assert neutral.tobytes() == anchor.tobytes(), f'변신 대기 연결: {state}'
            assert hashes[-1 if part == 'start' else 0] == sha(cocoon), f'공통 변신 연결: {state}'
            if part == 'loop':
                departure = sorted((directory.parent / (state + '_start')).glob('*.png'))
                assert hashes == list(reversed([sha(p) for p in departure])), f'변신 역순: {state}'
        else:
            anchor = directory.parent / f'{anchor_state}_loop/{anchor_state}_loop_00.png'
            assert hashes[0] == hashes[-1] == sha(anchor), f'공통 대기 연결: {state}'
        # 얼굴 합성은 동일 몸체를 의도적으로 재사용한다. 원본 재현성 검사는 위에서 별도로 수행한다.
        minimum = 3 if calm and config['faceRole'] == 'talk' else 8 if calm else 14 if transform else 12
        assert len(set(hashes)) >= minimum, f'독립 포즈 부족: {state}'
        info = probe(video)
        stream = info['streams'][0]
        duration = float(info['format']['duration'])
        assert (stream['width'], stream['height'], stream['codec_name']) == (size, size, 'vp9'), str(video)
        assert stream.get('tags', {}).get('alpha_mode') == '1', f'영상 알파: {state}'
        assert abs(duration - ticks / config['fps']) < .002, f'영상 길이: {state}'
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9', '-i', str(video), '-f', 'rawvideo', '-pix_fmt', 'rgba', 'pipe:1'])
        decoded = np.frombuffer(raw, np.uint8).reshape(-1, size, size, 4)
        assert len(decoded) == ticks, f'디코딩 틱 수: {state}'
        assert not np.any(decoded[:, [0, 0, -1, -1], [0, -1, 0, -1], 3]), f'디코딩 투명 배경: {state}'
        assert np.all(np.sum(decoded[:, :, :, 3] > 240, axis=(1, 2)) > 1000), f'빈 영상: {state}'
        assets.append((frames, hashes, video, duration))
    source_frames, source_hashes, source, _ = assets[0]
    frames, hashes, video, duration = assets[1]
    rel = lambda p: p.relative_to(ROOT).as_posix()
    record = {
        'clip': name, 'state': state, 'part': part, 'rate': 1,
        'sourceVideo': rel(source), 'sourceVideoSha256': sha(source),
        'sourceFrames': list(map(rel, source_frames)), 'sourceFrameHashes': source_hashes,
        'frames': list(map(rel, frames)), 'frameHashes': hashes,
        'candidate': rel(video), 'videoSha256': sha(video),
        'frameCount': 16, 'duration': duration, 'decodedTicks': ticks,
        'fps': config['fps'], 'holds': config['holds'], 'repeats': [],
        'sourceBytes': source.stat().st_size, 'candidateBytes': video.stat().st_size,
        'technicalReview': dict.fromkeys(['dimensions', 'alpha', 'duration', 'pngFrameOrder', 'decodedTickCount', 'sourceHash', 'neutralSeam', 'distinctPoses'], True),
        'status': 'audited',
    }
    print(f'PASS {state}: 16 poses, {ticks} ticks, 512/720 RGBA VP9, {video.stat().st_size} bytes', flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register', action='store_true', help='신규 기술 검수 기록을 자산 목록에 반영')
    args = parser.parse_args()
    motions = json.loads((ROOT / 'anims/halloween/motions.json').read_text())
    assert len(motions) == len({m['id'] for m in motions}) == 24
    records = [verify(m) for m in motions]
    if args.register:
        hd_path = ROOT / 'anims/hd720_manifest.json'
        hd = json.loads(hd_path.read_text())
        old = {c['clip']: c for c in hd['clips']}
        for record in records:
            previous = old.get(record['clip'])
            # 동일 영상·프레임의 재검증만 기존 시각/재생 검수를 보존한다.
            if previous and previous['videoSha256'] == record['videoSha256'] and previous['frameHashes'] == record['frameHashes']:
                record['status'] = previous['status']
                if 'review' in previous:
                    record['review'] = previous['review']
            old[record['clip']] = record
        hd['clips'] = list(old.values())
        hd['clipCount'] = len(hd['clips'])
        for total, field in [('frameCount', 'frameCount'), ('sourceVideoBytes', 'sourceBytes'), ('candidateVideoBytes', 'candidateBytes')]:
            hd[total] = sum(c[field] for c in hd['clips'])
        legacy_path = ROOT / 'anims/rebuild_manifest.json'
        legacy = json.loads(legacy_path.read_text())
        preserved = {c['file']: c for c in legacy['preservedOriginalClips']}
        for record in records:
            filename = Path(record['sourceVideo']).name
            preserved[filename] = {'file': filename, 'state': record['state'], 'sha256': record['sourceVideoSha256'], 'reason': 'ImageGen 할로윈 전용 모션. 원본/재구성 모드에서 공통 사용.'}
        legacy['preservedOriginalClips'] = list(preserved.values())
        for path, value in [(hd_path, hd), (legacy_path, legacy)]:
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(f'PASS {len(records)} clips / {sum(c["frameCount"] for c in records)} poses / {sum(c["candidateBytes"] for c in records)} HD bytes')


if __name__ == '__main__':
    main()
