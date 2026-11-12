"""The first route's land, for tools/make_landscape.py: the desert at sunset
(atardecer), the graveyard at dusk (cementerio), the desert under the moon
(noche) and the ghost town under its red moon (pueblo_fantasma).

Each theme is a palette and a list of what stands on its land; the painters
below are shared. Light comes from the upper left, as on every sprite: faces
turned left are lit, those turned right are in shade, tops catch a rim.
"""
from __future__ import annotations

import math

from landscape_kit import LAYERS, Canvas, Rng, dither, fbm, hash2, hx, mix, seed_of, wave

# ---- Palettes ------------------------------------------------------------------------------
# Ramps run dark to light. 'sky' is read by make_landscape.make_sky.

THEMES = {
    'atardecer': {
        'sky': {
            'stops': [(0, 0x251e20), (44, 0x2c2025), (64, 0x462836), (88, 0x61313c), (108, 0x7e353e),
                      (124, 0x983d3d), (138, 0xb94b36), (152, 0xd05432), (168, 0xe46c3a)],
            'orb': {'kind': 'sun', 'at': (150, 119), 'r': 15, 'glow': 13,
                    'colors': [0xe17727, 0xf6a648, 0xfed980],
                    'bars': [(4, -22, 20, 12), (9, -16, 26, 13)]},
            'clouds': [
                {'seed': 21, 'y': 80, 'spread': 9, 'count': 5, 'len': (60, 130), 'thick': (4, 7),
                 'colors': [0x2e1e2a, 0x3d2433, 0x4a2837, 0x8a3a42, 0xa84840]},
                {'seed': 22, 'y': 112, 'spread': 8, 'count': 6, 'len': (44, 100), 'thick': (3, 6),
                 'colors': [0x4a2734, 0x5c2c38, 0x742f3a, 0xd05a38, 0xf08a40], 'near_light': 0xffb050},
                {'seed': 23, 'y': 143, 'spread': 5, 'count': 7, 'len': (30, 76), 'thick': (2, 3),
                 'colors': [0x7a3238, 0x8e3a3a, 0xa8443a, 0xf08a40, 0xffc060], 'near_light': 0xffd070},
            ],
            'birds': [(330, 96, 4, 0x2e1e2a)],
        },
        'far': {'style': 'mesas', 'ramp': [0x4a2a30, 0x5b3235, 0x693b3d, 0x7c4440, 0x96503e], 'rim': 0xc8603a,
                'back': [0x8c4038, 0x9c4a3a, 0xd86a3c], 'haze': 0x7a3c38},
        'mid': {'ramp': [0x33232a, 0x3f2a2e, 0x4b2e31, 0x583134, 0x6a3a36], 'crest': 0xcd5431, 'lit': 0x8a4638,
                'plant': [0x2e2025, 0x4a2c2c], 'rock': [0x3a262a, 0x6a3c38, 0x9a5038],
                'stands': ['saguaros', 'outcrops', 'brush', 'poles']},
        'near': {'ramp': [0x231a19, 0x2a1f20, 0x312224, 0x3b272b, 0x47302f], 'crest': 0x6a3c34, 'lit': 0x55342f,
                 'plant': [0x241c16, 0x3a2a1e, 0x54392a], 'rock': [0x2c2020, 0x4a3030, 0x6a4238],
                 'stands': ['brush', 'boulders', 'grass', 'fence']},
        'ground': {'line': [0xa45a3a, 0x955437], 'ramp': [0x231818, 0x2c1e1e, 0x39272b, 0x4d3433, 0x62423a],
                   'stone': 0x7a5444, 'ruts': 2, 'stones': 30, 'cracks': 12, 'tufts': 12},
    },
    'cementerio': {
        'sky': {
            'stops': [(0, 0x121019), (50, 0x15131d), (72, 0x1d1927), (96, 0x272030), (116, 0x33283a),
                      (134, 0x463344), (150, 0x5a3d4a), (168, 0x6c4652)],
            'orb': {'kind': 'crescent', 'at': (158, 92), 'r': 12, 'glow': 9,
                    'colors': [0xa7a8a8, 0xd7d1bd], 'earthshine': 0x2c2838},
            'stars': [{'count': 150, 'bottom': 138, 'dim_above': 52,
                       'colors': [0x4a4658, 0x7a7488, 0xb8b0b8, 0xe8e0d0]}],
            'clouds': [
                {'seed': 31, 'y': 86, 'spread': 12, 'count': 4, 'len': (70, 140), 'thick': (4, 7),
                 'colors': [0x14121c, 0x1b1824, 0x221d2c, 0x33293c, 0x473a50], 'near_light': 0x5c5068},
                {'seed': 32, 'y': 128, 'spread': 8, 'count': 6, 'len': (40, 100), 'thick': (2, 4),
                 'colors': [0x2a2030, 0x33283a, 0x3c2e40, 0x5a4252, 0x705262]},
            ],
        },
        'far': {'style': 'graves', 'ramp': [0x241e2c, 0x2e2536, 0x382c40, 0x42344a, 0x4e3e56], 'rim': 0x6a5670,
                'back': [0x4a3648, 0x54404e, 0x7a5a68], 'haze': 0x3e3040},
        'mid': {'ramp': [0x1c1a22, 0x222028, 0x28262c, 0x2e2c30, 0x38363a], 'crest': 0x4a5038, 'lit': 0x3e4234,
                'plant': [0x1a1c18, 0x2c3226], 'rock': [0x26242c, 0x3c3a44, 0x5a566a],
                'stands': ['graves', 'trees', 'brush', 'railing']},
        'near': {'ramp': [0x100f14, 0x141318, 0x1a1820, 0x222028, 0x2b2832], 'crest': 0x3a3a34, 'lit': 0x30303a,
                 'plant': [0x14160f, 0x20261a, 0x303826], 'rock': [0x1c1a22, 0x32303a, 0x4a4856],
                 'stands': ['graves', 'grass', 'brush', 'boulders']},
        'ground': {'line': [0x8a7050, 0x6e5a40], 'ramp': [0x19171c, 0x211e24, 0x2b272c, 0x3b3434, 0x4a4240],
                   'stone': 0x625a58, 'ruts': 1, 'stones': 34, 'cracks': 8, 'tufts': 22, 'leaves': 0x5a4030},
        'fog': {'color': 0x4a4652, 'alpha': (42, 84)},
    },
    'noche': {
        'sky': {
            'stops': [(0, 0x0c0f1a), (48, 0x0e1220), (70, 0x151a2b), (94, 0x1c2236), (114, 0x252b42),
                      (132, 0x30344c), (148, 0x3c3e58), (168, 0x484a66)],
            'orb': {'kind': 'moon', 'at': (156, 94), 'r': 14, 'glow': 11,
                    'colors': [0x6a6e7e, 0xa7a8a8, 0xd7d1bd, 0xecdb9c],
                    'craters': [(-5, -4, 3), (4, 2, 2.5), (-2, 6, 2), (6, -6, 1.6)]},
            'stars': [{'count': 230, 'bottom': 142, 'dim_above': 52,
                       'colors': [0x3c4460, 0x6a7290, 0xa8acc0, 0xe8e6d8]}],
            'milky': {'from': (210, 150), 'to': (480, 40), 'width': 22, 'top': 54, 'haze': 0x1c2238, 'dust': 0x8088a4},
            'clouds': [
                {'seed': 41, 'y': 122, 'spread': 10, 'count': 5, 'len': (50, 120), 'thick': (3, 5),
                 'colors': [0x121628, 0x181d30, 0x1f2540, 0x3a4260, 0x525a7a], 'near_light': 0x6e7696},
            ],
        },
        'far': {'style': 'mesas', 'ramp': [0x1b2136, 0x232a40, 0x2b324a, 0x343c56, 0x414a66], 'rim': 0x5a6484,
                'back': [0x343a56, 0x3c4462, 0x56607e], 'haze': 0x2e3450},
        'mid': {'ramp': [0x171b28, 0x1b1f2d, 0x21263a, 0x262a3a, 0x30354a], 'crest': 0x4a5270, 'lit': 0x3a4058,
                'plant': [0x12151f, 0x232a3c], 'rock': [0x1c2030, 0x343b52, 0x525c7a],
                'stands': ['saguaros', 'outcrops', 'brush']},
        'near': {'ramp': [0x0c0e15, 0x10121b, 0x151824, 0x1b1f2d, 0x232838], 'crest': 0x343a50, 'lit': 0x2a3044,
                 'plant': [0x0e1016, 0x1a2030, 0x2a3246], 'rock': [0x151824, 0x2a3044, 0x444c66],
                 'stands': ['brush', 'boulders', 'grass', 'bones']},
        'ground': {'line': [0x7d6a52, 0x5e5040], 'ramp': [0x15161d, 0x1b1c24, 0x24242c, 0x34323a, 0x44424a],
                   'stone': 0x5c5a66, 'ruts': 2, 'stones': 32, 'cracks': 10, 'tufts': 10},
        'fog': {'color': 0x3e4560, 'alpha': (40, 80)},
    },
    'pueblo_fantasma': {
        'sky': {
            'stops': [(0, 0x140b0e), (48, 0x180d11), (70, 0x2a1418), (94, 0x3d181a), (114, 0x58201c),
                      (132, 0x7a2a1c), (148, 0x9a3a20), (168, 0xb04a26)],
            'orb': {'kind': 'sun', 'at': (166, 116), 'r': 15, 'glow': 12,
                    'colors': [0x902004, 0xd03305, 0xe55d22],
                    'bars': [(-3, -24, 22, 9), (3, -20, 26, 10), (8, -14, 20, 11)]},
            'stars': [{'count': 40, 'bottom': 100, 'dim_above': 52, 'colors': [0x5a3030, 0x8a5048, 0xc08a70]}],
            'clouds': [
                {'seed': 51, 'y': 84, 'spread': 10, 'count': 5, 'len': (70, 150), 'thick': (5, 8),
                 'colors': [0x180c10, 0x20100f, 0x2a1414, 0x5a201a, 0x7c2c1e]},
                {'seed': 52, 'y': 121, 'spread': 7, 'count': 6, 'len': (50, 110), 'thick': (3, 5),
                 'colors': [0x2c1214, 0x3d181a, 0x4c1c1c, 0xa03a20, 0xd05a28], 'near_light': 0xf08038},
                {'seed': 53, 'y': 146, 'spread': 4, 'count': 6, 'len': (30, 70), 'thick': (2, 3),
                 'colors': [0x58201c, 0x6a261c, 0x7e2e1e, 0xc85a2a, 0xe87a38]},
            ],
            'birds': [(300, 104, 3, 0x180c10), (396, 88, 2, 0x180c10)],
        },
        'far': {'style': 'town', 'ramp': [0x2c1418, 0x3a1a1e, 0x4a2024, 0x562628, 0x642c2a], 'rim': 0x8a3c2c,
                'back': [0x6a2a24, 0x763226, 0xa8482a], 'haze': 0x5a2422},
        'mid': {'ramp': [0x22141a, 0x28171b, 0x301b1f, 0x371f22, 0x432628], 'crest': 0x6a3228, 'lit': 0x4f2a26,
                'plant': [0x1e1014, 0x38201c], 'rock': [0x2a171b, 0x4a2a28, 0x70402e],
                'stands': ['shacks', 'outcrops', 'brush', 'poles']},
        'near': {'ramp': [0x100a0c, 0x160d10, 0x1e1216, 0x28171b, 0x321d20], 'crest': 0x4a2a24, 'lit': 0x3a2020,
                 'plant': [0x140c0c, 0x2a1a14, 0x40281c], 'rock': [0x1e1216, 0x3a2222, 0x58342c],
                 'stands': ['fence', 'brush', 'boulders', 'grass']},
        'ground': {'line': [0xa06c3c, 0x83582f], 'ramp': [0x1c1416, 0x241a1c, 0x2e2224, 0x43302c, 0x564036],
                   'stone': 0x6e5040, 'ruts': 3, 'stones': 26, 'cracks': 14, 'tufts': 8},
        'fog': {'color': 0x5a2a28, 'alpha': (40, 80)},
    },
}


