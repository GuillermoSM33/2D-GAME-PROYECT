#!/usr/bin/env python3
"""Make the sheets of setting a charge of dynamite (E), for the cowgirl and
the SWAT.

Usage: tools/make_plant.py

Writes (6 frames of 81 x 80 each, the shoot template, like the drink):
  assets/sprites/characters/cowgirl/plant.png
  assets/sprites/characters/swat/plant.png
The near hand takes a stick of dynamite from the belt; down on one knee (the SWAT
reaches out low) it sets it on the ground with the fuse spitting sparks and comes
back empty (the charge
itself is drawn on the road or the wall from then on). The game plays them
over PLANT_TIME (0.45 s). Bodies and arms come from tools/make_care.py's and
tools/make_swat.py's own helpers. Uses only the standard library.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_care import GLOVE, bent_arm, hand  # noqa: E402
from make_melee import AIM, HOLSTER, LOW, SHOULDER, body_without_arm, frame, sleeve  # noqa: E402
from make_powers import INK, load  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402
import make_swat  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 81, 80
FRAMES = 6
STICK_COLORS = {'r': rgb(0xc8402c), 'R': rgb(0xe8684a), 'd': rgb(0x86281c), 'p': rgb(0xe8dcc0),
                'f': rgb(0x4a3a2a)}
# A stick held upright under the hand: fuse, paper band, red body lit on its left.
STICK = ['.f', '.f', 'Rr', 'pp', 'Rr', 'Rr', 'Rd', 'pp', 'Rd']
SPARKS = [rgb(0xfff4b0), rgb(0xffc040), rgb(0xff7a20)]


def stick(at: tuple, lit: int) -> dict:
    """The stick's top-left at `at`, outlined; lit > 0 adds that many sparks
    round the fuse's tip."""
    out = {}
    for y, row in enumerate(STICK):
        for x, ch in enumerate(row):
            if ch != '.':
                out[(at[0] + x, at[1] + y)] = STICK_COLORS[ch]
    edged = dict(out)
    for (x, y), c in out.items():
        if c == STICK_COLORS['f']:
            continue                                     # The fuse is a thin line
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in out:
                edged[(x + dx, y + dy)] = INK
    tip = (at[0] + 1, at[1] - 1)
    for i, (dx, dy) in enumerate(((0, 0), (1, -1), (-1, -1), (2, 0), (0, -2))[:lit]):
        edged[(tip[0] + dx, tip[1] + dy)] = SPARKS[min(i, 2)]
    return edged


# She goes down on one knee to set it on the ground, her arm its normal length. Per
# frame: her near hand (frame px), the stick's top if it is out of her hand's way (None:
# it is gone), sparks and how far down she is. Standing she has her own legs.
COWGIRL = [((46, 51), (46, 48), 0, 0), ((48, 55), (48, 51), 0, 4), ((51, 57), (51, 54), 1, 8),
           ((52, 59), (52, 59), 3, 10), ((51, 56), (52, 59), 3, 8), ((47, 53), None, 0, 3)]
WAIST_DOWN = 51                   # Rows from here on are her legs, drawn again as they bend
HIP_NEAR, HIP_FAR = (38, 50), (32, 50)
FOOT_NEAR, FOOT_FAR = (43, 66), (26, 66)
THIGH, SHIN = 8.5, 9.0
SHOULDER_AT = (40, 38)            # Where her near arm starts on the standing frame
ARM_BONE = 7.5
GROUND_ROW = 67
TROUSER = [rgb(0x5e5650), rgb(0x48423e), rgb(0x423c38)]
FAR_TROUSER = [rgb(0x423c38), rgb(0x322e2c), rgb(0x322e2c)]
BOOT = [rgb(0x684833), rgb(0x463322), rgb(0x2c2c2c)]
STRAP_AT, STRAP_HALF = 0.72, 0.9  # Her thigh strap: how far down the thigh, and half its width in px
SASH_COLORS = {(0x64, 0x18, 0x2a), (0x8a, 0x24, 0x38), (0x46, 0x10, 0x1e)}
# The SWAT's, in his walk-frame points (make_swat's at() shifts them).
SWAT = [((24, 37), True, 0), ((27, 38), True, 0), ((30, 39), True, 1),
        ((31, 41), True, 3), ((29, 37), False, 0), ((26, 35), False, 0)]


def set_down(img: Image, f: int, px: dict) -> None:
    for (x, y), c in px.items():
        if 0 <= x < W and 0 <= y < H:
            img.set(f * W + x, y, c)


def knee(hip: tuple, foot: tuple) -> tuple:
    """Where the knee is, always to her front: the leg never stretches."""
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = max(math.hypot(dx, dy), 1.0)
    if d >= THIGH + SHIN:
        return (hip[0] + dx * THIGH / d, hip[1] + dy * THIGH / d)
    along = (THIGH * THIGH - SHIN * SHIN + d * d) / (2.0 * d)
    out = math.sqrt(max(0.0, THIGH * THIGH - along * along))
    ux, uy = dx / d, dy / d
    return (hip[0] + ux * along + uy * out, min(hip[1] + uy * along - ux * out, GROUND_ROW - 1))


def capsule(a: tuple, b: tuple, r0: float, r1: float, paint) -> dict:
    n = max(int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2), 1)
    px = {}
    for t in range(n + 1):
        k = t / n
        cx, cy, r = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, r0 + (r1 - r0) * k
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    px[(x, y)] = paint(x, y, (x + 0.5 - cx) / max(r, 0.5))
    return px


