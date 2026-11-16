#!/usr/bin/env python3
"""Check the actual painted SWAT assets and their animation seams."""
from pathlib import Path
from functools import lru_cache
import re
import math
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from embed_assets import decode_png_rgba
from swat_walk import BODY_MOTION
from swat_actions import DRINK_POSES, DRINK_FRAME_COUNT, MELEE_POSES, weapon_pose, drink_samples
from swat_aux import seated_elbow


@lru_cache(maxsize=None)
def sheet_data(sheet, folder):
    return decode_png_rgba(ROOT / folder / (sheet + '.png'))


@lru_cache(maxsize=None)
def load(sheet, f=0, width=81, folder='assets/sprites/characters/swat'):
    w, h, rgba = sheet_data(sheet, folder)
    return [[tuple(rgba[(y * w + f * width + x) * 4:(y * w + f * width + x) * 4 + 4])
             for x in range(width)] for y in range(h)]


def patch(image, box, dx=0, dy=0):
    l, t, r, b = box
    return [image[y + dy][x + dx] for y in range(t, b) for x in range(l, r)]


def groups(points):
    result = []
    while points:
        todo, component = [points.pop()], set()
        while todo:
            x, y = todo.pop()
            component.add((x, y))
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if (x + dx, y + dy) in points:
                    points.remove((x + dx, y + dy))
                    todo.append((x + dx, y + dy))
        result.append(component)
    return result


