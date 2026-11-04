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
from make_powers import INK, SLEEVE, load  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 81, 80
AIM, LOW, HOLSTER = 3, 0, 7      # Shoot-sheet frames used
ARM_ROWS = range(29, 43)         # Where her gun arm and gun are on the aim frame...
ARM_FROM_X = 36                  # ...from this column on
GUN_FROM_X = 46                  # The gun with its glove
WALK_SHIFT = (12, 7)             # A walk-frame point on the shoot template
WALK_CHIN_ROW = 23               # A walk row across her face, to find her middle
WALK_CHEST_ROWS = (28, 34)       # Walk rows from the choker to the lace
WALK_CHEST_HALF = 8              # Art columns each side of her neck
WALK_BODY_ROWS = (33, 41)        # Walk rows of her torso
ELBOW_AT = (44, 38)              # Where her glove starts, on the aim frame
HAND = (48, 35)                  # The glove's middle, on the aim frame: the gun turns about it
SHOULDER = (39, 36)
LACE_COLORS = {(0xec, 0xe6, 0xd6), (0xbc, 0xb6, 0xa6)}
WAIST = 44                       # Above it she leans into the blow
SWOOSH = [rgb(0xfff6dc), rgb(0xd8d0c0), rgb(0x9a9488)]
# Per frame: hand (from the shoulder), gun angle (degrees, + raises the
# muzzle), lean. Like the SWAT's: overhead and down.
POSES = [((7, -5), 55, 0), ((3, -11), 105, -1), ((8, -9), 50, 0), ((12, -2), -10, 1),
         ((11, 3), -40, 1), ((10, 0), -15, 0), None]


UPPER_ARM = 10.4                  # Shoulder to where the glove starts, whatever the pose: no stretching


def _steady(pose: tuple) -> tuple:
    """A pose with its hand moved along the arm so the sleeve keeps its length."""
    if pose is None:
        return None
    (hx, hy), angle, lean = pose
    a = math.radians(angle)
    ex, ey = ELBOW_AT[0] - HAND[0], ELBOW_AT[1] - HAND[1]
    rx, ry = ex * math.cos(a) + ey * math.sin(a), -ex * math.sin(a) + ey * math.cos(a)
    ux, uy = hx + rx, hy + ry
    d = max(math.hypot(ux, uy), 1.0)
    return ((round(ux * UPPER_ARM / d - rx), round(uy * UPPER_ARM / d - ry)), angle, lean)


POSES = [_steady(p) for p in POSES]


def sleeve(shoulder: tuple, hand: tuple) -> dict:
    """Her grey sleeve from the shoulder to the hand, as slim as on her art:
    a small round over the shoulder, narrowing to the wrist, lit on top and
    shaded under, outlined."""
    (sx, sy), (hx, hy) = shoulder, hand
    n = max(abs(hx - sx), abs(hy - sy), 1)
    px = {}

    def paint(x: int, y: int, cy: float, r: float) -> None:
        k = (y - cy) / max(r, 0.5)
        px[(x, y)] = SLEEVE[0] if k < -0.3 else SLEEVE[1] if k < 0.4 else SLEEVE[2]

    for t in range(n + 1):
        cx = sx + (hx - sx) * t / n
        cy = sy + (hy - sy) * t / n
        r = 1.7 - 0.6 * t / n
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    paint(x, y, cy, r)
    for y in range(sy - 3, sy + 3):                     # The shoulder
        for x in range(sx - 3, sx + 3):
            if (x + 0.5 - sx) ** 2 + (y + 0.5 - sy) ** 2 <= 2.2 ** 2:
                paint(x, y, sy, 2.2)
    out = dict(px)
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in px:
                out[(x + dx, y + dy)] = INK
    return out


def frame(sheet: Image, f: int) -> dict:
    out = {}
    for y in range(H):
        for x in range(W):
            c = sheet.get(f * W + x, y)
            if c[3]:
                out[(x, y)] = c
    return out


