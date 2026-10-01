"""춤의 이동·투명도와 기존 반응 모션의 재현성을 검사한다."""
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from build_reactions import ROOT, prepare_frames
from slice_and_key import body_box


class ReactionFramesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.reference = Path(self.temp.name) / 'idle.png'
        ref = Image.new('RGBA', (512, 512))
        ImageDraw.Draw(ref).rectangle((200, 100, 300, 400), fill=(255, 200, 100, 255))
        ref.save(self.reference)
        self.sheet = Image.new('RGBA', (2048, 2048))
        for i in range(16):
            x, y = (i % 4) * 512, (i // 4) * 512
            dx, dy = (-60, -40) if i == 1 else (0, 0)
            ImageDraw.Draw(self.sheet).rectangle((x + 200 + dx, y + 100 + dy,
                                                 x + 300 + dx, y + 400 + dy),
                                                fill=(20, 220, 30, 255))

    def test_dance_keeps_translation_jump_and_generated_alpha(self):
        frames = prepare_frames(self.sheet, {'grid': [4, 4], 'preserve_motion': True}, self.reference)
        self.assertEqual(len(frames), 16)
        _, bottom0, center0 = body_box(frames[0])
        _, bottom1, center1 = body_box(frames[1])
        self.assertAlmostEqual(center1 - center0, -60, delta=1)
        self.assertAlmostEqual(bottom1 - bottom0, -40, delta=1)
        self.assertEqual(frames[0].getpixel((250, 250)), (20, 220, 30, 255))
        self.assertEqual(frames[0].getpixel((0, 0))[3], 0)
        self.assertEqual(frames[0].tobytes(), frames[-1].tobytes())

    def test_large_pose_stays_inside_canvas_without_clipping(self):
        ImageDraw.Draw(self.sheet).rectangle((512 + 20, 20, 512 + 480, 480), fill='white')
        frames = prepare_frames(self.sheet, {'grid': [4, 4], 'preserve_motion': True}, self.reference)
        for frame in frames:
            left, top, right, bottom = frame.getchannel('A').getbbox()
            self.assertGreater(left, 0)
            self.assertGreater(top, 0)
            self.assertLess(right, 512)
            self.assertLess(bottom, 512)

    def test_existing_green_sheet_reproduces_committed_frames(self):
        config = json.loads((ROOT / 'anims/obs_reactions.json').read_text())['clap1']
        frames = prepare_frames(Image.open(ROOT / config['sheet']), config,
                                ROOT / 'sprites/rebuilt/frames/idle1_loop/idle1_loop_00.png')
        self.assertEqual(len(frames), 8)
        for i, frame in enumerate(frames):
            expected = Image.open(ROOT / f'sprites/clap1_loop/clap1_loop_{i:02d}.png')
            self.assertEqual(frame.tobytes(), expected.tobytes())


if __name__ == '__main__':
    unittest.main()
