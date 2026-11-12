#!/usr/bin/env python3
"""Paint the landscape behind every stage: the layers of all nine themes.

Usage: tools/make_landscape.py [assets_dir] [theme...]   (default: assets, every theme)

Writes backgrounds/<theme>/{sky,far,hills_far,hills_near,ground[,fog]}.png
(docs/LANDSCAPE.md) for the first route (atardecer, cementerio, noche,
pueblo_fantasma) and the second (afueras, centro, vias, ciudad_noche,
base_militar), at the sizes of LAYERS in tools/landscape_kit.py, the same as
BACKGROUND_LAYERS in src/game/themes.c.

Nothing here is a flat patch of color: the sky is bands with ragged edges,
streaks and clouds lit from below; the far land has its strata, its lit
edges and its shadowed faces; the hills carry brush, rock and tracks; the
road has its ruts, stones and cracks. What keeps the characters readable is
value, not emptiness: behind the bodies everything stays dark and close in
tone, and the light comes from one side (the upper left, as on the sprites).
Deterministic; standard library only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape_kit import LAYERS, Canvas, Rng, dither, fbm, hash2, hx, mix, save_all, seed_of  # noqa: E402
import landscape_city as city  # noqa: E402
import landscape_west as west  # noqa: E402

THEMES = {**west.THEMES, **city.THEMES}


# ---- The sky ---------------------------------------------------------------------------

def band_colors(stops: list, sub: int) -> list:
    """(row, color) of each band: every stretch between two stops split in sub."""
    bands = []
    for (ya, ca), (yb, cb) in zip(stops, stops[1:]):
        for j in range(sub):
            bands.append((ya + (yb - ya) * j / sub, mix(hx(ca), hx(cb), j / sub)))
    bands.append((stops[-1][0], hx(stops[-1][1])))
    return bands


def make_sky(name: str, t: dict) -> Canvas:
    """Bands of color from the dark over the HUD down to the horizon, their
    edges rolling like layers of cloud, streaks of each band reaching into
    the next; the sun or the moon with its glow, clouds lit from below (or
    by the moon), stars by night."""
    w, h, _top, _rep = LAYERS['sky']
    sky = t['sky']
    seed = seed_of(name)
    c = Canvas(w, h)
    bands = band_colors(sky['stops'], sky.get('sub', 2))
    n = len(bands)
    orb = sky.get('orb')

    def band_at(x: int, y: int) -> int:
        """Which band a pixel falls in: the edges roll and fray."""
        roll = (fbm(x / 90.0, y / 14.0, seed, 3) - 0.5) * sky.get('roll', 9.0)
        fray = (hash2(x // 3, y, seed + 5) - 0.5) * 1.6
        yy = y + roll + fray
        k = 0
        while k + 1 < n and yy >= bands[k + 1][0]:
            k += 1
        return k

    index = [[band_at(x, y) for x in range(w)] for y in range(h)]
    if orb:                                       # Its glow: the sky a band or two lighter round it
        ox, oy, r = orb['at'][0], orb['at'][1], orb['r']
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - ox, (y - oy) * 1.25) + (fbm(x / 9.0, y / 5.0, seed + 9, 2) - 0.5) * 7
                lift = 2 if d < r + orb.get('glow', 8) * 0.45 else 1 if d < r + orb.get('glow', 8) else 0
                if lift and orb.get('glow_up', True):
                    index[y][x] = min(n - 1, index[y][x] + lift) if sky.get('lighter_down', True) \
                        else max(0, index[y][x] - lift)
    for y in range(h):
        for x in range(w):
            c.set(x, y, bands[index[y][x]][1])
    rng = Rng(seed + 1)
    for k in range(1, n):                         # Streaks of each band in its neighbour
        row = bands[k][0]
        if row < sky.get('streaks_from', 60):
            continue
        for _ in range(sky.get('streaks', 16)):
            x0, length, dy = rng.range(0, w - 1), rng.range(5, 30), rng.range(-4, 4)
            y = int(row + dy + (fbm(x0 / 90.0, row / 14.0, seed, 3) - 0.5) * sky.get('roll', 9.0))
            col = bands[k][1] if dy < 0 else bands[k - 1][1]
            for x in range(x0, x0 + length):
                if 0 <= x < w and 0 <= y < h:
                    c.set(x, y, col)
    for star in sky.get('stars', []):             # Stars: under the clouds, over the bands
        draw_stars(c, star, seed, orb)
    if sky.get('milky'):
        milky_way(c, sky['milky'], seed)
    if orb:
        draw_orb(c, orb, bands, seed)
    for layer in sky.get('clouds', []):
        draw_clouds(c, layer, seed, orb)
    for bx, by, lean, length, col in sky.get('beams', []):   # Searchlights up from the ground, thinning out
        for k in range(length):
            y, mid, half = by - k, bx + lean * k, 1 + k // 12
            for x in range(int(mid - half), int(mid + half) + 1):
                if 0 <= x < w and 0 <= y < h and dither(x, y, 0.55 * (1 - k / length)):
                    c.set(x, y, mix(c.get(x, y), hx(col), 0.7))
    for flock in sky.get('birds', []):            # A few birds far off, two px each
        brng = Rng(seed + 77 + flock[0])
        bx, by = flock[0], flock[1]
        for _ in range(flock[2]):
            x, y = bx + brng.range(-22, 22), by + brng.range(-8, 8)
            col = hx(flock[3])
            c.set(x, y, col)
            c.set(x - 1, y - 1, col)
            c.set(x + 1, y - 1, col)
    return c


def draw_stars(c: Canvas, spec: dict, seed: int, orb) -> None:
    rng = Rng(seed + spec.get('seed', 3))
    colors = [hx(v) for v in spec['colors']]      # Faint to bright
    for _ in range(spec['count']):
        x, y = rng.range(0, c.w - 1), rng.range(spec.get('top', 2), spec['bottom'])
        if orb and math.hypot(x - orb['at'][0], y - orb['at'][1]) < orb['r'] + 5:
            continue
        depth = (y - spec.get('top', 2)) / max(1, spec['bottom'] - spec.get('top', 2))
        if rng.unit() < depth * 0.7:              # Fewer toward the horizon
            continue
        k = min(len(colors) - 1, int(rng.unit() ** 2.2 * len(colors)))
        if y < spec.get('dim_above', 0):          # Under the HUD: only the faint ones
            k = 0
        c.set(x, y, colors[k])
        if k == len(colors) - 1 and rng.chance(0.5):   # The brightest twinkle: a small cross
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.set(x + dx, y + dy, colors[max(0, k - 2)])


def milky_way(c: Canvas, spec: dict, seed: int) -> None:
    """A faint river of stars across the sky: a lighter haze in patches and
    a dusting of dim points along it."""
    haze, dust = hx(spec['haze']), hx(spec['dust'])
    x0, y0, x1, y1, width = spec['from'][0], spec['from'][1], spec['to'][0], spec['to'][1], spec['width']
    for y in range(max(0, min(y0, y1) - width), min(c.h, max(y0, y1) + width)):
        for x in range(c.w):
            t = (x - x0) / (x1 - x0)
            mid = y0 + (y1 - y0) * t
            d = abs(y - mid) / width
            if d >= 1:
                continue
            dense = fbm(x / 26.0, y / 12.0, seed + 31, 3) * (1 - d)
            if dense > 0.42 and (x + y) % 2 == 0 and y > spec.get('top', 0):
                c.set(x, y, haze)
            if dense > 0.3 and hash2(x, y, seed + 33) < 0.035 * (1 - d):
                c.set(x, y, dust)


def draw_orb(c: Canvas, orb: dict, bands: list, seed: int) -> None:
    """The sun or the moon. kind: 'sun' (a disc, paler at its top, its rim a
    shade deeper), 'moon' (a disc with its seas and a lit limb), 'crescent'."""
    ox, oy, r = orb['at'][0], orb['at'][1], orb['r']
    cols = [hx(v) for v in orb['colors']]         # Rim (or shadow) first, the lightest last
    kind = orb.get('kind', 'sun')
    for y in range(int(oy - r - 1), int(oy + r + 2)):
        for x in range(int(ox - r - 1), int(ox + r + 2)):
            d = math.hypot(x - ox + 0.5, y - oy + 0.5)
            if d > r or not (0 <= x < c.w and 0 <= y < c.h):
                continue
            if kind == 'sun':
                k = 0 if d > r - 1.5 else 1 if (y - oy) > r * 0.25 or d > r - 3.5 else 2
                col = cols[min(k, len(cols) - 1)]
            elif kind == 'moon':
                sea = fbm((x - ox) / 6.5, (y - oy) / 6.5, seed + 13, 3)
                limb = (x - ox) + (y - oy)        # Lit from the upper left
                col = cols[2] if sea < 0.42 else cols[3] if limb < r * 0.4 or sea > 0.62 else cols[2]
                if sea < 0.36:
                    col = cols[1]
                if d > r - 1.4 and limb > 0:
                    col = cols[1]
                if d > r - 1.2 and limb <= 0:
                    col = cols[3]
            else:                                 # A crescent: the disc less another, set to its right
                cut = math.hypot(x - ox - r * 0.55, y - oy + r * 0.2)
                if cut < r * 0.98:
                    if orb.get('earthshine') and (x + y) % 2 == 0 and d < r - 1:
                        c.set(x, y, hx(orb['earthshine']))
                    continue
                col = cols[-1] if cut > r * 1.12 else cols[-2]
            c.set(x, y, col)
    for crater in orb.get('craters', []):         # Rings on the moon: a dark floor, a lit far rim
        cx, cy, cr = ox + crater[0], oy + crater[1], crater[2]
        for y in range(int(cy - cr - 1), int(cy + cr + 2)):
            for x in range(int(cx - cr - 1), int(cx + cr + 2)):
                d = math.hypot(x - cx, y - cy)
                if d <= cr and math.hypot(x - ox, y - oy) < r - 1:
                    c.set(x, y, cols[1] if d < cr - 0.8 or (x - cx) + (y - cy) < 0 else cols[3])
    for bar in orb.get('bars', []):               # Thin cloud across its face
        y = int(oy + bar[0])
        col = bands[min(len(bands) - 1, max(0, bar[3]))][1] if len(bar) > 3 else hx(orb['bar_color'])
        for x in range(int(ox + bar[1]), int(ox + bar[2])):
            if math.hypot(x - ox, y - oy) <= r + 6 and hash2(x // 2, y, seed + 17) > 0.18:
                c.set(x, y, col)


def draw_clouds(c: Canvas, layer: dict, seed: int, orb) -> None:
    """A layer of cloud: long shapes of overlapping puffs, each with its
    flat belly lit (toward the light) and its top in shade.
    layer: y (row), spread, count, len (min, max), thick (min, max),
    colors (top shade, body, lower body, belly light, belly glint)."""
    rng = Rng(seed + layer.get('seed', 11))
    cols = [hx(v) for v in layer['colors']]
    for _ in range(layer['count']):
        cx = rng.range(-20, c.w + 20)
        cy = layer['y'] + rng.range(-layer['spread'], layer['spread'])
        length = rng.range(*layer['len'])
        thick = rng.range(*layer['thick'])
        mask = set()
        puffs = max(3, length // 7)
        for i in range(puffs):
            u = i / (puffs - 1)
            taper = math.sin(math.pi * u) ** 0.7  # Thin at both ends
            px = cx - length / 2 + u * length + rng.range(-2, 2)
            rx = 5 + rng.range(0, 6)
            ry = max(1.0, thick * taper * (0.6 + rng.unit() * 0.5))
            py = cy - ry * 0.55 + rng.range(-1, 1)
            for y in range(int(py - ry - 1), int(py + ry + 2)):
                if y > cy + max(1, thick // 3):   # A flat base
                    continue
                for x in range(int(px - rx - 1), int(px + rx + 2)):
                    if ((x - px) / rx) ** 2 + ((y - py) / ry) ** 2 <= 1.0:
                        mask.add((x, y))
        for x, y in mask:
            if not (0 <= x < c.w and 0 <= y < c.h):
                continue
            below = sum((x, y + d) in mask for d in (1, 2, 3))
            above = sum((x, y - d) in mask for d in (1, 2))
            if below == 0:
                col = cols[4] if layer.get('glint', True) and hash2(x // 2, y, seed + 19) > 0.35 else cols[3]
            elif below == 1:
                col = cols[3]
            elif above == 0:
                col = cols[0]
            elif below == 2 or above >= 2 and (x * 3 + y * 5) % 11 < 3:
                col = cols[2]
            else:
                col = cols[1]
            if orb and layer.get('near_light'):   # Brighter where it passes the sun
                d = math.hypot(x - orb['at'][0], (y - orb['at'][1]) * 1.4)
                if d < orb['r'] * 3.2 and below <= 1:
                    col = hx(layer['near_light'])
            c.set(x, y, col)


# ---- The ground --------------------------------------------------------------------------

def make_fog(name: str, t: dict):
    """Fog along the road: wisps that thin toward their edges. One color, two
    strengths, drawn behind the characters."""
    w, h, _top, _rep = LAYERS['fog']
    seed = seed_of(name) + 40
    spec = t['fog']
    c = Canvas(w, h, period=w)
    alpha = {}
    cells = 8                                     # The noise repeats every w px
    for y in range(h):
        for x in range(w):
            env = math.sin(math.pi * (y + 0.5) / h) ** 0.8          # Fades at its top and bottom
            d = fbm(x * cells / w, y / 14.0, seed, 4, wrap=cells) * env
            d += (fbm(x * cells * 3 / w, y / 5.0, seed + 3, 2, wrap=cells * 3) - 0.5) * 0.12
            if d > spec.get('dense', 0.47):
                c.set(x, y, hx(spec['color']))
                alpha[(x, y)] = spec['alpha'][1]
            elif d > spec.get('thin', 0.40) and (x + y * 2) % 4 != 0:
                c.set(x, y, hx(spec['color']))
                alpha[(x, y)] = spec['alpha'][0]
    return c.image(lambda x, y: alpha[(x, y)])


# ---- All of it ------------------------------------------------------------------------------

def theme_layers(name: str) -> dict:
    t = THEMES[name]
    painter = west if name in west.THEMES else city
    out = {
        'sky': make_sky(name, t).image(),
        'far': painter.make_far(name, t).image(),
        'hills_far': painter.make_hills_far(name, t).image(),
        'hills_near': painter.make_hills_near(name, t).image(),
        'ground': painter.make_ground(name, t).image(),
    }
    if t.get('fog'):
        out['fog'] = make_fog(name, t)
    for layer, img in out.items():
        assert (img.width, img.height) == LAYERS[layer][:2], (name, layer, img.width, img.height)
    return out


def main() -> int:
    args = sys.argv[1:]
    assets = Path(args[0]) if args and args[0] not in THEMES else Path(__file__).resolve().parent.parent / 'assets'
    names = [a for a in args if a in THEMES] or list(THEMES)
    out = {}
    for name in names:
        for layer, img in theme_layers(name).items():
            out[f'backgrounds/{name}/{layer}.png'] = img
    save_all(assets, out, 'make_landscape')
    return 0


if __name__ == '__main__':
    sys.exit(main())
