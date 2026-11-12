#!/usr/bin/env python3
"""Make the art of the second route: the neighbouring town and its army post.

Usage: tools/make_city.py [assets_dir]   (default: assets)

Writes:
  backgrounds/<theme>/{sky,far,hills_far,hills_near,ground[,fog]}.png for the
  five city themes (docs/LANDSCAPE.md): afueras (dawn on the outskirts),
  centro (downtown, a smoggy afternoon), vias (the rail yard at dusk),
  ciudad_noche (downtown by night) and base_militar (the army post, alarm red).
  sprites/props/<city prop>.png   Scenery on the ground line, daylight material
                                  colours (themes.c grades their light):
                                  hydrant, streetlight, trash, cone, tires,
                                  sandbags, jersey, pole, litter, signal, drums
  sprites/sparrow/sparrow.png     A sparrow, the crow's 8 frames of 16 x 12
  sprites/terrain/burner.png      A burning oil drum at her scale: flames, going
                                  over, burning on its side, burnt out (13 of 40 x 72)
  sprites/effects/flare.png       Its fire flaring up as it goes over (6 of 64 x 80)
  sprites/effects/paper.png       A newspaper blown down the street (4 of 14 x 14)
  sprites/terrain/siren_car.png   A patrol car with its light bar: dark, red,
                                  blue, smashed (4 frames of 136 x 52)
  sprites/terrain/car_wreck.png   The car that is a barricade: whole, smashed,
                                  burnt (3 of 136 x 46)
  sprites/terrain/vehicles.png    Vehicles to walk past: three sedans, an army
                                  jeep, an army truck (5 of 184 x 70)
  sprites/terrain/supply_truck.png  The town's supply point: an army truck,
                                  loaded and emptied (2 of 184 x 70)
  sprites/terrain/outpost.png     An army outpost to search: locked, then open
                                  with its floodlight on (2 of 168 x 92)
  sprites/terrain/city_fronts.png The town's fronts for walls, two storeys at
                                  her scale (4 of 240 x 192)
  sprites/terrain/train.png       A derailed freight train across the tracks,
                                  its two cars jammed together round a gap the
                                  wall's door fills (300 x 104)

The entry point uses make_landscape and make_props for current scenery and
refine_terrain for material detail on road objects. The older painters remain
source geometry, never the final exported backgrounds or prop sheets.
Deterministic; standard library only (tools/make_sprites.py writes the PNGs).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_sprites import Image, rgb  # noqa: E402
from make_terrain import FLAME, IRON, OUTLINE, SMOKE, Frame  # noqa: E402

CLEAR = (0, 0, 0, 0)


class Rng:
    def __init__(self, seed: int) -> None:
        self.state = seed & 0x7FFFFFFF

    def next(self) -> int:
        self.state = (self.state * 1103515245 + 12345) & 0x7FFFFFFF
        return self.state >> 8

    def range(self, lo: int, hi: int) -> int:
        """lo..hi inclusive."""
        return lo + self.next() % (hi - lo + 1)


# ---- Backgrounds ----------------------------------------------------------------

THEMES = {
    'afueras': {
        'hud': 0x221a22, 'bands': [0x3a2638, 0x522f44, 0x6e3a4c, 0x8c4652, 0xab5a52], 'strip': 0xc87050,
        'low': 0x2e2028, 'sun': (0xe8904a, 0xfcd890), 'sun_at': (182, 50, 9),
        'far': (0x5a3442, 0x6a3d4a, 0xa45a52), 'mid': (0x46283a, 0x36202c, 0x8a4a46),
        'near': (0x2e1e26, 0x261920, 0x1e1418),
        'line': (0x8a7a6e, 0x6e6258), 'road': (0x2a2426, 0x322a2c, 0x7a6a4a), 'fog': None,
    },
    'centro': {
        'hud': 0x1e1c1c, 'bands': [0x3a3030, 0x483834, 0x584238, 0x6a4c3c, 0x7e5840], 'strip': 0x9a6a46,
        'low': 0x2c2424, 'sun': (0xb08860, 0xd8b488), 'sun_at': (64, 30, 6),
        'far': (0x4a3a36, 0x56423c, 0x7e6048), 'mid': (0x3e302e, 0x2e2424, 0x6a5040),
        'near': (0x2a2020, 0x221a1a, 0x1a1414),
        'line': (0x8c8478, 0x6c6660), 'road': (0x262224, 0x2e2a2a, 0x8a847a), 'fog': None,
    },
    'vias': {
        'hud': 0x241a18, 'bands': [0x3c2228, 0x5a2a2c, 0x7a3430, 0xa04230, 0xc45a2e], 'strip': 0xe07a34,
        'low': 0x321c1e, 'sun': (0xf09040, 0xffd078), 'sun_at': (196, 54, 11),
        'far': (0x5e2e2e, 0x6e3634, 0xb05a3a), 'mid': (0x4c2628, 0x381e20, 0x9c4e34),
        'near': (0x2e1a1c, 0x26161a, 0x1c1012),
        'line': (0x9a8c80, 0x6a5e56), 'road': (0x3a302c, 0x2c2422, 0x4a3226), 'fog': None,
    },
    'ciudad_noche': {
        'hud': 0x0c0c16, 'bands': [0x12121e, 0x181828, 0x1e1e32, 0x262640, 0x30304c], 'strip': 0x45405e,
        'low': 0x16141f, 'sun': (0xa7a8a8, 0xd7d1bd), 'sun_at': (190, 34, 7),
        'far': (0x1e1e30, 0x24243a, 0x3a3a56), 'mid': (0x1a1a2a, 0x141420, 0x34344c),
        'near': (0x121220, 0x0e0e18, 0x0a0a12),
        'line': (0x6a6670, 0x4e4a56), 'road': (0x18161e, 0x1e1c24, 0x5e5a4e), 'fog': 0x3a3a52,
        'windows': 0x8a7040,
    },
    'base_militar': {
        'hud': 0x120a0c, 'bands': [0x1a0e12, 0x261216, 0x34161a, 0x48181a, 0x62201c], 'strip': 0x8a2c1e,
        'low': 0x1c0e10, 'sun': (0xa89480, 0xd0c4a8), 'sun_at': (60, 32, 6),
        'far': (0x2e1618, 0x3a1c1e, 0x5e2a26), 'mid': (0x2a1416, 0x1e0e10, 0x5a2824),
        'near': (0x1c0c0e, 0x160a0c, 0x10080a),
        'line': (0x7e7066, 0x5e544c), 'road': (0x26201e, 0x2e2826, 0x1a1614), 'fog': 0x4a2626,
        'windows': 0x8a3a24,
    },
}

SKY_W, SKY_H = 240, 117
TILE = 360          # Repeating layers: columns 0..358 tile, 359 copies 0


class Layer:
    """A cutout strip that repeats every PERIOD columns."""

    def __init__(self, w: int, h: int, period: int) -> None:
        self.img = Image(w, h)
        self.period = period

    def px(self, x: int, y: int, c: int) -> None:
        if 0 <= y < self.img.height:
            self.img.set(x % self.period, y, rgb(c))

    def get(self, x: int, y: int):
        return self.img.get(x % self.period, y)

    def fill(self, x0: int, y0: int, x1: int, y1: int, c: int) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def finish(self) -> Image:
        for y in range(self.img.height):
            for x in range(self.period, self.img.width):
                self.img.set(x, y, self.img.get(x % self.period, y))
        return self.img


def make_sky(t: dict) -> Image:
    """The HUD band, five flat bands down to the horizon strip, then the dark
    behind the bodies; the sun or moon over the right half."""
    img = Image(SKY_W, SKY_H)
    edges = [19, 27, 35, 42, 49, 55]          # Band tops; the strip from 55 to 60
    for y in range(SKY_H):
        if y < 19:
            c = t['hud']
        elif y < 55:
            k = max(i for i in range(5) if edges[i] <= y)
            c = t['bands'][k]
        elif y < 61:
            c = t['strip']
        else:
            c = t['low']
        for x in range(SKY_W):
            img.set(x, y, rgb(c))
    cx, cy, r = t['sun_at']
    rim, core = t['sun']
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d = math.hypot(x - cx, y - cy)
            if d <= r + .3 and y < 61:
                img.set(x, y, rgb(core if d < r - 1.6 else rim))
    if t is THEMES['ciudad_noche'] or t is THEMES['base_militar']:
        rng = Rng(77 if t is THEMES['ciudad_noche'] else 91)
        for _ in range(14):                     # A few stars, each two px
            x, y = rng.range(4, 230), rng.range(21, 44)
            if math.hypot(x - cx, y - cy) > r + 4:
                img.set(x, y, rgb(0x8a8aa0 if t is THEMES['ciudad_noche'] else 0x8a6a6a))
                img.set(x + 1, y, rgb(0x8a8aa0 if t is THEMES['ciudad_noche'] else 0x8a6a6a))
    return img


def building(l: Layer, x0: int, w: int, top: int, bottom: int, body: int, edge: int | None,
             roof: str = 'flat', windows: int | None = None, rng: Rng | None = None, wrows: int = 3) -> None:
    """A block: flat (or with a parapet, a pitched roof, a water tank) and its
    lit top edge; windows two px wide, in rows."""
    if roof == 'pitched':
        for i in range(w):
            ridge = top - min(i, w - 1 - i) // 2
            l.fill(x0 + i, ridge, x0 + i, bottom, body)
            if edge is not None:
                l.px(x0 + i, ridge, edge)
    else:
        l.fill(x0, top, x0 + w - 1, bottom, body)
        if edge is not None:
            l.fill(x0, top, x0 + w - 1, top, edge)
        if roof == 'parapet':
            l.fill(x0 + 1, top - 2, x0 + 2, top - 1, body)
            l.fill(x0 + w - 3, top - 2, x0 + w - 2, top - 1, body)
        elif roof == 'tank':
            tx = x0 + w // 3
            l.fill(tx, top - 6, tx + 4, top - 3, body)
            l.fill(tx, top - 2, tx, top - 1, body)
            l.fill(tx + 4, top - 2, tx + 4, top - 1, body)
            if edge is not None:
                l.fill(tx, top - 6, tx + 4, top - 6, edge)
        elif roof == 'antenna':
            ax = x0 + w // 2
            l.fill(ax, top - 7, ax, top - 1, body)
            l.fill(ax - 1, top - 4, ax + 1, top - 4, body)
    if windows is not None and rng is not None:
        for y in range(top + 3, bottom - 1, wrows):
            for x in range(x0 + 2, x0 + w - 3, 4):
                if rng.next() % 3 == 0:
                    l.fill(x, y, x + 1, y, windows)


def make_far(name: str, t: dict) -> Image:
    l = Layer(TILE, 24, 359)
    body, alt, edge = t['far']
    rng = Rng(hash_name(name) + 1)
    if name == 'afueras':                       # Hills far off, the town's low line, a water tower
        for x in range(359):
            h = 6 + round(3 * math.sin(x * math.tau / 359 * 2) + 2 * math.sin(x * math.tau / 359 * 5 + 1))
            l.fill(x, 23 - h, x, 23, alt)
            l.px(x, 23 - h, edge)
        x = 4
        while x < 340:
            w = rng.range(8, 18)
            h = rng.range(4, 9)
            building(l, x, w, 23 - h, 23, body, edge, 'pitched' if rng.next() % 3 == 0 else 'flat')
            x += w + rng.range(3, 14)
        tx = 120                                # Water tower
        l.fill(tx, 4, tx + 9, 9, body)
        l.fill(tx, 4, tx + 9, 4, edge)
        for lx in (tx + 1, tx + 8):
            l.fill(lx, 10, lx, 23, body)
        l.fill(tx + 1, 15, tx + 8, 15, body)
        sx = 250                                # Church steeple
        building(l, sx, 10, 11, 23, body, edge)
        l.fill(sx + 4, 4, sx + 5, 10, body)
        l.px(sx + 4, 3, edge)
    elif name in ('centro', 'ciudad_noche'):    # Towers
        x = 0
        lit = t.get('windows')
        while x < 352:
            w = rng.range(10, 22)
            h = rng.range(9, 21)
            roof = ['flat', 'antenna', 'tank', 'parapet'][rng.next() % 4]
            building(l, x, w, 23 - h, 23, body if rng.next() % 2 else alt, edge, roof,
                     lit if lit and 23 - h < 15 else None, rng, 3)
            x += w + rng.range(0, 4)
        if lit:                                 # Lit windows only above the heads (row 62 is 19 here)
            for y in range(17, 24):
                for x in range(359):
                    if l.get(x, y)[:3] == rgb(lit)[:3]:
                        l.px(x, y, body)
    elif name == 'vias':                        # Grain elevators, silos, a tank on legs
        for x in range(359):
            l.px(x, 23, alt)
        for x0, w, h in ((10, 14, 18), (26, 6, 12), (34, 6, 12), (42, 6, 12), (150, 12, 20), (164, 6, 14),
                         (172, 6, 14), (250, 18, 10), (300, 10, 16)):
            building(l, x0, w, 23 - h, 23, body, edge, 'flat')
            if w == 6:                          # Round silo tops
                l.px(x0, 23 - h, alt)
                l.px(x0 + 5, 23 - h, alt)
        for x0 in (12, 152):                    # Elevator heads
            l.fill(x0 + 3, 23 - 22, x0 + 7, 23 - 18, body)
            l.fill(x0 + 3, 1, x0 + 7, 1, edge)
        tx = 210
        l.fill(tx, 6, tx + 10, 11, body)
        l.fill(tx, 6, tx + 10, 6, edge)
        for lx in (tx + 1, tx + 9):
            l.fill(lx, 12, lx, 23, body)
        x = 60
        while x < 140:
            w = rng.range(10, 20)
            building(l, x, w, 23 - rng.range(3, 6), 23, alt, edge)
            x += w + rng.range(4, 10)
    else:                                       # base_militar: mountains, hangars, radar, control tower
        for x in range(359):
            h = 9 + round(4 * math.sin(x * math.tau / 359 * 3) + 2 * math.sin(x * math.tau / 359 * 7))
            l.fill(x, 23 - h, x, 23, alt)
            l.px(x, 23 - h, edge)
        for hx in (20, 200):                    # Hangars: low arcs
            for i in range(30):
                y = 23 - round(7 * math.sin(math.pi * i / 29))
                l.fill(hx + i, y, hx + i, 23, body)
                l.px(hx + i, y, edge)
        cx = 120                                # Control tower
        l.fill(cx + 2, 8, cx + 5, 23, body)
        l.fill(cx, 4, cx + 7, 7, body)
        l.fill(cx, 4, cx + 7, 4, edge)
        l.fill(cx + 1, 5, cx + 6, 5, t['windows'])
        rx = 290                                # Radar dish on its mast
        l.fill(rx + 4, 12, rx + 5, 23, body)
        for i in range(-6, 7):
            l.px(rx + 4 + i, 6 + (i * i) // 7, body)
            l.px(rx + 4 + i, 7 + (i * i) // 7, body)
        l.fill(rx + 4, 2, rx + 4, 8, body)
    return l.finish()


def hash_name(name: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate(name)) * 7919


def make_mid(name: str, t: dict) -> Image:
    """hills_far: 40 rows from 60 (rows 0-1 still over the heads)."""
    l = Layer(TILE, 40, 359)
    body, dark, crest = t['mid']
    rng = Rng(hash_name(name) + 2)
    for x in range(359):                        # A dark base under everything
        l.fill(x, 30, x, 39, dark)
    if name == 'vias':                          # Freight cars on a side track, a signal gantry
        for x in range(359):                    # The side track's bed
            l.fill(x, 34, x, 35, body)
        x = 2
        while x < 330:
            kind = rng.next() % 3
            w = rng.range(24, 32)
            if kind == 0:                       # A boxcar, its door's seam
                top = 18 + rng.range(0, 2)
                l.fill(x, top, x + w, 31, body)
                l.fill(x, top, x + w, top, crest)
                l.fill(x + w // 2, top + 2, x + w // 2, 30, dark)
            elif kind == 1:                     # A tank car: a rounded drum, a dome
                for i in range(w + 1):
                    edge = 2 if i in (0, w) else 1 if i in (1, w - 1) else 0
                    l.fill(x + i, 23 + edge, x + i, 30 - edge, body)
                    l.px(x + i, 23 + edge, crest)
                l.fill(x + w // 2 - 2, 21, x + w // 2 + 2, 22, body)
                l.fill(x + w // 2 - 2, 21, x + w // 2 + 2, 21, crest)
            else:                               # A hopper: sloping chutes under it
                l.fill(x, 21, x + w, 28, body)
                l.fill(x, 21, x + w, 21, crest)
                for i in range(w // 2):
                    l.fill(x + i, 29, x + i, 29 + min(3, i // 3), body)
                    l.fill(x + w - i, 29, x + w - i, 29 + min(3, i // 3), body)
            l.fill(x + 1, 31, x + w - 1, 31, dark)   # Frame, couplers, wheels
            for wx in (x + 3, x + 7, x + w - 9, x + w - 5):
                l.fill(wx, 32, wx + 2, 33, dark)
            x += w + rng.range(6, 16)
        gx = 180
        l.fill(gx, 6, gx + 1, 33, body)
        l.fill(gx + 40, 6, gx + 41, 33, body)
        l.fill(gx, 6, gx + 41, 8, body)
        l.fill(gx, 6, gx + 41, 6, crest)
        for i in range(6):
            l.fill(gx + 6 + i * 6, 9, gx + 7 + i * 6, 11, dark)
    elif name == 'base_militar':                # Bunkers, watchtowers, the perimeter fence
        for x in range(359):
            l.fill(x, 26, x, 29, dark)
        for bx in (30, 150, 260):
            for i in range(26):
                y = 20 + abs(i - 13) // 3
                l.fill(bx + i, y, bx + i, 29, body)
                l.px(bx + i, y, crest)
            l.fill(bx + 9, 24, bx + 16, 25, dark)
        for wx in (100, 220, 330):
            l.fill(wx, 4, wx + 9, 10, body)
            l.fill(wx - 1, 3, wx + 10, 3, crest)
            l.fill(wx + 1, 6, wx + 8, 7, dark)
            for lx in (wx + 1, wx + 8):
                l.fill(lx, 11, lx, 29, body)
            for k in range(11, 29, 6):
                l.fill(wx + 1, k, wx + 8, k, body)
        for x in range(0, 359, 9):              # Fence posts and its wire rows
            l.fill(x, 16, x, 29, body)
        for y in (17, 22):
            for x in range(359):
                l.px(x, y, body)
    else:                                       # Houses, shops and blocks
        x = 0
        lit = t.get('windows')
        while x < 352:
            w = rng.range(14, 30)
            h = rng.range(10, 26) if name != 'afueras' else rng.range(8, 16)
            roof = 'pitched' if name == 'afueras' and rng.next() % 2 else ['flat', 'parapet', 'tank'][rng.next() % 3]
            top = 34 - h
            building(l, x, w, top, 39, body, crest, roof)
            if lit:                             # A lit window now and then, above the heads only
                if rng.next() % 3 == 0 and top + 2 < 2:
                    l.fill(x + 3, top + 2, x + 4, top + 2, lit)
            for y in range(top + 3, 37, 4):     # Dark windows
                for wx in range(x + 3, x + w - 3, 5):
                    if rng.next() % 2:
                        l.fill(wx, y, wx + 1, y + 1, dark)
            x += w + rng.range(1, 8)
        if name == 'afueras':                   # Poles and wires between them
            for px_ in range(20, 359, 60):
                l.fill(px_, 4, px_, 33, body)
                l.fill(px_ - 3, 6, px_ + 3, 6, body)
            for px_ in range(20, 359, 60):
                for i in range(60):
                    l.px(px_ + i, 7 + round(3 * math.sin(math.pi * i / 60)), body)
    return l.finish()


def make_near(name: str, t: dict) -> Image:
    """hills_near: 38 rows from 80, down to the ground line; dark."""
    l = Layer(TILE, 38, 359)
    a, b, c = t['near']
    rng = Rng(hash_name(name) + 3)
    for x in range(359):
        l.fill(x, 30, x, 37, c)
    if name == 'vias':                          # Catenary posts with their arms and wires
        for x in range(359):
            l.fill(x, 26, x, 29, b)
        for px_ in range(10, 359, 72):
            l.fill(px_, 2, px_ + 1, 29, a)
            l.fill(px_ - 6, 4, px_ + 14, 5, a)
        for x in range(359):
            l.px(x, 8, a)
            l.px(x, 9 + round(2 * math.sin(math.pi * (x % 72) / 72)), a)
        x = 30
        while x < 340:                          # Piles of sleepers, a shed
            w = rng.range(12, 30)
            h = rng.range(3, 9)
            l.fill(x, 29 - h, x + w, 29, b)
            x += w + rng.range(20, 50)
    elif name == 'base_militar':                # Sandbag walls, tents, a barrier arm
        x = 0
        while x < 340:
            kind = rng.next() % 3
            if kind == 0:
                w = rng.range(20, 34)
                for i in range(w):
                    l.fill(x + i, 22 - (1 if (i // 4) % 2 else 0), x + i, 29, a)
            elif kind == 1:
                w = 28
                for i in range(w + 1):
                    y = 12 + abs(i - 14) * 2 // 3
                    l.fill(x + i, y, x + i, 29, b)
                l.fill(x + 12, 20, x + 16, 29, c)
            else:
                w = 24
                l.fill(x, 14, x + 2, 29, a)
                for i in range(w):
                    l.px(x + 2 + i, 16 - i // 6, a)
                    l.px(x + 2 + i, 17 - i // 6, a)
            x += w + rng.range(10, 30)
    else:                                       # Close buildings, awnings, lamp posts, fences
        x = 0
        while x < 352:
            w = rng.range(24, 44)
            top = rng.range(2, 14) if name != 'afueras' else rng.range(10, 20)
            l.fill(x, top, x + w, 29, a if rng.next() % 2 else b)
            if name in ('centro', 'ciudad_noche'):
                l.fill(x - 1, 18, x + w + 1, 19, b)        # An awning
                if rng.next() % 2:                          # A fire escape's zigzag
                    for i in range(top + 2, 17):
                        l.px(x + 3 + (i % 8 if (i // 8) % 2 == 0 else 7 - i % 8), i, c)
            else:
                for i in range(w + 1):                      # A pitched roof
                    l.px(x + i, top - min(i, w - i) // 3, a)
                    l.fill(x + i, top - min(i, w - i) // 3, x + i, top, a)
            gap = rng.range(6, 24)
            if gap > 12:                                    # A lamp post in the gap
                lx = x + w + gap // 2
                l.fill(lx, 4, lx, 29, a)
                l.fill(lx, 4, lx + 4, 4, a)
            x += w + gap
        if name == 'afueras':                   # A billboard on legs
            l.fill(200, 2, 236, 12, b)
            l.fill(206, 13, 207, 29, b)
            l.fill(229, 13, 230, 29, b)
    return l.finish()


def make_ground(name: str, t: dict) -> Image:
    """120 x 18, opaque: the 2-row line she walks on, then the road."""
    img = Image(120, 18)
    period = 119
    l1, l2 = t['line']
    r1, r2, mark = t['road']
    grid = [[0] * period for _ in range(18)]
    for x in range(period):
        grid[0][x], grid[1][x] = l1, l2
        for y in range(2, 18):
            grid[y][x] = r1 if (y < 10) else r2
    rng = Rng(hash_name(name) + 4)
    if name == 'vias':
        for x in range(period):
            grid[2][x] = 0x4a423e                    # The rail's web under its head
        for x0 in range(0, period, 17):              # Sleepers
            for y in range(3, 7):
                for x in range(x0, x0 + 9):
                    grid[y][x % period] = mark
        for _ in range(60):                          # Ballast stones, 2x1
            x, y = rng.range(0, period - 1), rng.range(7, 16)
            grid[y][x] = grid[y][(x + 1) % period] = 0x4a403a
    elif name == 'base_militar':
        for x0 in range(0, period, 40):              # Slabs and their joints
            for y in range(2, 18):
                grid[y][x0] = mark
        for x in range(period):
            grid[9][x] = mark
        for x0 in (12, 70):                          # A painted stripe, worn
            for x in range(x0, x0 + 14):
                grid[13][x] = grid[14][x] = 0x5a4a2a
    else:
        for x0 in range(0, period, 40):              # The lane's dashes
            for x in range(x0 + 6, x0 + 24):
                grid[11][x % period] = mark
        for _ in range(8):                           # Patches and cracks
            x, y, w = rng.range(0, period - 1), rng.range(4, 16), rng.range(4, 12)
            for i in range(w):
                if grid[y][(x + i) % period] != mark:
                    grid[y][(x + i) % period] = r2 if y < 10 else r1
        if name == 'ciudad_noche':                   # Wet: a lamp's sheen on the road
            for x0 in (20, 80):
                for x in range(x0, x0 + 10):
                    grid[5][x] = grid[6][x] = 0x2c2a3a
    for y in range(18):
        for x in range(120):
            img.set(x, y, rgb(grid[y][x % period]))
    return img


def make_fog(t: dict) -> Image:
    img = Image(240, 24)
    rng = Rng(5)
    c = t['fog']
    period = 239
    for i in range(9):
        cx, cy = rng.range(0, period), rng.range(8, 18)
        rx, ry = rng.range(18, 40), rng.range(3, 6)
        for y in range(cy - ry, cy + ry + 1):
            for dx in range(-rx, rx + 1):
                d = (dx / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1 and 0 <= y < 24:
                    x = (cx + dx) % period
                    alpha = 80 if d < .4 else 40
                    old = img.get(x, y)[3]
                    img.set(x, y, rgb(c, max(alpha, old)))
    for y in range(24):
        img.set(239, y, img.get(0, y))
    return img


# ---- Props: the six sunset colours (themes.c swaps them) -------------------------

DARK, MID, C_MID, F_LIT, C_LIT, LIT = 0x312224, 0x4f2b2a, 0x45332a, 0x5e302a, 0x6d3d1f, 0x5a4334


class Sheet:
    def __init__(self, w: int, h: int, n: int) -> None:
        self.img, self.w, self.h = Image(w * n, h), w, h
        self.f = 0

    def px(self, x: int, y: int, c: int) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img.set(self.f * self.w + x, y, rgb(c))

    def fill(self, x0: int, y0: int, x1: int, y1: int, c: int) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def disc(self, cx: float, cy: float, r: float, c: int) -> None:
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.px(x, y, c)


# Sized against her (56 px, 1.7 m): a hydrant to her knee, a bin to her waist,
# a jersey barrier to her hip, lamp posts and poles well over her head.

def prop_hydrant() -> Image:
    s = Sheet(14, 24, 1)
    s.fill(4, 5, 9, 23, DARK)
    s.fill(3, 3, 10, 5, DARK)
    s.fill(5, 1, 8, 2, DARK)
    s.fill(1, 10, 12, 13, DARK)                           # Side outlets
    s.fill(4, 5, 4, 22, LIT)
    s.fill(5, 3, 8, 3, LIT)
    s.fill(6, 11, 7, 12, MID)
    s.fill(2, 22, 11, 23, DARK)
    return s.img


def prop_streetlight() -> Image:
    """A street light: a tall post, its arm over the road, the lamp's hood
    (and one whose arm hangs broken)."""
    s = Sheet(40, 150, 2)
    for v in range(2):
        s.f = v
        s.fill(6, 8, 8, 149, DARK)
        s.fill(4, 140, 10, 149, DARK)                     # Its base
        s.fill(6, 8, 6, 139, LIT)
        for y in (60, 100):
            s.fill(5, y, 9, y + 1, MID)                   # Bands
        if v == 0:
            for i in range(26):                           # The arm, curving out
                s.fill(8 + i, 8 - min(4, i // 3), 8 + i, 9 - min(4, i // 3), DARK)
            s.fill(28, 5, 38, 8, DARK)                    # Hood
            s.fill(29, 9, 37, 9, C_LIT)
        else:
            for i in range(22):                           # Hanging by its cable
                s.fill(8 + i // 3, 10 + i, 9 + i // 3, 10 + i, DARK)
            s.fill(12, 32, 20, 36, DARK)
    return s.img


def prop_trash() -> Image:
    """A dustbin with its lid ajar; bags heaped up."""
    s = Sheet(26, 32, 2)
    s.f = 0
    s.fill(5, 8, 20, 31, DARK)
    s.fill(5, 8, 6, 31, LIT)
    for y in (14, 22):
        s.fill(5, y, 20, y, MID)
    for x in range(8, 20, 3):
        s.fill(x, 9, x, 30, MID)
    s.fill(2, 3, 19, 6, DARK)                             # Lid, tipped
    s.fill(2, 3, 14, 3, LIT)
    s.fill(9, 1, 12, 2, DARK)
    s.f = 1
    s.disc(8, 23, 8, DARK)
    s.disc(18, 25, 6.5, MID)
    s.disc(13, 14, 6, DARK)
    s.fill(12, 6, 14, 8, DARK)                            # Their knots
    s.fill(7, 13, 8, 15, DARK)
    s.fill(11, 10, 13, 10, LIT)
    s.fill(4, 18, 6, 18, LIT)
    return s.img


def prop_cone() -> Image:
    s = Sheet(16, 24, 1)
    for y in range(1, 21):
        half = 1 + y * 5 // 20
        s.fill(8 - half, y, 7 + half, y, F_LIT if y in (7, 8, 9, 14, 15) else DARK)
    s.fill(0, 21, 15, 23, DARK)
    s.fill(0, 21, 15, 21, MID)
    return s.img


def prop_tires() -> Image:
    s = Sheet(40, 34, 1)
    for i, (x, y) in enumerate(((10, 24), (29, 24), (19, 10))):
        s.disc(x, y, 9.2, DARK)
        s.disc(x, y, 6.0, MID if i < 2 else LIT)
        s.disc(x, y, 3.4, DARK)
    return s.img


def prop_sandbags() -> Image:
    s = Sheet(66, 28, 1)
    for row, (y, n) in enumerate(((21, 5), (14, 4), (7, 3), (0, 2))):
        off = row * 6
        for i in range(n):
            x0 = 1 + off + i * 13
            s.fill(x0 + 1, y, x0 + 11, y + 6, DARK)
            s.fill(x0, y + 1, x0 + 12, y + 5, DARK)
            s.fill(x0 + 2, y, x0 + 10, y, LIT if row >= 2 or i == 0 else MID)
            s.fill(x0 + 6, y + 2, x0 + 6, y + 4, MID)
    return s.img


def prop_jersey() -> Image:
    """Concrete road barriers end to end, to her hip."""
    s = Sheet(104, 27, 1)
    for x0 in (0, 52):
        for y in range(2, 27):
            inset = 9 if y < 14 else 9 - (y - 14) * 9 // 12
            s.fill(x0 + max(0, inset), y, x0 + 50 - max(0, inset), y, DARK)
        s.fill(x0 + 9, 2, x0 + 41, 2, LIT)
        s.fill(x0 + 10, 3, x0 + 10, 13, LIT)
        s.fill(x0 + 14, 18, x0 + 36, 19, MID)
        s.fill(x0 + 20, 8, x0 + 30, 10, MID)              # A lifting slot
    return s.img


def prop_pole() -> Image:
    """A wooden utility pole: crossarms with their insulators, a transformer,
    a lamp on a bracket."""
    s = Sheet(44, 160, 1)
    s.fill(20, 2, 23, 159, DARK)
    s.fill(20, 2, 20, 158, LIT)
    for y in (10, 22):
        s.fill(4, y, 39, y + 2, DARK)
        s.fill(4, y, 39, y, MID)
        for x in (5, 13, 30, 38):
            s.fill(x, y - 3, x + 1, y - 1, MID)
    s.fill(24, 34, 33, 52, DARK)                          # Transformer
    s.fill(24, 34, 24, 52, MID)
    s.fill(26, 31, 27, 33, MID)
    s.fill(30, 31, 31, 33, MID)
    for i in range(10):                                   # A guy wire
        s.px(19 - i, 100 + i * 6, MID)
    return s.img


def prop_fallen_pole() -> Image:
    """A pole down across the verge: snapped at its foot, its crossarm
    splintered, wires trailing."""
    s = Sheet(150, 26, 1)
    s.fill(2, 12, 7, 25, DARK)                            # The stump
    s.fill(2, 12, 2, 24, LIT)
    for x in range(8, 146):
        y = 20 - (x - 8) * 6 // 138
        s.fill(x, y, x, y + 3, DARK)
        s.px(x, y, LIT if x % 9 else MID)
    for i in range(22):                                   # Crossarm, askew
        s.fill(118 + i // 3, 4 + i, 120 + i // 3, 4 + i, DARK)
    s.fill(117, 3, 121, 4, MID)
    for x in range(60, 118, 2):                           # Wires on the ground
        s.px(x, 24 + (x // 6) % 2, MID)
        s.px(x + 20, 23 + (x // 8) % 3, DARK)
    return s.img


def prop_traffic_light() -> Image:
    """A traffic light: a post, an arm over the road, the head hanging from
    it (dead: one lens still faintly red) and a walk signal on the post."""
    s = Sheet(60, 140, 2)
    for v in range(2):
        s.f = v
        s.fill(6, 10, 9, 139, DARK)
        s.fill(4, 130, 11, 139, DARK)
        s.fill(6, 10, 6, 129, LIT)
        s.fill(9, 10, 52, 12, DARK)                       # The arm
        s.fill(9, 10, 52, 10, MID)
        for i in range(12):
            s.px(10 + i, 24 - i, DARK)                    # Its brace
        hx = 42 if v == 0 else 38
        tilt = 0 if v == 0 else 3
        s.fill(hx, 13, hx + 9, 40, DARK)                  # The head, three lenses under visors
        s.fill(hx - 1, 13, hx + 10, 14, MID)
        for k, y in enumerate((17, 25, 33)):
            s.disc(hx + 4.5 + (tilt if k == 2 else 0), y + 2, 2.6, 0x7a2018 if k == 0 and v == 0 else C_MID)
            s.fill(hx + 1, y - 1, hx + 8, y - 1, MID)
        s.fill(10, 70, 16, 82, DARK)                      # Walk signal
        s.fill(11, 72, 15, 75, MID)
        s.fill(1, 96, 5, 104, DARK)                       # A button box
    return s.img


def prop_litter() -> Image:
    """What the city leaves on the ground instead of grass (3)."""
    s = Sheet(20, 6, 3)
    s.f = 0
    s.fill(2, 4, 7, 5, MID)
    s.fill(11, 3, 13, 5, DARK)
    s.fill(15, 5, 18, 5, LIT)
    s.f = 1
    s.fill(3, 5, 9, 5, DARK)
    s.fill(4, 4, 6, 4, DARK)
    s.fill(13, 4, 15, 5, F_LIT)
    s.f = 2
    s.fill(1, 3, 4, 5, DARK)
    s.fill(8, 5, 16, 5, MID)
    s.fill(10, 4, 12, 4, MID)
    return s.img


def prop_signal() -> Image:
    """A railway signal: mast, a hooded head with two lamps, a ladder, its relay box."""
    s = Sheet(24, 110, 1)
    s.fill(10, 16, 12, 109, DARK)
    s.fill(10, 16, 10, 108, LIT)
    s.fill(5, 1, 17, 20, DARK)
    s.fill(4, 1, 18, 2, MID)
    s.disc(11, 7, 3.2, C_LIT)
    s.disc(11, 15, 3.0, MID)
    for y in range(28, 106, 7):
        s.fill(13, y, 18, y, MID)
    s.fill(18, 26, 18, 106, DARK)
    s.fill(2, 88, 9, 104, DARK)
    s.fill(2, 88, 9, 88, LIT)
    s.fill(6, 106, 16, 109, DARK)
    return s.img


def prop_drums() -> Image:
    s = Sheet(48, 34, 1)
    for x0, top in ((1, 3), (25, 6)):
        s.fill(x0, top, x0 + 20, 33, DARK)
        s.fill(x0, top, x0 + 20, top, LIT)
        s.fill(x0, top, x0 + 1, 33, LIT)
        for y in (top + 9, top + 18):
            s.fill(x0, y, x0 + 20, y + 1, MID)
        s.fill(x0 + 13, top + 2, x0 + 15, top + 3, MID)   # Bung
    return s.img


PROPS = {
    'hydrant': prop_hydrant, 'streetlight': prop_streetlight, 'trash': prop_trash,
    'cone': prop_cone, 'tires': prop_tires, 'sandbags': prop_sandbags, 'jersey': prop_jersey,
    'pole': prop_pole, 'litter': prop_litter, 'signal': prop_signal, 'drums': prop_drums,
    'fallen_pole': prop_fallen_pole, 'traffic_light': prop_traffic_light,
}


# ---- Things on the road: outlined, lively (like tools/make_terrain.py) -----------

def make_sparrow() -> Image:
    """A house sparrow, the crow's frames (pecking 0-1, wingbeat 2-5, falling,
    dead), smaller in its 16 x 12: brown back streaked dark, grey crown,
    pale belly, a short dark beak."""
    w, h = 16, 12
    img = Image(w * 8, h)
    back = [rgb(0x4a3020), rgb(0x7a5432), rgb(0xa47a4a)]
    belly = rgb(0xc8b89a)
    crown = rgb(0x6a6660)
    beak = rgb(0x2a2420)
    for frame in range(8):
        f = Frame(img, frame * w, w)
        if frame >= 6:
            y0 = 5 if frame == 6 else 9
            f.fill(5, y0, 10, y0 + 1, back[1])
            f.fill(6, y0 + 1, 9, y0 + 1, belly)
            f.px(11, y0 + 1, crown)
            f.px(12, y0 + 1, beak)
            f.px(7, y0 - 1, beak)
            f.px(9, y0 - 1, beak)
            if frame == 7:
                f.px(3, 11, back[2])
                f.px(13, 11, back[0])
            f.outline()
            continue
        flying = frame >= 2
        by = 7 if not flying else 6
        f.fill(6, by, 10, by + 2, back[1])                # Body
        f.fill(7, by + 2, 10, by + 2, belly)
        f.px(7, by, back[2])
        f.px(9, by, back[0])
        f.fill(3, by + 1, 5, by + 1, back[0])             # Tail
        hy = by - 1 if frame != 1 else by + 1
        f.fill(10, hy, 11, hy + 1, back[1])               # Head
        f.px(10, hy, crown)
        f.px(11, hy, crown)
        f.px(11, hy + 1, belly)
        f.px(12, hy + 1, beak)
        if not flying:
            f.px(8, by + 3, beak)
            f.px(8, by + 4, beak)
        else:
            beat = frame - 2
            tip = {0: (7, 1), 1: (4, by - 1), 2: (8, 11), 3: (4, by - 1)}[beat]
            for bx in (7, 8, 9):
                steps = max(abs(tip[0] - bx), abs(tip[1] - by), 1)
                for i in range(steps + 1):
                    f.px(bx + round((tip[0] - bx) * i / steps), by + round((tip[1] - by) * i / steps),
                         back[2] if bx == 7 else back[0])
        f.outline()
    return img


DRUM = [rgb(0x22262a), rgb(0x3a4046), rgb(0x56606a), rgb(0x7a8690)]
RUST = [rgb(0x4a2416), rgb(0x7a3c1e), rgb(0x9a5428)]
STONE = [rgb(0x3a3838), rgb(0x5a5654), rgb(0x807a74), rgb(0x9c968e)]
EMBER = [rgb(0x7a2a10), rgb(0xd0581a), rgb(0xffa040)]


def drum_fire(f: Frame, frame: int, base: int, cx: int, stones: bool) -> None:
    """A burning oil drum standing on the ground at row base, at a person's
    scale (to her waist): a steel drum with two ribs, rust, a flared rim,
    glowing holes punched round its foot and a tall ragged flame out of it;
    flat stones round its foot."""
    top = base - 29
    x0, x1 = cx - 11, cx + 10
    state = 911 + (frame % 6) * 613
    for x in range(cx - 9, cx + 9):                       # The flame
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        lean = (frame % 3) - 1
        tall = 16 + (state >> 16) % 16 - abs(x - cx) * 3 // 2
        tall = max(3, tall)
        for y in range(top, top - tall, -1):
            k = (top - y) / tall
            c = 'W' if k < .3 and abs(x - cx) < 5 else 'Y' if k < .55 else 'o' if k < .82 else 'r'
            f.px(x + (lean if k > .5 else 0), y, FLAME[c])
    for i in range(5):                                    # Sparks
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        f.px(cx - 8 + (state >> 16) % 17, top - 18 - (state >> 8) % 12, FLAME['Y'] if i % 2 else FLAME['o'])
    drum_body(f, x0, top, x1, base, frame)
    f.fill(x0 - 1, top - 1, x1 + 1, top, DRUM[3])         # Flared rim, the fire inside it
    f.fill(x0, top, x1, top, EMBER[2 if frame % 2 else 1])
    for i, hx in enumerate(range(x0 + 2, x1 - 1, 3)):     # Glowing holes at the foot
        f.px(hx, base - 4 - (i % 2) * 2, FLAME['Y'] if (i + frame) % 3 else FLAME['o'])
    if stones:
        for i, sx in enumerate((cx - 17, cx + 11, cx - 5)):
            f.box(sx, base - 2 + (i == 2), sx + 6, base, STONE[1:])


def drum_body(f: Frame, x0: int, top: int, x1: int, base: int, frame: int) -> None:
    for y in range(top, base + 1):                        # Lit from the left, sooty near its mouth
        for x in range(x0, x1 + 1):
            u = (x - x0) / (x1 - x0)
            c = DRUM[3] if u < .16 else DRUM[2] if u < .45 else DRUM[1] if u < .8 else DRUM[0]
            if (x * 7 + y * 3) % 13 == 0 or (y > base - 7 and (x + y) % 4 == 0):
                c = RUST[1] if u < .5 else RUST[0]
            if y < top + 4 and (x + y) % 2:
                c = DRUM[0]
            f.px(x, y, c)
    for y in (top + 9, top + 19):                         # Ribs
        f.fill(x0, y, x1, y, DRUM[3])
        f.fill(x0, y + 1, x1, y + 1, DRUM[0])


BURNER_W, BURNER_H = 40, 72


def make_burner() -> Image:
    """A burning drum on the road (13 frames of 40 x 72): 0-5 burning; 6-7
    going over, its fire flaring out of its mouth; 8-11 lying on its side,
    flames still licking out; 12 burnt out."""
    w, h = BURNER_W, BURNER_H
    img = Image(w * 13, h)
    b = h - 1
    for frame in range(6):
        f = Frame(img, frame * w, w)
        drum_fire(f, frame, b, 20, False)
        f.outline()
    for k in range(2):                                    # Tipping to the right
        f = Frame(img, (6 + k) * w, w)
        lean = 6 + k * 8
        for y in range(b - 29, b + 1):
            shift = (b - y) * lean // 29
            for x in range(9, 31):
                u = (x - 9) / 21
                c = DRUM[3] if u < .16 else DRUM[2] if u < .45 else DRUM[1] if u < .8 else DRUM[0]
                if (x * 7 + y * 3) % 13 == 0:
                    c = RUST[1]
                f.px(x + shift, y - k * 3, c)
        state = 77 + k * 31
        for i in range(60 + k * 30):                      # The fire thrown out of it
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            dx, dy = (state >> 16) % (14 + k * 8), (state >> 8) % (22 + k * 6)
            c = 'W' if dx + dy < 10 else 'Y' if dx + dy < 20 else 'o' if dx + dy < 30 else 'r'
            f.px(18 + lean + dx - dy // 4, b - 30 - k * 3 - dy + dx // 2, FLAME[c])
        f.outline()
    for k in range(5):                                    # On its side: burning, then dead
        f = Frame(img, (8 + k) * w, w)
        for y in range(b - 21, b + 1):
            for x in range(2, 32):
                v = (y - (b - 21)) / 21
                c = DRUM[3] if v < .15 else DRUM[2] if v < .45 else DRUM[1] if v < .8 else DRUM[0]
                if (x * 5 + y) % 11 == 0:
                    c = RUST[1]
                if k == 4 and (x + y) % 3 == 0:
                    c = DRUM[0]
                f.px(x, y, c)
        for x in (11, 21):
            f.fill(x, b - 21, x, b, DRUM[3])
            f.fill(x + 1, b - 21, x + 1, b, DRUM[0])
        f.fill(32, b - 20, 32, b - 1, EMBER[0] if k == 4 else EMBER[2])
        if k < 4:                                         # Flames out of its mouth, along the road
            state = 300 + k * 97
            for x in range(33, 40):
                state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                tall = 6 + (state >> 16) % 12 - (x - 33)
                for y in range(b, b - max(2, tall), -1):
                    kk = (b - y) / max(2, tall)
                    f.px(x, y, FLAME['Y' if kk < .4 else 'o' if kk < .75 else 'r'])
            for x in range(6, 30, 5):                     # And off the oil on its skin
                state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                for y in range(b - 22, b - 24 - (state >> 16) % 6, -1):
                    f.px(x + (y % 2), y, FLAME['o' if y % 2 else 'Y'])
        else:
            f.px(34, b - 12, SMOKE[1])
            f.px(35, b - 16, SMOKE[2])
        f.outline()
    return img


def make_flare() -> Image:
    """A drum's fire flaring up as it goes over (6 frames of 64 x 80): a
    ball of flame swelling, rolling up and breaking into smoke."""
    w, h = 64, 80
    img = Image(w * 6, h)
    for frame in range(6):
        f = Frame(img, frame * w, w)
        cx, cy = 32, h - 20 - frame * 7
        r = [10, 18, 24, 26, 24, 20][frame]
        state = 5 + frame * 131
        for y in range(cy - r - 4, min(h, cy + r + 4)):
            for x in range(cx - r - 4, cx + r + 4):
                state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                d = math.hypot(x - cx, (y - cy) * 1.1) + ((state >> 16) % 5 - 2)
                if d > r:
                    continue
                k = d / r
                if frame < 4:
                    c = FLAME['W'] if k < .3 - frame * .07 else FLAME['Y'] if k < .6 - frame * .08 else \
                        FLAME['o'] if k < .85 else FLAME['r']
                else:
                    c = FLAME['o'] if k < .25 and frame == 4 else SMOKE[1] if k < .6 else SMOKE[0]
                    if (x + y + frame) % 3 == 0:
                        continue
                f.px(x, y, c)
        if frame < 3:                                     # A lick still on the ground
            for x in range(cx - 14, cx + 14):
                f.fill(x, h - 3 - (x * 7 + frame) % 4, x, h - 1, FLAME['Y' if (x + frame) % 2 else 'o'])
    return img


HYDRANT_W, HYDRANT_H = 20, 28
JET_W, JET_H = 72, 120
WATER = [rgb(0x24485e), rgb(0x4a86a0), rgb(0x8cc4d4), rgb(0xd8f0f4)]


def make_hydrant() -> Image:
    """A fire hydrant on the pavement, to her knee (2 frames of 20 x 28):
    whole, red with its caps and chain; burst, its top blown off, its stub
    leaking."""
    red = [rgb(0x4a1612), rgb(0x74231a), rgb(0x9c3424), rgb(0xc24e32), rgb(0xe07a50)]
    img = Image(HYDRANT_W * 2, HYDRANT_H)
    b = HYDRANT_H - 1
    for frame in range(2):
        f = Frame(img, frame * HYDRANT_W, HYDRANT_W)
        top = 6 if frame == 0 else 15
        for y in range(top, b - 1):
            for x in range(6, 14):
                f.px(x, y, red[4] if x == 6 else red[3] if x < 9 else red[2] if x < 12 else red[1])
        f.fill(4, b - 2, 15, b, red[1])                   # Its foot flange, bolts
        f.fill(4, b - 2, 15, b - 2, red[3])
        for x in (5, 9, 14):
            f.px(x, b - 1, IRON[4])
        if frame == 0:
            f.fill(5, 4, 14, 6, red[2])                   # Bonnet and its nut
            f.fill(5, 4, 14, 4, red[4])
            f.fill(8, 1, 11, 3, IRON[3])
            f.fill(2, 12, 5, 17, red[2])                  # Side caps
            f.fill(2, 12, 5, 12, red[4])
            f.fill(14, 12, 17, 17, red[1])
            f.fill(8, 12, 11, 17, IRON[2])                # The big outlet's cap
            f.fill(8, 12, 11, 12, IRON[4])
            for i in range(4):
                f.px(12 + i % 2, 18 + i, IRON[3])         # Chain
        else:
            for x in range(6, 14):                        # Torn metal, water welling
                f.px(x, top - 1 - (x * 5) % 3, red[1])
            f.fill(7, top, 12, top + 1, WATER[2])
            f.fill(3, b, 16, b, WATER[1])
        f.outline()
    return img


def make_hydrant_jet() -> Image:
    """A burst hydrant's water (4 frames of 72 x 120): a column shooting up
    out of it, fanning out at the top and falling back in sheets either side."""
    img = Image(JET_W * 4, JET_H)
    for frame in range(4):
        f = Frame(img, frame * JET_W, JET_W)
        cx, b = JET_W // 2, JET_H - 1
        state = 41 + frame * 211
        for y in range(b - 14, 12, -1):                   # The column, widening
            k = (b - 14 - y) / (b - 26)
            half = 3 + int(k * 5)
            for x in range(cx - half, cx + half + 1):
                state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                edge = abs(x - cx) / (half + .01)
                c = WATER[3] if edge < .35 else WATER[2] if edge < .75 else WATER[1]
                if (state >> 16) % 9 == 0:
                    c = WATER[3]
                if ((y + frame * 3) // 4 + x) % 7 == 0:
                    c = WATER[1]                          # Streaks running up it
                f.px(x, y, c)
        for side in (-1, 1):                              # The crown falling away
            for i in range(60):
                state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                t = i / 59
                x = cx + side * int(6 + t * 26 + ((state >> 16) % 5 - 2))
                y = int(14 - 10 * math.sin(math.pi * min(1.0, t * 1.4)) + t * t * 96) + (state >> 8) % 4
                if 0 <= y < JET_H:
                    f.px(x, y, WATER[3] if i % 3 == frame % 3 else WATER[2])
                    f.px(x, y + 1, WATER[1])
        for i in range(26):                               # Spray
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            f.px(cx - 30 + (state >> 16) % 61, 4 + (state >> 8) % 100, WATER[3] if i % 2 else WATER[2])
        for x in range(cx - 30, cx + 31):                 # Water spreading on the road
            if (x + frame) % 3:
                f.px(x, b, WATER[1 + (x + frame) % 2])
    return img


TAG = {
    'B': ['##. ', '#.# ', '##. ', '#.# ', '#.# ', '##. '], 'U': ['#.# ', '#.# ', '#.# ', '#.# ', '#.# ', '.## '],
    'I': ['### ', '.#. ', '.#. ', '.#. ', '.#. ', '### '], 'T': ['### ', '.#. ', '.#. ', '.#. ', '.#. ', '.#. '],
    'R': ['##. ', '#.# ', '##. ', '#.# ', '#.# ', '#.# '], 'E': ['### ', '#.. ', '##. ', '#.. ', '#.. ', '### '],
    'S': ['.## ', '#.. ', '.#. ', '..# ', '..# ', '##. '],
}


def graffiti(f: Frame, x: int, y: int, paint, scale: int = 2, mark: bool = True) -> None:
    """The looters' tag sprayed on a wall: BUITRES, dripping, and their mark,
    a vulture's head (a hooked beak under a bald crown) over three claw
    slashes. Who they are is for the next route."""
    cx = x
    for ch in 'BUITRES':
        for j, row in enumerate(TAG[ch]):
            for i, bit in enumerate(row):
                if bit == '#':
                    f.fill(cx + i * scale, y + j * scale, cx + i * scale + scale - 1, y + j * scale + scale - 1, paint)
        if ch in 'UTS':                                   # Drips
            f.fill(cx + scale, y + 6 * scale, cx + scale, y + 6 * scale + 2 + (ord(ch) % 4), paint)
        cx += 4 * scale
    if not mark:
        return
    mx, my = cx + 4, y - 4                                # Their mark
    for yy in range(-6, 7):
        for xx in range(-6, 7):
            if 20 <= xx * xx + yy * yy <= 40:
                f.px(mx + 6 + xx, my + 8 + yy, paint)     # The head, a ring
    f.fill(mx + 11, my + 7, mx + 16, my + 8, paint)       # The hooked beak
    f.fill(mx + 15, my + 9, mx + 16, my + 12, paint)
    f.fill(mx + 5, my + 6, mx + 6, my + 7, paint)         # Its eye
    for k in range(3):                                    # Three slashes under it
        for i in range(8):
            f.px(mx + k * 5 + i // 2, my + 17 + i, paint)
            f.px(mx + 1 + k * 5 + i // 2, my + 17 + i, paint)


def make_paper() -> Image:
    """A sheet of newspaper blown down the street, tumbling (4 frames of
    14 x 14): what rolls by in the town instead of a tumbleweed."""
    img = Image(14 * 4, 14)
    paper = [rgb(0x8a8474), rgb(0xb4ae9c), rgb(0xd8d2be)]
    shapes = [((2, 4), (11, 3), (12, 9), (3, 10)), ((4, 2), (10, 4), (9, 12), (3, 10)),
              ((2, 6), (11, 5), (12, 8), (3, 9)), ((5, 2), (9, 3), (10, 11), (4, 12))]
    for frame, quad in enumerate(shapes):
        f = Frame(img, frame * 14, 14)
        xs, ys = [p[0] for p in quad], [p[1] for p in quad]
        for y in range(min(ys), max(ys) + 1):
            for x in range(min(xs), max(xs) + 1):
                f.px(x, y, paper[2] if y < (min(ys) + max(ys)) // 2 else paper[1])
        for y in range(min(ys) + 1, max(ys), 2):          # Its columns of print
            f.fill(min(xs) + 1, y, max(xs) - 1 - (y % 3), y, paper[0])
        f.outline()
    return img


POLICE = {'black': [rgb(0x141418), rgb(0x24242a), rgb(0x34343c), rgb(0x4a4a54)],
          'white': [rgb(0x8c8e94), rgb(0xb8bac0), rgb(0xdcdee2), rgb(0xf0f2f4)]}
GLASS = [rgb(0x1a2a36), rgb(0x2c4656), rgb(0x5a7a8a)]
PAINTS = {
    'green': [rgb(0x1c2a26), rgb(0x2c4038), rgb(0x40584a), rgb(0x5c7660)],
    'red': [rgb(0x3a1414), rgb(0x5a1e1c), rgb(0x7c2c26), rgb(0xa04436)],
    'sand': [rgb(0x4a4030), rgb(0x6a5c42), rgb(0x8a7a58), rgb(0xa89a74)],
    'burnt': [rgb(0x141210), rgb(0x241e1a), rgb(0x3a2e26), rgb(0x54402e)],
    'blue': [rgb(0x141c30), rgb(0x1e2c4a), rgb(0x2c4068), rgb(0x44608c)],
    'olive': [rgb(0x22261a), rgb(0x343a24), rgb(0x4a5232), rgb(0x646e44)],
}
CAR_W, CAR_H = 136, 46        # A sedan at her scale: 4.5 m long, 1.45 m tall (she is 56 px)


def tire(f: Frame, cx: int, cy: int, r: float, rim: bool = True) -> None:
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                c = IRON[0] if d > r * .62 else IRON[2] if d > r * .28 else IRON[3]
                if not rim and d <= r * .62:
                    c = IRON[1]
                f.px(x, y, c)


def sedan(f: Frame, ox: int, base: int, paint: list, state: int = 0, police: bool = False,
          shape: str = 'sedan') -> None:
    """A sedan, side on, facing right, its wheels on row base. state 0 whole,
    1 smashed up (dents, cracked glass, a flat), 2 burnt out on its rims.
    police: black with white doors. shape: 'sedan'; 'wagon' (its roof runs
    to the back); 'pickup' (a short cab, an open bed behind it)."""
    rear0, rear1 = {'sedan': (26, 44), 'wagon': (6, 14), 'pickup': (58, 62)}[shape]   # The cabin's back slope
    sag = 0 if state == 0 else 1 if state == 1 else 4
    top = base - 45 + sag                                  # Roof row
    belt = top + 16                                        # Where glass meets body
    sill = base - 8                                        # Bottom of the doors

    def body_color(x: int, y: int):
        ramp = paint
        if police and 44 <= x <= 92 and y >= belt:
            ramp = POLICE['white']
        if y <= belt + 1:
            return ramp[3]
        if y < belt + 9:
            return ramp[2]
        return ramp[1] if y < sill - 2 else ramp[0]

    for x in range(2, 134):                                # Lower body: trunk, doors, hood
        y0 = belt + (2 if x < 22 and shape == 'sedan' else 0) + (3 if x > 112 else 1 if x > 100 else 0)
        if x < 5 or x > 131:
            y0 = belt + 7
        for y in range(y0, sill + 1):
            f.px(ox + x, y, body_color(x, y))
    if shape == 'pickup':                                  # Its bed: the walls' rim, dark inside
        f.fill(ox + 6, belt, ox + 57, belt, paint[3])
        f.fill(ox + 8, belt + 1, ox + 56, belt + 2, rgb(0x0e0c0c))
    for x in range(rear0, 100):                            # Cabin: pillars and roof
        if x < rear1:
            y0 = belt - (x - rear0) * 15 // (rear1 - rear0)
        elif x <= 82:
            y0 = top
        else:
            y0 = top + (x - 82) * 15 // 17
        for y in range(y0, belt):
            f.px(ox + x, y, paint[3] if y == y0 else paint[2])
    glass = GLASS if state < 2 else [rgb(0x0e0c0c)] * 3    # Windows
    for x in range(rear0 + 6, 96):
        if x in (62, 63, 64) or (shape == 'wagon' and x in (36, 37, 38)):
            continue                                       # Pillars
        if x < rear1:
            y0 = belt - (x - rear0 - 4) * 13 // max(1, rear1 - rear0 - 4)
        elif x <= 80:
            y0 = top + 3
        else:
            y0 = top + 3 + (x - 80) * 12 // 15
        for y in range(max(y0, top + 3), belt - 1):
            c = glass[1] if (x + y) % 9 else glass[2]
            if state == 1 and x > 64 and (x * 3 + y * 5) % 7 == 0:
                c = glass[2]                               # Cracked
            f.px(ox + x, y, c)
    for x in (44, 63, 93):                                 # Door seams, handles
        f.fill(ox + x, belt + 2, ox + x, sill - 1, paint[0])
    for hx in (50, 70):
        f.fill(ox + hx, belt + 5, ox + hx + 4, belt + 5, IRON[3] if state < 2 else paint[0])
    f.fill(ox + 2, sill - 3, ox + 6, sill, IRON[2])        # Bumpers
    f.fill(ox + 129, sill - 3, ox + 134, sill, IRON[2])
    f.fill(ox + 130, belt + 6, ox + 133, belt + 9, rgb(0xe8d8a0) if state == 0 else IRON[1])   # Headlight
    f.fill(ox + 2, belt + 6, ox + 4, belt + 9, rgb(0xa02020) if state < 2 else IRON[0])
    if state >= 1:                                         # Dents
        f.fill(ox + 100, belt + 3, ox + 118, belt + 5, paint[0])
        f.fill(ox + 46, belt + 10, ox + 58, belt + 11, paint[0])
    if state == 2:
        for x in range(8, 128, 3):                         # Rust and scorch
            f.px(ox + x, belt + 3 + (x * 7) % 14, rgb(0x6a3a1e))
    for wx in (28, 108):                                   # Wheel arches and wheels
        for y in range(sill - 8, sill + 1):
            for x in range(wx - 11, wx + 12):
                if math.hypot(x - wx, y - (base - 8)) <= 10.5:
                    f.px(ox + x, y, rgb(0x0c0a0a))
        if state == 2:
            tire(f, ox + wx, base - 5, 5.2, rim=False)
        else:
            tire(f, ox + wx, base - 8, 8.2)
    if state == 1:                                         # A flat: its tyre squashed
        f.fill(ox + 20, base - 2, ox + 36, base, IRON[0])


def light_bar(f: Frame, ox: int, top: int, frame: int) -> None:
    red = rgb(0xff3a2a) if frame == 1 else rgb(0x7a1c16)
    blue = rgb(0x3a7aff) if frame == 2 else rgb(0x1a2a5a)
    if frame < 3:
        f.fill(ox + 52, top - 5, ox + 61, top - 1, red)
        f.fill(ox + 64, top - 5, ox + 73, top - 1, blue)
        f.fill(ox + 62, top - 5, ox + 63, top - 1, POLICE['black'][2])
        f.fill(ox + 52, top - 5, ox + 61, top - 5, rgb(0xffb0a0) if frame == 1 else red)
        f.fill(ox + 64, top - 5, ox + 73, top - 5, rgb(0xb0d0ff) if frame == 2 else blue)
        if frame in (1, 2):                                # Its glare
            gx = ox + (56 if frame == 1 else 68)
            for dx, dy in ((-7, -7), (0, -9), (7, -7)):
                f.px(gx + dx, top - 4 + dy, red if frame == 1 else blue)
    else:
        f.fill(ox + 52, top - 2, ox + 73, top - 1, POLICE['black'][2])
        for x in (54, 59, 66, 71):
            f.px(ox + x, top - 3, rgb(0x7a1c16) if x < 62 else rgb(0x1a2a5a))


SIREN_W, SIREN_H = 136, 52


def make_siren_car() -> Image:
    """A patrol car left on the road (4 frames of 136 x 52), at her scale:
    black with white doors and a brass star, its light bar dark; red lit;
    blue lit; smashed and silent."""
    img = Image(SIREN_W * 4, SIREN_H)
    for frame in range(4):
        f = Frame(img, frame * SIREN_W, SIREN_W)
        b = SIREN_H - 1
        sedan(f, 0, b, POLICE['black'], 0, police=True)
        for yy in range(-3, 4):                            # The star on the door
            for xx in range(-3, 4):
                if abs(xx) + abs(yy) <= 3 or (abs(xx) == abs(yy) and abs(xx) <= 2):
                    f.px(68 + xx, b - 19 + yy, rgb(0xd0a848) if xx <= 0 else rgb(0x9c7a32))
        light_bar(f, 0, b - 45, frame)
        f.outline()
    return img


def make_car_wreck() -> Image:
    """The cars across the road that are barricades (3 looks x 3 frames of
    136 x 46): a sand sedan, a red pickup, a blue station wagon; each dead
    but whole, smashed up, a burnt shell on its rims (it blew up)."""
    looks = (('sedan', 'sand'), ('pickup', 'red'), ('wagon', 'blue'))
    img = Image(CAR_W * 3 * len(looks), CAR_H)
    for k, (shape, paint) in enumerate(looks):
        for state in range(3):
            f = Frame(img, (k * 3 + state) * CAR_W, CAR_W)
            sedan(f, 0, CAR_H - 1, PAINTS[paint] if state < 2 else PAINTS['burnt'], state, shape=shape)
            f.outline()
    return img


VEHICLE_W, VEHICLE_H = 184, 70


def jeep(f: Frame, ox: int, base: int) -> None:
    """An army light truck (the boxy four-door kind), side on, facing right:
    a flat hood, a raked windshield, a hard top sloping down at the back,
    two doors with their windows, angular wheel arches, big tyres, a whip
    antenna, tow hooks and a star on the door."""
    o = PAINTS['olive']
    belt = base - 38                                       # Top of the hood and the doors' lower half
    roof = base - 60
    sill = base - 13                                       # Bottom of the body

    def top_at(x: int) -> int:
        if x < 10:
            return belt + 4
        if x < 34:                                         # The sloping back
            return belt - (x - 10) * (belt - roof) // 24
        if x <= 92:
            return roof
        if x <= 102:                                       # The windshield
            return roof + (x - 92) * (belt - roof) // 10
        return belt + (2 if x > 140 else 0)

    for x in range(6, 148):
        y0 = top_at(x)
        for y in range(y0, sill + 1):
            c = o[3] if y == y0 else o[2] if y < belt + 12 else o[1]
            if y > sill - 3:
                c = o[0]
            f.px(ox + x, y, c)
    for x in range(36, 100):                               # Glass: a rear and a front door window, the windshield
        if x in (62, 63, 64):
            continue
        y0 = roof + 4 + (max(0, x - 90) * (belt - roof) // 10 if x > 90 else 0)
        for y in range(y0, belt - 2):
            f.px(ox + x, y, GLASS[2] if (x - y) % 11 == 0 else GLASS[1] if x > 64 else GLASS[0])
    f.fill(ox + 34, roof + 3, ox + 35, belt - 2, o[1])     # Pillars
    f.fill(ox + 62, roof + 3, ox + 64, belt - 2, o[2])
    for x in (36, 64, 98):                                 # Door seams
        f.fill(ox + x, belt, ox + x, sill - 3, o[0])
    for hx in (42, 70):                                    # Handles
        f.fill(ox + hx, belt + 5, ox + hx + 5, belt + 6, o[0])
    for dx0 in (40, 68):                                   # The doors' pressed X
        for i in range(18):
            f.px(ox + dx0 + i, belt + 9 + i * 10 // 18, o[1])
            f.px(ox + dx0 + i, belt + 19 - i * 10 // 18, o[1])
    for yy in range(-4, 5):                                # A white star
        for xx in range(-4, 5):
            if abs(xx) + abs(yy) <= 4 and not (abs(xx) + abs(yy) == 4 and xx * yy != 0):
                f.px(ox + 82 + xx, belt + 14 + yy, rgb(0xc8c8b8))
    f.fill(ox + 100, belt - 6, ox + 103, belt - 3, o[0])   # Mirror
    f.fill(ox + 106, belt + 1, ox + 138, belt + 2, o[1])   # Hood louvres
    for x in range(110, 136, 5):
        f.fill(ox + x, belt + 4, ox + x + 2, belt + 4, o[0])
    for i in range(5):                                     # Grille slots, headlight, bumper, tow hook
        f.fill(ox + 143, belt + 6 + i * 3, ox + 147, belt + 6 + i * 3, o[0])
    f.fill(ox + 144, belt + 19, ox + 147, belt + 22, rgb(0xe8d8a0))
    dark = rgb(0x1a1c14)
    f.fill(ox + 146, sill - 5, ox + 149, sill - 1, dark)   # Front bumper, dark like the sills
    f.fill(ox + 4, sill - 5, ox + 7, sill - 1, dark)       # Rear bumper, tail light, jerrycan
    f.fill(ox + 6, belt + 8, ox + 8, belt + 12, rgb(0xa02020))
    f.fill(ox + 10, belt + 14, ox + 18, belt + 24, o[0])
    f.fill(ox + 10, belt + 14, ox + 18, belt + 14, o[2])
    ax = 20                                                # Whip antenna, on its mount on the rear deck
    f.fill(ox + ax - 1, top_at(ax) - 2, ox + ax + 1, top_at(ax) - 1, o[0])
    for i in range(30):
        f.px(ox + ax - i * i // 110, top_at(ax) - 3 - i, o[0] if i < 26 else o[1])
    for wx in (32, 122):                                   # Angular arches, big tyres
        for y in range(sill - 13, sill + 1):
            half = 15 if y > sill - 9 else 15 - (sill - 9 - y) * 2
            f.fill(ox + wx - half, y, ox + wx + half, y, rgb(0x0c0a0a))
        tire(f, ox + wx, base - 12, 12.2)
        for k in range(8):                                 # Lugs
            a = k * math.tau / 8
            f.px(ox + wx + round(5.5 * math.cos(a)), base - 12 + round(5.5 * math.sin(a)), IRON[0])


def army_truck(f: Frame, ox: int, base: int, load: int = 0) -> None:
    """An army truck: a cab at the front, a cargo bed under a canvas cover.
    load 0 the canvas shut; 1 its side rolled up on crates of supplies (the
    supply point); 2 rolled up, the bed empty."""
    o = PAINTS['olive']
    canvas = [rgb(0x3a3c28), rgb(0x52563a), rgb(0x6c7050), rgb(0x868a66)]
    bed_top, bed_floor = base - 62, base - 22
    for x in range(4, 122):                                # Canvas cover over its hoops
        y0 = bed_top + (2 if x < 8 or x > 117 else 0)
        for y in range(y0, bed_floor - (26 if load else 0)):
            c = canvas[3] if y == y0 else canvas[2] if (x - 4) % 22 > 2 else canvas[1]
            if y > bed_top + 20 and not load:
                c = canvas[1] if (x - 4) % 22 > 2 else canvas[0]
            f.px(ox + x, y, c)
    if load:                                               # Rolled up: what is inside
        f.fill(ox + 4, bed_floor - 26, ox + 121, bed_floor - 24, canvas[0])
        f.fill(ox + 6, bed_floor - 23, ox + 119, bed_floor - 1, rgb(0x14120e))
        for x in (6, 62, 118):
            f.fill(ox + x, bed_floor - 23, ox + x + 1, bed_floor - 1, o[1])
        if load == 1:
            for i, (cx0, w, hgt) in enumerate(((10, 22, 14), (34, 20, 18), (58, 26, 12), (88, 24, 16),
                                               (38, 16, 8), (92, 16, 7))):
                y1 = bed_floor - 1 - (18 if i == 4 else 16 if i == 5 else 0)
                f.box(ox + cx0, y1 - hgt, ox + cx0 + w, y1, [o[0], o[1], o[2], o[3]])
                f.fill(ox + cx0 + 3, y1 - hgt + 3, ox + cx0 + w - 3, y1 - hgt + 4, rgb(0xc8b860))
    f.fill(ox + 2, bed_floor, ox + 123, bed_floor + 5, o[1])   # Bed side
    f.fill(ox + 2, bed_floor, ox + 123, bed_floor, o[3])
    for x in range(8, 120, 14):
        f.fill(ox + x, bed_floor + 1, ox + x, bed_floor + 5, o[0])
    for x in range(126, 176):                              # Cab and hood
        y0 = base - 52 if x < 152 else base - 36
        for y in range(y0, base - 14):
            f.px(ox + x, y, o[3] if y == y0 else o[2] if y < base - 26 else o[1])
    f.fill(ox + 132, base - 48, ox + 148, base - 36, GLASS[1])
    f.fill(ox + 132, base - 48, ox + 138, base - 45, GLASS[2])
    f.fill(ox + 150, base - 50, ox + 151, base - 15, o[0])
    f.fill(ox + 174, base - 30, ox + 177, base - 25, rgb(0xe8d8a0))
    f.fill(ox + 172, base - 16, ox + 179, base - 12, IRON[2])   # Bumper
    for i in range(4):
        f.fill(ox + 168, base - 33 + i * 3, ox + 172, base - 33 + i * 3, o[0])
    for yy in range(-4, 5):                                # A white star on the door
        for xx in range(-4, 5):
            if abs(xx) + abs(yy) <= 4:
                f.px(ox + 140 + xx, base - 26 + yy, rgb(0xc8c8b8))
    f.fill(ox + 6, base - 16, ox + 172, base - 14, IRON[0])   # Frame
    for wx in (26, 50, 152):
        tire(f, ox + wx, base - 10, 10.2)
    if load == 1:                                          # Crates set down by it
        f.box(ox + 80, base - 9, ox + 96, base, [o[0], o[1], o[2], o[3]])
        f.box(ox + 100, base - 7, ox + 112, base, [rgb(0x3a2316), rgb(0x56351f), rgb(0x76492a), rgb(0x9a643a)])


def make_vehicles() -> Image:
    """Vehicles left on the road, to walk past (5 frames of 184 x 70): a
    green sedan, a red one, a burnt one, an army jeep, an army truck."""
    img = Image(VEHICLE_W * 5, VEHICLE_H)
    b = VEHICLE_H - 1
    for i in range(5):
        f = Frame(img, i * VEHICLE_W, VEHICLE_W)
        if i < 3:
            sedan(f, 24, b, PAINTS[('green', 'red', 'burnt')[i]], 2 if i == 2 else 0)
        elif i == 3:
            jeep(f, 30, b)
        else:
            army_truck(f, 2, b)
        f.outline()
    return img


def make_supply_truck() -> Image:
    """The supply point in the town (2 frames of 184 x 70): an army truck,
    its canvas rolled up on crates; then emptied."""
    img = Image(VEHICLE_W * 2, VEHICLE_H)
    for i in range(2):
        f = Frame(img, i * VEHICLE_W, VEHICLE_W)
        army_truck(f, 2, VEHICLE_H - 1, 1 + i)
        f.outline()
    return img


OUTPOST_W, OUTPOST_H = 168, 92


def make_outpost() -> Image:
    """An army outpost by the road (2 frames of 168 x 92): a tarp on poles
    over a table with a radio, a locker of supplies, a sandbag wall and a
    floodlight on a mast. Frame 1: searched (the locker open and empty) and
    its floodlight switched on."""
    img = Image(OUTPOST_W * 2, OUTPOST_H)
    o = PAINTS['olive']
    sand = [rgb(0x6a5638), rgb(0x8c7450), rgb(0xae9468), rgb(0xcab284)]
    for frame in range(2):
        f = Frame(img, frame * OUTPOST_W, OUTPOST_W)
        b = OUTPOST_H - 1
        for x in range(10, 122):                           # The tarp, sagging between its poles
            y0 = 26 + round(3 * math.sin(math.pi * ((x - 10) % 56) / 56))
            f.fill(x, y0, x, y0 + 4, o[2] if (x // 8) % 2 else o[1])
            f.px(x, y0, o[3])
        for x in (10, 66, 121):
            f.fill(x, 24, x + 1, b, rgb(0x56351f))
        f.fill(24, b - 30, 60, b - 28, rgb(0x76492a))      # Table, its legs
        for x in (26, 57):
            f.fill(x, b - 27, x + 1, b, rgb(0x56351f))
        f.fill(30, b - 42, 48, b - 31, o[1])               # The radio, its dial lit, its antenna
        f.fill(32, b - 40, 38, b - 36, rgb(0xa8e080) if frame else rgb(0x2a3a26))
        f.fill(41, b - 39, 46, b - 34, o[0])
        f.fill(47, b - 70, 47, b - 43, IRON[3])
        f.box(74, b - 34, 110, b, [o[0], o[1], o[2], o[3]])  # The locker of supplies
        f.fill(76, b - 32, 108, b - 30, rgb(0xc8b860))
        if frame == 0:
            f.fill(90, b - 20, 94, b - 14, rgb(0xd0a848))  # Its padlock
            f.fill(76, b - 17, 108, b - 17, o[0])
        else:                                              # Open: its lid thrown back, empty
            f.fill(76, b - 28, 108, b - 4, rgb(0x14120e))
            f.fill(74, b - 44, 110, b - 36, o[2])
            f.fill(74, b - 44, 110, b - 44, o[3])
        for row, (y, n, off) in enumerate(((b - 6, 13, 0), (b - 13, 12, 6), (b - 20, 11, 12))):
            for i in range(n):                             # The sandbag wall in front
                if 5 <= i <= 8 and row == 2:
                    continue                               # A gap to step through
                x0 = off + i * 12
                for yy in range(7):
                    for xx in range(12):
                        if (xx in (0, 11) and yy in (0, 6)):
                            continue
                        c = sand[3] if yy == 0 else sand[2] if yy < 4 else sand[1] if yy < 6 else sand[0]
                        f.px(x0 + xx, y + yy, c)
        mx = 146                                           # Floodlight mast
        f.fill(mx, 6, mx + 1, b, IRON[2])
        f.fill(mx - 3, b - 3, mx + 4, b, IRON[1])
        f.fill(mx - 10, 2, mx + 4, 12, IRON[1])
        f.fill(mx - 9, 3, mx - 3, 11, rgb(0xfff4c8) if frame else rgb(0x4a4a44))
        # The switched-on lens is part of the sprite. Its beam is a real
        # directional world light, rendered with the flashlight's occlusion
        # and falloff; never bake a dotted triangle into this sheet.
        f.outline()
    return img


FRONT_W, FRONT_H = 240, 192   # Two storeys at her scale: a floor is 3 m, 100 px
BRICK = [rgb(0x3e1e18), rgb(0x5a2a1e), rgb(0x763626), rgb(0x8e4630), rgb(0xa85a3c)]
CONCRETE = [rgb(0x4a4642), rgb(0x6a645c), rgb(0x8a8278), rgb(0xa49c90), rgb(0xbcb4a6)]
TRIM = [rgb(0x2e2420), rgb(0x4a3a30), rgb(0x6a5646), rgb(0x8c7860), rgb(0xb09a7c)]
GLOW = [rgb(0x8a5a2a), rgb(0xd09040), rgb(0xf0c870)]
HOLE = rgb(0x140e0e)


def brickwork(f: Frame, x0: int, y0: int, x1: int, y1: int) -> None:
    """Bricks 8 x 3, staggered, mortar between them, a few darker or chipped."""
    for y in range(y0, y1 + 1):
        row = (y - y0) // 4
        for x in range(x0, x1 + 1):
            mortar = (y - y0) % 4 == 3 or (x - x0 + row * 5) % 10 == 9
            k = ((x - x0 + row * 5) // 10 * 7 + row * 13) % 11
            c = BRICK[1] if mortar else BRICK[3] if k == 0 else BRICK[1] if k == 5 else BRICK[2]
            if x > x0 + (x1 - x0) * .78 and not mortar:
                c = BRICK[1] if c == BRICK[2] else BRICK[0] if c == BRICK[1] else BRICK[2]
            f.px(x, y, c)


def blockwork(f: Frame, x0: int, y0: int, x1: int, y1: int) -> None:
    for y in range(y0, y1 + 1):
        row = (y - y0) // 8
        for x in range(x0, x1 + 1):
            seam = (y - y0) % 8 == 7 or (x - x0 + row * 9) % 18 == 17
            c = CONCRETE[1] if seam else CONCRETE[3] if (x * 3 + y * 7) % 37 else CONCRETE[2]
            if x > x0 + (x1 - x0) * .8 and not seam:
                c = CONCRETE[2]
            f.px(x, y, c)


def big_window(f: Frame, x: int, y: int, w: int, h: int, look: str = 'dark') -> None:
    """A sash window a person could lean out of: stone lintel and sill, a
    frame, two sashes of four panes. look: dark, lit, curtain, boarded,
    broken, bars."""
    f.fill(x - 3, y - 4, x + w + 2, y - 1, CONCRETE[3])    # Lintel
    f.fill(x - 3, y - 1, x + w + 2, y - 1, CONCRETE[1])
    f.fill(x - 4, y + h, x + w + 3, y + h + 2, CONCRETE[4])   # Sill and its shadow
    f.fill(x - 3, y + h + 3, x + w + 2, y + h + 3, BRICK[0])
    f.fill(x - 1, y, x + w, y + h - 1, TRIM[3])            # Frame
    for yy in range(y + 1, y + h - 1):
        for xx in range(x + 1, x + w - 1):
            if look == 'lit' or look == 'curtain':
                c = GLOW[2] if yy < y + h // 2 and xx < x + w // 2 else GLOW[1]
            else:
                c = HOLE if (xx - x + yy - y) % 13 else GLASS[0]
            f.px(xx, yy, c)
    if look in ('dark', 'bars'):                           # The sky in the top panes
        for i in range(w // 3):
            f.px(x + 2 + i, y + 3 + i // 2, GLASS[1])
    if look == 'curtain':
        for xx in range(x + 1, x + w // 3):
            f.fill(xx, y + 1, xx, y + h - 2, rgb(0x9a4a3a) if xx % 2 else rgb(0x7a3428))
        for xx in range(x + w - w // 3, x + w - 1):
            f.fill(xx, y + 1, xx, y + h - 2, rgb(0x9a4a3a) if xx % 2 else rgb(0x7a3428))
    f.fill(x + w // 2 - 1, y, x + w // 2, y + h - 1, TRIM[3])   # Mullion, the meeting rail
    f.fill(x, y + h // 2 - 1, x + w - 1, y + h // 2, TRIM[2])
    for xx in (x + w // 4, x + 3 * w // 4):
        f.fill(xx, y + 1, xx, y + h - 2, TRIM[1])
    if look == 'boarded':
        for k, yy in enumerate(range(y + 4, y + h - 6, 9)):
            f.fill(x - 2, yy + (k % 2), x + w + 1, yy + 5 + (k % 2), rgb(0x76492a))
            f.fill(x - 2, yy + (k % 2), x + w + 1, yy + (k % 2), rgb(0x9a643a))
            f.px(x, yy + 2, IRON[3])
            f.px(x + w - 1, yy + 3, IRON[3])
    if look == 'broken':
        for i in range(h // 2):
            f.px(x + 3 + i * (w - 6) // (h // 2), y + h // 2 + (i * 5) % (h // 2 - 2), GLASS[2])
        f.fill(x + w // 2 + 2, y + h // 2 + 2, x + w - 3, y + h - 3, HOLE)
    if look == 'bars':
        for xx in range(x + 2, x + w - 1, 4):
            f.fill(xx, y, xx, y + h - 1, IRON[2])
        f.fill(x, y + h // 4, x + w - 1, y + h // 4, IRON[1])
        f.fill(x, y + 3 * h // 4, x + w - 1, y + 3 * h // 4, IRON[1])


def doorway(f: Frame, door: tuple, frame: list) -> None:
    x, y, w, h = door
    f.fill(x - 5, y - 6, x + w + 4, y + h - 1, frame[2])
    f.fill(x - 5, y - 6, x + w + 4, y - 5, frame[4])
    f.fill(x - 5, y - 6, x - 4, y + h - 1, frame[3])
    f.fill(x, y, x + w - 1, y + h - 1, HOLE)


def front_store(f: Frame, w: int, h: int, door: tuple) -> None:
    """A corner store with a flat over it: brick, big shop windows taped and
    cracked either side of the shutter, a striped awning, a blank sign
    board, sash windows upstairs, a cornice, a newspaper box and a drainpipe."""
    b = h - 1
    dx, dy, dw, dh = door
    brickwork(f, 4, 14, w - 5, b)
    f.fill(1, 6, w - 2, 13, CONCRETE[3])                   # Cornice
    f.fill(1, 6, w - 2, 7, CONCRETE[4])
    f.fill(1, 13, w - 2, 13, CONCRETE[0])
    for x in range(6, w - 6, 9):
        f.fill(x, 10, x + 3, 12, CONCRETE[1])              # Dentils
    for i, x0 in enumerate((22, 76, 136, 190)):            # Upstairs
        big_window(f, x0, 30, 28, 46, ('curtain', 'dark', 'boarded', 'lit')[i])
    f.fill(10, 92, w - 11, 108, TRIM[1])                   # The sign board, its letters gone
    f.fill(12, 94, w - 13, 106, rgb(0x23423a))
    for x in range(40, w - 40, 14):
        f.fill(x, 98, x + 8, 102, rgb(0x35594e))
    for x in range(6, w - 6):                              # The awning, striped, torn at one end
        drop = 122 + (2 if x % 12 < 6 else 0)
        if x > w - 52 and (x * 7) % 5 < 2:
            drop -= 8 + (x % 7)
        for y in range(110, drop):
            c = rgb(0x8a2a24) if (x // 12) % 2 else rgb(0xcfc4a8)
            if y > 118:
                c = rgb(0x661814) if (x // 12) % 2 else rgb(0xa0947c)
            f.px(x, y, c)
    for x0 in (10, dx + dw + 12):                          # Shop windows
        x1 = x0 + 74
        f.fill(x0 - 3, 126, x1 + 3, b - 12, TRIM[2])
        f.fill(x0, 129, x1, b - 15, GLASS[0])
        for i in range(30):                                # Reflections, a crack, tape
            f.px(x0 + 4 + i, 133 + i // 2, GLASS[1])
            f.px(x0 + 10 + i, 133 + i // 2, GLASS[1])
        for i in range(22):
            f.px(x0 + 50 - i, 131 + i * 2 % 40, GLASS[2])
        f.fill(x0 + 20, 150, x0 + 52, 151, rgb(0xcfc4a8))
        f.fill(x0 + 35, 140, x0 + 36, 162, rgb(0xcfc4a8))
        f.fill(x0 - 3, b - 11, x1 + 3, b - 2, BRICK[1])    # Stall riser
        f.fill(x0 - 3, b - 11, x1 + 3, b - 11, CONCRETE[3])
    graffiti(f, 162, 138, rgb(0xd8d0c0), 2, mark=False)   # The looters' tag across the glass
    doorway(f, door, TRIM)
    f.fill(w - 12, 14, w - 10, b - 2, IRON[2])             # Drainpipe
    f.fill(w - 30, b - 30, w - 16, b - 2, rgb(0x24386a))   # Newspaper box
    f.fill(w - 28, b - 27, w - 18, b - 18, GLASS[1])
    f.fill(w - 30, b - 30, w - 16, b - 30, rgb(0x3a5aa0))
    f.fill(0, b - 1, w - 1, b, CONCRETE[1])


def front_police(f: Frame, w: int, h: int, door: tuple) -> None:
    """The police station: concrete blocks, pilasters by the door, a blue
    board over it and a blue lamp either side, barred windows, a flag on a
    pole off the wall, steps."""
    b = h - 1
    dx, dy, dw, dh = door
    blockwork(f, 4, 16, w - 5, b)
    f.fill(1, 8, w - 2, 15, CONCRETE[4])
    f.fill(1, 15, w - 2, 15, CONCRETE[0])
    f.fill(4, 92, w - 5, 96, CONCRETE[4])                  # String course between the floors
    f.fill(4, 96, w - 5, 96, CONCRETE[1])
    for i, x0 in enumerate((20, 70, 142, 192)):
        big_window(f, x0, 32, 28, 46, ('dark', 'lit', 'dark', 'broken')[i])
    for x0 in (10, 46, 166, 202):
        big_window(f, x0, 116, 28, 46, 'bars')
    for x0 in (dx - 16, dx + dw + 8):                      # Pilasters
        f.fill(x0, 100, x0 + 7, b - 3, CONCRETE[4])
        f.fill(x0 + 6, 100, x0 + 7, b - 3, CONCRETE[2])
        f.fill(x0 - 2, 98, x0 + 9, 101, CONCRETE[4])
    f.fill(dx - 18, 102, dx + dw + 17, 116, rgb(0x182440))   # Its board, the star on it
    f.fill(dx - 18, 102, dx + dw + 17, 103, rgb(0x3a5aa0))
    cx = dx + dw // 2
    for yy in range(-5, 6):
        for xx in range(-5, 6):
            if abs(xx) + abs(yy) <= 5 or (abs(xx) == abs(yy) and abs(xx) <= 3):
                f.px(cx + xx, 109 + yy, rgb(0xd0a848) if xx <= 0 else rgb(0x9c7a32))
    for lx in (dx - 28, dx + dw + 21):                     # Blue lamps on brackets
        f.fill(lx + 2, 118, lx + 3, 122, IRON[2])
        f.fill(lx, 122, lx + 6, 132, rgb(0x3a5aa0))
        f.fill(lx + 1, 123, lx + 3, 127, rgb(0xa0c0ff))
        f.fill(lx, 132, lx + 6, 133, IRON[1])
    for i in range(34):                                    # Flag pole off the wall, the flag limp
        f.px(w - 40 + i, 70 - i // 2, IRON[3])
    f.fill(w - 14, 54, w - 6, 78, rgb(0x6a2a24))
    f.fill(w - 11, 54, w - 9, 78, rgb(0xcfc4a8))
    doorway(f, door, CONCRETE)
    for i in range(3):
        f.fill(dx - 10 - i * 4, b - i, dx + dw + 9 + i * 4, b - i, CONCRETE[3 - i % 2])


def front_flats(f: Frame, w: int, h: int, door: tuple) -> None:
    """A block of flats: brick, a canopy over the door, sash windows (some
    lit, one boarded), an air conditioner, a fire escape with its railing
    and a ladder that stops over the pavement, a water tank on the roof."""
    b = h - 1
    dx, dy, dw, dh = door
    brickwork(f, 6, 22, w - 7, b)
    f.fill(3, 16, w - 4, 21, CONCRETE[3])
    f.fill(3, 21, w - 4, 21, CONCRETE[0])
    f.fill(30, 0, 62, 13, rgb(0x56351f))                   # Water tank on its legs
    f.fill(30, 0, 62, 0, rgb(0x9a643a))
    for x in range(30, 63, 6):
        f.fill(x, 1, x, 13, rgb(0x3a2316))
    f.fill(33, 14, 34, 16, IRON[2])
    f.fill(58, 14, 59, 16, IRON[2])
    for i, x0 in enumerate((18, 66, 146, 194)):
        big_window(f, x0, 38, 28, 46, ('lit', 'dark', 'dark', 'curtain')[i])
    for i, x0 in enumerate((14, 56, 158, 198)):
        big_window(f, x0, 118, 26, 44, ('dark', 'boarded', 'lit', 'dark')[i])
    graffiti(f, 10, 94, rgb(0xc8c0b0), 2)                 # Sprayed between the floors
    f.fill(104, 96, 124, 108, CONCRETE[2])                 # An air conditioner under a window
    for y in range(98, 107, 2):
        f.fill(106, y, 122, y, CONCRETE[0])
    ex0, ex1, ey = 138, 232, 92                            # Fire escape: platform, railing, ladder
    f.fill(ex0, ey, ex1, ey + 2, IRON[2])
    f.fill(ex0, ey + 3, ex1, ey + 3, IRON[0])
    f.fill(ex0, ey - 16, ex1, ey - 15, IRON[3])
    for x in range(ex0, ex1 + 1, 5):
        f.fill(x, ey - 15, x, ey - 1, IRON[2])
    for x in (ex0 + 2, ex1 - 2):                           # Brackets
        for i in range(8):
            f.px(x + (i if x == ex0 + 2 else -i), ey + 4 + i, IRON[1])
    lx = ex0 + 10
    f.fill(lx, ey + 3, lx, ey + 46, IRON[3])
    f.fill(lx + 8, ey + 3, lx + 8, ey + 46, IRON[2])
    for y in range(ey + 8, ey + 46, 6):
        f.fill(lx, y, lx + 8, y, IRON[2])
    for i in range(46):                                    # Stairs up to the next floor
        f.px(ex1 - 12 - i, ey - 1 - i * 70 // 46, IRON[2])
        f.px(ex1 - 4 - i, ey - 1 - i * 70 // 46, IRON[1])
    doorway(f, door, TRIM)
    f.fill(dx - 14, dy - 16, dx + dw + 13, dy - 11, CONCRETE[3])   # Canopy
    f.fill(dx - 14, dy - 10, dx + dw + 13, dy - 9, CONCRETE[0])
    for x in (dx - 8, dx + dw + 6):                        # Its lamp, its bells
        f.fill(x, dy + 8, x + 2, dy + 20, IRON[2])
    f.fill(0, b - 1, w - 1, b, CONCRETE[1])


def front_checkpoint(f: Frame, w: int, h: int, door: tuple) -> None:
    """The army post's checkpoint: a concrete wall three metres high under
    razor wire, a guard tower with its cabin and searchlight, hazard stripes
    round the gate, a barrier arm raised, sandbags and a floodlight mast."""
    b = h - 1
    dx, dy, dw, dh = door
    o = PAINTS['olive']
    top = 92
    for y in range(top, b + 1):                            # The wall, in panels
        for x in range(2, w - 2):
            seam = x % 40 == 0
            c = CONCRETE[0] if seam else CONCRETE[3] if y < top + 3 else CONCRETE[2] if (x // 40) % 2 else CONCRETE[1]
            if (x * 5 + y * 3) % 41 == 0:
                c = CONCRETE[0]
            f.px(x, y, c)
    for x in range(2, w - 2):                              # Razor wire, two coils
        for k in (0, 1):
            y = top - 5 - k * 6 + round(3 * math.sin(x * .55 + k * 1.6))
            f.px(x, y, IRON[4] if x % 3 else IRON[2])
        if x % 9 == 0:
            f.fill(x, top - 12, x, top - 1, IRON[1])
    tx0, tx1 = 8, 78                                       # Guard tower
    for lx in (tx0 + 4, tx1 - 5):
        f.fill(lx, 62, lx + 2, b, o[1])
    for i in range(60):
        f.px(tx0 + 5 + i, 70 + i * (b - 80) // 60, o[0])
        f.px(tx1 - 6 - i, 70 + i * (b - 80) // 60, o[0])
    f.fill(tx0, 16, tx1, 62, o[2])                         # Its cabin
    f.fill(tx0 - 4, 10, tx1 + 4, 16, o[3])
    f.fill(tx0 - 4, 16, tx1 + 4, 16, o[0])
    f.fill(tx0 + 6, 26, tx1 - 6, 42, GLASS[0])
    f.fill(tx0 + 6, 26, tx1 - 6, 27, o[0])
    for x in range(tx0 + 18, tx1 - 6, 14):
        f.fill(x, 26, x, 42, o[1])
    f.fill(tx0, 46, tx1, 48, o[1])
    f.fill(tx1 - 2, 30, tx1 + 10, 38, IRON[1])             # Searchlight
    f.fill(tx1 + 8, 31, tx1 + 11, 37, rgb(0xf0e8c0))
    for x in range(dx - 12, dx + dw + 12):                 # Hazard stripes round the gate
        for y in range(dy - 14, dy - 6):
            f.px(x, y, rgb(0xd0a030) if (x + y) // 6 % 2 else rgb(0x1a1a1a))
    for side in (dx - 12, dx + dw + 5):
        for y in range(dy - 6, b + 1):
            for x in range(side, side + 7):
                f.px(x, y, rgb(0xd0a030) if (x + y) // 6 % 2 else rgb(0x1a1a1a))
    doorway(f, door, CONCRETE)
    for i in range(70):                                    # The barrier arm, up
        x, y = dx + dw + 16 + i, b - 30 - i
        c = rgb(0xc24e32) if (i // 8) % 2 else rgb(0xe0d6bc)
        f.fill(x, y, x + 1, y + 2, c)
    f.fill(dx + dw + 12, b - 34, dx + dw + 19, b, o[1])
    graffiti(f, 152, 108, rgb(0x9c2a20), 2)                # They got this far: red on the concrete
    mx = w - 18                                            # Floodlight mast
    f.fill(mx, 20, mx + 1, top - 1, IRON[2])
    f.fill(mx - 8, 14, mx + 6, 24, IRON[1])
    f.fill(mx - 7, 15, mx + 5, 23, rgb(0xf0e8c0))
    sand = [rgb(0x6a5638), rgb(0x8c7450), rgb(0xae9468), rgb(0xcab284)]
    for row, (y, n, off) in enumerate(((b - 6, 6, 150), (b - 13, 5, 156), (b - 20, 4, 162))):
        for i in range(n):
            x0 = off + i * 13
            f.fill(x0 + 1, y, x0 + 11, y + 6, sand[2])
            f.fill(x0 + 1, y, x0 + 11, y, sand[3])
            f.fill(x0 + 1, y + 6, x0 + 11, y + 6, sand[0])


FRONTS = [front_store, front_police, front_flats, front_checkpoint]


def make_city_fronts() -> Image:
    """The town's fronts for walls (4 frames of 240 x 192): store, police
    station, flats, checkpoint. Their doorway, 44 x 64, is in the middle on
    the ground: the door sheet's shutter fills it."""
    img = Image(FRONT_W * len(FRONTS), FRONT_H)
    door = ((FRONT_W - 44) // 2, FRONT_H - 64, 44, 64)
    for i, draw in enumerate(FRONTS):
        f = Frame(img, i * FRONT_W, FRONT_W)
        draw(f, FRONT_W, FRONT_H, door)
        f.outline()
    return img

TRAIN_W, TRAIN_H = 300, 104
CAR = {'body': [rgb(0x3a1e16), rgb(0x5a2e1e), rgb(0x7a4028), rgb(0x9a5634)],
       'steel': [IRON[0], IRON[1], IRON[2], IRON[3]]}


def make_train() -> Image:
    """A freight train off its rails, across the line (300 x 104): a boxcar
    on the left, tipped a little; the locomotive's long hood on the right,
    nosed into it. Between them, over the road, the gap that the wall's door
    (DOOR_W x DOOR_H) fills: blown, it is the way through."""
    img = Image(TRAIN_W, TRAIN_H)
    f = Frame(img, 0, TRAIN_W)
    b = TRAIN_H - 1
    gap0, gap1 = (TRAIN_W - 44) // 2, (TRAIN_W + 44) // 2
    body, steel = CAR['body'], CAR['steel']
    for x in range(4, gap0 - 2):                          # The boxcar, tilted: its left end lifted
        lift = (gap0 - x) // 14
        top, bottom = 30 - lift, b - 14 - lift
        for y in range(top, bottom + 1):
            c = body[2] if (x - 4) % 9 < 7 else body[1]
            if y == top:
                c = body[3]
            if (x * 3 + y * 7) % 29 == 0:
                c = body[0]
            f.px(x, y, c)
        for y in (top + 6, bottom - 6):
            f.px(x, y, body[1])
    for x0 in (40, 76):                                   # Its sliding door, its rail
        f.fill(x0, 40, x0 + 22, 82, body[1])
        f.fill(x0 + 11, 40, x0 + 11, 82, body[0])
        f.fill(x0 - 2, 38, x0 + 24, 38, steel[2])
    for x in range(8, gap0 - 6):                          # Frame and trucks off the rail
        lift = (gap0 - x) // 14
        f.fill(x, b - 14 - lift, x, b - 12 - lift, steel[0])
    for wx, lift in ((24, 7), (40, 6), (100, 2), (116, 1)):
        for y in range(b - 10 - lift, b - lift + 1):
            for x in range(wx - 5, wx + 6):
                d = math.hypot(x - wx, y - (b - 5 - lift))
                if d <= 5.4:
                    f.px(x, y, steel[3] if d < 1.8 else steel[1] if d < 4 else steel[0])
    for x in range(gap1 + 2, TRAIN_W - 4):                # The locomotive: long hood, cab at the far end
        cab = x > TRAIN_W - 60
        top = 22 if cab else 44
        for y in range(top, b - 13):
            c = rgb(0x5a4c24) if y < top + 4 else rgb(0x725f28) if y < 70 else rgb(0x3e3418)
            if not cab and (x - gap1) % 12 == 0:
                c = rgb(0x3a301a)                         # Hood doors
            if 60 <= y <= 64:
                c = rgb(0x9c3424)                         # Its red stripe
            f.px(x, y, c)
    f.fill(TRAIN_W - 52, 28, TRAIN_W - 36, 40, GLASS[1])   # Cab windows, one broken
    f.fill(TRAIN_W - 30, 28, TRAIN_W - 14, 40, GLASS[0])
    f.fill(TRAIN_W - 52, 28, TRAIN_W - 46, 31, GLASS[2])
    f.fill(gap1 + 30, 36, gap1 + 34, 43, steel[1])         # Exhaust stack, cold
    f.fill(gap1 + 2, b - 13, TRAIN_W - 6, b - 11, steel[0])
    for wx in (gap1 + 26, gap1 + 44, TRAIN_W - 46, TRAIN_W - 28):
        for y in range(b - 10, b + 1):
            for x in range(wx - 5, wx + 6):
                d = math.hypot(x - wx, y - (b - 5))
                if d <= 5.4:
                    f.px(x, y, steel[3] if d < 1.8 else steel[1] if d < 4 else steel[0])
    for x in range(0, TRAIN_W):                           # The rail, bent where it went off
        y = b - 1 + (1 if gap0 - 30 < x < gap1 + 30 else 0)
        f.px(x, y, steel[3])
    f.outline()
    return img


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'assets'
    out: dict[str, Image] = {}
    # Current landscape and prop geometry, shared with their dedicated tools.
    # The older painters below remain source geometry for road objects only.
    from make_landscape import theme_layers
    from make_props import build_assets as props
    from refine_terrain import build_assets as terrain
    for name in THEMES:
        for layer, image in theme_layers(name).items():
            out[f'backgrounds/{name}/{layer}.png'] = image
    current_props = props()
    for name in PROPS:
        path = f'sprites/props/{name}.png'
        out[path] = current_props[path]
    out['sprites/sparrow/sparrow.png'] = make_sparrow()
    out['sprites/terrain/burner.png'] = make_burner()
    out['sprites/effects/flare.png'] = make_flare()
    out['sprites/effects/paper.png'] = make_paper()
    out['sprites/terrain/hydrant.png'] = make_hydrant()
    out['sprites/effects/hydrant_jet.png'] = make_hydrant_jet()
    out['sprites/terrain/siren_car.png'] = make_siren_car()
    out['sprites/terrain/car_wreck.png'] = make_car_wreck()
    out['sprites/terrain/vehicles.png'] = make_vehicles()
    out['sprites/terrain/supply_truck.png'] = make_supply_truck()
    out['sprites/terrain/outpost.png'] = make_outpost()
    out['sprites/terrain/city_fronts.png'] = make_city_fronts()
    out['sprites/terrain/train.png'] = make_train()
    for name, image in terrain().items():
        if name in out:
            out[name] = image
    for name, img in out.items():
        path = assets / name
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        print(f'make_city: {name} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
