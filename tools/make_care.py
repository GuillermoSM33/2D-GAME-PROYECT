#!/usr/bin/env python3
"""Make the cowgirl's care sheets: drinking from a jug and binding a wound.

Usage: tools/make_care.py

Writes (6 frames of 81 x 80 each, the shoot template, like her reload):
  assets/sprites/characters/cowgirl/drink.png    The jug up to her lips: low,
      coming up, tipped to her lips, tipped right up, tipping back, lowered.
  assets/sprites/characters/cowgirl/bandage.png  Her hand winding a bandage
      round her thigh, a turn more each frame; the last, done, blood showing.

Her body is her aim frame without the gun arm (tools/make_melee.py's
body_without_arm; the gun is holstered); the arm is her slim grey sleeve
drawn from the shoulder to the hand, and the jug turns in her hand in whole
pixels. The SWAT's come from tools/make_swat.py. Uses only the standard
library.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_melee import AIM, HOLSTER, LOW, SHOULDER, frame, body_without_arm, sleeve, turn  # noqa: E402
from make_powers import INK, load  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 81, 80
GLOVE = [rgb(0x999a9c), rgb(0x696867)]
JUG_COLORS = {'c': rgb(0x9a643a), 'b': rgb(0x2a5a86), 'B': rgb(0x5aa0d0), 'w': rgb(0xd8f0fa)}
JUG = ['.cc.', 'bccb', 'BBBB', 'BwBB', 'BwBB', 'BBBB', 'bbbb']
BANDAGE = [rgb(0x9a9488), rgb(0xd8d4c8), rgb(0xf6f2e6)]
# Drinking: her hand (frame px) and the jug's tilt (degrees, its mouth toward her lips).
DRINK = [((46, 40), 0), ((45, 35), 20), ((42, 31), 65), ((41, 30), 110), ((42, 31), 65), ((45, 38), 10)]
# Binding: her hand going round her thigh (in front, behind, in front...).
BIND = [(40, 47), (37, 50), (41, 49), (37, 47), (41, 50), (40, 48)]
THIGH = (34, 39, 47, 52)          # x0, x1, y0, y1 of her near thigh


def jug() -> dict:
    out = {}
    for y, row in enumerate(JUG):
        for x, ch in enumerate(row):
            if ch != '.':
                out[(x, y)] = JUG_COLORS[ch]
    edged = dict(out)
    for (x, y) in out:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in out:
                edged[(x + dx, y + dy)] = INK
    return edged


def hand(at: tuple) -> dict:
    return {(at[0] + i, at[1] + j): GLOVE[j] for i in (0, 1) for j in (0, 1)}


def wraps(turns: int, done: bool) -> dict:
    """The bandage round her thigh: turns slanted strips, outlined."""
    x0, x1, y0, y1 = THIGH
    out = {}
    for t in range(turns):
        y = y1 - t * 2
        for x in range(x0, x1 + 1):
            out[(x, y + (x - x0) // 4 - 1)] = BANDAGE[2] if x < x1 - 2 else BANDAGE[1]
    if done:
        out[(x0 + 4, y1 - 4)] = rgb(0x9c3424)
        out[(x0 + 5, y1 - 4)] = rgb(0x9c3424)
        out[(x0 + 4, y1 - 3)] = rgb(0x74231a)
    edged = dict(out)
    for (x, y) in out:
        for dx, dy in ((0, 1), (0, -1)):
            if (x, y + dy) not in out and (x, y + dy) not in edged:
                edged[(x, y + dy)] = BANDAGE[0]
    return edged


def make_drink(body: dict) -> Image:
    img = Image(W * len(DRINK), H)
    for f, (at, tilt) in enumerate(DRINK):
        px = dict(body)
        px.update(sleeve(SHOULDER, at))
        px.update(turn(jug(), (1.5, 3.5), tilt, (at[0] + 0.5, at[1] - 1.5)))  # Held about its middle
        px.update(hand(at))
        if f == 3:                                       # A drop or two at her lips
            for x, y in ((38, 33), (39, 35)):
                px[(x, y)] = JUG_COLORS['w']
        for (x, y), c in px.items():
            if 0 <= x < W and 0 <= y < H:
                img.set(f * W + x, y, c)
    return img


def make_bandage(body: dict) -> Image:
    img = Image(W * len(BIND), H)
    for f, at in enumerate(BIND):
        px = dict(body)
        done = f == len(BIND) - 1
        behind = not done and f % 2 == 1                 # Round the back of her leg
        if behind:
            px.update(sleeve(SHOULDER, at))
        px.update(wraps(min(f + 1, 5), done))
        if not behind:
            px.update(sleeve(SHOULDER, at))
            if not done:                                 # The roll in her hand
                px.update({(at[0] + 2 + i, at[1] + j): BANDAGE[2 - j] for i in (0, 1) for j in (0, 1)})
            px.update(hand(at))
        for (x, y), c in px.items():
            if 0 <= x < W and 0 <= y < H:
                img.set(f * W + x, y, c)
    return img


def main() -> int:
    shoot = load(ROOT / 'assets/sprites/characters/cowgirl/shoot.png')
    body = body_without_arm(frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER))
    for name, img in (('drink', make_drink(body)), ('bandage', make_bandage(body))):
        path = ROOT / f'assets/sprites/characters/cowgirl/{name}.png'
        img.save(path)
        print(f'make_care: {path.relative_to(ROOT).as_posix()} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
