#!/usr/bin/env python3
"""Make the sprites of the things a stage's route is built from.

Usage: tools/make_terrain.py [assets_dir]   (default: assets)

Writes, under sprites/:
  terrain/barricade.png  Crates and sandbags across the road: whole, cracked,
                         wrecked (3 frames of 52 x 20). Zombies have to claw
                         through; she can jump on top (it stays under her
                         jump's peak).
  terrain/barrel.png     A powder barrel that blows up when shot (20 x 28)
  terrain/wall.png       A palisade of sharpened stakes her height: whole,
                         cracked, wrecked (3 frames of 44 x 60). Only a blast
                         (dynamite, a barrel) brings it down quickly.
  terrain/dynamite.png   A box of dynamite to pick up (20 x 14)
  terrain/charge.png     A lit bundle of dynamite on a wall, the fuse
                         flickering (2 frames of 12 x 16)
  terrain/crate.png      A loose crate: whole, split, broken open (3 of 18 x 16)
  terrain/bottles.png    Three bottles on a fence rail: 3, 2, 1, 0 left (4 of 36 x 22)
  terrain/trap.png       A bear trap: open, snapping, shut (3 of 32 x 12)
  terrain/coffin.png     An upright coffin: shut, burst open (2 of 20 x 44)
  terrain/lamp.png       An oil lamp on a post: lit, gone (2 of 14 x 56)
  terrain/fire.png       Burning oil on the ground (4 of 32 x 24)
  terrain/supply.png     The covered supply wagon: loaded, then emptied
                         (2 frames of 100 x 56). Walking up to it refills
                         guns and health.
  terrain/goal.png       The stage's way out: a ranch gate of logs with a
                         skull, a hanging board and lanterns (108 x 96)
  terrain/bench.png      A bench to rest on, its seat at sitting hip height (44 x 14)
  terrain/campfire.png   A campfire to rest by (4 frames of 28 x 22)
  effects/heal.png       A green aura with a + rising off a healed head (8 of 24 x 32)
  effects/glow.png       The light around a flame, drawn additively (32 x 32)
  effects/explosion.png  A barrel blowing up: flash, fireball, smoke
                         (8 frames of 48 x 48)

Sized against the characters (about 57 px tall): the barrel reaches her
waist, the wagon stands taller than her, the gate almost twice her height.
Unlike the scenery (sprites/props, muted silhouettes in the background),
these can be used, so they get an outline and livelier colors, like the
chest. Light comes from the top left. Each rests on its last row, on the
ground line. Deterministic; uses only the standard library.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_sprites import Image, rgb  # noqa: E402

OUTLINE = rgb(0x231a14)
WOOD = [rgb(0x3a2316), rgb(0x56351f), rgb(0x76492a), rgb(0x9a643a), rgb(0xbf8650)]
GREY_WOOD = [rgb(0x3a3230), rgb(0x544a44), rgb(0x72665c), rgb(0x948676)]
IRON = [rgb(0x24242a), rgb(0x3c3c44), rgb(0x5c5c66), rgb(0x8a8a94), rgb(0xb8b8c0)]
RED = [rgb(0x4a1612), rgb(0x74231a), rgb(0x9c3424), rgb(0xc24e32), rgb(0xe07a50)]
OLIVE = [rgb(0x2e2a1c), rgb(0x46412a), rgb(0x5f5938), rgb(0x7c7449)]
SAND = [rgb(0x6a5638), rgb(0x8c7450), rgb(0xae9468), rgb(0xcab284)]
CANVAS = [rgb(0x6e6048), rgb(0x968466), rgb(0xbaa784), rgb(0xd9c8a2), rgb(0xeee0bc)]
BRASS = [rgb(0x6a4e1e), rgb(0x9c7a32), rgb(0xd0a848), rgb(0xf0d27a)]
BONE = [rgb(0x8a7e68), rgb(0xb8ac90), rgb(0xe0d6bc), rgb(0xf6efdc)]
ROPE = [rgb(0x7a6040), rgb(0xa88a5c)]
LAMP = [rgb(0xf08a24), rgb(0xffd23c), rgb(0xfff2b0)]
FLAME = {'W': rgb(0xfff6dc), 'Y': rgb(0xffd23c), 'o': rgb(0xf08a24), 'r': rgb(0xc84a14)}
SMOKE = [rgb(0x4a4444), rgb(0x6a6262), rgb(0x8a8282)]


class Frame:
    """Draws into one frame of a sheet (offset ox), clipped to its width; oy
    moves the drawing down (so y may go negative above it)."""

    def __init__(self, img: Image, ox: int, w: int, oy: int = 0) -> None:
        self.img, self.ox, self.w, self.oy = img, ox, w, oy

    def px(self, x: int, y: int, c) -> None:
        if 0 <= x < self.w:
            self.img.set(self.ox + x, y + self.oy, c)

    def get(self, x: int, y: int):
        inside = 0 <= x < self.w and 0 <= y + self.oy < self.img.height
        return self.img.get(self.ox + x, y + self.oy) if inside else (0, 0, 0, 0)

    def fill(self, x0: int, y0: int, x1: int, y1: int, c) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def box(self, x0: int, y0: int, x1: int, y1: int, ramp: list) -> None:
        """Block lit from the top left: light top/left edge, dark bottom/right."""
        n = len(ramp)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                c = ramp[n // 2]
                if y == y0 or x == x0:
                    c = ramp[n - 1] if n > 3 else ramp[-1]
                if y == y1 or x == x1:
                    c = ramp[0]
                self.px(x, y, c)

    def outline(self) -> None:
        rows = range(-self.oy, self.img.height - self.oy)
        solid = {(x, y) for y in rows for x in range(self.w) if self.get(x, y)[3]}
        for x, y in solid:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.w and ny in rows and (nx, ny) not in solid:
                    self.px(nx, ny, OUTLINE)


def grain(f: Frame, x0: int, y0: int, x1: int, y1: int, ramp: list, seed: int) -> None:
    """Short dark grain strokes along a horizontal board, and a knot."""
    state = seed
    for y in range(y0 + 1, y1):
        for x in range(x0 + 1, x1):
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            if (state >> 16) % 11 == 0:
                f.px(x, y, ramp[1])
                f.px(x + 1, y, ramp[1])
    kx = x0 + (seed % max(1, x1 - x0 - 3)) + 1
    ky = (y0 + y1) // 2
    if x0 < kx < x1 - 1 and y0 < ky < y1:
        f.px(kx, ky, ramp[0])
        f.px(kx + 1, ky, ramp[1])


def crate(f: Frame, x0: int, y0: int, w: int, h: int, seed: int, cracked: bool = False) -> None:
    """A crate of horizontal boards inside a frame of battens, a cross brace,
    iron corner brackets with a nail each."""
    x1, y1 = x0 + w - 1, y0 + h - 1
    f.box(x0, y0, x1, y1, WOOD)
    for y in range(y0 + 2, y1 - 1):                       # Board seams
        if (y - y0) % 3 == 0:
            for x in range(x0 + 2, x1 - 1):
                f.px(x, y, WOOD[1])
    grain(f, x0 + 2, y0 + 1, x1 - 2, y1 - 1, WOOD, seed)
    for y in range(y0 + 1, y1):                           # Side battens
        f.px(x0 + 1, y, WOOD[3])
        f.px(x1 - 1, y, WOOD[1])
    for x in range(x0 + 1, x1):                           # Top and bottom battens
        f.px(x, y0 + 1, WOOD[4])
        f.px(x, y1 - 1, WOOD[1])
    for i in range(w - 4):                                # Diagonal brace
        y = y0 + 2 + round(i * (h - 5) / max(1, w - 5))
        f.px(x0 + 2 + i, y, WOOD[3])
        f.px(x0 + 2 + i, y + 1, WOOD[1])
    for cx, cy in ((x0, y0), (x1 - 1, y0), (x0, y1 - 1), (x1 - 1, y1 - 1)):  # Brackets
        f.fill(cx, cy, cx + 1, cy + 1, IRON[2])
        f.px(cx, cy, IRON[3])
    for nx, ny in ((x0 + 3, y0 + 1), (x1 - 3, y0 + 1), (x0 + 3, y1 - 1), (x1 - 3, y1 - 1)):
        f.px(nx, ny, IRON[4])
    if cracked:                                           # A split through the boards
        x, y = x0 + w // 2, y0 + 1
        for step in range(h - 2):
            f.px(x, y + step, OUTLINE)
            if step % 2:
                x += 1 if step % 4 == 1 else -1


def sandbag(f: Frame, x0: int, y0: int, w: int, h: int) -> None:
    """A rounded sack with a tied seam."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            dx = (x - (x0 + (w - 1) / 2)) / (w / 2)
            dy = (y - (y0 + (h - 1) / 2)) / (h / 2)
            if dx * dx + dy * dy > 1.05:
                continue
            lit = -dx * 0.6 - dy * 0.8
            c = SAND[3] if lit > 0.5 else SAND[2] if lit > 0.0 else SAND[1] if lit > -0.6 else SAND[0]
            f.px(x, y, c)
    f.px(x0 + w // 2, y0 + 1, SAND[0])
    f.px(x0 + w // 2, y0 + 2, SAND[0])


def make_barricade() -> Image:
    """The barricades, long and over her head: too high to jump (their top is
    BARRICADE_TOP), she gets over with a vault (N) or breaks them. Four kinds
    (Piece.variant), three frames each (whole, cracked, wrecked): crates and
    sandbags, a sandbag wall, logs lashed between sharpened stakes, a steel
    crowd barrier. Each is drawn on its 26-row base, RAISE rows lower, and
    built up above it (negative y)."""
    w, h = 68, 26 + RAISE
    img = Image(w * 12, h)
    for kind in range(4):
        for state in range(3):
            f = Frame(img, (kind * 3 + state) * w, w, RAISE)
            (barricade_crates, barricade_sandbags, barricade_logs, barricade_fence)[kind](f, state)
            f.outline()
    return img


RAISE = 18  # Rows the barricades grew by (BARRICADE_FRAME_H 44)


def barricade_crates(f: Frame, state: int) -> None:
    """Crates on sandbags, two more piled on top, a post, a plank nailed across."""
    if state < 2:
        cracked = state == 1
        crate(f, 6, -9, 24, 11, seed=17)                 # The pile on top
        crate(f, 30, -10, 26, 12, seed=23, cracked=cracked)
        crate(f, 16, -17, 26, 9, seed=29)
        sandbag(f, 44, -16, 12, 7)
        sandbag(f, 0, 18, 11, 8)                          # Sandbags at the feet
        sandbag(f, 56, 18, 12, 8)
        sandbag(f, 3, 12, 10, 7)
        sandbag(f, 52, 12, 10, 7)
        crate(f, 8, 10, 25, 16, seed=3, cracked=cracked)
        crate(f, 33, 10, 25, 16, seed=11)
        crate(f, 18, 1, 28, 10, seed=7, cracked=cracked)  # Top crate: the step she stands on
        f.box(46, -14, 49, 10, WOOD)                     # A post sticking up
        if state == 0:                                   # A plank nailed across
            f.box(5, 16, 62, 18, WOOD[1:])
            grain(f, 5, 16, 62, 18, WOOD, 5)
            for x in (9, 31, 58):
                f.px(x, 17, IRON[4])
        else:                                            # Torn loose, hanging
            for i in range(24):
                y = 16 + i // 4
                f.px(36 + i, y, WOOD[3])
                f.px(36 + i, y + 1, WOOD[1])
            for i in range(8):                           # Splinters
                f.px(12 + i * 4, 9 - (i % 2), WOOD[4])
    else:                                                # Wrecked: boards and burst sacks
        for x0, y0, x1, y1 in ((2, 20, 20, 23), (16, 16, 38, 19), (34, 21, 56, 23),
                               (44, 16, 52, 19), (8, 15, 13, 18)):
            f.box(x0, y0, x1, y1, WOOD[1:])
        sandbag(f, 55, 18, 12, 8)
        for x in range(20, 34):                          # Spilled sand
            f.px(x, 25, SAND[1])
            if x % 3:
                f.px(x, 24, SAND[2])


def barricade_sandbags(f: Frame, state: int) -> None:
    """A wall of sandbags laid like bricks, four courses, the top one shorter."""
    if state == 2:                                       # Wrecked: a few sacks, sand everywhere
        for x0 in (2, 16, 40, 54):
            sandbag(f, x0, 18, 13, 8)
        sandbag(f, 27, 20, 12, 6)
        for x in range(0, 68, 2):
            f.px(x, 25, SAND[1 + x % 2])
        return
    courses = ((19, 0, 5), (13, 4, 5), (7, 1, 5), (1, 4, 5), (-5, 8, 4), (-11, 8, 4),
               (-17, 15, 3))                                # (y, x start, sacks)
    for row, (y0, x0, n) in enumerate(courses):
        for i in range(n):
            if state == 1 and row == 6 and i == 1:
                continue                                 # A sack shot out of the top
            sandbag(f, x0 + i * 14 - (row % 2), y0, 14, 7)
    if state == 1:                                       # Holes leaking sand
        for x, y in ((20, 15), (44, 21), (33, 9), (25, -3), (47, -9)):
            f.px(x, y, OUTLINE)
            f.px(x, y + 1, SAND[3])
            f.px(x, y + 2, SAND[2])


def barricade_logs(f: Frame, state: int) -> None:
    """Three logs stacked between stakes, sawn ends ringed, points up."""
    if state == 2:                                       # Wrecked: logs rolled apart, a stump
        for x0, y0, x1 in ((0, 20, 30), (34, 21, 66)):
            log(f, x0, y0, x1, 5)
        f.box(22, 14, 25, 19, WOOD)
        return
    for i, y in enumerate((18, 12, 6, 0, -6, -12)):      # Logs, narrowing up
        log(f, 2 + i * 2, y, 64 - i * 2, 6)
    for x in (6, 24, 44, 60):                            # Stakes, sharpened
        top = -17 if x != 44 or state == 0 else -10
        for y in range(top + 3, 26):
            f.px(x, y, WOOD[3])
            f.px(x + 1, y, WOOD[2])
            f.px(x + 2, y, WOOD[1])
        f.px(x + 1, top, WOOD[4])
        f.fill(x, top + 1, x + 2, top + 2, WOOD[3])
        f.px(x + 1, top + 1, WOOD[4])
        for y in (-9, 3, 15):                            # Lashed with rope
            f.fill(x - 1, y, x + 3, y, ROPE[0])
            f.fill(x - 1, y + 1, x + 3, y + 1, ROPE[1])
    if state == 1:                                       # A split along the top log
        for x in range(12, 40):
            f.px(x, -10 + (x // 5) % 2, OUTLINE)


def log(f: Frame, x0: int, y0: int, x1: int, h: int) -> None:
    """A horizontal log, bark on top and bottom, its sawn end ringed."""
    for x in range(x0, x1 + 1):
        for y in range(y0, y0 + h):
            t = (y - y0) / (h - 1)
            c = WOOD[3] if t < 0.25 else WOOD[2] if t < 0.7 else WOOD[1]
            if (x * 7 + y * 3) % 11 == 0:
                c = WOOD[0]                              # Bark cracks
            f.px(x, y, c)
    cx, cy = x1 - 1, y0 + h // 2
    for y in range(y0, y0 + h):                          # The sawn end
        for x in range(x1 - 3, x1 + 2):
            dx, dy = (x - cx) / 2.6, (y - cy) / (h / 2)
            if dx * dx + dy * dy <= 1.0:
                f.px(x, y, BONE[1] if (abs(x - cx) + abs(y - cy)) % 2 else SAND[2])


def barricade_fence(f: Frame, state: int) -> None:
    """A steel crowd barrier: a rounded tube frame, bars, slanted feet."""
    tube = IRON[3:] + [IRON[2]]
    if state == 2:                                       # Knocked flat, bent
        for x in range(2, 66):
            f.px(x, 22 + (1 if 20 < x < 40 else 0), IRON[3])
            f.px(x, 23 + (1 if 20 < x < 40 else 0), IRON[1])
        for x in range(6, 62, 5):
            f.fill(x, 19, x, 21, IRON[2])
        return
    bend = 4 if state == 1 else 0
    for x in range(4, 64):                               # Top and bottom tubes
        sag = bend if 28 <= x <= 40 else bend // 2 if 22 <= x <= 46 else 0
        f.px(x, -16 + sag, IRON[4])
        f.px(x, -15 + sag, IRON[2])
        f.px(x, 1, IRON[3])                              # A rail half way
        f.px(x, 2, IRON[1])
        f.px(x, 18, IRON[3])
        f.px(x, 19, IRON[1])
    for y in range(-14, 18):                             # Rounded ends
        f.px(2, y, IRON[4])
        f.px(3, y, IRON[2])
        f.px(64, y, IRON[3])
        f.px(65, y, IRON[1])
    f.px(3, -16, IRON[4]); f.px(2, -15, IRON[4]); f.px(64, -16, IRON[3]); f.px(65, -15, IRON[3])
    for x in range(8, 62, 4):                            # Bars
        sag = bend if 28 <= x <= 40 else bend // 2 if 22 <= x <= 46 else 0
        for y in range(-14 + sag, 18):
            if y not in (1, 2):
                f.px(x, y, IRON[3])
    for i in range(0, 14):                               # Wire coiled along the top
        for x in range(4 + i * 4, 8 + i * 4):
            if x < 64:
                f.px(x, -18 + (x + i) % 3, IRON[2] if x % 2 else IRON[4])
    f.fill(1, -8, 1, -6, IRON[2])                        # Hooks to the next one
    f.fill(66, 12, 66, 14, IRON[2])
    for x0, d in ((10, -1), (58, 1)):                    # Slanted feet
        for i in range(7):
            f.px(x0 + d * i // 2, 19 + i, IRON[2])
            f.px(x0 - d * i // 2, 19 + i, IRON[3])


def make_barrel() -> Image:
    """A powder keg as tall as a zombie's waist: bulging red staves, three
    iron hoops with rivets, a lid with its bung and a fuse, a painted bomb
    on its belly and a warning band."""
    w, h = 26, 36
    img = Image(w, h)
    f = Frame(img, 0, w)
    cx = w / 2
    for y in range(3, h - 1):                                 # Bulging staves
        t = (y - 3) / (h - 5)
        half = 9.0 + 2.2 * math.sin(math.pi * t)
        for x in range(w):
            u = (x + 0.5 - cx) / half
            if abs(u) > 1.0:
                continue
            c = RED[4] if u < -0.6 else RED[3] if u < -0.15 else RED[2] if u < 0.4 else RED[1] if u < 0.78 else RED[0]
            f.px(x, y, c)
    for y in range(3, h - 1):                                 # Stave joints
        for x in (7, 11, 15, 19):
            if f.get(x, y)[3] and f.get(x - 1, y)[3] and f.get(x + 1, y)[3]:
                f.px(x, y, RED[1] if x > 9 else RED[2])
    for y in (6, 17, 30):                                     # Iron hoops with rivets
        for x in range(w):
            if f.get(x, y)[3]:
                f.px(x, y, IRON[3] if x < 10 else IRON[2] if x < 17 else IRON[1])
                if f.get(x, y + 1)[3]:
                    f.px(x, y + 1, IRON[1])
        for x in (5, 13, 21):
            if f.get(x, y)[3]:
                f.px(x, y, IRON[4])
    for x in range(5, 21):                                    # Lid: a dark rim and its planks
        f.px(x, 3, RED[2] if x < 11 else RED[1])
        f.px(x, 2, WOOD[3] if x < 11 else WOOD[2])
    f.fill(12, 0, 14, 1, WOOD[2])                             # Bung
    f.px(12, 0, WOOD[3])
    for x in range(4, 22):                                    # Warning band under the top hoop
        if f.get(x, 11)[3]:
            f.px(x, 11, BONE[2] if (x // 2) % 2 else OUTLINE)
    # Painted powder mark: a round bomb with a lit fuse, in black and brass.
    for y in range(20, 28):
        for x in range(8, 17):
            if (x - 12.0) ** 2 + (y - 24.0) ** 2 <= 11.0:
                f.px(x, y, OUTLINE if (x, y) != (10, 22) else IRON[3])
    f.px(11, 21, IRON[2])
    for x, y in ((14, 20), (15, 19), (16, 19)):
        f.px(x, y, BRASS[1])
    f.px(17, 18, LAMP[1])
    f.px(18, 17, LAMP[2])
    f.px(17, 17, LAMP[0])
    f.outline()
    return img


def wheel(f: Frame, cx: float, cy: float, r: float, spin: float = 0.0) -> None:
    """Spoked wheel: iron tire, wooden felloe, 10 spokes, hub with a cap."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d > r:
                continue
            lit = (cx - (x + 0.5)) * 0.6 + (cy - (y + 0.5)) * 0.8
            if d > r - 1.2:
                f.px(x, y, IRON[3] if lit > 0 else IRON[1])
            elif d > r - 3.0:
                f.px(x, y, WOOD[3] if lit > 0 else WOOD[1])
            elif d < 2.2:
                f.px(x, y, IRON[2] if lit > 0 else IRON[1])
            elif d < 3.4:
                f.px(x, y, WOOD[3] if lit > 0 else WOOD[2])
    for k in range(10):
        a = spin + k * math.pi / 5
        for s in range(30):
            t = 3.4 + (r - 6.4) * s / 29
            x, y = cx + math.cos(a) * t, cy + math.sin(a) * t
            f.px(int(x), int(y), WOOD[3] if math.sin(a) < 0 else WOOD[2])
    f.px(int(cx), int(cy), IRON[4])


def make_supply() -> Image:
    w, h = 100, 56
    img = Image(w * 2, h)
    for frame in range(2):
        f = Frame(img, frame * w, w)
        full = frame == 0
        # Bed: side boards with planks and iron straps, tongue to the front.
        f.box(6, 32, 90, 41, WOOD)
        for y in (35, 38):
            for x in range(7, 90):
                f.px(x, y, WOOD[1])
        grain(f, 6, 32, 90, 41, WOOD, 17)
        for x in (12, 30, 48, 66, 84):
            f.fill(x, 32, x + 1, 41, IRON[2])
            f.px(x, 33, IRON[4])
            f.px(x, 40, IRON[4])
        f.fill(90, 37, 99, 38, WOOD[2])                   # Tongue
        f.px(99, 36, IRON[3])
        f.fill(4, 42, 92, 43, WOOD[1])                    # Axle beam
        # Canvas hood on wooden hoops.
        for x in range(10, 87):
            u = (x - 48.0) / 39.0
            top = 32 - int(26 * math.sqrt(max(0.0, 1.0 - u ** 6)))
            for y in range(top, 32):
                if not full and 30 <= x <= 66 and y > top + 2:
                    continue                              # Emptied: the side rolled up, inside dark
                fold = (x - 10) % 13
                c = CANVAS[3]
                if y < top + 2:
                    c = CANVAS[4]
                elif fold in (0, 1):
                    c = CANVAS[1]
                elif fold == 2 or x > 78:
                    c = CANVAS[2]
                if y > 28:
                    c = CANVAS[1]
                f.px(x, y, c)
        for x in (10, 23, 36, 49, 62, 75, 86):            # Hoops showing through
            u = (x - 48.0) / 39.0
            top = 32 - int(26 * math.sqrt(max(0.0, 1.0 - u ** 6)))
            for y in range(top, 32, 2):
                f.px(x, y, CANVAS[0])
        if full:
            for x in range(14, 84, 7):                    # Rope lacing along the bottom
                f.px(x, 30, ROPE[1])
                f.px(x + 1, 31, ROPE[0])
            # Crates of ammunition stacked at the open back.
            f.box(0, 22, 13, 31, OLIVE)
            f.box(2, 14, 12, 21, OLIVE)
            for x0, y0 in ((3, 25), (4, 16)):
                f.box(x0, y0, x0 + 6, y0 + 2, BRASS)
            for y in (22, 31):
                f.px(6, y, IRON[3])
        else:
            for y in range(8, 30):                        # Inside: the dark under the hood
                for x in range(31, 66):
                    if f.get(x, y) == (0, 0, 0, 0) and y > 32 - int(26 * math.sqrt(max(0.0, 1.0 - ((x - 48.0) / 39.0) ** 6))) + 2:
                        f.px(x, y, WOOD[0] if (x + y) % 5 else OUTLINE)
            for x in range(30, 67):                       # The rolled canvas
                f.px(x, 9 + abs(x - 48) // 9, CANVAS[3])
                f.px(x, 10 + abs(x - 48) // 9, CANVAS[1])
            f.box(36, 25, 44, 31, OLIVE)                  # One empty crate, lid off
            f.fill(46, 30, 55, 31, OLIVE[2])
        # Lantern hanging at the front.
        f.px(88, 12, IRON[2])
        f.fill(87, 13, 90, 19, IRON[1])
        f.fill(88, 14, 89, 18, LAMP[1] if full else IRON[0])
        if full:
            f.px(88, 15, LAMP[2])
        # Wheels: the back one bigger.
        wheel(f, 22.0, 44.5, 11.5, spin=0.15)
        wheel(f, 76.0, 46.5, 9.5, spin=0.4)
        f.outline()
    return img


def log_post(f: Frame, x0: int, y0: int, x1: int, y1: int) -> None:
    """An upright log: rounded light, bark streaks, a sawn top with rings."""
    w = x1 - x0 + 1
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u = (x - x0 + 0.5) / w
            c = WOOD[4] if u < 0.25 else WOOD[3] if u < 0.5 else WOOD[2] if u < 0.8 else WOOD[1]
            if (y * 7 + x * 3) % 13 == 0:
                c = WOOD[1]
            f.px(x, y, c)
    for x in range(x0, x1 + 1):                            # Sawn top
        f.px(x, y0, BONE[1] if x0 < x < x1 else WOOD[2])
    f.px((x0 + x1) // 2, y0, WOOD[2])


def make_goal() -> Image:
    w, h = 108, 96
    img = Image(w, h)
    f = Frame(img, 0, w)
    # Fence stubs either side.
    for x0 in (0, 98):
        log_post(f, x0, 66, x0 + 3, 95)
        log_post(f, x0 + 6 if x0 == 0 else x0 - 6, 70, (x0 + 6 if x0 == 0 else x0 - 6) + 3, 95)
    for y in (74, 84):
        for x in list(range(0, 18)) + list(range(90, 108)):
            f.px(x, y, GREY_WOOD[2])
            f.px(x, y + 1, GREY_WOOD[0])
    # Posts.
    log_post(f, 14, 10, 23, 95)
    log_post(f, 84, 10, 93, 95)
    # Crossbeam, overhanging both posts, with pegs.
    for y in range(12, 21):
        for x in range(4, 104):
            v = (y - 12) / 8
            c = WOOD[4] if v < 0.2 else WOOD[3] if v < 0.5 else WOOD[2] if v < 0.8 else WOOD[1]
            if (x * 5 + y * 3) % 17 == 0:
                c = WOOD[1]
            f.px(x, y, c)
    for x in (18, 88):
        f.fill(x, 15, x + 1, 16, WOOD[0])
    f.box(3, 12, 6, 20, WOOD[1:])                          # Sawn ends
    f.box(101, 12, 104, 20, WOOD[1:])
    # Diagonal braces under the beam.
    for i in range(12):
        f.px(24 + i, 21 + i, WOOD[3])
        f.px(24 + i, 22 + i, WOOD[1])
        f.px(83 - i, 21 + i, WOOD[3])
        f.px(83 - i, 22 + i, WOOD[1])
    # A longhorn skull on the beam.
    for y in range(4, 13):
        for x in range(46, 62):
            dx = (x - 53.5) / 6.0
            dy = (y - 7.5) / 5.0
            if dx * dx + dy * dy <= 1.0 and not (y > 10 and abs(x - 53.5) > 3):
                f.px(x, y, BONE[3] if dx < -0.2 and dy < 0 else BONE[2] if dx < 0.3 else BONE[1])
    for x in (50, 57):                                     # Eye holes and nose
        f.fill(x, 7, x + 1, 8, OUTLINE)
    f.px(53, 10, OUTLINE)
    f.px(54, 10, OUTLINE)
    for i in range(10):                                    # Horns curling up
        y = 7 - (i * i) // 22
        f.px(45 - i, y, BONE[2])
        f.px(45 - i, y + 1, BONE[0])
        f.px(62 + i, y, BONE[1])
        f.px(62 + i, y + 1, BONE[0])
    # Hanging board on two chains.
    for x in (38, 69):
        for y in range(21, 27):
            f.px(x, y, IRON[2] if y % 2 else IRON[3])
    f.box(32, 27, 75, 39, WOOD[1:])
    for y in (31, 35):
        for x in range(33, 75):
            f.px(x, y, WOOD[1])
    grain(f, 32, 27, 75, 39, WOOD, 29)
    for x, y in ((35, 29), (72, 29), (35, 37), (72, 37)):  # Nails
        f.px(x, y, IRON[4])
    # A painted star in the middle of the board (no text: it reads in any language).
    for y in range(29, 38):
        for x in range(47, 61):
            a = math.atan2(y + 0.5 - 33.5, x + 0.5 - 53.5)
            r = math.hypot(x + 0.5 - 53.5, y + 0.5 - 33.5)
            spike = 2.0 + 2.6 * (0.5 + 0.5 * math.cos(5 * (a + math.pi / 2)))
            if r <= spike:
                f.px(x, y, BRASS[3] if y < 33 else BRASS[2])
    # Lanterns on hooks, lit.
    for cx in (28, 79):
        f.px(cx, 21, IRON[3])
        f.px(cx, 22, IRON[2])
        f.fill(cx - 2, 23, cx + 2, 23, IRON[2])
        for y in range(24, 31):
            for x in range(cx - 2, cx + 3):
                edge = x in (cx - 2, cx + 2)
                f.px(x, y, IRON[1] if edge else LAMP[1] if y > 25 else LAMP[2])
        f.px(cx, 27, LAMP[0])
        f.fill(cx - 2, 31, cx + 2, 31, IRON[2])
    # Rope coiled on the left post.
    for y in range(44, 52, 2):
        for x in range(13, 25):
            f.px(x, y, ROPE[1] if x < 19 else ROPE[0])
    f.outline()
    return img


def stake(f: Frame, x0: int, top: int, w: int, bottom: int, seed: int) -> None:
    """A sharpened upright log of the palisade: point on top, bark streaks."""
    for y in range(top, bottom + 1):
        tip = y - top
        for x in range(x0, x0 + w):
            if tip < w // 2 and abs(x - (x0 + (w - 1) / 2)) > tip:
                continue                                   # The point
            u = (x - x0 + 0.5) / w
            c = WOOD[4] if u < 0.3 else WOOD[3] if u < 0.55 else WOOD[2] if u < 0.85 else WOOD[1]
            if (y * 5 + x * 7 + seed) % 11 == 0:
                c = WOOD[1]
            f.px(x, y, c)


def make_wall() -> Image:
    """The tall palisade closing the gap of a ruined house: sharpened stakes
    over her head, two crossbeams lashed with rope and an iron band.
    Cracked: a split stake and a gap; wrecked: stumps and splinters she can
    walk over."""
    w, h = 44, 72
    img = Image(w * 3, h)
    tops = [6, 2, 5, 0, 4, 1, 6]
    for frame in range(3):
        f = Frame(img, frame * w, w)
        if frame < 2:
            for i, top in enumerate(tops):
                if frame == 1 and i == 4:
                    stake(f, 2 + i * 6, 36, 6, h - 1, i)   # Snapped half way
                    for k in range(5):
                        f.px(3 + i * 6 + k, 36 - (k % 3), WOOD[4])
                    continue
                stake(f, 2 + i * 6, top, 6, h - 1, i)
            for y0 in (18, 52):                             # Crossbeams with rope lashing
                f.box(0, y0, 43, y0 + 4, WOOD[1:])
                grain(f, 0, y0, 43, y0 + 4, WOOD, y0)
                for x in range(4, 44, 6):
                    f.px(x, y0 + 1, ROPE[1])
                    f.px(x + 1, y0 + 2, ROPE[1])
                    f.px(x, y0 + 3, ROPE[0])
            f.fill(0, 36, 43, 37, IRON[2])                   # Iron band with bolts
            for x in range(3, 44, 6):
                f.px(x, 36, IRON[4])
            if frame == 1:                                   # A split down another stake
                for y in range(8, 48):
                    f.px(15 + (y // 6) % 2, y, OUTLINE)
                for y in range(24, 54):                      # Light through the gap
                    f.px(27, y, (0, 0, 0, 0))
                    f.px(28, y, (0, 0, 0, 0))
        else:
            for i in range(7):                               # Stumps and splinters
                top = h - 6 - (i * 5) % 7
                stake(f, 2 + i * 6, top, 6, h - 1, i)
                for x in range(2 + i * 6, 8 + i * 6):
                    f.px(x, top, WOOD[4] if x % 2 else WOOD[2])
            f.box(4, h - 4, 30, h - 2, WOOD[1:])             # A beam on the ground
        f.outline()
    return img


ADOBE = [rgb(0x4a3024), rgb(0x664230), rgb(0x82583e), rgb(0x9c704e), rgb(0xb48a64)]


def adobe_wall(f: Frame, x0: int, x1: int, tops: list, bottom: int, seed: int) -> None:
    """A stretch of adobe wall with a jagged broken top (tops: its height per
    column), mud bricks in rows, cracks."""
    state = seed
    for x in range(x0, x1 + 1):
        top = tops[x - x0]
        for y in range(top, bottom + 1):
            row = (y - top) // 4
            brick = (x + (row % 2) * 4) % 8
            c = ADOBE[2]
            if (y + 1) % 4 == 0 or brick == 0:
                c = ADOBE[1]                                 # Mortar lines
            elif y == top:
                c = ADOBE[4]                                 # Its broken edge, lit
            elif brick in (1, 2) and (y % 4) == 0:
                c = ADOBE[3]
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            if (state >> 16) % 29 == 0:
                c = ADOBE[0]                                 # Chips and holes
            f.px(x, y, c)


def make_wall_ruins() -> Image:
    """What is left of a house round the palisade, drawn behind it: a corner
    of adobe wall with a broken window and a roof beam hanging off it on one
    side, a lower wall with a door frame on the other, rubble at their feet.
    The middle stays open for the palisade."""
    w, h = 180, 84
    img = Image(w, h)
    f = Frame(img, 0, w)
    bottom = h - 1
    # Left: tall corner, its top broken down toward the middle.
    left_tops = [max(14, 10 + (x * 7) % 5 + max(0, x - 34) // 2) for x in range(0, 61)]
    adobe_wall(f, 4, 64, left_tops, bottom, 17)
    f.fill(18, 36, 34, 52, OUTLINE)                          # Window, dark inside
    f.fill(19, 37, 33, 51, rgb(0x1c1418))
    f.box(16, 34, 36, 35, WOOD[1:])                          # Its lintel and sill
    f.box(16, 53, 36, 54, WOOD[1:])
    for y in range(37, 50):                                  # A shutter hanging askew
        f.px(21 + (y - 37) // 3, y, WOOD[2])
        f.px(22 + (y - 37) // 3, y, WOOD[3])
    f.box(62, 6, 66, bottom, WOOD)                           # Corner post
    for t in range(0, 84):                                   # Roof beam, broken, sagging in
        x = 2 + t
        y = 4 + t * 26 // 84
        for dy in range(3):
            f.px(x, y + dy, WOOD[3] if dy == 0 else WOOD[2] if dy == 1 else WOOD[0])
    for i, x in enumerate(range(6, 60, 9)):                  # Rafters' stubs under it
        y = 4 + (x - 2) * 26 // 84
        f.box(x, y + 3, x + 2, y + 7 + (i % 3), WOOD[:4])
    # Right: a lower wall, a door frame with its lintel fallen across.
    right_tops = [30 + (x * 5) % 6 + max(0, 20 - x) // 3 for x in range(0, 66)]
    adobe_wall(f, 112, 177, right_tops, bottom, 29)
    f.fill(140, 40, 158, bottom, OUTLINE)                    # Doorway
    f.fill(141, 41, 157, bottom, rgb(0x1c1418))
    f.box(136, 34, 140, bottom, WOOD)                        # Door posts
    f.box(158, 38, 162, bottom, WOOD)
    for t in range(0, 30):                                   # Lintel fallen at a slant
        x = 134 + t
        y = 34 + t * 14 // 30
        for dy in range(3):
            f.px(x, y + dy, WOOD[3] if dy == 0 else WOOD[1])
    for x in range(112, 118):                                # Its broken post by the palisade
        f.px(x, 28, WOOD[3])
    f.box(112, 28, 116, bottom, WOOD)
    # Rubble: fallen bricks and splinters along the foot of both.
    for i in range(26):
        x = 2 + (i * 37) % 176
        if 66 < x < 112:
            continue
        y = bottom - 2 - (i * 3) % 4
        f.box(x, y, x + 3 + i % 3, y + 2, ADOBE[1:4])
    f.outline()
    return img


def make_dynamite() -> Image:
    """A crate of dynamite: a wooden box with rope handles and a stenciled
    mark, red sticks in paper wrappers poking out of the straw, their fuses
    twisted together."""
    w, h = 24, 18
    img = Image(w, h)
    f = Frame(img, 0, w)
    for x in range(2, 22):                                    # Straw packing behind the sticks
        f.px(x, 7, SAND[3] if x % 3 else SAND[2])
    for i, x0 in enumerate((3, 7, 11, 15)):                   # Sticks, a little uneven
        top = 2 + (i % 2)
        for y in range(top, 9):
            for x in range(x0, x0 + 3):
                f.px(x, y, RED[4] if x == x0 else RED[3] if x == x0 + 1 else RED[1])
        f.px(x0, top + 2, BONE[2])                            # Paper wrapper band
        f.px(x0 + 1, top + 2, BONE[3])
        f.px(x0 + 2, top + 2, BONE[1])
        f.px(x0 + 1, top - 1, ROPE[1])                        # Its fuse
    for x, y in ((4, 0), (8, 1), (12, 0), (16, 1), (19, 0), (20, 1)):
        f.px(x, y, ROPE[0])                                   # Fuses twisted into one
    f.box(1, 8, 22, 17, WOOD)                                 # The box
    grain(f, 1, 8, 22, 17, WOOD, 41)
    f.fill(1, 12, 22, 12, WOOD[1])                            # Board seam
    for x in (1, 22):
        f.fill(x, 9, x, 16, WOOD[0])                          # Corner battens
    # Stencil on its side: a bomb and three bars.
    for y in range(13, 16):
        for x in range(7, 10):
            if (x, y) not in ((7, 13), (9, 13)):
                f.px(x, y, OUTLINE)
    f.px(10, 12, OUTLINE)
    for x in range(12, 18):
        for y in (13, 15):
            f.px(x, y, OUTLINE if x % 2 == 0 else WOOD[1])
    for y in (10, 11):                                        # Rope handles
        f.px(0, y, ROPE[1])
        f.px(23, y, ROPE[1])
    f.outline()
    return img


def make_charge() -> Image:
    """A bundle of four sticks tied with cord and a paper band, its fuse
    curling up and burning: 2 frames of the spark flickering."""
    w, h = 14, 20
    img = Image(w * 2, h)
    for frame in range(2):
        f = Frame(img, frame * w, w)
        for i, x0 in enumerate((1, 4, 7, 10)):
            top = 8 + (i % 2)
            for y in range(top, 20):
                for x in range(x0, min(x0 + 3, w)):
                    f.px(x, y, RED[4] if x == x0 else RED[3] if x == x0 + 1 else RED[1])
            f.px(x0 + 1, top, RED[0])                         # Its end cap
        for x in range(1, 13):
            f.px(x, 12, ROPE[0])                              # Tied with cord
            f.px(x, 16, BONE[2] if x % 4 else BONE[1])        # Paper band
        for x, y in ((6, 7), (6, 6), (7, 5), (8, 4), (8, 3), (7, 2)):
            f.px(x, y, ROPE[1])
        spark = ((7, 1), (8, 0), (6, 0), (9, 1), (5, 2)) if frame == 0 else ((7, 1), (6, 0), (9, 0), (8, 2), (10, 1))
        for i, (x, y) in enumerate(spark):
            f.px(x, y, LAMP[2] if i == 0 else LAMP[1] if i < 3 else LAMP[0])
        f.outline()
    return img


GLASS = [rgb(0x2e5a3a), rgb(0x4a8a5a), rgb(0x9ad0a0)]
AMBER = [rgb(0x6a3a14), rgb(0xa8641e), rgb(0xe0a050)]
DARK_WOOD = [rgb(0x24161a), rgb(0x3a2228), rgb(0x553038), rgb(0x744650)]


def make_crate() -> Image:
    """A loose supply crate with what it holds stencilled on a label: for each
    loot (ammo, health, dynamite, gold, water: the order of Loot in
    terrain.h) whole and split by a shot; then broken open (boards and straw)."""
    w, h = 32, 36
    img = Image(w * 11, h)
    marks = {
        0: ['...yy...', '..yYYy..', '..yYYy..', '..yYYy..', '..yYYy..', '..rrrr..',
            '..yyyy..', '........'],                                  # A cartridge
        1: ['...RR...', '...RR...', '.RRRRRR.', '.RRRRRR.', '...RR...', '...RR...',
            '........', '........'],                                  # A red cross
        2: ['......f.', '.....f..', '..RRRR..', '..RrRR..', '..RrRR..', '..RrRR..',
            '..RRRR..', '........'],                                  # A stick and its fuse
        3: ['..yyyy..', '.yYYYYy.', '.yYyyYy.', '.yYyyYy.', '.yYYYYy.', '..yyyy..',
            '........', '........'],                                  # A gold coin
        4: ['...cc...', '..bccb..', '.bBBBBb.', '.bBwBBb.', '.bBwBBb.', '.bBBBBb.',
            '..bbbb..', '........'],                                  # A jug of water
    }
    colors = {'y': BRASS[1], 'Y': BRASS[3], 'r': RED[2], 'R': RED[3], 'f': IRON[1],
              'c': WOOD[3], 'b': rgb(0x2a5a86), 'B': rgb(0x5aa0d0), 'w': rgb(0xd8f0fa)}
    for frame in range(11):
        f = Frame(img, frame * w, w, h - 28)              # Drawn on its old 28 rows, grown up
        if frame < 10:
            loot, cracked = frame // 2, frame % 2 == 1
            crate(f, 1, -5, 30, 33, seed=23 + loot)
            for y in (-2, 24):                            # Iron straps round it
                f.fill(1, y, 30, y, IRON[2])
                for x in (2, 15, 29):
                    f.px(x, y, IRON[4])
            for y in (4, 5, 6):                           # Rope handles at the sides
                f.px(0, y, ROPE[0])
                f.px(31, y, ROPE[1])
            f.fill(4, -4, 8, -4, BONE[1])                 # A stencilled lot number
            f.fill(24, 26, 27, 26, BONE[1])
            f.fill(10, 8, 21, 19, BONE[2])                # The label, nailed on
            f.fill(10, 19, 21, 19, BONE[1])
            f.fill(21, 8, 21, 19, BONE[1])
            for x, y in ((10, 8), (21, 8), (10, 19), (21, 19)):
                f.px(x, y, IRON[3])
            for row, line in enumerate(marks[loot]):
                for col, ch in enumerate(line):
                    if ch in colors:
                        f.px(12 + col, 10 + row, colors[ch])
            f.px(3, -4, BRASS[3])                         # A glint on the top corner
            f.px(4, -4, BRASS[2])
            if cracked:                                   # A split through boards and label
                x = 16
                for y in range(-4, 27):
                    f.px(x, y, OUTLINE)
                    if y % 3 == 0:
                        x += 1 if y % 6 == 0 else -1
                for y in (10, 17):
                    f.px(x - 1, y, WOOD[4])
        else:
            for x0, y0, x1, y1 in ((1, 23, 14, 25), (12, 24, 30, 26), (3, 20, 9, 22), (19, 20, 27, 22)):
                f.box(x0, y0, x1, y1, WOOD[1:])
            for x in range(5, 27, 2):                     # Straw spilling out
                f.px(x, 18 + (x % 3), BRASS[2])
                f.px(x + 1, 19, BRASS[1])
            f.fill(11, 25, 16, 26, BONE[1])               # The torn label
        f.outline()
    return img



def make_net() -> Image:
    """A net trap laid on the road under dry leaves, its rope running off up
    to a branch; springing (the net whipping up off the road, leaves flying);
    sprung (only the trampled leaves)."""
    w, h = 40, 30
    img = Image(w * 3, h)
    leaves = [rgb(0x5a3e22), rgb(0x7e5a30), rgb(0xa07a3e)]
    for frame in range(3):
        f = Frame(img, frame * w, w)
        for i in range(34):                              # Leaves, thick over it
            x, y = (i * 7) % 38 + 1, 27 + (i * 5) % 3
            if frame == 1 and i % 3 == 0:
                y -= 6 + i % 7                           # Thrown up
            f.px(x, y, leaves[i % 3])
            f.px(x + 1, y, leaves[(i + 1) % 3])
        if frame == 0:
            for x in range(4, 36, 9):                    # A cord or two peeking out
                f.px(x, 29, ROPE[0])
            for y in range(0, 27):                       # Its rope going up, a dark vine
                f.px(36 + (y // 9) % 2, y, WOOD[1])
        elif frame == 1:                                 # The net whipping up, closing
            for y in range(2, 28):
                half = 2 + (y - 2) * 14 // 26
                for x in range(20 - half, 20 + half):
                    if (x + y) % 4 == 0 or (x - y) % 4 == 0 or x in (20 - half, 20 + half - 1):
                        f.px(x, y, ROPE[1] if (x + y) % 2 else ROPE[0])
            for y in range(0, 3):
                f.px(20, y, ROPE[0])
        f.outline()
    return img

def make_net_bag() -> Image:
    """The net closed round whoever stepped in, hanging: a mesh bag (drawn
    over the body, see-through between the cords), swaying left, then right."""
    w, h = 44, 66
    img = Image(w * 4, h)
    for frame in range(4):
        f = Frame(img, frame * w, w)
        lean = -1 if frame % 2 == 0 else 1
        open_mouth = (frame == 2) * 8 + (frame == 3) * 3   # Just sprung: its mouth still open
        for y in range(h):
            t = y / (h - 1)                              # A teardrop: narrow at the knot
            half = 2 + (19 * (t ** 0.6) if t < 0.85 else 19 - (t - 0.85) * 50)
            half += open_mouth * (1 - t) ** 2
            cx = 22 + lean * (1 - t) * 2
            x0, x1 = int(cx - half), int(cx + half)
            for x in range(x0, x1 + 1):
                edge = x in (x0, x1) or y == h - 1
                mesh = (x + y) % 7 == 0 or (x - y) % 7 == 0
                if edge or mesh:
                    f.px(x, y, ROPE[0] if edge else ROPE[1])
        f.fill(20, 0, 23, 2, ROPE[0])                    # The knot
    return img


SNARE_RAISE = 20  # Rows the sapling grew by (SNARE_FRAME_H 84): she hangs higher


def make_snare() -> Image:
    """A snare: a sapling bent down to a trigger peg, its noose open on the
    ground; sprung, the sapling stands up (the rope to the foot is drawn by
    the game, from the tip)."""
    w, h = 48, 64 + SNARE_RAISE
    img = Image(w * 3, h)
    leaf = [rgb(0x3e5a28), rgb(0x4a6a30), rgb(0x5e7e3a)]
    litter = [rgb(0x5a3e22), rgb(0x7e5a30), rgb(0xa07a3e)]
    for frame in range(3):
        f = Frame(img, frame * w, w, SNARE_RAISE)
        for y in range(40, 64):                          # The trunk
            f.px(41, y, WOOD[2])
            f.px(42, y, WOOD[1])
        if frame == 0:                                   # Bent over in an arc to the peg
            for i in range(30):
                x = 41 - i
                y = 40 - int(14 * (1 - ((i - 15) / 15) ** 2))
                f.px(x, y, WOOD[3])
                f.px(x, y + 1, WOOD[1])
                if i % 3 == 0:                           # Leafy: it reads as a bush
                    for dx, dy in ((0, -1), (1, -2), (-1, -1), (0, -2)):
                        f.px(x + dx, y + dy, leaf[(i + dx) % 3])
            for y in range(40, 61):                      # Line down to the peg, a dark vine
                if y % 3:
                    f.px(12, y, WOOD[1])
            f.box(10, 60, 13, 63, WOOD[:3])              # The trigger peg, pushed in low
            for a in range(0, 360, 30):                  # The noose, under the litter
                x = 22 + round(7 * math.cos(math.radians(a)))
                y = 62 + round(1 * math.sin(math.radians(a)))
                if a % 90:
                    f.px(x, y, ROPE[0])
            for i in range(22):                          # Dead leaves strewn over it
                x, y = 9 + (i * 5) % 26, 61 + (i * 7) % 3
                f.px(x, y, litter[i % 3])
                f.px(x + 1, y, litter[(i + 1) % 3])
        elif frame == 1:                                 # Springing: whipping up
            for i in range(40 + SNARE_RAISE // 2):
                x = 41 - i // 2
                y = 40 - i
                f.px(x, y, WOOD[3])
                f.px(x + 1, y, WOOD[1])
            for x, y in ((26, -2), (28, -6), (23, 4), (31, 2)):
                f.px(x, y, rgb(0x4a6a30))                # Leaves shaken off
            f.box(10, 59, 13, 63, WOOD)                  # The peg jerked loose
        else:                                            # Sprung upright, swaying
            for y in range(2 - SNARE_RAISE, 40):
                x = 41 - (40 - y) // 14
                f.px(x, y, WOOD[3])
                f.px(x + 1, y, WOOD[1])
            for x, y in ((36, -12), (37, -11), (42, -4), (43, -5), (35, 2), (38, 10), (44, 18)):
                f.px(x, y, rgb(0x4a6a30))                # A few leaves
            f.box(10, 61, 13, 63, WOOD)                  # The peg, pulled out
        for x, y in ((38, 63), (40, 62), (44, 63), (46, 63)):
            f.px(x, y, rgb(0x4a6a30))                    # Grass at its foot
        f.outline()
    return img


def make_spikes() -> Image:
    """A spike plate in the dirt: flat (its holes showing), the spikes coming
    up, the spikes out with blood on the tips."""
    w, h = 32, 16
    img = Image(w * 3, h)
    for frame in range(3):
        f = Frame(img, frame * w, w)
        f.fill(1, 13, 30, 15, IRON[1])                   # The plate
        f.fill(1, 13, 30, 13, IRON[3])
        for x in range(3, 30, 4):
            f.px(x, 14, OUTLINE)                         # Its holes
            if frame == 0:
                continue
            top = 7 if frame == 1 else 0
            for y in range(top, 14):
                f.px(x, y, IRON[4] if y < top + 2 else IRON[3])
                if y > top + 2:
                    f.px(x + 1, y, IRON[2])
            if frame == 2 and x % 8 == 3:
                f.px(x, 1, RED[2])
                f.px(x, 2, RED[1])
        f.outline()
    return img


BAT_FRAMES = [
    ['................', '.m............m.', '.mM..........Mm.', '..mMM......MMm..',
     '...mMM.^^.MMm...', '....mMBBHHMm....', '......BBHe......', '......BB........',
     '.......f........', '................'],                         # Wings up
    ['................', '................', '................', '.......^^.......',
     'mMMMMMBBHHMMMMMm', '.mMMMMBBHeMMMMm.', '..m.m.BB..m.m...', '.......f........',
     '................', '................'],                         # Level
    ['................', '................', '.......^^.......', '......BBHH......',
     '....MMBBHeMM....', '...MMMBB..MMM...', '..mMM..f...MMm..', '.mM..........Mm.',
     '.m............m.', '................'],                         # Down
    ['................', '................', '................', '........^^......',
     '.....MMBBHH.....', '....mMMBBHe.....', '.....mMBB.......', '.......f........',
     '................', '................'],                         # Folded in
    ['................', '................', '....m......m....', '.....MBBBBM.....',
     '......BBBBr.....', '.....fHHe.......', '......^^........', '................',
     '................', '................'],                         # Shot, tumbling
    ['................', '................', '................', '................',
     '................', '................', '................', '...mMMBBBBHH^...',
     '..mMMMMBBBBre...', '.......r........'],                         # Dead on the road
]


def make_bat() -> Image:
    """A bat, side on, facing right: a wingbeat (wings up, level, down,
    folded in), shot and tumbling, dead on the road. Dark fur, membranes a
    shade lighter with darker tips, pricked ears, a pale glint of an eye."""
    w, h = 16, 10
    img = Image(w * 6, h)
    colors = {'B': rgb(0x2c2430), 'H': rgb(0x18141a), '^': rgb(0x18141a), 'f': rgb(0x18141a),
              'M': rgb(0x564658), 'm': rgb(0x3a2e3c), 'e': rgb(0xe0d8b0), 'r': rgb(0x8a1e1e)}
    for frame, rows in enumerate(BAT_FRAMES):
        f = Frame(img, frame * w, w)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in colors:
                    f.px(x, y, colors[ch])
        f.outline()
    return img


def make_crow() -> Image:
    """A crow, side on and facing right: standing, pecking, a wingbeat (wings
    up, level, down, level), shot and falling (on its back, wings limp), dead
    on the road with a few feathers. Black with a blue sheen, a grey beak."""
    w, h = 16, 12
    img = Image(w * 8, h)
    k = [rgb(0x101014), rgb(0x22242c), rgb(0x3a4256)]   # Black, its sheen
    beak = rgb(0x6c6c70)
    for frame in range(8):
        f = Frame(img, frame * w, w)
        if frame >= 6:                                   # Dead: falling, then lying
            y0 = 4 if frame == 6 else 8
            for x in range(3, 13):                       # Body on its back
                f.px(x, y0 + 1, k[0])
                f.px(x, y0 + 2, k[0] if x % 3 else k[1])
            f.fill(12, y0, 13, y0 + 1, k[0])             # Head lolling, beak down
            f.px(14, y0 + 1, beak)
            f.px(13, y0 + 2, rgb(0x8a1e1e))              # Blood
            for x in (6, 9):                             # Feet up
                f.px(x, y0, beak)
                f.px(x, y0 - 1, beak)
            if frame == 6:                               # Wings trailing up
                for i in range(3):
                    f.px(4 + i, y0 - 1 - i, k[1])
                    f.px(10 - i, y0 - 1 - i, k[1])
            else:                                        # A few loose feathers
                for x, y in ((1, 10), (2, 11), (14, 11)):
                    f.px(x, y, k[1])
            f.outline()
            continue
        flying = frame >= 2
        body_y = 6 if not flying else 5
        for x in range(4, 12):                           # Body
            for y in range(body_y, body_y + 3 + (x > 6 and x < 10)):
                f.px(x, y, k[1] if y == body_y else k[0])
        for x in range(1, 5):                            # Tail
            f.px(x, body_y + 1 + (x < 3), k[0])
        head = (12, body_y - 2) if frame != 1 else (12, body_y + 1)
        f.fill(head[0] - 1, head[1], head[0] + 1, head[1] + 1, k[0])
        f.px(head[0], head[1], k[2])                     # The sheen on its head
        f.px(head[0] + 1, head[1], rgb(0xc8c8c8))        # Eye
        f.px(head[0] + 2, head[1] + 1, beak)
        f.px(head[0] + 3, head[1] + 1, beak)
        if not flying:
            f.fill(8, body_y - 1, 10, body_y - 1, k[2])  # Folded wing
            for x in (7, 9):                             # Legs
                f.px(x, body_y + 4, beak)
                f.px(x, body_y + 5, beak)
        else:
            beat = frame - 2                             # Up, level, down, level
            tip = {0: (7, 0), 1: (3, body_y - 1), 2: (8, 11), 3: (3, body_y - 1)}[beat]
            for bx in range(6, 11):                      # A fan from the shoulder to the tip
                steps = max(abs(tip[0] - bx), abs(tip[1] - body_y), 1)
                for i in range(steps + 1):
                    x = bx + round((tip[0] - bx) * i / steps)
                    y = body_y + round((tip[1] - body_y) * i / steps)
                    f.px(x, y, k[2] if bx in (6, 10) else k[1])
        f.outline()
    return img


WATER = [rgb(0x1c3446), rgb(0x24485e), rgb(0x2f5f78), rgb(0x4a86a0), rgb(0x8cc4d4), rgb(0xd8f0f4)]
MUD = [rgb(0x3a2a1c), rgb(0x54402a), rgb(0x6e5638)]


def make_river() -> Image:
    """A river across the road, wide and flowing right: muddy banks sloping
    to a deep middle (RIVER_DEEP_SHARE of it, dark: waist deep), its sandy
    bed and pebbles showing through where it is shallow, from just over the
    ground line down to the bottom of the view. 4 frames: ripples, foam
    streaks and glints drift right a quarter of their spacing each frame, so
    it loops and the current shows."""
    w, h = 200, 22
    return river_frames(w, h)


def river_depth(x: int, w: int) -> float:
    """0 at the water's edge (5 px in) to 1 in the deep middle, like
    terrain_river_depth (RIVER_DEEP_SHARE 0.55)."""
    wet = w / 2 - 5
    from_bank = wet - abs(x + 0.5 - w / 2)
    return max(0.0, min(1.0, from_bank / (wet * 0.45)))


def river_frames(w: int, h: int) -> Image:
    img = Image(w * 4, h)
    bed = [rgb(0x5e7a72), rgb(0x749088), rgb(0x8aa69a), rgb(0xa2bcaa)]   # Sand through water
    deep = [rgb(0x183040), rgb(0x1f3e52), rgb(0x285068), rgb(0x3a6a82)]
    for frame in range(4):
        f = Frame(img, frame * w, w)
        for y in range(2, h):
            for x in range(w):
                bank = min(x, w - 1 - x)
                if bank < 4 - (y > 5):                   # Muddy banks
                    f.px(x, y, MUD[(x + y) % 3] if y > 3 else MUD[2])
                    continue
                if y <= 3:                               # The surface, level with her ankles
                    f.px(x, y, WATER[4] if y == 2 and (x + frame) % 6 else WATER[3])
                    continue
                d = river_depth(x, w)
                shallow = bed[1 + ((x * 7 + y * 13) % 5 == 0)] if y < 12 else bed[0 + ((x * 5 + y * 3) % 4 == 0)]
                dark = deep[2 - (y > 9) - (y > 15) + ((x * 5 + y * 7) % 9 == 0)]
                # The bed drops away: past a row set by the depth, deep water
                f.px(x, y, dark if y > 4 + int((1 - d) * 16) else shallow)
        for i in range(0, w, 7):                         # Pebbles on the shallow bed
            x, y = (i * 13) % (w - 10) + 5, 6 + (i * 5) % 14
            if river_depth(x, w) < 0.6:
                f.px(x, y, MUD[1])
                f.px(x + 1, y, bed[0])
        for y in range(5, h, 3):                         # Ripples drifting with the current
            for i in range(0, w, 14):
                x0 = (i + frame * 4 + y * 7) % w
                for k in range(5 if river_depth(x0, w) > 0.5 else 3):
                    x = (x0 + k) % w
                    if min(x, w - 1 - x) >= 5:
                        f.px(x, y, deep[3] if river_depth(x, w) > 0.5 and k % 2 else bed[3] if k % 2 else WATER[4])
        for i in range(0, w, 23):                        # Foam streaks on the surface, swept right
            x0 = (i * 3 + frame * 6) % w
            for k in range(7):
                x = (x0 + k) % w
                if min(x, w - 1 - x) >= 6:
                    f.px(x, 3, WATER[5] if k < 4 else WATER[4])
    return img


def make_river_front() -> Image:
    """The river drawn again over whoever wades it: its rows from the surface
    down (rows 2 to 2 + RIVER_FRONT_H), so a body sunk in the deep middle is
    under water to the waist, its feet just covered on the shallow sides."""
    w, h = 200, 17
    river = river_frames(w, 22)
    img = Image(w * 4, h)
    for frame in range(4):
        for y in range(h):
            for x in range(w):
                img.set(frame * w + x, y, river.get(frame * w + x, y + 2))
    return img


def make_puddle() -> Image:
    """A wide puddle on the road: still (two shimmer frames), then rings
    spreading when someone steps in (two frames)."""
    w, h = 64, 6
    cx = w // 2
    img = Image(w * 4, h)
    for frame in range(4):
        f = Frame(img, frame * w, w)
        for y in range(h):
            half = [20, 27, 30, 31, 28, 22][y]
            wobble = (y * 3) % 4 - 1                     # Uneven edges
            for x in range(cx - half + wobble, cx + half - wobble):
                edge = x in (cx - half + wobble, cx + half - wobble - 1)
                f.px(x, y, MUD[1] if edge else WATER[2] if y > 1 else WATER[3])
            if 2 <= y <= 4:                              # Mud and sky reflected in it
                for x in range(cx - half + 6, cx + half - 6, 9):
                    f.px(x, y, WATER[1])
        if frame < 2:                                     # Shimmer: glints sliding along
            for x in (14 + frame * 5, 30 + frame * 3, 44 + frame * 4):
                f.px(x, 1, WATER[5])
                f.px(x + 1, 1, WATER[4])
        else:                                             # Rings
            r = 6 if frame == 2 else 14
            for x in range(cx - r, cx + r + 1):
                f.px(x, 1 if abs(x - cx) > r - 2 else 0, WATER[4])
                if abs(x - cx) >= r - 1:
                    f.px(x, 4, WATER[4])
    return img


def make_splash() -> Image:
    """A splash at someone's feet: drops thrown up and out, falling back."""
    w, h = 20, 12
    img = Image(w * 5, h)
    for frame in range(5):
        f = Frame(img, frame * w, w)
        up = [3, 7, 9, 7, 3][frame]
        spread = 2 + frame * 2
        for d in (-1, 1):
            for k in range(3):
                x = 10 + d * (spread - k * 2)
                y = 11 - up + k * 2 + (frame > 2) * k
                if 0 <= y < h:
                    f.px(x, y, WATER[5] if k == 0 else WATER[4])
                    if frame < 3:
                        f.px(x, y + 1, WATER[3])
        if frame < 2:
            f.fill(8, 11 - up, 11, 11, WATER[4])          # The column of water
        f.fill(4, 11, 15, 11, WATER[3] if frame < 4 else WATER[2])
    return img


def make_tumbleweed() -> Image:
    """A tumbleweed rolling in the wind: 4 frames of a quarter turn."""
    import math
    w = h = 14
    img = Image(w * 4, h)
    dry = [rgb(0x5e4426), rgb(0x8a6a3a), rgb(0xb89458)]
    for frame in range(4):
        f = Frame(img, frame * w, w)
        for i in range(9):                                # Twigs looping round
            a0 = math.radians(i * 40 + frame * 22)
            for t in range(12):
                a = a0 + t * 0.45
                r = 5.5 - (t % 4) * 0.6
                x = 7 + round(r * math.cos(a))
                y = 7 + round(r * math.sin(a))
                f.px(x, y, dry[(i + t) % 3])
        f.outline()
    return img


def make_sign() -> Image:
    """A warning sign by the road: a weathered board on a post, a red
    triangle with a black ! painted on it."""
    w, h = 22, 30
    img = Image(w, h)
    f = Frame(img, 0, w)
    f.box(10, 12, 12, 29, GREY_WOOD)                     # The post
    f.box(1, 1, 20, 16, WOOD[1:])                        # The board
    grain(f, 2, 2, 19, 15, WOOD, 9)
    for x, y in ((3, 3), (18, 3), (3, 14), (18, 14)):
        f.px(x, y, IRON[4])                              # Nails
    for y in range(4, 15):                               # A red triangle...
        half = (y - 4) * 7 // 10
        for x in range(11 - half - 1, 11 + half + 1):
            f.px(x, y, RED[3] if y < 14 else RED[2])
    f.fill(10, 7, 11, 10, OUTLINE)                       # ...and its !
    f.fill(10, 12, 11, 12, OUTLINE)
    f.outline()
    return img



def make_wire() -> Image:
    """Barbed wire coiled across the road between two stakes: whole, cut
    through once (loops sagging), cut apart (strands flat on the ground)."""
    w, h = 80, 22
    img = Image(w * 3, h)
    import math
    for state in range(3):
        f = Frame(img, state * w, w)
        for x in (2, 76):                                # Stakes
            f.box(x, 4, x + 2, 21, GREY_WOOD)
        if state == 2:
            for x in range(4, 76):                       # Strands on the ground
                y = 19 + int(1.5 * math.sin(x * 0.7))
                f.px(x, y, IRON[3])
                if x % 4 == 0:
                    f.px(x, y - 1, IRON[4])              # Barbs
                    f.px(x + 1, y + 1, IRON[4])
            continue
        loops = 7
        for i in range(loops):                           # Overlapping coils
            cx = 9 + i * 10
            sag = 3 if state == 1 and 2 <= i <= 4 else 0
            r = 8 - (sag // 2)
            for a in range(0, 360, 6):
                if state == 1 and i == 3 and 200 < a < 300:
                    continue                             # The cut loop opens
                rad = math.radians(a)
                x = cx + round(r * 0.75 * math.cos(rad))
                y = 12 + sag + round(r * math.sin(rad))
                if 0 <= y < h:
                    f.px(x, y, IRON[4] if a < 180 else IRON[2])
            for a in (30, 100, 160, 230, 300):           # Barbs: short crossed ticks
                rad = math.radians(a + i * 17)
                x = cx + round(r * 0.75 * math.cos(rad))
                y = 12 + sag + round(r * math.sin(rad))
                f.px(x - 1, y - 1, IRON[3])
                f.px(x + 1, y + 1, IRON[3])
                f.px(x + 1, y - 1, IRON[1])
        for x in range(4, 76):                           # A straight strand along the top
            f.px(x, 5 if state == 0 else 7, IRON[3])
            if x % 6 == 0:
                f.px(x, 4 if state == 0 else 6, IRON[4])
        f.outline()
    return img


def make_bottles() -> Image:
    """A saloon table out on the road with three bottles on it: a tall wine
    bottle, a squat whisky and a corked one, a shot glass and cards beside
    them; 3, 2, 1 and 0 left (shards and a spreading stain)."""
    w, h = 40, 40
    img = Image(w * 4, h)
    top = 22                                              # The tabletop's upper row
    shapes = [(7, 'wine'), (17, 'whisky'), (27, 'cork')]
    for frame in range(4):
        f = Frame(img, frame * w, w)
        for x0 in (4, 33):                                # Turned legs, splayed a little
            f.box(x0, top + 3, x0 + 2, h - 1, WOOD)
            f.px(x0 + 1, top + 8, WOOD[4])
            f.px(x0 + 1, top + 12, WOOD[4])
        f.box(6, h - 8, 33, h - 7, WOOD[:4])               # Stretcher between them
        f.box(0, top, w - 1, top + 2, WOOD[1:])            # Tabletop, its lit edge
        grain(f, 0, top, w - 1, top + 2, WOOD, 41)
        f.box(2, top + 3, w - 3, top + 5, WOOD[:3])        # Apron under it
        for x in (8, 20, 31):
            f.px(x, top + 4, BRASS[2])                     # Nail heads
        for i in range(5):                                 # Playing cards, fanned
            f.fill(1 + i * 2, top - 1, 2 + i * 2, top - 1, BONE[3] if i % 2 else BONE[2])
        f.px(3, top - 1, RED[3])
        f.fill(35, top - 3, 37, top - 1, GLASS[2])         # A shot glass
        f.px(36, top - 2, AMBER[2])
        for b, (x0, kind) in enumerate(shapes):
            ramp = AMBER if kind != 'whisky' else GLASS
            if b < frame:                                  # Shot: shards and a stain
                for dx, dy in ((0, 0), (2, -1), (4, 0), (5, -1)):
                    f.px(x0 + dx, top - 1 + dy, ramp[2] if dx % 4 == 0 else ramp[1])
                f.fill(x0 - 1, top, x0 + 5, top, ramp[0])
                continue
            if kind == 'wine':                             # Tall and slim, long neck
                body, neck = range(top - 12, top), range(top - 17, top - 12)
                x_body, x_neck = (x0, x0 + 3), (x0 + 1, x0 + 2)
            elif kind == 'whisky':                         # Squat and square, short neck
                body, neck = range(top - 9, top), range(top - 12, top - 9)
                x_body, x_neck = (x0 - 1, x0 + 4), (x0 + 1, x0 + 2)
            else:                                          # Round shouldered, a cork in it
                body, neck = range(top - 10, top), range(top - 14, top - 10)
                x_body, x_neck = (x0, x0 + 3), (x0 + 1, x0 + 2)
            for y in neck:
                for x in range(x_neck[0], x_neck[1] + 1):
                    f.px(x, y, ramp[2] if x == x_neck[0] else ramp[1])
            for y in body:
                for x in range(x_body[0], x_body[1] + 1):
                    c = ramp[0] if x == x_body[1] else ramp[1]
                    if x == x_body[0] + 1 and y < body[-1] - 2:
                        c = ramp[2]                        # The shine down its side
                    f.px(x, y, c)
            label = body[len(body) // 2]
            f.fill(x_body[0], label, x_body[1], label + 2, BONE[2])
            f.px(x_body[0] + 1, label + 1, RED[2])
            if kind == 'cork':
                f.fill(x_neck[0], neck[0] - 2, x_neck[1], neck[0] - 1, WOOD[3])
            else:
                f.fill(x_neck[0], neck[0] - 1, x_neck[1], neck[0] - 1, ramp[0])
        f.outline()
    return img


def make_trap() -> Image:
    """A big bear trap on the road: open (wide toothed jaws up, the pan in the
    middle, a chain to a stake), snapping (the jaws swinging up), shut."""
    w, h = 32, 12
    img = Image(w * 3, h)
    for frame in range(3):
        f = Frame(img, frame * w, w)
        f.fill(3, 10, 28, 11, IRON[1])                     # Base plate in the dirt
        f.fill(3, 10, 28, 10, IRON[2])
        f.fill(13, 8, 18, 9, IRON[3])                      # The pan
        f.fill(14, 8, 17, 8, IRON[4])
        for x in range(28, 32, 2):                         # Chain to a stake
            f.px(x, 10, IRON[3])
            f.px(x + 1, 9, IRON[2])
        f.fill(30, 6, 31, 11, WOOD[2])
        if frame == 1:                                     # Snapping: jaws halfway up
            for x0, d in ((4, 1), (27, -1)):
                for i in range(9):
                    x = x0 + d * i
                    y = 9 - i
                    f.px(x, y, IRON[3])
                    f.px(x + d, y, IRON[1])
                    if i % 2 == 0:
                        f.px(x + d * 2, y - 1, IRON[4])    # Teeth
            for x in (3, 28):
                f.fill(x - 1, 9, x + 1, 10, IRON[4])
            f.px(15, 4, IRON[4])                           # A spark where they meet
            f.px(16, 3, BONE[3])
        elif frame == 0:
            for x0, d in ((1, 1), (30, -1)):               # Open jaws, big teeth up
                for i in range(12):
                    x = x0 + d * i
                    f.px(x, 9, IRON[2])
                    f.px(x, 8, IRON[3] if i < 11 else IRON[2])
                    if i % 2 == 0:
                        f.px(x, 7, IRON[4])
                        f.px(x, 6, IRON[3])
            for x in (3, 28):                              # Springs
                f.fill(x - 1, 9, x + 1, 10, IRON[4])
        else:
            for y in range(1, 10):                         # Jaws snapped up together
                f.px(15, y, IRON[3])
                f.px(16, y, IRON[1])
            for y in range(1, 9, 2):                       # Teeth crossed
                f.px(14, y, IRON[4])
                f.px(17, y + 1, IRON[4])
            for y in (3, 6):                               # A splash of blood on them
                f.px(17, y, RED[1])
        f.outline()
    return img


def make_coffin() -> Image:
    """An upright coffin, by day and by night (frames: day shut, day burst,
    night shut, night burst). Day: sun-bleached boards, brass handles, a
    white cross. Night: dark wood gone green with moss, iron bands, and a
    sickly glow through the cracks and the eyes of what is inside."""
    w, h = 32, 68
    img = Image(w * 4, h)
    day = [rgb(0x5c4430), rgb(0x86684a), rgb(0xa8885e), rgb(0xc8a878)]
    night = [rgb(0x1c1418), rgb(0x2e2228), rgb(0x44323a), rgb(0x5a4450)]
    moss = [rgb(0x2a4026), rgb(0x46663a)]
    glow = [rgb(0x5a9a4a), rgb(0xa8f088)]

    cx = w // 2

    def half_at(y: int) -> int:
        return 8 + min(y, 16) * 7 // 16 if y < 18 else 15 - (y - 18) * 7 // 50

    for frame in range(4):
        f = Frame(img, frame * w, w)
        ramp = day if frame < 2 else night
        burst = frame % 2 == 1
        for y in range(h):                                 # The hexagon outline of a coffin
            half = half_at(y)
            for x in range(cx - half, cx + half):
                c = ramp[3] if x < cx - half + 2 else ramp[2] if x < cx else ramp[1]
                if (x - (cx - half)) % 5 == 4:
                    c = ramp[0]                            # Board seams
                f.px(x, y, c)
        if not burst:
            if frame == 0:
                f.fill(cx - 5, 14, cx + 4, 15, BONE[2])    # White cross
                f.fill(cx - 1, 7, cx, 34, BONE[2])
                for y in (22, 46):                         # Brass handles
                    f.fill(cx - half_at(y), y, cx + 1 - half_at(y), y + 2, BRASS[2])
                    f.fill(cx - 2 + half_at(y), y, cx - 1 + half_at(y), y + 2, BRASS[1])
            else:
                for y in (11, 34, 57):                     # Iron bands
                    half = half_at(y)
                    f.fill(cx - half, y, cx - 1 + half, y + 1, IRON[2])
                    f.px(cx - half + 1, y, IRON[4])
                for (x, y) in ((9, 20), (10, 21), (21, 50), (22, 51), (11, 60), (20, 28), (12, 41)):
                    f.px(x, y, moss[1] if (x + y) % 2 else moss[0])
                for y in range(22, 50):                    # A crack, glowing
                    f.px(cx + (y // 5) % 2, y, glow[0])
                f.px(cx - 2, 18, glow[1])                  # Eyes in the dark gap
                f.px(cx + 2, 18, glow[1])
        else:
            for y in range(4, h - 4):                      # Burst open: dark inside, splinters
                half = half_at(y) - 3
                for x in range(cx - half, cx + half):
                    f.px(x, y, OUTLINE if (x + y) % 7 else ramp[0])
            for i in range(7):
                f.px(27 + i % 3, 9 + i * 8, ramp[3])
                f.px(3 + i % 2, 13 + i * 7, ramp[2])
            if frame == 3:
                for y in range(11, 57, 9):                 # Its glow spilling out
                    f.px(cx, y, glow[0])
        f.outline()
    return img


def make_lamp() -> Image:
    """An oil lamp hung high on a post braced with a stay: lit; then the post
    alone, its hook bare. The lamp keeps its rows at the top of the frame (the
    light, lighting.c, sits LAMP_FRAME_H - 8 rows up)."""
    w, h = 14, 76
    img = Image(w * 2, h)
    for frame in range(2):
        f = Frame(img, frame * w, w)
        f.box(3, 6, 5, h - 1, GREY_WOOD)                    # Post
        for y in range(20, h - 4, 9):
            f.px(4, y, GREY_WOOD[0])                        # Cracks in the old wood
        f.fill(5, 7, 10, 8, GREY_WOOD[2])                   # Arm
        for i in range(6):                                  # The stay under it
            f.px(5 + i, 14 - i, GREY_WOOD[1])
        f.fill(2, h - 6, 6, h - 1, GREY_WOOD[1])            # Foot, stones round it
        f.px(1, h - 1, IRON[2]); f.px(7, h - 1, IRON[3])
        f.px(10, 9, IRON[3])                                # Hook
        if frame == 0:
            f.fill(9, 9, 11, 10, IRON[2])                   # Lamp cap and ring
            f.px(10, 8, IRON[3])
            for y in range(11, 19):
                for x in range(8, 13):
                    edge = x in (8, 12)
                    f.px(x, y, IRON[1] if edge else LAMP[1] if y > 12 else LAMP[2])
            f.px(10, 15, LAMP[0])
            f.fill(9, 13, 11, 13, LAMP[2])                  # The flame's bright core
            f.fill(8, 19, 12, 20, IRON[2])                  # Its oil font
            f.px(9, 19, IRON[3])
        f.outline()
    return img


def make_fire() -> Image:
    """Burning oil on the ground: four frames of tongues flickering."""
    w, h = 32, 24
    img = Image(w * 4, h)
    for frame in range(4):
        state = 991 + frame * 313
        for x in range(2, 30):
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            tall = 6 + (state >> 16) % 14 - abs(x - 16) // 3
            for y in range(h - 1, h - 1 - max(2, tall), -1):
                k = (h - 1 - y) / max(1, tall)
                c = 'W' if k < 0.2 and abs(x - 16) < 8 else 'Y' if k < 0.45 else 'o' if k < 0.75 else 'r'
                img.set(frame * w + x, y, FLAME[c])
    return img


def make_bench() -> Image:
    """A bench to rest on, seen from the front, its seat at a sitting
    character's lap (10 rows above the ground), a tall backrest and arms:
    frame 0 of wood (slats on posts, braced legs), frame 1 of wrought iron
    (scrolled ends, a lattice back, wooden seat slats)."""
    w, h = 76, 44
    img = Image(w * 2, h)
    seat = h - 10
    for frame in range(2):
        f = Frame(img, frame * w, w)
        if frame == 0:
            for x in (7, w - 10):
                f.box(x, 0, x + 2, seat, WOOD)              # Backrest posts, capped
                f.fill(x - 1, 0, x + 3, 1, WOOD[4])
            for y0 in (3, 10, 17, 24):                      # Backrest slats
                f.box(1, y0, w - 2, y0 + 4, WOOD[1:])
                grain(f, 1, y0, w - 2, y0 + 4, WOOD, 31 + y0)
            for x in (8, w - 9):
                for y0 in (3, 10, 17, 24):
                    f.px(x, y0 + 2, IRON[4])                # Bolts
            for x0 in (0, w - 5):                           # Arms
                f.box(x0, seat - 7, x0 + 4, seat - 5, WOOD[1:])
                f.box(x0 + 1, seat - 5, x0 + 3, seat, WOOD[:4])
            f.box(0, seat, w - 1, seat + 3, WOOD[1:])       # Seat planks, their front edge
            grain(f, 0, seat, w - 1, seat + 2, WOOD, 77)
            f.fill(1, seat + 3, w - 2, seat + 3, WOOD[0])
            f.box(8, seat + 6, w - 9, seat + 7, WOOD[:4])   # Stretcher
            for x0 in (3, w - 9):                           # Legs, iron-shod
                f.box(x0, seat + 4, x0 + 5, h - 1, WOOD)
                f.fill(x0, h - 2, x0 + 5, h - 1, IRON[2])
                f.px(x0 + 1, h - 2, IRON[3])
        else:
            iron = IRON[1:]
            for x0 in (2, w - 6):                           # Cast ends: post, scroll, foot
                f.box(x0, 2, x0 + 3, h - 1, iron)
                for a in range(0, 360, 30):                 # A scroll for the arm
                    x = x0 + 2 + round(3 * math.cos(math.radians(a)))
                    y = seat - 8 + round(3 * math.sin(math.radians(a)))
                    f.px(x, y, IRON[3])
                f.fill(x0 - 1, h - 2, x0 + 4, h - 1, IRON[2])
            for y in (2, 26):                               # Top and bottom rails of the back
                f.box(4, y, w - 5, y + 1, iron)
            for y in range(4, 26):                          # Lattice: crossing diagonals
                for x in range(6, w - 6):
                    if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                        f.px(x, y, IRON[3] if (x + y) % 6 == 0 else IRON[2])
            for x in range(9, w - 8, 12):                   # Rosettes where they cross
                f.fill(x, 14, x + 1, 15, IRON[4])
            for y0 in (seat, seat + 2):                     # Seat slats of wood on iron
                f.box(0, y0, w - 1, y0 + 1, WOOD[1:])
            f.fill(1, seat + 4, w - 2, seat + 4, IRON[1])
            for x in range(10, w - 10, 6):                  # Apron curls under the seat
                f.px(x, seat + 5, IRON[3])
                f.px(x + 1, seat + 6, IRON[3])
                f.px(x + 2, seat + 5, IRON[3])
        f.outline()
    return img


def make_campfire() -> Image:
    """A campfire to rest by: a ring of shaded stones, logs crossed in the
    embers, tall flames with sparks. Frames 0-3 the fire alone; 4-7 the same
    with a cooking rig over it: two forked sticks, a pole across and a pot
    hanging from it on a wire, steaming."""
    w, h = 48, 56
    img = Image(w * 8, h)
    stone = [rgb(0x3a3838), rgb(0x5a5654), rgb(0x807a74), rgb(0x9c968e)]
    ember = [rgb(0x7a2a10), rgb(0xd0581a), rgb(0xffa040)]
    pot = [rgb(0x18181c), rgb(0x2c2c32), rgb(0x46464e), rgb(0x6a6a74)]
    for frame in range(8):
        f = Frame(img, frame * w, w, h - 44)                # Drawn on its old 44 rows, flames grown up
        rig = frame >= 4
        base = 44 - 8
        cx = w // 2
        state = 4211 + (frame % 4) * 977
        for x in range(cx - 12, cx + 12):                   # Flames
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            tall = 20 + (state >> 16) % 16 - abs(x - cx) * 3 // 2
            if rig:
                tall = min(tall, 17)                        # Licking the pot's bottom
            tall = max(2, tall)
            for y in range(base, base - tall, -1):
                k = (base - y) / tall
                c = 'W' if k < 0.3 and abs(x - cx) < 6 else 'Y' if k < 0.55 else 'o' if k < 0.82 else 'r'
                f.px(x, y, FLAME[c])
        for i in range(4):                                  # Sparks rising
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            sx = cx - 9 + (state >> 16) % 19
            sy = (-10 if not rig else 1) + ((state >> 8) % 10) + frame % 4
            f.px(sx, sy, FLAME['Y'] if i % 2 else FLAME['o'])
        for (x0, y0, x1, y1) in ((7, base, 36, base - 6), (41, base, 12, base - 6)):
            n = max(abs(x1 - x0), abs(y1 - y0))             # Logs crossed in the fire
            for t in range(n + 1):
                x = round(x0 + (x1 - x0) * t / n)
                y = round(y0 + (y1 - y0) * t / n)
                for dy in (0, 1, 2):
                    f.px(x, y + dy, (WOOD[3] if t % 5 else WOOD[4]) if dy == 0 else WOOD[2] if dy == 1 else WOOD[0])
            for dy in (0, 1, 2):                            # Glowing ends
                f.px(x1, y1 + dy, ember[2 if frame % 2 else 1])
        for x in range(10, w - 10):                         # Embers in the bed
            f.px(x, base + 1, ember[(x + frame) % 3])
            f.px(x, base + 2, ember[0])
        for i, sx in enumerate(range(3, w - 2, 6)):         # Ring of stones, uneven, two deep
            top = 44 - 8 + (i % 2)
            f.box(sx - 2, top, sx + 3, 44 - 4, stone[:3])
            f.px(sx - 1, top + 1, stone[3])
        for i, sx in enumerate(range(0, w, 7)):
            top = 44 - 5 + (i % 2)
            f.box(sx, top, sx + 5, 44 - 1, stone[1:])
            f.px(sx + 1, top + 1, stone[3])
        for y0, x0 in ((44 - 3, 0), (44 - 5, 1)):            # Firewood stacked at the side
            f.box(x0, y0, x0 + 5, y0 + 1, WOOD[1:4])
            f.px(x0 + 5, y0, BONE[1])
        if rig:
            for px0 in (3, w - 5):                          # Forked sticks driven in
                f.box(px0, 6, px0 + 1, h - 3, WOOD[1:4])
                f.px(px0 - 1, 4, WOOD[2])
                f.px(px0 - 2, 3, WOOD[3])
                f.px(px0 + 2, 4, WOOD[2])
                f.px(px0 + 3, 3, WOOD[3])
            for x in range(0, w):                           # The pole across, bark and knots
                f.px(x, 5, WOOD[3] if x % 7 else WOOD[4])
                f.px(x, 6, WOOD[1] if x % 5 else WOOD[0])
            for y in range(7, 12):                          # Its wire bail
                f.px(cx - 4 + (11 - y) // 2, y, IRON[3])
                f.px(cx + 3 - (11 - y) // 2, y, IRON[3])
            for y in range(12, 25):                         # The pot: dark tin, a lit side, its rim
                for x in range(cx - 6, cx + 6):
                    c = pot[1]
                    if x <= cx - 4:
                        c = pot[2] if y > 12 else pot[3]
                    elif x >= cx + 3:
                        c = pot[0]
                    if y == 12:
                        c = pot[3] if x < cx + 3 else pot[2]
                    if y >= 22 and (x + frame) % 3 == 0:
                        c = ember[0]                        # Soot glowing at its bottom
                    f.px(x, y, c)
            for i in range(3):                              # Steam off it
                sx = cx - 3 + i * 3 + (frame % 2)
                sy = 9 - (frame + i) % 4
                f.px(sx, sy, SMOKE[2])
        f.outline()
    return img


def make_heal() -> Image:
    """Healing, big enough to see in a fight: a bright green aura swelling
    round the whole body in two rings, a column of sparkles rising from the
    feet and a big outlined + floating up over the head (12 frames of
    64 x 96, pivot at the bottom center, on the ground)."""
    w, h = 64, 96
    frames = 12
    img = Image(w * frames, h)
    green = [rgb(0x1e6a2a), rgb(0x3cb04c), rgb(0x7cf08a), rgb(0xd8ffdc)]
    cx = 31.5
    for frame in range(frames):
        ox = frame * w
        fade = frame / (frames - 1)
        for k, (start, grow) in enumerate(((10.0, 1.6), (4.0, 1.6))):   # Two rings, one after the other
            ring = start + frame * grow
            cy = 60 - frame * 1.5
            shade = green[2] if fade < 0.4 else green[1] if fade < 0.75 else green[0]
            if k == 1 and frame < 2:
                continue
            for y in range(h):
                for x in range(w):
                    d = ((x - cx) ** 2 + ((y - cy) * 0.65) ** 2) ** 0.5
                    if abs(d - ring) < (1.4 if k == 0 else 0.9) and frame < frames - 1:
                        if k == 0 or (x + y) % 2 == 0:
                            img.set(ox + x, y, shade)
        for i in range(14):                                 # Sparkles rising from the feet
            sx = 6 + (i * 23) % 52
            sy = h - 4 - ((i * 13 + frame * 7) % 84)
            if (i + frame) % 4 == 3 or frame == frames - 1:
                continue
            img.set(ox + sx, sy, green[3])
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= sy + dy < h:
                    img.set(ox + sx + dx, sy + dy, green[2])
        if frame < frames - 1:                              # The + rising over the head, outlined
            py = 22 - frame * 1.5
            py = int(py)
            arm = 6 if frame > 1 else 3 + frame * 2
            plus = set()
            for i in range(-arm, arm + 1):
                for t in (-1, 0, 1):
                    plus.add((31 + i, py + t))
                    plus.add((31 + t, py + i))
            for (x, y) in plus:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in plus and 0 <= q[1] < h:
                        img.set(ox + q[0], q[1], green[0])
            for (x, y) in plus:
                if 0 <= y < h:
                    img.set(ox + x, y, green[3] if abs(x - 31) + abs(y - py) <= 2 else green[2])
    return img


def make_glow() -> Image:
    """Light around a flame: a soft warm disc, brightest in the middle, drawn
    additively and stretched (32 x 32)."""
    s = 32
    img = Image(s, s)
    for y in range(s):
        for x in range(s):
            d = (((x - 15.5) ** 2 + (y - 15.5) ** 2) ** 0.5) / 16.0
            if d >= 1.0:
                continue
            a = (1.0 - d) ** 2
            img.set(x, y, (int(255 * a), int(170 * a), int(80 * a), 255))
    return img


def make_explosion() -> Image:
    """A barrel going up (8 frames of 72 x 72, pivot at the bottom center):
    a fireball that swells and burns out under a rising cloud, sparks and
    bits flung out, a scorch flash along the ground."""
    w = h = 72
    img = Image(w * 8, h)
    cx, cy = 36.0, 50.0
    for frame in range(8):
        ox = frame * w
        fire = [5, 13, 20, 23, 21, 16, 7, 0][frame]      # Fireball radius
        smoke = [0, 0, 9, 15, 20, 24, 27, 28][frame]     # Smoke radius, rising
        rise = frame * 2.5
        state = 12345 + frame * 977
        for y in range(h):
            for x in range(w):
                state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                n = (state >> 16) % 100 / 100.0
                ds = math.hypot(x - cx, (y - (cy - 12 - rise)) * 1.2)
                df = math.hypot(x - cx, (y - cy) * 1.15)
                if fire and df <= fire * (0.85 + 0.3 * n) and y < h - 2:
                    k = df / fire
                    c = 'W' if k < 0.35 else 'Y' if k < 0.6 else 'o' if k < 0.85 else 'r'
                    if frame >= 4 and c == 'W':
                        c = 'Y'
                    img.set(ox + x, y, FLAME[c])
                elif smoke and ds <= smoke * (0.8 + 0.35 * n) and frame >= 2:
                    k = ds / smoke
                    img.set(ox + x, y, SMOKE[2] if k < 0.4 else SMOKE[1] if k < 0.75 else SMOKE[0])
        if frame < 5:                                     # Flash along the ground
            reach = 14 + frame * 7
            for x in range(int(cx - reach), int(cx + reach)):
                if 0 <= x < w:
                    for y in (h - 3, h - 2):
                        img.set(ox + x, y, FLAME['o' if abs(x - cx) > reach * 0.6 else 'Y'])
        if frame in (1, 2, 3, 4):                         # Sparks and bits flung out
            for i in range(16):
                a = i * 2 * math.pi / 16 + frame * 0.3
                r = 14 + frame * 7
                x, y = int(cx + math.cos(a) * r), int(cy + math.sin(a) * r * 0.75)
                if 0 <= x < w and 0 <= y < h - 1:
                    img.set(ox + x, y, FLAME['Y'] if i % 3 else WOOD[2])
                    if i % 2 and 0 <= x + 1 < w:
                        img.set(ox + x + 1, y, FLAME['o'] if i % 3 else WOOD[1])
    return img


# Background houses are drawn in the props' sunset colors only (dark to
# light below), so each theme's palette swap (themes.c) recolors them like the
# props; the window glass and lamplight stay as they are.
H = [rgb(0x312224), rgb(0x45332a), rgb(0x4f2b2a), rgb(0x5a4334), rgb(0x5e302a), rgb(0x6d3d1f)]
H_HOLE = rgb(0x1a1214)
H_GLOW = [rgb(0x8a5a2a), rgb(0xd09040), rgb(0xf0c870)]


def h_planks(f: Frame, x0: int, y0: int, x1: int, y1: int, seed: int, shade: int = 0) -> None:
    """A wall of vertical boards, 3 px wide: a lit edge, a dark seam, knots,
    a darker foot. shade darkens it (the side away from the sun)."""
    state = seed
    for x in range(x0, x1 + 1):
        k = (x - x0) % 3
        for y in range(y0, y1 + 1):
            c = [3, 2, 1][k] - shade
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            if (state >> 16) % 37 == 0:
                c = 0
            if y >= y1 - 1:
                c = min(c, 1)
            f.px(x, y, H[max(0, c)])


def h_roof(f: Frame, cx: float, top: int, x0: int, x1: int, eave: int) -> None:
    """A pitched roof of shingle rows: the sunlit slope on the left."""
    for y in range(top, eave + 1):
        half = (y - top) * (x1 - x0) / 2 / max(1, eave - top)
        for x in range(int(round(cx - half)), int(round(cx + half)) + 1):
            row = (y - top) // 3
            seam = (y - top) % 3 == 2 or (x + row * 2) % 5 == 0
            left = x < cx
            c = (4 if not seam else 3) if left else (2 if not seam else 1)
            f.px(x, y, H[c])
    for x in range(x0, x1 + 1):                              # Its shadow under the eave
        f.px(x, eave + 1, H[0])


def h_window(f: Frame, x: int, y: int, w: int, h: int, lit: bool) -> None:
    f.fill(x - 1, y - 1, x + w, y + h, H[4])                 # Frame
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if lit:
                c = H_GLOW[2] if yy < y + h // 2 and xx < x + w // 2 else H_GLOW[1]
            else:
                c = H_HOLE
            f.px(xx, yy, c)
    f.fill(x + w // 2, y, x + w // 2, y + h - 1, H[1])       # Muntins
    f.fill(x, y + h // 2, x + w - 1, y + h // 2, H[1])
    f.fill(x - 2, y + h, x + w + 1, y + h + 1, H[5])         # Sill
    f.fill(x - 2, y + h + 1, x + w + 1, y + h + 1, H[1])


def h_door(f: Frame, x: int, y: int, w: int, b: int) -> None:
    f.fill(x - 1, y - 1, x + w, b, H[4])
    for xx in range(x, x + w):
        for yy in range(y, b + 1):
            f.px(xx, yy, H[1] if (xx - x) % 3 == 2 else H[2])
    f.px(x + w - 2, (y + b) // 2, H_GLOW[1])                 # Knob


def make_houses() -> Image:
    """Buildings far off the road, seen past it (5 frames of 80 x 64, resting
    on their last row): a saloon with a false front, a balcony and a porch;
    a shack with a chimney and a woodpile; a barn with its loft and hay
    hoist; a house fallen in; a water tower on its legs."""
    w, h = 80, 64
    img = Image(w * 5, h)
    b = h - 1

    # Saloon.
    f = Frame(img, 0, w)
    h_planks(f, 12, 22, 67, b, 11)
    h_planks(f, 52, 22, 67, b, 12, shade=1)
    h_planks(f, 8, 4, 71, 26, 13)
    f.fill(24, 0, 55, 4, H[4])                               # Stepped crown
    f.fill(24, 0, 55, 0, H[5])
    f.fill(8, 4, 71, 4, H[5])
    f.fill(18, 8, 61, 16, H[0])                              # Sign board, its letters
    f.fill(19, 9, 60, 15, H[1])
    for i, x in enumerate(range(22, 58, 5)):
        f.fill(x, 11, x + 2, 13, H[5] if i % 2 == 0 else H[4])
    f.fill(4, 26, 75, 28, H[4])                              # Balcony and its railing
    f.fill(4, 26, 75, 26, H[5])
    for x in range(6, 75, 4):
        f.fill(x, 20, x, 25, H[3])
    f.fill(4, 20, 75, 20, H[4])
    h_window(f, 18, 31, 8, 9, True)
    h_window(f, 54, 31, 8, 9, False)
    f.fill(2, 42, 77, 44, H[4])                              # Porch roof on posts
    f.fill(2, 42, 77, 42, H[5])
    f.fill(2, 45, 77, 45, H[0])
    for x in (4, 38, 74):
        f.fill(x, 45, x + 1, b, H[3])
    f.fill(30, 48, 47, b, H_HOLE)                            # Swinging doors
    for x0 in (31, 40):
        f.fill(x0, 50, x0 + 6, 57, H[3])
        f.fill(x0, 50, x0 + 6, 50, H[5])
    h_window(f, 14, 49, 8, 8, True)
    f.fill(58, 54, 64, b, H[2])                              # A barrel by the door
    f.fill(58, 56, 64, 56, H[0])
    f.fill(58, 60, 64, 60, H[0])
    f.fill(58, 54, 58, b, H[4])
    f.outline()

    # Shack.
    f = Frame(img, w, w)
    f.fill(52, 8, 58, 30, H[1])                              # Stone chimney
    for y in range(8, 30, 3):
        for x in range(52, 59, 3):
            f.px(x + (y // 3) % 2, y, H[3])
    f.fill(51, 7, 59, 8, H[3])
    h_roof(f, 39.5, 12, 8, 71, 33)
    h_planks(f, 14, 34, 65, b, 21)
    h_planks(f, 50, 34, 65, b, 22, shade=1)
    h_door(f, 22, 44, 9, b)
    h_window(f, 40, 42, 8, 8, True)
    for i in range(3):                                       # A woodpile: log ends
        for j in range(4 - i):
            x, y = 67 + j * 3 + i, b - 1 - i * 3
            f.fill(x, y - 1, x + 2, y + 1, H[2])
            f.px(x + 1, y, H[5])
    f.outline()

    # Barn.
    f = Frame(img, 2 * w, w)
    for y in range(4, 30):                                   # Gambrel roof
        if y < 14:
            half = 14 + (y - 4) * 1.6
        else:
            half = 30 + (y - 14) * 0.6
        for x in range(int(39.5 - half), int(39.5 + half) + 1):
            row = (y - 4) // 3
            seam = (y - 4) % 3 == 2 or (x + row * 2) % 5 == 0
            f.px(x, y, H[(4 if not seam else 3) if x < 39.5 else (2 if not seam else 1)])
    f.fill(6, 30, 73, 30, H[0])
    h_planks(f, 8, 31, 71, b, 31)
    h_planks(f, 52, 31, 71, b, 32, shade=1)
    f.fill(33, 12, 46, 24, H[4])                             # Loft door, the hoist beam
    f.fill(34, 13, 45, 23, H_HOLE)
    f.fill(36, 8, 43, 9, H[3])
    f.fill(39, 10, 39, 18, H[1])
    for x in range(35, 45, 2):                               # Hay showing
        f.px(x, 22, H_GLOW[0])
    f.fill(24, 40, 55, b, H[4])                              # Big doors, X-braced
    f.fill(25, 41, 54, b, H[2])
    for t in range(0, 22):
        for x0, sign in ((25, 1), (39, 1), (40, -1), (54, -1)):
            x = x0 + sign * (t * 14 // 21)
            f.px(x, 41 + t, H[4])
    f.fill(39, 41, 40, b, H[0])
    f.outline()

    # Fallen in.
    f = Frame(img, 3 * w, w)
    f.fill(56, 4, 63, b, H[1])                               # The chimney left standing
    for y in range(4, b, 3):
        for x in range(56, 64, 3):
            f.px(x + (y // 3) % 2, y, H[3])
    f.fill(55, 3, 64, 4, H[3])
    h_planks(f, 8, 28, 30, b, 41)
    for x in range(8, 31):                                   # Its broken top
        for y in range(28, 28 + (x * 7) % 6):
            f.px(x, y, (0, 0, 0, 0))
    h_planks(f, 36, 40, 66, b, 42, shade=1)
    for x in range(36, 67):
        for y in range(40, 40 + (x * 5) % 4):
            f.px(x, y, (0, 0, 0, 0))
    h_window(f, 14, 38, 8, 9, False)
    for t in range(0, 44):                                   # Roof beams down at a slant
        x, y = 10 + t, 18 + t * 22 // 44
        f.px(x, y, H[4])
        f.px(x, y + 1, H[1])
    for t in range(0, 26):
        x, y = 30 + t, 12 + t * 26 // 26
        f.px(x, y, H[3])
        f.px(x, y + 1, H[0])
    for i in range(6):                                       # Boards on the ground
        f.fill(32 + i * 6, b - 1 - i % 2, 36 + i * 6, b, H[2 + i % 2])
    f.outline()

    # Water tower.
    f = Frame(img, 4 * w, w)
    for x0 in (20, 58):                                      # Legs and braces
        f.fill(x0, 30, x0 + 1, b, H[2])
    for x0 in (30, 48):
        f.fill(x0, 30, x0 + 1, b, H[1])
    for y0 in (30, 46):
        for t in range(0, 16):
            f.px(20 + t * 38 // 15, y0 + t, H[3])
            f.px(59 - t * 38 // 15, y0 + t, H[1])
    f.fill(16, 28, 63, 30, H[4])                             # Deck
    f.fill(16, 28, 63, 28, H[5])
    for x in range(16, 64, 3):
        f.fill(x, 24, x, 27, H[3])
    h_planks(f, 22, 8, 57, 27, 51)                           # The tank, banded
    h_planks(f, 46, 8, 57, 27, 52, shade=1)
    for y in (12, 20):
        f.fill(22, y, 57, y, H[0])
    for y in range(0, 8):                                    # Its cone roof
        half = 6 + y * 3
        for x in range(int(39.5 - half), int(39.5 + half) + 1):
            f.px(x, y, H[4] if x < 39.5 else H[2])
    f.fill(38, 0, 41, 1, H[5])
    f.fill(57, 10, 60, 11, H[1])                             # Spout
    f.fill(60, 10, 60, 18, H[1])
    f.outline()
    return img

# --- Town structures: church, sheriff's office, blacksmith, stable, bank -------
# Drawn at any size with a doorway where asked, in a palette: the background's
# (the props' colors, so themes recolor them) or the road's (their own colors:
# a wall that is a building's front with its door barred, blown to get through).

BG_PAL = {
    'wood': H, 'hole': H_HOLE, 'glow': H_GLOW, 'stone': [H[0], H[1], H[2], H[3], H[4]],
    'paint': [H[1], H[2], H[3], H[4], H[5]], 'metal': [H[0], H[1], H[3]], 'brass': [H[3], H[5]],
}
ROAD_PAL = {
    'wood': [rgb(0x2e1c12), WOOD[0], WOOD[1], WOOD[2], WOOD[3], WOOD[4]],
    'hole': rgb(0x140e0e), 'glow': H_GLOW,
    'stone': [rgb(0x3a3838), rgb(0x5a5654), rgb(0x807a74), rgb(0x9c968e), rgb(0xb8b2a8)],
    'paint': [rgb(0x7a7268), rgb(0xa49c8c), rgb(0xc8c0ae), rgb(0xe0d8c6), rgb(0xf2ecdc)],
    'metal': [IRON[0], IRON[2], IRON[3]], 'brass': [BRASS[1], BRASS[3]],
}


def s_planks(f: Frame, x0: int, y0: int, x1: int, y1: int, ramp: list, seed: int, shade: int = 0) -> None:
    state = seed
    for x in range(x0, x1 + 1):
        k = (x - x0) % 3
        for y in range(y0, y1 + 1):
            c = [3, 2, 1][k] - shade
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            if (state >> 16) % 37 == 0:
                c = 0
            f.px(x, y, ramp[max(0, min(len(ramp) - 1, c))])


def s_stone(f: Frame, x0: int, y0: int, x1: int, y1: int, ramp: list) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            row = (y - y0) // 3
            seam = (y - y0) % 3 == 2 or (x + row * 3) % 6 == 0
            f.px(x, y, ramp[1] if seam else ramp[2 + (x * 7 + y * 3) % 2])


def s_roof(f: Frame, cx: float, top: int, half_w: float, eave: int, ramp: list) -> None:
    for y in range(top, eave + 1):
        half = (y - top) * half_w / max(1, eave - top)
        for x in range(int(round(cx - half)), int(round(cx + half)) + 1):
            row = (y - top) // 3
            seam = (y - top) % 3 == 2 or (x + row * 2) % 5 == 0
            c = (4 if not seam else 3) if x < cx else (2 if not seam else 1)
            f.px(x, y, ramp[c])
    for x in range(int(cx - half_w), int(cx + half_w) + 1):
        f.px(x, eave + 1, ramp[0])


def s_window(f: Frame, x: int, y: int, w: int, h: int, pal: dict, lit: bool, bars: bool = False,
             arch: bool = False) -> None:
    wood = pal['wood']
    f.fill(x - 1, y - 1, x + w, y + h, wood[4])
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if arch and yy < y + 2 and (xx == x or xx == x + w - 1):
                f.px(xx, yy, wood[4])
                continue
            c = (pal['glow'][2] if yy < y + h // 2 and xx < x + w // 2 else pal['glow'][1]) if lit else pal['hole']
            f.px(xx, yy, c)
    if bars:
        for xx in range(x + 1, x + w, 2):
            f.fill(xx, y, xx, y + h - 1, pal['metal'][2])
    else:
        f.fill(x + w // 2, y, x + w // 2, y + h - 1, wood[1])
        f.fill(x, y + h // 2, x + w - 1, y + h // 2, wood[1])
    f.fill(x - 2, y + h, x + w + 1, y + h + 1, wood[5])


def s_doorway(f: Frame, door: tuple, pal: dict) -> None:
    """The dark doorway and its frame: where the door hangs (or the road
    goes through once it is blown)."""
    x, y, w, h = door
    wood = pal['wood']
    f.fill(x - 3, y - 3, x + w + 2, y + h - 1, wood[2])
    f.fill(x - 3, y - 3, x + w + 2, y - 3, wood[4])
    f.fill(x - 3, y - 3, x - 3, y + h - 1, wood[4])
    f.fill(x, y, x + w - 1, y + h - 1, pal['hole'])


def church(f: Frame, w: int, h: int, door: tuple, pal: dict) -> None:
    """White clapboard, a steeple over the door with its bell and cross, a
    round window, tall arched windows, steps."""
    b = h - 1
    dx, dy, dw, dh = door
    cx = dx + dw / 2
    body_top = dy - h // 6
    s_roof(f, cx, body_top - h // 5, w * 0.48, body_top, pal['wood'])
    s_planks(f, 2, body_top + 1, w - 3, b, pal['paint'], 61)
    s_planks(f, int(w * 0.72), body_top + 1, w - 3, b, pal['paint'], 62, shade=1)
    tw = max(8, int(w * 0.14))                               # The steeple, over the ridge
    t0 = int(cx - tw / 2)
    tower_top = max(tw // 2 + 6, body_top - h // 5 - 2)
    s_planks(f, t0, tower_top, t0 + tw - 1, body_top, pal['paint'], 63)
    f.fill(t0 + 2, tower_top + 2, t0 + tw - 3, tower_top + 2 + tw // 2, pal['hole'])   # Bell opening
    f.fill(int(cx) - 1, tower_top + 3, int(cx) + 1, tower_top + 1 + tw // 2, pal['brass'][1])
    s_roof(f, cx, max(5, tower_top - tw), tw / 2 + 2, tower_top - 1, pal['wood'])
    top = max(0, tower_top - tw - 1)                         # Cross
    f.fill(int(cx), top, int(cx), top + 5, pal['metal'][2])
    f.fill(int(cx) - 2, top + 1, int(cx) + 2, top + 1, pal['metal'][2])
    r = max(2, dw // 6)                                      # Round window over the door
    for yy in range(-r, r + 1):
        for xx in range(-r, r + 1):
            d = (xx * xx + yy * yy) ** 0.5
            if d <= r:
                f.px(int(cx) + xx, dy - r - 4 + yy, pal['glow'][1] if d < r - 1 else pal['wood'][4])
    ww = max(4, w // 14)
    for x0 in (int(w * 0.12), int(w * 0.82) - ww):
        s_window(f, x0, dy + 2, ww, dh // 2, pal, x0 < cx, arch=True)
    s_doorway(f, door, pal)
    for i in range(3):                                       # Steps
        f.fill(dx - 4 - i * 2, b - i, dx + dw + 3 + i * 2, b - i, pal['stone'][3 - i % 2])


def sheriff(f: Frame, w: int, h: int, door: tuple, pal: dict) -> None:
    """A brick-and-board office: a false front with the star on its sign,
    barred windows, a lantern by the door, a boardwalk."""
    b = h - 1
    dx, dy, dw, dh = door
    cx = dx + dw / 2
    front_top = max(2, dy - h // 3)
    s_stone(f, 3, front_top + 8, w - 4, b, pal['stone'])
    s_planks(f, 1, front_top, w - 2, front_top + 9, pal['wood'], 71)
    f.fill(1, front_top, w - 2, front_top, pal['wood'][5])
    sw = min(w - 8, dw * 2 + 8)                              # The sign and its star
    f.fill(int(cx - sw / 2), front_top - 6, int(cx + sw / 2), front_top + 1, pal['wood'][1])
    f.fill(int(cx - sw / 2) + 1, front_top - 5, int(cx + sw / 2) - 1, front_top, pal['wood'][3])
    for yy in range(-3, 4):
        for xx in range(-3, 4):
            if abs(xx) + abs(yy) <= 3 or (abs(xx) == abs(yy) and abs(xx) <= 2) or (yy == 1 and abs(xx) <= 3):
                f.px(int(cx) + xx, front_top - 2 + yy, pal['brass'][1] if xx <= 0 else pal['brass'][0])
    for x0 in range(int(cx - sw / 2) + 2, int(cx) - 5, 3):
        f.fill(x0, front_top - 3, x0 + 1, front_top - 2, pal['wood'][0])
    for x0 in range(int(cx) + 5, int(cx + sw / 2) - 2, 3):
        f.fill(x0, front_top - 3, x0 + 1, front_top - 2, pal['wood'][0])
    ww = max(5, w // 9)
    for x0 in (int(w * 0.1), int(w * 0.9) - ww):
        s_window(f, x0, dy + dh // 5, ww, max(5, dh // 3), pal, False, bars=True)
    s_doorway(f, door, pal)
    lx = dx + dw + 5                                          # Lantern
    f.fill(lx, dy + 4, lx + 2, dy + 8, pal['glow'][2])
    f.fill(lx, dy + 3, lx + 2, dy + 3, pal['metal'][1])
    f.fill(0, b - 1, w - 1, b, pal['wood'][2])                # Boardwalk
    for x0 in range(0, w, 5):
        f.px(x0, b - 1, pal['wood'][0])


def blacksmith(f: Frame, w: int, h: int, door: tuple, pal: dict) -> None:
    """A smithy: a stone chimney glowing at its foot, a lean-to with the anvil
    and the forge's light, a horseshoe sign, a heavy plank front."""
    b = h - 1
    dx, dy, dw, dh = door
    cx = dx + dw / 2
    body_top = max(10, dy - h // 5)
    s_roof(f, cx, body_top - h // 6, w * 0.4, body_top, pal['wood'])
    ch = int(w * 0.8)                                         # Chimney
    s_stone(f, ch, max(0, body_top - h // 3), ch + max(5, w // 12), b, pal['stone'])
    s_planks(f, int(w * 0.12), body_top + 1, int(w * 0.78), b, pal['wood'], 81)
    s_planks(f, int(w * 0.6), body_top + 1, int(w * 0.78), b, pal['wood'], 82, shade=1)
    lean = int(w * 0.12)                                      # The lean-to: anvil by the forge
    for x in range(0, lean + 1):
        f.px(x, body_top + 6 + (lean - x) // 3, pal['wood'][4])
    f.fill(1, body_top + 8, 1, b, pal['wood'][2])
    f.fill(2, b - 4, lean - 1, b, pal['glow'][0])
    f.fill(3, b - 6, lean - 3, b - 5, pal['metal'][1])
    f.fill(4, b - 4, lean - 4, b - 1, pal['metal'][0])
    f.fill(ch + 1, b - 4, ch + max(3, w // 12) - 1, b - 1, pal['glow'][1])   # Forge mouth
    hx, hy = int(cx), body_top + 3                            # Horseshoe sign
    for t in range(-3, 4):
        f.px(hx + t, hy + 4 - (3 - abs(t)) // 2 - (0 if abs(t) < 3 else 2), pal['metal'][2])
    f.fill(hx - 3, hy, hx - 3, hy + 2, pal['metal'][2])
    f.fill(hx + 3, hy, hx + 3, hy + 2, pal['metal'][2])
    ww = max(5, w // 10)
    s_window(f, int(w * 0.62), dy + dh // 5, ww, max(5, dh // 3), pal, True)
    s_doorway(f, door, pal)


def stable(f: Frame, w: int, h: int, door: tuple, pal: dict) -> None:
    """A long stable: a wide gable with the hay loft open, a horseshoe over
    the door, stall half-doors either side, a trough."""
    b = h - 1
    dx, dy, dw, dh = door
    cx = dx + dw / 2
    body_top = max(12, dy - h // 6)
    s_roof(f, cx, max(2, body_top - h // 3), w * 0.5, body_top, pal['wood'])
    s_planks(f, 2, body_top + 1, w - 3, b, pal['wood'], 91)
    s_planks(f, int(w * 0.7), body_top + 1, w - 3, b, pal['wood'], 92, shade=1)
    lw = max(6, dw // 2)                                       # Hay loft
    ly = max(4, body_top - h // 6)
    f.fill(int(cx - lw / 2), ly, int(cx + lw / 2), ly + lw // 2 + 2, pal['wood'][4])
    f.fill(int(cx - lw / 2) + 1, ly + 1, int(cx + lw / 2) - 1, ly + lw // 2 + 1, pal['hole'])
    for x in range(int(cx - lw / 2) + 1, int(cx + lw / 2), 2):
        f.px(x, ly + lw // 2 + 1, pal['glow'][0])
    for t in range(-2, 3):                                     # Horseshoe over the door
        f.px(int(cx) + t, dy - 6 + abs(t) // 2, pal['metal'][2])
    sw = max(6, w // 9)
    for x0 in (int(w * 0.08), int(w * 0.92) - sw):             # Stall half-doors
        f.fill(x0, dy + dh // 3, x0 + sw, b, pal['wood'][4])
        f.fill(x0 + 1, dy + dh // 3 + 1, x0 + sw - 1, dy + dh // 2, pal['hole'])
        for t in range(0, sw - 1):
            f.px(x0 + 1 + t, dy + dh // 2 + 1 + t * (b - dy - dh // 2 - 2) // max(1, sw - 2), pal['wood'][5])
    s_doorway(f, door, pal)
    tx = dx + dw + 4                                           # Trough
    f.fill(tx, b - 3, min(w - 2, tx + dw // 2), b, pal['wood'][2])
    f.fill(tx + 1, b - 3, min(w - 2, tx + dw // 2) - 1, b - 3, pal['metal'][1])


def bank(f: Frame, w: int, h: int, door: tuple, pal: dict) -> None:
    """The bank: a stone front with a cornice and a pediment, two columns
    either side of the door, a gilded coin on the sign, tall barred windows
    and stone steps."""
    b = h - 1
    dx, dy, dw, dh = door
    cx = dx + dw / 2
    body_top = max(14, dy - h // 4)
    s_stone(f, 2, body_top, w - 3, b, pal['stone'])
    s_roof(f, cx, max(2, body_top - h // 7), w * 0.3, body_top - 3, pal['stone'])   # Pediment
    f.fill(1, body_top - 3, w - 2, body_top - 1, pal['stone'][4])   # Cornice
    f.fill(1, body_top - 1, w - 2, body_top - 1, pal['stone'][1])
    r = max(2, dw // 5)                                      # The gilded coin in the pediment
    for yy in range(-r, r + 1):
        for xx in range(-r, r + 1):
            if xx * xx + yy * yy <= r * r:
                f.px(int(cx) + xx, body_top - 4 - r + yy, pal['brass'][1] if xx < 0 else pal['brass'][0])
    cw = max(3, dw // 6)                                     # Columns by the door
    for x0 in (dx - 6 - cw, dx + dw + 5):
        f.fill(x0 - 1, body_top + 1, x0 + cw, body_top + 2, pal['stone'][4])
        for x in range(x0, x0 + cw):
            f.fill(x, body_top + 3, x, b - 2, pal['stone'][4 if x == x0 else 3 if x < x0 + cw - 1 else 1])
        f.fill(x0 - 1, b - 2, x0 + cw, b - 1, pal['stone'][2])
    ww = max(5, w // 10)
    for x0 in (int(w * 0.08), int(w * 0.92) - ww):
        s_window(f, x0, body_top + 4, ww, max(6, (b - body_top) // 2), pal, x0 < cx, bars=True, arch=True)
    s_doorway(f, door, pal)
    for i in range(3):                                       # Stone steps
        f.fill(dx - 4 - i * 3, b - i, dx + dw + 3 + i * 3, b - i, pal['stone'][4 - i % 2])


STRUCTURES = [church, sheriff, blacksmith, stable, bank]

# A wall that is a building's front: the road runs through its door.
FACADE_W, FACADE_H = 180, 128
DOOR_W, DOOR_H = 44, 64


def make_facades() -> Image:
    """The fronts of the five structures (5 frames of 180 x 128), their
    doorway over the road in the middle, DOOR_W x DOOR_H on the ground."""
    img = Image(FACADE_W * len(STRUCTURES), FACADE_H)
    door = ((FACADE_W - DOOR_W) // 2, FACADE_H - DOOR_H, DOOR_W, DOOR_H)
    for i, draw in enumerate(STRUCTURES):
        f = Frame(img, i * FACADE_W, FACADE_W)
        draw(f, FACADE_W, FACADE_H, door, ROAD_PAL)
        f.outline()
    return img


def make_door() -> Image:
    """The door in a building's doorway (3 frames of 44 x 64): heavy planks
    with iron straps, barred with a beam and a padlock; split by claws or a
    shot of dynamite starting; blown: splinters hanging off the hinges."""
    w, h = DOOR_W, DOOR_H
    img = Image(w * 3, h)
    for frame in range(3):
        f = Frame(img, frame * w, w)
        if frame < 2:
            s_planks(f, 1, 1, w - 2, h - 1, ROAD_PAL['wood'], 101)
            for y0 in (8, h - 12):                           # Iron straps, rivets
                f.fill(1, y0, w - 2, y0 + 2, IRON[2])
                for x in range(3, w - 2, 6):
                    f.px(x, y0 + 1, IRON[4])
            f.box(0, h // 2 - 3, w - 1, h // 2 + 2, WOOD)    # The bar across
            f.fill(w // 2 - 3, h // 2 + 3, w // 2 + 2, h // 2 + 9, BRASS[1])   # Padlock
            f.fill(w // 2 - 2, h // 2 + 1, w // 2 + 1, h // 2 + 2, IRON[3])
            f.px(w // 2 - 1, h // 2 + 6, OUTLINE)
            if frame == 1:
                for y in range(4, h - 4):                    # Split boards, a gap
                    f.px(14 + (y // 7) % 2, y, OUTLINE)
                for y in range(10, h // 2 - 4):
                    f.px(30, y, (0, 0, 0, 0))
                    f.px(31, y, (0, 0, 0, 0))
        else:
            for side, x0 in ((0, 0), (1, w - 9)):           # Splinters on the hinges
                for i in range(4):
                    top = 4 + i * 15
                    length = 6 + (i * 5 + side * 3) % 8
                    s_planks(f, x0, top, x0 + 8, min(h - 1, top + length), ROAD_PAL['wood'], 111 + i)
                    for x in range(x0, x0 + 9):
                        if (x + i) % 2:
                            f.px(x, min(h - 1, top + length), (0, 0, 0, 0))
            for i in range(5):                               # Planks on the ground
                f.fill(4 + i * 7, h - 3 - i % 2, 9 + i * 7, h - 1, WOOD[2 + i % 2])
        f.outline()
    return img


def make_town_houses() -> Image:
    """The five structures far off, for the background strip (80 x 64,
    props' colors), appended to the houses."""
    img = Image(80 * len(STRUCTURES), 64)
    for i, draw in enumerate(STRUCTURES):
        f = Frame(img, i * 80, 80)
        draw(f, 80, 64, (34, 40, 12, 24), BG_PAL)
        f.outline()
    return img



# --- Off-road only: more houses for the background strip -----------------------

def general_store(f: Frame, w: int, h: int, pal: dict) -> None:
    """A two-storey store: a false front with its sign, an awning over the
    shop window, an upstairs with two windows, barrels by the door."""
    b = h - 1
    s_planks(f, 8, 6, w - 9, b, pal['wood'], 121)
    s_planks(f, int(w * 0.62), 6, w - 9, b, pal['wood'], 122, shade=1)
    f.fill(6, 2, w - 7, 6, pal['wood'][4])                   # False front, its sign
    f.fill(18, 3, w - 19, 5, pal['wood'][1])
    for x in range(20, w - 20, 4):
        f.fill(x, 4, x + 1, 4, pal['wood'][5])
    for x0 in (16, w - 26):                                  # Upstairs windows
        s_window(f, x0, 12, 9, 10, pal, x0 < w // 2)
    f.fill(4, 28, w - 5, 31, pal['wood'][5])                 # Awning, striped
    for x in range(4, w - 4, 4):
        f.fill(x, 32, x + 1, 33, pal['paint'][3])
    s_window(f, 12, 38, 22, 14, pal, True)                   # Shop window
    f.fill(46, 38, 57, b, pal['wood'][4])                    # Door
    f.fill(48, 40, 55, 50, pal['hole'])
    for x0 in (60, 67):                                      # Barrels
        f.box(x0, b - 7, x0 + 5, b, pal['wood'][1:5])
        f.fill(x0, b - 5, x0 + 5, b - 5, pal['metal'][1])
    f.fill(0, b - 1, w - 1, b, pal['wood'][2])               # Boardwalk


def adobe(f: Frame, w: int, h: int, pal: dict) -> None:
    """A low adobe house: thick rounded walls, a flat roof with the beam
    ends sticking out, a small deep window, a ladder to the roof and a
    string of chilies by the door."""
    b = h - 1
    top = 26
    for y in range(top, b + 1):                              # Walls, corners rounded
        inset = 2 if y == top else 1 if y == top + 1 else 0
        for x in range(10 + inset, w - 10 - inset):
            c = pal['paint'][3] if x < w * 0.66 else pal['paint'][1]
            if (x * 5 + y * 3) % 23 == 0:
                c = pal['paint'][2]
            f.px(x, y, c)
    f.fill(12, top - 3, w - 13, top - 1, pal['paint'][2])    # Parapet
    for x in range(16, w - 14, 8):                           # Beam ends
        f.fill(x, top + 3, x + 2, top + 4, pal['wood'][1])
    f.fill(26, 38, 37, b, pal['wood'][3])                    # Door, chilies by it
    f.fill(28, 40, 35, 52, pal['wood'][1])
    for y in range(36, 48, 2):
        f.px(40, y, pal['glow'][0])
    s_window(f, 50, 38, 8, 7, pal, True)
    for y in range(top - 10, b, 3):                          # Ladder to the roof
        f.fill(64, y, 69, y, pal['wood'][4])
    f.fill(64, top - 10, 64, b, pal['wood'][2])
    f.fill(69, top - 10, 69, b, pal['wood'][2])


def fallen_silo(f: Frame, w: int, h: int, pal: dict) -> None:
    """A grain silo fallen over: the tin drum lying on its side, ribbed and
    rusted, its dome cap rolled off beside it, the stub of its base and a
    spill of grain."""
    b = h - 1
    m = pal['metal']
    f.fill(4, b - 10, 13, b, m[1])                           # The stub still standing
    for x in range(4, 14, 3):
        f.fill(x, b - 10, x, b, m[0])
    for x in range(4, 14):
        if x % 3:
            f.px(x, b - 11 + (x * 7) % 3, m[2])              # Its torn top edge
    cy, r = b - 13, 13                                       # The drum, lying down
    for x in range(16, w - 14):
        for y in range(cy - r, cy + r + 1):
            d = abs(y - cy) / r
            c = m[2] if y < cy - r // 2 else m[1] if y < cy + r // 2 else m[0]
            if (x - 16) % 6 == 0:
                c = m[0]                                     # Ribs
            if d > 0.92:
                c = m[0]
            if (x * 3 + y * 5) % 17 == 0:
                c = pal['wood'][2]                           # Rust
            f.px(x, y, c)
    for y in range(cy - r + 3, cy + r - 2):                  # The open end, dark inside
        half = int((r * r - (y - cy) ** 2) ** 0.5 * 0.35)
        f.fill(w - 14, y, w - 14 + half, y, pal['hole'])
    for i in range(10):                                      # Its dome cap, rolled off
        for x in range(w - 11 + i // 3, w - 2 - i // 3):
            f.px(x, b - i, m[2] if i > 6 else m[1])
    for x in range(14, 40):                                  # Spilled grain
        f.px(x, b, pal['glow'][0] if x % 2 else pal['paint'][3])
        if 20 < x < 34:
            f.px(x, b - 1, pal['glow'][0])


def make_more_houses() -> Image:
    """The background-only houses (80 x 64, props' colors), appended last."""
    draws = [general_store, adobe, fallen_silo]
    img = Image(80 * len(draws), 64)
    for i, draw in enumerate(draws):
        f = Frame(img, i * 80, 80)
        draw(f, 80, 64, BG_PAL)
        f.outline()
    return img


def join(a: Image, b: Image) -> Image:
    """Two sheets of the same height side by side."""
    out = Image(a.width + b.width, a.height)
    for y in range(a.height):
        for x in range(a.width):
            out.set(x, y, a.get(x, y))
        for x in range(b.width):
            out.set(a.width + x, y, b.get(x, y))
    return out


def make_blood() -> Image:
    """Drops of blood on the road, her trail while she bleeds (4 frames of
    8 x 4, resting on the ground): splats of dark red with a wet glint."""
    blood = [rgb(0x4a0c0c), rgb(0x7a1414), rgb(0xa82020), rgb(0xd84848)]
    shapes = [
        ['..1221..', '.122221.', '..1111..', '........'],
        ['...12...', '.12221..', '1222321.', '.11111..'],
        ['.1......', '.21.121.', '..1.2321', '.....11.'],
        ['..121...', '.12321..', '..1221..', '...1....'],
    ]
    img = Image(8 * 4, 4)
    for f, rows in enumerate(shapes):
        for y, row in enumerate(rows):
            for x, k in enumerate(row):
                if k != '.':
                    img.set(f * 8 + x, y, blood[int(k) - 1] if k != '3' else blood[3])
    return img


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'assets'
    out = {
        'sprites/terrain/barricade.png': make_barricade(),
        'sprites/terrain/barrel.png': make_barrel(),
        'sprites/terrain/wall.png': make_wall(),
        'sprites/terrain/wall_ruins.png': make_wall_ruins(),
        'sprites/props/houses.png': join(join(make_houses(), make_town_houses()), make_more_houses()),
        'sprites/terrain/facades.png': make_facades(),
        'sprites/terrain/door.png': make_door(),
        'sprites/terrain/dynamite.png': make_dynamite(),
        'sprites/terrain/charge.png': make_charge(),
        'sprites/terrain/crate.png': make_crate(),
        'sprites/terrain/wire.png': make_wire(),
        'sprites/terrain/net.png': make_net(),
        'sprites/terrain/snare.png': make_snare(),
        'sprites/terrain/spikes.png': make_spikes(),
        'sprites/effects/net_bag.png': make_net_bag(),
        'sprites/crow/crow.png': make_crow(),
        'sprites/bat/bat.png': make_bat(),
        'sprites/terrain/river.png': make_river(),
        'sprites/terrain/river_front.png': make_river_front(),
        'sprites/terrain/puddle.png': make_puddle(),
        'sprites/terrain/sign.png': make_sign(),
        'sprites/effects/splash.png': make_splash(),
        'sprites/effects/tumbleweed.png': make_tumbleweed(),
        'sprites/terrain/bottles.png': make_bottles(),
        'sprites/terrain/trap.png': make_trap(),
        'sprites/terrain/coffin.png': make_coffin(),
        'sprites/terrain/lamp.png': make_lamp(),
        'sprites/terrain/fire.png': make_fire(),
        'sprites/terrain/bench.png': make_bench(),
        'sprites/terrain/campfire.png': make_campfire(),
        'sprites/effects/heal.png': make_heal(),
        'sprites/effects/glow.png': make_glow(),
        'sprites/terrain/supply.png': make_supply(),
        'sprites/terrain/goal.png': make_goal(),
        'sprites/effects/explosion.png': make_explosion(),
        'sprites/effects/blood.png': make_blood(),
    }
    for name, img in out.items():
        path = assets / name
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        print(f'make_terrain: {name} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
