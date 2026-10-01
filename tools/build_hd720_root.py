"""고해상도 생성 원본과 기존 동작 계획으로 기본 모션 13개를 720px로 재현한다."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import minimum_filter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from slice_and_key import chroma_key
import compose_anim
import compose_idle
import compose_happy1
import compose_talk

SIZE = 720
FACTOR = SIZE / 512
OUT = ROOT / 'sprites/hd720'
OWNED = ['idle1_loop', 'basic1_loop', 'basic2_loop', 'basic3_loop', 'happy1_start',
         'happy1_loop', 'happy1_end', 'happy2_loop', 'excited1_loop', 'boxing1_loop',
         'sad1_loop', 'sad2_loop', 'talk_loop']
SOURCES = {}
REPAIR_QA = OUT / 'qa/pastry/root_green_repair'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard_snapshot():
    """원본과 다른 담당 자산의 해시를 보존해 이번 실행의 변경 범위를 검증한다."""
    paths = list((ROOT / 'sprites/rebuilt/frames').rglob('*.png'))
    paths += list((ROOT / 'sprites/rebuilt/raw_poses').glob('*.png'))
    paths += list((ROOT / 'sprites/rebuilt/sheets').glob('*.png'))
    for folder in (OUT / 'frames').iterdir():
        if folder.is_dir() and folder.name not in OWNED:
            paths += list(folder.glob('*.png'))
    paths += [p for p in (OUT / 'videos').glob('*.webm')
              if p.stem.removeprefix('anim_') not in OWNED]
    ledger = json.loads((ROOT / 'anims/rebuild_manifest.json').read_text(encoding='utf-8'))
    for clip in ledger['clips']:
        paths += [ROOT / p for p in clip['frames']]
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in set(paths)}


def clean_matte(name, previous):
    """반투명 외곽 띠의 과도한 녹색만 바꾸고 알파와 내부 색은 정확히 보존한다."""
    records = []
    for path in sorted((OUT / 'frames' / name).glob('*.png')):
        im = Image.open(path).convert('RGBA')
        before = np.array(im)
        rgb = before[:, :, :3].astype(int)
        alpha = before[:, :, 3]
        band = minimum_filter(alpha, size=9) < 250
        excess = rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2])
        mask = band & (excess > 20) & (alpha > 20) & (alpha < 250)
        after = before.copy()
        after[:, :, 1] = np.where(mask, np.maximum(rgb[:, :, 0], rgb[:, :, 2]), rgb[:, :, 1]).astype(np.uint8)
        assert np.array_equal(after[:, :, 3], before[:, :, 3])
        assert np.array_equal(after[:, :, [0, 2]], before[:, :, [0, 2]])
        assert np.array_equal(after[~mask], before[~mask])
        assert Image.fromarray(after).getbbox() == im.getbbox()
        if path.as_posix() in previous:
            old = np.array(Image.open(io.BytesIO(previous[path.as_posix()])).convert('RGBA'))
            assert np.array_equal(old, before) or np.array_equal(old, after), path
        REPAIR_QA.mkdir(parents=True, exist_ok=True)
        baseline = REPAIR_QA / (path.stem + '_before.png')
        if baseline.exists():
            assert np.array_equal(np.array(Image.open(baseline).convert('RGBA')), before), baseline
        else:
            im.save(baseline)
        maskpath = REPAIR_QA / (path.stem + '_mask.png')
        Image.fromarray(mask.astype(np.uint8) * 255).save(maskpath)
        if mask.any():
            Image.fromarray(after).save(path)
        yy, xx = np.where(mask)
        records.append({'frame': path.relative_to(ROOT).as_posix(), 'beforeSHA256': sha(baseline),
                        'afterSHA256': sha(path), 'mask': maskpath.relative_to(ROOT).as_posix(),
                        'maskSHA256': sha(maskpath), 'changedPixels': int(mask.sum()),
                        'changedBBox': None if not len(xx) else [int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)],
                        'alphaExact': True, 'redBlueExact': True, 'outsideMaskExact': True,
                        'bboxExact': True, 'opaquePixelsExact': True})
    return records


def invoke(module, args):
    sys.argv = [module.__name__, *map(str, args)]
    module.main()


def donor(path):
    old = Path(path)
    target = OUT / 'poses/root' / old.name
    if str(old) in SOURCES:
        return ROOT / SOURCES[str(old)]['target']
    if 'batches' in old.parts:
        sheet = ROOT / 'sprites/rebuilt/sheets' / (old.parent.name + '.png')
        cell = int(old.stem.split('_')[-1])
        source = Image.open(sheet).convert('RGB')
        side = source.width // 2
        raw = source.crop(((cell % 2) * side, (cell // 2) * side,
                           (cell % 2 + 1) * side, (cell // 2 + 1) * side))
        cell_box = [(cell % 2) * side, (cell // 2) * side,
                    (cell % 2 + 1) * side, (cell // 2 + 1) * side]
        target = OUT / 'poses/root' / f'{old.parent.name}_{old.name}'
    else:
        sheet = ROOT / 'sprites/rebuilt/raw_poses' / (old.stem.removesuffix('_00') + '.png')
        raw = Image.open(sheet).convert('RGB')
        cell_box = [0, 0, raw.width, raw.height]
    target.parent.mkdir(parents=True, exist_ok=True)
    keyed = chroma_key(raw.resize((SIZE, SIZE), Image.Resampling.LANCZOS), keep_components=True)
    keyed.save(target)
    SOURCES[str(old)] = {'source': sheet.relative_to(ROOT).as_posix(), 'nativeCell': list(raw.size),
                         'sourceSHA256': hashlib.sha256(sheet.read_bytes()).hexdigest(), 'nativeCellBox': cell_box,
                         'target': target.relative_to(ROOT).as_posix(), 'sourceLimited': min(raw.size) < SIZE}
    return target


def main():
    guards = guard_snapshot()
    previous = {p.as_posix(): p.read_bytes() for name in OWNED
                for p in (OUT / 'frames' / name).glob('*.png')}
    ledger = json.loads((ROOT / 'anims/rebuild_manifest.json').read_text(encoding='utf-8'))
    clips = {c['clip']: c for c in ledger['clips']}
    base = donor('sprites/rebuilt/poses/idle_open_00.png')
    closed = donor('sprites/rebuilt/poses/idle_closed_00.png')
    compose_idle.EYE_RECTS = [tuple(round(v * FACTOR) for v in r) for r in compose_idle.EYE_RECTS]
    compose_idle.FEATHER = round(compose_idle.FEATHER * FACTOR)
    compose_idle.PLAN = [(eye, bob * FACTOR) for eye, bob in compose_idle.PLAN]
    invoke(compose_idle, ['--base', base, '--closed', closed, '--register-closed',
                         '--outdir', OUT / 'frames/idle1_loop', '--prefix', 'idle1_loop'])
    # 같은 좌표 단위를 쓰되 더 큰 원본에서 동작을 직접 합성한다.
    for name in ['basic1', 'basic2', 'basic3', 'happy2', 'excited1', 'boxing1', 'sad1', 'sad2']:
        plan = json.loads((ROOT / f'sprites/rebuilt/configs/{name}_plan.json').read_text(encoding='utf-8'))
        plan['base'] = str(donor(plan['base']))
        plan['poses'] = {key: str(donor(path)) for key, path in plan.get('poses', {}).items()}
        for frames in plan['parts'].values():
            for frame in frames:
                for key in ('dx', 'dy'):
                    if key in frame:
                        frame[key] *= FACTOR
        path = OUT / f'configs/{name}_plan.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        # 저장된 계획은 다른 체크아웃에서도 재현할 수 있는 저장소 상대경로다.
        plan['base'] = Path(plan['base']).relative_to(ROOT).as_posix()
        plan['poses'] = {k: Path(v).relative_to(ROOT).as_posix() for k, v in plan['poses'].items()}
        path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        invoke(compose_anim, [path, '--outdir', OUT / f'frames/{name}_loop'])
    compose_happy1.BOUNCE = [v * FACTOR for v in compose_happy1.BOUNCE]
    invoke(compose_happy1, ['--base', base, '--mid', donor('sprites/rebuilt/poses/happy1_mid_00.png'),
                           '--full', donor('sprites/rebuilt/poses/happy1_full_00.png'),
                           '--outdir', OUT / 'frames', '--split-parts'])
    compose_talk.FEATHER = round(compose_talk.FEATHER * FACTOR)
    invoke(compose_talk, ['--base', base, '--open', donor('sprites/rebuilt/poses/talk_open_00.png'),
                         '--half', donor('sprites/rebuilt/poses/talk_half_00.png'),
                         '--mouth-rect', *[round(v * FACTOR) for v in compose_talk.MOUTH_RECT],
                         '--outdir', OUT / 'frames/talk_loop'])
    results = []
    for name in OWNED:
        clip = clips[name]
        folder = OUT / 'frames' / name
        frames = sorted(folder.glob('*.png'))
        assert len(frames) == clip['count'], name
        assert all(Image.open(p).size == (SIZE, SIZE) for p in frames), name
        repair = clean_matte(name, previous)
        config = OUT / 'configs' / f'{name}.json'
        config.write_text(json.dumps({'name': name, 'holds': clip.get('holds', {}),
                                      'repeats': clip.get('repeats', [])}), encoding='utf-8')
        video = OUT / 'videos' / ('anim_' + name + '.webm')
        video.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, str(ROOT / 'tools/encode_holds.py'), str(config),
                        '--frames-dir', str(folder), '--fps', str(clip['fps']), '--out', str(video)], check=True)
        contact = Image.new('RGB', (4 * 180, ((len(frames) + 3) // 4) * 180), '#eeeeee')
        for i, path in enumerate(frames):
            im = Image.open(path).convert('RGBA')
            bg = Image.new('RGBA', im.size, '#eeeeee')
            bg.alpha_composite(im)
            contact.paste(bg.convert('RGB').resize((180, 180), Image.Resampling.LANCZOS), ((i % 4) * 180, (i // 4) * 180))
        qa = ROOT / 'sprites/rebuilt/qa/hd720_root'
        qa.mkdir(parents=True, exist_ok=True)
        contact.save(qa / f'{name}.png')
        results.append({'clip': name, 'frameCount': len(frames), 'fps': clip['fps'],
                        'duration': clip['sourceDuration'], 'sourceVideo': clip['candidate'],
                        'video': video.relative_to(ROOT).as_posix(),
                        'videoSha256': hashlib.sha256(video.read_bytes()).hexdigest(),
                        'matteRepair': {'condition': 'minimum_filter(alpha,size=9)<250 & G-max(R,B)>20 & 20<alpha<250',
                                        'records': repair},
                        'method': 'Native ImageGen raw donors keyed at720; original procedural motion and patch coordinates scaled720/512.'})
    mismatches = [p for p, expected in guards.items() if sha(ROOT / p) != expected]
    assert not mismatches, mismatches
    REPAIR_QA.mkdir(parents=True, exist_ok=True)
    (REPAIR_QA / 'scope_guard.json').write_text(json.dumps({'checkedFiles': len(guards),
        'allUnchanged': True, 'hashes': guards}, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'anims/hd720_root.json').write_text(json.dumps({'size': SIZE, 'clips': results, 'donors': SOURCES}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
