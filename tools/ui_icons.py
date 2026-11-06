#!/usr/bin/env python3
"""The interface's look, all by the same hand: its materials and detailed art.

Everything under sprites/ui and sprites/weapons takes its colors from the
materials below. tools/make_ui.py writes the icons (24 x 24, UiIcon order) to
sprites/ui/icons_hd.png and the guns to sprites/ui/weapons_hd.png. Each is built
from Art layers, so the rules hold by construction: each shape gets a closed
ink outline, the light comes from the top left, and its volume uses a five-tone
ramp. Only details (rivets, stitches, glints) are placed by hand.

Standard library only; deterministic.
"""
from __future__ import annotations

import math

SIZE = 24
INK = (0x1a, 0x12, 0x10, 255)


def rgb(value: int) -> tuple:
    return (value >> 16 & 255, value >> 8 & 255, value & 255, 255)


def ramp(*values: int) -> tuple:
    return tuple(rgb(v) for v in values)


# Light to shade: highlight, lit, base, shade, deep shade.
BRASS = ramp(0xfff0b0, 0xf0d27a, 0xd0a848, 0x9c7a32, 0x6a4e1e)
RED = ramp(0xffb090, 0xf0705a, 0xd8402e, 0x9c2a20, 0x661814)
BONE = ramp(0xfffaea, 0xf0e6cc, 0xcfc4a8, 0xa0947c, 0x6e6452)
IRON = ramp(0xf0f0f6, 0xc8c8d2, 0x9a9aa6, 0x6c6c78, 0x44444e)
WOOD = ramp(0xecb884, 0xc98f58, 0x9a643a, 0x76492a, 0x4e2f1b)
WATER = ramp(0xe8f8ff, 0x9ad6f4, 0x58aee4, 0x2f7cb6, 0x1c4f80)
ICE = ramp(0xffffff, 0xe2f2fb, 0xb8dcf0, 0x84b4d2, 0x5a88a8)
GREEN = ramp(0xe0f8c0, 0xa8e080, 0x7cc45c, 0x4f8f3e, 0x2e5f28)
FIRE = ramp(0xfff2b0, 0xffcf5a, 0xf6962a, 0xd8592a, 0x9c3420)
COPPER = ramp(0xffcfa8, 0xeea06e, 0xcc7440, 0x9a4f2c, 0x66331c)
UNLIT = ramp(0x9c8c76, 0x7e705e, 0x64584a, 0x4e443a, 0x3a322c)
FEATHER = ramp(0x7a7a9c, 0x5a5a7a, 0x40405c, 0x2c2c44, 0x1e1e30)
GUNMETAL = ramp(0xb4bac4, 0x868c98, 0x5c606c, 0x40434c, 0x2a2c32)
OLIVE = ramp(0xc8d48a, 0xa0ac62, 0x7a8644, 0x565e30, 0x34381e)
BLACK = ramp(0x7c808a, 0x565962, 0x3a3c44, 0x28292f, 0x1a1b1f)


def hex_of(color: tuple) -> int:
    return color[0] << 16 | color[1] << 8 | color[2]


# The canvas the masks fall on. Art is designed on one grid and can be drawn at
# a fraction of it (scale), so a small version keeps the same design.
_width, _height, _scale = SIZE, SIZE, 1.0


def canvas(width: int, height: int, scale: float = 1.0) -> None:
    global _width, _height, _scale
    _width, _height, _scale = width, height, scale


def _centers():
    for y in range(_height):
        for x in range(_width):
            yield x, y, (x + .5) / _scale, (y + .5) / _scale


def ellipse(cx: float, cy: float, rx: float, ry: float) -> set:
    return {(x, y) for x, y, px, py in _centers() if ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1}


def rect(x0: int, y0: int, x1: int, y1: int) -> set:
    return {(x, y) for x, y, px, py in _centers() if x0 <= px < x1 + 1 and y0 <= py < y1 + 1}


def poly(points: list) -> set:
    mask = set()
    for x, y, px, py in _centers():
        inside = False
        for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
            if (ay > py) != (by > py) and px < ax + (py - ay) * (bx - ax) / (by - ay):
                inside = not inside
        if inside:
            mask.add((x, y))
    return mask


