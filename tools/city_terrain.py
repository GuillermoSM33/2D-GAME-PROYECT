"""The second route's pieces that live in tools/make_terrain.py's sheets.

make_terrain.py appends these after the first route's frames, which stay as
they were: three city barricades, four city fronts for walls, the steel
shutter and the train's jammed coupling for their doors, eight buildings for
the background strip and the burning drum for the rest stop. Drawn with
make_terrain's Frame, palettes and outline, so they match.
"""
from __future__ import annotations

import math

from make_city import drum_fire
from make_sprites import Image, rgb
from make_terrain import (BG_PAL, BONE, BRASS, IRON, OUTLINE, RED, ROAD_PAL, SAND, Frame, sandbag)

CAR_PAINT = [rgb(0x24302e), rgb(0x34463e), rgb(0x4a5e50), rgb(0x6a7c66)]
GLASS = [rgb(0x1a2a36), rgb(0x2c4656), rgb(0x5a7a8a)]
CONCRETE = [rgb(0x4a4642), rgb(0x6a645c), rgb(0x8a8278), rgb(0xa49c90), rgb(0xbcb4a6)]
BRICK = [rgb(0x3e1e18), rgb(0x5a2a1e), rgb(0x763626), rgb(0x8e4630), rgb(0xa85a3c)]
OLIVE = [rgb(0x2a2c1c), rgb(0x3e4228), rgb(0x565c36), rgb(0x707848)]
BLUE = [rgb(0x182440), rgb(0x24386a), rgb(0x3a5aa0)]


# ---- Barricades (68 x 36, ground on row 25, built up to row -10) ---------------

def wheel(f: Frame, cx: int, cy: int, r: float, flat: bool) -> None:
    for y in range(cy - int(r) - 1, cy + int(r) + 2):
        for x in range(cx - int(r) - 1, cx + int(r) + 2):
            d = math.hypot(x - cx, (y - cy) * (1.4 if flat and y > cy else 1))
            if d <= r:
                f.px(x, y, IRON[3] if d < r * .35 else IRON[1] if d < r * .7 else IRON[0])


