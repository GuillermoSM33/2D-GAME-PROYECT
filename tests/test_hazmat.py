"""Real suit sprites: sealed hoods, extra SWAT protection and intact weapons."""
from pathlib import Path
import math
import sys
import unittest
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from embed_assets import decode_png_rgba
from make_hazmat import INK, read, CHARS
from swat_actions import weapon_pose, READY, AIM
import cowgirl_pose as pose
import hazmat_art as art
import hazmat_figure
import hazmat_legs
import make_hazmat as hazmat

CLOTH, BLUE, GREY = (art.cloth_tones(), {c[:3] for c in art.BLUE}, {c[:3] for c in art.GREY})
WINDOW = art.WINDOW
AMBER = {art.COLORS[k][:3] for k in 'hijko'}
BAND = {art.COLORS[k][:3] for k in 'rR'}         # On the air bottle
# The revolver's steel, shared with nothing the suit is made of.
STEEL = {hazmat.hx(c) for c in (0x30343b, 0x4c535b, 0x777e85, 0xb3b8b6, 0xa1aaa9, 0x747b77)}


@lru_cache(maxsize=None)
def generated(name):
    width, height, source = read(CHARS / 'cowgirl' / (name + '.png'))
    return source, hazmat.suit_cowgirl(source, width, height, name)


