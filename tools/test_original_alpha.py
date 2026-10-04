"""원본 화학 엔딩에서 본체 대신 연기·별만 남았던 프레임의 회귀 검사."""
from pathlib import Path
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


class OriginalAlphaTest(unittest.TestCase):
    def test_character_survives_matte_cleanup(self):
        for clip, index in [('chem1_end1', 4), ('chem1_end3', 16)]:
            with self.subTest(clip=clip, index=index):
                frame = Image.open(ROOT / f'sprites/{clip}/{clip}_{index:02d}.png')
                self.assertEqual(frame.mode, 'RGBA')
                self.assertEqual(frame.size, (512, 512))
                alpha = np.asarray(frame.getchannel('A'))
                # 작은 별 하나가 남아도 max(alpha)=255이므로 본체의 면적을 검사한다.
                self.assertGreater(int((alpha > 240).sum()), 30_000)
                ys, xs = np.nonzero(alpha > 240)
                self.assertGreater(int(ys.max() - ys.min()), 400)
                self.assertGreater(int(xs.max() - xs.min()), 150)
                for edge in (alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]):
                    self.assertFalse(edge.any())


if __name__ == '__main__':
    unittest.main()
