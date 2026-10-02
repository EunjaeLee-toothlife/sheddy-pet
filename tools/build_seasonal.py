"""확정한 기념일 복장별 ImageGen 시트를 기존 투명 영상 파이프라인으로 조립한다."""
import argparse
import json

from build_halloween import ROOT, build


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('states', nargs='*')
    args = parser.parse_args()
    motions = json.loads((ROOT / 'anims/seasonal/motions.json').read_text())
    known = {m['id'] for m in motions}
    if set(args.states) - known:
        parser.error('알 수 없는 모션: ' + ', '.join(sorted(set(args.states) - known)))
    for motion in motions:
        if not args.states or motion['id'] in args.states:
            build(motion, theme='seasonal', anchor_state=motion['mode'] + '_breathe1')
