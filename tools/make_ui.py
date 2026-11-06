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
  icons_hd.png The detailed icons, 24 x 24, in UiIcon order (src/game/ui.h):
               tools/ui_icons.py. What ui_icon draws from scale 2 up
  icons.png    The same icons at 12 x 12, for the few places with no room for
               more, under the same rules: see ICONS and check_icon
  weapons_hd.png  The guns traced over their sprites in play, 72 x 28, in WeaponId
               order and then the grenade: tools/ui_icons.py. What ui_weapon draws
               from scale 2 up
  weapons.png  The sprites themselves, 36 x 14: pistol.png and the SWAT's templates
               in tools/make_swat.py, for the compact shortcuts
  notice_dev.png  The "in development" notice, 280 x 48: a site sign with hazard
               stripes and a plank for its icon

Everything else takes its colors from the materials in tools/ui_icons.py.

Deterministic; uses only the standard library.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui_icons as KIT  # noqa: E402
from embed_assets import decode_png_rgba  # noqa: E402
from make_swat import INK as SWAT_INK, METAL as SWAT_METAL  # noqa: E402
from make_swat import rifle as swat_rifle, shotgun as swat_shotgun  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402
from ui_icons import SIZE as ICON_HD_SIZE, draw_all as draw_icons_hd  # noqa: E402

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


# The shared materials (tools/ui_icons.py), here darkest first.
INK = KIT.INK
WOOD = list(reversed(KIT.WOOD))
LEATHER = [rgb(0x1e1614), rgb(0x2a201c), rgb(0x362a24)]
BRASS = list(reversed(KIT.BRASS))[:4]
IRON = list(reversed(KIT.IRON))
RED = list(reversed(KIT.RED))[1:]
BONE = list(reversed(KIT.BONE))[1:]
GREEN = list(reversed(KIT.GREEN))[1:]
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


