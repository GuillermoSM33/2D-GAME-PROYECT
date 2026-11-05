#!/usr/bin/env python3
"""Make the cowgirl's care sheets: drinking from a jug and binding a wound.

Usage: tools/make_care.py

Writes (6 frames of 81 x 80 each, the shoot template, like her reload):
  assets/sprites/characters/cowgirl/drink.png    The jug up to her lips: low,
      coming up, tipped to her lips, tipped right up, tipping back, lowered.
  assets/sprites/characters/cowgirl/bandage.png  Her arm bent to her thigh,
      winding a bandage round it, a turn more each frame; the last, blood showing.

Her body is her aim frame without the gun arm (tools/make_melee.py's
body_without_arm; the gun is holstered); the arm is her slim grey sleeve
drawn from the shoulder to the hand, and the jug turns in her hand in whole
pixels. The SWAT's come from tools/make_swat.py. Uses only the standard
library.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cowgirl_arm import GLOVE, arm_limb as bent_arm, glove  # noqa: E402
from make_melee import AIM, HOLSTER, LOW, SHOULDER, frame, body_without_arm, sleeve, turn  # noqa: E402
from make_powers import INK, load  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 81, 80
JUG_COLORS = {'c': rgb(0x9a643a), 'b': rgb(0x2a5a86), 'B': rgb(0x5aa0d0), 'w': rgb(0xd8f0fa)}
JUG = ['.cc.', 'bccb', 'BBBB', 'BwBB', 'BwBB', 'BBBB', 'bbbb']
BANDAGE = [rgb(0xb8ac94), rgb(0xe6dcc0), rgb(0xf4ecd8)]
# Drinking: her hand (frame px) and the jug's tilt (degrees, its mouth toward her lips).
DRINK = [((46, 41), 0), ((45, 37), 25), ((44, 34), 75), ((43, 33), 110), ((44, 34), 75), ((45, 39), 10)]
# Binding: her hand going round her thigh (in front, behind, in front...).
BIND = [(40, 51), (39, 52), (41, 52), (39, 52), (40, 52), (40, 52)]
ARM_TOP = (38, 38)
BONE = 7.5                        # Upper arm and forearm, the same as on her other poses
THIGH = (35, 41, 52, 56)          # x0, x1, y0, y1 round her near thigh


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
    return glove(at)


def bent_to(top: tuple, at: tuple, under: bool = False) -> dict:
    """Her arm from the shoulder to the hand, bones of one length whatever the reach: the
    elbow goes out to her front or, with the hand up, down under it."""
    d = math.hypot(at[0] - top[0], at[1] - top[1])
    out = math.sqrt(max(0.0, BONE * BONE - d * d / 4.0))
    mx, my = (top[0] + at[0]) / 2, (top[1] + at[1]) / 2
    return bent_arm(top, (round(mx), round(my + out)) if under else (round(mx + out), round(my)), at)


def arm(at: tuple) -> dict:
    """Her arm hanging from the shoulder, reaching down to her thigh."""
    return bent_to(ARM_TOP, at)


def wraps(body: dict, turns: int, done: bool) -> dict:
    """The bandage round her thigh, turn on turn upward: linen-coloured, only on
    the leg itself so it follows its shape; the last, a spot of blood through it."""
    x0, x1, y0, y1 = THIGH
    out = {}
    for y in range(y1 - min(turns, y1 - y0 + 1) + 1, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) in body:
                out[(x, y)] = BANDAGE[0] if (x + y) % 5 == 0 else BANDAGE[1]
    if done:
        for at, c in (((38, 53), rgb(0x9c3424)), ((39, 53), rgb(0x9c3424)), ((38, 54), rgb(0x74231a))):
            if at in out:
                out[at] = c
    return out


def make_drink(body: dict) -> Image:
    img = Image(W * len(DRINK), H)
    for f, (at, tilt) in enumerate(DRINK):
        px = dict(body)
        px.update(bent_to(SHOULDER, at, under=True))
        px.update(turn(jug(), (1.5, 3.5), tilt, (at[0] + 0.5, at[1] - 1.5)))  # Held about its middle
        px.update(hand(at))
        if f == 3:                                       # A drop or two at her lips
            for x, y in ((39, 34), (40, 36)):
                px[(x, y)] = JUG_COLORS['w']
        for (x, y), c in px.items():
            if 0 <= x < W and 0 <= y < H:
                img.set(f * W + x, y, c)
    return img


def make_bandage(body: dict) -> Image:
    img = Image(W * len(BIND), H)
    for f, at in enumerate(BIND):
        px = {p: c for p, c in body.items()                # Without the stray specks round her
              if any((p[0] + dx, p[1] + dy) in body for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        done = f == len(BIND) - 1
        px.update(wraps(px, f + 2, done))
        px.update(arm(at))                               # Always in front: going round, the roll a bit lower
        if not done:                                     # The roll in her hand
            px.update({(at[0] - 1 + i, at[1] + 1 + j): BANDAGE[2 - j] for i in (0, 1, 2) for j in (0, 1)})
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
