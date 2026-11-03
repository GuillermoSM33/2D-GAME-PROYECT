#!/usr/bin/env python3
"""Make the cowgirl's melee sheets: a smash with the gun (V), overhead and
down like a mace (like the SWAT's), drawn from her own shoot sheet.

Usage: tools/make_melee.py

Writes (7 frames of 81 x 80, the shoot template's frame size):
  assets/sprites/characters/cowgirl/melee.png       Her hand cannon, in one hand
  assets/sprites/characters/cowgirl/melee_dual.png  The dual pistols, one in each hand

Frames: 0 the gun coming up; 1 raised over her head, the muzzle back; 2
swinging down; 3 the smash, level in front of her with a swoosh (the hit
lands here: PLAYER_MELEE_HIT_FRAME); 4 the follow-through, down; 5 back up;
6 the holster frame of its shoot sheet. Her body is the aim frame without
the gun arm (what differs from her other poses, her clothes carried on where
it lay); the arm is her grey sleeve drawn again, as slim as on her art, from the
shoulder to the hand, and the gun with its glove is turned about
the hand in whole pixels, so nothing stretches or breaks off. With one gun
her other hand stays on her hip; with the duals that arm (off her hip:
without_hip_arm) swings across her front under her gun arm, a shade
darker, its gun just behind and under the first, never over the near one. The SWAT's sheets come from
tools/make_swat.py. Uses only the standard library.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_powers import INK, SLEEVE, load, without_hip_arm  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 81, 80
AIM, LOW, HOLSTER = 3, 0, 7      # Shoot-sheet frames used
ARM_ROWS = range(29, 43)         # Where her gun arm and gun are on the aim frame...
ARM_FROM_X = 36                  # ...from this column on
GUN_FROM_X = 46                  # The gun with its glove
HAND = (48, 35)                  # The glove's middle, on the aim frame: the gun turns about it
SHOULDER = (39, 36)
WAIST = 44                       # Above it she leans into the blow
SWOOSH = [rgb(0xfff6dc), rgb(0xd8d0c0), rgb(0x9a9488)]
# Per frame: hand (from the shoulder), gun angle (degrees, + raises the
# muzzle), lean. Like the SWAT's: overhead and down.
POSES = [((7, -5), 55, 0), ((3, -11), 105, -1), ((8, -9), 50, 0), ((12, -2), -10, 1),
         ((11, 3), -40, 1), ((10, 0), -15, 0), None]
BEHIND = (-2, 3)                 # With the duals, her far hand: a little behind and under the first


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


def dim(c: tuple) -> tuple:
    """A shade darker: what is farther from us."""
    return tuple(round(v * 0.8) for v in c[:3]) + (255,) if c[:3] != INK[:3] else c


def frame(sheet: Image, f: int) -> dict:
    out = {}
    for y in range(H):
        for x in range(W):
            c = sheet.get(f * W + x, y)
            if c[3]:
                out[(x, y)] = c
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
    return body


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


def make(shoot: Image, dual: bool, holster: dict) -> Image:
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    body = body_without_arm(aim, low, rest)
    if dual:  # Her other arm leaves her hip for its gun
        body, far_shoulder = without_hip_arm(body)
    gun = {p: c for p, c in aim.items() if p[0] >= GUN_FROM_X and p[1] in range(26, 42)}
    img = Image(W * len(POSES), H)
    for f, pose in enumerate(POSES):
        if pose is None:
            pixels = holster
        else:
            (hx, hy), angle, lean = pose
            hand = (SHOULDER[0] + hx, SHOULDER[1] + hy)
            a = math.radians(angle)
            # Back to front: her; with the duals her other arm across her front,
            # a shade darker, its gun just behind and under the first; over
            # them her gun arm and its gun. With one gun her other hand stays
            # on her hip.
            pixels = dict(body)
            if dual:
                far = (hand[0] + BEHIND[0], hand[1] + BEHIND[1])
                pixels.update({p: dim(c) for p, c in sleeve(far_shoulder, far).items()})
                pixels.update({p: dim(c) for p, c in turn(gun, HAND, angle, far).items()})
            pixels.update(sleeve(SHOULDER, hand))
            pixels.update(turn(gun, HAND, angle, hand))
            if f in (3, 4):
                swoosh(pixels, gun, POSES[f - 1], pose, heavy=f == 3)
            pixels = {(x + (lean if y < WAIST else 0), y): c for (x, y), c in pixels.items()}
        for (x, y), c in pixels.items():
            if 0 <= x < W and 0 <= y < H:
                img.set(f * W + x, y, c)
    return img


def main() -> int:
    # Both from her one-gun sheet: with the duals the second gun is drawn
    # again in her far hand, under the first, as on shoot_dual.
    for dst, dual in (('melee', False), ('melee_dual', True)):
        shoot = load(ROOT / 'assets/sprites/characters/cowgirl/shoot.png')
        own = load(ROOT / f'assets/sprites/characters/cowgirl/{"shoot_dual" if dual else "shoot"}.png')
        img = make(shoot, dual, frame(own, HOLSTER))  # Back to rest as on its shoot sheet
        path = ROOT / f'assets/sprites/characters/cowgirl/{dst}.png'
        img.save(path)
        print(f'make_melee: {path.relative_to(ROOT).as_posix()} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
