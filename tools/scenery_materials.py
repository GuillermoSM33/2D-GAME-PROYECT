"""Small, deterministic material painters shared by the map's pixel art.

All coordinates are native art pixels, boxes include their last pixel. Light
comes from above and left. Texture follows a material's construction rather
than sprinkling noise over the whole object.
"""
from __future__ import annotations

import math

from landscape_kit import Canvas, hash2, hx, mix, shade


def planks(c: Canvas, box: tuple, base, seed: int = 1,
           vertical: bool = False, width: int = 7) -> None:
    x0, y0, x1, y1 = box
    base = hx(base)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            across, along = (x - x0, y - y0) if vertical else (y - y0, x - x0)
            board, edge = divmod(across, width)
            tone = 0.86 + hash2(board, 0, seed) * 0.25
            if edge == 0:
                tone *= 0.55
            elif edge == 1:
                tone *= 1.17
            # Thin, interrupted fibers run along a board, with occasional knots.
            fiber = (across + round(math.sin(along / 13 + board * 2) * 1.2)) % width
            grain = hash2(along // 6, board, seed + 2)
            if fiber in (3, width - 2) and grain > 0.45:
                tone *= 0.82
            if (along + board * 13) % 51 == 0 and 1 < edge < width - 1:
                tone *= 0.7
            c.set(x, y, shade(base, tone))
    # Iron nail heads at the ends, with one worn highlight beside each.
    ncol, glint = shade(base, 0.35), shade(base, 1.3)
    if vertical:
        for x in range(x0 + width // 2, x1, width):
            for y in (y0 + 3, y1 - 3):
                c.set(x, y, ncol)
                c.set(x - 1, y, glint)
    else:
        for y in range(y0 + width // 2, y1, width):
            for x in (x0 + 3, x1 - 3):
                c.set(x, y, ncol)
                c.set(x - 1, y, glint)


def masonry(c: Canvas, box: tuple, base, seed: int = 1,
            brick: tuple = (14, 7)) -> None:
    x0, y0, x1, y1 = box
    base = hx(base)
    bw, bh = brick
    for y in range(y0, y1 + 1):
        row, ry = divmod(y - y0, bh)
        for x in range(x0, x1 + 1):
            column, rx = divmod(x - x0 + (bw // 2 if row % 2 else 0), bw)
            tone = 0.85 + hash2(column, row, seed) * 0.27
            if ry == bh - 1 or rx == bw - 1:
                tone *= 0.48
            elif ry == 0 or rx == 0:
                tone *= 1.12
            elif hash2(x // 2, y, seed + 4) > 0.9:
                tone *= 0.87
            c.set(x, y, shade(base, tone))


def metal(c: Canvas, box: tuple, base, seed: int = 1) -> None:
    x0, y0, x1, y1 = box
    base = hx(base)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            tone = 1.12 - 0.26 * (y - y0) / max(1, y1 - y0)
            # Rust gathers along the bottom seam and spreads in clusters.
            stain = hash2(x // 5, y // 4, seed)
            col = shade(base, tone)
            if stain > 0.8 and hash2(x // 2, y // 2, seed + 3) > 0.45:
                col = mix(col, (109, 65, 40), 0.6)
            if y == y0 or x == x0:
                col = shade(base, 1.3)
            elif y == y1 or x == x1:
                col = shade(base, 0.5)
            c.set(x, y, col)
    for x in range(x0 + 3, x1 - 1, 13):
        for y in (y0 + 2, y1 - 2):
            c.set(x, y, shade(base, 0.4))
            c.set(x - 1, y - 1, shade(base, 1.5))


def window(c: Canvas, x: int, y: int, w: int, h: int,
           lit: bool = False, broken: bool = False) -> None:
    c.fill(x - 2, y - 2, x + w + 1, y + h + 1, (38, 32, 30))
    c.hline(x - 3, x + w + 2, y - 3, (151, 133, 104))
    c.vline(x - 2, y - 2, y + h + 1, (112, 94, 75))
    for yy in range(h):
        for xx in range(w):
            color = (65, 84, 86) if xx < w // 2 and yy < h // 2 else (31, 43, 47)
            if lit:
                c.light(x + xx, y + yy, (197, 136, 61) if yy > h // 3 else (231, 177, 94))
            else:
                c.set(x + xx, y + yy, color)
    if broken:
        c.poly([(x + w // 2, y), (x + w // 3, y + h // 3),
                (x + w * 2 // 3, y + h // 2), (x + w // 2, y + h),
                (x + w - 1, y + h), (x + w - 1, y + 2)], (20, 23, 26))
    c.vline(x + w // 2, y, y + h - 1, (103, 91, 74))
    c.hline(x, x + w - 1, y + h // 2, (103, 91, 74))
    c.hline(x - 3, x + w + 2, y + h + 2, (139, 122, 94))
    c.hline(x - 2, x + w + 1, y + h + 3, (46, 38, 32))


FONT = {
    'A': ('010','101','111','101','101'), 'B': ('110','101','110','101','110'),
    'C': ('011','100','100','100','011'), 'D': ('110','101','101','101','110'),
    'E': ('111','100','110','100','111'), 'F': ('111','100','110','100','100'),
    'G': ('011','100','101','101','011'), 'H': ('101','101','111','101','101'),
    'I': ('111','010','010','010','111'), 'J': ('001','001','001','101','010'),
    'K': ('101','101','110','101','101'), 'L': ('100','100','100','100','111'),
    'M': ('101','111','111','101','101'), 'N': ('101','111','111','111','101'),
    'O': ('010','101','101','101','010'), 'P': ('110','101','110','100','100'),
    'Q': ('010','101','101','111','011'), 'R': ('110','101','110','101','101'),
    'S': ('011','100','010','001','110'), 'T': ('111','010','010','010','010'),
    'U': ('101','101','101','101','111'), 'V': ('101','101','101','101','010'),
    'W': ('101','101','111','111','101'), 'X': ('101','101','010','101','101'),
    'Y': ('101','101','010','010','010'), 'Z': ('111','001','010','100','111'),
    '0': ('111','101','101','101','111'), '1': ('010','110','010','010','111'),
    '2': ('110','001','010','100','111'), '3': ('110','001','010','001','110'),
    '4': ('101','101','111','001','001'), '5': ('111','100','110','001','110'),
    '6': ('011','100','111','101','111'), '7': ('111','001','010','010','010'),
    '8': ('111','101','111','101','111'), '9': ('111','101','111','001','110'),
    '-': ('000','000','111','000','000'), '.': ('000','000','000','000','010'),
}


def lettering(c: Canvas, text: str, x: int, y: int, color, scale: int = 1) -> None:
    color = hx(color)
    for i, char in enumerate(text.upper()):
        for row, bits in enumerate(FONT.get(char, ('000',) * 5)):
            for col, bit in enumerate(bits):
                if bit == '1':
                    px, py = x + (i * 4 + col) * scale, y + row * scale
                    c.fill(px, py, px + scale - 1, py + scale - 1, color)
