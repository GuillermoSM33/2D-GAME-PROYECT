"""Construct the road's vehicles and field equipment in native pixel art.

finish(name, image) adds shaped body panels, cabin interiors, running gear,
canvas construction and machinery to the scenery pass. Frames and gameplay
anchors stay unchanged. No light cone is painted into a sprite.

Run this file to write comparison sheets under build/, without changing assets.
Only the standard library is required.
"""
from __future__ import annotations

import math
from pathlib import Path

from make_sprites import Image, rgb
from scenery_materials import FONT

WIDTHS = {'vehicles': 184, 'car_wreck': 136, 'siren_car': 136,
          'supply_truck': 184, 'train': 300, 'outpost': 168,
          'burner': 40, 'hydrant': 20}
INK, STEEL, EDGE = 0x18191c, 0x60656b, 0xa7aaa6
FLAMES = {(255, 246, 220), (255, 210, 60), (240, 138, 36), (200, 74, 20)}


def color(value):
    return rgb(value) if isinstance(value, int) else value


def shade(value: int, amount: float) -> int:
    c = rgb(value)
    return sum(max(0, min(255, round(c[k] * amount))) << (16 - 8 * k) for k in range(3))


class Draw:
    def __init__(self, image: Image, frame: int, width: int, ox: int = 0):
        self.image, self.frame, self.w, self.ox = image, frame, width, ox

    def get(self, x: int, y: int):
        x += self.ox
        return self.image.get(self.frame * self.w + x, y) if 0 <= x < self.w else (0, 0, 0, 0)

    def p(self, x: int, y: int, value, flame_safe: bool = False):
        x += self.ox
        if 0 <= x < self.w and 0 <= y < self.image.height:
            if flame_safe and self.image.get(self.frame * self.w + x, y)[:3] in FLAMES:
                return
            self.image.set(self.frame * self.w + x, y, color(value))

    def box(self, x0: int, y0: int, x1: int, y1: int, value):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.p(x, y, value)

    def line(self, x0: int, y0: int, x1: int, y1: int, value):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.p(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), value)

    def poly(self, points: list, value):
        for y in range(math.floor(min(p[1] for p in points)), math.ceil(max(p[1] for p in points)) + 1):
            crosses = []
            for i, (xa, ya) in enumerate(points):
                xb, yb = points[(i + 1) % len(points)]
                if min(ya, yb) <= y < max(ya, yb):
                    crosses.append(xa + (y - ya) * (xb - xa) / (yb - ya))
            crosses.sort()
            for xa, xb in zip(crosses[::2], crosses[1::2]):
                self.box(math.ceil(xa), y, math.floor(xb), y, value)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, value):
        for y in range(math.floor(cy - ry), math.ceil(cy + ry) + 1):
            for x in range(math.floor(cx - rx), math.ceil(cx + rx) + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    self.p(x, y, value)

    def bolt(self, x: int, y: int, light: int = EDGE):
        self.p(x, y, INK)
        self.p(x - 1, y - 1, light)

    def text(self, text: str, x0: int, y0: int, value):
        for i, char in enumerate(text):
            for y, row in enumerate(FONT.get(char, ('000',) * 5)):
                for x, bit in enumerate(row):
                    if bit == '1':
                        self.p(x0 + i * 4 + x, y0 + y, value)


def tyre(d: Draw, cx: int, cy: int, radius: float, bare: bool = False, heavy: bool = False):
    """Rounded rubber, tread shoulders, deep rim, ventilation and a bolted hub."""
    d.ellipse(cx, cy, radius + .8, radius + .5, 0x111115)
    for y in range(math.floor(cy - radius), math.ceil(cy + radius) + 1):
        for x in range(math.floor(cx - radius), math.ceil(cx + radius) + 1):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            if r > radius:
                continue
            if bare:
                value = 0x66584c if r < radius * .7 else 0x302d2b
            elif r > radius * .71:
                value = 0x3b3c3e if dx < 0 and dy < 0 else 0x292a2d if dy < 1 else 0x17181c
                sector = round(math.atan2(dy, dx) * (9 if heavy else 7) / math.pi)
                if sector % 2 == 0 and r > radius * .85:
                    value = 0x131419
            else:
                value = 0x3e4146 if r > radius * .53 else 0x8a8a83 if dy < 0 else 0x62646a
            d.p(x, y, value)
    ring = radius * .52
    for k in range(6 if not heavy else 8):
        a = k * math.tau / (8 if heavy else 6)
        x, y = cx + round(ring * .67 * math.cos(a)), cy + round(ring * .67 * math.sin(a))
        d.p(x, y, 0x22252a)
        if radius > 9:
            d.p(x + 1, y, 0x33373b)
    d.ellipse(cx, cy, max(1, radius * .17), max(1, radius * .17), 0x36393b)
    d.p(cx - 1, cy - 1, 0xb7b2a4)
    d.p(cx, cy, 0x70757a)
    d.p(cx + 1, cy + 1, 0x24282c)


def pressed_panel(d: Draw, x0: int, y0: int, x1: int, y1: int, paint: int, crease: int = 0):
    """The side is curved stamped steel, with a recessed joint and lower lip."""
    if x1 <= x0 or y1 <= y0:
        return
    d.box(x0, y0, x1, y1, shade(paint, .76))
    d.poly([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x1 - 2, y1 - 3),
            (x0 + 2, y1 - 2)], paint)
    d.line(x0 + 1, y0 + 1, x1 - 1, y0 + 1, shade(paint, 1.27))
    d.line(x0 + 2, y0 + 2, x1 - 2, y0 + 2, shade(paint, 1.08))
    d.line(x0 + 2, y1 - 3, x1 - 2, y1 - 4, shade(paint, .57))
    d.line(x1, y0, x1, y1, 0x1b2022)
    d.line(x1 - 1, y0 + 2, x1 - 1, y1 - 1, shade(paint, .54))
    if crease:
        d.poly([(x0 + 4, y0 + 6), (x1 - 4, y0 + 3), (x1 - 8, y0 + 8),
                (x0 + 5, y0 + 8)], shade(paint, .51))
        d.line(x0 + 5, y0 + 5, x1 - 4, y0 + 3, shade(paint, 1.13))


