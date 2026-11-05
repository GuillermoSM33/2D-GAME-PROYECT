#!/usr/bin/env python3
"""Draw the cowgirl's ricochet bullet: assets/sprites/characters/cowgirl/weapons/bullet.png.

Usage: tools/make_ricochet.py   (run by tools/rebuild_cowgirl.py)

14 frames of 20 x 16, the ball's centre near (10, 8), flying to the right:
  0-3   in flight: a gold ball and its short flickering trail
  4-7   after glancing off a body: smaller, spinning, its trail curving away
  8-13  the impact, drawn once for each of her two bullets: a hot flash, then a few
        fragments thrown forward. Small: it is a glance, not an explosion.
Standard library only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_sprites import Image, rgb  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / 'assets/sprites/characters/cowgirl/weapons/bullet.png'
W, H = 20, 16
CX, CY = 10, 8
INK = rgb(0x4a2a12)
WHITE, HOT, GOLD, EMBER, ASH = rgb(0xfffbe0), rgb(0xfff1a0), rgb(0xfbaa38), rgb(0xc8641c), rgb(0x7a4a22)
FLY, SPIN, BURST = 4, 4, 6


def ball(px: dict, x: float, y: float, r: float) -> None:
    for py in range(H):
        for pxx in range(W):
            d = math.hypot(pxx + 0.5 - x, py + 0.5 - y)
            if d <= r + 0.7:
                px[(pxx, py)] = INK
    for py in range(H):
        for pxx in range(W):
            d = math.hypot(pxx + 0.5 - x, py + 0.5 - y)
            if d <= r:
                px[(pxx, py)] = HOT if d <= r * 0.55 else GOLD


def fly(f: int) -> dict:
    px = {}
    length = 6 + f % 2                                   # It flickers
    for k in range(length):
        x = CX - 3 - k
        px[(x, CY - 1 + (k + f) % 2)] = GOLD if k < 2 else EMBER if k < 4 else ASH
    if f % 2:
        px[(CX - 4, CY + 1)] = EMBER
    ball(px, CX + 1, CY, 1.9)
    return px


def spin(f: int) -> dict:
    px = {}
    for k in range(5):                                   # Its trail curves away where it came from
        px[(CX - 3 - k, CY + 1 + k // 2 + (f + k) % 2 // 2)] = GOLD if k < 1 else EMBER if k < 3 else ASH
    ball(px, CX, CY, 1.5)
    a = f * math.pi / 2                                  # A fleck going round it: it spins
    px[(round(CX + 3.4 * math.cos(a)), round(CY + 3.4 * math.sin(a)))] = HOT
    return px


# Fragments thrown forward: angle (degrees, 0 ahead, + up), and how far each frame takes it.
FRAGMENTS = (0, 28, -30, 62, -58, 112, -118)


def burst(f: int) -> dict:
    px = {}
    if f == 0:                                           # The hit: a hot point
        for a, b in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            px[(CX + a, CY + b)] = WHITE if abs(a) + abs(b) < 2 else HOT
        return px
    if f == 1:                                           # A star
        for k in range(1, 6):
            c = HOT if k < 3 else GOLD
            px[(CX + k, CY)] = c
            px[(CX, CY + k - 1 if k > 4 else CY + min(k, 3))] = GOLD
            px[(CX, CY - min(k, 3))] = GOLD
            if k < 3:
                px[(CX - k, CY)] = GOLD
                px[(CX + k, CY + k)] = EMBER
                px[(CX + k, CY - k)] = EMBER
        px.update({(CX + a, CY + b): WHITE for a in (0, 1) for b in (0,)})
        return px
    reach = 2.5 + f * 1.25
    color = {2: HOT, 3: GOLD, 4: EMBER, 5: ASH}[f]
    fragments = FRAGMENTS if f < 4 else FRAGMENTS[:5] if f < 5 else FRAGMENTS[:3]
    for angle in fragments:
        a = math.radians(angle)
        far = reach * (1.0 if abs(angle) < 90 else 0.6)  # The few thrown back don't go as far
        x, y = round(CX + far * math.cos(a)), round(CY - far * math.sin(a))
        if 0 <= x < W and 0 <= y < H:
            px[(x, y)] = color
            if f < 4:                                    # Still a streak back toward the hit
                bx, by = round(CX + (far - 1.2) * math.cos(a)), round(CY - (far - 1.2) * math.sin(a))
                px.setdefault((bx, by), EMBER)
    if f == 2:
        px[(CX, CY)] = GOLD
    return px


def main() -> int:
    frames = [fly(f) for f in range(FLY)] + [spin(f) for f in range(SPIN)] + [burst(f) for f in range(BURST)]
    img = Image(W * len(frames), H)
    for i, px in enumerate(frames):
        for (x, y), c in px.items():
            if 0 <= x < W and 0 <= y < H:
                img.set(i * W + x, y, c)
    OUT.parent.mkdir(exist_ok=True)
    img.save(OUT)
    print(f'make_ricochet: {OUT.name} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