def tone(ramp: list, k: int):
    return hx(ramp[max(0, min(len(ramp) - 1, k))])


# ---- Shapes that stand on the land ------------------------------------------------------------

def saguaro(c: Canvas, x: int, base: int, tall: int, dark, lit) -> None:
    """A cactus far off: a column with an arm or two, its left edge lit."""
    c.vline(x, base - tall, base, dark)
    c.vline(x + 1, base - tall + 1, base, dark)
    c.vline(x, base - tall + 1, base - 1, lit)
    if tall >= 7:
        ay = base - tall // 2 - (x % 3)
        c.hline(x - 2, x - 1, ay, dark)
        c.vline(x - 2, ay - 2 - (x % 2), ay, dark)
        c.set(x - 2, ay - 2 - (x % 2), lit)
    if tall >= 9 and x % 2:
        ay = base - tall // 3
        c.hline(x + 2, x + 3, ay, dark)
        c.vline(x + 3, ay - 3, ay, dark)


def shrub(c: Canvas, x: int, base: int, wide: int, tall: int, cols: list, seed: int) -> None:
    """A round bush: dark underneath, lighter on its upper left, a few
    twigs breaking its edge."""
    cx, cy, rx, ry = x + wide / 2.0, base - tall / 2.0, wide / 2.0, tall / 2.0
    for yy in range(base - tall - 1, base + 1):
        for xx in range(x - 1, x + wide + 2):
            d = ((xx - cx) / rx) ** 2 + ((yy - cy) / (ry * 1.15)) ** 2
            d += (hash2(xx, yy, seed) - 0.5) * 0.5
            if d > 1.0 or yy > base:
                continue
            light = -(xx - cx) / rx * 0.6 - (yy - cy) / ry * 0.9
            k = 2 if light > 0.75 and len(cols) > 2 else 1 if light > 0.1 else 0
            if hash2(xx, yy, seed + 3) < 0.12:
                k = max(0, k - 1)
            c.set(xx, yy, hx(cols[min(k, len(cols) - 1)]))
    for i in range(max(1, wide // 4)):                    # Twigs
        tx = x + 1 + int(hash2(i, seed, 5) * (wide - 2))
        c.set(tx, base - tall - 1 - int(hash2(i, seed, 6) * 2), hx(cols[0]))


def boulder(c: Canvas, x: int, base: int, wide: int, tall: int, cols: list, seed: int) -> None:
    """A rock: flat facets, the top and left ones lit, a dark foot, a crack."""
    top = base - tall
    for xx in range(x, x + wide):
        u = (xx - x) / max(1, wide - 1)
        rise = min(1.0, math.sin(math.pi * min(1.0, u * 1.1 + 0.04)) * 1.5) ** 0.8   # A flat top, steep ends
        y0 = base - max(1, round(tall * rise + (hash2(xx // 2, seed, 1) - 0.5) * 1.2))
        for yy in range(max(top, y0), base + 1):
            v = (yy - y0) / max(1, base - y0)
            k = 2 if (v < 0.34 and u < 0.7) else 1 if (u < 0.45 or v < 0.6) else 0
            c.set(xx, yy, hx(cols[k]))
        if u > 0.25 and hash2(xx, seed, 2) < 0.14:
            c.vline(xx, y0 + 1, min(base, y0 + 2 + int(hash2(xx, seed, 3) * 3)), hx(cols[0]))


def tuft(c: Canvas, x: int, base: int, tall: int, dark, lit) -> None:
    """Dry grass: a few blades fanning out."""
    for i, dx in enumerate((-2, -1, 0, 1, 2)):
        hgt = max(1, tall - abs(dx) - (i * 7 + x) % 2)
        for k in range(hgt):
            c.set(x + dx + (k * dx) // max(2, tall), base - k, lit if dx <= 0 and k >= hgt - 1 else dark)


def cross(c: Canvas, x: int, base: int, tall: int, dark, lit, lean: int = 0) -> None:
    for k in range(tall):
        c.set(x + (lean * k) // max(1, tall), base - k, lit if k == tall - 1 else dark)
    arm = max(1, tall // 3)
    ay = base - tall + max(1, tall // 4)
    c.hline(x + lean - arm, x + lean + arm, ay, dark)
    c.set(x + lean - arm, ay, lit)


def headstone(c: Canvas, x: int, base: int, wide: int, tall: int, dark, lit) -> None:
    for yy in range(base - tall, base + 1):
        inset = 1 if yy == base - tall and wide > 2 else 0
        c.hline(x + inset, x + wide - 1 - inset, yy, dark)
    c.vline(x, base - tall + 1, base, lit)
    if wide > 2:
        c.hline(x + 1, x + wide - 2, base - tall, lit)


def bare_tree(c: Canvas, x: int, base: int, tall: int, dark, lit, seed: int) -> None:
    """A dead tree far off: a trunk that forks, and forks again."""
    def branch(bx: float, by: float, angle: float, length: float, width: int, depth: int) -> None:
        ex, ey = bx + math.cos(angle) * length, by - math.sin(angle) * length
        c.line(bx, by, ex, ey, dark, width)
        if width > 1:
            c.line(bx, by, ex, ey, lit, 1)
        if depth > 0:
            spread = 0.45 + hash2(depth, seed, int(bx)) * 0.5
            branch(ex, ey, angle + spread, length * 0.62, max(1, width - 1), depth - 1)
            branch(ex, ey, angle - spread * 0.8, length * 0.58, max(1, width - 1), depth - 1)
    branch(x, base, math.pi / 2 + (hash2(x, seed, 9) - 0.5) * 0.3, tall * 0.45, 2 if tall > 14 else 1, 3 if tall > 14 else 2)


def fence_run(c: Canvas, x0: int, x1: int, ground, tall: int, dark, lit, seed: int, gap: int = 9) -> None:
    """Posts and rails along the land (ground(x) gives its row), a rail down
    here and there."""
    for x in range(x0, x1):
        g = ground(x)
        if g is None:
            continue
        if (x - x0) % gap == 0:
            lean = int(hash2(x, seed, 1) * 3) - 1
            for k in range(tall + 1):
                c.set(x + (lean * k) // (tall + 1), g - k, lit if k == tall else dark)
        elif hash2((x - x0) // gap, seed, 2) > 0.22:
            c.set(x, g - tall + 2, dark)
            if tall > 5 and hash2((x - x0) // gap, seed, 4) > 0.4:
                c.set(x, g - tall // 2 + 1, dark)


def pole_line(c: Canvas, x0: int, x1: int, ground, tall: int, dark, lit, gap: int = 46) -> None:
    """Telegraph poles marching off with their wire sagging between them."""
    tips = []
    for x in range(x0, x1, gap):
        g = ground(x)
        if g is None:
            continue
        c.vline(x, g - tall, g, dark)
        c.set(x, g - tall, lit)
        c.hline(x - 2, x + 2, g - tall + 2, dark)
        tips.append((x, g - tall + 2))
    for (xa, ya), (xb, yb) in zip(tips, tips[1:]):
        for x in range(xa + 1, xb):
            u = (x - xa) / (xb - xa)
            y = round(ya + (yb - ya) * u + 4 * math.sin(math.pi * u))
            if (x + y) % 3:
                c.set(x, y, dark)


# ---- The far land -----------------------------------------------------------------------------

def plateaus(period: int, seed: int, base: float, count: int, width: tuple, height: tuple,
             spires: int = 0) -> list:
    """Heights (rows over the layer's foot) of mesas and buttes in a line,
    repeating every period: flat tops, cliffs that step down by ledges, a
    slope of fallen rock at the foot."""
    rng = Rng(seed)
    hgt = [base + 2.5 * wave(x, period, seed + 1, 4) + 1.5 for x in range(period)]

    def raise_one(cx: float, half: float, tall: float, slope: float) -> None:
        sides = []
        for _ in range(2):                                # Each side: (how far out, share of the height lost)
            a, b = 0.2 + rng.unit() * 0.18, 0.5 + rng.unit() * 0.2
            l1, l2 = 2 + rng.range(0, 7), 3 + rng.range(0, 9)
            sides.append([(0, 0.0), (2, a), (2 + l1, a + 0.05), (4 + l1, b), (4 + l1 + l2, b + 0.06),
                          (4 + l1 + l2 + slope, 1.0)])
        for x in range(int(cx - half - 60 - slope), int(cx + half + 60 + slope)):
            d = abs(x - cx) - half
            if d <= 0:
                drop = 0.0
                bump = 1.0 if hash2(x // 5, seed, 7) > 0.72 else 0.0   # Small steps along the top
            else:
                pts = sides[0 if x < cx else 1]
                drop, bump = 1.0, 0.0
                for (xa, da), (xb, db) in zip(pts, pts[1:]):
                    if xa <= d < xb:
                        drop = da + (db - da) * (d - xa) / (xb - xa)
                        break
            y = base + (tall - bump) * (1.0 - drop)
            if y > hgt[x % period]:
                hgt[x % period] = y

    for i in range(count):
        cx = (i + 0.2 + rng.unit() * 0.6) * period / count
        raise_one(cx, rng.range(*width) / 2.0, rng.range(*height), 10 + rng.range(0, 14))
    for i in range(spires):                               # Lone towers of rock
        cx = rng.range(0, period - 1)
        raise_one(cx, 2 + rng.range(0, 3), rng.range(height[0] - 4, height[1] - 6), 6 + rng.range(0, 6))
    return hgt


def paint_plateaus(c: Canvas, hgt: list, ramp: list, rim, seed: int, haze=None, plain: bool = False) -> None:
    """Rock in level strata, lit on its left faces and its tops, in shade on
    its right faces, cracked down from its edges; haze over its foot."""
    period, h = c.period, c.h
    strata = [2, 1, 2, 3, 2, 2, 1, 2, 3, 3, 2, 1]
    for x in range(period):
        top = h - round(hgt[x])
        crack = hash2(x, seed, 21) < 0.055
        crack_from = 1 + int(hash2(x, seed, 25) * 5)
        crack_len = 3 + int(hash2(x, seed, 22) * 10)
        for y in range(max(0, top), h):
            e = h - y                                     # Rows over the foot
            d = y - top
            band = int((e + 1.6 * (fbm(x / 34.0, e / 9.0, seed + 23, 2, wrap=max(1, period // 34)) - 0.5) * 4) // 4)
            k = strata[band % len(strata)]
            if plain:
                k = 1 + (band % 3 == 0)
            left = min((dx for dx in range(1, 7) if h - round(hgt[(x - dx) % period]) > y), default=9)
            right = min((dx for dx in range(1, 9) if h - round(hgt[(x + dx) % period]) > y), default=9)
            if left <= 2:
                k += 2
            elif left <= 5:
                k += 1
            if right <= 3:
                k -= 2
            elif right <= 7:
                k -= 1
            if crack and crack_from <= d <= crack_from + crack_len:
                k -= 1
            col = tone(ramp, k)
            if d == 0:
                col = hx(rim) if right > 3 else tone(ramp, 3)
            elif d == 1 and left > 5 and right > 7 and hash2(x // 3, seed, 24) > 0.5:
                col = tone(ramp, 4)                       # The top's edge, broken
            if haze is not None and e < 20 and dither(x, y, (20 - e) / 20 * 0.7):
                col = hx(haze)
            c.set(x, y, col)


def far_rolling(period: int, seed: int, base: float, amp: float, terms: int = 5) -> list:
    return [base + amp * wave(x, period, seed, terms, base=2) + 1.2 * wave(x, period, seed + 3, 3, base=11)
            for x in range(period)]


def make_far(name: str, t: dict) -> Canvas:
    w, h, _top, _rep = LAYERS['far']
    far, seed = t['far'], seed_of(name) + 100
    c = Canvas(w, h, period=w)
    style = far['style']
    back = plateaus(w, seed, 30, 6, (50, 120), (18, 30), spires=2) if style != 'graves' \
        else far_rolling(w, seed, 44, 9)
    paint_plateaus(c, back, [far['back'][0], far['back'][0], far['back'][1], far['back'][1], far['back'][1]],
                   far['back'][2], seed, plain=True)
    if style == 'graves':                                 # Far hills, and on them the old graveyard's wall
        front = far_rolling(w, seed + 7, 30, 8)
        paint_plateaus(c, front, far['ramp'], far['rim'], seed + 7, far['haze'], plain=True)
        ground = lambda x: h - round(front[x % w]) - 1   # noqa: E731
        dark, lit = tone(far['ramp'], 0), hx(far['rim'])
        rng = Rng(seed + 9)
        chapel = 250                                      # A chapel on the hill: gable, belfry, cross
        g = ground(chapel + 8)
        c.fill(chapel, g - 12, chapel + 16, g, dark)
        for i in range(9):
            c.hline(chapel + i, chapel + 16 - i, g - 13 - i, dark)
        c.set(chapel + 8, g - 21, dark)
        c.fill(chapel + 6, g - 27, chapel + 10, g - 20, dark)
        cross(c, chapel + 8, g - 28, 6, dark, lit)
        c.vline(chapel, g - 12, g, lit)
        c.fill(chapel + 7, g - 25, chapel + 9, g - 23, tone(far['ramp'], 4))
        for x in range(8, w, 1):
            if rng.chance(0.045) and not chapel - 12 < x < chapel + 30:
                if rng.chance(0.5):
                    cross(c, x, ground(x), rng.range(4, 7), dark, lit, rng.range(-1, 1))
                else:
                    headstone(c, x, ground(x), rng.range(2, 3), rng.range(3, 5), dark, lit)
        for x in (70, 410, 590):
            bare_tree(c, x, ground(x), rng.range(16, 22), dark, tone(far['ramp'], 3), seed + x)
        fence_run(c, 120, 230, ground, 4, dark, lit, seed + 11, 6)
        fence_run(c, 470, 560, ground, 4, dark, lit, seed + 12, 6)
        return c
    front = plateaus(w, seed + 7, 12, 4, (60, 150), (30, 54), spires=2)
    paint_plateaus(c, front, far['ramp'], far['rim'], seed + 7, far['haze'])
    if style == 'town':                                   # The town's line in front of the mesas
        town_line(c, far, seed)
    return c


def town_line(c: Canvas, far: dict, seed: int) -> None:
    """The ghost town seen from afar, against the red sky: false fronts and
    gables, the church with its steeple, a water tower, a windmill, a
    gallows; every window dark."""
    h, w = c.h, c.period
    dark, body, lit = tone(far['ramp'], 0), tone(far['ramp'], 1), hx(far['rim'])
    hole = mix(dark, (0, 0, 0), 0.35)
    base = h - 9
    c.fill(0, base, w - 1, h - 1, dark)
    rng = Rng(seed + 60)

    def block(x0: int, wide: int, tall: int, roof: str) -> None:
        top = base - tall
        c.fill(x0, top, x0 + wide - 1, base, body)
        c.vline(x0, top, base, lit)                       # Its lit corner
        c.fill(x0 + wide - 3, top, x0 + wide - 1, base, dark)
        if roof == 'front':                               # A false front: stepped, taller than the house
            c.fill(x0 - 1, top - 4, x0 + wide, top, body)
            c.fill(x0 + wide // 4, top - 7, x0 + wide - wide // 4, top - 4, body)
            c.hline(x0 - 1, x0 + wide, top - 4, lit)
            c.hline(x0 + wide // 4, x0 + wide - wide // 4, top - 7, lit)
        elif roof == 'gable':
            for i in range(wide // 2 + 2):
                c.hline(x0 - 1 + i, x0 + wide - i, top - i, body if i else lit)
                c.set(x0 - 1 + i, top - i, lit)
        else:
            c.hline(x0, x0 + wide - 1, top, lit)
        for wy in range(top + 4, base - 3, 7):            # Windows, all dark; a door
            for wx in range(x0 + 3, x0 + wide - 5, 6):
                if rng.chance(0.75):
                    c.fill(wx, wy, wx + 2, wy + 3, hole)
                    c.hline(wx, wx + 2, wy + 4, lit if rng.chance(0.3) else body)
        c.fill(x0 + wide // 2 - 1, base - 6, x0 + wide // 2 + 1, base, hole)

    x = 6
    while x < w - 40:
        kind = rng.pick(['front', 'gable', 'flat', 'front', 'gap', 'gable'])
        wide = rng.range(16, 30)
        if 262 < x + wide and x < 310 or 468 < x + wide and x < 500 or 600 < x + wide and x < 640:
            x += 12                                       # Room for the church, the tower, the mill
            continue
        if kind != 'gap':
            block(x, wide, rng.range(12, 20), kind)
        x += wide + rng.range(2, 12)
    cx = 276                                              # The church: nave, steeple, cross
    block(cx, 28, 18, 'gable')
    c.fill(cx + 10, base - 44, cx + 17, base - 18, body)
    c.vline(cx + 10, base - 44, base - 18, lit)
    c.fill(cx + 15, base - 44, cx + 17, base - 18, dark)
    c.fill(cx + 12, base - 40, cx + 15, base - 35, hole)
    for i in range(6):
        c.hline(cx + 10 + i // 2 + (i > 3), cx + 17 - i // 2 - (i > 3), base - 45 - i, body)
    cross(c, cx + 13, base - 51, 7, dark, lit)
    tx = 476                                              # The water tower, its legs braced
    c.fill(tx, base - 38, tx + 15, base - 26, body)
    c.vline(tx, base - 38, base - 26, lit)
    c.fill(tx + 13, base - 38, tx + 15, base - 26, dark)
    for i in range(5):
        c.hline(tx - 1 + i * 2, tx + 16 - i * 2, base - 39 - i, body if i else lit)
    for yy in (base - 34, base - 30):
        c.hline(tx, tx + 15, yy, dark)
    for lx in (tx + 1, tx + 14):
        c.vline(lx, base - 25, base, dark)
    c.line(tx + 1, base - 25, tx + 14, base - 1, dark)
    c.line(tx + 14, base - 25, tx + 1, base - 1, dark)
    c.hline(tx - 1, tx + 16, base - 25, lit)
    mx = 616                                              # The windmill: a lattice mast, its wheel, its vane
    for k in range(40):
        spread = (40 - k) // 8
        c.set(mx - spread, base - k, dark)
        c.set(mx + spread, base - k, dark)
        if k % 6 == 0:
            c.hline(mx - spread, mx + spread, base - k, dark)
    for a in range(12):
        ang = a * math.tau / 12 + 0.2
        c.line(mx, base - 42, mx + math.cos(ang) * 7, base - 42 + math.sin(ang) * 7, dark if a % 2 else body)
    c.hline(mx + 2, mx + 12, base - 42, dark)
    c.fill(mx + 9, base - 44, mx + 12, base - 40, body)
    gx = 150                                              # A gallows, its rope still hanging
    c.vline(gx, base - 17, base, dark)
    c.hline(gx, gx + 9, base - 17, dark)
    c.line(gx, base - 12, gx + 4, base - 17, dark)
    c.vline(gx + 8, base - 16, base - 10, body)
    c.hline(gx - 3, gx + 12, base - 5, dark)
    for lx in (gx - 3, gx + 12):
        c.vline(lx, base - 5, base, dark)


# ---- The hills ---------------------------------------------------------------------------------

def rolling(period: int, seed: int, top: float, amp: float, rough: float = 1.0) -> list:
    """The crest's row for each column, repeating every period."""
    return [top + amp * wave(x, period, seed, 5, base=1) + rough * wave(x, period, seed + 5, 4, base=9)
            for x in range(period)]


def paint_hills(c: Canvas, crest: list, spec: dict, seed: int, depths: tuple = (3, 9, 18, 30)) -> None:
    """Land in bands that follow the crest, lighter toward it and on the
    slopes turned to the light, each band's edge broken; the crest's rim."""
    period, h = c.period, c.h
    ramp = spec['ramp']
    for x in range(period):
        top = round(crest[x])
        slope = crest[(x + 3) % period] - crest[(x - 3) % period]   # > 0: falls away to the right, in shade
        for y in range(max(0, top), h):
            d = y - top
            wob = (fbm(x / 22.0, y / 7.0, seed, 2, wrap=max(1, period // 22)) - 0.5) * 7
            k = 4
            for limit in depths:
                if d + wob > limit:
                    k -= 1
            if slope < -0.6 and d < depths[1]:
                k += 1
            elif slope > 0.6 and d < depths[2]:
                k -= 1
            col = tone(ramp, k)
            if d == 0:
                col = hx(spec['crest']) if slope < 0.5 else hx(spec['lit'])
            elif d == 1 and slope < -0.3 and hash2(x // 2, seed, 31) > 0.35:
                col = hx(spec['lit'])
            if d > 1 and hash2(x // 2, y, seed + 33) < 0.085:   # Grain: sand and small stones
                col = tone(ramp, k + (1 if hash2(x // 2, y, seed + 34) < 0.45 else -1))
            c.set(x, y, col)
    rng = Rng(seed + 2)
    for _ in range(period // 2):                          # Marks along the bands: erosion, tracks of water
        x, length = rng.range(0, period - 1), rng.range(4, 14)
        d = rng.range(4, h - 4)
        up = rng.chance(0.5)
        for i in range(length):
            xx = x + i
            y = round(crest[xx % period]) + d + round(i * 0.15)
            old = c.get(xx, y)
            if old is not None and y < h:
                c.set(xx, y, mix(old, tone(ramp, 4 if up else 0), 0.55))


def surface(crest: list, period: int):
    return lambda x: round(crest[x % period])


def stand(c: Canvas, what: str, crest: list, spec: dict, seed: int, scale: float, floor: int) -> None:
    """Puts one kind of thing on the land. scale: how near (1 the far hills, 2
    the near ones); floor: the row below which nothing stands (the road)."""
    period, h = c.period, c.h
    rng = Rng(seed)
    ground = surface(crest, period)
    plant, rock = spec['plant'], spec['rock']
    dark, lit = hx(plant[0]), hx(plant[-1])

    def spot(margin: int = 2):
        """A place on the slope, nearer the crest more often: (x, row)."""
        x = rng.range(0, period - 1)
        g = ground(x)
        y = g + margin + int((rng.unit() ** 1.6) * max(1, floor - g - margin - 2))
        return x, min(y, floor)

    if what == 'saguaros':
        for _ in range(int(16 * scale)):
            x = rng.range(0, period - 1)
            saguaro(c, x, ground(x), rng.range(5, 10), tone(spec['ramp'], 0), hx(spec['lit']))
    elif what == 'outcrops':
        for _ in range(int(9 * scale)):
            x, y = spot()
            boulder(c, x, y, rng.range(7, 16), rng.range(3, 6), rock, seed + x)
    elif what == 'boulders':
        for _ in range(int(7 * scale)):
            x, y = spot(6)
            boulder(c, x, y, rng.range(8, 20), rng.range(4, 9), rock, seed + x)
    elif what == 'brush':
        for _ in range(int(34 * scale)):
            x, y = spot()
            near = (y - ground(x)) / max(1, floor - ground(x))
            wide = int((3 + rng.range(0, 3)) * (1 + near * scale))
            shrub(c, x, y, wide, max(2, wide * 2 // 3), plant, seed + x)
    elif what == 'grass':
        for _ in range(int(40 * scale)):
            x, y = spot(1)
            tuft(c, x, y, rng.range(2, 5), dark, lit)
        for x in range(0, period, 2):                     # And along the crest, against the sky
            if hash2(x, seed, 41) < 0.3:
                tuft(c, x, ground(x), 2 + int(hash2(x, seed, 42) * 3), dark, lit)
    elif what == 'poles':
        line = lambda x: ground(x) + 5                    # noqa: E731
        pole_line(c, 30, period - 20, line, int(9 * scale), tone(spec['ramp'], 0), hx(spec['lit']), int(40 * scale))
    elif what == 'fence':
        line = lambda x: min(floor, ground(x) + 9)        # noqa: E731
        for x0, x1 in ((40, 190), (300, 420), (520, 690)):
            fence_run(c, x0, x1, line, int(4 * scale), tone(spec['ramp'], 0), hx(spec['lit']), seed + x0, int(6 * scale))
    elif what == 'railing':                               # The graveyard's iron railing along its crest
        for x in range(period):
            g = ground(x)
            if 330 < x < 390:
                continue                                  # Its gate, open
            if x % 3 == 0:
                c.vline(x, g - 7, g, tone(spec['ramp'], 0))
                c.set(x, g - 8, hx(spec['lit']))
            c.set(x, g - 6, tone(spec['ramp'], 0))
            c.set(x, g - 2, tone(spec['ramp'], 0))
        for gx in (329, 391):                             # Gate posts with their urns
            g = ground(gx)
            c.fill(gx - 1, g - 12, gx + 1, g, tone(spec['ramp'], 0))
            c.vline(gx - 1, g - 12, g, hx(spec['lit']))
            c.hline(gx - 2, gx + 2, g - 13, hx(spec['lit']))
    elif what == 'graves':
        stone = [hx(v) for v in rock]
        for _ in range(int(46 * scale)):
            x, y = spot(3)
            near = (y - ground(x)) / max(1, floor - ground(x))
            size = 1 + near * scale
            if rng.chance(0.45):
                cross(c, x, y, int(rng.range(5, 8) * size), stone[0], stone[2], rng.range(-1, 1))
            else:
                wide = int(rng.range(3, 4) * size)
                headstone(c, x, y, wide, int(rng.range(4, 6) * size), stone[1], stone[2])
                c.hline(x - 1, x + wide + 2, y + 1, stone[0])     # Its shadow, its mound
    elif what == 'trees':
        for x in (60, 228, 446, 610):
            bare_tree(c, x, ground(x) + 2, rng.range(26, 36), tone(spec['ramp'], 0), hx(spec['lit']), seed + x)
    elif what == 'bones':
        bone = hx(rock[2])
        for _ in range(int(3 * scale)):                   # A steer's ribs in the sand
            x, y = spot(8)
            for i in range(5):
                c.vline(x + i * 2, y - 4 + abs(i - 2), y, bone if i % 2 == 0 else hx(rock[1]))
            c.hline(x - 1, x + 9, y - 5, hx(rock[1]))
    elif what == 'shacks':                                # The town's back yards: sheds, fences, an outhouse
        dark2, body, lit2 = tone(spec['ramp'], 0), tone(spec['ramp'], 2), hx(spec['lit'])
        hole = mix(dark2, (0, 0, 0), 0.4)
        for x0 in range(20, period - 40, 86):
            x = x0 + rng.range(0, 30)
            g = max(ground(x + k) for k in range(0, 26, 5)) + 2
            wide, tall = rng.range(18, 28), rng.range(10, 15)
            c.fill(x, g - tall, x + wide, g, body)
            for xx in range(x, x + wide + 1, 3):          # Boards
                c.vline(xx, g - tall + 1, g, dark2)
            c.vline(x, g - tall, g, lit2)
            for i in range(wide // 2 + 3):                # A roof sagging in
                yy = g - tall - 1 - i // 2 + (2 if abs(i - wide // 3) < 3 else 0)
                c.hline(x - 2 + i, x + wide + 2 - i, yy, dark2 if i else lit2)
            c.fill(x + 4, g - 7, x + 7, g, hole)
            c.fill(x + wide - 8, g - tall + 4, x + wide - 5, g - tall + 7, hole)
            ox = x + wide + 8                             # An outhouse leaning
            c.fill(ox, g - 9, ox + 5, g, body)
            c.vline(ox, g - 9, g, lit2)
            c.hline(ox - 1, ox + 6, g - 10, dark2)
            c.set(ox + 3, g - 7, hole)


def make_hills_far(name: str, t: dict) -> Canvas:
    w, h, _top, _rep = LAYERS['hills_far']
    spec, seed = t['mid'], seed_of(name) + 200
    c = Canvas(w, h, period=w)
    crest = rolling(w, seed, 16, 9, 1.4)
    paint_hills(c, crest, spec, seed, (2, 7, 15, 27))
    for i, what in enumerate(spec['stands']):
        stand(c, what, crest, spec, seed + 11 * (i + 1), 1.0, h - 14)
    return c


def make_hills_near(name: str, t: dict) -> Canvas:
    """The last rise before the road. Its foot is the road's far verge: level,
    in the ground's own tones, so what stands behind the road stands on it."""
    w, h, _top, _rep = LAYERS['hills_near']
    spec, seed = t['near'], seed_of(name) + 300
    c = Canvas(w, h, period=w)
    crest = rolling(w, seed, 22, 8, 1.2)
    paint_hills(c, crest, spec, seed, (3, 10, 20, 34))
    for i, what in enumerate(spec['stands']):
        stand(c, what, crest, spec, seed + 13 * (i + 1), 2.0, h - 10)
    ground = t['ground']['ramp']
    for y in range(h - 7, h):                             # The verge
        for x in range(w):
            k = 1 if y < h - 4 else 2
            if hash2(x // 3, y, seed + 9) < 0.2:
                k += 1 if hash2(x // 3, y, seed + 10) < 0.5 else -1
            edge = (fbm(x / 12.0, 0.0, seed + 8, 2, wrap=w // 12) - 0.5) * 4
            if y - (h - 7) >= edge:
                c.set(x, y, tone(ground, k))
    return c


# ---- The road ----------------------------------------------------------------------------------

def make_ground(name: str, t: dict) -> Canvas:
    """Packed earth: the lit line they walk on, then the road darkening
    toward the viewer, its ruts, its stones with their lit tops and their
    shadows, cracks, dry tufts."""
    w, h, _top, _rep = LAYERS['ground']
    g, seed = t['ground'], seed_of(name) + 400
    c = Canvas(w, h, period=w)
    ramp = g['ramp']
    for y in range(h):
        for x in range(w):
            if y < 2:
                col = hx(g['line'][y])
                if y == 1 and hash2(x // 2, 0, seed) < 0.16:
                    col = tone(ramp, 3)
            else:
                wob = (fbm(x / 26.0, y / 5.0, seed, 3, wrap=max(1, w // 26)) - 0.5) * 9
                k = 3 if y + wob < 5 else 2 if y + wob < 13 else 1 if y + wob < 23 else 0
                if hash2(x // 2, y, seed + 1) < 0.10:     # Grain
                    k += 1 if hash2(x, y, seed + 2) < 0.5 else -1
                col = tone(ramp, k)
            c.set(x, y, col)
    rng = Rng(seed + 3)
    for r in range(g.get('ruts', 2)):                     # Wheel ruts: a dark groove, a lit lip over it
        y0 = 6 + r * 8 + rng.range(0, 2)
        for x in range(w):
            y = y0 + round(1.5 * wave(x, w, seed + 20 + r, 3))
            if hash2(x // 9, r, seed + 4) < 0.16:
                continue                                  # Worn away in places
            c.set(x, y, tone(ramp, 0))
            c.set(x, y - 1, tone(ramp, 4 if (x // 3) % 2 else 3))
    for _ in range(g.get('cracks', 10)):
        x, y = rng.range(0, w - 1), rng.range(4, h - 3)
        for i in range(rng.range(5, 14)):
            c.set(x + i, y, tone(ramp, 0))
            if rng.chance(0.35):
                y += rng.pick([-1, 1])
            if not 3 < y < h - 1:
                break
    for _ in range(g.get('stones', 30)):                  # Stones: lit top, body, a shadow to their right
        x, y = rng.range(0, w - 1), rng.range(4, h - 2)
        wide = rng.range(2, 5 if y > 12 else 3)
        c.hline(x, x + wide - 1, y, hx(g['stone']))
        c.hline(x, x + wide - 1, y + 1, tone(ramp, 3))
        c.set(x + wide, y + 1, tone(ramp, 0))
        if wide > 3:
            c.hline(x + 1, x + wide - 2, y - 1, hx(g['stone']))
            c.hline(x + 1, x + wide, y + 2, tone(ramp, 0))
    for _ in range(g.get('tufts', 12)):
        x, y = rng.range(0, w - 1), rng.range(8, h - 1)
        tuft(c, x, y, rng.range(2, 4), tone(ramp, 0), tone(ramp, 4))
    if g.get('leaves'):                                   # Fallen leaves
        for _ in range(40):
            x, y = rng.range(0, w - 1), rng.range(3, h - 1)
            c.set(x, y, hx(g['leaves']))
            if rng.chance(0.5):
                c.set(x + 1, y, mix(hx(g['leaves']), (0, 0, 0), 0.3))
    return c