def pane(d: Draw, points: list, broken: bool = False, seat: bool = True):
    """A glass plane with interior volume, a dashboard and restrained reflection."""
    x0, x1 = min(p[0] for p in points), max(p[0] for p in points)
    y0, y1 = min(p[1] for p in points), max(p[1] for p in points)
    # A mask keeps seats, reflections and damage inside the angled pane.
    pixels = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            odd = False
            for i, (xa, ya) in enumerate(points):
                xb, yb = points[(i + 1) % len(points)]
                if (ya > y) != (yb > y) and x < xa + (y - ya) * (xb - xa) / (yb - ya):
                    odd = not odd
            if odd:
                pixels.append((x, y))
    occupied = set(pixels)
    for x, y in pixels:
        t = (y - y0) / max(1, y1 - y0)
        value = 0x435958 if t < .2 else 0x2c4144 if t < .5 else 0x1b2b30
        if seat and x0 + 3 <= x <= x0 + 7 and y > y0 + 4:
            value = 0x252b2d if x < x0 + 6 else 0x3c3c36
        if y == y1 - 1:
            value = 0x131e22
        if not broken and y < y0 + 4 and x < x0 + (x1 - x0) * .65:
            value = 0x648080
        d.p(x, y, value)
    if broken:
        cx = (x0 + x1) // 2
        for y in range(y0 + 1, y1):
            x = cx + (y - y0) // 3 - (2 if y > y0 + 5 else 0)
            for dx in range(-2, 3 + (y % 2)):
                if (x + dx, y) in occupied:
                    d.p(x + dx, y, 0x111c20)
            if (x - 3, y) in occupied:
                d.p(x - 3, y, 0x8a9d96)
        for x, y in ((x1 - 2, y0 + 2), (x0 + 1, y1 - 2), (cx - 2, y0 + 1)):
            if (x, y) in occupied:
                d.p(x, y, 0x9bafa6)


