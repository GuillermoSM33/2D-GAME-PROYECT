"""The second route's land, for tools/make_landscape.py: Santa Brasa's
outskirts at dawn (afueras), its downtown on a smoggy afternoon (centro),
the rail yard at dusk (vias), downtown by night (ciudad_noche) and the army
post under its alarm (base_militar).

Buildings are built, not stamped: each has a lit corner and a shaded one, a
roof line with what stands on it, floors, windows with their sills, and its
own wear. Lit windows only show above the heads; behind the bodies the town
is dark. Light comes from the upper left, as on every sprite.
"""
from __future__ import annotations

import math

from landscape_kit import LAYERS, Canvas, Rng, dither, fbm, hash2, hx, mix, seed_of, wave
from landscape_west import (boulder, far_rolling, fence_run, paint_hills, paint_plateaus, plateaus, pole_line, rolling,
                            shrub, tone, tuft)

THEMES = {
    'afueras': {
        'sky': {
            'stops': [(0, 0x221a22), (46, 0x2a1e2a), (66, 0x3a2638), (90, 0x522f44), (110, 0x6e3a4c),
                      (126, 0x8c4652), (140, 0xab5a52), (154, 0xc87050), (168, 0xe08a58)],
            'orb': {'kind': 'sun', 'at': (144, 124), 'r': 15, 'glow': 14,
                    'colors': [0xe8904a, 0xf6b468, 0xfcd890], 'bars': [(6, -20, 24, 13)]},
            'clouds': [
                {'seed': 61, 'y': 82, 'spread': 9, 'count': 5, 'len': (60, 130), 'thick': (4, 7),
                 'colors': [0x2e2030, 0x3a283a, 0x463044, 0x8a4a5a, 0xb06068]},
                {'seed': 62, 'y': 114, 'spread': 8, 'count': 6, 'len': (44, 100), 'thick': (3, 5),
                 'colors': [0x5a3246, 0x6a3a4c, 0x7e4452, 0xe08a60, 0xffb878], 'near_light': 0xffd090},
                {'seed': 63, 'y': 144, 'spread': 5, 'count': 6, 'len': (30, 70), 'thick': (2, 3),
                 'colors': [0x8c4652, 0xa05252, 0xb86052, 0xf0a060, 0xffd088]},
            ],
            'birds': [(350, 92, 5, 0x2e2030)],
        },
        'far': {'ramp': [0x4a2a3a, 0x5a3442, 0x6a3d4a, 0x7c4a52, 0x8e5658], 'rim': 0xb86a5c, 'hole': 0x3a2230,
                'back': [0x8a4a52, 0x985456, 0xd07a5a], 'haze': 0x7a4450, 'lit': None},
        'mid': {'ramp': [0x2e1c28, 0x36202c, 0x40263a, 0x46283a, 0x543244], 'rim': 0x8a4a46, 'hole': 0x22141e,
                'roof': [0x3a2030, 0x4e2a38, 0x623440], 'leaf': [0x241a22, 0x3a2a30, 0x54383a], 'lit': None},
        'near': {'ramp': [0x1a1216, 0x1e1418, 0x261920, 0x2e1e26, 0x3a2630], 'rim': 0x54323a, 'lit': 0x402a32,
                 'crest': 0x54323a, 'plant': [0x1a141a, 0x2a1e24, 0x3e2a2e], 'rock': [0x241a20, 0x3a2a32, 0x58404a]},
        'ground': {'kind': 'asphalt', 'line': [0x8a7a6e, 0x6e6258], 'ramp': [0x1e1a1c, 0x2a2426, 0x322a2c, 0x3e3436, 0x4a4042],
                   'mark': 0x7a6a4a, 'walk': [0x4a3e40, 0x5c4e4e, 0x6e5e5a]},
    },
    'centro': {
        'sky': {
            'stops': [(0, 0x1e1c1c), (46, 0x262222), (66, 0x3a3030), (90, 0x483834), (110, 0x584238),
                      (126, 0x6a4c3c), (140, 0x7e5840), (154, 0x9a6a46), (168, 0xae7a50)],
            'roll': 6.0,
            'orb': {'kind': 'sun', 'at': (150, 86), 'r': 11, 'glow': 20,
                    'colors': [0xb08860, 0xc89c70, 0xd8b488], 'bars': [(2, -18, 18, 5), (6, -12, 22, 6)]},
            'clouds': [
                {'seed': 71, 'y': 76, 'spread': 6, 'count': 4, 'len': (120, 220), 'thick': (2, 4),
                 'colors': [0x2e2828, 0x3a3230, 0x443832, 0x5c4638, 0x6e5440], 'glint': False},
                {'seed': 72, 'y': 118, 'spread': 8, 'count': 5, 'len': (100, 200), 'thick': (2, 4),
                 'colors': [0x4a3a34, 0x584238, 0x624a3c, 0x866446, 0x9c764e], 'glint': False},
                {'seed': 73, 'y': 146, 'spread': 5, 'count': 5, 'len': (80, 160), 'thick': (2, 3),
                 'colors': [0x6a4c3c, 0x76543e, 0x845e42, 0xae8052, 0xc49460], 'glint': False},
            ],
            'birds': [(300, 100, 4, 0x2e2828)],
        },
        'far': {'ramp': [0x3e302e, 0x4a3a36, 0x56423c, 0x624c42, 0x70584a], 'rim': 0x8a6c52, 'hole': 0x32282a,
                'back': [0x74583e, 0x80644a, 0xa88458], 'haze': 0x6a5040, 'lit': None},
        'mid': {'ramp': [0x261e1e, 0x2e2424, 0x362a28, 0x3e302e, 0x4a3a36], 'rim': 0x6a5040, 'hole': 0x1c1616,
                'roof': [0x2a2020, 0x3a2c2a, 0x4a3a34], 'leaf': [0x201a18, 0x302820, 0x443a2a], 'lit': None},
        'near': {'ramp': [0x161212, 0x1a1414, 0x221a1a, 0x2a2020, 0x342828], 'rim': 0x4a3a34, 'lit': 0x3a2e2a,
                 'crest': 0x4a3a34, 'plant': [0x181412, 0x26201a, 0x3a3022], 'rock': [0x201a1a, 0x362e2c, 0x504642]},
        'ground': {'kind': 'asphalt', 'line': [0x8c8478, 0x6c6660], 'ramp': [0x1a1819, 0x262224, 0x2e2a2a, 0x3a3534, 0x464040],
                   'mark': 0x8a847a, 'walk': [0x4a4442, 0x5e5650, 0x70685e]},
    },
    'vias': {
        'sky': {
            'stops': [(0, 0x241a18), (46, 0x2c1e1e), (66, 0x3c2228), (90, 0x5a2a2c), (110, 0x7a3430),
                      (126, 0xa04230), (140, 0xc45a2e), (154, 0xe07a34), (168, 0xf09a44)],
            'orb': {'kind': 'sun', 'at': (168, 130), 'r': 18, 'glow': 15,
                    'colors': [0xf09040, 0xf8b058, 0xffd078], 'bars': [(3, -26, 26, 13), (10, -20, 30, 14)]},
            'clouds': [
                {'seed': 81, 'y': 80, 'spread': 10, 'count': 5, 'len': (70, 150), 'thick': (4, 8),
                 'colors': [0x2a1a1e, 0x362024, 0x44262a, 0x8a3a30, 0xb04c32]},
                {'seed': 82, 'y': 114, 'spread': 8, 'count': 6, 'len': (50, 110), 'thick': (3, 6),
                 'colors': [0x4a2428, 0x5a2a2c, 0x70302e, 0xe06a30, 0xffa040], 'near_light': 0xffc060},
                {'seed': 83, 'y': 146, 'spread': 5, 'count': 7, 'len': (30, 80), 'thick': (2, 3),
                 'colors': [0xa04230, 0xb04c30, 0xc45a2e, 0xffa848, 0xffd070]},
            ],
            'birds': [(360, 90, 5, 0x2a1a1e)],
        },
        'far': {'ramp': [0x4c2628, 0x5e2e2e, 0x6e3634, 0x7e3e38, 0x90483c], 'rim': 0xc8643c, 'hole': 0x3c1e22,
                'back': [0x9c4630, 0xac5234, 0xe4803c], 'haze': 0x8a4030, 'lit': None},
        'mid': {'ramp': [0x2c1819, 0x381e20, 0x422224, 0x4c2628, 0x5c2e2e], 'rim': 0x9c4e34, 'hole': 0x200f12,
                'roof': [0x381c1e, 0x4c2626, 0x603030], 'leaf': [0x241616, 0x3a2420, 0x52342a], 'lit': None},
        'near': {'ramp': [0x160c0e, 0x1c1012, 0x26161a, 0x2e1a1c, 0x3a2224], 'rim': 0x5a3028, 'lit': 0x422622,
                 'crest': 0x5a3028, 'plant': [0x1a1010, 0x2c1c16, 0x44281c], 'rock': [0x24161a, 0x402a28, 0x60403a]},
        'ground': {'kind': 'rails', 'line': [0x9a8c80, 0x6a5e56], 'ramp': [0x201a18, 0x2c2422, 0x3a302c, 0x4a403a, 0x5c5048],
                   'mark': 0x4a3226, 'tie': [0x2e1e16, 0x4a3226, 0x60442e], 'steel': [0x3a3634, 0x6a6460, 0xb0a89e]},
    },
    'ciudad_noche': {
        'sky': {
            'stops': [(0, 0x0c0c16), (48, 0x0e0e1a), (70, 0x12121e), (92, 0x181828), (112, 0x1e1e32),
                      (130, 0x262640), (146, 0x30304c), (166, 0x45405e)],
            'orb': {'kind': 'moon', 'at': (150, 82), 'r': 10, 'glow': 9,
                    'colors': [0x70727e, 0xa7a8a8, 0xd7d1bd, 0xe8e2cc], 'craters': [(-3, -2, 2.2), (3, 3, 1.8)]},
            'stars': [{'count': 90, 'bottom': 118, 'dim_above': 52, 'colors': [0x34344c, 0x5a5a78, 0x8a8aa0, 0xc8c8d4]}],
            'clouds': [
                {'seed': 91, 'y': 96, 'spread': 10, 'count': 4, 'len': (80, 160), 'thick': (4, 7),
                 'colors': [0x0e0e18, 0x141422, 0x1a1a2c, 0x30304a, 0x44446a], 'near_light': 0x6a6a8c},
                {'seed': 92, 'y': 138, 'spread': 7, 'count': 6, 'len': (60, 130), 'thick': (3, 5),
                 'colors': [0x1e1e32, 0x262640, 0x2e2e4a, 0x524c70, 0x6a6084]},
            ],
        },
        'far': {'ramp': [0x161626, 0x1e1e30, 0x24243a, 0x2c2c46, 0x363652], 'rim': 0x4a4a6a, 'hole': 0x10101c,
                'back': [0x2e2c48, 0x363454, 0x56527a], 'haze': 0x2a2a44, 'lit': [0x8a7040, 0xc8a050, 0x5a7a9a]},
        'mid': {'ramp': [0x0e0e18, 0x141420, 0x1a1a2a, 0x202034, 0x282840], 'rim': 0x3a3a56, 'hole': 0x08080e,
                'roof': [0x12121c, 0x1c1c2c, 0x28283c], 'leaf': [0x0c0e14, 0x161c22, 0x222a30],
                'lit': [0x8a7040, 0xc8a050, 0x5a7a9a]},
        'near': {'ramp': [0x08080e, 0x0a0a12, 0x0e0e18, 0x121220, 0x1a1a2a], 'rim': 0x2c2c44, 'lit': 0x202034,
                 'crest': 0x2c2c44, 'plant': [0x0a0c10, 0x12181c, 0x1e262a], 'rock': [0x101018, 0x22222e, 0x383848]},
        'ground': {'kind': 'asphalt', 'line': [0x6a6670, 0x4e4a56], 'ramp': [0x100f15, 0x18161e, 0x1e1c24, 0x282630, 0x32303c],
                   'mark': 0x5e5a4e, 'walk': [0x2c2a36, 0x3a3846, 0x484656], 'wet': [0x2c2a3e, 0x44425e, 0x6a6884]},
        'fog': {'color': 0x3a3a52, 'alpha': (40, 80)},
    },
    'base_militar': {
        'sky': {
            'stops': [(0, 0x120a0c), (48, 0x160c0e), (70, 0x1a0e12), (92, 0x261216), (112, 0x34161a),
                      (130, 0x48181a), (146, 0x62201c), (166, 0x8a2c1e)],
            'orb': {'kind': 'moon', 'at': (132, 78), 'r': 9, 'glow': 8,
                    'colors': [0x7a6c62, 0xa89480, 0xd0c4a8, 0xe0d8c0], 'craters': [(-2, -2, 2), (3, 2, 1.6)]},
            'stars': [{'count': 60, 'bottom': 112, 'dim_above': 52, 'colors': [0x4a2c2c, 0x6e4444, 0x9a6a62, 0xc8a090]}],
            'clouds': [
                {'seed': 101, 'y': 94, 'spread': 10, 'count': 4, 'len': (80, 170), 'thick': (4, 8),
                 'colors': [0x140a0c, 0x1c0e10, 0x261214, 0x4a1a1a, 0x66241e], 'near_light': 0x8a5a4a},
                {'seed': 102, 'y': 136, 'spread': 7, 'count': 6, 'len': (50, 120), 'thick': (3, 5),
                 'colors': [0x30141a, 0x3e181a, 0x4c1c1c, 0x8a3020, 0xb04428]},
            ],
            'beams': [(300, 176, -0.38, 150, 0x6a2e28), (410, 176, 0.3, 130, 0x6a2e28)],
        },
        'far': {'ramp': [0x24100f, 0x2e1618, 0x3a1c1e, 0x462224, 0x54292a], 'rim': 0x7a3630, 'hole': 0x180a0a,
                'back': [0x54201c, 0x602620, 0x8e3a26], 'haze': 0x4a1e1c, 'lit': [0x8a3a24, 0xd05a30, 0xe8c070]},
        'mid': {'ramp': [0x160a0c, 0x1e0e10, 0x241214, 0x2a1416, 0x361a1c], 'rim': 0x5a2824, 'hole': 0x0c0506,
                'roof': [0x1c0c0e, 0x2a1416, 0x3a1c1e], 'leaf': [0x140a0a, 0x241412, 0x38201a],
                'lit': [0x8a3a24, 0xd05a30, 0xe8c070]},
        'near': {'ramp': [0x0c0607, 0x10080a, 0x160a0c, 0x1c0c0e, 0x261214], 'rim': 0x3e1c1a, 'lit': 0x2e1416,
                 'crest': 0x3e1c1a, 'plant': [0x100808, 0x1e100e, 0x301a16], 'rock': [0x180c0e, 0x301a1a, 0x4a2c28]},
        'ground': {'kind': 'slabs', 'line': [0x7e7066, 0x5e544c], 'ramp': [0x181412, 0x26201e, 0x2e2826, 0x3a3230, 0x483e3a],
                   'mark': 0x1a1614, 'paint': [0x5a4a2a, 0x7a6434]},
        'fog': {'color': 0x4a2626, 'alpha': (40, 80)},
    },
}


