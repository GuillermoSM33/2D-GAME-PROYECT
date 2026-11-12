#!/usr/bin/env python3
"""Dress the cowgirl: her costume over her base sheets, frame by frame.

Usage: tools/rebuild_cowgirl.py runs this and all that build on it, in order.

Reads docs/templates/cowgirl/{walk,shoot,jump}.png and writes the same
names to assets/sprites/characters/cowgirl/, and stand.png: stood still, hands on her
hips. On walk, jump and stand her body is whole and the same as on every pose
(TORSO_FRONT and so on) with no arm of the art left on it, and both arms are drawn apart:
swinging as she walks. Her hat and her guns stay. Over the
rest: long red hair falling down her back, a neckline curving up to her shoulders
with a lace edge, dark slate puffed sleeves covering them, a slate corset with the
sheriff's brass star on her chest, a wide leather belt with
a brass buckle, a dark red sash hanging from it, striped trousers. Standard
library only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_powers import load  # noqa: E402
from cowgirl_arm import arm_limb, glove  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs/templates/cowgirl'
OUT = ROOT / 'assets/sprites/characters/cowgirl'
SHEETS = {'walk': 42, 'shoot': 81, 'jump': 54}
WALK_FRAMES = 8
ARMED = {'walk', 'jump'}          # Her gun in its holster; in the others, it is in her hand

INK = (0x25, 0x20, 0x18)
BELT_GOLD = (0x9c, 0x85, 0x26)
SKIN = {(0xfe, 0xdc, 0xa3), (0xd9, 0x9a, 0x5b), (0x89, 0x41, 0x1f), (0x8a, 0x43, 0x22)}
HAIR = [rgb(0x6b333a), rgb(0x902004), rgb(0xd03305)]
# Sleeves, everywhere: her greys to slate.
SLEEVES = {(0xa7, 0xa8, 0xa8): rgb(0x6c7a84), (0x99, 0x9a, 0x9c): rgb(0x6c7a84),
           (0x86, 0x86, 0x89): rgb(0x505c66), (0x50, 0x50, 0x50): rgb(0x38424a)}
CORSET = {(0x46, 0x33, 0x22): rgb(0x2c363c), (0x68, 0x48, 0x33): rgb(0x48565e),
          (0x42, 0x42, 0x42): rgb(0x38444a), (0x2c, 0x2c, 0x2c): rgb(0x242c32)}
TROUSERS = {(0x42, 0x42, 0x42): (rgb(0x5e5650), rgb(0x48423e)), (0x2c, 0x2c, 0x2c): (rgb(0x423c38), rgb(0x322e2c)),
            (0x46, 0x33, 0x22): (rgb(0x4c4640), rgb(0x3a3532)), (0x68, 0x48, 0x33): (rgb(0x6e6660), rgb(0x585250))}
LACE = [rgb(0xece6d6), rgb(0xbcb6a6)]
CORSET_TOP = rgb(0x2c363c)
LEATHER = [rgb(0x4a2e18), rgb(0x6c4626)]
HOLSTER = [rgb(0x6c4626), rgb(0x4a2e18)]
CORD = rgb(0x6a6a68)
CORSET_TONES = {(0x2c, 0x36, 0x3c), (0x48, 0x56, 0x5e), (0x38, 0x44, 0x4a), (0x24, 0x2c, 0x32)}
# Canonical material tags for the short open jacket. It is part of the shared
# body before poses are derived, so its lapels rotate with a fall and stay put
# when the head nods in SIT. detail_cowgirl applies the finished wine palette.
JACKET = [rgb(0x8f5968), rgb(0x704052), rgb(0x4c2938)]
JACKET_TONES = {color[:3] for color in JACKET}
# Separate brass snap tags: distinct from the buckle and the sheriff's star.
JACKET_BUTTON = [rgb(0xac8b52), rgb(0x7a5931), rgb(0x34281e)]
BUTTON_TONES = {color[:3] for color in JACKET_BUTTON}
HIP_CURVE = (7, 7, 7, 7, 7, 6)    # Art columns from her belt's middle to her hip, rows down from the belt
HIP_MOST = 2                      # ...and at most this much on what the leg already is
STRAP_UNDER_BELT = 9              # Art rows from her belt to the strap on her thigh
LACING_ROWS = 4
GLOVE = [rgb(0x684833), rgb(0x463322)]
GLOVES_FROM = 7                   # Art rows over the belt where her chest has ended
GUN_BUTT = rgb(0x8a6a3e)
BRASS = [rgb(0xb8903a), rgb(0xecc868)]
SASH = [rgb(0x64182a), rgb(0x8a2438), rgb(0x46101e)]
TORSO_HALF = 9                    # Art columns from her middle, and rows up from the belt, of her torso
TORSO_ROWS = 14
SASH_ROWS = 8                     # Down her thigh, clear of the boots
BELT_UNDER_FACE = 22              # Rows from the top of her face to her belt, in every upright frame
BROWN_SKIN = {(0x89, 0x41, 0x1f), (0x8a, 0x43, 0x22)}
CHOKER = rgb(0x1e1a20)
# The blouse's neckline, a smile: rows under the choker its lace runs at, by art
# columns from the middle of her neck. High at her shoulders, lowest on her chest.
LACE_SMILE = (5, 4, 4, 4, 3, 3, 2, 2)
BARE_WIDTH = {1: 2, 2: 3, 3: 4, 4: 2}  # Rows under the choker: bare columns each side of her neck
CORSET_HALF = 8                   # Art columns from her belt's middle that are her corset
TRAPEZIUS_WIDEST = 5              # Art columns from the middle of her neck that the bare slope reaches
NEAR_HOLSTER, FAR_HOLSTER = 5, 8  # Art columns from her belt's middle to each
CHOKER_UNDER_FACE = 8             # Rows from the top of her face to it
# Her one body, in every pose where she stands: from her belt's row to the last column of
# her side, from her buckle's middle. A curve in runs of two rows: one column a row reads as
# a staircase. Her arms never change it.
TORSO_FRONT = {-10: 6, -9: 6, -8: 5, -7: 5, -6: 4, -5: 3, -4: 3, -3: 4, -2: 4}
BELT_FRONT = {-1: 5, 0: 5, 1: 6}
BACK_SIDE = {-8: -8, -7: -8, -6: -7, -5: -6, -4: -6, -3: -6, -2: -7}  # Its outline, where no arm covers it
CORSET_EDGE = [rgb(0x2c363c), rgb(0x242c32)]
# The sheriff's badge: a six-pointed brass star on her chest, on the wide side of
# her corset as we see her (the near side is only 4 columns from the lacing to
# her outline: it would cut the star). Under the lace, clear of the lacing. Light
# from the top left, as on everything of hers. Only over the corset: an arm in
# front hides it.
BADGE = ('..L..',
         'LLBBB',
         '.LBD.',
         'BBBDD',
         '..D..')
BADGE_TONES = {'L': rgb(0xf6dc86), 'B': rgb(0xd0a848), 'D': rgb(0x8e6c28)}
BADGE_X = -6                       # Art columns from the middle of her neck to its left edge
BADGE_UNDER_FACE = 15              # Rows from the top of her face to its top: under the lace's lowest point
CORD_TONE = (0x6a, 0x6a, 0x68)
LACE_TONES = {(0xec, 0xe6, 0xd6), (0xbc, 0xb6, 0xa6)}
BELT_BACK = {-1: -8, 0: -9, 1: -9}
CHEST_BACK = {-10: -9, -9: -9}
HAND_ROWS = (2, 3)                # Rows under her belt where the art's hands hung by her hips
HIP_LINE, HIP_BACK = 8, -10       # ...and her hips' outlines, past which it was only those hands
LEG_SHADOW, BOOT_SHADOW = rgb(0x322e2c), rgb(0x463322)
SASH_FROM = -9                    # Columns from her buckle's middle to the sash's edge
# Her arms, from her belt and buckle: all 15 long. Stood still, her hands on her hips.
NEAR_SHOULDER, FAR_SHOULDER = (7, -12), (-9, -12)  # At her chest's edges, level
ON_HIPS = (((-9, -12), (-14, -7), (-8, -2)), ((7, -12), (12, -7), (6, -2)))
ARM_BONE = 6.5
# A fixed, relaxed elbow rotated from the shoulder. Solving a fresh elbow
# after rounding the hand made adjacent frames alternate bent/straight.
WALK_ARM_ELBOW = (0.8, 6.4)
WALK_ARM_HAND = (3.3, 12.3)
WALK_ARM_SWING = 4.0              # Degrees each way; a quiet counter-swing to the legs
WALK_COLUMN = 22                  # Her buckle on every walk frame, as on stand and shoot: her body stays put, only bobbing
# In the air: where each hand is, from its shoulder, frame by frame of her jump.
JUMP_FAR = ((-3, 12), (-5, 10), (-7, 8), (-8, 7), (-7, 8), (-5, 10), (-4, 11), (-3, 12))
JUMP_NEAR = ((3, 12), (5, 10), (8, 8), (9, 7), (8, 8), (6, 10), (4, 11), (3, 12))
COLLAR_FROM = 5                   # Art columns from the middle of her neck that the chest's shading is evened over


def over_arm(out: dict, x: int, y: int) -> bool:
    """On one of her sleeves, or the outline around it."""
    sleeve = {c[:3] for c in SLEEVES.values()}
    c = out.get((x, y))
    if c is None:
        return False
    if c[:3] in sleeve:
        return True
    return c[:3] == INK and any(out.get((x + a, y + b), (0, 0, 0, 0))[:3] in sleeve
                                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def outlined(px: dict, over: dict) -> None:
    """Puts px in over, with an outline only on what is empty around it."""
    for (x, y), c in px.items():
        over[(x, y)] = c
    for (x, y) in px:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + a, y + b) not in over:
                over[(x + a, y + b)] = INK + (255,)


def arm_in_front(px: dict, moved: set, x: int, y: int) -> bool:
    """A sleeve that has swung over her chest in this frame, or the outline around
    it: the outline between corset and sleeve goes under. An arm leaves from her
    shoulder, so the neckline itself stays whole over the top of it."""
    def sleeve(a: int, b: int) -> bool:
        return px.get((a, b), (0, 0, 0, 0))[:3] in SLEEVES
    if (x, y) not in moved:
        return False
    return sleeve(x, y) or (px[(x, y)][:3] == INK and any(sleeve(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))))


def neckline(px: dict, moved: set, out: dict, neck_x: float, choker: int) -> None:
    """Skin in a scoop under the choker, its lace edge curving up to her shoulders
    like a smile, the corset up to the lace, an outline parting it from her sleeves.
    Only on her body: never past her outline."""
    def body(x: int, y: int) -> bool:
        return all((x + a, y + b) in out for a, b in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)))

    middle = round(neck_x)
    half = len(LACE_SMILE) - 1
    bottom = choker + max(LACE_SMILE) + 1
    for dx in range(-half - 1, half + 2):
        x = middle + dx
        if abs(dx) > half:                               # Where the corset meets the sleeve
            for y in range(choker + LACE_SMILE[-1] + 1, bottom + 1):
                if body(x, y) and not arm_in_front(px, moved, x, y):
                    out[(x, y)] = INK + (255,)
            continue
        lace_y = choker + LACE_SMILE[abs(dx)]
        for y in range(choker + 1, bottom + 1):
            if not body(x, y):
                continue
            if y < lace_y:
                bare = BARE_WIDTH.get(y - choker, 0)
                if abs(dx) <= bare:
                    out[(x, y)] = rgb(0xd99a5b) if abs(dx) == bare or y == lace_y - 1 else rgb(0xfedca3)
                else:
                    out[(x, y)] = rgb(0x6c7a84) if abs(dx) <= bare + 1 else rgb(0x505c66)
            elif y == lace_y:
                out[(x, y)] = LACE[0]
            elif y == lace_y + 1 and abs(dx) % 2 == 0:
                out[(x, y)] = LACE[1]
            else:
                out[(x, y)] = CORSET_TOP
    if (middle, choker + 1) in out:
        out[(middle, choker + 1)] = rgb(0xb8903a)        # The pendant, over the skin


def outlined_on(out: dict, px: dict) -> None:
    """px over out, with an outline where it meets nothing."""
    out.update(px)
    for (x, y) in px:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + a, y + b) not in out:
                out[(x + a, y + b)] = INK + (255,)


def holster(x0: int, belt: int) -> dict:
    """A small holster on the belt, close to her leg, the gun's butt showing above it."""
    px = {(x0 + i, belt + 2 + j): HOLSTER[i == 1 or j == 3] for i in (0, 1) for j in range(4)}
    px.update({(x0 + i, belt + j): GUN_BUTT for i in (0, 1) for j in (0, 1)})
    return px