def sedan(d: Draw, base: int, paint: int, state: int = 0, shape: str = 'sedan', police: bool = False):
    sag = 0 if state == 0 else 1 if state == 1 else 4
    roof, belt, sill = base - 45 + sag, base - 29 + sag, base - 8
    # The existing silhouette supplies the fenders, roof and different bodies.
    # New panels are individually stamped rather than a textured rectangle.
    door_color = 0xa6aba3 if police else paint
    pressed_panel(d, 45, belt + 2, 62, sill - 1, door_color, state > 0)
    pressed_panel(d, 65, belt + 2, 92, sill - 1, door_color, state > 0)
    d.line(7, belt + 3, 129, belt + 3, shade(paint, 1.21))
    d.line(8, belt + 4, 127, belt + 4, shade(paint, .62))
    d.line(39, sill, 96, sill, 0x151a1c)
    d.line(41, sill - 1, 95, sill - 1, shade(paint, 1.1))
    for x in (51, 72):
        d.box(x - 1, belt + 6, x + 5, belt + 7, 0x252b2c)
        d.line(x, belt + 6, x + 4, belt + 6, 0xa3a49b if state < 2 else 0x61564a)
        d.p(x, belt + 9, 0x25292b)
    # Window shapes follow the roof, including the pickup's short cabin.
    rear0, rear1 = {'sedan': (26, 44), 'wagon': (6, 14), 'pickup': (58, 62)}[shape]
    if shape != 'pickup':
        pane(d, [(rear0 + 7, belt - 3), (rear1 + 2, roof + 3), (60, roof + 3), (60, belt - 2)], state > 0)
    pane(d, [(66, roof + 3), (79, roof + 3), (93, belt - 2), (66, belt - 2)], state > 0)
    # A recessed sill, chrome edge, wiper, wing mirror and small vent window.
    d.line(rear0 + 7, belt - 1, 94, belt - 1, 0x82918a if state < 2 else 0x554b40)
    d.line(84, belt - 2, 89, belt - 6, 0x151f23)
    d.line(95, belt - 2, 98, belt - 4, 0x353c3b)
    d.box(97, belt - 5, 101, belt - 3, 0x1d2427)
    d.line(98, belt - 5, 100, belt - 5, 0x8d9b96)
    # The broad hood has a top plane and an inset lid, with a folded front lip.
    if state < 2:
        d.poly([(99, belt + 1), (124, belt + 3), (130, belt + 5), (100, belt + 4)], shade(paint, 1.22))
        d.line(102, belt + 4, 127, belt + 5, shade(paint, .6))
        for x in range(106, 120, 3):
            d.line(x, belt + 2, x + 1, belt + 2, shade(paint, .52))
        d.box(128, belt + 8, 133, belt + 11, 0xb5ab88 if state == 0 else 0x655c49)
        d.p(129, belt + 8, 0xeee1b4 if state == 0 else 0xa59b7d)
        d.line(129, belt + 12, 133, belt + 12, 0x24282a)
        for y in (belt + 5, belt + 7):
            d.line(131, y, 134, y, 0x232b2a)
    else:
        # A sprung hood exposes the radiator, belt, block and loose hose.
        d.box(99, belt + 2, 126, sill - 1, 0x171b1d)
        d.poly([(99, belt + 1), (119, belt - 11), (125, belt - 9), (109, belt + 2)], 0x574b3b)
        d.line(101, belt, 120, belt - 10, 0x85725b)
        d.line(105, belt + 1, 123, belt - 8, 0x2b2925)
        d.box(102, belt + 5, 115, sill - 3, 0x3a3e3f)
        for x in range(103, 116, 3):
            d.line(x, belt + 5, x, sill - 3, 0x777970)
        d.box(120, belt + 4, 126, sill - 2, 0x272c2d)
        for x in (121, 123, 125):
            d.line(x, belt + 5, x, sill - 3, 0x60665f)
        d.line(110, belt + 3, 118, belt + 8, 0x8a6748)
        d.line(117, belt + 8, 120, belt + 6, 0x191c1d)
        d.poly([(49, belt + 8), (58, belt + 6), (60, sill - 3), (50, sill - 1)], 0x171d1e)
        d.line(50, belt + 8, 54, belt + 7, 0x837258)
    # Curved metal wheel arch lips and suspension, with meaningful tread.
    for cx in (28, 108):
        cy, radius = (base - 5, 5.2) if state == 2 else (base - 8, 8.1)
        for k in range(20):
            a = math.pi + k * math.pi / 19
            x, y = cx + round(11 * math.cos(a)), base - 8 + round(11 * math.sin(a))
            if y >= belt + 5:
                d.p(x, y, shade(paint, .48))
                d.p(x, y - 1, shade(paint, 1.08))
        tyre(d, cx, cy, radius, state == 2)
    if state == 1:
        # The crushed near corner and diagonal crease are structural damage.
        d.line(113, belt + 5, 123, belt + 9, 0x302921)
        d.line(112, belt + 4, 124, belt + 8, shade(paint, 1.15))
    # Broken paint along the lower sill appears in coherent chips, not noise.
    for x, y, length in ((47, sill - 3, 6), (82, sill - 4, 8), (13, belt + 9, 5)):
        d.line(x, y, x + length, y, 0x8a6546 if state > 0 else shade(paint, .56))
        d.line(x + 2, y + 1, x + length - 1, y + 1, 0x3c342b)


def jeep(d: Draw, base: int):
    paint, belt, floor = 0x5c6544, base - 38, base - 13
    for x0, x1 in ((37, 62), (65, 97)):
        pressed_panel(d, x0, belt + 1, x1, floor - 2, paint)
        d.poly([(x0 + 4, belt + 8), (x1 - 4, belt + 8), (x1 - 6, floor - 6),
                (x0 + 6, floor - 6)], 0x48543b)
        d.line(x0 + 4, belt + 8, x1 - 4, belt + 8, 0x84906a)
        d.box(x0 + 5, belt + 4, x0 + 10, belt + 5, 0x222a26)
        d.line(x0 + 6, belt + 4, x0 + 10, belt + 4, 0x9a9e87)
        for y in (belt + 3, floor - 5):
            d.bolt(x0, y, 0x909174)
    pane(d, [(37, base - 56), (60, base - 56), (60, belt - 3), (37, belt - 3)])
    pane(d, [(66, base - 56), (88, base - 56), (96, belt - 3), (66, belt - 3)], True)
    d.line(85, belt - 3, 90, belt - 9, 0x1a2224)
    d.poly([(101, belt), (138, belt + 1), (143, belt + 4), (101, belt + 4)], 0x7a8358)
    for x in range(108, 136, 4):
        d.line(x, belt + 4, x + 1, belt + 6, 0x293426)
    d.box(141, belt + 5, 147, belt + 18, 0x222a25)
    for y in range(belt + 6, belt + 18, 3):
        d.line(142, y, 147, y, 0x737b63)
    d.box(141, belt + 20, 147, belt + 23, 0xb9b08a)
    d.p(142, belt + 20, 0xeee1b7)
    d.line(145, floor - 5, 150, floor - 3, 0x6f7566)
    for x in (7, 147):
        d.ellipse(x, floor - 1, 2, 2, 0x222b26)
        d.p(x, floor - 2, 0x858775)
    # Rear-mounted spare, canvas tool roll and the jerrycan's pressed cross.
    tyre(d, 9, belt + 4, 7.2, heavy=True)
    d.box(12, belt + 13, 21, belt + 24, 0x3c4b33)
    d.line(13, belt + 14, 20, belt + 23, 0x75815b)
    d.line(20, belt + 14, 13, belt + 23, 0x263724)
    d.box(13, belt + 12, 19, belt + 13, 0x89926c)
    d.line(17, belt + 13, 17, belt + 23, 0x293426)
    for cx in (32, 122):
        tyre(d, cx, base - 12, 12.1, heavy=True)
    # A small faded military stencil, kept at the same door as the source.
    for yy in range(-4, 5):
        for xx in range(-4, 5):
            if abs(xx) + abs(yy) <= 4:
                d.p(82 + xx, belt + 14 + yy, 0xc4c5aa if xx < 0 else 0xa4ad91)


