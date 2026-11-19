"""Furnishings for the laboratory train's rooms (tools/train_art.py draws the
rooms with them). Every piece takes a Room and draws on it in its own
pixels: worked materials lit from the upper left with a dark contour, never
flat fills or uniform noise. Standard library only and deterministic.

Car 01: the sliding side door on the yard, the decontamination booth, the
rail of hazmat suits (the suits themselves are sprites/terrain/train_gear,
drawn by the game while they hang there) and the open locker whose shelf
holds the tablet. Car 02: the tool board. Car 05: reagent bottles and glass.
Car 07: the burst cryogenic pod. Cars 09-13: dormitory, mess, infirmary,
armory and radio room. The control room's tablet dock. And the gear sheet.
"""
from __future__ import annotations

import math

from landscape_kit import Canvas, hx, mix, shade, hash2, fbm, dither

FLOOR = 240
GEAR_W, GEAR_H = 32, 80
INK = hx(0x101417)


def pipe_run(r, points, col=0x657572, radius=2):
    """A narrow service pipe with its wall shadow, edge light and clamps."""
    b = hx(col)
    for (xa, ya), (xb, yb) in zip(points, points[1:]):
        for d in range(-radius, radius + 1):
            tone = shade(b, 1.3 if d == -radius + 1 else .48 if d == radius else .88)
            if ya == yb:
                r.hl(min(xa, xb), max(xa, xb), ya + d, tone)
            else:
                r.vl(xa + d, min(ya, yb), max(ya, yb), tone)
        if ya == yb:
            for x in range(min(xa, xb) + 12, max(xa, xb) - 3, 31):
                r.block(x, ya - radius - 2, x + 2, ya + radius + 2, 0x3e4948)
                r.px(x, ya - radius - 1, 0x9ba7a0)
        else:
            for y in range(min(ya, yb) + 10, max(ya, yb) - 3, 29):
                r.block(xa - radius - 2, y, xa + radius + 2, y + 2, 0x3e4948)
                r.px(xa - radius - 1, y, 0x9ba7a0)
    for x, y in points[1:-1]:
        r.disc(x, y, radius + 1, shade(b, .8))
        r.px(x - 1, y - 1, shade(b, 1.35))


def notice(r, x, y, title, w=32, h=22, col=0xd0c8ac):
    """A small pinned notice, legible title, ruled lines and a faded stamp."""
    r.block(x, y, x + w, y + h, 0x413e34)
    r.fill(x + 2, y + 2, x + w - 2, y + h - 2, col)
    r.text(title, x + 4, y + 4, 0x524b3d)
    for k in range(2):
        r.hl(x + 4, x + w - 5 - k * 3, y + 12 + k * 3, 0x97917b)
    r.disc(x + w - 7, y + h - 6, 3, 0x9c5846)
    r.disc(x + w - 7, y + h - 6, 2, col)
    for xx in (x + 3, x + w - 3): r.px(xx, y + 2, 0xad8150)