def fit_torso(out: dict, belt: int, mid: int) -> None:
    """Her side and her belt's end, the same on every sheet: all that lay past them goes, and
    her clothes carry on where a hand lay on them."""
    keep = LACE_TONES | {CORD_TONE} | SKIN | CORSET_TONES | JACKET_TONES | BUTTON_TONES
    for row, front in TORSO_FRONT.items():
        y, edge = belt + row, mid + front
        for x in [x for (x, yy) in out if yy == y and x > edge + 1]:
            del out[(x, y)]
        out[(edge + 1, y)] = INK + (255,)
        for x in range(mid - 1, edge + 1):
            c = out.get((x, y))
            if c is None or c[:3] not in keep or x == edge and c[:3] in CORSET_TONES:
                out[(x, y)] = CORSET_EDGE[x == edge]
    for row, front in BELT_FRONT.items():
        y, edge = belt + row, mid + front
        for x in [x for (x, yy) in out if yy == y and x > edge + 1]:
            del out[(x, y)]
        out[(edge + 1, y)] = INK + (255,)
        for x in range(mid + 3, edge + 1):               # Whole from the buckle
            out[(x, y)] = LEATHER[row == -1]


def fit_back(out: dict, belt: int, mid: int) -> None:
    """Her back whole, with none of the art's arm on it, and her belt to its end."""
    hair = {h[:3] for h in HAIR}
    keep = LACE_TONES | {CORD_TONE} | SKIN | CORSET_TONES | JACKET_TONES | BUTTON_TONES
    for row, back in {**CHEST_BACK, **BACK_SIDE}.items():
        y, line = belt + row, mid + back
        for x in [x for (x, yy) in out if yy == y and x < line and out[(x, y)][:3] not in hair]:
            del out[(x, y)]
        out[(line, y)] = INK + (255,)
        for x in range(line + 1, mid):
            c = out.get((x, y))
            if c is None or c[:3] not in keep:
                out[(x, y)] = CORSET_EDGE[x == line + 1]
    for row, back in BELT_BACK.items():
        y, line = belt + row, mid + back
        for x in [x for (x, yy) in out if yy == y and x < line and out[(x, y)][:3] not in hair]:
            del out[(x, y)]
        out[(line, y)] = INK + (255,)
        for x in range(line + 1, mid - 1):
            out[(x, y)] = LEATHER[row == -1]


