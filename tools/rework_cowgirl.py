#!/usr/bin/env python3
"""Dress the cowgirl: her costume over her base sheets, and her whole body in three quarters.

Usage: tools/rebuild_cowgirl.py runs this and all that build on it, in order.

Reads docs/templates/cowgirl/{walk,shoot}.png and writes to
assets/sprites/characters/cowgirl/:
  walk.png, walk_dual.png    20 frames: her run, measured on the reference (cowgirl_pose.py)
  stand.png, stand_dual.png  6 frames: 4 stood still, breathing, then 2 pulling up from a run
  legs.png, legs_dual.png    20 frames: her running legs at the height she stands at, for the
      legs under another action (player_render.c)
  jump.png, jump_dual.png    8 frames, 54 x 82
  shoot.png                  the dressed template: its flash is used by make_flashlight.py
Her head, hat and hair are her own pixels from the template, the same in every frame. Her
torso, hips and legs are one three-quarter body (cowgirl_torso.py, cowgirl_legs.py) and her
arms are drawn apart (cowgirl_arm.py): the far one behind her body, the near one in front.
dress() still makes the body she has from the front, for the bench (make_sit.py). Standard
library only.
"""
from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_powers import load  # noqa: E402
from cowgirl_arm import GLOVE as GLOVE_TAGS, SLEEVE as SLEEVE_TAGS, arm_limb, glove  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402
import cowgirl_legs as legs  # noqa: E402
import cowgirl_pose as pose  # noqa: E402
import cowgirl_torso as figure  # noqa: E402
from cowgirl_pose import bob as stride_bob  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs/templates/cowgirl'
OUT = ROOT / 'assets/sprites/characters/cowgirl'
SHEETS = {'walk': 42, 'shoot': 81, 'jump': 54}
WALK_H, JUMP_H = 67, 82
WALK_FRAMES = pose.FRAMES
STAND_BREATHS, STAND_SETTLES = 4, 2  # PLAYER_STAND_*

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
# Her arms, from her belt and buckle (walk grid). Stood still: one hand on her hip, the other
# hanging by her gun.
ARM_BONE = pose.ARM_BONE
WALK_COLUMN = pose.MID            # Her buckle on every walk frame, as on stand and shoot: her body stays put, only bobbing
NEAR_ON_HIP = ((-7.2, -11.8), (-11.7, -6.8), (-7.2, -1.8))
FAR_HANGING = ((5.0, -11.0), (7.0, -5.8), (7.2, -.6))
# Pulling up from a run: how far she leans, rows she is down, how her chest and the tip of her
# hair carry on, and her arms on their way to rest.
SETTLE = (
    dict(lean=1, down=1, chest=1, sway=1.2, near=((-6.6, -11.4), (-9.0, -5.2), (-3.4, -3.4)),
         far=((5.2, -11.0), (6.4, -4.6), (10.4, -1.6))),
    dict(lean=0, down=0, chest=-1, sway=.6, near=((-7.0, -11.6), (-10.9, -6.4), (-6.0, -2.2)),
         far=((5.0, -11.0), (7.0, -5.0), (8.6, -.4))),
)
SETTLE_LEGS = (((18.2, 45.9), (19.2, 51.0), (16.4, 56.5), 4), ((23.9, 45.9), (26.8, 50.9), (26.2, 56.5), 3))
BREATH = ((0, 0., 0.), (-1, .4, -.4), (-1, .8, -.5), (0, .4, -.1))   # Chest, hair tip, hands
# In the air, frame by frame: rows her belt is off its mark, her lean, her chest, her hair's
# tip, then her near and far legs (knee, ankle, foot) and where each hand is from its shoulder.
JUMP_MID, JUMP_DROP = 6, 8        # The jump grid's, from the walk's
JUMP = (
    (4, 1, 0, .4, (20.8, 52.8, 16.8, 56.5, 5), (28.2, 52.4, 26.0, 56.5, 3), (-4.5, 11), (5.0, 10)),
    (1, 1, -1, -.4, (18.2, 50.8, 15.4, 55.8, 52), (27.2, 49.6, 26.4, 54.6, 56), (-5.5, 9.5), (6.5, 9)),
    (1, 1, 0, -1.2, (18.4, 50.2, 14.2, 53.2, 94), (28.2, 48.8, 27.6, 53.2, 62), (-6.5, 8.5), (8.0, 7)),
    (-1, 0, 0, -1.4, (20.6, 48.2, 16.4, 51.0, 104), (27.8, 47.0, 26.8, 51.4, 68), (-7.0, 8), (8.5, 6)),
    (-1, 0, 0, -.8, (21.0, 48.2, 17.4, 51.6, 96), (27.4, 47.2, 27.0, 51.8, 60), (-7.0, 8), (8.0, 7)),
    (0, 0, -1, .2, (19.4, 49.4, 16.8, 53.8, 54), (27.0, 48.8, 28.2, 53.2, 34), (-6.0, 9), (7.0, 8.5)),
    (5, 1, 1, 1.2, (21.8, 53.4, 17.2, 56.5, 4), (28.8, 52.8, 26.8, 56.5, 3), (-5.0, 10), (6.0, 9.5)),
    (0, 0, 0, .6, (18.8, 50.6, 16.8, 56.4, 5), (25.8, 50.6, 25.8, 56.4, 4), (-4.5, 11), (5.0, 10.5)),
)
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


