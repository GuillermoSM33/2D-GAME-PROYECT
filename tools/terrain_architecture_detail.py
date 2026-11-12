#!/usr/bin/env python3
"""Authored construction detail for the road's interactive architecture.

finish(name, image) keeps every frame and doorway aligned with the collision
geometry. Fronts have readable construction, deep openings, ironwork and
objects belonging to their trade. Damage follows timber joints or masonry
rather than adding noise. The five small western fronts are drawn afresh at
their existing 180 x 128 size; urban fronts retain their larger architecture.
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


def urban(c: Canvas,index:int) -> None:
    # All urban door openings remain at x98,y128, 44x64; dress around them.
    door_reveal(c,98,128,44,64,stone=index!=0)
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
    for name in names:
        w,h,raw=decode_png_rgba(assets/f'sprites/terrain/{name}.png')
        image=Image(w,h)
        image.px=[tuple(raw[i:i+4]) for i in range(0,len(raw),4)]
        pairs.append((name,image,finish(name,image)))
    scale=3
    height=sum(image.height*scale+35 for _,image,_ in pairs)
    review=Canvas(1500,height)
    review.fill(0,0,1499,height-1,hx(0x292627))
    top=0
    for name,before,after in pairs:
        lettering(review,name.upper(),12,top+4,CREAM)
        count=FRAME_WIDTH[name]
        for side,image in enumerate((before,after)):
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
        top+=before.height*scale+35
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
