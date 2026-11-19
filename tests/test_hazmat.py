"""Real suit sprites: sealed hoods, extra SWAT protection and intact weapons."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from embed_assets import decode_png_rgba
from make_hazmat import AMBER_VISOR, ARMOR, VISOR, COW_GUN_STEEL, read, CHARS
from swat_actions import weapon_pose, READY, AIM


class HazmatArtTests(unittest.TestCase):
    def test_every_animation_has_a_matching_opaque_suit_sheet(self):
        for who in ('cowgirl', 'swat'):
            sources = {p.name for p in (CHARS / who).glob('*.png')}
            suits = {p.name for p in (CHARS / who / 'suit').glob('*.png')}
            self.assertEqual(sources, suits)
            for name in sorted(sources):
                with self.subTest(character=who, sheet=name):
                    w, h, _ = decode_png_rgba(CHARS / who / name)
                    sw, sh, pixels = decode_png_rgba(CHARS / who / 'suit' / name)
                    self.assertEqual((w, h), (sw, sh))
                    self.assertTrue(set(pixels[3::4]) <= {0, 255}, 'A mask tag leaked into the game art')

    def test_sheriff_and_swat_have_full_face_shields(self):
        _, _, sheriff = read(CHARS / 'cowgirl/suit/stand.png')
        _, _, swat = read(CHARS / 'swat/suit/stand.png')
        self.assertGreater(sum(c[:3] in VISOR for (x, y), c in sheriff.items() if x < 42 and y < 29), 20)
        self.assertGreater(sum(c[:3] in AMBER_VISOR for (x, y), c in swat.items() if x < 42 and y < 28), 50)
        # The original third optical tube protruded beyond the sealed hood.
        self.assertNotIn((32, 10), swat)

    def test_sheriff_overalls_cover_the_fitted_waist_and_old_badge(self):
        _, _, original = read(CHARS / 'cowgirl/stand.png')
        _, _, sheriff = read(CHARS / 'cowgirl/suit/stand.png')
        # The new garment fills the gaps beside the fitted waist and keeps
        # its width from chest to hip. It has no corset panel or badge glints.
        self.assertNotIn((13, 36), original)
        self.assertIn((13, 36), sheriff)
        for y in (33, 36, 39, 43):
            self.assertTrue(all((x, y) in sheriff for x in range(13, 28)))
        self.assertNotEqual(original[23, 36], sheriff[23, 36])

    def test_sheriff_visible_revolver_steel_survives_the_loose_overalls(self):
        _, _, source = read(CHARS / 'cowgirl/shoot.png')
        _, _, suited = read(CHARS / 'cowgirl/suit/shoot.png')
        checked = 0
        for p, color in source.items():
            if p[0] % 81 >= 45 and color[:3] in COW_GUN_STEEL:
                self.assertEqual(suited[p], color)
                checked += 1
        self.assertGreater(checked, 100)

    def test_sheriff_crossing_does_not_push_fabric_through_the_car_floor(self):
        _, _, source = read(CHARS / 'cowgirl/car.png')
        _, _, suited = read(CHARS / 'cowgirl/suit/car.png')
        for frame in range(55):
            for row in range(2):
                a = [y for (x, y) in source if x // 81 == frame and y // 80 == row]
                b = [y for (x, y) in suited if x // 81 == frame and y // 80 == row]
                if a:
                    self.assertLessEqual(max(b), max(a))

    def test_sheriff_care_actions_keep_the_hood_on(self):
        for name in ('drink', 'bandage', 'plant'):
            width, _, suited = read(CHARS / 'cowgirl/suit' / (name + '.png'))
            for frame in range(width // 81):
                with self.subTest(action=name, frame=frame):
                    glass = sum(c[:3] in VISOR for (x, _), c in suited.items() if x // 81 == frame)
                    self.assertGreater(glass, 20)

    def test_sheriff_walking_reload_preserves_the_whole_foreground_action(self):
        for name in ('reload_dual_lower', 'reload_dual_b_lower'):
            _, _, source = read(CHARS / 'cowgirl' / (name + '.png'))
            _, _, suited = read(CHARS / 'cowgirl/suit' / (name + '.png'))
            self.assertEqual(set(source), set(suited), 'The moving-legs overlay lost an arm, hand or barrel')

    def test_swat_carrier_knee_pads_and_air_pack_are_visible(self):
        _, _, swat = read(CHARS / 'swat/suit/stand.png')
        def armor_in(box):
            x0, y0, x1, y1 = box
            return sum(c[:3] in ARMOR for (x, y), c in swat.items() if x0 <= x <= x1 and y0 <= y <= y1)
        self.assertGreater(armor_in((7, 26, 29, 42)), 45)
        self.assertGreater(armor_in((8, 44, 31, 56)), 25)
        self.assertGreaterEqual(armor_in((7, 27, 10, 43)), 20)

    def test_rifle_and_shotgun_keep_their_native_visible_pixels(self):
        for kind, suffix in (('rifle', ''), ('shotgun', '_shotgun')):
            name = 'shoot' + suffix + '.png'
            _, _, source = read(CHARS / 'swat' / name)
            _, _, suited = read(CHARS / 'swat/suit' / name)
            for frame, pose in ((0, READY), (3, AIM)):
                weapon, _, _, _ = weapon_pose(kind, *pose)
                checked = 0
                for (x, y), color in weapon.px.items():
                    p = x + frame * 81, y
                    # Bright steel is distinct from gloves in the source;
                    # the same dark grey/ink can also be a hand in front.
                    if source.get(p) == color and max(color[:3]) >= 95:
                        with self.subTest(weapon=kind, frame=frame, pixel=p):
                            self.assertEqual(suited.get(p), color)
                        checked += 1
                self.assertGreater(checked, 10)


if __name__ == '__main__':
    unittest.main()