def walk_arms(f: int) -> tuple:
    """Her running arms, the near one first, from her belt and buckle: the elbows bent and
    nearly still, the forearms swinging against her legs. Each from its own shoulder, with
    bones of one length."""
    dx, dy = WALK_COLUMN, pose.BELT + stride_bob(f)
    return tuple(tuple((x - dx, y - dy) for x, y in pose.arm(f, far)) for far in (False, True))


def rest_arms() -> tuple:
    """Stood still, the near one first: a hand on her hip; the other hangs by her holster."""
    return NEAR_ON_HIP, FAR_HANGING


def jump_arms(f: int) -> tuple:
    near, far = JUMP[f][6:]
    return (pose.bent(NEAR_ON_HIP[0], (NEAR_ON_HIP[0][0] + near[0], NEAR_ON_HIP[0][1] + near[1])),
            pose.bent(FAR_HANGING[0], (FAR_HANGING[0][0] + far[0], FAR_HANGING[0][1] + far[1])))


FAR_TONES = {SLEEVE_TAGS[0]: SLEEVE_TAGS[1], SLEEVE_TAGS[1]: SLEEVE_TAGS[2]}


def arm_pixels(arm: tuple, belt: float, mid: float, far: bool = False) -> dict:
    """An arm with its gloved hand; the far one a tone deeper, away from the light."""
    top, elbow, hand = ((mid + a, belt + b) for a, b in arm)
    px = arm_limb(top, elbow, hand, shoulder_radius=1.9 if far else 2.0)
    if far:
        px = {p: FAR_TONES.get(c, c) for p, c in px.items()}
    px.update(glove(hand, elbow))
    return px


def draw_arm(out: dict, arm: tuple, belt: float, mid: float, far: bool = False) -> None:
    out.update(arm_pixels(arm, belt, mid, far))


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


