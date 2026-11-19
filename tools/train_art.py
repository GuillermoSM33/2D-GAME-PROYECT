"""The laboratory train of 2-3: its cars from outside, from inside and the
prototype's pieces. Standard library only and deterministic.

  sprites/terrain/train.png              5432 x 192: thirteen Vantrell boxcars,
                                         the cabless booster (machinery) and the
                                         control locomotive, every unit drawn at
                                         its final pixel size (nothing resampled).
  sprites/terrain/train_interior.png     15 x 360 x 270: the fifteen rooms from
                                         inside. Enamel, steel and rubber lit by
                                         their own tubes (light from the upper
                                         left, falloff and dithered bands),
                                         gangways that join the tiles and the
                                         interaction spots drawn where the game
                                         places them (src/game/train.c).
  sprites/terrain/experimental_parts.png 8 x 32 x 32: one silhouette per piece,
                                         brass and steel around a lit core.
  sprites/terrain/train_gear.png         2 x 32 x 80: a hazmat suit hanging
                                         from its hook and the tablet, which the
                                         game draws in car 01 while they are there.

Interaction spots in a room's own pixels (TRAIN_ROOM_W = 360): car 01's side
door at x 40, its suits' hooks either side of x 218 and the tablet's locker
at x 311; the parts' cradles at x 259 of cars 02, 07 and the machinery; the
terminal (and its tablet dock) at x 234 and the exit hatch at x 320 of the
control room. The furniture is in tools/train_furnishing.py.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_sprites import Image  # noqa: E402
from terrain_vehicle_detail import Draw, pane, pressed_panel, shade as tshade  # noqa: E402
from landscape_kit import Canvas, hx, mix, shade, fbm, hash2, dither  # noqa: E402
from scenery_materials import lettering  # noqa: E402
import train_furnishing as tf  # noqa: E402

CARS, ROOM_W, INTERIOR_H = 13, 360, 270
ROOMS = 15
WIDTH, HEIGHT = ROOM_W * ROOMS + 32, 192
PART = 32
FLOOR = 240                      # The feet's row, as everywhere in the game
ENTRY_X, TERMINAL_X, EXIT_X, CRADLE_X = 40, 234, 320, 259
CRADLE_ROOMS = (1, 6, CARS)       # Prototypes, cryogenics, machinery
SUIT_X, SUIT_HOOK, SUIT_BOTTOM = 218, 13, 236
TABLET_X, TABLET_BOTTOM = 311, 201
LAMPS = (92, 268)                # Every room's two ceiling tubes (x of their centre)
# The game's supply placements are the source of truth for clear floor bays.
_train_header = (Path(__file__).resolve().parents[1] / 'src/game/train.h').read_text(encoding='utf-8')


def _train_macro(name, columns):
    body = _train_header.split(f'#define {name}(X)', 1)[1].split('\n\n', 1)[0]
    rows = [tuple(int(value.strip()) for value in row.split(','))
            for row in re.findall(r'X\(([^)]+)\)', body)]
    if not rows or any(len(row) != columns for row in rows):
        raise ValueError(f'{name}: expected rows of {columns} art coordinates')
    return rows


SUPPLY_BAYS = dict(_train_macro('TRAIN_SUPPLY_BAYS', 2))
VENT_FANS = _train_macro('TRAIN_VENT_FANS', 3)

INK = hx(0x101417)


# ======================================================================
# Outside: the consist on the rails
# ======================================================================

def rail_wheel(d, x, y):
    """A freight wheel about one fifth of the body height, with a steel rim."""
    d.ellipse(x, y, 16, 16, 0x171c20)
    d.ellipse(x, y, 14, 14, 0x737b79)
    d.ellipse(x, y, 11, 11, 0x303b40)
    d.ellipse(x, y, 8, 8, 0x414d50)
    d.ellipse(x - 1, y - 1, 4, 4, 0x9eaa9f)
    d.ellipse(x, y, 2, 2, 0x343e40)
    d.line(x - 6, y + 12, x + 6, y + 12, 0xadb3a2)
    for dx, dy in ((-7, -5), (5, -7), (7, 5), (-5, 7)):
        d.ellipse(x + dx, y + dy, 1, 2, 0x1e282d)


def bogie(d, x, y):
    for wx in (x, x + 36): rail_wheel(d, wx, y + 4)
    d.poly([(x - 14, y - 8), (x + 50, y - 8), (x + 52, y - 2),
            (x + 41, y + 5), (x - 5, y + 5), (x - 16, y - 2)], 0x343e40)
    d.line(x - 11, y - 7, x + 47, y - 7, 0x85908a)
    d.line(x + 8, y + 4, x + 28, y + 4, 0x1b252a)
    for sx in (x + 10, x + 20):
        d.box(sx, y - 6, sx + 6, y + 2, 0x1c272d)
        for sy in range(y - 5, y + 2, 2):
            d.line(sx, sy, sx + 6, sy, 0x7c8580)
    for wx in (x, x + 36):
        d.box(wx - 4, y, wx + 4, y + 7, 0x596665)
        d.line(wx - 4, y, wx + 4, y, 0xa1aaa0)
        d.bolt(wx, y + 4)


def loco_truck(d, x, y):
    """A three-axle locomotive truck: side frame, springs and journal boxes."""
    for k in range(3): rail_wheel(d, x + k * 34, y + 4)
    d.poly([(x - 14, y - 9), (x + 82, y - 9), (x + 85, y - 3), (x + 74, y + 4),
            (x - 6, y + 4), (x - 17, y - 3)], 0x2f383a)
    d.line(x - 12, y - 8, x + 80, y - 8, 0x8a948c)
    d.line(x - 5, y + 3, x + 73, y + 3, 0x1a2124)
    for sx in (x + 12, x + 46):
        d.box(sx, y - 6, sx + 9, y + 1, 0x1a2326)
        for sy in range(y - 5, y + 1, 2): d.line(sx, sy, sx + 9, sy, 0x77817c)
    for k in range(3):
        wx = x + k * 34
        d.box(wx - 4, y, wx + 4, y + 7, 0x56625f)
        d.line(wx - 4, y, wx + 4, y, 0x9aa497)
        d.bolt(wx, y + 4)


def coupling(d, x, y):
    d.box(x - 8, y - 2, x + 8, y + 2, 0x292f30)
    d.line(x - 7, y - 2, x + 6, y - 2, 0x8b8b7e)
    d.box(x - 2, y - 4, x + 3, y + 3, 0x59615c)
    d.line(x - 5, y + 4, x - 2, y + 10, 0x242c30)
    d.line(x - 2, y + 10, x + 4, y + 9, 0x5f6965)


def roof_vent(d, x, y, paint):
    """A louvred vent high on the side: the lab breathes through them."""
    d.box(x - 1, y - 1, x + 15, y + 8, 0x1d2629)
    d.box(x, y, x + 14, y + 7, tshade(paint, .55))
    for yy in range(y + 1, y + 7, 2):
        d.line(x + 1, yy, x + 13, yy, tshade(paint, 1.3))
        d.line(x + 1, yy + 1, x + 13, yy + 1, 0x1f282b)


def boxcar(d, start, end, index):
    top, bottom = 19 + index % 2 * 3, 164
    # The body occludes the upper rims; all wheels meet the same rail row.
    for x in (start + 39, end - 75): bogie(d, x, 169)
    paint = (0x697e79, 0x667a77, 0x697c7d, 0x6b7571, 0x747c72, 0x76766b, 0x687b82, 0x74756a,
             0x6e7a70, 0x6a7879, 0x72776c, 0x66756f, 0x6d7a7e)[index]
    d.box(start + 2, top + 2, end - 2, bottom, tshade(paint, .8))
    d.poly([(start + 1, top + 2), (start + 9, top - 3), (end - 8, top - 3),
            (end - 1, top + 2)], tshade(paint, 1.24))
    d.line(start + 3, top + 3, end - 3, top + 3, tshade(paint, 1.5))
    for x in range(start + 5, end - 2, 12):
        pressed_panel(d, x, top + 5, min(x + 10, end - 3), bottom - 3, paint)
        d.line(x, top + 5, x, bottom - 4, tshade(paint, 1.25))
        for y in range(top + 8, bottom - 4, 13): d.bolt(x + 1, y, tshade(paint, 1.5))
        # Rain streaks collect below ribs and at the lower body seam.
        d.line(x + 4, bottom - 10 - (x % 7), x + 4, bottom - 4, tshade(paint, .6))
    mid = (start + end) // 2
    d.box(mid - 27, top + 14, mid + 27, bottom - 4, tshade(paint, .6))
    d.box(mid - 24, top + 16, mid + 24, bottom - 7, tshade(paint, .94))
    for x in range(mid - 23, mid + 24, 8):
        d.line(x, top + 18, x, bottom - 9, tshade(paint, .5))
        d.line(x + 1, top + 18, x + 1, bottom - 9, tshade(paint, 1.3))
    for y in (top + 12, bottom - 5):
        d.line(mid - 31, y, mid + 31, y, 0x9a9b88)
        d.line(mid - 31, y + 1, mid + 31, y + 1, 0x222b2f)
    d.line(mid + 18, top + 37, mid + 18, top + 48, 0x252e30)
    d.line(mid + 19, top + 37, mid + 19, top + 48, 0xc2b99c)
    d.line(mid + 15, top + 43, mid + 21, top + 43, 0x7d8376)
    d.line(start + 3, bottom + 1, end - 3, bottom + 1, 0x1b262b)
    d.line(start + 5, bottom + 2, end - 5, bottom + 2, 0x7c8376)
    for vx in (start + 70, end - 92): roof_vent(d, vx, top + 7, paint)
    d.box(start + 5, top + 34, start + 32, top + 44, 0x303b3a)
    d.text('TM ' + str(20 + index), start + 8, top + 37, 0xc1bba4)
    d.text('%02d' % (index + 1), end - 28, bottom - 15, 0xbeb49a)
    # End ladder, grab irons, hazard diamond and inspection labels.
    for x in (end - 15, end - 7): d.line(x, top + 6, x, bottom + 4, 0x98a092)
    for y in range(top + 8, bottom + 3, 8): d.line(end - 15, y, end - 7, y, 0x626e69)
    d.poly([(start + 20, bottom - 25), (start + 25, bottom - 20),
            (start + 20, bottom - 15), (start + 15, bottom - 20)], 0xc3ae6a)
    d.line(start + 17, bottom - 20, start + 23, bottom - 20, 0x554939)
    for y in (bottom - 10, bottom - 7): d.line(start + 8, y, start + 25, y, 0xa9a38c)
    d.line(start + 4, top + 31, end - 4, top + 31, 0x94b1ac)
    d.line(start + 4, top + 34, end - 4, top + 34, 0x263c40)
    d.text('VANTRELL / LAB 4-G', start + 35, top + 19, 0xd0c9b0)
    d.text('%02d' % (index + 1), start + 19, top + 6, 0xd3cbb1)
    if index == 0:
        # The side door she boards through, ajar, with its step below.
        d.box(start + 33, bottom - 64, start + 64, bottom - 1, 0x23373d)
        d.line(start + 34, bottom - 63, start + 63, bottom - 63, 0x8ab7b0)
        pane(d, [(start + 39, bottom - 58), (start + 58, bottom - 58), (start + 58, bottom - 40), (start + 39, bottom - 40)])
        for y in (bottom + 1, bottom + 7, bottom + 13): d.line(start + 31, y, start + 68, y, 0x9ca598)


OLIVE = 0x6d6c43


def hood(d, x0, x1, top, paint):
    """A locomotive's long hood: access doors, louvres, a radiator and a roof."""
    d.box(x0, top, x1, 155, tshade(paint, .72))
    d.poly([(x0, top + 1), (x0 + 5, top - 4), (x1 - 5, top - 4), (x1, top + 1)], tshade(paint, 1.18))
    d.line(x0 + 4, top - 4, x1 - 4, top - 4, tshade(paint, 1.45))
    d.line(x0 + 1, top + 1, x1 - 1, top + 1, tshade(paint, 1.3))
    for x in range(x0 + 4, x1 - 24, 27):
        pressed_panel(d, x, top + 4, x + 24, 146, paint)
        d.line(x, top + 4, x, 146, tshade(paint, 1.22))
        # Louvres on every other door, latch and hinges on all of them.
        if (x - x0) // 27 % 2 == 0:
            d.box(x + 4, top + 9, x + 20, top + 30, 0x262f2a)
            for y in range(top + 10, top + 30, 3):
                d.line(x + 5, y, x + 19, y, tshade(paint, 1.25))
                d.line(x + 5, y + 1, x + 19, y + 1, 0x343f37)
        d.box(x + 17, top + 52, x + 20, top + 54, 0xb7b49a)
        for y in (top + 12, 140): d.bolt(x + 2, y)
    # Radiator grille and its fans, at the rear of the hood.
    rx = x1 - 22
    d.box(rx - 2, top + 3, x1 - 3, 146, 0x1e2622)
    for y in range(top + 5, 145, 2): d.line(rx, y, x1 - 5, y, 0x55604f if y % 4 else 0x7f8a74)
    d.line(rx - 2, top + 3, x1 - 3, top + 3, tshade(paint, 1.4))
    # Safety stripe, weathered along the lower edge, and grime under it.
    for y in (147, 148, 149):
        for x in range(x0 + 1, x1):
            d.p(x, y, 0xb59a49 if (x // 9 + y) % 7 else 0x8d7a44)
    for x in range(x0 + 2, x1 - 1, 5):
        d.line(x, 150, x, 150 + (x * 7) % 4, tshade(paint, .5))


def roof_gear(d, x0, x1, top, fans):
    for fx in fans:
        d.ellipse(fx, top - 5, 13, 4, 0x2b332f)
        d.line(fx - 11, top - 8, fx + 11, top - 8, 0x9ea38a)
        for dx in range(-9, 10, 3): d.line(fx + dx, top - 8, fx + dx, top - 3, 0x4a5547)
    sx = x0 + 52
    d.box(sx, top - 16, sx + 9, top - 4, 0x3a4340)
    d.line(sx, top - 16, sx + 9, top - 16, 0x99a08b)
    d.box(sx + 1, top - 15, sx + 8, top - 14, 0x1b2122)
    d.box(sx + 3, top - 22, sx + 6, top - 17, 0x2a3032)  # Exhaust stack


def underframe(d, x0, x1, front=None):
    """Deck, handrail, fuel tank, trucks and the pilots at both ends."""
    for tx in (x0 + 24, x1 - 92): loco_truck(d, tx, 169)
    d.box(x0 - 3, 156, x1 + 3, 163, 0x2a3236)
    d.line(x0 - 3, 156, x1 + 3, 156, 0x8d968c)
    d.line(x0 - 3, 163, x1 + 3, 163, 0x161c1f)
    for x in range(x0, x1, 12): d.bolt(x + 4, 160)
    for x in range(x0 + 3, x1, 26):
        d.line(x, 131, x, 155, 0x9da38f)
        d.p(x, 131, 0xc7c5ac)
    d.line(x0 + 3, 131, x1 - 3, 131, 0xb9b49a)
    d.line(x0 + 3, 132, x1 - 3, 132, 0x4b524b)
    mid = (x0 + x1) // 2
    d.box(mid - 52, 165, mid + 52, 179, 0x283033)
    d.ellipse(mid - 52, 172, 4, 7, 0x3a4446)
    d.ellipse(mid + 52, 172, 4, 7, 0x1d2427)
    d.line(mid - 50, 166, mid + 50, 166, 0x6f7a76)
    d.line(mid - 50, 178, mid + 50, 178, 0x141a1c)
    d.box(mid + 30, 168, mid + 38, 174, 0x3d4748)
    d.ellipse(mid + 34, 171, 2, 2, 0xa9ad97)
    d.text('DIESEL', mid - 20, 169, 0x8f9583)
    ends = [(x0, -1), (x1, 1)]
    for ex, side in ends:
        if front == side: continue
        d.poly([(ex, 164), (ex + side * 7, 164), (ex + side * 7, 172), (ex, 176)], 0x2f383b)
        for y in (166, 170): d.line(ex, y, ex + side * 6, y, 0x8d958a)
        coupling(d, ex + side * 9, 168)


def booster(d, start, end):
    """Index 8, the machinery: a cabless unit, its hood the full length."""
    top = 52
    hood(d, start + 4, end - 4, top, OLIVE)
    roof_gear(d, start + 4, end - 4, top, (start + 120, start + 180, start + 240))
    underframe(d, start + 6, end - 6)
    d.box(start + 34, 104, start + 92, 116, 0x2d3631)
    d.text('MAQUINAS', start + 37, 108, 0xd0c9a2)
    d.text('TM 08', end - 70, 108, 0xd0c9a2)


def locomotive(d, start, end):
    """Index 9, the control cab: long hood behind, cab, short nose to the right."""
    top = 58
    cab0, cab1 = start + 206, start + 282
    nose1 = end + 8
    hood(d, start + 4, cab0, top, OLIVE)
    roof_gear(d, start + 4, cab0, top, (start + 70, start + 130))
    # The cab: taller, two side windows, a door with its own pane.
    d.box(cab0, 22, cab1, 155, tshade(OLIVE, .9))
    d.poly([(cab0 - 6, 23), (cab0 - 1, 16), (cab1 + 3, 16), (cab1 + 8, 23)], 0xa59f72)
    d.line(cab0 - 4, 17, cab1 + 4, 17, 0xc8c39a)
    d.line(cab0 - 6, 23, cab1 + 8, 23, 0x3d3f2c)
    d.line(cab0, 24, cab0, 155, tshade(OLIVE, 1.25))
    d.line(cab1, 24, cab1, 155, tshade(OLIVE, .55))
    pane(d, [(cab0 + 6, 30), (cab0 + 31, 30), (cab0 + 31, 54), (cab0 + 6, 54)])
    pane(d, [(cab0 + 38, 30), (cab1 - 7, 30), (cab1 - 4, 54), (cab0 + 38, 54)])
    d.line(cab0 + 34, 28, cab0 + 34, 56, 0xb8b79c)
    pressed_panel(d, cab0 + 8, 62, cab0 + 30, 146, 0x6c6e4e)
    pane(d, [(cab0 + 12, 67), (cab0 + 26, 67), (cab0 + 26, 82), (cab0 + 12, 82)], seat=False)
    d.box(cab0 + 25, 104, cab0 + 28, 106, 0xc0bfa4)
    for y in range(146, 163, 5): d.line(cab0 + 10, y, cab0 + 28, y, 0x98a092)  # Steps
    d.box(cab0 + 36, 66, cab1 - 6, 78, 0x2d3631)
    d.text('TM 07', cab0 + 40, 70, 0xd8d1a8)
    d.line(cab0 + 12, 15, cab0 + 12, 6, 0x78867b)  # Antenna
    d.box(cab0 + 30, 12, cab0 + 44, 15, 0x5e675a)  # Horn
    d.line(cab0 + 30, 12, cab0 + 44, 12, 0xa6ab95)
    for y in (88, 120):
        d.line(cab0 + 36, y, cab1 - 6, y, tshade(OLIVE, 1.2))
        d.line(cab0 + 36, y + 1, cab1 - 6, y + 1, tshade(OLIVE, .6))
    # Short nose, sloping down to the headlight and the number board.
    d.poly([(cab1, 70), (nose1 - 8, 76), (nose1, 86), (nose1, 155), (cab1, 155)], tshade(OLIVE, .86))
    d.line(cab1 + 1, 70, nose1 - 8, 76, tshade(OLIVE, 1.4))
    d.line(nose1 - 8, 76, nose1, 86, tshade(OLIVE, 1.2))
    d.line(nose1, 86, nose1, 155, 0x1d2321)
    pressed_panel(d, cab1 + 4, 84, nose1 - 6, 144, OLIVE)
    d.box(nose1 - 6, 90, nose1 - 1, 99, 0x232b29)
    d.ellipse(nose1 - 3, 94, 2, 3, 0xf3e3a8)
    d.p(nose1 - 4, 92, 0xffffff)
    d.box(cab1 + 8, 104, cab1 + 24, 112, 0x26322f)
    d.text('07', cab1 + 11, 106, 0xd8d1a8)
    for y in (147, 148, 149):
        for x in range(cab0, nose1):
            d.p(x, y, 0xb59a49 if (x // 9 + y) % 7 else 0x8d7a44)
    d.line(cab1 + 2, 100, nose1 - 2, 100, 0xb7b49a)  # Nose handrail
    underframe(d, start + 6, nose1 - 2, front=1)
    # Pilot, plough and ditch lights at the front.
    px = nose1 + 1
    d.poly([(px - 6, 164), (px + 4, 164), (px + 9, 186), (px - 14, 186)], 0x2f3a37)
    for k in range(4): d.line(px - 10 + k * 5, 184, px - 4 + k * 5, 168, 0xb59a49)
    d.box(px - 1, 158, px + 3, 162, 0x232b29)
    d.p(px + 2, 160, 0xf3e3a8)
    coupling(d, px + 6, 170)


def make_train():
    image = Image(WIDTH, HEIGHT)
    d = Draw(image, 0, WIDTH)
    for i in range(CARS):
        start = 16 + i * ROOM_W
        boxcar(d, start, start + ROOM_W - 16, i)
        coupling(d, start + ROOM_W - 8, 168)
    start = 16 + CARS * ROOM_W
    booster(d, start, start + ROOM_W - 16)
    coupling(d, start + ROOM_W - 8, 168)
    locomotive(d, start + ROOM_W, start + 2 * ROOM_W - 16)
    for x in range(WIDTH):
        d.p(x, 191, 0x7d8580)
        d.p(x, 190, 0x2a373a)
        if x % 22 < 8: d.p(x, 189, 0x665b48)
    return image


# ======================================================================
# Inside: fifteen rooms, one material system
# ======================================================================

class Room:
    """A room's canvas plus what shines by itself and what lights the rest."""

    def __init__(self, index):
        self.index = index
        self.c = Canvas(ROOM_W, INTERIOR_H)
        self.glow = set()        # Emissive pixels: never darkened by the lighting
        self.lamps = [True, True]
        self.tints = []          # (x, y, radius, rgb, strength): coloured light
        self.ambient = .62

    # -- primitives -------------------------------------------------------
    def px(self, x, y, col):
        self.c.set(x, y, hx(col))
        self.glow.discard((x, y))

    def fill(self, x0, y0, x1, y1, col):
        self.c.fill(x0, y0, x1, y1, hx(col))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.glow.discard((x, y))

    def hl(self, x0, x1, y, col): self.fill(x0, y, x1, y, col)

    def vl(self, x, y0, y1, col): self.fill(x, y0, x, y1, col)

    def line(self, x0, y0, x1, y1, col):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.px(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), col)

    def disc(self, cx, cy, r, col, ry=None):
        ry = r if ry is None else ry
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if ((x - cx) / r) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.px(x, y, col)

    def poly(self, pts, col):
        ys = [p[1] for p in pts]
        for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
            xs = []
            for i, (xa, ya) in enumerate(pts):
                xb, yb = pts[(i + 1) % len(pts)]
                if ya != yb and min(ya, yb) <= y < max(ya, yb):
                    xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for a, b in zip(xs[0::2], xs[1::2]):
                self.hl(int(math.ceil(a - .5)), int(math.floor(b + .5)), y, col)

    def lit(self, x, y, col):
        """A pixel that gives light: a tube, a screen, a lamp, a liquid."""
        self.c.set(x, y, hx(col))
        self.glow.add((x, y))

    def lit_fill(self, x0, y0, x1, y1, col):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.lit(x, y, col)

    def get(self, x, y):
        return self.c.get(x, y)

    def text(self, s, x, y, col, glow=False):
        before = set((xx, yy) for yy in range(y, y + 5) for xx in range(x, x + len(s) * 4))
        lettering(self.c, s, x, y, hx(col))
        for p in before:
            if self.c.get(*p) == hx(col):
                (self.glow.add if glow else self.glow.discard)(p)

    # -- materials ----------------------------------------------------------
    def block(self, x0, y0, x1, y1, base, ink=True):
        """A solid lit from the upper left, with a dark contour. A big one is
        worked metal, not a flat fill: its paint darkens down and away from
        the light, brushed in short streaks, worn to bare metal on its lit
        edges and dirty along its foot, with a double bevel."""
        b = hx(base)
        if ink:
            self.fill(x0, y0, x1, y1, INK)
            x0, y0, x1, y1 = x0 + 1, y0 + 1, x1 - 1, y1 - 1
        if x1 < x0 or y1 < y0: return
        if x1 - x0 < 9 or y1 - y0 < 7:                       # Small: a plain lit solid
            self.fill(x0, y0, x1, y1, b)
            self.hl(x0, x1, y0, shade(b, 1.32))
            self.vl(x0, y0, y1, shade(b, 1.16))
            self.hl(x0 + 1, x1, y1, shade(b, .6))
            self.vl(x1, y0 + 1, y1, shade(b, .7))
            return
        h, w = max(1, y1 - y0), max(1, x1 - x0)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                tone = 1.07 - .19 * (y - y0) / h - .05 * (x - x0) / w
                tone += (hash2(x // 5, y, 31) - .5) * .05     # Brushed in short streaks
                col = shade(b, tone)
                edge = min(x - x0, x1 - x, y - y0, y1 - y)
                n = hash2(x, y, 57)
                if edge <= 2 and n > .84 and (y - y0 <= 2 or x - x0 <= 2):
                    col = mix(col, (178, 184, 174), .45)      # Paint worn off its lit edges
                elif y1 - y <= 3 and n > .8:
                    col = mix(col, (88, 64, 46), .4)          # Grime and rust along its foot
                self.c.set(x, y, col)
                self.glow.discard((x, y))
        self.hl(x0, x1, y0, shade(b, 1.32))
        self.hl(x0 + 1, x1 - 1, y0 + 1, shade(b, 1.13))
        self.vl(x0, y0, y1, shade(b, 1.16))
        self.vl(x0 + 1, y0 + 1, y1 - 1, shade(b, 1.05))
        self.hl(x0 + 1, x1, y1, shade(b, .6))
        self.hl(x0 + 2, x1 - 1, y1 - 1, shade(b, .8))
        self.vl(x1, y0 + 1, y1, shade(b, .7))
        self.vl(x1 - 1, y0 + 2, y1 - 1, shade(b, .86))
        self.px(x0 + 1, y0 + 1, shade(b, 1.45))

    def recess(self, x0, y0, x1, y1, base):
        b = hx(base)
        self.fill(x0, y0, x1, y1, b)
        self.hl(x0, x1, y0, shade(b, .55))
        self.vl(x0, y0, y1, shade(b, .65))
        self.hl(x0, x1, y1, shade(b, 1.25))
        self.vl(x1, y0, y1, shade(b, 1.12))

    def grime(self, x0, y0, x1, y1, seed, amount=.45, col=(52, 47, 40), mixk=.32):
        """Dirt collects low, in small soft clusters, never as uniform noise."""
        for y in range(y0, y1 + 1):
            t = (y - y0) / max(1, y1 - y0)
            for x in range(x0, x1 + 1):
                if (x, y) in self.glow: continue
                n = fbm(x / 5, y / 3, seed, 2)
                if n + t * amount > 1.0:
                    cur = self.get(x, y)
                    if cur: self.c.set(x, y, mix(cur, col, mixk))

    def streaks(self, x0, y0, x1, y1, seed, col=(56, 52, 44), share=.5):
        """Water and oil run down from seams and rivets: thin, fading lines."""
        for sx in range(x0, x1 + 1, 3):
            if hash2(sx, seed, 2) > share: continue
            start = y0 + int(hash2(sx, seed, 3) * (y1 - y0) * .6)
            ln = 5 + int(hash2(sx, seed, 4) * 26)
            for i in range(ln):
                y = start + i
                if y > y1: break
                cur = self.get(sx, y)
                if cur and (sx, y) not in self.glow:
                    self.c.set(sx, y, mix(cur, col, .26 * (1 - i / ln)))

    def scratches(self, x0, y0, x1, y1, seed, count=6):
        for k in range(count):
            h = hash2(k, seed, 11)
            x = x0 + int(hash2(k, seed, 3) * (x1 - x0))
            y = y0 + int(hash2(k, seed, 5) * (y1 - y0))
            ln = 3 + int(h * 7)
            for i in range(ln):
                xx, yy = x + i, y + (i * (1 if h > .5 else -1)) // 3
                cur = self.get(xx, yy)
                if cur and x0 <= xx <= x1: self.c.set(xx, yy, shade(cur, 1.22 if i % 2 else 1.1))

    def rivets(self, x0, x1, y, step, base):
        b = hx(base)
        for x in range(x0, x1 + 1, step):
            self.px(x, y, shade(b, .45))
            self.px(x - 1, y - 1, shade(b, 1.45))

    def hazard(self, x0, y0, x1, y1, slope=1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                k = (x + slope * y) // 4 % 2
                self.px(x, y, 0xb99a3e if k else 0x23211e)
        self.hl(x0, x1, y0, 0xd8bd66)
        self.hl(x0, x1, y1, 0x141312)

    def stain(self, cx, cy, rx, ry, seed, col=(92, 34, 30), mixk=.6):
        """Dried blood: an irregular body and drips running down."""
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d + (fbm(x / 3, y / 3, seed, 2) - .5) * .9 < 1:
                    cur = self.get(x, y)
                    if cur: self.c.set(x, y, mix(cur, col, mixk))
        for k in range(3):
            x = int(cx - rx * .6 + k * rx * .6)
            ln = 3 + int(hash2(k, seed, 9) * ry * 1.4)
            for i in range(ln):
                cur = self.get(x, int(cy + ry * .4) + i)
                if cur: self.c.set(x, int(cy + ry * .4) + i, mix(cur, col, mixk * (1 - i / (ln + 2))))

    def handprint(self, x, y, seed):
        col = (104, 34, 30)
        for dx, dy in ((0, 2), (1, 2), (2, 2), (0, 3), (1, 3), (2, 3), (3, 3), (1, 4), (2, 4)):
            self.px(x + dx, y + dy, mix(self.get(x + dx, y + dy) or col, col, .7))
        for k, (fx, ln) in enumerate(((0, 2), (1, 3), (2, 3), (3, 2), (4, 1))):
            for i in range(ln):
                yy = y + 1 - i + (1 if k in (0, 4) else 0)
                self.px(x + fx - (1 if k == 4 else 0), yy, mix(self.get(x + fx, yy) or col, col, .65))
        for i in range(3 + seed % 4):
            self.px(x + 1, y + 5 + i, mix(self.get(x + 1, y + 5 + i) or col, col, .5))

    def paper(self, x, y, w=5, h=3, tilt=0):
        for yy in range(h):
            for xx in range(w):
                self.px(x + xx, y + yy + (xx * tilt) // w, 0xc9c3ad if (xx + yy) % 5 else 0xa49f8c)
        self.hl(x + 1, x + w - 2, y + 1 + tilt // 2, 0x8b8678)

    def glass_shards(self, x0, x1, seed):
        for k in range(10):
            x = x0 + int(hash2(k, seed, 2) * (x1 - x0))
            self.px(x, FLOOR - 1, 0xb9d3cc if k % 2 else 0x6f9496)
            if k % 3 == 0: self.px(x + 1, FLOOR - 2, 0xdfeee6)

    def screen(self, x0, y0, x1, y1, ink=(127, 208, 138), seed=0, kind='lines', mount=True):
        """A monitor: a deep housing with a bevelled bezel, its maker's strip and
        power lamp; dark lit glass with scanlines and darker corners where the
        tube curves; on it text under a header, a trace on its grid, a flatline
        or bars on an axis; the ceiling's tube reflected across its top left;
        and the bracket it hangs from."""
        ink = hx(ink)
        self.block(x0 - 4, y0 - 4, x1 + 4, y1 + 6, 0x3a4446)
        self.recess(x0 - 2, y0 - 2, x1 + 2, y1 + 2, 0x20272a)
        self.hl(x0, x0 + 6, y1 + 4, 0x7d8784)
        self.lit(x1 + 1, y1 + 4, 0x7fe39a)
        bg = mix(ink, (10, 18, 18), .87)
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                k = .72 if min(xx - x0, x1 - xx) + min(yy - y0, y1 - yy) < 3 else 1.0
                if (yy - y0) % 2: k *= .86
                self.lit(xx, yy, shade(bg, k))
        dim, bright = mix(ink, bg, .55), mix(ink, (255, 255, 255), .25)
        if kind == 'lines':
            for xx in range(x0 + 1, x1):
                self.lit(xx, y0 + 1, dim)
            self.lit(x0 + 2, y0 + 1, bright)
            last = (x0 + 2, y0 + 4)
            for k, yy in enumerate(range(y0 + 4, y1 - 1, 3)):
                w = int((x1 - x0 - 4) * (.3 + .6 * hash2(k, seed, 1)))
                for xx in range(x0 + 2, x0 + 2 + w):
                    if hash2(xx, yy, seed) > .2 and (xx - x0) % 5 != 4: self.lit(xx, yy, mix(ink, bg, .2))
                last = (x0 + 3 + w, yy)
            self.lit_fill(last[0], last[1] - 1, last[0] + 1, last[1], bright)    # The cursor
        elif kind == 'trace':
            for yy in range(y0 + 2, y1, 4):
                for xx in range(x0 + 2, x1, 4): self.lit(xx, yy, shade(bg, 1.6))
            mid = (y0 + y1) // 2
            prev = None
            for xx in range(x0 + 1, x1):
                yy = mid + int(round(math.sin(xx * .7 + seed) * 2)) if (xx // 7) % 3 else mid - 4 + (xx % 7 > 3) * 6
                yy = max(y0 + 1, min(y1 - 1, yy))
                if prev is not None:
                    for y_ in range(min(prev, yy), max(prev, yy) + 1): self.lit(xx, y_, ink)
                self.lit(xx, yy, bright)
                if yy + 1 < y1: self.lit(xx, yy + 1, mix(ink, bg, .6))
                prev = yy
        elif kind == 'flat':
            mid = (y0 + y1) // 2 + 2
            for xx in range(x0 + 1, x1): self.lit(xx, mid, ink)
            for xx in range(x0 + 1, x1): self.lit(xx, mid + 1, mix(ink, bg, .6))
            self.lit_fill(x1 - 9, y0 + 2, x1 - 7, y0 + 2, bright)
            self.lit_fill(x1 - 5, y0 + 2, x1 - 3, y0 + 2, bright)
        elif kind == 'bars':
            for xx in range(x0 + 1, x1): self.lit(xx, y1 - 1, dim)
            for k, xx in enumerate(range(x0 + 2, x1 - 1, 4)):
                hgt = 2 + int((y1 - y0 - 5) * hash2(k, seed, 7))
                for yy in range(y1 - 1 - hgt, y1 - 1):
                    col = bright if yy == y1 - 1 - hgt else ink
                    self.lit(xx, yy, col); self.lit(xx + 1, yy, mix(col, bg, .25))
        for k in range(min(x1 - x0, y1 - y0) // 2):              # The tube reflected on the glass
            xx, yy = x0 + 3 + k * 2, y0 + 1 + k
            if xx > x1 - 4 or yy > y1 - 2: break
            for d, a in ((-1, .08), (0, .16), (1, .16), (2, .08)):
                cur = self.get(xx + d, yy)
                if cur and x0 <= xx + d <= x1: self.lit(xx + d, yy, mix(cur, (230, 246, 240), a))
        self.hl(x0 - 3, x1 + 3, y1 + 5, 0x1a2023)
        if mount:
            mx = (x0 + x1) // 2
            self.block(mx - 3, y1 + 7, mx + 3, y1 + 9, 0x2a3132)
        self.tints.append(((x0 + x1) // 2, (y0 + y1) // 2, max(x1 - x0, 18) + 10, ink, .16))

    def led(self, x, y, col):
        self.lit(x, y, col)

    def contact_shadow(self, x0, x1, depth=3):
        for k in range(depth):
            for x in range(x0 - k, x1 + k + 1):
                cur = self.get(x, FLOOR - 1 - k)
                if cur and (x, FLOOR - 1 - k) not in self.glow:
                    self.c.set(x, FLOOR - 1 - k, shade(cur, .62 + k * .1))


# -- the shell every room shares -------------------------------------------

WALL = hx(0x7f8c84)
WAINSCOT = hx(0x5b6865)
STEEL = hx(0x6e7a78)
CEILING = hx(0x1a2227)


def shell(r):
    c = r
    i = r.index
    # Ceiling: deck, ribs, a duct and a cable tray.
    c.fill(0, 0, 359, 44, CEILING)
    for x in range(8, 360, 40):
        c.fill(x, 0, x + 5, 27, 0x232d32)
        c.vl(x, 0, 27, 0x313d42)
    for y, col in ((28, 0x6f7c7b), (29, 0x56615f), (30, 0x4a5655), (31, 0x46514f), (32, 0x3c4645),
                   (33, 0x343d3c), (34, 0x2d3534), (35, 0x262e2e), (36, 0x1d2324)):
        c.hl(0, 359, y, col)
    for x in range(30, 360, 60):
        c.fill(x, 27, x + 2, 37, 0x5b6766)
        c.vl(x, 27, 37, 0x8b9695)
        c.vl(x + 3, 28, 36, 0x161b1c)
    c.fill(0, 38, 359, 43, 0x252e31)
    c.hl(0, 359, 38, 0x4d5958)
    for k, (x0, x1, col) in enumerate(((14, 70, 0x1b1d1f), (120, 210, 0x6b2b24), (230, 330, 0x1b1d1f))):
        sag = 2 + (k + i) % 3
        for x in range(x0, x1 + 1):
            t = (x - x0) / (x1 - x0)
            c.px(x, 43 + round(sag * 4 * t * (1 - t)), col)
    # Ceiling tubes; a dead one where the room says so.
    for k, lx in enumerate(LAMPS):
        on = r.lamps[k]
        c.block(lx - 30, 44, lx + 30, 49, 0x353f42)
        for x in range(lx - 27, lx + 28):
            if on:
                c.lit(x, 48, 0xeef7ee)
                c.lit(x, 49, 0xc9e5da if x % 6 else 0xb5d4ca)
            else:
                c.px(x, 48, 0x6c7875)
                c.px(x, 49, 0x4f5a58)
        if not on:
            c.px(lx - 4, 50, 0x8a958f); c.px(lx + 9, 51, 0x6c7875)
    # Cornice and upper trim.
    c.fill(0, 50, 359, 57, 0x37413f)
    c.hl(0, 359, 50, 0x55605d)
    c.hl(0, 359, 57, 0x1e2526)
    c.rivets(4, 356, 54, 12, 0x37413f)
    # Enamel panels, the dado rail, the steel wainscot and its kick plate.
    for x0 in range(16, 344, 48):
        x1 = min(x0 + 47, 343)
        for y0, y1 in ((58, 103), (104, 149)):
            base = shade(WALL, .96 + .08 * hash2(x0, y0, i))  # No two panels alike
            c.fill(x0, y0, x1, y1, base)
            c.hl(x0, x1, y0, shade(base, 1.18))
            c.vl(x0, y0, y1, shade(base, 1.1))
            c.hl(x0, x1, y1, shade(base, .66))
            c.vl(x1, y0, y1, shade(base, .58))
            for xx, yy in ((x0 + 2, y0 + 2), (x1 - 2, y0 + 2), (x0 + 2, y1 - 2), (x1 - 2, y1 - 2)):
                c.px(xx, yy, shade(base, .5)); c.px(xx - 1, yy - 1, shade(base, 1.3))
    c.streaks(16, 60, 343, 149, 31 + i)
    c.grime(16, 58, 343, 149, 41 + i, amount=.35, col=(70, 68, 56), mixk=.12)
    c.scratches(16, 70, 343, 148, 50 + i, 9)
    for y, col in ((150, 0xc5ccc3), (151, 0x98a29c), (152, 0x7b8580), (153, 0x4a5352), (154, 0x262e2f)):
        c.hl(16, 343, y, col)
    for x0 in range(16, 344, 24):
        x1 = min(x0 + 23, 343)
        c.fill(x0, 155, x1, 232, WAINSCOT)
        c.vl(x0, 155, 232, shade(WAINSCOT, 1.18))
        c.vl(x1, 155, 232, shade(WAINSCOT, .6))
        for y in (159, 228):
            c.px(x0 + 3, y, shade(WAINSCOT, .45)); c.px(x0 + 2, y - 1, shade(WAINSCOT, 1.45))
    c.streaks(16, 156, 343, 232, 61 + i, col=(44, 40, 34), share=.35)
    c.grime(16, 155, 343, 232, 71 + i, amount=.7, col=(48, 44, 38), mixk=.18)
    c.scratches(16, 190, 343, 232, 90 + i, 12)
    c.fill(16, 233, 343, 239, 0x3c4545)
    c.hl(16, 343, 233, 0x7d8783)
    c.hl(16, 343, 239, 0x15191b)
    for x in range(20, 340, 17):
        if hash2(x, i, 4) > .45:
            c.hl(x, x + 3 + int(hash2(x, i, 6) * 5), 236, 0x5a6462)


def gangway(r, side):
    """One car's end: its frame and half the bellows to the next car."""
    c = r
    x0, x1 = (0, 15) if side < 0 else (344, 359)
    frame = (x1 - 5, x1) if side < 0 else (x0, x0 + 5)
    c.fill(x0, 50, x1, 239, 0x0f1417)
    # Bellows, pleated, lit only at their folds.
    for x in range(x0, x1 + 1):
        if (frame[0] <= x <= frame[1]): continue
        col = 0x283135 if x % 3 == 0 else 0x1b2226 if x % 3 == 1 else 0x121719
        c.vl(x, 62, 239, col)
    c.fill(x0, 50, x1, 61, 0x222b2e)
    c.hl(x0, x1, 50, 0x4a5654)
    # The door frame of this car, with a hazard edge at the threshold.
    fx0, fx1 = frame
    c.block(fx0, 50, fx1, 239, 0x46524f)
    c.fill(fx0 + 1, 152, fx1 - 1, 239, 0x56625f)
    c.vl(fx0 + 1, 152, 239, 0x7f8a85)
    for y in range(160, 236, 9):
        c.px(fx0 + 3, y, 0x232a2b); c.px(fx0 + 2, y - 1, 0x9aa49e)
    c.hazard(fx0, 140, fx1, 147, slope=side)


def end_wall(r, side):
    """The closed end of the train (car 01's tail)."""
    c = r
    x0, x1 = (0, 15) if side < 0 else (344, 359)
    c.block(x0, 50, x1, 239, 0x46524f)
    for y in range(60, 236, 11):
        c.px(x0 + 4, y, 0x232a2b); c.px(x0 + 3, y - 1, 0x9aa49e)
        c.px(x1 - 4, y, 0x232a2b); c.px(x1 - 5, y - 1, 0x9aa49e)
    # A fire extinguisher on its bracket.
    c.block(x0 + 4, 176, x0 + 11, 204, 0x9c3128)
    c.fill(x0 + 5, 182, x0 + 10, 188, 0xc9c1a5)
    c.block(x0 + 5, 170, x0 + 9, 176, 0x2a2f31)


def floor(r):
    """Identical in every room (the tiles meet on it): diamond plate on a sill."""
    c = r
    for x in range(360):
        c.px(x, 240, 0x9aa39c)
        for y in range(241, 250):
            lx, ly = x % 12, (y - 241) % 6
            col = 0x4c5454
            if (lx == 3 and ly == 1) or (lx == 9 and ly == 4): col = 0x828b86
            elif (lx == 4 and ly == 2) or (lx == 10 and ly == 5): col = 0x2f3536
            c.px(x, y, col)
        for y, col in ((250, 0x6c7472), (251, 0x2a3133), (252, 0x20272a)):
            c.px(x, y, col)
        for y in range(253, 261):
            c.px(x, y, 0x252c2f if y > 253 else 0x3d4648)
        if x % 12 == 6:
            c.px(x, 256, 0x5d6664); c.px(x - 1, 255, 0x7c8582)
        for y in range(261, 270):
            c.px(x, y, 0x13181b if (x // 30) % 2 else 0x171d20)
        if x % 30 == 0:
            c.vl(x, 261, 269, 0x262e31)


def relight(r):
    """Light from the two tubes (upper left of each object is brighter), the
    coloured spill of screens and liquids, then dithered bands."""
    c = r
    lamps = [(lx, 49) for k, lx in enumerate(LAMPS) if r.lamps[k]]
    for y in range(0, FLOOR):
        for x in range(360):
            if (x, y) in r.glow: continue
            col = c.get(x, y)
            if col is None: continue
            light = r.ambient - .1 * max(0, (y - 150) / 90)
            for lx, ly in lamps:
                dy = y - ly
                if dy < 0:
                    light += .22 * max(0, 1 - abs(x - lx) / 40) * max(0, 1 + dy / 14)
                    continue
                half = 34 + dy * .62
                t = abs(x - (lx - dy * .06)) / half
                if t < 1: light += .44 * (1 - t * t) * max(.2, 1 - dy / 260)
            # Ordered dithering between bands of .08: crisp pixel-art shading.
            q = light / .08
            lo = math.floor(q)
            k = (lo + (1 if dither(x, y, q - lo) else 0)) * .08
            col = shade(col, k)
            for tx, ty, rad, tcol, s in r.tints:
                d = math.hypot((x - tx) / rad, (y - ty) / (rad * .8))
                if d < 1:
                    amt = s * (1 - d)
                    if dither(x, y, min(1, amt * 3)): col = mix(col, tcol, amt)
            c.c.set(x, y, col)


# -- furniture -----------------------------------------------------------

def side_door_open(r, x0):
    """Car 01's sliding side door, open on the yard at dusk."""
    c = r
    x1 = x0 + 31
    c.block(x0 - 4, 156, x1 + 4, 239, 0x46524f)
    for y in range(160, 240):
        t = (y - 160) / 46
        for x in range(x0, x1 + 1):
            if y < 206:
                q = t * 5
                band = int(q) + (1 if dither(x, y, q - int(q)) else 0)
                col = mix(hx(0xf2b16a), hx(0xa94f37), min(1, band / 5))
            else:
                col = hx(0x3b2a28) if y < 214 else hx(0x2a1f1f)
                if y == 214 or y == 222: col = hx(0x8d5d3e)
            c.lit(x, y, col)
    # Yard silhouettes: a telegraph pole and a distant water tower.
    for y in range(166, 214): c.lit(x0 + 22, y, 0x3a2526)
    c.lit_fill(x0 + 18, 170, x0 + 26, 170, 0x3a2526)
    c.lit_fill(x0 + 4, 192, x0 + 11, 200, 0x4a2c2a)
    c.lit_fill(x0 + 6, 200, x0 + 7, 213, 0x4a2c2a)
    c.lit_fill(x0 + 9, 200, x0 + 10, 213, 0x4a2c2a)
    c.disc(x0 + 26, 180, 4, 0xffd89a)
    for y in range(176, 185):
        for x in range(x0 + 22, x0 + 31):
            if c.get(x, y) == hx(0xffd89a): c.glow.add((x, y))
    c.hazard(x0 - 4, 150, x1 + 4, 155)
    # The leaf, slid along the inside of the wall.
    c.block(x1 + 5, 158, x1 + 36, 239, 0x6c7974)
    c.recess(x1 + 9, 166, x1 + 32, 196, 0x5a6763)
    c.block(x1 + 9, 206, x1 + 13, 222, 0x2c3233)
    c.tints.append((x0 + 16, 205, 70, (236, 150, 92), .35))
    c.tints.append((x0 + 16, 238, 46, (236, 150, 92), .3))
    c.block(x0 + 2, 132, x1 - 2, 143, 0x1d2a22)
    c.text('SALIDA', x0 + 4, 135, 0x8fe39d, glow=True)
    c.contact_shadow(x1 + 5, x1 + 36)


def hatch(r, x0):
    """The control room's exit: a heavy door with a porthole and a lamp."""
    c = r
    x1 = x0 + 29
    c.hazard(x0 - 5, 150, x1 + 5, 155)
    c.block(x0 - 5, 156, x1 + 5, 239, 0x3d4746)
    c.block(x0, 162, x1, 239, 0x74817b)
    c.recess(x0 + 3, 200, x1 - 3, 234, 0x66726d)
    c.disc((x0 + x1) / 2, 180, 8, INK)
    c.disc((x0 + x1) / 2, 180, 7, 0x9da79e)
    for y in range(174, 187):
        for x in range(x0 + 9, x1 - 8):
            if ((x - (x0 + x1) / 2) / 5.5) ** 2 + ((y - 180) / 5.5) ** 2 <= 1:
                c.lit(x, y, mix(hx(0xf0a866), hx(0xa64f39), (y - 174) / 12))
    c.lit((x0 + x1) // 2 - 2, 176, 0xffe3b4)
    c.disc((x0 + x1) / 2, 214, 6, INK)
    c.disc((x0 + x1) / 2, 214, 5, 0x8f6b3e)
    c.disc((x0 + x1) / 2, 214, 3, 0x3d4746)
    for a in range(4):
        ang = a * math.pi / 2 + .4
        c.line((x0 + x1) // 2, 214, round((x0 + x1) / 2 + math.cos(ang) * 5), round(214 + math.sin(ang) * 5), 0xc0995a)
    # Socket for the lock lamp the game lights (red: locked, green: open).
    c.block(x1 + 1, 164, x1 + 4, 171, 0x1a1f21)
    c.block(x0 + 1, 132, x1 - 1, 143, 0x1d2a22)
    c.text('SALIDA', x0 + 3, 135, 0x8fe39d, glow=True)
    c.contact_shadow(x0 - 5, x1 + 5)


def cradle(r, cx):
    """The research cradle the game sets a part on (part's bottom at row 211)."""
    c = r
    c.block(cx - 15, 226, cx + 15, 239, 0x2f3738)
    c.hazard(cx - 13, 228, cx + 13, 230)
    c.block(cx - 6, 214, cx + 6, 226, 0x4e5958)
    c.block(cx - 13, 211, cx + 13, 215, 0x8a9590)
    for s in (-1, 1):
        x = cx + s * 12
        c.block(min(x, x + s * 3), 196, max(x, x + s * 3), 212, 0x5d6866)
        c.px(x + s * 2, 197, 0xc6cbbf)
    for k, lx in enumerate((cx - 9, cx - 5, cx + 4, cx + 8)):
        c.led(lx, 220, (0x7fe39a, 0xe8b25a, 0x7fe39a, 0x5fc8e0)[k])
    c.lit_fill(cx - 10, 212, cx + 10, 212, 0x9fe8e0)
    c.tints.append((cx, 205, 34, (130, 220, 210), .22))
    c.block(cx - 18, 134, cx + 18, 143, 0x24302d)
    c.text('MUESTRA', cx - 13, 136, 0xd6d0ae)
    c.contact_shadow(cx - 15, cx + 15)


def locker(r, x0, x1, top=162, col=0x7f8c88):
    c = r
    c.block(x0, top, x1, 238, col)
    b = hx(col)
    mid = (x0 + x1) // 2
    c.vl(mid, top + 2, 236, shade(b, .55))
    c.vl(mid + 1, top + 2, 236, shade(b, 1.2))
    for k, xx in enumerate((x0 + 3, mid + 3)):
        wide = (mid - x0) - 7
        for yy in range(top + 5, top + 14, 3):                # Louvres: a slit and its lit lip
            c.hl(xx, xx + wide, yy, shade(b, .45))
            c.hl(xx, xx + wide, yy + 1, shade(b, 1.22))
        c.recess(xx + 1, top + 18, xx + wide - 2, top + 22, shade(b, .8))
        c.fill(xx + 2, top + 19, xx + wide - 3, top + 21, 0xcfc8b0)
        c.hl(xx + 3, xx + wide - 5, top + 20, 0x7d776a)
        hxx = xx + wide - 1                                   # A recessed pull
        c.recess(hxx - 1, top + 34, hxx + 2, top + 43, shade(b, .7))
        c.block(hxx, top + 36, hxx + 1, top + 41, 0xc8c2a6, ink=False)
        if k == 1:                                            # A padlock on it
            c.block(hxx - 1, top + 44, hxx + 2, top + 48, 0xb08a3a)
            c.vl(hxx, top + 42, top + 44, 0x8f9a94)
            c.px(hxx + 1, top + 46, INK)
        for yy in (top + 10, top + 34, 228):                 # Hinges on its outer edge
            hx_ = x0 + 1 if k == 0 else x1 - 2
            c.fill(hx_, yy, hx_ + 1, yy + 4, shade(b, .5))
            c.px(hx_, yy, shade(b, 1.4))
    dx, dy = x0 + (mid - x0) // 2, top + 57                   # A dent in its left door
    for y in range(dy - 6, dy + 7):
        for x in range(dx - 4, dx + 5):
            d = ((x - dx) / 4) ** 2 + ((y - dy) / 6) ** 2
            if d <= 1:
                cur = c.get(x, y)
                if cur: c.c.set(x, y, shade(cur, .78 if y < dy else 1.16 if d > .4 else 1.0))
    c.grime(x0, top, x1, 238, x0, .6, (50, 46, 40), .16)
    c.contact_shadow(x0, x1)


def bench(r, x0, x1, top=204, col=0x3f4b4b):
    c = r
    c.block(x0, top, x1, top + 3, 0x8f9a94)
    c.block(x0 + 2, top + 4, x1 - 2, 238, col)
    for xx in range(x0 + 4, x1 - 20, 30):
        c.recess(xx, top + 7, xx + 25, top + 16, shade(hx(col), 1.1))
        c.block(xx + 10, top + 10, xx + 15, top + 11, 0xbfb79a, ink=False)
        c.recess(xx, top + 19, xx + 25, 234, shade(hx(col), 1.05))
    c.contact_shadow(x0, x1)


def flask(r, x, y, liquid, h=8):
    """A test tube: its rim, the light down its left, the liquid lit with its
    meniscus, the glass shadowed on the right and a round bottom."""
    c = r
    liq = hx(liquid)
    lvl = y + h // 3
    for yy in range(y, y + h + 1):
        last = yy == y + h
        c.px(x, yy, INK if last else 0xd4e3dc)
        for xx in (x + 1, x + 2):
            if yy >= lvl: c.lit(xx, yy, liq if xx == x + 1 else shade(liq, .72))
            else: c.px(xx, yy, 0x93aaa6 if xx == x + 1 else 0x6f8582)
        c.px(x + 3, yy, INK if last else 0x3e4c4a)
    c.lit(x + 1, lvl, mix(liq, (255, 255, 255), .55))
    c.lit(x + 2, lvl, mix(liq, (255, 255, 255), .3))
    c.hl(x, x + 3, y + h + 1, INK)
    c.px(x + 1, y + h, shade(liq, .6)); c.px(x + 2, y + h, shade(liq, .5))
    c.hl(x - 1, x + 4, y - 1, 0xb3c3bf)
    c.px(x - 1, y - 1, 0xe6efec)


def chair(r, x, flip=1):
    """A 0.9 m chair: 17 px seat, 34 px back beside a 64 px human."""
    c = r
    c.block(x, 222, x + 14, 225, 0x2b3436)
    c.block(x + (12 if flip > 0 else 0), 205, x + (15 if flip > 0 else 3), 222, 0x2b3436)
    c.vl(x + 7, 226, 236, 0x4c5759)
    c.hl(x + 1, x + 13, 237, 0x4c5759)
    c.px(x + 1, 238, 0x1b2022); c.px(x + 13, 238, 0x1b2022)


# -- the rooms ---------------------------------------------------------

def room_access(r):
    c = r
    tf.side_door(r, ENTRY_X - 15)
    tf.decon_booth(r, 136)
    tf.suit_rail(r, SUIT_X, SUIT_HOOK)
    locker(r, 250, 288)
    tf.open_locker(r, TABLET_X - 19, TABLET_X + 19, TABLET_BOTTOM)
    c.paper(100, 238, 6, 2); c.paper(198, 238, 5, 2)
    c.handprint(186, 176, 3)
    c.stain(232, 238, 10, 2, 7)


def room_prototypes(r):
    c = r
    tf.tool_board(r, 28, 162, 166, 195)
    bench(r, 24, 140)
    c.screen(36, 187, 58, 199, (124, 220, 150), 4, 'trace', mount=False)
    c.block(76, 196, 100, 203, 0x5c6a68)
    c.block(114, 199, 132, 203, 0x8d7a44)
    c.block(120, 193, 126, 199, 0x6c7472)
    # A wall-mounted test frame, with a clear supply bay below it.
    c.block(174, 140, 236, 196, 0x29343a)
    c.recess(178, 144, 232, 192, 0x1d262b)
    c.text('PLASMA', 194, 147, 0x9fd8d0)
    for k in range(8):
        sx, sy = 182 + (k % 4) * 12, 158 + (k // 4) * 16
        c.block(sx, sy, sx + 9, sy + 12, 0x3c494c)
        c.recess(sx + 2, sy + 3, sx + 7, sy + 10, 0x141a1d)
        c.led(sx + 4, sy + 1, 0xd94d3a)
    cradle(r, CRADLE_X)
    c.block(290, 133, 336, 162, 0x2f5878)
    for x in range(294, 334, 6): c.vl(x, 136, 159, 0x4a76a0)
    c.line(296, 154, 330, 140, 0xcde0ef)
    c.disc(312, 147, 6, 0xcde0ef); c.disc(312, 147, 4, 0x2f5878)
    c.px(292, 135, 0xd94d3a); c.px(334, 135, 0xd94d3a)
    locker(r, 300, 330, top=171, col=0x6c7976)
    c.paper(60, 238, 6, 2); c.paper(226, 237, 4, 2, 1)


def tank(r, x0, liquid, broken=False, seed=0):
    """A culture tank: steel caps, thick glass and a lit column of medium."""
    c = r
    x1 = x0 + 34
    c.block(x0, 84, x1, 98, 0x55615f)
    c.block(x0 - 2, 222, x1 + 2, 239, 0x46514f)
    c.hazard(x0, 226, x1, 228)
    for y in range(99, 222):
        for x in range(x0 + 2, x1 - 1):
            if broken and y < 186:
                col = mix(hx(0x334446), hx(0x1c2527), (y - 99) / 87)
                if (x + y) % 13 == 0: col = shade(col, 1.25)
                c.px(x, y, col)
                continue
            t = (x - x0) / 34
            base = mix(hx(liquid), shade(hx(liquid), .55), abs(t - .35) * 1.6)
            if hash2(x, y // 2, seed) > .97: base = mix(base, (240, 255, 240), .6)
            c.lit(x, y, base)
    for y in range(99, 222):
        c.px(x0 + 1, y, 0x2a3537); c.px(x1 - 1, y, 0x2a3537)
        if not broken or y > 160: c.lit(x0 + 5, y, mix(hx(liquid), (255, 255, 255), .55))
    for yy in (130, 180): c.hl(x0 + 1, x1 - 1, yy, 0x6c7876)
    if not broken:
        # A shape suspended in the medium.
        c.disc(x0 + 17, 157, 5, shade(hx(liquid), .45))
        c.poly([(x0 + 11, 164), (x0 + 23, 164), (x0 + 24, 189), (x0 + 20, 215), (x0 + 15, 215), (x0 + 10, 189)],
               shade(hx(liquid), .5))
        for y in range(150, 216):
            for x in range(x0 + 8, x0 + 27):
                if (x, y) in r.glow: continue
                if c.get(x, y) == shade(hx(liquid), .5) or c.get(x, y) == shade(hx(liquid), .45):
                    c.glow.add((x, y))
        for k in range(6):
            c.lit(x0 + 8 + int(hash2(k, seed, 1) * 18), 104 + k * 17, 0xe9fff6)
    else:
        # What is left of the glass: jagged teeth round the hole.
        for x in range(x0 + 2, x1 - 1):
            tooth = 4 + int(hash2(x, 7, seed) * 12) if (x - x0) % 9 < 5 else 1
            for y in range(186 - tooth, 186):
                c.px(x, y, 0x9fc0ba if (x - x0) % 9 == 0 else 0x5f8682)
        c.hl(x0 + 2, x1 - 2, 186, mix(hx(liquid), (255, 255, 255), .5))
        for y in range(99, 112): c.px(x0 + 3, y, 0x9fc0ba); c.px(x1 - 3, y, 0x5f8682)
        c.glass_shards(x0 - 14, x1 + 22, seed)
        for x in range(x0 - 10, x1 + 26):
            if hash2(x, 1, seed) > .35: c.lit(x, FLOOR - 1, mix(hx(liquid), (30, 40, 40), .5))
    c.tints.append((x0 + 17, 160, 46, hx(liquid), .2))
    c.contact_shadow(x0 - 2, x1 + 2)


def room_cultures(r):
    c = r
    tank(r, 26, 0x6fd28a, seed=1)
    tank(r, 74, 0x6fd28a, seed=2)
    tank(r, 150, 0x8bd86a, broken=True, seed=3)
    # Incubator shelf with lit flasks.
    c.block(240, 88, 338, 150, 0x3b4747)
    for k, y in enumerate((96, 118, 140)):
        c.recess(244, y - 4, 334, y + 9, 0x222c2e)
        for x in range(248, 330, 7):
            flask(r, x, y - 2, (0x8bd86a, 0x6fd28a, 0xd6c35a)[(x + k) % 3], 9)
        c.hl(244, 334, y + 10, 0x9aa49e)
    c.tints.append((290, 120, 60, (140, 220, 120), .18))
    bench(r, 236, 340)
    c.block(250, 194, 278, 203, 0x8d9792)  # Centrifuge
    c.disc(264, 198, 4, 0x3b4747); c.disc(264, 198, 2, 0x6fd28a)
    c.block(296, 194, 330, 203, 0xb4952f)
    c.text('MRC-2', 300, 197, 0x2a2622)
    c.block(204, 98, 226, 120, 0xd3b93f)
    c.disc(215, 109, 7, 0x2a2622); c.disc(215, 109, 4, 0xd3b93f); c.disc(215, 109, 2, 0x2a2622)
    c.stain(196, 200, 7, 12, 4)
    c.handprint(120, 150, 5)


def room_surgery(r):
    c = r
    # An examination cot is visible through the opening in a supported,
    # near-floor privacy curtain. Supplies have their own bay farther right.
    tf.clinical_cot(r, 33, 76)
    tf.clinical_curtain(r, 25, 112, 30, 9)
    c.stain(46, 211, 3, 9, 2)
    # A two-metre surgical table, about 85 cm high.
    c.block(132, 207, 208, 212, 0xa9b2aa)
    c.block(168, 213, 177, 231, 0x55605f)
    c.block(153, 231, 192, 236, 0x3c4545)
    c.hl(133, 207, 208, 0xdfe6e0)
    for y in range(216, 230, 5): c.hl(169, 176, y, 0x7d8886)
    for x in (158, 187): c.disc(x, 238, 1.5, 0x22292b)
    c.poly([(138, 207), (152, 200), (180, 199), (201, 202), (205, 207)], 0xc9cdc1)
    c.disc(145, 203, 5, 0xc9cdc1, 3)
    for k in range(4):
        x = 155 + k * 12
        c.line(x, 201, x + 4, 207, 0xa4a99e)
        c.line(x + 1, 201, x + 5, 207, 0xe2e5dc)
    c.stain(185, 206, 10, 2, 6, (110, 32, 28), .7)
    for y in range(212, 239, 6): c.px(199 + y % 2, y, 0x6b2420)
    c.stain(200, 239, 11, 2, 8, (90, 28, 26), .7)
    c.contact_shadow(132, 208)
    # Long ceiling arm; the lamp head remains a normal surgical light.
    c.line(196, 58, 196, 139, 0x8f9a94)
    c.line(197, 58, 197, 139, 0x5a6563)
    c.line(196, 139, 169, 164, 0x8f9a94)
    c.disc(163, 170, 11, INK, 5); c.disc(163, 169, 10, 0xb9c1b8, 4)
    c.lit_fill(155, 171, 171, 173, 0xfff3d4)
    c.tints.append((163, 198, 40, (255, 240, 200), .2))
    c.block(259, 211, 285, 214, 0x9aa49e)
    c.vl(272, 215, 236, 0x6c7472); c.hl(262, 282, 237, 0x6c7472)
    for k in range(4): c.hl(262 + k * 5, 265 + k * 5, 210, 0xd4dad2)
    c.vl(311, 160, 237, 0x9aa49e); c.hl(306, 316, 160, 0x9aa49e)
    c.block(305, 163, 310, 175, 0xb7cdc6)
    c.lit_fill(306, 168, 309, 174, 0xb94a3c)
    c.screen(258, 175, 281, 189, (232, 98, 82), 3, 'flat')
    c.handprint(330, 190, 1); c.handprint(120, 188, 4)


def room_analysis(r):
    c = r
    bench(r, 22, 338, col=0x445150)
    # Human-height extraction cabinet; bottles are 7-13 px high.
    c.block(26, 155, 112, 203, 0x6c7976)
    c.recess(31, 162, 107, 201, 0x2f3b3d)
    for y in range(164, 181):
        for x in range(32, 107):
            if (x + y) % 11 == 0: c.px(x, y, 0x5a7a7b)
    c.hl(31, 107, 181, 0xc6d4cf)
    tf.bottle(r, 39, 200, 'reagent', 0x6b3a1e, 'red', 1)
    tf.bottle(r, 53, 200, 'erlenmeyer', 0x8bd86a, None, 2)
    tf.bottle(r, 70, 200, 'round', 0xd6c35a, None, 3)
    tf.bottle(r, 99, 200, 'cylinder', 0x6fb7d2, None, 4)
    c.hl(31, 107, 201, 0x8f9a95)
    for mx in (135, 223):
        c.block(mx, 200, mx + 15, 203, 0x2b3436)
        c.block(mx + 9, 187, mx + 12, 200, 0x2b3436)
        c.line(mx + 10, 187, mx + 5, 181, 0x3c4546)
        c.block(mx + 2, 179, mx + 7, 182, 0x6c7472)
        c.hl(mx + 3, mx + 10, 193, 0x9aa49e)
        c.lit(mx + 6, 196, 0xfff3d4)
    for rx in (171, 261, 303):
        c.block(rx, 200, rx + 22, 203, 0x6c7472)
        for k in range(4):
            flask(r, rx + 2 + k * 5, 193, (0xd06a4e, 0x8bd86a, 0xd6c35a, 0x6fb7d2)[k], 6)
    c.screen(140, 163, 163, 177, (127, 208, 138), 7, 'bars')
    c.screen(228, 163, 251, 177, (232, 170, 90), 9, 'lines')
    c.screen(304, 163, 327, 177, (127, 208, 138), 11, 'trace')
    c.block(140, 129, 330, 140, 0x34413e)
    c.text('ANALISIS DE MUESTRAS MRC-2', 158, 132, 0xcfc8ae)
    for k in range(5): c.paper(130 + k * 34, 237, 5, 2, k % 2)
    c.stain(320, 236, 8, 3, 9)


def cell(r, x0, open_=False):
    c = r
    x1 = x0 + 74
    c.block(x0, 76, x1, 239, 0x3a4442)
    c.recess(x0 + 4, 82, x1 - 4, 236, 0x182023)
    for y in range(84, 234):
        for x in range(x0 + 5, x1 - 4):
            if fbm(x / 6, y / 9, x0, 2) > .62: c.px(x, y, 0x222b2d)
    c.tints.append(((x0 + x1) // 2, 150, 40, (200, 60, 50), .12))
    # A short fixed bench, a blanket and a bowl sit behind the bars. The
    # restraint chain hangs from a bolted bracket rather than free in space.
    c.block(x0 + 10, 218, x1 - 12, 222, 0x5a7061)
    c.block(x0 + 24, 214, x1 - 16, 218, 0x6c7759)
    for x in (x0 + 13, x1 - 15): c.vl(x, 223, 235, 0x4f6455)
    c.disc(x1 - 11, 233, 4, 0x7d8f7b, 1.5)
    c.hl(x1 - 14, x1 - 8, 232, 0xa2b195)
    c.block(x0 + 11, 112, x0 + 17, 117, 0x536b58)
    c.px(x0 + 13, 114, 0xa5b494)
    for y in range(118, 153, 4):
        c.disc(x0 + 14 + (y % 8 == 2), y, 1.3, 0x7f9380, 2)
    if not open_:
        for x in range(x0 + 8, x1 - 4, 8):
            c.vl(x, 84, 234, 0x9aa49e); c.vl(x + 1, 84, 234, 0x4f5a58)
        for y in (110, 200): c.block(x0 + 5, y, x1 - 5, y + 4, 0x6c7876)
    else:
        # Bars bent outward, claw marks on the frame.
        for k, x in enumerate(range(x0 + 8, x1 - 4, 8)):
            bend = 9 - abs(k - 4) * 2 if 2 <= k <= 6 else 0
            for y in range(84, 235):
                t = math.sin(max(0, min(1, (y - 120) / 70)) * math.pi)
                xx = x + int(bend * t)
                c.px(xx, y, 0x9aa49e); c.px(xx + 1, y, 0x4f5a58)
        c.block(x0 + 5, 110, x0 + 30, 114, 0x6c7876)
        c.block(x1 - 24, 200, x1 - 5, 204, 0x6c7876)
        for k in range(4): c.line(x1 + 2 + k * 3, 120 + k, x1 + 6 + k * 3, 148 + k, 0xc9d0c6)
        c.stain(x1 - 4, 230, 10, 4, x0)
    c.hazard(x0, 236, x1, 239)
    c.block(x0 + 20, 64, x1 - 20, 74, 0x23302b)
    c.text('CELDA', x0 + 27, 67, 0xe6d27c)


def room_containment(r):
    c = r
    cell(r, 24)
    cell(r, 134, open_=True)
    cell(r, 254)
    for x in (122, 232):
        c.block(x - 3, 92, x + 3, 100, 0x2a2f31)
        c.lit_fill(x - 2, 93, x + 2, 98, 0xe5523e)
        c.tints.append((x, 110, 34, (230, 80, 60), .25))
    c.block(110, 205, 124, 222, 0x2b3436)  # Restraint chair
    c.block(108, 222, 126, 225, 0x3c4546)
    c.vl(111, 226, 238, 0x4c5759); c.vl(123, 226, 238, 0x4c5759)
    c.hl(110, 124, 213, 0x8a5b3a)
    c.glass_shards(200, 236, 5)


def pod(r, x0, broken=False, seed=0):
    """A cryogenic capsule: frosted glass over a blue-lit sleeper."""
    c = r
    x1 = x0 + 42
    c.block(x0, 80, x1, 239, 0x46524f)
    c.block(x0 + 2, 82, x1 - 2, 92, 0x7c8986)
    c.block(x0 + 2, 218, x1 - 2, 239, 0x55615f)
    c.hazard(x0 + 4, 222, x1 - 4, 224)
    for k in range(3): c.led(x0 + 8 + k * 4, 230, (0x6fc8e8, 0x6fc8e8, 0xe8b25a)[k])
    for y in range(93, 218):
        for x in range(x0 + 4, x1 - 3):
            t = (x - x0 - 4) / (x1 - x0 - 7)
            col = mix(hx(0x7ec7e0), hx(0x2d6f8c), min(1, abs(t - .4) * 1.8))
            if broken: col = mix(hx(0x2a3a40), hx(0x1a2428), (y - 93) / 125)
            edge = min(y - 93, 217 - y, x - x0 - 4, x1 - 4 - x)
            if edge < 3 and hash2(x, y, seed) > .25 * edge:
                col = mix(col, (220, 240, 245), .55 - edge * .12)
            elif hash2(x, y, seed + 9) > .985:
                col = mix(col, (235, 250, 255), .7)
            (c.px if broken else c.lit)(x, y, col)
    if not broken:
        c.disc(x0 + 21, 159, 5, 0x3c6f82)
        c.poly([(x0 + 15, 166), (x0 + 27, 166), (x0 + 28, 188), (x0 + 25, 214), (x0 + 17, 214), (x0 + 14, 188)], 0x3f7286)
        for y in range(153, 216):
            for x in range(x0 + 10, x0 + 33):
                if c.get(x, y) in (hx(0x3c6f82), hx(0x3f7286)): c.glow.add((x, y))
        c.tints.append((x0 + 21, 150, 50, (126, 199, 224), .26))
    else:
        for k in range(6):
            c.line(x0 + 6 + k * 6, 96 + (k * 13) % 30, x0 + 3 + k * 6, 140 + (k * 7) % 40, 0xbad3d8)
        c.glass_shards(x0 - 10, x1 + 12, seed)
        for x in range(x0 - 6, x1 + 8):
            if hash2(x, 3, seed) > .5: c.px(x, FLOOR - 1, 0xc8dde2)
    c.contact_shadow(x0, x1)


def room_cryo(r):
    c = r
    pod(r, 22, seed=1)
    pod(r, 72, seed=2)
    tf.burst_pod(r, 122, 3)
    pod(r, 172, seed=4)
    cradle(r, CRADLE_X)
    # Liquid nitrogen dewars with gauges and frosted hoses.
    for k, x in enumerate((288, 316)):
        c.block(x, 150, x + 22, 238, 0x8d9894)
        c.disc(x + 11, 150, 11, 0x8d9894, 4)
        c.hl(x + 2, x + 20, 150, 0xc9d1cb)
        c.block(x + 6, 164, x + 16, 172, 0xd8dcd2)
        c.disc(x + 11, 168, 3, 0x2a2f31)
        c.line(x + 11, 168, x + 13, 166, 0xd94d3a)
        c.text('N2', x + 7, 190, 0x2f6f8c)
        c.contact_shadow(x, x + 22)
    c.line(299, 140, 270, 110, 0xcfe3e8); c.line(300, 140, 271, 110, 0x8fa8ae)
    c.block(276, 70, 338, 108, 0x24302d)
    c.text('CRIOGENIA', 282, 76, 0x9fd8e8)
    c.screen(284, 88, 330, 102, (126, 199, 224), 5, 'bars')


def room_archive(r):
    c = r
    for k, x in enumerate((24, 108)):
        c.block(x, 159, x + 56, 238, 0x5a6764)
        for y in range(164, 234, 17):
            c.recess(x + 4, y, x + 52, y + 13, 0x3e4846)
            for bx in range(x + 6, x + 46, 15):
                c.block(bx, y + 3, bx + 12, y + 12, 0x8d7652 if (bx + y) % 3 else 0x7b6648)
                c.hl(bx + 3, bx + 9, y + 7, 0xd8cfb0)
        c.contact_shadow(x, x + 56)
    # The supply bay at x188 is separate from shelves and desk.
    c.block(211, 211, 277, 214, 0x6f6448)
    for x in (215, 270): c.block(x, 215, x + 3, 238, 0x4e4635)
    c.screen(216, 192, 236, 205, (232, 170, 90), 13, 'lines', mount=False)
    c.block(248, 205, 270, 211, 0x3a3f3c)
    for k in range(4): c.px(251 + k * 4, 208, 0xc6c0a5)
    c.block(252, 200, 267, 204, 0xc8c2a6)
    # Chair is pulled to the right, rather than drawn through the desk legs.
    chair(r, 282, -1)
    c.block(316, 187, 338, 238, 0x3c4546)
    c.recess(319, 191, 334, 220, 0x141a1d)
    c.block(335, 190, 342, 222, 0x56625f)
    c.disc(338, 207, 2, 0xa88c4f)
    c.block(298, 165, 340, 175, 0x23302b)
    c.text('ARCHIVO 4', 302, 168, 0xe6d27c)
    c.paper(322, 216, 6, 3, 1)
    for k in range(6): c.paper(42 + k * 30, 237, 5, 2, k % 2)
    c.stain(150, 238, 10, 2, 6)


def room_machinery(r):
    c = r
    r.ambient = .56
    # The generator: engine block, flywheel, exhaust up through the roof.
    c.block(22, 132, 190, 238, 0x4c5655)
    for x in range(28, 182, 14):
        c.block(x, 140, x + 11, 176, 0x5f6a68)
        for y in range(144, 174, 3): c.hl(x + 2, x + 9, y, 0x3a4341)
    c.block(26, 180, 186, 186, 0x8d7a44)
    c.disc(60, 210, 22, INK)
    c.disc(60, 210, 21, 0x6c7876)
    c.disc(60, 210, 16, 0x3c4545)
    c.disc(60, 210, 6, 0xa88c4f)
    for a in range(6):
        ang = a * math.pi / 3
        c.line(60, 210, round(60 + math.cos(ang) * 15), round(210 + math.sin(ang) * 15), 0x8a9592)
    c.block(150, 60, 164, 132, 0x3c4545)
    c.vl(151, 60, 131, 0x6c7876)
    c.block(146, 96, 168, 102, 0x5a6563)
    for x in range(100, 180, 22):
        c.block(x, 194, x + 16, 210, 0x2f3738)
        c.disc(x + 8, 202, 5, 0xd8dcd2); c.disc(x + 8, 202, 4, 0x2a2f31)
        c.line(x + 8, 202, x + 10 + (x % 3), 199, 0xd94d3a)
    c.grime(22, 132, 190, 238, 77, 1.1, (30, 28, 24), .45)
    c.contact_shadow(22, 190)
    for y in (70, 78):
        c.hl(196, 340, y, 0x6c7876); c.hl(196, 340, y + 1, 0x2c3434)
    for x in (210, 262, 318):
        c.block(x - 3, 68, x + 3, 82, 0x8d4a36)
    cradle(r, CRADLE_X)
    c.line(232, 210, 210, 236, 0x1b1d1f); c.line(233, 210, 211, 236, 0x6b2b24)
    # Breaker cabinet with warning lamps.
    c.block(286, 92, 340, 238, 0x55625f)
    c.recess(292, 100, 334, 160, 0x2b3436)
    for y in range(104, 156, 8):
        for x in range(296, 330, 6):
            c.block(x, y, x + 3, y + 5, 0x8a9592, ink=False)
            c.px(x + 1, y + (2 if (x + y) % 3 else 4), 0x1b1d1f)
    for k, x in enumerate((298, 312, 326)):
        c.disc(x, 176, 3, INK)
        c.lit_fill(x - 1, 175, x + 1, 177, (0xe5523e, 0xe8b25a, 0x7fe39a)[k])
    c.block(296, 196, 330, 206, 0xd3b93f)
    c.text('PELIGRO', 299, 199, 0x2a2622)
    c.contact_shadow(286, 340)
    c.tints.append((310, 176, 30, (230, 120, 60), .18))


def room_control(r):
    c = r
    # Consoles under a route map; the terminal in the middle; the hatch last.
    c.block(20, 70, 170, 128, 0x24302d)
    for y in range(74, 126):
        for x in range(24, 166):
            c.lit(x, y, 0x1c2c26 if (x + y) % 2 else 0x1a2924)
    pts = [(30, 118), (58, 110), (80, 112), (104, 98), (132, 92), (156, 80)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        n = max(abs(xb - xa), abs(yb - ya))
        for k in range(n + 1):
            c.lit(round(xa + (xb - xa) * k / n), round(ya + (yb - ya) * k / n), 0xe8b25a)
    for x, y in pts[:-1]: c.lit(x, y, 0xfff3d4)
    c.disc(156, 80, 3, 0xe5523e)
    c.glow.update((x, y) for x in range(152, 161) for y in range(76, 85) if c.get(x, y) == hx(0xe5523e))
    c.text('CERRO GRIS', 112, 86, 0xe8d6a0, glow=True)
    c.text('RUTA 4-G', 28, 76, 0x8fe39d, glow=True)
    c.tints.append((95, 100, 80, (232, 178, 90), .12))
    c.block(20, 204, 158, 207, 0x8f9a94)
    c.block(22, 208, 156, 238, 0x3f4b4b)
    for k, x in enumerate((26, 70, 114)):
        c.screen(x + 2, 182, x + 30, 197, ((127, 208, 138), (232, 170, 90), (126, 199, 224))[k], 20 + k,
                 ('lines', 'bars', 'trace')[k], mount=False)
        c.recess(x + 1, 213, x + 33, 234, 0x34403f)
        for kk in range(5): c.led(x + 5 + kk * 5, 216, (0x7fe39a, 0xe8b25a, 0xe5523e)[(kk + k) % 3])
    chair(r, 176)
    tx = TERMINAL_X
    c.block(tx - 21, 169, tx + 21, 238, 0x4a5655)
    c.screen(tx - 17, 176, tx + 17, 196, (232, 170, 90), 31, 'lines', mount=False)
    c.lit_fill(tx - 17, 178, tx + 17, 185, mix(hx(0xe8aa5a), (12, 22, 22), .86))
    c.text('ARCHIVO 4', tx - 17, 180, 0xffd27a, glow=True)
    c.block(tx - 19, 204, tx + 19, 208, 0x8f9a94)
    for k in range(9): c.px(tx - 16 + k * 4, 206, 0x2a2f31)
    # The tablet slides into a reachable recess below the keyboard.
    c.recess(tx - 10, 215, tx + 10, 225, 0x141c1e)
    c.hl(tx - 8, tx + 8, 224, 0xc19a4c)
    c.led(tx + 14, 219, 0x7fe39a)
    c.recess(tx - 17, 229, tx + 17, 235, 0x34403f)
    c.block(tx - 18, 153, tx + 18, 162, 0x24302d)
    c.text('TERMINAL', tx - 15, 155, 0xd6d0ae)
    c.contact_shadow(tx - 21, tx + 21)
    hatch(r, EXIT_X - 14)
    c.stain(270, 238, 10, 2, 4)
    c.paper(60, 237, 5, 2); c.paper(180, 238, 6, 2, 1)


ROOM_NAMES = ['DESCONTAMINACION', 'PROTOTIPOS', 'CULTIVOS MRC-2', 'CIRUGIA', 'ANALISIS',
              'CONTENCION', 'CRIOGENIA', 'ARCHIVO MOVIL', 'DORMITORIO', 'COMEDOR', 'ENFERMERIA',
              'ARMERIA', 'COMUNICACIONES', 'MAQUINAS', 'CONTROL']
ROOM_ART = [room_access, room_prototypes, room_cultures, room_surgery, room_analysis,
            room_containment, room_cryo, room_archive, tf.room_dormitory, tf.room_mess,
            tf.room_infirmary, tf.room_armory, tf.room_radio, room_machinery, room_control]
DEAD_TUBES = {3: (False, True), 5: (True, False), 9: (False, True), 11: (True, False), 13: (True, False)}


def interior_room(index):
    r = Room(index)
    r.lamps = list(DEAD_TUBES.get(index, (True, True)))
    shell(r)
    tf.room_wall_services(r)
    if index == 0: end_wall(r, -1)
    else: gangway(r, -1)
    if index == ROOMS - 1: end_wall(r, 1)
    else: gangway(r, 1)
    # The car's number on its door frame, at eye level beside each gangway.
    num = '%02d' % (index + 1)
    for x in ((4,) if index else ()) + ((348,) if index < ROOMS - 1 else ()):
        r.block(x - 1, 112, x + 9, 120, 0x1d2a22)
        r.text(num, x + 1, 114, 0xe6d27c)
    ROOM_ART[index](r)
    tf.room_dressing(r)
    for room, cx, cy in VENT_FANS:
        if room == index: tf.extractor_housing(r, cx, cy)
    relight(r)
    floor(r)
    for x in range(20, 340):
        if hash2(x, index, 12) > .985: r.px(x, 245, 0x9aa39c)
    return r


def make_interior():
    out = Image(ROOM_W * ROOMS, INTERIOR_H)
    for i in range(ROOMS):
        c = interior_room(i).c
        for y in range(INTERIOR_H):
            for x in range(ROOM_W):
                col = c.get(x, y) or (0, 0, 0)
                out.set(i * ROOM_W + x, y, (col[0], col[1], col[2], 255))
    return out


# ======================================================================
# The prototype's eight pieces
# ======================================================================

def part_art(part):
    """One piece of the plasma cannon: dark contour, brass and steel, a lit core."""
    c = Canvas(PART, PART)
    brass, steel, core = hx(0xc19a4c), hx(0x9aa6a2), [hx(0x7ff0e6), hx(0xb98cff), hx(0x9ff07a), hx(0xffc46b)][part % 4]

    def blk(x0, y0, x1, y1, col):
        c.fill(x0 - 1, y0 - 1, x1 + 1, y1 + 1, INK)
        c.fill(x0, y0, x1, y1, col)
        c.hline(x0, x1, y0, shade(col, 1.35)); c.vline(x0, y0, y1, shade(col, 1.18))
        c.hline(x0 + 1, x1, y1, shade(col, .6)); c.vline(x1, y0 + 1, y1, shade(col, .7))

    def glow(x0, y0, x1, y1, col):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t = abs((x - (x0 + x1) / 2) / max(1, (x1 - x0) / 2))
                c.set(x, y, mix(mix(col, (255, 255, 255), .45), col, t))

    if part == 0:   # Plasma chamber: a cylinder with a window on its core
        blk(6, 6, 25, 27, steel)
        blk(4, 4, 27, 8, brass); blk(4, 25, 27, 28, brass)
        c.fill(10, 11, 21, 22, INK); glow(11, 12, 20, 21, core)
        for y in (14, 18): c.hline(11, 20, y, shade(core, .75))
        c.set(12, 13, (255, 255, 255))
    elif part == 1:  # Cryogenic coil: copper turns round a frosted bar
        blk(13, 3, 18, 28, steel)
        for k, y in enumerate(range(6, 27, 4)):
            c.fill(6, y - 1, 25, y + 1, INK)
            c.hline(7, 24, y, hx(0xd38a4a)); c.hline(7, 24, y - 1 if k % 2 else y + 1, hx(0x8c4f2a))
        glow(14, 4, 17, 27, core)
        c.set(9, 8, (240, 255, 255)); c.set(22, 20, (240, 255, 255))
    elif part == 2:  # Power cell: a battery with a charge gauge
        blk(7, 6, 24, 28, hx(0x5b6a66))
        blk(12, 3, 19, 6, brass)
        c.fill(10, 10, 21, 25, INK)
        for k in range(4): c.fill(11, 22 - k * 4, 20, 24 - k * 4, core if k < 3 else shade(core, .4))
        c.vline(8, 8, 26, shade(hx(0x5b6a66), 1.5))
    elif part == 3:  # Regulator: a box with a dial and a knob
        blk(4, 8, 27, 26, hx(0x6d7a5a))
        c.fill(7, 11, 18, 22, INK)
        c.fill(8, 12, 17, 21, hx(0xe8e0c4))
        c.set(12, 14, INK); c.set(13, 15, INK); c.set(14, 16, hx(0xd94d3a)); c.set(15, 17, hx(0xd94d3a))
        blk(20, 12, 25, 17, brass)
        for k in range(3): c.set(21 + k * 2, 22, core)
        blk(12, 4, 19, 7, steel)
    elif part == 4:  # Focusing lens: glass in a ringed brass mount
        c.disc(15.5, 15.5, 13, INK); c.disc(15.5, 15.5, 12, brass)
        c.disc(15.5, 15.5, 9, INK); c.disc(15.5, 15.5, 8, mix(core, (40, 60, 70), .35))
        c.disc(13, 13, 4, mix(core, (255, 255, 255), .5))
        c.set(11, 11, (255, 255, 255)); c.set(12, 11, (255, 255, 255))
        for a in range(8):
            ang = a * math.pi / 4
            c.set(round(15.5 + math.cos(ang) * 10.5), round(15.5 + math.sin(ang) * 10.5), shade(brass, .55))
    elif part == 5:  # Injector: a nozzle on a feed pipe
        blk(4, 12, 15, 19, steel)
        blk(15, 9, 22, 22, brass)
        c.poly([(23, 11), (29, 14), (29, 17), (23, 20)], INK)
        c.poly([(23, 12), (28, 14), (28, 17), (23, 19)], steel)
        glow(25, 14, 28, 17, core)
        blk(8, 4, 11, 11, hx(0x5b6a66))
    elif part == 6:  # Insulator: stacked ceramic discs
        for k, y in enumerate(range(5, 26, 5)):
            blk(6 + (k % 2), y, 25 - (k % 2), y + 3, hx(0xd8d0bc) if k % 2 == 0 else hx(0xb44f36))
        blk(13, 2, 18, 4, steel); blk(13, 27, 18, 29, steel)
        c.set(9, 6, (255, 255, 255))
    else:            # Control core: a chip with pins and a lit heart
        blk(7, 7, 24, 24, hx(0x2f3a3c))
        for k in range(5):
            for s in (5, 26):
                c.fill(9 + k * 3, s - 1 if s == 5 else s, 9 + k * 3, s if s == 5 else s + 1, brass)
                c.fill(s - 1 if s == 5 else s, 9 + k * 3, s if s == 5 else s + 1, 9 + k * 3, brass)
        c.fill(11, 11, 20, 20, INK)
        glow(12, 12, 19, 19, core)
        c.set(13, 13, (255, 255, 255))
    return c


def make_gear():
    c = tf.make_gear()
    out = Image(c.w, c.h)
    for y in range(c.h):
        for x in range(c.w):
            col = c.get(x, y)
            if col is not None:
                out.set(x, y, (col[0], col[1], col[2], 255))
    return out


def make_parts():
    out = Image(PART * 8, PART)
    for part in range(8):
        c = part_art(part)
        for y in range(PART):
            for x in range(PART):
                col = c.get(x, y)
                if col is not None:
                    out.set(part * PART + x, y, (col[0], col[1], col[2], 255))
    return out


def main(argv):
    target = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1] / 'assets'
    for name, art in [('train', make_train()), ('train_interior', make_interior()),
                      ('experimental_parts', make_parts()), ('train_gear', make_gear())]:
        path = target / f'sprites/terrain/{name}.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        art.save(path)
        print(name, art.width, art.height)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