class SwatPaintedArt(unittest.TestCase):
    def test_head_neck_and_boots_are_one_shared_drawing(self):
        base = load('shoot')
        for sheet in ('shoot', 'shoot_shotgun', 'reload', 'reload_shotgun'):
            for f in range(8):
                image = load(sheet, f)
                # A raised gun may cross the collar. The helmet/face stay
                # shared without erasing the weapon to enforce a rectangle.
                self.assertTrue(all(image[y][x] == base[y][x] for y in range(8, 27)
                                    for x in range(19, 46) if base[y][x][3]), (sheet, f))
                self.assertEqual(patch(image, (0, 57, 81, 80)), patch(base, (0, 57, 81, 80)), (sheet, f))

    def test_walking_upper_body_and_head_move_together(self):
        for suffix in ('', '_shotgun'):
            base = load('shoot' + suffix)
            for f, (dx, dy) in enumerate(BODY_MOTION):
                walk = load('carry' + suffix, f)
                self.assertEqual(patch(base, (0, 0, 80, 50)),
                                 patch(walk, (0, 0, 80, 50), dx, dy), (suffix, f))
                legs = load('legs', f, 42)
                # Below the moving waist, every knee and boot is from the
                # animated leg layer, never the shooting stance.
                self.assertEqual(patch(walk, (12, 53, 54, 74)), patch(legs, (0, 46, 42, 67)))

    def test_breathing_with_a_held_weapon_has_no_transparent_waist_cut(self):
        for name in ('carry', 'carry_shotgun', 'light_walk', 'light_walk_shotgun'):
            for f in range(8, 12):
                image = load(name, f)
                self.assertTrue(all(image[y][x][3] for y in range(47, 53) for x in range(27, 38)), (name, f))

    def test_pelvis_root_stays_under_the_belt_through_the_entire_gait(self):
        body = load('body_actions', folder='docs/templates/swat/rig')
        for name in ('carry', 'carry_shotgun', 'light_walk', 'light_walk_shotgun'):
            for f in range(8):
                image = load(name, f)
                self.assertEqual(patch(image, (22, 52, 43, 53)), patch(body, (22, 52, 43, 53)), (name, f))
                self.assertEqual(BODY_MOTION[f][0], 0)

    def test_reload_keeps_the_right_trigger_hand_still(self):
        for suffix in ('', '_shotgun'):
            reference = patch(load('reload' + suffix), (32, 40, 36, 43))
            for f in range(8):
                self.assertEqual(patch(load('reload' + suffix, f), (32, 40, 36, 43)), reference, (suffix, f))

    def test_melee_drives_the_weapon_away_from_the_operator(self):
        for kind in ('rifle', 'shotgun'):
            muzzles = []
            for grip, angle, lean in MELEE_POSES:
                _, _, _, point = weapon_pose(kind, grip, angle)
                muzzle = point((21, 3))
                self.assertGreater(muzzle[0], grip[0] + 17)
                self.assertGreaterEqual(math.cos(math.radians(angle)), .9)
                muzzles.append(muzzle[0])
            self.assertGreater(muzzles[3] - muzzles[1], 10)

    def test_drinking_uses_the_requested_hand_sequence_without_wrist_teleports(self):
        for kind in ('rifle', 'shotgun'):
            hands = []
            for f, grip, angle, right, left, tilt in drink_samples(kind):
                _, guard, _, _ = weapon_pose(kind, grip, angle)
                right, left = right or grip, left or guard
                hands.append((right, left))
                if 4 <= f <= 7:
                    self.assertGreater(math.dist(right, grip), 4)
                    self.assertGreater(math.dist(left, guard), 4)
                if 9 <= f <= 13:
                    self.assertLess(math.dist(right, grip), 2)
                if 4 <= f <= 13:
                    self.assertIsNotNone(tilt)
                    self.assertEqual(grip, (33, 40))
            for previous, current in zip(hands, hands[1:]):
                for a, b in zip(previous, current):
                    self.assertLess(math.dist(a, b), 5)

    def test_jump_keeps_the_weapon_inside_its_own_atlas_cell(self):
        for name in ('jump', 'jump_shotgun'):
            for f in range(8):
                image = load(name, f, 54)
                self.assertFalse(any(row[0][3] or row[-1][3] for row in image), (name, f))
                self.assertGreater(sum(bool(c[3]) for row in image for c in row), 500)

    def test_layers_reassemble_the_painted_aim_in_both_weapons(self):
        rig = 'docs/templates/swat/rig'
        for name, suffix in (('rifle', ''), ('shotgun', '_shotgun')):
            for f in (0, 1, 2, 3, 5, 6, 7):
                upper = load('upper_' + name, f, folder=rig)
                lower = load('lower_' + name, f, folder=rig)
                full = load('shoot' + suffix, f)
                self.assertEqual(full, upper[:51] + lower[51:], (name, f))

    def test_idle_aim_and_reload_endpoints_do_not_change_the_body(self):
        for suffix in ('', '_shotgun'):
            idle = load('carry' + suffix, 8)
            ready = load('shoot' + suffix)
            self.assertEqual(idle, ready)
            for f in (0, 7):
                self.assertEqual(load('reload' + suffix, f), ready)
            aim = load('shoot' + suffix, 3)
            self.assertEqual(patch(ready, (0, 51, 81, 80)), patch(aim, (0, 51, 81, 80)))
            # The belt/waist remains the same broad mass when the arms rise.
            for y in (48, 49):
                a = sum(c[3] > 0 for c in ready[y][:39])
                b = sum(c[3] > 0 for c in aim[y][:39])
                self.assertLessEqual(abs(a-b), 3)

    def test_optics_have_three_distinct_bright_lenses(self):
        image = load('shoot')
        glass = {(x, y) for y in range(13, 21) for x in range(30, 47)
                 if image[y][x][1] >= 150 and image[y][x][1] - image[y][x][0] >= 4
                 and image[y][x][1] - image[y][x][2] >= 30}
        lenses = groups(glass)
        self.assertEqual(len(lenses), 3)
        self.assertGreaterEqual(min(map(len, lenses)), 4)

    def test_muzzle_and_lamp_offsets_match_the_visible_art(self):
        weapons = (ROOT / 'src/game/weapons.c').read_text()
        for gun, suffix in (('RIFLE', ''), ('SHOTGUN', '_shotgun')):
            block = weapons.split('[WEAPON_' + gun + '] = {')[1].split('},')[0]
            value = lambda key: float(re.search(r'\.' + key + r' = ([0-9.]+)f', block)[1])
            aim = load('shoot' + suffix, 3)
            # The bayonet can extend past the barrel below its bore. Check
            # the actual barrel/flash contact instead of the rightmost pixel.
            x = round(31.5 + value('muzzle_dx'))
            y = round(68 - value('muzzle_rows') - .5)
            self.assertTrue(aim[y][x - 1][3])
            self.assertIn(load('shoot' + suffix, 4)[y][x][:3],
                          ((255, 246, 220), (255, 210, 60), (240, 138, 36)))
            light = load('light' + suffix, 15)
            lens = (round(31.5 + value('light_dx') - .5), round(68 - value('light_rows') - .5))
            self.assertEqual(light[lens[1]][lens[0]], (0xd4, 0xd9, 0x90, 255))

    def test_reload_foreground_does_not_contain_a_standing_thigh(self):
        for suffix in ('', '_shotgun'):
            count = 0
            for f in range(8):
                low = load('reload' + suffix + '_lower', f)
                for y, row in enumerate(low):
                    for x, c in enumerate(row):
                        if c[3]:
                            count += 1
                            self.assertTrue(29 <= x < 48 and 51 <= y < 59, (suffix, f, x, y))
                            self.assertEqual(c, load('reload' + suffix, f)[y][x])
            if suffix == '':
                self.assertGreater(count, 5)

    def test_recoil_weapon_and_body_stay_connected(self):
        for suffix in ('', '_shotgun'):
            for f in (0, 1, 2, 3, 5, 6, 7):
                image = load('shoot' + suffix, f)
                components = groups({(x, y) for y, row in enumerate(image)
                                     for x, c in enumerate(row) if c[3]})
                largest = max(components, key=len)
                self.assertGreater(len(largest), 700)
                self.assertLess(sum(len(c) for c in components if c is not largest), 5,
                                (suffix, f))

    def test_torso_remains_filled_behind_every_requested_action(self):
        body = load('body_actions', folder='docs/templates/swat/rig')
        for name, count in (('shoot', 8), ('shoot_shotgun', 8),
                            ('reload', 8), ('reload_shotgun', 8), ('light', 16),
                            ('light_shotgun', 16), ('drink_rifle', DRINK_FRAME_COUNT), ('drink_shotgun', DRINK_FRAME_COUNT)):
            for f in range(count):
                image = load(name, f)
                self.assertTrue(all(image[y][x][3] for y in range(32, 51) for x in range(26, 39)
                                    if body[y][x][3]), (name, f))

    def test_melee_weight_transfer_keeps_a_filled_torso_and_planted_pelvis(self):
        body = load('body_actions', folder='docs/templates/swat/rig')
        for name in ('melee', 'melee_shotgun'):
            for f in range(7):
                image = load(name, f)
                self.assertEqual(patch(image, (20, 51, 44, 80)), patch(body, (20, 51, 44, 80)))
                for y in range(34, 51):
                    self.assertGreaterEqual(sum(bool(image[y][x][3]) for x in range(18, 55)), 12, (name, f, y))

    def test_light_support_hand_reaches_switch_before_lens_lights(self):
        for suffix, x in (('', 54), ('_shotgun', 55)):
            poses = {tuple(patch(load('light' + suffix, f), (39, 32, 55, 46))) for f in range(7, 14)}
            self.assertGreaterEqual(len(poses), 4)
            for f in range(14):
                self.assertNotEqual(load('light' + suffix, f)[35][x], (0xd4, 0xd9, 0x90, 255))
            for f in (14, 15):
                self.assertEqual(load('light' + suffix, f)[35][x], (0xd4, 0xd9, 0x90, 255))
            self.assertEqual(load('light' + suffix, 15), load('shoot' + suffix + '_lit', 3))

    def test_recoil_beam_offsets_follow_the_drawn_lens_in_each_weapon(self):
        weapons = (ROOT / 'src/game/weapons.c').read_text()
        for gun, suffix in (('RIFLE', ''), ('SHOTGUN', '_shotgun')):
            block = weapons.split('[WEAPON_' + gun + '] = {')[1].split('\n    },')[0]
            origin = (54, 35) if gun == 'RIFLE' else (55, 35)
            values = [float(v) for v in re.findall(r'(-?[0-9.]+)f', block.split('.light_kick = ')[1])[:6]]
            for f in (5, 6):
                image = load('shoot' + suffix + '_lit', f)
                bright = [(x, y) for y in range(25, 41) for x in range(47, 75)
                          if image[y][x] == (0xd4, 0xd9, 0x90, 255)]
                dx, dy, angle = values[(f - 5) * 3:(f - 4) * 3]
                self.assertEqual(bright, [(origin[0] + dx, origin[1] + dy)], (gun, f))
                self.assertLess(angle, 0)

    def test_drink_shows_bottle_sling_and_returns_to_the_same_ready_pose(self):
        for kind, suffix in (('rifle', ''), ('shotgun', '_shotgun')):
            poses = [load('drink_' + kind, f) for f in range(DRINK_FRAME_COUNT)]
            ready = load('shoot' + suffix)
            self.assertEqual(poses[0], ready)
            self.assertEqual(poses[-1], ready)
            bottle_colors = {(0x3a, 0x52, 0x53), (0x6f, 0x90, 0x87), (0xb9, 0xc4, 0xad), (0x9f, 0xb8, 0xb5)}
            previous_center = None
            for f in range(7, 26):
                self.assertGreater(sum(c[:3] in bottle_colors for row in poses[f] for c in row), 4, (kind, f))
                bottle = [(x, y) for y, row in enumerate(poses[f]) for x, c in enumerate(row)
                          if c[3] and c[:3] in bottle_colors]
                center = (sum(x for x, y in bottle) / len(bottle), sum(y for x, y in bottle) / len(bottle))
                if previous_center:
                    self.assertLess(math.dist(center, previous_center), 6, (kind, f, 'bottle discontinuity'))
                previous_center = center
                low = load('drink_' + kind + '_lower', f)
                self.assertGreater(sum(bool(c[3]) for row in low[51:] for c in row), 20)
                self.assertFalse(any(c[3] for row in low[:51] for c in row))
                self.assertFalse(any(c[3] for row in low[68:] for c in row), (kind, f, 'weapon below ground'))

    def test_drinking_bottle_has_visible_contact_with_the_left_glove(self):
        bottle_colors = {(0x3a, 0x52, 0x53), (0x6f, 0x90, 0x87),
                         (0xb9, 0xc4, 0xad), (0x9f, 0xb8, 0xb5)}
        glove_colors = {(0x41, 0x49, 0x4a), (0x29, 0x34, 0x3b)}
        for kind in ('rifle', 'shotgun'):
            for index, (phase, grip, angle, right, left, tilt) in enumerate(drink_samples(kind)):
                if not 3.5 <= phase <= 12.5:
                    continue
                image = load('drink_' + kind, index)
                wrist = [(x, y) for y in range(round(left[1]) - 3, round(left[1]) + 4)
                         for x in range(round(left[0]) - 3, round(left[0]) + 4)
                         if image[y][x][:3] in glove_colors]
                contact = [(x, y) for x, y in wrist
                           if any(image[y + dy][x + dx][:3] in bottle_colors
                                  for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0),
                                                 (0, 2), (0, -2), (2, 0), (-2, 0)))]
                self.assertGreaterEqual(len(contact), 2, (kind, index, 'bottle floats above glove'))

    def test_assets_have_crisp_alpha_and_no_frame_edge_clipping(self):
        for name, count in (('carry', 12), ('carry_shotgun', 12), ('shoot', 8), ('shoot_shotgun', 8),
                            ('reload', 8), ('reload_shotgun', 8), ('light', 16), ('light_shotgun', 16),
                            ('melee', 7), ('melee_shotgun', 7), ('drink_rifle', DRINK_FRAME_COUNT), ('drink_shotgun', DRINK_FRAME_COUNT)):
            for f in range(count):
                image = load(name, f)
                self.assertTrue(all(c[3] in (0, 255) for row in image for c in row))
                self.assertFalse(any(row[0][3] or row[-1][3] for row in image), (name, f))
                self.assertFalse(any(c[3] for c in image[0] + image[-1]), (name, f))

    def test_grenade_is_held_until_release_and_recovers_each_current_weapon(self):
        grenade_colors = {(0xb9, 0xb7, 0x8a), (0x93, 0x99, 0x6d), (0x70, 0x7e, 0x52),
                          (0x4d, 0x5c, 0x3b), (0x2e, 0x3d, 0x2c)}
        for suffix in ('', '_shotgun'):
            self.assertEqual(load('throw' + suffix), load('shoot' + suffix))
            self.assertEqual(load('throw' + suffix, 23), load('shoot' + suffix))
            for f in range(7, 15):
                self.assertGreater(sum(c[:3] in grenade_colors for row in load('throw' + suffix, f) for c in row), 2)
            for f in range(15, 24):
                self.assertFalse(any(c[:3] in grenade_colors for row in load('throw' + suffix, f) for c in row))
        config = (ROOT / 'src/config.h').read_text()
        value = lambda key: float(re.search(r'#define ' + key + r' ([0-9.]+)', config)[1])
        self.assertEqual(value('PLAYER_THROW_FRAMES'), 24)
        self.assertEqual(value('PLAYER_THROW_RELEASE_FRAME'), 15)
        self.assertEqual(value('GRENADE_RELEASE_DX'), (46 - 31.5) * 4)
        self.assertEqual(value('GRENADE_RELEASE_HEIGHT'), (68 - 32 - 4) * 4)

    def test_seated_hand_off_and_rest_keep_both_parked_guns_visible(self):
        rest = load('sit', 8, 72)
        for name in ('sit', 'sit_shotgun'):
            for f in (7, 8, 10, 12, 35):
                self.assertEqual(load(name, f, 72), rest, (name, f))
            self.assertGreater(sum(c[3] > 0 for c in patch(rest, (5, 31, 20, 51))), 20)
            self.assertGreater(sum(c[3] > 0 for c in patch(rest, (55, 31, 69, 51))), 20)

    def test_seated_boots_stay_planted_and_auxiliary_frames_have_room(self):
        body = load('body_actions', folder='docs/templates/swat/rig')
        for name in ('sit', 'sit_shotgun'):
            w, h, _ = sheet_data(name, 'assets/sprites/characters/swat')
            self.assertEqual((w, h), (72 * 40, 67))
            for f in range(40):
                image = load(name, f, 72)
                for y in range(56, 61):
                    for x in range(4, 68):
                        if body[y + 7][x - 4][3]:
                            self.assertEqual(image[y][x], body[y + 7][x - 4], (name, f, x, y))
        for name, width, count in (('throw', 81, 24), ('throw_shotgun', 81, 24), ('sit', 72, 40), ('sit_shotgun', 72, 40)):
            for f in range(count):
                image = load(name, f, width)
                self.assertFalse(any(row[0][3] or row[-1][3] for row in image), (name, f))
                self.assertFalse(any(c[3] for c in image[0] + image[-1]), (name, f))
                self.assertTrue(all(c[3] in (0, 255) for row in image for c in row))

    def test_seated_elbow_does_not_flip_when_a_wrist_crosses_the_old_thresholds(self):
        poses = ((True, (28, 33.5), ((24, 40), (28, 39), (22, 40), (31, 45), (20.5, 44), (12, 39))),
                 (False, (43, 33.5), ((39, 45), (47, 45), (43, 48), (60, 38), (36.3, 47.5), (50, 37))))
        for near, shoulder, wrists in poses:
            for x, y in wrists:
                first = seated_elbow(shoulder, (x - .01, y - .01), near)
                last = seated_elbow(shoulder, (x + .01, y + .01), near)
                self.assertLess(math.dist(first, last), .1, (near, x, y, 'elbow flipped'))
                self.assertLessEqual(math.dist(shoulder, last), 9.51, (near, x, y, 'upper arm stretched'))
                self.assertGreaterEqual(math.dist((x + .01, y + .01), last), 5.99)
                self.assertLessEqual(math.dist((x + .01, y + .01), last), 10.01)


if __name__ == '__main__':
    unittest.main()