def back_hair(out: dict, source: dict, belt: int, motion: float = 0) -> None:
    """A continuous red mane behind the shoulder, ending at the upper hip.

    Keep the source fringe and head intact. The new back mass has broad
    colour planes rather than a thin tail or detached highlight dashes.
    Existing face, clothes, limbs and their outlines always stay in front.
    """
    tones = {colour[:3] for colour in HAIR}
    face = belt - BELT_UNDER_FACE
    chin = [x for (x, y), colour in source.items()
            if y == face + 3 and colour[:3] == (0xfe, 0xdc, 0xa3)]
    if not chin or not any(colour[:3] in tones and y >= face
                           for (x, y), colour in source.items()):
        return
    middle = round(sum(chin) / len(chin))
    foreground = {p for p, colour in out.items() if colour[:3] not in tones | {INK}}
    protected = {p for p, colour in out.items() if colour[:3] == INK and
                 any((p[0] + dx, p[1] + dy) in foreground
                     for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))}
    # Replace the old projecting one-pixel curl with a continuous far-side
    # lock. Its outer edge follows the cheek instead of ending in a red dot.
    stray = {p for p, colour in out.items() if colour[:3] in tones and
             p[0] > middle + 7 and face <= p[1] <= face + 13}
    for x, y in stray:
        out.pop((x, y), None)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = x + dx, y + dy
            if out.get(point) == INK + (255,) and point not in protected:
                out.pop(point, None)
    first, last = face + 2, belt + 1
    length = last - first
    pixels = {}
    for y in range(first, last + 1):
        k = y - first
        lag = min(1.0, k / 10)
        lag = lag * lag * (3 - 2 * lag)
        wave = round(.35 * math.sin(k / 6) + max(-1., min(1., motion)) * .5 * lag)
        widths = (5, 5, 6, 6, 7, 7, 7, 6, 6, 6, 6, 5, 5, 5, 5, 5, 4, 4, 4, 3, 2, 2)
        width = widths[min(k, len(widths) - 1)]
        left = middle - 13 + wave + int(k < 2) + max(0, k - 14) // 5
        for dx in range(width):
            point = (left + dx, y)
            previous = out.get(point)
            if point in foreground or point in protected:
                continue
            if previous is not None and previous[:3] not in tones | {INK}:
                continue
            # Preserve the original dark/base balance. Its bright red was
            # only a few pixels, never a continuous orange stripe.
            colour = HAIR[1] if 1 <= dx <= max(2, width // 2) else HAIR[0]
            if dx == 0 and (3 <= k <= 6 or 11 <= k <= 14):
                colour = HAIR[1]
            if dx == 2 and k in (4, 13):
                colour = HAIR[2]
            pixels[point] = colour
    # The far lock is narrower in three quarters and disappears naturally
    # behind the collar. Existing face, clothing and arms still occlude it.
    for y in range(face - 1, face + 14):
        left = middle + (6 if y <= face + 7 else 5)
        width = 2 if y <= face + 9 else 1
        for dx in range(width):
            point = left + dx, y
            previous = out.get(point)
            if point in foreground or point in protected or \
                    previous is not None and previous[:3] not in tones | {INK}:
                continue
            pixels[point] = HAIR[1 if dx == 0 else 0]
    outlined(pixels, out)


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
    back_hair(out, px, belt, motion)
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


@lru_cache(maxsize=1)
def _template() -> dict:
    source = load(SOURCE / 'walk.png')
    return steady({(x, y): source.get(x, y) for y in range(source.height) for x in range(SHEETS['walk'])
                   if source.get(x, y)[3]})


@lru_cache(maxsize=1)
def _front_body() -> dict:
    return dress(_template(), armed=False, arms=())


def front_body() -> dict:
    """Her body seen from the front, without arms: what the bench is made from."""
    return dict(_front_body())


@lru_cache(maxsize=1)
def _head() -> tuple:
    """Her own head, from the hat to her chin, the far lock of her hair below it and the long
    one down her back. The loose ends of the far lock's old outline, stuck out of it like
    thorns, go."""
    chin = pose.BELT - 15
    top = {p: c for p, c in _front_body().items() if p[1] <= chin}
    for (x, y), c in list(top.items()):
        if c[:3] == INK and x >= 29 and y >= 20 and not any(
                top.get((x + a, y + b), c)[:3] != INK for a in (-1, 0, 1) for b in (-1, 0, 1)):
            del top[x, y]
    hair = {}
    back_hair(hair, _template(), pose.BELT, 0)
    lock = {p: c for p, c in hair.items() if p[0] >= WALK_COLUMN and p[1] > chin}
    back = {p: c for p, c in hair.items() if p[0] < WALK_COLUMN}
    return top, lock, back


def head(dx: int = 0, dy: int = 0) -> dict:
    """Her head as the template has it, every pixel of her face: it is only moved."""
    return {(x + dx, y + dy): c for (x, y), c in _head()[0].items()}


def mane(ahead: int = 0, sway: float = 0., dy: int = 0) -> dict:
    """The long lock down her back, its root going with her head (ahead columns) and its tip
    swaying a column or so. Its inner side carries on under her back and her arm, so no block
    of outline is left between them."""
    out = {}
    for (x, y), c in _head()[2].items():
        t = max(0., min(1., (y - 22) / 20))
        out[x + round(ahead * (1 - t) + sway * t), y] = c
    rows = {}
    for x, y in out:
        rows[y] = max(rows.get(y, x), x)
    for y, edge in rows.items():
        deep = 0 if y < 30 else 2 if y < 33 else 4 if y < 37 else max(1, 40 - y)
        if deep and out[edge, y][:3] == INK:
            out.update({(edge + k, y): HAIR[(k + y // 3) % 3 == 0] for k in range(deep)})
            out[edge + deep, y] = INK + (255,)
    return {(x, y + dy): c for (x, y), c in out.items()}


def dressed(behind: dict, body: dict, *, ahead: int = 0, dy: int = 0, sway: float = 0., hair: bool = True) -> dict:
    """Her whole body without arms: her hair, what hangs behind her, her body, her head."""
    out = mane(ahead, sway, dy) if hair else {}
    out.update(behind)
    out.update(body)
    out.update(head(ahead, dy))
    out.update({(x + ahead, y + dy): c for (x, y), c in _head()[1].items() if (x + ahead, y + dy) not in body})
    return out


def standing_body(armed: bool = False, dual: bool = False, *, chest: int = 0, lean: int = 0, sway: float = 0.,
                  legs_px: dict = None, hair: bool = True) -> dict:
    """Her one body standing, on the walk grid, without arms. chest: rows her covered chest is
    off it. lean: columns she leans at her head. legs_px: other hips and legs. hair: with the
    long lock down her back."""
    behind, body = figure.standing(chest, armed=armed, dual=dual, legs_px=legs_px)
    out = dressed(behind, body, sway=sway, hair=hair)
    if lean:                                             # From her waist up
        upper = {p: c for p, c in out.items() if p[1] <= figure.BELT_ROW - 1}
        out = {p: c for p, c in out.items() if p not in upper}
        out.update(figure.leaned(upper, lean))
    return out


def walking_body(frame: int, armed: bool = False, dual: bool = False) -> dict:
    """Her body on a frame of the run, on the walk grid, without arms."""
    behind, body = figure.running(frame, armed=armed, dual=dual)
    sway = -.6 + .8 * math.sin(2 * math.pi * pose.phase_of(frame) / 5 - .6)
    return dressed(behind, body, ahead=pose.LEAN, dy=stride_bob(frame), sway=sway)


CROOK = 6                                                # Art px: more hair than this is not a sliver


def behind_arm(body: dict, arm: dict) -> dict:
    """Her body where an arm in front leaves only specks of the star or of a snap in sight:
    cloth there instead, so no loose bits of brass are left beside the arm. Through the crook
    of the arm, her jacket's side in shade instead of slivers of the lock down her back."""
    out = dict(body)
    edge = INK + (255,)
    hair = {p for p, c in body.items() if c in HAIR and p not in arm}
    for group in _groups(hair):
        if len(group) <= CROOK and all(
                any((x - k, y) in arm for k in range(1, CROOK)) and
                any(body.get((x + k, y), edge) not in HAIR + [edge] for k in range(1, CROOK)) for x, y in group):
            out.update({p: figure.COLORS['d'] for p in group})
    for tones, share, limit in ((figure.STAR_TONES, .62, 12), (figure.SNAP_TONES, 1., 6)):
        spots = {p for p, c in body.items() if c in tones}
        for group in _groups(spots):
            if len(group) > limit + 4 or len(group) < 3:
                continue                                 # The far snap is a pair; nothing else has these tones
            if sum(p not in arm for p in group) < share * len(group):
                left = min(x for x, _ in group)
                for x, y in group:
                    out[x, y] = figure.COLORS['c' if tones is figure.STAR_TONES and x > left + 1 else 'w']
    return out


def _groups(points: set) -> list:
    """Points by touching, corners too."""
    left, out = set(points), []
    while left:
        group = {left.pop()}
        todo = list(group)
        while todo:
            x, y = todo.pop()
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    if (x + a, y + b) in left:
                        left.discard((x + a, y + b))
                        group.add((x + a, y + b))
                        todo.append((x + a, y + b))
        out.append(group)
    return out


def with_arms(body: dict, near: dict, far: dict) -> dict:
    """The far arm behind her, the near one in front."""
    out = dict(far)
    out.update(behind_arm(body, near))
    out.update(near)
    return out


def put(img: Image, f: int, w: int, px: dict) -> None:
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < img.height:
            img.set(f * w + x, y, c)


def walk_sheet(armed: bool, dual: bool = False, arms: bool = True) -> Image:
    """Her run, her gun in its holster or not; without arms, what the flashlight's is made on."""
    w = SHEETS['walk']
    img = Image(w * WALK_FRAMES, WALK_H)
    for f in range(WALK_FRAMES):
        body = walking_body(f, armed, dual)
        if arms:
            at = pose.BELT + stride_bob(f)
            near, far = (arm_pixels(arm, at, WALK_COLUMN, i == 1) for i, arm in enumerate(walk_arms(f)))
            body = with_arms(body, near, far)
        put(img, f, w, body)
    return img


def action_legs(frame: int) -> dict:
    """Her running legs on the hips she stands with, for the legs under another action."""
    chains = []
    for far in (True, False):
        (_, knee, ankle, foot), side = pose.leg_chain(frame, far), 1 if far else -1
        chains.append(((20.8 + side * 2.9, 45.0), knee, ankle, foot))
    far, near = (legs.painted(legs.sections(c), c, i == 0) for i, c in enumerate(chains))
    return legs.lower_body(far, near, legs.hips(20.9, pose.BELT + .4, 6.6), pose.BELT, pose.SOLE)


def legs_sheet(dual: bool = False) -> Image:
    w = SHEETS['walk']
    img = Image(w * WALK_FRAMES, WALK_H)
    for f in range(WALK_FRAMES):
        put(img, f, w, standing_body(True, dual, legs_px=action_legs(f)))
    return img


def stand_arms(f: int) -> tuple:
    """Her arms on a frame of stand.png, the near one first, from her belt and buckle."""
    if f < STAND_BREATHS:
        rise = BREATH[f][2]
        return tuple((arm[0], (arm[1][0], arm[1][1] + rise), arm[2]) for arm in rest_arms())
    how = SETTLE[f - STAND_BREATHS]
    return tuple(tuple((x + how['lean'], y + how['down']) for x, y in how[side]) for side in ('near', 'far'))


def stand_frame(f: int, dual: bool = False) -> dict:
    """Stood still, breathing (0-3); pulling up from a run (4-5)."""
    breathing = f < STAND_BREATHS
    if breathing:
        chest, sway, _ = BREATH[f]
        body, down = standing_body(True, dual, chest=chest, sway=sway), 0
    else:
        how = SETTLE[f - STAND_BREATHS]
        down, lower = how['down'], None
        if down:                                         # Her knees give a little
            chains = [(*((x, y - down) for x, y in c[:3]), c[3]) for c in SETTLE_LEGS]
            near, far = (legs.painted(legs.sections(c), c, i == 1) for i, c in enumerate(chains))
            lower = legs.lower_body(far, near, legs.hips(20.9, pose.BELT + .4, 6.6), pose.BELT, pose.SOLE - down)
        body = standing_body(True, dual, chest=how['chest'], lean=how['lean'], sway=how['sway'], legs_px=lower)
        body = {(x, y + down): c for (x, y), c in body.items()}
    arms = stand_arms(f)
    near, far = (arm_pixels(arm, pose.BELT, WALK_COLUMN, i == 1) for i, arm in enumerate(arms))
    out = with_arms(body, near, far)
    if breathing:                                        # Her far hand rests on the gun's grip
        (ex, ey), (hx, hy) = arms[1][1:]
        out.update(glove((WALK_COLUMN + hx + .2, pose.BELT + hy - .4), (WALK_COLUMN + ex, pose.BELT + ey)))
    return {p: c for p, c in out.items() if p[1] <= pose.SOLE}


def stand_sheet(dual: bool) -> Image:
    w = SHEETS['walk']
    img = Image(w * (STAND_BREATHS + STAND_SETTLES), WALK_H)
    for f in range(STAND_BREATHS + STAND_SETTLES):
        put(img, f, w, stand_frame(f, dual))
    return img


def jump_sheet(dual: bool) -> Image:
    w = SHEETS['jump']
    img = Image(w * len(JUMP), JUMP_H)
    for f, (down, lean, chest, sway, near_leg, far_leg, *_) in enumerate(JUMP):
        chains = []
        for side, (kx, ky, ax, ay, foot) in ((1, far_leg), (-1, near_leg)):
            chains.append(((20.9 + side * 2.5, 45.0), (kx, ky - down), (ax, ay - down), foot))
        far, near = (legs.painted(legs.sections(c), c, i == 0) for i, c in enumerate(chains))
        lower = legs.lower_body(far, near, legs.hips(20.9, pose.BELT + .4, 6.2), pose.BELT, pose.SOLE + 8)
        body = standing_body(True, dual, chest=chest, lean=lean, sway=sway, legs_px=lower)
        arms = [tuple((x + lean, y) for x, y in arm) for arm in jump_arms(f)]
        near_arm, far_arm = (arm_pixels(arm, pose.BELT, WALK_COLUMN, i == 1) for i, arm in enumerate(arms))
        put(img, f, w, {(x + JUMP_MID, y + JUMP_DROP + down): c
                        for (x, y), c in with_arms(body, near_arm, far_arm).items()})
    return img


def dressed_shoot() -> Image:
    """The old shoot template in her costume: only its muzzle flash is used (make_flashlight.py)."""
    w = SHEETS['shoot']
    source = load(SOURCE / 'shoot.png')
    img = Image(source.width, source.height)
    first = {(x, y): source.get(x, y) for y in range(source.height) for x in range(w) if source.get(x, y)[3]}
    reference, there = dress(first), landmarks(first)
    for f in range(source.width // w):
        px = {(x, y): source.get(f * w + x, y) for y in range(source.height) for x in range(w)
              if source.get(f * w + x, y)[3]}
        here = landmarks(px)
        moved = set()
        if here and there:                               # What isn't where it is on the first frame
            dx, dy = here[1] - there[1], here[0] - there[0]
            moved = {(x, y) for (x, y), c in px.items() if first.get((x - dx, y - dy)) != c}
        out = dress(px, moved)
        if here and there:
            out = whole_torso(out, here, reference, there)
        put(img, f, w, out)
    return img


def main() -> int:
    for name, img in (('walk', walk_sheet(True)), ('walk_dual', walk_sheet(True, True)),
                      ('legs', legs_sheet()), ('legs_dual', legs_sheet(True)),
                      ('stand', stand_sheet(False)), ('stand_dual', stand_sheet(True)),
                      ('jump', jump_sheet(False)), ('jump_dual', jump_sheet(True)),
                      ('shoot', dressed_shoot())):
        img.save(OUT / f'{name}.png')
        print(f'rework_cowgirl: {name} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
