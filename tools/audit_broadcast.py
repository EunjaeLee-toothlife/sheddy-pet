"""방송 영상의 모든 디코딩 프레임·PTS·표정·루프를 검사하고 전수 검수판을 만든다."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from PIL import Image, ImageChops, ImageDraw, ImageStat

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output/broadcast/sheddy-just-chatting'
REVIEW = OUT / 'qa/frame-review'
FPS, COUNT, SIZE = 15, 360, (1920, 1080)
# 렌더러의 효과 마스크와 별개로, 실제 얼굴이 보이는 영역을 지정한다.
FACES = {
    'lab': (995, 475, 1190, 610),
    'lecture': (995, 434, 1120, 529),
    'cafe': (965, 495, 1115, 607),
    'mountain': (660, 463, 727, 539),
}
BLINK_WINDOWS = [(46, 55), (130, 139), (224, 235), (319, 329)]
BLINK_STARTS = [48, 132, 227, 321]


def expected_eye_state(index):
    for start in BLINK_STARTS:
        if index - start in (0, 3):
            return 'half'
        if index - start in (1, 2):
            return 'closed'
    return 'open'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean_difference(a, b):
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3


def read_frame(stream):
    remaining = SIZE[0] * SIZE[1] * 3
    parts = []
    while remaining:
        data = stream.read(remaining)
        if not data:
            break
        parts.append(data)
        remaining -= len(data)
    if not parts:
        return None
    if remaining:
        raise ValueError('잘린 RGB 프레임')
    return b''.join(parts)


def audit(key):
    video = OUT / f'sheddy-{key}-1080p15.mp4'
    info = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_frames',
        '-show_format', '-of', 'json', str(video),
    ]))
    streams = info['streams']
    assert len(streams) == 1 and streams[0]['codec_type'] == 'video', '무음 영상 필요'
    stream = streams[0]
    assert (stream['width'], stream['height']) == SIZE
    assert stream['codec_name'] == 'h264' and stream['pix_fmt'] == 'yuv420p'
    assert stream['avg_frame_rate'] == '15/1' and stream['r_frame_rate'] == '15/1'
    assert abs(float(info['format']['duration']) - 24) < .0001
    metadata = info['frames']
    assert len(metadata) == COUNT
    for i, frame in enumerate(metadata):
        assert abs(float(frame['best_effort_timestamp_time']) - i / FPS) < .00001, f'PTS {i}'

    open_face = Image.open(OUT / 'qa' / f'{key}-open.png').convert('RGB').crop(FACES[key])
    half_face = Image.open(OUT / 'qa' / f'{key}-half.png').convert('RGB').crop(FACES[key])
    shut_face = Image.open(OUT / 'qa' / f'{key}-blink.png').convert('RGB').crop(FACES[key])
    assert mean_difference(open_face, shut_face) > .1, '열린 눈/감은 눈 검수 기준 동일'
    folder = REVIEW / key
    folder.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen([
        'ffmpeg', '-v', 'error', '-xerror', '-i', str(video),
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1',
    ], stdout=subprocess.PIPE)
    frames, first, previous = [], None, None
    contact = None
    blink_sheet = Image.new('RGB', (12 * 180, 4 * 156), '#172019')
    blink_draw = ImageDraw.Draw(blink_sheet)
    scene_sheets = []
    while (data := read_frame(process.stdout)) is not None:
        i = len(frames)
        image = Image.frombytes('RGB', SIZE, data)
        gray = image.convert('L')
        mean = ImageStat.Stat(gray).mean[0]
        black_fraction = sum(gray.histogram()[:5]) / (SIZE[0] * SIZE[1])
        face = image.crop(FACES[key])
        dist_open = mean_difference(face, open_face)
        dist_half = mean_difference(face, half_face)
        dist_shut = mean_difference(face, shut_face)
        distances = {'open': dist_open, 'half': dist_half, 'closed': dist_shut}
        pose = min(distances, key=distances.get)
        assert pose == expected_eye_state(i), f'{key} 표정 순서/잔상 의심 F{i}: {pose} {distances}'
        delta = None if previous is None else mean_difference(previous, image)
        frames.append({
            'index': i, 'pts': float(metadata[i]['best_effort_timestamp_time']),
            'sha256': hashlib.sha256(data).hexdigest(),
            'meanLuma': round(mean, 6), 'blackFraction': round(black_fraction, 6),
            'deltaPrevious': None if delta is None else round(delta, 6),
            'eyeOpenDistance': round(dist_open, 6), 'eyeHalfDistance': round(dist_half, 6),
            'eyeClosedDistance': round(dist_shut, 6), 'eyeState': pose,
        })
        assert mean > 10 and black_fraction < .8, f'{key} 검은 화면: {i}'
        if i % 60 == 0:
            contact = Image.new('RGB', (6 * 320, 10 * 200), '#172019')
        x, y = (i % 6) * 320, ((i % 60) // 6) * 200
        contact.paste(image.resize((320, 180), Image.Resampling.LANCZOS), (x, y))
        ImageDraw.Draw(contact).text((x + 6, y + 182), f'{key}  F{i:03d}  {i/FPS:06.3f}s', fill='#e9f0df')
        if i % 60 == 59:
            name = f'all-frames-{i//60+1}.jpg'
            contact.save(folder / name, quality=90)
            scene_sheets.append(name)
        for row, (start, end) in enumerate(BLINK_WINDOWS):
            if start <= i <= end:
                left = (i - start) * 180
                tile = Image.new('RGB', (180, 136), '#172019')
                face.thumbnail((180, 136), Image.Resampling.LANCZOS)
                tile.paste(face, ((180 - face.width) // 2, (136 - face.height) // 2))
                blink_sheet.paste(tile, (left, row * 156))
                blink_draw.text((left + 5, row * 156 + 137), f'F{i:03d} {i/FPS:.3f}s', fill='#e9f0df')
        if first is None:
            first = image.copy()
        previous = image
    process.stdout.close()
    assert process.wait() == 0, '전체 영상 디코딩 실패'
    assert len(frames) == COUNT
    hashes = [row['sha256'] for row in frames]
    assert len(set(hashes)) == COUNT, '누락/정지 의심: 동일 프레임 반복'
    for start, end in BLINK_WINDOWS:
        assert any(row['eyeClosedDistance'] < row['eyeOpenDistance'] for row in frames[start:end+1]), f'눈 감김 누락 {start}'
    # 예정한 깜빡임 사이에는 열린 표정이 유지되어야 한다.
    off_windows = [row for row in frames if not any(a <= row['index'] <= b for a, b in BLINK_WINDOWS)]
    assert all(row['eyeOpenDistance'] < row['eyeClosedDistance'] for row in off_windows), '깜빡임 구간 밖 표정 변경'
    seam = mean_difference(first, previous)
    transitions = [row['deltaPrevious'] for row in frames[1:]]
    # RGB 0~255 기준 평균 차이. 국소 표정은 허용하되 전체 장면 전환/번쩍임을 잡는다.
    assert max(transitions) < 3 and seam < 3, '급격한 변화 또는 반복 경계'
    blink_sheet.save(folder / 'blink-details.jpg', quality=95)
    result = {
        'file': str(video.relative_to(ROOT)), 'sha256': sha(video),
        'frameCount': len(frames), 'uniqueFrames': len(set(hashes)),
        'fps': 15, 'duration': 24, 'resolution': list(SIZE), 'silent': True,
        'maxFrameDeltaMeanRGB': max(transitions), 'loopSeamMeanRGB': seam,
        'lumaRange': [min(row['meanLuma'] for row in frames), max(row['meanLuma'] for row in frames)],
        'closedEyeEvents': 4, 'sheets': scene_sheets + ['blink-details.jpg'],
        'frames': frames,
    }
    (folder / 'frames.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(key, f'{len(frames)} frames PASS', 'seam', round(seam, 4), 'maxDelta', round(max(transitions), 4), flush=True)
    return {k: v for k, v in result.items() if k != 'frames'}


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    summary = {'scope': 'all 1440 decoded frames', 'scenes': {key: audit(key) for key in FACES}}
    summary['sourceHashes'] = {str(p.relative_to(ROOT)): sha(p) for p in [
        ROOT / 'tools/broadcast_renderer.html', ROOT / 'tools/render_broadcast.js', Path(__file__),
        *sorted((OUT / 'assets').glob('*.png')),
        *sorted((ROOT / 'output/imagegen/chzzk-concepts-20261008-v2').glob('*.png')),
    ]}
    (REVIEW / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    # 검수한 영상과 배포 ZIP의 내용이 어긋나지 않도록 같은 명령에서 묶는다.
    bundle = OUT.parent / 'sheddy-just-chatting-1080p15.zip'
    files = [*sorted(OUT.glob('*.mp4')), OUT / 'preview.html', OUT / 'OBS-사용법.txt',
             OUT / 'assets/blink-prompts.json', OUT / 'assets/half-blink-prompts.json']
    with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file in files:
            archive.write(file, Path('sheddy-just-chatting') / file.relative_to(OUT))
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
        for file in files:
            assert hashlib.sha256(archive.read(str(Path('sheddy-just-chatting') / file.relative_to(OUT)))).hexdigest() == sha(file)
    print('ZIP 내용 일치 PASS', flush=True)


if __name__ == '__main__':
    main()
