#!/usr/bin/env python3
"""Make the characters' faint sheets: out cold from a heatstroke.

Usage: tools/make_faint.py [cowgirl|swat ...]   (after tools/rework_cowgirl.py: from her dressed walk)

Writes assets/sprites/characters/<id>/faint.png for the cowgirl and the SWAT:
8 frames of 80 x 67 (wide enough to lie down in), drawn from the standing
frame of their walk sheet, its ground on row 61 and its pivot on column 40
like the walk template's. Frames: 0-1 swaying on her feet, 2-3 the knees
giving way, 4-5 toppling forward, 6-7 lying face down on the ground. The
falls are turns of the standing art, whole quarter turns at the end, so the
lying frames stay true pixel art. Uses only the standard library.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_powers import load  # noqa: E402
from make_sprites import Image  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WALK_W, WALK_H = 42, 67          # The walk template
WALK_ANCHOR, GROUND = 19.5, 61   # Its pivot column and ground row
W, H = 80, 67
PIVOT = 40                       # Where the walk pivot goes in a faint frame
KNEE = 47                        # Rows above this drop when the knees give way


def standing(walk: Image) -> dict:
    out = {}
    for y in range(WALK_H):
        for x in range(WALK_W):
            c = walk.get(x, y)
            if c[3]:
                out[(x - round(WALK_ANCHOR) + PIVOT, y)] = c
    return out


def sway(px: dict, dx: int) -> dict:
    """Her upper body leaning dx px (the higher the row, the more)."""
    return {(x + (dx if y < 30 else dx // 2 if y < KNEE else 0), y): c for (x, y), c in px.items()}


def kneel(px: dict, drop: int) -> dict:
    """The knees giving way: rows above KNEE come down drop px (the rows they
    land on, the thighs, are folded under)."""
    out = {}
    for (x, y), c in px.items():
        if y >= KNEE:
            out[(x, y)] = c
    for (x, y), c in sorted(px.items(), key=lambda p: p[0][1]):
        if y < KNEE:
            out[(x, y + drop)] = c
    return out


def topple(px: dict, angle: float) -> dict:
    """Turned angle degrees forward (the way she faces) about her toes, whole
    pixels; then rested on the ground row."""
    a = math.radians(-angle)  # Forward: her head goes the way she faces
    ca, sa = math.cos(a), math.sin(a)
    pivot = (PIVOT + 4, GROUND)
    xs = [x for x, _ in px]
    ys = [y for _, y in px]
    r = int(math.hypot(max(xs) - min(xs), max(ys) - min(ys))) + 4
    out = {}
    for y in range(GROUND - r, GROUND + r):
        for x in range(pivot[0] - r, pivot[0] + r):
            fx, fy = x + 0.5 - pivot[0], y + 0.5 - pivot[1]
            # Back from the frame to the standing art (a turn the other way).
            src = (math.floor(fx * ca - fy * sa + pivot[0]), math.floor(fx * sa + fy * ca + pivot[1]))
            if src in px:
                out[(x, y)] = px[src]
    low = max(y for _, y in out)
    mid = (min(x for x, _ in out) + max(x for x, _ in out)) // 2
    # Falling, she comes back toward the middle of the frame: all of her stays in it.
    shift = (PIVOT - mid if abs(angle) >= 80 else PIVOT + 6 - mid if abs(angle) >= 50 else 0, GROUND - low)
    return {(x + shift[0], y + shift[1]): c for (x, y), c in out.items()}


def make(walk: Image) -> Image:
    up = standing(walk)
    frames = [
        sway(up, 1),
        sway(up, -1),
        kneel(sway(up, 1), 3),
        kneel(up, 8),
        topple(kneel(up, 8), 30),
        topple(kneel(up, 6), 60),
        topple(up, 90),
        topple(up, 90),                                  # Still
    ]
    img = Image(W * len(frames), H)
    for f, px in enumerate(frames):
        for (x, y), c in px.items():
            if 0 <= x < W and 0 <= y < H:
                img.set(f * W + x, y, c)
    return img


def main() -> int:
    for who in sys.argv[1:] or ('cowgirl', 'swat'):
        folder = ROOT / f'assets/sprites/characters/{who}'
        walk = load(folder / ('stand.png' if (folder / 'stand.png').exists() else 'walk.png'))
        img = make(walk)
        path = ROOT / f'assets/sprites/characters/{who}/faint.png'
        img.save(path)
        print(f'make_faint: {path.relative_to(ROOT).as_posix()} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
