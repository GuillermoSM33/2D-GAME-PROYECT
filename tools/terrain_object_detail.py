#!/usr/bin/env python3
"""Construction and volume for the western road's equipment, at native size.

``finish(name, image)`` accepts a freshly generated terrain sheet and returns
a new sheet. It adds joinery, curved staves, folded canvas, forged fittings,
mechanisms and broken end grain. It does not rescale images, touch flames,
fill net holes, move feet, alter frame order, or obscure loot/warning marks.
Unknown names are returned unchanged. Only the Python standard library is used.

Run this module to write a before/after contact sheet under build/; it never
writes to assets. Production generation is owned by refine_terrain.py.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_sprites import Image, rgb  # noqa: E402
from landscape_kit import Canvas  # noqa: E402
from scenery_materials import lettering  # noqa: E402


WIDTHS = {
    'barricade':68, 'barrel':26, 'crate':32, 'coffin':32,
    'supply':100, 'goal':108, 'bench':76, 'campfire':48,
    'wire':112, 'trap':48, 'spikes':40, 'net':84, 'snare':72,
    'sign':22, 'bottles':40, 'dynamite':24, 'charge':14, 'lamp':14,
}

WOOD = [rgb(v) for v in (0x332218,0x513522,0x785032,0xA87547,0xC69A62,0xDEBD87)]
GREY = [rgb(v) for v in (0x302A27,0x4B433B,0x706353,0x94846A,0xB8AA8D)]
STEEL = [rgb(v) for v in (0x202127,0x36383E,0x555A60,0x80878C,0xB4B9B5,0xD2D4C5)]
RUST = [rgb(v) for v in (0x382820,0x68402B,0x905A38,0xB57C4C)]
CLOTH = [rgb(v) for v in (0x62513D,0x8C7656,0xAD9770,0xD1BA8F,0xE4D1A8)]
STONE = [rgb(v) for v in (0x333033,0x514B49,0x766D63,0x9C9180,0xC3B7A0)]
BRASS = [rgb(v) for v in (0x5C4420,0x92703A,0xC4A261,0xE5C888)]
ROPE = [rgb(v) for v in (0x59442E,0x8B6A44,0xB89B6A,0xD7C08C)]
RED = [rgb(v) for v in (0x471D18,0x762D23,0xA94A32,0xD2744D,0xE3A077)]
CHAR = [rgb(v) for v in (0x19191B,0x302623,0x4B3527,0x804228)]
FLAME = {rgb(v) for v in (0xFFF6DC,0xFFD23C,0xF08A24,0xC84A14,0xFFF2B0)}


def luminance(p) -> float:
    return p[0]*.3+p[1]*.6+p[2]*.1


class Craft:
    """One sheet, addressed by frame, with an immutable source mask.

    Every stroke is clipped to an existing pixel. This is especially useful
    for dangling ropes, cut wire, mesh and broken states: finishing an object
    can never accidentally heal it or make its empty frame visible again.
    """
    def __init__(self, name: str, image: Image) -> None:
        self.name, self.source, self.w = name, image, WIDTHS[name]
        self.out = Image(image.width,image.height)
        self.out.px = list(image.px)
        self.h = image.height
        self.frames = image.width//self.w

    def at(self, f: int, x: int, y: int):
        if 0<=f<self.frames and 0<=x<self.w and 0<=y<self.h:
            return self.source.get(f*self.w+x,y)
        return (0,0,0,0)

    def p(self, f: int, x: int, y: int, color, guard=None) -> None:
        old=self.at(f,x,y)
        if not old[3] or old in FLAME or old[3]==254 or (guard and not guard(x,y,old)):
            return
        # Keep any pre-existing opacity, including translucent glass and smoke.
        color=rgb(color) if isinstance(color,int) else color
        self.out.set(f*self.w+x,y,(color[0],color[1],color[2],old[3]))

    def line(self,f:int,x0:int,y0:int,x1:int,y1:int,color,guard=None) -> None:
        n=max(abs(x1-x0),abs(y1-y0),1)
        for k in range(n+1):
            self.p(f,round(x0+(x1-x0)*k/n),round(y0+(y1-y0)*k/n),color,guard)

    def path(self,f:int,points:list,color,glint=None,guard=None) -> None:
        for (x0,y0),(x1,y1) in zip(points,points[1:]):
            if glint:
                self.line(f,x0-1,y0,x1-1,y1,glint,guard)
            self.line(f,x0,y0,x1,y1,color,guard)

    def rect(self,f:int,box:tuple,color,guard=None) -> None:
        x0,y0,x1,y1=box
        for y in range(y0,y1+1):
            for x in range(x0,x1+1): self.p(f,x,y,color,guard)

    def ring(self,f:int,x:int,y:int,rx:float,ry:float,color,guard=None) -> None:
        for k in range(max(16,round(math.tau*max(rx,ry)*2))):
            a=math.tau*k/max(16,round(math.tau*max(rx,ry)*2))
            self.p(f,round(x+rx*math.cos(a)),round(y+ry*math.sin(a)),color,guard)

    def rivet(self,f:int,x:int,y:int,brass=False,guard=None) -> None:
        pal=BRASS if brass else STEEL
        self.p(f,x,y,pal[0],guard); self.p(f,x-1,y-1,pal[-2],guard)
        self.p(f,x+1,y,pal[2],guard)

    def corner(self,f:int,x:int,y:int,dx:int,dy:int) -> None:
        # Folded corner bracket: one flange lies on either face of the timber.
        self.rect(f,(min(x,x+dx*4),y,max(x,x+dx*4),y+1),STEEL[2])
        self.rect(f,(x,min(y,y+dy*4),x+1,max(y,y+dy*4)),STEEL[1])
        self.line(f,x,y,x+dx*4,y,STEEL[4])
        self.rivet(f,x+dx*2,y+dy*2)

    def knot(self,f:int,x:int,y:int,rx=2,ry=3,grey=False,guard=None) -> None:
        pal=GREY if grey else WOOD
        self.ring(f,x,y,rx,ry,pal[1],guard)
        self.ring(f,x,y,rx*.55,ry*.55,pal[3],guard)
        self.p(f,x,y,pal[0],guard)

    def rope(self,f:int,points:list) -> None:
        for (x0,y0),(x1,y1) in zip(points,points[1:]):
            n=max(abs(x1-x0),abs(y1-y0),1)
            for k in range(n+1):
                x,y=round(x0+(x1-x0)*k/n),round(y0+(y1-y0)*k/n)
                self.p(f,x,y,ROPE[3 if k%3==0 else 1])
                if k%3==1: self.p(f,x-1,y,ROPE[0])


def wood_color(p) -> bool:
    return p[3] and p[0]>p[1]*1.12 and p[1]>p[2]*1.1 and 35<luminance(p)<190


def old_wood(_x,_y,p) -> bool:
    return wood_color(p)


def grain(c:Craft,f:int,box:tuple,vertical=False,grey=False,guard=old_wood) -> None:
    """Visible board fibres and raised edges, not a full-surface noise pass."""
    x0,y0,x1,y1=box
    pal=GREY if grey else WOOD
    if vertical:
        for x in range(x0+2,x1,5):
            points=[(x,y0),(x-1,y0+5),(x+1,(y0+y1)//2),(x,y1-3)]
            c.path(f,points,pal[1],pal[3],guard)
    else:
        for y in range(y0+2,y1,5):
            points=[(x0,y),(x0+7,y-1),((x0+x1)//2,y),(x1-3,y-1)]
            c.path(f,points,pal[1],pal[3],guard)


def crate(c:Craft) -> None:
    for f in range(c.frames):
        if f==10:
            # Exposed pale end grain and split ends on the wrecked planks.
            for x0,y0,x1,y1 in ((1,31,14,33),(12,32,30,34),(3,28,9,30),(19,28,27,30)):
                c.line(f,x0,y0,x1,y0,WOOD[4],old_wood)
                c.path(f,[(x0+2,y0+1),(x0+6,y0+1),(x0+8,y1)],WOOD[0],WOOD[3],old_wood)
                c.line(f,x1-1,y0,x1-1,y1,WOOD[5],old_wood)
                c.rivet(f,x0+2,y0+1)
            continue
        # Labels and the deep shot split remain exactly as the source drew
        # them. The surrounding face is assembled from raised separate boards.
        def face(x,y,p):
            return not (9<=x<=22 and 15<=y<=28) and wood_color(p)
        for y in (8,14,20,26,32):
            c.line(f,3,y,28,y,WOOD[1],face)
            c.line(f,3,y-1,28,y-1,WOOD[4],face)
        grain(c,f,(3,6,29,32),guard=face)
        c.knot(f,6,18,2,3,guard=face); c.knot(f,26,11,1,2,guard=face)
        # Front battens and dark right-hand return give the crate depth.
        c.line(f,2,5,2,33,WOOD[4],face); c.line(f,29,5,29,33,WOOD[0],face)
        for x,y,dx,dy in ((2,5,1,1),(29,5,-1,1),(2,32,1,-1),(29,32,-1,-1)):
            c.corner(f,x,y,dx,dy)
        for y in (6,32):
            c.line(f,4,y,27,y,STEEL[2]); c.line(f,4,y-1,27,y-1,STEEL[4])
            for x in (5,26): c.rivet(f,x,y)
        # Recessed pocket behind the existing rope handles.
        for x in (1,30):
            c.line(f,x,12,x,16,WOOD[0]); c.p(f,x,11,WOOD[4])
        if f%2:
            # A sheared pale edge beside the dark split exposes heartwood.
            c.path(f,[(18,7),(19,12),(18,17)],WOOD[5],guard=face)
            c.path(f,[(18,28),(17,31),(19,34)],WOOD[5],guard=face)


def barrel(c:Craft) -> None:
    f=0
    # Full-length curved staves bulge at the waist. Each stave has its own
    # face, dark joint and scraped left edge, following the barrel's section.
    for y in range(4,35):
        half=9+2.2*math.sin(math.pi*(y-3)/31)
        for x in range(2,25):
            old=c.at(f,x,y)
            if not old[3] or not (old[0]>old[1]*1.2 and old[1]>old[2]*1.1): continue
            if y in (6,7,11,17,18,30,31) or (8<=x<=19 and 19<=y<=28): continue
            u=(x-12.5)/half
            a=math.asin(max(-1,min(1,u)))
            stave=(a+math.pi/2)/(math.pi/6)
            local=stave%1
            k=3 if u<-.35 else 2 if u<.4 else 1
            if local<.15:k=max(0,k-2)
            elif local<.3:k=min(4,k+1)
            c.p(f,x,y,RED[k])
    for y in (6,17,30):
        for x in range(3,24):
            c.p(f,x,y,STEEL[4 if x<10 else 2]); c.p(f,x,y+1,STEEL[0])
        for x in (5,14,21):c.rivet(f,x,y)
        # A joined hoop has an overlapping plate and two little rivets.
        c.rect(f,(18,y,21,y+1),STEEL[1]); c.p(f,18,y,STEEL[3]); c.p(f,21,y,STEEL[3])
    c.ring(f,13,3,8,1,WOOD[1]); c.line(f,6,2,19,2,WOOD[4])
    c.line(f,9,2,9,3,WOOD[0]); c.line(f,16,2,16,3,WOOD[0])
    c.ring(f,13,1,1,1,WOOD[0]); c.p(f,12,0,WOOD[5])
    c.path(f,[(5,22),(5,25),(6,27)],RED[0],RED[3])
    c.path(f,[(20,22),(21,25),(20,28)],RED[0],RED[3])
    c.line(f,6,34,20,34,WOOD[0]); c.line(f,7,33,19,33,RED[3])


def coffin(c:Craft) -> None:
    for f in range(c.frames):
        night=f>=2
        pal=[rgb(v) for v in ((0x21191F,0x38262E,0x614250,0x82616C,0x9B7A80) if night else
                             (0x45301F,0x6D4D30,0x9A754E,0xBE9B6C,0xE0C18F))]
        def boards(x,y,p):
            if (f==0 and 10<=x<=21 and 6<=y<=35) or (night and 14<=x<=18 and 17<=y<=53):return False
            # Deep gaps and the open interior are left dark and open.
            return luminance(p)>30 and not (f%2 and 8<=x<=24 and 6<=y<=61)
        for y in range(4,65):
            half=8+min(y,16)*7//16 if y<18 else 15-(y-18)*7//50
            for x in (16-half+2,16+half-3):
                c.p(f,x,y,pal[3 if x<16 else 0],boards)
        for x,y in ((6,25),(24,44),(12,57)):
            c.ring(f,x,y,1,3,pal[0],boards); c.p(f,x-1,y-1,pal[3],boards)
        for points in ([(9,3),(10,8),(9,12)],[(25,20),(24,29),(25,34)],[(9,42),(10,48),(9,60)]):
            c.path(f,points,pal[0],pal[3],boards)
        # Bevelled lid, mortised corners and actual hinged handle loops.
        for y in (22,46):
            half=15-(max(18,y)-18)*7//50
            left,right=16-half+1,16+half-2
            for x in (left,right):
                c.rect(f,(x-1,y-1,x+1,y+3),STEEL[1] if night else BRASS[1])
                c.ring(f,x,y+1,2,1,STEEL[3] if night else BRASS[2])
                c.rivet(f,x,y-1,not night)
        if f%2:
            for x,y in ((5,15),(26,28),(6,48),(24,58)):
                c.line(f,x,y,x+1,y+4,pal[4],boards)
                c.line(f,x+1,y,x+2,y+2,pal[0],boards)
        elif night:
            for y in (11,34,57):
                c.rivet(f,5 if y<20 else 7,y); c.rivet(f,26 if y<20 else 24,y)


def wagon_wheel(c:Craft,f:int,cx:int,cy:int,r:int) -> None:
    for k in range(48):
        a=k*math.tau/48
        x,y=round(cx+(r-1)*math.cos(a)),round(cy+(r-1)*math.sin(a))
        c.p(f,x,y,STEEL[3 if k>22 else 1])
    for k in range(10):
        a=.15+k*math.tau/10
        x,y=round(cx+(r-4)*math.cos(a)),round(cy+(r-4)*math.sin(a))
        c.line(f,cx,cy,x,y,WOOD[4 if math.sin(a)<0 else 2])
        if k%2==0:c.rivet(f,round(cx+(r-1)*math.cos(a)),round(cy+(r-1)*math.sin(a)))
    c.ring(f,cx,cy,3,3,WOOD[0]); c.ring(f,cx,cy,2,2,STEEL[3])
    c.p(f,cx,cy,STEEL[4]); c.p(f,cx+1,cy,STEEL[0]); c.p(f,cx-1,cy+1,STEEL[1])


def supply(c:Craft) -> None:
    for f in range(c.frames):
        def canvas(_x,_y,p):return p[0]>120 and p[1]>100 and p[2]>65 and p[0]<p[1]*1.3
        # Folds follow the hoops and gather into the lower tension points.
        for x in (23,36,49,62,75):
            points=[(x,8),(x-2,16),(x-1,23),(x,29)]
            c.path(f,points,CLOTH[1],CLOTH[3],canvas)
            for y in range(11,29,3):c.p(f,x+1,y,CLOTH[4],canvas)
        for x in (17,42,69):
            c.path(f,[(x,21),(x-1,28),(x-1,32)],rgb(0x533625))
            c.path(f,[(x+1,21),(x+1,27)],rgb(0xA3855B),guard=canvas)
            c.rect(f,(x-2,27,x+2,30),STEEL[1]); c.line(f,x-1,27,x+1,27,STEEL[3]); c.p(f,x,29,BRASS[2])
        # The rolled canvas in the emptied state has layered cloth and ties.
        if f:
            for x in range(32,66):
                y=10+abs(x-48)//9
                c.p(f,x,y,CLOTH[4]); c.p(f,x,y+1,CLOTH[0])
            for x in (37,59):c.rope(f,[(x,10),(x+1,12),(x,14)])
        else:
            for x in (5,11):c.corner(f,x,16,1,1)
            for y in (24,28):c.line(f,2,y,11,y,STEEL[1])
            c.rivet(f,6,25,True); c.rivet(f,5,17,True)
        # Bed boards have joints; iron ties turn under the bed into its axle.
        grain(c,f,(6,33,89,41))
        for x in (12,30,48,66,84):
            c.line(f,x,33,x,41,STEEL[0]); c.line(f,x-1,33,x-1,40,STEEL[3])
            c.rivet(f,x,34); c.rivet(f,x,39)
        c.line(f,7,42,89,42,WOOD[0]); c.line(f,9,41,89,41,WOOD[4])
        wagon_wheel(c,f,22,44,11); wagon_wheel(c,f,76,46,9)
        c.rect(f,(94,37,98,38),STEEL[2]); c.rivet(f,97,37)


def goal(c:Craft) -> None:
    for x in (18,88):
        for points in ([[(x-2,24),(x-3,33),(x-1,42)],[(x+2,53),(x,63),(x+1,71)],
                        [(x-1,75),(x-2,84),(x,93)]]):
            c.path(0,points,WOOD[0],WOOD[4])
        c.knot(0,x,61,2,4)
        c.ring(0,x,12,3,1,WOOD[1]); c.p(0,x-1,11,WOOD[5])
        # Iron straps have a proper folded return and a square washer.
        for y in (18,78):
            c.line(0,x-4,y,x+5,y,STEEL[0]); c.line(0,x-4,y-1,x+4,y-1,STEEL[3])
            c.rivet(0,x,y)
    grain(c,0,(6,13,101,21))
    for x in (6,102):
        c.ring(0,x,16,1,3,WOOD[0]); c.p(0,x-1,15,WOOD[5])
    # A carved rope border frames the existing sheriff star; the star itself
    # stays unobscured and gets a small shadow under its raised brass center.
    for x in range(34,74):
        c.p(0,x,28,WOOD[4 if x%3 else 1]); c.p(0,x,38,WOOD[0 if x%3 else 3])
    for x in (33,74):c.line(0,x,30,x,37,WOOD[1])
    c.line(0,47,37,60,37,BRASS[0]); c.p(0,51,32,BRASS[3]); c.p(0,54,34,BRASS[1])
    for y in (44,46,48,50):
        c.ring(0,18,y,5,1,ROPE[0]); c.line(0,14,y,21,y,ROPE[2])
    c.rope(0,[(22,45),(24,49),(21,53),(18,55)])
    # Pegged braces, skull sutures and small forged lantern mounting plates.
    for x,y in ((26,23),(33,30),(81,23),(74,30)):c.rivet(0,x,y)
    c.path(0,[(53,4),(54,6),(53,9)],rgb(0x8C7B61))
    for x in (28,79):
        c.ring(0,x,22,1,1,STEEL[3]); c.p(0,x-2,23,STEEL[4]); c.p(0,x+1,31,STEEL[0])


def bench(c:Craft) -> None:
    for f in range(c.frames):
        for y in ((3,10,17,24,34) if not f else (34,36)):
            # Slat face, undercut, relieved front edge and curved wood fibre.
            c.line(f,3,y,72,y,WOOD[4],old_wood)
            c.path(f,[(13,y+2),(24,y+1),(41,y+2),(62,y+1)],WOOD[1],WOOD[3],old_wood)
        if not f:
            for x in (8,67):
                for y in (5,12,19,26):
                    c.rect(f,(x-1,y-1,x+1,y+1),STEEL[1]); c.rivet(f,x,y)
            c.knot(f,35,12,3,1); c.knot(f,54,25,2,1)
            for x in (5,69):
                c.line(f,x,39,x,42,WOOD[0]); c.line(f,x-1,39,x-1,41,WOOD[4])
                c.rivet(f,x,42)
        else:
            # The crossing lattice has collars and cast floral rosettes.
            for x in range(10,68,12):
                c.ring(f,x,14,2,2,STEEL[1]); c.p(f,x-1,13,STEEL[4]); c.p(f,x,15,STEEL[2])
            for x in (4,72):
                c.ring(f,x,26,3,3,STEEL[1]); c.ring(f,x,26,2,2,STEEL[3])
                for y in (8,39):c.rivet(f,x,y)
        c.line(f,4,37,71,37,WOOD[0]); c.line(f,5,35,70,35,WOOD[4],old_wood)


def campfire(c:Craft) -> None:
    for f in range(c.frames):
        if f<8:
            # Individual stones have broad top facets and fractured side
            # faces. A continuous stripe would make the ring look moulded.
            for k,x in enumerate(range(0,48,7)):
                y=51+k%2
                c.line(f,x+1,y,x+4,y,STONE[4])
                c.path(f,[(x+4,y+1),(x+3,y+2),(x+5,y+3)],STONE[0],STONE[2])
                c.line(f,x+1,y+2,x+2,y+2,STONE[2])
                c.p(f,x+5,55,STONE[0])
            for a,b in (((7,48),(36,42)),((41,48),(12,42))):
                n=abs(b[0]-a[0])
                for k in range(n+1):
                    x,y=round(a[0]+(b[0]-a[0])*k/n),round(a[1]+(b[1]-a[1])*k/n)
                    c.p(f,x,y,CHAR[3] if k%7<2 else WOOD[2])
                    c.p(f,x,y+1,CHAR[0] if k%6<3 else CHAR[2])
                    if k%7==2:c.p(f,x,y+2,rgb(0xA34C2C))
                c.ring(f,b[0],b[1]+1,1,1,WOOD[5])
                c.p(f,b[0],b[1]+1,CHAR[0])
            # Dark charcoal cracks on the firebed retain every flame pixel.
            for x in (12,18,25,31,36):
                c.line(f,x,49,x+1,50,CHAR[0]); c.p(f,x-1,49,rgb(0xB56636))
            if f>=4:
                # Pot at rows24-36: rolled rim, folded seam, handle rivets,
                # polished lip, dark soot plate and hammered metal facets.
                c.line(f,19,24,28,24,STEEL[3]); c.line(f,20,25,28,25,STEEL[0])
                c.path(f,[(20,27),(19,30),(20,33)],STEEL[2],STEEL[3])
                c.line(f,28,27,28,34,STEEL[0]); c.rivet(f,19,26); c.rivet(f,28,26)
                for x,y in ((23,28),(25,30),(22,32)):c.p(f,x,y,STEEL[1])
                c.line(f,20,35,27,35,CHAR[0]); c.p(f,21,34,CHAR[2])
                for x in (3,43):
                    c.line(f,x,30,x,49,WOOD[0]); c.line(f,x-1,31,x-1,49,WOOD[4])
        else:
            # City campfire: embossed drum hoops, vent slots and folded rim.
            for y in (30,43,52):
                c.line(f,14,y,34,y,STEEL[0]); c.line(f,15,y-1,33,y-1,STEEL[3])
                for x in (16,31):c.rivet(f,x,y)
            for x in range(16,33,4):
                c.line(f,x,46,x,49,STEEL[0]); c.p(f,x-1,46,RUST[2])
            c.path(f,[(29,34),(27,38),(29,41)],STEEL[0],RUST[3])


def bag(c:Craft,f:int,x:int,y:int,w:int,h=7) -> None:
    # Crossed pressure folds, a sewn rolled seam and a puckered tied neck.
    c.path(f,[(x+2,y+2),(x+w//2-2,y+3),(x+w//2,y+2)],CLOTH[1],CLOTH[3])
    c.path(f,[(x+w-3,y+1),(x+w-5,y+4),(x+w-3,y+h-2)],CLOTH[0],CLOTH[2])
    c.line(f,x+2,y+h-2,x+w-3,y+h-2,CLOTH[0])
    for xx in range(x+2,x+w-2,3):c.p(f,xx,y+h-3,CLOTH[3])
    c.p(f,x+w-3,y+2,ROPE[3]); c.p(f,x+w-2,y+2,ROPE[0])


def barricade(c:Craft) -> None:
    for f in range(c.frames):
        kind,state=divmod(f,3)
        if kind==0:
            if state<2:
                def woodface(x,y,p):return wood_color(p) and not(14<=x<=25 and 5<=y<=24)
                grain(c,f,(5,5,34,34),vertical=True,guard=woodface)
                c.knot(f,7,19,1,3,guard=woodface);c.knot(f,31,25,1,2,guard=woodface)
                for x,y,dx,dy in ((5,5,1,1),(32,5,-1,1),(5,32,1,-1),(32,32,-1,-1),
                                  (35,20,1,1),(52,20,-1,1)):
                    c.corner(f,x,y,dx,dy)
                for x in (11,27):
                    c.line(f,x,6,x,33,STEEL[2]); c.line(f,x+1,6,x+1,33,STEEL[0])
                    for y in (8,16,30):c.rivet(f,x,y)
                if state:
                    c.path(f,[(34,20),(39,25),(43,25)],WOOD[5],guard=old_wood)
            else:
                for x0,y0,x1 in ((2,30,20),(16,26,38),(34,31,56),(44,26,52)):
                    c.line(f,x0,y0,x1,y0,WOOD[5],old_wood)
                    c.path(f,[(x0+3,y0+1),(x0+7,y0+2),(x1-1,y0+1)],WOOD[0],guard=old_wood)
        elif kind==1:
            layouts=((30,((0,11),(11,14),(25,12),(37,15),(52,15))),
                     (24,((4,13),(17,12),(29,15),(44,14),(58,8))),
                     (18,((7,15),(22,13),(35,12),(47,14))),
                     (12,((11,12),(23,14),(37,15),(52,7))),
                     (6,((13,13),(39,14))))
            if state<2:
                for y,bags in layouts:
                    for x,w in bags:bag(c,f,x,y,w)
            else:
                for x in (2,16,40,54):bag(c,f,x,28,13,7)
        elif kind==2:
            if state<2:
                # Timber end grain and bark plates on the horizontal beams;
                # spiked poles receive a sharp planed edge and rope lashings.
                for y in (13,26):
                    for x in (12,29,44):
                        c.path(f,[(x,y),(x+5,y+1),(x+9,y)],WOOD[0],WOOD[4],old_wood)
                c.ring(f,64,16,2,3,WOOD[5]); c.ring(f,64,16,1,2,WOOD[1])
                for x in (9,16,51,58):
                    for y in (14,16,18):c.rope(f,[(x-1,y),(x+2,y)])
                    c.ring(f,x+1,20,1,1,ROPE[0])
                # Colour the existing twisted strands and barbs, preserving
                # the damaged state's missing central wire.
                for x in range(3,65):
                    y=5+round(2*math.sin(x*.55))
                    c.p(f,x,y,STEEL[4 if x%4==0 else 1])
            else:
                for x0,y0,x1 in ((0,30,30),(34,31,66)):
                    c.path(f,[(x0+3,y0+1),(x0+10,y0+2),(x1-4,y0+1)],WOOD[0],WOOD[4],old_wood)
        elif kind==3:
            for x in (2,64):
                for y in (15,28):c.rivet(f,x,y)
            if state<2:
                # Keep the central safety stripes; side mounting flanges and
                # tube welds establish how the steel barrier is constructed.
                for x in (5,61):
                    for y in (3,15,28):
                        c.rect(f,(x,y,x+2,y+2),STEEL[1]);c.p(f,x,y,STEEL[4])
                for x in (10,58):c.rivet(f,x,34)
        else:
            # The remaining urban barricade geometries keep their detailed
            # vehicle drawings. Only their real mounting plates are finished.
            if kind in (4,5) and state<2:
                for x in (10,56):
                    c.rivet(f,x,28); c.rivet(f,x,31)
            if kind==5 and state<2:
                for y,n,start in ((11,6,6),(6,5,10)):
                    for k in range(n):bag(c,f,start+k*9,y,9,6)


def wire(c:Craft) -> None:
    for f in range(c.frames):
        for x in (4,106):
            c.line(f,x,4,x,28,GREY[0]);c.line(f,x-1,4,x-1,27,GREY[3])
            c.knot(f,x,15,1,3,True)
            for y in (6,24):
                c.rect(f,(x-1,y-1,x+2,y+1),STEEL[1]);c.rivet(f,x,y)
        # A wire's twist is a rhythm along the existing strand. No pixel is
        # added in the cut aperture or between the loops.
        for y in range(3,30):
            for x in range(7,105):
                p=c.at(f,x,y)
                if p[3] and max(p[:3])-min(p[:3])<24 and luminance(p)>55:
                    c.p(f,x,y,STEEL[3 if (x+y)%5<2 else 1 if (x+y)%5==4 else 2])
        for x,y in ((10,25),(98,25)):
            c.ring(f,x,y,2,1,STEEL[3]);c.p(f,x+1,y,STEEL[0])


def trap(c:Craft) -> None:
    for f in range(c.frames):
        # A pressure pan, latch lever, pivot washers and laminated springs
        # distinguish a mechanism from a line of teeth painted on the road.
        c.rect(f,(20,12,26,14),RUST[2]);c.line(f,21,12,25,12,STEEL[3])
        c.line(f,21,14,26,14,STEEL[0]);c.p(f,23,13,RUST[0])
        c.line(f,10,16,34,16,STEEL[0]);c.line(f,10,15,33,15,STEEL[2])
        for x in (5,41):
            c.ring(f,x,14,2,1,STEEL[1]);c.p(f,x-1,13,STEEL[4]);c.p(f,x,14,STEEL[0])
            c.line(f,x-2,16,x+2,16,RUST[2])
        for x in (43,45):c.ring(f,x,15,1,1,STEEL[2])
        c.line(f,46,10,46,16,WOOD[0]);c.p(f,45,9,WOOD[4])
        if f==0:
            for x in (5,11,17,31,37,43):
                c.line(f,x,11,x,13,STEEL[3]);c.p(f,x+1,13,RUST[0])
        elif f==1:
            for points in ([(7,13),(12,8),(17,3)],[(39,13),(34,8),(29,3)]):
                c.path(f,points,STEEL[3],STEEL[1])
        else:
            for y in (3,7,11):
                # Do not repaint the blood down the closed jaws.
                c.p(f,22,y,STEEL[3]);c.p(f,23,y,STEEL[1])


def spikes(c:Craft) -> None:
    for f in range(c.frames):
        for x in (3,36):c.rivet(f,x,19)
        for x in range(6,35,5):
            c.line(f,x-1,18,x+2,18,STEEL[0]);c.p(f,x-1,17,STEEL[2]);c.p(f,x+2,19,RUST[2])
        c.line(f,4,20,35,20,STEEL[1])
        if f:
            # Forged blades have two facets and a center ridge. Existing red
            # blood streaks and needle points are preserved verbatim.
            for x in range(5,37):
                for y in range(3,18):
                    p=c.at(f,x,y)
                    if p[3] and p[2]>p[0]*.9 and luminance(p)>55:
                        c.p(f,x,y,STEEL[4 if c.at(f,x-1,y)[3]==0 else 2])


def net(c:Craft) -> None:
    for f in range(c.frames):
        # Long bark plates follow the narrow trunk and curve into the bough.
        for points in ([(7,122),(6,110),(8,98),(7,84)],[(10,118),(11,105),(9,91),(10,72)],
                       [(8,69),(7,57),(9,46),(10,36)],[(12,35),(20,29),(27,22),(35,17)]):
            c.path(f,points,GREY[0],GREY[3])
        c.knot(f,9,82,2,5,True)
        c.knot(f,9,50,1,3,True)
        for x,y in ((4,121),(11,119),(14,124)):
            c.line(f,x,y,x+3,127,GREY[0]);c.p(f,x-1,y,GREY[3])
        # Rope is twisted on its existing pixels only: holes in the springing
        # mesh remain alpha0 and the cut rope remains cut in the final state.
        for y in range(c.h):
            for x in range(12,c.w):
                p=c.at(f,x,y)
                if p[3] and p[0]>p[1]*1.12 and p[1]>p[2]*1.25 and luminance(p)>65:
                    c.p(f,x,y,ROPE[2 if (x+y)%4<2 else 0])


def snare(c:Craft) -> None:
    for f in range(c.frames):
        # Paired leaves and twig shadows give the cover bush depth, preserving
        # its original mask and the identical decoy/trap silhouettes.
        for y in range(92,c.h):
            for x in range(5,67):
                p=c.at(f,x,y)
                if not p[3] or not(p[1]>p[0]*1.12 and p[1]>p[2]*1.25):continue
                if x%7 in (1,2) and y%5==1:
                    c.p(f,x,y,rgb(0x74804B));c.p(f,x+1,y,rgb(0x58643A))
                elif x%7==3 and y%5==2:c.p(f,x,y,rgb(0x293421))
        if f:
            # The slender sprung sapling carries a lit bark edge and dark
            # raised nodes; its tip and the game's rope anchor do not move.
            for y in range(12,119):
                for x in range(24,58):
                    p=c.at(f,x,y)
                    if wood_color(p):
                        c.p(f,x,y,WOOD[4 if x%2==0 else 1])
            for x,y in ((48,70),(43,41),(52,94)):c.knot(f,x,y,1,2)


def sign(c:Craft) -> None:
    def timber(x,y,p):return wood_color(p) and not(4<=x<=19 and 4<=y<=14)
    grain(c,0,(2,2,19,15),guard=timber)
    for x,y in ((3,3),(18,3),(3,14),(18,14)):c.rivet(0,x,y)
    c.line(0,20,3,20,15,WOOD[0]);c.line(0,2,1,19,1,WOOD[5])
    c.path(0,[(11,18),(10,22),(11,26)],GREY[0],GREY[3])
    c.p(0,10,28,GREY[4]);c.p(0,12,28,GREY[0])


def bottles(c:Craft) -> None:
    for f in range(c.frames):
        c.path(f,[(3,23),(10,22),(17,23),(24,22),(35,23)],WOOD[0],WOOD[4],old_wood)
        c.line(f,3,25,36,25,WOOD[0]);c.line(f,4,24,35,24,WOOD[4],old_wood)
        for x in (5,34):
            c.line(f,x,28,x,38,WOOD[1]);c.p(f,x-1,29,WOOD[4]);c.rivet(f,x,27)
        c.knot(f,16,23,2,1)
        for b,x in enumerate((7,17,27)):
            if b<f:
                # A crescent of glass and the shaded meniscus of the spill.
                c.p(f,x,21,rgb(0x8CBE99));c.p(f,x+2,20,rgb(0x5C9473));c.p(f,x+3,22,rgb(0x3A3020))
                continue
            top=(5,10,8)[b]
            # Heavy glass has a long shoulder reflection and dark base, with
            # a separate rolled lip at the mouth. Labels remain untouched.
            c.p(f,x+1,top,rgb(0xBDD5B2));c.p(f,x+2,top,rgb(0x406A4C))
            c.line(f,x,19,x+3,19,rgb(0x294D36) if b==1 else rgb(0x76512C))
            c.p(f,x+1,20,rgb(0x8AA976) if b==1 else rgb(0xBC8549))
            if b==2:c.p(f,x+1,6,WOOD[4]);c.p(f,x+2,6,WOOD[0])
        c.p(f,36,19,rgb(0xD6E1C1));c.p(f,37,20,rgb(0x66816B))


def dynamite(c:Craft) -> None:
    grain(c,0,(2,9,21,16))
    for x in (2,21):
        c.line(0,x,10,x,16,STEEL[1]);c.p(0,x-1,10,STEEL[4]);c.rivet(0,x,15)
    for x,top in ((3,2),(7,3),(11,2),(15,3)):
        c.line(0,x,top+1,x,top+4,RED[4]);c.line(0,x+2,top+1,x+2,8,RED[0])
        c.p(0,x+1,top,RED[1]);c.p(0,x,top,RED[3])
    c.line(0,2,8,21,8,WOOD[5]);c.line(0,3,17,20,17,WOOD[0])


def charge(c:Craft) -> None:
    for f in range(c.frames):
        for k,x in enumerate((1,4,7,10)):
            top=8+k%2
            c.line(f,x,top+1,x,19,RED[4]);c.line(f,x+2,top+1,x+2,19,RED[0])
            c.p(f,x+1,top,RED[1]);c.p(f,x,top,RED[3])
            # Preserve the broad paper warning band across the bundle.
            c.p(f,x,16,CLOTH[4]);c.p(f,x+2,16,CLOTH[1])
        c.line(f,1,12,12,12,ROPE[0])
        for x in range(2,12,3):c.p(f,x,12,ROPE[3])
        c.ring(f,7,12,1,1,ROPE[2]);c.p(f,7,13,ROPE[0])


def lamp(c:Craft) -> None:
    for f in range(c.frames):
        c.path(f,[(4,25),(3,32),(4,40)],GREY[0],GREY[3])
        c.path(f,[(4,46),(5,53),(4,62)],GREY[0],GREY[3])
        c.knot(f,4,56,1,3,True)
        for y in (9,15,70):c.rivet(f,4,y)
        c.line(f,3,73,6,73,STEEL[2]);c.p(f,2,75,STEEL[4])
        if not f:
            # Rolled cap, vent and oil-font seam; the illuminated glass and
            # flame retain every source color with no new glow or light ray.
            c.line(f,9,10,11,10,STEEL[3]);c.p(f,10,9,STEEL[0])
            c.line(f,8,12,8,18,STEEL[3]);c.line(f,12,12,12,18,STEEL[0])
            c.line(f,9,20,11,20,STEEL[0]);c.p(f,9,19,STEEL[4])


DRAW = {
    'crate':crate,'barrel':barrel,'coffin':coffin,'supply':supply,'goal':goal,
    'bench':bench,'campfire':campfire,'barricade':barricade,'wire':wire,
    'trap':trap,'spikes':spikes,'net':net,'snare':snare,'sign':sign,
    'bottles':bottles,'dynamite':dynamite,'charge':charge,'lamp':lamp,
}


def finish(name: str,image: Image) -> Image:
    """Return the object's crafted sheet; leave other terrain sheets alone."""
    name=Path(name).stem
    if name not in DRAW:return image
    c=Craft(name,image)
    DRAW[name](c)
    return c.out


