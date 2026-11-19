#!/usr/bin/env python3
"""Authored construction detail for the road's interactive architecture.

finish(name, image) keeps every frame and doorway aligned with the collision
geometry. Fronts have readable construction, deep openings, ironwork and
objects belonging to their trade. Damage follows timber joints or masonry
rather than adding noise. Construction templates are 180x128 (west) and
240x192 (city); street_scale exports 288x200 and 288x216 with 44x64 doors.
Only the standard library is used. This module never imports the refiner.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

from landscape_kit import Canvas, hash2, hx, mix
from make_sprites import Image, rgb
from scenery_materials import planks, masonry, metal, window, lettering

SUPPORTED = {'wall', 'wall_ruins', 'facades', 'city_fronts', 'door'}
FRAME_WIDTH = {'wall': 44, 'wall_ruins': 180, 'facades': 180,
               'city_fronts': 240, 'door': 44}
INK = hx(0x252321)
HOLE = hx(0x191718)
WOOD = hx(0x956f45)
WOOD_LIT = hx(0xb5986b)
STONE = hx(0xaaa18d)
IRON = hx(0x777b77)
RUST = hx(0x915d3d)
BRASS = hx(0xb79a57)
CREAM = hx(0xc8bea4)


def box(c: Canvas, bounds, color) -> None:
    x0,y0,x1,y1=bounds
    color=hx(color)
    c.fill(x0,y0,x1,y1,color)
    c.hline(x0,x1,y0,mix(color,CREAM,.34))
    c.vline(x0,y0,y1,mix(color,CREAM,.2))
    c.hline(x0,x1,y1,mix(color,INK,.48))
    c.vline(x1,y0,y1,mix(color,INK,.38))


def beam(c: Canvas, x0,y0,x1,y1,width=3,color=WOOD) -> None:
    c.line(x0,y0+1,x1,y1+1,mix(color,INK,.5),width+1)
    c.line(x0,y0,x1,y1,color,width)
    c.line(x0,y0,x1,y1,mix(color,WOOD_LIT,.55))
    for x,y in ((x0+width//2,y0+1),(x1+width//2,y1-1)):
        c.set(x,y,INK)
        c.set(x-1,y-1,mix(IRON,CREAM,.35))


def bolt(c: Canvas,x,y,color=IRON) -> None:
    c.fill(x-1,y-1,x+1,y+1,mix(color,INK,.4))
    c.hline(x-1,x,y-1,mix(color,CREAM,.5))
    c.set(x,y,color)


def patch(c: Canvas, points, base, brick=(10,5), seed=1) -> None:
    """An irregular missing-plaster patch with a recess and exposed bricks."""
    mask=Canvas(c.w,c.h)
    mask.poly(points,hx(base))
    xs=[p[0] for p in points]
    ys=[p[1] for p in points]
    material=Canvas(c.w,c.h)
    masonry(material,(min(xs),min(ys),max(xs),max(ys)),base,seed=seed,brick=brick)
    for y in range(min(ys),max(ys)+1):
        for x in range(min(xs),max(xs)+1):
            if not mask.solid(x,y):continue
            col=material.get(x,y)
            if not mask.solid(x,y-1) or not mask.solid(x-1,y):
                col=mix(base,INK,.5)
            elif not mask.solid(x,y+1):
                col=mix(base,CREAM,.28)
            c.set(x,y,col)


def crack(c: Canvas,points,color=INK,lip=STONE) -> None:
    for a,b in zip(points,points[1:]):
        c.line(a[0]+1,a[1],b[0]+1,b[1],mix(lip,CREAM,.2))
        c.line(*a,*b,color)


def roof(c: Canvas,x0,x1,top,eave,base=WOOD,seed=1) -> None:
    cx=(x0+x1)//2
    for y in range(top,eave+1):
        half=round((x1-x0)*.5*(y-top)/max(1,eave-top))
        row=(y-top)//4
        for x in range(cx-half,cx+half+1):
            tile=(x+row*4)//8
            n=hash2(tile,row,seed)
            col=mix(base,INK,.03+n*.15+(.12 if x>cx else 0))
            if (y-top)%4==3 or (x+row*4)%8==0:col=mix(col,INK,.3)
            elif (y-top)%4==0:col=mix(col,CREAM,.18)
            if n>.95 and (y-top)%4>1:col=mix(col,INK,.3)
            c.set(x,y,col)
    beam(c,cx,top,x0,eave+1,2,mix(base,CREAM,.18))
    beam(c,cx,top,x1,eave+1,2,mix(base,INK,.15))
    box(c,(x0,eave+2,x1+2,eave+5),mix(base,INK,.15))
    for x in range(x0+6,x1-3,14):
        c.fill(x,eave+5,x+3,eave+8,mix(base,INK,.45))
        c.set(x,eave+5,mix(base,CREAM,.28))


def opening(c: Canvas,x,y,w,h,lit=False,bars=False,arch=False,broken=False) -> None:
    """A deep reveal, stepped lintel, pane edges and projecting stone sill."""
    box(c,(x-4,y-5,x+w+3,y+h+3),STONE)
    c.fill(x-2,y-2,x+w+1,y+h+1,mix(STONE,INK,.56))
    window(c,x,y,w,h,lit=lit,broken=broken)
    c.hline(x-4,x+w+3,y-5,CREAM)
    c.vline(x-3,y-3,y+h,mix(STONE,CREAM,.22))
    c.vline(x+w+2,y-2,y+h,mix(STONE,INK,.35))
    box(c,(x-5,y+h+2,x+w+4,y+h+5),mix(STONE,CREAM,.2))
    for xx in (x-2,x+w-1):
        c.vline(xx,y+h+6,y+h+8,mix(STONE,INK,.4))
    if arch:
        center=x+w/2
        for t in range(11):
            a=math.pi+math.pi*t/10
            xx=center+math.cos(a)*(w/2+3)
            yy=y+math.sin(a)*(w/2+3)
            c.disc(xx,yy,2,mix(STONE,CREAM,.18 if t<6 else 0),2)
    if bars:
        for xx in range(x+3,x+w-1,5):
            c.vline(xx,y,y+h-1,mix(IRON,INK,.1))
            c.vline(xx+1,y,y+h-1,mix(IRON,INK,.5))
            bolt(c,xx,y+5)
            bolt(c,xx,y+h-6)
        c.hline(x,x+w-1,y+6,IRON)
        c.hline(x,x+w-1,y+h-6,IRON)
    elif not broken:
        # Tied-back fabric is confined to the pane edges.
        curtain=hx(0x9a866b) if lit else hx(0x657268)
        for yy in range(2,h-1):
            spread=3 if yy<h//4 or yy>h*3//4 else 2
            for xx in range(spread):
                c.set(x+xx+1,y+yy,mix(curtain,INK,.14 if xx%2 else 0))
                c.set(x+w-xx-2,y+yy,mix(curtain,INK,.14 if xx%2 else 0))
        c.vline(x+w//2,y,y+h-1,mix(WOOD,INK,.25))
        c.hline(x,x+w-1,y+h//2,mix(WOOD,INK,.25))


def shutter(c: Canvas,x,y,w,h,tilt=0) -> None:
    for yy in range(h):
        dx=round(tilt*yy/max(1,h-1))
        for xx in range(w):
            color=mix(WOOD,INK,.12 if yy%4 else .42)
            c.set(x+xx+dx,y+yy,color)
            if yy%4==1:c.set(x+xx+dx,y+yy,mix(WOOD,CREAM,.25))
    c.line(x,y,x+tilt,y+h-1,mix(WOOD,CREAM,.25),2)
    for yy in (y+4,y+h-5):
        c.hline(x-1,x+3,yy,IRON)
        c.set(x+1,yy,CREAM)


def door_reveal(c: Canvas,x,y,w,h,stone=False) -> None:
    base=STONE if stone else WOOD
    box(c,(x-6,y-7,x+w+5,y-1),base)
    for xx in (x-6,x+w+3):
        box(c,(xx,y,xx+2,y+h-1),base)
    c.vline(x-2,y-2,y+h-1,mix(base,INK,.52))
    c.vline(x+w+1,y-2,y+h-1,mix(base,INK,.52))
    c.hline(x-1,x+w,y-1,mix(base,INK,.6))
    for xx in (x-4,x+w+4):
        for yy in (y+9,y+h-14):bolt(c,xx,yy)
    for xx in (x-5,x+w+3):
        c.set(xx,y+h-7,mix(base,CREAM,.3))


def sign(c: Canvas,text,x,y,w,color=WOOD) -> None:
    box(c,(x,y,x+w,y+12),mix(color,INK,.18))
    c.fill(x+2,y+2,x+w-2,y+9,color)
    tw=len(text)*4-1
    lettering(c,text,x+(w-tw)//2,y+4,CREAM)
    for xx in (x+3,x+w-3):c.set(xx,y+2,IRON)


def pipe(c: Canvas,x,top,bottom,color=IRON) -> None:
    c.vline(x,top,bottom,mix(color,INK,.4))
    c.vline(x+1,top,bottom,mix(color,CREAM,.25))
    c.vline(x+2,top,bottom,color)
    for yy in range(top+9,bottom,24):
        c.hline(x-1,x+3,yy,mix(color,INK,.3))
        c.set(x+3,yy+1,INK)
    c.line(x+1,bottom-4,x+5,bottom,color,2)


def poster(c: Canvas,x,y,w=13,h=19,portrait=False) -> None:
    paper=hx(0xc0b598)
    c.fill(x,y,x+w,y+h,paper)
    c.hline(x,x+w,y+h,mix(paper,INK,.4))
    c.set(x+2,y+1,IRON)
    c.set(x+w-2,y+1,INK)
    c.hline(x+2,x+w-2,y+4,mix(paper,INK,.6))
    if portrait:
        c.disc(x+w/2,y+10,2,mix(paper,INK,.4),3)
        c.hline(x+3,x+w-3,y+8,mix(paper,INK,.5))
        c.poly([(x+2,y+16),(x+5,y+12),(x+w-4,y+12),(x+w-2,y+16)],mix(paper,INK,.4))
    else:
        for yy in (8,11,15):c.hline(x+2,x+w-3-(yy%3),y+yy,mix(paper,INK,.5))


def rubble(c: Canvas,x,bottom=127,count=4) -> None:
    for i in range(count):
        xx=x+i*6
        yy=bottom-(i%2)*3
        c.poly([(xx,yy),(xx+1,yy-4),(xx+5,yy-5),(xx+8,yy-2),(xx+7,yy)],mix(STONE,WOOD,.4))
        c.line(xx+2,yy-4,xx+5,yy-4,mix(STONE,CREAM,.3))


def western(index: int) -> Canvas:
    c=Canvas(180,128)
    if index==0:
        # Chapel: clapboard, a working bell, stained rose and arched windows.
        roof(c,2,176,18,43,base=hx(0x6d776f),seed=31)
        planks(c,(3,47,176,127),hx(0xbab399),seed=901,width=6)
        planks(c,(153,47,176,127),hx(0x9d9b85),seed=902,width=6)
        planks(c,(75,24,104,58),hx(0xc0b69d),seed=903,width=6)
        c.poly([(72,24),(90,3),(108,24)],hx(0x758076))
        beam(c,90,3,73,24,2,WOOD_LIT)
        c.vline(90,0,9,IRON)
        c.hline(86,94,3,IRON)
        c.fill(81,28,98,43,HOLE)
        c.disc(90,33,5,BRASS,6)
        c.poly([(85,34),(95,34),(98,40),(82,40)],BRASS)
        c.hline(82,98,41,mix(BRASS,INK,.35))
        c.vline(90,27,29,IRON)
        c.vline(90,40,44,mix(BRASS,INK,.5))
        c.line(97,43,96,55,hx(0x948260))
        c.disc(90,55,7,STONE,7)
        c.disc(90,55,5,HOLE,5)
        for dx,dy,col in ((-2,-2,0xa78d63),(2,-2,0x71887b),(-2,2,0x8e756f),(2,2,0xafa47a)):
            c.fill(90+dx-1,55+dy-1,90+dx+1,55+dy+1,hx(col))
        c.vline(90,50,60,WOOD_LIT)
        c.hline(85,95,55,WOOD_LIT)
        opening(c,19,70,17,35,lit=True,arch=True)
        opening(c,145,70,17,35,arch=True,broken=True)
        shutter(c,166,75,7,28,tilt=-3)
        pipe(c,173,50,125,hx(0x7e8171))
        patch(c,[(43,105),(54,101),(59,108),(55,115),(62,120),(59,127),(41,127)],hx(0x9a846a),seed=11)
        for yy in (123,125,127):box(c,(61-(yy-123),yy,118+(yy-123),yy),STONE)
        door_reveal(c,68,64,44,64)
    elif index==1:
        # Sheriff's office: deep barred openings, ashlar corners, portrait notice.
        masonry(c,(4,36,175,127),hx(0x8c7e69),seed=911,brick=(13,6))
        planks(c,(1,25,178,37),WOOD,seed=912,width=5)
        box(c,(0,24,179,27),WOOD_LIT)
        sign(c,'SHERIFF',42,14,95,color=hx(0x735d43))
        for x in (4,166):
            masonry(c,(x,39,x+8,125),hx(0xa2967b),seed=x,brick=(9,7))
        opening(c,17,72,28,32,bars=True)
        opening(c,135,72,28,32,bars=True)
        poster(c,48,84,13,24,portrait=True)
        c.poly([(153,112),(170,112),(170,116),(154,116)],WOOD)
        beam(c,155,116,155,127,2)
        beam(c,167,116,167,127,2)
        door_reveal(c,68,64,44,64,stone=True)
        box(c,(119,77,126,91),IRON)
        c.fill(120,80,124,88,hx(0xe3b56c))
        c.hline(118,127,92,INK)
        c.line(121,76,121,72,IRON)
        c.line(121,72,116,72,IRON)
        pipe(c,172,39,125)
        planks(c,(0,124,179,127),hx(0x82745d),seed=913,width=4)
        crack(c,[(143,43),(143,49),(138,52),(138,59)],color=hx(0x504b40),lip=STONE)
    elif index==2:
        # Working smithy: an open lean-to, real forge, tools, horseshoes and smoke-dark brick.
        roof(c,22,148,17,40,base=hx(0x6f756d),seed=92)
        planks(c,(25,45,141,127),hx(0x8b714f),seed=921,vertical=True,width=7)
        masonry(c,(147,3,164,127),hx(0x8c8b7e),seed=922,brick=(10,6))
        box(c,(143,0,167,5),hx(0x9c9986))
        c.hline(148,162,2,HOLE)
        for x in (150,158):c.vline(x,6,22,hx(0x5f6056))
        c.fill(3,77,59,125,HOLE)
        beam(c,1,75,59,68,4)
        beam(c,2,78,2,127,3)
        beam(c,58,73,58,127,3)
        for x in (9,17,25,36):
            c.vline(x,81,97,IRON)
            c.hline(x-2,x+3,82,IRON)
        c.poly([(14,108),(35,108),(42,104),(42,112),(35,115),(25,115),(23,121),(32,123),(13,123),(20,118),(20,114),(15,113)],IRON)
        c.hline(15,34,108,CREAM)
        masonry(c,(44,107,55,125),hx(0x716d5f),seed=923,brick=(6,4))
        for x in (46,49,52):c.set(x,109,hx(0xba7645))
        c.line(45,103,55,108,IRON,2)
        c.line(43,103,47,98,WOOD_LIT,2)
        c.fill(150,111,160,123,HOLE)
        c.hline(150,160,113,hx(0xbc7c42))
        for x in range(151,161,3):c.vline(x,116,122,IRON)
        opening(c,118,77,17,25,lit=True)
        for x in (83,95):
            c.vline(x,49,54,IRON)
        c.line(83,54,86,57,IRON,2)
        c.line(86,57,92,57,IRON,2)
        c.line(92,57,95,54,IRON,2)
        door_reveal(c,68,64,44,64)
        rubble(c,126,127,3)
    elif index==3:
        # Stable: layered barn cladding, actual stall gates, hay and hanging tack.
        roof(c,1,176,4,40,base=hx(0x926c42),seed=93)
        planks(c,(3,45,176,127),hx(0x98734c),seed=931,vertical=True,width=7)
        for x in (13,128):
            c.fill(x,72,x+36,124,HOLE)
            planks(c,(x+1,98,x+35,125),WOOD,seed=x,vertical=True,width=7)
            box(c,(x,97,x+36,101),WOOD_LIT)
            beam(c,x+2,120,x+32,102,3,WOOD_LIT)
            for yy in (103,120):
                c.hline(x+1,x+8,yy,IRON)
                c.set(x+6,yy,CREAM)
        c.fill(79,23,101,36,HOLE)
        for x in range(81,99,3):c.line(x,35,x+5,30,hx(0xbda35e))
        beam(c,77,21,103,21,3)
        c.vline(90,22,34,hx(0x9e906a))
        c.disc(90,34,2,IRON,2)
        c.poly([(137,85),(141,79),(148,79),(152,82),(160,79),(162,84),(154,89),(142,89)],hx(0x725741))
        c.vline(152,89,96,hx(0x674c39))
        box(c,(128,117,166,126),WOOD)
        c.hline(130,164,119,hx(0x667467))
        c.line(131,120,160,121,hx(0x829384))
        for yy in (116,119,123):c.hline(7,23,yy,hx(0xb6a06b))
        door_reveal(c,68,64,44,64)
        pipe(c,172,47,125,hx(0x7e7968))
    else:
        # Bank: a stone pediment, fluted pillars, secure windows and keyed plaques.
        masonry(c,(3,36,176,127),hx(0xaca593),seed=941,brick=(17,8))
        roof(c,1,176,5,31,base=hx(0xaaa68f),seed=94)
        box(c,(1,32,178,38),CREAM)
        c.disc(90,21,6,hx(0xb7a264),6)
        c.disc(90,21,4,hx(0x938762),4)
        c.vline(90,17,25,CREAM)
        c.hline(87,93,20,CREAM)
        sign(c,'BANCO',67,42,46,color=hx(0x777b6d))
        opening(c,18,65,18,37,bars=True,arch=True)
        opening(c,144,65,18,37,bars=True,arch=True)
        for x in (52,118):
            box(c,(x-3,54,x+12,59),CREAM)
            box(c,(x,60,x+9,121),hx(0xbdb8a2))
            for xx in (x+2,x+5,x+8):c.vline(xx,62,119,hx(0x989d8b))
            box(c,(x-3,121,x+12,127),CREAM)
        door_reveal(c,68,64,44,64,stone=True)
        box(c,(8,112,32,122),hx(0x777e6b))
        lettering(c,'BANCO',10,115,CREAM)
        box(c,(151,111,170,121),hx(0x777e6b))
        c.hline(154,167,114,INK)
        c.set(165,118,BRASS)
        crack(c,[(166,42),(162,49),(164,54),(159,58)],color=hx(0x77796b),lip=STONE)
    return c




# ---- The western fronts, drawn at their final size ----
#
# They used to be drawn at 180 x 128 and stretched to 288 x 200 by
# street_scale: every pixel came out one or two wide, and the user found the
# fronts plastic and some of their parts unreadable. The same buildings are
# now drawn at 288 x 200 (their layout keeps street_scale's: the door's
# band and the lower 72 rows at their size, the rest spread), each material
# painted at that size, with the trade inside every opening.

WEST_W, WEST_H = 288, 200


def WX(x: float) -> int:
    """A column of the 180-wide layout at 288: its 56 middle ones as they are."""
    if x < 62:
        return round(x * 116 / 62)
    if x < 118:
        return round(116 + x - 62)
    return 288 - round((180 - x) * 116 / 62)


def WY(y: float) -> int:
    """A row of the 128-high layout at 200: its lower 72 rows as they are."""
    return round(y + 72) if y >= 56 else round(y * 128 / 56)


def WB(x0, y0, x1, y1):
    """A box of the layout (inclusive) at 288 x 200."""
    return WX(x0), WY(y0), WX(x1 + 1) - 1, WY(y1 + 1) - 1


def big_sign(c: Canvas, text, x, y, w, color=WOOD) -> None:
    """A board with its letters twice as big, nailed at its corners."""
    box(c, (x, y, x + w, y + 17), mix(color, INK, .18))
    c.fill(x + 2, y + 2, x + w - 2, y + 15, color)
    for yy in range(y + 3, y + 15, 4):
        c.hline(x + 3, x + w - 3, yy, mix(color, INK, .12))
    tw = len(text) * 8 - 2
    lettering(c, text, x + (w - tw) // 2 + 1, y + 5, mix(color, INK, .5), 2)
    lettering(c, text, x + (w - tw) // 2, y + 4, CREAM, 2)
    for xx in (x + 3, x + w - 3):
        c.set(xx, y + 3, IRON)
        c.set(xx, y + 14, IRON)


def interior(c: Canvas, x0, y0, x1, y1, glow=None, seed=1) -> None:
    """A dark room through an opening: its back wall's boards just seen,
    darker up under its lintel; glow (x, y, radius) a warm fire lighting it."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t = (y - y0) / max(1, y1 - y0)
            board = (x - x0) // 6
            base = mix(hx(0x2a211b), hx(0x3a2d22), .3 + .4 * t + .15 * hash2(board, 0, seed))
            if (x - x0) % 6 == 0:
                base = mix(base, INK, .45)
            if glow:
                gx, gy, r = glow
                d = math.hypot(x - gx, y - gy)
                if d < r:
                    base = mix(base, hx(0xc0682c), .55 * (1 - d / r) ** 1.6)
            c.set(x, y, base)