# ---- Buildings ---------------------------------------------------------------------------------

def block(c: Canvas, x0: int, wide: int, top: int, base: int, pal: dict, rng: Rng, *, body: int = 2,
          win: tuple = (2, 2, 4, 5), roof: str = 'flat', lit_above: int = -1, style: str = 'grid') -> None:
    """A building from top to base: a lit left corner, a shaded right one,
    its floors, its windows (win: width, height, pitch across, pitch down)
    dark with a sill, some lit where lit_above allows (rows over that), and
    what its roof carries."""
    ramp = pal['ramp']
    main, light, dark = tone(ramp, body), tone(ramp, body + 1), tone(ramp, body - 1)
    hole, rim = hx(pal['hole']), hx(pal['rim'])
    lights = [hx(v) for v in pal['lit']] if pal.get('lit') else []
    x1 = x0 + wide - 1
    c.fill(x0, top, x1, base, main)
    shade_w = max(2, wide // 6)
    c.fill(x1 - shade_w + 1, top, x1, base, dark)            # The side away from the light
    c.vline(x0, top, base, light)
    if wide > 12:
        c.vline(x0 + 1, top + 1, base, light)
    c.hline(x0, x1, top, rim)
    ww, wh, px, py = win
    if style == 'bands':                                     # Ribbon windows: a dark band a floor
        for y in range(top + 3, base - 2, py):
            c.fill(x0 + 2, y, x1 - shade_w, y + wh - 1, hole)
            for x in range(x0 + 2, x1 - shade_w, px):
                c.vline(x, y, y + wh - 1, main)
                if lights and y < lit_above and rng.chance(0.22):
                    c.fill(x + 1, y, x + px - 1, y + wh - 1, rng.pick(lights[:2]))
    elif style != 'blank':
        for y in range(top + 3, base - wh - 1, py):
            if py >= 7:
                c.hline(x0 + 1, x1 - shade_w, y + wh + 1, dark)     # The floor's line
            for x in range(x0 + 2, x1 - ww - 1, px):
                if rng.chance(0.14):
                    continue                                 # A blind bay
                in_shade = x > x1 - shade_w - ww
                glow = lights and y + wh < lit_above and rng.chance(0.16) and not in_shade
                col = rng.pick(lights) if glow else hole
                c.fill(x, y, x + ww - 1, y + wh - 1, col)
                if glow and wh > 2:
                    c.hline(x, x + ww - 1, y + wh - 1, mix(col, hole, 0.35))
                elif not glow and ww > 2 and rng.chance(0.3):
                    c.set(x, y, mix(hole, light, 0.3))       # A pane catching the sky
                if wh >= 3 and not in_shade:
                    c.hline(x, x + ww - 1, y + wh, light)    # Sill
    if roof == 'parapet':
        c.hline(x0 - 1, x1 + 1, top - 1, main)
        c.hline(x0 - 1, x1 + 1, top - 2, rim)
        c.set(x1 + 1, top - 1, dark)
    elif roof == 'tank':                                     # A water tank on its legs
        tx = x0 + wide // 2 - 4 + rng.range(-2, 2)
        c.fill(tx, top - 10, tx + 7, top - 4, main)
        c.vline(tx, top - 10, top - 4, light)
        c.fill(tx + 6, top - 10, tx + 7, top - 4, dark)
        c.hline(tx, tx + 7, top - 7, dark)
        for i in range(3):
            c.hline(tx + i, tx + 7 - i, top - 11 - i, rim if i == 0 else main)
        for lx in (tx + 1, tx + 6):
            c.vline(lx, top - 3, top - 1, dark)
    elif roof == 'antenna':
        ax = x0 + wide // 2 + rng.range(-3, 3)
        tall = rng.range(8, 16)
        c.vline(ax, top - tall, top - 1, dark)
        for k in range(3, tall, 4):
            c.hline(ax - 1, ax + 1, top - k, dark)
        c.set(ax, top - tall - 1, hx(pal['lit'][1]) if pal.get('lit') else rim)
    elif roof == 'setback':                                  # A narrower storey on top, a bulkhead
        inset = max(3, wide // 5)
        c.fill(x0 + inset, top - 7, x1 - inset, top - 1, main)
        c.vline(x0 + inset, top - 7, top - 1, light)
        c.fill(x1 - inset - 1, top - 7, x1 - inset, top - 1, dark)
        c.hline(x0 + inset, x1 - inset, top - 7, rim)
        for x in range(x0 + inset + 2, x1 - inset - 2, 4):
            c.fill(x, top - 5, x + 1, top - 3, hole)
    elif roof == 'units':                                    # Air units, a stair head
        c.fill(x0 + 2, top - 3, x0 + 6, top - 1, dark)
        c.hline(x0 + 2, x0 + 6, top - 3, main)
        c.fill(x1 - 7, top - 5, x1 - 3, top - 1, main)
        c.vline(x1 - 7, top - 5, top - 1, light)
        c.hline(x1 - 7, x1 - 3, top - 5, rim)
    elif roof == 'sign':                                     # A billboard's frame on the roof
        c.fill(x0 + 2, top - 9, x1 - 2, top - 3, dark)
        c.fill(x0 + 3, top - 8, x1 - 3, top - 4, main)
        c.hline(x0 + 2, x1 - 2, top - 9, rim)
        for lx in range(x0 + 4, x1 - 3, 6):
            c.vline(lx, top - 2, top - 1, dark)
    elif roof == 'gable':
        for i in range(wide // 2 + 2):
            y = top - 1 - i * 2 // 3
            c.hline(x0 - 1 + i, x1 + 1 - i, y, tone(pal.get('roof', ramp), 1))
            c.set(x0 - 1 + i, y, rim)
            c.set(x1 + 1 - i, y, tone(pal.get('roof', ramp), 0))


def skyline(c: Canvas, pal: dict, seed: int, base: int, tall: tuple, wide: tuple, lit_above: int,
            body: int = 2, gap: tuple = (0, 3), win: tuple = (2, 2, 4, 5), roofs: tuple | None = None) -> None:
    """Buildings side by side along the whole layer."""
    rng = Rng(seed)
    roofs = roofs or ('flat', 'parapet', 'tank', 'antenna', 'setback', 'units', 'flat', 'sign')
    x = -rng.range(0, 8)
    while x < c.period - 6:
        w = min(rng.range(*wide), c.period - x)
        h = rng.range(*tall)
        style = 'bands' if rng.chance(0.2) and w > 16 else 'grid'
        block(c, x, w, base - h, base, pal, rng, body=body + rng.range(-1, 0), win=win, roof=rng.pick(roofs),
              lit_above=lit_above, style=style)
        x += w + rng.range(*gap)


def tree(c: Canvas, x: int, base: int, tall: int, leaf: list, trunk) -> None:
    """A street tree: a trunk and a crown of leaves in clumps, lit on its upper left."""
    c.vline(x, base - tall // 2, base, trunk)
    c.vline(x + 1, base - tall // 2 + 2, base, trunk)
    r = tall * 0.36
    cy = base - tall + r
    for dy in range(-int(r) - 1, int(r) + 2):
        for dx in range(-int(r * 1.3) - 1, int(r * 1.3) + 2):
            d = (dx / (r * 1.3)) ** 2 + (dy / r) ** 2 + (hash2(x + dx, base + dy, 3) - 0.5) * 0.55
            if d > 1.0:
                continue
            light = -dx / (r * 1.3) * 0.5 - dy / r * 0.9
            k = 2 if light > 0.55 else 1 if light > -0.1 else 0
            if hash2((x + dx) // 2, (base + dy) // 2, 5) < 0.25:
                k = max(0, k - 1)
            c.set(x + dx, int(cy + dy), hx(leaf[k]))


def wires(c: Canvas, xs: list, y_of, color, sag: int = 4) -> None:
    for xa, xb in zip(xs, xs[1:]):
        for x in range(xa, xb + 1):
            u = (x - xa) / max(1, xb - xa)
            c.set(x, round(y_of(xa) + (y_of(xb) - y_of(xa)) * u + sag * math.sin(math.pi * u)), color)


# ---- The far land ---------------------------------------------------------------------------------

def make_far(name: str, t: dict) -> Canvas:
    w, h, top, _rep = LAYERS['far']
    far, seed = t['far'], seed_of(name) + 100
    c = Canvas(w, h, period=w)
    back = {**far, 'ramp': [far['back'][0]] * 2 + [far['back'][1]] * 3, 'rim': far['back'][2], 'hole': far['back'][0]}
    heads = 180 - top                                        # Rows of this layer over the heads: all of it
    if name == 'afueras':                                    # Hills, and the town's low line before them
        hills = far_rolling(w, seed, 34, 8)
        paint_plateaus(c, hills, [far['back'][0], far['back'][0], far['back'][1], far['back'][1], far['back'][1]],
                       far['back'][2], seed, plain=True)
        skyline(c, far, seed + 1, h - 1, (10, 20), (14, 30), heads, gap=(2, 14), win=(2, 2, 5, 5),
                roofs=('gable', 'gable', 'flat', 'parapet', 'gable', 'tank'))
        rng = Rng(seed + 2)
        for x in range(10, w, 37):                           # Trees between the roofs
            tree(c, x + rng.range(0, 12), h - 1, rng.range(12, 20), [tone(far['ramp'], 0), tone(far['ramp'], 1),
                                                                    tone(far['ramp'], 3)], tone(far['ramp'], 0))
        steeple(c, 250, h - 1, far)
        water_tower(c, 470, h - 1, far, 34)
        haze_foot(c, far['haze'], 14)
    elif name in ('centro', 'ciudad_noche'):                 # Towers, two rows deep
        skyline(c, back, seed + 1, h - 1, (34, 62), (18, 40), heads, gap=(2, 12), win=(2, 2, 4, 4),
                roofs=('flat', 'antenna', 'setback', 'flat'))
        skyline(c, far, seed + 2, h - 1, (18, 50), (16, 38), heads, gap=(0, 6), win=(2, 3, 5, 6))
        crane(c, 420, h - 30, far)
        haze_foot(c, far['haze'], 12)
    elif name == 'vias':                                     # The yard: elevators, silos, stacks, a gantry
        low = far_rolling(w, seed, 20, 4)
        paint_plateaus(c, low, [far['back'][0], far['back'][0], far['back'][1], far['back'][1], far['back'][1]],
                       far['back'][2], seed, plain=True)
        skyline(c, far, seed + 1, h - 1, (8, 16), (24, 50), heads, gap=(6, 30), win=(3, 2, 7, 6),
                roofs=('flat', 'gable', 'units'))
        for x0 in (40, 330, 560):
            elevator(c, x0, h - 1, far, seed + x0)
        for x0, tall in ((190, 58), (204, 46), (640, 54)):
            stack(c, x0, h - 1, tall, far, seed + x0)
        water_tower(c, 276, h - 1, far, 40)
        gantry(c, 440, h - 1, far)
        haze_foot(c, far['haze'], 12)
    else:                                                    # The post: mountains, hangars, the tower, the radar
        peaks = plateaus(w, seed, 26, 5, (30, 90), (18, 34), spires=0)
        paint_plateaus(c, peaks, [far['back'][0], far['back'][0], far['back'][1], far['back'][1], far['back'][1]],
                       far['back'][2], seed, plain=True)
        for hx0 in (20, 110, 520):
            hangar(c, hx0, h - 1, 70, 22, far)
        skyline(c, far, seed + 1, h - 1, (8, 14), (30, 50), heads, gap=(40, 120), win=(3, 2, 6, 6),
                roofs=('flat', 'units', 'antenna'))
        control_tower(c, 300, h - 1, far)
        radar(c, 430, h - 1, far)
        for x0 in (228, 610, 676):                           # Masts with their red lights
            c.vline(x0, h - 46, h - 1, tone(far['ramp'], 0))
            for k in range(6, 46, 8):
                c.hline(x0 - 1, x0 + 1, h - k, tone(far['ramp'], 0))
            c.set(x0, h - 47, hx(far['lit'][1]))
        haze_foot(c, far['haze'], 12)
    return c


def haze_foot(c: Canvas, haze: int, rows: int) -> None:
    for y in range(c.h - rows, c.h):
        for x in range(c.w):
            if c.solid(x, y) and dither(x, y, (y - (c.h - rows)) / rows * 0.6):
                c.set(x, y, hx(haze))


def steeple(c: Canvas, x: int, base: int, pal: dict) -> None:
    body, light, dark, rim = tone(pal['ramp'], 2), tone(pal['ramp'], 3), tone(pal['ramp'], 1), hx(pal['rim'])
    c.fill(x, base - 16, x + 20, base, body)
    for i in range(12):
        c.hline(x - 1 + i, x + 21 - i, base - 17 - i * 2 // 3, dark if i else rim)
    c.fill(x + 7, base - 40, x + 13, base - 22, body)
    c.vline(x + 7, base - 40, base - 22, light)
    c.fill(x + 12, base - 40, x + 13, base - 22, dark)
    c.fill(x + 9, base - 36, x + 11, base - 32, hx(pal['hole']))
    for i in range(7):
        c.hline(x + 7 + i // 2, x + 13 - i // 2, base - 41 - i, dark if i else rim)
    c.vline(x + 10, base - 53, base - 47, dark)
    c.hline(x + 9, x + 11, base - 51, dark)
    c.vline(x, base - 16, base, light)


def water_tower(c: Canvas, x: int, base: int, pal: dict, tall: int) -> None:
    body, light, dark, rim = tone(pal['ramp'], 2), tone(pal['ramp'], 3), tone(pal['ramp'], 0), hx(pal['rim'])
    top = base - tall
    c.fill(x, top, x + 15, top + 11, body)
    c.vline(x, top, top + 11, light)
    c.vline(x + 1, top + 1, top + 11, light)
    c.fill(x + 12, top, x + 15, top + 11, tone(pal['ramp'], 1))
    for y in (top + 3, top + 8):
        c.hline(x, x + 15, y, dark)
    for i in range(5):
        c.hline(x - 1 + i * 2, x + 16 - i * 2, top - 1 - i, body if i else rim)
    c.hline(x - 1, x + 16, top + 12, rim)
    for lx in (x + 1, x + 14):
        c.vline(lx, top + 13, base, dark)
    c.line(x + 1, top + 13, x + 14, base, dark)
    c.line(x + 14, top + 13, x + 1, base, dark)
    c.vline(x + 8, top + 13, base, dark)                      # Its pipe


def crane(c: Canvas, x: int, top: int, pal: dict) -> None:
    """A tower crane left standing over a building half built."""
    dark, body = tone(pal['ramp'], 0), tone(pal['ramp'], 1)
    for y in range(top - 30, c.h):
        c.set(x, y, dark)
        c.set(x + 3, y, dark)
        if (y - top) % 4 == 0:
            c.hline(x, x + 3, y, dark)
        elif (y - top) % 4 == 2:
            c.set(x + 1 + (y // 4) % 2, y, body)
    c.hline(x - 14, x + 46, top - 30, dark)
    for k in range(-14, 46, 4):
        c.set(k + x + 1, top - 31, dark)
        c.set(k + x + 2, top - 32, dark)
    c.hline(x - 14, x + 46, top - 33, body)
    c.fill(x - 14, top - 29, x - 8, top - 25, dark)           # Counterweight
    c.vline(x + 34, top - 29, top - 12, body)                 # Its cable, its hook
    c.fill(x + 33, top - 12, x + 35, top - 10, dark)


def elevator(c: Canvas, x: int, base: int, pal: dict, seed: int) -> None:
    """A grain elevator: a row of silos, a headhouse over them, a leg."""
    body, light, dark, rim, hole = (tone(pal['ramp'], 2), tone(pal['ramp'], 3), tone(pal['ramp'], 1),
                                    hx(pal['rim']), hx(pal['hole']))
    for i in range(5):
        x0 = x + i * 9
        c.fill(x0, base - 34, x0 + 8, base, body)
        c.vline(x0, base - 34, base, light)
        c.vline(x0 + 1, base - 33, base, light)
        c.fill(x0 + 6, base - 34, x0 + 8, base, dark)
        c.hline(x0 + 1, x0 + 7, base - 35, rim)
        for y in range(base - 28, base, 8):
            c.hline(x0, x0 + 8, y, dark)
    c.fill(x + 4, base - 46, x + 40, base - 36, body)
    c.hline(x + 4, x + 40, base - 46, rim)
    c.fill(x + 36, base - 46, x + 40, base - 36, dark)
    for wx in range(x + 8, x + 34, 6):
        c.fill(wx, base - 43, wx + 2, base - 40, hole)
    c.fill(x + 16, base - 58, x + 24, base - 47, body)
    c.vline(x + 16, base - 58, base - 47, light)
    c.hline(x + 16, x + 24, base - 58, rim)
    c.fill(x + 19, base - 55, x + 21, base - 52, hole)
    c.line(x + 46, base, x + 24, base - 50, dark)             # Its spout down to the track


def stack(c: Canvas, x: int, base: int, tall: int, pal: dict, seed: int) -> None:
    """A smokestack with its bands, a thread of smoke leaning with the wind."""
    body, light, dark = tone(pal['ramp'], 1), tone(pal['ramp'], 3), tone(pal['ramp'], 0)
    for y in range(base - tall, base + 1):
        half = 1 + (y - (base - tall)) // 22
        c.hline(x - half, x + half + 1, y, body)
        c.set(x - half, y, light)
        c.set(x + half + 1, y, dark)
        if (y - base) % 9 == 0:
            c.hline(x - half, x + half + 1, y, dark)
    smoke = mix(hx(pal['back'][0]), hx(pal['ramp'][1]), 0.5)
    for k in range(26):
        sx, sy = x + 1 + k + int(2 * math.sin(k * 0.5)), base - tall - 2 - k // 3
        for d in range(1 + k // 6):
            if hash2(sx + d, sy, seed) > 0.25:
                c.set(sx + d, sy - d % 2, smoke)


def gantry(c: Canvas, x: int, base: int, pal: dict) -> None:
    """A signal gantry across the yard's tracks."""
    dark, rim = tone(pal['ramp'], 0), hx(pal['rim'])
    for lx in (x, x + 60):
        c.fill(lx, base - 26, lx + 1, base, dark)
    c.fill(x, base - 28, x + 61, base - 26, dark)
    c.hline(x, x + 61, base - 28, rim)
    for k in range(x + 4, x + 58, 6):
        c.line(k, base - 26, k + 3, base - 23, dark)
        c.line(k + 3, base - 23, k + 6, base - 26, dark)
    for k in range(x + 8, x + 56, 12):
        c.fill(k, base - 22, k + 2, base - 17, dark)
        c.set(k + 1, base - 20, hx(pal['lit'][1]) if pal.get('lit') else rim)


def hangar(c: Canvas, x: int, base: int, wide: int, tall: int, pal: dict) -> None:
    body, light, dark, rim, hole = (tone(pal['ramp'], 2), tone(pal['ramp'], 3), tone(pal['ramp'], 1),
                                    hx(pal['rim']), hx(pal['hole']))
    for i in range(wide):
        y = base - round(tall * math.sin(math.pi * (i + 0.5) / wide) ** 0.55)
        c.vline(x + i, y, base, body if i < wide * 0.7 else dark)
        c.set(x + i, y, rim if i < wide * 0.6 else light)
        if i % 7 == 3 and i < wide * 0.7:
            c.vline(x + i, y + 1, base, dark)                 # Its ribs
    door = wide // 3
    c.fill(x + door, base - tall + 8, x + wide - door, base, hole)
    for k in range(x + door, x + wide - door, 5):
        c.vline(k, base - tall + 8, base, dark)
    c.hline(x + door, x + wide - door, base - tall + 8, light)


def control_tower(c: Canvas, x: int, base: int, pal: dict) -> None:
    body, light, dark, rim = tone(pal['ramp'], 2), tone(pal['ramp'], 3), tone(pal['ramp'], 1), hx(pal['rim'])
    c.fill(x + 3, base - 40, x + 10, base, body)
    c.vline(x + 3, base - 40, base, light)
    c.fill(x + 9, base - 40, x + 10, base, dark)
    for y in range(base - 34, base, 8):
        c.hline(x + 3, x + 10, y, dark)
    c.fill(x - 1, base - 51, x + 14, base - 41, body)        # Its cab, glass all round, lit
    c.hline(x - 2, x + 15, base - 52, rim)
    c.fill(x, base - 49, x + 13, base - 45, hx(pal['lit'][2]) if pal.get('lit') else hx(pal['hole']))
    for k in range(x + 2, x + 13, 3):
        c.vline(k, base - 49, base - 45, dark)
    c.hline(x - 2, x + 15, base - 41, dark)
    c.vline(x + 6, base - 62, base - 53, dark)
    c.set(x + 6, base - 63, hx(pal['lit'][1]) if pal.get('lit') else rim)


def radar(c: Canvas, x: int, base: int, pal: dict) -> None:
    body, light, dark, rim = tone(pal['ramp'], 2), tone(pal['ramp'], 3), tone(pal['ramp'], 0), hx(pal['rim'])
    c.fill(x - 6, base - 12, x + 7, base, body)
    c.vline(x - 6, base - 12, base, light)
    c.hline(x - 6, x + 7, base - 12, rim)
    c.fill(x, base - 30, x + 1, base - 13, dark)
    for i in range(-11, 12):                                  # The dish, turned to the left
        y = base - 34 + (i * i) // 9
        c.set(x + i, y, rim if i < 0 else light)
        c.set(x + i, y + 1, body)
        if i % 4 == 0:
            c.vline(x + i, y + 1, base - 30 + abs(i) // 6, dark)
    c.line(x, base - 30, x - 4, base - 42, dark)
    c.set(x - 4, base - 43, light)


# ---- The town behind the road ------------------------------------------------------------------------

def make_hills_far(name: str, t: dict) -> Canvas:
    w, h, top, _rep = LAYERS['hills_far']
    mid, seed = t['mid'], seed_of(name) + 200
    c = Canvas(w, h, period=w)
    heads = 180 - top                                        # Rows of this layer still over the heads
    base = h - 1
    rng = Rng(seed)
    if name == 'afueras':
        suburb(c, mid, seed, base, heads)
    elif name in ('centro', 'ciudad_noche'):
        skyline(c, mid, seed + 1, base, (36, 62), (34, 70), heads, gap=(0, 5), win=(4, 5, 8, 9),
                roofs=('parapet', 'tank', 'units', 'setback', 'sign', 'flat', 'antenna'))
        for x in range(0, w, 3):                             # Along the street: awnings, doors, shutters
            pass
        street_level(c, mid, seed + 2, base)
    elif name == 'vias':
        siding(c, mid, seed, base)
    else:
        perimeter(c, mid, seed, base, heads)
    _ = rng
    return c


def suburb(c: Canvas, pal: dict, seed: int, base: int, heads: int) -> None:
    """Houses of the outskirts: gabled roofs in rows of shingles, chimneys,
    sash windows, porches, garages, fences between them, trees, and the
    poles with their wires above."""
    rng = Rng(seed + 1)
    ramp, roof = pal['ramp'], pal['roof']
    hole, rim = hx(pal['hole']), hx(pal['rim'])
    c.fill(0, base - 5, c.period - 1, base, tone(ramp, 0))
    x = 4
    while x < c.period - 30:
        wide = rng.range(34, 58)
        if x + wide > c.period - 2:
            break
        wall = rng.range(15, 22)
        peak = rng.range(10, 16)
        top = base - wall
        body = rng.range(2, 3)
        c.fill(x, top, x + wide - 1, base, tone(ramp, body))
        c.fill(x + wide - wide // 5, top, x + wide - 1, base, tone(ramp, body - 1))
        for y in range(top + 2, base, 3):                    # Siding
            c.hline(x + 1, x + wide - 2, y, tone(ramp, body - 1))
        c.vline(x, top, base, tone(ramp, body + 1))
        for i in range(peak + 1):                            # The roof, seen from its side: rows of shingles
            y = top - 1 - i
            inset = i * (wide // 2 - 3) // max(1, peak)
            for xx in range(x - 2 + inset, x + wide + 2 - inset):
                seam = i % 3 == 2 or (xx + (i // 3) * 2) % 5 == 0
                c.set(xx, y, hx(roof[0 if seam else 1 if xx > x + wide * 0.6 else 2]))
            c.set(x - 2 + inset, y, rim)
        c.hline(x - 2, x + wide + 1, top, hx(roof[0]))        # Its eave's shadow
        chim = x + wide // 4 + rng.range(0, wide // 3)
        c.fill(chim, top - peak - 3 + rng.range(0, 4), chim + 3, top - 4, tone(ramp, 1))
        c.vline(chim, top - peak - 3, top - 4, tone(ramp, 3))
        door = x + 5 + rng.range(0, wide - 20)
        c.fill(door, base - 11, door + 4, base, hole)
        c.hline(door - 1, door + 5, base - 12, tone(ramp, body + 1))
        for wx in range(x + 4, x + wide - 9, 11):
            if abs(wx - door) < 7:
                continue
            c.fill(wx, top + 4, wx + 5, top + 10, hole)
            c.vline(wx + 2, top + 4, top + 10, tone(ramp, body))        # Its bars
            c.hline(wx, wx + 5, top + 7, tone(ramp, body))
            c.hline(wx - 1, wx + 6, top + 11, tone(ramp, body + 1))
            if rng.chance(0.25):
                c.set(wx + 1, top + 5, mix(hole, rim, 0.4))
        if rng.chance(0.6):                                  # A porch
            c.fill(x - 3, base - 13, x + 8, base - 12, hx(roof[1]))
            c.vline(x - 3, base - 11, base, tone(ramp, 1))
        gap = rng.range(14, 34)
        gx = x + wide + 2
        if gap > 24:                                         # A tree in the yard
            tree(c, gx + gap // 2, base - 1, rng.range(22, 34), pal['leaf'], tone(ramp, 0))
        for fx in range(gx, gx + gap - 2, 3):                # A picket fence
            c.vline(fx, base - 6, base, tone(ramp, 1))
            c.set(fx, base - 7, tone(ramp, 3))
        c.hline(gx, gx + gap - 3, base - 4, tone(ramp, 1))
        x += wide + gap
    poles = list(range(18, c.period, 62))                    # Poles and their wires over the roofs
    for px in poles:
        c.vline(px, base - 58, base, tone(ramp, 0))
        c.hline(px - 4, px + 4, base - 55, tone(ramp, 0))
        c.hline(px - 3, px + 3, base - 50, tone(ramp, 0))
        c.set(px, base - 59, tone(ramp, 3))
    wires(c, poles + [poles[0] + c.period], lambda _x: base - 55, tone(ramp, 0), 5)
    wires(c, poles + [poles[0] + c.period], lambda _x: base - 50, tone(ramp, 0), 6)


def street_level(c: Canvas, pal: dict, seed: int, base: int) -> None:
    """The foot of the downtown blocks: shop fronts shut, awnings, signs
    without a word left on them, a fire escape or two up the walls."""
    rng = Rng(seed)
    ramp = pal['ramp']
    hole, rim = hx(pal['hole']), hx(pal['rim'])
    x = 2
    while x < c.period - 20:
        wide = rng.range(16, 30)
        kind = rng.range(0, 3)
        c.fill(x, base - 13, x + wide, base, tone(ramp, 1))
        if kind == 0:                                        # A shutter, ribbed
            for y in range(base - 11, base, 2):
                c.hline(x + 2, x + wide - 2, y, tone(ramp, 0))
        elif kind == 1:                                      # A shop window, dark, taped
            c.fill(x + 2, base - 11, x + wide - 2, base - 3, hole)
            c.line(x + 3, base - 4, x + wide - 3, base - 10, tone(ramp, 2))
        else:                                                # A doorway and a window
            c.fill(x + 2, base - 11, x + 6, base, hole)
            c.fill(x + 9, base - 11, x + wide - 2, base - 5, hole)
        for i in range(wide + 3):                            # The awning, striped, sagging
            y = base - 15 + (1 if (i // 4) % 2 else 0)
            c.set(x - 1 + i, y, tone(ramp, 3 if (i // 3) % 2 else 2))
            c.set(x - 1 + i, y - 1, rim if (i // 3) % 2 else tone(ramp, 2))
        if rng.chance(0.5):                                  # A sign hung out over the pavement
            c.fill(x + wide - 5, base - 26, x + wide - 1, base - 18, tone(ramp, 0))
            c.fill(x + wide - 4, base - 25, x + wide - 2, base - 19, tone(ramp, 3))
        if rng.chance(0.35):                                 # A fire escape climbing the wall
            fx = x + 2
            for level in range(3):
                y = base - 22 - level * 12
                c.hline(fx, fx + 10, y, tone(ramp, 0))
                c.hline(fx, fx + 10, y - 4, tone(ramp, 0))
                for k in range(fx, fx + 11, 2):
                    c.set(k, y - 2, tone(ramp, 0))
                c.line(fx + 10, y, fx + 2, y + 11, tone(ramp, 0))
        x += wide + rng.range(1, 4)


def siding(c: Canvas, pal: dict, seed: int, base: int) -> None:
    """Freight cars left on a side track: boxcars with their doors and
    ladders, tank cars with their domes and bands, hoppers with their ribs;
    a shed, a signal bridge, a water crane."""
    rng = Rng(seed + 1)
    ramp = pal['ramp']
    hole, rim = hx(pal['hole']), hx(pal['rim'])
    dark, main, light = tone(ramp, 0), tone(ramp, 2), tone(ramp, 3)
    c.fill(0, base - 4, c.period - 1, base, dark)            # The track's bed
    for x in range(0, c.period, 5):
        c.hline(x, x + 2, base - 5, tone(ramp, 1))            # Ties
    c.hline(0, c.period - 1, base - 6, rim)                   # The rail
    x = 6
    while x < c.period - 60:
        kind = rng.range(0, 2)
        wide = rng.range(52, 66)
        deck = base - 12
        if kind == 0:                                        # A boxcar
            top = deck - rng.range(22, 26)
            c.fill(x, top, x + wide, deck, main)
            for xx in range(x, x + wide + 1, 4):
                c.vline(xx, top + 2, deck - 1, tone(ramp, 1))
            c.fill(x + wide - 5, top, x + wide, deck, tone(ramp, 1))
            c.vline(x, top, deck, light)
            c.hline(x - 1, x + wide + 1, top, rim)
            c.hline(x - 1, x + wide + 1, top + 1, tone(ramp, 1))
            dx = x + wide // 2 - 7
            c.fill(dx, top + 3, dx + 14, deck - 1, tone(ramp, 1))     # Its door, on its rail
            c.vline(dx, top + 3, deck - 1, light)
            c.hline(dx - 4, dx + 20, top + 2, dark)
            c.fill(dx + 6, top + 11, dx + 8, top + 13, dark)
            for y in range(top + 4, deck, 4):                # A ladder at its end
                c.hline(x + 2, x + 5, y, dark)
            if rng.chance(0.5):                              # Paint someone sprayed on it
                for k in range(8):
                    c.set(x + 10 + k * 2 + rng.range(0, 1), deck - 6 - (k * 3) % 5, tone(ramp, 4))
        elif kind == 1:                                      # A tank car
            cy, r = deck - 9, 9
            for xx in range(x + 2, x + wide - 1):
                end = min(xx - (x + 2), (x + wide - 2) - xx)
                rr = r if end > 4 else r - (4 - end) * 1.2
                for yy in range(int(cy - rr), int(cy + rr) + 1):
                    v = (yy - cy) / r
                    c.set(xx, yy, light if v < -0.6 else main if v < 0.25 else tone(ramp, 1))
            for bx in range(x + 10, x + wide - 8, 13):
                c.vline(bx, cy - r, cy + r, dark)             # Bands
            c.fill(x + wide // 2 - 4, cy - r - 4, x + wide // 2 + 4, cy - r - 1, main)   # Dome
            c.hline(x + wide // 2 - 4, x + wide // 2 + 4, cy - r - 4, rim)
            c.hline(x + 2, x + wide - 2, cy - r - 1, rim)
            c.hline(x, x + wide, deck, dark)
        else:                                                # A hopper
            top = deck - rng.range(18, 22)
            c.fill(x, top, x + wide, deck - 6, main)
            c.hline(x - 1, x + wide + 1, top, rim)
            for xx in range(x + 6, x + wide - 2, 8):
                c.vline(xx, top + 1, deck - 6, tone(ramp, 1))         # Ribs
            c.vline(x, top, deck - 6, light)
            c.fill(x + wide - 5, top, x + wide, deck - 6, tone(ramp, 1))
            for k in range(3):                               # Its chutes
                cx0 = x + 6 + k * (wide - 12) // 3
                for i in range(6):
                    c.hline(cx0 + i, cx0 + (wide - 12) // 3 - 2 - i, deck - 5 + i, tone(ramp, 1))
        c.fill(x + 1, deck + 1, x + wide - 1, deck + 2, dark)          # Frame, couplers
        c.hline(x - 4, x, deck + 1, dark)
        c.hline(x + wide, x + wide + 4, deck + 1, dark)
        for wx in (x + 7, x + 15, x + wide - 16, x + wide - 8):       # Wheels
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    if dx * dx + dy * dy <= 10:
                        c.set(wx + dx, base - 9 + dy, dark if dx * dx + dy * dy > 3 else tone(ramp, 2))
        x += wide + rng.range(8, 30)
    gx = c.period - 52                                       # A signal bridge at the yard's throat
    for lx in (gx, gx + 40):
        c.fill(lx, base - 50, lx + 1, base - 5, dark)
    c.fill(gx, base - 52, gx + 41, base - 49, dark)
    c.hline(gx, gx + 41, base - 52, rim)
    for k in range(gx + 6, gx + 38, 10):
        c.fill(k, base - 48, k + 3, base - 41, dark)
        c.set(k + 1, base - 46, hx(0xd05a30) if (k // 10) % 2 else tone(ramp, 3))
        c.set(k + 1, base - 43, tone(ramp, 2))


def perimeter(c: Canvas, pal: dict, seed: int, base: int, heads: int) -> None:
    """The post's perimeter: a wire fence on its posts under coils of razor
    wire, bunkers dug in, watchtowers on their legs, tents, trucks parked
    in a row."""
    rng = Rng(seed + 1)
    ramp = pal['ramp']
    hole, rim = hx(pal['hole']), hx(pal['rim'])
    dark, main, light = tone(ramp, 0), tone(ramp, 2), tone(ramp, 3)
    c.fill(0, base - 8, c.period - 1, base, tone(ramp, 1))    # The cleared ground
    for x in range(c.period):
        if hash2(x // 3, 0, seed) < 0.3:
            c.set(x, base - 8, dark)
    for bx in (40, 300, 560):                                # Bunkers: a low mound, a firing slit
        for i in range(44):
            y = base - 8 - round(12 * math.sin(math.pi * (i + 0.5) / 44) ** 0.6)
            c.vline(bx + i, y, base - 8, main if i < 30 else tone(ramp, 1))
            c.set(bx + i, y, rim if i < 26 else light)
        c.fill(bx + 12, base - 15, bx + 30, base - 13, hole)
        c.hline(bx + 11, bx + 31, base - 16, light)
    for tx in (130, 420, 660):                               # Watchtowers
        top = base - 56
        c.fill(tx, top, tx + 15, top + 12, main)
        c.vline(tx, top, top + 12, light)
        c.fill(tx + 12, top, tx + 15, top + 12, tone(ramp, 1))
        c.fill(tx + 2, top + 3, tx + 13, top + 7, hole)
        for i in range(4):
            c.hline(tx - 2 + i, tx + 17 - i, top - 1 - i, tone(ramp, 1) if i else rim)
        c.hline(tx - 1, tx + 16, top + 13, rim)
        for lx in (tx + 1, tx + 14):
            c.vline(lx, top + 14, base - 8, dark)
        for k in range(top + 14, base - 10, 14):
            c.line(tx + 1, k, tx + 14, k + 13, dark)
            c.line(tx + 14, k, tx + 1, k + 13, dark)
        if pal.get('lit'):                                   # Its searchlight, on
            c.fill(tx + 16, top + 4, tx + 18, top + 6, hx(pal['lit'][2]))
    for vx in (210, 240, 500):                               # Trucks parked: canvas backs, cabs
        c.fill(vx, base - 24, vx + 20, base - 12, tone(ramp, 1))
        c.hline(vx, vx + 20, base - 24, light)
        for k in range(vx + 4, vx + 20, 5):
            c.vline(k, base - 23, base - 12, dark)
        c.fill(vx + 21, base - 19, vx + 27, base - 12, main)
        c.fill(vx + 23, base - 18, vx + 26, base - 15, hole)
        for wx in (vx + 4, vx + 15, vx + 24):
            c.fill(wx, base - 11, wx + 2, base - 9, dark)
    for ex in (350, 600):                                    # Tents
        for i in range(30):
            y = base - 8 - (15 - abs(i - 15))
            c.vline(ex + i, y, base - 8, main if i < 15 else tone(ramp, 1))
            c.set(ex + i, y, rim if i < 15 else light)
        c.fill(ex + 13, base - 16, ex + 16, base - 8, hole)
    for x in range(c.period):                                # The fence in front of it all
        if x % 14 == 0:
            c.vline(x, base - 22, base, dark)
            c.set(x, base - 23, light)
            c.set(x + 1, base - 24, dark)                     # The arm its top strand hangs from
        if x % 2 == 0:
            for y in range(base - 20, base - 2, 2):
                if (x // 2 + y // 2) % 2 == 0:
                    c.set(x, y, tone(ramp, 1 if y < base - 8 else 0))
        yy = base - 25 + round(1.5 * math.sin(x * 0.9))       # Razor wire in coils
        c.set(x, yy, light if x % 3 else dark)
    _ = rng, heads


# ---- The last things before the road --------------------------------------------------------------------

def make_hills_near(name: str, t: dict) -> Canvas:
    """What lines the far side of the road, low and dark: it is behind the
    bodies. Its foot is the pavement (or the ballast, or the apron)."""
    w, h, _top, _rep = LAYERS['hills_near']
    near, seed = t['near'], seed_of(name) + 300
    c = Canvas(w, h, period=w)
    ramp = near['ramp']
    dark, main, light, rim = tone(ramp, 0), tone(ramp, 2), tone(ramp, 3), hx(near['rim'])
    floor = h - 8                                            # Where the pavement starts
    rng = Rng(seed + 1)
    if name == 'afueras':                                    # Hedges, low walls, mailboxes, a bus stop
        crest = rolling(w, seed, 34, 5, 1.0)
        paint_hills(c, crest, near, seed, (3, 9, 16, 24))
        x = 0
        while x < w - 30:
            kind = rng.range(0, 3)
            wide = rng.range(40, 90)
            if kind == 0:                                    # A clipped hedge
                for xx in range(x, x + wide):
                    top = floor - 15 - int(2 * hash2(xx // 3, 1, seed))
                    for yy in range(top, floor):
                        k = 2 if yy < top + 3 and hash2(xx // 2, yy, seed + 2) > 0.4 else \
                            1 if hash2(xx // 2, yy // 2, seed + 3) > 0.35 else 0
                        c.set(xx, yy, hx(near['plant'][k]))
            elif kind == 1:                                  # A block wall with its cap
                wall(c, x, x + wide, floor - 14, floor, near, seed + x)
            elif kind == 2:                                  # A chain-link fence
                chain_link(c, x, x + wide, floor - 20, floor, dark, light)
            else:                                            # A row of bushes
                for bx in range(x, x + wide - 10, 13):
                    shrub(c, bx, floor - 1, rng.range(10, 15), rng.range(8, 12), near['plant'], seed + bx)
            x += wide + rng.range(4, 14)
        for mx in range(30, w, 150):                         # Mailboxes on their posts
            c.vline(mx, floor - 12, floor, dark)
            c.fill(mx - 2, floor - 16, mx + 4, floor - 12, main)
            c.hline(mx - 2, mx + 4, floor - 16, rim)
        bus_stop(c, 400, floor, near)
    elif name in ('centro', 'ciudad_noche'):                 # Hoardings, planters, parked cars, a kiosk
        x = 0
        while x < w - 20:
            kind = rng.range(0, 4)
            wide = rng.range(36, 80)
            if kind == 0:                                    # A hoarding round a building site
                c.fill(x, floor - 26, x + wide, floor, main)
                for xx in range(x, x + wide + 1, 12):
                    c.vline(xx, floor - 26, floor, dark)
                c.hline(x, x + wide, floor - 26, rim)
                for k in range(3):                           # Posters, torn
                    px0 = x + 3 + k * (wide // 3)
                    c.fill(px0, floor - 21, px0 + 7, floor - 10, tone(ramp, 4))
                    c.fill(px0 + 1, floor - 20, px0 + 6, floor - 16, dark)
                    c.set(px0 + 7, floor - 11, main)
                    c.set(px0 + 6, floor - 10, main)
            elif kind == 1:                                  # A parked car, dead
                car_shape(c, x + 4, floor, near, rng)
                wide = 66
            elif kind == 2:                                  # Planters with what is left of their trees
                for px0 in range(x, x + wide - 14, 22):
                    c.fill(px0, floor - 7, px0 + 12, floor, main)
                    c.hline(px0 - 1, px0 + 13, floor - 8, rim)
                    c.fill(px0 + 10, floor - 7, px0 + 12, floor, dark)
                    for k in range(6):
                        c.line(px0 + 6, floor - 8, px0 + 2 + k * 2, floor - 16 - (k * 5) % 7, dark)
            elif kind == 3:
                chain_link(c, x, x + wide, floor - 24, floor, dark, light)
            else:
                wall(c, x, x + wide, floor - 18, floor, near, seed + x)
            x += wide + rng.range(3, 10)
        kiosk(c, 250, floor, near)
        bus_stop(c, 560, floor, near)
    elif name == 'vias':                                     # Sleepers piled, rails stacked, a hand car, weeds
        crest = rolling(w, seed, 40, 3, 1.0)
        paint_hills(c, crest, near, seed, (3, 8, 14, 20))
        x = 6
        while x < w - 40:
            kind = rng.range(0, 3)
            if kind == 0:                                    # A stack of sleepers, crossed
                for row in range(rng.range(3, 5)):
                    y = floor - 3 - row * 4
                    if row % 2 == 0:
                        c.fill(x, y, x + 40, y + 3, main)
                        c.hline(x, x + 40, y, light)
                        for k in range(x + 5, x + 40, 9):
                            c.vline(k, y + 1, y + 3, dark)
                    else:
                        for k in range(x + 2, x + 38, 8):
                            c.fill(k, y, k + 4, y + 3, tone(ramp, 1))
                            c.hline(k, k + 4, y, light)
                wide = 44
            elif kind == 1:                                  # Rails laid by
                for k in range(3):
                    c.hline(x, x + 70, floor - 2 - k * 3, rim if k == 2 else light)
                    c.hline(x, x + 70, floor - 1 - k * 3, dark)
                wide = 74
            elif kind == 2:                                  # A switch stand and its lamp
                c.vline(x + 4, floor - 22, floor, dark)
                c.fill(x + 2, floor - 27, x + 6, floor - 22, main)
                c.set(x + 4, floor - 25, hx(0xd05a30))
                c.hline(x, x + 12, floor - 2, dark)
                wide = 20
            else:                                            # A heap of ballast
                for i in range(46):
                    top = floor - round(9 * math.sin(math.pi * (i + 0.5) / 46) ** 0.7)
                    for yy in range(top, floor):
                        c.set(x + i, yy, hx(near['rock'][2 if yy == top and i < 26 else 1 if hash2(x + i, yy, seed) > 0.4 else 0]))
                wide = 48
            x += wide + rng.range(14, 40)
        for wx in range(0, w, 7):                            # Weeds between it all
            if hash2(wx, 2, seed) < 0.4:
                tuft(c, wx, floor - 1, 2 + int(hash2(wx, 3, seed) * 4), hx(near['plant'][0]), hx(near['plant'][2]))
    else:                                                    # The post: sandbags, concrete blocks, a barrier arm
        x = 0
        while x < w - 30:
            kind = rng.range(0, 3)
            wide = rng.range(44, 84)
            if kind == 0:                                    # A sandbag wall, stepped
                for row in range(4):
                    y = floor - 5 - row * 5
                    for bx in range(x + row * 3 + (row % 2) * 4, x + wide - row * 3 - 6, 9):
                        c.fill(bx + 1, y, bx + 7, y + 4, main)
                        c.fill(bx, y + 1, bx + 8, y + 3, main)
                        c.hline(bx + 1, bx + 7, y, light if row > 1 else tone(ramp, 3))
                        c.hline(bx + 1, bx + 7, y + 4, dark)
            elif kind == 1:                                  # Concrete blocks in a row
                for bx in range(x, x + wide - 14, 18):
                    c.fill(bx, floor - 13, bx + 14, floor, main)
                    c.fill(bx + 11, floor - 13, bx + 14, floor, tone(ramp, 1))
                    c.hline(bx, bx + 14, floor - 13, rim)
                    c.vline(bx, floor - 13, floor, light)
                    c.fill(bx + 4, floor - 9, bx + 8, floor - 7, dark)   # Its lifting slot
            elif kind == 2:
                chain_link(c, x, x + wide, floor - 26, floor, dark, light)
                for xx in range(x, x + wide):
                    c.set(xx, floor - 28 + round(1.5 * math.sin(xx * 0.9)), light if xx % 3 else dark)
            else:                                            # Fuel drums and crates
                for bx in range(x, x + wide - 10, 12):
                    tall = 12 + (bx % 3) * 2
                    c.fill(bx, floor - tall, bx + 8, floor, main)
                    c.vline(bx, floor - tall, floor, light)
                    c.fill(bx + 7, floor - tall, bx + 8, floor, dark)
                    c.hline(bx, bx + 8, floor - tall, rim)
                    c.hline(bx, bx + 8, floor - tall // 2, dark)
            x += wide + rng.range(6, 18)
        ax = 330                                             # A barrier arm, down
        c.fill(ax, floor - 16, ax + 4, floor, main)
        c.vline(ax, floor - 16, floor, light)
        for k in range(60):
            c.set(ax + 5 + k, floor - 13, hx(0x8a3a24) if (k // 6) % 2 else tone(ramp, 4))
            c.set(ax + 5 + k, floor - 12, dark)
    pavement(c, name, t, floor, seed)
    return c


def wall(c: Canvas, x0: int, x1: int, top: int, floor: int, near: dict, seed: int) -> None:
    ramp = near['ramp']
    for y in range(top, floor):
        row = (y - top) // 4
        for x in range(x0, x1):
            seam = (y - top) % 4 == 3 or (x + row * 5) % 10 == 0
            c.set(x, y, tone(ramp, 1 if seam else 2 + (hash2(x // 10, row, seed) > 0.8)))
    c.hline(x0 - 1, x1, top - 1, hx(near['rim']))
    c.hline(x0 - 1, x1, top, tone(ramp, 3))
    for k in range(6):                                        # Paint sprayed on it
        gx = x0 + 6 + int(hash2(k, 1, seed) * max(1, x1 - x0 - 14))
        c.line(gx, floor - 4 - k % 3, gx + 5, top + 4 + k % 4, tone(ramp, 4))


def chain_link(c: Canvas, x0: int, x1: int, top: int, floor: int, dark, light) -> None:
    for x in range(x0, x1 + 1):
        if (x - x0) % 16 == 0 or x == x1:
            c.vline(x, top - 1, floor, dark)
            c.set(x, top - 2, light)
        for y in range(top + 1, floor):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                c.set(x, y, dark)
    c.hline(x0, x1, top, dark)


def bus_stop(c: Canvas, x: int, floor: int, near: dict) -> None:
    ramp = near['ramp']
    dark, main, rim = tone(ramp, 0), tone(ramp, 2), hx(near['rim'])
    c.fill(x, floor - 32, x + 36, floor - 30, main)
    c.hline(x - 1, x + 37, floor - 33, rim)
    for lx in (x + 1, x + 35):
        c.vline(lx, floor - 29, floor, dark)
    c.fill(x + 2, floor - 28, x + 12, floor - 6, tone(ramp, 1))       # Its side panel, an ad torn off
    c.fill(x + 3, floor - 26, x + 11, floor - 14, tone(ramp, 3))
    c.fill(x + 4, floor - 25, x + 8, floor - 20, dark)
    c.hline(x + 14, x + 34, floor - 9, main)                  # The bench
    c.hline(x + 14, x + 34, floor - 8, dark)
    for lx in (x + 16, x + 32):
        c.vline(lx, floor - 7, floor, dark)
    c.vline(x + 42, floor - 36, floor, dark)                  # Its sign
    c.fill(x + 39, floor - 42, x + 45, floor - 36, main)
    c.hline(x + 39, x + 45, floor - 42, rim)


def kiosk(c: Canvas, x: int, floor: int, near: dict) -> None:
    ramp = near['ramp']
    dark, main, light, rim = tone(ramp, 0), tone(ramp, 2), tone(ramp, 3), hx(near['rim'])
    c.fill(x, floor - 30, x + 30, floor, main)
    c.vline(x, floor - 30, floor, light)
    c.fill(x + 25, floor - 30, x + 30, floor, tone(ramp, 1))
    for i in range(5):
        c.hline(x - 3 + i, x + 33 - i, floor - 31 - i, tone(ramp, 1) if i else rim)
    for y in range(floor - 26, floor - 8, 2):                 # Its shutter down
        c.hline(x + 3, x + 22, y, dark)
    c.fill(x + 3, floor - 7, x + 22, floor - 6, light)        # The counter
    for k in range(4):                                        # Papers still in its rack
        c.fill(x + 4 + k * 5, floor - 5, x + 7 + k * 5, floor - 1, tone(ramp, 4 if k % 2 else 3))


def car_shape(c: Canvas, x: int, floor: int, near: dict, rng: Rng) -> None:
    """A car parked across the street, seen dark against the wall: body,
    cabin, glass, wheels; a door ajar or a flat now and then."""
    ramp = near['ramp']
    dark, main, light, rim = tone(ramp, 0), tone(ramp, 2), tone(ramp, 3), hx(near['rim'])
    for i in range(60):
        top = floor - 12 if i < 8 or i > 50 else floor - 13
        c.vline(x + i, top, floor - 4, main)
        c.set(x + i, top, rim if 8 <= i <= 50 else light)
    for i in range(14, 44):                                  # Cabin
        top = floor - 22 + (max(0, 20 - i) * 9 // 6 if i < 20 else max(0, i - 36) * 9 // 7)
        c.vline(x + i, top, floor - 13, main)
        c.set(x + i, top, rim)
        if 17 < i < 41 and i not in (28, 29):
            c.vline(x + i, top + 2, floor - 15, dark)         # Glass
    for wx in (x + 12, x + 46):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 18:
                    c.set(wx + dx, floor - 4 + dy, dark if dx * dx + dy * dy > 5 else tone(ramp, 1))
    c.hline(x + 1, x + 58, floor - 8, tone(ramp, 1))
    if rng.chance(0.5):
        c.fill(x + 30, floor - 12, x + 31, floor - 5, dark)   # A door's seam, sprung


def pavement(c: Canvas, name: str, t: dict, floor: int, seed: int) -> None:
    """The foot of the layer: the pavement on the far side of the street (its
    slabs and their joints, a kerb), ballast in the yard, the apron's
    concrete at the post."""
    g = t['ground']
    w, h = c.period, c.h
    if g['kind'] == 'rails':                                 # The next track over: ballast, ties, a rail
        ramp = g['ramp']
        for y in range(floor, h):
            for x in range(w):
                k = 2 if hash2(x // 2, y, seed + 5) > 0.55 else 1 if hash2(x, y, seed + 6) > 0.3 else 3
                c.set(x, y, tone(ramp, k))
        for x in range(0, w, 9):
            c.fill(x, floor + 2, x + 4, floor + 4, hx(g['tie'][1]))
            c.hline(x, x + 4, floor + 2, hx(g['tie'][2]))
        c.hline(0, w - 1, floor + 1, hx(g['steel'][2]))
        c.hline(0, w - 1, floor + 2, hx(g['steel'][0]))
        return
    walk = g.get('walk') or [g['ramp'][2], g['ramp'][3], g['ramp'][4]]
    for y in range(floor, h):
        for x in range(w):
            k = 1
            if y == floor:
                k = 2                                        # The slabs' far edge, lit
            elif x % 24 == 0 or (y == floor + 4 and g['kind'] != 'slabs'):
                k = 0                                        # Joints
            elif hash2(x // 3, y, seed + 7) < 0.12:
                k = 0 if hash2(x, y, seed + 8) < 0.5 else 2
            c.set(x, y, hx(walk[k]))
    for x in range(w):                                       # The kerb's shadow at its foot
        c.set(x, h - 1, hx(walk[0]))


# ---- The street -------------------------------------------------------------------------------------------

def make_ground(name: str, t: dict) -> Canvas:
    w, h, _top, _rep = LAYERS['ground']
    g, seed = t['ground'], seed_of(name) + 400
    c = Canvas(w, h, period=w)
    ramp = g['ramp']
    rng = Rng(seed + 3)
    if g['kind'] == 'rails':
        ballast(c, g, seed, rng)
        return c
    for y in range(h):
        for x in range(w):
            if y < 2:
                col = hx(g['line'][y])                       # The kerb she walks along
                if x % 30 == 0:
                    col = tone(ramp, 3)
            else:
                wob = (fbm(x / 30.0, y / 6.0, seed, 3, wrap=max(1, w // 30)) - 0.5) * 8
                k = 3 if y + wob < 4 else 2 if y + wob < 14 else 1
                if hash2(x // 2, y, seed + 1) < 0.14:        # The aggregate in the surface
                    k += 1 if hash2(x, y, seed + 2) < 0.4 else -1
                col = tone(ramp, k)
            c.set(x, y, col)
    if g['kind'] == 'slabs':
        slabs(c, g, seed, rng)
        return c
    for x0 in range(0, w, 60):                               # The lane's dashes, worn through
        for x in range(x0 + 8, x0 + 36):
            for y in (14, 15):
                if hash2(x // 2, y, seed + 4) > 0.22:
                    c.set(x, y, hx(g['mark']) if y == 14 else mix(hx(g['mark']), tone(ramp, 1), 0.4))
    for _ in range(9):                                       # Patches of newer tar
        x, y, wide = rng.range(0, w - 1), rng.range(5, h - 6), rng.range(14, 40)
        for yy in range(y, y + rng.range(3, 6)):
            for xx in range(x + (yy % 2), x + wide - (yy % 3)):
                if c.get(xx, yy) != hx(g['mark']):
                    c.set(xx, yy, tone(ramp, 1 if (xx + yy) % 7 else 0))
    for _ in range(14):                                      # Cracks, running and forking
        x, y = rng.range(0, w - 1), rng.range(4, h - 2)
        for i in range(rng.range(8, 26)):
            c.set(x + i, y, tone(ramp, 0))
            if rng.chance(0.4):
                y += rng.pick([-1, 1])
            if rng.chance(0.08):
                c.set(x + i, y + 1, tone(ramp, 0))
                c.set(x + i + 1, y + 2, tone(ramp, 0))
            if not 3 < y < h - 1:
                break
    for mx in (96, 330):                                     # Manhole covers: a ring, its pattern
        my = 9 if mx == 96 else 22
        for dy in range(-2, 3):
            for dx in range(-6, 7):
                d = (dx / 6.5) ** 2 + (dy / 2.6) ** 2
                if d <= 1.0:
                    c.set(mx + dx, my + dy, tone(ramp, 4) if d > 0.62 else tone(ramp, 0) if (dx + dy) % 2 else tone(ramp, 2))
        c.hline(mx - 5, mx + 5, my + 3, tone(ramp, 0))
    for dx0 in (200, 420):                                   # Drains at the kerb
        c.fill(dx0, 2, dx0 + 11, 4, tone(ramp, 0))
        for k in range(dx0 + 1, dx0 + 11, 2):
            c.vline(k, 2, 4, tone(ramp, 3))
    for _ in range(26):                                      # Grit, glass, bottle caps
        x, y = rng.range(0, w - 1), rng.range(4, h - 1)
        c.set(x, y, tone(ramp, 4))
        c.set(x + 1, y + 1, tone(ramp, 0))
    for _ in range(5):                                       # Oil stains
        x, y = rng.range(0, w - 1), rng.range(8, h - 4)
        for dy in range(-1, 2):
            for dx in range(-5, 6):
                if (dx / 5.5) ** 2 + (dy / 1.6) ** 2 <= 1 and (dx + dy) % 3:
                    c.set(x + dx, y + dy, tone(ramp, 0))
    if g.get('wet'):                                         # Wet: the lamps' light lying on the road
        wet = [hx(v) for v in g['wet']]
        for x0 in (40, 170, 300, 440):
            for y in range(4, h - 2, 2):
                half = 3 + (y % 5) + (y // 6)
                for x in range(x0 - half, x0 + half):
                    if hash2(x, y, seed + 9) > 0.35:
                        c.set(x, y, wet[2 if abs(x - x0) < 2 and y < 12 else 1 if abs(x - x0) < half - 2 else 0])
        for _ in range(8):                                   # Puddles holding the sky
            x, y = rng.range(0, w - 1), rng.range(6, h - 3)
            for dx in range(-7, 8):
                if abs(dx) < 7 - (dx % 3):
                    c.set(x + dx, y, wet[0])
            c.hline(x - 3, x + 2, y - 1, wet[1])
    return c


def ballast(c: Canvas, g: dict, seed: int, rng: Rng) -> None:
    """The track she walks: the rail's lit head, its web, ties with their
    plates and spikes, and stone ballast, each stone with its light and
    its shadow."""
    w, h = c.period, c.h
    ramp = g['ramp']
    steel = [hx(v) for v in g['steel']]
    tie = [hx(v) for v in g['tie']]
    for y in range(h):
        for x in range(w):
            wob = (fbm(x / 24.0, y / 6.0, seed, 2, wrap=max(1, w // 24)) - 0.5) * 6
            k = 3 if y + wob < 9 else 2 if y + wob < 19 else 1
            r = hash2(x // 2, y, seed + 1)
            if r < 0.22:
                k += 1
            elif r < 0.44:
                k -= 1
            c.set(x, y, tone(ramp, k))
    for x0 in range(0, w, 20):                               # Ties: grain, a split, plates
        for y in range(3, 9):
            for x in range(x0, x0 + 11):
                k = 2 if y == 3 else 0 if y == 8 or x == x0 + 10 else 1
                if hash2(x, y // 2, seed + 2) < 0.18:
                    k = max(0, k - 1)
                c.set(x, y, tie[k])
        c.fill(x0 + 3, 2, x0 + 7, 3, steel[1])                # The tie plate under the rail
        c.set(x0 + 3, 4, steel[2])                            # Spikes
        c.set(x0 + 7, 4, steel[2])
    for x in range(w):                                       # The rail: head, web, foot
        c.set(x, 0, steel[2] if hash2(x // 5, 0, seed) > 0.12 else steel[1])
        c.set(x, 1, steel[1])
        c.set(x, 2, steel[0] if (x % 20) not in range(3, 8) else steel[1])
    for y0 in (17, 18):                                      # The far rail's gleam, nearer the eye
        for x in range(w):
            c.set(x, y0, steel[1] if y0 == 17 else steel[0])
    for x0 in range(10, w, 20):
        for y in range(19, 25):
            for x in range(x0, x0 + 11):
                k = 2 if y == 19 else 0 if y == 24 or x == x0 + 10 else 1
                if not (c.get(x, y) in steel):
                    c.set(x, y, tie[k])
    for _ in range(70):                                      # Stones that stand out
        x, y = rng.range(0, w - 1), rng.range(9, h - 2)
        if c.get(x, y) in tie or c.get(x, y) in steel:
            continue
        c.set(x, y, tone(ramp, 4))
        c.set(x + 1, y, tone(ramp, 4))
        c.set(x + 1, y + 1, tone(ramp, 0))
    for wx in range(6, w, 37):                               # Weeds through the stones
        tuft(c, wx + rng.range(0, 12), rng.range(12, h - 2), rng.range(2, 4), tone(ramp, 0), hx(g['tie'][2]))
    for _ in range(4):                                       # Oil dripped between the rails
        x, y = rng.range(0, w - 1), rng.range(11, 15)
        for dx in range(-4, 5):
            if (dx % 3) and c.get(x + dx, y) not in tie:
                c.set(x + dx, y, tone(ramp, 0))


def slabs(c: Canvas, g: dict, seed: int, rng: Rng) -> None:
    """The post's concrete: slabs and their tarred joints, cracks sealed,
    painted lines worn off, tyre marks, a drain."""
    w, h = c.period, c.h
    ramp = g['ramp']
    paint = [hx(v) for v in g['paint']]
    for x0 in range(0, w, 60):                               # Joints across
        for y in range(2, h):
            c.set(x0, y, hx(g['mark']))
            if hash2(x0, y, seed) > 0.5:
                c.set(x0 + 1, y, tone(ramp, 0))
    for y0 in (11, 22):                                      # Joints along
        for x in range(w):
            c.set(x, y0, hx(g['mark']) if hash2(x // 4, y0, seed + 1) > 0.08 else tone(ramp, 1))
    for x in range(w):                                       # A hazard line along the kerb: slashes, worn
        for y in (4, 5, 6):
            if (x + y * 2) // 6 % 2 == 0 and hash2(x // 2, y, seed + 2) > 0.3:
                c.set(x, y, paint[1] if y == 4 else paint[0])
    for x0 in (30, 270):                                     # Stencilled bars: a parking bay's end
        for x in range(x0, x0 + 30):
            for y in (15, 16, 17):
                if hash2(x // 3, y, seed + 3) > 0.35:
                    c.set(x, y, paint[0])
    for _ in range(10):                                      # Cracks, sealed with tar
        x, y = rng.range(0, w - 1), rng.range(4, h - 2)
        for i in range(rng.range(10, 30)):
            c.set(x + i, y, tone(ramp, 0))
            c.set(x + i, y + 1, hx(g['mark']))
            if rng.chance(0.35):
                y += rng.pick([-1, 1])
            if not 3 < y < h - 2:
                break
    for y0 in (8, 26):                                       # Tyre marks
        for x in range(w):
            if hash2(x // 7, y0, seed + 4) > 0.45:
                c.set(x, y0 + round(1.2 * wave(x, w, seed + y0, 2)), tone(ramp, 0))
    dx0 = 150                                                # A drain: its grating
    c.fill(dx0, 13, dx0 + 15, 19, tone(ramp, 0))
    for k in range(dx0 + 1, dx0 + 15, 2):
        c.vline(k, 14, 18, tone(ramp, 4))
    for _ in range(18):                                      # Spent shells, grit
        x, y = rng.range(0, w - 1), rng.range(4, h - 1)
        c.set(x, y, paint[1])
        c.set(x + 1, y, tone(ramp, 0))
