#!/usr/bin/env python3
"""The cowgirl's melee poses and arm (tools/make_flashlight.py draws the sheets): a smash with the gun (V), overhead and
down like a mace (like the SWAT's), drawn from her own shoot sheet.

Frames: 0 the gun coming up; 1 raised over her head, the muzzle back; 2
swinging down; 3 the smash, level in front of her with a swoosh (the hit
lands here: PLAYER_MELEE_HIT_FRAME); 4 the follow-through, down; 5 back up;
6 the holster frame of its shoot sheet. Her body is the aim frame without
the gun arm (what differs from her other poses, her clothes carried on where
it lay); the arm is her grey sleeve drawn again, as slim as on her art, from the
shoulder to the hand, and the gun with its glove is turned about
the hand in whole pixels, so nothing stretches or breaks off. Her other hand
stays on her hip. The SWAT's sheets come from tools/make_swat.py. Uses only the standard library.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cowgirl_arm import arm_limb, glove, pistol_pointing  # noqa: E402
from make_powers import INK, SLEEVE, load  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402
from rework_cowgirl import ON_HIPS, draw_arm, fit_back, fit_torso, no_art_arms  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 81, 80
AIM, LOW, HOLSTER = 3, 0, 7      # Shoot-sheet frames used
ARM_ROWS = range(29, 43)         # Where her gun arm and gun are on the aim frame...
ARM_FROM_X = 36                  # ...from this column on
WALK_SHIFT = (12, 7)             # A walk-frame point on the shoot template
WALK_CHIN_ROW = 23               # A walk row across her face, to find her middle
WALK_CHEST_ROWS = (28, 34)       # Walk rows from the choker to the lace
WALK_CHEST_HALF = 8              # Art columns each side of her neck
WALK_BODY_ROWS = (33, 41)        # Walk rows of her torso
HAND = (48, 35)                  # A hand to measure the blow's arc from
SHOULDER = (39, 36)
SWOOSH = [rgb(0xfff6dc), rgb(0xd8d0c0), rgb(0x9a9488)]
# Per frame: hand (from the shoulder), gun angle (degrees, + raises the
# muzzle), lean. Like the SWAT's: overhead and down.
POSES = [((7, -5), 55, 0), ((3, -11), 105, -1), ((8, -9), 50, 0), ((12, -2), -10, 1),
         ((11, 3), -40, 1), ((10, 0), -15, 0), None]


GUN_ARM = 12.4                    # Shoulder to hand, whatever the pose: no stretching


def _steady(pose: tuple) -> tuple:
    """A pose with its hand at her arm's length, in the same direction."""
    if pose is None:
        return None
    (hx, hy), angle, lean = pose
    d = max(math.hypot(hx, hy), 1.0)
    return ((round(hx * GUN_ARM / d), round(hy * GUN_ARM / d)), angle, lean)


POSES = [_steady(p) for p in POSES]


def sleeve(shoulder: tuple, hand: tuple) -> dict:
    """Her gun arm: the same arm as all her others, straight from the shoulder to the hand."""
    return arm_limb(shoulder, ((shoulder[0] + hand[0]) / 2, (shoulder[1] + hand[1]) / 2), hand)


def frame(sheet: Image, f: int) -> dict:
    out = {}
    for y in range(H):
        for x in range(W):
            c = sheet.get(f * W + x, y)
            if c[3]:
                out[(x, y)] = c
    return out


SHOOT_BELT, SHOOT_MID = 49, 34    # Her belt's row and her buckle's middle, on the shoot template