def bell(c: Canvas, cx, top) -> None:
    """A bronze bell in its belfry: a crown, a waisted body flaring to its lip,
    its clapper under it; lit from the upper left."""
    c.hline(cx - 9, cx + 9, top - 4, WOOD_LIT)            # Its yoke
    c.hline(cx - 9, cx + 9, top - 3, mix(WOOD, INK, .4))
    c.fill(cx - 1, top - 2, cx + 1, top, IRON)
    for dy in range(0, 19):
        half = 3 + dy * .28 + (dy - 12) * .9 * (dy > 12) + (dy > 16) * 1.4
        for dx in range(-round(half), round(half) + 1):
            t = (dx + half) / (2 * half)
            col = mix(hx(0xe0c278), hx(0x7d6430), min(1, t * 1.25))
            if dy < 3:
                col = mix(col, hx(0xf0dca0), .35)
            c.set(cx + dx, top + dy, col)
    for dy in range(2, 16):
        c.set(cx - 2 - dy // 5, top + dy, hx(0xf6e6b4))  # Its highlight
    c.hline(cx - 9, cx + 9, top + 18, mix(BRASS, INK, .45))   # The lip
    c.hline(cx - 6, cx + 6, top + 12, mix(BRASS, INK, .3))    # A cast band
    c.vline(cx, top + 19, top + 21, IRON)
    c.disc(cx, top + 22, 1.6, mix(IRON, INK, .3))           # Clapper


def rose(c: Canvas, cx, cy) -> None:
    c.disc(cx, cy, 11, STONE)
    c.disc(cx, cy, 11, mix(STONE, INK, .25), 11)
    c.disc(cx, cy, 10, STONE, 10)
    c.disc(cx, cy, 8, HOLE, 8)
    colours = (0xb3823e, 0x5f8a7c, 0x9a5650, 0xc3b264, 0x6f7fa0, 0x8f6aa0)
    for y in range(cy - 7, cy + 8):
        for x in range(cx - 7, cx + 8):
            d = math.hypot(x - cx, y - cy)
            if d <= 7.2:
                wedge = int((math.atan2(y - cy, x - cx) + math.pi) / (math.tau / 6)) % 6
                col = hx(colours[wedge])
                if d < 2.2:
                    col = hx(0xe2d08a)
                c.light(x, y, mix(col, CREAM, .18 if y < cy else 0))
    for a in range(6):                                     # Its lead tracery
        ang = a * math.tau / 6
        c.line(cx, cy, cx + 7 * math.cos(ang), cy + 7 * math.sin(ang), mix(INK, IRON, .3))
    c.disc(cx, cy, 1.4, mix(INK, IRON, .3))


def horse_head(c: Canvas, x, y) -> None:
    """A bay looking out over its stall's half door, side on, facing right:
    neck, head, dark muzzle, an eye, two ears and its black mane."""
    coat, dark, light = hx(0x7a4a2c), hx(0x4a2c1c), hx(0xa06a40)
    c.poly([(x, y + 22), (x + 2, y + 8), (x + 6, y + 2), (x + 10, y + 1), (x + 14, y + 6),
            (x + 22, y + 12), (x + 23, y + 16), (x + 19, y + 18), (x + 12, y + 15), (x + 9, y + 22)], coat)
    c.poly([(x + 17, y + 11), (x + 22, y + 12), (x + 23, y + 16), (x + 19, y + 18), (x + 16, y + 15)], dark)
    c.set(x + 21, y + 14, INK)                             # Nostril
    c.line(x + 3, y + 8, x + 8, y + 3, light)
    c.line(x + 9, y + 3, x + 16, y + 9, light)
    c.set(x + 11, y + 6, INK)                              # Its eye, with a glint
    c.set(x + 10, y + 5, hx(0xd8c8a8))
    c.poly([(x + 7, y + 2), (x + 8, y - 3), (x + 10, y + 1)], coat)    # Ears
    c.poly([(x + 9, y + 2), (x + 11, y - 2), (x + 12, y + 2)], dark)
    for k in range(9):                                     # The mane down its neck
        c.set(x + 5 - k // 3, y + 3 + k * 2, INK)
        c.set(x + 6 - k // 3, y + 3 + k * 2, dark)


def saddle(c: Canvas, x, rail) -> None:
    """A western saddle thrown over a half door's top rail (row rail): its high
    cantle, the seat dipping to the horn above the rail; a striped blanket
    wider than it, the short rounded skirt, and the fender strap down the door
    to a wooden stirrup."""
    leather, dark, light = hx(0x7f5230), hx(0x4a2c1a), hx(0xb5804c)
    for yy in range(rail + 1, rail + 11):                  # The blanket, striped, under it all
        col = (hx(0xa83c30), hx(0xd8c8a0), hx(0x2f4a5a))[(yy - rail) % 3]
        c.hline(x - 3, x + 25, yy, col)
    c.vline(x - 3, rail + 1, rail + 10, mix(hx(0xa83c30), INK, .4))
    c.vline(x + 25, rail + 1, rail + 10, mix(hx(0xa83c30), INK, .4))
    for yy in range(rail + 1, rail + 8):                   # The skirt, its corners rounded
        inset = 1 if yy == rail + 7 else 0
        c.hline(x + 1 + inset, x + 21 - inset, yy, leather)
    c.hline(x + 2, x + 20, rail + 8, dark)
    for xx in range(x + 3, x + 20, 3):
        c.set(xx, rail + 6, light)                         # Stitching
    for yy in range(rail + 4, rail + 16):                  # The fender strap
        c.hline(x + 8, x + 12, yy, leather if yy < rail + 15 else dark)
        c.set(x + 8, yy, light)
    c.hline(x + 7, x + 13, rail + 16, hx(0x8a6440))        # A wooden stirrup
    c.hline(x + 7, x + 13, rail + 19, hx(0x8a6440))
    c.vline(x + 7, rail + 16, rail + 19, hx(0x8a6440))
    c.vline(x + 13, rail + 16, rail + 19, hx(0x8a6440))
    c.hline(x + 8, x + 12, rail + 20, dark)
    profile = {0: 7, 1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 3, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2,
               13: 3, 14: 3, 15: 4, 16: 5, 17: 6, 18: 6, 19: 6, 20: 5}
    for dx, h in profile.items():                          # Cantle, the seat's dip, the pommel
        c.vline(x + 1 + dx, rail - h, rail, leather)
        c.set(x + 1 + dx, rail - h, light if dx < 8 else leather)
        c.set(x + 1 + dx, rail, dark)
    c.vline(x + 1, rail - 7, rail, dark)
    c.fill(x + 18, rail - 9, x + 19, rail - 7, dark)        # The horn and its cap
    c.hline(x + 17, x + 20, rail - 10, light)


def wanted(c: Canvas, x, y) -> None:
    """A wanted notice: SE BUSCA, a face, the reward."""
    paper = hx(0xc9bd9c)
    c.fill(x, y, x + 23, y + 31, paper)
    c.hline(x, x + 23, y + 31, mix(paper, INK, .4))
    c.vline(x + 23, y, y + 31, mix(paper, INK, .3))
    c.set(x + 2, y + 1, IRON)
    c.set(x + 21, y + 1, IRON)
    lettering(c, 'SE', x + 8, y + 2, mix(INK, RUST, .3))
    lettering(c, 'BUSCA', x + 2, y + 8, mix(INK, RUST, .3))
    c.disc(x + 11.5, y + 18, 3, mix(paper, INK, .55), 3.5)
    c.poly([(x + 5, y + 26), (x + 8, y + 22), (x + 15, y + 22), (x + 18, y + 26)], mix(paper, INK, .5))
    lettering(c, '500', x + 6, y + 27, mix(INK, RUST, .5))
    c.set(x + 3, y + 28, mix(INK, RUST, .5))


def hay(c: Canvas, x0, y0, x1, y1, seed=1) -> None:
    """A bale: packed straw, two twine bands, loose strands at its edges."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            n = hash2(x, y // 2, seed)
            col = mix(hx(0xc8a64e), hx(0x8a6a2a), .25 + .5 * n + .3 * (y - y0) / max(1, y1 - y0))
            c.set(x, y, col)
    for x in (x0 + (x1 - x0) // 3, x1 - (x1 - x0) // 3):
        c.vline(x, y0, y1, hx(0x6b4e2a))
    c.hline(x0, x1, y0, hx(0xe2c878))
    for k in range(0, x1 - x0, 3):
        c.set(x0 + k, y0 - 1 - (k % 2), hx(0xd8bc66))


def anvil(c: Canvas, x, y) -> None:
    """An anvil on its stump: horn to the left, flat face, waist and feet."""
    iron, dark, light = hx(0x55585a), hx(0x2c2e30), hx(0x9da2a0)
    c.poly([(x - 14, y + 1), (x - 4, y), (x + 12, y), (x + 12, y + 5), (x + 4, y + 6), (x - 4, y + 5)], iron)
    c.hline(x - 10, x + 12, y, light)                      # Its worked face
    c.poly([(x - 3, y + 6), (x + 5, y + 6), (x + 4, y + 11), (x - 2, y + 11)], iron)
    c.poly([(x - 6, y + 11), (x + 8, y + 11), (x + 9, y + 14), (x - 7, y + 14)], dark)
    c.fill(x - 5, y + 15, x + 7, y + 28, hx(0x6a4a30))      # The stump
    for yy in range(y + 17, y + 28, 3):
        c.hline(x - 5, x + 7, yy, hx(0x553a26))
    c.vline(x - 5, y + 15, y + 28, hx(0x8a6440))


def hanging_tools(c: Canvas, x0, x1, y) -> None:
    """A rack of a smith's tools on the back wall: a hammer, tongs, a file
    and horseshoes on their nails."""
    c.hline(x0, x1, y, WOOD)
    c.hline(x0, x1, y + 1, mix(WOOD, INK, .5))
    steel, handle = hx(0x8c9190), hx(0x8a6440)
    hx0 = x0 + 4                                           # Hammer
    c.vline(hx0, y + 2, y + 13, handle)
    c.fill(hx0 - 2, y + 2, hx0 + 3, y + 4, steel)
    t = x0 + 13                                            # Tongs, crossed
    c.line(t, y + 2, t + 4, y + 16, steel)
    c.line(t + 4, y + 2, t, y + 16, steel)
    c.set(t + 2, y + 9, INK)
    c.vline(x0 + 23, y + 2, y + 14, mix(steel, INK, .3))    # A file
    c.vline(x0 + 24, y + 2, y + 14, steel)
    for k, hxp in enumerate(range(x0 + 31, x1 - 4, 9)):    # Horseshoes
        c.line(hxp, y + 3, hxp, y + 8, steel)
        c.line(hxp + 5, y + 3, hxp + 5, y + 8, steel)
        c.hline(hxp + 1, hxp + 4, y + 9, steel)
        c.set(hxp + 2, y + 2, INK)


def forge(c: Canvas, x0, y0, x1, y1) -> None:
    """The hearth: a brick box with its coals glowing, the bellows' pipe."""
    masonry(c, (x0, y0, x1, y1), hx(0x6c5f52), seed=925, brick=(7, 4))
    for x in range(x0 + 2, x1 - 1):
        for y in range(y0 - 3, y0 + 1):
            n = hash2(x, y, 77)
            c.light(x, y, hx(0xf6d070) if n > .75 else hx(0xe08a30) if n > .35 else hx(0x9a3a1c))
    c.line(x1, y0 + 4, x1 + 6, y0 + 4, IRON, 2)


def bucket(c: Canvas, x, y) -> None:
    c.fill(x, y, x + 9, y + 10, hx(0x6a4a30))
    for yy in (y + 2, y + 8):
        c.hline(x, x + 9, yy, IRON)
    c.hline(x + 1, x + 8, y, hx(0x2c3c40))
    c.vline(x, y, y + 10, hx(0x8a6440))


def weathered(c: Canvas, eave: int, keep) -> None:
    """Age on a front's walls: shadow under its eave, grime up from the road,
    rain streaks under its sills; keep(x, y) says what is left as it is."""
    for y in range(WEST_H):
        for x in range(WEST_W):
            if not c.solid(x, y) or keep(x, y) or (x, y) in c.lights:
                continue
            col = c.get(x, y)
            k = 0.0
            if eave <= y < eave + 7:
                k += .32 * (1 - (y - eave) / 7)
            if y > WEST_H - 12:
                k += .22 * (y - (WEST_H - 12)) / 12
            if hash2(x // 3, y // 9, 5) > .93:
                k += .08
            if k:
                c.set(x, y, mix(col, INK, min(.5, k)))


def western_native(index: int) -> Canvas:
    """The five western fronts (church, sheriff, smithy, stable, bank) at 288 x 200."""
    c = Canvas(WEST_W, WEST_H)
    door = (122, 136, 44, 64)                              # Where the game puts the door
    in_door = lambda x, y: 116 <= x < 172 and y >= 128     # noqa: E731
    if index == 0:
        # Chapel: clapboard, a bronze bell in its belfry, a rose and arched windows.
        roof(c, WX(2), WX(176), WY(18), WY(43), base=hx(0x6d776f), seed=31)
        planks(c, (WX(3), WY(47), WX(176), 199), hx(0xbab399), seed=901, width=6)
        planks(c, (WX(153), WY(47), WX(176), 199), hx(0x9d9b85), seed=902, width=6)
        planks(c, (WX(75), WY(24), WX(104), WY(58)), hx(0xc0b69d), seed=903, width=6)
        c.poly([(WX(72), WY(24)), (WX(90), WY(3)), (WX(108), WY(24))], hx(0x758076))
        for k in range(1, 12):                             # Its slates in rows
            y = WY(3) + k * (WY(24) - WY(3)) // 12
            half = (WX(108) - WX(72)) * k // 24
            c.hline(WX(90) - half + 1, WX(90) + half - 1, y, hx(0x5f6a62))
        beam(c, WX(90), WY(3), WX(73), WY(24), 2, WOOD_LIT)
        c.vline(WX(90), 0, WY(9), IRON)
        c.hline(WX(90) - 4, WX(90) + 4, 4, IRON)
        x0, y0, x1, y1 = WB(81, 28, 98, 43)
        interior(c, x0, y0, x1, y1, seed=3)
        bell(c, (x0 + x1) // 2, y0 + 8)
        c.line(x1 - 3, y0 + 29, x1 - 3, y1, hx(0x948260))   # Its rope
        rose(c, WX(90), WY(55) - 4)
        opening(c, WX(19), WY(70), WX(36) - WX(19), 35, lit=True, arch=True)
        opening(c, WX(145), WY(70), WX(162) - WX(145), 35, arch=True, broken=True)
        shutter(c, WX(166), WY(75), WX(173) - WX(166), 28, tilt=-3)
        pipe(c, WX(173), WY(50), WY(125))
        patch(c, [(WX(x), WY(y)) for x, y in ((43, 105), (54, 101), (59, 108), (55, 115), (62, 120), (59, 127),
                                              (41, 127))], hx(0x9a846a), seed=11)
        for k, yy in enumerate((195, 197, 199)):
            box(c, (WX(61) - k * 2, yy, WX(118) + k * 2, yy), STONE)
        door_reveal(c, *door)
        weathered(c, WY(43) + 9, in_door)
    elif index == 1:
        # Sheriff's office: ashlar, deep barred openings, a wanted notice, a lamp.
        masonry(c, (WX(4), WY(36), WX(175), 199), hx(0x8c7e69), seed=911, brick=(13, 6))
        planks(c, (WX(1), WY(25), WX(178), WY(37)), WOOD, seed=912, width=5)
        box(c, (0, WY(24), 287, WY(24) + 3), WOOD_LIT)
        big_sign(c, 'SHERIFF', WX(42), WY(14) - 6, WX(137) - WX(42), color=hx(0x735d43))
        for x in (4, 166):
            masonry(c, (WX(x), WY(39), WX(x + 8), 197), hx(0xa2967b), seed=x, brick=(9, 7))
        opening(c, WX(17), WY(72), WX(45) - WX(17), 32, bars=True)
        opening(c, WX(135), WY(72), WX(163) - WX(135), 32, bars=True)
        wanted(c, WX(48) + 1, WY(84) - 4)
        c.poly([(WX(153), WY(112)), (WX(170), WY(112)), (WX(170), WY(116)), (WX(154), WY(116))], WOOD)
        beam(c, WX(155), WY(116), WX(155), 197, 2)
        beam(c, WX(167), WY(116), WX(167), 197, 2)
        box(c, (WX(119), WY(77), WX(126), WY(91)), IRON)
        c.fill(WX(119) + 2, WY(80), WX(126) - 2, WY(88), hx(0xe3b56c))
        for y in range(WY(80), WY(88) + 1):
            for x in range(WX(119) + 2, WX(126) - 1):
                c.light(x, y, hx(0xf0c47a) if y < WY(83) else hx(0xd9a35c))
        c.hline(WX(118), WX(127), WY(92), INK)
        c.line(WX(121), WY(76), WX(121), WY(72), IRON)
        c.line(WX(121), WY(72), WX(116), WY(72), IRON)
        pipe(c, WX(172), WY(39), WY(125))
        planks(c, (0, 196, 287, 199), hx(0x82745d), seed=913, width=4)
        crack(c, [(WX(143), WY(43)), (WX(143), WY(49)), (WX(138), WY(52)), (WX(138), WY(59))],
              color=hx(0x504b40), lip=STONE)
        door_reveal(c, *door, stone=True)
        weathered(c, WY(37) + 1, in_door)
    elif index == 2:
        # Smithy: an open lean-to with its forge glowing, the anvil, tools on the wall.
        roof(c, WX(22), WX(148), WY(17), WY(40), base=hx(0x6f756d), seed=92)
        planks(c, (WX(25), WY(45), WX(141), 199), hx(0x8b714f), seed=921, vertical=True, width=7)
        masonry(c, (WX(147), WY(3), WX(164), 199), hx(0x8c8b7e), seed=922, brick=(10, 6))
        box(c, (WX(143), 0, WX(167), WY(5)), hx(0x9c9986))
        c.hline(WX(148), WX(162), WY(2), HOLE)
        for x in (150, 158):
            c.vline(WX(x), WY(6), WY(22), hx(0x5f6056))
        x0, y0, x1, y1 = WB(3, 77, 59, 125)
        interior(c, x0, y0, x1, y1, glow=(x1 - 16, y1 - 18, 46), seed=7)
        hanging_tools(c, x0 + 6, x1 - 30, y0 + 6)
        forge(c, x1 - 26, y1 - 16, x1 - 4, y1)
        anvil(c, x0 + 34, y1 - 28)
        bucket(c, x0 + 6, y1 - 10)
        beam(c, WX(1), WY(75), WX(59), WY(68), 4)
        beam(c, WX(2), WY(78), WX(2), 199, 3)
        beam(c, WX(58), WY(73), WX(58), 199, 3)
        sx0, sy0, sx1, sy1 = WB(150, 111, 160, 123)          # The chimney's fire door
        c.fill(sx0, sy0, sx1, sy1, HOLE)
        for x in range(sx0 + 1, sx1):
            c.light(x, sy0 + 2, hx(0xbc7c42))
        for x in range(sx0 + 1, sx1, 3):
            c.vline(x, sy0 + 4, sy1 - 1, IRON)
        opening(c, WX(118), WY(77), WX(135) - WX(118), 25, lit=True)
        hs = WX(90)                                        # A horseshoe over the door, points up
        c.line(hs - 5, WY(52), hs - 5, WY(52) + 7, IRON, 2)
        c.line(hs + 4, WY(52), hs + 4, WY(52) + 7, IRON, 2)
        c.hline(hs - 4, hs + 3, WY(52) + 8, IRON)
        c.hline(hs - 4, hs + 3, WY(52) + 9, mix(IRON, INK, .4))
        rubble(c, WX(126), 199, 3)
        door_reveal(c, *door)
        weathered(c, WY(40) + 9, in_door)
    elif index == 3:
        # Stable: barn cladding, stalls with a horse and a saddle, a hayloft.
        roof(c, WX(1), WX(176), WY(4), WY(40), base=hx(0x926c42), seed=93)
        planks(c, (WX(3), WY(45), WX(176), 199), hx(0x98734c), seed=931, vertical=True, width=7)
        for k, x in enumerate((13, 128)):
            x0, y0, x1, y1 = WB(x, 72, x + 36, 124)
            interior(c, x0, y0, x1, y1, seed=11 + k)
            c.vline((x0 + x1) // 2 + 6, y0, y1, mix(WOOD, INK, .4))     # A stall's post
            for yy in range(y1 - 5, y1 + 1):                  # Straw on its floor
                for xx in range(x0, x1 + 1):
                    if hash2(xx, yy, 9) > .55:
                        c.set(xx, yy, hx(0xb7963e) if hash2(xx, yy, 4) > .5 else hx(0x8a6a2a))
            if k == 0:
                horse_head(c, x0 + 14, y0 + 6)
            half = y0 + 26
            planks(c, (x0 + 1, half, x1 - 1, y1 + 1), WOOD, seed=x, vertical=True, width=7)
            box(c, (x0, half - 1, x1, half + 3), WOOD_LIT)
            beam(c, x0 + 3, y1 - 2, x1 - 4, half + 5, 3, WOOD_LIT)
            for yy in (half + 6, y1 - 3):
                c.hline(x0 + 1, x0 + 9, yy, IRON)
                c.set(x0 + 7, yy, CREAM)
            if k == 1:
                saddle(c, x0 + 10, half - 1)
        x0, y0, x1, y1 = WB(79, 23, 101, 36)                 # The hayloft
        interior(c, x0, y0, x1, y1, seed=21)
        hay(c, x0 + 1, y1 - 12, x1 - 1, y1, seed=5)
        for k in range(8):
            c.set(x0 + 2 + k * 3, y1 + 1 + k % 2, hx(0xc8a64e))
        beam(c, WX(77), WY(21), WX(103), WY(21), 3)
        c.disc(WX(90), WY(21) + 4, 2, IRON)
        c.vline(WX(90), WY(21) + 6, y0 + 10, hx(0x9e906a))   # Its rope and hook
        c.line(WX(90), y0 + 10, WX(90) + 2, y0 + 12, IRON)
        tx0, ty0, tx1, ty1 = WB(128, 117, 166, 126)          # A water trough
        box(c, (tx0, ty0, tx1, ty1), WOOD)
        c.hline(tx0 + 2, tx1 - 2, ty0 + 2, hx(0x667467))
        c.line(tx0 + 3, ty0 + 3, tx1 - 6, ty0 + 3, hx(0x829384))
        for yy in (188, 191, 195):
            c.hline(WX(7), WX(23), yy, hx(0xb6a06b))
        pipe(c, WX(172), WY(47), WY(125), hx(0x7e7968))
        door_reveal(c, *door)
        weathered(c, WY(40) + 9, in_door)
    else:
        # Bank: a stone pediment, fluted pillars, secure windows and keyed plaques.
        masonry(c, (WX(3), WY(36), WX(176), 199), hx(0xaca593), seed=941, brick=(17, 8))
        roof(c, WX(1), WX(176), WY(5), WY(31), base=hx(0xaaa68f), seed=94)
        box(c, (WX(1), WY(32), WX(178), WY(38)), CREAM)
        for x in range(WX(4), WX(176), 6):                   # Dentils under its cornice
            c.fill(x, WY(38) + 1, x + 2, WY(38) + 3, mix(CREAM, INK, .3))
        c.disc(WX(90), WY(21), 9, hx(0xb7a264), 9)
        c.disc(WX(90), WY(21), 6, hx(0x938762), 6)
        c.vline(WX(90), WY(21) - 6, WY(21) + 6, CREAM)
        c.hline(WX(90) - 4, WX(90) + 4, WY(21) - 2, CREAM)
        big_sign(c, 'BANCO', WX(67) - 2, WY(42), WX(113) - WX(67) + 4, color=hx(0x777b6d))
        opening(c, WX(18), WY(65), WX(36) - WX(18), 37, bars=True, arch=True)
        opening(c, WX(144), WY(65), WX(162) - WX(144), 37, bars=True, arch=True)
        for x in (52, 118):
            box(c, WB(x - 3, 54, x + 12, 59), CREAM)
            px0, py0, px1, py1 = WB(x, 60, x + 9, 121)
            box(c, (px0, py0, px1, py1), hx(0xbdb8a2))
            for xx in range(px0 + 2, px1 - 1, 3):
                c.vline(xx, py0 + 2, py1 - 2, hx(0x989d8b))
                c.vline(xx + 1, py0 + 2, py1 - 2, mix(hx(0xbdb8a2), CREAM, .3))
            box(c, WB(x - 3, 121, x + 12, 127), CREAM)
        bx0, by0, bx1, by1 = WB(8, 112, 32, 122)
        box(c, (bx0, by0, bx1, by1), hx(0x777e6b))
        lettering(c, 'BANCO', bx0 + 4, by0 + 3, CREAM)
        sx0, sy0, sx1, sy1 = WB(151, 111, 170, 121)
        box(c, (sx0, sy0, sx1, sy1), hx(0x777e6b))
        c.hline(sx0 + 4, sx1 - 4, sy0 + 3, INK)
        c.set(sx1 - 5, sy1 - 3, BRASS)
        crack(c, [(WX(166), WY(42)), (WX(162), WY(49)), (WX(164), WY(54)), (WX(159), WY(58))],
              color=hx(0x77796b), lip=STONE)
        door_reveal(c, *door, stone=True)
        weathered(c, WY(38) + 4, in_door)
    return c


def finish_west(image: Image) -> Image:
    """terrain/facades at 288 x 200, drawn at that size; the doorway band is
    the refined source's, unscaled (the door overlay and the road through it)."""
    frames = image.width // FRAME_WIDTH['facades']
    out = Image(WEST_W * frames, WEST_H)
    for index in range(frames):
        drawn = western_native(index).image()
        for y in range(WEST_H):
            for x in range(WEST_W):
                color = drawn.get(x, y)
                if 122 <= x < 166 and y >= 136:
                    color = image.get(index * FRAME_WIDTH['facades'] + x - 54, y - 72)
                out.set(index * WEST_W + x, y, color)
    return out


def urban(c: Canvas,index:int) -> None:
    index %= 8
    # All urban door openings remain at x98,y128, 44x64; dress around them.
    door_reveal(c,98,128,44,64,stone=index!=0)
    if index>=4:
        # New service buildings have authored equipment; add only grounded
        # architectural wear, without substituting the checkpoint's furniture.
        for x in (8,230):
            c.vline(x,139,185,mix(STONE,INK,.35))
        crack(c,[(49,176),(53,180),(51,186)],color=hx(0x545c53),lip=STONE)
        for x in (95,145):
            bolt(c,x,135);bolt(c,x,181)
        return
    if index==0:
        sign(c,'MERCADO MARTIN',13,93,212,color=hx(0x34594c))
        for x in (22,76,136,190):
            for xx in range(x-2,x+31,8):
                box(c,(xx,24,xx+5,27),STONE)
            c.hline(x-3,x+30,79,mix(STONE,INK,.35))
        # Readable goods behind the shop glass, shelves and hanging price tags.
        for x0 in (12,155):
            for yy in (147,168):
                c.hline(x0+3,x0+65,yy,hx(0x6c715d))
            for i,x in enumerate(range(x0+7,x0+63,10)):
                col=hx(0x819477) if i%2 else hx(0xac9c6d)
                c.fill(x,137,x+4,146,col)
                c.fill(x+1,134,x+3,137,col)
                c.hline(x+1,x+3,141,hx(0xc8bea3))
            for x in range(x0+6,x0+62,14):
                c.disc(x+5,163,5,hx(0xa48655),3)
                c.line(x+3,162,x+5,164,hx(0xd0b27a))
            c.fill(x0+23,153,x0+40,158,hx(0xb9b294))
            lettering(c,'OFERTA',x0+22,153,hx(0x5c6653))
        for x in range(8,230,12):
            c.set(x,111,hx(0xe1d8b9))
            c.vline(x+9,112,118,hx(0x665d4e))
        for x in (12,225):
            c.line(x,121,x+4 if x<50 else x-4,128,IRON,2)
        box(c,(211,163,223,188),hx(0x365273))
        c.fill(213,165,221,177,hx(0xc1bba5))
        lettering(c,'HOY',212,168,hx(0x515b5b))
        c.hline(214,220,175,hx(0x5b625b))
        c.hline(213,221,182,INK)
        pipe(c,229,16,189)
        patch(c,[(18,178),(37,178),(41,184),(36,190),(17,189)],hx(0x8c6852),seed=62)
    elif index==1:
        # Cast plaque, duty roster, speaking grille and articulated flag cloth.
        box(c,(81,102,158,116),hx(0x263c57))
        lettering(c,'POLICIA',107,107,hx(0xc4c3ac))
        pts=[]
        for k in range(10):
            a=-math.pi/2+k*math.pi/5
            r=5 if k%2==0 else 2
            pts.append((91+math.cos(a)*r,109+math.sin(a)*r))
        c.poly(pts,BRASS)
        box(c,(44,170,72,188),hx(0x66766a))
        c.fill(47,173,69,185,hx(0xb3ad92))
        for yy in (176,179,182):c.hline(49,66-(yy%3)*2,yy,hx(0x5e675b))
        box(c,(153,141,160,158),hx(0x6a7776))
        for yy in range(144,153,3):c.hline(155,158,yy,INK)
        c.set(156,156,hx(0xc4b986))
        for x in (11,47,167,203):
            for yy in (123,155):
                c.hline(x,x+25,yy,IRON)
                for xx in range(x+2,x+26,5):bolt(c,xx,yy)
        for y in range(56,79):
            left=218+round(math.sin((y-56)/7)*2)
            for x in range(left,min(235,left+12)):
                col=hx(0x925746) if x-left<4 else hx(0xc3b99a) if x-left<8 else hx(0x566d6b)
                if x%4==0:col=mix(col,INK,.2)
                c.set(x,y,col)
        crack(c,[(185,90),(181,96),(184,101),(176,108),(177,115)],color=hx(0x787b70),lip=STONE)
        for x in (83,153):
            c.vline(x,121,186,hx(0x9d9d8e))
            c.vline(x+2,121,186,hx(0xc8c5ae))
    elif index==2:
        # Services explain the building's use: meter boxes, real AC pipework,
        # mailboxes, washing left out, and rain stains below the cornice.
        pipe(c,9,25,188,hx(0x788276))
        for x in (18,31,44):
            box(c,(x,171,x+10,181),hx(0x708172))
            c.hline(x+2,x+8,174,INK)
            c.set(x+7,178,BRASS)
        box(c,(58,171,78,187),hx(0x65766b))
        for x in (63,73):
            c.disc(x,176,3,hx(0xaaa991),3)
            c.set(x,176,INK)
        c.vline(69,164,170,IRON)
        c.hline(106,122,109,IRON)
        c.line(123,103,129,106,IRON)
        c.vline(129,106,119,IRON)
        c.vline(129,120,126,hx(0x6a705d))
        c.line(56,111,94,110,hx(0x5e5b4f))
        for x,col in ((61,0x9c9d82),(75,0x6e8577),(86,0xb2a689)):
            c.poly([(x,111),(x+6,111),(x+7,120),(x+1,120)],hx(col))
            c.vline(x+2,113,119,mix(hx(col),INK,.2))
        for x in (140,160,181,201,221):
            c.set(x,93,hx(0xb7b8a2))
        for x in (143,229):
            c.line(x,95,x+7 if x<160 else x-7,104,IRON,2)
            bolt(c,x,95)
        lettering(c,'AGUA',38,4,hx(0xc8ba93))
        patch(c,[(170,168),(185,165),(194,171),(191,178),(204,185),(196,190),(169,190)],hx(0x9b765c),seed=65)
        for x in (96,130,182):c.vline(x,23,29+(x%7),hx(0x8e705b))
        poster(c,82,161,10,22)
    else:
        # The checkpoint's panels are cast concrete, not generic brick. Tie
        # holes, exposed aggregate and rebar follow the large panel joints.
        for x in (18,58,178,218):
            for y in (109,151,179):
                if 94<x<146:continue
                c.disc(x,y,2,hx(0x646b60),2)
                c.set(x-1,y-1,hx(0xaaa994))
        patch(c,[(6,169),(20,165),(29,172),(25,180),(34,187),(30,191),(6,191)],hx(0x858474),brick=(12,7),seed=66)
        for x,y in ((9,176),(20,181),(25,188)):
            c.line(x,y,x+7,y-4,hx(0x6c6f64))
            c.set(x+3,y-2,IRON)
        crack(c,[(188,98),(183,106),(186,111),(179,120),(181,131)],color=hx(0x5a6258),lip=STONE)
        box(c,(17,129,63,150),hx(0x697765))
        lettering(c,'RETEN',28,133,CREAM)
        lettering(c,'NO PASAR',21,141,hx(0xc0b18c))
        box(c,(64,151,78,177),hx(0x66745f))
        for yy in (155,158,161):c.hline(67,75,yy,INK)
        c.set(69,170,hx(0xa5a485))
        c.set(74,170,hx(0x98684d))
        c.vline(71,97,150,IRON)
        c.hline(71,81,98,IRON)
        for x in (12,32,52,73):
            bolt(c,x,17,hx(0x77806a))
            bolt(c,x,59,hx(0x77806a))
        box(c,(11,44,75,48),hx(0x657460))
        c.hline(14,71,44,hx(0x9fa68a))
        c.line(17,29,27,34,hx(0x617975))
        c.line(45,29,57,34,hx(0x617975))
        c.disc(158,159,6,hx(0x65725d),6)
        c.disc(158,159,3,hx(0x95977a),3)
        c.set(158,159,INK)
        for y in range(171,187,5):
            c.hline(159,166,y,hx(0x747f68))
        c.line(74,68,83,91,IRON)
        for y in range(71,93,6):c.hline(74,81,y,IRON)
        # A cabin with folded corner posts, recessed glazing and lower panels.
        for x in (9,74):
            c.line(x,19,x,61,hx(0x293a2f),2)
            c.vline(x+2,20,61,hx(0x87927a))
        for x in (13,34,55):
            box(c,(x,50,x+17,59),hx(0x50644d))
            c.hline(x+2,x+14,52,hx(0x6e8062))
        c.hline(12,73,24,INK);c.hline(12,73,43,hx(0x829180))
        for x in (29,48,67):
            c.line(x,26,x,42,hx(0x33473f),2)
            c.vline(x-1,27,41,hx(0x7a8981))
        # Hooded cylindrical spotlight and its U-shaped tilt bracket.
        c.fill(76,28,90,40,None)
        c.line(75,43,85,43,IRON,2);c.line(85,43,86,38,IRON,2)
        c.poly([(76,30),(87,26),(92,29),(91,38),(78,40)],hx(0x526866))
        c.line(77,30,88,27,hx(0x91a29a))
        for x in (79,82):c.line(x,32,x+1,37,hx(0x2d4141))
        c.disc(90,32,3,INK,6);c.disc(91,32,2,hx(0x94aaa2),4)
        c.line(90,29,90,31,hx(0xc8cbb4))
        c.light(91,33,hx(0xe4d39c));c.light(92,32,hx(0xd1c58f))
        c.line(77,29,90,25,IRON,2);bolt(c,84,39)
        # Rectangular floodlight: deep housing, cooling fins and recessed glass.
        c.fill(212,12,229,25,None)
        box(c,(213,13,228,25),hx(0x3d5154))
        c.fill(215,15,226,22,hx(0x202e32))
        c.fill(216,16,225,21,hx(0xa6b4ac))
        for x in (217,220,223):c.light(x,18,hx(0xe1d4aa))
        c.hline(215,226,14,hx(0x99aaa4))
        c.line(217,26,224,26,IRON);c.vline(221,26,31,IRON)
        for y in (15,19,23):c.set(212,y,hx(0x778987))


def palisade(c: Canvas,state:int) -> None:
    if state<2:
        # Bolted diagonal brace and U-shaped iron shoes on the original rails.
        beam(c,3,24,38,48,3,hx(0x81603c))
        for x in (3,15,33,40):
            for y in (18,52):
                box(c,(x-2,y,x+2,y+5),hx(0x686d65))
                bolt(c,x,y+2)
        for x in (5,11,23,35):
            c.vline(x,40,46,hx(0x513a28))
            c.set(x+1,45,hx(0xba9562))
        if state==1:
            crack(c,[(14,7),(16,15),(14,23),(17,29),(15,36),(16,44)],color=hx(0x2e251e),lip=WOOD_LIT)
            c.line(27,36,32,32,IRON,2)
            c.line(32,32,35,34,IRON)
            c.hline(28,34,55,hx(0xbaa176))
    else:
        # Visible end grain on the same snapped stakes and a twisted strap.
        for x,y in ((5,62),(11,65),(23,64),(35,61)):
            c.hline(x-2,x+2,y,hx(0xb99a65))
            c.hline(x-1,x+1,y+1,hx(0x6e5031))
        c.line(7,69,20,65,IRON,2)
        c.line(20,65,29,69,IRON)
        for x in (10,18):c.set(x,68,hx(0xb3b39c))


def ruins(c: Canvas) -> None:
    # Rough plaster survives over exposed adobe, with deep reveals in the
    # left window and loose lath visible through its broken shutter.
    patch(c,[(8,20),(16,21),(21,29),(29,26),(38,34),(33,42),(14,37),(8,30)],hx(0xb09c78),seed=81)
    crack(c,[(44,29),(42,38),(47,44),(43,52),(44,64),(38,72)],color=hx(0x493d2d),lip=WOOD_LIT)
    crack(c,[(121,43),(127,49),(125,58),(132,65),(129,76)],color=hx(0x493d2d),lip=WOOD_LIT)
    box(c,(14,32,38,36),hx(0x9f784a))
    c.vline(16,37,52,hx(0xb59360))
    c.vline(35,37,52,hx(0x4b3524))
    c.hline(15,37,55,hx(0xb99b6d))
    c.hline(17,35,56,hx(0x483c2b))
    shutter(c,19,37,8,17,tilt=5)
    for x,y in ((8,10),(27,16),(47,22),(65,27)):
        bolt(c,x,y)
    for x in (9,20,31,42,53):
        c.line(x,15+x//4,x+4,15+x//4+12,hx(0x60452f),2)
        c.set(x+1,16+x//4,hx(0xb5915d))
    c.line(112,35,120,53,WOOD_LIT,3)
    c.line(120,53,115,60,hx(0x583f2b),2)
    for x,y in ((7,80),(20,77),(37,80),(52,76),(118,79),(163,78)):
        c.poly([(x,y),(x+1,y-4),(x+6,y-5),(x+9,y-1),(x+8,y+2)],hx(0x967452))
        c.hline(x+2,x+6,y-4,hx(0xc09e6e))
    # Do not place debris across the 44 px road opening.
    c.line(5,76,31,80,hx(0x8e6d44),3)
    c.line(151,81,176,76,hx(0x8e6d44),2)


def doors(c: Canvas,index:int) -> None:
    state=index%3
    kind=index//3
    if kind==0:
        if state<2:
            # Forged strap hinges wrap round a pin, with individual rivets.
            for y in (9,52):
                box(c,(1,y-2,41,y+2),hx(0x656d68))
                c.vline(2,y-4,y+4,hx(0x929b8f))
                for x in (5,13,23,33,39):bolt(c,x,y)
            box(c,(3,28,40,34),hx(0x8d693f))
            for x in (5,37):
                box(c,(x-2,26,x+2,36),hx(0x747b70))
                bolt(c,x,29)
                bolt(c,x,34)
            box(c,(18,36,26,46),hx(0xb19555))
            c.line(19,37,19,34,IRON,2)
            c.line(19,34,25,34,IRON,2)
            c.line(25,34,25,37,IRON,2)
            c.disc(22,41,1,INK,2)
            c.set(19,37,hx(0xd4bd78))
            for x,y in ((7,16),(20,21),(35,47)):
                c.line(x,y,x+2,y+5,hx(0x4b3322))
                c.set(x+3,y+5,hx(0xb18b55))
            if state==1:
                crack(c,[(14,5),(16,13),(14,19),(17,25),(15,33),(17,41),(15,51),(17,59)],color=HOLE,lip=WOOD_LIT)
                c.line(26,22,35,15,hx(0xc1a06c),2)
                c.line(27,24,35,18,INK)
        else:
            for x in (3,38):
                for y in (9,52):
                    c.vline(x,y-3,y+3,IRON)
                    bolt(c,x,y)
            c.line(1,16,7,19,WOOD_LIT)
            c.line(36,38,41,34,WOOD_LIT)
            c.line(11,62,25,59,IRON)
    elif kind==1:
        if state<2:
            for y in range(4,59,4):
                c.hline(3,40,y,hx(0x8a9690))
                c.hline(3,40,y+1,hx(0x58665f))
            for x in (2,41):
                c.vline(x,2,63,hx(0x9aa28f))
                for y in (11,31,53):bolt(c,x,y)
            box(c,(17,51,27,58),hx(0x727d73))
            c.hline(19,25,53,INK)
            box(c,(19,58,25,63),BRASS)
            if state==1:
                # Bowed slats follow the ragged impact, not a straight stripe.
                crack(c,[(13,18),(11,24),(15,29),(12,36),(15,43)],color=HOLE,lip=IRON)
                for y,xx in ((18,27),(22,29),(26,31)):
                    c.line(xx,y,35,y+2,hx(0xb0b7a3),2)
                    c.line(xx,y+1,35,y+3,HOLE)
        else:
            for x in range(3,40,6):
                c.vline(x,3,7+(x%4),hx(0xa3aa96))
            c.line(8,61,20,59,IRON,2)
            c.line(20,59,27,62,hx(0xb5b79f))
    else:
        # Railway coupling door: pin heads, forged jaws, chain and torn sheets.
        if state<2:
            for x in (8,14,29,35):
                for y in (45,54):bolt(c,x,y)
            for x in (11,31):
                c.vline(x,44,56,hx(0x9ca79a))
                c.vline(x+1,44,56,hx(0x4e5b53))
            for x in range(4,40,6):
                c.disc(x,26,2,hx(0xa4ac9d),1)
                c.set(x,26,hx(0x4c554e))
            if state==1:
                crack(c,[(22,30),(19,37),(23,43),(21,50)],color=HOLE,lip=RUST)
        else:
            for x in (4,36):
                c.line(x,4,x+3,8,IRON)
                bolt(c,x+1,5)


def _canvas(image: Image,frame:int,width:int) -> Canvas:
    c=Canvas(width,image.height)
    for y in range(image.height):
        for x in range(width):
            color=image.get(frame*width+x,y)
            if color[3]:
                if color[3]==254:c.light(x,y,color[:3])
                else:c.set(x,y,color[:3])
    return c


FRONT_SIZES = {'facades': (288, 200), 'city_fronts': (288, 216)}


def street_scale(name: str, image: Image) -> Image:
    """Expand the architecture around a fixed, person-sized door and jambs.

    The lower 72 rows and middle 56 columns retain their native dimensions;
    walls, upper floors and roofs supply the extra span. No door is stretched.
    Apply after the construction pass so equipment and markings move with it.
    """
    old_w = FRAME_WIDTH[name]
    width, height = FRONT_SIZES[name]
    out = Image(image.width // old_w * width, height)
    def source(at, old, new, fixed, bottom=False):
        if bottom:
            return old - (new - at) if at >= new - fixed else at * (old - fixed) // (new - fixed)
        lo, hi = (new - fixed) // 2, (old - fixed) // 2
        if at < lo: return at * hi // lo
        if at < lo + fixed: return hi + at - lo
        return old - 1 - (new - 1 - at) * hi // lo
    for frame in range(image.width // old_w):
        for y in range(height):
            sy = source(y, image.height, height, 72, True)
            for x in range(width):
                sx = source(x, old_w, width, 56)
                out.set(frame * width + x, y, image.get(frame * old_w + sx, sy))
    return out


def finish(name: str, image: Image) -> Image:
    """Return the finished sheet, preserving frame bounds and open doorways."""
    if name not in SUPPORTED:
        return image
    width=FRAME_WIDTH[name]
    if image.width%width:
        raise ValueError(f'{name}: width {image.width} is not a whole {width}px frame')
    out=Image(image.width,image.height)
    for index in range(image.width//width):
        source=_canvas(image,index,width)
        c=western(index) if name=='facades' else source
        if name=='wall':palisade(c,index)
        elif name=='wall_ruins':ruins(c)
        elif name=='city_fronts':urban(c,index)
        elif name=='door':doors(c,index)
        drawn=c.image()
        for y in range(image.height):
            for x in range(width):
                original=image.get(index*width+x,y)
                color=drawn.get(x,y)
                # Torn timber/shutter gaps are part of their visible state.
                # Preserve every original transparent pixel in those sheets.
                if name in ('wall','door') and original[3]==0:color=original
                # Fronts' central opening is reserved for the door overlay and
                # the road through it. It is copied byte-for-byte from source.
                if name in ('facades','city_fronts'):
                    dx=(width-44)//2
                    if dx<=x<dx+44 and y>=image.height-64:color=original
                if name=='wall_ruins' and 68<=x<112:color=original
                out.set(index*width+x,y,color)
    return out


def preview(path:Path,assets:Path) -> None:
    """Before/after authored details at 3x, read from PNGs without regeneration."""
    from embed_assets import decode_png_rgba
    names=['wall','wall_ruins','facades','city_fronts','door']
    pairs=[]
    import make_terrain, make_city
    from refine_terrain import refine
    for name in names:
        w,h,raw=decode_png_rgba(assets/f'sprites/terrain/{name}.png')
        image=Image(w,h)
        image.px=[tuple(raw[i:i+4]) for i in range(0,len(raw),4)]
        if name in FRONT_SIZES:
            source = make_terrain.make_facades() if name=='facades' else make_city.make_city_fronts(marked=False)
            pairs.append((name,source,refine(name,source)))
        else: pairs.append((name,image,finish(name,image)))
    scale=3
    height=sum(max(before.height,after.height)*scale+35 for _,before,after in pairs)
    review=Canvas(1500,height)
    review.fill(0,0,1499,height-1,hx(0x292627))
    top=0
    for name,before,after in pairs:
        lettering(review,name.upper(),12,top+4,CREAM)
        for side,image in enumerate((before,after)):
            count=FRONT_SIZES[name][0] if name in FRONT_SIZES and side else FRAME_WIDTH[name]
            max_frames=min(3,image.width//count)
            for frame in range(max_frames):
                # Show western church, sheriff and smithy; three urban uses;
                # all three destruction states of walls and wooden doors.
                ox=12+side*750+frame*count*scale
                if ox+count*scale>side*750+747:break
                for y in range(image.height):
                    for x in range(count):
                        color=image.get(frame*count+x,y)
                        if color[3]:
                            review.fill(ox+x*scale,top+22+y*scale,
                                        ox+x*scale+scale-1,top+22+y*scale+scale-1,color[:3])
        top+=max(before.height,after.height)*scale+35
    review.image().save(path)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,default=Path(__file__).resolve().parent.parent/'assets')
    parser.add_argument('--preview',type=Path,default=Path(__file__).resolve().parent.parent/'build/terrain_architecture_review.png')
    args=parser.parse_args()
    preview(args.preview,args.assets)
    print(f'architecture: preview {args.preview}')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
