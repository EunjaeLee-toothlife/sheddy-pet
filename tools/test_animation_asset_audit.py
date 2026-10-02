"""같은 프레임 수·길이로 인코딩해도 포즈/hold가 바뀌면 검출하는지 확인한다."""
import unittest

import numpy as np

from audit_animation_assets import compare_sequence, ticks


class SequenceAuditTest(unittest.TestCase):
    def setUp(self):
        self.poses = np.zeros((3, 8, 8, 4), dtype=np.float32)
        for i in range(3):
            self.poses[i, 1:7, 1:7, i] = 1
            self.poses[i, 1:7, 1:7, 3] = 1

    def test_swapped_poses_are_detected(self):
        _, errors = compare_sequence(self.poses, self.poses[[0, 2, 1]], [0, 1, 2])
        self.assertEqual([e['tick'] for e in errors], [1, 2])

    def test_same_duration_wrong_hold_is_detected(self):
        order = ticks(3, {'holds': {'1': 3}})
        self.assertEqual(order, [0, 1, 1, 1, 2])
        _, errors = compare_sequence(self.poses, self.poses[[0, 0, 0, 1, 2]], order)
        self.assertEqual([e['tick'] for e in errors], [1, 2])

    def test_repeats_and_small_compression_noise(self):
        order = ticks(3, {'holds': {'1': 2}, 'repeats': [{'frames': [0, 1], 'times': 2}]})
        self.assertEqual(order, [0, 1, 1, 0, 1, 1, 2])
        _, errors = compare_sequence(self.poses, self.poses[order] * .999, order)
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
