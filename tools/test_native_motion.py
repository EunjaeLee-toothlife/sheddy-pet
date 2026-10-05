"""포즈 원본의 규격·확대 금지와 18프레임 재현 검사를 검증한다."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

import build_native_motion
import verify_native_sources


class NativeMotionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'anims/native').mkdir(parents=True)

    def prepare(self, size=720, height=500, clipped=False):
        image = Image.new('RGBA', (size * 3, size))
        draw = ImageDraw.Draw(image)
        for i in range(3):
            draw.rectangle((i * size + (0 if clipped else 20), 20,
                            (i + 1) * size - 21, size - 21), fill=(220, 150, i * 60, 255))
        image.save(self.root / 'source.png')
        cfg = {'name': 'sample_loop', 'fps': 12, 'holds': {}, 'frames': ['pose'] * 18}
        (self.root / 'anims/sample_loop.json').write_text(json.dumps(cfg))
        geometry = {'sample': {'theme': 'dance', 'mode': 'normal', 'anchor': '',
                    'poses': [{'height': height, 'x': 360, 'bottom': 680}] * 18,
                    'sources': [{'path': 'source.png', 'columns': 3, 'cell': i % 3} for i in range(18)]}}
        (self.root / 'anims/native/geometry.json').write_text(json.dumps(geometry))

    def build(self):
        with patch.object(build_native_motion, 'ROOT', self.root), patch.object(build_native_motion.subprocess, 'run'):
            build_native_motion.build('sample')

    def test_eighteen_poses_reproduce_exactly_and_detect_pixel_changes(self):
        self.prepare()
        self.build()
        cfg = json.loads((self.root / 'anims/sample_loop.json').read_text())
        with patch.object(verify_native_sources, 'ROOT', self.root):
            verify_native_sources.verify_sources(cfg)
            frame = self.root / 'sprites/hd720/frames/sample_loop/sample_loop_05.png'
            image = Image.open(frame)
            image.putpixel((360, 360), (0, 0, 0, 0))
            image.save(frame)
            with self.assertRaisesRegex(AssertionError, '원본 재현 불일치'):
                verify_native_sources.verify_sources(cfg)

    def test_small_native_cells_are_rejected(self):
        self.prepare(size=512)
        with self.assertRaisesRegex(AssertionError, '원본 셀 규격 미달'):
            self.build()

    def test_upscaling_is_rejected(self):
        self.prepare(height=700)
        with self.assertRaisesRegex(AssertionError, '원본 확대 금지'):
            self.build()

    def test_clipped_sources_are_rejected(self):
        self.prepare(clipped=True)
        with self.assertRaisesRegex(AssertionError, '원본 잘림'):
            self.build()


if __name__ == '__main__':
    unittest.main()
