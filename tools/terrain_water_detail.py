"""Flowing water, wet banks and burning oil at their native terrain scale."""
from __future__ import annotations

import math

from landscape_kit import Canvas, hash2, hx, mix, sheet
from make_sprites import Image
from make_terrain import river_depth


def river() -> Image:
    frames = []
    for frame in range(4):
        c = Canvas(200, 22)
        for y in range(2, 22):
            for x in range(200):
                bank = min(x, 199 - x)
                if bank < 3 + (y < 8):
                    color = (61, 48, 35) if bank == 0 else (87, 71, 50)
                    if (x + y * 3) % 7 == 0:
                        color = (119, 101, 71)
                else:
                    depth = river_depth(x, 200)
                    shallow = (104, 126, 112) if y < 10 else (69, 91, 83)
                    deep = (40, 76, 89) if y < 9 else (26, 54, 69) if y < 16 else (20, 42, 55)
                    color = mix(shallow, deep, depth)
                    if y == 2:
                        color = (102, 143, 153)
                    elif y == 3:
                        color = (49, 88, 105)
                c.set(x, y, color)
        # Reflections stretch along the water, interrupted by the current.
        # Four art-pixel shifts over a 16-pixel period make a clean loop.
        for y in (6, 10, 15, 19):
            for slot in range(-1, 13):
                x0 = slot * 16 + frame * 4 + (y * 7 % 16)
                length = 5 + (slot * 7 + y) % 7
                for k in range(length):
                    x = x0 + k
                    if not 6 <= x < 194:
                        continue
                    yy = y + (1 if k > length * .7 else 0)
                    col = (81, 122, 134) if k < length - 2 else (48, 88, 104)
                    if river_depth(x, 200) < .6:
                        col = mix(col, (140, 156, 127), .35)
                    c.set(x, yy, col)
                    if k < 2 and yy > 6:
                        c.set(x, yy + 1, (24, 50, 65))
        for slot in range(4):
            start = 10 + slot * 48 + frame * 4
            for k in range(13):
                x = (start + k) % 192 + 4
                if x >= 194:
                    continue
                y = 3 + (1 if 3 <= k < 10 else 0)
                c.set(x, y, (168, 197, 194) if k < 7 else (102, 143, 153))
        # Ground is visible beneath the shallows: stones with a darker wet
        # underside, reeds caught against the bank and small eddies behind them.
        for side in range(2):
            for pebble in range(6):
                x = 5 + pebble * 4 % 18
                if side:
                    x = 199 - x
                y = 7 + pebble * 5 % 13
                c.hline(x - 1, x + 1, y, (101, 117, 99))
                c.hline(x - 1, x + 1, y + 1, (49, 73, 69))
                if pebble % 2 == 0:
                    c.hline(x + 2, x + 5, y, (123, 152, 149))
            for y in (6, 13, 19):
                x = 2 if side == 0 else 197
                c.set(x, y, (137, 120, 80))
                c.set(x + (1 if side == 0 else -1), y - 1, (80, 83, 55))
        frames.append(c)
    return sheet(frames)


def puddle(source: Image) -> Image:
    out = Image(source.width, source.height)
    for frame in range(4):
        for y in range(6):
            for x in range(64):
                old = source.get(frame * 64 + x, y)
                if not old[3]:
                    continue
                edge = (x == 0 or x == 63 or not source.get(frame * 64 + x - 1, y)[3]
                        or not source.get(frame * 64 + x + 1, y)[3])
                color = (72, 61, 46) if edge else (42, 73, 84) if y > 2 else (64, 101, 111)
                if not edge and y in (1, 4) and (x + frame * 3 + y * 5) % 29 < 12:
                    color = (113, 145, 143) if y == 1 else (72, 103, 111)
                if frame >= 2:
                    radius = 9 if frame == 2 else 19
                    dist = abs(x - 32)
                    if y in (1, 4) and radius - 3 <= dist <= radius:
                        color = (149, 174, 163)
                    elif y == 2 and radius - 1 <= dist <= radius + 1:
                        color = (87, 125, 132)
                out.set(frame * 64 + x, y, (*color, old[3]))
    return out


def burning_oil() -> Image:
    frames = []
    for frame in range(4):
        c = Canvas(32, 24)
        # A dark pool and irregular crust, with heat between the charred pieces.
        c.disc(16, 21.5, 14, hx(0x291a17), 2)
        for i in range(7):
            x = 3 + i * 4
            c.hline(x, x + 2, 23, hx(0x5d2a1b))
            c.set(x + 1, 22, hx(0xe36522) if (i + frame) % 3 else hx(0xffba43))
        # Each tongue bends into the next frame. Overlapping outer, inner and
        # hot-core shapes replace the old independent vertical strips.
        for i, (cx, height, width) in enumerate(((5, 10, 4), (10, 16, 6), (16, 21, 7), (23, 16, 6), (28, 10, 4))):
            sway = math.sin((frame + i) * math.pi / 2) * 2
            tip_y = 23 - height + ((frame + i) % 2)
            c.poly([(cx - width, 22), (cx - width + 1, 17),
                    (cx + sway - 1, tip_y + 5), (cx + sway + 2, tip_y),
                    (cx + sway + 1, tip_y + 7), (cx + width, 19), (cx + width, 23)], hx(0xb83e18))
            c.poly([(cx - width + 2, 23), (cx - width + 2, 19),
                    (cx + sway, tip_y + 5), (cx + 1, 17), (cx + width - 1, 23)], hx(0xee7924))
            c.poly([(cx - 2, 23), (cx - 1, 19), (cx + sway, tip_y + 10),
                    (cx + 2, 20), (cx + 3, 23)], hx(0xffc14a))
            if i in (1, 2, 3):
                c.disc(cx, 22, 2, hx(0xfff1b0), 1)
        # A detached ember follows a short upward arc and fades across the loop.
        for i in range(3):
            x, y = 7 + i * 9 + (frame + i) % 3, 12 - (frame + i * 2) % 9
            if not c.solid(x, y):
                c.set(x, y, hx(0xd8762c))
        frames.append(c)
    return sheet(frames)


def finish(name: str, source: Image) -> Image:
    if name == 'river':
        return river()
    if name == 'river_front':
        full = river()
        out = Image(800, 17)
        for y in range(17):
            for x in range(800):
                out.set(x, y, full.get(x, y + 2))
        return out
    if name == 'puddle':
        return puddle(source)
    if name == 'fire':
        return burning_oil()
    return source
