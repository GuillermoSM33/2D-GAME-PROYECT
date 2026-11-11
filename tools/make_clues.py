#!/usr/bin/env python3
"""Make the clues' pictures (src/game/casefile.c, "Encuentra la causa").

Usage: tools/make_clues.py [assets_dir]   (default: assets)

Writes sprites/clues/clues.png: one 24 x 24 frame per clue, in CLUES order,
and sprites/clues/stamp.png: the tilted RESUELTO stamp of a solved case.
Drawn like the HUD's icons: a dark outline, flat colors, light from the top
left. They show on the case file's board (at 2x), in the popup when one is
found and big in the story beats. Deterministic; standard library only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_cinematics import Canvas, GLYPHS, poly  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SIZE = 24
OUTLINE = rgb(0x231a14)
PAPER = [rgb(0xa89a7c), rgb(0xcfc3a4), rgb(0xebe1c6), rgb(0xfaf4e2)]
INK = rgb(0x3a3430)
INK_LIGHT = rgb(0x7a7064)
RED = [rgb(0x5a1410), rgb(0x902004), rgb(0xc03a14), rgb(0xe8573a)]
WOOD = [rgb(0x3a2316), rgb(0x56351f), rgb(0x76492a), rgb(0x9a643a)]
METAL = [rgb(0x3c3c44), rgb(0x6a6a74), rgb(0xa8a8b0), rgb(0xd8d8e0)]
TAPE = [rgb(0x141418), rgb(0x24242a), rgb(0x3a3a42), rgb(0x5a5a64)]
TEAL = [rgb(0x123636), rgb(0x1c5250), rgb(0x2f7a72), rgb(0x6cc4b4)]
GREEN = [rgb(0x0f3a22), rgb(0x1f7a3e), rgb(0x46c060), rgb(0x9cf08a)]
BLUE = [rgb(0x142a5a), rgb(0x24489a), rgb(0x4a78d0), rgb(0xa8c8f0)]
GOLD = [rgb(0x6a4e1e), rgb(0x9c7a32), rgb(0xd0a848), rgb(0xf0d27a)]
SEPIA = [rgb(0x4a3422), rgb(0x7a5a3a), rgb(0xa88458), rgb(0xd8bc8a)]
BLOOD = rgb(0x6a1410)


def outline(c: Canvas) -> None:
    solid = {(x, y) for y in range(SIZE) for x in range(c.w) if c.get(x, y)[3] and c.get(x, y) != OUTLINE}
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in solid and 0 <= x + dx < c.w and 0 <= y + dy < SIZE \
                    and not c.get(x + dx, y + dy)[3]:
                c.px(x + dx, y + dy, OUTLINE)


def paper(c: Canvas, x0: int, y0: int, x1: int, y1: int, fold: bool = True) -> None:
    c.fill(x0, y0, x1, y1, PAPER[2])
    c.hline(x0, x1, y0, PAPER[3])
    c.vline(x0, y0, y1, PAPER[3])
    c.hline(x0, x1, y1, PAPER[0])
    c.vline(x1, y0, y1, PAPER[1])
    if fold:  # A dog-eared corner
        c.px(x1, y0, (0, 0, 0, 0))
        c.px(x1 - 1, y0, PAPER[1])
        c.px(x1, y0 + 1, PAPER[1])


def lines(c: Canvas, x0: int, x1: int, y0: int, rows: int, step: int = 2, seed: int = 0) -> None:
    for r in range(rows):
        end = x1 - ((r * 3 + seed) % 4)
        c.hline(x0, end, y0 + r * step, INK_LIGHT)


def text(c: Canvas, x: int, y: int, s: str, col) -> None:
    for ch in s:
        for j, row in enumerate(GLYPHS[ch]):
            for i, bit in enumerate(row):
                if bit == '#':
                    c.px(x + i, y + j, col)
        x += 4


def clipboard(c: Canvas) -> None:
    c.fill(4, 3, 19, 22, WOOD[2])
    c.hline(4, 19, 3, WOOD[3])
    c.vline(4, 3, 22, WOOD[3])
    c.hline(4, 19, 22, WOOD[0])
    paper(c, 6, 6, 17, 21, fold=False)
    c.fill(8, 1, 15, 5, METAL[2])  # The clip
    c.hline(8, 15, 1, METAL[3])
    c.fill(10, 2, 13, 3, METAL[0])


def cassette(c: Canvas, label, number: str) -> None:
    c.fill(2, 6, 21, 18, TAPE[1])
    c.hline(2, 21, 6, TAPE[3])
    c.vline(2, 6, 18, TAPE[2])
    c.fill(4, 8, 19, 13, label[2])          # Its label
    c.hline(4, 19, 8, label[3])
    c.fill(9, 10, 17, 12, TAPE[0])          # The window onto the reels
    c.fill(10, 11, 11, 11, METAL[2])
    c.fill(15, 11, 16, 11, METAL[2])
    c.fill(6, 15, 17, 18, TAPE[2])          # The bottom ridge with its holes
    c.px(8, 16, TAPE[0])
    c.px(15, 16, TAPE[0])
    c.fill(4, 8, 7, 13, label[3])           # The tape's number on its label's end
    text(c, 5, 8, number, INK)


def make_clues() -> Image:
    img = Image(SIZE * 15, SIZE)

    def frame(i: int) -> Canvas:
        return Canvas(img, i * SIZE, SIZE)

    # 0 Orden de traslado: a transfer form on a clipboard, its header red
    c = frame(0)
    clipboard(c)
    c.fill(7, 7, 16, 9, RED[2])
    c.hline(7, 16, 7, RED[3])
    lines(c, 8, 15, 12, 5, seed=1)
    c.fill(13, 18, 15, 19, RED[1])          # A signature's scrawl
    outline(c)

    # 1 Credencial de prensa: a press card on its lanyard, a blood stain
    c = frame(1)
    c.vline(11, 0, 4, BLUE[1])
    c.vline(12, 0, 4, BLUE[2])
    c.fill(5, 5, 18, 22, PAPER[3])
    c.hline(5, 18, 5, METAL[3])
    c.fill(5, 6, 18, 9, BLUE[2])            # Its PRESS band
    c.hline(5, 18, 6, BLUE[3])
    c.fill(7, 11, 11, 16, SEPIA[2])         # The photo
    c.fill(8, 12, 10, 13, SEPIA[1])
    c.fill(7, 15, 11, 16, SEPIA[1])
    c.hline(13, 17, 12, INK_LIGHT)
    c.hline(13, 16, 14, INK_LIGHT)
    c.hline(7, 17, 19, INK)
    for (x, y) in ((12, 16), (13, 16), (13, 17), (14, 17), (14, 18), (15, 17), (12, 20), (13, 21)):
        c.px(x, y, BLOOD)
    outline(c)

    # 2, 9, 10 The tapes: Valeria's cassettes, labels of different colors
    for i, label, n in ((2, PAPER, '1'), (9, GOLD, '2'), (10, TEAL, '3')):
        c = frame(i)
        cassette(c, label, n)
        outline(c)

    # 3 Registro de ingreso: the hospital's admissions book, open, a ribbon in it
    c = frame(3)
    c.fill(1, 5, 22, 20, RED[1])            # Its cover around the pages
    c.fill(2, 5, 11, 18, PAPER[2])
    c.fill(12, 5, 21, 18, PAPER[3])
    c.vline(11, 5, 18, PAPER[0])            # The spine's fold
    c.vline(12, 5, 18, PAPER[1])
    for r in range(5):                      # Rows of entries, the last one in red
        c.hline(3, 10 - (r % 2), 7 + r * 2, INK_LIGHT)
        c.hline(13, 20 - (r % 3), 7 + r * 2, RED[2] if r == 4 else INK_LIGHT)
    c.vline(16, 2, 9, RED[2])               # The ribbon
    c.px(16, 10, RED[1])
    outline(c)

    # 4 Foto del pasillo: a snapshot of stretchers in a green-lit corridor
    c = frame(4)
    c.fill(3, 3, 20, 21, PAPER[3])
    c.hline(3, 20, 21, PAPER[1])
    c.fill(5, 5, 18, 16, TEAL[0])
    c.fill(5, 5, 18, 7, TEAL[1])            # The ceiling's light
    c.hline(5, 18, 13, TEAL[1])             # The floor's line
    for x0 in (6, 12):                      # Two stretchers
        c.fill(x0, 10, x0 + 4, 11, PAPER[2])
        c.px(x0, 12, METAL[1])
        c.px(x0 + 4, 12, METAL[1])
        c.px(x0 + 1, 9, rgb(0x2c2c2c))      # Someone lying on it
    outline(c)

    # 5 Hoja clínica: a chart whose heartbeat goes flat, then jumps
    c = frame(5)
    paper(c, 4, 2, 19, 21)
    c.fill(4, 2, 19, 4, RED[1])
    trace = [0, 0, 0, -3, 1, 0, 0, 0, 0, 0, 0, -4, 2, 0, 0]
    for k, dy in enumerate(trace):          # A continuous line: each step joined to the last
        y = 11 + dy
        prev = 11 + (trace[k - 1] if k else 0)
        for yy in range(min(y, prev), max(y, prev) + 1):
            c.px(5 + k, yy, RED[2])
    lines(c, 6, 17, 15, 3, seed=3)
    outline(c)

    # 6 Memorándum de Vantrell: its V in teal and a red CONFIDENCIAL stamp
    c = frame(6)
    paper(c, 4, 2, 19, 21)
    for k in range(4):                      # The V
        c.px(6 + k // 2, 4 + k, TEAL[2])
        c.px(10 - k // 2, 4 + k, TEAL[2])
    lines(c, 6, 17, 10, 3, seed=1)
    c.fill(7, 16, 17, 19, RED[2])           # The stamp, a little crooked
    c.fill(8, 17, 16, 18, PAPER[2])
    c.hline(9, 15, 17, RED[1])
    outline(c)

    # 7 Informe del día 94: a curve going up and up
    c = frame(7)
    paper(c, 4, 2, 19, 21)
    c.vline(6, 5, 17, INK)
    c.hline(6, 17, 17, INK)
    for k in range(11):
        c.px(7 + k, 16 - int((k / 10) ** 2.2 * 10), RED[2] if k > 7 else INK)
    text(c, 13, 4, '9', RED[2])
    outline(c)

    # 8 Muestra rota: a snapped tube, still glowing
    c = frame(8)
    c.fill(7, 12, 15, 20, rgb(0x283038))    # The tube's lower half
    c.fill(8, 15, 14, 19, GREEN[2])
    c.hline(8, 14, 15, GREEN[3])
    c.vline(9, 16, 18, GREEN[3])
    for (x, y) in ((7, 11), (9, 12), (11, 11), (13, 12), (15, 11)):  # Its jagged edge
        c.px(x, y, rgb(0x9aa8b4))
    for (x0, y0) in ((5, 5), (14, 3), (18, 8)):   # Shards of its top half, flung off
        c.px(x0, y0, rgb(0x9aa8b4))
        c.px(x0 + 1, y0, rgb(0xdce6ee))
        c.px(x0, y0 + 1, rgb(0x56626e))
    c.px(11, 7, GREEN[3])                   # Drops in the air
    c.px(13, 9, GREEN[2])
    for (x, y) in ((17, 20), (18, 19), (5, 21)):  # Drops on the ground
        c.px(x, y, GREEN[2])
    c.fill(9, 13, 13, 13, PAPER[3])         # Its label
    outline(c)

    # 11 Tarjeta de acceso: a teal keycard, gold chip, the name scratched out
    c = frame(11)
    c.fill(2, 6, 21, 18, TEAL[2])
    c.hline(2, 21, 6, TEAL[3])
    c.vline(2, 6, 18, TEAL[3])
    c.hline(2, 21, 18, TEAL[1])
    c.fill(4, 9, 8, 13, GOLD[2])
    c.hline(4, 8, 9, GOLD[3])
    c.px(6, 11, GOLD[1])
    text(c, 11, 8, '4', PAPER[3])
    for k in range(7):                      # The scratches over the name
        c.px(10 + k, 15 - (k % 2), PAPER[1])
    c.fill(10, 14, 12, 16, PAPER[3])        # ...all but its first letter
    outline(c)

    # 12 Bata quemada: a folded lab coat, scorched along its sleeve
    c = frame(12)
    poly(c, [(4, 4), (19, 4), (21, 20), (2, 20)], PAPER[3])
    poly(c, [(9, 4), (14, 4), (12, 11)], PAPER[1])          # The collar's V
    c.vline(12, 11, 20, PAPER[1])
    c.fill(5, 8, 7, 9, BLUE[2])             # The name embroidered on the chest
    for (x, y) in ((16, 13), (17, 14), (18, 14), (17, 15), (18, 16), (19, 17), (16, 16)):
        c.px(x, y, rgb(0x3a2a20))           # The plasma's burns
    c.px(17, 13, rgb(0x2a1a14))
    c.px(18, 15, GOLD[1])
    outline(c)

    # 13 Plano del prototipo: a blueprint with a long gun drawn in white
    c = frame(13)
    c.fill(2, 4, 21, 20, BLUE[1])
    c.hline(2, 21, 4, BLUE[2])
    for x in range(4, 21, 4):
        c.vline(x, 5, 19, rgb(0x2a52a8))
    c.hline(5, 18, 11, BLUE[3])             # The cannon's barrel...
    c.fill(6, 9, 12, 13, BLUE[3])           # ...its body...
    c.fill(7, 10, 11, 12, BLUE[1])
    c.fill(8, 14, 9, 16, BLUE[3])           # ...and grip
    c.px(19, 11, rgb(0x9cf08a))             # Where the plasma comes out
    outline(c)

    # 14 Foto vieja: two friends, sepia, a corner bent
    c = frame(14)
    c.fill(3, 3, 20, 21, PAPER[2])
    c.fill(5, 5, 18, 16, SEPIA[2])
    c.fill(5, 5, 18, 8, SEPIA[3])           # Bright sky
    for (x, hair) in ((8, SEPIA[0]), (14, SEPIA[1])):
        c.fill(x - 1, 9, x + 1, 10, SEPIA[1])     # Heads
        c.hline(x - 1, x + 1, 9, hair)
        c.fill(x - 2, 11, x + 2, 16, SEPIA[0])    # Shoulders
    c.hline(10, 12, 12, SEPIA[0])           # An arm around the other
    c.px(20, 3, (0, 0, 0, 0))
    c.px(19, 3, PAPER[0])
    c.px(20, 4, PAPER[0])
    outline(c)
    return img


STAMP_RED = [rgb(0x7a1a10), rgb(0x9c2414)]
STAMP_GLYPHS = dict(GLYPHS, U=['#.#', '#.#', '#.#', '#.#', '###'])


def make_stamp() -> Image:
    """RESUELTO, the rubber stamp on a solved case's report: its letters and a
    frame in red ink, worn in spots, then tilted the way a hand stamps it.
    The tilt is done here, a pixel at a time, so it stays crisp at 3x."""
    word = 'RESUELTO'
    k = 2                                            # Each glyph pixel is 2 x 2
    text_w = len(word) * 4 * k - k
    w, h = text_w + 14, 5 * k + 14
    flat = [[None] * w for _ in range(h)]
    for x in range(w):                               # A double frame
        for y in (0, 1, h - 2, h - 1):
            flat[y][x] = 1
    for y in range(h):
        for x in (0, 1, w - 2, w - 1):
            flat[y][x] = 1
    for x in range(4, w - 4):
        flat[4][x] = flat[h - 5][x] = 1
    cx = 7
    for ch in word:
        for j, row in enumerate(STAMP_GLYPHS[ch]):
            for i, bit in enumerate(row):
                if bit == '#':
                    for dy in range(k):
                        for dx in range(k):
                            flat[7 + j * k + dy][cx + i * k + dx] = 1
        cx += 4 * k
    angle = math.radians(-11)
    ca, sa = math.cos(angle), math.sin(angle)
    out_w, out_h = int(w * abs(ca) + h * abs(sa)) + 2, int(w * abs(sa) + h * abs(ca)) + 2
    img = Image(out_w, out_h)
    seed = 7
    for y in range(out_h):
        for x in range(out_w):
            # Back into the flat stamp: nearest pixel, no blending
            fx = (x - out_w / 2) * ca + (y - out_h / 2) * sa + w / 2
            fy = -(x - out_w / 2) * sa + (y - out_h / 2) * ca + h / 2
            ix, iy = int(math.floor(fx)), int(math.floor(fy))
            if 0 <= ix < w and 0 <= iy < h and flat[iy][ix]:
                seed = (seed * 1103515245 + 12345) & 0x7fffffff
                if seed % 100 < 7:                   # Where the ink didn't take
                    continue
                img.set(x, y, STAMP_RED[1] if (seed >> 8) % 4 else STAMP_RED[0])
    return img


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'assets'
    image = make_clues()
    image.save(assets / 'sprites/clues/clues.png')
    print(f'sprites/clues/clues.png: {image.width} x {image.height}')
    stamp = make_stamp()
    stamp.save(assets / 'sprites/clues/stamp.png')
    print(f'sprites/clues/stamp.png: {stamp.width} x {stamp.height}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
