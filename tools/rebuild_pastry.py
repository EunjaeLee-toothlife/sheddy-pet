"""Align generated pastry donors at their planted feet, preserving pose and effects."""
import argparse
import json
import subprocess
import shutil
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'anims/rebuild_worker_pastry.json'

# Ordinary chef poses match the original/canonical apparent character size.
# Only the overhead celebration needs headroom. Its pre-registered donors are
# already pulled back; intermediate lowered-plate poses ease that camera change.
CHEF_CAMERA_SCALE = .96
OVERHEAD_CAMERA_SCALE = .9594
CAMERA_EASE_SCALE = .87


def align(name):
    folder = ROOT / 'sprites/rebuilt/frames' / name
    records = []
    for path in sorted(folder.glob('*.png')):
        im = Image.open(path).convert('RGBA')
        alpha = np.array(im)[:, :, 3]
        yy, xx = np.where(alpha > 100)
        bottom = int(yy.max())
        # Bottom 20 pixels are the loafers, unaffected by whisk/hair/sparkles.
        shoe_y, shoe_x = np.where((alpha > 100) & (np.indices(alpha.shape)[0] >= bottom - 20))
        center = (int(shoe_x.min()) + int(shoe_x.max()) + 1) / 2
        frame_index = int(path.stem.rsplit('_', 1)[1])
        lift = {('pastry1_outro', 1): 12, ('pastry1_start', 2): 4,
                ('pastry1_start', 7): 6}.get((name, frame_index), 0)
        dx, dy = round(256 - center), 497 - lift - bottom
        out = Image.new('RGBA', im.size)
        out.alpha_composite(im, (dx, dy))
        before = int(np.count_nonzero(alpha > 100))
        after = int(np.count_nonzero(np.array(out)[:, :, 3] > 100))
        if before != after:
            raise ValueError(f'Alignment would crop {path.name}')
        out.save(path)
        records.append({'frame': path.name, 'offset': [dx, dy], 'method': 'planted loafer center/baseline; no scaling or pose replacement'})
    config = ROOT / 'sprites/rebuilt/configs' / (name + '_alignment.json')
    config.write_text(json.dumps(records, indent=2), encoding='utf-8')


def decode(name):
    video = ROOT / 'sprites/rebuilt/videos' / ('anim_' + name + '.webm')
    decoded = subprocess.run(['ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9', '-i', str(video), '-f', 'rawvideo', '-pix_fmt', 'rgba', 'pipe:1'], check=True, capture_output=True).stdout
    arr = np.frombuffer(decoded, dtype=np.uint8).reshape(-1, 512, 512, 4)
    corners = arr[:, [0, 0, -1, -1], [0, -1, 0, -1], 3]
    if np.any(corners != 0) or any(np.count_nonzero(frame[:, :, 3] > 240) == 0 for frame in arr):
        raise ValueError('Decoded alpha failed')
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    clip = next(c for c in data['clips'] if c['clip'] == name)
    clip.setdefault('evidence', {})['decodedAlpha'] = {'frames': len(arr), 'allCornersTransparent': True, 'opaqueForegroundEveryFrame': True}
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Decoded {name}: {len(arr)} frames with alpha')


def common(name):
    folder = ROOT / 'sprites/rebuilt/frames' / name
    source = ROOT / 'sprites/rebuilt/poses/pastry_camera_source/pastry1_end1'
    if not source.exists():
        source = ROOT / 'sprites/rebuilt/frames/pastry1_end1'
    for index in [0, 1, 2, 8, 9, 10, 11]:
        shutil.copyfile(source / f'pastry1_end1_{index:02d}.png', folder / f'{name}_{index:02d}.png')


def seams(name):
    if name.startswith('pastry1_end'):
        pairs = [('pastry1_loop', 0, 0), ('pastry1_outro', 0, 11)]
    elif name == 'pastry1_start':
        pairs = [('pastry1_loop', 0, 13)]
    else:
        pairs = []
    for source_name, source_index, target_index in pairs:
        source = ROOT / 'sprites/rebuilt/frames' / source_name / f'{source_name}_{source_index:02d}.png'
        target = ROOT / 'sprites/rebuilt/frames' / name / f'{name}_{target_index:02d}.png'
        shutil.copyfile(source, target)