def truck(d: Draw, base: int, load: int):
    top, bed, paint = base - 62, base - 22, 0x5a6542
    # Broad canvas sags between rigid hoops; an end flap and stitches give
    # the cover actual thickness instead of a striped rectangular panel.
    bottom = bed - 26 if load else bed - 1
    for x in range(5, 122):
        bay = (x - 5) // 22
        t = ((x - 5) % 22) / 21
        crest = top + 1 + round(2 * math.sin(math.pi * t))
        for y in range(crest, bottom + 1):
            across = (y - crest) / max(1, bottom - crest)
            value = 0x8d9271 if across < .12 else 0x707959 if t < .25 else 0x626b4b if t < .78 else 0x414c35
            if y > bottom - 3:
                value = 0x424b34 if t < .8 else 0x2c3728
            d.p(x, y, value)
        d.p(x, crest, 0xa1a581)
        if x % 3 == 0:
            d.p(x, bottom - 1, 0xaba488)
        if (x - 5) % 22 == 1:
            d.line(x, crest + 2, x, bottom - 2, 0x384530)
    for x in (8, 29, 51, 73, 95, 117):
        d.line(x, bottom - 2, x, bottom + 3, 0x302f25)
        d.line(x, bottom + 2, x + 2, bottom + 2, 0x9a9276)
    if not load:
        d.poly([(6, top + 4), (18, top + 6), (16, bed - 5), (7, bed - 2)], 0x4b563b)
        d.line(17, top + 6, 15, bed - 5, 0xa2a284)
        d.line(8, bed - 4, 15, bed - 6, 0x252e25)
    else:
        # Rolled canvas has an elliptical end and leather securing loops.
        d.box(7, bottom, 121, bottom + 3, 0x343e2c)
        d.line(9, bottom, 119, bottom, 0x939779)
        for x in (18, 62, 106):
            d.box(x, top + 2, x + 1, bottom + 4, 0x55442f)
            d.line(x, bottom + 2, x + 3, bottom + 2, 0x9d977b)
    # Pressed cargo-bed fascia, hinges and lower frame seen between wheels.
    d.box(4, bed, 124, bed + 5, 0x3d4933)
    d.line(5, bed, 123, bed, 0x8e9770)
    d.line(5, bed + 4, 123, bed + 4, 0x232f26)
    for x in range(12, 121, 27):
        d.box(x, bed + 1, x + 3, bed + 3, 0x6f7762)
        d.bolt(x + 1, bed + 2, 0xb0b19a)
    # Cab side, bonnet top plane, air intake, radiator and a boxed bumper.
    pressed_panel(d, 129, base - 33, 150, base - 15, paint)
    pane(d, [(133, base - 48), (147, base - 48), (147, base - 37), (133, base - 37)], False)
    d.line(133, base - 36, 148, base - 36, 0xa2aa8b)
    d.line(144, base - 38, 147, base - 43, 0x1f2a26)
    d.box(146, base - 33, 150, base - 32, 0x252f26)
    d.p(147, base - 33, 0xc0bfa0)
    d.poly([(153, base - 36), (173, base - 35), (176, base - 32), (153, base - 32)], 0x929b68)
    d.line(154, base - 31, 174, base - 31, 0x303d2b)
    d.box(169, base - 29, 174, base - 18, 0x1e2824)
    for y in range(base - 28, base - 17, 3):
        d.line(170, y, 174, y, 0x889078)
    d.box(174, base - 30, 177, base - 26, 0xbeb58c)
    d.p(174, base - 30, 0xf1dfad)
    d.box(172, base - 16, 180, base - 13, 0x3a4441)
    d.line(173, base - 16, 179, base - 16, 0x959b8c)
    # A proper mirror on a bent bracket, still inside the frame.
    d.line(151, base - 40, 155, base - 41, 0x394640)
    d.box(154, base - 45, 157, base - 40, 0x2b3532)
    d.line(154, base - 44, 154, base - 41, 0x9aa79f)
    for cx in (26, 50, 152):
        tyre(d, cx, base - 10, 10.1, heavy=True)
    for yy in range(-4, 5):
        for xx in range(-4, 5):
            if abs(xx) + abs(yy) <= 4:
                d.p(140 + xx, base - 26 + yy, 0xbec2a8 if xx < 0 else 0x929d83)


