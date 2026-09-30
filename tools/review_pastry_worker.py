"""Record contact-sheet review and exact shared pastry anchors after audit/decode."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / 'anims/rebuild_worker_pastry.json'
OWNED = ['pastry1_start', 'pastry1_loop', 'pastry1_outro'] + [f'pastry1_end{i}' for i in range(1, 6)]

def frame(clip, index):
    return ROOT / 'sprites/rebuilt/frames' / clip / f'{clip}_{index:02d}.png'

def equal(left, right):
    assert left.read_bytes() == right.read_bytes(), (left, right)
    return {'candidate': left.relative_to(ROOT).as_posix(), 'reference': right.relative_to(ROOT).as_posix(), 'byteExact': True}

data = json.loads(LEDGER.read_text(encoding='utf-8'))
for clip in data['clips']:
    name = clip['clip']
    if name not in OWNED:
        continue
    evidence = clip['evidence']
    assert evidence['originalsUnchanged'] and evidence['timingPreserved']
    assert not evidence['framesTouchingCanvas']
    assert evidence['decodedAlpha']['allCornersTransparent']
    clip['review'] = {'style': True, 'motion': False, 'alpha': True, 'seams': False}
    evidence['visualReview'] = {
        'contact': f'sprites/rebuilt/qa/{name}_contact.png',
        'allFramesViewed': True,
        'whiteCostumeAndFaceClean': True,
        'chefHatPreserved': True,
        'majorActionsComparedWithSourceDescriptions': True,
        'browserPlaybackReviewed': False,
        'note': 'Contact sheets preserve transformation, mixing, food reveal, overhead plate with visible toque, puffed-cheek chewing, and return actions. Temporal smoothness and full browser transitions remain for integration review.'
    }
    evidence['cameraConfig'] = f'sprites/rebuilt/configs/{name}_camera.json'
    anchors = []
    if name == 'pastry1_start':
        anchors += [equal(frame(name, 13), frame('pastry1_loop', 0)), equal(frame(name, 8), frame('pastry1_outro', 0))]
    elif name == 'pastry1_loop':
        anchors += [equal(frame(name, 13), frame(name, 0))]
    elif name == 'pastry1_outro':
        anchors += [equal(frame(name, 9), ROOT / 'sprites/rebuilt/poses/idle_open_00.png')]
    else:
        anchors += [equal(frame(name, 0), frame('pastry1_loop', 0)), equal(frame(name, 11), frame('pastry1_outro', 0))]
        evidence['sharedFoodIndependentFrames'] = [equal(frame(name, i), frame('pastry1_end1', i)) for i in [0, 1, 2, 8, 9, 10, 11]]
        evidence['eatingCorrectionPrompt'] = 'prompts/rebuild/pastry_eating_puff_correction.md'
    evidence['exactSeamAnchors'] = anchors
    assert evidence['videoSha256'] == hashlib.sha256((ROOT / clip['candidate']).read_bytes()).hexdigest()
    print(f'{name}: {clip["count"]} PNG slots, {evidence["decodedAlpha"]["frames"]} decoded ticks; exact anchors {len(anchors)}')
LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