def no_art_arms(out: dict, belt: int, mid: int) -> None:
    """What is left of the art's arms and hands past her hips and her shoulders."""
    sleeve = {c[:3] for c in SLEEVES.values()}
    for row in HAND_ROWS:
        y = belt + row
        for side, line in ((1, mid + HIP_LINE), (-1, mid + HIP_BACK)):
            past = [x for (x, yy) in out if yy == y and (x - line) * side > 0]
            for x in past:
                del out[(x, y)]
            if past:
                out[(line, y)] = INK + (255,)
    for y in (belt - 12, belt - 11):
        for x in [x for (x, yy) in out if yy == y and x < mid - 12 and out[(x, y)][:3] in sleeve]:
            del out[(x, y)]
    for (x, y), c in list(out.items()):                  # Its outline, left alone
        if belt - 14 <= y <= belt + 3 and c[:3] == INK and x < mid - 8 and \
                not any((x + a, y + b) in out and out[(x + a, y + b)][:3] != INK for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            del out[(x, y)]


def bent(top: tuple, hand: tuple) -> tuple:
    """An arm of one length to that hand, its soft elbow back, away from where she walks."""
    dx, dy = hand[0] - top[0], hand[1] - top[1]
    d = max(math.hypot(dx, dy), 1.0)
    along = min(d / 2, ARM_BONE)
    out = math.sqrt(max(0.0, ARM_BONE * ARM_BONE - along * along))
    px, py = -dy / d, dx / d
    if px > 0:
        px, py = -px, -py
    return (top, (top[0] + dx / 2 + px * out, top[1] + dy / 2 + py * out), hand)


def walk_arms(f: int) -> tuple:
    """Both arms swing as fixed limbs: stable elbows, float coordinates until rasterization."""
    swing = math.cos(2 * math.pi * f / WALK_FRAMES)
    arms = []
    for top, side in ((FAR_SHOULDER, -1), (NEAR_SHOULDER, 1)):
        angle = math.radians(WALK_ARM_SWING * swing * side)
        ca, sa = math.cos(angle), math.sin(angle)
        points = [top]
        for x, y in (WALK_ARM_ELBOW, WALK_ARM_HAND):
            x *= side
            points.append((top[0] + x * ca + y * sa, top[1] - x * sa + y * ca))
        arms.append(tuple(points))
    return tuple(arms)


def jump_arms(f: int) -> tuple:
    return tuple(bent(top, (top[0] + at[0], top[1] + at[1])) for top, at in ((FAR_SHOULDER, JUMP_FAR[f]), (NEAR_SHOULDER, JUMP_NEAR[f])))


def draw_arm(out: dict, arm: tuple, belt: int, mid: int) -> None:
    """An arm with its gloved hand."""
    top, elbow, hand = ((mid + a, belt + b) for a, b in arm)
    out.update(arm_limb(top, elbow, hand))
    out.update(glove(hand, elbow))


def legs_apart(out: dict, belt: int, boots: int) -> None:
    """Where her legs cross, the art has a block of outline between them, a hole in her
    trousers: one line of it, and the cloth in shadow either side."""
    for y in range(belt + 3, max(p[1] for p in out)):
        row = sorted(x for (x, yy) in out if yy == y)
        x = row[0]
        while x <= row[-1]:
            end = x
            while out.get((end, y), (0, 0, 0, 0))[:3] == INK:
                end += 1
            inside = (x - 1, y) in out and (end, y) in out
            if end - x >= 3 and inside:
                line = (x + end - 1) // 2
                for k in range(x, end):
                    if k != line:
                        out[(k, y)] = LEG_SHADOW if y < boots else BOOT_SHADOW
            x = max(end, x + 1)


def sheriff_badge(out: dict, neck_x: float, face: int) -> None:
    """Her badge on the corset/jacket fabric, so an arm or gun in front hides it."""
    for j, row in enumerate(BADGE):
        for i, mark in enumerate(row):
            x, y = round(neck_x) + BADGE_X + i, face + BADGE_UNDER_FACE + j
            if mark != '.' and out.get((x, y), (0, 0, 0, 0))[:3] in CORSET_TONES | JACKET_TONES:
                out[(x, y)] = BADGE_TONES[mark]


def corset_bust(out: dict, belt: int, mid: float) -> None:
    """A small rounded volume in the covered chest, on the same body in every pose."""
    cups = {-10: (2, 3), -9: (1, 4), -8: (1, 4), -7: (2, 3)}
    for (x, y), color in list(out.items()):
        if color[:3] not in CORSET_TONES:
            continue
        row, distance = y - belt, abs(x - mid)
        if row in cups and cups[row][0] <= distance <= cups[row][1]:
            out[(x, y)] = rgb(0x48565e)
        elif row == -6 and 1 <= distance <= 4:
            out[(x, y)] = rgb(0x242c32)


def cropped_jacket(out: dict, belt: int, mid: float, front: bool = False) -> None:
    """Open wine side panels over the corset; lapels taper and stop above the belt.

    Outer lace ends are tucked under the lapels, so no pale flecks sit on the
    wine fabric. Hair, arms, lacing and the badge remain in front.
    """
    lapels = {-12: (-3, 2), -11: (-4, 2), -10: (-4, 3),
              -9: (-5, 3), -8: (-5, 4)}
    for (x, y), color in list(out.items()):
        row, column = y - belt, x - mid
        if not -12 <= row <= -3:
            continue
        far, near = lapels.get(row, (-6, 4))
        if front:
            far = -near  # SIT faces the viewer: equal lapels on both sides.
        on_panel = column <= far or column >= near
        if (color[:3] in LACE_TONES and (on_panel or abs(column) >= 4)) or \
                (color[:3] in SKIN and abs(column) >= 4):
            out[(x, y)] = JACKET[1]
            continue
        if color[:3] not in CORSET_TONES:
            continue
        if on_panel:
            fold = row in lapels and min(abs(column - far), abs(column - near)) < 1
            out[(x, y)] = JACKET[0 if fold else 2 if row == -3 else 1]


def jacket_buttons(out: dict, belt: int, mid: float, front: bool = False) -> None:
    """Two small, bevelled brass snaps on the lapels; never paint over skin or an arm."""
    snaps = ((-5.5, -10), (4.5, -10)) if front else ((-7, -11), (4, -10))
    under = JACKET_TONES | BUTTON_TONES
    for dx, dy in snaps:
        x, y = round(mid + dx), belt + dy
        at = ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1))
        if all(out.get(p, (0, 0, 0, 0))[:3] in under for p in at):
            for p, color in zip(at, (JACKET_BUTTON[0], JACKET_BUTTON[1], JACKET_BUTTON[1], JACKET_BUTTON[2])):
                out[p] = color