def make_notice_dev() -> Image:
    """The "in development" notice: a site sign with hazard-striped bands and, on
    the left, a plank for its icon (24 x 24 art px at x 6, y 12)."""
    w, h = 280, 48
    img = Image(w, h)
    rect(img, 0, 0, w - 1, h - 1, INK)
    rect(img, 1, 1, w - 2, h - 2, WOOD[2])                  # Wooden frame
    rect(img, 1, 1, w - 2, 1, WOOD[4])
    rect(img, 1, 1, 1, h - 2, WOOD[3])
    rect(img, 1, h - 2, w - 2, h - 2, WOOD[0])
    rect(img, w - 2, 1, w - 2, h - 2, WOOD[1])
    rect(img, 3, 2, w - 4, h - 3, INK)
    for top in (3, h - 7):                                  # Hazard stripes
        for y in range(top, top + 4):
            for x in range(4, w - 4):
                img.set(x, y, KIT.FIRE[1] if (x + y) // 4 % 2 else KIT.BLACK[3])
    rect(img, 4, 8, w - 5, h - 9, LEATHER[1])               # Leather inside
    rect(img, 4, 8, w - 5, 8, LEATHER[2])
    rect(img, 4, 8, 31, h - 9, WOOD[1])                     # The icon's plank
    rect(img, 4, 8, 31, 8, WOOD[3])
    rect(img, 32, 8, 32, h - 9, INK)
    for k in range(36, w - 6, 2):                           # Stitching along the edge
        img.set(k, 10, LEATHER[0])
        img.set(k, h - 11, LEATHER[0])
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
        rect(img, ox + 1, 2, ox + 1, s - 3, edge[3])
        rect(img, ox + s - 2, 2, ox + s - 2, s - 3, edge[1])
        fill = [WOOD[0], WOOD[1], WOOD[2]] if not f else [WOOD[1], WOOD[2], WOOD[3]]
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
    rect(img, 1, 1, s - 3, 1, BONE[2])
    rect(img, 1, 1, 1, s - 4, BONE[2])
    rect(img, s - 2, 2, s - 2, s - 4, BONE[0])
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
            rect(img, ox + 1, 1, ox + 1, h - 3, BRASS[3])
        else:
            rect(img, ox + 1, 1, ox + 3, h - 2, LEATHER[1])
            rect(img, ox + 1, 1, ox + 3, 1, LEATHER[0])
            rect(img, ox + 1, h - 2, ox + 3, h - 2, LEATHER[2])
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


# One hand for every icon: a 12 x 12 cell with the drawing centered in it, a
# closed one-pixel ink outline, the light from the top left, and three tones
# of a shared material (H light, M base, S shade) bright enough to read on the
# dark leather. check_icon enforces what can be measured.
BRASS_ICON = {'H': rgb(0xffe9a0), 'M': BRASS[3], 'S': BRASS[1]}
RED_ICON = {'H': RED[3], 'M': rgb(0xdc4a34), 'S': RED[1]}
BONE_ICON = {'H': BONE[2], 'M': BONE[1], 'S': BONE[0]}
IRON_ICON = {'H': rgb(0xe4e4ea), 'M': IRON[4], 'S': IRON[3]}
WOOD_ICON = {'H': rgb(0xe0a870), 'M': WOOD[4], 'S': WOOD[3]}
WATER_ICON = {'H': rgb(0xd8f0fa), 'M': rgb(0x62b4e6), 'S': rgb(0x2f76aa)}
ICE_ICON = {'H': rgb(0xffffff), 'M': rgb(0xc8e4f4), 'S': rgb(0x7fb0cc)}
GREEN_ICON = {'H': rgb(0xcfeeb0), 'M': rgb(0x8ccc70), 'S': GREEN[1]}
FIRE_ICON = {'H': rgb(0xffe08a), 'M': rgb(0xf49a2c), 'S': rgb(0xd0502a)}
UNLIT_ICON = {'H': rgb(0x8a7a66), 'M': rgb(0x64574a), 'S': rgb(0x4c4238)}


def materials(main: dict, **others: dict) -> dict:
    """A palette: main's tones as H M S, others' as <letter>, <letter upper>..."""
    colors = {'k': INK, **main}
    for key, (light, base, shade) in others.items():
        colors[key[0]], colors[key[1]], colors[key[2]] = light, base, shade
    return colors


def tones(material: dict) -> tuple:
    return material['H'], material['M'], material['S']


ICONS = [
    ('heart', [  # Life
        '............',
        '..kkk..kkk..',
        '.kHHMkkMMSk.',
        '.kHMMMMMMSk.',
        '.kHMMMMMMSk.',
        '.kMMMMMMMSk.',
        '..kMMMMMSk..',
        '...kMMMSk...',
        '....kMSk....',
        '.....kk.....',
        '............',
        '............'], materials(RED_ICON)),
    ('bullet', [  # A round: copper head, brass case
        '............',
        '.....kk.....',
        '....kabk....',
        '...kaabck...',
        '...kaabck...',
        '...kkkkkk...',
        '...kHMMSk...',
        '...kHMMSk...',
        '...kHMMSk...',
        '...kHMSSk...',
        '...kkkkkk...',
        '............'], materials(BRASS_ICON, abc=(rgb(0xf6b48a), rgb(0xd67a4a), rgb(0x9a4f2c)))),
    ('skull', [  # Zombies
        '............',
        '...kkkkkk...',
        '..kHHMMMSk..',
        '.kHMMMMMMSk.',
        '.kHkkMMkkSk.',
        '.kMkkMMkkSk.',
        '.kMMMkkMMSk.',
        '..kMMMMMSk..',
        '..kMkMkSkk..',
        '...kkkkkk...',
        '............',
        '............'], materials(BONE_ICON)),
    ('flag', [  # The road's end
        '............',
        '..kk........',
        '.kabkkkkkkk.',
        '.kabHHMMMSk.',
        '.kabHMMMMSk.',
        '.kabMMMMSSk.',
        '.kabkkkkkkk.',
        '.kabk.......',
        '.kabk.......',
        '.kabk.......',
        '..kkk.......',
        '............'], materials(RED_ICON, abc=tones(WOOD_ICON))),
    ('dynamite', [  # A bundle, its fuse lit
        '........kk..',
        '.......kabk.',
        '......kckk..',
        '..kkkkkkkk..',
        '.kHSkHSkHSk.',
        '.kHSkHSkHSk.',
        '.kddddddddk.',
        '.kHSkHSkHSk.',
        '.kHSkHSkHSk.',
        '.kMSkMSkMSk.',
        '..kkkkkkkk..',
        '............'], materials(RED_ICON, abc=tones(FIRE_ICON), def_=tones(BONE_ICON))),
    ('speaker', [  # A horn, and one wave of sound
        '............',
        '.....kk..k..',
        '....kHk.kSk.',
        '.kkkHMk..kSk',
        '.kHHMMk..kSk',
        '.kHMMMk..kSk',
        '.kMMMMk..kSk',
        '.kkkMSk.kSk.',
        '....kSk..k..',
        '.....kk.....',
        '............',
        '............'], materials(BONE_ICON)),
    ('star', [  # Experience
        '.....kk.....',
        '....kHMk....',
        '.kkkkHMkkkk.',
        '.kHHMMMMMSk.',
        '..kHMMMMSk..',
        '...kMMMMk...',
        '...kMMMSk...',
        '..kMSkkSSk..',
        '..kSk..kSk..',
        '..kk....kk..',
        '............',
        '............'], materials(GREEN_ICON)),
    ('lock', [  # Not yet: iron shackle, brass body
        '............',
        '....kkkk....',
        '...kabbck...',
        '...kbkkck...',
        '...kbkkck...',
        '..kkkkkkkk..',
        '..kHMMMMSk..',
        '..kHMkkMSk..',
        '..kMMkkMSk..',
        '..kMMMMSSk..',
        '..kkkkkkkk..',
        '............'], materials(BRASS_ICON, abc=tones(IRON_ICON))),
    ('check', [  # Done
        '............',
        '.........kk.',
        '........kHMk',
        '.......kHMk.',
        '.kk...kHMk..',
        'kHMk.kHMk...',
        '.kMMkHMk....',
        '..kMMMk.....',
        '...kMSk.....',
        '....kk......',
        '............',
        '............'], materials(GREEN_ICON)),
    ('shell', [  # A shotgun shell: red hull, brass head
        '............',
        '....kkkk....',
        '...kHMMSk...',
        '...kHMMSk...',
        '...kHMMSk...',
        '...kHMMSk...',
        '...kHMSSk...',
        '...kkkkkk...',
        '...kabbck...',
        '...kabcck...',
        '...kkkkkk...',
        '............'], materials(RED_ICON, abc=tones(BRASS_ICON))),
    ('blood', [  # Bleeding: the same drop as water, in red
        '.....kk.....',
        '....kHSk....',
        '....kHSk....',
        '...kHMMSk...',
        '..kHMMMMSk..',
        '..kHMMMMSk..',
        '..kMMMMMSk..',
        '..kMMMMSSk..',
        '...kMMSSk...',
        '....kkkk....',
        '............',
        '............'], materials(RED_ICON)),
    ('slow', [  # A boot held back by an iron ball
        '...kkkkk....',
        '...kHMSk....',
        '...kHMSk....',
        '...kHMSk....',
        '...kHMMkkk..',
        '...kHMMMMSk.',
        '...kMMMMMSk.',
        '.kkkkkkkkkk.',
        'kabck.......',
        'kbcck.......',
        '.kkk........',
        '............'], materials(WOOD_ICON, abc=tones(IRON_ICON))),
    ('gold', [  # A coin: the same disc as the watch
        '............',
        '...kkkkkk...',
        '..kHHHMMSk..',
        '.kHHMkkMMSk.',
        '.kHMMkMMMSk.',
        '.kHMMkMMMSk.',
        '.kMMMkMMMSk.',
        '.kMMkkkMSSk.',
        '..kMMMMSSk..',
        '...kkkkkk...',
        '............',
        '............'], materials(BRASS_ICON)),
    ('wind', [  # Gusts: two curling bands
        '......kkk...',
        '.....kHMSk..',
        '.....kkkSk..',
        'kkkkkkkkSk..',
        'kHHHHHMMSk..',
        'kkkkkkkkkkk.',
        '.kHHHHHHMMSk',
        '.kkkkkkkkkSk',
        '.....kkkkkSk',
        '.....kHMMSSk',
        '.....kkkkkk.',
        '............'], materials(IRON_ICON)),
    ('current', [  # Waves: two bands of water
        '............',
        '..kk....kk..',
        '.kHHk..kHHk.',
        'kHMMSkkHMMSk',
        'kSkkMMMMkkSk',
        '.k..kkkk..k.',
        '..kk....kk..',
        '.kHHk..kHHk.',
        'kHMMSkkHMMSk',
        'kSkkMMMMkkSk',
        '.k..kkkk..k.',
        '............'], materials(WATER_ICON)),
    ('heat', [  # A blazing sun
        '.....kk.....',
        '....kHSk....',
        '...kkkkkk...',
        '..kHHMMMSk..',
        '.kkHMMMMSkk.',
        'kHkHMMMMSkSk',
        'kSkMMMMSSkSk',
        '.kkMMMMSSkk.',
        '..kMMSSSSk..',
        '...kkkkkk...',
        '....kHSk....',
        '.....kk.....'], materials(FIRE_ICON)),
    ('omen', [  # A crow's eye
        '............',
        '............',
        '...kkkkkk...',
        '..kHHMMMSk..',
        '.kHMkaakMSk.',
        '.kHMkabkMSk.',
        '.kMMkkkkMSk.',
        '..kMMMMSSk..',
        '...kkkkkk...',
        '............',
        '............',
        '............'], materials(BONE_ICON, abc=tones(RED_ICON))),
    ('cold', [  # A snowflake
        '.....kk.....',
        '..k.kHMk.k..',
        '.kHkkHMkkMk.',
        '..kHkHMkMk..',
        '.kkkHHMMkkk.',
        'kHHHHMMMMMSk',
        'kMMMMMMSSSSk',
        '.kkkHMSSkkk.',
        '..kHkMSkSk..',
        '.kMkkMSkkSk.',
        '..k.kMSk.k..',
        '.....kk.....'], materials(ICE_ICON)),
    ('wet', [  # Drops: the same drop, twice
        '............',
        '...kk.......',
        '..kHSk......',
        '.kHMMSk.....',
        '.kHMMSk.kk..',
        '.kHMMSkkHSk.',
        '.kMMSSkHMMSk',
        '..kkkkkHMMSk',
        '......kMMSSk',
        '.......kkkk.',
        '............',
        '............'], materials(WATER_ICON)),
    ('cozy', [  # A campfire over two logs
        '.....kk.....',
        '....kHSk....',
        '...kHMSk.k..',
        '..kkHMMSkSk.',
        '..kHHMMMMSk.',
        '.kHHMMMMMSk.',
        '.kHMMMMMMSk.',
        '..kkMMMSkk..',
        '.kkabkkabkk.',
        'kabbbkkbbbck',
        '.kkkkkkkkkk.',
        '............'], materials(FIRE_ICON, abc=tones(WOOD_ICON))),
    ('water', [  # A canteen: wooden stopper, water behind glass
        '....kkkk....',
        '....kabk....',
        '...kkkkkk...',
        '..kHHMMSSk..',
        '.kHHMMMMSSk.',
        '.kHMMMMMMSk.',
        '.kHMMMMMMSk.',
        '.kMMMMMMSSk.',
        '..kMMMMSSk..',
        '...kkkkkk...',
        '............',
        '............'], materials(WATER_ICON, abc=tones(WOOD_ICON))),
    ('fresh', [  # Refreshed: the drop, and a sparkle
        '........kk..',
        '....kk.kaak.',
        '...kHSkkaak.',
        '...kHSk.kk..',
        '..kHMMSk....',
        '.kHMMMMSk...',
        '.kHMMMMSk...',
        '.kMMMMMSk...',
        '.kMMMMSSk...',
        '..kMMSSk....',
        '...kkkk.....',
        '............'], materials(WATER_ICON, abc=tones(ICE_ICON))),
    ('save', [  # A disk: brass case, iron shutter, paper label
        '............',
        '.kkkkkkkkkk.',
        '.kHHabbckMk.',
        '.kHMabkckMk.',
        '.kHMabbckMk.',
        '.kHMkkkkMSk.',
        '.kMkdddekSk.',
        '.kMkddeekSk.',
        '.kMkdeeekSk.',
        '.kkkkkkkkkk.',
        '............',
        '............'], materials(BRASS_ICON, abc=tones(IRON_ICON), def_=tones(BONE_ICON))),
    ('clock', [  # A pocket watch: the same disc as the coin
        '.....kk.....',
        '...kkkkkk...',
        '..kHHabbSk..',
        '.kHaabkbbSk.',
        '.kHabbkbbSk.',
        '.kHabbkkkSk.',
        '.kMabbbbbSk.',
        '.kMbbbbbcSk.',
        '..kMbbbcSk..',
        '...kkkkkk...',
        '............',
        '............'], materials(BRASS_ICON, abc=tones(BONE_ICON))),
    ('mission_star', [  # A star earned
        '.....kk.....',
        '....kHMk....',
        '.kkkkHMkkkk.',
        '.kHHMMMMMSk.',
        '..kHMMMMSk..',
        '...kMMMMk...',
        '...kMMMSk...',
        '..kMSkkSSk..',
        '..kSk..kSk..',
        '..kk....kk..',
        '............',
        '............'], materials(BRASS_ICON)),
    ('mission_star_empty', [  # A star still to earn: the same star, unlit
        '.....kk.....',
        '....kHMk....',
        '.kkkkHMkkkk.',
        '.kHHMMMMMSk.',
        '..kHMMMMSk..',
        '...kMMMMk...',
        '...kMMMSk...',
        '..kMSkkSSk..',
        '..kSk..kSk..',
        '..kk....kk..',
        '............',
        '............'], materials(UNLIT_ICON)),
    ('arrow_left', [  # An ambush coming, out of sight
        '............',
        '.....kk.....',
        '....kHk.....',
        '...kHMkkkkk.',
        '..kHMMMMMMk.',
        '.kHMMMMMMSk.',
        '..kMMMMMSSk.',
        '...kMSkkkkk.',
        '....kSk.....',
        '.....kk.....',
        '............',
        '............'], materials(RED_ICON)),
    ('arrow_right', [
        '............',
        '.....kk.....',
        '.....kMk....',
        '.kkkkkHMk...',
        '.kHHHHMMMk..',
        '.kHMMMMMMSk.',
        '.kMMMMMMSk..',
        '.kkkkkMSk...',
        '.....kSk....',
        '.....kk.....',
        '............',
        '............'], materials(RED_ICON)),
    ('construction', [  # In development: a striped barrier with its red lamp
        '............',
        '.....kk.....',
        '....kHSk....',
        '.kkkkkkkkkk.',
        '.kMMMkMMMkk.',
        '.kMMkMMMkMk.',
        '.kMkMMMkMMk.',
        '.kkkkkkkkkk.',
        '..kbk..kbk..',
        '..kbk..kbk..',
        '.kkkk..kkkk.',
        '............'], materials({'H': KIT.RED[1], 'M': KIT.FIRE[1], 'S': KIT.RED[3]},
                                   abc=tones(IRON_ICON))),
]


def check_icon(name: str, rows: list[str]) -> None:
    """Refuse an icon that breaks the shared rules, rather than ship it."""
    if len(rows) != 12 or any(len(row) != 12 for row in rows):
        raise ValueError(f'icon {name}: not 12 x 12')
    drawn = {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c != '.'}
    xs, ys = [x for x, _ in drawn], [y for _, y in drawn]
    if abs(min(xs) - (11 - max(xs))) > 1 or abs(min(ys) - (11 - max(ys))) > 2:
        raise ValueError(f'icon {name}: not centered in its cell')
    for x, y in drawn:
        if rows[y][x] == 'k':
            continue
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if (nx, ny) not in drawn:
                raise ValueError(f'icon {name}: outline open at {x},{y}')


def make_icons() -> Image:
    img = Image(12 * len(ICONS), 12)
    for frame, (name, rows, colors) in enumerate(ICONS):
        check_icon(name, rows)
        icon(img, frame, rows, colors)
    return img


def make_icons_hd() -> Image:
    icons = draw_icons_hd()
    img = Image(ICON_HD_SIZE * len(icons), ICON_HD_SIZE)
    for frame, pixels in enumerate(icons):
        for (x, y), color in pixels.items():
            img.set(frame * ICON_HD_SIZE + x, y, color)
    return img


def pistol_pixels() -> dict:
    """Her hand cannon exactly as in play (one drawing for both hands)."""
    w, h, px = decode_png_rgba(ROOT / 'assets/sprites/characters/cowgirl/weapons/pistol.png')
    return {(x, y): tuple(px[(y * w + x) * 4:(y * w + x) * 4 + 4])
            for y in range(h) for x in range(w) if px[(y * w + x) * 4 + 3]}


def swat_pixels(gun: dict) -> dict:
    """A SWAT gun template (tools/make_swat.py) in its metal colors, outlined
    like on his shoot sheets: flashlight, and on the rifle the bayonet, included."""
    xs, ys = [x for x, _ in gun], [y for _, y in gun]
    inked = {(x - min(xs) + 1, y - min(ys) + 1): SWAT_METAL[key] for (x, y), key in gun.items()}
    out = dict(inked)
    for x, y in inked:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in inked:
                out[(x + dx, y + dy)] = SWAT_INK
    return out


def grenade_pixels() -> dict:
    """The SWAT's hand grenade (weapons/grenade.png frame 0), twice as big."""
    w, h, px = decode_png_rgba(ROOT / 'assets/sprites/weapons/grenade.png')
    out = {}
    for y in range(8):
        for x in range(8):
            i = (y * w + x) * 4
            if px[i + 3]:
                for dx in range(2):
                    for dy in range(2):
                        out[(2 * x + dx, 2 * y + dy)] = tuple(px[i:i + 4])
    return out


def gun_sheet(guns: list, w: int, h: int) -> Image:
    """Centered in w x h frames."""
    img = Image(w * len(guns), h)
    for f, pixels in enumerate(guns):
        xs, ys = [x for x, _ in pixels], [y for _, y in pixels]
        ox, oy = (w - 1 - max(xs) - min(xs)) // 2, (h - 1 - max(ys) - min(ys)) // 2
        for (x, y), c in pixels.items():
            if 0 <= x + ox < w and 0 <= y + oy < h:  # The rifle's outline is wider than its frame
                img.set(f * w + x + ox, y + oy, c)
    return img


def make_weapons() -> Image:
    """The guns as sprites in play, in WeaponId order and then the grenade.
    Run tools/make_powers.py first."""
    pistol = pistol_pixels()
    return gun_sheet([pistol, swat_pixels(swat_rifle()[0]), swat_pixels(swat_shotgun()[0]),
                      KIT.tinted(pistol, KIT.HERO_TINT), KIT.paired(pistol, 3, 3), grenade_pixels()], 36, 14)


def make_weapons_hd() -> Image:
    return gun_sheet(KIT.draw_guns(), KIT.GUN_W, KIT.GUN_H)


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'assets'
    out = {
        'font': make_font(), 'panel': make_panel(), 'button': make_button(), 'key': make_key(),
        'pip': make_pip(), 'bar': make_bar(), 'icons': make_icons(), 'icons_hd': make_icons_hd(),
        'weapons': make_weapons(), 'weapons_hd': make_weapons_hd(), 'notice_dev': make_notice_dev(),
    }
    for name, img in out.items():
        path = assets / 'sprites' / 'ui' / f'{name}.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        print(f'make_ui: sprites/ui/{name}.png ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
