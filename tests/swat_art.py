#!/usr/bin/env python3
"""Check the actual painted SWAT assets and their animation seams."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from embed_assets import decode_png_rgba
from swat_walk import BODY_MOTION


def load(sheet, f=0, width=81, folder='assets/sprites/characters/swat'):
    w, h, rgba = decode_png_rgba(ROOT / folder / (sheet + '.png'))
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
                self.assertEqual(patch(image, (0, 0, 46, 32)), patch(base, (0, 0, 46, 32)), (sheet, f))
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
            right = max(x for y in range(25, 51) for x in range(48, 81) if aim[y][x][3])
            self.assertEqual(value('muzzle_dx'), right + 1 - 31.5)
            y = round(sum(y for y in range(25, 51) if aim[y][right][3]) /
                      sum(bool(aim[y][right][3]) for y in range(25, 51)))
            self.assertEqual(value('muzzle_rows'), 68 - (y + .5))
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
                            self.assertEqual(suffix, '')
                            self.assertEqual(f, 2)
                            self.assertTrue(40 <= x < 47 and 51 <= y < 56)
            if suffix == '':
                self.assertGreater(count, 5)

    def test_assets_have_crisp_alpha_and_no_frame_edge_clipping(self):
        for name, count in (('carry', 12), ('carry_shotgun', 12), ('shoot', 8), ('shoot_shotgun', 8),
                            ('reload', 8), ('reload_shotgun', 8), ('light', 16), ('light_shotgun', 16)):
            for f in range(count):
                image = load(name, f)
                self.assertTrue(all(c[3] in (0, 255) for row in image for c in row))
                self.assertFalse(any(row[0][3] or row[-1][3] for row in image), (name, f))
                self.assertFalse(any(c[3] for c in image[0] + image[-1]), (name, f))


if __name__ == '__main__':
    unittest.main()
