#!/usr/bin/env python3
"""Generate the game's procedural pixel-art sprites as PNG files.

Usage: tools/make_sprites.py [assets_dir]   (default: assets)

Writes:
  sprites/ui/badge_player.png  Her level badge: brass, with a star (17 x 19)
  sprites/ui/badge_zombie.png  A zombie's: rusted iron and blood, with a skull
  sprites/chest/sparks.png        Sparks bursting out of an opening chest:
                                  8 frames of 72 x 72, on the chest's template

The badges are an inverted pyramid: a band on top where the game writes the
level, then facets narrowing to a point that hangs over the owner's head. The
number is not in the art, so one badge serves every level.

8-bit RGBA, non-interlaced, as tools/embed_assets.py reads them. Deterministic,
so re-running gives the same files. Uses only the standard library.
"""
from __future__ import annotations

import math
import struct
import sys
import zlib
from pathlib import Path

Color = tuple[int, int, int, int]
CLEAR: Color = (0, 0, 0, 0)


def rgb(value: int, alpha: int = 255) -> Color:
    return (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF, alpha


class Image:
    def __init__(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        self.px: list[Color] = [CLEAR] * (width * height)

    def get(self, x: int, y: int) -> Color:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.px[y * self.width + x]
        return CLEAR

    def set(self, x: int, y: int, color: Color) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.px[y * self.width + x] = color

    def put_over(self, x: int, y: int, color: Color) -> None:
        """Keeps the more opaque of the two, so overlapping sparks don't dim."""
        if color[3] > self.get(x, y)[3]:
            self.set(x, y, color)

    def save(self, path: Path) -> None:
        raw = b''.join(b'\0' + b''.join(bytes(self.px[y * self.width + x])
                                        for x in range(self.width))
                       for y in range(self.height))

        def chunk(kind: bytes, data: bytes) -> bytes:
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'\x89PNG\r\n\x1a\n'
                         + chunk(b'IHDR', struct.pack('>IIBBBBB', self.width, self.height, 8, 6, 0, 0, 0))
                         + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


# --- Level badges -------------------------------------------------------------

BADGE_W, BADGE_H = 17, 19
BAND_BOTTOM = 10   # Row of the divider between the number band and the pyramid
CENTER = BADGE_W // 2

BADGE_STYLES = {
    'player': {  # Brass and dark leather
        'outline': 0x17100b, 'rim': 0xcf9a45, 'rim_dark': 0x8a5e24,
        'band': 0x4f2e16, 'band_light': 0x6e4422, 'band_shade': 0x3a2210,
        'facet_light': 0xc08a40, 'facet_dark': 0x7a4f22, 'ridge': 0xf0c870,
        'icon': 0xffe7a0, 'icon_dark': 0x17100b, 'rivet': 0xffe7a0,
        'icon_rows': ['..#..', '#####', '.###.', '.#.#.'],  # Star
    },
    'zombie': {  # Rusted iron and dried blood
        'outline': 0x120c0e, 'rim': 0x8d929c, 'rim_dark': 0x55585f,
        'band': 0x45191b, 'band_light': 0x642626, 'band_shade': 0x2c0f11,
        'facet_light': 0x9c4a42, 'facet_dark': 0x5a2424, 'ridge': 0xc4705f,
        'icon': 0xe8e0d0, 'icon_dark': 0x120c0e, 'rivet': 0xb8bcc4,
        'icon_rows': ['.###.', '#o#o#', '.###.', '.#.#.'],  # Skull: eyes, jaw, teeth
    },
}


def badge_mask(x: int, y: int) -> bool:
    """Band with cut top corners, then rows narrowing by one each side to a point."""
    if not (0 <= x < BADGE_W and 0 <= y < BADGE_H):
        return False
    if y == 0:
        return 1 <= x <= BADGE_W - 2
    if y <= BAND_BOTTOM:
        return True
    return abs(x - CENTER) <= CENTER - (y - BAND_BOTTOM)


NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def on_edge(x: int, y: int) -> bool:
    return badge_mask(x, y) and any(not badge_mask(x + dx, y + dy) for dx, dy in NEIGHBORS)


def ring(x: int, y: int) -> int:
    """0 on the outline, 1 just inside it, 2 deeper (4-neighbors: crisp stair steps)."""
    if on_edge(x, y):
        return 0
    if any(on_edge(x + dx, y + dy) for dx, dy in NEIGHBORS):
        return 1
    return 2


def make_badge(style: dict) -> Image:
    img = Image(BADGE_W, BADGE_H)
    for y in range(BADGE_H):
        for x in range(BADGE_W):
            if not badge_mask(x, y):
                continue
            depth = ring(x, y)
            if depth == 0:
                c = style['outline']
            elif depth == 1:
                # Metal rim, lit on the upper left, darker on the lower right.
                c = style['rim'] if (x < CENTER or y <= 2) and y < BAND_BOTTOM + 3 else style['rim_dark']
            elif y == BAND_BOTTOM:
                c = style['rim']                       # Divider under the number
            elif y < BAND_BOTTOM:
                c = (style['band_light'] if y == 2 else
                     style['band_shade'] if y == BAND_BOTTOM - 1 else style['band'])
            else:
                c = (style['ridge'] if x == CENTER else
                     style['facet_light'] if x < CENTER else style['facet_dark'])
            img.set(x, y, rgb(c))
    # Rivets in the band's corners.
    for rx, ry in ((2, 2), (BADGE_W - 3, 2), (2, BAND_BOTTOM - 1), (BADGE_W - 3, BAND_BOTTOM - 1)):
        img.set(rx, ry, rgb(style['rivet']))
    # Icon on the pyramid's facets, centered on the ridge.
    rows = style['icon_rows']
    for iy, row in enumerate(rows):
        for ix, ch in enumerate(row):
            x, y = CENTER - len(row) // 2 + ix, BAND_BOTTOM + 2 + iy
            if ch == '#':
                img.set(x, y, rgb(style['icon']))
            elif ch == 'o':
                img.set(x, y, rgb(style['icon_dark']))
    return img


# --- Chest sparks -------------------------------------------------------------

SPARK_FRAME = 72
SPARK_FRAMES = 8
ORIGIN = (36, 33)  # Where the lid opens, on the chest's 72 x 72 template
SPARK_WHITE, SPARK_GOLD, SPARK_ORANGE = 0xfff7d6, 0xffd25a, 0xe08a2a


def lcg(seed: int):
    state = seed
    while True:
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        yield state / 0x7FFFFFFF


def plus(img: Image, ox: int, x: int, y: int, color: Color, arm: int) -> None:
    img.put_over(ox + x, y, color)
    for d in range(1, arm + 1):
        dim = (color[0], color[1], color[2], max(0, color[3] - 70 * d))
        for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
            img.put_over(ox + x + dx, y + dy, dim)


def make_sparks() -> Image:
    img = Image(SPARK_FRAME * SPARK_FRAMES, SPARK_FRAME)
    cx, cy = ORIGIN
    rand = lcg(7)
    # Sparkles that fly out of the chest, mostly upward.
    particles = []
    for _ in range(22):
        angle = math.radians(-90 + (next(rand) - 0.5) * 160)
        speed = 2.5 + next(rand) * 3.0
        color = (SPARK_WHITE, SPARK_GOLD, SPARK_GOLD, SPARK_ORANGE)[int(next(rand) * 4)]
        particles.append((math.cos(angle) * speed, math.sin(angle) * speed, color))

    for f in range(SPARK_FRAMES):
        ox = f * SPARK_FRAME
        if f <= 1:
            # Light leaking through the seam as the lid lifts.
            half = 6 + 5 * f
            for x in range(cx - half, cx + half + 1):
                a = 120 + 80 * f - 8 * abs(x - cx)
                img.put_over(ox + x, cy, rgb(SPARK_GOLD, max(40, a)))
            if f == 1:
                plus(img, ox, cx, cy - 1, rgb(SPARK_WHITE), 1)
        if 2 <= f <= 4:
            # Burst: eight rays leaving the opening, then breaking off.
            inner, outer = (2, 7) if f == 2 else (5, 11) if f == 3 else (9, 13)
            alpha = (255, 220, 140)[f - 2]
            for k in range(8):
                ang = math.radians(-90 + k * 45)
                if math.sin(ang) > 0.5:
                    continue  # Not down into the chest
                for r in range(inner, outer + 1):
                    x = round(cx + math.cos(ang) * r)
                    y = round(cy + math.sin(ang) * r * 0.9)
                    color = SPARK_WHITE if r < inner + 2 else SPARK_GOLD
                    img.put_over(ox + x, y, rgb(color, alpha))
            if f == 2:
                plus(img, ox, cx, cy - 1, rgb(SPARK_WHITE), 2)
        if f >= 3:
            # Sparkles drift up and away, shrinking and fading.
            t = f - 2
            fade = max(0, 255 - 45 * max(0, f - 4))
            for vx, vy, color in particles:
                x = round(cx + vx * t)
                y = round(cy + vy * t + 0.25 * t * t)  # A little gravity
                if (f + x) % 5 == 0 and f >= 6:
                    continue  # Twinkle out
                arm = 1 if f <= 5 else 0
                plus(img, ox, x, y, rgb(color, fade), arm)
    return img


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('assets')
    outputs = {
        assets / 'sprites/ui/badge_player.png': make_badge(BADGE_STYLES['player']),
        assets / 'sprites/ui/badge_zombie.png': make_badge(BADGE_STYLES['zombie']),
        assets / 'sprites/chest/sparks.png': make_sparks(),
    }
    for path, img in outputs.items():
        img.save(path)
        print(f'make_sprites: {path} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
