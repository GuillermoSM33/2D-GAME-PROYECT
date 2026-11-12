#!/usr/bin/env python3
"""Paint the road's decorative objects at the landscape's human scale.

Usage: tools/make_props.py [assets_dir] [--preview]

The 24 sheets match PropDef in src/game/props.c. Every frame is newly drawn
at its native size, grounded on its last row. Materials use daylight colors;
scene.c grades them for sunset, moonlight and the city. A lit bulb is marked
with LIGHT_ALPHA, so it keeps its warm color under that grading.
Deterministic, standard library only; no scaling of the old sprites.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape_kit import Canvas, Rng, fbm, hash2, hx, mix, save_all, sheet  # noqa: E402
from make_sprites import Image  # noqa: E402
from scenery_materials import lettering, planks  # noqa: E402


# Materials in daylight, darkest first. The full value range survives the
# landscape's light grading; highlights are deliberately broken, never glossy.
WOOD = [hx(v) for v in (0x30291F, 0x57442F, 0x826441, 0xA18155, 0xC2A574, 0xDECAA0)]
IRON = [hx(v) for v in (0x20282B, 0x3A4548, 0x5B6667, 0x84908C, 0xB4B9A7, 0xD9D8BA)]
RUST = [hx(v) for v in (0x4E3629, 0x744532, 0x9C6241, 0xBC8854)]
STONE = [hx(v) for v in (0x333635, 0x515550, 0x73766A, 0x949483, 0xBAB6A0, 0xD8D0B8)]
BONE = [hx(v) for v in (0x514939, 0x84745A, 0xAE9C78, 0xD2C096, 0xE7D8B6)]
GREEN = [hx(v) for v in (0x253526, 0x3C5030, 0x59703C, 0x7B8E4E, 0x9DAB6B, 0xC3C48A)]
RUBBER = [hx(v) for v in (0x1D2425, 0x313A38, 0x4B5450, 0x69716A, 0x8A8B7C)]
RED = [hx(v) for v in (0x3C2825, 0x6D3E31, 0x9F5740, 0xC97D53, 0xE0AE7B)]


def rim(c: Canvas, light, dark) -> None:
    """A restrained, broken upper-left edge; preserve the object's interior."""
    marks = []
    for y in range(c.h):
        for x in range(c.w):
            if not c.solid(x, y):
                continue
            if not c.solid(x, y - 1) or not c.solid(x - 1, y):
                marks.append((x, y, light if (x * 3 + y) % 7 != 0 else c.get(x, y)))
            elif not c.solid(x, y + 1) or not c.solid(x + 1, y):
                marks.append((x, y, dark))
    for x, y, col in marks:
        c.set(x, y, col)