def dress(px: dict, moved: set = frozenset(), armed: bool = False, arms: tuple = None, dual: bool = False, motion: int = 0) -> dict:
    """One frame. Lying or fallen frames (no belt under a face) get colours only. Arms: her
    one body with no arm of the art on it, and these drawn on it (from walk_arms and so on).
    Dual: a second holster, on her far hip."""
    fit = arms is not None
    faces = [y for (_, y), c in px.items() if c[:3] == (0xfe, 0xdc, 0xa3)]
    out = dict(px)
    for p, c in px.items():
        if c[:3] in SLEEVES:
            out[p] = SLEEVES[c[:3]]
    if not faces:
        return out
    face = min(faces)
    # Her belt's buckle is always this far under her face; without it, she has
    # fallen and only the colours change.
    belt = face + BELT_UNDER_FACE
    belt_x = [x for (x, y), c in px.items() if c[:3] == BELT_GOLD and y == belt]
    if not belt_x:
        return out
    mid = sum(belt_x) // len(belt_x)
    if fit:                                              # Under her chin, as on the other sheets
        chin_row = [x for (x, y), c in px.items() if y == face + 3 and c[:3] == (0xfe, 0xdc, 0xa3)]
        mid = round(sum(chin_row) / len(chin_row)) if chin_row else mid
    neck = face + 9
    # Corset, between her chest and the belt
    for (x, y), c in px.items():
        if neck <= y < belt and c[:3] in CORSET and abs(x - mid) <= CORSET_HALF:  # Not her glove, nor the gun
            out[(x, y)] = CORSET[c[:3]]
    # Trousers striped, down to the boots
    feet = max(y for (_, y) in px)
    boots = feet - 7
    for (x, y), c in px.items():
        if belt < y < boots and c[:3] in TROUSERS:
            out[(x, y)] = TROUSERS[c[:3]][1 if x % 3 == 0 else 0]
    # The middle of her neck, which needn't be over the belt's
    chin = [x for (x, y), c in px.items() if y == face + 3 and c[:3] == (0xfe, 0xdc, 0xa3)]
    neck_x = sum(chin) / len(chin) if chin else float(mid)
    # Bare only along the upper trapezius: the skin opens from her neck down the
    # slope to her shoulders, and the sleeves cover all the rest, following it.
    choker = face + CHOKER_UNDER_FACE
    collar = {}
    for (x, y), c in px.items():
        if choker <= y < belt - 4 and c[:3] in SKIN and x < neck_x:
            opening = min(TRAPEZIUS_WIDEST, 2 + y - choker)
            gap = neck_x - x - 0.5
            if gap > opening:
                collar[(x, y)] = rgb(0x6c7a84) if gap <= opening + 1 else rgb(0x505c66)
    # Her far shoulder, the same; not with that arm out of the frame
    has_far_arm = any(c[:3] in SLEEVES and x > neck_x and y <= choker + max(LACE_SMILE) for (x, y), c in px.items())
    if has_far_arm:
        for (x, y), c in list(collar.items()):
            collar[(round(2 * neck_x - x), y)] = c
    out.update(collar)
    # A dark choker with a little gold pendant, on her neck, bare skin below it
    for (x, y), c in px.items():
        if choker < y < belt - 4 and c[:3] in BROWN_SKIN and (x, y) not in collar and abs(x - neck_x) <= COLLAR_FROM:
            out[(x, y)] = rgb(0xd99a5b)
    for dx in range(-2, 3):
        x = round(neck_x) + dx
        if (x, choker) in out:
            out[(x, choker)] = CHOKER
    hair_tones = {h[:3] for h in HAIR}
    for dx in (-3, 3):                                   # Past its ends, the sleeve
        x = round(neck_x) + dx
        if (x, choker) in out:
            out[(x, choker)] = rgb(0x505c66)
        if out.get((x, choker + 1), (0, 0, 0, 0))[:3] in hair_tones:
            out[(x, choker + 1)] = rgb(0x505c66)
    out[(round(neck_x), choker)] = rgb(0xecc868)
    out[(round(neck_x), choker + 1)] = rgb(0xb8903a)
    neckline(px, moved, out, neck_x, choker)
    # Below her chest there is no bare skin: what is left of her hands has its gloves
    for (x, y), c in list(out.items()):
        if y >= belt - GLOVES_FROM and c[:3] in SKIN:
            # Lower down it was only ever a stain on her leg
            out[(x, y)] = TROUSERS[(0x2c, 0x2c, 0x2c)][0] if y > belt + 1 else GLOVE[c[:3] != (0xfe, 0xdc, 0xa3)]
    # A wide belt with a brass buckle
    for x in range(mid - 9, mid + 10):
        for y in (belt - 1, belt, belt + 1):
            if (x, y) in px and px[(x, y)][:3] != INK:
                out[(x, y)] = LEATHER[y == belt - 1]
    for y in (belt - 1, belt, belt + 1):
        for x in (mid - 1, mid, mid + 1, mid + 2):
            out[(x, y)] = BRASS[y == belt - 1]
    out[(mid, belt)] = LEATHER[0]
    out[(mid + 1, belt)] = LEATHER[0]
    # Her hips: the leg meets the belt in a curve, no step down from it to a thin thigh
    for k, reach in enumerate(HIP_CURVE):
        y = belt + 2 + k
        row = [x for (x, yy) in out if yy == y and x > mid]
        if not row:
            continue
        edge = max(row)
        side = min(mid + reach, edge + HIP_MOST)          # A leg swung in keeps its own shape, no bulge beside it
        if edge > side:
            continue
        start = edge                                      # All of the leg's old outline: none left inside her thigh
        while start > mid and out.get((start - 1, y), (0, 0, 0, 0))[:3] == INK:
            start -= 1
        for x in range(start, side + 1):
            out[(x, y)] = TROUSERS[(0x42, 0x42, 0x42)][1 if x % 3 == 0 else 0]
        out[(side + 1, y)] = INK + (255,)
    # The strap round her near thigh
    for y in (belt + STRAP_UNDER_BELT, belt + STRAP_UNDER_BELT + 1):
        for x in [x for (x, yy) in out if yy == y and x > mid + 1]:
            if out[(x, y)][:3] != INK:
                out[(x, y)] = LEATHER[y != belt + STRAP_UNDER_BELT]
    # The corset's lacing, crossing up its middle
    lace_x = round(neck_x)
    for y in range(belt - LACING_ROWS - 1, belt - 1):
        for x in ((lace_x,) if (y - belt) % 2 else (lace_x - 1, lace_x + 1)):
            if out.get((x, y), (0, 0, 0, 0))[:3] in CORSET_TONES:
                out[(x, y)] = CORD
    if fit:
        legs_apart(out, belt, boots)
        fit_torso(out, belt, mid)
        fit_back(out, belt, mid)
        no_art_arms(out, belt, mid)
    corset_bust(out, belt, mid)
    sheriff_badge(out, neck_x, face)                     # On her finished body, before any arm crosses it
    cropped_jacket(out, belt, mid)
    jacket_buttons(out, belt, mid)
    # The gun in its holster on her near hip, when it isn't in her hand
    if armed:
        outlined_on(out, holster(mid + NEAR_HOLSTER, belt))
    # The sash, from the belt at her back, ragged at its end
    back = mid + SASH_FROM if fit else min(x for (x, y) in px if y == belt + 1)
    sash = {}
    for i in range(SASH_ROWS):
        width = 5 - i // 3
        for w in range(width):
            x = back + 1 + w - (i // 5) - round(motion * i / (SASH_ROWS - 1))
            if i == SASH_ROWS - 1 and w % 2:
                continue
            sash[(x, belt + 1 + i)] = SASH[(w + i // 3) % 2] if w else SASH[2]
    outlined(sash, out)
    if dual:                                             # On her far hip, over the sash
        outlined_on(out, holster(mid - FAR_HOLSTER, belt))
    if fit:                                              # Over all of her: the far one, then the near
        for arm in arms:
            draw_arm(out, arm, belt, mid)
    # Her hair, in waves over her shoulder and down her back, to the waist
    hair = [(x, y) for (x, y), c in px.items() if c[:3] in {h[:3] for h in HAIR}]
    if hair:
        lowest = max(y for _, y in hair)
        left = min(x for x, y in hair if y >= lowest - 4)
        for y in range(lowest - 2, belt - 3):
            k = y - (lowest - 2)
            wave = (k // 3) % 3 - 1 + round(motion * min(1.0, k / 8))
            width = max(2, 4 - k // 6)
            x0 = left + 1 + wave
            if all(over_arm(out, x0 + w, y) for w in range(width)):
                break                                    # Her arm hides it here: no loose end past it
            for w in range(width):                       # Behind her arm: only where it isn't
                if not over_arm(out, x0 + w, y):
                    out[(x0 + w, y)] = HAIR[2] if w == 1 and k % 4 == 0 else HAIR[1] if w < width - 1 else HAIR[0]
            for x in (x0 - 1, x0 + width):
                if (x, y) not in out:
                    out[(x, y)] = INK + (255,)
    return out


def landmarks(px: dict) -> tuple | None:
    """Her belt's row and middle, if she is upright."""
    faces = [y for (_, y), c in px.items() if c[:3] == (0xfe, 0xdc, 0xa3)]
    if not faces:
        return None
    belt = min(faces) + BELT_UNDER_FACE
    golds = [x for (x, y), c in px.items() if c[:3] == BELT_GOLD and y == belt]
    return (belt, sum(golds) // len(golds)) if golds else None


def whole_torso(dressed: dict, here: tuple, reference: dict, there: tuple) -> dict:
    """Where her swinging arm has left a gap there was never any body drawn, its
    place always covered: her torso from the reference frame fills it."""
    sleeve = {c[:3] for c in SLEEVES.values()}
    out = dict(dressed)
    dx, dy = here[1] - there[1], here[0] - there[0]
    added = []
    for (x, y), c in reference.items():
        mx, my = x + dx, y + dy
        near = abs(x - there[1]) <= TORSO_HALF and there[0] - TORSO_ROWS <= y < there[0]
        if near and (mx, my) not in out and c[:3] not in sleeve and c[:3] != INK:
            out[(mx, my)] = c
            added.append((mx, my))
    for (x, y) in added:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + a, y + b) not in out:
                out[(x + a, y + b)] = INK + (255,)
    return out


def steady(px: dict) -> dict:
    """A walk frame moved so her chin, and so her buckle, is on WALK_COLUMN."""
    face = min(y for (_, y), c in px.items() if c[:3] == (0xfe, 0xdc, 0xa3))
    chin = [x for (x, y), c in px.items() if y == face + 3 and c[:3] == (0xfe, 0xdc, 0xa3)]
    dx = WALK_COLUMN - round(sum(chin) / len(chin))
    return {(x + dx, y): c for (x, y), c in px.items()}


def on_legs(upper: dict, legs: dict) -> dict:
    """The upper body of one walk frame, down to her belt, on the legs of another, bobbing with them."""
    def top(px: dict) -> int:
        return min(y for (_, y), c in px.items() if c[:3] == (0xfe, 0xdc, 0xa3))
    up, down = top(upper), top(legs)
    under = BELT_UNDER_FACE + 2                          # Rows from the top of her face to under her belt
    out = {(x, y + down - up): c for (x, y), c in upper.items() if y < up + under}
    out.update({p: c for p, c in legs.items() if p[1] >= down + under})
    return out


def dressed_sheet(name: str, armed: bool, dual: bool = False, no_arms: bool = False) -> Image:
    """A whole sheet in her costume, the gun in its holster or not; on the sheets with her own
    arms, both drawn in their poses, or none at all (what her legs join to)."""
    w = SHEETS[name]
    source = load(SOURCE / f'{name}.png')
    img = Image(source.width, source.height)
    pose = {'walk': walk_arms, 'jump': jump_arms}.get(name)
    first = {(x, y): source.get(x, y) for y in range(source.height) for x in range(w) if source.get(x, y)[3]}
    reference, there = dress(first, armed=armed), landmarks(first)
    for f in range(source.width // w):
        px = {(x, y): source.get(f * w + x, y) for y in range(source.height) for x in range(w)
              if source.get(f * w + x, y)[3]}
        if pose:
            if name == 'walk':                           # As with the flashlight up: one upper body, on the legs of each frame
                px = on_legs(steady(first), steady(px))
            # Cloth and the ends of her hair lag behind the step/takeoff;
            # the belt and head remain fixed on the shared body landmarks.
            motion = {'walk': (0, -1, -1, 0, 1, 1, 0, 0),
                      'jump': (-1, -1, -1, 0, 1, 1, 0, 0)}[name][f]
            dressed = dress(px, armed=armed, arms=() if no_arms else pose(f), dual=dual, motion=motion)
        else:
            here = landmarks(px)
            moved = set()
            if here and there:                           # What isn't where it is on the first frame
                dx, dy = here[1] - there[1], here[0] - there[0]
                moved = {(x, y) for (x, y), c in px.items() if first.get((x - dx, y - dy)) != c}
            dressed = dress(px, moved, armed)
            if here and there:
                dressed = whole_torso(dressed, here, reference, there)
        for (x, y), c in dressed.items():
            if 0 <= x < w and 0 <= y < source.height:
                img.set(f * w + x, y, c)
    return img


def stand_sheet(dual: bool) -> Image:
    """Stood still: the walk's first legs, her hands on her hips."""
    source = load(SOURCE / 'walk.png')
    w = SHEETS['walk']
    img = Image(w, source.height)
    px = {(x, y): source.get(x, y) for y in range(source.height) for x in range(w) if source.get(x, y)[3]}
    for (x, y), c in dress(px, armed=True, arms=ON_HIPS, dual=dual).items():
        if 0 <= x < w and 0 <= y < source.height:
            img.set(x, y, c)
    return img


def main() -> int:
    for name in SHEETS:
        img = dressed_sheet(name, name in ARMED)
        img.save(OUT / f'{name}.png')
        print(f'rework_cowgirl: {name} ({img.width} x {img.height})')
        if name in ARMED:                                # With the duals, the second on her far hip
            dressed_sheet(name, True, True).save(OUT / f'{name}_dual.png')
    # Her walk with no arms, for the walking legs under another pose (player_render.c)
    dressed_sheet('walk', True, no_arms=True).save(OUT / 'legs.png')
    dressed_sheet('walk', True, True, no_arms=True).save(OUT / 'legs_dual.png')
    stand_sheet(False).save(OUT / 'stand.png')
    stand_sheet(True).save(OUT / 'stand_dual.png')
    return 0


if __name__ == '__main__':
    sys.exit(main())