def body_without_arm(aim: dict, low: dict, rest: dict, hand_on_hip: bool = True) -> dict:
    """The aim frame less her gun arm and gun: what is not the same in her
    other poses there. Her clothes carry on (from the left) where it lay. Her other arm is
    the one she stands with, its hand on her hip; or none, for a pose that draws it."""
    moving = {p for p, c in aim.items()
              if p[0] >= ARM_FROM_X and p[1] in ARM_ROWS and not (low.get(p) == c and rest.get(p) == c)}
    body = {p: c for p, c in aim.items() if p not in moving}
    for y in ARM_ROWS:
        inside = [x for (x, yy) in body if yy == y and x < ARM_FROM_X + 10]
        if not inside:
            continue
        fill = None
        for x in range(min(inside), max(inside) + 1):   # Holes inside her: the cloth to their left
            c = body.get((x, y))
            if c is not None and c[:3] != INK[:3]:
                fill = c
            elif c is None and fill is not None:
                body[(x, y)] = fill
    # Her side, under where the arm lay, was never drawn: from her standing pose.
    walk = load(ROOT / 'assets/sprites/characters/cowgirl/stand.png')
    grey = {tuple(c[:3]) for c in SLEEVE}
    added = []
    for y in range(WALK_BODY_ROWS[0], WALK_BODY_ROWS[1] + 1):
        for x in range(42):
            c = walk.get(x, y)
            at = (x + WALK_SHIFT[0], y + WALK_SHIFT[1])
            if c[3] and at not in body and c[:3] != INK[:3] and c[:3] not in grey and at[0] >= ARM_FROM_X - 4 and at[0] <= ARM_FROM_X + 8:
                body[at] = c
                added.append(at)
    for x, y in added:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + a, y + b) not in body:
                body[(x + a, y + b)] = INK
    # Her neckline, whole, the same as standing: choker, skin, shoulders and lace.
    # What she had here lost parts with the arm.
    skin = [x for y in range(WALK_CHIN_ROW, WALK_CHIN_ROW + 1) for x in range(42)
            if walk.get(x, y)[3] and walk.get(x, y)[:3] == (0xfe, 0xdc, 0xa3)]
    neck = sum(skin) // len(skin)
    for y in range(WALK_CHEST_ROWS[0], WALK_CHEST_ROWS[1] + 1):
        for x in range(neck - WALK_CHEST_HALF, neck + WALK_CHEST_HALF + 1):
            c = walk.get(x, y)
            if c[3]:
                body[(x + WALK_SHIFT[0], y + WALK_SHIFT[1])] = c
    fit_torso(body, SHOOT_BELT, SHOOT_MID)
    fit_back(body, SHOOT_BELT, SHOOT_MID)
    no_art_arms(body, SHOOT_BELT, SHOOT_MID)
    body = {p: c for p, c in body.items()                  # No loose speck left where the arm was
            if any((p[0] + a, p[1] + b) in body for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b)}
    if hand_on_hip:
        draw_arm(body, ON_HIPS[0], SHOOT_BELT, SHOOT_MID)
    return body


def no_holes(px: dict) -> dict:
    """Pixels the turning left out, inside a shape: a gap with something on at
    least three sides takes the colour most of them have."""
    out = dict(px)
    for _ in range(2):
        xs = [x for x, _y in out]
        ys = [y for _x, y in out]
        for y in range(min(ys), max(ys) + 1):
            for x in range(min(xs), max(xs) + 1):
                if (x, y) in out:
                    continue
                around = [out[n] for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if n in out]
                if len(around) >= 3:
                    out[(x, y)] = max(around, key=around.count)
    return out


def turn(pixels: dict, pivot: tuple, angle: float, at: tuple) -> dict:
    """pixels turned by angle about pivot, pivot placed at `at`: each frame
    pixel takes the source pixel under its center (whole pixels, no blur)."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    if not pixels:
        return {}
    r = max(math.hypot(x - pivot[0], y - pivot[1]) for (x, y) in pixels) + 2
    out = {}
    for y in range(int(at[1] - r), int(at[1] + r) + 1):
        for x in range(int(at[0] - r), int(at[0] + r) + 1):
            fx, fy = x + 0.5 - at[0], y + 0.5 - at[1]
            key = (math.floor(fx * ca - fy * sa + pivot[0] + 0.5), math.floor(fx * sa + fy * ca + pivot[1] + 0.5))
            if key in pixels:
                out[(x, y)] = pixels[key]
    return out


def tip(gun: dict, angle: float, at: tuple) -> tuple:
    """Where the muzzle (the gun's farthest pixel) ends up."""
    mx, my = max(gun, key=lambda p: (p[0] - HAND[0]) ** 2 + (p[1] - HAND[1]) ** 2)
    a = math.radians(angle)
    lx, ly = mx - HAND[0], my - HAND[1]
    return (at[0] + lx * math.cos(a) + ly * math.sin(a), at[1] - lx * math.sin(a) + ly * math.cos(a))


def swoosh(out: dict, gun: dict, before: tuple, now: tuple, heavy: bool) -> None:
    """The muzzle's path from the last pose to this one: a pale arc."""
    (h0, a0, _), (h1, a1, _) = before, now
    h0 = (SHOULDER[0] + h0[0], SHOULDER[1] + h0[1])
    h1 = (SHOULDER[0] + h1[0], SHOULDER[1] + h1[1])
    steps = 14
    for i in range(steps + 1):
        t = i / steps
        at = (h0[0] + (h1[0] - h0[0]) * t, h0[1] + (h1[1] - h0[1]) * t)
        x, y = tip(gun, a0 + (a1 - a0) * t, at)
        x, y = round(x) + 1, round(y)
        shade = SWOOSH[0] if t > 0.6 else SWOOSH[1] if t > 0.3 else SWOOSH[2]
        for k in range(2 if heavy and t > 0.4 else 1):
            if (x + k, y) not in out:
                out[(x + k, y)] = shade




def striking_arm(pixels: dict, f: int) -> None:
    """Over her, on pose f: her gun arm and its gun, and the arc of the blow."""
    pose = POSES[f]
    (hx, hy), angle, _ = pose
    hand = (SHOULDER[0] + hx, SHOULDER[1] + hy)
    pixels.update(sleeve(SHOULDER, hand))
    pixels.update(pistol_pointing(hand, angle))
    pixels.update(glove(hand, SHOULDER))
    if f in (3, 4):
        swoosh(pixels, pistol_pointing(HAND, 0), POSES[f - 1], pose, heavy=f == 3)
