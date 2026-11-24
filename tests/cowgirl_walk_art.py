"""The sheriff's measured run and the one body under all her poses; standard library only.

These check what went wrong before: legs that got thin or broke in some frames, a chest
that jumped about, a stance that was another figure, belts and scarves in loose bits.
They do not replace looking at the sheets beside the reference, enlarged.
"""
import math
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import cowgirl_legs as legs
import cowgirl_pose as pose
import cowgirl_torso as figure
import rework_cowgirl as art
from cowgirl_arm import arm_limb, glove
from finish_cowgirl import finish
from make_powers import load

FRAMES = range(pose.FRAMES)
W, H = art.SHEETS['walk'], art.WALK_H


def correlation(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    covariance = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return covariance / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


def components(pixels):
    return art._groups(set(pixels))


def frame_of(sheet, f, width=W):
    return {(x, y): sheet.get(f * width + x, y) for y in range(sheet.height) for x in range(width)
            if sheet.get(f * width + x, y)[3]}


def leg(frame, far):
    chain = pose.leg_chain(frame, far)
    return chain, legs.outlined(legs.painted(legs.sections(chain), chain, far, pose.seat(frame)))


def width_across(px, a, b, t):
    """How thick the painted leg is at t of the way down a bone, outline included."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    nx, ny = dy / length, -dx / length
    cx, cy = a[0] + dx * t, a[1] + dy * t
    inside = 0
    for side in (-1, 1):
        k = 0.
        while (math.floor(cx + nx * k * side), math.floor(cy + ny * k * side)) in px and k < 12:
            k += .05
        inside += k
    return inside


class SheriffRun(unittest.TestCase):
    def test_both_arms_keep_their_bones_shoulders_and_the_side_their_elbow_bends(self):
        for far in (False, True):
            for frame in FRAMES:
                with self.subTest(far=far, frame=frame):
                    top, elbow, hand = pose.arm(frame, far)
                    self.assertAlmostEqual(math.dist(top, elbow), pose.ARM_BONE, places=6)
                    self.assertAlmostEqual(math.dist(elbow, hand), pose.ARM_BONE, places=6)
                    root = pose.FAR_SHOULDER if far else pose.NEAR_SHOULDER
                    self.assertAlmostEqual(top[0], root[0])
                    self.assertAlmostEqual(top[1], root[1] + pose.bob(frame))
                    self.assertGreater(elbow[1], top[1] + 3.5, 'The elbow hangs under its shoulder')
                    upper = (elbow[0] - top[0], elbow[1] - top[1])
                    fore = (hand[0] - elbow[0], hand[1] - elbow[1])
                    self.assertLess(upper[0] * fore[1] - upper[1] * fore[0], 0, 'The elbow bends one way')
                    following = pose.arm(frame + 1, far)
                    self.assertLess(math.dist(elbow, following[1]), 1.6, 'An elbow must not snap')
                    self.assertLess(math.dist(hand, following[2]), 2.0)
                    painted = set(arm_limb(top, elbow, hand)) | set(glove(hand, elbow))
                    self.assertEqual(len(components(painted)), 1, 'Sleeve and glove separated')
                    self.assertTrue(all(0 <= x < W for x, _ in painted), 'The 42 px frame must not crop a hand')

    def test_each_arm_swings_against_the_leg_on_its_side(self):
        for far in (False, True):
            hands = [pose.arm(f, far)[2][0] for f in FRAMES]
            feet = [pose.leg_chain(f, far)[2][0] for f in FRAMES]
            self.assertLess(correlation(hands, feet), -.75 if not far else -.1)
            lift = [pose.arm(f, far)[2][1] for f in FRAMES]
            self.assertLess(max(hands) - min(hands), 6, 'A forearm swings; it does not sweep')
            self.assertLess(max(lift) - min(lift), 8)
        near, far = ([pose.arm(f, side)[2][1] for f in FRAMES] for side in (False, True))
        self.assertLess(correlation(near, far), 0, 'One hand comes up as the other goes down')

    def test_no_leg_gets_thin_or_swells_in_any_frame(self):
        """The same thigh, knee and calf in all twenty frames, fuller than the reference's 6/5/4 px."""
        least = {(0, .3): 7.0, (0, .6): 6.4, (0, .95): 5.6, (1, .22): 5.6}
        for far in (False, True):
            seen = {k: [] for k in least}
            for frame in FRAMES:
                chain, px = leg(frame, far)
                for bone, t in least:
                    wide = width_across(px, chain[bone], chain[bone + 1], t)
                    seen[bone, t].append(wide)
                    with self.subTest(far=far, frame=frame, bone=bone, t=t):
                        # A knee folded up behind her meets its calf: there it can only read wider.
                        self.assertGreaterEqual(wide, least[bone, t] - .35, 'A leg went thin')
            for key, widths in seen.items():
                usual = sorted(widths)[len(widths) // 2]
                self.assertLess(sum(abs(w - usual) > 1.6 for w in widths), 7, f'{key}: the leg keeps its thickness')

    def test_legs_are_one_piece_from_hip_to_toe_and_move_without_jumps(self):
        for far in (False, True):
            for frame in FRAMES:
                with self.subTest(far=far, frame=frame):
                    chain, px = leg(frame, far)
                    self.assertEqual(len(components(px)), 1, 'A shin or a boot came off')
                    self.assertTrue(all(0 <= x < W for x, _ in px))
                    following = pose.leg_chain(frame + 1, far)
                    for joint, limit in ((0, 1.4), (1, 4.2), (2, 4.2)):
                        self.assertLess(math.dist(chain[joint], following[joint]), limit)
                    self.assertGreater(math.dist(chain[0], chain[1]), 4.4)
                    self.assertGreater(math.dist(chain[1], chain[2]), 4.2)
                    self.assertGreater(chain[1][1], chain[0][1] + 2.5, 'A knee never comes up over the belt')

    def test_planted_feet_reach_the_ground_and_hold_it_at_her_walking_speed(self):
        config = (ROOT / 'src/config.h').read_text(encoding='utf-8')

        def number(name):
            return float(re.search(r'^#define\s+' + name + r'\s+([\d.]+)', config, re.MULTILINE).group(1))

        self.assertEqual(int(number('PLAYER_SHERIFF_WALK_FRAMES')), pose.FRAMES)
        a_frame = number('PLAYER_WALK_SPEED') / number('SPRITE_SCALE') / number('PLAYER_SHERIFF_WALK_FPS')
        airborne = 0
        for frame in FRAMES:
            airborne += not any(pose.planted(frame, far) for far in (False, True))
        self.assertGreater(airborne, 1, 'A run has both feet off the ground for a moment')
        for far in (False, True):
            steps = []
            for frame in FRAMES:
                chain, px = leg(frame, far)
                bottom = max(y for _, y in px)
                with self.subTest(far=far, frame=frame):
                    self.assertLessEqual(bottom, pose.SOLE + 1)
                    own = pose.own_phase(frame, far)
                    if 7.4 <= own <= 9.6:
                        self.assertEqual(min(bottom, pose.SOLE), pose.SOLE, 'A supporting boot reaches the ground')
                    if 1 <= own <= 4:
                        self.assertLess(bottom, pose.SOLE, 'The foot coming back clears it')
                    if 7 <= own < 9.5:
                        steps.append(chain[2][0] - pose.leg_chain(frame + 1, far)[2][0])
            self.assertTrue(all(step > 0 for step in steps), 'A foot on the ground goes back under her')
            self.assertAlmostEqual(sum(steps) / len(steps), a_frame, delta=.5, msg='Her feet must not slide on the ground')

    def test_frame_zero_and_ten_are_the_landings_the_footsteps_sound_on(self):
        self.assertAlmostEqual(pose.own_phase(0, True), 7)
        self.assertAlmostEqual(pose.own_phase(pose.FRAMES // 2, False), 7)

    def test_the_bob_is_the_table_the_flashlight_follows_in_the_game(self):
        source = (ROOT / 'src/game/player.c').read_text(encoding='utf-8')
        table = re.search(r'SHERIFF_STRIDE\[[^\]]*\][^{]*\{([^}]*)\}', source).group(1)
        self.assertEqual([int(v) for v in table.split(',')], [pose.bob(f) for f in FRAMES])
        self.assertTrue(all(abs(pose.bob(f + 1) - pose.bob(f)) <= 1 for f in FRAMES))
        self.assertEqual([pose.bob(f) for f in range(10)], [pose.bob(f + 10) for f in range(10)])


class SheriffBody(unittest.TestCase):
    """One body: the chest, the face and the width of her, standing and running."""

    def test_the_covered_chest_only_settles_a_row_and_a_column(self):
        still = figure.torso()
        for chest in (-1, 0, 1):
            for opened in (False, True):
                px = figure.torso(chest, opened)
                for y in range(28, 42):
                    row = [x for x, yy in px if yy == y]
                    rest = [x for x, yy in still if yy == y]
                    with self.subTest(chest=chest, opened=opened, row=y):
                        self.assertLessEqual(abs(min(row) - min(rest)), 1)
                        self.assertLessEqual(abs(max(row) - max(rest)), 1, 'She neither thins nor swells')
                self.assertEqual(len(components(px)), 1)
        lags = [pose.chest_lag(f) for f in FRAMES]
        self.assertEqual(set(lags), {-1, 0, 1})
        self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(lags, lags[1:] + lags[:1])), 'It never jumps two rows')
        opened = [pose.seat(f) > .6 for f in FRAMES]
        self.assertEqual(sum(a != b for a, b in zip(opened, opened[1:] + opened[:1])), 2, 'It opens once and shuts once')

    def test_every_pixel_of_her_face_and_hat_is_only_moved(self):
        head = art.head()
        self.assertGreater(len(head), 380)
        for f in FRAMES:
            body = art.walking_body(f)
            dy = pose.bob(f)
            for (x, y), c in head.items():
                self.assertEqual(body[x + pose.LEAN, y + dy], c, 'Running must not redraw her face')
        standing = art.standing_body()
        for p, c in head.items():
            self.assertEqual(standing[p], c)

    def test_her_torso_is_as_wide_running_as_standing(self):
        standing = figure.standing()[1]
        for f in FRAMES:
            _, body = figure.running(f)
            dy = pose.bob(f)
            for y in range(29, 37):
                row = [x for x, yy in body if yy == y + dy]
                rest = [x for x, yy in standing if yy == y]
                with self.subTest(frame=f, row=y):
                    self.assertGreaterEqual(max(row) - min(row), max(rest) - min(rest) - 1)

    def test_the_belt_is_a_thin_band_that_tilts_and_the_buckle_goes_round_with_it(self):
        shown = []
        for f in FRAMES:
            lower, rows = figure.running_lower(f)
            self.assertLessEqual(max(rows.values()) - min(rows.values()), 4)
            band = figure.belt(rows, 0, 0)
            for x in rows:
                self.assertEqual(sum(p[0] == x for p in band), 3, 'Outline, leather, outline: no thick slab')
            _, body = figure.running(f)
            belt = pose.BELT + pose.bob(f)
            shown.append(sum(c in (figure.COLORS['G'], figure.COLORS['g']) and abs(y - belt) <= 2
                             for (x, y), c in body.items()))
        turned = [f for f in FRAMES if pose.yaw(f) > 75]
        toward = [f for f in FRAMES if pose.yaw(f) < 20]
        self.assertTrue(turned and toward)
        self.assertTrue(all(shown[f] == 0 for f in turned), 'The buckle hides as her pelvis turns away')
        self.assertTrue(all(shown[f] >= 8 for f in toward))
        lifts = [pose.belt_tilt(f)[0] for f in FRAMES]
        self.assertGreater(max(lifts), 2)
        self.assertEqual(min(lifts), 0)

    def test_her_seat_turns_to_us_with_the_seam_of_her_trousers_between_both_sides(self):
        """As in the reference's keys 5-8: two lit sides and a dark seam down between them."""
        checked = 0
        for f in FRAMES:
            if pose.seat(f) < .9:
                continue
            lower, rows = figure.running_lower(f)
            belt = pose.BELT + pose.bob(f)
            for y in range(belt + 2, belt + 4):
                row = {x: c for (x, yy), c in lower.items() if yy == y}
                seam = [x for x, c in row.items() if c == legs.TONES[3] and
                        any(row.get(x - k) in legs.TONES[:2] for k in (1, 2, 3, 4)) and
                        any(row.get(x + k) in legs.TONES[:2] for k in (1, 2, 3))]
                self.assertTrue(seam, f'frame {f}, row {y}: the seam is missing')
                checked += 1
        self.assertGreaterEqual(checked, 10)

    def test_whole_silhouettes_hold_together_inside_their_frame(self):
        for dual in (False, True):
            sheet = art.walk_sheet(True, dual)
            for f in FRAMES:
                px = frame_of(sheet, f)
                with self.subTest(dual=dual, frame=f):
                    self.assertEqual(len(components(px)), 1, 'A part of her came off')
                    self.assertLessEqual(max(y for _, y in px), pose.SOLE + 1)
            stand = art.stand_sheet(dual)
            for f in range(stand.width // W):
                px = frame_of(stand, f)
                self.assertEqual(len(components(px)), 1)
                self.assertEqual(max(y for _, y in px), pose.SOLE, 'Both feet on the ground, pulling up too')

    def test_no_loose_specks_of_brass_scarf_or_hair_beside_her_arms(self):
        materials = {'star': figure.STAR_TONES, 'sash': figure.SASH_TONES, 'hair': {c for c in art.HAIR}}
        sheets = [(art.walk_sheet(True), pose.FRAMES), (art.stand_sheet(False), 6)]
        for sheet, count in sheets:
            for f in range(count):
                px = finish(frame_of(sheet, f), W, H)
                for name, tones in materials.items():
                    for group in components({p for p, c in px.items() if c in tones}):
                        with self.subTest(frame=f, material=name):
                            self.assertGreaterEqual(len(group), 3 if name == 'hair' else 4,
                                                    f'{name}: a speck alone at {sorted(group)[0]}')

    def test_stopping_goes_from_the_run_to_the_stance_by_a_pose_between_them(self):
        """Her head, hips and hands come to rest in small steps, not in a jump to another figure."""
        run = art.walk_arms(2)
        poses = [run, art.stand_arms(4), art.stand_arms(5), art.stand_arms(0)]
        for hand in range(2):
            gaps = [math.dist(a[hand][2], b[hand][2]) for a, b in zip(poses, poses[1:])]
            self.assertLess(max(gaps), 8.5)
            self.assertLess(sum(gaps), 18)
        leans = [pose.LEAN] + [how['lean'] for how in art.SETTLE] + [0]
        self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(leans, leans[1:])))
        # Where a run starts, both feet are about where she stands on them.
        start = 2
        near, far = (pose.leg_chain(start, side)[2][0] for side in (False, True))
        lower = figure.pixels(figure.LOWER, figure.LOWER_X0)
        soles = [x for x, y in lower if y == pose.SOLE]
        self.assertLess(abs(near - sum(x for x in soles if x < 20) / sum(x < 20 for x in soles)), 2.5)
        self.assertLess(abs(far - sum(x for x in soles if x > 20) / sum(x > 20 for x in soles)), 2.5)

    def test_breathing_moves_her_chest_and_not_her_feet_head_or_belt(self):
        sheet = art.stand_sheet(False)
        frames = [frame_of(sheet, f) for f in range(art.STAND_BREATHS)]
        self.assertGreater(len({tuple(sorted(f.items())) for f in frames}), 1, 'She breathes')
        for f in frames[1:]:
            for rows in (range(0, 18), range(44, H)):
                for y in rows:
                    self.assertEqual({x: c for (x, yy), c in f.items() if yy == y and 13 <= x <= 28},
                                     {x: c for (x, yy), c in frames[0].items() if yy == y and 13 <= x <= 28})

    def test_the_stance_has_two_legs_apart_as_full_as_the_reference_and_flat_soles(self):
        lower = figure.pixels(figure.LOWER, figure.LOWER_X0)
        for y in range(48, 60):
            row = sorted(x for x, yy in lower if yy == y)
            split = [i for i, (a, b) in enumerate(zip(row, row[1:])) if b - a > 1]
            self.assertEqual(len(split), 1, f'row {y}: two legs apart')
            near, far = row[:split[0] + 1], row[split[0] + 1:]
            for side in (near, far):
                self.assertGreaterEqual(len(side), 6 if y < 53 else 5, f'row {y}: a thin leg')
        self.assertEqual(max(y for _, y in lower), pose.SOLE)


    def test_the_second_holster_hangs_outside_her_and_never_covers_her(self):
        """With the duals: it was painted over her belt, her hip and her seat as she ran."""
        for f in list(FRAMES) + [None]:
            plain = figure.running(f)[1] if f is not None else figure.standing()[1]
            dual = figure.running(f, dual=True)[1] if f is not None else figure.standing(dual=True)[1]
            case = {p: c for p, c in dual.items() if p not in plain}
            with self.subTest(frame=f):
                self.assertEqual({p: dual[p] for p in plain}, plain, 'The holster is over her body')
                self.assertGreater(sum(c in figure.LEATHER_TONES for c in case.values()), 7, 'It does show')
                self.assertEqual(len(components(case)), 1)
                for x, y in case:                        # Beside her near hip, never out in the air
                    row = [a for a, b in plain if b == y]
                    self.assertLess(x, min(row) if row else 99)

    def test_the_second_holster_is_on_the_installed_sheets_too(self):
        for name in ('walk', 'stand', 'jump'):
            single, both = load(art.OUT / f'{name}.png'), load(art.OUT / f'{name}_dual.png')
            width = 54 if name == 'jump' else W
            for f in range(both.width // width):
                a, b = frame_of(single, f, width), frame_of(both, f, width)
                belt = [y for (x, y), c in a.items() if c in (figure.COLORS['b'], figure.COLORS['v']) and 38 <= y <= 56]
                self.assertTrue(belt)
                gone = [p for p, c in a.items() if p[1] > min(belt) + 2 and b.get(p) != c and c in legs.TONES]
                with self.subTest(sheet=name, frame=f):
                    self.assertEqual(gone, [], 'Her trousers are covered')


class SheriffSheets(unittest.TestCase):
    """The installed sheets are the ones these parts make, at the sizes the game reads."""

    def test_sizes(self):
        breaths = art.STAND_BREATHS + art.STAND_SETTLES
        for name, width, height, count in (('walk', W, H, pose.FRAMES), ('walk_dual', W, H, pose.FRAMES),
                                           ('legs', W, H, pose.FRAMES), ('legs_dual', W, H, pose.FRAMES),
                                           ('stand', W, H, breaths), ('stand_dual', W, H, breaths),
                                           ('jump', 54, 82, 8), ('light_walk', 81, 80, pose.FRAMES + 4)):
            sheet = load(art.OUT / f'{name}.png')
            self.assertEqual((sheet.width, sheet.height), (width * count, height), name)

    def test_installed_frames_have_the_legs_and_torso_of_the_rig(self):
        sheet = load(art.OUT / 'walk.png')
        for f in FRAMES:
            px = frame_of(sheet, f)
            drawn = art.walking_body(f, True)
            near = art.arm_pixels(art.walk_arms(f)[0], pose.BELT + pose.bob(f), W // 2 + 1)
            kept = [p for p, c in drawn.items() if c in legs.TONES and p not in near]
            self.assertGreater(len(kept), 60)
            for p in kept:
                self.assertEqual(px.get(p), drawn[p], f'frame {f} at {p}: rebuild her sheets')

    def test_the_legs_under_an_action_keep_the_hips_she_stands_with(self):
        sheet = load(art.OUT / 'legs.png')
        rows = {}
        for f in FRAMES:
            px = frame_of(sheet, f)
            for y in (44, 45, 46):
                rows.setdefault(y, set()).add((min(x for x, yy in px if yy == y and x >= 12),
                                               max(x for x, yy in px if yy == y and x <= 28)))
        for y, spans in rows.items():
            self.assertLessEqual(max(a for a, _ in spans) - min(a for a, _ in spans), 2, f'row {y}: her hips slide')


if __name__ == '__main__':
    unittest.main()
