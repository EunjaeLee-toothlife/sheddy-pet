"""기념일별 10종 구성과 투명 영상/연결 프레임을 검증하고 배포 자산에 등록한다."""
import argparse
import json
from pathlib import Path

from build_halloween import ROOT, write_json
from verify_halloween import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register', action='store_true')
    parser.add_argument('--mode', choices=['seollal', 'christmas', 'childrensday', 'summer'])
    args = parser.parse_args()
    motions = json.loads((ROOT / 'anims/seasonal/motions.json').read_text())
    assert len(motions) == len({m['id'] for m in motions}) == 40
    for mode in ['seollal', 'christmas', 'childrensday', 'summer']:
        group = [m for m in motions if m['mode'] == mode]
        assert len(group) == 10
        assert {role: sum(m['role'] == role for m in group) for role in ['idle', 'talk', 'special']} == {'idle': 3, 'talk': 1, 'special': 6}
    selected = [m for m in motions if not args.mode or m['mode'] == args.mode]
    records = [verify(m, anchor_state=m['mode'] + '_breathe1') for m in selected]
    if args.register:
        hd_path = ROOT / 'anims/hd720_manifest.json'
        hd = json.loads(hd_path.read_text())
        old = {c['clip']: c for c in hd['clips']}
        for record in records:
            previous = old.get(record['clip'])
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
            preserved[filename] = {'file': filename, 'state': record['state'], 'sha256': record['sourceVideoSha256'], 'reason': 'ImageGen 기념일 전용 모션. 원본/재구성 모드에서 공통 사용.'}
        legacy['preservedOriginalClips'] = list(preserved.values())
        write_json(hd_path, hd)
        write_json(legacy_path, legacy)
    print(f'PASS {len(records)} clips / {sum(c["frameCount"] for c in records)} poses / {sum(c["candidateBytes"] for c in records)} HD bytes')


if __name__ == '__main__':
    main()
