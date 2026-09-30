"""Record static review evidence without claiming unperformed browser seam QA."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding='utf-8'))
    for name, food in [('pastry1_end6', 'golden caramel custard pudding with dripping dark caramel and red cherry'), ('pastry1_end7', 'golden layered crescent croissant'), ('pastry1_end8', 'upright vanilla soft-serve waffle cone with red cherry on white plate')]:
        clip = next(c for c in data['clips'] if c['clip'] == name)
        folder = ROOT / 'sprites/rebuilt/frames' / name
        anchors = []
        for index, reference in [(0, 'pastry1_loop/pastry1_loop_00.png'), (11, 'pastry1_outro/pastry1_outro_00.png')]:
            frame = folder / f'{name}_{index:02d}.png'
            donor = ROOT / 'sprites/rebuilt/frames' / reference
            assert digest(frame) == digest(donor)
            anchors.append({'frame': index, 'reference': 'sprites/rebuilt/frames/' + reference, 'pixelIdentical': True, 'sha256': digest(frame)})
        common = []
        for index in [0, 1, 2, 8, 9, 10, 11]:
            hashes = [digest(ROOT / 'sprites/rebuilt/frames' / f'pastry1_end{n}' / f'pastry1_end{n}_{index:02d}.png') for n in [6, 7, 8]]
            assert len(set(hashes)) == 1
            common.append(index)
        clip['review']['style'] = True
        clip['review']['motion'] = True
        clip['review']['seams'] = False
        clip['evidence']['exactSeamAnchors'] = anchors
        clip['evidence']['commonFoodIndependentFrames'] = common
        clip['visualReviewNotes'] = [
            'All 12 original PNG poses and source pose descriptions compared with the final per-frame contact sheet.',
            'Food identity preserved: ' + food + '; food disappears by the empty-plate NOM slot 8.',
            'Generated from a shared chef display master using food-only ImageGen edits. Retains starry admire, raised plate with visible toque, eyes-closed then eyes-open overhead hold, eager mouth/plate lowering, empty plate, two pink hearts, cheek touch and behind-back ending.',
            'White jacket and facial interiors have clean flat fills; intentional magical glows in slots 1/2 remain.',
            'Shared camera normal scale 0.78, overhead scale 0.9594, feet-band center 256 and baseline 497; no nonuniform scaling or cropping.',
            'Shared eating slots 8/9 corrected using the generated puffed-cheek master: both clearly swollen chipmunk cheeks, closed H-shaped chewing mouth, closed eyes, empty plate chest-to-waist and two hearts retained. Source prompt prompts/rebuild/pastry_eating_puff_correction.md.',
            'Display slot 7 appears slightly smaller than slot 4 in the shared display master; final browser scale/seam review remains the parent responsibility. All original action stages remain present.',
            'Browser playback and state-machine transition seams not inspected by this worker; seams remain false.'
        ]
    args.manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Recorded static style and exact shared anchor evidence for pastry endings 6-8')


if __name__ == '__main__':
    main()