def frame_of(px, frame, width):
    return {(x - frame * width, y): c for (x, y), c in px.items() if x // width == frame}


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

    def test_maps_are_whole(self):
        for name in ('HOOD', 'HOOD_FRONT', 'TORSO', 'TORSO_FRONT', 'BELT', 'TANK', 'SWAT_HEAD'):
            rows = getattr(art, name)
            with self.subTest(part=name):
                self.assertEqual(len({len(row) for row in rows}), 1)
                self.assertTrue(set(''.join(rows)) <= set(art.COLORS) | {'.'})

    def test_sheriff_and_swat_have_a_window_over_a_respirator(self):
        for who in ('cowgirl', 'swat'):
            _, _, px = read(CHARS / who / 'suit/stand.png')
            head = {p: c for p, c in px.items() if p[0] < 42 and p[1] < 29}
            with self.subTest(character=who):
                self.assertGreater(sum(c[:3] in WINDOW for c in head.values()), 30)
                self.assertGreater(sum(c[:3] in GREY for c in head.values()), 60)
        _, _, sheriff = read(CHARS / 'cowgirl/suit/stand.png')
        self.assertFalse(any(c[:3] in AMBER for c in sheriff.values()), 'Amber is for the SWAT')
        _, _, swat = read(CHARS / 'swat/suit/stand.png')
        self.assertGreater(sum(c[:3] in AMBER for c in swat.values()), 20)
        # The optical tubes protruded beyond the sealed helmet.
        self.assertNotIn((34, 10), swat)

    def test_the_hood_keeps_the_share_of_her_height_measured_on_the_reference(self):
        """22 columns of hood on the reference (tools/pixel_grid.py), and its head and mask over
        two fifths of the figure: hers, on her own body."""
        self.assertLessEqual(abs(len(art.HOOD[0]) - 22), 1)
        _, _, px = read(CHARS / 'cowgirl/suit/stand.png')
        rows = [y for x, y in px if x < 42]
        self.assertGreater(len(art.HOOD) / (max(rows) - min(rows) + 1), .4)
        self.assertEqual(max(rows), pose.SOLE)

    def test_every_upright_frame_wears_the_whole_suit_and_nothing_of_her_costume(self):
        """The hood, the bottle, the belt and both boots in every frame; no hair, scarf, wine,
        corset or badge left beside them (a yellow rag, a broken sleeve, an unpainted gap)."""
        costume = {hazmat.hx(c) for c in (0x6b333a, 0x902004, 0xd03305, 0x6f2638, 0x924657, 0x441c2a, 0x743044, 0x995367,
                                          0x4c2633, 0xebc1a4, 0xd7a786, 0x404c53, 0x364149)}
        leather = {c[:3] for c in art.LEATHER}
        for sheet in hazmat_figure.UPRIGHT:
            _, suited = generated(sheet)
            width = hazmat_legs.frame_width(sheet)
            count = len(hazmat_figure.layers(sheet))
            for frame in range(count):
                px = frame_of(suited, frame, width)
                with self.subTest(sheet=sheet, frame=frame):
                    found = {c[:3] for c in px.values()} & costume
                    self.assertFalse(found, f'Her costume shows: {found}')
                    ground = max(y for _, y in px)
                    self.assertGreater(sum(c[:3] in leather for (x, y), c in px.items() if y > ground - 8), 14, 'Boots')
                    if sheet.startswith('legs'):
                        continue
                    cx, cy = hazmat_figure.place(sheet, frame)
                    # A hand, a gun or a jug may be held up in front of the window.
                    glass = sum(c[:3] in WINDOW for (x, y), c in px.items() if math.hypot(x - cx, y - cy) < 9)
                    self.assertGreater(glass, 14)
                    arms = hazmat_figure.layers(sheet)[frame][1]
                    bottle = {p: c for p, c in art.tank(cx, cy).items() if p not in arms}
                    shown = sum(px.get(p) == c for p, c in bottle.items())
                    self.assertGreater(shown, .4 * len(bottle), 'The air bottle is always on her back')

    def test_the_torso_has_no_gaps_and_holds_to_its_hood_and_legs(self):
        for sheet in ('stand', 'walk', 'jump', 'shoot', 'reload', 'melee', 'drink', 'plant', 'light_walk'):
            _, suited = generated(sheet)
            width = hazmat_legs.frame_width(sheet)
            for frame in range(len(hazmat_figure.layers(sheet))):
                px = frame_of(suited, frame, width)
                cx, cy = hazmat_figure.place(sheet, frame)
                _, middle, belt = hazmat_legs.upright(sheet, frame)
                with self.subTest(sheet=sheet, frame=frame):
                    for y in range(round(cy) + 6, round(belt) + 3):
                        t = (y - cy) / (belt - cy)
                        x0 = cx + (middle - cx) * t
                        for x in range(round(x0) - 4, round(x0) + 5):
                            self.assertIn((x, y), px, 'A part of the suit was not drawn')

    def test_sheriff_visible_revolver_steel_survives_the_loose_overalls(self):
        _, _, source = read(CHARS / 'cowgirl/shoot.png')
        _, _, suited = read(CHARS / 'cowgirl/suit/shoot.png')
        checked = 0
        for p, color in source.items():
            if p[0] % 81 >= 45 and color[:3] in STEEL:
                self.assertEqual(suited[p], color)
                checked += 1
        self.assertGreater(checked, 100)

    def test_gloves_and_sleeves_are_the_ones_of_her_own_poses(self):
        """Every working hand of hers is there in blue rubber, its sleeve in the suit's cloth
        or in the gauntlet of the glove."""
        from cowgirl_arm import GLOVE, SLEEVE
        patch = {art.COLORS[k][:3] for k in 'EDB'}
        checked = 0
        for sheet in ('walk', 'stand', 'jump', 'shoot', 'shoot_dual', 'shoot_dual_b', 'reload', 'reload_dual',
                      'melee', 'light', 'swap', 'ricochet', 'drink', 'plant'):
            _, suited = generated(sheet)
            width = hazmat_legs.frame_width(sheet)
            for frame, (_, front) in enumerate(hazmat_figure.layers(sheet)):
                for (x, y), tag in front.items():
                    if tag not in GLOVE + SLEEVE or not 0 <= x < width:
                        continue
                    self.assertIn(suited[x + frame * width, y][:3], BLUE if tag in GLOVE else CLOTH | BLUE | patch,
                                  f'{sheet} {frame}: a hand or a sleeve was lost at {x, y}')
                    checked += 1
        self.assertGreater(checked, 4000)

    def test_a_sleeve_in_front_of_her_is_outlined_on_the_suit(self):
        """Cloth of one colour on another of the same, an arm would be lost."""
        from cowgirl_arm import SLEEVE
        sleeves = {c[:3] for c in SLEEVE}
        for sheet in ('walk', 'stand', 'shoot', 'reload'):
            _, suited = generated(sheet)
            width = hazmat_legs.frame_width(sheet)
            for frame, (_, front) in enumerate(hazmat_figure.layers(sheet)):
                px = frame_of(suited, frame, width)
                loose = sum(1 for (x, y), c in front.items() if c[:3] in sleeves
                            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                            if q not in front and px.get(q, (0,))[:3] in CLOTH)
                self.assertEqual(loose, 0, f'{sheet} {frame}: a sleeve melts into the suit')

    def test_sheriff_crossing_does_not_push_fabric_through_the_car_floor(self):
        _, _, source = read(CHARS / 'cowgirl/car.png')
        _, _, suited = read(CHARS / 'cowgirl/suit/car.png')
        for frame in range(55):
            for row in range(2):
                a = [y for (x, y) in source if x // 81 == frame and y // 80 == row]
                b = [y for (x, y) in suited if x // 81 == frame and y // 80 == row]
                self.assertEqual(bool(a), bool(b), 'She is on the same side of the car')
                if a:
                    self.assertLessEqual(max(b), max(a))

    def test_sheriff_walking_reload_preserves_the_whole_foreground_action(self):
        for name in ('reload_dual_lower', 'reload_dual_b_lower'):
            _, _, source = read(CHARS / 'cowgirl' / (name + '.png'))
            _, _, suited = read(CHARS / 'cowgirl/suit' / (name + '.png'))
            self.assertEqual(set(source), set(suited), 'The moving-legs overlay lost an arm, hand or barrel')

    def test_the_suit_runs_stands_and_jumps_on_her_own_legs(self):
        import rework_cowgirl as her
        for sheet, shift in (('walk', (0, 0)), ('walk_dual', (0, 0)), ('light_walk', (12, 7))):
            for frame in range(pose.FRAMES):
                pair, middle, _ = hazmat_legs.upright(sheet, frame)
                for far, chain in zip((True, False), pair):
                    expected = pose.leg_chain(frame, far)
                    for got, want in zip(chain[:3], expected[:3]):
                        self.assertAlmostEqual(got[0], want[0] + shift[0])
                        self.assertAlmostEqual(got[1], want[1] + shift[1])
                self.assertAlmostEqual(middle, pose.hips(frame) + shift[0])
        for frame in range(len(her.JUMP)):
            pair, _, _ = hazmat_legs.upright('jump', frame)
            near = her.JUMP[frame][4]
            self.assertEqual(pair[1][2], (near[2] + her.JUMP_MID, near[3] + her.JUMP_DROP))
        for hip, kn, ankle, _ in hazmat_legs.STAND:
            self.assertLess(abs(hip[0] - ankle[0]), 1.2, 'Resting legs support the hips, without a cowboy flare')
            self.assertLess(abs(kn[0] - hip[0]), .8)

    def test_resting_boots_stand_where_hers_do(self):
        _, _, suited = read(CHARS / 'cowgirl/suit/stand.png')
        lower = [(x, y) for x, y in suited if x < 42 and 48 <= y <= 61]
        self.assertGreaterEqual(min(x for x, _ in lower), 10)
        self.assertLessEqual(max(x for x, _ in lower), 31)
        self.assertEqual(max(y for _, y in lower), pose.SOLE)

    def test_loose_fabric_never_goes_under_a_boot_sole(self):
        for sheet, ground in (('walk', 59), ('light_walk', 66), ('stand', 59), ('shoot', 66)):
            _, suited = generated(sheet)
            self.assertLessEqual(max(y for _, y in suited), ground)

    def test_suit_leaves_no_outline_specks_in_the_air(self):
        around = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
        for who in ('cowgirl', 'swat'):
            for path in sorted((CHARS / who / 'suit').glob('*.png')):
                _, _, suited = read(path)
                ink = {p for p, c in suited.items() if c[:3] == INK}
                specks = [p for p in ink if not any((p[0] + dx, p[1] + dy) in suited for dx, dy in around)]
                with self.subTest(character=who, sheet=path.name):
                    self.assertEqual(specks, [], 'Lone outline pixels float round the hood')

    def test_fainting_is_the_suited_stance_falling_with_nothing_loose(self):
        _, suited = generated('faint')
        for frame in range(8):
            px = frame_of(suited, frame, 80)
            groups = components(px)
            self.assertEqual(len(groups), 1, f'frame {frame}: a loose piece beside her')
            self.assertGreater(sum(c[:3] in WINDOW for c in px.values()), 14)

    def test_sitting_she_faces_us_in_the_whole_suit(self):
        _, suited = generated('sit')
        for frame in range(14):
            px = frame_of(suited, frame, 72)
            with self.subTest(frame=frame):
                self.assertGreater(sum(c[:3] in WINDOW for c in px.values()), 25)
                self.assertGreater(sum(c[:3] in BLUE for c in px.values()), 25, 'Both gloves')
                self.assertGreater(sum(c[:3] in BAND for c in px.values()), 2, 'Her bottle')

    def test_every_frame_of_the_swat_has_one_helmet_and_one_mask(self):
        """The helmet is put by the one it wore: never a second on a grenade, never one squeezed."""
        for path in sorted((CHARS / 'swat/suit').glob('*.png')):
            if path.stem.endswith('_lower'):
                continue
            _, _, px = read(path)
            width = hazmat.SWAT_WIDTHS.get(path.stem, 81)
            for frame in range(max(x for x, _ in px) // width + 1):
                spots = [p for p, c in px.items() if p[0] // width == frame and c[:3] in AMBER]
                with self.subTest(sheet=path.name, frame=frame):
                    # The goggles, their glint and the reflection beside the window.
                    self.assertTrue(20 <= len(spots) <= 44, len(spots))
                    xs, ys = [x for x, _ in spots], [y for _, y in spots]
                    self.assertLess(max(xs) - min(xs), 19)
                    self.assertLess(max(ys) - min(ys), 19)

    def test_swat_carrier_knee_pads_boots_and_air_bottle_are_visible(self):
        _, _, swat = read(CHARS / 'swat/suit/stand.png')

        def seen(tones, box):
            x0, y0, x1, y1 = box
            return sum(c[:3] in tones for (x, y), c in swat.items() if x0 <= x <= x1 and y0 <= y <= y1)
        self.assertGreater(seen(GREY, (12, 26, 29, 42)), 45)
        self.assertGreater(seen(GREY, (8, 44, 31, 54)), 25)
        self.assertGreater(seen({c[:3] for c in art.LEATHER}, (5, 54, 34, 60)), 30)
        self.assertGreaterEqual(seen(GREY | BAND, (3, 25, 9, 44)), 35)
        self.assertGreater(seen(BLUE, (8, 28, 41, 45)), 25)

    def test_swat_walks_in_boots_and_with_its_bottle_whatever_it_holds(self):
        """The game draws its walk from carry and light_walk, not only from walk."""
        for name in ('walk', 'carry', 'carry_shotgun', 'light_walk', 'light_walk_shotgun', 'shoot', 'reload', 'melee', 'throw', 'jump'):
            _, _, px = read(CHARS / 'swat/suit' / f'{name}.png')
            width = hazmat.SWAT_WIDTHS.get(name, 81)
            for frame in range(max(x for x, _ in px) // width + 1):
                one = frame_of(px, frame, width)
                ground = max(y for (x, y), c in one.items() if c[:3] in {q[:3] for q in art.LEATHER})
                soles = [c[:3] for (x, y), c in one.items() if ground - 2 <= y <= ground and c[:3] != INK]
                with self.subTest(sheet=name, frame=frame):
                    self.assertFalse(any(c in CLOTH for c in soles), 'Cloth where its boot is')
                    if name != 'throw':                  # Its arm swings back over the band
                        self.assertGreater(sum(c[:3] in BAND for c in one.values()), 0, 'No bottle on its back')

    def test_rifle_and_shotgun_keep_their_native_visible_pixels(self):
        for kind, suffix in (('rifle', ''), ('shotgun', '_shotgun')):
            name = 'shoot' + suffix + '.png'
            _, _, source = read(CHARS / 'swat' / name)
            _, _, suited = read(CHARS / 'swat/suit' / name)
            for frame, at in ((0, READY), (3, AIM)):
                weapon, _, _, _ = weapon_pose(kind, *at)
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


def components(pixels):
    from rework_cowgirl import _groups
    return _groups(set(pixels))


if __name__ == '__main__':
    unittest.main()
