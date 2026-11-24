"""Physical constraints for the sheriff's reloads; standard library only."""
import math
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import make_flashlight as art
import cowgirl_reload as single
from cowgirl_arm import arm_limb, glove, pistol_muzzle, pistol_pointing
from make_powers import load
import cowgirl_torso as figure
from rework_cowgirl import CROOK, HAIR, SKIN

# Her star and a snap give way to cloth where the near arm covers most of them, and the few
# pixels of hair in the crook of that arm to her jacket in shade (behind_arm).
BRASSES = figure.STAR_TONES | figure.SNAP_TONES
SHADE = figure.COLORS['d']


class ReloadArms(unittest.TestCase):
    def test_walking_overlay_keeps_every_low_held_gun_and_glove(self):
        # The walk joins at row 46, with ground rows 61 (walk) and 68
        # (reload): action pixels from row 53 must survive the torso cut.
        split = 46 + 68 - 61
        for other, name in ((False, 'reload_dual_lower'), (True, 'reload_dual_b_lower')):
            overlay = load(art.OUT / (name + '.png'))
            for second in (False, True):
                for frame in range(24):
                    hands, angles, held = art.dual_reload_pose(other, frame, second)
                    for hand in range(2):
                        top = art.FAR_TOP if hand else art.SHOULDER
                        lengths = art.FAR_ARM if hand else (7, 7)
                        elbow, wrist = art.reload_bones(top, hands[hand], lengths, -1 if hand else 1)
                        expected = art.glove(wrist, elbow)
                        if held[hand]:
                            expected.update(art.pistol_pointing(wrist, angles[hand]))
                        with self.subTest(other=other, second=second, frame=frame, hand=hand):
                            for x, y in expected:
                                if split <= y < 80:
                                    self.assertNotEqual(overlay.get((frame + second * 24) * 81 + x, y)[3], 0,
                                                        'Walking lost a hand or a segment of its held revolver')

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
                    for x in range(31, 38):
                        at = sheets[0].get(x, y)
                        if at not in BRASSES:
                            self.assertEqual(sheet.get(frame * 81 + x, y), at,
                                             'Reload sleeve must not fold across the chest or neckline')


class SingleReloadArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = art.body_without_arm({}, {}, {}, False)
        cls.aim = art.body_without_arm({}, {}, {}, True)
        cls.aim.update(art.held_gun((0, 0))[0])
        cls.frames = single.single_reload_frames(cls.body, cls.aim)

    def test_fixed_shoulders_and_bones_with_elbows_below_them(self):
        expected_tops = (art.SHOULDER, art.FAR_TOP)
        for frame in range(7):
            for hand, bone in enumerate((6.5, 7.5)):
                with self.subTest(frame=frame, hand=hand):
                    top, elbow, wrist = single.joints(frame)[hand]
                    self.assertEqual(top, expected_tops[hand])
                    self.assertAlmostEqual(math.dist(top, elbow), bone, places=6)
                    self.assertAlmostEqual(math.dist(elbow, wrist), bone, places=6)
                    self.assertGreater(elbow[1] - top[1], 2,
                                       'Reload elbows must stay below their shoulders')
            gun_arm, _, angle = single.joints(frame)
            forearm = (gun_arm[2][0] - gun_arm[1][0], gun_arm[2][1] - gun_arm[1][1])
            forearm_angle = math.degrees(math.atan2(-forearm[1], forearm[0]))
            self.assertLess(abs((angle - forearm_angle + 180) % 360 - 180), 45,
                            'The reload must lift the forearm rather than break the wrist backward')

    def test_bones_turn_smoothly_and_each_arm_is_one_connected_shape(self):
        # Each key lasts 150 ms. A bone must not rotate into the opposite
        # elbow solution between adjacent keys, including the belt reach.
        for hand in range(2):
            previous = None
            for frame in range(7):
                limb = single.joints(frame)[hand]
                if previous is not None:
                    for a, b in ((0, 1), (1, 2)):
                        before = (previous[b][0] - previous[a][0], previous[b][1] - previous[a][1])
                        after = (limb[b][0] - limb[a][0], limb[b][1] - limb[a][1])
                        cosine = sum(x * y for x, y in zip(before, after)) / (
                            math.hypot(*before) * math.hypot(*after))
                        self.assertLess(math.degrees(math.acos(max(-1, min(1, cosine)))), 60,
                                        'Reload elbow flipped to the other side')
                previous = limb
                top, elbow, wrist = limb
                pixels = set(arm_limb(top, elbow, wrist, corner_radius=1.0)) | set(glove(wrist, elbow))
                reached = {next(iter(pixels))}
                todo = list(reached)
                while todo:
                    x, y = todo.pop()
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            at = (x + dx, y + dy)
                            if at in pixels and at not in reached:
                                reached.add(at)
                                todo.append(at)
                self.assertEqual(reached, pixels, 'Reload sleeve or glove detached')

    def test_upright_gun_cylinder_and_loading_hand_stay_together(self):
        for frame in range(1, 6):
            gun_arm, helper_arm, angle = single.joints(frame)
            wrist, helper = gun_arm[2], helper_arm[2]
            muzzle = pistol_muzzle(wrist, angle)
            self.assertGreater(wrist[1] - muzzle[1], 13,
                               'The reference reload holds its barrel upright')
            self.assertLess(abs(muzzle[0] - wrist[0]), 6)
            cylinder = single.cylinder_position(wrist, angle)
            # An open cylinder swings out from the actual weapon, rather
            # than becoming a disconnected metal wheel on the chest.
            gun_pixels = pistol_pointing(wrist, angle)
            self.assertLess(min(math.dist(cylinder, p) for p in gun_pixels), 2.5)
            face = single.open_cylinder(cylinder, loaded=False)
            self.assertEqual(max(x for x, _ in face) - min(x for x, _ in face), 4)
            self.assertEqual(sum(c == single.INK for c in face.values()), 8)
            if frame in (2, 4, 5):
                self.assertLess(math.dist(cylinder, helper), 4,
                                'The loading hand must actually reach the cylinder')

    def test_head_torso_and_planted_feet_are_preserved_under_the_action(self):
        body = dict(self.body)
        original = dict(body)
        frames = single.single_reload_frames(body, self.aim)
        action = single.single_reload_frames({}, {})
        face = {p: c for p, c in body.items() if c[:3] in SKIN and p[1] < 35}
        self.assertGreater(len(face), 20)
        for frame, pixels in enumerate(frames[:-1]):
            with self.subTest(frame=frame):
                # The barrel may pass in front of the hat's outer edge and
                # a sleeve may cover the corset. Everything outside the
                # authored arm/weapon mask must keep its exact native place.
                crook = {p for p, c in body.items() if c in HAIR and pixels.get(p) == SHADE}
                self.assertLessEqual(len(crook), CROOK)
                protected = {p: c for p, c in body.items()
                             if p not in action[frame] and p not in crook and c not in BRASSES}
                self.assertGreater(len(protected), 250)
                self.assertEqual({p: pixels.get(p) for p in protected}, protected,
                                 'Reload moved its shared head, torso or planted feet')
                self.assertEqual({p: pixels.get(p) for p in face}, face,
                                 'The upright revolver must remain beside the face')
        self.assertEqual(body, original, 'The pose builder must not mutate its input body')

    def test_reload_returns_to_the_exact_aim_and_keeps_input_independent(self):
        self.assertEqual(len(self.frames), 8)
        self.assertEqual(self.frames[-1], self.aim)
        self.assertIsNot(self.frames[-1], self.aim)

    def test_aim_muzzle_matches_the_runtime_bullet_origin(self):
        root = Path(__file__).resolve().parents[1]
        config = (root / 'src/config.h').read_text(encoding='utf-8')
        player = (root / 'src/game/player.c').read_text(encoding='utf-8')

        def number(source, name):
            return float(re.search(r'^#define\s+' + name + r'\s+([\d.]+)', source, re.MULTILINE).group(1))

        expected = (number(player, 'SHOOT_ANCHOR_X') + number(config, 'PLAYER_MUZZLE_DX'),
                    number(player, 'SHOOT_GROUND_Y') - number(config, 'PLAYER_MUZZLE_DY'))
        hand = tuple(round(a + b) for a, b in zip(art.SHOULDER, art.GUN_HAND))
        muzzle = pistol_muzzle(hand, art.GUN_PITCH)
        self.assertLess(math.dist(muzzle, expected), .75,
                        'The bullet must emerge from the new aimed barrel')
        pixels = art.held_gun((0, 0))[0]
        self.assertLess(min(math.dist(expected, p) for p in pixels), 1.5,
                        'The rendered aim does not reach the runtime muzzle')


if __name__ == '__main__':
    unittest.main()