# Shoot-frame rows of her waist and the last column of her side on each. Her art only
# has the thin middle of it, its sides always under her arms; with the arm away it
# has to meet her hips. What else was there is the rest of that arm's hand.
WAIST_SIDE = {41: 41, 42: 41, 43: 40, 44: 39, 45: 39, 46: 39, 47: 40}
BELT_SIDE = {48: 40, 49: 41, 50: 41}  # ...and her belt's, as wide as her hips: a V into them, no step
WAIST_FROM = 36                   # Column her corset is drawn out from
CORSET_FILL = [rgb(0x2c363c), rgb(0x242c32)]
BELT_FILL = {48: rgb(0x6c4626), 49: rgb(0x4a2e18), 50: rgb(0x4a2e18)}


def fuller_waist(body: dict) -> dict:
    out = dict(body)
    for y, edge in WAIST_SIDE.items():
        for x in range(WAIST_FROM, edge + 8):
            if x > edge + 1:
                out.pop((x, y), None)
            elif x == edge + 1:
                out[(x, y)] = INK
            else:
                c = out.get((x, y))
                if c is None or c[:3] not in LACE_COLORS:
                    out[(x, y)] = CORSET_FILL[x >= edge - 1]
    for y, edge in BELT_SIDE.items():
        for x in range(WAIST_FROM + 2, edge + 8):
            if x > edge + 1:
                out.pop((x, y), None)
            elif x == edge + 1:
                out[(x, y)] = INK
            elif (x, y) not in out or out[(x, y)][:3] == INK[:3]:
                out[(x, y)] = BELT_FILL[y]
    return out


def body_without_arm(aim: dict, low: dict, rest: dict) -> dict:
    """The aim frame less her gun arm and gun: what is not the same in her
    other poses there. Her clothes carry on (from the left) where it lay."""
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
    walk = load(ROOT / 'assets/sprites/characters/cowgirl/walk.png')
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
    body = fuller_waist(body)
    return {p: c for p, c in body.items()                  # No loose speck left where the arm was
            if any((p[0] + a, p[1] + b) in body for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b)}


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


BARREL_CUT = (54, 57)             # Columns taken out of the base art's barrel: a pistol, not as long as her leg


def shorter_gun(px: dict) -> dict:
    """The gun off her aim frame with its barrel cut down."""
    a, b = BARREL_CUT
    return {(x if x < a else x - (b - a), y): c for (x, y), c in px.items() if not a <= x < b}


def gun_with_glove(aim: dict, body: dict) -> dict:
    """The gun with her glove on it, whole, as on her aim frame."""
    skin = {(0xfe, 0xdc, 0xa3), (0xd9, 0x9a, 0x5b), (0x89, 0x41, 0x1f), (0x8a, 0x43, 0x22)}
    return shorter_gun({p: c for p, c in aim.items() if p[0] >= ELBOW_AT[0] and p[1] in range(26, 44) and body.get(p) != c and c[:3] not in skin})


def striking_arm(pixels: dict, gun: dict, f: int) -> None:
    """Over her, on pose f: her gun arm and its gun, and the arc of the blow."""
    pose = POSES[f]
    (hx, hy), angle, _ = pose
    hand = (SHOULDER[0] + hx, SHOULDER[1] + hy)
    a = math.radians(angle)
    # The sleeve up to where that glove begins, so they join.
    ex, ey = ELBOW_AT[0] - HAND[0], ELBOW_AT[1] - HAND[1]
    elbow = (hand[0] + ex * math.cos(a) + ey * math.sin(a), hand[1] - ex * math.sin(a) + ey * math.cos(a))
    pixels.update(sleeve(SHOULDER, (round(elbow[0]), round(elbow[1]))))
    pixels.update(turn(gun, HAND, angle, hand))
    if f in (3, 4):
        swoosh(pixels, gun, POSES[f - 1], pose, heavy=f == 3)