def train(d: Draw):
    # Boxcar: the ribbed wall has a weathered top flange, individual sheet
    # panels, riveted channel ribs, sliding door tracks and a maintenance step.
    for x in range(5, 125):
        lift = (128 - x) // 14
        top, bottom = 30 - lift, 89 - lift
        for y in range(top + 2, bottom - 1):
            rib = (x - 5) % 12
            value = 0x774a32 if rib < 7 else 0x59372a
            if rib == 0:
                value = 0xa16c43
            elif rib == 1:
                value = 0x442e26
            if y > bottom - 8:
                value = shade(value, .7)
            d.p(x, y, value)
        d.p(x, top + 1, 0xba8251)
        d.p(x, bottom - 1, 0x332c29)
        if (x - 5) % 12 in (0, 1):
            for y in range(top + 5, bottom - 5, 10):
                d.bolt(x, y, 0xa38a69)
    for x0 in (39, 75):
        d.box(x0, 39, x0 + 25, 82, 0x493229)
        d.box(x0 + 2, 42, x0 + 23, 79, 0x724a33)
        for x in range(x0 + 5, x0 + 22, 5):
            d.line(x, 43, x, 78, 0x4b352a)
            d.line(x + 1, 43, x + 1, 78, 0x99704a)
        d.line(x0 - 2, 37, x0 + 28, 37, 0x9f9d87)
        d.line(x0 - 2, 38, x0 + 28, 38, 0x323539)
        d.line(x0 + 4, 77, x0 + 20, 46, 0x49362c)
        d.line(x0 + 5, 77, x0 + 21, 46, 0x9a7050)
        d.box(x0 + 20, 58, x0 + 22, 64, 0x2b2b2c)
        d.line(x0 + 21, 59, x0 + 21, 63, 0xa29d87)
    for y in range(37, 78, 8):
        d.line(7, y, 16, y, 0x7e8077)
        d.line(7, y + 1, 16, y + 1, 0x36393b)
    d.box(21, 48, 33, 56, 0x453d30)
    d.text('07', 23, 50, 0xc4b596)
    # Locomotive: an upper hood plane, removable access hatches and deep
    # louver banks above the safety stripe; no drawing enters the door gap.
    d.poly([(175, 43), (236, 43), (242, 47), (175, 47)], 0x9a8b4e)
    d.box(176, 48, 238, 59, 0x4a4b31)
    for x0 in (178, 200, 222):
        d.box(x0, 49, x0 + 17, 59, 0x282e28)
        d.line(x0, 49, x0 + 17, 49, 0xb0aa82)
        for x in range(x0 + 2, x0 + 16, 3):
            d.line(x, 51, x, 57, 0x858773)
            d.line(x + 1, 51, x + 1, 58, 0x3b4136)
        d.bolt(x0 + 1, 58)
        d.bolt(x0 + 16, 58)
    for x0 in (177, 198, 219):
        pressed_panel(d, x0, 66, x0 + 18, 85, 0x615a32)
        d.box(x0 + 12, 69, x0 + 14, 73, 0x272d26)
        d.bolt(x0 + 3, 69, 0x8a896f)
    d.line(176, 61, 294, 61, 0xbb5139)
    d.line(176, 64, 294, 64, 0x572d26)
    # Cab has a framed pair of windows, steering wheel and one shattered pane.
    d.poly([(240, 20), (296, 20), (299, 24), (238, 24)], 0x9a8e59)
    pane(d, [(246, 27), (261, 27), (261, 40), (246, 40)], False)
    pane(d, [(267, 27), (287, 27), (287, 40), (267, 40)], True)
    d.line(245, 26, 288, 26, 0xb5b28c)
    d.line(264, 26, 264, 41, 0x323b2d)
    d.ellipse(255, 38, 3, 2, 0x24302b)
    d.p(254, 37, 0x9d9c80)
    d.box(248, 46, 273, 57, 0x5a5736)
    d.text('07', 253, 49, 0xd0c5a1)
    for y in range(46, 85, 7):
        d.line(282, y, 290, y, 0x919483)
        d.line(282, y + 1, 290, y + 1, 0x2a302c)
    # Handrail and cylindrical fuel tank under the engine's hood.
    for y in (71, 72):
        d.line(175, y, 239, y, 0xa3a58d if y == 71 else 0x272d29)
    for x in (180, 203, 226):
        d.line(x, 72, x, 87, 0x585e51)
        d.p(x - 1, 73, 0xb1b099)
    d.box(220, 88, 239, 94, 0x414849)
    d.ellipse(220, 91, 3, 3, 0x636b65)
    d.ellipse(238, 91, 2, 3, 0x282f31)
    d.line(221, 89, 235, 89, 0x969b89)
    for x in (224, 235):
        d.line(x, 89, x, 94, 0x232b2e)
    for x, lift in ((24, 7), (40, 6), (100, 2), (116, 1)):
        tyre(d, x, 98 - lift, 5.1, bare=True)
    for x in (198, 216, 254, 272):
        tyre(d, x, 98, 5.1, bare=True)


