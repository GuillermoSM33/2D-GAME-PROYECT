"""Physical constraints for the sheriff's two reloads; standard library only."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import make_flashlight as art
from make_powers import load


class ReloadArms(unittest.TestCase):
    def test_bones_elbows_and_wrists_stay_anatomically_consistent(self):
        for other in (False, True):
            for second in (False, True):
                for frame in range(24):
                    hands, angles, held = art.dual_reload_pose(other, frame, second)
                    for hand in range(2):
                        with self.subTest(other=other, second=second, frame=frame, hand=hand):
                            top = art.FAR_TOP if hand else art.SHOULDER
                            lengths = art.FAR_ARM if hand else (7, 7)
                            elbow, wrist = art.reload_bones(top, hands[hand], lengths, -1 if hand else 1)
                            self.assertAlmostEqual(math.dist(top, elbow), lengths[0], places=6)
                            self.assertAlmostEqual(math.dist(elbow, wrist), lengths[1], places=6)
                            upper = (elbow[0] - top[0], elbow[1] - top[1])
                            fore = (wrist[0] - elbow[0], wrist[1] - elbow[1])
                            cross = upper[0] * fore[1] - upper[1] * fore[0]
                            if hand:
                                self.assertLess(cross, 0)
                            else:
                                self.assertGreater(cross, 0)
                            self.assertGreater(elbow[1] - top[1], 3.5, 'Elbow must hang below the shoulder')
                            if 5 <= frame <= 18:
                                self.assertGreaterEqual(wrist[1], 47, 'Reload work stays at the belt')
                            if held[hand]:
                                fore_angle = math.degrees(math.atan2(-fore[1], fore[0]))
                                wrist_bend = abs((angles[hand] - fore_angle + 180) % 360 - 180)
                                self.assertLess(wrist_bend, 45, 'Gun must not fold back across the forearm')

    def test_elbows_do_not_snap_between_poses(self):
        for other in (False, True):
            for second in (False, True):
                previous = [None, None]
                for frame in range(24):
                    hands, _, _ = art.dual_reload_pose(other, frame, second)
                    for hand in range(2):
                        top = art.FAR_TOP if hand else art.SHOULDER
                        lengths = art.FAR_ARM if hand else (7, 7)
                        elbow, _ = art.reload_bones(top, hands[hand], lengths, -1 if hand else 1)
                        if previous[hand] is not None:
                            self.assertLess(math.dist(previous[hand], elbow), 3)
                        previous[hand] = elbow

    def test_rotations_take_the_short_arc(self):
        self.assertAlmostEqual(art.turn_toward(165, -145, .5), 190)
        self.assertAlmostEqual(art.turn_toward(-145, 165, .5), -170)

    def test_finished_first_gun_matches_the_next_handoff(self):
        sheets = [load(art.OUT / (name + '.png')) for name in ('reload_dual', 'reload_dual_b')]
        for sheet in sheets:
            self.assertEqual((sheet.width, sheet.height), (48 * 81, 80))
        for hand in range(2):
            for y in range(80):
                for x in range(81):
                    self.assertEqual(sheets[hand].get(18 * 81 + x, y), sheets[1 - hand].get(24 * 81 + x, y))

    def test_reload_keeps_the_neckline_clear(self):
        sheets = [load(art.OUT / (name + '.png')) for name in ('reload_dual', 'reload_dual_b')]
        for sheet in sheets:
            for frame in range(48):
                for y in range(33, 44):
                    for x in range(29, 37):
                        self.assertEqual(sheet.get(frame * 81 + x, y), sheets[0].get(x, y),
                                         'Reload sleeve must not fold across the chest or neckline')


if __name__ == '__main__':
    unittest.main()