def leg(hip: tuple, foot: tuple, tones: list, toe: int, strap: bool = False) -> dict:
    """A trouser leg bent at the knee, the striped cloth of her art, into its boot."""
    kn = knee(hip, foot)
    cloth = lambda x, y, side: tones[2] if side > 0.5 else tones[1 if x % 3 == 0 else 0]  # noqa: E731
    leather = lambda x, y, side: BOOT[1] if side > 0.3 else BOOT[0]  # noqa: E731
    ankle = (kn[0] + (foot[0] - kn[0]) * 0.6, kn[1] + (foot[1] - kn[1]) * 0.6)
    px = capsule(hip, kn, 2.5, 1.9, cloth)
    px.update(capsule(kn, ankle, 1.9, 1.5, cloth))
    if strap:                                            # Round her thigh, a thin band across it: not along it
        tx, ty = kn[0] - hip[0], kn[1] - hip[1]
        length = max(math.hypot(tx, ty), 1.0)
        for (x, y) in capsule(hip, kn, 2.5, 1.9, cloth):
            along = ((x + 0.5 - hip[0]) * tx + (y + 0.5 - hip[1]) * ty) / length
            if abs(along - length * STRAP_AT) <= STRAP_HALF:
                px[(x, y)] = BOOT[1]
    px.update(capsule(ankle, foot, 1.7, 1.5, leather))
    for x in range(min(foot[0], foot[0] + toe), max(foot[0], foot[0] + toe) + 1):  # The foot, flat on the ground
        for y in (foot[1], foot[1] + 1):
            px[(x, y)] = BOOT[0] if y == foot[1] else BOOT[2]
    return px


def edged(px: dict) -> dict:
    out = dict(px)
    for (x, y) in px:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + a, y + b) not in px:
                out[(x + a, y + b)] = INK
    return out


def down_on_a_knee(body: dict, drop: int) -> dict:
    """Her upper half, belt and sash, come down leaning a little forward, on her legs
    drawn bent; a standing frame keeps its own."""
    if drop == 0:
        return dict(body)
    lean = drop // 4
    sash = {p: c for p, c in body.items() if c[:3] in SASH_COLORS}
    near_hip = (HIP_NEAR[0] + lean, HIP_NEAR[1] + drop)
    far_hip = (HIP_FAR[0] + lean, HIP_FAR[1] + drop)
    px = edged(leg(far_hip, FOOT_FAR, FAR_TROUSER, -1))
    px.update(edged(leg(near_hip, FOOT_NEAR, TROUSER, 3, True)))
    for (x, y), c in sorted(body.items(), key=lambda p: p[0][1]):
        if y < WAIST_DOWN:
            px[(x + lean, y + drop)] = c
    px.update({(x + lean, y + drop): c for (x, y), c in sash.items() if y + drop <= GROUND_ROW - 2})
    return {p: c for p, c in px.items() if p[1] <= GROUND_ROW + 1}


def reaching(at: tuple, drop: int) -> dict:
    """Her near arm, of its normal length, the elbow back and down as it reaches."""
    top = (SHOULDER_AT[0] + drop // 4, SHOULDER_AT[1] + drop)
    d = math.hypot(at[0] - top[0], at[1] - top[1])
    out = math.sqrt(max(0.0, ARM_BONE * ARM_BONE - d * d / 4.0))
    ux, uy = (at[0] - top[0]) / max(d, 1.0), (at[1] - top[1]) / max(d, 1.0)
    elbow = (round((top[0] + at[0]) / 2 - uy * out), round((top[1] + at[1]) / 2 + ux * out))
    return bent_arm(top, elbow, at)


def big_hand(at: tuple) -> dict:
    return {(at[0] + i, at[1] + j): GLOVE[j > 0] for i in (-1, 0, 1) for j in (-1, 0, 1)}


def make_cowgirl() -> Image:
    shoot = load(ROOT / 'assets/sprites/characters/cowgirl/shoot.png')
    body = body_without_arm(frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER))
    img = Image(W * FRAMES, H)
    for f, (at, top, lit, drop) in enumerate(COWGIRL):
        px = down_on_a_knee(body, drop)
        if top:
            px.update(stick(top, lit))
        px.update(reaching(at, drop))
        px.update(edged(big_hand(at)))
        set_down(img, f, px)
    return img


def make_swat_sheet() -> Image:
    source = make_swat.load(make_swat.SOURCE)
    make_swat.detail_head(source)
    body = make_swat.without_arm(make_swat.frame(source, 0))
    sx, sy = make_swat.SHOOT_SHIFT

    def at(p: tuple) -> tuple:
        return (p[0] + sx, p[1] + sy)

    sheet = Image(W * FRAMES, H)
    for f, (near, holding, lit) in enumerate(SWAT):
        hx, hy = at(near)
        parts = [
            make_swat.arm(at(make_swat.FAR_SHOULDER), at((27, 38)), near=False, upper=7.5, fore=8.0),
            (body, sx, sy),
        ]
        if holding:
            layer = make_swat.Layer()
            layer.px.update(stick((int(hx), int(hy) - 1), lit))
            parts.append(layer)
        parts.append(make_swat.arm(at(make_swat.NEAR_SHOULDER), (hx, hy), near=True, upper=7.5, fore=8.0))
        make_swat.paste(sheet, make_swat.compose(W, H, parts), f * W, 0)
    return sheet


def main() -> int:
    for who, img in (('cowgirl', make_cowgirl()), ('swat', make_swat_sheet())):
        path = ROOT / f'assets/sprites/characters/{who}/plant.png'
        img.save(path)
        print(f'make_plant: {path.relative_to(ROOT).as_posix()} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
