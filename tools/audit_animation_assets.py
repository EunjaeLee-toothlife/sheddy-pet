"""검수 원장을 변경하지 않고 전체 런타임 자산의 해시·영상 포즈 순서를 검사한다."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SIZE = 96
MAX_ERROR = .03


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ticks(count, timing):
    holds = {int(k): max(1, int(v)) for k, v in timing.get('holds', {}).items()}
    repeats = {r['frames'][0]: (r['frames'][1], max(1, int(r['times'])))
               for r in timing.get('repeats', [])}
    order, index = [], 0
    while index < count:
        if index in repeats:
            end, times = repeats[index]
            order.extend(list(range(index, end + 1)) * times)
            index = end + 1
        else:
            order.append(index)
            index += 1
    return [i for i in order for _ in range(holds.get(i, 1))]


def features(rgba):
    # 투명 영역의 숨은 RGB는 제외하고, 색과 알파를 같은 비중으로 비교한다.
    values = rgba.astype(np.float32) / 255
    values[..., :3] *= values[..., 3:4]
    return values


def compare_sequence(expected, decoded, order):
    errors, substitutions = [], []
    for tick, pose in enumerate(order):
        distances = np.mean(np.abs(expected - decoded[tick]), axis=(1, 2, 3))
        nearest = int(np.argmin(distances))
        error = float(distances[pose])
        errors.append(error)
        # 손실 압축·리사이즈 오차 내의 유사 포즈는 바뀌었다고 단정하지 않는다.
        if error > float(distances[nearest]) + .002:
            substitutions.append({'tick': tick, 'expected': pose, 'nearest': nearest,
                                  'error': error, 'nearestError': float(distances[nearest])})
    return errors, substitutions


def audit(record):
    video = ROOT / record['video']
    if sha(video) != record['videoHash']:
        raise ValueError('검수 이후 영상 변경: ' + str(video))
    expected = []
    for filename, digest in zip(record['frames'], record['hashes'], strict=True):
        path = ROOT / filename
        if sha(path) != digest:
            raise ValueError('검수 이후 PNG 변경: ' + str(path))
        with Image.open(path) as im:
            if im.mode != 'RGBA' or im.size != (record['size'], record['size']):
                raise ValueError('PNG 규격 오류: ' + str(path))
            expected.append(features(np.asarray(im.resize((SIZE, SIZE), Image.Resampling.BOX))))
    order = ticks(len(expected), record)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,codec_name:stream_tags=alpha_mode:format=duration:frame=best_effort_timestamp_time',
        '-of', 'json', str(video)]))
    stream = probe['streams'][0]
    if (stream['width'], stream['height']) != (record['size'], record['size']) or stream.get('tags', {}).get('alpha_mode') != '1':
        raise ValueError('영상 규격/알파 오류: ' + str(video))
    duration = len(order) / record['fps']
    if abs(float(probe['format']['duration']) - duration) > .015:
        raise ValueError('영상 길이 오류: ' + str(video))
    timestamps = [float(f['best_effort_timestamp_time']) for f in probe['frames']]
    if len(timestamps) != len(order) or any(abs(t - i / record['fps']) > .002 for i, t in enumerate(timestamps)):
        raise ValueError('영상 타임스탬프 오류: ' + str(video))
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-threads', '1', '-c:v', 'libvpx-vp9',
        '-i', str(video), '-vf', f'scale={SIZE}:{SIZE}:flags=area', '-threads', '1',
        '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgba', 'pipe:1'])
    decoded = np.frombuffer(raw, np.uint8).reshape(-1, SIZE, SIZE, 4)
    if len(decoded) != len(order):
        raise ValueError('디코딩 프레임 수 오류: ' + str(video))
    opaque_missing = np.flatnonzero(np.max(decoded[..., 3], axis=(1, 2)) < 240).tolist()
    corners_present = np.flatnonzero(np.any(decoded[:, [0, 0, -1, -1], [0, -1, 0, -1], 3], axis=1)).tolist()
    errors, substitutions = compare_sequence(np.stack(expected), features(decoded), order)
    result = {'video': record['video'], 'sha256': record['videoHash'], 'poses': len(expected),
              'ticks': len(order), 'duration': duration, 'maximumError': max(errors),
              'substitutions': substitutions, 'hashesDimensionsTiming': True,
              'opaqueMissingTicks': opaque_missing, 'nontransparentCornerTicks': corners_present}
    print(('REVIEW' if needs_review(result) else 'PASS'), record['video'], flush=True)
    return result


def needs_review(result):
    return bool(result.get('error') or result['substitutions'] or result['opaqueMissingTicks']
                or result['nontransparentCornerTicks'] or result['maximumError'] > MAX_ERROR)


def audit_safe(record):
    try:
        return audit(record)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('ERROR', record['video'], str(error), flush=True)
        return {'video': record['video'], 'error': str(error)}


def records():
    hd = json.loads((ROOT / 'anims/hd720_manifest.json').read_text())
    rebuilt = json.loads((ROOT / 'anims/rebuild_manifest.json').read_text())
    old = {c['clip']: c for c in rebuilt['clips']}
    for clip in hd['clips']:
        timing = {k: clip[k] for k in ('fps', 'holds', 'repeats')}
        yield dict(timing, video=clip['candidate'], videoHash=clip['videoSha256'],
                   frames=clip['frames'], hashes=clip['frameHashes'], size=720)
        if clip['clip'] in old:
            original = old[clip['clip']]
            yield dict(timing, video=original['webm'], videoHash=original['sourceVideoHash'],
                       frames=original['frames'], hashes=original['sourceFrameHashes'], size=512)
        yield dict(timing, video=clip['sourceVideo'], videoHash=clip['sourceVideoSha256'],
                   frames=clip['sourceFrames'], hashes=clip['sourceFrameHashes'], size=512)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(audit_safe, records()))
    # Pages의 중복 영상은 원본과 바이트 단위로 같은지 검사한다.
    copies = []
    for path in sorted((ROOT / 'docs/sprites').rglob('*.webm')):
        source = ROOT / path.relative_to(ROOT / 'docs')
        if sha(path) != sha(source):
            raise ValueError('Pages 복사본 불일치: ' + str(path))
        copies.append(path.relative_to(ROOT).as_posix())
    tracked = subprocess.check_output(['git', 'ls-files', '*.webm', '*.mp4'], cwd=ROOT, text=True).splitlines()
    covered = {r['video'] for r in results} | set(copies)
    other = []
    for filename in sorted(set(tracked) - covered):
        path = ROOT / filename
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
            'stream=codec_name,width,height:format=duration', '-of', 'json', str(path)]))
        subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'], check=True)
        other.append({'video': filename, 'sha256': sha(path), 'probe': probe, 'fullDecode': True})
    report = {'method': 'SHA256 + PNG dimensions + decoded alpha + every timestamp + 96px premultiplied RGBA pose comparison',
              'limits': 'Lossy-compression tolerance is 0.002 mean absolute channel error; visually indistinguishable poses cannot prove exact ordering. Absolute image error above 0.03 requires review. Artistic quality uses existing hash-bound visual reviews.',
              'runtimeVideos': len(results), 'pngPoses': sum(r.get('poses', 0) for r in results),
              'decodedTicks': sum(r.get('ticks', 0) for r in results), 'clips': results,
              'pagesCopies': copies, 'otherTrackedVideos': other}
    Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print('Complete', len(results), 'runtime videos,', len(copies), 'Pages copies', flush=True)
    if any(needs_review(r) for r in results):
        raise SystemExit('차이가 있는 클립은 보고서에서 직접 검토해야 한다.')


if __name__ == '__main__':
    main()