def sawhorse(f: Frame, x0: int, w: int, top: int, state: int) -> None:
    """A police sawhorse: a striped board on two A-legs."""
    tilt = 0 if state == 0 else 2
    for x in range(x0, x0 + w):
        y = top + (tilt * (x - x0)) // w
        for d in range(4):
            stripe = ((x - x0) + d) // 4 % 2
            f.px(x, y + d, BLUE[2] if stripe else BONE[2])
        f.px(x, y + 4, BLUE[0])
    for lx in (x0 + 3, x0 + w - 4):
        for i in range(25 - top - 4):
            f.px(lx - i // 4, top + 5 + i, IRON[2])
            f.px(lx + i // 4, top + 5 + i, IRON[3])


def cone(f: Frame, cx: int, base: int) -> None:
    for y in range(base - 9, base):
        half = (y - base + 10) // 2
        for x in range(cx - half, cx + half + 1):
            band = y in (base - 6, base - 5)
            f.px(x, y, BONE[2] if band else rgb(0xe0602a) if x < cx else rgb(0xb84418))
    f.fill(cx - 4, base, cx + 4, base, rgb(0x8a3010))


def barricade_police(f: Frame, state: int) -> None:
    """Police barricade: two striped sawhorses, one over the other, a lamp
    on top and cones at the foot; knocked over at last."""
    if state == 2:
        for x in range(4, 64):
            for d in range(3):
                f.px(x, 21 + d, BLUE[2] if (x + d) // 4 % 2 else BONE[2])
        for x in range(10, 60, 9):
            f.fill(x, 18, x + 1, 20, IRON[2])
        cone(f, 60, 25)
        return
    sawhorse(f, 4, 60, 6, state)
    sawhorse(f, 8, 52, -6, state)
    f.fill(30, -10, 35, -7, rgb(0xd0a030) if state == 0 else IRON[1])   # Warning lamp
    f.fill(31, -9, 34, -9, rgb(0xffe080) if state == 0 else IRON[2])
    cone(f, 7, 25)
    if state == 0:
        cone(f, 61, 25)


def barricade_military(f: Frame, state: int) -> None:
    """Army barricade: a concrete jersey barrier, sandbags heaped on it and
    razor wire on top; cracked; broken in two."""
    if state == 2:
        for x0, w in ((2, 26), (40, 26)):
            for y in range(14, 26):
                inset = 2 if y < 18 else 0
                f.fill(x0 + inset, y, x0 + w - inset, y, CONCRETE[2] if y < 17 else CONCRETE[1])
        for i, x in enumerate(range(26, 44, 6)):
            sandbag(f, x, 20 + i % 2, 7, 5)
        return
    for y in range(6, 26):                                # The jersey barrier
        inset = 6 if y < 14 else 6 - (y - 14) // 2
        for x in range(2 + max(0, inset), 66 - max(0, inset)):
            c = CONCRETE[3] if y == 6 else CONCRETE[2] if x < 34 else CONCRETE[1]
            if (x * 5 + y * 3) % 23 == 0:
                c = CONCRETE[0]
            f.px(x, y, c)
    for x in range(10, 58, 6):                            # Its stencilled stripe, worn
        f.fill(x, 16, x + 2, 17, rgb(0xb89030))
    for row, (y, n, off) in enumerate(((1, 6, 6), (-4, 5, 10))):
        for i in range(n):
            sandbag(f, off + i * 9, y, 9, 6)
            f.fill(off + i * 9 + 2, y + 5, off + i * 9 + 6, y + 5, SAND[0])
    for x in range(10, 58):                               # Razor wire coil
        y = -9 + round(2 * math.sin(x * .9))
        f.px(x, y, IRON[4] if x % 3 else IRON[2])
        if x % 4 == 0:
            f.px(x, y + 2, IRON[3])
    if state == 1:
        for y in range(8, 25):                            # A crack down it
            f.px(33 + (y // 3) % 2, y, OUTLINE)
        f.fill(42, 10, 46, 13, CONCRETE[0])


def motorcycle(f: Frame, ox: int, base: int, paint: list, lean: int = 0, dead: bool = False,
               kind: int = 0) -> None:
    """A motorcycle at her scale, side on, facing right, its wheels on row
    base (2 m long, the bars at her chest): spoked wheels, engine and
    exhaust, tank, seat, rear fender, forks, bars and headlamp. lean tips it
    toward the viewer (its top slides right). kind 0 a street bike; 1 a
    chopper (long raked forks, high bars, a sissy bar); 2 a dirt bike (high
    fenders, a flat seat up high, a number plate)."""
    front = 60 if kind == 1 else 55
    def px(x: int, y: int, c) -> None:
        f.px(ox + x + (base - y) * lean // 24, y, c)

    for wx in (11, front):                                # Wheels
        for yy in range(-10, 11):
            for xx in range(-10, 11):
                d = math.hypot(xx, yy)
                if d <= 10.3:
                    spoke = d < 7 and (abs(xx) < 1 or abs(yy) < 1 or abs(abs(xx) - abs(yy)) < 1)
                    c = IRON[0] if d > 7 else IRON[3] if d < 2 or spoke else (0, 0, 0, 0)
                    if c[3]:
                        px(wx + xx, base - 10 + yy, c)
    for x in range(22, 44):                               # Engine and gearbox
        for y in range(base - 19, base - 6):
            if x + (base - y) > 26:
                px(x, y, IRON[3] if (x + y) % 4 == 0 else IRON[2] if y < base - 12 else IRON[1])
    for x in range(26, 34, 2):                            # Cooling fins
        px(x, base - 20, IRON[4])
    for x in range(4, 32):                                # Exhaust
        px(x, base - 5, IRON[4] if x < 26 else IRON[2])
        px(x, base - 4, IRON[1])
    for x in range(26, 48):                               # Tank
        for y in range(base - 29, base - 20):
            if (x - 37) ** 2 / 121 + (y - (base - 24)) ** 2 / 25 <= 1.0:
                px(x, y, paint[3] if y < base - 26 else paint[2] if y < base - 22 else paint[1])
    for x in range(8, 28):                                # Seat, rear fender
        px(x, base - 26, OUTLINE)
        px(x, base - 25, IRON[1])
        px(x, base - 24, IRON[1] if x > 12 else paint[1])
    for i in range(9):
        px(3 + i, base - 22 + i // 3, paint[2])
    px(2, base - 21, RED[3] if not dead else IRON[1])     # Tail light
    rake = 18 if kind == 1 else 9
    for i in range(24):                                   # Forks, raked
        px(front - i * rake // 24, base - 10 - i, IRON[4])
        px(front + 1 - i * rake // 24, base - 10 - i, IRON[2])
    if kind == 1:                                         # High bars, a sissy bar behind the seat
        for i in range(8):
            px(41, base - 34 - i, IRON[4])
            px(6, base - 26 - i, IRON[3])
        for x in range(36, 43):
            px(x, base - 42, IRON[3])
    if kind == 2:                                         # High fenders, a number plate
        for x in range(front - 12, front + 4):
            px(x, base - 23, paint[3])
        for x in range(2, 16):
            px(x, base - 30, paint[3])
        for y in range(base - 33, base - 27):
            for x in range(44, 49):
                px(x, y, BONE[2])
        for x in range(10, 36):
            px(x, base - 29, OUTLINE)
            px(x, base - 28, IRON[1])
    for x in range(40, 50):                               # Bars, a mirror
        px(x, base - 35, IRON[3])
    px(40, base - 36, IRON[4])
    px(39, base - 38, IRON[2])
    for y in range(base - 32, base - 26):                 # Headlamp
        for x in range(49, 54):
            px(x, y, BONE[2] if not dead and x > 51 else IRON[2])


def barricade_motos(f: Frame, state: int, kind: int = 0) -> None:
    """A motorcycle chained across the road, another dropped on its side in
    front of it; knocked half over, holed; both flat and burnt (it blew up).
    kind: a red street bike, a black chopper, a yellow dirt bike."""
    red = [[rgb(0x4a1612), rgb(0x74231a), rgb(0x9c3424), rgb(0xc24e32)],
           [rgb(0x101014), rgb(0x1e1e24), rgb(0x30303a), rgb(0x4a4a56)],
           [rgb(0x5a4410), rgb(0x8a6a18), rgb(0xc09a24), rgb(0xe8c84a)]][kind]
    blue = [[rgb(0x182440), rgb(0x24386a), rgb(0x3a5aa0), rgb(0x5a7ac0)],
            [rgb(0x3a1414), rgb(0x5a1e1c), rgb(0x7c2c26), rgb(0xa04436)],
            [rgb(0x1c2a26), rgb(0x2c4038), rgb(0x40584a), rgb(0x5c7660)]][kind]
    if state == 2:
        red = blue = [rgb(0x141210), rgb(0x241e1a), rgb(0x3a2e26), rgb(0x54402e)]

    def fallen(x0: int, paint: list) -> None:             # Seen from above its side, on the road
        for x in range(x0, x0 + 56):
            f.px(x, 22, IRON[2] if x % 6 else IRON[4])
            f.px(x, 23, IRON[1])
        f.fill(x0 + 20, 19, x0 + 38, 21, paint[2])
        f.fill(x0 + 20, 19, x0 + 38, 19, paint[3])
        for wx in (x0 + 6, x0 + 50):
            f.fill(wx - 6, 20, wx + 6, 24, IRON[0])
            f.fill(wx - 2, 21, wx + 2, 22, IRON[3])

    if state == 2:
        fallen(2, red)
        fallen(10, blue)
        for x in range(20, 44, 4):
            f.px(x, 17 + x % 3, IRON[2])                  # A bent bar sticking up
        return
    motorcycle(f, 1 if kind != 1 else 0, 25, red, 0 if state == 0 else 7, state == 1, kind)
    fallen(8, blue)
    if state == 0:
        for i in range(44):                               # The chain to a post, a padlock
            f.px(10 + i, 12 + round(3 * math.sin(i * .15)), IRON[4] if i % 2 else IRON[2])
        f.fill(30, 15, 33, 18, BRASS[1])
    else:
        for y in range(-2, 6):
            f.px(44 + y // 2, y, OUTLINE)                 # Cracked: its bars twisted


def barricade_motos_2(f: Frame, state: int) -> None:
    barricade_motos(f, state, 1)


def barricade_motos_3(f: Frame, state: int) -> None:
    barricade_motos(f, state, 2)


# After the first route's four in the sheet: police, army and the three
# motorcycles. The cars that are barricades are not here: a car at her scale
# is twice a cell's width, so they have their own sheet (terrain/car_wreck).
URBAN_BARRICADES = [barricade_police, barricade_military, barricade_motos, barricade_motos_2, barricade_motos_3]


def make_urban_doors(w: int, h: int) -> Image:
    """Two more doors, 3 frames each (whole, cracked, blown): a steel roller
    shutter, padlocked at its foot; and the train's coupling, jammed shut
    with crumpled sheet steel, crates and a chain."""
    img = Image(w * 6, h)
    for frame in range(3):                                 # The shutter
        f = Frame(img, frame * w, w)
        if frame < 2:
            for y in range(1, h):
                for x in range(1, w - 1):
                    slat = y % 4
                    c = IRON[3] if slat == 0 else IRON[2] if slat < 3 else IRON[1]
                    if (x * 3 + y * 7) % 31 == 0:
                        c = rgb(0x6a3a1e)
                    f.px(x, y, c)
            f.fill(0, 0, w - 1, 2, IRON[1])                # Its box at the top
            f.fill(w // 2 - 3, h - 8, w // 2 + 2, h - 2, BRASS[1])   # Padlock at the foot
            f.fill(w // 2 - 2, h - 10, w // 2 + 1, h - 9, IRON[3])
            if frame == 1:                                 # Bowed in, a hole torn
                for y in range(20, 44):
                    f.px(12 + (y // 5) % 3, y, OUTLINE)
                f.fill(26, 18, 33, 26, OUTLINE)
        else:                                              # Torn off: a rolled lip, sheets on the ground
            f.fill(1, 0, w - 2, 6, IRON[2])
            for x in range(1, w - 1, 3):
                f.fill(x, 7, x, 7 + (x * 7) % 9, IRON[1])
            for i in range(4):
                f.fill(3 + i * 10, h - 3 - i % 2, 11 + i * 10, h - 1, IRON[2 + i % 2])
        f.outline()
    for frame in range(3):                                 # The jammed coupling
        f = Frame(img, (3 + frame) * w, w)
        if frame < 2:
            for y in range(4, h):                          # Crumpled sheet steel, rust
                for x in range(1, w - 1):
                    k = (x + y // 3) % 7
                    c = [rgb(0x5a2e1e), rgb(0x7a4028), rgb(0x3a1e16)][k % 3]
                    if (x * 5 + y) % 17 == 0:
                        c = IRON[2]
                    f.px(x, y, c)
            for x in range(0, w):                          # A torn top edge
                f.fill(x, 4 - (x * 7) % 4, x, 4, rgb(0x7a4028))
            f.box(4, h - 22, 19, h - 6, IRON[1:4])         # Coupler knuckles locked
            f.box(24, h - 20, 39, h - 6, IRON[1:4])
            for i in range(12):                            # A chain across
                f.px(3 + i * 3, 26 + (i % 2), IRON[4])
                f.px(4 + i * 3, 26 + (i % 2), IRON[2])
            if frame == 1:
                f.fill(14, 10, 28, 20, OUTLINE)
                for y in range(30, 50):
                    f.px(20 + (y // 4) % 2, y, OUTLINE)
        else:                                              # Blown apart: scraps on the rail
            for i in range(5):
                f.fill(2 + i * 8, h - 4 + (i % 2), 8 + i * 8, h - 1, rgb(0x5a2e1e) if i % 2 else IRON[2])
            f.fill(2, 0, 7, 10, rgb(0x3a1e16))
            f.fill(w - 8, 0, w - 3, 14, rgb(0x3a1e16))
        f.outline()
    return img


# ---- Buildings off the road (80 x 64, BG_PAL: recoloured per theme) ----------

def h_billboard(f: Frame, w: int, h: int, pal: dict) -> None:
    b = h - 1
    f.fill(8, 14, w - 9, 40, pal['wood'][2])
    f.fill(10, 16, w - 11, 38, pal['wood'][4])
    f.fill(14, 20, 40, 34, pal['wood'][1])                 # Its picture, peeling
    for x in range(44, w - 14, 3):
        f.fill(x, 22, x + 1, 32, pal['wood'][3])
    for lx in (18, w - 20):
        f.fill(lx, 41, lx + 2, b, pal['metal'][1])
    f.fill(10, 41, w - 11, 42, pal['metal'][0])            # Catwalk


def h_gas_station(f: Frame, w: int, h: int, pal: dict) -> None:
    b = h - 1
    f.fill(2, 22, w - 3, 26, pal['paint'][3])              # Canopy
    f.fill(2, 27, w - 3, 27, pal['wood'][0])
    for px_ in (10, w - 12):
        f.fill(px_, 28, px_ + 2, b, pal['metal'][1])
    for px_ in (28, 46):                                    # Pumps
        f.fill(px_, 42, px_ + 6, b, pal['paint'][1])
        f.fill(px_ + 1, 44, px_ + 5, 47, pal['hole'])
    f.fill(w - 10, 4, w - 8, 21, pal['metal'][1])          # Price sign pole
    f.fill(w - 16, 4, w - 2, 12, pal['paint'][2])


def h_shop_row(f: Frame, w: int, h: int, pal: dict) -> None:
    b = h - 1
    for i, x0 in enumerate((2, 28, 54)):
        top = 26 + (i % 2) * 4
        f.fill(x0, top, x0 + 24, b, pal['paint'][1 + i % 3])
        f.fill(x0, top, x0 + 24, top + 1, pal['wood'][5])
        f.fill(x0 + 3, b - 14, x0 + 15, b - 4, pal['glow'][1] if i == 1 else pal['hole'])
        f.fill(x0 + 18, b - 16, x0 + 22, b, pal['wood'][1])
        f.fill(x0 + 1, b - 18, x0 + 23, b - 17, pal['wood'][4])


def h_apartment(f: Frame, w: int, h: int, pal: dict) -> None:
    b = h - 1
    f.fill(12, 4, w - 13, b, pal['paint'][1])
    f.fill(12, 4, w - 13, 5, pal['paint'][3])
    for y in range(9, b - 6, 8):
        for x in range(16, w - 16, 9):
            lit = (x * 3 + y) % 5 == 0
            f.fill(x, y, x + 4, y + 4, pal['glow'][1] if lit else pal['hole'])
    f.fill(w // 2 - 4, b - 8, w // 2 + 3, b, pal['wood'][1])


def h_warehouse(f: Frame, w: int, h: int, pal: dict) -> None:
    b = h - 1
    for x in range(2, w - 2):                              # Saw-tooth roof
        f.fill(x, 24 - (x % 16) // 3, x, b, pal['metal'][1] if x % 16 < 12 else pal['metal'][0])
    f.fill(2, 24, w - 3, b, pal['paint'][0])
    for x0 in (10, 44):
        f.fill(x0, 38, x0 + 22, b, pal['metal'][2])
        for y in range(38, b, 3):
            f.fill(x0, y, x0 + 22, y, pal['metal'][0])
    for x in range(6, w - 6, 8):
        f.fill(x, 28, x + 4, 31, pal['hole'])


def h_hangar(f: Frame, w: int, h: int, pal: dict) -> None:
    b = h - 1
    for i in range(w - 4):
        top = b - round(38 * math.sin(math.pi * i / (w - 5)))
        for y in range(top, b + 1):
            f.px(2 + i, y, pal['metal'][2] if (i // 6) % 2 else pal['metal'][1])
        f.px(2 + i, top, pal['paint'][3])
    f.fill(20, b - 20, w - 21, b, pal['hole'])             # Its open door
    f.fill(20, b - 20, w - 21, b - 20, pal['metal'][0])


def h_watchtower(f: Frame, w: int, h: int, pal: dict) -> None:
    b = h - 1
    cx = w // 2
    f.fill(cx - 12, 4, cx + 12, 16, pal['wood'][2])
    f.fill(cx - 14, 2, cx + 14, 4, pal['wood'][4])
    f.fill(cx - 9, 7, cx + 9, 11, pal['hole'])
    f.fill(cx + 4, 8, cx + 7, 9, pal['glow'][2])           # Its searchlight
    for i in range(b - 17):
        f.px(cx - 10 + i // 8, 17 + i, pal['wood'][1])
        f.px(cx + 10 - i // 8, 17 + i, pal['wood'][1])
    for y in range(22, b, 10):
        f.fill(cx - 9, y, cx + 9, y, pal['wood'][1])


def h_radar(f: Frame, w: int, h: int, pal: dict) -> None:
    b = h - 1
    cx = w // 2
    f.fill(cx - 14, b - 14, cx + 14, b, pal['paint'][1])   # Its shed
    f.fill(cx - 14, b - 14, cx + 14, b - 13, pal['paint'][3])
    f.fill(cx - 1, 22, cx + 1, b - 15, pal['metal'][1])
    for i in range(-18, 19):                               # The dish, tilted up
        y = 14 + (i * i) // 22
        f.fill(cx + i, y - 1, cx + i, y + 1, pal['metal'][2])
    f.fill(cx, 4, cx, 14, pal['metal'][1])


URBAN_HOUSES = [h_billboard, h_gas_station, h_shop_row, h_apartment, h_warehouse, h_hangar, h_watchtower,
                h_radar]


def make_urban_houses() -> Image:
    img = Image(80 * len(URBAN_HOUSES), 64)
    for i, draw in enumerate(URBAN_HOUSES):
        f = Frame(img, i * 80, 80)
        draw(f, 80, 64, BG_PAL)
        f.outline()
    return img


def make_campfire_barrel(w: int, h: int, oy: int) -> Image:
    """The rest stop's fire in the city: a burning drum on flat stones (4
    frames, the campfire's size), like the ones people warm their hands at."""
    img = Image(w * 4, h)
    for frame in range(4):
        f = Frame(img, frame * w, w)
        drum_fire(f, frame, h - 1, w // 2, True)
        f.outline()
    return img
