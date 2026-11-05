#!/usr/bin/env python3
"""The cowgirl's arm, gloved hand and second pistol, the same in every pose that draws them.

Imported by tools/rework_cowgirl.py, make_melee.py, make_care.py and make_flashlight.py.

An arm is one continuous stroke from the shoulder, as thick on both sides, lit along its
upper edge: never two pieces meeting at a corner. It starts inside her shoulder with no
outline of its own there, so it grows out of her sleeve. The pistol is one sprite for every hand and
pose, assets/sprites/characters/cowgirl/weapons/pistol.png: change the gun there.
Standard library only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import rgb  # noqa: E402

INK = (0x25, 0x20, 0x18, 255)
SLEEVE = [rgb(0x6c7a84), rgb(0x505c66), rgb(0x38424a)]  # Light to dark
GLOVE = [rgb(0x684833), rgb(0x463322)]
ARM_AT_SHOULDER, ARM_AT_WRIST = 2.0, 1.5                # Art px, half its width
SOFT_ELBOW = 2.5                                        # Px off the straight line: under it, a curve
SHOULDER_BLEND = 4.0                                    # Px from its top with no outline: it is inside her sleeve
STEPS = 48
HAND_R, HAND_LONG = 1.6, 1                               # Art px: half its width, and how far it carries on
SIDES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def arm_limb(top: tuple, elbow: tuple, hand: tuple) -> dict:
    """The arm from its shoulder to the wrist. An arm nearly straight bends in one soft curve;
    one really bent has its elbow where it is asked."""
    middle = ((top[0] + hand[0]) / 2, (top[1] + hand[1]) / 2)
    soft = math.hypot(elbow[0] - middle[0], elbow[1] - middle[1]) <= SOFT_ELBOW
    samples = []
    for i in range(STEPS + 1):
        t = i / STEPS
        if soft:                                         # Through the elbow, as one curve
            cx, cy = 2 * elbow[0] - middle[0], 2 * elbow[1] - middle[1]
            x = (1 - t) ** 2 * top[0] + 2 * t * (1 - t) * cx + t * t * hand[0]
            y = (1 - t) ** 2 * top[1] + 2 * t * (1 - t) * cy + t * t * hand[1]
        else:
            a, b, k = (top, elbow, t * 2) if t < 0.5 else (elbow, hand, t * 2 - 1)
            x, y = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        samples.append((x, y, ARM_AT_SHOULDER + (ARM_AT_WRIST - ARM_AT_SHOULDER) * t))
    px, nearest = {}, {}
    for i, (x, y, r) in enumerate(samples):
        ax, ay, _ = samples[max(i - 1, 0)]
        bx, by, _ = samples[min(i + 1, STEPS)]
        tx, ty = bx - ax, by - ay
        length = max(math.hypot(tx, ty), 0.01)
        nx, ny = ty / length, -tx / length
        if ny > 0.2 or (abs(ny) <= 0.2 and nx > 0):      # Its lit edge: up, or to the left
            nx, ny = -nx, -ny
        for py in range(int(y - r - 1), int(y + r + 2)):
            for pxx in range(int(x - r - 1), int(x + r + 2)):
                dx, dy = pxx + 0.5 - x, py + 0.5 - y
                d = dx * dx + dy * dy
                if d <= r * r and d < nearest.get((pxx, py), 1e9):
                    nearest[(pxx, py)] = d
                    side = (dx * nx + dy * ny) / r
                    px[(pxx, py)] = SLEEVE[0] if side > 0.2 else SLEEVE[1] if side > -0.4 else SLEEVE[2]
    out = dict(px)
    for (x, y) in px:
        for a, b in SIDES:
            at = (x + a, y + b)
            if at not in px and math.hypot(at[0] - top[0], at[1] - top[1]) > SHOULDER_BLEND:
                out[at] = INK
    return out


def glove(at: tuple, coming_from: tuple = None) -> dict:
    """Her gloved hand: a round end to the wrist, no wider than it. Given where the arm comes
    from, it carries on along it, closing the arm instead of sitting across it."""
    ux, uy = 0.0, 1.0
    if coming_from:
        d = max(math.hypot(at[0] - coming_from[0], at[1] - coming_from[1]), 1.0)
        ux, uy = (at[0] - coming_from[0]) / d, (at[1] - coming_from[1]) / d
    px = {}
    for k in range(HAND_LONG * 2 + 1):
        cx, cy = at[0] + ux * k / 2, at[1] + uy * k / 2
        for y in range(int(cy) - 3, int(cy) + 4):
            for x in range(int(cx) - 3, int(cx) + 4):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                if dx * dx + dy * dy <= HAND_R * HAND_R:
                    px[(x, y)] = GLOVE[(dx * uy - dy * ux) * (1 if uy >= 0 else -1) > 0.3 or dy > 0.8]
    out = dict(px)
    for (a, b) in px:
        for c, d in SIDES:
            if (a + c, b + d) not in px:
                out[(a + c, b + d)] = INK
    return out


PISTOL = Path(__file__).resolve().parent.parent / 'assets/sprites/characters/cowgirl/weapons/pistol.png'
GRIP_AT = (2.0, 9.5)             # On the sprite: where her hand closes, what the gun turns about
MUZZLE_AT = (16.0, 3.0)             # ...and the middle of its muzzle
ZOOM = 8                          # Three doublings: lines keep their width when turned
_cache = {}


def _double(px: dict, w: int, h: int) -> tuple:
    """Scale2x: twice the size, edges staying sharp, no new colours."""
    out = {}
    for y in range(h):
        for x in range(w):
            e = px.get((x, y))
            b, d, f, g = px.get((x, y - 1)), px.get((x - 1, y)), px.get((x + 1, y)), px.get((x, y + 1))
            if b != g and d != f:
                parts = (d if d == b else e, f if b == f else e, d if d == g else e, f if g == f else e)
            else:
                parts = (e, e, e, e)
            for k, c in enumerate(parts):
                if c is not None:
                    out[(2 * x + k % 2, 2 * y + k // 2)] = c
    return out, 2 * w, 2 * h


def _zoomed() -> tuple:
    if 'zoom' not in _cache:
        w, h, rgba = decode_png_rgba(PISTOL)
        px = {(x, y): tuple(rgba[(y * w + x) * 4:(y * w + x) * 4 + 4]) for y in range(h) for x in range(w)
              if rgba[(y * w + x) * 4 + 3]}
        size = (w, h)
        for _ in range(3):
            px, *size = _double(px, *size)
        _cache['zoom'] = px
    return _cache['zoom']


def turned(offset: tuple, degrees: float) -> tuple:
    """An offset turned (+ raises it, y down)."""
    a = math.radians(degrees)
    return offset[0] * math.cos(a) + offset[1] * math.sin(a), -offset[0] * math.sin(a) + offset[1] * math.cos(a)


def pistol_muzzle(at: tuple, angle: float) -> tuple:
    dx, dy = turned((MUZZLE_AT[0] - GRIP_AT[0], MUZZLE_AT[1] - GRIP_AT[1]), angle)
    return at[0] + dx, at[1] + dy


def pistol_pointing(at: tuple, angle: float) -> dict:
    """Her pistol, the one sprite, its grip at the hand and turned about it (degrees, + raises
    the muzzle). The sprite goes up eight times, turns there and comes back: it keeps its lines."""
    key = round(angle)
    if key not in _cache:
        zoom = _zoomed()
        a = math.radians(key)
        ca, sa = math.cos(a), math.sin(a)
        reach = 26
        turned_px = {}
        for y in range(-reach, reach + 1):
            for x in range(-reach, reach + 1):
                dx, dy = x + 0.5, y + 0.5                # The pixel's centre, from the hand
                sx = dx * ca - dy * sa + GRIP_AT[0]      # ...back on the sprite
                sy = dx * sa + dy * ca + GRIP_AT[1]
                c = zoom.get((math.floor(sx * ZOOM), math.floor(sy * ZOOM)))
                if c:
                    turned_px[(x, y)] = c
        _cache[key] = turned_px
    x0, y0 = math.floor(at[0]), math.floor(at[1])
    return {(x + x0, y + y0): c for (x, y), c in _cache[key].items()}