def texture(c: Canvas, palette: list, seed: int, axis: str = 'stone') -> None:
    """Shade a mask with clustered grain. Long wood fibres, broad stone facets."""
    for y in range(c.h):
        for x in range(c.w):
            if not c.solid(x, y):
                continue
            if axis == 'wood':
                n = fbm(x / 2.0, y / 17.0, seed, 3)
            elif axis == 'bark':
                n = fbm(x / 1.5, y / 11.0, seed, 3)
            else:
                n = fbm(x / 8.0, y / 5.0, seed, 3)
            lighting = (1 - x / max(1, c.w - 1)) * 0.24 + (1 - y / max(1, c.h - 1)) * 0.13
            k = max(1, min(len(palette) - 2, int((n * 0.74 + lighting) * (len(palette) - 1))))
            c.set(x, y, palette[k])
            if hash2(x // 2, y, seed + 8) > 0.977:
                c.set(x, y, palette[min(len(palette) - 1, k + 1)])
    rim(c, palette[-2], palette[0])


def bolt(c: Canvas, x: int, y: int, brass: bool = False) -> None:
    p = WOOD if brass else IRON
    c.set(x - 1, y, p[0]); c.set(x, y + 1, p[0])
    c.set(x, y, p[4]); c.set(x + 1, y, p[2])


def beam(c: Canvas, x0: int, y0: int, x1: int, y1: int, width: int, seed: int = 1) -> None:
    """Rough timber, lit along one side, dark grain and chipped ends."""
    dx, dy = x1 - x0, y1 - y0
    length = max(1, math.hypot(dx, dy))
    nx, ny = -dy / length, dx / length
    pts = [(round(x0 + nx * width / 2), round(y0 + ny * width / 2)),
           (round(x1 + nx * width / 2), round(y1 + ny * width / 2)),
           (round(x1 - nx * width / 2), round(y1 - ny * width / 2)),
           (round(x0 - nx * width / 2), round(y0 - ny * width / 2))]
    part = Canvas(c.w, c.h)
    part.poly(pts, WOOD[2]); texture(part, WOOD, seed, 'wood')
    c.paste(part, 0, 0)


def cactus(variant: int) -> Canvas:
    c = Canvas(44, 100)
    # A mature saguaro, a young fork, an old broken saguaro, a flowering cholla.
    heights = (94, 77, 98, 60)
    top, cx = 99 - heights[variant], (21, 22, 24, 21)[variant]
    stems = []

    def stalk(x: int, y0: int, y1: int, radius: int) -> None:
        c.fill(x - radius, y0 + radius, x + radius, y1, GREEN[2])
        c.disc(x, y0 + radius, radius, GREEN[2])
        stems.append((x, y0, y1, radius))

    stalk(cx, top, 99, 6 if variant != 3 else 5)
    if variant in (0, 2):
        left_top, bend = top + 21, top + 55
        stalk(8, left_top, bend, 4)
        c.disc(12, bend, 8, GREEN[2], 5); c.fill(10, bend, cx, bend + 5, GREEN[2])
        if variant == 0:
            stalk(36, top + 35, top + 64, 4)
            c.disc(31, top + 64, 8, GREEN[2], 5)
        else:
            c.fill(28, top + 66, 38, top + 72, GREEN[2])
            c.poly([(36, top + 66), (40, top + 60), (41, top + 70), (37, top + 72)], GREEN[1])
    elif variant == 1:
        stalk(34, top + 22, top + 51, 4)
        c.fill(cx, top + 50, 35, top + 55, GREEN[2])
    else:
        for x, y, b in ((8, 59, 81), (35, 48, 69), (11, 38, 61)):
            stalk(x, y, b, 3); c.line(x, b, cx, b + 6, GREEN[2], 5)
    texture(c, GREEN, 120 + variant, 'wood')
    for x, y0, y1, r in stems:
        for rx in range(x - r + 2, x + r, 3):
            for y in range(y0 + r + 1, y1):
                if c.solid(rx, y):
                    c.set(rx, y, GREEN[1] if rx > x else GREEN[3])
        for y in range(y0 + r + 4, y1 - 1, 5):
            for dx in (-r, 0, r):
                xx = x + dx
                if (y + dx + variant) % 3:
                    c.set(xx, y, GREEN[4]); c.set(xx + (-1 if dx < 0 else 1), y - 1, BONE[3])
    if variant == 2:
        c.line(cx - 2, top + 65, cx - 2, top + 82, WOOD[0])
        c.disc(cx - 1, top + 64, 2, WOOD[1], 3)
    if variant in (1, 3):
        for x, y in ((cx, top), (34, top + 22 if variant == 1 else 48)):
            c.disc(x, y + 1, 3, hx(0x874A48), 2)
            c.hline(x - 1, x + 1, y, hx(0xD49B91)); c.set(x, y - 1, hx(0xE4BE9E))
    for y in range(95, 100):
        for x in range(cx - 5, cx + 5):
            if c.solid(x, y) and hash2(x, y, variant) < 0.45:
                c.set(x, y, WOOD[1 if y > 97 else 2])
    return c


def rock(variant: int) -> Canvas:
    c = Canvas(48, 24)
    points = [[(2, 22), (7, 12), (17, 5), (32, 7), (41, 14), (46, 23)],
              [(1, 23), (4, 17), (14, 15), (21, 3), (33, 2), (41, 10), (46, 23)],
              [(3, 23), (5, 11), (16, 4), (29, 5), (31, 12), (41, 15), (46, 23)]][variant]
    c.poly(points, STONE[2]); texture(c, STONE, 221 + variant)
    if variant == 0:
        c.poly([(7, 12), (17, 5), (32, 7), (25, 13), (13, 15)], STONE[4])
        c.poly([(25, 13), (32, 7), (41, 14), (46, 23), (29, 23)], STONE[1])
        c.line(17, 7, 21, 11, STONE[5]); c.line(21, 11, 25, 12, STONE[5])
    elif variant == 1:
        c.poly([(22, 4), (32, 3), (36, 10), (23, 15)], STONE[4])
        c.poly([(36, 10), (41, 10), (46, 23), (30, 23)], STONE[1])
        c.line(17, 16, 23, 14, STONE[0]); c.line(23, 14, 25, 19, STONE[0])
    else:
        c.poly([(5, 11), (16, 4), (29, 5), (22, 11)], STONE[4])
        c.line(10, 14, 23, 15, STONE[0]); c.line(23, 15, 30, 12, STONE[0])
        c.line(25, 18, 38, 19, STONE[4])
    for y in range(7, 24):
        for x in range(3, 47):
            if c.solid(x, y) and hash2(x // 2, y, 225 + variant) > 0.94:
                c.set(x, y, STONE[3 if y % 3 else 1])
    c.hline(7, 42, 23, STONE[0])
    return c


def fence(variant: int) -> Canvas:
    c = Canvas(72, 40)
    for y in (14, 29):
        beam(c, 1, y, 70, y + (1 if variant else 0), 5, 301 + y)
    for k, x in enumerate((6, 35, 65)):
        ytop = (2, 0, 5)[k] + variant * (k == 1) * 10
        part = Canvas(72, 40)
        part.poly([(x - 3, ytop + 2), (x - 1, ytop), (x + 3, ytop + 1),
                   (x + 4, 39), (x - 4, 39)], WOOD[2])
        texture(part, WOOD, 306 + k + variant, 'wood'); c.paste(part, 0, 0)
        for y in (14, 29):
            bolt(c, x, y)
    if variant:
        # A slanted missing rail, split ends and some fence wire.
        beam(c, 38, 19, 60, 37, 4, 321)
        for x in range(13, 34):
            c.clear(x, 14); c.clear(x, 15)
        for x in range(12, 64):
            y = 8 + int(2 * math.sin((x - 12) / 52 * math.pi))
            if not c.solid(x, y):
                c.set(x, y, IRON[2])
        c.line(14, 27, 19, 23, WOOD[0]); c.line(47, 28, 53, 25, WOOD[0])
    return c


def dead_tree(variant: int) -> Canvas:
    c = Canvas(100, 150)
    rng = Rng(401 + variant)
    # Each segment tapers; old branches have short broken tips rather than leaves.
    branches = [(50, 149, 48, 94, 13, 9), (48, 94, 57, 49, 9, 5),
                (57, 49, 54, 8, 5, 2), (49, 105, 28, 83, 8, 5),
                (28, 83, 13, 48, 5, 2), (17, 57, 4, 41, 3, 1),
                (28, 83, 11, 77, 4, 1), (51, 81, 75, 65, 7, 4),
                (75, 65, 85, 25, 4, 1), (78, 53, 95, 43, 3, 1),
                (55, 44, 34, 30, 4, 2), (34, 30, 30, 12, 2, 1),
                (57, 48, 68, 17, 4, 1)]
    if variant:
        branches = [(100-x, y, 100-a + rng.range(-4, 4), b + (rng.range(-6, 6) if b < 120 else 0), w, z)
                    for x, y, a, b, w, z in branches if b != 17]
        branches += [(49, 112, 29, 94, 7, 3), (29, 94, 18, 96, 3, 1)]
    for x0, y0, x1, y1, w0, w1 in branches:
        dx, dy = x1 - x0, y1 - y0
        n = max(1, math.hypot(dx, dy)); nx, ny = -dy / n, dx / n
        c.poly([(round(x0 + nx*w0/2), round(y0 + ny*w0/2)),
                (round(x1 + nx*w1/2), round(y1 + ny*w1/2)),
                (round(x1 - nx*w1/2), round(y1 - ny*w1/2)),
                (round(x0 - nx*w0/2), round(y0 - ny*w0/2))], WOOD[2])
    for x in (35, 42, 57, 65):
        c.poly([(48, 137), (x, 149), (x + 5, 149), (54, 136)], WOOD[2])
    texture(c, WOOD, 411 + variant, 'bark')
    for x0, y0, x1, y1, w0, _ in branches:
        if w0 < 4:
            continue
        # Sparse deep fissures along the direction of the trunk/branch.
        for k in range(3, max(4, int(math.hypot(x1-x0, y1-y0))), 10):
            n = max(1, math.hypot(x1-x0, y1-y0))
            t = k / n
            x, y = round(x0 + (x1-x0)*t), round(y0 + (y1-y0)*t)
            for d in range(4):
                xx, yy = x + d * (1 if x1 > x0 else -1) // 3, y - d
                if c.solid(xx, yy): c.set(xx, yy, WOOD[0])
    c.disc(50, 115, 3, WOOD[0], 6); c.disc(49, 114, 1, WOOD[3], 3)
    c.disc(54 if not variant else 45, 88, 2, WOOD[0], 4)
    return c


def grass(variant: int) -> Canvas:
    c = Canvas(24, 14)
    rng = Rng(501 + variant)
    for _ in range(19):
        root = rng.range(7, 17)
        tip, high = rng.range(1, 22), rng.range(1 + variant, 10)
        col = WOOD[rng.range(1, 4)] if variant != 2 else GREEN[rng.range(1, 4)]
        c.line(root, 13, (root + tip) // 2, (high + 13) // 2, col)
        c.line((root + tip) // 2, (high + 13) // 2, tip, high, col)
        if variant in (1, 3) and tip % 3 == 0:
            c.line(tip - 1, high + 1, tip + 1, high - 1, BONE[2])
    c.hline(7, 18, 13, WOOD[0])
    return c


def wagon_wheel(variant: int) -> Canvas:
    c = Canvas(44, 44)
    cx, cy, r = 22, 22, 20
    for spoke in range(12):
        ang = spoke * math.tau / 12 + variant * 0.12
        if variant and spoke in (2, 3):
            continue
        x, y = cx + math.cos(ang)*18, cy + math.sin(ang)*18
        c.line(cx, cy, x, y, WOOD[0], 3)
        c.line(cx - 1, cy - 1, x - 1, y - 1, WOOD[3], 1)
    for y in range(44):
        for x in range(44):
            d = math.hypot(x - cx, y - cy)
            if 16.6 <= d <= 20.8:
                if variant and x > 33 and y < 13:
                    continue
                band = 0 if d > 20 or d < 17.5 else 2 + (x < cx and y < cy)
                c.set(x, y, IRON[band] if d > 19.5 else WOOD[band])
                if (x - cx)*2 + y < 41 and d > 20:
                    c.set(x, y, IRON[3])
                if hash2(x, y, 610 + variant) > 0.94:
                    c.set(x, y, RUST[1])
    c.disc(cx, cy, 5, WOOD[0]); c.disc(cx-1, cy-1, 4, WOOD[3])
    c.disc(cx, cy, 2, IRON[1]); bolt(c, cx, cy)
    for k in range(8):
        a = k*math.tau/8
        bolt(c, round(cx + 19*math.cos(a)), round(cy + 19*math.sin(a)))
    if variant:
        c.line(34, 6, 37, 12, WOOD[5]); c.line(38, 13, 41, 15, WOOD[4])
        c.line(15, 26, 9, 36, WOOD[0])
    c.hline(19, 26, 43, WOOD[0])
    return c


def skull(variant: int) -> Canvas:
    c = Canvas(34, 18)
    if variant == 0:
        c.poly([(7, 6), (10, 2), (17, 1), (24, 4), (25, 10), (21, 16), (13, 17), (9, 13)], BONE[2])
        c.line(9, 6, 4, 3, BONE[2], 3); c.line(4, 3, 2, 0, BONE[3], 2)
        c.line(24, 5, 29, 3, BONE[2], 3); c.line(29, 3, 32, 0, BONE[3], 2)
    else:
        c.poly([(8, 5), (11, 1), (22, 2), (27, 6), (24, 12), (21, 16), (12, 17), (8, 12)], BONE[2])
    texture(c, BONE, 704 + variant)
    c.poly([(10, 6), (15, 6), (14, 10), (10, 10)], BONE[0])
    c.poly([(21, 6), (25, 7), (23, 11), (19, 10)], BONE[0])
    c.poly([(17, 10), (19, 13), (15, 13)], BONE[0])
    c.hline(13, 21, 14, BONE[1])
    for x in range(13, 22, 3): c.vline(x, 14, 16, BONE[4])
    c.line(18, 2, 17, 5, BONE[1]); c.line(17, 5, 19, 7, BONE[1])
    return c


def tombstone(variant: int) -> Canvas:
    c = Canvas(28, 40)
    if variant == 1:
        c.poly([(11, 2), (17, 2), (17, 10), (24, 10), (24, 16), (17, 16),
                (18, 35), (24, 36), (25, 39), (3, 39), (4, 36), (10, 35), (11, 16), (4, 16), (4, 10), (11, 10)], STONE[2])
    elif variant == 2:
        c.poly([(11, 2), (16, 0), (20, 30), (24, 35), (25, 39), (2, 39), (4, 35), (8, 30)], STONE[2])
    else:
        c.fill(4, 11, 24, 36, STONE[2]); c.disc(14, 11, 10, STONE[2], 9)
        c.fill(2, 36, 25, 39, STONE[2])
        if variant == 3:
            for x, y in ((4, 7), (5, 8), (22, 4), (23, 5), (24, 6), (24, 7)):
                c.clear(x, y)
    texture(c, STONE, 800 + variant)
    if variant in (0, 3):
        c.line(7, 14, 21, 14, STONE[1]); c.line(7, 15, 20, 15, STONE[4])
        lettering(c, 'RIP', 9, 18, STONE[1])
        for y, w in ((27, 11), (30, 8)):
            c.hline(14-w//2, 14+w//2, y, STONE[1]); c.hline(14-w//2, 14+w//2-1, y+1, STONE[3])
    elif variant == 1:
        c.vline(13, 7, 28, STONE[4]); c.hline(8, 20, 12, STONE[4])
    else:
        c.line(12, 6, 11, 27, STONE[4]); c.line(17, 8, 20, 30, STONE[1])
    if variant in (0, 3):
        c.line(19, 4, 16, 12, STONE[0]); c.line(16, 12, 19, 17, STONE[0]); c.line(16, 12, 11, 14, STONE[0])
    for x in range(3, 26):
        y = 38 - int(hash2(x // 2, 1, variant + 820)*3)
        if c.solid(x, y): c.set(x, y, GREEN[1])
    return c


def sign(variant: int) -> Canvas:
    c = Canvas(36, 62)
    beam(c, 18, 10, 18, 61, 5, 901)
    if variant == 0:
        c.poly([(1, 5), (28, 5), (34, 13), (28, 21), (1, 21)], WOOD[2])
        planks(c, (2, 7, 28, 19), WOOD[3], seed=905, width=6)
        c.line(29, 7, 33, 13, WOOD[4]); c.line(33, 13, 29, 18, WOOD[1])
        lettering(c, 'TOWN', 4, 10, WOOD[0]); bolt(c, 18, 8); bolt(c, 18, 19)
    else:
        c.poly([(3, 4), (32, 6), (31, 27), (1, 24)], WOOD[2])
        planks(c, (3, 7, 30, 23), WOOD[3], seed=908, width=6)
        lettering(c, 'KEEP', 6, 10, WOOD[0]); lettering(c, 'OUT', 9, 17, WOOD[0])
        c.line(4, 22, 11, 19, WOOD[0]); bolt(c, 18, 7); bolt(c, 18, 24)
    c.line(16, 41, 17, 54, WOOD[0]); c.line(19, 29, 20, 37, WOOD[4])
    return c


def hydrant(_variant: int) -> Canvas:
    c = Canvas(14, 24)
    c.fill(4, 5, 10, 21, RED[2]); c.disc(7, 5, 4, RED[2], 3)
    c.fill(2, 20, 12, 23, IRON[1]); c.hline(3, 11, 20, IRON[3])
    c.fill(0, 9, 13, 14, RED[1]); c.fill(1, 9, 3, 14, IRON[1]); c.fill(11, 9, 13, 14, IRON[1])
    c.vline(4, 7, 19, RED[3]); c.vline(10, 7, 19, RED[0])
    c.hline(4, 9, 4, RED[4]); c.hline(4, 10, 7, RED[0]); c.hline(5, 9, 8, RED[3])
    c.fill(6, 0, 8, 2, IRON[2]); bolt(c, 7, 1); bolt(c, 6, 12)
    c.line(11, 15, 11, 17, IRON[2]); c.line(11, 17, 9, 19, IRON[2])
    for x, y in ((5, 16), (8, 18), (9, 10)): c.set(x, y, IRON[3])
    return c


def streetlight(variant: int) -> Canvas:
    c = Canvas(40, 150)
    x = 24 if not variant else 13
    c.poly([(x-4, 149), (x-3, 136), (x-2, 31), (x, 19), (x+2, 31), (x+3, 136), (x+5, 149)], IRON[1])
    for xx in range(x-3, x+4):
        for y in range(33, 150):
            if c.solid(xx, y):
                c.set(xx, y, IRON[3 if xx < x-1 else 1 if xx > x else 2])
    if not variant:
        c.line(x, 22, x-3, 12, IRON[1], 3); c.line(x-3, 12, 12, 6, IRON[2], 3)
        c.line(12, 6, 7, 7, IRON[3], 2)
        c.poly([(2, 7), (14, 7), (18, 11), (1, 11)], IRON[1])
        c.hline(3, 14, 8, IRON[4]); c.hline(4, 14, 12, hx(0xB39D65))
        for xx in range(5, 14): c.light(xx, 12, hx(0xE0C38B))
    else:
        c.line(x, 22, x+4, 15, IRON[2], 3); c.line(x+4, 15, 28, 14, IRON[2], 3)
        c.poly([(24, 10), (36, 10), (37, 15), (23, 15)], IRON[1])
        c.line(24, 10, 35, 10, IRON[4]); c.hline(25, 34, 14, IRON[3])
        # Broken, hanging glass and a bent lamp head.
        c.line(30, 16, 31, 24, IRON[1]); c.line(31, 24, 27, 27, IRON[1])
        c.line(25, 16, 27, 20, IRON[4])
    c.fill(x-5, 143, x+5, 149, IRON[1]); c.hline(x-5, x+4, 143, IRON[3])
    c.fill(x-2, 112, x+2, 122, IRON[0]); c.vline(x-2, 112, 122, IRON[3]); bolt(c, x+1, 115)
    for y in (46, 87, 132):
        c.hline(x-2, x+2, y, IRON[0]); c.set(x-1, y-1, RUST[1])
    for y in range(30, 143):
        if hash2(x, y, 1001) > 0.94: c.set(x, y, RUST[2])
    return c


def trash(variant: int) -> Canvas:
    c = Canvas(26, 32)
    if not variant:
        c.poly([(3, 7), (22, 7), (20, 30), (6, 31)], IRON[2]); texture(c, IRON, 1110)
        for x in (7, 11, 15, 19):
            c.line(x, 10, x, 28, IRON[1]); c.line(x-1, 10, x-1, 26, IRON[3])
        c.disc(12, 7, 11, IRON[1], 3); c.hline(3, 20, 6, IRON[4])
        c.fill(8, 2, 15, 4, IRON[1]); c.hline(9, 14, 2, IRON[3])
        c.fill(0, 11, 2, 16, IRON[1]); c.fill(23, 11, 25, 16, IRON[1])
        c.line(6, 26, 10, 28, RUST[2]); c.line(18, 16, 17, 21, RUST[1])
    else:
        c.poly([(3, 15), (8, 8), (10, 5), (18, 7), (21, 16), (25, 28),
                (20, 31), (4, 31), (0, 27)], RUBBER[1]); texture(c, RUBBER, 1119)
        c.fill(9, 2, 15, 6, RUBBER[1]); c.line(10, 1, 13, 4, IRON[2]); c.line(15, 1, 13, 4, IRON[1])
        c.line(7, 16, 5, 26, RUBBER[0]); c.line(15, 10, 20, 27, RUBBER[0])
        c.line(12, 17, 11, 23, RUBBER[3]); c.line(3, 28, 7, 30, RUBBER[3])
        c.poly([(18, 18), (24, 17), (24, 21), (20, 23)], BONE[2]); c.hline(20, 23, 19, IRON[1])
    return c


def cone(_variant: int) -> Canvas:
    c = Canvas(16, 24)
    c.poly([(1, 20), (12, 19), (15, 22), (13, 23), (0, 23)], RUBBER[1])
    c.poly([(7, 1), (9, 1), (13, 21), (2, 21)], RED[2])
    for y in range(2, 21):
        left, right = 7 - y//5, 9 + y//6
        c.hline(left, right, y, RED[3] if y % 6 < 3 else RED[2])
        c.set(left, y, RED[4]); c.set(right, y, RED[1])
        if 8 <= y <= 11 or 16 <= y <= 18:
            c.hline(left, right-1, y, BONE[3]); c.set(right, y, BONE[1])
    c.hline(3, 12, 21, RED[0]); c.set(5, 18, RED[1]); c.set(10, 11, RED[1])
    return c


def tire(c: Canvas, cx: int, cy: int, rx: int, ry: int, seed: int) -> None:
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x-cx)/rx)**2 + ((y-cy)/ry)**2
            if d > 1.05: continue
            if d < 0.30:
                c.set(x, y, RUBBER[0]); continue
            k = 3 if y < cy-ry*0.35 else 2 if x < cx else 1
            if d > 0.85: k = 0 if y > cy else 2
            if (x + (y//2)*3 + seed) % 6 < 2 and d > 0.54: k = max(0, k-1)
            c.set(x, y, RUBBER[k])
    c.hline(cx-rx+4, cx+rx-5, cy-ry+2, RUBBER[3])
    for xx in range(cx-rx+5, cx+rx-4, 6): c.set(xx, cy-ry+1, RUBBER[4])


def tires(_variant: int) -> Canvas:
    c = Canvas(40, 34)
    tire(c, 24, 28, 15, 5, 1); tire(c, 24, 23, 14, 5, 3); tire(c, 25, 18, 13, 5, 5)
    tire(c, 11, 23, 10, 10, 7)
    c.disc(11, 23, 4, RUBBER[0]); c.line(6, 16, 4, 21, RUBBER[3])
    c.line(12, 28, 15, 30, RUBBER[1]); c.line(30, 16, 33, 17, WOOD[2])
    return c


def sandbag(c: Canvas, x: int, y: int, w: int, h: int, seed: int) -> None:
    c.poly([(x+3, y), (x+w-4, y), (x+w-1, y+2), (x+w, y+h-3),
            (x+w-3, y+h-1), (x+2, y+h-1), (x, y+h-3), (x+1, y+2)], WOOD[2])
    for yy in range(y+1, y+h-1):
        for xx in range(x+1, x+w):
            if not c.solid(xx, yy): continue
            k = 4 if yy < y+3 else 3 if xx < x+w-4 else 2
            if hash2(xx//2, yy, seed) > 0.85: k -= 1
            c.set(xx, yy, WOOD[k])
    c.hline(x+4, x+w-4, y+h-2, WOOD[1]); c.line(x+2, y+3, x+3, y+h-4, WOOD[1])
    for yy in range(y+3, y+h-3, 2): c.set(x+3, yy, BONE[2])
    c.set(x+w-2, y+3, WOOD[0]); c.set(x+w-3, y+4, WOOD[0])


def sandbags(_variant: int) -> Canvas:
    c = Canvas(66, 28)
    for row, y in enumerate((18, 10, 1)):
        for k in range(3):
            x = 1 + k*21 + (4 if row == 1 else 0)
            if x + 20 > 66: continue
            sandbag(c, x, y + k%2, 20, 9, 1200+row*5+k)
    c.hline(2, 62, 27, WOOD[0])
    return c


def jersey(_variant: int) -> Canvas:
    c = Canvas(104, 27)
    c.poly([(5, 26), (5, 22), (16, 14), (19, 1), (87, 1), (89, 14), (99, 22), (99, 26)], STONE[2])
    texture(c, STONE, 1301)
    c.poly([(19, 2), (86, 2), (87, 8), (18, 8)], STONE[4])
    c.line(18, 9, 16, 15, STONE[5]); c.line(16, 15, 6, 23, STONE[4])
    c.hline(7, 98, 23, STONE[1]); c.hline(6, 98, 26, STONE[0])
    # Faded hazard stripes on the sloped lower face, interrupted by chips.
    for y in range(15, 23):
        for x in range(18, 87):
            if c.solid(x, y) and hash2(x//3, y//2, 1302) > 0.16:
                c.set(x, y, WOOD[4] if (x + y) % 24 < 11 else IRON[0])
    for points in ([(32, 3), (35, 9), (31, 14), (34, 18)], [(76, 8), (73, 13), (76, 23)]):
        for a, b in zip(points, points[1:]): c.line(*a, *b, STONE[1])
    for x, y in ((25, 4), (53, 10), (66, 3), (84, 23)):
        c.hline(x, x+3, y, STONE[0]); c.hline(x, x+2, y+1, STONE[4])
    c.fill(25, 24, 31, 26, IRON[0]); c.fill(74, 24, 80, 26, IRON[0])
    for x in (32, 72):
        c.line(x, 2, x, 0, IRON[1]); c.hline(x, x+3, 0, IRON[2]); c.vline(x+3, 0, 2, IRON[1])
    return c


def pole(_variant: int) -> Canvas:
    c = Canvas(44, 160)
    beam(c, 23, 6, 23, 159, 7, 1401)
    beam(c, 3, 17, 41, 17, 4, 1403); beam(c, 9, 29, 36, 29, 4, 1404)
    c.line(8, 19, 23, 44, IRON[1]); c.line(38, 19, 23, 44, IRON[1])
    for x, y in ((6, 10), (21, 10), (38, 10), (12, 22), (34, 22)):
        c.fill(x-1, y, x+1, y+6, IRON[1]); c.hline(x-2, x+2, y+1, IRON[3]); c.hline(x-2, x+2, y+4, IRON[3])
    # A transformer, ridged cap, porcelain bushings and strapped conduit.
    c.fill(28, 36, 39, 59, IRON[1]); c.disc(33, 36, 6, IRON[2], 2)
    c.fill(29, 38, 36, 56, IRON[3]); c.vline(30, 38, 56, IRON[4])
    c.hline(29, 38, 58, IRON[0]); c.hline(29, 39, 39, IRON[1]); c.hline(29, 39, 54, IRON[1])
    c.vline(30, 30, 34, IRON[1]); c.vline(36, 30, 34, IRON[1]); c.hline(29, 31, 31, IRON[4])
    c.line(12, 27, 15, 32, IRON[0]); c.line(15, 32, 30, 31, IRON[0])
    c.line(37, 24, 41, 28, IRON[0]); c.line(41, 28, 36, 31, IRON[0])
    c.vline(27, 58, 159, IRON[1]); c.vline(28, 60, 159, IRON[3])
    for y in (65, 102, 140): c.hline(20, 28, y, IRON[0]); bolt(c, 22, y)
    for y in range(92, 147, 12):
        c.line(19, y, 15, y+1, IRON[1]); c.set(15, y, IRON[3])
    c.fill(20, 78, 25, 86, BONE[2]); c.vline(22, 80, 83, IRON[0]); c.set(22, 85, IRON[0])
    return c


def litter(variant: int) -> Canvas:
    c = Canvas(20, 6)
    if not variant:
        c.poly([(1, 3), (5, 0), (10, 1), (13, 0), (19, 4), (17, 5), (2, 5)], BONE[2])
        c.line(5, 1, 6, 4, BONE[4]); c.line(7, 1, 8, 5, BONE[0])
        for y in (2, 4): c.hline(10, 15, y, IRON[2])
    elif variant == 1:
        c.poly([(2, 4), (3, 1), (11, 1), (13, 3), (11, 5), (4, 5)], IRON[2])
        c.hline(4, 10, 1, IRON[4]); c.line(5, 2, 8, 4, RED[2]); c.vline(12, 2, 4, IRON[0])
        c.line(15, 4, 18, 3, IRON[2]); c.set(16, 2, IRON[4])
    else:
        c.poly([(1, 4), (5, 3), (7, 1), (15, 1), (17, 4), (14, 5), (5, 5)], GREEN[1])
        c.hline(8, 13, 1, GREEN[4]); c.hline(8, 11, 3, GREEN[3]); c.hline(1, 4, 4, IRON[3])
    return c


def signal(_variant: int) -> Canvas:
    c = Canvas(24, 110)
    c.fill(10, 15, 14, 109, IRON[1]); c.vline(10, 17, 107, IRON[3]); c.vline(14, 17, 109, IRON[0])
    c.fill(5, 105, 19, 109, IRON[1]); c.hline(6, 18, 105, IRON[3])
    c.poly([(5, 2), (16, 2), (20, 7), (20, 31), (16, 36), (5, 36), (1, 31), (1, 7)], IRON[0])
    c.hline(5, 16, 2, IRON[3]); c.vline(2, 8, 30, IRON[2])
    for cy in (12, 26):
        c.disc(10, cy, 6, IRON[2]); c.disc(10, cy, 4, RED[0] if cy == 12 else GREEN[0])
        c.hline(5, 16, cy-5, IRON[0]); c.line(4, cy-4, 4, cy-1, IRON[3])
        c.set(8, cy-2, RED[2] if cy == 12 else GREEN[2])
        if cy == 12:
            c.light(9, cy, hx(0xE3AA70)); c.light(10, cy, hx(0xCF7956)); c.light(10, cy+1, hx(0xCF7956))
    c.fill(16, 65, 22, 79, IRON[1]); c.hline(16, 21, 65, IRON[3]); bolt(c, 20, 68)
    c.vline(17, 79, 109, IRON[0])
    for y in range(42, 104, 8):
        c.hline(6, 10, y, IRON[2]); c.set(6, y-1, IRON[4])
    c.fill(8, 48, 16, 57, BONE[2]); lettering(c, '7', 11, 50, IRON[0])
    return c


def drum(c: Canvas, x: int, y: int, w: int, h: int, seed: int, red: bool = False) -> None:
    pal = RED if red else IRON
    c.fill(x, y+3, x+w-1, y+h-3, pal[2]); c.disc(x+w/2-0.5, y+3, w/2-0.5, pal[2], 3)
    c.disc(x+w/2-0.5, y+h-4, w/2-0.5, pal[1], 3)
    for yy in range(y+4, y+h-3):
        for xx in range(x, x+w):
            if not c.solid(xx, yy): continue
            k = 3 if xx < x+w/3 else 2 if xx < x+w*0.7 else 1
            if fbm(xx/3, yy/5, seed, 2) > 0.65: k = max(0, k-1)
            c.set(xx, yy, pal[k])
            if hash2(xx//2, yy//2, seed+2) > 0.87: c.set(xx, yy, RUST[1 if xx>x+w/2 else 2])
    for yy in (y+3, y+h//3, y+h*2//3, y+h-4):
        c.hline(x, x+w-1, yy, IRON[0]); c.hline(x+1, x+w-3, yy-1, pal[3])
    c.disc(x+w/2, y+2, w/2-1, pal[3], 2); c.hline(x+3, x+w-4, y+1, pal[-1])
    c.disc(x+w-5, y+2, 1, IRON[0])
    c.poly([(x+5, y+11), (x+w-5, y+11), (x+w-5, y+17), (x+5, y+17)], BONE[2])
    c.line(x+w//2, y+12, x+w//2-2, y+15, IRON[0]); c.line(x+w//2-2, y+15, x+w//2+2, y+15, IRON[0])


def drums(_variant: int) -> Canvas:
    c = Canvas(48, 34)
    drum(c, 22, 0, 21, 33, 1511, red=False)
    drum(c, 2, 5, 23, 29, 1512, red=True)
    return c


def fallen_pole(_variant: int) -> Canvas:
    c = Canvas(150, 26)
    beam(c, 9, 20, 136, 10, 7, 1601)
    # Split heartwood at the snapped end, loose cross-arm and porcelain caps.
    c.poly([(7, 17), (1, 14), (4, 19), (0, 20), (7, 22)], WOOD[4])
    c.line(9, 19, 23, 18, WOOD[0]); c.line(10, 21, 26, 20, WOOD[1])
    beam(c, 121, 1, 128, 24, 4, 1602)
    for x, y in ((120, 3), (123, 11), (127, 21)):
        c.fill(x+2, y-2, x+7, y+1, IRON[1]); c.vline(x+5, y-2, y+1, IRON[4])
    for y in range(10, 25):
        for x in range(60, 145):
            if abs(y-(22+3*math.sin(x/13))) < 0.45 and not c.solid(x, y): c.set(x, y, IRON[0])
    bolt(c, 125, 11); bolt(c, 111, 12)
    c.line(95, 10, 99, 12, IRON[1]); c.line(99, 12, 111, 10, IRON[1])
    return c


def traffic_light(variant: int) -> Canvas:
    c = Canvas(60, 140)
    polex = 13 if not variant else 45
    c.fill(polex-2, 5, polex+2, 139, IRON[1]); c.vline(polex-2, 8, 135, IRON[3]); c.vline(polex+2, 8, 137, IRON[0])
    c.fill(polex-5, 134, polex+5, 139, IRON[1]); c.hline(polex-5, polex+4, 134, IRON[3])
    end = 43 if not variant else 19
    c.line(polex, 11, end, 11, IRON[1], 3); c.line(polex-1, 9, end, 9, IRON[3])
    c.line(polex, 28, end-5 if not variant else end+5, 12, IRON[1])
    x, top = end-6, 15 if not variant else 20
    if variant:
        c.line(end, 11, end-1, 19, IRON[0]); c.line(end-1, 19, end+2, 23, IRON[0])
    c.poly([(x, top+2), (x+2, top), (x+11, top), (x+13, top+2), (x+13, top+39),
            (x+11, top+41), (x+2, top+41), (x, top+39)], WOOD[1])
    c.vline(x, top+2, top+38, WOOD[4]); c.hline(x+2, x+11, top, WOOD[4])
    for k, cy in enumerate((top+8, top+21, top+34)):
        pal = RED if k == 0 else WOOD if k == 1 else GREEN
        c.disc(x+6, cy, 5, IRON[0]); c.disc(x+6, cy+1, 3, pal[1])
        c.hline(x+1, x+12, cy-5, IRON[0]); c.hline(x+2, x+10, cy-6, IRON[2])
        c.set(x+5, cy-1, pal[2]); c.set(x+6, cy+2, pal[0])
        if not variant and k == 0:
            for xx, yy in ((5, 0), (6, 0), (6, 1), (7, 0)):
                c.light(x+xx, cy+yy, hx(0xD99165))
    c.fill(polex-3, 86, polex+4, 100, IRON[1]); c.hline(polex-3, polex+3, 86, IRON[3]); bolt(c, polex+2, 89)
    c.vline(polex+4, 101, 139, IRON[0])
    for y in (40, 76, 128): c.set(polex, y, RUST[2]); c.set(polex, y+1, RUST[1])
    return c


def shrub(variant: int) -> Canvas:
    c = Canvas(40, 36)
    rng = Rng(1700+variant)
    for k in range(7):
        x = rng.range(6, 33); y = rng.range(10, 24)
        c.line(19, 35, x, y, WOOD[1], 2)
    # Broad clusters with branching shadows and small, directional leaf pairs.
    clusters = [(9, 26, 8), (16, 18, 10), (24, 12+variant*2, 9), (31, 24, 8), (21, 27, 13)]
    if variant == 3: clusters = [(8, 28, 7), (15, 24, 8), (24, 22, 9), (32, 29, 7)]
    mask = Canvas(40, 36)
    for x, y, r in clusters:
        mask.disc(x, y, r, GREEN[1], r*0.8)
    for y in range(36):
        for x in range(40):
            if not mask.solid(x, y): continue
            n = fbm(x/5, y/4, 1710+variant, 3)
            if hash2(x//2, y//2, variant+1711) < 0.065: continue
            k = 1 + min(3, int(n*3 + (1-y/36)*0.9))
            c.set(x, y, GREEN[k])
    for y in range(3, 34, 3):
        for x in range(2, 39, 3):
            if not c.solid(x, y) or hash2(x, y, variant+1720) < 0.48: continue
            top = not c.solid(x, y-2)
            col = GREEN[4 if top else 3 if hash2(x,y,variant)>.45 else 1]
            c.set(x, y, col)
            if c.solid(x+1, y): c.set(x+1, y, col)
            if top and c.solid(x, y+1): c.set(x, y+1, GREEN[2])
    if variant == 1:
        for x, y in ((11, 13), (24, 7), (29, 18), (15, 23)):
            c.set(x, y, hx(0xBDAA85)); c.set(x+1, y, hx(0xD2BD92)); c.set(x, y+1, hx(0x9D7858))
    elif variant == 2:
        for x, y in ((9, 26), (18, 15), (29, 22)):
            c.line(x, y, x+3, y-5, WOOD[2]); c.line(x+1, y-2, x-1, y-5, WOOD[3])
    c.line(19, 29, 18, 35, WOOD[1]); c.line(21, 30, 23, 35, WOOD[1])
    return c


def telegraph(variant: int) -> Canvas:
    c = Canvas(40, 176)
    beam(c, 20, 2, 20+variant*2, 175, 7, 1801+variant)
    for y, ext in ((16, 18), (31, 14)):
        beam(c, 20-ext, y, 20+ext, y, 4, 1803+y)
        for x in (20-ext+2, 12, 28, 20+ext-2):
            c.vline(x, y-7, y-1, IRON[1]); c.hline(x-2, x+2, y-6, IRON[3]); c.hline(x-2, x+2, y-3, IRON[3])
            c.set(x-1, y-7, IRON[4])
        c.line(20-ext+3, y+2, 20, y+24, IRON[1]); c.line(20+ext-3, y+2, 20, y+24, IRON[1])
        bolt(c, 20, y)
    for y in range(66, 172, 17):
        c.line(16, y, 11, y+1, IRON[1]); c.set(11, y, IRON[3])
    c.fill(17, 108, 23, 117, BONE[2]); lettering(c, '4', 19, 110, WOOD[0])
    if variant:
        # A broken wire loops below the crossarm, with no disconnected floaters.
        c.line(34, 24, 37, 40, IRON[0]); c.line(37, 40, 34, 57, IRON[0]); c.line(34, 57, 29, 65, IRON[0])
        c.line(29, 65, 27, 62, IRON[0]); c.line(27, 62, 28, 56, IRON[0])
    c.line(18, 137, 19, 151, WOOD[0]); c.line(21, 155, 23, 170, WOOD[0])
    return c


def incise(c: Canvas, points: list, color, allowed=None, glint=None) -> None:
    """Carve a connected feature into its material, without painting the air.

    A pale lower edge beside a dark groove describes its depth. These marks
    follow an actual split, fold, joint or casting seam; they are not noise.
    """
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        length = max(abs(x1-x0), abs(y1-y0), 1)
        for step in range(length+1):
            x = round(x0+(x1-x0)*step/length)
            y = round(y0+(y1-y0)*step/length)
            if c.solid(x, y) and (allowed is None or c.get(x, y) in allowed) and (x,y) not in c.lights:
                c.set(x, y, color)
                if glint is not None and c.solid(x-1, y) and (allowed is None or c.get(x-1, y) in allowed):
                    c.set(x-1, y, glint)


def ellipse_ring(c: Canvas, x: int, y: int, rx: float, ry: float, color, clipped=True) -> None:
    steps = max(12, round(math.tau*max(rx, ry)*2))
    for step in range(steps):
        a = math.tau*step/steps
        xx, yy = round(x+rx*math.cos(a)), round(y+ry*math.sin(a))
        if not clipped or c.solid(xx, yy):
            c.set(xx, yy, color)


def insulator(c: Canvas, x: int, y: int, scale=1) -> None:
    """Stacked porcelain sheds, a steel pin, an iron cap and its wire groove."""
    c.fill(x, y, x+scale, y+7*scale, IRON[0])
    for k in range(3):
        yy = y+k*2*scale
        c.hline(x-2*scale, x+3*scale, yy, hx(0x6B8C83))
        c.hline(x-2*scale+1, x+2*scale, yy+scale, hx(0xB3C2A4))
        c.set(x-2*scale, yy, hx(0xD3D5B7))
    c.hline(x-1, x+2*scale, y-1, IRON[1])
    c.set(x, y-2, IRON[4])


def finish_cactus(c: Canvas, variant: int) -> None:
    allowed = set(GREEN)
    cx = (21,22,24,21)[variant]
    top = 99-(94,77,98,60)[variant]
    # The ribs follow the swollen column, narrowing and curling into its cap.
    for offset in (-4,-1,2,4):
        points=[]
        for y in range(top+8,95,3):
            x=cx+offset+round(math.sin(y*.085+offset)*.6)
            points.append((x,y))
        incise(c,points,GREEN[1 if offset>0 else 2],allowed,GREEN[4 if offset<1 else 3])
    for y in range(top+13,92,11):
        for dx in (-4,1,4):
            x=cx+dx; yy=y+(dx%3)*2
            if c.get(x,yy) not in allowed: continue
            c.set(x,yy,WOOD[1])
            # Three tiny needles radiate from one pale areole, in a group.
            c.set(x-1,yy-1,BONE[2]); c.set(x+1,yy-1,BONE[3]); c.set(x,yy-2,BONE[3])
    # Corked scars have a depressed center and a raised, irregular rim.
    wound_y=top+42 if variant != 3 else 76
    for dx,dy in ((0,-2),(-1,-1),(1,-1),(-2,0),(1,0),(-1,1),(0,2)):
        x,y=cx+2+dx,wound_y+dy
        if c.solid(x,y): c.set(x,y,WOOD[3] if dx<0 else WOOD[1])
    incise(c,[(cx+2,wound_y-1),(cx+1,wound_y+1)],WOOD[0])
    # Young offsets emerge from the base; flowers have a dark throat and
    # distinct petals rather than a flat pink cap.
    if variant in (0,2):
        x,y=cx-7,85
        c.disc(x,y,3,GREEN[1],6); incise(c,[(x-1,y-4),(x-1,y+5)],GREEN[4])
        c.set(x,y-6,BONE[3]); c.set(x-2,y-1,BONE[2])
    if variant in (1,3):
        for x,y in ((cx,top),(34,top+22 if variant==1 else 48)):
            for dx,dy in ((-2,0),(0,-2),(2,0),(-1,2),(1,2)):
                c.set(x+dx,y+dy,hx(0xC28B87)); c.set(x+dx-1,y+dy,hx(0xE2B5A3))
            c.set(x,y,hx(0x70423D)); c.set(x,y+1,hx(0xD3AF6A))


def finish_rock(c: Canvas, variant: int) -> None:
    # Stacked sediment cuts across the lit face and changes direction at a
    # corner. A second face sits under it, dark and fractured.
    paths = [([(8,13),(17,12),(24,14)],[(7,17),(18,17),(27,19),(33,18)],[(24,13),(26,17),(24,21)]),
             ([(9,18),(19,16),(29,15)],[(23,8),(30,9),(35,8)],[(28,4),(27,10),(30,13),(29,21)]),
             ([(7,12),(15,11),(24,12)],[(6,18),(16,18),(24,20),(31,19)],[(20,5),(18,9),(21,13),(19,17)])][variant]
    for path in paths:
        incise(c,path,STONE[1],glint=STONE[4])
    incise(c,[(34,14),(34,18),(39,22)],STONE[0])
    incise(c,[(34,18),(41,17)],STONE[0])
    # Chipped ledges are short facets, paired with their undersides.
    for x,y in ((12,15),(28,21),(39,20)):
        if not c.solid(x,y): continue
        incise(c,[(x,y),(x+3,y-1),(x+5,y)],STONE[4])
        incise(c,[(x+1,y+1),(x+5,y+1)],STONE[1])
    for x,y in ((10,21),(31,19)):
        for dx,dy in ((0,0),(1,0),(2,1),(1,2)):
            if c.solid(x+dx,y+dy): c.set(x+dx,y+dy,hx(0x73774F) if dy<2 else hx(0x4D553D))


def finish_fence(c: Canvas, variant: int) -> None:
    # End grain in each post is an ellipse with a central check split.
    for k,x in enumerate((6,35,65)):
        y=(2,0,5)[k]+variant*(k==1)*10
        c.hline(x-2,x+2,y+2,WOOD[5]); c.hline(x-1,x+2,y+3,WOOD[1]); c.set(x,y+2,WOOD[2])
        incise(c,[(x+1,y+2),(x,y+8),(x+1,y+11)],WOOD[0],glint=WOOD[3])
        # An oblong knot and two long checks make the post read as timber.
        yy=20 if k!=1 else 23
        ellipse_ring(c,x,yy,2,4,WOOD[1]); c.set(x,yy,WOOD[0])
        incise(c,[(x-2,yy+4),(x-1,yy+8),(x-2,38)],WOOD[1],glint=WOOD[4])
        for yy in (14,29):
            c.fill(x-2,yy-2,x+2,yy+2,IRON[1]); bolt(c,x,yy)
    # Rail scarfs and a forged repair strap have an actual join and fasteners.
    for y in (14,29):
        incise(c,[(48,y-2),(46,y),(47,y+2)],WOOD[0],glint=WOOD[4])
        incise(c,[(14,y+1),(22,y),(29,y+1)],WOOD[1])
    if variant:
        c.fill(44,27,52,30,IRON[1]); bolt(c,45,28); bolt(c,51,28)
        # Tight barbed wire, with hanging slack at the broken middle post.
        for x in range(10,64):
            y=8+round(4*math.sin((x-10)*math.pi/54))
            if not c.solid(x,y): c.set(x,y,IRON[1])
            if x%11==0:
                c.line(x-1,y-2,x+1,y+2,IRON[2]); c.line(x+1,y-1,x-1,y+1,IRON[1])


def finish_tree(c: Canvas, variant: int) -> None:
    # Secondary twigs grow from the large limbs, giving the crown an organic
    # hierarchy. They are deliberately sparse, dead and broken at their ends.
    twigs=[((18,60),(9,56),(5,50)),((29,82),(33,67),(30,60)),
           ((37,32),(42,22),(41,15)),((56,29),(48,20),(47,13)),
           ((70,68),(77,79),(84,82)),((84,37),(92,31),(94,26)),
           ((56,50),(65,44),(70,35))]
    for a,b,d in twigs:
        if variant:
            a,b,d=tuple((100-x,y) for x,y in (a,b,d))
        if not c.solid(*a):
            nearby=[(x,y) for y in range(max(0,a[1]-5),min(c.h,a[1]+6))
                    for x in range(max(0,a[0]-5),min(c.w,a[0]+6)) if c.solid(x,y)]
            if not nearby:
                continue
            a=min(nearby,key=lambda p:(p[0]-a[0])**2+(p[1]-a[1])**2)
        c.line(*a,*b,WOOD[1],2); c.line(*b,*d,WOOD[1])
        c.line(a[0]-1,a[1],b[0]-1,b[1],WOOD[3])
    # Bark comes away in long curved plates, revealing pale heartwood. These
    # checks wind around the lower trunk and the two main forks.
    paths=[[(45,146),(46,133),(44,122),(46,110),(45,102)],
           [(52,143),(50,132),(51,125),(49,118)],
           [(54,108),(52,100),(54,91),(52,82)],
           [(49,88),(45,82),(40,78),(36,72)],
           [(58,65),(59,53),(56,42),(57,30)]]
    for points in paths:
        if variant: points=[(100-x,y) for x,y in points]
        incise(c,points,WOOD[0],glint=WOOD[4])
    x=50 if not variant else 49
    ellipse_ring(c,x,116,3,7,WOOD[1]); ellipse_ring(c,x,116,2,5,WOOD[4])
    c.disc(x,116,1,WOOD[0],3)
    # Flaring roots, with a lit upper edge and earth gathered between them.
    for end in (33,40,59,67):
        xx=100-end if variant else end
        start=48 if end<50 else 53
        if variant:start=100-start
        c.line(start,139,xx,149,WOOD[1],2); c.line(start-1,139,xx-1,148,WOOD[3])
    for x in (40,56):
        incise(c,[(x,148),(x+3,146),(x+6,148)],WOOD[0])


def finish_wheel(c: Canvas, variant: int) -> None:
    # The iron tyre is in two rolled rings; joins in the bent wooden felloe
    # are offset from the twelve mortised spokes.
    ellipse_ring(c,22,22,19,19,IRON[1]); ellipse_ring(c,22,22,17,17,WOOD[4])
    for k in range(8):
        a=k*math.tau/8+.15
        x,y=round(22+18*math.cos(a)),round(22+18*math.sin(a))
        if variant and x>33 and y<13: continue
        incise(c,[(x,y),(round(22+16*math.cos(a)),round(22+16*math.sin(a)))],WOOD[0])
    ellipse_ring(c,22,22,5,5,IRON[1]); ellipse_ring(c,22,22,3,3,IRON[3]); c.set(22,22,IRON[0])
    if variant:
        for x,y in ((33,7),(36,10),(38,13)):
            c.clear(x,y); c.clear(x+1,y)
    incise(c,[(6,24),(7,28),(10,32)],RUST[2])


def finish_grass(c: Canvas, variant: int) -> None:
    pal=GREEN if variant==2 else WOOD
    # Broad curled blades flank the fine stalks; oat-like seed pairs follow
    # the upper stem, leaving air between one grass head and the next.
    for x,tip in ((8,4),(16,20)):
        c.line(12,13,x,8,pal[2]); c.line(x,8,tip,6,pal[3]); c.set(tip,7,pal[1])
    if variant in (1,3):
        for x,top in ((7,3),(16,2)):
            c.line(x+1,11,x,top,pal[2])
            for y in range(top,top+5,2):
                c.set(x-1,y,pal[4]); c.set(x+1,y+1,pal[3])
    incise(c,[(10,12),(12,10),(14,12)],pal[1])


def finish_skull(c: Canvas, variant: int) -> None:
    incise(c,[(15,3),(16,5),(15,7)],BONE[1],glint=BONE[4])
    incise(c,[(15,5),(12,4)],BONE[1]); incise(c,[(22,11),(20,13),(20,15)],BONE[0])
    c.set(10,7,BONE[3]); c.set(21,7,BONE[2])
    for x in range(13,22,2):
        if c.solid(x,16): c.set(x,16,BONE[1])
    if not variant:
        incise(c,[(3,2),(5,4),(8,5)],BONE[0],glint=BONE[3])
        incise(c,[(25,4),(28,3),(30,1)],BONE[1],glint=BONE[4])


def finish_stone(c: Canvas, variant: int) -> None:
    # A carved bevel sits inside the outline, catching light while the sunk
    # face stays dark. The cross/obelisk receive chamfers along their shafts.
    if variant in (0,3):
        ellipse_ring(c,14,11,8,6,STONE[4])
        incise(c,[(6,13),(6,33),(22,33),(22,13)],STONE[1],glint=STONE[4])
        for x,y in ((7,11),(21,28),(5,31)):
            incise(c,[(x,y),(x+2,y-1),(x+3,y+1)],STONE[0],glint=STONE[3])
        incise(c,[(20,24),(18,27),(20,31),(18,35)],STONE[0],glint=STONE[4])
    elif variant==1:
        incise(c,[(12,4),(12,12),(6,12)],STONE[5])
        incise(c,[(15,18),(15,32)],STONE[1],glint=STONE[4])
    else:
        incise(c,[(13,5),(12,28),(9,32)],STONE[5])
        incise(c,[(15,15),(17,20),(16,23),(18,27)],STONE[1])
    # Moss spreads in rooted patches at the damp foot, not random green dots.
    for start,length,high in ((5,7,3),(17,6,5)):
        for x in range(start,start+length):
            peak=39-high+round(math.sin(x*1.1)*1.3)
            for y in range(peak,39):
                if c.solid(x,y): c.set(x,y,GREEN[2 if (x+y)%4 else 3] if y<37 else GREEN[1])
    for x,y in ((8,9),(23,25)):
        if c.solid(x,y): c.clear(x,y); c.set(x+1,y+1,STONE[4])


def finish_sign(c: Canvas, variant: int) -> None:
    # Paired strap bolts, splits from nail holes, a water-stained board end.
    for y in ((8,19) if not variant else (7,24)):
        bolt(c,18,y)
        incise(c,[(19,y+1),(22,y+3),(27,y+2)],WOOD[1])
    incise(c,[(16,31),(16,40),(17,46),(16,58)],WOOD[1],glint=WOOD[4])
    ellipse_ring(c,19,49,1,3,WOOD[0]); c.set(18,48,WOOD[4])
    if variant:
        for x,y in ((2,22),(28,25),(30,6)):
            if c.solid(x,y): c.clear(x,y)


def finish_hydrant(c: Canvas, _variant: int) -> None:
    # Fluted cast body and the cap's wrench flats remain legible at 14px.
    incise(c,[(6,15),(6,19)],RED[0],glint=RED[4])
    c.fill(5,5,9,6,RED[2]); c.hline(5,8,5,RED[4]); c.set(9,6,RED[0])
    c.set(1,11,IRON[4]); c.set(12,11,IRON[3]); c.set(11,13,IRON[0])
    c.hline(4,10,21,IRON[4]); c.hline(4,10,22,IRON[0])
    c.set(9,17,IRON[2]); c.set(8,18,RUST[2])


def finish_lamp(c: Canvas, variant: int) -> None:
    x=24 if not variant else 13
    # Anchored inspection hatch: projecting hinges, keyhole and galvanized
    # mounting bands; a ribbed foundation casting carries four anchor nuts.
    c.fill(x-3,108,x+3,123,IRON[0]); c.fill(x-2,109,x+2,122,IRON[2])
    c.vline(x-2,110,121,IRON[3]); c.vline(x+2,110,121,IRON[1])
    for y in (112,120): c.hline(x-3,x-2,y,IRON[4])
    c.set(x+1,116,IRON[0]); c.set(x+1,117,IRON[0])
    for y in (79,101,130):
        c.hline(x-2,x+2,y,IRON[0]); c.hline(x-2,x+1,y-1,IRON[3])
    for dx in (-3,3):
        c.vline(x+dx,144,148,IRON[0]); bolt(c,x+dx,148)
    if not variant:
        # A segmented diffuser, metal housing seam and cable entry.
        for xx in range(4,15,3): c.set(xx,10,IRON[1]); c.set(xx,11,IRON[3])
        c.hline(4,14,9,IRON[1]); bolt(c,13,8)
        c.line(18,12,20,20,IRON[0])
    else:
        c.hline(25,35,12,IRON[3]); c.set(26,13,IRON[0]); c.set(34,13,IRON[0])
        c.line(26,16,25,21,IRON[3]); c.set(27,21,IRON[4])
    incise(c,[(x+1,47),(x+1,54),(x,57)],RUST[1],glint=IRON[3])


def finish_trash(c: Canvas, variant: int) -> None:
    if not variant:
        ellipse_ring(c,12,7,9,2,IRON[1]); incise(c,[(4,8),(20,8)],IRON[4])
        # A punched handle, stamped rim, rolled seam and dented vertical ribs.
        c.hline(9,14,3,IRON[0]); c.hline(9,14,2,IRON[4])
        incise(c,[(18,12),(16,16),(18,20),(17,25)],IRON[0],glint=IRON[4])
        c.poly([(7,16),(12,17),(12,22),(8,23)],BONE[2]); c.hline(8,11,18,IRON[1]); c.hline(8,10,20,IRON[2])
        c.set(11,22,BONE[0]); c.set(8,16,BONE[4])
        incise(c,[(6,28),(18,28)],IRON[3]); incise(c,[(7,30),(19,30)],IRON[0])
    else:
        # Creases converge on the tied mouth and pinch where the bag rests.
        for points in ([(11,7),(8,15),(9,22)],[(14,7),(16,16),(14,25)],
                       [(17,13),(20,23),(23,28)],[(4,20),(6,25),(12,29)],
                       [(10,27),(14,30),(19,29)]):
            incise(c,points,RUBBER[0],glint=RUBBER[3])
        c.line(10,4,6,2,RUBBER[1]); c.line(14,4,18,2,RUBBER[1])
        c.set(11,5,IRON[3]); c.set(12,6,IRON[2])
        # One crumpled newspaper protrudes through a slit, with its folded edge.
        c.poly([(17,17),(23,15),(24,20),(21,23),(18,21)],BONE[2])
        c.line(20,16,21,22,BONE[4]); c.line(21,16,22,21,BONE[1])
        c.hline(18,20,18,IRON[1]); c.hline(19,21,20,IRON[1])


def finish_cone(c: Canvas, _variant: int) -> None:
    incise(c,[(7,3),(6,7),(6,10)],RED[4])
    incise(c,[(5,14),(4,17),(4,20)],RED[1])
    c.hline(3,12,22,RUBBER[0]); c.set(3,21,RUBBER[3]); c.set(12,21,RUBBER[2])
    c.set(10,17,RED[1]); c.set(10,18,RED[0]); c.set(5,10,RED[2])


def finish_tires(c: Canvas, _variant: int) -> None:
    # The standing tyre's opening is actual transparent air. Sidewalls have
    # concentric mould lines; tread blocks wrap around its curved outside.
    for y in range(14,33):
        for x in range(1,22):
            d=math.hypot((x-11)/10,(y-23)/10)
            if d<.37:
                c.clear(x,y)
            elif .65<d<.76 and c.solid(x,y):
                c.set(x,y,RUBBER[3] if x<11 and y<24 else RUBBER[1])
    for step in range(14):
        a=step*math.tau/14
        x,y=round(11+9*math.cos(a)),round(23+9*math.sin(a))
        incise(c,[(x,y),(x+round(2*math.cos(a+.6)),y+round(2*math.sin(a+.6)))],RUBBER[0],glint=RUBBER[2])
    for cy,rx in ((18,13),(23,14),(28,15)):
        for x in range(15,39,5):
            y=cy+round((x-26)/12)
            incise(c,[(x,y),(x+2,y+1),(x+3,y)],RUBBER[0],glint=RUBBER[3])
        incise(c,[(25-rx,cy+2),(37,cy+2)],RUBBER[0])
    incise(c,[(6,16),(7,18),(6,20)],RUBBER[0])


def finish_bags(c: Canvas, _variant: int) -> None:
    # Stitches follow each sack's gathered end; broad diagonal folds curve
    # around the soft fill, with frayed seams and a small cloth patch.
    for row,y in enumerate((18,10,1)):
        for k in range(3):
            x=1+k*21+(4 if row==1 else 0)
            if x+20>66: continue
            incise(c,[(x+3,y+3),(x+7,y+4),(x+10,y+3)],WOOD[2],glint=WOOD[4])
            incise(c,[(x+15,y+2),(x+12,y+5),(x+15,y+6)],WOOD[1],glint=WOOD[3])
            for dy in (2,4,6):
                if c.solid(x+17,y+dy): c.set(x+17,y+dy,BONE[2])
    c.fill(28,13,32,16,WOOD[2]); c.set(28,13,BONE[3]); c.set(30,16,BONE[3])


def finish_jersey(c: Canvas, _variant: int) -> None:
    # Lift eyes, recessed sockets, vertical formwork seams and exposed steel
    # at the chipped edge make the barrier look cast rather than painted.
    for x in (35,69):
        c.fill(x,4,x+3,7,STONE[1]); c.hline(x,x+2,4,STONE[5]); c.vline(x,5,7,STONE[0])
    for x in (21,52,85):
        incise(c,[(x,3),(x,11),(x-2,14)],STONE[2],glint=STONE[4])
    incise(c,[(93,20),(90,21),(89,24),(85,25)],STONE[0],glint=STONE[4])
    c.line(90,23,96,23,IRON[1]); c.set(94,22,RUST[2]); c.set(96,23,IRON[3])
    for x,y in ((17,18),(44,21),(73,17)):
        incise(c,[(x,y),(x+4,y+1)],STONE[3])


def finish_pole(c: Canvas, _variant: int) -> None:
    for x,y in ((6,10),(21,10),(38,10),(12,22),(34,22)):
        insulator(c,x,y)
    # A transformer has cooling fins, two bushing studs, a riveted nameplate,
    # mounting straps and a cable running from the service loop into conduit.
    for x in (30,33,36):
        incise(c,[(x,42),(x,54)],IRON[1],glint=IRON[4])
    c.fill(31,46,35,50,BONE[1]); c.hline(32,34,47,IRON[0]); c.hline(32,34,49,IRON[0])
    for y in (38,57):
        c.hline(26,39,y,IRON[0]); bolt(c,28,y)
    c.line(36,31,41,33,IRON[0]); c.line(41,33,42,43,IRON[0]); c.line(42,43,39,49,IRON[0])
    c.line(30,31,27,26,IRON[0]); c.line(27,26,21,15,IRON[0])
    c.fill(16,60,29,65,IRON[1]); c.hline(16,28,60,IRON[3]); bolt(c,18,62); bolt(c,27,62)
    for points in ([(21,70),(20,79)],[(23,93),(22,108),(23,116)],[(21,123),(20,132),(21,141)]):
        incise(c,points,WOOD[0],glint=WOOD[4])


def finish_litter(c: Canvas, variant: int) -> None:
    if not variant:
        incise(c,[(4,2),(9,3),(12,2)],BONE[4])
        incise(c,[(8,1),(9,3),(8,5)],BONE[0])
        for x,y in ((12,2),(14,3),(15,4)): c.set(x,y,IRON[1])
    elif variant==1:
        ellipse_ring(c,4,3,1,2,IRON[0]); c.set(4,1,IRON[4]); c.set(5,4,IRON[3])
        c.set(9,2,RED[3]); c.set(8,3,RED[1]); c.set(10,4,IRON[0])
    else:
        incise(c,[(6,4),(8,2),(13,2)],GREEN[4])
        c.set(14,3,GREEN[0]); c.set(12,4,GREEN[0]); c.set(8,4,BONE[2])


def finish_signal(c: Canvas, _variant: int) -> None:
    for cy in (12,26):
        for x in (8,10,12):
            for y in range(cy-2,cy+3):
                if (x,y) not in c.lights and c.solid(x,y):
                    c.set(x,y,RED[2] if cy==12 else GREEN[2])
        c.hline(5,15,cy-5,IRON[0]); bolt(c,3,cy-3)
    c.fill(16,66,22,79,IRON[0]); c.fill(17,67,21,78,IRON[2]); c.vline(17,68,77,IRON[3])
    c.set(20,73,IRON[0]); bolt(c,20,68); bolt(c,20,77)
    for y in (42,88,103):
        c.hline(9,15,y,IRON[0]); c.hline(10,14,y-1,IRON[3])
    c.line(15,34,18,41,IRON[0]); c.vline(18,41,65,IRON[0])


def finish_drums(c: Canvas, _variant: int) -> None:
    for x,y,w,h in ((22,0,21,33),(2,5,23,29)):
        ellipse_ring(c,x+w//2,y+3,w/2-1,2,IRON[1])
        incise(c,[(x+3,y+3),(x+w-5,y+3)],IRON[4])
        # A dent is a curved crease with a bright raised lip; it bends around
        # the rim and interrupts a stamped strengthening rib.
        incise(c,[(x+w-7,y+8),(x+w-10,y+11),(x+w-9,y+15)],IRON[0],glint=RUST[3])
        incise(c,[(x+5,y+20),(x+9,y+21),(x+12,y+19)],RUST[1],glint=IRON[3])
        c.set(x+w-5,y+1,IRON[4]); c.set(x+w-4,y+2,IRON[0])
        c.set(x+5,y+h-5,RUST[3]); c.set(x+6,y+h-4,RUST[1])


def finish_fallen(c: Canvas, _variant: int) -> None:
    # Splinters align with the broken timber; longitudinal checks and exposed
    # growth rings sit on its snapped end, not across the porcelain hardware.
    incise(c,[(8,18),(18,17),(29,17),(39,15)],WOOD[0],glint=WOOD[5])
    incise(c,[(32,21),(58,18),(73,18)],WOOD[1],glint=WOOD[4])
    incise(c,[(79,12),(91,12),(104,10)],WOOD[0],glint=WOOD[4])
    for x,y in ((120,3),(123,11),(127,21)):
        c.hline(x+2,x+7,y-2,IRON[1]); c.vline(x+4,y-2,y+1,IRON[4]); c.set(x+6,y,IRON[3])
    c.line(11,21,5,25,WOOD[2]); c.line(7,18,1,16,WOOD[4])
    c.line(137,9,147,11,IRON[0]); c.line(147,11,148,17,IRON[0]); c.line(148,17,145,20,IRON[0])


def finish_traffic(c: Canvas, variant: int) -> None:
    polex=13 if not variant else 45
    end=43 if not variant else 19
    x,top=end-6,15 if not variant else 20
    # Concentric moulded lenses with radial ribs sit under separate hoods.
    for k,cy in enumerate((top+8,top+21,top+34)):
        pal=RED if k==0 else WOOD if k==1 else GREEN
        ellipse_ring(c,x+6,cy+1,3,3,pal[2])
        for dx in (-2,0,2):
            for dy in (-1,1):
                xx,yy=x+6+dx,cy+dy
                if (xx,yy) not in c.lights and c.solid(xx,yy): c.set(xx,yy,pal[1 if dx==2 else 3])
        c.hline(x+2,x+11,cy-5,IRON[3]); c.set(x+2,cy-4,IRON[1]); c.set(x+12,cy-3,IRON[0])
    # Hinges, sunshade fasteners, arm clamps and the controller cabinet.
    for y in (top+3,top+37):
        c.set(x,y,IRON[3]); c.set(x+12,y,IRON[0])
    for y in (12,31,82):
        c.hline(polex-3,polex+3,y,IRON[0]); bolt(c,polex,y)
    c.fill(polex-4,86,polex+5,101,IRON[0]); c.fill(polex-3,87,polex+4,100,IRON[2])
    c.vline(polex-3,87,100,IRON[3]); c.hline(polex-2,polex+2,90,IRON[1]); c.set(polex+2,95,IRON[0])
    for y in (89,98): c.hline(polex-4,polex-3,y,IRON[4])
    bolt(c,polex+3,88); bolt(c,polex+3,99)
    incise(c,[(polex+4,103),(polex+4,118),(polex+3,121)],IRON[0])


def finish_shrub(c: Canvas, variant: int) -> None:
    # Exposed internal twigs and paired lanceolate leaves establish a plant's
    # structure. The branching remains visible in the shadow between clumps.
    for points in ([(20,33),(17,25),(13,20)],[(20,32),(24,24),(28,19)],[(19,26),(20,18),(24,12)]):
        incise(c,points,WOOD[1],glint=WOOD[3])
    for x,y in ((8,24),(13,18),(18,13),(24,7+variant*2),(31,23),(23,28),(15,29)):
        if not c.solid(x,y): continue
        c.line(x-2,y,x,y-2,GREEN[4],2); c.line(x+1,y+1,x+3,y-1,GREEN[3],2)
        c.set(x,y,GREEN[1]); c.set(x+2,y,GREEN[5])
        c.set(x-1,y-1,GREEN[5]); c.set(x+1,y+2,GREEN[1])
    if variant==3:
        for x,y in ((8,28),(19,22),(29,29)):
            c.line(x,y,x+1,y-5,WOOD[2]); c.line(x+1,y-3,x+4,y-5,WOOD[3])


def finish_telegraph(c: Canvas, variant: int) -> None:
    for y,ext in ((16,18),(31,14)):
        for x in (20-ext+2,12,28,20+ext-2): insulator(c,x,y-7)
        # Wire saddles, a two-bolt splice plate and steel bracing at the arm.
        c.fill(17,y-1,23,y+3,IRON[1]); bolt(c,18,y+1); bolt(c,22,y+1)
        c.line(5 if y==16 else 9,y-8,35 if y==16 else 31,y-8,IRON[0])
    for points in ([(18,66),(17,79),(18,85)],[(21,91),(20,99)],
                   [(19,121),(18,136),(20,142)],[(23,149),(22,158),(23,169)]):
        incise(c,points,WOOD[0],glint=WOOD[4])
    ellipse_ring(c,20,96,2,5,WOOD[1]); c.set(20,96,WOOD[0])
    # An earth strap and a service ID plate are fixed with real mounting bands.
    c.vline(24,55,174,IRON[1]); c.set(24,73,RUST[2])
    for y in (64,105,151): c.hline(17,24,y,IRON[0]); bolt(c,18,y)


FINISHERS = {
    'cactus':finish_cactus, 'rock':finish_rock, 'fence':finish_fence, 'dead_tree':finish_tree,
    'grass':finish_grass, 'wagon_wheel':finish_wheel, 'skull':finish_skull, 'tombstone':finish_stone,
    'sign':finish_sign, 'hydrant':finish_hydrant, 'streetlight':finish_lamp,
    'trash':finish_trash, 'cone':finish_cone, 'tires':finish_tires,
    'sandbags':finish_bags, 'jersey':finish_jersey, 'pole':finish_pole,
    'litter':finish_litter, 'signal':finish_signal, 'drums':finish_drums,
    'fallen_pole':finish_fallen, 'traffic_light':finish_traffic,
    'shrub':finish_shrub, 'telegraph':finish_telegraph,
}


# Order, frame sizes and variants mirror src/game/props.c.
SPECS = {
    'cactus': (44, 100, 4, cactus), 'rock': (48, 24, 3, rock),
    'fence': (72, 40, 2, fence), 'dead_tree': (100, 150, 2, dead_tree),
    'grass': (24, 14, 4, grass), 'wagon_wheel': (44, 44, 2, wagon_wheel),
    'skull': (34, 18, 2, skull), 'tombstone': (28, 40, 4, tombstone),
    'sign': (36, 62, 2, sign), 'hydrant': (14, 24, 1, hydrant),
    'streetlight': (40, 150, 2, streetlight), 'trash': (26, 32, 2, trash),
    'cone': (16, 24, 1, cone), 'tires': (40, 34, 1, tires),
    'sandbags': (66, 28, 1, sandbags), 'jersey': (104, 27, 1, jersey),
    'pole': (44, 160, 1, pole), 'litter': (20, 6, 3, litter),
    'signal': (24, 110, 1, signal), 'drums': (48, 34, 1, drums),
    'fallen_pole': (150, 26, 1, fallen_pole), 'traffic_light': (60, 140, 2, traffic_light),
    'shrub': (40, 36, 4, shrub), 'telegraph': (40, 176, 2, telegraph),
}


def prop_images() -> dict:
    out = {}
    for name, (w, h, count, painter) in SPECS.items():
        frames = [painter(v) for v in range(count)]
        for variant, frame in enumerate(frames):
            if name in FINISHERS:
                FINISHERS[name](frame, variant)
        assert all((c.w, c.h) == (w, h) for c in frames), name
        out[f'sprites/props/{name}.png'] = sheet(frames)
    return out


def build_assets() -> dict:
    """Public entry point used by the coordinated scenery rebuild."""
    return prop_images()


def preview(path: Path, out: dict) -> None:
    """A contact sheet on a neutral ground, at the actual 2x game art scale."""
    cell_w, cell_h, cols, scale = 322, 202, 4, 2
    rows = (len(SPECS)+cols-1)//cols
    img = Image(cell_w*cols, cell_h*rows)
    for y in range(img.height):
        for x in range(img.width): img.set(x,y,(36,34,33,255))
    for i, (name, (_, h, _, _)) in enumerate(SPECS.items()):
        col, row = i % cols, i // cols
        label = Canvas(cell_w, 10)
        lettering(label, name.upper().replace('_', ' '), 4, 2, BONE[3])
        for y in range(10):
            for x in range(cell_w):
                if label.solid(x,y): img.set(col*cell_w+x,row*cell_h+y,(*label.get(x,y),255))
        art = out[f'sprites/props/{name}.png']
        # Fit only when a multi-frame sheet exceeds the cell; never change assets.
        s = min(scale, max(1,(cell_w-8)//art.width), max(1,(cell_h-15)//h))
        ox, oy = col*cell_w+4, (row+1)*cell_h-5-h*s
        for y in range(art.height):
            for x in range(art.width):
                p = art.get(x,y)
                if not p[3]: continue
                for dy in range(s):
                    for dx in range(s): img.set(ox+x*s+dx,oy+y*s+dy,(p[0],p[1],p[2],255))
    img.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path,
                        default=Path(__file__).resolve().parent.parent / 'assets')
    parser.add_argument('--preview', nargs='?', type=Path,
                        const=Path(__file__).resolve().parent.parent / 'build' / 'props-refactor-preview.png')
    args = parser.parse_args()
    out = prop_images()
    save_all(args.assets_dir, out, 'make_props')
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview, out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