def contact(name):
    files = sorted((ROOT / 'sprites/rebuilt/frames' / name).glob('*.png'))
    out = Image.new('RGB', (1024, ((len(files) + 3) // 4) * 256), (230, 230, 230))
    for index, path in enumerate(files):
        im = Image.open(path).convert('RGBA')
        im = Image.alpha_composite(Image.new('RGBA', im.size, (230, 230, 230, 255)), im)
        out.paste(im.convert('RGB').resize((256, 256)), ((index % 4) * 256, (index // 4) * 256))
    path = ROOT / 'sprites/rebuilt/qa' / (name + '_contact.png')
    out.save(path)
    print(path)


def anchor(name):
    loop = Image.open(ROOT / 'sprites/rebuilt/frames/pastry1_loop/pastry1_loop_00.png').convert('RGBA')
    path = ROOT / 'sprites/rebuilt/frames/pastry1_start/pastry1_start_08.png'
    im = Image.open(path).convert('RGBA')
    lb, ib = loop.getbbox(), im.getbbox()
    scale = (lb[3] - lb[1]) / (ib[3] - ib[1])
    cropped = im.crop(ib)
    scaled = cropped.resize((round(cropped.width * scale), round(cropped.height * scale)), Image.Resampling.LANCZOS)
    out = Image.new('RGBA', (512, 512))
    out.alpha_composite(scaled, (256 - scaled.width // 2, lb[3] - scaled.height))
    out.save(path)
    targets = [ROOT / 'sprites/rebuilt/frames/pastry1_outro/pastry1_outro_00.png']
    targets += [ROOT / 'sprites/rebuilt/frames' / f'pastry1_end{i}' / f'pastry1_end{i}_11.png' for i in range(1, 9)]
    for target in targets:
        if target.parent.exists():
            shutil.copyfile(path, target)
    (ROOT / 'sprites/rebuilt/configs/pastry_behind_back_anchor.json').write_text(json.dumps({'reference': 'pastry1_loop_00', 'before': list(ib), 'after': list(out.getbbox()), 'uniformScale': scale}, indent=2), encoding='utf-8')
    print(f'Behind-back anchor normalized: {scale:.5f}, bbox {out.getbbox()}')


def camera(name):
    folder = ROOT / 'sprites/rebuilt/frames' / name
    backups = ROOT / 'sprites/rebuilt/poses/pastry_camera_source' / name
    backups.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted(folder.glob('*.png')):
        index = int(path.stem.rsplit('_', 1)[1])
        if name == 'pastry1_start' and index < 6:
            continue
        if name == 'pastry1_outro' and index > 3:
            continue
        original = backups / path.name
        if not original.exists():
            shutil.copyfile(path, original)
        im = Image.open(original).convert('RGBA')
        bbox = im.getbbox()
        alpha = np.array(im)[:, :, 3]
        rows, columns = np.where(alpha > 100)
        shoe_bottom = int(rows.max())
        shoe_rows, shoe_columns = np.where((alpha > 100) & (np.indices(alpha.shape)[0] >= shoe_bottom - 20))
        shoe_center = (float(shoe_columns.min()) + float(shoe_columns.max()) + 1) / 2
        overhead_ending = name.startswith('pastry1_end') and name not in ['pastry1_end9', 'pastry1_end10']
        if overhead_ending and index in [5, 6]:
            factor, camera_intent = OVERHEAD_CAMERA_SCALE, 'overhead gesture headroom'
        elif overhead_ending and index in [4, 7]:
            factor, camera_intent = CAMERA_EASE_SCALE, 'ease into/out of overhead headroom'
        else:
            factor, camera_intent = CHEF_CAMERA_SCALE, 'original-size ordinary chef pose'
        crop = im.crop(bbox)
        resized = crop.resize((round(crop.width * factor), round(crop.height * factor)), Image.Resampling.LANCZOS)
        if resized.width > 492 or resized.height > 490:
            raise ValueError(f'Camera normalization cannot fit {name}/{index}: {resized.size}; do not crop')
        dx = round(256 - (shoe_center - bbox[0]) * factor)
        lift = {('pastry1_outro', 1): 12, ('pastry1_start', 7): 6}.get((name, index), 0)
        target_baseline = 497 - lift
        dy = round(target_baseline - (shoe_bottom - bbox[1]) * factor)
        if dx < 0 or dy < 0 or dx + resized.width > 512 or dy + resized.height > 512:
            raise ValueError(f'Foot-anchored camera would crop {name}/{index}; do not crop')
        out = Image.new('RGBA', (512, 512))
        out.alpha_composite(resized, (dx, dy))
        out.save(path)
        records.append({'frame': path.name, 'source': original.relative_to(ROOT).as_posix(), 'uniformScale': factor, 'cameraIntent': camera_intent, 'bbox': list(out.getbbox()), 'sourceShoeCenter': shoe_center, 'sourceShoeBottom': shoe_bottom, 'placement': [dx, dy], 'targetShoeCenter': 256, 'targetShoeBaseline': target_baseline, 'intentionalAirborneLift': lift})
    (ROOT / 'sprites/rebuilt/configs' / (name + '_camera.json')).write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(f'Applied common chef camera to {name}: {len(records)} frames')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['align', 'decode', 'common', 'contact', 'anchor', 'camera', 'seams'])
    parser.add_argument('clip')
    parser.add_argument('--manifest', type=Path, default=MANIFEST,
                        help='ledger for decoded-alpha evidence; other actions do not mutate the ledger')
    args = parser.parse_args()
    MANIFEST = args.manifest
    {'align': align, 'decode': decode, 'common': common, 'contact': contact, 'anchor': anchor, 'camera': camera, 'seams': seams}[args.action](args.clip)
