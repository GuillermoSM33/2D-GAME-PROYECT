#!/usr/bin/env python3
"""Make the interface's pixel art: the font and the UI kit.

Usage: tools/make_ui.py [assets_dir]   (default: assets)

Writes, under sprites/ui/:
  font.png     The game's pixel font, uppercase: one 6 x 10 cell per glyph,
               in GLYPHS order (src/engine/pixfont.c has the same string).
               Rows 0-1 hold accents, 2-8 the letter, 9 a descender. White,
               so the game tints it. Lowercase is drawn with these.
  panel.png    A board for windows (24 x 24, 9-slice with 8 px corners):
               dark leather inside a wooden frame with brass corner studs
  button.png   A button, normal and selected (2 frames of 16 x 16, 9-slice
               with 5 px corners): a plank; selected, brass-edged and lit
  key.png      A key cap for the controls (14 x 14, 9-slice with 4 px corners)
  pip.png      A notch of a volume bar, empty and full (2 frames of 6 x 10)
  bar.png      The frame of a health or XP bar (12 x 8, 9-slice with 3 px corners)
  icons.png    12 x 12 icons: heart, bullet, skull, flag, dynamite, speaker,
               star, lock, check, shell, states, save, clock and mission stars
  weapons.png  The guns as they look in play, in WeaponId order (4 frames of
               36 x 14): the hand cannon cut from the cowgirl's shoot sheet,
               the SWAT's rifle and shotgun from tools/make_swat.py, and the
               plasma cannon as the Hero's stand-in shows it (the hand cannon
               in his tint). Re-run it after changing those sheets.

Deterministic; uses only the standard library.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402
from make_swat import INK as SWAT_INK, METAL as SWAT_METAL  # noqa: E402
from make_swat import rifle as swat_rifle, shotgun as swat_shotgun  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Same order as PIXFONT_GLYPHS in src/engine/pixfont.c.
GLYPHS = (" !¡?¿.,:;'\"-+/()%×·→←↑↓=✓∞"
          "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZÁÉÍÓÚÜ")
CELL_W, CELL_H = 6, 10

# 7 body rows each (rows 2-8 of the cell); "accent" adds rows 0-1, "desc" row 9.
FONT = {
    ' ': ['...'] * 7,
    '!': ['#', '#', '#', '#', '#', '.', '#'],
    '¡': ['#', '.', '#', '#', '#', '#', '#'],
    '?': ['.###.', '#...#', '....#', '...#.', '..#..', '.....', '..#..'],
    '¿': ['..#..', '.....', '..#..', '.#...', '#....', '#...#', '.###.'],
    '.': ['.', '.', '.', '.', '.', '.', '#'],
    ',': ['.', '.', '.', '.', '.', '.', '#'],
    ':': ['.', '#', '.', '.', '.', '#', '.'],
    ';': ['.', '#', '.', '.', '.', '.', '#'],
    "'": ['#', '#', '.', '.', '.', '.', '.'],
    '"': ['#.#', '#.#', '...', '...', '...', '...', '...'],
    '-': ['....', '....', '....', '####', '....', '....', '....'],
    '+': ['.....', '..#..', '..#..', '#####', '..#..', '..#..', '.....'],
    '/': ['....#', '...#.', '...#.', '..#..', '.#...', '.#...', '#....'],
    '(': ['.#', '#.', '#.', '#.', '#.', '#.', '.#'],
    ')': ['#.', '.#', '.#', '.#', '.#', '.#', '#.'],
    '%': ['##..#', '##.#.', '...#.', '..#..', '.#...', '.#.##', '#..##'],
    '×': ['.....', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '.....'],
    '·': ['.', '.', '.', '#', '.', '.', '.'],
    '→': ['.....', '..#..', '...#.', '#####', '...#.', '..#..', '.....'],
    '←': ['.....', '..#..', '.#...', '#####', '.#...', '..#..', '.....'],
    '↑': ['..#..', '.###.', '#.#.#', '..#..', '..#..', '..#..', '..#..'],
    '↓': ['..#..', '..#..', '..#..', '..#..', '#.#.#', '.###.', '..#..'],
    '=': ['.....', '.....', '#####', '.....', '#####', '.....', '.....'],
    '✓': ['.....', '.....', '....#', '...#.', '#.#..', '.#...', '.....'],
    '∞': ['.....', '.....', '.#.#.', '#.#.#', '.#.#.', '.....', '.....'],
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '1': ['.#.', '##.', '.#.', '.#.', '.#.', '.#.', '###'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    '3': ['####.', '....#', '....#', '.###.', '....#', '....#', '####.'],
    '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
    '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
    '6': ['.###.', '#....', '#....', '####.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.####', '....#', '....#', '.###.'],
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
    'G': ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.####'],
    'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '###'],
    'J': ['..###', '...#.', '...#.', '...#.', '#..#.', '#..#.', '.##..'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
    'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'Q': ['.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'V': ['#...#', '#...#', '#...#', '#...#', '#...#', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '#.#.#', '.#.#.'],
    'X': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    'Y': ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
}
ACCENT = {'Á': ('A', ['...#.', '..#..']), 'É': ('E', ['...#.', '..#..']),
          'Í': ('I', ['..#', '.#.']), 'Ó': ('O', ['...#.', '..#..']),
          'Ú': ('U', ['...#.', '..#..']), 'Ü': ('U', ['.....', '.#.#.']),
          'Ñ': ('N', ['.##.#', '#.##.'])}
DESCENDER = {',': '#', ';': '#'}


def make_font() -> Image:
    img = Image(CELL_W * len(GLYPHS), CELL_H)
    white = rgb(0xffffff)
    for i, ch in enumerate(GLYPHS):
        base, accent = ACCENT.get(ch, (ch, None))
        rows = FONT[base]
        assert len(rows) == 7, ch
        for y, row in enumerate(rows):
            for x, c in enumerate(row):
                if c == '#':
                    img.set(i * CELL_W + x, 2 + y, white)
        for y, row in enumerate(accent or []):
            for x, c in enumerate(row):
                if c == '#':
                    img.set(i * CELL_W + x, y, white)
        if ch in DESCENDER:
            img.set(i * CELL_W, 9, white)
    return img


INK = rgb(0x1a1210)
WOOD = [rgb(0x3a2316), rgb(0x56351f), rgb(0x76492a), rgb(0x9a643a), rgb(0xbf8650)]
LEATHER = [rgb(0x1e1614), rgb(0x2a201c), rgb(0x362a24)]
BRASS = [rgb(0x6a4e1e), rgb(0x9c7a32), rgb(0xd0a848), rgb(0xf0d27a)]
IRON = [rgb(0x24242a), rgb(0x3c3c44), rgb(0x5c5c66), rgb(0x8a8a94), rgb(0xb8b8c0)]
RED = [rgb(0x5a1c16), rgb(0x9c3424), rgb(0xd0503a), rgb(0xf08a6a)]
BONE = [rgb(0x8a7e68), rgb(0xcfc4a8), rgb(0xf6efdc)]
GREEN = [rgb(0x2e4a26), rgb(0x4f7a3a), rgb(0x7fb069)]
TEAL = [rgb(0x1e5a50), rgb(0x3aa08a), rgb(0x80ffd8)]
CLEAR = (0, 0, 0, 0)


def rect(img: Image, x0: int, y0: int, x1: int, y1: int, c) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            img.set(x, y, c)


def make_panel() -> Image:
    s = 24
    img = Image(s, s)
    rect(img, 0, 0, s - 1, s - 1, INK)
    rect(img, 1, 1, s - 2, s - 2, WOOD[2])                 # Wooden frame
    rect(img, 1, 1, s - 2, 1, WOOD[4])
    rect(img, 1, 1, 1, s - 2, WOOD[3])
    rect(img, 1, s - 2, s - 2, s - 2, WOOD[0])
    rect(img, s - 2, 1, s - 2, s - 2, WOOD[1])
    rect(img, 4, 4, s - 5, s - 5, INK)                      # Leather inside
    rect(img, 5, 5, s - 6, s - 6, LEATHER[1])
    rect(img, 5, 5, s - 6, 5, LEATHER[2])
    for k in range(6, s - 6, 2):                            # Stitching along the edge
        img.set(k, 6, LEATHER[0])
        img.set(6, k, LEATHER[0])
        img.set(k, s - 7, LEATHER[0])
        img.set(s - 7, k, LEATHER[0])
    for cx, cy in ((2, 2), (s - 4, 2), (2, s - 4), (s - 4, s - 4)):  # Brass studs
        rect(img, cx, cy, cx + 1, cy + 1, BRASS[2])
        img.set(cx, cy, BRASS[3])
        img.set(cx + 1, cy + 1, BRASS[1])
    return img


def make_button() -> Image:
    s = 16
    img = Image(s * 2, s)
    for f in range(2):
        ox = f * s
        edge = BRASS if f else WOOD
        rect(img, ox, 0, ox + s - 1, s - 1, INK)
        rect(img, ox + 1, 1, ox + s - 2, s - 2, edge[2])
        rect(img, ox + 1, 1, ox + s - 2, 1, edge[3])
        rect(img, ox + 1, s - 2, ox + s - 2, s - 2, edge[0])
        fill = [WOOD[1], WOOD[2], WOOD[3]] if not f else [WOOD[2], WOOD[3], WOOD[4]]
        rect(img, ox + 3, 3, ox + s - 4, s - 4, fill[1])
        rect(img, ox + 3, 3, ox + s - 4, 3, fill[2])
        rect(img, ox + 3, s - 4, ox + s - 4, s - 4, fill[0])
        for x in (ox + 2, ox + s - 3):                      # Nails
            img.set(x, 2, IRON[4] if f == 0 else BRASS[3])
            img.set(x, s - 3, IRON[3] if f == 0 else BRASS[2])
    return img


def make_key() -> Image:
    s = 14
    img = Image(s, s)
    rect(img, 0, 0, s - 1, s - 1, INK)
    rect(img, 1, 1, s - 2, s - 2, BONE[0])
    rect(img, 1, 1, s - 2, s - 4, BONE[1])
    rect(img, 2, 1, s - 3, 1, BONE[2])
    return img


def make_pip() -> Image:
    w, h = 6, 10
    img = Image(w * 2, h)
    for f in range(2):
        ox = f * w
        rect(img, ox, 0, ox + 4, h - 1, INK)
        if f:
            rect(img, ox + 1, 1, ox + 3, h - 2, BRASS[2])
            rect(img, ox + 1, 1, ox + 3, 2, BRASS[3])
            rect(img, ox + 1, h - 3, ox + 3, h - 2, BRASS[1])
        else:
            rect(img, ox + 1, 1, ox + 3, h - 2, LEATHER[2])
    return img


def make_bar() -> Image:
    w, h = 12, 8
    img = Image(w, h)
    rect(img, 0, 0, w - 1, h - 1, INK)
    rect(img, 1, 1, w - 2, h - 2, IRON[2])
    rect(img, 1, 1, w - 2, 1, IRON[3])
    rect(img, 2, 2, w - 3, h - 3, LEATHER[0])               # The empty tube the fill goes in
    return img


def icon(img: Image, frame: int, rows: list[str], colors: dict) -> None:
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != '.':
                img.set(frame * 12 + x, y, colors[c])


def make_icons() -> Image:
    img = Image(12 * 26, 12)
    k = INK
    icon(img, 0, [  # Heart
        '............', '.kk....kk...', 'krrk..krrk..', 'krRrkkrrrk..', 'krRrrrrrrk..',
        'krrrrrrrrk..', '.krrrrrrk...', '..krrrrk....', '...krrk.....', '....kk......',
        '............', '............'], {'k': k, 'r': RED[1], 'R': RED[3]})
    icon(img, 1, [  # Bullet
        '............', '.....kk.....', '....kYYk....', '....kYyk....', '....kYyk....',
        '...kbbbbk...', '...kBbbbk...', '...kBbbbk...', '...kBbbbk...', '...kbbbbk...',
        '...kkkkkk...', '............'],
        {'k': k, 'Y': BRASS[3], 'y': BRASS[2], 'b': BRASS[1], 'B': BRASS[2]})
    icon(img, 2, [  # Skull
        '............', '...kkkkk....', '..kwwwwwk...', '.kwWwwwwwk..', '.kwkkwkkwk..',
        '.kwkkwkkwk..', '.kwwwkwwwk..', '..kwwwwwk...', '..kwkwkwk...', '...kkkkk....',
        '............', '............'], {'k': k, 'w': BONE[1], 'W': BONE[2]})
    icon(img, 3, [  # Flag
        '............', '.kk.........', '.kgkkkkk....', '.kgRRRRRk...', '.kgRrRrRk...',
        '.kgRRRRRk...', '.kgkkkkk....', '.kgk........', '.kgk........', '.kgk........',
        'kkkkk.......', '............'], {'k': k, 'g': WOOD[3], 'R': RED[2], 'r': RED[3]})
    icon(img, 4, [  # Dynamite
        '.......y....', '......Y.y...', '.....kk.....', '..kkkkkkk...', '.krrkrrkrk..',
        '.kRrkRrkRk..', '.kwwwwwwwk..', '.kRrkRrkRk..', '.krrkrrkrk..', '.krrkrrkrk..',
        '..kkkkkkk...', '............'],
        {'k': k, 'r': RED[1], 'R': RED[2], 'w': WOOD[3], 'y': BRASS[2], 'Y': BRASS[3]})
    icon(img, 5, [  # Speaker
        '............', '.....k......', '....kk...k..', '.kkkwk.k..k.', '.kwwwk..k.k.',
        '.kwwwk..k.k.', '.kkkwk.k..k.', '....kk...k..', '.....k......', '............',
        '............', '............'], {'k': k, 'w': BONE[1]})
    icon(img, 6, [  # Star
        '.....k......', '....kYk.....', '....kYk.....', 'kkkkYYYkkkk.', '.kYYYYYYYk..',
        '..kYYyYYk...', '..kYykyYk...', '.kYyk.kyYk..', '.kkk...kkk..', '............',
        '............', '............'], {'k': k, 'Y': BRASS[3], 'y': BRASS[2]})
    icon(img, 7, [  # Lock
        '............', '...kkkk.....', '..kiiiik....', '..ki..ik....', '..ki..ik....',
        '.kkkkkkkk...', '.kbbbbbbk...', '.kbbkkbbk...', '.kbbkkbbk...', '.kbbbbbbk...',
        '.kkkkkkkk...', '............'], {'k': k, 'i': IRON[3], 'b': BRASS[2]})
    icon(img, 8, [  # Check
        '............', '.........kk.', '........kgk.', '.......kgk..', '.kk...kgk...',
        'kgk..kgk....', '.kgkkgk.....', '..kggk......', '...kk.......', '............',
        '............', '............'], {'k': k, 'g': GREEN[2]})
    icon(img, 9, [  # Shotgun shell
        '............', '....kkk.....', '...kRRrk....', '...kRrrk....', '...kRrrk....',
        '...kRrrk....', '...kRrrk....', '...kYYyk....', '...kYyyk....', '...kkkkk....',
        '............', '............'], {'k': k, 'R': RED[3], 'r': RED[2], 'Y': BRASS[3], 'y': BRASS[2]})
    icon(img, 10, [  # Blood drop: bleeding
        '.....k......', '....krk.....', '....krk.....', '...krrrk....', '...kRrrk....',
        '..kRrrrrk...', '..kRrrrrk...', '..krrrrrk...', '...krrrk....', '....kkk.....',
        '............', '............'], {'k': k, 'r': RED[1], 'R': RED[2]})
    icon(img, 11, [  # Boot and shackle: slowed down
        '............', '...kkkk.....', '...kbbk.....', '...kbbk.....', '...kbbk.....',
        '...kbbkkkk..', '...kbbbbbbk.', '...kkkkkkkk.', '..kiik......', '.kik.kik....',
        '..kiik......', '............'], {'k': k, 'b': WOOD[2], 'i': IRON[3]})
    icon(img, 12, [  # Gold coin
        '............', '...kkkkk....', '..kYYYYyk...', '.kYYyyyYyk..', '.kYyYYYyyk..', '.kYyYyyyyk..',
        '.kYyYyyyyk..', '.kYyyyyyyk..', '..kyyyyyk...', '...kkkkk....', '............',
        '............'], {'k': k, 'Y': BRASS[3], 'y': BRASS[2]})
    icon(img, 13, [  # Wind: gusts
        '............', '.kkkkkk.....', '.wwwwwwk....', '.kkkkkkwk...', '......kwk...', 'kkkkkkkkkk..',
        'wwwwwwwwwwk.', 'kkkkkkkkkk..', '...kkkkk....', '...wwwwwk...', '...kkkkkk...',
        '............'], {'k': k, 'w': IRON[4]})
    icon(img, 14, [  # Current: waves
        '............', '............', '.kk...kk....', 'kbbk.kbbk.k.', 'b..bkb..bkb.', '.....k...k..',
        '.kk...kk....', 'kbbk.kbbk.k.', 'b..bkb..bkb.', '.....k...k..', '............',
        '............'], {'k': k, 'b': rgb(0x6ab0d0)})
    icon(img, 15, [  # Heat: a blazing sun
        '.....r......', '..r..r..r...', '...kkkkk....', '..kyyyyyk...', 'rrkyYYYykrr.', '..kyYYYyk...',
        '..kyyyyyk...', '...kkkkk....', '..r..r..r...', '.....r......', '............',
        '............'], {'k': k, 'y': BRASS[2], 'Y': BRASS[3], 'r': RED[2]})
    icon(img, 16, [  # Omen: a crow's eye
        '............', '..kkkkkkk...', '.kkbbbbbkk..', 'kkbbwwwbbkk.', 'kbbwwrrwbbk.', 'kbbwwrrwbbk.',
        'kkbbwwwbbkk.', '.kkbbbbbkk..', '..kkkkkkk...', '............', '............',
        '............'], {'k': k, 'b': rgb(0x22242c), 'w': rgb(0xd8d4c8), 'r': RED[2]})
    icon(img, 17, [  # Cold: a snowflake
        '.....k......', '..k.kwk.k...', '.kwkkwkkwk..', '..kwkwkwk...', 'kkkkwwwkkkk.', 'kwwwwiwwwwk.',
        'kkkkwwwkkkk.', '..kwkwkwk...', '.kwkkwkkwk..', '..k.kwk.k...', '.....k......',
        '............'], {'k': k, 'w': rgb(0xc8e4f4), 'i': rgb(0xffffff)})
    icon(img, 18, [  # Wet: drops
        '...k........', '..kbk.......', '.kbbbk...k..', '.kbwbk..kbk.', '.kbbbk.kbbbk', '..kkk..kbwbk',
        '.......kbbbk', '...k....kkk.', '..kbk.......', '.kbwbk......', '.kbbbk......',
        '..kkk.......'], {'k': k, 'b': rgb(0x5aa0c8), 'w': rgb(0xc8e4f4)})
    icon(img, 19, [  # Cozy: a campfire's flame over logs
        '.....k......', '....kyk.....', '...kyyk.k...', '..kyoyykok..', '..kyooyooyk.', '.kyoorroook.',
        '.kyorrrrook.', '..kooroook..', '.kkkkkkkkkk.', 'kwwkwwwkwwk.', '.kkkkkkkkk..',
        '............'], {'k': k, 'y': BRASS[3], 'o': rgb(0xf08a24), 'r': RED[2], 'w': WOOD[3]})
    icon(img, 20, [  # Water: a jug
        '....kkk.....', '...kccck....', '...kkckk....', '..kbbbbbk...', '.kbBBBBBbk..', '.kBwBBBBBk..',
        '.kBwBBBBBk..', '.kBBBBBBBk..', '.kbBBBBBbk..', '..kbbbbbk...', '...kkkkk....',
        '............'], {'k': k, 'c': WOOD[3], 'b': rgb(0x2a5a86), 'B': rgb(0x5aa0d0), 'w': rgb(0xd8f0fa)})
    icon(img, 21, [  # Refreshed: a drop and a sparkle
        '........w...', '....k..wWw..', '...kbk..w...', '...kbk......', '..kbBbk.....', '.kbBBBbk....',
        '.kbBwBbk....', '.kbBwBbk....', '..kbBbk.....', '...kkk......', '............',
        '............'], {'k': k, 'b': rgb(0x2a5a86), 'B': rgb(0x5aa0d0), 'w': rgb(0xd8f0fa), 'W': rgb(0xffffff)})
    icon(img, 22, [  # Bevelled brass case, steel shutter, label and red ink
        '.kkkkkkkkk..', 'kHBBBBBBBDk.', 'kBksswskBDk.', 'kBksswskBDk.', 'kBkkkkkkBDk.',
        'kHBBBBBBBDk.', 'kBkpppppkDk.', 'kBkpprrpkDk.', 'kBkpppppkDk.', 'kBkpppppkDk.',
        'kBDDDDDDDkk.', '.kkkkkkkkk..'],
        {'k': k, 'H': BRASS[3], 'B': BRASS[2], 'D': BRASS[0],
         's': IRON[2], 'w': IRON[3], 'p': rgb(0xead6b1), 'r': RED[1]})
    # A pocket-watch face: ink outline, warm metal rim, ivory dial and hands.
    for y in range(12):
        for x in range(12):
            distance = (x - 5.5) ** 2 + (y - 5.5) ** 2
            if distance > 30:
                continue
            color = k if distance > 23 else (BRASS[3] if x + y < 10 else BRASS[1]) if distance > 14 else rgb(0xead6b1)
            img.set(23 * 12 + x, y, color)
    for x, y in ((5, 2), (9, 5), (6, 9), (2, 6), (5, 3), (5, 4), (5, 5), (6, 5), (7, 5), (8, 5)):
        img.set(23 * 12 + x, y, k)
    stars = ['.....kk.....', '....kHHk....', '....kHYk....', '.kkkHYYkkk..',
             'kHHHYYYYyyk.', '.kHYYYYyyk..', '..kYYYYyk...', '..kYYyyyk...',
             '.kYYYkYyyk..', '.kYYk.kYyk..', '.kkk...kkk..', '............']
    icon(img, 24, stars, {'k': k, 'H': rgb(0xffedb0), 'Y': BRASS[3], 'y': BRASS[1]})
    icon(img, 25, stars, {'k': rgb(0x65594c), 'H': rgb(0x514236), 'Y': rgb(0x362b25), 'y': rgb(0x261f1d)})
    return img


WEAPON_W, WEAPON_H = 36, 14
HERO_TINT = 0x70c8b0  # The Hero's stand-in tint (src/game/characters.c): his gun in play


def revolver_pixels() -> dict:
    """The cowgirl's hand cannon as she aims it (shoot.png, frame 3), her hand
    and sleeve left out: (x, y) -> RGBA, from (0, 0)."""
    w, h, px = decode_png_rgba(ROOT / 'assets/sprites/characters/cowgirl/shoot.png')
    ox, x0, y0, x1, y1 = 81 * 3, 44, 29, 64, 38
    out = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            i = (y * w + ox + x) * 4
            c = tuple(px[i:i + 4])
            r, g, bl = c[:3]
            skin = r > 150 and g > 90 and r > bl + 40     # Her hand
            sleeve = x < 50 and y >= 37 and not (r > 90 and g > 90 and bl > 90)
            if c[3] and not skin and not sleeve:
                out[(x - x0, y - y0)] = c
    # Bits of her fingers' outline left on their own.
    lone = [xy for xy in out
            if sum((xy[0] + dx, xy[1] + dy) in out for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) == 0]
    for xy in lone:
        del out[xy]
    return out


def swat_pixels(gun: dict) -> dict:
    """A SWAT gun template (tools/make_swat.py) in its metal colors, outlined
    like on his shoot sheets."""
    inked = {}
    xs = [x for x, _ in gun]
    ys = [y for _, y in gun]
    for (x, y), key in gun.items():
        inked[(x - min(xs) + 1, y - min(ys) + 1)] = SWAT_METAL[key]
    out = dict(inked)
    for (x, y) in inked:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in inked:
                out[(x + dx, y + dy)] = SWAT_INK
    return out


def tinted(pixels: dict, tint: int) -> dict:
    """The same recolor as a stand-in character (character_skin.c): every
    color a shade of the tint by its brightness."""
    out = {}
    for xy, c in pixels.items():
        lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
        shade = lum / 150.0
        out[xy] = tuple(min(255, round(((tint >> (8 * k)) & 0xFF) * shade)) for k in (2, 1, 0)) + (255,)
    return out


def dual_pixels(revolver: dict) -> dict:
    """The cowgirl's dual pistols: a second hand cannon up and behind, darker
    (as on her shoot_dual sheet)."""
    out = {}
    for (x, y), c in revolver.items():
        out[(x, y)] = tuple(round(v * 0.72) for v in c[:3]) + (255,)
    shifted = {(x + 3, y + 4): c for (x, y), c in revolver.items()}
    out = {(x, y + 0): c for (x, y), c in out.items()}
    out.update(shifted)
    return out


def grenade_pixels() -> dict:
    """The SWAT's hand grenade (weapons/grenade.png frame 0), twice as big."""
    w, h, px = decode_png_rgba(ROOT / 'assets/sprites/weapons/grenade.png')
    out = {}
    for y in range(8):
        for x in range(8):
            i = (y * w + x) * 4
            if px[i + 3]:
                for dy in range(2):
                    for dx in range(2):
                        out[(x * 2 + dx, y * 2 + dy)] = tuple(px[i:i + 4])
    return out