def stroke(points: list, width: float) -> set:
    """Everything within width / 2 of a line through points."""
    mask = set()
    for x, y, px, py in _centers():
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / max(dx * dx + dy * dy, 1e-9)))
            if (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2 <= width * width / 4:
                mask.add((x, y))
                break
    return mask


class Art:
    def __init__(self) -> None:
        self.pixels: dict = {}

    def fill(self, mask: set, material: tuple, outline: bool = True) -> None:
        """A shape with volume: lit on its top-left edge, shaded on the other."""
        if not mask:
            return
        lo = min(x + y for x, y in mask)
        hi = max(x + y for x, y in mask)
        for x, y in mask:
            out = lambda dx, dy: (x + dx, y + dy) not in mask
            if out(-1, 0) or out(0, -1):
                tone = 0
            elif out(1, 0) or out(0, 1):
                tone = 4
            elif out(-2, 0) or out(0, -2) or out(-1, -1):
                tone = 1
            elif out(2, 0) or out(0, 2) or out(1, 1):
                tone = 3
            else:
                along = (x + y - lo) / max(hi - lo, 1)
                tone = 1 if along < .3 else 3 if along > .72 else 2
            self.pixels[(x, y)] = material[tone]
        if outline:
            for x, y in mask:
                for p in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if p not in mask and p in self.pixels:
                        self.pixels[p] = INK

    def flat(self, points, color: tuple) -> None:
        """A detail by hand: in one tone, with no outline of its own."""
        for p in points:
            self.pixels[p] = color

    def finish(self) -> dict:
        """Closes the outline around everything drawn."""
        for (x, y), color in list(self.pixels.items()):
            if color == INK:
                continue
            for p in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if p not in self.pixels and 0 <= p[0] < _width and 0 <= p[1] < _height:
                    self.pixels[p] = INK
        return self.pixels


def heart(a: Art) -> None:
    a.fill(ellipse(7.5, 8.5, 5.6, 5.6) | ellipse(16.5, 8.5, 5.6, 5.6) | poly([(2.2, 10), (21.8, 10), (12, 22.4)]), RED)
    a.flat(rect(5, 5, 7, 6) | {(4, 7), (5, 7), (4, 8)}, RED[0])
    a.flat({(15, 5), (16, 5), (17, 5)}, RED[1])
    a.flat({(12, 19), (13, 18), (15, 16), (16, 15), (18, 13), (19, 11)}, RED[4])


def bullet(a: Art) -> None:
    a.fill(rect(7, 11, 16, 21), BRASS)
    a.fill(rect(6, 20, 17, 22), BRASS)
    a.fill(poly([(12, .8), (15, 3.5), (16.8, 8), (16.8, 11), (7.2, 11), (7.2, 8), (9, 3.5)]), COPPER)
    a.flat(rect(8, 12, 15, 12), BRASS[4])
    a.flat({(10, 4), (9, 5), (9, 6), (9, 7), (9, 8)}, COPPER[0])
    a.flat(rect(9, 14, 9, 18), BRASS[0])
    a.flat(rect(14, 14, 14, 18), BRASS[3])


def skull(a: Art) -> None:
    a.fill(rect(8, 16, 15, 21), BONE)
    a.fill(ellipse(12, 9.5, 9.6, 8.6), BONE)
    a.flat(rect(5, 9, 9, 12) | {(6, 13), (7, 13), (8, 13)} | rect(14, 9, 18, 12) | {(15, 13), (16, 13), (17, 13)}, INK)
    a.flat({(6, 9), (15, 9)}, RED[3])
    a.flat({(11, 14), (12, 14), (10, 15), (11, 15), (12, 15), (13, 15)}, INK)
    a.flat(rect(10, 18, 10, 21) | rect(13, 18, 13, 21) | {(8, 17), (9, 17), (14, 17), (15, 17)}, BONE[4])
    a.flat({(17, 2), (16, 3), (17, 4), (16, 5), (15, 6)}, BONE[4])
    a.flat({(6, 4), (7, 3), (8, 3), (5, 5)}, BONE[0])


def flag(a: Art) -> None:
    a.fill(poly([(7, 3), (21.5, 4.5), (18.5, 8.5), (22, 13), (7, 14)]), RED)
    a.flat({(10, 6), (11, 6), (12, 7), (13, 7), (14, 7), (15, 7)}, RED[0])
    a.flat({(12, 11), (13, 11), (14, 12), (15, 12), (16, 11), (17, 11)}, RED[4])
    a.fill(rect(4, 2, 6, 22), WOOD)
    a.fill(ellipse(5.5, 2.5, 2.4, 2.4), BRASS)
    a.fill(rect(2, 21, 9, 23), IRON)
    a.flat({(4, 9), (4, 13), (4, 17)}, WOOD[3])


def dynamite(a: Art) -> None:
    a.fill(stroke([(12, 8), (14, 4.5), (17, 3.5)], 1.5), IRON, outline=False)
    a.fill(poly([(19, .5), (20, 2.5), (22.5, 3.5), (20, 4.5), (19, 6.5), (18, 4.5), (15.5, 3.5), (18, 2.5)]), FIRE)
    for x0 in (3, 9, 15):
        a.fill(rect(x0, 8, x0 + 5, 21), RED)
        a.fill(ellipse(x0 + 3, 8, 3, 1.6), BONE)
    a.fill(rect(2, 13, 21, 16), WOOD)
    a.flat({(5, 14), (6, 15), (11, 14), (12, 15), (17, 14), (18, 15)}, WOOD[4])
    a.flat(rect(4, 18, 4, 20) | rect(10, 18, 10, 20) | rect(16, 18, 16, 20), RED[0])


def speaker(a: Art) -> None:
    a.fill(poly([(2, 8.5), (7.5, 8.5), (14, 2.5), (14, 21.5), (7.5, 15.5), (2, 15.5)]), BRASS)
    a.fill(rect(2, 9, 6, 15), IRON)
    a.flat({(3, 11), (4, 11), (3, 13), (4, 13)}, IRON[4])
    a.flat({(11, 7), (10, 8), (12, 8), (11, 9)}, BRASS[0])
    a.fill(stroke([(16.5, 8.5), (18, 12), (16.5, 15.5)], 2), ICE)
    a.fill(stroke([(19.2, 5), (21.8, 12), (19.2, 19)], 2), ICE)


def _star(a: Art, material: tuple) -> None:
    points = [(12, .6), (15.1, 8), (23, 8.7), (17, 14), (18.8, 22), (12, 17.8), (5.2, 22), (7, 14), (1, 8.7), (8.9, 8)]
    a.fill(poly(points), material)
    a.flat(poly([(12, 3), (12, 16), (6.5, 19), (8, 13.5), (4, 10), (9.5, 9.5)]), material[1])
    a.flat(poly([(12, 3), (12, 16), (17.5, 19), (16, 13.5), (20, 10), (14.5, 9.5)]), material[3])
    a.flat({(11, 4), (11, 5), (10, 6), (10, 7), (9, 8), (6, 10), (5, 10)}, material[0])
    a.flat({(12, y) for y in range(9, 16)}, material[2])


def star(a: Art) -> None:
    _star(a, GREEN)


def mission_star(a: Art) -> None:
    _star(a, BRASS)


def mission_star_empty(a: Art) -> None:
    _star(a, UNLIT)


def lock(a: Art) -> None:
    ring = ellipse(12, 8.5, 7.2, 7.5) - ellipse(12, 8.5, 3.8, 4.2)
    a.fill(ring - rect(0, 11, 23, 23), IRON)
    a.fill(rect(5, 8, 7, 11) | rect(16, 8, 18, 11), IRON, outline=False)
    a.fill(rect(3, 11, 20, 22), BRASS)
    a.flat(ellipse(12, 15, 2.1, 2.1) | rect(11, 16, 12, 19), INK)
    a.flat({(5, 13), (18, 13), (5, 20), (18, 20)}, BRASS[0])
    a.flat({x for x in rect(4, 21, 19, 21)}, BRASS[4])


def check(a: Art) -> None:
    a.fill(poly([(1.5, 13), (5, 9.5), (9.5, 14), (19.5, 2.5), (23, 5.5), (10, 21.5)]), GREEN)
    a.flat({(6, 11), (7, 12), (8, 13), (9, 14), (18, 5), (17, 6), (16, 7), (15, 8)}, GREEN[0])


def shell(a: Art) -> None:
    a.fill(rect(7, 2, 16, 15), RED)
    a.flat(rect(8, 2, 15, 3), RED[4])
    a.flat({(x, y) for y in (5, 8, 11) for x in range(8, 16)}, RED[3])
    a.flat(rect(9, 6, 9, 7) | rect(9, 9, 9, 10) | rect(9, 12, 9, 13), RED[0])
    a.fill(rect(7, 15, 16, 20), BRASS)
    a.fill(rect(6, 20, 17, 22), BRASS)
    a.flat(rect(9, 16, 9, 19), BRASS[0])
    a.flat(rect(14, 16, 14, 19), BRASS[3])


def _drop(cx: float, top: float, r: float) -> set:
    return ellipse(cx, top + r * 1.9, r, r) | poly([(cx, top), (cx + r * .95, top + r * 1.6), (cx - r * .95, top + r * 1.6)])


def blood(a: Art) -> None:
    a.fill(_drop(11, 1, 7.5), RED)
    a.flat({(7, 11), (6, 12), (6, 13), (6, 14), (7, 15), (9, 8), (8, 9)}, RED[0])
    a.flat({(13, 19), (14, 18), (15, 17), (16, 16)}, RED[4])
    a.fill(_drop(20, 13, 2.2), RED)


def slow(a: Art) -> None:
    a.fill(stroke([(6.5, 19), (10, 21.5)], 1.6), IRON, outline=False)
    a.fill(ellipse(4.8, 19, 3.6, 3.6), IRON)
    a.flat({(3, 17), (4, 17), (3, 18)}, IRON[0])
    a.fill(poly([(9, 1), (17, 1), (17, 10), (22.5, 13.5), (22.5, 18), (9, 18)]), WOOD)
    a.fill(rect(8, 18, 23, 20), WOOD)
    a.flat(rect(9, 19, 22, 20), WOOD[4])
    a.flat(rect(9, 4, 16, 4) | rect(9, 8, 16, 8), WOOD[4])
    a.flat({(14, 11), (15, 10), (16, 12), (17, 11), (18, 13), (19, 12)}, BONE[1])
    a.flat(rect(11, 5, 11, 15), WOOD[0])
    a.fill(rect(8, 12, 16, 14), IRON)


def gold(a: Art) -> None:
    a.fill(ellipse(12, 12, 10.6, 10.6), BRASS)
    a.fill(ellipse(12, 12, 7.6, 7.6), BRASS)
    points = [(12, 6.2), (13.5, 10), (17.6, 10.2), (14.4, 12.8), (15.5, 16.8), (12, 14.6), (8.5, 16.8), (9.6, 12.8), (6.4, 10.2), (10.5, 10)]
    a.flat(poly(points), BRASS[0])
    a.flat({(12, 15), (14, 13), (15, 16)}, BRASS[3])
    for x, y in ((12, 2), (19, 5), (21, 12), (19, 19), (12, 21), (4, 19), (2, 12), (4, 5)):
        a.flat({(x, y)}, BRASS[4])


def wind(a: Art) -> None:
    a.fill(stroke([(1.5, 8), (14, 8), (17.5, 6), (16.5, 2.8), (13, 3)], 2.6), ICE)
    a.fill(stroke([(1.5, 13), (19, 13), (22.5, 15.5), (21, 19), (17.5, 18.5)], 2.6), ICE)
    a.fill(stroke([(4.5, 18), (11, 18), (13.5, 20), (11.5, 22.2)], 2.4), ICE)
    a.flat({(3, 7), (4, 7), (5, 7), (6, 7), (3, 12), (4, 12), (5, 12), (6, 12), (7, 12)}, ICE[0])


def _wave(y: float) -> list:
    return [(x, y + (2.2 if x % 8 < 4 else -2.2) * (1 if x % 4 == 2 else .5))
            for x in range(1, 24, 2)]


def current(a: Art) -> None:
    for y, width in ((5.5, 3.6), (12, 3.6), (18.5, 3.6)):
        a.fill(stroke(_wave(y), width), WATER)
    a.flat({(4, 3), (5, 3), (12, 3), (13, 3), (20, 3), (4, 10), (5, 10), (12, 10), (13, 10), (20, 10),
            (4, 16), (5, 16), (12, 16), (13, 16), (20, 16)}, WATER[0])


def heat(a: Art) -> None:
    for points in ([(12, 0), (14.4, 6), (9.6, 6)], [(12, 24), (14.4, 18), (9.6, 18)],
                   [(0, 12), (6, 9.6), (6, 14.4)], [(24, 12), (18, 9.6), (18, 14.4)],
                   [(3.2, 3.2), (9, 6), (6, 9)], [(20.8, 3.2), (15, 6), (18, 9)],
                   [(3.2, 20.8), (9, 18), (6, 15)], [(20.8, 20.8), (15, 18), (18, 15)]):
        a.fill(poly(points), FIRE)
    a.fill(ellipse(12, 12, 6.8, 6.8), FIRE)
    a.flat(ellipse(11, 11, 3.6, 3.6), FIRE[0])
    a.flat({(8, 8), (9, 7), (10, 7)}, (255, 255, 255, 255))


def omen(a: Art) -> None:
    a.fill(poly([(1, 13), (6, 6), (12, 3), (18, 5), (23, 10), (19, 17), (12, 20.5), (6, 19)]), FEATHER)
    a.flat({(5, 8), (8, 6), (11, 5), (15, 5), (18, 7), (5, 17), (9, 19), (14, 19), (18, 16)}, FEATHER[0])
    a.fill(ellipse(12, 12, 7.4, 5.4), BONE)
    a.fill(ellipse(12, 12, 4.4, 4.4), RED)
    a.flat(ellipse(12, 12, 2.1, 2.1), INK)
    a.flat({(10, 9), (11, 9), (10, 10)}, (255, 255, 255, 255))


def cold(a: Art) -> None:
    """Six arms, each with a pair of branches, from one rotated stroke."""
    mask = set()
    for arm in range(6):
        angle = math.radians(60 * arm + 90)
        ax, ay = math.cos(angle), -math.sin(angle)
        tip = (12 + 11.4 * ax, 12 + 11.4 * ay)
        mask |= stroke([(12, 12), tip], 2.2)
        at = (12 + 6.8 * ax, 12 + 6.8 * ay)
        for side in (-1, 1):
            branch = angle + side * math.radians(55)
            mask |= stroke([at, (at[0] + 4.2 * math.cos(branch), at[1] - 4.2 * math.sin(branch))], 1.7)
    a.fill(mask, ICE)
    a.fill(ellipse(12, 12, 3.2, 3.2), ICE)
    a.flat({(11, 11), (12, 11), (11, 12)}, (255, 255, 255, 255))


def wet(a: Art) -> None:
    a.fill(ellipse(16, 21.2, 7, 2), WATER)
    a.fill(_drop(8, 1, 5.6), WATER)
    a.flat({(5, 8), (4, 9), (4, 10), (4, 11), (5, 12)}, WATER[0])
    a.fill(_drop(18, 6, 3.8), WATER)
    a.flat({(16, 11), (16, 12), (16, 13)}, WATER[0])


def cozy(a: Art) -> None:
    a.fill(stroke([(3, 21.5), (20, 17.5)], 3.6), WOOD)
    a.fill(stroke([(21, 21.5), (4, 17.5)], 3.6), WOOD)
    a.fill(ellipse(2.8, 21.5, 2.2, 2.2), BONE)
    a.fill(ellipse(21.2, 21.5, 2.2, 2.2), BONE)
    a.fill(poly([(12, 0), (14.5, 5), (18.5, 7), (17.5, 10), (20, 12), (18.5, 17), (14, 19.5), (9, 19.5),
                 (5, 17), (4, 12), (6.5, 10), (7, 6.5), (9.5, 7.5)]), FIRE)
    a.fill(poly([(12, 8), (14.5, 11.5), (15.5, 15), (13.5, 18.5), (10.5, 18.5), (8.5, 15), (10, 12)]), ramp(0xffffff, 0xfff2b0, 0xffdf70, 0xffcf5a, 0xf6962a), outline=False)
    a.flat({(20, 4), (4, 3), (21, 8)}, FIRE[1])


def water(a: Art) -> None:
    a.fill(rect(9, 0, 14, 4), WOOD)
    a.flat(rect(10, 2, 13, 2), WOOD[4])
    a.fill(rect(10, 4, 13, 6), IRON)
    a.fill(ellipse(12, 14, 9.8, 9), WATER)
    a.fill(rect(2, 12, 21, 15), WOOD)
    a.flat({(x, y) for x in range(4, 21, 3) for y in (13,)}, BONE[1])
    a.flat({(6, 8), (7, 7), (5, 9), (8, 7), (5, 10)}, WATER[0])
    a.flat({(8, 19), (9, 20), (10, 20), (11, 20), (13, 19), (14, 19)}, WATER[4])


def _sparkle(a: Art, cx: int, cy: int, reach: int) -> None:
    a.fill(poly([(cx + .5, cy - reach), (cx + 1.6, cy - .6), (cx + reach + 1, cy + .5), (cx + 1.6, cy + 1.6),
                 (cx + .5, cy + reach + 1), (cx - .6, cy + 1.6), (cx - reach, cy + .5), (cx - .6, cy - .6)]), ICE)


def fresh(a: Art) -> None:
    a.fill(_drop(9, 3, 6.6), WATER)
    a.flat({(5, 12), (4, 13), (4, 14), (4, 15), (5, 16), (7, 9)}, WATER[0])
    a.flat({(10, 20), (11, 19), (12, 18), (13, 17)}, WATER[4])
    _sparkle(a, 19, 5, 4)
    _sparkle(a, 20, 15, 2)


def save(a: Art) -> None:
    a.fill(poly([(1, 1), (20, 1), (23, 4), (23, 23), (1, 23)]), BRASS)
    a.fill(rect(6, 1, 17, 8), IRON)
    a.flat(rect(13, 2, 15, 7), INK)
    a.flat(rect(7, 2, 7, 7), IRON[0])
    a.fill(rect(4, 12, 19, 22), BONE)
    a.flat(rect(6, 14, 17, 14) | rect(6, 17, 17, 17), BONE[3])
    a.flat(rect(6, 20, 10, 20), RED[2])
    a.flat({(2, 3), (2, 22), (22, 22)}, BRASS[4])


def clock(a: Art) -> None:
    a.fill(ellipse(12, 3, 3, 2.6) - ellipse(12, 3, 1.2, 1), BRASS)
    a.fill(rect(10, 4, 13, 6), BRASS)
    a.fill(ellipse(12, 14, 9.8, 9.8), BRASS)
    a.fill(ellipse(12, 14, 7.3, 7.3), BONE)
    for x, y in ((12, 8), (17, 13), (12, 19), (7, 13), (15, 9), (9, 9), (15, 18), (9, 18)):
        a.flat({(x, y)}, BONE[4])
    a.flat(rect(12, 10, 12, 14) | {(13, 14), (14, 14), (15, 14)}, INK)
    a.flat({(12, 14)}, RED[2])
    a.flat({(7, 8), (6, 9), (5, 10)}, BRASS[0])


def arrow_left(a: Art) -> None:
    a.fill(poly([(1, 12), (11.5, 2), (11.5, 8), (23, 8), (23, 16), (11.5, 16), (11.5, 22)]), RED)
    a.flat({(10, 5), (9, 6), (8, 7), (7, 8), (6, 9), (5, 10)} | rect(12, 9, 21, 9), RED[0])
    a.flat(rect(12, 15, 22, 15) | {(9, 18), (8, 17), (7, 16)}, RED[4])


def arrow_right(a: Art) -> None:
    a.fill(poly([(23, 12), (12.5, 2), (12.5, 8), (1, 8), (1, 16), (12.5, 16), (12.5, 22)]), RED)
    a.flat({(14, 5), (15, 6), (16, 7), (17, 8)} | rect(2, 9, 12, 9), RED[0])
    a.flat(rect(2, 15, 12, 15) | {(14, 18), (15, 17), (16, 16), (17, 15), (18, 14)}, RED[4])


def construction(a: Art) -> None:
    """A roadworks barrier: hazard-striped board on two iron legs, red lamp on top."""
    a.fill(rect(4, 13, 6, 21) | rect(17, 13, 19, 21), IRON)
    a.fill(rect(1, 21, 9, 23) | rect(14, 21, 22, 23), GUNMETAL)
    board = rect(1, 6, 22, 14)
    a.fill(board, FIRE)
    a.flat({(x, y) for x, y in rect(2, 7, 21, 13) if (x + y) // 4 % 2 == 0}, BLACK[3])
    a.fill(ellipse(12, 3, 3.4, 3.2), RED)
    a.flat({(11, 1), (10, 2)}, RED[0])


ICONS = [heart, bullet, skull, flag, dynamite, speaker, star, lock, check, shell, blood, slow, gold,
         wind, current, heat, omen, cold, wet, cozy, water, fresh, save, clock, mission_star,
         mission_star_empty, arrow_left, arrow_right, construction]


def draw_all() -> list:
    """One {(x, y): (r, g, b, a)} per icon, in UiIcon order."""
    canvas(SIZE, SIZE)
    drawn = []
    for draw in ICONS:
        art = Art()
        draw(art)
        drawn.append(art.finish())
    return drawn


# ---- The guns, 72 x 28: each traced over its sprite in play ---------------
#
# In coordinates of that sprite: _Trace places them on the bigger grid, part by
# part, so the shape stays the game's. Her hand cannon is pistol.png (17 x 11);
# the SWAT's guns are tools/make_swat.py's templates, with the flashlight fixed
# under both barrels and the rifle's bayonet.

GUN_W, GUN_H = 72, 28


class _Trace:
    def __init__(self, art: Art, scale: float, ox: float = 0.0, oy: float = 0.0) -> None:
        self.art, self.scale, self.ox, self.oy = art, scale, ox, oy

    def at(self, x: float, y: float) -> tuple:
        return self.ox + x * self.scale, self.oy + y * self.scale

    def box(self, x0: float, y0: float, x1: float, y1: float) -> set:
        return poly([self.at(x0, y0), self.at(x1, y0), self.at(x1, y1), self.at(x0, y1)])

    def shape(self, *points: tuple) -> set:
        return poly([self.at(x, y) for x, y in points])


def _cannon(trace: _Trace) -> None:
    """Her hand cannon: thin wooden grip, grey frame, wood along the barrel over
    a brass band, the rod under it and the flared brass muzzle."""
    a, box, shape = trace.art, trace.box, trace.shape
    a.fill(shape((3.4, 6.8), (5.6, 7), (2.4, 10.8), (0, 10.8)), WOOD)
    a.flat(shape((3.6, 7.6), (4.4, 7.6), (1.8, 10.2), (1, 10.2)), WOOD[3])
    a.fill(shape((0, 9.6), (2.4, 9.6), (2.2, 11), (.2, 11)), BRASS)
    a.fill(box(7, 6, 13, 7), GUNMETAL)
    a.fill(box(13, 6, 14, 7), BRASS)
    a.fill(box(6.6, 6, 7.8, 8), BRASS)
    a.fill(box(3, 1, 6, 4), GUNMETAL)
    a.fill(box(3, 4, 6, 7), IRON)
    a.flat(box(3.8, 4.8, 4.2, 6.2), IRON[3])
    a.flat(box(5, 4.8, 5.4, 6.2), IRON[3])
    a.fill(box(6, 4, 9, 6), GUNMETAL)
    a.fill(box(6, 1, 13.4, 2), IRON)
    a.fill(box(6.6, 2, 13.4, 4), WOOD)
    a.flat(box(9, 2.1, 13.2, 2.8), WOOD[4])
    a.fill(box(7.8, 3, 9, 4), BRASS, outline=False)
    a.fill(box(9, 4, 14, 5), BRASS)
    a.fill(box(13.4, 1, 15, 5), GUNMETAL)
    a.fill(box(15, 0.6, 16, 5.4), BRASS)
    a.fill(box(16, 1.4, 17, 4.6), GUNMETAL)
    a.fill(box(14.8, 0, 15.8, 1), GUNMETAL)


def gun_cannon(a: Art) -> None:
    _cannon(_Trace(a, 2.5, 2, .4))


def _mounted_light(trace: _Trace) -> None:
    """The flashlight fixed under the barrel: its switch, and its glass."""
    a, box = trace.art, trace.box
    a.fill(box(22, 5, 27, 7), BLACK)
    a.flat(box(24, 6, 25, 6.6), RED[1])
    a.fill(box(26, 5, 27, 7), ICE, outline=False)


def gun_rifle(a: Art) -> None:
    trace = _Trace(a, 1.92, .7, 3)
    box, shape = trace.box, trace.shape
    a.fill(box(0, 2, 5, 4), GUNMETAL)                                   # Folded stock
    a.fill(box(0, 4, 2, 6), GUNMETAL)
    a.fill(shape((7, 6), (9, 6), (8.6, 9), (6, 9)), BLACK)              # Grip
    a.fill(shape((11, 6), (14, 6), (15, 10), (12, 10)), GUNMETAL)       # Magazine
    a.flat(box(12, 7.6, 14, 8.1), GUNMETAL[4])
    a.fill(box(5, 1, 17, 6), GUNMETAL)                                  # Receiver
    a.flat(box(6.5, 2, 11, 2.6), GUNMETAL[0])
    a.flat(box(13, 3, 16, 3.5), GUNMETAL[4])
    a.fill(box(8, -1, 14, 1), BLACK)                                    # Optic
    a.fill(box(12.4, -.6, 14, .6), WATER, outline=False)
    a.fill(box(17, 2, 24, 5), GUNMETAL)                                 # Handguard
    a.flat(box(18.4, 3, 18.9, 4.2) | box(20, 3, 20.5, 4.2) | box(21.6, 3, 22.1, 4.2), GUNMETAL[4])
    a.fill(box(24, 3, 29, 4), IRON)                                     # Barrel
    a.fill(box(26, 2, 28, 5), GUNMETAL)                                 # Muzzle brake
    _mounted_light(trace)
    a.fill(shape((29, 3.8), (34, 3.8), (36.4, 4.6), (33.6, 6), (30, 6), (30, 5), (29, 5)), IRON)  # Bayonet
    a.flat(box(30.4, 4.1, 34, 4.5), IRON[0])
    a.fill(box(28, 3.6, 29.6, 5.6), BLACK)


def gun_shotgun(a: Art) -> None:
    trace = _Trace(a, 2.05, 8.6, 1)
    box, shape = trace.box, trace.shape
    a.fill(shape((-4, 3), (-3, 2), (2, 2), (5, 3), (5, 6), (1, 7), (-4, 7)), BLACK)  # Full stock
    a.flat(box(-3, 3.6, 2, 4.1), BLACK[0])
    a.fill(shape((5, 6), (7, 6), (6.4, 9), (4, 9)), BLACK)              # Grip
    a.fill(box(5, 2, 13, 6), GUNMETAL)                                  # Receiver
    a.flat(box(6.5, 3, 10, 3.5), GUNMETAL[0])
    a.fill(box(13, 4, 25, 5), BLACK)                                    # Magazine tube
    a.fill(box(13, 2, 29, 4), GUNMETAL)                                 # Barrel
    a.flat(box(15, 2.4, 19, 2.9), GUNMETAL[0])
    a.fill(box(27, 1, 28, 2), IRON)                                     # Bead sight
    _mounted_light(trace)
    a.fill(box(15, 4, 22, 6), BLACK)                                    # Ribbed pump
    a.flat(box(16, 4.4, 16.4, 5.6) | box(18, 4.4, 18.4, 5.6) | box(20, 4.4, 20.4, 5.6), BLACK[0])


def gun_grenade(a: Art) -> None:
    a.fill(stroke([(40, 7), (47, 9), (45, 16)], 2.4), IRON)
    a.fill(ellipse(25, 5, 3.4, 3.4) - ellipse(25, 5, 1.3, 1.3), BRASS)
    a.fill(rect(30, 2, 41, 7), IRON)
    a.fill(ellipse(36, 17, 10.5, 10.4), OLIVE)
    a.flat({p for p in ellipse(36, 17, 9.6, 9.6) if (p[0] - 30) % 5 == 0 or (p[1] - 10) % 5 == 0}, OLIVE[4])


def tinted(pixels: dict, tint: int) -> dict:
    """The recolor of a stand-in character (character_skin.c): every color a
    shade of the tint by its brightness."""
    out = {}
    for xy, c in pixels.items():
        shade = (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 150.0
        out[xy] = tuple(min(255, round(((tint >> (8 * k)) & 0xFF) * shade)) for k in (2, 1, 0)) + (c[3],)
    return out


def paired(pixels: dict, dx: int, dy: int) -> dict:
    """Her duals as her shoot_dual sheet has them: a second gun up and behind,
    darker, and the near one over it."""
    out = {xy: tuple(round(v * .72) for v in c[:3]) + (c[3],) for xy, c in pixels.items()}
    out.update({(x + dx, y + dy): c for (x, y), c in pixels.items()})
    return out


HERO_TINT = 0x70c8b0  # The Hero's stand-in tint (src/game/characters.c): his gun in play


def draw_guns() -> list:
    """One {(x, y): color} per gun, in WeaponId order and then the grenade."""
    canvas(GUN_W, GUN_H)
    def drawn(draw, *args) -> dict:
        art = Art()
        draw(art, *args)
        return art.finish()
    near = drawn(lambda a: _cannon(_Trace(a, 2.1, 0, 0)))
    guns = [drawn(gun_cannon), drawn(gun_rifle), drawn(gun_shotgun), tinted(drawn(gun_cannon), HERO_TINT),
            paired(near, 8, 5), drawn(gun_grenade)]
    canvas(SIZE, SIZE)
    return guns


def grenade_frames() -> list:
    """The tumbling grenade in play: 8 x 8, a quarter turn per frame, with the
    light staying top left however it turns."""
    canvas(8, 8)
    frames = []
    body = ellipse(3.8, 4.4, 3, 3.1)
    lever = rect(3, 1, 5, 1)
    for turn in range(4):
        def turned(mask: set) -> set:
            out = set(mask)
            for _ in range(turn):
                out = {(7 - y, x) for x, y in out}
            return out
        art = Art()
        art.fill(turned(body), OLIVE)
        art.fill(turned(lever), IRON, outline=False)
        frames.append(art.finish())
    canvas(SIZE, SIZE)
    return frames


# The round every gun fires: grey, because the game tints it per gun. The ball
# spans columns 1-6 and every row (bullet.c's anchor is its center).
BULLET_ROWS = ['...kk...', '..kHMk..', '.kHMMSk.', '.kMMSSk.', '..kSSk..', '...kk...']
BULLET_TONES = {'k': INK, 'H': rgb(0xf4f4f8), 'M': rgb(0xb8b8c0), 'S': rgb(0x76767e)}
BULLET_GLINTS = ((), ((3, 2, FIRE[0]), (4, 2, FIRE[1])), (), ((4, 2, FIRE[1]),))


def bullet_frames() -> list:
    frames = []
    for glints in BULLET_GLINTS:
        pixels = {(x, y): BULLET_TONES[c] for y, row in enumerate(BULLET_ROWS)
                  for x, c in enumerate(row) if c != '.'}
        for x, y, color in glints:
            pixels[(x, y)] = color
        frames.append(pixels)
    return frames
