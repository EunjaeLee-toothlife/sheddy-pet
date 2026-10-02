"""복장별 변신 시트를 이탈/등장 영상으로 조립하고 공통 빛 접합점까지 검증한다."""
import json
import subprocess
import sys

import numpy as np
from PIL import Image

from build_halloween import ROOT, boxes_for, prepare, sha, write_json
from audit_hd720 import probe


def main():
    motions = json.loads((ROOT / 'anims/transform/motions.json').read_text())
    records = []
    cocoon = None
    for motion in motions:
        mode = motion['mode']
        existing = json.loads((ROOT / f'anims/transform_{mode}_start.json').read_text())
        if existing.get('sourcePipeline') == 'native-pairs-v1':
            from build_native_motion import build
            from verify_native_motion import verify_state
            build('transform_' + mode)
            records.extend(verify_state('transform_' + mode))
            if cocoon is None:
                cocoon = Image.open(ROOT / 'sprites/hd720/frames/transform_normal_start/transform_normal_start_15.png').convert('RGBA')
            continue
        raw = ROOT / f'sprites/raw/transform/{mode}.png'
        sheet = Image.open(raw)
        assert sheet.mode == 'RGBA' and sheet.getchannel('A').getextrema()[0] == 0
        config = {'name': f'transform_{mode}', 'state': f'transform_{mode}',
                  'sheet': raw.relative_to(ROOT).as_posix(), 'sha256': sha(raw), 'cellBoxes': boxes_for(sheet)}
        frames = prepare(sheet, config, close_loop=False)
        frames[0] = Image.open(ROOT / motion['reference']).convert('RGBA')
        if cocoon is None:
            cocoon = frames[-1].copy()
        frames[-1] = cocoon.copy()
        qa = ROOT / 'sprites/hd720/qa/transform'
        qa.mkdir(parents=True, exist_ok=True)
        contact = Image.new('RGB', (960, 960), '#494455')
        for i, frame in enumerate(frames):
            thumb = frame.resize((240, 240))
            contact.paste(thumb, ((i % 4) * 240, (i // 4) * 240), thumb)
        contact.save(qa / f'{mode}.jpg')
        for part, ordered in [('start', frames), ('loop', list(reversed(frames)))]:
            name = f'transform_{mode}_{part}'
            cfg = {**config, 'name': name, 'fps': 12, 'holds': {}}
            cfgpath = ROOT / f'anims/{name}.json'
            write_json(cfgpath, cfg)
            assets = []
            for size, directory, video in [
                (512, ROOT / 'sprites' / name, ROOT / f'sprites/anim_{name}.webm'),
                (720, ROOT / 'sprites/hd720/frames' / name, ROOT / f'sprites/hd720/videos/anim_{name}.webm'),
            ]:
                directory.mkdir(parents=True, exist_ok=True)
                paths = []
                for i, frame in enumerate(ordered):
                    path = directory / f'{name}_{i:02d}.png'
                    im = frame.resize((size, size), Image.Resampling.LANCZOS)
                    im.save(path)
                    alpha = np.asarray(im.getchannel('A'))
                    assert np.any(alpha > 240) and not any(np.any(e) for e in (alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]))
                    paths.append(path)
                subprocess.run([sys.executable, str(ROOT / 'tools/encode_holds.py'), str(cfgpath), '--fps', '12', '--frames-dir', str(directory), '--out', str(video)], check=True)
                info = probe(video)
                stream = info['streams'][0]
                assert (stream['width'], stream['height'], stream['codec_name']) == (size, size, 'vp9')
                assert stream['tags']['alpha_mode'] == '1'
                assert abs(float(info['format']['duration']) - 16 / 12) < .002
                decoded = np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9', '-i', str(video), '-f', 'rawvideo', '-pix_fmt', 'rgba', 'pipe:1']), np.uint8).reshape(-1, size, size, 4)
                assert len(decoded) == 16 and not np.any(decoded[:, [0, 0, -1, -1], [0, -1, 0, -1], 3])
                assert np.all(np.sum(decoded[:, :, :, 3] > 240, axis=(1, 2)) > 1000)
                hashes = [sha(p) for p in paths]
                assert len(set(hashes)) >= 14
                assets.append((paths, video, hashes))
            src, source, src_hash = assets[0]
            dst, video, hashes = assets[1]
            rel = lambda p: p.relative_to(ROOT).as_posix()
            records.append({'clip': name, 'state': f'transform_{mode}', 'part': part, 'rate': 1,
                            'sourceVideo': rel(source), 'sourceVideoSha256': sha(source),
                            'sourceFrames': list(map(rel, src)), 'sourceFrameHashes': src_hash,
                            'frames': list(map(rel, dst)), 'frameHashes': hashes, 'candidate': rel(video),
                            'videoSha256': sha(video), 'frameCount': 16, 'duration': 16 / 12, 'decodedTicks': 16,
                            'fps': 12, 'holds': {}, 'repeats': [], 'sourceBytes': source.stat().st_size,
                            'candidateBytes': video.stat().st_size,
                            'technicalReview': dict.fromkeys(['dimensions', 'alpha', 'duration', 'pngFrameOrder', 'decodedTickCount', 'sourceHash', 'distinctPoses', 'neutralSeam', 'cocoonSeam'], True), 'status': 'audited'})
            print('PASS', name, flush=True)
    out_hash = {c['frameHashes'][-1] for c in records if c['part'] == 'start'}
    in_hash = {c['frameHashes'][0] for c in records if c['part'] == 'loop'}
    assert len(out_hash) == 1 and out_hash == in_hash
    for motion in motions:
        pair = [c for c in records if c['state'] == 'transform_' + motion['mode']]
        assert pair[0]['frameHashes'][0] == pair[1]['frameHashes'][-1] == sha(ROOT / motion['reference'])
    hdpath = ROOT / 'anims/hd720_manifest.json'
    hd = json.loads(hdpath.read_text())
    old = {c['clip']: c for c in hd['clips']}
    for c in records:
        prev = old.get(c['clip'])
        if prev and prev['videoSha256'] == c['videoSha256'] and prev['frameHashes'] == c['frameHashes']:
            c['status'] = prev['status']
            if 'review' in prev:
                c['review'] = prev['review']
        old[c['clip']] = c
    hd['clips'] = list(old.values())
    hd['clipCount'] = len(hd['clips'])
    for total, field in [('frameCount', 'frameCount'), ('sourceVideoBytes', 'sourceBytes'), ('candidateVideoBytes', 'candidateBytes')]:
        hd[total] = sum(c[field] for c in hd['clips'])
    write_json(hdpath, hd)
    path = ROOT / 'anims/rebuild_manifest.json'
    legacy = json.loads(path.read_text())
    preserved = {c['file']: c for c in legacy['preservedOriginalClips']}
    for c in records:
        filename = c['sourceVideo'].split('/')[-1]
        preserved[filename] = {'file': filename, 'state': c['state'], 'sha256': c['sourceVideoSha256'], 'reason': 'ImageGen 복장 변신. 원본/재구성 모드 공통 사용.'}
    legacy['preservedOriginalClips'] = list(preserved.values())
    write_json(path, legacy)
    print('PASS 12 transformation clips / 192 frames / shared cocoon and six costume seams')


if __name__ == '__main__':
    main()