def make_weapons() -> Image:
    """The guns as they look in play, centered in 36 x 14 frames, in WeaponId
    order: hand cannon, rifle, shotgun, plasma cannon, dual pistols; then the
    grenade (UI_GRENADE). Run tools/make_powers.py first."""
    revolver = revolver_pixels()
    guns = [revolver, swat_pixels(swat_rifle()[0]), swat_pixels(swat_shotgun()[0]),
            tinted(revolver, HERO_TINT), dual_pixels(revolver), grenade_pixels()]
    img = Image(WEAPON_W * len(guns), WEAPON_H)
    for f, pixels in enumerate(guns):
        w = max(x for x, _ in pixels) + 1
        h = max(y for _, y in pixels) + 1
        ox, oy = (WEAPON_W - w) // 2, (WEAPON_H - h) // 2
        for (x, y), c in pixels.items():
            img.set(f * WEAPON_W + ox + x, oy + y, c)
    return img


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'assets'
    out = {
        'font': make_font(), 'panel': make_panel(), 'button': make_button(), 'key': make_key(),
        'pip': make_pip(), 'bar': make_bar(), 'icons': make_icons(), 'weapons': make_weapons(),
    }
    for name, img in out.items():
        path = assets / 'sprites' / 'ui' / f'{name}.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        print(f'make_ui: sprites/ui/{name}.png ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
