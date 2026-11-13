#!/usr/bin/env python3
"""Draw the 21 off-road buildings at the landscape's human scale.

Usage: tools/make_houses.py [assets_dir]

Each 256 x 192 frame stands on its last row, with a door about 60 art
pixels tall (Dolores is 56). The order is HOUSE_FRAMES in config.h and the
house indices in themes.c. Materials are drawn in daylight; scene.c grades
them into each landscape's light. Only actual lamps/window light use alpha
254, which the grader preserves. Standard library only, deterministic.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape_kit import Canvas, Rng, hash2, hx, mix, sheet, save_all  # noqa: E402
from scenery_materials import planks as material_planks, masonry, metal, window, lettering  # noqa: E402

W, H, FLOOR = 256, 192, 191
INK = hx(0x28282b)
HOLE = hx(0x25292d)
WOOD = hx(0x987653)
PALE_WOOD = hx(0xb8a17a)
GREY_WOOD = hx(0x837f70)
RED_WOOD = hx(0x956255)
TRIM = hx(0xbfb293)
STONE = hx(0xa19a86)
IRON = hx(0x777d7b)
RUST = hx(0x925d43)
ROOF = hx(0x77766e)
GLASS = hx(0x667e87)


def planks(c: Canvas, bounds, base, seed=1, vertical=False, width=7) -> None:
    """Cladding with staggered butt joints and a few knots in the grain.

    The marks belong to individual boards: no noise is laid over windows,
    trim, empty space or an already finished facade.
    """
    material_planks(c, bounds, base, seed=seed, vertical=vertical, width=width)
    x0, y0, x1, y1 = bounds
    base = hx(base)
    across = x1-x0+1 if vertical else y1-y0+1
    length = y1-y0+1 if vertical else x1-x0+1
    if width < 6 or length < 20:
        return

    def mark(a, b, color):
        if 0 <= a < across and 0 <= b < length:
            x, y = (x0+a, y0+b) if vertical else (x0+b, y0+a)
            c.set(x, y, color)

    for board in range(across//width):
        k = board*width + width//2
        along = 8 + int(hash2(board, 1, seed+37)*max(1, length-15))
        if hash2(board, 2, seed+37) > .4:
            # A dark oval heart, two enclosing fibres and a lit lower lip.
            for a,b in ((-1,-2),(-1,-1),(0,-3),(0,3),(1,-1),(1,1)):
                mark(k+a, along+b, mix(base,INK,.23))
            mark(k,along,mix(base,INK,.6))
            mark(k,along+1,mix(base,INK,.35))
            mark(k+1,along+2,mix(base,TRIM,.3))
        if length > 65:
            joint = 24 + int(hash2(board,3,seed+37)*max(1,length-45))
            for a in range(1,width):
                mark(board*width+a,joint,mix(base,INK,.48))
            for b in (joint-3,joint+3):
                mark(k,b,mix(base,INK,.6))
                mark(k-1,b-1,mix(base,TRIM,.36))
        if board%3 == 1:
            # A shallow end split, tapering into the board rather than a stripe.
            for b in range(2,7):
                mark(k+(b>4),b,mix(base,INK,.29))


def frame() -> Canvas:
    return Canvas(W, H)


def beam(c: Canvas, x0: int, y0: int, x1: int, y1: int, color=WOOD, width=4) -> None:
    """A solid timber, with a chipped lit edge and nail heads."""
    c.line(x0, y0 + 1, x1, y1 + 1, mix(color, INK, .52), width + 1)
    c.line(x0, y0, x1, y1, color, width)
    c.line(x0, y0, x1, y1, mix(color, TRIM, .42))
    c.set(x0 + width // 2, y0 + 2, INK)
    c.set(x1 + width // 2, y1 - 2, INK)
    if width >= 4 and x0 == x1 and abs(y1-y0) > 25:
        ym = (y0+y1)//2
        c.vline(x0+2,ym-3,ym+3,mix(color,INK,.27))
        c.set(x0+3,ym+3,mix(color,TRIM,.25))
        for y in range(y1-8,y1-2):
            c.set(x0+width-1,y,mix(color,INK,.3))


def box(c: Canvas, bounds, color, edge=TRIM) -> None:
    x0, y0, x1, y1 = bounds
    c.fill(x0, y0, x1, y1, color)
    c.hline(x0, x1, y0, mix(color, edge, .55))
    c.vline(x0, y0, y1, mix(color, edge, .32))
    c.hline(x0, x1, y1, mix(color, INK, .65))
    c.vline(x1, y0, y1, mix(color, INK, .45))


def foundation(c: Canvas, x0: int, x1: int, height=7) -> None:
    masonry(c, (x0, FLOOR-height+1, x1, FLOOR), hx(0x827c69), seed=x0+7, brick=(17, 5))
    c.hline(x0, x1, FLOOR-height+1, hx(0xb3a78a))
    c.hline(x0, x1, FLOOR, hx(0x4d463b))


def boardwalk(c: Canvas, x0: int, x1: int, top=184) -> None:
    planks(c, (x0, top, x1, FLOOR), GREY_WOOD, seed=x0+top, width=4)
    c.hline(x0, x1, top, hx(0xb0a68e))
    for x in range(x0 + 7, x1, 21):
        c.vline(x, top, FLOOR, hx(0x555148))
        c.set(x + 2, top + 2, INK)


def door(c: Canvas, x: int, bottom=184, width=28, height=61, barred=False, color=WOOD) -> None:
    y = bottom - height
    box(c, (x-3, y-4, x+width+3, bottom+1), mix(color, TRIM, .45))
    c.fill(x, y, x+width, bottom, HOLE)
    planks(c, (x+2, y+2, x+width-2, bottom-1), color, seed=x+height, vertical=True, width=6)
    # Recessed panels and a glazed upper panel, all inside a human-sized jamb.
    box(c, (x+5, y+8, x+width-5, y+height//2-2), mix(color, INK, .24), color)
    box(c, (x+5, y+height//2+6, x+width-5, bottom-7), mix(color, INK, .18), color)
    # Worn jamb edges, a raised lock escutcheon and a turned brass handle.
    c.vline(x-2,y+2,bottom-3,mix(color,TRIM,.6))
    for yy in (y+12,y+31,bottom-9):
        c.vline(x-2,yy,yy+2,mix(color,INK,.12))
    lock_y = y+height//2
    box(c,(x+width-7,lock_y-1,x+width-3,lock_y+7),hx(0x8e784e))
    c.hline(x+width-6,x+width-2,lock_y+1,hx(0xc2ab6f))
    c.set(x+width-5,lock_y+5,INK)
    for yy in (y+11, bottom-12):
        c.hline(x, x+7, yy, INK)
        c.hline(x+1, x+5, yy-1, IRON)
        c.set(x+2, yy, mix(IRON,TRIM,.35))
        c.set(x+6, yy, mix(IRON,TRIM,.35))
    if barred:
        c.fill(x+5, y+7, x+width-5, y+28, HOLE)
        for bx in range(x+7, x+width-4, 5):
            c.vline(bx, y+7, y+28, IRON)
        c.hline(x+5, x+width-5, y+18, IRON)
    c.hline(x-4, x+width+4, bottom+2, hx(0xb7aa8c))
    for xx in range(x+4,x+width-2,6):
        c.hline(xx,xx+2,bottom-4,mix(color,TRIM,.42))
        c.set(xx+2,bottom-3,mix(color,INK,.3))
    c.hline(x-3,x+width+3,y-3,mix(TRIM,color,.35))
    c.hline(x+1,x+width-1,y+1,mix(color,INK,.48))


def sash(c: Canvas, x: int, y: int, width=23, height=30, lit=False, boards=False, arched=False) -> None:
    # Projecting sill and top drip moulding give the window depth.
    window(c, x, y, width, height, lit=lit, broken=boards)
    if not boards and width >= 20 and height >= 22:
        # Curtains sit behind the sash. Their taper and folds leave the glass
        # visible, so lit windows have depth rather than one yellow rectangle.
        curtain=hx(0xa18c73) if lit else hx(0x59645b)
        for yy in range(2,height-1):
            spread=4 if yy<height//3 or yy>height*3//4 else 2
            for side in (0,1):
                for xx in range(spread):
                    px=x+1+xx if side==0 else x+width-2-xx
                    c.set(px,y+yy,mix(curtain,INK,.16 if xx%2 else 0))
        c.hline(x+1,x+width-2,y+1,mix(curtain,INK,.2))
        for xx in (x+width//2,x+width//2-1):
            c.vline(xx,y,y+height-1,hx(0x675b4a))
        c.hline(x,x+width-1,y+height//2,hx(0x675b4a))
    elif not boards and width >= 14:
        # A diagonal reflection confined to one pane of unlit glass.
        if not lit:
            c.line(x+3,y+4,x+width//2-3,y+height//2-3,mix(GLASS,TRIM,.12))
    box(c, (x-3, y-4, x+width+2, y-2), TRIM)
    box(c, (x-4, y+height, x+width+3, y+height+3), mix(TRIM, INK, .12))
    c.vline(x-2, y-1, y+height-1, mix(TRIM, INK, .12))
    c.vline(x+width+1, y-1, y+height, mix(TRIM, INK, .35))
    for xx in (x-2,x+width):
        c.vline(xx,y+height+4,y+height+6,mix(TRIM,INK,.38))
        c.set(xx,y+height+4,mix(TRIM,INK,.13))
    c.hline(x+4,x+9,y+height+1,mix(TRIM,INK,.35))
    c.set(x+9,y+height+2,mix(TRIM,INK,.5))
    if arched:
        cx = x + width/2
        for yy in range(y-10, y):
            half = math.sqrt(max(0, (width/2)**2 - (yy-y)**2))
            c.hline(round(cx-half), round(cx+half), yy, mix(TRIM, INK, .12))
        c.hline(x+3, x+width-3, y-1, HOLE)
    if boards:
        beam(c, x-2, y+height-8, x+width+1, y+9, GREY_WOOD, 3)


def roof(c: Canvas, x0: int, x1: int, top: int, eave: int, color=ROOF, seed=1, hip=0) -> None:
    """Gable roof: staggered shingles on its two differently lit faces."""
    cx = (x0+x1)//2
    for y in range(top, eave+1):
        f = (y-top)/max(1, eave-top)
        half = int((x1-x0)*.5*f)
        left, right = cx-half, cx+half
        row = (y-top)//5
        for x in range(left, right+1):
            n = hash2((x+row*5)//9, row, seed)
            col = mix(color, TRIM, .05 + n*.14) if x < cx else mix(color, INK, .12+n*.16)
            if (y-top)%5 == 4 or (x+row*5)%10 == 0:
                col = mix(color, INK, .37)
            if (y-top)%5 == 0 and (x+row*5)%10 not in (0, 1):
                col = mix(color, TRIM, .26)
            # A few slipped or chipped shingles expose the dark felt below.
            shingle=(x+row*5)//10
            if hash2(shingle,row,seed+71)>.97 and (y-top)%5 in (2,3,4):
                col=mix(color,INK,.46 if (x+row*5)%10<5 else .24)
            c.set(x, y, col)
    beam(c, cx, top, x0-3, eave+2, mix(color, TRIM, .25), 3)
    beam(c, cx, top, x1+1, eave+2, mix(color, INK, .12), 3)
    # The gutter has a curved lip, a shadowed trough and regular hangers.
    c.hline(x0-3, x1+4, eave+4, mix(IRON,TRIM,.25))
    c.hline(x0-3, x1+4, eave+5, mix(IRON,INK,.3))
    c.hline(x0-2, x1+3, eave+6, INK)
    for xx in range(x0+7,x1,24):
        c.vline(xx,eave+4,eave+6,mix(IRON,INK,.4))
    for yy in range(top+7,eave,14):
        c.hline(cx-2,cx+2,yy,mix(color,TRIM,.4))
    if hip:
        box(c, (cx-3, top-2, cx+3, top+3), mix(color, TRIM, .4))


def chimney(c: Canvas, x: int, top: int, bottom: int, width=16) -> None:
    masonry(c, (x, top, x+width, bottom), hx(0x8e7a69), seed=x, brick=(9, 5))
    box(c, (x-3, top-3, x+width+3, top+1), hx(0x9a8d79))
    c.hline(x, x+width, top-3, hx(0x3d3b36))
    c.hline(x+3,x+width-3,top-2,hx(0x28282a))
    for xx in (x+3,x+width-4):
        for yy in range(top+2,min(bottom,top+18)):
            old=c.get(xx,yy)
            if old:c.set(xx,yy,mix(old,INK,.38*(1-(yy-top)/20)))
    c.line(x+3,top+25,x+5,min(bottom,top+33),hx(0x60594e))
    c.vline(x+width, top+2, bottom, hx(0x504a42))


def sign(c: Canvas, text: str, x0: int, y: int, width: int, color=WOOD, small=False) -> None:
    height=12 if small else 18
    box(c, (x0, y, x0+width, y+height), mix(color, INK, .38))
    planks(c, (x0+2, y+2, x0+width-2, y+height-2), color, seed=x0+y, width=6)
    scale=1 if small else 2
    tw=(len(text)*4-1)*scale
    lettering(c, text, x0+(width-tw)//2, y+(height-5*scale)//2, hx(0xe0cc9a), scale=scale)
    for x in (x0+3,x0+width-3):
        c.set(x,y+3,IRON)
        c.set(x,y+height-3,INK)


def porch(c: Canvas, x0: int, x1: int, top: int, bottom=184, posts=4, color=WOOD, rail=False) -> None:
    planks(c, (x0-4, top, x1+5, top+9), mix(color, GREY_WOOD, .35), seed=top, width=4)
    c.hline(x0-4,x1+5,top,hx(0xc1b18c))
    c.hline(x0-4,x1+5,top+10,INK)
    for x in range(x0+8,x1,15):
        c.vline(x,top+6,top+10,mix(color,INK,.5))
        c.set(x-1,top+6,mix(color,TRIM,.4))
    for i in range(posts):
        x=x0+(x1-x0)*i//(posts-1)
        beam(c,x,top+11,x,bottom,color,4)
        # Two-sided knee braces and a shaped corbel under the porch beam.
        c.line(x+4,top+23,x+17,top+11,mix(color,TRIM,.2),2)
        c.line(x,top+23,x-11,top+11,mix(color,INK,.12),2)
        box(c,(x-2,top+10,x+7,top+14),color)
        c.set(x+7,top+15,mix(color,TRIM,.2))
        box(c,(x-2,bottom-3,x+6,bottom),hx(0x746e5c))
    if rail:
        rail_y=bottom-19
        for xa,xb in ((x0,x0+43),(x1-43,x1)):
            beam(c,xa,rail_y,xb,rail_y,color,3)
            for x in range(xa+5,xb,9):
                c.vline(x,rail_y+1,bottom,color)


def barrel(c: Canvas, x: int, bottom=184, width=17, height=24) -> None:
    for y in range(bottom-height,bottom+1):
        taper=2 if y in (bottom-height,bottom) else 1 if y in (bottom-height+1,bottom-1) else 0
        for xx in range(x+taper,x+width-taper+1):
            k=(xx-x)//4
            col=mix(WOOD,INK,.12) if (xx-x)%4==0 else mix(WOOD,TRIM,.08-k*.018)
            c.set(xx,y,col)
    for yy in (bottom-height+5,bottom-5):
        box(c,(x,yy,x+width,yy+2),IRON)
        c.set(x+width-3,yy+1,INK)
    c.hline(x+3,x+width-3,bottom-height,TRIM)


def crates(c: Canvas, x: int, bottom=184, count=2) -> None:
    for i in range(count):
        xx=x+(i%2)*21
        yy=bottom-(i//2)*20
        planks(c,(xx,yy-19,xx+19,yy),PALE_WOOD,seed=i+xx,vertical=True,width=5)
        box(c,(xx,yy-19,xx+19,yy-17),WOOD)
        box(c,(xx,yy-2,xx+19,yy),WOOD)
        beam(c,xx+2,yy-16,xx+16,yy-4,WOOD,2)


def lantern(c: Canvas,x:int,y:int) -> None:
    c.line(x,y-5,x+7,y-5,IRON,2)
    c.vline(x+7,y-5,y,IRON)
    box(c,(x+3,y,x+11,y+13),hx(0x58594f))
    for yy in range(y+3,y+11):
        for xx in range(x+5,x+10):
            c.light(xx,yy,hx(0xd99e57) if xx in (x+5,x+9) else hx(0xe8c582))
    c.hline(x+2,x+12,y+12,INK)


def saloon() -> Canvas:
    c=frame()
    planks(c,(36,41,218,184),WOOD,seed=101,width=7)
    planks(c,(191,41,218,184),mix(WOOD,INK,.18),seed=102,width=7)
    planks(c,(28,30,226,70),RED_WOOD,seed=103,width=7)
    box(c,(74,15,181,30),RED_WOOD)
    box(c,(25,27,229,32),TRIM)
    box(c,(70,12,185,17),TRIM)
    sign(c,'SALOON',65,36,125,WOOD)
    for x in (47,111,176):
        sash(c,x,76,25,34,lit=x==47,boards=x==176)
    # Balcony attached to the second storey, with a narrow open stair landing.
    box(c,(24,117,231,123),GREY_WOOD)
    beam(c,25,103,228,103,PALE_WOOD,3)
    for x in range(28,228,11):
        beam(c,x,104,x,116,WOOD,2)
    porch(c,28,225,124,posts=4,color=PALE_WOOD)
    c.fill(103,140,149,184,HOLE)
    for x in (106,130):
        planks(c,(x,149,x+17,175),WOOD,seed=x,width=7)
        c.line(x+1,151,x+15,170,PALE_WOOD,2)
    sash(c,51,143,28,25,lit=True)
    sash(c,177,143,25,25,boards=True)
    barrel(c,205,183)
    lantern(c,89,142)
    boardwalk(c,20,237)
    return c


def cabin() -> Canvas:
    c=frame()
    chimney(c,174,35,118,18)
    planks(c,(39,106,211,184),GREY_WOOD,seed=201,width=8)
    planks(c,(184,106,211,184),mix(GREY_WOOD,INK,.18),seed=202,width=8)
    roof(c,28,223,46,105,ROOF,203)
    # Roof boards, fascia and a hand-sawn porch.
    beam(c,39,108,39,184,PALE_WOOD,4)
    beam(c,207,108,207,184,WOOD,4)
    door(c,104,width=30,height=63,color=GREY_WOOD)
    sash(c,57,130,27,30,lit=True)
    sash(c,160,130,27,30,boards=True)
    porch(c,34,218,115,posts=3,color=WOOD)
    for row in range(3):
        for k in range(4-row):
            x,y=218+k*7+row*3,181-row*7
            c.disc(x,y,4,WOOD,3)
            c.disc(x,y,2,PALE_WOOD,2)
            c.set(x,y,mix(WOOD,INK,.45))
    boardwalk(c,30,221)
    return c


def barn() -> Canvas:
    c=frame()
    planks(c,(27,72,230,184),RED_WOOD,seed=301,vertical=True,width=8)
    # Gambrel roof makes the barn unmistakable; each pitch has different light.
    points=[(20,80),(47,39),(84,19),(174,19),(210,39),(238,80)]
    c.poly(points,hx(0x625f57))
    for y in range(21,81):
        for x in range(20,239):
            if c.get(x,y)==hx(0x625f57):
                pitch=.18 if y<40 else .02
                col=mix(ROOF,INK,pitch+.07*hash2(x//9,y//5,304))
                if y%5==0 or (x+(y//5)*5)%11==0: col=mix(col,INK,.3)
                c.set(x,y,col)
    for a,b in zip(points,points[1:]): beam(c,*a,*b,mix(ROOF,TRIM,.3),3)
    box(c,(23,81,235,85),TRIM)
    planks(c,(98,49,158,81),WOOD,seed=305,vertical=True,width=7)
    c.fill(104,52,151,76,HOLE)
    for x in range(107,150,3): c.line(x,74,x+4,69,hx(0xb19b55))
    beam(c,121,31,137,31,PALE_WOOD,4)
    c.vline(129,34,65,hx(0x9f936e))
    c.disc(129,64,3,IRON,3)
    for x in (77,130):
        planks(c,(x,115,x+49,183),WOOD,seed=x,vertical=True,width=8)
        for yy in (115,179): box(c,(x,yy,x+49,yy+4),TRIM)
        beam(c,x+3,120,x+43,177,PALE_WOOD,3)
        beam(c,x+43,120,x+3,177,PALE_WOOD,3)
    box(c,(72,108,184,114),TRIM)
    beam(c,128,115,128,184,mix(WOOD,INK,.6),2)
    sash(c,40,101,20,24,boards=True)
    sash(c,195,101,20,24)
    crates(c,30,184,2)
    foundation(c,24,237)
    return c


def ruined() -> Canvas:
    c=frame()
    chimney(c,184,25,185,21)
    planks(c,(34,101,89,184),GREY_WOOD,seed=401,width=8)
    planks(c,(125,136,214,184),mix(GREY_WOOD,INK,.12),seed=402,width=7)
    for x in range(34,90):
        for y in range(101,101+int(hash2(x//5,0,403)*13)):
            c.clear(x,y)
    for x in range(125,215):
        for y in range(136,136+int(hash2(x//7,0,404)*11)):
            c.clear(x,y)
    # The surviving fireplace belongs to the right-hand wall: a broad masonry
    # breast rises from the shared foundation and narrows into the flue. Keep
    # it in front of the broken cladding so it cannot read as an isolated post.
    masonry(c,(172,133,214,184),hx(0x8e7a69),seed=407,brick=(10,6))
    c.poly([(178,133),(184,114),(205,114),(212,133)],hx(0x7d7163))
    for yy in (119,125,131):
        c.hline(183-(yy-119)//3,207+(yy-119)//4,yy,hx(0x554f47))
    box(c,(169,143,217,148),hx(0x9c8e77))
    c.hline(169,217,143,TRIM)
    c.fill(182,153,203,181,HOLE)
    c.fill(184,154,201,179,hx(0x191c1e))
    c.hline(181,204,151,hx(0x4a423a))
    c.hline(180,205,182,hx(0xb0a18a))
    for xx in range(185,201,4):
        c.line(xx,177,xx+2,179,hx(0x5b5145))
    sash(c,49,127,23,30,boards=True)
    beam(c,32,85,151,145,GREY_WOOD,5)
    beam(c,95,54,169,135,WOOD,5)
    beam(c,73,84,115,184,WOOD,4)
    beam(c,105,100,179,184,GREY_WOOD,3)
    # Broken roof timbers meet the flue at a visible flashing collar.
    beam(c,118,88,183,105,GREY_WOOD,4)
    beam(c,160,132,183,105,WOOD,3)
    box(c,(181,101,207,105),hx(0x686b62))
    c.hline(181,207,101,hx(0x9b9c8c))
    c.vline(181,103,111,hx(0x424a45))
    for i in range(24):
        x=40+i*7
        y=181-int(hash2(i,0,406)*7)
        beam(c,x,y,x+12,y-2-(i%3),GREY_WOOD,2)
    for i in range(14):
        x=92+i*7
        box(c,(x,185-i%3,x+5,190),hx(0x8c806a))
    foundation(c,28,226,5)
    return c


def water_tower() -> Canvas:
    c=frame()
    for x in (77,167):
        beam(c,x,85,x-5 if x<128 else x+5,187,WOOD,7)
        box(c,(x-8,185,x+9,191),STONE)
    for ya,yb in ((93,139),(140,183)):
        beam(c,83,ya,168,yb,GREY_WOOD,4)
        beam(c,168,ya,80,yb,WOOD,4)
    beam(c,76,139,176,139,PALE_WOOD,5)
    box(c,(62,87,191,95),GREY_WOOD)
    # Tank's staves follow its cylinder, with darker flanks and iron hoops.
    for y in range(31,87):
        for x in range(70,185):
            t=(x-70)/114
            shade=abs(t-.34)*.5
            col=mix(PALE_WOOD,INK,shade)
            if (x-70)%7==0: col=mix(col,INK,.35)
            if hash2(x//3,y,501)>.965: col=mix(col,TRIM,.28)
            c.set(x,y,col)
    for y in (42,66,82):
        box(c,(69,y,185,y+3),IRON)
        for x in range(75,184,13): c.set(x,y+1,INK)
    roof(c,63,191,4,30,ROOF,502)
    # Deck rail, manhole and ladder are distinct from the supporting trestle.
    for x in range(65,190,13): beam(c,x,78,x,86,WOOD,2)
    beam(c,64,77,188,77,PALE_WOOD,2)
    box(c,(98,47,119,64),WOOD)
    c.hline(101,116,50,PALE_WOOD)
    for x in (121,131): beam(c,x,94,x,185,GREY_WOOD,2)
    for y in range(99,186,8): c.hline(121,133,y,TRIM)
    beam(c,186,60,197,60,IRON,3)
    beam(c,196,60,196,102,IRON,3)
    return c


def church() -> Canvas:
    c=frame()
    masonry(c,(38,105,217,184),hx(0xb6ac91),seed=601,brick=(20,9))
    roof(c,26,229,48,104,hx(0x777e7e),602)
    # A bell tower with an open belfry and a narrow steeple.
    masonry(c,(104,36,153,129),hx(0xb3aa8e),seed=603,brick=(15,7))
    c.poly([(98,38),(128,4),(159,38)],hx(0x747b79))
    beam(c,128,4,99,38,TRIM,2)
    box(c,(99,36,159,42),TRIM)
    c.fill(115,52,143,76,HOLE)
    c.disc(129,58,8,HOLE,8)
    c.disc(129,65,6,hx(0xb49c61),8)
    c.hline(120,139,73,hx(0x7c7150))
    c.line(128,0,128,9,TRIM,2)
    c.line(123,4,134,4,TRIM,2)
    door(c,111,width=33,height=61,color=hx(0x82745b))
    sash(c,58,126,22,36,lit=True,arched=True)
    sash(c,177,126,22,36,lit=True,arched=True)
    foundation(c,34,223)
    return c


def sheriff() -> Canvas:
    c=frame()
    planks(c,(32,54,224,184),GREY_WOOD,seed=701,width=7)
    planks(c,(203,54,224,184),mix(GREY_WOOD,INK,.2),seed=702,width=7)
    box(c,(27,48,229,55),TRIM)
    box(c,(61,29,195,49),WOOD)
    sign(c,'SHERIFF',68,31,120,WOOD)
    sash(c,51,75,29,32)
    sash(c,106,75,29,32)
    sash(c,167,75,29,32,boards=True)
    porch(c,24,230,120,posts=4,color=PALE_WOOD)
    door(c,117,width=28,height=59,color=GREY_WOOD)
    sash(c,52,137,35,29)
    for x in range(56,85,6): c.vline(x,140,163,IRON)
    sash(c,170,137,30,29)
    for x in range(174,198,6): c.vline(x,140,163,IRON)
    # Five-point sheriff's star on the wall, not a large featureless sign.
    pts=[]
    for k in range(10):
        a=-math.pi/2+k*math.pi/5
        r=7 if k%2==0 else 3
        pts.append((99+math.cos(a)*r,148+math.sin(a)*r))
    c.poly(pts,hx(0xbba66d))
    lantern(c,151,137)
    boardwalk(c,20,237)
    return c


def smithy() -> Canvas:
    c=frame()
    masonry(c,(36,100,218,184),hx(0x928b7b),seed=801,brick=(18,8))
    roof(c,25,230,45,99,hx(0x6d716d),802)
    chimney(c,182,21,103,20)
    sign(c,'HERRERIA',70,104,120,WOOD,small=True)
    # Wide open working bay: cooled forge, anvil and bellows.
    c.fill(76,126,181,184,HOLE)
    beam(c,72,121,181,121,WOOD,6)
    for x in (72,180): beam(c,x,124,x,184,WOOD,5)
    masonry(c,(148,155,172,184),hx(0x68665c),seed=803,brick=(9,5))
    c.fill(151,150,168,156,hx(0x3a3531))
    for x in range(154,167,3): c.light(x,154,hx(0xb6673e))
    c.poly([(102,159),(128,159),(135,156),(135,163),(128,166),(112,166),(109,172),(120,176),(98,176),(107,169),(107,165),(99,164)],IRON)
    beam(c,113,177,113,184,GREY_WOOD,10)
    sash(c,46,126,19,30,boards=True)
    # Iron horseshoes outside, tools hanging in the open bay.
    for x in (191,202):
        c.disc(x,136,4,IRON,5)
        c.disc(x,135,2,HOLE,3)
        c.clear(x,131)
    for x in (91,101,114):
        c.vline(x,131,147,IRON)
        c.hline(x-2,x+3,132,IRON)
    foundation(c,31,225)
    return c


def stable() -> Canvas:
    c=frame()
    planks(c,(24,90,233,184),hx(0x95806b),seed=901,vertical=True,width=8)
    roof(c,16,240,45,89,ROOF,902)
    sign(c,'ESTABLO',77,95,100,WOOD,small=True)
    for x in (45,128):
        c.fill(x,122,x+64,184,HOLE)
        planks(c,(x+2,151,x+61,182),WOOD,seed=x,vertical=True,width=7)
        beam(c,x+1,151,x+60,151,PALE_WOOD,4)
        beam(c,x+3,178,x+58,156,PALE_WOOD,3)
        beam(c,x-4,117,x+65,117,PALE_WOOD,5)
        beam(c,x-4,121,x-4,184,WOOD,5)
    # Hay bales and a hanging leather bridle.
    planks(c,(205,162,235,184),hx(0xb8a16b),seed=905,width=3)
    for x in (211,230): c.vline(x,162,184,hx(0x756346))
    c.line(27,122,27,143,hx(0x735342),2)
    c.disc(28,144,5,hx(0x735342),7)
    c.disc(28,144,3,HOLE,5)
    boardwalk(c,21,238)
    return c


def bank() -> Canvas:
    c=frame()
    masonry(c,(36,48,221,184),hx(0xafa795),seed=1001,brick=(22,9))
    pediment=hx(0x9a9687)
    c.poly([(26,48),(127,15),(231,48)],pediment)
    for y in range(17,49):
        row=(y-15)//7
        for x in range(26,232):
            if c.get(x,y)!=pediment:continue
            offset=(x+row*13)%26
            col=mix(pediment,INK,.08*hash2(x//26,row,1003))
            if (y-15)%7==6 or offset==25:col=mix(col,INK,.18)
            c.set(x,y,col)
    beam(c,127,15,28,48,TRIM,3)
    beam(c,127,15,227,48,hx(0x8d8b7c),3)
    c.line(127,22,67,42,mix(TRIM,INK,.16),2)
    c.line(127,22,190,42,mix(TRIM,INK,.26),2)
    c.hline(67,190,42,mix(TRIM,INK,.3))
    c.disc(127,37,8,hx(0x73796d),6)
    c.disc(127,36,6,hx(0xb8b197),4)
    c.vline(127,33,39,hx(0x747a6e))
    c.hline(123,131,36,hx(0x747a6e))
    box(c,(28,47,229,56),TRIM)
    sign(c,'BANCO',89,62,76,hx(0x7f7e70))
    door(c,111,width=34,height=69,barred=True,color=hx(0x72796f))
    for x in (52,178):
        sash(c,x,105,26,48,arched=True)
        for xx in range(x+4,x+24,6): c.vline(xx,108,150,IRON)
    for x in (88,157):
        box(c,(x-4,96,x+11,104),TRIM)
        box(c,(x,105,x+7,175),hx(0xb2ac99))
        c.vline(x+2,106,174,TRIM)
        c.vline(x+6,106,174,hx(0x797b71))
        box(c,(x-4,175,x+11,182),TRIM)
    foundation(c,29,229,10)
    return c


def store() -> Canvas:
    c=frame()
    planks(c,(30,42,225,184),hx(0x8c8b75),seed=1101,width=7)
    box(c,(24,32,231,42),TRIM)
    box(c,(60,18,196,32),WOOD)
    sign(c,'ALMACEN',63,20,130,WOOD,small=True)
    for x in (51,113,175): sash(c,x,55,28,30,boards=x==175)
    # Canvas awning, folded and damaged on its right side.
    for x in range(23,234):
        col=hx(0xb6ae8b) if ((x-23)//11)%2==0 else hx(0x798b7a)
        c.vline(x,103,122+(x%11<8)*3,col)
        if x%11==0: c.vline(x,104,124,mix(col,INK,.24))
    beam(c,23,102,233,102,WOOD,3)
    sash(c,45,137,58,34,lit=True)
    door(c,124,width=28,height=58,color=WOOD)
    sash(c,177,138,31,31,boards=True)
    crates(c,184,184,3)
    boardwalk(c,22,235)
    return c


def adobe() -> Canvas:
    c=frame()
    base=hx(0xb5a17e)
    for y in range(85,185):
        for x in range(34,222):
            inset=3 if y==85 else 1 if y==86 else 0
            if not 34+inset<=x<222-inset: continue
            shade=.06+.12*hash2(x//9,y//6,1201)+(.13 if x>191 else 0)
            c.set(x,y,mix(base,INK,shade))
    box(c,(34,79,221,87),base)
    box(c,(40,74,215,79),mix(base,TRIM,.35))
    for x in range(48,214,21): box(c,(x,93,x+8,99),WOOD)
    for x,y in ((60,112),(180,154),(152,91)):
        c.line(x,y,x+2,y+11,hx(0x7f715b))
        c.line(x+2,y+11,x-3,y+18,hx(0x7f715b))
    door(c,91,width=31,height=60,color=hx(0x8a6b4f))
    sash(c,156,119,28,30,lit=True)
    # Exposed patch of adobe bricks where the lime plaster has fallen away.
    masonry(c,(40,159,72,182),hx(0x978369),seed=1202,brick=(12,6))
    for x in (202,213): beam(c,x,61,x,185,GREY_WOOD,3)
    for y in range(70,182,10): beam(c,202,y,214,y,PALE_WOOD,2)
    c.line(132,121,135,154,hx(0x665d47))
    for y in range(124,156,5):
        c.disc(132+(y%3),y,2,hx(0x94553f),4)
    foundation(c,31,225,5)
    return c


def fallen_silo() -> Canvas:
    c=frame()
    # Ribbed galvanized drum lying on its side, with a torn open end.
    cx,cy=123,153
    for y in range(112,185):
        for x in range(56,207):
            v=(y-cy)/36
            if abs(v)>1: continue
            edge=int(math.sqrt(max(0,1-v*v))*13)
            if x<56+13-edge or x>194+edge:continue
            col=mix(hx(0x8a8f86),INK,.12+max(0,v)*.35)
            if (x-55)%12 in (0,1): col=mix(col,INK,.35)
            elif (x-55)%12==2: col=mix(col,TRIM,.3)
            if hash2(x//3,y//2,1301)>.87:col=mix(col,RUST,.52)
            c.set(x,y,col)
    c.disc(204,150,13,IRON,35)
    c.disc(207,151,10,HOLE,30)
    c.line(202,117,211,126,RUST,2)
    c.line(211,171,201,184,RUST,2)
    metal(c,(31,136,52,189),IRON,seed=1302)
    for x in range(32,53,5):c.vline(x,136+(x%3)*4,189,HOLE)
    for i in range(64):
        x=76+int(hash2(i,0,1303)*150)
        y=185+int(hash2(i,1,1303)*7)
        c.hline(x,x+1,y,hx(0xbca76d))
    return c


def billboard() -> Canvas:
    c=frame()
    for x in (79,172):
        metal(c,(x,81,x+7,191),mix(IRON,INK,.12),seed=x)
        c.line(x+2,137,x+66 if x<100 else x-60,80,IRON,3)
        box(c,(x-4,185,x+13,191),STONE)
    planks(c,(24,34,234,104),GREY_WOOD,seed=1401,vertical=True,width=10)
    # Weathered advertisement painted on boards, not an unbroken giant block.
    box(c,(19,28,239,35),IRON)
    box(c,(19,104,239,110),IRON)
    c.fill(29,39,229,99,hx(0x8d9b91))
    for y in range(39,100):
        for x in range(29,230):
            if (x-24)%10==0: c.set(x,y,hx(0x5a645f))
            elif hash2(x//3,y,1402)>.92:c.set(x,y,hx(0x7f877b))
    lettering(c,'THE MIRACLE',48,48,hx(0xcfc8a5),scale=3)
    lettering(c,'BIENVENIDOS',68,78,hx(0x414e4d),scale=2)
    # Torn lower corner, lattice support and service ladder.
    for y in range(85,101):
        for x in range(211+(y-85)//2,230):c.set(x,y,GREY_WOOD)
    beam(c,25,111,234,111,IRON,2)
    for x in (88,96): c.vline(x,114,191,IRON)
    for y in range(119,190,7):c.hline(88,98,y,IRON)
    c.line(36,25,36,20,IRON,2)
    c.line(215,25,215,20,IRON,2)
    box(c,(29,17,43,21),IRON)
    box(c,(208,17,222,21),IRON)
    return c


def gas_station() -> Canvas:
    c=frame()
    masonry(c,(137,93,237,184),hx(0xb6b2a0),seed=1501,brick=(16,8))
    box(c,(131,86,242,94),hx(0x7d918c))
    sash(c,164,115,51,34,boards=True)
    door(c,143,width=18,height=53,color=hx(0x849087))
    # Forecourt canopy with thin structural columns, deep fascia and lamps.
    for x in (32,117):
        metal(c,(x,106,x+5,189),hx(0x8b938c),seed=x)
        box(c,(x-3,185,x+8,191),STONE)
    box(c,(17,83,146,104),hx(0x829891))
    c.hline(19,145,87,TRIM)
    c.hline(19,145,97,hx(0xa56250))
    c.fill(23,105,142,110,HOLE)
    for x in (45,106):
        box(c,(x,109,x+10,111),TRIM)
    sign(c,'GAS',55,86,50,hx(0x7d9288),small=True)
    for x in (52,94):
        box(c,(x,148,x+20,187),hx(0x9b6b5f))
        box(c,(x-2,144,x+22,153),TRIM)
        c.fill(x+4,155,x+16,163,HOLE)
        lettering(c,'08',x+6,157,hx(0xbfbda3))
        c.vline(x+4,168,182,hx(0x876050))
        c.line(x+21,155,x+27,161,HOLE,2)
        c.line(x+27,161,x+27,181,HOLE,2)
        c.line(x+27,181,x+21,178,HOLE,2)
    foundation(c,22,242,3)
    return c


def shops() -> Canvas:
    c=frame()
    # Two adjoining shops, one brick and one painted timber, different heights.
    masonry(c,(19,47,130,185),hx(0x9e8470),seed=1601,brick=(13,6))
    planks(c,(133,68,237,185),hx(0x8a978b),seed=1602,width=6)
    box(c,(15,41,133,49),TRIM)
    box(c,(130,61,241,69),hx(0xb4b199))
    sign(c,'FARMACIA',24,99,103,hx(0x6b827a),small=True)
    sign(c,'MERCADO',139,103,92,WOOD,small=True)
    for x in (34,84): sash(c,x,61,25,28,boards=x==84)
    for x in (148,194): sash(c,x,76,22,20)
    for x in range(17,242):
        if 128<x<136:continue
        base=hx(0x9ea994) if (x//9)%2 else hx(0x7f8b7a)
        c.vline(x,121,131+(x%9<6)*3,base)
    sash(c,30,144,54,30,lit=True)
    door(c,94,width=24,height=49,color=WOOD)
    door(c,144,width=23,height=49,color=hx(0x7b8b7a))
    sash(c,182,144,42,30,boards=True)
    crates(c,205,184,1)
    boardwalk(c,15,242)
    return c


def flats() -> Canvas:
    c=frame()
    masonry(c,(24,23,233,185),hx(0x9e9687),seed=1701,brick=(17,7))
    masonry(c,(211,23,233,185),hx(0x898578),seed=1702,brick=(17,7))
    box(c,(19,15,237,24),TRIM)
    box(c,(25,10,231,15),hx(0x8c8e82))
    for y in (41,103):
        for i,x in enumerate((42,95,148,199)):
            sash(c,x,y,21,32,lit=(x+y)%5==0,boards=i==2 and y==103)
    box(c,(25,88,232,93),hx(0xaaa48e))
    door(c,103,width=29,height=54,color=hx(0x6e7c74))
    for x in (46,159): sash(c,x,151,30,22,boards=x==159)
    # Exposed fire escape on the right, with open space through its rungs.
    for y in (83,145):
        beam(c,163,y,238,y,IRON,3)
        beam(c,166,y-15,238,y-15,IRON,2)
        for x in range(169,239,9):c.vline(x,y-14,y-1,IRON)
    c.line(227,84,173,144,IRON,2)
    c.line(237,84,183,144,IRON,2)
    for t in range(7):
        x,y=227-t*8,85+t*9
        c.hline(x,x+10,y,IRON)
    for x in (50,203):
        box(c,(x,1,x+16,10),hx(0x747e77))
        c.hline(x-2,x+18,1,TRIM)
    foundation(c,21,237,7)
    return c


def warehouse() -> Canvas:
    c=frame()
    masonry(c,(21,99,237,184),hx(0x8c8777),seed=1801,brick=(19,8))
    roof(c,11,246,49,98,hx(0x727d7b),1802)
    metal(c,(84,112,200,183),hx(0x7a8580),seed=1803)
    for y in range(115,183,6):
        c.hline(85,199,y,mix(IRON,INK,.4))
        c.hline(86,198,y+1,mix(IRON,TRIM,.25))
    box(c,(79,107,204,113),IRON)
    c.fill(97,151,186,183,HOLE)
    crates(c,108,183,5)
    sash(c,39,119,27,32,boards=True)
    sign(c,'BODEGA',98,84,89,WOOD,small=True)
    c.vline(226,105,183,hx(0x5a6762))
    c.line(226,179,231,184,hx(0x5a6762),2)
    barrel(c,216,184)
    foundation(c,17,242,7)
    return c


def hangar() -> Canvas:
    c=frame()
    # Arched corrugated steel shed. Its silhouette and radial panels identify it.
    for x in range(18,239):
        u=(x-128)/110
        top=round(103-math.sqrt(max(0,1-u*u))*69)
        for y in range(top,185):
            col=mix(hx(0x839085),INK,.08+max(0,u)*.23)
            if (x-18)%8 in (0,1):col=mix(col,INK,.3)
            elif (x-18)%8==2:col=mix(col,TRIM,.3)
            if hash2(x//3,y//5,1901)>.9:col=mix(col,RUST,.2)
            c.set(x,y,col)
        c.set(x,top,mix(IRON,TRIM,.42))
    box(c,(55,103,203,184),mix(IRON,INK,.15))
    metal(c,(60,108,198,183),hx(0x7c8980),seed=1902)
    for x in range(64,198,10):c.vline(x,109,182,mix(IRON,INK,.4))
    c.fill(114,112,159,184,HOLE)
    sign(c,'HANGAR 04',77,78,104,hx(0x667b6b),small=True)
    sash(c,29,130,18,27)
    c.line(218,119,218,175,IRON,2)
    box(c,(207,112,230,119),IRON)
    foundation(c,15,242,7)
    return c


def watchtower() -> Canvas:
    c=frame()
    # Four thin legs and cross-bracing leave actual transparent gaps.
    for x in (73,178):
        beam(c,x,91,x-7 if x<100 else x+7,185,GREY_WOOD,6)
        box(c,(x-10,185,x+12,191),STONE)
    for ya,yb in ((95,136),(137,184)):
        beam(c,78,ya,179,yb,GREY_WOOD,3)
        beam(c,179,ya,75,yb,WOOD,3)
    planks(c,(62,44,194,91),hx(0x7c8770),seed=2001,width=6)
    for x in (73,114,155):sash(c,x,51,27,22)
    roof(c,49,206,8,43,hx(0x6b7d72),2002)
    box(c,(49,92,208,99),GREY_WOOD)
    for x in range(51,207,15):beam(c,x,79,x,92,GREY_WOOD,2)
    beam(c,50,78,207,78,PALE_WOOD,2)
    for x in (119,132):beam(c,x,100,x,185,IRON,2)
    for y in range(105,186,8):beam(c,120,y,133,y,IRON,2)
    c.line(162,15,162,0,IRON,2)
    # Hooded searchlight on the balcony.
    beam(c,198,67,207,70,IRON,3)
    box(c,(203,58,220,69),IRON)
    c.fill(218,59,222,68,hx(0xb8b89b))
    return c


def radar() -> Canvas:
    c=frame()
    masonry(c,(42,136,213,184),hx(0x8c907d),seed=2101,brick=(18,8))
    box(c,(36,129,218,137),hx(0x9a9e88))
    door(c,62,width=24,height=42,color=hx(0x727e6b))
    sash(c,150,151,31,20)
    metal(c,(114,87,140,130),hx(0x798575),seed=2102)
    c.poly([(99,128),(120,93),(134,93),(155,128)],hx(0x78816e))
    # Tilted dish: the right-hand face has a fine wire mesh, not a solid arc.
    for y in range(22,104):
        for x in range(62,184):
            xx=(x-123)/63
            yy=(y-63)/43
            if xx*xx+yy*yy>1:continue
            # An open slice defines the concave upper-right lip.
            if x>105+(y-25)*.66:continue
            col=mix(hx(0x8c9990),INK,.12+max(0,xx)*.2)
            if (x+2*y)%10==0 or (x-y)%9==0:col=mix(col,INK,.35)
            c.set(x,y,col)
    c.line(107,23,158,98,TRIM,3)
    c.line(85,55,159,98,IRON,2)
    c.line(72,76,159,98,IRON,2)
    c.line(93,95,159,98,IRON,2)
    c.line(122,56,177,34,IRON,2)
    box(c,(174,29,183,37),IRON)
    # Antenna and vent grilles on the service hut.
    c.vline(199,98,128,IRON)
    c.hline(187,211,106,IRON)
    for yy in range(151,177,4):c.hline(108,132,yy,HOLE)
    foundation(c,38,218,7)
    return c


def downpipe(c: Canvas, x: int, top: int, bottom=183, iron=IRON) -> None:
    """Sheet-metal gutter pipe with joined elbows, seams and wall brackets."""
    c.line(x-4,top,x,top+5,mix(iron,INK,.4),3)
    c.vline(x,top+5,bottom-5,mix(iron,INK,.35))
    c.vline(x+1,top+5,bottom-5,mix(iron,TRIM,.28))
    c.vline(x+2,top+5,bottom-5,iron)
    for y in range(top+17,bottom-7,30):
        c.hline(x-1,x+3,y,mix(iron,INK,.4))
        c.hline(x,x+2,y+1,mix(iron,TRIM,.3))
        c.set(x+4,y,INK)
    c.line(x+1,bottom-5,x+6,bottom-1,iron,2)
    c.hline(x+5,x+8,bottom,mix(iron,INK,.6))


def small_bench(c: Canvas, x: int, bottom=184, width=34) -> None:
    for xx in (x+3,x+width-4):
        beam(c,xx,bottom-14,xx,bottom,GREY_WOOD,2)
    for y in (bottom-19,bottom-15):
        box(c,(x,y,x+width,y+2),GREY_WOOD)
        c.set(x+3,y+1,INK)
        c.set(x+width-3,y+1,INK)
    box(c,(x-2,bottom-9,x+width+2,bottom-6),PALE_WOOD)
    c.line(x+6,bottom-6,x+width-7,bottom-1,GREY_WOOD)


def pot(c: Canvas, x: int, bottom=184, plant=False) -> None:
    clay=hx(0x986c50)
    c.poly([(x,bottom-14),(x+16,bottom-14),(x+13,bottom),(x+3,bottom)],clay)
    c.line(x+2,bottom-12,x+4,bottom-2,mix(clay,TRIM,.36),2)
    c.line(x+14,bottom-12,x+12,bottom-1,mix(clay,INK,.35),2)
    box(c,(x-1,bottom-16,x+17,bottom-13),mix(clay,TRIM,.12))
    c.hline(x+2,x+14,bottom-15,hx(0x4c4435))
    if plant:
        for dx,dy in ((-6,-23),(1,-28),(7,-24)):
            c.line(x+8,bottom-15,x+8+dx,bottom+dy,hx(0x6c7754))
            c.hline(x+6+dx,x+9+dx,bottom+dy,hx(0x869064))
            c.set(x+10+dx,bottom+dy-1,hx(0x869064))


def bucket(c: Canvas, x: int, bottom=184, color=IRON) -> None:
    c.poly([(x,bottom-12),(x+12,bottom-12),(x+10,bottom),(x+2,bottom)],color)
    c.vline(x+2,bottom-10,bottom-2,mix(color,TRIM,.35))
    c.vline(x+10,bottom-10,bottom-1,mix(color,INK,.3))
    c.hline(x-1,x+13,bottom-13,mix(color,TRIM,.3))
    c.line(x,bottom-12,x+2,bottom-18,mix(color,INK,.3))
    c.line(x+2,bottom-18,x+10,bottom-18,color)
    c.line(x+10,bottom-18,x+12,bottom-12,color)
    c.hline(x+4,x+8,bottom-18,WOOD)


def sack(c: Canvas,x:int,bottom=184,width=19,height=22) -> None:
    cloth=hx(0xb0a079)
    c.poly([(x+3,bottom),(x,bottom-4),(x+1,bottom-height+5),(x+6,bottom-height),
            (x+width-4,bottom-height),(x+width,bottom-4),(x+width-3,bottom)],cloth)
    c.line(x+3,bottom-4,x+4,bottom-height+7,mix(cloth,INK,.23))
    c.line(x+width-3,bottom-4,x+width-5,bottom-height+6,mix(cloth,INK,.3))
    for y in range(bottom-height+8,bottom-3,4):c.set(x+width-4,y,mix(cloth,TRIM,.3))
    c.hline(x+6,x+width-5,bottom-height+3,hx(0x706149))
    c.line(x+8,bottom-height+3,x+7,bottom-height+7,hx(0x706149))
    c.hline(x+5,x+width-5,bottom-7,mix(cloth,INK,.12))


def poster(c: Canvas,x:int,y:int,width=17,height=23,portrait=False) -> None:
    paper=hx(0xb5ab8c)
    c.fill(x+1,y,x+width-1,y+height,paper)
    c.fill(x,y+2,x+width,y+height-2,mix(paper,TRIM,.12))
    c.hline(x+1,x+width-1,y+height,mix(paper,INK,.38))
    c.set(x+3,y+2,INK)
    c.set(x+width-2,y+2,IRON)
    c.hline(x+3,x+width-3,y+4,hx(0x655c49))
    c.hline(x+4,x+width-4,y+6,hx(0x655c49))
    if portrait:
        c.disc(x+width//2,y+13,3,hx(0x766c55),4)
        c.hline(x+4,x+width-4,y+11,hx(0x5c5646))
        c.poly([(x+3,y+20),(x+6,y+16),(x+width-6,y+16),(x+width-3,y+20)],hx(0x766c55))
    else:
        for yy,length in ((10,width-6),(13,width-8),(17,width-7)):
            c.hline(x+3,x+length,y+yy,hx(0x766c55))
    # A torn curl still covers the wall; it does not punch a transparent hole.
    c.poly([(x+width-3,y+height-4),(x+width,y+height-7),(x+width,y+height-1)],mix(paper,INK,.25))


def dress_building(c: Canvas, index: int) -> None:
    """Signs of construction and daily use, specific to each building.

    These are authored objects and joints, not a texture filter. They are
    deliberately small beside a human door, and keep windows/entryways clear.
    """
    if index == 0:  # Saloon: a seat outside, a performance notice and a spittoon.
        small_bench(c,44,width=34)
        poster(c,154,149,14,23)
        c.disc(146,179,6,hx(0xa18a54),3)
        c.disc(146,177,4,hx(0x6a603e),2)
        c.hline(141,151,181,hx(0xb4a170))
        for x in (36,218):
            downpipe(c,x,72,118,iron=hx(0x787666))
        for x in (77,128,180):
            box(c,(x,65,x+4,69),mix(WOOD,INK,.25))
            c.set(x+1,66,TRIM)
    elif index == 1:  # Cabin: water pail, doorstep, repaired shingles and logs.
        bucket(c,185,183)
        pot(c,46,184,plant=True)
        downpipe(c,207,111)
        for x,y in ((135,78),(146,82),(157,87)):
            c.line(x,y,x+8,y+3,hx(0x8e8874),2)
            c.set(x+2,y+1,INK)
        c.hline(107,132,185,hx(0x79705d))
    elif index == 2:  # Barn: an iron hay fork and working hinges on the gates.
        c.vline(225,133,181,WOOD)
        c.vline(226,134,181,PALE_WOOD)
        for x in (220,224,228,232):c.vline(x,126,138,IRON)
        c.hline(220,232,138,IRON)
        for x in (80,171):
            for y in (132,168):
                c.hline(x,x+9,y,IRON)
                c.set(x+1,y,INK)
                c.set(x+8,y,INK)
        c.line(125,140,125,148,IRON,2)
        c.line(134,140,134,148,IRON,2)
        for x in (64,188):
            box(c,(x,88,x+5,102),mix(RED_WOOD,INK,.2))
            c.line(x+2,97,x+9,88,TRIM)
    elif index == 3:  # Ruin: broken lath, exposed plaster and individual rubble.
        for x in (39,49,60,72):
            c.vline(x,108+(x%7),120,mix(PALE_WOOD,INK,.25))
        c.poly([(133,149),(154,145),(170,151),(164,157),(145,158)],hx(0xaba28c))
        c.line(144,149,148,154,hx(0x786e5d))
        for x,y in ((90,184),(110,186),(162,183),(183,185),(208,182)):
            box(c,(x,y,x+7,y+3),hx(0x8d7b65))
            c.set(x+2,y+1,hx(0xb2a18a))
        beam(c,80,130,84,160,GREY_WOOD,3)
        c.line(82,136,88,137,IRON)
    elif index == 4:  # Water tower: capacity stencil, rusty spout and stays.
        lettering(c,'AGUA',128,51,mix(WOOD,INK,.5),scale=2)
        lettering(c,'12000 L',131,65,mix(WOOD,INK,.5))
        for x in (84,105,161,178):
            c.vline(x,70,80,mix(WOOD,INK,.2))
            c.set(x+1,79,mix(WOOD,TRIM,.3))
        for y in (61,65,69,74):c.set(197,y,RUST)
        c.line(64,95,49,189,mix(IRON,INK,.2))
        c.line(192,95,207,189,mix(IRON,INK,.2))
        box(c,(44,186,53,191),STONE)
        box(c,(203,186,212,191),STONE)
        poster(c,86,105,13,18)
    elif index == 5:  # Church: rose window, bell rope, stone steps and votive pot.
        c.disc(128,99,11,hx(0xbab196),11)
        c.disc(128,99,8,HOLE,8)
        for k in range(8):
            a=math.pi*k/4
            c.line(128,99,128+round(math.cos(a)*8),99+round(math.sin(a)*8),hx(0x978a6d))
        for x,y,col in ((125,96,0x967b58),(131,96,0x6e857a),(125,102,0x7f776d),(131,102,0x9c865d)):
            c.fill(x-1,y-1,x+1,y+1,hx(col))
        c.disc(128,99,2,hx(0xaea17b),2)
        c.vline(143,70,114,hx(0x827458))
        c.disc(143,114,2,hx(0x827458),3)
        for yy,xa,xb in ((183,106,150),(186,102,154),(189,98,158)):
            box(c,(xa,yy,xb,min(191,yy+2)),STONE)
        pot(c,196,184,plant=True)
        downpipe(c,211,110)
    elif index == 6:  # Sheriff: wanted portrait, public bench, corner fittings.
        poster(c,94,159,14,22,portrait=True)
        small_bench(c,43,width=40)
        downpipe(c,216,58,116)
        for x in (37,211):
            for yy in (62,90):
                c.hline(x,x+7,yy,IRON)
                c.set(x+1,yy,INK)
                c.set(x+6,yy,INK)
        c.line(116,142,121,147,hx(0xb2a284))
    elif index == 7:  # Smithy: a whetstone, bellows, tongs, coal and hard edges.
        c.disc(53,170,10,hx(0x8c8d7d),10)
        c.disc(53,170,6,hx(0xa6a48f),6)
        c.disc(53,170,2,IRON,2)
        beam(c,48,177,45,184,WOOD,3)
        beam(c,57,177,62,184,WOOD,3)
        c.line(54,169,63,165,IRON)
        c.vline(63,165,172,WOOD)
        c.poly([(133,167),(144,157),(151,166),(140,176)],hx(0x785e48))
        c.line(136,166,143,164,TRIM)
        c.line(139,171,146,167,TRIM)
        c.hline(102,129,159,TRIM)
        c.line(118,153,126,148,WOOD,2)
        c.line(122,148,129,151,IRON,3)
        bucket(c,188,184,color=hx(0x68726d))
        for x in (96,102,111):
            c.hline(x,x+3,182,IRON)
            c.set(x+3,181,IRON)
        downpipe(c,214,107)
    elif index == 8:  # Stable: a saddle and buckled reins over the stall door.
        c.poly([(157,141),(160,134),(167,131),(172,133),(181,130),(185,135),
                (179,141),(166,143)],hx(0x76604a))
        c.line(160,138,177,138,hx(0xac9470),2)
        c.vline(176,140,153,hx(0x62503f))
        c.hline(172,180,154,IRON)
        c.line(93,125,102,128,hx(0x6d5745))
        c.line(102,128,100,144,hx(0x6d5745))
        c.line(100,144,91,141,hx(0x6d5745))
        c.set(93,139,IRON)
        c.vline(218,130,157,WOOD)
        for x in (214,217,220,223):c.vline(x,123,132,IRON)
        c.hline(214,223,132,IRON)
        sack(c,25,184,17,20)
    elif index == 9:  # Bank: cast plaque, mail slot and polished door wear.
        box(c,(205,150,218,168),hx(0x777e6e))
        c.hline(207,216,154,HOLE)
        c.hline(207,216,155,TRIM)
        c.set(214,164,hx(0xb8a56b))
        for x in (84,169):
            box(c,(x,84,x+8,91),mix(STONE,TRIM,.3))
            c.disc(x+4,87,2,hx(0x7b7d6e),2)
        for x in (93,162):
            c.vline(x,108,172,mix(STONE,INK,.15))
        c.hline(116,140,178,mix(TRIM,WOOD,.5))
        box(c,(109,186,150,188),STONE)
        box(c,(105,189,154,191),mix(STONE,TRIM,.2))
    elif index == 10:  # General store: shelves of bottles and sacks on the porch.
        c.hline(49,99,156,hx(0x6e6851))
        for x in (52,60,70,83,94):
            col=hx(0x6c795b) if x%3 else hx(0x8a7755)
            c.fill(x,147,x+3,154,col)
            c.fill(x+1,144,x+2,147,col)
            c.set(x+1,149,hx(0xb7aa83))
        sack(c,54,184,19,17)
        sack(c,76,184,18,15)
        poster(c,107,139,11,20)
        downpipe(c,225,45,100)
        c.line(38,104,32,119,IRON)
        c.line(217,104,224,119,IRON)
    elif index == 11:  # Adobe: chipped lime plaster, pottery and a wall fountain.
        pot(c,63,184)
        pot(c,39,184,plant=True)
        for yy in range(151,183):
            xx=47+((yy//6)%3)*6
            if yy<159:
                c.hline(xx,xx+12,yy,hx(0x9a866b))
                if yy%6==2:c.hline(xx,xx+12,yy,hx(0x75654e))
        c.line(174,94,177,104,hx(0x7f7059))
        c.line(177,104,173,111,hx(0x7f7059))
        c.fill(48,125,59,141,hx(0xa9a18b))
        c.line(51,130,57,130,IRON,2)
        c.vline(54,130,134,IRON)
        c.disc(54,147,10,hx(0x8b8d78),3)
        c.hline(45,63,146,hx(0xb4b49a))
    elif index == 12:  # Collapsed silo: bolted seam, curled sheet and spilled grain.
        for x in range(64,196,12):
            c.set(x,120,INK)
            c.set(x+1,119,mix(IRON,TRIM,.3))
            c.set(x,178,INK)
        for yy in range(128,174,9):
            c.set(195,yy,INK)
            c.set(196,yy-1,TRIM)
        c.line(76,181,91,188,RUST,2)
        c.line(91,188,113,185,IRON,2)
        c.line(113,185,122,187,IRON,2)
        c.hline(80,88,184,INK)
        c.hline(96,107,188,hx(0xb7a16d))
    elif index == 13:  # Billboard: catwalk, cable and the lattice behind the panel.
        c.line(86,116,172,177,mix(IRON,INK,.2),2)
        c.line(172,116,86,177,mix(IRON,INK,.2),2)
        c.hline(77,182,143,IRON)
        for x in range(29,232,12):
            c.vline(x,109,113,INK)
            c.set(x+2,110,TRIM)
        c.line(217,22,229,25,IRON)
        c.line(229,25,232,183,INK)
        for x in (35,215):
            c.hline(x-3,x+4,22,mix(IRON,TRIM,.5))
        # Paper peeling along a diagonal cut in the faded advertisement.
        c.line(201,78,215,90,hx(0xb4b9a5))
        c.line(200,79,214,91,hx(0x657369))
    elif index == 14:  # Service station: air compressor, conduits, meters and hoses.
        box(c,(222,151,234,182),hx(0x8e9b8a))
        c.disc(228,156,3,hx(0xc3bba1),3)
        c.line(228,156,229,154,INK)
        c.line(234,163,241,167,HOLE,2)
        c.line(241,167,240,181,HOLE,2)
        c.line(240,181,233,178,HOLE,2)
        c.vline(235,101,148,IRON)
        c.hline(215,235,110,IRON)
        box(c,(218,108,229,121),hx(0x79877d))
        for x in (221,226):c.vline(x,110,119,HOLE)
        c.disc(221,103,6,hx(0xb4b49a),6)
        c.disc(221,103,4,hx(0x595f54),4)
        c.line(221,103,221,100,TRIM)
        c.line(221,103,224,104,TRIM)
        for x in range(23,141,13):c.set(x,101,INK)
    elif index == 15:  # Shops: hanging pharmacy cross, rolled blind and parcel.
        c.line(123,140,132,140,IRON)
        c.fill(124,144,130,157,hx(0x72856a))
        c.fill(120,148,134,153,hx(0x72856a))
        c.hline(123,129,147,hx(0xa6b390))
        box(c,(180,137,227,140),hx(0x7b826c))
        for x in range(182,227,5):c.vline(x,138,140,TRIM)
        sack(c,173,184,18,15)
        poster(c,26,113,12,19)
        downpipe(c,235,72)
    elif index == 16:  # Apartments: antenna, rainwater pipe, laundry and AC unit.
        downpipe(c,28,29)
        c.vline(115,0,14,IRON)
        c.line(105,2,125,2,IRON)
        c.line(101,7,129,7,IRON)
        c.line(107,11,123,11,IRON)
        c.line(69,96,138,94,hx(0x514d42))
        for x,col in ((78,0x8d8d77),(91,0x697b71),(106,0xa49c82)):
            c.poly([(x,96),(x+7,95),(x+8,105),(x+2,106)],hx(col))
            c.vline(x+3,97,104,mix(hx(col),INK,.2))
            c.set(x+1,95,TRIM)
        box(c,(150,77,175,87),hx(0x8c9384))
        for x in range(153,173,3):c.vline(x,79,84,hx(0x4e5b55))
        c.hline(151,174,86,INK)
        for x in (51,70,206):
            c.vline(x,26,31+(x%7),hx(0x7f8173))
    elif index == 17:  # Warehouse: chain hoist, fuse box and the loading platform.
        downpipe(c,233,106)
        box(c,(38,160,56,177),hx(0x6f7d73))
        c.vline(52,163,174,INK)
        c.set(51,167,TRIM)
        c.line(46,159,46,153,IRON)
        c.line(46,153,32,153,IRON)
        for yy in range(118,149,3):
            c.set(87,yy,IRON)
            c.set(88,yy+1,INK)
        c.line(87,148,91,152,IRON)
        c.line(91,152,94,149,IRON)
        box(c,(94,184,189,187),hx(0x8e8a75))
        c.hline(95,188,185,hx(0xb4aa8c))
        poster(c,211,118,13,20)
    elif index == 18:  # Hangar: roof vent, assembly bolts, repair kit and oil drum.
        box(c,(111,51,148,65),hx(0x79897c))
        for yy in (54,58,62):c.hline(115,144,yy,HOLE)
        for x in range(34,233,24):
            for y in (100,136,172):
                if x<55 or x>203:
                    c.set(x,y,INK)
                    c.set(x-1,y-1,TRIM)
        box(c,(174,169,194,183),hx(0x7e5e4e))
        box(c,(172,166,196,170),hx(0x966c53))
        c.hline(181,188,164,IRON)
        c.vline(181,164,166,IRON)
        c.vline(188,164,166,IRON)
        c.set(185,172,IRON)
        barrel(c,27,184,width=17,height=25)
        c.hline(115,158,184,TRIM)
    elif index == 19:  # Watchtower: battery box, cables and boards along the deck.
        box(c,(80,117,92,138),hx(0x6e7b65))
        for y in (122,126,130):c.hline(83,89,y,HOLE)
        c.line(85,117,88,105,INK)
        c.line(88,105,95,98,INK)
        for x in range(55,207,12):c.vline(x,94,97,INK)
        sack(c,65,91,18,12)
        c.line(160,16,181,40,INK)
        c.line(181,40,197,58,INK)
        for x in (76,183):
            c.set(x,104,IRON)
            c.set(x,144,IRON)
    elif index == 20:  # Radar: control box and wiring, rivets on the dish frame.
        box(c,(187,148,203,169),hx(0x738271))
        c.disc(192,154,2,hx(0xbab48b),2)
        c.set(198,161,hx(0x9e6a4e))
        c.line(129,126,148,140,INK,2)
        c.line(148,140,194,142,INK,2)
        c.vline(194,142,147,INK)
        c.hline(192,205,112,IRON)
        c.hline(194,203,118,IRON)
        for x,y in ((109,27),(122,47),(134,67),(148,88)):
            c.set(x,y,INK)
            c.set(x-1,y-1,TRIM)
        box(c,(152,177,188,182),hx(0x787b69))
        c.hline(155,185,178,TRIM)


HOUSES = [saloon, cabin, barn, ruined, water_tower, church, sheriff, smithy,
          stable, bank, store, adobe, fallen_silo, billboard, gas_station,
          shops, flats, warehouse, hangar, watchtower, radar]


def make_houses():
    frames=[draw() for draw in HOUSES]
    for index,c in enumerate(frames):
        dress_building(c,index)
    return sheet(frames)


def build_assets():
    """The complete output for rebuild_scenery and reproducibility checks."""
    return {'sprites/props/houses.png':make_houses()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path,
                        default=Path(__file__).resolve().parent.parent / 'assets')
    args = parser.parse_args()
    save_all(args.assets_dir, build_assets(), 'make_houses')
    return 0


if __name__=='__main__':
    sys.exit(main())