def read_png(path:Path) -> Image:
    from embed_assets import decode_png_rgba
    w,h,data=decode_png_rgba(path)
    image=Image(w,h)
    image.px=[tuple(data[i:i+4]) for i in range(0,len(data),4)]
    return image


def preview(path:Path,assets:Path) -> None:
    samples=[('goal',0),('supply',0),('barrel',0),('crate',0),('crate',7),('coffin',0),
             ('barricade',0),('barricade',3),('barricade',6),('bench',0),('campfire',4),
             ('wire',0),('trap',0),('spikes',2),('net',1),('snare',2),('sign',0),
             ('bottles',0),('dynamite',0),('charge',0),('lamp',0),('coffin',3)]
    colw,scale=740,3
    heights=[]
    sources={name:read_png(assets/'sprites'/'terrain'/(name+'.png')) for name,_ in samples}
    finished={name:finish(name,image) for name,image in sources.items()}
    for row in range((len(samples)+1)//2):
        heights.append(max(sources[n].height for n,_ in samples[row*2:row*2+2])*scale+24)
    image=Image(colw*2,sum(heights))
    image.px=[rgb(0x282526)]*(image.width*image.height)
    top=0
    for row,row_h in enumerate(heights):
        for column,(name,f) in enumerate(samples[row*2:row*2+2]):
            ox=column*colw
            title=Canvas(colw,12)
            lettering(title,f'{name.upper()} {f}  BEFORE / AFTER',4,2,(214,195,158))
            for y in range(title.h):
                for x in range(title.w):
                    p=title.get(x,y)
                    if p:image.set(ox+x,top+y,(*p,255))
            for side,source in enumerate((sources[name],finished[name])):
                fw=WIDTHS[name]
                for y in range(source.height):
                    for x in range(fw):
                        p=source.get(f*fw+x,y)
                        if not p[3]:continue
                        for dy in range(scale):
                            for dx in range(scale):
                                image.set(ox+side*(colw//2)+8+x*scale+dx,top+18+y*scale+dy,p)
        top+=row_h
    path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,default=Path(__file__).resolve().parent.parent/'assets')
    parser.add_argument('--preview',type=Path,default=Path(__file__).resolve().parent.parent/'build'/'terrain-object-craft-v3.png')
    args=parser.parse_args()
    preview(args.preview,args.assets)
    print(f'terrain objects: wrote review sheet {args.preview}; assets unchanged')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