def sack(d: Draw, x: int, y: int, width: int = 12):
    d.poly([(x + 2, y), (x + width - 3, y), (x + width - 1, y + 2),
            (x + width - 2, y + 6), (x + 1, y + 6), (x, y + 3)], 0x756244)
    d.line(x + 2, y, x + width - 3, y, 0xc5b28a)
    d.line(x + 2, y + 1, x + width - 3, y + 1, 0xb09a71)
    d.line(x + 1, y + 5, x + width - 2, y + 5, 0x594b37)
    for xx in range(x + 2, x + width - 2, 3):
        d.p(xx, y + 4, 0xc2ab82)
        d.p(xx + 1, y + 4, 0x766046)
    d.p(x + width - 3, y + 2, 0x4f4433)
    d.p(x + width - 2, y + 3, 0xb9a17b)


def outpost(d: Draw, source: Image):
    # Keep the mast and off/on lens exactly where the world-light code anchors
    # them. The area behind the equipment remains transparent; no painted ray.
    for y in range(17, 92):
        for x in range(0, 134):
            d.p(x, y, (0, 0, 0, 0))
    # Canopy top, sloping planes, folded cloth overhang and a scalloped hem.
    d.poly([(8, 26), (40, 18), (88, 19), (123, 25), (119, 30), (12, 31)], 0x636b47)
    d.poly([(10, 26), (40, 20), (87, 21), (118, 26), (66, 25)], 0x89906a)
    d.poly([(10, 27), (65, 25), (119, 27), (118, 33), (12, 34)], 0x3b4832)
    d.line(10, 26, 40, 18, 0xacad83)
    d.line(40, 18, 88, 19, 0xa1a77b)
    for x, ridge in ((17, 43), (43, 53), (66, 66), (94, 78), (116, 88)):
        d.line(ridge, 21, x, 28, 0x434f36)
        d.line(ridge + 1, 21, x + 1, 28, 0xa0a37b)
    for x in range(13, 119):
        y = 33 + (1 if (x // 9) % 2 else 0)
        d.p(x, y, 0x8d9271)
        if x % 3 == 0:
            d.p(x, y - 1, 0xb3ad8d)
    # Bent folding supports with clamps and lashings, rather than flat sticks.
    for x in (10, 66, 121):
        d.line(x, 28, x, 89, 0x323d35)
        d.line(x + 1, 28, x + 1, 89, 0x78836a)
        for y in (34, 57, 84):
            d.line(x - 1, y, x + 2, y, 0xaaa181)
            d.p(x, y + 1, 0x292e28)
        d.line(x - 2, 89, x + 3, 89, 0x3f493d)
    # Heavy field table and its folding legs, braces and front-edge grain.
    d.poly([(22, 58), (59, 58), (64, 61), (24, 61)], 0x9b7950)
    d.box(24, 61, 63, 63, 0x563f2c)
    d.line(25, 61, 61, 61, 0xb19466)
    for x in (28, 57):
        d.line(x, 63, x - 3 if x == 28 else x + 3, 87, 0x5e6861)
        d.line(x + 1, 63, x - 2 if x == 28 else x + 4, 87, 0x262f2b)
    d.line(28, 76, 59, 68, 0x3d4840)
    # Portable radio, weather seals, tuning dial, speaker grille and cable.
    d.box(29, 45, 51, 57, 0x26372b)
    d.line(30, 45, 50, 45, 0x8a9671)
    d.line(30, 46, 30, 56, 0x576a4a)
    d.box(32, 48, 39, 52, 0x171f1b if d.frame == 0 else 0x91b76d)
    d.line(33, 49, 38, 49, 0x56734b if d.frame == 0 else 0xd2db9d)
    d.p(35, 51, 0x22371f)
    for y in (48, 50, 52):
        d.line(43, y, 49, y, 0x121c18)
        d.p(43, y - 1, 0x788368)
    for x in (33, 39, 47):
        d.ellipse(x, 55, 1, 1, 0x1b2421)
        d.p(x, 54, 0xb6b495)
    d.line(47, 44, 46, 22, 0x7e8980)
    d.p(46, 22, 0xc4c3a3)
    d.line(30, 55, 26, 66, 0x1a211e)
    d.line(26, 66, 34, 69, 0x2d352a)
    d.line(34, 69, 38, 65, 0x8a7c53)
    # A rolled map, mug and hand tools on the table; these have their own shapes.
    d.box(54, 54, 60, 57, 0xbfb08a)
    d.ellipse(60, 55, 1, 2, 0x6f644e)
    d.box(24, 54, 27, 57, 0x79817a)
    d.line(25, 54, 27, 54, 0xc6c7b2)
    d.line(69, 43, 73, 51, 0x889186)
    d.line(72, 42, 69, 44, 0xaeb3a0)
    d.line(68, 50, 73, 46, 0x55402d)
    # Locking equipment chest: a recessed front, folded steel corner plates,
    # padlock, lid rim and an empty interior after collecting supplies.
    d.poly([(76, 56), (108, 54), (114, 58), (112, 87), (76, 87)], 0x34432e)
    d.box(78, 58, 108, 85, 0x61704b)
    d.poly([(109, 58), (114, 58), (112, 87), (109, 85)], 0x273725)
    d.line(78, 58, 108, 56, 0x98a477)
    if d.frame == 0:
        d.box(78, 60, 108, 66, 0x718158)
        d.line(78, 66, 108, 66, 0x202e21)
        d.box(90, 64, 96, 70, 0x383e2c)
        d.box(91, 66, 95, 71, 0xb39b5b)
        d.p(93, 69, 0x4c4127)
    else:
        d.poly([(76, 54), (79, 44), (112, 44), (111, 54)], 0x647751)
        d.line(80, 45, 110, 45, 0xadb28c)
        d.box(80, 58, 107, 78, 0x15241c)
        d.line(81, 76, 105, 76, 0x3b4b31)
        d.line(81, 64, 105, 64, 0x283c26)
    for x in (79, 106):
        for y in (59, 82):
            d.bolt(x, y, 0x9fa98d)
    # Medical/tool case and individual fabric sandbags retain the open path.
    d.box(13, 66, 27, 76, 0x3b4b36)
    d.line(14, 66, 26, 66, 0x95a47a)
    d.box(19, 68, 21, 74, 0xd2c8a8)
    d.box(17, 70, 23, 72, 0xd2c8a8)
    for y, n, start in ((85, 13, 0), (78, 12, 6), (71, 11, 12)):
        for i in range(n):
            if y == 71 and 5 <= i <= 8:
                continue
            sack(d, start + i * 12, y)
    # Restore the existing physical lamp head and its rim; no emitted beam.
    for y in range(0, 17):
        for x in range(134, 153):
            d.p(x, y, source.get(d.frame * d.w + x, y))


def burner(d: Draw):
    """The same thirteen fire states, with rolled hoops and a cylindrical shell."""
    frame, base = d.frame, 71
    source = [d.get(x, y) for y in range(72) for x in range(40)]
    flames = {(x, y): source[y * 40 + x] for y in range(72) for x in range(40)
              if source[y * 40 + x][:3] in FLAMES}
    def plot(x, y, value):
        if (x, y) not in flames:
            d.p(x, y, value)
    if frame < 8:
        k = frame - 6 if frame >= 6 else 0
        lean = 6 + k * 8 if frame >= 6 else 0
        def xy(x, y):
            return x + (base - y) * lean // 29, y - k * 3
        for y in range(43, 72):
            for x in range(9, 31):
                u = (x - 9) / 21
                value = 0x929990 if u < .08 else 0x747e7b if u < .22 else 0x4f6061 if u < .51 else 0x34464b if u < .79 else 0x202e35
                if y < 47:
                    value = shade(value, .55)
                xx, yy = xy(x, y)
                plot(xx, yy, value)
        for y in (51, 61):
            for x in range(9, 31):
                for off, value in ((0, 0x929d94), (1, 0x25333b), (2, 0x435258)):
                    xx, yy = xy(x, y + off)
                    plot(xx, yy, value)
        for x0, y0 in ((12, 47), (25, 55), (16, 65)):
            for dx, dy in ((0, 0), (1, 0), (2, 1), (1, 2), (2, 3), (3, 3)):
                xx, yy = xy(x0 + dx, y0 + dy)
                plot(xx, yy, 0x875337 if dy < 2 else 0x5d3a2a)
        for y in range(55, 60):
            for x in range(13, 20):
                if not (x == 19 and y % 2):
                    xx, yy = xy(x, y)
                    plot(xx, yy, 0xa59f82 if y < 58 else 0x6b7466)
        for x in range(14, 19, 2):
            xx, yy = xy(x, 57)
            plot(xx, yy, 0x3b4949)
    else:
        for y in range(51, 72):
            for x in range(3, 32):
                t = (y - 51) / 20
                value = 0x90998e if t < .12 else 0x637776 if t < .35 else 0x3c535c if t < .65 else 0x21343d
                if frame == 12:
                    value = shade(value, .64)
                plot(x, y, value)
        for x in (11, 21):
            for y in range(51, 72):
                plot(x, y, 0x8e9a8d if y < 59 else 0x4b6264)
                plot(x + 1, y, 0x23383e)
        for x0, y0 in ((5, 59), (15, 67), (24, 55)):
            for dx, dy in ((0, 0), (1, 0), (2, 1), (3, 2), (2, 3)):
                plot(x0 + dx, y0 + dy, 0x7b5038)
    for (x, y), value in flames.items():
        d.p(x, y, value)


def hydrant(d: Draw):
    # The cast barrel and caps have rounded volume, hexagonal nuts and worn
    # red enamel. The broken frame keeps the water opening and torn casting.
    water = {(x, y): d.get(x, y) for y in range(28) for x in range(20)
             if d.get(x, y)[:3] in ((36, 72, 94), (74, 134, 160), (140, 196, 212), (216, 240, 244))}
    d.box(0, 0, 19, 27, (0, 0, 0, 0))
    top = 6 if d.frame == 0 else 15
    for y in range(top, 26):
        for x in range(6, 14):
            d.p(x, y, (0xd07a52, 0xb55338, 0x9c3d2a, 0x843326, 0x722c24, 0x5b2420, 0x4a2220, 0x3a1e1c)[x - 6])
    d.ellipse(10, 26, 7, 1, 0x392623)
    d.ellipse(10, 25, 6, 1, 0x8c4c35)
    d.line(5, 25, 14, 25, 0xb5734f)
    for x in (5, 10, 14):
        d.bolt(x, 26, 0xaca18a)
    if d.frame == 0:
        d.ellipse(10, 6, 5, 2, 0x762e25)
        d.line(6, 5, 13, 5, 0xcf8055)
        d.poly([(8, 1), (11, 1), (12, 2), (11, 4), (8, 4), (7, 2)], 0x6f736e)
        d.line(8, 1, 11, 1, 0xc8c3a6)
        for cx, cy, rx in ((4, 14, 3), (15, 14, 3), (10, 15, 4)):
            d.ellipse(cx, cy, rx, 3, 0x492924)
            d.ellipse(cx - .3, cy - .5, rx - .5, 2, 0xaa6444)
            d.poly([(cx - 1, cy - 1), (cx + 1, cy - 1), (cx + 2, cy),
                    (cx + 1, cy + 1), (cx - 1, cy + 1), (cx - 2, cy)], 0x6a7775)
            d.p(cx - 1, cy - 1, 0xbbbda4)
        for x, y in ((13, 18), (14, 19), (13, 20), (14, 21)):
            d.p(x, y, 0x8d9891)
        d.p(7, 21, 0xd1986c)
        d.p(8, 22, 0x664632)
    else:
        d.poly([(6, 15), (7, 11), (8, 14), (10, 12), (11, 15), (13, 12), (13, 17)], 0x542b25)
        d.line(7, 15, 11, 15, 0x9d9d87)
        d.ellipse(10, 16, 3, 1, 0x263c42)
        d.p(7, 13, 0xa18568)
    for (x, y), value in water.items():
        d.p(x, y, value)


def finish(name: str, image: Image) -> Image:
    """Return a finished sheet, or the original image for unsupported names."""
    if name not in WIDTHS:
        return image
    fw = WIDTHS[name]
    assert image.width % fw == 0, (name, image.width, fw)
    out = Image(image.width, image.height)
    out.px = list(image.px)
    for frame in range(image.width // fw):
        d = Draw(out, frame, fw)
        if name == 'vehicles':
            if frame < 3:
                d.ox = 24
                sedan(d, 69, (0x4e6653, 0x914338, 0x514335)[frame], 2 if frame == 2 else 0)
            elif frame == 3:
                d.ox = 30
                jeep(d, 69)
            else:
                d.ox = 2
                truck(d, 69, 0)
        elif name == 'car_wreck':
            sedan(d, 45, (0x9d8b65, 0x944039, 0x405d7b)[frame // 3] if frame % 3 < 2 else 0x514335,
                  frame % 3, ('sedan', 'pickup', 'wagon')[frame // 3])
        elif name == 'siren_car':
            # Preserve the animated light bar and its glare from the source.
            sedan(d, 51, 0x384448, 1 if frame == 3 else 0, police=True)
            for y in range(0, 9):
                for x in range(45, 82):
                    d.p(x, y, image.get(frame * fw + x, y))
            # The original sheriff star on the white door remains legible.
            for yy in range(-3, 4):
                for xx in range(-3, 4):
                    if abs(xx) + abs(yy) <= 3 or abs(xx) == abs(yy) and abs(xx) <= 2:
                        d.p(68 + xx, 32 + yy, 0xc1a366 if xx < 0 else 0x97804f)
        elif name == 'supply_truck':
            d.ox = 2
            truck(d, 69, 1 + frame)
        elif name == 'train':
            train(d)
        elif name == 'outpost':
            outpost(d, image)
        elif name == 'burner':
            burner(d)
        elif name == 'hydrant':
            hydrant(d)
    return out


def _preview() -> None:
    from embed_assets import decode_png_rgba
    root = Path(__file__).resolve().parent.parent
    originals, results = {}, {}
    for name in WIDTHS:
        w, h, data = decode_png_rgba(root / 'assets/sprites/terrain' / f'{name}.png')
        original = Image(w, h)
        original.px = [tuple(data[i:i + 4]) for i in range(0, len(data), 4)]
        originals[name], results[name] = original, finish(name, original)
    # One supported sheet per comparison: all frames at 3x, before then after.
    for name, original in originals.items():
        result, scale = results[name], 3
        preview = Image(original.width * scale + 16, original.height * scale * 2 + 48)
        preview.px = [rgb(0x2b2525)] * len(preview.px)
        for row, img in enumerate((original, result)):
            for y in range(img.height):
                for x in range(img.width):
                    c = img.get(x, y)
                    if not c[3]:
                        continue
                    for dy in range(scale):
                        for dx in range(scale):
                            preview.set(8 + x * scale + dx, 8 + row * (img.height * scale + 24) + y * scale + dy, c)
        preview.save(root / 'build' / f'terrain_{name}_v3.png')
        print(f'preview: build/terrain_{name}_v3.png')


if __name__ == '__main__':
    _preview()
