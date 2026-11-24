"""The fuller mane stays connected behind the same protected face and clothes."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import cowgirl_pose as pose
import rework_cowgirl as art


class HairArtTests(unittest.TestCase):
    def test_original_tone_balance_stays_dark_with_sparse_bright_red(self):
        colours = list(art.standing_body().values())
        counts = [colours.count(tone) for tone in art.HAIR]
        total = sum(counts)
        # The earlier sprite was about 43% shadow, 53% base and 4% light.
        # Keeping the palette alone did not prevent a broad orange stripe.
        self.assertAlmostEqual(counts[0] / total, .43, delta=.14)
        self.assertAlmostEqual(counts[1] / total, .53, delta=.14)
        self.assertLessEqual(counts[2] / total, .06)

    def test_mane_has_volume_reaches_the_hip_and_uses_the_original_reds(self):
        source = art._template()
        tones = set(art.HAIR)
        before = {p for p, c in source.items() if c in tones and 22 <= p[1] <= 43 and p[0] < 18}
        for motion in (-1.5, 0, 1.5):
            layer = {}
            art.back_hair(layer, source, 42, motion)
            self.assertTrue(set(layer.values()) <= tones | {art.INK + (255,)})
            hair = {p for p, c in layer.items() if c in tones}
            self.assertGreater(len(hair), len(before) + 35)
            self.assertLessEqual(sum(c == art.HAIR[2] for c in layer.values()), len(hair) * .06,
                                 'Bright red must remain a small accent, not an orange stripe')
            self.assertEqual(max(y for x, y in hair), 43)
            self.assertGreaterEqual(min(x for x, y in layer), 0)
            locks = art._groups(hair)
            self.assertEqual(len(locks), 2, 'Two continuous side locks, without detached red pixels')
            for lock in locks:
                self.assertGreaterEqual(max(y for x, y in lock) - min(y for x, y in lock), 13)

    def test_the_long_lock_hangs_from_her_head_in_every_pose_without_holes(self):
        """Its root goes with her head, its tip only a column or so late; it is one shape."""
        still = art.mane()
        tips = []
        for f in range(pose.FRAMES):
            sway = -.6 + .8 * __import__('math').sin(2 * 3.141592653589793 * pose.phase_of(f) / 5 - .6)
            lock = art.mane(pose.LEAN, sway, pose.bob(f))
            tones = {p for p, c in lock.items() if c in set(art.HAIR)}
            self.assertEqual(len(art._groups(tones)), 1, 'The lock broke')
            for y in range(24, 43):
                row = [x for x, yy in tones if yy == y + pose.bob(f)]
                rest = [x for x, yy in still if yy == y and still[x, yy] in set(art.HAIR)]
                with self.subTest(frame=f, row=y):
                    self.assertTrue(row, 'cut')
                    self.assertLessEqual(abs(min(row) - min(rest)), pose.LEAN + 1, 'It does not swing away from her')
            tips.append(min(x for x, y in tones if y == 42 + pose.bob(f)))
        self.assertLessEqual(max(tips) - min(tips), 2, 'A small sway, not a whip')

    def test_only_her_sleeve_scarf_and_body_hide_the_lock_as_she_runs(self):
        tones = set(art.HAIR)
        for f in range(pose.FRAMES):
            lock = {p for p, c in art.walking_body(f).items() if c in tones and p[0] < 14}
            at = pose.BELT + pose.bob(f)
            near = art.arm_pixels(art.walk_arms(f)[0], at, art.WALK_COLUMN)
            drawn = art.with_arms(art.walking_body(f), near, {})
            for p in lock:
                if drawn[p] not in tones:
                    self.assertIn(p, near, f'frame {f}: something else covered her hair at {p}')


if __name__ == '__main__':
    unittest.main()