def wall_cabinet(r, x, y, w=44, h=25, col=0x64746b, glass=False):
    """A small cabinet bolted to the wall; optional glass shows its stores."""
    r.block(x, y, x + w, y + h, col)
    for xx in (x + 2, x + w - 2):
        r.px(xx, y + 2, 0xaeb9af); r.px(xx, y + h - 2, 0x293330)
    mid = x + w // 2
    r.vl(mid, y + 2, y + h - 2, 0x28322e)
    for a, b in ((x + 3, mid - 2), (mid + 2, x + w - 3)):
        if glass:
            r.recess(a, y + 3, b, y + h - 3, 0x243c3c)
            r.hl(a + 1, b - 1, y + h // 2, 0x738a81)
            for xx in range(a + 3, b - 2, 5):
                r.block(xx, y + h - 11, xx + 2, y + h - 4, 0xadb29d)
                r.px(xx + 1, y + h - 11, 0x50726a)
            r.line(a + 1, y + 9, min(a + 6, b - 1), y + 4, 0x6e9390)
        else:
            r.recess(a + 1, y + 4, b - 1, y + h - 4, shade(hx(col), .93))
    for xx in (mid - 4, mid + 3): r.vl(xx, y + h // 2 - 2, y + h // 2 + 3, 0xb1b9a5)
    r.hl(x + 3, x + w - 3, y + h + 1, 0x26312d)


def trolley(r, x, width=22, col=0x687c76, seed=0):
    """A waist-high service trolley, two trays and four small castors."""
    for xx in (x + 2, x + width - 2):
        r.block(xx, 211, xx + 1, 235, col)
        r.disc(xx, 237, 1.5, 0x1d2526)
        r.px(xx - 1, 236, 0x84968b)
    for y in (211, 229):
        r.block(x, y, x + width, y + 3, col)
        r.hl(x + 2, x + width - 2, y + 1, 0xb5beb0)
    r.block(x + 5, 222, x + width - 5, 228, 0x897653)
    r.hl(x + 7, x + width - 7, 224, 0xb4aa88)
    r.block(x + 4, 206, x + 11, 210, 0xc2c6b4)
    r.px(x + 6, 207, 0x66847a)
    r.block(x + width - 7, 204, x + width - 3, 210, 0x586f69)
    r.hl(x + width - 6, x + width - 4, 204, 0xa8b6aa)
    r.contact_shadow(x, x + width)


def small_bin(r, x, col=0x68716a):
    r.block(x, 222, x + 12, 238, col)
    r.block(x - 1, 220, x + 13, 223, shade(hx(col), .85))
    r.vl(x + 2, 225, 236, shade(hx(col), 1.2))
    r.vl(x + 10, 225, 236, shade(hx(col), .75))
    r.contact_shadow(x, x + 12)


def clinical_cot(r, x, length=76):
    """A spare cot for a curtained examination bay, at the existing scale."""
    r.block(x, 216, x + length, 220, 0xa3b0a6)
    r.block(x + 2, 212, x + length - 2, 215, 0xd2dbd1)
    r.hl(x + 3, x + length - 3, 212, 0xf0f3e6)
    r.block(x + 4, 208, x + 15, 212, 0xe6ebdf)
    r.block(x + length - 20, 209, x + length - 5, 212, 0x617b7b)
    for xx in (x + 4, x + length - 4):
        r.vl(xx, 221, 235, 0x76847a)
        r.disc(xx, 237, 1.5, 0x222a29)
    r.hl(x + 4, x + length - 4, 231, 0x76847a)
    r.contact_shadow(x, x + length)


def clinical_curtain(r, x0, x1, left_width=24, right_width=8):
    """A privacy curtain on a ceiling-mounted rail, partly drawn around a cot.

    Continuous steel hangers meet bolted ceiling plates. Rollers and cloth
    loops join the rail to the fabric; the hem stops just above the floor.
    The open middle shows the bed and makes the clinical bay read clearly.
    """
    for x in (x0 + 3, x1 - 3):
        r.block(x - 4, 55, x + 4, 61, 0x606f6a)
        r.px(x - 2, 57, 0xb2beb1); r.px(x + 2, 58, 0x27312e)
        r.vl(x, 62, 146, 0xa4b1a8)
        r.vl(x + 1, 62, 146, 0x4b5d58)
        r.block(x - 2, 136, x + 3, 140, 0x697c72)
    r.block(x0 - 2, 145, x1 + 2, 149, 0x73877e)
    r.hl(x0 - 1, x1 + 1, 145, 0xc0cbc0)
    r.hl(x0 - 1, x1 + 1, 149, 0x34453f)
    for a, b in ((x0, x0 + left_width), (x1 - right_width, x1)):
        for x in range(a, b + 1):
            fold = (x - a) % 6
            bottom = 234 + (1 if fold in (2, 3) else 0)
            for y in range(155, bottom + 1):
                tone = (0.85, 1.0, 1.1, 1.08, .84, .70)[fold]
                tone *= 1 - .09 * (y - 155) / 80
                r.px(x, y, shade(hx(0x76988a), tone))
            r.px(x, 233 + (fold in (2, 3)), 0x425d52)
        for x in range(a + 2, b, 6):
            r.px(x, 150, 0xc2cec2); r.vl(x, 151, 154, 0x8b9e92)
            r.px(x + 1, 151, 0x394f44)
        r.hl(a, b, 160, 0x95aea0)
        r.vl(a, 156, 233, 0x4f6b5c)
        r.vl(b, 156, 233, 0x4f6b5c)


def extractor_housing(r, cx, cy):
    """A mounted housing; its five-pixel blades are drawn by the game."""
    r.block(cx - 9, cy - 9, cx + 9, cy + 9, 0x4d6059)
    r.disc(cx, cy, 7, 0x91a499)
    r.disc(cx, cy, 6, 0x142522)
    for dx in (-7, 7):
        for dy in (-7, 7):
            r.px(cx + dx, cy + dy, 0x1f2d26)
            r.px(cx + dx - 1, cy + dy - 1, 0xb2bca8)
    r.block(cx - 4, cy + 10, cx + 4, cy + 12, 0x3a4b44)


def vent_grille(r, x, y, w=54, h=21):
    r.block(x, y, x + w, y + h, 0x66776d)
    r.recess(x + 3, y + 3, x + w - 3, y + h - 3, 0x293c35)
    for yy in range(y + 5, y + h - 3, 3):
        r.hl(x + 5, x + w - 5, yy, 0x8da091)
        r.hl(x + 5, x + w - 5, yy + 1, 0x3c5146)
    for xx in (x + 2, x + w - 2):
        for yy in (y + 2, y + h - 2): r.px(xx, yy, 0xc0c9b8)


def wall_clock(r, cx, cy):
    r.disc(cx, cy, 8, 0x25372d)
    r.disc(cx, cy, 7, 0x8a9d89)
    r.disc(cx, cy, 6, 0xd0d3b9)
    for dx, dy in ((0, -5), (5, 0), (0, 5), (-5, 0)):
        r.px(cx + dx, cy + dy, 0x3d5140)
    r.line(cx, cy, cx - 3, cy - 2, 0x334735)
    r.line(cx, cy, cx + 1, cy - 4, 0x334735)
    r.px(cx, cy, 0xa46243)


def clipboard(r, x, y, signed=False):
    r.block(x, y, x + 10, y + 14, 0x7b6849)
    r.fill(x + 1, y + 2, x + 9, y + 13, 0xcfc8aa)
    r.block(x + 3, y, x + 7, y + 2, 0x819389)
    for k in range(3): r.hl(x + 3, x + 7 - k % 2, y + 5 + k * 3, 0x8c8d73)
    if signed: r.line(x + 3, y + 11, x + 7, y + 9, 0x905347)


def room_wall_services(r):
    """Useful high wall space: supported pipes, conduits and cable trays.

    These are fixed building services, with narrow real pipe diameters.
    They add depth to the tall car without changing any human furniture.
    Room-specific art is painted in front of them.
    """
    i = r.index
    pipe_col = 0x66766b if i in (8, 9, 11, 12, 14) else 0x777f74
    pipe_run(r, [(21, 68), (337, 68)], pipe_col, 2)
    pipe_run(r, [(22, 80), (337, 80)], 0x64766e, 2)
    bx = (38, 184, 218, 113, 179)[i % 5]
    pipe_run(r, [(bx, 80), (bx, 112), (bx + 23, 112)], 0x7c6951, 1)
    r.disc(bx + 13, 112, 4, 0x35463b)
    r.disc(bx + 13, 112, 3, 0x98a68d)
    r.line(bx + 13, 112, bx + 14, 110, 0x8f5842)
    # Flanged isolation valve, rather than an unexplained disk on the wall.
    vx = 74 + (i % 4) * 58
    r.block(vx - 3, 64, vx + 3, 73, 0x475b4b)
    r.vl(vx, 60, 64, 0x8b9a84)
    r.hl(vx - 5, vx + 5, 60, 0x7d4d3c)
    for x in (vx - 5, vx + 5): r.vl(x, 59, 61, 0xa16a4f)
    # Electrical conduits are secured to the wall and terminate at a box.
    cx = 330 if i % 2 else 26
    for dx in (0, 3): r.vl(cx + dx, 84, 128, 0x4b5f52)
    r.block(cx - 2, 127, cx + 7, 140, 0x697d6a)
    r.px(cx + 1, 130, 0xa5b396); r.px(cx + 4, 137, 0x263e2c)
    tx = 117 + (i % 3) * 23
    r.block(tx, 89, tx + 62, 94, 0x42584a)
    for k, col in enumerate((0x26332e, 0x7a5143, 0x4c6757)):
        for x in range(tx + 2, tx + 61):
            r.px(x, 90 + k, col)
    for x in range(tx + 5, tx + 60, 13):
        r.vl(x, 88, 95, 0x718675)
        r.vl(x + 1, 95, 102, 0x384c3e)


def room_dressing(r):
    """Small, room-specific evidence of the crew's work and daily routine."""
    i = r.index
    if i == 0:
        notice(r, 24, 92, 'EPP', 46, 29)
        r.fill(77, 96, 102, 116, 0x344d3c)
        r.text('LAVAR', 80, 100, 0xbcc6a4)
        r.text('MANOS', 80, 107, 0xbcc6a4)
        vent_grille(r, 214, 112, 53, 22)
        clipboard(r, 272, 183, True)
    elif i == 1:
        wall_cabinet(r, 30, 128, 73, 27, 0x63776c, True)
        notice(r, 116, 111, 'PRUEBA', 43, 36, 0xb9c4b0)
        clipboard(r, 217, 119, True)
        small_bin(r, 218, 0x5e7165)
        r.paper(86, 203, 10, 2)
    elif i == 2:
        trolley(r, 198, 23, 0x667d71)
        notice(r, 110, 96, 'MRC-2', 30, 30)
        clipboard(r, 211, 139)
        r.block(195, 188, 213, 191, 0x849a87)
        for k in range(3): r.block(197 + k * 5, 178, 200 + k * 5, 187, 0x70907d)
    elif i == 3:
        notice(r, 250, 109, 'ESTERIL', 43, 28, 0xc2cbb9)
        clipboard(r, 283, 193, True)
        steel_cylinder(r, 326, 334, 192, 236, 0x527f72)
        r.block(328, 188, 332, 193, 0x6b7561)
        r.hl(329, 333, 205, 0xbec8ac)
        r.line(327, 194, 320, 199, 0x2d4436)
    elif i == 4:
        notice(r, 30, 106, 'MUESTRAS', 51, 31, 0xc5cdb8)
        wall_cabinet(r, 116, 123, 56, 29, 0x5b7568, True)
        clipboard(r, 184, 131, True)
        clipboard(r, 205, 132)
        r.block(277, 188, 286, 194, 0xb3c4ae)
        r.px(278, 189, 0x597f70)
    elif i == 5:
        for x in (114, 224):
            r.block(x - 6, 163, x + 6, 181, 0x516c5c)
            r.lit_fill(x - 3, 167, x + 3, 171, 0x58784d)
            r.px(x - 2, 176, 0xc7b07c)
            r.px(x + 2, 176, 0x98654e)
    elif i == 6:
        notice(r, 230, 78, '-20C', 37, 31, 0xb5cbd0)
        pipe_run(r, [(24, 62), (210, 62)], 0x829d9a, 2)
        for x in (43, 93, 143, 193):
            r.vl(x, 64, 79, 0x738e89)
            r.vl(x + 1, 64, 79, 0xb5c8bc)
    elif i == 7:
        wall_cabinet(r, 26, 117, 57, 29, 0x6b7762)
        notice(r, 107, 111, 'REGISTRO', 54, 32)
        clipboard(r, 207, 156, True)
        clipboard(r, 224, 155)
        small_bin(r, 300, 0x6d7060)
        r.paper(216, 210, 8, 2)
    elif i == 8:
        vent_grille(r, 29, 94, 60, 22)
        notice(r, 126, 94, 'GUARDIAS', 57, 26)
        wall_clock(r, 311, 108)
        wall_cabinet(r, 286, 130, 49, 24, 0x657a67)
        r.hl(215, 231, 173, 0x93a48b)
        for x in (218, 227):
            r.px(x, 175, 0x9aa991)
            r.block(x - 3, 179, x + 3, 198, 0x586c56)
            r.hl(x - 2, x + 2, 182, 0x788a66)
        r.paper(76, 186, 7, 2)
    elif i == 9:
        notice(r, 30, 94, 'RACION', 46, 25)
        notice(r, 287, 133, 'TURNOS', 44, 41)
        wall_clock(r, 245, 106)
        r.block(162, 170, 193, 173, 0x6e806b)
        for x in (166, 176, 187):
            r.vl(x, 174, 186, 0xa7b69b)
            r.disc(x, 188, 2, 0x798d79, 3)
        r.recess(132, 201, 147, 203, 0x506e62)
        r.vl(143, 195, 200, 0x9eaf94); r.hl(140, 143, 195, 0x9eaf94)
    elif i == 10:
        notice(r, 28, 96, 'HIGIENE', 57, 29, 0xc5d1bc)
        wall_clock(r, 112, 109)
        notice(r, 240, 95, 'TURNOS DE GUARDIA', 89, 27, 0xc9d0ba)
        r.block(40, 179, 104, 190, 0x6e8778)
        for k, x in enumerate((49, 68, 89)):
            r.disc(x, 184, 3, 0x294c3c)
            r.disc(x, 184, 2, (0x9bb79b, 0x9c7457, 0x749c9b)[k])
        clipboard(r, 91, 157, True)
        clinical_curtain(r, 137, 218, 21, 12)
    elif i == 11:
        notice(r, 26, 96, 'LIMPIEZA', 46, 33)
        notice(r, 84, 95, 'INVENTARIO', 51, 33)
        r.block(214, 148, 293, 151, 0x84967c)
        for x in (227, 253, 279): r.vl(x, 152, 157, 0x6b8069)
        r.block(249, 104, 285, 124, 0x4c6655)
        r.text('HALCON', 255, 108, 0xb3c19c)
        for k, x in enumerate((255, 266, 278)): r.led(x, 119, (0x8bac6b, 0xc99d64, 0x7f9e7a)[k])
        pipe_run(r, [(287, 114), (315, 114), (315, 149)], 0x5c7360, 1)
    elif i == 12:
        vent_grille(r, 25, 118, 68, 24)
        notice(r, 125, 103, 'FRECUENCIAS', 95, 34, 0xbbc6a9)
        r.screen(274, 98, 308, 118, (145, 194, 129), 64, 'bars', mount=False)
        clipboard(r, 249, 188)
        r.paper(207, 209, 7, 2)
    elif i == 13:
        small_bin(r, 204, 0x776a51)
        notice(r, 211, 106, 'PRESION', 47, 26, 0xc4c6a7)
        r.block(214, 172, 237, 175, 0x738676)
        for x in (216, 228):
            r.block(x, 161, x + 6, 171, 0x7c7753)
            r.hl(x + 1, x + 5, 164, 0xb1aa7d)
        pipe_run(r, [(225, 176), (225, 193), (239, 193)], 0x4c6553, 1)
    elif i == 14:
        r.block(179, 104, 211, 137, 0x485e4b)
        for y in range(109, 133, 6):
            r.recess(183, y, 207, y + 3, 0x2c4434)
            r.px(204, y + 1, 0xa6b784)
        notice(r, 256, 97, 'RED 4-G', 44, 27, 0xbcc8af)
        wall_clock(r, 321, 105)
        r.block(273, 176, 285, 196, 0x4d6a58)
        r.block(275, 178, 278, 194, 0x2d4635)
        for y in range(198, 220):
            r.px(279 + y % 2, y, 0x263e2d)
        r.block(271, 225, 286, 228, 0x536f58)
        for x in (273, 283): r.vl(x, 229, 238, 0x405b44)


def cyl(t):
    """Light on an upright cylinder at t (-1 its left edge .. 1 its right),
    from the upper left and a little in front: 0 dark .. 1 lit."""
    t = max(-1.0, min(1.0, t))
    return max(0.0, -.55 * t + .83 * math.sqrt(max(0.0, 1 - t * t)))


def bands(v, steps=5):
    """Shading in a few crisp steps, as pixel art is."""
    return round(max(0.0, min(1.0, v)) * (steps - 1)) / (steps - 1)


def steel_cylinder(r, x0, x1, y0, y1, base, lo=.5, hi=1.25, rim=True):
    """A drum or post standing upright: banded light across it, a lit rim on
    top and a dark one under it."""
    b = hx(base)
    cx, rad = (x0 + x1) / 2, max(1.0, (x1 - x0) / 2 + .5)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            k = lo + (hi - lo) * bands(cyl((x - cx) / rad), 6)
            r.px(x, y, shade(b, k))
    r.vl(x0, y0, y1, INK)
    r.vl(x1, y0, y1, INK)
    if rim:
        r.hl(x0 + 1, x1 - 1, y0, shade(b, 1.45))
        r.hl(x0 + 1, x1 - 1, y1, shade(b, .42))


# ======================================================================
# Car 01
# ======================================================================

def side_door(r, x0):
    """Car 01's sliding side door, open on the yard at dusk. The frame stands
    proud of the wall and its reveal shows how thick the wall is; the yard
    beyond has depth (sky, a far water tower, a pole and its wires, rails and
    the step down); the heavy leaf hangs slid along the inside of the wall
    from its track, with a porthole, a grab handle and its rollers."""
    x1, top = x0 + 31, 160
    # The frame and the hazard header over it.
    r.hazard(x0 - 6, 148, x1 + 6, 153)
    r.block(x0 - 6, 154, x1 + 6, 239, 0x4f5b58)
    for y in range(158, 236, 10):                             # Its bolts
        for x in (x0 - 4, x1 + 4):
            r.px(x, y, 0x252c2d); r.px(x - 1, y - 1, 0xa3ada6)
    # The yard at dusk, then what stands in it.
    horizon = 206
    for y in range(top, 240):
        for x in range(x0, x1 + 1):
            if y < horizon:
                q = (y - top) / (horizon - top) * 6
                k = int(q) + (1 if dither(x, y, q - int(q)) else 0)
                col = mix(hx(0xf7c985), hx(0xa94a36), min(1.0, k / 6))
            elif y < 216:
                col = hx(0x4d3631) if (y - horizon) % 4 else hx(0x5d4237)
                if y in (209, 213): col = hx(0xa47c5a) if (x + y) % 6 else hx(0x6e4c3a)
            elif y < 223:
                col = hx(0x3a2a27)
            else:
                col = hx(0x2a1f1e) if (x // 4 + y) % 3 else hx(0x31252a)
            r.lit(x, y, col)
    for x in range(x0, x1 + 1):                               # The step's lit edge
        r.lit(x, 223, 0x9a6a48)
    sun = (x0 + 24, 186)
    for y in range(sun[1] - 5, sun[1] + 6):
        for x in range(sun[0] - 5, sun[0] + 6):
            d = math.hypot(x - sun[0], y - sun[1])
            if d <= 4.6 and x0 <= x <= x1:
                r.lit(x, y, 0xffe2a8 if d < 3.2 else 0xffc882)
    for x in range(x0 + 3, x0 + 12):                          # A far water tower
        for y in range(181, 189):
            r.lit(x, y, 0x5a2f2b if (x + y) % 5 else 0x643530)
    for x in (x0 + 4, x0 + 10):
        for y in range(189, horizon):
            r.lit(x, y, 0x52302b)
    r.lit_fill(x0 + 4, 196, x0 + 10, 196, 0x52302b)
    for y in range(168, horizon):                             # A telegraph pole and its wires
        r.lit(x0 + 19, y, 0x3b2526)
    r.lit_fill(x0 + 15, 171, x0 + 23, 171, 0x3b2526)
    for x in range(x0, x1 + 1):
        r.lit(x, 172 + round(2 * math.sin((x - x0) / 9)), 0x7a4436)
    for x in range(x0 + 14, x1 + 1):                          # A boxcar on the next track
        for y in range(198, horizon):
            r.lit(x, y, 0x4a2c29 if (x - x0) % 6 else 0x3f2523)
    # The reveal: the jambs' inner faces and the lintel's underside.
    r.fill(x0, top, x0 + 2, 239, 0x283130)
    r.vl(x0 + 3, top, 239, 0x1b2223)
    r.fill(x1 - 2, top, x1, 239, 0x93a09a)
    r.vl(x1 - 3, top, 239, 0x6c7874)
    r.vl(x1, top, 239, 0xb6c1ba)
    r.fill(x0, top, x1, top + 2, 0x182021)
    r.hl(x0, x1, top + 3, 0x2c3434)
    for y in range(top + 4, 239, 3):                          # The rubber seal on the right jamb
        r.px(x1 - 3, y, 0x161b1c)
    # Threshold: a tread plate with a hazard edge.
    r.block(x0 - 6, 232, x1 + 6, 239, 0x5d6763)
    for x in range(x0 - 4, x1 + 5, 4):
        r.px(x, 235, 0x9aa49e); r.px(x + 2, 237, 0x9aa49e)
    r.hazard(x0 - 6, 230, x1 + 6, 231)
    # The track the leaf ran on, out over the wall to the right.
    lx0, lx1 = x1 + 8, x1 + 40
    r.block(x0 - 6, 155, lx1 + 3, 158, 0x3a4443)
    r.hl(x0 - 5, lx1 + 2, 156, 0x8d9893)
    # The leaf: heavy steel with stiffening ribs, a porthole on the dusk
    # outside, its leading edge thick and lit, a grab handle and rollers.
    r.block(lx0, 159, lx1, 239, 0x6d7a75)
    b = hx(0x6d7a75)
    for y in (180, 205):                                      # Pressed ribs across it
        r.hl(lx0 + 3, lx1 - 3, y, shade(b, .62))
        r.hl(lx0 + 3, lx1 - 3, y + 1, shade(b, 1.22))
    for x in range(lx0 + 6, lx1 - 3, 7):
        r.vl(x, 209, 234, shade(b, .78))
        r.vl(x + 1, 209, 234, shade(b, 1.12))
    r.fill(lx0 + 1, 160, lx0 + 3, 238, shade(b, 1.28))       # The leading edge, toward the light
    r.vl(lx0 + 3, 160, 238, shade(b, .7))
    for y in range(165, 236, 4):                              # ...and its rubber nose
        r.px(lx0 + 1, y, 0x1d2324)
    pcx, pcy = (lx0 + lx1) // 2 + 2, 170
    r.disc(pcx, pcy, 7, INK)
    r.disc(pcx, pcy, 6, 0x9aa6a0)
    r.disc(pcx, pcy, 5, 0x3b4644)
    for y in range(pcy - 4, pcy + 5):
        for x in range(pcx - 4, pcx + 5):
            if (x - pcx) ** 2 + (y - pcy) ** 2 <= 16:
                r.lit(x, y, mix(hx(0xf3b878), hx(0xb5583c), (y - pcy + 4) / 8))
    r.lit(pcx - 2, pcy - 2, 0xffe8c0); r.lit(pcx - 1, pcy - 3, 0xffe8c0)
    for a in range(8):                                        # Bolts round the porthole
        ang = a * math.pi / 4
        r.px(round(pcx + 6.5 * math.cos(ang)), round(pcy + 6.5 * math.sin(ang)), 0x3a4442)
    r.recess(lx0 + 6, 186, lx0 + 9, 200, shade(b, .7))       # The grab handle
    r.block(lx0 + 7, 188, lx0 + 8, 198, 0xc9c2a4, ink=False)
    r.block(lx1 - 14, 214, lx1 - 5, 219, 0xd3b93f)            # A warning label
    r.hl(lx1 - 13, lx1 - 6, 216, 0x2a2622)
    for rx in (lx0 + 4, lx1 - 4):                             # Rollers on the track
        r.disc(rx, 157, 2, INK)
        r.px(rx, 157, 0x9aa49e); r.px(rx - 1, 156, 0xc6cdc6)
    r.tints.append((x0 + 16, 205, 70, (238, 152, 92), .36))
    r.tints.append((x0 + 16, 238, 50, (238, 152, 92), .32))
    r.tints.append((lx0 + 8, 200, 26, (238, 152, 92), .2))
    r.block(x0 + 1, 132, x1 - 1, 143, 0x1d2a22)
    r.text('SALIDA', x0 + 4, 135, 0x8fe39d, glow=True)
    r.contact_shadow(lx0, lx1)


def decon_booth(r, cx, rad=22):
    """A person-sized shower booth: 90 px high with a 44 px glass drum."""
    x0, x1, top, cap, glass = cx - rad, cx + rad, 150, 165, 225
    for x, col in ((cx - 10, 0x5f6b6a), (cx + 9, 0x4f5a59)):
        steel_cylinder(r, x - 1, x + 1, 44, top, col, rim=False)
        for y in (83, 118): r.block(x - 2, y, x + 2, y + 3, 0x7d8884)
    steel_cylinder(r, x0 - 2, x1 + 2, top, cap, 0x6f7c79)
    r.block(cx - 28, 139, cx + 28, 147, 0x1f2b25)
    r.text('DESCONTAMINAR', cx - 25, 141, 0xf0d77e, glow=True)
    r.led(cx + 17, top + 4, 0xf3b44a)
    for y in range(cap + 1, glass + 1):
        for x in range(x0, x1 + 1):
            t = (x - cx) / rad
            back = mix(hx(0x5d7472), hx(0x2c3c3d), (y - cap) / 85 + abs(t) * .2)
            if x % 4 == 0 and y % 3 == 0: back = shade(back, .7)
            col = mix(back, hx(0x4e908b), .3)
            if abs(t) > .8: col = mix(col, hx(0xa9cfc9), (abs(t) - .8) * 1.7)
            if -.65 <= t <= -.5: col = mix(col, hx(0xe6f6f0), .65)
            r.lit(x, y, col)
    for x in (x0, cx - 9, cx + 9, x1):
        r.vl(x, cap + 1, glass, 0x8a9590)
        r.vl(x + 1, cap + 1, glass, 0x364441)
    for k in range(5):
        x = cx - 16 + k * 8
        r.px(x, cap + 2, 0x283031); r.lit(x, cap + 3, 0xd8ece6)
        for i in range(10):
            xx, yy = x + (i % 3 - 1), cap + 5 + i * 3 + k % 2
            if hash2(k, i, 41) > .35: r.lit(xx, yy, mix(r.get(xx, yy), hx(0xeaf6f2), .45))
    for y in range(cap + 8, glass - 4, 5): r.px(cx - 7, y, 0x1d2526)
    r.block(cx + 4, 194, cx + 6, 207, 0xc9d2cc)
    r.disc(cx, glass - 2, 4, 0x1e292a, 1.5)
    steel_cylinder(r, x0 - 2, x1 + 2, glass + 1, 239, 0x55615f)
    r.hazard(x0 - 1, 230, x1 + 1, 232)
    r.block(cx - 13, 235, cx + 13, 239, 0x6f7a76)
    r.tints.append((cx, 195, 40, (120, 200, 190), .14))
    r.contact_shadow(x0 - 2, x1 + 2)
    px = x1 + 8
    r.block(px, 184, px + 12, 215, 0x46524f)
    r.recess(px + 2, 187, px + 10, 193, 0x101718)
    r.text('OK', px + 3, 188, 0x8fe39d, glow=True)
    for k, col in enumerate((0x7fe39a, 0xe8b25a, 0x6fc8e8)):
        r.led(px + 4 + k * 3, 200, col)
    r.disc(px + 6, 209, 2, 0xc0382b)
    r.vl(px + 6, 216, 235, 0x1b1f21)


def suit_rail(r, cx, hook):
    """Hooks and suits are reachable at shoulder height."""
    r.block(cx - 26, 150, cx + 26, 158, 0x1f2b25)
    r.text('TRAJES EPP', cx - 19, 152, 0xe6d27c)
    r.block(cx - 24, 163, cx + 24, 166, 0x7f8a85)
    for x in (cx - 21, cx + 21):
        r.px(x, 164, 0x262d2e); r.px(x - 1, 163, 0xc6cdc6)
    for x in (cx - hook, cx + hook):
        r.fill(x - 1, 167, x, 172, 0xb1bab4)
        r.vl(x + 1, 167, 172, 0x4d5755)
        r.px(x - 2, 172, 0xb1bab4); r.px(x - 2, 171, 0xd8ded8)
    r.block(cx - 24, 236, cx + 24, 239, 0x22282a)
    for x in range(cx - 22, cx + 23, 3): r.px(x, 237, 0x3c4446)


def open_locker(r, x0, x1, shelf):
    """A 78 px locker: helmet above the tablet, small boots below it."""
    b = hx(0x77847f)
    r.block(x0, 161, x1, 238, b)
    r.fill(x0 + 3, 165, x1 - 3, 235, 0x1a2123)
    for y in range(165, 236):
        for x in range(x0 + 3, x1 - 2):
            r.px(x, y, shade(hx(0x2f393a), .95 - .35 * (y - 165) / 70 - .25 * (x - x0) / (x1 - x0)))
    for x in range(x0 + 4, x1 - 3): r.lit(x, 166, 0xd8efe6)
    r.tints.append(((x0 + x1) // 2, 191, 26, (210, 236, 228), .16))
    for sy in (181, shelf):
        r.block(x0 + 3, sy, x1 - 3, sy + 2, 0x8f9a95)
        r.hl(x0 + 4, x1 - 4, sy + 3, 0x0f1314)
    hcx = x0 + 12
    r.disc(hcx, 178, 6, 0xd9b23a, 4)
    r.hl(hcx - 7, hcx + 7, 180, 0x8c6f20)
    r.hl(hcx - 3, hcx + 2, 175, 0xf1d690)
    r.block(x1 - 13, 176, x1 - 5, 180, 0x3c4d5a)
    r.hl(x1 - 12, x1 - 6, 178, 0x56697a)
    scx = (x0 + x1) // 2
    r.block(scx - 8, shelf - 2, scx + 8, shelf - 1, 0x2a3133)
    r.block(scx - 6, shelf - 10, scx - 5, shelf - 2, 0x2a3133)
    r.led(scx + 7, shelf - 2, 0x7fe39a)
    for bx in (x0 + 8, x0 + 21):
        r.block(bx, 226, bx + 4, 234, 0x2b2c27)
        r.block(bx, 231, bx + 7, 234, 0x2b2c27)
        r.vl(bx + 1, 227, 232, 0x55564d)
    d0 = x1 + 1
    r.poly([(d0, 161), (d0 + 6, 164), (d0 + 6, 235), (d0, 238)], INK)
    r.poly([(d0 + 1, 163), (d0 + 5, 165), (d0 + 5, 234), (d0 + 1, 236)], shade(b, .92))
    for y in range(169, 178, 3): r.hl(d0 + 2, d0 + 4, y, shade(b, .5))
    r.vl(d0 + 1, 164, 235, shade(b, 1.25))
    r.block(d0 + 2, 199, d0 + 4, 207, 0xc8c2a6)
    for y in (172, 204, 229): r.px(x1, y, 0xb1bab4)
    r.contact_shadow(x0, d0 + 6)


def tablet_dock(r, cx, y):
    """At the control terminal: the cradle the tablet locks into to read
    Archivo 4, with its label and lamp."""
    r.block(cx - 13, y, cx + 13, y + 15, 0x2f3839)
    r.recess(cx - 10, y + 2, cx + 10, y + 11, 0x121819)
    for x in range(cx - 9, cx + 10):                         # Its contacts, brass
        if x % 3 == 0: r.px(x, y + 10, 0xc19a4c)
    r.led(cx + 11, y + 3, 0xe8b25a)
    r.block(cx - 15, y - 9, cx + 15, y - 2, 0x1d2a22)
    r.text('TABLETA', cx - 13, y - 8, 0xd6d0ae)


# ======================================================================
# Car 02: the tool board
# ======================================================================

def _ink_outline(r, pts, col):
    for x, y in pts:
        r.px(x, y, col)


def tool_board(r, x0, y0, x1, y1):
    """Native 12-23 px hand tools on a pegboard; no tool is person-sized."""
    board = hx(0x7a6848)
    r.block(x0, y0, x1, y1, board)
    for y in range(y0 + 3, y1 - 1, 4):
        for x in range(x0 + 3, x1 - 1, 4):
            r.px(x, y, shade(board, .5)); r.px(x + 1, y + 1, shade(board, 1.12))
    r.grime(x0 + 1, y0 + 1, x1 - 1, y1 - 1, 23, .5, (60, 48, 34), .2)
    def hook(x, y):
        r.px(x, y, 0xc6cdc6); r.px(x + 1, y + 1, 0x3e4644)
    wx, wy = x0 + 10, y0 + 5
    r.block(wx - 2, wy, wx + 3, wy + 4, 0x9aa6a2)
    r.fill(wx, wy, wx + 1, wy + 2, board)
    r.block(wx, wy + 4, wx + 1, wy + 17, 0x9aa6a2)
    r.vl(wx, wy + 5, wy + 16, 0xd8e0dc); hook(wx, wy - 2)
    sx = wx + 16
    r.block(sx, wy, sx + 5, wy + 6, 0x8b4a2c)
    r.fill(sx + 2, wy + 2, sx + 3, wy + 4, board)
    for k in range(16):
        w = max(1, 5 - k // 4)
        r.hl(sx + 1, sx + w, wy + 7 + k, 0xb9c1bb)
        r.px(sx, wy + 7 + k, INK)
        r.px(sx + w + 1, wy + 7 + k, 0x5a6462 if k % 2 else INK)
    hook(sx + 2, wy - 2)
    px = sx + 17
    for side in (-1, 1):
        r.line(px + side, wy, px + side, wy + 5, 0x8a9690)
        r.line(px + side, wy + 5, px + side * 3, wy + 16, 0xb5392a)
        r.line(px + side * 2, wy + 7, px + side * 4, wy + 16, 0x7a2219)
    r.disc(px, wy + 5, 1, 0xc6cdc6); hook(px, wy - 2)
    for k, (col, ln) in enumerate(((0xd29a2e, 16), (0xb5392a, 13), (0x3f74a8, 10))):
        x = px + 14 + k * 8
        r.block(x - 1, wy, x + 1, wy + 6, col)
        r.vl(x - 1, wy + 1, wy + 5, shade(hx(col), 1.35))
        r.vl(x, wy + 7, wy + ln, 0xc6cdc6); hook(x, wy - 2)
    # Empty hammer outline, and a compact multimeter with looped leads.
    x = px + 47
    r.block(x - 4, wy, x + 4, wy + 2, shade(board, .7))
    r.vl(x, wy + 3, wy + 17, shade(board, .7)); hook(x, wy - 2)
    mx = x1 - 15
    r.block(mx, wy, mx + 9, wy + 14, 0xd2a838)
    r.recess(mx + 2, wy + 2, mx + 7, wy + 5, 0x2a3132)
    r.lit_fill(mx + 3, wy + 3, mx + 6, wy + 4, 0x9ccc7a)
    r.disc(mx + 4, wy + 9, 2, 0x3a4142); hook(mx + 4, wy - 2)
    for k, col in enumerate((0xb5392a, 0x1b1d1f)):
        cx, cy = mx + 2 + k * 5, wy + 20
        r.line(mx + 2 + k * 5, wy + 13, cx - 2, cy, col)
        for a in range(0, 360, 30):
            ang = math.radians(a)
            r.px(round(cx + 2 * math.cos(ang)), round(cy + 3 * math.sin(ang)), col)


def bottle(r, x, bottom, kind, liquid, label=None, seed=0):
    """7-13 px glassware, with 2-7 px bodies and native one-pixel detail."""
    liq, glass = hx(liquid), hx(0x9fbab6)
    h = {'reagent': 11, 'erlenmeyer': 10, 'cylinder': 13, 'round': 9}[kind]
    top = bottom - h + 1
    def half(y):
        k = y - top
        if kind == 'reagent': return 1 if k < 3 else 2
        if kind == 'erlenmeyer': return 1 if k < 3 else 1 + (k - 3) * 2 / (h - 3)
        if kind == 'cylinder': return 1 if k < h - 1 else 2
        return 1 if k < 3 else max(1, 3 * math.sqrt(max(0, 1 - ((k - 5) / 3.5) ** 2)))
    level = top + h // 2
    for y in range(top, bottom + 1):
        hw = round(half(y)); lo, hi = x - hw, x + hw
        r.px(lo - 1, y, INK); r.px(hi + 1, y, INK)
        for xx in range(lo, hi + 1):
            col = mix(liq, shade(liq, .55), abs(xx - x + .5) / (hw + 1)) if y >= level else glass
            if kind == 'reagent' and y < top + 2: col = hx(0x3f74a8 if seed % 2 else 0x2f3536)
            (r.lit if y >= level and liquid != 0x5a3a22 else r.px)(xx, y, col)
        r.px(lo, y, 0xd4e5e0)
    r.hl(x - round(half(level)) + 1, x + round(half(level)) - 1, level, mix(liq, (255, 255, 255), .5))
    if label:
        r.hl(x - 1, x + 1, bottom - 3, 0xe1dac2)
        r.px(x, bottom - 2, 0xa83a2c if label == 'red' else 0x2f5878)
    if kind == 'round':
        r.hl(x - 1, x + 6, top + 2, 0x6c7472)
        r.vl(x + 6, top - 8, bottom + 1, 0x4a5452)
        r.hl(x + 3, x + 9, bottom + 1, 0x3a4142)


def glass_shelf(r, x0, x1, bottom, seed):
    """A row of mixed glassware standing on a shelf at row bottom + 1."""
    kinds = (('reagent', 0x6b3a1e, 'red'), ('erlenmeyer', 0x8bd86a, None), ('reagent', 0xd6c35a, 'blue'),
             ('cylinder', 0x6fb7d2, None), ('erlenmeyer', 0xd06a4e, None), ('reagent', 0x9fd8d0, 'red'))
    x = x0 + 5
    k = 0
    while x < x1 - 5:
        kind, liq, lab = kinds[(k + seed) % len(kinds)]
        bottle(r, x, bottom, kind, liq, lab, seed + k)
        x += {'reagent': 10, 'erlenmeyer': 14, 'cylinder': 8, 'round': 16}[kind]
        k += 1


# ======================================================================
# Car 07: the pod that burst
# ======================================================================

def burst_pod(r, x0, seed=3):
    """A cryogenic capsule broken from inside. What is left of its front is
    frosted glass as pale as the others', starred round where it was struck:
    a hole with teeth pointing in, its rim lit and its thickness shadowed,
    long splits running out to the frame with a dark side to each, short
    rings of cracks between them and glints. Through the hole, the empty
    quilted bed with its cut straps and a dark stain. Cold mist creeps over
    the base, and the glass is all over the floor."""
    x1 = x0 + 42
    gx0, gx1, gy0, gy1 = x0 + 4, x1 - 4, 93, 217
    r.block(x0, 80, x1, 239, 0x46524f)
    r.block(x0 + 2, 82, x1 - 2, 92, 0x7c8986)
    r.block(x0 + 2, 218, x1 - 2, 239, 0x55615f)
    r.hazard(x0 + 4, 222, x1 - 4, 224)
    for k in range(3):                                       # Its lamps, red now
        r.led(x0 + 8 + k * 4, 230, 0xe5523e if k != 1 else 0x5a2420)
    # Behind: the bed, quilted vinyl in the dark, its straps cut.
    for y in range(gy0, gy1 + 1):
        for x in range(gx0, gx1 + 1):
            t = (x - (gx0 + gx1) / 2) / ((gx1 - gx0) / 2)
            col = shade(hx(0x27404a), .6 + .5 * bands(cyl(t * .8), 4))
            if (x - gx0) % 8 == 0 and (y - gy0) % 12 < 9: col = shade(col, .82)   # Quilted seams
            if (x - gx0) % 8 == 4 and (y - gy0) % 12 == 6: col = shade(col, .7)     # ...and buttons
            r.px(x, y, col)
    for sy in (130, 176):
        r.fill(gx0, sy, gx0 + 6, sy + 2, 0x3a3328)
        r.line(gx0 + 6, sy + 1, gx0 + 9, sy + 10, 0x3a3328)
        r.fill(gx1 - 7, sy, gx1, sy + 2, 0x3a3328)
        r.line(gx1 - 7, sy + 1, gx1 - 9, sy + 14, 0x3a3328)
        r.px(gx0 + 2, sy + 1, 0xa88c4f); r.px(gx1 - 2, sy + 1, 0xa88c4f)
    r.stain((gx0 + gx1) // 2, 160, 7, 20, seed, (40, 30, 34), .55)
    # The hole: teeth pointing in, around where the blow came from.
    ix, iy = (gx0 + gx1) // 2 - 2, 140
    hole = []
    for k in range(30):
        ang = k * 2 * math.pi / 30
        rad = (8 if k % 2 else 14) + 5 * hash2(k, seed, 2)
        hole.append((ix + rad * math.cos(ang), iy + rad * 2.3 * math.sin(ang)))

    def inside(x, y):
        c = False
        for i in range(len(hole)):
            (xa, ya), (xb, yb) = hole[i], hole[(i + 1) % len(hole)]
            if (ya > y) != (yb > y) and x < xa + (y - ya) * (xb - xa) / (yb - ya):
                c = not c
        return c

    for y in range(gy0, gy1 + 1):                            # Frosted glass over the rest
        for x in range(gx0, gx1 + 1):
            if inside(x, y): continue
            t = (x - gx0 - 2) / (gx1 - gx0 - 4)
            col = mix(hx(0x8fc6d8), hx(0x3f7d96), min(1.0, abs(t - .35) * 1.7))
            col = mix(col, r.get(x, y), .22)
            edge = min(y - gy0, gy1 - y, x - gx0, gx1 - x)
            if edge < 3 and hash2(x, y, seed) > .25 * edge:
                col = mix(col, hx(0xdcf0f6), .55 - edge * .12)
            elif hash2(x, y, seed + 9) > .975:
                col = mix(col, hx(0xeefaff), .7)
            r.lit(x, y, col)
    for k in range(len(hole)):                               # The rim: lit edge, shadowed thickness
        (xa, ya), (xb, yb) = hole[k], hole[(k + 1) % len(hole)]
        n = max(abs(round(xb) - round(xa)), abs(round(yb) - round(ya)), 1)
        for i in range(n + 1):
            x, y = round(xa + (xb - xa) * i / n), round(ya + (yb - ya) * i / n)
            if gx0 <= x <= gx1 and gy0 <= y <= gy1:
                r.lit(x, y, 0xf2fbff if (y < iy) == (x < ix) else 0xb8dce6)
                inward = (1 if x < ix else -1, 1 if y < iy else -1)
                xx, yy = x + inward[0], y + inward[1]
                if inside(xx, yy): r.px(xx, yy, 0x14232a)
    for k in range(10):                                      # Splits out to the frame
        ang = k * 2 * math.pi / 10 + (hash2(k, seed, 7) - .5) * .5
        x, y = ix + 13 * math.cos(ang), iy + 30 * math.sin(ang)
        for i in range(80):
            x += math.cos(ang) * .9 + (hash2(k, i, seed) - .5) * .9
            y += math.sin(ang) * 2.1
            xi, yi = round(x), round(y)
            if not (gx0 + 1 <= xi <= gx1 - 1 and gy0 + 1 <= yi <= gy1 - 1): break
            if inside(xi, yi): continue
            r.lit(xi, yi, 0xf4fcff)
            r.lit(xi + 1, yi, mix(r.get(xi + 1, yi), hx(0x2f5866), .6))
    for ring in (1.9, 2.9):                                  # Short rings of cracks between them
        for k in range(30):
            if hash2(k, int(ring * 10), seed) < .45: continue
            a0, a1 = k * 2 * math.pi / 30, (k + 1) * 2 * math.pi / 30
            rad = 11 * ring
            xa, ya = ix + rad * math.cos(a0), iy + rad * 2.3 * math.sin(a0)
            xb, yb = ix + rad * math.cos(a1), iy + rad * 2.3 * math.sin(a1)
            n = max(abs(round(xb - xa)), abs(round(yb - ya)), 1)
            for i in range(n + 1):
                xi, yi = round(xa + (xb - xa) * i / n), round(ya + (yb - ya) * i / n)
                if gx0 + 1 <= xi <= gx1 - 1 and gy0 + 1 <= yi <= gy1 - 1 and not inside(xi, yi):
                    r.lit(xi, yi, 0xe2f4fa)
                    r.lit(xi, yi + 1, mix(r.get(xi, yi + 1), hx(0x2f5866), .5))
    for k in range(6):                                       # Glints
        gx = gx0 + 3 + int(hash2(k, seed, 13) * (gx1 - gx0 - 6))
        gy = gy0 + 6 + int(hash2(k, seed, 17) * 108)
        if not inside(gx, gy) and not inside(gx + 1, gy + 1):
            r.lit(gx, gy, 0xffffff); r.lit(gx + 1, gy + 1, 0xffffff)
            r.lit(gx - 1, gy + 1, 0xd2ecf2); r.lit(gx + 1, gy - 1, 0xd2ecf2)
    # Mist creeping over the base: soft wisps, thicker at the floor.
    for y in range(214, FLOOR):
        depth = (y - 214) / (FLOOR - 214)
        for x in range(x0 - 16, x1 + 20):
            n = fbm(x / 9, y / 2.5, seed + 4, 2)
            a = (n - .45) * 1.4 * (.3 + .7 * depth)
            if a > .08:
                cur = r.get(x, y)
                if cur and (x, y) not in r.glow:
                    r.px(x, y, mix(cur, hx(0xbcdbe4), min(.42, a)))
    for k in range(20):                                      # Glass on the floor
        x = x0 - 12 + int(hash2(k, seed, 21) * (x1 - x0 + 30))
        r.px(x, FLOOR - 1, 0xbcdde4 if k % 2 else 0x6f949c)
        if k % 3 == 0: r.lit(x + 1, FLOOR - 2, 0xf0fbff)
        if k % 4 == 1: r.px(x - 1, FLOOR - 1, 0x9ec4cc); r.px(x, FLOOR - 2, 0x9ec4cc)
    r.tints.append((ix, 160, 40, (126, 199, 224), .14))
    r.contact_shadow(x0, x1)


# ======================================================================
# Cars 09-13
# ======================================================================

def bunk(r, x0, x1, seed):
    """Two 2 m berths, with a 70 px frame and 30 px between mattresses."""
    for y0 in (183, 216):
        for y in range(y0 - 9, y0 + 5):
            for x in range(x0 + 2, x1 - 1):
                cur = r.get(x, y)
                if cur: r.px(x, y, shade(cur, .65 if y > y0 - 6 else .8))
        r.block(x0, y0 + 6, x1, y0 + 9, 0x56625f)
        r.block(x0 + 2, y0 + 2, x1 - 2, y0 + 5, 0xc9c3ad)
        for x in range(x0 + 4, x1 - 3, 4): r.vl(x, y0 + 3, y0 + 4, 0xa9a28c)
        r.hl(x0 + 3, x1 - 3, y0 + 2, 0xe8e2cc)
        bl = hx(0x5a6e4a if (y0 + seed) % 2 else 0x7a4a3a)
        for x in range(x0 + 14, x1 - 2):
            lift = round(1.4 * math.sin((x - x0) / 5 + seed)) + 2
            for y in range(y0 + 2 - lift, y0 + 6):
                k = 1.3 if y == y0 + 2 - lift else .72 if y == y0 + 5 or (x - x0) % 11 == 0 else 1.0
                r.px(x, y, shade(bl, k))
        r.block(x0 + 3, y0 - 1, x0 + 12, y0 + 2, 0xe4dfcd)
        r.hl(x0 + 4, x0 + 11, y0 - 1, 0xfffbe8)
    r.fill(x0 + 2, 226, x1 - 2, 238, 0x1c2224)
    for dx0 in (x0 + 4, (x0 + x1) // 2 + 2):
        r.block(dx0, 228, dx0 + (x1 - x0) // 2 - 8, 236, 0x4a5655)
        r.hl(dx0 + 12, dx0 + 18, 231, 0xc8c2a6)
    for x in (x0, x1):
        r.block(x - 1, 168, x + 2, 238, 0x6f7c78)
        r.px(x, 169, 0xb1bab4)
    for y in range(187, 236, 7):
        r.hl(x1 - 8, x1 - 2, y, 0x8f9a95)
        r.hl(x1 - 8, x1 - 2, y + 1, 0x3c4644)
    r.vl(x1 - 8, 180, 236, 0x6f7c78)
    r.contact_shadow(x0 - 1, x1 + 2)


def room_dormitory(r):
    """Compact bunks and personal belongings with clear space between bays."""
    bunk(r, 24, 104, 1); bunk(r, 126, 206, 4)
    r.block(273, 228, 296, 238, 0x3f4a3a)
    r.hl(275, 294, 229, 0x5a6852)
    r.line(277, 228, 284, 223, 0x2a3026); r.line(292, 228, 284, 223, 0x2a3026)
    for bx in (312, 324):
        r.block(bx, 230, bx + 4, 238, 0x3a2a20)
        r.block(bx, 235, bx + 7, 238, 0x3a2a20)
    for k, (px, py) in enumerate(((232, 164), (246, 168), (260, 162))):
        r.block(px, py, px + 8, py + 10, 0xe6e0cc)
        r.fill(px + 1, py + 1, px + 7, py + 7, (0x6a7a8a, 0x8a6a4a, 0x5a7a5a)[k])
        r.disc(px + 4, py + 4, 1, 0xd8b090)
        r.px(px + 1, py - 1, 0xd8d0b0)
    r.block(286, 161, 336, 185, 0x6c7976)
    r.vl(311, 163, 183, 0x3f4a48)
    for x in (305, 317): r.block(x, 169, x + 1, 176, 0xc8c2a6, ink=False)
    r.block(103, 177, 106, 180, 0x2a3132)
    r.line(106, 179, 113, 174, 0x3a4142)
    r.poly([(110, 173), (116, 173), (118, 178), (108, 178)], 0x3f5a4a)
    for x in range(110, 117): r.lit(x, 178, 0xfff1c8)
    r.tints.append((113, 193, 22, (255, 236, 190), .24))
    r.stain(170, 236, 14, 2, 31); r.handprint(215, 192, 2)
    r.block(28, 128, 204, 138, 0x34413e)
    r.text('DESCANSO DE LA TRIPULACION', 42, 131, 0xcfc8ae)


def room_mess(r):
    """Human-sized galley: 68 px fridge, 36 px counter and 28 px table.
    A person is about 64 px tall; the high wall belongs to the large car."""
    x0, x1, top = 26, 54, 171
    r.block(x0, top, x1, 238, 0xb9c0b8)
    r.vl(x0 + 1, top + 1, 237, 0xe6ebe4)
    r.hl(x0 + 1, x1 - 1, 193, 0x6f7874)
    r.hl(x0 + 1, x1 - 1, 194, 0xe6ebe4)
    r.block(50, 180, 51, 190, 0x8f9a95)
    r.block(50, 201, 51, 215, 0x8f9a95)
    for k, (nx, ny) in enumerate(((31, 178), (39, 182), (32, 206))):
        r.block(nx, ny, nx + 5, ny + 5, (0xe8d27a, 0xf0b0a0, 0xa0d0e8)[k])
        r.hl(nx + 1, nx + 4, ny + 2, 0x6b6a60)
        r.px(nx + 2, ny, 0xc0382b)
    r.contact_shadow(x0, x1)
    # Galley units have room to open beside the fridge.
    r.block(68, 204, 150, 207, 0x8f9a95)
    r.block(70, 208, 148, 238, 0x4a5655)
    for x in range(74, 145, 24):
        r.recess(x, 211, x + 19, 234, 0x55615f)
        r.block(x + 7, 214, x + 11, 215, 0xc8c2a6, ink=False)
    steel_cylinder(r, 76, 87, 188, 203, 0xb9c0b8)
    r.block(78, 185, 85, 188, 0x2a3132)
    r.block(80, 198, 83, 200, 0x2a3132)
    r.led(86, 195, 0xe5523e)
    r.block(100, 191, 124, 203, 0x3a4142)
    r.recess(102, 193, 116, 201, 0x101618)
    r.lit_fill(103, 194, 115, 200, 0x1a2224)
    r.lit_fill(119, 194, 122, 195, 0x7fe39a)
    for y in (198, 200): r.hl(119, 122, y, 0x8f9a95)
    r.block(136, 196, 142, 203, 0xd8d4c4)
    r.hl(137, 141, 198, 0xc0382b)
    r.contact_shadow(70, 148)
    # Plates and cups are 3-5 px wide (8-14 cm), on reachable shelves.
    r.block(70, 167, 154, 170, 0x8f9a95)
    for k in range(6):
        x = 75 + k * 4
        r.block(x, 160, x + 2, 166, 0xe1dac2)
        r.vl(x, 161, 165, 0xfffbe8)
    for k, col in enumerate((0xe1dac2, 0x6fb7d2, 0xe1dac2, 0xb5392a)):
        x = 111 + k * 10
        r.block(x, 162, x + 4, 166, col)
        r.vl(x + 5, 163, 165, col)
    r.vl(73, 171, 176, 0x5a6462); r.vl(151, 171, 176, 0x5a6462)
    r.block(212, 126, 278, 156, 0x24302d)
    r.text('MENU', 236, 130, 0xe6e0cc)
    for k in range(3):
        r.hl(219, 248 + int(hash2(k, 4, 9) * 22), 140 + k * 5, 0xa9a59a)
    # x160..192 is reserved for the playable supply crate.
    r.block(202, 211, 294, 214, 0x8d7652)
    for x in (207, 287): r.block(x, 215, x + 3, 238, 0x4e4635)
    r.block(210, 226, 286, 229, 0x6f6448)
    for x in (215, 277): r.vl(x, 230, 238, 0x4e4635)
    for k, tx in enumerate((211, 241, 272)):
        r.block(tx, 208, tx + 14, 210, 0x9aa49e)
        r.disc(tx + 4, 208, 2, (0xc89a4a, 0x8a6a3e, 0xd8c070)[k], 1)
        r.hl(tx + 9, tx + 12, 208, 0x6b8a4a if k % 2 else 0xb5392a)
    r.block(262, 205, 266, 210, 0xe1dac2)
    r.vl(267, 206, 208, 0xe1dac2)
    r.block(230, 207, 235, 210, 0xe1dac2)
    for x in range(225, 237): r.px(x, 214 + (x % 3 == 0), 0x4a2c1c)
    for y in range(215, 222): r.px(232, y, 0x4a2c1c)
    r.stain(232, 238, 6, 1.5, 9, (60, 36, 24), .7)
    r.contact_shadow(202, 294)
    r.block(308, 229, 330, 232, 0x2b3436)
    r.block(327, 218, 330, 231, 0x2b3436)
    r.line(311, 233, 307, 238, 0x4c5759)
    r.line(324, 233, 328, 238, 0x4c5759)
    r.handprint(164, 191, 6)
    # Service labels and a vent fill the tall wall without enlarging furniture.
    r.block(28, 128, 152, 144, 0x34413e)
    r.text('AGUA POTABLE', 40, 133, 0xcfc8ae)
    for x in range(34, 149, 5): r.vl(x, 145, 148, 0x1e2828)


def room_infirmary(r):
    """Cots, IV stands and medical furniture sized for the 64 px crew."""
    for k, x0 in enumerate((34, 140)):
        r.block(x0, 216, x0 + 76, 220, 0xa9b2aa)
        r.block(x0 + 2, 212, x0 + 74, 215, 0xdfe3dc)
        r.hl(x0 + 3, x0 + 73, 212, 0xffffff)
        r.block(x0 + 4, 208, x0 + 15, 212, 0xeef0ea)
        for x in range(x0 + 21, x0 + 74):
            lift = round(1.3 * math.sin((x - x0) / 4 + k)) + 1
            for y in range(211 - lift, 216):
                kk = 1.12 if y == 211 - lift else .82 if (x - x0) % 9 == 0 else 1.0
                r.px(x, y, shade(hx(0xd2dcd8), kk))
        r.block(x0 + 61, 208, x0 + 73, 211, 0x5a7a8a)
        for x in (x0 + 4, x0 + 72):
            r.vl(x, 221, 235, 0x6f7c78)
            r.disc(x, 237, 1.5, 0x22292b)
        r.hl(x0 + 4, x0 + 72, 231, 0x6f7c78)
        ix = x0 - 10
        r.vl(ix, 163, 237, 0x9aa49e)
        r.hl(ix - 5, ix + 5, 163, 0x9aa49e)
        r.block(ix - 5, 166, ix - 1, 177, 0xcfe0dc)
        r.lit_fill(ix - 4, 171, ix - 2, 176, 0xd8e6c8 if k else 0xb94a3c)
        r.line(ix - 3, 178, ix + 3, 194, 0xbfd0cc)
        r.line(ix + 3, 194, x0 + 25, 212, 0xbfd0cc)
        r.hl(ix - 5, ix + 5, 237, 0x6f7c78)
        r.contact_shadow(x0, x0 + 76)
    r.stain(178, 213, 10, 2, 14, (110, 32, 28), .7)
    r.block(236, 156, 271, 188, 0xdfe3dc)
    r.recess(239, 159, 268, 185, 0xb9c0b8)
    for y in (168, 179):
        r.hl(240, 267, y, 0x8f9a95)
        for x in range(242, 266, 6):
            r.block(x, y - 6, x + 3, y - 1, (0xd8d4c4, 0xc0382b, 0x6fb7d2)[(x // 6 + y) % 3])
    r.fill(251, 178, 255, 186, 0xc0382b); r.fill(248, 180, 258, 184, 0xc0382b)
    # Each floor item has its own footprint: cart, sink unit, then waste bin.
    r.block(234, 213, 269, 236, 0xb94a3c)
    for y in (221, 229): r.hl(236, 267, y, 0x7a2a22)
    r.block(241, 209, 260, 212, 0xe1dac2)
    for x in (239, 264): r.disc(x, 238, 1, 0x22292b)
    r.screen(242, 195, 262, 206, (232, 98, 82), 41, 'trace', mount=False)
    r.block(282, 204, 310, 208, 0x9aa49e)
    r.recess(285, 205, 307, 207, 0x6f7874)
    r.vl(297, 196, 204, 0xc6cdc6); r.hl(297, 302, 196, 0xc6cdc6)
    r.block(285, 209, 307, 238, 0x55615f)
    r.block(323, 223, 336, 238, 0xd3b93f)
    r.disc(329, 230, 3, 0x2a2622); r.disc(329, 230, 1, 0xd3b93f)
    r.contact_shadow(234, 269); r.contact_shadow(285, 307); r.contact_shadow(323, 336)
    r.block(236, 126, 336, 136, 0x34413e)
    r.text('ENFERMERIA', 264, 129, 0xcfc8ae)


def rifle(r, x, top, col=0x2c3133):
    """A 38 px rifle, about one metre, rather than a person-long weapon."""
    r.vl(x, top, top + 14, 0x5a6462)
    r.block(x - 1, top + 14, x + 2, top + 27, col)
    r.block(x + 3, top + 20, x + 4, top + 24, col)
    r.block(x - 2, top + 27, x + 3, top + 37, 0x5a4632)
    r.vl(x - 1, top + 28, top + 36, 0x7d6448)
    r.px(x, top + 2, 0x8a9690)


def room_armory(r):
    """A rifle is 38 px, a vest 22 px and the bench 28 px high."""
    r.block(24, 164, 140, 215, 0x3a4442)
    r.recess(28, 167, 136, 212, 0x1d2426)
    for k, x in enumerate(range(36, 134, 12)):
        if k == 4:
            r.block(x - 2, 206, x + 3, 210, 0x2a3132)
        else: rifle(r, x, 171 + (k % 2))
    r.hl(28, 136, 210, 0x8f9a95)
    r.block(24, 216, 140, 238, 0x46524f)
    for x in range(30, 136, 26): r.recess(x, 220, x + 22, 234, 0x3a4442)
    r.contact_shadow(24, 140)
    r.block(153, 199, 202, 202, 0x6f7c78)
    for bx in (156, 182):
        r.block(bx, 185, bx + 19, 198, 0x4f5a3a)
        r.text('HAL', bx + 3, 190, 0xd6d0ae)
    for x in (220, 246, 272):
        r.px(x + 7, 167, 0xa9b3ad)
        r.poly([(x + 2, 171), (x + 12, 171), (x + 14, 176), (x + 13, 192), (x, 192), (x - 1, 176)], 0x3c4434)
        r.vl(x + 7, 173, 190, 0x2a3026)
        r.hl(x + 1, x + 12, 178, 0x56604a)
        r.block(x + 1, 182, x + 5, 188, 0x2a3026)
        r.block(x + 9, 182, x + 12, 188, 0x2a3026)
        r.disc(x + 7, 159, 6, 0x4a5440, 5)
        r.hl(x, x + 14, 163, 0x2a3026)
    r.block(216, 211, 294, 214, 0x6f6448)
    for x in (220, 286): r.block(x, 215, x + 3, 238, 0x4e4635)
    r.fill(227, 210, 280, 211, 0xb9b09a)
    r.block(230, 207, 258, 210, 0x2c3133)
    r.block(266, 207, 271, 210, 0x5a4632)
    for k in range(4): r.px(278 + k * 3, 209, 0xc19a4c)
    r.contact_shadow(216, 294)
    # The security gate is door-sized; no furniture shares its opening.
    for x in range(308, 340, 5):
        r.vl(x, 157, 236, 0x8f9a95); r.vl(x + 1, 157, 236, 0x4f5a58)
    r.block(306, 154, 340, 157, 0x6c7876)
    r.block(306, 197, 340, 200, 0x6c7876)
    r.block(319, 204, 324, 211, 0xb08a3a)
    r.line(319, 211, 314, 220, 0x8f9a94)
    r.block(160, 128, 202, 140, 0x23302b)
    r.text('ARMERIA', 166, 132, 0xe6d27c)


def room_radio(r):
    """Radio furniture at human scale; the high map shows the large car."""
    for k, x in enumerate((24, 64)):
        r.block(x, 158, x + 30, 238, 0x3c4644)
        for j, y in enumerate(range(164, 231, 17)):
            r.recess(x + 3, y, x + 27, y + 13, 0x2a3132)
            for d in range(2):
                dx = x + 9 + d * 12
                r.disc(dx, y + 7, 3, INK); r.disc(dx, y + 7, 2, 0xd8d4c4)
                r.line(dx, y + 7, dx + (j % 3 - 1), y + 5, 0xb5392a)
            r.led(x + 25, y + 2, (0x7fe39a, 0xe8b25a, 0xe5523e)[(j + k) % 3])
        r.contact_shadow(x, x + 30)
    for y in range(44, 158):
        for k, col in enumerate((0x1b1d1f, 0x2a2f31, 0x6b2b24)):
            r.px(38 + k * 2 + (y % 5 == 0), y, col)
    r.block(124, 211, 235, 214, 0x6f6448)
    for x in (129, 228): r.block(x, 215, x + 3, 238, 0x4e4635)
    rx = 133
    r.block(rx, 188, rx + 27, 210, 0x8f9a95)
    for k, cx in enumerate((rx + 7, rx + 20)):
        r.disc(cx, 196, 6, INK); r.disc(cx, 196, 5, 0x6b4a2a)
        r.disc(cx, 196, 2, 0xc6cdc6)
        for a in range(3):
            ang = a * 2 * math.pi / 3 + k
            r.px(round(cx + 3 * math.cos(ang)), round(196 + 3 * math.sin(ang)), 0x2a1f16)
    r.hl(rx + 6, rx + 21, 202, 0x4a3420)
    for k in range(4): r.block(rx + 3 + k * 6, 205, rx + 6 + k * 6, 207, 0x2a3132)
    r.screen(185, 191, 208, 205, (127, 208, 138), 51, 'trace', mount=False)
    r.block(214, 207, 228, 210, 0x6b2b24)
    r.paper(165, 208, 8, 3)
    r.px(239, 183, 0xa9b3ad)
    r.line(235, 188, 239, 183, 0x2a3132); r.line(243, 188, 239, 183, 0x2a3132)
    r.block(233, 188, 236, 194, 0x2a3132); r.block(242, 188, 245, 194, 0x2a3132)
    r.line(235, 195, 236, 208, 0x1b1d1f)
    r.block(254, 140, 338, 190, 0xcfc8ae)
    for y in range(142, 189):
        for x in range(256, 337):
            if (x - 256) % 14 == 0 or (y - 142) % 11 == 0: r.px(x, y, 0xa49f8a)
    r.line(258, 180, 300, 158, 0x6fb7d2); r.line(300, 158, 336, 166, 0x6fb7d2)
    for k, (px, py) in enumerate(((272, 154), (296, 180), (318, 160), (330, 180))):
        r.disc(px, py, 1, 0x3f74a8 if k == 2 else 0xc0382b)
    r.line(272, 154, 318, 160, 0xc0382b)
    r.text('SANTA BRASA', 260, 144, 0x3a3328)
    r.block(276, 211, 338, 238, 0x46524f)
    for y in (215, 226):
        r.recess(280, y, 334, y + 8, 0x55615f)
        r.hl(302, 309, y + 3, 0xc8c2a6)
    # Pulled to the side of the desk: no chair drawn through its pedestal.
    r.block(246, 222, 260, 225, 0x2b3436)
    r.block(258, 205, 261, 222, 0x2b3436)
    r.vl(253, 226, 236, 0x4c5759); r.hl(247, 259, 237, 0x4c5759)
    r.contact_shadow(124, 235); r.contact_shadow(276, 338)
    r.stain(110, 237, 8, 2, 52)


def hanging_suit(c, ox):
    """A native 64 px suit in the 80 px cell, boots on its bottom row."""
    yel, ink, cx = hx(0xd7ae3a), hx(0x2a2010), ox + 16
    for y in range(19, 74):
        if y < 23: half = 3 + (y - 19)
        elif y < 32: half = 6
        elif y < 36: half = 7 + (y - 32) // 2
        elif y < 57: half = 8 - (y - 36) // 15
        else: half = 6
        for x in range(cx - half, cx + half):
            col = shade(yel, .62 + .62 * bands(cyl((x - cx + .5) / half), 5))
            c.set(x, y, col)
        c.set(cx - half - 1, y, ink); c.set(cx + half, y, ink)
    for y in range(58, 74): c.set(cx - 1, y, ink); c.set(cx, y, ink)
    c.set(cx - 1, 16, hx(0x3a3a34)); c.set(cx, 16, hx(0x3a3a34))
    c.set(cx - 2, 17, hx(0x3a3a34)); c.set(cx + 1, 17, hx(0x3a3a34))
    for y in range(23, 30):
        for x in range(cx - 5, cx + 5):
            if ((x - cx + .5) / 5) ** 2 + ((y - 26) / 3.5) ** 2 <= 1:
                c.set(x, y, mix(hx(0x284650), hx(0x15262c), (y - 23) / 7))
    c.hline(cx - 4, cx - 1, 24, hx(0x9cc8cc))
    c.fill(cx - 2, 30, cx + 1, 32, hx(0x2b2c27))
    for y in range(35, 57, 2): c.set(cx + 1, y, hx(0x8c6f20))
    for y, col in ((41, hx(0xc9d0c6)), (42, hx(0x8a918a))):
        c.hline(cx - 7, cx + 6, y, col)
    for y in (67, 68):
        c.hline(cx - 6, cx - 2, y, hx(0xb9c0b6))
        c.hline(cx + 1, cx + 5, y, hx(0xb9c0b6))
    for side in (-1, 1):
        for y in range(35, 56):
            ax = cx + side * 9 + (0 if side < 0 else -1)
            c.set(ax, y, shade(yel, .78)); c.set(ax + side, y, shade(yel, 1.15 if side < 0 else .95))
            c.set(ax + side * 2, y, ink)
        c.fill(cx - 12 if side < 0 else cx + 8, 56, cx - 9 if side < 0 else cx + 11, 60, hx(0x2b2c27))
        x0 = cx - 6 if side < 0 else cx + 1
        c.fill(x0, 74, x0 + 4, 79, hx(0x2b2c27))
        c.hline(x0, x0 + 4, 74, hx(0x5a5b52))
        c.vline(x0 - 1, 74, 79, ink); c.vline(x0 + 5, 74, 79, ink)
        c.hline(x0, x0 + 4, 79, hx(0x15160f))


def tablet_art(c, ox):
    """A rugged 30 cm tablet, twelve pixels wide, aligned with its stand."""
    x0, y0, x1, y1 = ox + 10, 71, ox + 21, 79
    c.fill(x0, y0, x1, y1, hx(0x14181a))
    c.fill(x0 + 1, y0 + 1, x1 - 1, y1 - 1, hx(0x1f5f5a))
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)): c.set(x, y, hx(0xc8902e))
    for row in range(2):
        for k in range(3):
            x, y = x0 + 2 + k * 3, y0 + 2 + row * 3
            c.hline(x, x + 1, y, hx(0xf0c070 if (row, k) == (0, 0) else 0x8fe8de))
    c.set(x0 + 1, y0 + 1, hx(0xd8fff6))


def make_gear():
    c = Canvas(GEAR_W * 2, GEAR_H)
    hanging_suit(c, 0)
    tablet_art(c, GEAR_W)
    return c
