"""대기·말하기의 전신 흔들림과 루프 연결 회귀를 실제 PNG로 검사한다."""
import json
import unittest

import numpy as np
from PIL import Image

from compose_calm_motion import ROOT, CONFIG, frames, variants


class CalmMotionTest(unittest.TestCase):
    def test_expression_changes_stay_inside_face(self):
        for mode, config in json.loads(CONFIG.read_text()).items():
            poses = variants(config)
            base = np.array(poses['base'])
            for name, pose in poses.items():
                if name == 'base':
                    continue
                with self.subTest(mode=mode, pose=name):
                    allowed = np.zeros(base.shape[:2], bool)
                    boxes = config['eyeRects'] if name == 'blink' else [config['mouthRect']]
                    for x0, y0, x1, y1 in boxes:
                        allowed[y0:y1, x0:x1] = True
                    actual = np.array(pose)
                    self.assertTrue(np.array_equal(actual[~allowed], base[~allowed]))
                    self.assertTrue(np.array_equal(actual[:, :, 3], base[:, :, 3]))

    def test_breathing_feet_and_seam(self):
        for mode, config in json.loads(CONFIG.read_text()).items():
            images = frames(config, 'idle')
            base = np.array(images[0])
            self.assertEqual(images[0].tobytes(), images[-1].tobytes(), mode)
            for frame in images:
                self.assertTrue(np.array_equal(np.array(frame)[560:], base[560:]), mode)

    def test_exported_talk_has_no_body_motion(self):
        for mode, config in json.loads(CONFIG.read_text()).items():
            state = 'witchtalk1' if mode == 'halloween' else mode + '_talk1'
            folder = ROOT / f'sprites/hd720/frames/{state}_loop'
            base = np.array(Image.open(ROOT / config['base']))
            allowed = np.zeros(base.shape[:2], bool)
            x0, y0, x1, y1 = config['mouthRect']
            allowed[y0:y1, x0:x1] = True
            for path in sorted(folder.glob('*.png')):
                with self.subTest(mode=mode, frame=path.name):
                    self.assertTrue(np.array_equal(np.array(Image.open(path))[~allowed], base[~allowed]))


if __name__ == '__main__':
    unittest.main()
