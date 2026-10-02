"""기념일·변신의 고해상도 원본과 두 해상도 영상을 검사하고 자산 목록을 갱신한다."""
import argparse
import json
from pathlib import Path

from build_halloween import ROOT, write_json
from verify_halloween import verify


def verify_state(state):
    geometry = json.loads((ROOT / 'anims/native/geometry.json').read_text())[state]
    records = []
    for part in (['start', 'loop'] if geometry['theme'] == 'transform' else ['loop']):
        config = json.loads((ROOT / f'anims/{state}_{part}.json').read_text())
        assert config['sourcePipeline'] == 'native-pairs-v1', f'미교체 원본: {state}'
        if geometry['theme'] == 'seasonal':
            motion = next(m for m in json.loads((ROOT / 'anims/seasonal/motions.json').read_text()) if m['id'] == state)
        else:
            motion = {'id': state, 'fps': 12, 'holds': {}}
        record = verify(motion, anchor_state=geometry['mode'] + '_breathe1', part=part, transform=geometry['theme'] == 'transform')
        record['technicalReview']['nativeSourceResolution'] = True
        record['technicalReview']['noSourceUpscaling'] = True
        record['technicalReview']['sourcePixelReproduction'] = True
        records.append(record)
    return records


def register(records):
    path = ROOT / 'anims/hd720_manifest.json'
    ledger = json.loads(path.read_text())
    clips = {c['clip']: c for c in ledger['clips']}
    for record in records:
        previous = clips.get(record['clip'])
        if previous and previous['videoSha256'] == record['videoSha256'] and previous['frameHashes'] == record['frameHashes']:
            record['status'] = previous['status']
            if 'review' in previous:
                record['review'] = previous['review']
        clips[record['clip']] = record
    ledger['clips'] = list(clips.values())
    ledger['clipCount'] = len(ledger['clips'])
    for total, field in [('frameCount', 'frameCount'), ('sourceVideoBytes', 'sourceBytes'), ('candidateVideoBytes', 'candidateBytes')]:
        ledger[total] = sum(c[field] for c in ledger['clips'])
    write_json(path, ledger)
    path = ROOT / 'anims/rebuild_manifest.json'
    ledger = json.loads(path.read_text())
    clips = {c['file']: c for c in ledger['preservedOriginalClips']}
    for record in records:
        name = Path(record['sourceVideo']).name
        clips[name] = {'file': name, 'state': record['state'], 'sha256': record['sourceVideoSha256'], 'reason': 'ImageGen 고해상도 원본에서 축소한 기념일·변신 모션. 원본/재구성 모드 공통 사용.'}
    ledger['preservedOriginalClips'] = list(clips.values())
    write_json(path, ledger)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('states', nargs='+')
    parser.add_argument('--register', action='store_true')
    args = parser.parse_args()
    records = [record for state in args.states for record in verify_state(state)]
    if args.register:
        register(records)
    print(f'PASS {len(records)} clips / {sum(c["frameCount"] for c in records)} poses')
