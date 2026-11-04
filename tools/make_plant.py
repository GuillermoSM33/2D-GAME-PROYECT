#!/usr/bin/env python3
"""Make the sheets of setting a charge of dynamite (E), for the cowgirl and
the SWAT.

Usage: tools/make_plant.py

Writes (6 frames of 81 x 80 each, the shoot template, like the drink):
  assets/sprites/characters/cowgirl/plant.png
  assets/sprites/characters/swat/plant.png
The near hand takes a stick of dynamite from the belt, reaches it out low,
sets it down with the fuse spitting sparks, and comes back empty (the charge
itself is drawn on the road or the wall from then on). The game plays them
over PLANT_TIME (0.45 s). Bodies and arms come from tools/make_care.py's and
tools/make_swat.py's own helpers. Uses only the standard library.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_care import hand  # noqa: E402
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


# Her near hand per frame (frame px), whether the stick is in it, and sparks:
# from the belt, out and down, set down lit, the hand back up empty.
COWGIRL = [((41, 45), True, 0), ((43, 46), True, 0), ((45, 47), True, 1),
           ((46, 48), True, 3), ((44, 44), False, 0), ((42, 41), False, 0)]
# The SWAT's, in his walk-frame points (make_swat's at() shifts them).
SWAT = [((24, 37), True, 0), ((27, 38), True, 0), ((30, 39), True, 1),
        ((31, 41), True, 3), ((29, 37), False, 0), ((26, 35), False, 0)]


def set_down(img: Image, f: int, px: dict) -> None:
    for (x, y), c in px.items():
        if 0 <= x < W and 0 <= y < H:
            img.set(f * W + x, y, c)


def make_cowgirl() -> Image:
    shoot = load(ROOT / 'assets/sprites/characters/cowgirl/shoot.png')
    body = body_without_arm(frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER))
    img = Image(W * FRAMES, H)
    for f, (at, holding, lit) in enumerate(COWGIRL):
        px = dict(body)
        px.update(sleeve(SHOULDER, at))
        if holding:                                      # Gripped about its middle
            px.update(stick((at[0], at[1] - 1), lit))
        px.update(hand(at))
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
