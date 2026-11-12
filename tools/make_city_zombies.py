#!/usr/bin/env python3
"""Draw the city's zombie family: five townspeople of Santa Brasa, by trade.

Usage: tools/make_city_zombies.py [assets_dir]   (default: assets)

Writes sprites/zombies/<id>/{idle,walk,run,attack,hurt,death,caught}.png
(frames of 72 x 72, the first route's sizes, anchors and frame counts) for:
  city_guard    A security guard: black cap, sky-blue shirt with navy pocket
                flaps and epaulettes, navy trousers, a belt with a torch
  city_nurse    A nurse: blue scrubs with a V neck, a stethoscope, a dark
                ponytail, white shoes; her forearms bare
  city_police   A police officer: navy uniform, a brass badge, a radio on the
                shoulder, a duty belt with holster and cuffs
  city_worker   A building worker: orange hard hat, orange high-visibility
                vest with reflective bands over a khaki shirt, jeans, boots
  city_office   An office worker: white shirt, a red tie pulled loose, dark
                slacks, a lanyard

Each is drawn from its own skeleton, not dyed from another family: a hip,
a leaning spine, a head, two arms and two legs (their feet placed, the knees
found), posed for every frame of every action and dressed part by part in
its trade's clothes, which are painted in the limbs' own coordinates so
pockets, bands and stains stay where they are as the body moves. Hunched
and heavy like the first route's zombies, the same green skin, yellow eye
and red mouth, the same dark outline, the claw's slash shared with them.
Deterministic; standard library only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_zombie_attack import load, slash_mask  # noqa: E402
from make_sprites import Image  # noqa: E402
from make_zombies import ACTIONS, FRAME  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GROUND = 66                     # The row their soles rest on, as the first route's
OUTLINE = (0x25, 0x20, 0x18, 255)


def c(value: int) -> tuple:
    return (value >> 16) & 255, (value >> 8) & 255, value & 255, 255


def ramp(*values: int) -> list:
    return [c(v) for v in values]


SKIN = ramp(0x4a5240, 0x6f7a5c, 0x9aa37e)
EYE = c(0xfff1a0)
MOUTH = c(0x902004)
BLOOD = c(0x6b333a)
BLACK = ramp(0x1a1a1c, 0x2c2c2c, 0x424242)
BELT = ramp(0x1a1a1c, 0x2c2c2c, 0x505050)
STEEL = c(0xa7a8a8)
BRASS = c(0xd7ab57)

# Bones, in px.
THIGH, SHIN, TORSO, UPPER, FORE = 12.0, 11.5, 16.5, 10.0, 9.0
HIP_Y = GROUND - 4 - 21.6       # Standing, knees a little bent
HIP_X = 22.0


class Canvas:
    def __init__(self) -> None:
        self.px = [[(0, 0, 0, 0)] * FRAME for _ in range(FRAME)]

    def set(self, x: int, y: int, color: tuple) -> None:
        if 0 <= x < FRAME and 0 <= y < FRAME:
            self.px[y][x] = color

    def get(self, x: int, y: int) -> tuple:
        return self.px[y][x] if 0 <= x < FRAME and 0 <= y < FRAME else (0, 0, 0, 0)

    def limb(self, p0, p1, r0: float, r1: float, paint, flip: bool = False) -> None:
        """A tapered limb from p0 to p1. paint(t, s, tone) gives a pixel's
        colour: t 0..1 along it, s -1 (its back) .. +1 (its front, the way
        she faces), tone 0 shade, 1 base, 2 lit (the light is up and behind)."""
        (x0, y0), (x1, y1) = p0, p1
        vx, vy = x1 - x0, y1 - y0
        length2 = vx * vx + vy * vy or 1e-6
        length = math.sqrt(length2)
        reach = max(r0, r1) + 2
        cells = []
        for y in range(int(min(y0, y1) - reach), int(max(y0, y1) + reach) + 1):
            for x in range(int(min(x0, x1) - reach), int(max(x0, x1) + reach) + 1):
                t = max(0.0, min(1.0, ((x - x0) * vx + (y - y0) * vy) / length2))
                nx, ny = x - (x0 + vx * t), y - (y0 + vy * t)
                d = math.hypot(nx, ny)
                r = r0 + (r1 - r0) * t
                if d > r + 1.0:
                    continue
                if d > r:
                    cells.append((x, y, None))
                    continue
                s = (vx * (y - y0) - vy * (x - x0)) / (length * max(r, .5))
                s = max(-1.0, min(1.0, -s if flip else s))
                light = (nx * -.55 + ny * -.83) / max(r, .5)
                tone = 2 if light > .28 else 0 if light < -.38 else 1
                cells.append((x, y, paint(t, s, tone)))
        for x, y, color in cells:           # Its outline first, over what is behind it
            if color is None and self.get(x, y) != OUTLINE:
                self.set(x, y, OUTLINE)
        for x, y, color in cells:
            if color is not None:
                self.set(x, y, color)

    def oval(self, center, rx: float, ry: float, angle: float, paint) -> None:
        """An oval turned by angle (radians, clockwise on screen). paint(lx,
        ly, tone): lx toward its front, ly down, in its own px."""
        cx, cy = center
        ca, sa = math.cos(angle), math.sin(angle)
        reach = int(max(rx, ry)) + 3
        cells = []
        for y in range(int(cy) - reach, int(cy) + reach + 1):
            for x in range(int(cx) - reach, int(cx) + reach + 1):
                dx, dy = x - cx, y - cy
                lx, ly = dx * ca + dy * sa, -dx * sa + dy * ca
                d = (lx / rx) ** 2 + (ly / ry) ** 2
                if d > ((rx + 1) / rx) ** 2:
                    continue
                if d > 1.0:
                    cells.append((x, y, None))
                    continue
                light = (dx * -.55 + dy * -.83) / max(rx, ry)
                tone = 2 if light > .3 else 0 if light < -.4 else 1
                cells.append((x, y, paint(lx, ly, tone)))
        for x, y, color in cells:
            if color is None and self.get(x, y) != OUTLINE:
                self.set(x, y, OUTLINE)
        for x, y, color in cells:
            if color is not None:
                self.set(x, y, color)


def knee(hip, ankle, forward: float = 1.0):
    """Where the knee is for a hip and an ankle (two bones of THIGH, SHIN)."""
    dx, dy = ankle[0] - hip[0], ankle[1] - hip[1]
    d = min(THIGH + SHIN - .01, max(1.0, math.hypot(dx, dy)))
    a = (THIGH * THIGH - SHIN * SHIN + d * d) / (2 * d)
    h = math.sqrt(max(0.0, THIGH * THIGH - a * a))
    span = math.hypot(dx, dy) or 1.0
    ux, uy = dx / span, dy / span
    # Off the hip-ankle line toward her front: (uy, -ux) is that line turned forward.
    return hip[0] + ux * a + forward * h * uy, hip[1] + uy * a - forward * h * ux


def polar(origin, angle_deg: float, length: float):
    """A point length away from origin: 0 degrees straight down, 90 forward."""
    a = math.radians(angle_deg)
    return origin[0] + math.sin(a) * length, origin[1] + math.cos(a) * length


# ---- Poses --------------------------------------------------------------------

def pose(action: str, i: int) -> dict:
    """hip (dx, dy from standing), lean and head (degrees forward), each foot
    (x from the hip, lift off the ground), each arm (shoulder and elbow
    angles: 0 down, 90 forward), near first."""
    p = {'hip': (0.0, 0.0), 'lean': 24.0, 'head': 16.0, 'feet': [(5.0, 0.0), (-6.0, 0.0)],
         'arms': [(40.0, 34.0), (-8.0, 14.0)], 'flat': False}
    if action == 'idle':
        sway = (0.0, 1.0, 0.0, -1.0)[i]
        p['lean'] = 23.0 + sway
        p['hip'] = (0.0, (0, 0, 1, 1)[i])
        p['arms'] = [(36.0 + 3 * sway, 34.0), (-8.0 - 2 * sway, 14.0)]
    elif action in ('walk', 'run'):
        phase = math.tau * i / 8
        run = action == 'run'
        stride, lift = (12.0, 6.0) if run else (8.0, 3.5)
        p['feet'] = [(1.0 + stride * math.cos(phase), max(0.0, lift * math.sin(phase))),
                     (-1.0 - stride * math.cos(phase), max(0.0, -lift * math.sin(phase)))]
        p['hip'] = (1.0 if run else 0.0, (1.6 if run else .8) * abs(math.cos(phase)) - (1.0 if run else 0.0))
        p['lean'] = (33.0 if run else 24.0) + 2 * math.sin(phase * 2)
        p['head'] = 14.0 if run else 12.0
        swing = (26.0 if run else 6.0) * math.sin(phase)
        p['arms'] = [(60.0 if run else 42.0) - swing, 34.0 + (10 if run else 0)], \
                    [(0.0 if run else -8.0) + swing, 16.0]
        p['arms'] = [tuple(a) for a in p['arms']]
    elif action == 'attack':                    # Wind up, strike, follow through, recover
        lean = (16.0, 12.0, 38.0, 34.0, 28.0, 24.0)[i]
        near = ((140.0, -30.0), (176.0, -40.0), (84.0, 6.0), (60.0, 10.0), (48.0, 24.0), (40.0, 34.0))[i]
        p['lean'], p['head'] = lean, (6.0, 2.0, 22.0, 20.0, 14.0, 12.0)[i]
        p['hip'] = ((-1.0, 0.0), (-2.0, 0.0), (4.0, 1.0), (3.0, 1.0), (1.0, 0.0), (0.0, 0.0))[i]
        p['feet'] = [((4.0, 0.0), (4.0, 0.0), (8.0, 0.0), (8.0, 0.0), (6.0, 0.0), (4.0, 0.0))[i], (-6.0, 0.0)]
        p['arms'] = [near, (-20.0, 16.0)]       # The other arm back, out of the blow's way
    elif action == 'hurt':
        p['lean'] = (4.0, -5.0, 12.0)[i]
        p['head'] = (-18.0, -10.0, 4.0)[i]
        p['hip'] = ((-2.0, 0.0), (-3.0, 1.0), (-1.0, 0.0))[i]
        p['arms'] = [((104.0, 34.0), (92.0, 40.0), (70.0, 30.0))[i], ((40.0, 50.0), (30.0, 50.0), (16.0, 34.0))[i]]
    elif action == 'caught':                    # Held by a leg: wrenching at it
        p['lean'] = (16.0, 27.0, 18.0, 30.0)[i]
        p['head'] = (-6.0, 16.0, 0.0, 20.0)[i]
        p['feet'] = [(5.0, 0.0), ((-4.0, 0.0), (-7.0, 2.0), (-5.0, 0.0), (-8.0, 3.0))[i]]
        p['arms'] = [((84.0, 30.0), (122.0, 14.0), (70.0, 40.0), (112.0, 20.0))[i],
                     ((60.0, 30.0), (20.0, 30.0), (74.0, 24.0), (30.0, 40.0))[i]]
    elif action == 'death':                     # Hit, staggering, to its knees, onto its face
        lean = (2.0, -6.0, 24.0, 44.0, 62.0, 80.0, 90.0, 92.0)[i]
        drop = (0.0, 1.0, 6.0, 12.0, 16.0, 18.0, 18.6, 19.0)[i]
        p['lean'], p['head'] = lean, (-16.0, -20.0, 10.0, 24.0, 30.0, 20.0, 8.0, 4.0)[i]
        p['hip'] = ((-2.0, -3.0, -2.0, 0.0, 0.0, -2.0, -3.0, -4.0)[i], drop)
        feet = [((5.0, 0.0), (-6.0, 0.0)), ((4.0, 0.0), (-7.0, 0.0)), ((6.0, 0.0), (-6.0, 0.0)),
                ((7.0, 0.0), (-9.0, 0.0)), ((4.0, 0.0), (-12.0, 0.0)), ((-10.0, 0.0), (-15.0, 0.0)),
                ((-16.0, 0.0), (-18.0, 0.0)), ((-18.0, 0.0), (-19.0, 0.0))][i]
        p['feet'] = list(feet)
        # Lying, the arms are flat on the road ahead of it (the angles are
        # from the body's own lean: half of it is added to them).
        p['arms'] = [((100.0, 30.0), (90.0, 44.0), (60.0, 20.0), (40.0, 30.0), (30.0, 40.0), (44.0, 10.0),
                      (42.0, 2.0), (42.0, 0.0))[i],
                     ((40.0, 40.0), (30.0, 46.0), (20.0, 30.0), (16.0, 40.0), (20.0, 40.0), (36.0, 14.0),
                      (38.0, 6.0), (40.0, 2.0))[i]]
        p['flat'] = i >= 5
        p['pool'] = (0, 0, 0, 0, 0, 0, 5, 12)[i]
    return p


# ---- The trades ---------------------------------------------------------------

def stain(t: float, s: float, seed: int) -> bool:
    """Blood and dirt fixed on a piece of clothing, in its own coordinates."""
    k = int(t * 9) * 7 + int((s + 1) * 4) * 13 + seed
    return (k * 2654435761 >> 7) % 23 == 0


class Trade:
    """What a townsperson wears. Each method paints one part."""
    shirt = ramp(0x8e8266, 0xb8ab8a, 0xd6c8a7)
    legs = ramp(0x2c2c2c, 0x424242, 0x505050)
    boots = BLACK
    hair = ramp(0x2c2018, 0x463322, 0x684833)
    sleeves = 1.0                      # Share of the arm the sleeve covers
    seed = 1

    def torso(self, t, s, tone):
        color = self.shirt[tone]
        if t < .1:
            return BELT[tone] if not (.2 < s < .5) else STEEL
        if stain(t, s, self.seed) and s > -.2:
            return BLOOD
        return color

    @staticmethod
    def worn(color_ramp: list, t: float, s: float, tone: int, seed: int) -> tuple:
        """Cloth lived in and died in: flecks of its shade through it."""
        k = int(t * 13) * 31 + int((s + 1) * 6) * 17 + seed * 7
        if (k * 2654435761 >> 5) % 7 == 0:
            return color_ramp[max(0, tone - 1)]
        return color_ramp[tone]

    def arm(self, t, s, tone, upper: bool, far: bool):
        share = t * .5 + (0 if upper else .5)
        if share > self.sleeves:
            return SKIN[max(0, tone - (1 if far else 0))]
        return self.sleeve(share, s, max(0, tone - (1 if far else 0)))

    def sleeve(self, share, s, tone):
        return self.shirt[tone]

    def leg(self, t, s, tone, upper: bool, far: bool):
        tone = max(0, tone - (1 if far else 0))
        if stain(t, s, self.seed + (3 if upper else 5)) and not far:
            return BLOOD if upper else self.legs[0]
        return self.worn(self.legs, t, s, tone, self.seed + 9)

    def head(self, lx, ly, tone):
        """Face, the same on all of them; then hair (hat() comes after)."""
        if ly < -5.4 - max(0.0, lx) * .5 or (lx < -6.2 and ly < 0.5):
            return self.hair[tone]                                   # Cropped short: no hood of hair
        if 1.6 <= lx <= 5.2 and -3.2 <= ly <= -0.6:                  # The eye, sunk in its socket
            if 3.0 <= lx <= 4.6 and -2.4 <= ly <= -1.2:
                return EYE
            return SKIN[0] if ly < -0.8 else OUTLINE
        if 0.5 <= lx <= 1.6 and -4.0 <= ly <= -3.0:
            return SKIN[0]                                           # The brow
        if lx >= 1.6 and 2.2 <= ly <= 5.0:                           # The mouth, hanging open: teeth, blood
            if ly < 3.0:
                return c(0xd6c8a7) if int(lx) % 2 else OUTLINE
            return MOUTH if ly < 4.4 else OUTLINE
        if lx >= 2.0 and ly > 5.0:
            return SKIN[0]                                           # The jaw
        if -2.5 <= lx <= -1.0 and -1.0 <= ly <= 1.6:
            return SKIN[0]                                           # The ear
        if (int(lx * 3) * 7 + int(ly * 3) * 5) % 19 == 0:
            return SKIN[0]                                           # Rot
        return SKIN[tone]

    def extras(self, cv: Canvas, rig: dict) -> None:
        """What hangs on the body: drawn after it."""


class Guard(Trade):
    shirt = ramp(0x3f6298, 0x5c80b0, 0x7c9cc6)      # Sky blue, gone grey with dust
    legs = ramp(0x16203a, 0x1f3256, 0x2e4a7a)
    seed = 11

    def torso(self, t, s, tone):
        if t < .1:
            return BELT[tone] if not (.25 < s < .5) else STEEL
        if .56 <= t <= .66 and .1 <= s <= .85:
            return self.legs[1] if t > .58 else self.legs[0]        # The navy pocket flap
        if .44 <= t < .56 and (abs(s - .1) < .06 or abs(s - .85) < .06):
            return self.shirt[0]                                    # The pocket's seams under it
        if t > .9 and -.5 < s < .4:
            return self.legs[1] if not (-.1 < s < .1) else BRASS    # Epaulette, its bars
        if abs(t - .76) < .04 and .45 < s < .7:
            return BRASS                                            # The company's emblem
        if stain(t, s, self.seed) and s > 0:
            return BLOOD
        return self.worn(self.shirt, t, s, tone, self.seed)

    def sleeve(self, share, s, tone):
        if abs(s) < .28 and share < .9:
            return self.legs[1]                                     # The navy stripe down the arm
        return self.shirt[tone] if share < .92 else self.shirt[0]

    def head(self, lx, ly, tone):
        if ly < -2.2:                                               # A black cap, its crown
            return BLACK[tone]
        return super().head(lx, ly, tone)

    def extras(self, cv, rig):
        hx, hy = rig['head']
        a = rig['head_angle']
        for k in range(1, 8):                                       # The cap's brim, out over the eyes
            x = hx + math.cos(a) * (3.5 + k) + math.sin(a) * 2.6
            y = hy + math.sin(a) * (3.5 + k) - math.cos(a) * 2.6
            cv.set(round(x), round(y), BLACK[2] if k < 6 else BLACK[1])
            cv.set(round(x), round(y) + 1, OUTLINE)
        tx, ty = rig['belt_back']                                   # A torch on the belt
        for k in range(5):
            cv.set(round(tx), round(ty) + k, BLACK[2] if k else STEEL)


class Nurse(Trade):
    shirt = ramp(0x263e68, 0x3a5c94, 0x5578b0)      # Blue scrubs, top and trousers
    legs = ramp(0x1f3256, 0x2e4a7a, 0x4a74b5)
    boots = ramp(0x8e8266, 0xb8ab8a, 0xd6c8a7)
    hair = ramp(0x1a1614, 0x2c2420, 0x463322)
    sleeves = .42
    seed = 23

    def torso(self, t, s, tone):
        if t > .8 and s > .25 + (1 - t) * 1.2:
            return SKIN[tone]                                       # The V of her neck
        if .28 <= t <= .44 and .3 <= s <= .8:
            return self.shirt[0] if t > .42 or abs(s - .3) < .05 else self.shirt[tone]   # A pocket
        if stain(t, s, self.seed) and s > -.3:
            return BLOOD
        return self.worn(self.shirt, t, s, tone, self.seed)

    def head(self, lx, ly, tone):
        if ly < -4.0 - max(0.0, lx) * .5 or lx < -5.2 or (lx < -1.5 and ly < -2.5):
            return self.hair[tone]
        return super().head(lx, ly, tone)

    def extras(self, cv, rig):
        hx, hy = rig['head']
        a = rig['head_angle']
        bx, by = hx - math.cos(a) * 8.0, hy - math.sin(a) * 8.0     # The back of her head
        for k in range(11):                                         # Her ponytail, hanging from its band
            x = bx - 1.5 - k * .2 + rig['sway'] * (k / 10)
            y = by - 1 + k
            wide = 2 if 1 < k < 9 else 1
            for d in range(wide + 1):
                cv.set(round(x) - d, round(y), self.hair[2] if d == 0 and k % 3 == 0 else self.hair[1] if d < wide
                       else self.hair[0])
            cv.set(round(x) - wide - 1, round(y), OUTLINE)
            cv.set(round(x) + 1, round(y), OUTLINE if k > 2 else cv.get(round(x) + 1, round(y)))
        cv.set(round(bx) - 1, round(by) - 1, c(0xd6c8a7))           # The band
        (px, py), (qx, qy) = rig['hip'], rig['neck']                # Her stethoscope, down her front
        fx, fy = math.cos(rig['lean']), math.sin(rig['lean'])
        for k in range(8):
            t = .95 - k * .055
            x = px + (qx - px) * t + fx * (5.2 - k * .15)
            y = py + (qy - py) * t + fy * (5.2 - k * .15)
            cv.set(round(x), round(y), BLACK[0])
        cv.set(round(x), round(y) + 1, STEEL)
        cv.set(round(x) + 1, round(y) + 1, STEEL)
        cv.set(round(x) + 1, round(y) + 2, STEEL)


class Police(Trade):
    shirt = ramp(0x121a30, 0x1f3256, 0x2e4a7a)      # Navy
    legs = ramp(0x121a30, 0x1a2848, 0x2e4a7a)
    hair = ramp(0x1a1614, 0x2c2420, 0x463322)
    seed = 37

    def torso(self, t, s, tone):
        if t < .13:                                                 # The duty belt: buckle, pouches
            return STEEL if .3 < s < .5 else BLACK[2] if int((s + 1) * 4) % 2 else BLACK[1]
        if abs(t - .72) < .05 and .4 < s < .68:
            return BRASS                                            # The badge
        if .5 <= t <= .56 and .05 <= s <= .9:
            return self.shirt[0]                                    # Pocket flaps' shadow
        if t > .92 and -.5 < s < .3:
            return self.shirt[2]                                    # Shoulder strap
        if abs(s - .15) < .05 and t > .15:
            return self.shirt[0] if int(t * 12) % 2 else BLACK[2]   # The button line
        if stain(t, s, self.seed) and s > 0:
            return BLOOD
        return self.worn(self.shirt, t, s, tone, self.seed)

    def sleeve(self, share, s, tone):
        if .16 < share < .3 and s > -.4:
            return BRASS if .2 < share < .26 and abs(s) < .3 else self.shirt[2]   # The arm patch
        return self.shirt[tone]

    def extras(self, cv, rig):
        sx, sy = rig['shoulder']
        for dx, dy, col in ((1, -1, BLACK[1]), (2, -1, BLACK[1]), (1, 0, BLACK[2]), (2, 0, BLACK[1]),
                            (1, 1, BLACK[1]), (2, 1, BLACK[1]), (3, 2, BLACK[2]), (3, 4, BLACK[2])):
            cv.set(round(sx) + dx + 2, round(sy) + dy, col)         # The radio's microphone, its cord
        bx, by = rig['belt_back']
        for k in range(6):                                          # Holster on the hip
            cv.set(round(bx) + 1, round(by) + k, BLACK[2])
            cv.set(round(bx) + 2, round(by) + k, BLACK[1])
        fx, fy = rig['belt_front']                                  # Handcuffs
        cv.set(round(fx), round(fy) + 2, STEEL)
        cv.set(round(fx) - 1, round(fy) + 3, STEEL)
        cv.set(round(fx) + 1, round(fy) + 3, STEEL)


class Worker(Trade):
    shirt = ramp(0x684833, 0x8f7859, 0xb4996d)      # A khaki work shirt under the vest
    vest = ramp(0x89411f, 0xb45c32, 0xd0783c)
    legs = ramp(0x2a2e38, 0x3c4250, 0x5a6272)       # Jeans
    boots = ramp(0x463322, 0x684833, 0x876439)
    hair = ramp(0x2c2c2c, 0x424242, 0x505050)
    seed = 53

    def torso(self, t, s, tone):
        if t < .1:
            return BELT[tone]
        if t < .2:
            return self.shirt[tone]                                 # The shirt's tail under the vest
        if abs(t - .36) < .045 or abs(t - .62) < .045:
            return STEEL if tone else c(0x868689)                   # Reflective bands round it
        if abs(s - .5) < .12 or abs(s + .45) < .12:
            return STEEL if tone else c(0x868689)                   # ...and over the shoulders
        if s > .86:
            return self.shirt[0]                                    # Open down the front
        if stain(t, s, self.seed) and s > -.2:
            return BLOOD
        return self.worn(self.vest, t, s, tone, self.seed)

    def head(self, lx, ly, tone):
        if ly < -1.8:                                               # The hard hat's shell
            return self.vest[2] if ly < -5 and lx < 1 else self.vest[tone]
        if lx < -3.8 and ly < 2:
            return self.hair[tone]
        if lx > 0 and ly > 4.4:
            return self.hair[1]                                     # His beard
        return super().head(lx, ly, tone)

    def extras(self, cv, rig):
        hx, hy = rig['head']
        a = rig['head_angle']
        for k in range(-8, 9):                                      # The hat's rim, all round
            x = hx + math.cos(a) * k + math.sin(a) * 2.0
            y = hy + math.sin(a) * k - math.cos(a) * 2.0
            cv.set(round(x), round(y), self.vest[2] if k < 5 else self.vest[1])
            cv.set(round(x), round(y) + 1, OUTLINE if abs(k) > 6 else self.vest[0])


class Office(Trade):
    shirt = ramp(0x8e8266, 0xb8ab8a, 0xd6c8a7)      # A white shirt, not white any more
    legs = ramp(0x1a1a1c, 0x2c2c2c, 0x424242)
    hair = ramp(0x424242, 0x505050, 0x868689)       # Greying
    seed = 71

    def torso(self, t, s, tone):
        if t < .1:
            return BELT[tone] if not (.3 < s < .5) else BRASS
        if t > .35 and abs(s - .6 - (1 - t) * .25) < .14:
            return MOUTH if int(t * 14) % 3 else BLOOD              # A red tie, pulled loose
        if t > .86 and s > .1:
            return self.shirt[2]                                    # The collar, open
        if abs(s + .1 - (1 - t) * .5) < .05 and .3 < t < .9:
            return c(0x2e4a7a)                                      # A lanyard
        if .26 < t < .34 and -.3 < s < -.02:
            return c(0xd6c8a7) if t > .29 else c(0x2e4a7a)          # ...and its card
        if stain(t, s, self.seed):
            return BLOOD
        return self.worn(self.shirt, t, s, tone, self.seed)

    def sleeve(self, share, s, tone):
        return self.shirt[tone] if share < .62 else SKIN[tone]      # Rolled to the elbow

    def head(self, lx, ly, tone):
        if lx < -5.6 and -3.0 < ly < 1.5:
            return self.hair[tone]                                  # Bald on top, a fringe round the back
        return super().head(lx, ly, tone)

    def extras(self, cv, rig):
        hx, hy = rig['head']
        a = rig['head_angle']
        for k in (1, 2, 3, 4, 5):                                   # His glasses, one lens cracked
            x = hx + math.cos(a) * k + math.sin(a) * 2.8
            y = hy + math.sin(a) * k - math.cos(a) * 2.8
            cv.set(round(x), round(y), BLACK[0])
        for k in range(-5, 1):
            cv.set(round(hx + math.cos(a) * k + math.sin(a) * 2.4), round(hy + math.sin(a) * k - math.cos(a) * 2.4),
                   BLACK[0])


FAMILIES = {'city_guard': Guard(), 'city_nurse': Nurse(), 'city_police': Police(), 'city_worker': Worker(),
            'city_office': Office()}


# ---- Drawing a frame -------------------------------------------------------------

def draw(trade: Trade, action: str, i: int) -> Canvas:
    p = pose(action, i)
    cv = Canvas()
    hip = (HIP_X + p['hip'][0], HIP_Y + p['hip'][1])
    lean = math.radians(p['lean'])
    neck = (hip[0] + math.sin(lean) * TORSO, hip[1] - math.cos(lean) * TORSO)
    head_angle = math.radians(p['lean'] * .45 + p['head'])
    head = (neck[0] + math.sin(head_angle) * 7.0 + 2.6 * math.cos(head_angle),
            neck[1] - math.cos(head_angle) * 7.0 + 2.6 * math.sin(head_angle))
    sole = GROUND - 4.0
    ankles = []
    for k, (fx, lift) in enumerate(p['feet']):
        y = sole - lift + (2.5 if p['flat'] else 0.0)
        ankles.append((hip[0] + fx + (0 if k == 0 else -1), min(y, GROUND - 1.5)))
    shoulder = (neck[0] - math.sin(lean) * 3.0 - 1.0 * math.cos(lean), neck[1] + math.cos(lean) * 3.0)

    def arm(index: int, far: bool) -> None:
        a1, a2 = p['arms'][index]
        base = math.degrees(lean) * .5
        root = (shoulder[0] + (-1.5 if far else 1.0), shoulder[1] + (0.5 if far else 0.0))
        elbow = polar(root, a1 + base, UPPER)
        wrist = polar(elbow, a1 + a2 + base, FORE)
        tip = polar(wrist, a1 + a2 + base, 3.2)
        cv.limb(root, elbow, 3.9, 3.3, lambda t, s, tone: trade.arm(t, s, tone, True, far), flip=True)
        cv.limb(elbow, wrist, 3.3, 2.7, lambda t, s, tone: trade.arm(t, s, tone, False, far), flip=True)
        cv.limb(wrist, tip, 2.9, 2.1, lambda t, s, tone: SKIN[max(0, tone - (1 if far else 0))], flip=True)
        claw = polar(tip, a1 + a2 + base, 2.4)                     # Claws, bloody
        cv.set(round(claw[0]), round(claw[1]), MOUTH)
        cv.set(round(claw[0]), round(claw[1]) - 1 if abs(tip[0] - wrist[0]) > abs(tip[1] - wrist[1]) else round(claw[1]),
               MOUTH)
        cv.set(round(claw[0]) - (0 if abs(tip[0] - wrist[0]) > abs(tip[1] - wrist[1]) else 2), round(claw[1]) + (
            2 if abs(tip[0] - wrist[0]) > abs(tip[1] - wrist[1]) else 0), MOUTH)

    def leg(index: int, far: bool) -> None:
        ankle = ankles[index]
        root = (hip[0] + (-1.2 if far else 1.0), hip[1] + 1.0)
        joint = knee(root, ankle)
        cv.limb(root, joint, 4.8, 3.8, lambda t, s, tone: trade.leg(t, s, tone, True, far), flip=True)
        cv.limb(joint, ankle, 3.7, 3.1, lambda t, s, tone: trade.leg(t, s, tone, False, far), flip=True)
        toe = (ankle[0] + (4.6 if not p['flat'] else -1.0), ankle[1] + (1.4 if not p['flat'] else 1.0))
        heel = (ankle[0] - 1.4, ankle[1] + 1.4 if not p['flat'] else ankle[1] + 1.0)
        cv.limb(heel, toe, 2.7, 2.4, lambda t, s, tone: trade.boots[max(0, tone - (1 if far else 0))])

    arm(1, True)
    leg(1, True)
    leg(0, False)
    cv.limb((hip[0], hip[1] + 0.5), neck, 6.4, 8.4, trade.torso)
    cv.limb(neck, (neck[0] + math.sin(head_angle) * 2, neck[1] - math.cos(head_angle) * 2), 2.6, 2.6,
            lambda t, s, tone: SKIN[max(0, tone - 1)])
    cv.oval(head, 8.4, 8.6, head_angle, trade.head)
    cross = (math.cos(lean), math.sin(lean))
    rig = {'head': head, 'head_angle': head_angle, 'neck': neck, 'hip': hip, 'lean': lean, 'shoulder': shoulder,
           'belt_back': (hip[0] - cross[0] * 6.5, hip[1] - cross[1] * 6.5),
           'belt_front': (hip[0] + cross[0] * 5.5, hip[1] + cross[1] * 5.5),
           'sway': (-1 if action in ('walk', 'run') and i % 4 < 2 else 0)}
    trade.extras(cv, rig)
    arm(0, False)
    for k in range(p.get('pool', 0)):                               # Blood spreading under the head
        cv.set(min(FRAME - 1, round(head[0]) + 4 + k), GROUND, MOUTH)
    return cv


def sheet(trade: Trade, action: str, riot: Image) -> Image:
    count = ACTIONS[action]
    img = Image(FRAME * count, FRAME)
    for i in range(count):
        cv = draw(trade, action, i)
        for y in range(FRAME):
            for x in range(FRAME):
                img.set(i * FRAME + x, y, cv.px[y][x])
        if action == 'attack' and i in (2, 3):                      # The claw's slash, the first route's
            for (x, y) in slash_mask(riot, i):
                img.set(i * FRAME + x, y, riot.get(i * FRAME + x, y))
    return img


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'assets'
    riot = load(ROOT / 'assets/sprites/zombies/riot/attack.png')
    for identifier, trade in FAMILIES.items():
        for action in ACTIONS:
            path = assets / 'sprites/zombies' / identifier / f'{action}.png'
            path.parent.mkdir(parents=True, exist_ok=True)
            sheet(trade, action, riot).save(path)
        print(f'make_city_zombies: sprites/zombies/{identifier}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
