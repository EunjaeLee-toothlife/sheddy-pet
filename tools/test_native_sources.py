"""실제 생성 원본 증빙이 틀리면 배포 검증을 통과할 수 없는지 검사한다."""
import copy
import json
import unittest

from build_halloween import ROOT
from verify_native_sources import verify_sources


class NativeSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / 'anims/christmas_breathe1_loop.json').read_text())

    def test_real_sources_reproduce_all_frames(self):
        verify_sources(self.config)

    def test_invalid_source_evidence_is_rejected(self):
        for field, value in [('scale', 1.1), ('sourceSha256', 'tampered'), ('nativeSize', [313, 313])]:
            with self.subTest(field=field):
                config = copy.deepcopy(self.config)
                config['nativeSources'][0][field] = value
                with self.assertRaises(AssertionError):
                    verify_sources(config)

    def test_missing_pose_evidence_is_rejected(self):
        config = copy.deepcopy(self.config)
        config['nativeSources'].pop()
        with self.assertRaises(AssertionError):
            verify_sources(config)


if __name__ == '__main__':
    unittest.main()
