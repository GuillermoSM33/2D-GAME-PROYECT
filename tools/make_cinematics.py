#!/usr/bin/env python3
"""Make the art of the opening cinematic (docs/LORE.md, "La filtración").

Usage: tools/make_cinematics.py [assets_dir]   (default: assets)

Writes:
  cinematics/lab/corridor.png   Laboratorio 4's corridor at night, wider than
                                the window so the camera can pan (480 x 180)
  cinematics/lab/monitors.png   The desk where an AI designs The Miracle: three
                                monitors (DNA, a neural network, sequences),
                                6 frames of 320 x 180, looped
  cinematics/lab/alarm.png      Close-up of a monitor gone red: MRC-1 dividing
                                and mutating, 8 frames of 320 x 180, played once
  sprites/mercenary/walk.png    A mercenary in silhouette walking with his rifle
                                and flashlight (12 frames of 81 x 80, the SWAT's
                                light_walk body, so the same scale and pivot)
  sprites/mercenary/aim.png     The first of them facing her camera, rifle at it:
                                aiming (2 frames), the shot with its flash, the
                                recoil settling (4 frames of 110 x 130, waist up)
  sprites/vial/held.png         Valeria's fist raising the sample against a
                                flashlight, seen from her camera (64 x 100)
  sprites/ambulance/drive.png   The ambulance driving right, wheels turning and
                                lights flashing (4 frames of 72 x 34)

The cinematic images are whole screens at the world's pixel size: one art px
is 3 window px (the window is 320 x 180 art px). The lab is cool and dark, the
opposite of the warm desert outside. No dithering, light from the top left
(the flashlights from the right in their scenes). Deterministic; uses only the
standard library.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CLEAR = (0, 0, 0, 0)

INK = rgb(0x07080a)
LAB = [rgb(0x0e1115), rgb(0x14181d), rgb(0x1b2026), rgb(0x242a32), rgb(0x323a45), rgb(0x4a5562)]
TEAL = [rgb(0x0c2222), rgb(0x123636), rgb(0x1c5250), rgb(0x2f7a72), rgb(0x6cc4b4)]
SCREEN = [rgb(0x08201a), rgb(0x0f3a2e), rgb(0x1e6a50), rgb(0x48b088), rgb(0xa8ecc8)]
RED = [rgb(0x1c0505), rgb(0x3a0a08), rgb(0x66140f), rgb(0xa8281a), rgb(0xe8573a), rgb(0xffb08a)]
AMBER = [rgb(0x5a4216), rgb(0x8e6c28), rgb(0xc89a3e), rgb(0xf0cc72)]
VIAL = [rgb(0x0f3a22), rgb(0x1f7a3e), rgb(0x46c060), rgb(0x9cf08a), rgb(0xe4ffd0)]
GLASS = [rgb(0x283038), rgb(0x56626e), rgb(0x9aa8b4), rgb(0xdce6ee)]
RIM = rgb(0x8c96a2)            # A flashlight catching an edge
SKIN_SHADE = [rgb(0x0c0a0a), rgb(0x171313), rgb(0x251e1c)]  # A backlit hand: nearly black
VAN = [rgb(0x5a5048), rgb(0x8a7e70), rgb(0xb8aa94), rgb(0xe0d2b8), rgb(0xf6ead2)]  # White at sunset
STRIPE = [rgb(0x5a1410), rgb(0x902004), rgb(0xc03a14)]
TYRE = [rgb(0x161412), rgb(0x2a2622), rgb(0x46403a), rgb(0x7a7068)]
WINDOW = [rgb(0x1a1c22), rgb(0x2c3038), rgb(0x56606a), rgb(0xa8b0b4)]
SIREN_RED = [rgb(0x5a1410), rgb(0xd83a1c), rgb(0xffb07a)]
SIREN_BLUE = [rgb(0x142a5a), rgb(0x2e64d8), rgb(0x9cc4ff)]

# 3 x 5 glyphs for the few labels on the screens.
GLYPHS = {
    'M': ['#.#', '###', '###', '#.#', '#.#'], 'R': ['##.', '#.#', '##.', '#.#', '#.#'],
    'C': ['.##', '#..', '#..', '#..', '.##'], '-': ['...', '...', '###', '...', '...'],
    '1': ['.#.', '##.', '.#.', '.#.', '###'], '2': ['##.', '..#', '.#.', '#..', '###'],
    '4': ['#.#', '#.#', '###', '..#', '..#'], 'A': ['.#.', '#.#', '###', '#.#', '#.#'],
    'L': ['#..', '#..', '#..', '#..', '###'], 'E': ['###', '#..', '##.', '#..', '###'],
    'T': ['###', '.#.', '.#.', '.#.', '.#.'], 'I': ['###', '.#.', '.#.', '.#.', '###'],
    'G': ['.##', '#..', '#.#', '#.#', '.##'], 'N': ['#.#', '###', '###', '###', '#.#'],
    'S': ['.##', '#..', '.#.', '..#', '##.'], 'O': ['.#.', '#.#', '#.#', '#.#', '.#.'],
    'D': ['##.', '#.#', '#.#', '#.#', '##.'], '!': ['.#.', '.#.', '.#.', '...', '.#.'],
    '%': ['#.#', '..#', '.#.', '#..', '#.#'], '0': ['###', '#.#', '#.#', '#.#', '###'],
    '7': ['###', '..#', '.#.', '.#.', '.#.'], '3': ['##.', '..#', '.#.', '..#', '##.'],
    '5': ['###', '#..', '##.', '..#', '##.'], '6': ['.##', '#..', '###', '#.#', '###'],
    '8': ['###', '#.#', '###', '#.#', '###'], '9': ['###', '#.#', '###', '..#', '##.'], ' ': ['...', '...', '...', '...', '...'],
}


class Canvas:
    """One frame of a sheet: drawing clipped to (ox, 0, w, h)."""

    def __init__(self, img: Image, ox: int = 0, w: int | None = None) -> None:
        self.img, self.ox = img, ox
        self.w = img.width if w is None else w
        self.h = img.height

    def px(self, x: int, y: int, c) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img.set(self.ox + x, y, c)

    def get(self, x: int, y: int):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.img.get(self.ox + x, y)
        return CLEAR

    def fill(self, x0: int, y0: int, x1: int, y1: int, c) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def hline(self, x0: int, x1: int, y: int, c) -> None:
        self.fill(x0, y, x1, y, c)

    def vline(self, x: int, y0: int, y1: int, c) -> None:
        self.fill(x, y0, x, y1, c)

    def frame(self, x0: int, y0: int, x1: int, y1: int, light, dark) -> None:
        """A bevel: lit top/left edges, dark bottom/right."""
        self.hline(x0, x1, y0, light)
        self.vline(x0, y0, y1, light)
        self.hline(x0, x1, y1, dark)
        self.vline(x1, y0, y1, dark)

    def text(self, x: int, y: int, s: str, c) -> int:
        for ch in s:
            rows = GLYPHS[ch]
            for j, row in enumerate(rows):
                for i, bit in enumerate(row):
                    if bit == '#':
                        self.px(x + i, y + j, c)
            x += 4
        return x

    def disc(self, cx: float, cy: float, rx: float, ry: float, c) -> None:
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.px(x, y, c)


def lcg(seed: int):
    state = seed & 0x7fffffff
    while True:
        state = (state * 1103515245 + 12345) & 0x7fffffff
        yield state


# --- Laboratorio 4: the corridor ----------------------------------------------

CORRIDOR_W, SCREEN_W, SCREEN_H = 480, 320, 180
CEILING, WALL_TOP, RAIL, WALL_BOTTOM, FLOOR = 18, 22, 104, 129, 130


def corridor_door(c: Canvas, x: int) -> None:
    top = 46
    c.fill(x, top, x + 33, WALL_BOTTOM, LAB[0])             # The recess
    c.frame(x, top, x + 33, WALL_BOTTOM, LAB[4], LAB[0])    # The jamb
    c.fill(x + 3, top + 3, x + 30, WALL_BOTTOM, LAB[2])     # The door leaf
    c.vline(x + 3, top + 3, WALL_BOTTOM, LAB[3])
    c.vline(x + 30, top + 3, WALL_BOTTOM, LAB[1])
    c.fill(x + 10, top + 10, x + 23, top + 27, TEAL[0])     # Its window, a dim room behind
    c.frame(x + 10, top + 10, x + 23, top + 27, LAB[1], LAB[4])
    for k in range(10):                                      # A reflection across it
        c.px(x + 12 + k, top + 24 - k, TEAL[1])
        if k < 6:
            c.px(x + 12 + k, top + 20 - k, TEAL[2])
    c.fill(x + 25, top + 44, x + 27, top + 45, AMBER[1])     # The handle
    c.px(x + 25, top + 44, AMBER[3])
    c.fill(x + 5, top + 58, x + 28, top + 59, LAB[3])        # Kick plate
    c.fill(x + 10, top - 9, x + 23, top - 3, LAB[4])         # Its number plate: 4
    c.frame(x + 10, top - 9, x + 23, top - 3, LAB[5], LAB[2])
    c.text(x + 15, top - 8, '4', INK)


def corridor_vitrine(c: Canvas, x0: int, x1: int, seed: int) -> None:
    top, bottom = 50, 98
    c.fill(x0, top, x1, bottom, LAB[3])
    c.frame(x0, top, x1, bottom, LAB[5], LAB[1])
    c.fill(x0 + 3, top + 3, x1 - 3, bottom - 3, LAB[0])      # The glass, dark inside
    shelves = (top + 17, top + 32, bottom - 4)
    rnd = lcg(seed)
    liquids = [VIAL[2], AMBER[2], RED[3], TEAL[3], VIAL[1]]
    for s in shelves:
        c.hline(x0 + 3, x1 - 3, s, LAB[4])
        c.hline(x0 + 3, x1 - 3, s + 1, LAB[2])
        x = x0 + 6
        while x < x1 - 8:
            tall = 6 + next(rnd) % 6
            liquid = liquids[next(rnd) % len(liquids)]
            c.fill(x, s - tall, x + 2, s - 1, GLASS[0])      # A tube
            c.fill(x, s - tall // 2, x + 2, s - 1, liquid)    # Its liquid
            c.px(x, s - tall // 2, GLASS[2])                  # The meniscus catching light
            c.hline(x, x + 2, s - tall - 1, LAB[5])           # Its cap
            x += 5 + next(rnd) % 4
    for k in (12, 16, 58):                                    # Two streaks of reflection on the glass
        for j in range(bottom - top - 7):
            xx = x0 + k + j // 2
            if x0 + 3 < xx < x1 - 3 and c.get(xx, bottom - 4 - j) == LAB[0]:
                c.px(xx, bottom - 4 - j, LAB[2])


def make_corridor() -> Image:
    img = Image(CORRIDOR_W, SCREEN_H)
    c = Canvas(img)
    c.fill(0, 0, CORRIDOR_W - 1, CEILING, LAB[0])             # Ceiling
    c.hline(0, CORRIDOR_W - 1, CEILING + 1, LAB[2])
    c.hline(0, CORRIDOR_W - 1, CEILING + 2, LAB[3])
    c.fill(0, CEILING + 3, CORRIDOR_W - 1, WALL_TOP - 1, LAB[1])
    for x in range(30, CORRIDOR_W, 120):                      # Ceiling lights, off
        c.fill(x, CEILING - 4, x + 39, CEILING - 1, LAB[3])
        c.hline(x, x + 39, CEILING - 4, LAB[4])
        for k in range(x + 2, x + 38, 4):
            c.vline(k, CEILING - 3, CEILING - 1, LAB[2])
    c.fill(0, WALL_TOP, CORRIDOR_W - 1, RAIL - 1, LAB[1])     # Upper wall
    c.hline(0, CORRIDOR_W - 1, 62, LAB[0])
    c.hline(0, CORRIDOR_W - 1, 63, LAB[2])
    for x in range(0, CORRIDOR_W, 48):                        # Panel seams
        c.vline(x, WALL_TOP, WALL_BOTTOM, LAB[0])
        c.vline(x + 1, WALL_TOP, WALL_BOTTOM, LAB[2])
        c.px(x + 4, WALL_TOP + 3, LAB[3])                     # Screws
        c.px(x + 4, RAIL - 4, LAB[3])
    c.hline(0, CORRIDOR_W - 1, RAIL, TEAL[3])                 # The lab's teal band
    c.fill(0, RAIL + 1, CORRIDOR_W - 1, RAIL + 2, TEAL[1])
    c.hline(0, CORRIDOR_W - 1, RAIL + 3, LAB[0])
    c.fill(0, RAIL + 4, CORRIDOR_W - 1, WALL_BOTTOM - 2, LAB[2])  # Lower wall, kick panels
    c.hline(0, CORRIDOR_W - 1, RAIL + 4, LAB[3])
    c.fill(0, WALL_BOTTOM - 1, CORRIDOR_W - 1, WALL_BOTTOM, LAB[0])  # Skirting
    corridor_door(c, 92)
    corridor_vitrine(c, 150, 252, 7)
    corridor_door(c, 300)
    corridor_vitrine(c, 352, 444, 19)
    # A warning plate between them and an emergency light above
    c.fill(268, 70, 284, 84, AMBER[2])
    c.frame(268, 70, 284, 84, AMBER[3], AMBER[0])
    for j in range(9):                                        # A black triangle with a '!'
        half = j * 6 // 8
        c.hline(276 - half, 276 + half, 73 + j, INK)
        if 2 <= j <= 7:
            c.hline(276 - half + 1, 276 + half - 1, 73 + j, AMBER[3])
    c.vline(276, 76, 78, INK)
    c.px(276, 80, INK)
    for ex in (60, 236, 420):
        c.fill(ex, WALL_TOP + 2, ex + 5, WALL_TOP + 4, RED[3])
        c.hline(ex + 1, ex + 4, WALL_TOP + 2, RED[5])
        c.hline(ex - 1, ex + 6, WALL_TOP + 5, RED[1])          # Its red spill on the wall
        c.hline(ex, ex + 5, WALL_TOP + 6, RED[0])
    # Floor: polished, catching the doors' and lights' reflections
    c.fill(0, FLOOR, CORRIDOR_W - 1, SCREEN_H - 1, LAB[1])
    c.hline(0, CORRIDOR_W - 1, FLOOR, LAB[3])
    for y, col in ((136, LAB[0]), (146, LAB[0]), (160, LAB[0]), (176, LAB[0])):
        c.hline(0, CORRIDOR_W - 1, y, col)
    for x in range(30, CORRIDOR_W, 120):                      # Lamp reflections, broken by the tiles
        for y in (139, 151, 166):
            half = 14 + (y - 139) // 3
            c.hline(x + 20 - half, x + 20 + half, y, LAB[2])
    for x in (92, 300):
        for y in range(FLOOR + 2, FLOOR + 14, 2):             # The doors' reflections
            c.hline(x + 3, x + 30, y, LAB[2])
    for ex in (60, 236, 420):
        c.hline(ex, ex + 5, 141, RED[1])
    return img


# --- The desk where the AI works -----------------------------------------------

MONITOR_FRAMES = 6
DESK_TOP = 146


def monitor_box(c: Canvas, x0: int, y0: int, w: int, h: int) -> tuple[int, int, int, int]:
    x1, y1 = x0 + w - 1, y0 + h - 1
    c.fill(x0, y0, x1, y1, LAB[1])
    c.frame(x0, y0, x1, y1, LAB[4], INK)
    c.frame(x0 + 1, y0 + 1, x1 - 1, y1 - 1, LAB[3], LAB[0])
    sx0, sy0, sx1, sy1 = x0 + 4, y0 + 4, x1 - 4, y1 - 4
    c.fill(sx0, sy0, sx1, sy1, SCREEN[0])
    cx = (x0 + x1) // 2
    c.fill(cx - 2, y1 + 1, cx + 2, DESK_TOP - 3, LAB[2])      # Neck and base
    c.vline(cx - 2, y1 + 1, DESK_TOP - 3, LAB[3])
    c.fill(cx - 12, DESK_TOP - 2, cx + 12, DESK_TOP - 1, LAB[3])
    c.hline(cx - 12, cx + 12, DESK_TOP - 2, LAB[4])
    return sx0, sy0, sx1, sy1


def draw_helix(c: Canvas, box, phase: float) -> None:
    sx0, sy0, sx1, sy1 = box
    cy = (sy0 + sy1) / 2
    amp = (sy1 - sy0) / 2 - 9
    for x in range(sx0 + 2, sx1 - 1):
        t = (x - sx0) * 0.105 + phase
        a, b = math.sin(t), math.sin(t + math.pi)
        front_a = math.cos(t) > 0
        ya, yb = round(cy + a * amp), round(cy + b * amp)
        if (x - sx0) % 5 == 0:                                # A rung between them
            for y in range(min(ya, yb) + 1, max(ya, yb)):
                c.px(x, y, SCREEN[1])
        c.px(x, ya, SCREEN[4] if front_a else SCREEN[2])
        c.px(x, yb, SCREEN[2] if front_a else SCREEN[4])
        if front_a:
            c.px(x, ya + 1, SCREEN[3])
        else:
            c.px(x, yb + 1, SCREEN[3])


NET_LAYERS = ((3,), (5,), (5,), (2,))


def draw_network(c: Canvas, box, frame: int) -> None:
    sx0, sy0, sx1, sy1 = box
    cols = [sx0 + 6 + i * (sx1 - sx0 - 12) // 3 for i in range(4)]
    nodes = []
    for i, (n,) in enumerate(NET_LAYERS):
        step = (sy1 - sy0 - 8) / (n - 1) if n > 1 else 0
        nodes.append([(cols[i], round(sy0 + 4 + j * step) if n > 1 else (sy0 + sy1) // 2)
                      for j in range(n)])
    lit_layer = frame % len(NET_LAYERS)
    for i in range(len(nodes) - 1):
        for a in nodes[i]:
            for b in nodes[i + 1]:
                steps = b[0] - a[0]
                if (a[1] + b[1]) % 3 == 1:
                    continue
                for k in range(0, steps, 3):
                    y = round(a[1] + (b[1] - a[1]) * k / steps)
                    c.px(a[0] + k, y, SCREEN[2] if i == lit_layer else SCREEN[1])
    for i, layer in enumerate(nodes):
        for (x, y) in layer:
            col = SCREEN[4] if i == lit_layer or i == (lit_layer + 1) % len(nodes) else SCREEN[3]
            c.fill(x - 1, y - 1, x + 1, y + 1, col)
            c.px(x - 1, y - 1, SCREEN[2])


def draw_sequence(c: Canvas, box, frame: int) -> None:
    sx0, sy0, sx1, sy1 = box
    rnd = lcg(31)
    rows = [[next(rnd) % 4 for _ in range(12)] for _ in range(20)]
    colors = (SCREEN[2], SCREEN[3], TEAL[3], AMBER[2])
    for r in range((sy1 - sy0 - 2) // 3):
        row = rows[(r + frame) % len(rows)]
        x = sx0 + 2
        for k, base in enumerate(row):
            w = 2 + (k + r) % 3
            if x + w > sx1 - 2:
                break
            c.hline(x, x + w - 1, sy0 + 2 + r * 3, colors[base])
            x += w + 1


def make_monitors() -> Image:
    img = Image(SCREEN_W * MONITOR_FRAMES, SCREEN_H)
    for f in range(MONITOR_FRAMES):
        c = Canvas(img, f * SCREEN_W, SCREEN_W)
        c.fill(0, 0, SCREEN_W - 1, SCREEN_H - 1, LAB[0])       # The dark room behind
        for x in range(0, SCREEN_W, 64):                       # Its wall's panel seams, barely there
            c.vline(x, 0, DESK_TOP - 1, LAB[1])
        c.fill(0, 118, SCREEN_W - 1, 119, TEAL[0])
        boxes = [monitor_box(c, 6, 66, 96, 62), monitor_box(c, 106, 40, 108, 82),
                 monitor_box(c, 218, 66, 96, 62)]
        draw_sequence(c, boxes[0], f)
        draw_helix(c, boxes[1], f * (2 * math.pi / MONITOR_FRAMES))
        draw_network(c, boxes[2], f)
        bx0, by0, bx1, _ = boxes[1]
        _, _, _, by1 = boxes[1]
        c.text(bx0 + 3, by1 - 7, 'MRC-1', SCREEN[3])           # The project's code on screen
        # The desk, lit by the screens
        c.fill(0, DESK_TOP, SCREEN_W - 1, DESK_TOP + 6, LAB[3])
        c.hline(0, SCREEN_W - 1, DESK_TOP, LAB[5])
        c.fill(0, DESK_TOP + 7, SCREEN_W - 1, SCREEN_H - 1, LAB[1])
        c.hline(0, SCREEN_W - 1, DESK_TOP + 7, INK)
        for (x0, _, x1, _) in boxes:
            c.hline(x0 - 2, x1 + 2, DESK_TOP + 1, SCREEN[1])   # The screens' glow on the desk
            c.hline(x0 + 4, x1 - 4, DESK_TOP + 2, SCREEN[1])
        c.fill(120, DESK_TOP + 2, 200, DESK_TOP + 5, LAB[2])   # The keyboard
        c.hline(120, 200, DESK_TOP + 2, LAB[4])
        for k in range(122, 199, 3):
            c.px(k, DESK_TOP + 3, LAB[4])
            c.px(k + 1, DESK_TOP + 4, LAB[4])
        c.fill(236, DESK_TOP + 1, 262, DESK_TOP + 4, GLASS[2])  # Papers
        c.hline(238, 258, DESK_TOP + 2, GLASS[1])
        c.fill(30, DESK_TOP - 9, 36, DESK_TOP - 1, GLASS[0])   # A mug
        c.frame(30, DESK_TOP - 9, 36, DESK_TOP - 1, GLASS[1], LAB[1])
        c.vline(37, DESK_TOP - 7, DESK_TOP - 4, GLASS[1])
    return img


# --- The alarm: MRC-1 under the microscope ------------------------------------

ALARM_FRAMES = 8


def cell(c: Canvas, cx: float, cy: float, rx: float, ry: float, spikes: int, frame: int) -> None:
    c.disc(cx, cy, rx + 1, ry + 1, RED[4])                    # Membrane
    c.disc(cx, cy, rx, ry, RED[2])
    c.disc(cx - rx * 0.25, cy - ry * 0.25, rx * 0.55, ry * 0.5, RED[3])
    c.disc(cx + rx * 0.15, cy + ry * 0.1, max(1.5, rx * 0.22), max(1.5, ry * 0.22), RED[5])  # Nucleus
    for k in range(spikes):                                    # Mutation: barbs pushing out
        a = k * 2 * math.pi / spikes + frame * 0.2
        for d in range(3):
            x = cx + math.cos(a) * (rx + 2 + d)
            y = cy + math.sin(a) * (ry + 2 + d)
            c.px(round(x), round(y), RED[4] if d < 2 else RED[5])


def make_alarm() -> Image:
    img = Image(SCREEN_W * ALARM_FRAMES, SCREEN_H)
    for f in range(ALARM_FRAMES):
        c = Canvas(img, f * SCREEN_W, SCREEN_W)
        c.fill(0, 0, SCREEN_W - 1, SCREEN_H - 1, LAB[1])       # The bezel fills the view
        c.frame(0, 0, SCREEN_W - 1, SCREEN_H - 1, LAB[3], INK)
        x0, y0, x1, y1 = 14, 12, SCREEN_W - 15, SCREEN_H - 13
        c.fill(x0, y0, x1, y1, RED[0])
        c.frame(x0 - 1, y0 - 1, x1 + 1, y1 + 1, INK, LAB[3])
        for y in range(y0, y1, 3):                             # Scanlines
            c.hline(x0, x1, y, RED[1])
        cx, cy, r = 160, 92, 56                                # The microscope's field
        c.disc(cx, cy, r + 2, r + 2, RED[3])
        c.disc(cx, cy, r, r, RED[1])
        for y in range(cy - r, cy + r, 3):
            for x in range(cx - r, cx + r):
                if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                    c.px(x, y, RED[0])
        # The cell divides and divides, then mutates
        if f == 0:
            cell(c, cx, cy, 14, 12, 0, f)
        elif f == 1:
            cell(c, cx, cy, 19, 11, 0, f)
        elif f == 2:
            cell(c, cx - 9, cy, 12, 11, 0, f)
            cell(c, cx + 9, cy, 12, 11, 0, f)
        elif f == 3:
            cell(c, cx - 14, cy, 12, 11, 0, f)
            cell(c, cx + 14, cy, 12, 11, 0, f)
        else:
            spikes = (f - 3) * 3
            size = 10 + (f - 4)
            for (dx, dy) in ((-16, -14), (16, -14), (-16, 14), (16, 14)):
                cell(c, cx + dx, cy + dy, size, size - 1, spikes, f)
            if f >= 6:
                for (dx, dy) in ((0, -34), (-34, 0), (34, 0), (0, 34)):
                    cell(c, cx + dx, cy + dy, size - 3, size - 4, spikes - 3, f)
        c.text(x0 + 6, y0 + 14, 'MRC-1', RED[4])           # Below the camera's REC
        if f % 2 == 0:                                         # A blinking warning
            c.fill(x1 - 22, y0 + 4, x1 - 6, y0 + 12, RED[4])
            c.text(x1 - 15, y0 + 6, '!', RED[0])
        # Mutation rate climbing on a graph in the corner
        gx0, gy1 = x0 + 6, y1 - 6
        c.hline(gx0, gx0 + 50, gy1, RED[3])
        c.vline(gx0, gy1 - 30, gy1, RED[3])
        top = 4 + f * 3
        for k in range(48):
            y = gy1 - 1 - round((k / 47) ** 2.2 * top)
            c.px(gx0 + 2 + k, y, RED[5] if k > 40 else RED[4])
        pct = str(min(99, 12 + f * 12)) + '%'
        c.text(gx0 + 54, gy1 - 6, pct, RED[4])
    return img


# --- Mercenaries in silhouette --------------------------------------------------

MERC_FRAME_W, MERC_FRAME_H = 81, 80


def make_mercenary(assets: Path) -> Image:
    w, h, raw = decode_png_rgba(assets / 'sprites/characters/swat/light_walk.png')
    img = Image(w, h)
    solid = set()
    lum = {}
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            r, g, b, a = raw[i:i + 4]
            if a > 0:
                solid.add((x, y))
                lum[(x, y)] = 0.3 * r + 0.59 * g + 0.11 * b
    for (x, y) in solid:
        # Four cloth planes retain the anonymous silhouette and the equipment.
        value = lum[(x, y)]
        img.set(x, y, LAB[3] if value > 145 else LAB[2] if value > 95 else LAB[1] if value > 50 else INK)
    for (x, y) in solid:
        # A cold rim on his top and back edges from the emergency lights.
        if (x, y - 1) not in solid or ((x - 1, y) not in solid and (x, y - 2) not in solid):
            img.set(x, y, LAB[5] if (x, y - 1) not in solid else LAB[4])
        # The flashlight's lens: bright pixels out on the gun, past his face
        if lum[(x, y)] > 150 and x % MERC_FRAME_W > 52:
            img.set(x, y, GLASS[3])
    from support_finishes import finish_mercenary
    return finish_mercenary(img, MERC_FRAME_W, LAB, GUN, GLASS, TEAL, INK, RIM)


# --- The mercenary facing her camera, firing -----------------------------------

FRONT_W, FRONT_H, FRONT_FRAMES = 110, 130, 4
FRONT_LENS = (67, 81)       # The flashlight's lens under his rifle, at rest (frame 0)
FRONT_MUZZLE = (54, 72)     # The rifle's bore, at rest
GUN = [rgb(0x14171b), rgb(0x22272e), rgb(0x343b44), rgb(0x4e5864), rgb(0x76828e)]  # Gunmetal, a step lighter than him
GLOVE = [rgb(0x0b0a09), rgb(0x16130f), rgb(0x24201a)]


def poly(c: Canvas, pts: list[tuple[float, float]], col) -> None:
    """A filled polygon, by scanlines through pixel centers."""
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        yc = y + 0.5
        xs = []
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            for x in range(int(round(xs[k])), int(round(xs[k + 1]))):
                c.px(x, y, col)


def front_body(c: Canvas, lift: int, breathe: int) -> None:
    """Waist up, facing her camera, the rifle at his right shoulder pointed at
    it, turned a little so its side shows. Backlit: a dark mass whose form
    is in its values, not in outlines; the rifle a step lighter so it reads."""
    d = -lift          # The recoil throws his shoulders and the rifle up
    h = d - breathe    # Breathing lifts the head and shoulders, not the hips
    # Torso: round shoulders, a plate carrier, narrowing to the waist
    poly(c, [(46, 42 + h), (64, 42 + h), (80, 48 + h), (86, 56 + h), (80, 70 + d), (78, FRONT_H),
             (32, FRONT_H), (30, 70 + d), (24, 56 + h), (30, 48 + h)], INK)
    poly(c, [(36, 52 + h), (74, 52 + h), (76, 90 + d), (74, FRONT_H), (36, FRONT_H), (34, 90 + d)], LAB[0])
    c.hline(37, 73, 52 + h, LAB[1])                                                          # The plate's top edge
    # The plate carrier has broad fabric planes, webbing and separate shoulder
    # straps. No identifying marks or skin: his identity stays hidden.
    poly(c, [(36, 50 + h), (42, 51 + h), (40, 68 + d), (35, 66 + d)], LAB[2])
    poly(c, [(68, 51 + h), (74, 50 + h), (76, 67 + d), (70, 68 + d)], LAB[1])
    poly(c, [(40, 55 + h), (70, 55 + h), (72, 91 + d), (38, 91 + d)], LAB[1])
    poly(c, [(40, 55 + h), (66, 55 + h), (67, 88 + d), (39, 88 + d)], LAB[2])
    c.hline(41, 66, 55 + h, LAB[3])
    c.vline(39, 60 + d, 86 + d, LAB[3])
    for y in (61, 67, 83):
        c.hline(41, 67, y + d, LAB[0])
        for x in range(42, 66, 6):
            c.hline(x, x + 2, y - 1 + d, LAB[3])
    for (x0, x1) in ((38, 48), (62, 72)):                                                    # Pouches
        c.fill(x0, 98 + d, x1, 108 + d, LAB[1])
        c.hline(x0, x1, 98 + d, LAB[2])
        c.fill(x0, 112 + d, x1, 122 + d, LAB[1])
        c.hline(x0, x1, 112 + d, LAB[2])
        for top in (98 + d, 112 + d):
            c.fill(x0 + 1, top + 2, x1 - 1, top + 8, LAB[2])
            c.hline(x0 + 1, x1 - 1, top + 2, LAB[3])
            c.hline(x0 + 2, x1 - 1, top + 5, LAB[0])
            c.px(x0 + 5, top + 4, LAB[3])
    c.vline(55, 92 + d, FRONT_H - 1, INK)
    # Head: hood, helmet, goggles
    c.fill(48, 36 + h, 62, 44 + h, INK)
    c.disc(55, 26 + h, 11, 13, INK)
    c.disc(55, 19 + h, 14, 11, LAB[1])
    c.disc(52, 15 + h, 8, 5, LAB[2])                                                         # The light on its dome
    c.hline(47, 56, 10 + h, LAB[3])
    c.hline(44, 47, 13 + h, LAB[3])
    c.fill(64, 16 + h, 66, 20 + h, LAB[0])
    c.fill(41, 19 + h, 69, 21 + h, LAB[1])
    c.hline(42, 68, 22 + h, INK)
    c.fill(40, 21 + h, 43, 29 + h, LAB[1])
    c.fill(67, 21 + h, 70, 29 + h, LAB[1])
    c.fill(45, 24 + h, 65, 28 + h, LAB[2])
    for gx in (47, 57):
        c.fill(gx, 24 + h, gx + 5, 27 + h, TEAL[0])
        c.hline(gx + 1, gx + 2, 25 + h, TEAL[2])
    # Arms: his right (our left) bent to the grip, his left (our right) out
    # to the elbow and across to the handguard; light between them and him
    poly(c, [(26, 50 + h), (34, 54 + h), (28, 70 + d), (40, 74 + d), (40, 80 + d), (24, 80 + d), (18, 72 + d),
             (20, 56 + h)], INK)
    poly(c, [(84, 50 + h), (90, 56 + h), (94, 72 + d), (88, 82 + d), (66, 86 + d), (64, 80 + d), (84, 74 + d),
             (80, 58 + h)], INK)
    poly(c, [(25, 54 + h), (31, 56 + h), (25, 69 + d), (29, 73 + d), (39, 76 + d),
             (38, 79 + d), (25, 77 + d), (21, 71 + d)], LAB[1])
    poly(c, [(25, 55 + h), (28, 56 + h), (23, 68 + d), (22, 68 + d)], LAB[2])
    poly(c, [(85, 55 + h), (88, 58 + h), (91, 71 + d), (86, 77 + d), (68, 82 + d),
             (68, 84 + d), (87, 80 + d), (93, 72 + d)], LAB[1])
    c.hline(24, 27, 65 + d, LAB[2])
    c.hline(87, 90, 68 + d, LAB[2])
    c.hline(29, 36, 76 + d, LAB[2])
    c.hline(72, 81, 81 + d, LAB[2])
    c.hline(20, 26, 70 + d, LAB[1])
    c.hline(87, 92, 70 + d, LAB[1])
    c.hline(24, 30, 54 + h, LAB[1])                                                          # Shoulder seams
    c.hline(80, 86, 54 + h, LAB[1])
    # The rifle: stock in his shoulder, receiver and sight, the handguard
    # coming down toward her, the muzzle nearest
    poly(c, [(28, 54 + d), (36, 52 + d), (58, 66 + d), (60, 76 + d), (52, 78 + d), (30, 62 + d)], GUN[1])
    poly(c, [(36, 52 + d), (58, 66 + d), (57, 68 + d), (34, 55 + d)], GUN[3])               # Its lit top edge
    c.fill(38, 47 + d, 46, 52 + d, GUN[2])                                                   # Sight on its rail
    c.hline(38, 46, 47 + d, GUN[4])
    c.fill(39, 48 + d, 41, 50 + d, TEAL[1])                                                  # Its glass
    c.px(39, 48 + d, TEAL[3])
    poly(c, [(40, 64 + d), (46, 66 + d), (44, 80 + d), (38, 78 + d)], GUN[0])                # Magazine
    c.vline(45, 67 + d, 78 + d, GUN[2])
    for k in range(3):                                                                       # Vent slots on the handguard
        c.fill(48 + k * 3, 66 + d + k * 2, 49 + k * 3, 67 + d + k * 2, GUN[0])
    mx, my = FRONT_MUZZLE[0], FRONT_MUZZLE[1] + d
    c.disc(mx + 0.5, my + 0.5, 4.2, 4.6, GUN[0])                                             # The muzzle, end on
    c.disc(mx + 0.5, my + 0.5, 3.2, 3.6, GUN[2])
    c.disc(mx + 0.5, my + 0.5, 1.6, 1.8, INK)                                                # The bore, at her
    lx, ly = FRONT_LENS[0], FRONT_LENS[1] + d
    poly(c, [(lx - 10, ly - 6), (lx - 2, ly - 4), (lx - 2, ly + 4), (lx - 10, ly + 2)], GUN[1])  # The light's body
    c.disc(lx + 0.5, ly + 0.5, 4.2, 4.2, GUN[2])
    c.disc(lx + 0.5, ly + 0.5, 3, 3, GLASS[3])                                               # Its lens, burning
    c.disc(lx + 0.5, ly + 0.5, 1.8, 1.8, rgb(0xffffff))
    # Gloves on the grip and around the handguard
    c.fill(36, 68 + d, 42, 75 + d, GLOVE[1])
    c.hline(36, 42, 68 + d, GLOVE[2])
    c.fill(52, 72 + d, 60, 77 + d, GLOVE[1])                                                 # (clear of the lens)
    c.hline(52, 59, 72 + d, GLOVE[2])
    for k in range(3):
        c.px(53 + k * 2, 74 + d, GLOVE[0])


def front_rim(c: Canvas) -> None:
    """Only what faces up catches the corridor's light: helmet, shoulders."""
    solid = {(x, y) for y in range(FRONT_H) for x in range(FRONT_W) if c.get(x, y)[3]}
    for (x, y) in solid:
        if c.get(x, y) in (INK, LAB[0], LAB[1]) and (x, y - 1) not in solid and y < 60:
            c.px(x, y, LAB[3])


FLASH = [rgb(0xd03305), rgb(0xe55d22), rgb(0xfbaa38), rgb(0xfff1a0), rgb(0xffffff)]


def muzzle_flash(c: Canvas, x: int, y: int, size: float) -> None:
    """A star of fire straight at the camera: rays, then a white-hot core."""
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        reach = size * (1.0 if k % 2 == 0 else 0.6)
        for step in range(int(reach)):
            f = step / reach
            col = FLASH[4] if f < 0.25 else FLASH[3] if f < 0.5 else FLASH[2] if f < 0.75 else FLASH[1]
            px = x + round(math.cos(a) * step)
            py = y + round(math.sin(a) * step)
            c.px(px, py, col)
            if f < 0.5:
                c.px(px + 1, py, col)
    c.disc(x + 0.5, y + 0.5, size * 0.45, size * 0.45, FLASH[2])
    c.disc(x + 0.5, y + 0.5, size * 0.32, size * 0.32, FLASH[3])
    c.disc(x + 0.5, y + 0.5, size * 0.18, size * 0.18, FLASH[4])


def make_mercenary_front() -> Image:
    """Frames: 0-1 aiming, breathing; 2 the shot (recoil and the flash);
    3 the rifle settling, a last lick of fire."""
    img = Image(FRONT_W * FRONT_FRAMES, FRONT_H)
    poses = ((0, 0), (0, 1), (2, 0), (1, 0))
    for f, (lift, breathe) in enumerate(poses):
        c = Canvas(img, f * FRONT_W, FRONT_W)
        front_body(c, lift, breathe)
        front_rim(c)
        if f == 2:
            mx, my = FRONT_MUZZLE[0], FRONT_MUZZLE[1] - lift
            for y in range(FRONT_H):                      # The flash lights him up, warm, close to it
                for x in range(FRONT_W):
                    col = c.get(x, y)
                    dist = math.hypot(x - mx, y - my)
                    if not col[3] or col not in (INK, LAB[0], LAB[1], LAB[2]) or dist >= 32:
                        continue
                    band = 0 if dist < 14 else 1 if dist < 23 else 2
                    if col == INK:
                        c.px(x, y, (rgb(0x3a1c10), rgb(0x26130b), rgb(0x170c08))[band])
                    else:
                        c.px(x, y, (rgb(0x6a3418), rgb(0x45220f), rgb(0x2a160c))[band])
            muzzle_flash(c, mx, my, 24)
        elif f == 3:
            muzzle_flash(c, FRONT_MUZZLE[0], FRONT_MUZZLE[1] - lift, 9)
    from support_finishes import finish_mercenary
    return finish_mercenary(img, FRONT_W, LAB, GUN, GLASS, TEAL, INK, RIM)


# --- Valeria's fist and the sample ---------------------------------------------

VIAL_W, VIAL_H = 64, 100


def make_vial() -> Image:
    img = Image(VIAL_W, VIAL_H)
    c = Canvas(img)
    tx0, tx1, ttop, tbottom = 27, 35, 8, 52
    # Its glow on the dark: see-through, so the scene shows behind it
    for y in range(VIAL_H):
        for x in range(VIAL_W):
            d = math.hypot(x + 0.5 - 31, (y + 0.5 - 28) / 1.25)
            for radius, alpha in ((8, 70), (13, 42), (19, 20)):
                if d < radius:
                    c.px(x, y, rgb(0x46c060, alpha))
                    break
    c.fill(tx0 - 1, ttop - 5, tx1 + 1, ttop, LAB[4])           # Cap
    c.hline(tx0 - 1, tx1 + 1, ttop - 5, LAB[5])
    c.hline(tx0 - 1, tx1 + 1, ttop, LAB[2])
    c.fill(tx0, ttop + 1, tx1, tbottom, GLASS[0])              # Glass
    c.fill(tx0 + 1, ttop + 12, tx1 - 1, tbottom, VIAL[2])      # The liquid
    c.hline(tx0 + 1, tx1 - 1, ttop + 12, VIAL[4])              # Meniscus
    c.vline(tx0 + 2, ttop + 13, tbottom, VIAL[3])
    c.vline(tx1 - 1, ttop + 13, tbottom, VIAL[1])
    for k in range(4):                                         # Bubbles
        c.px(tx0 + 4 + (k % 2) * 2, ttop + 16 + k * 6, VIAL[4])
    c.vline(tx0, ttop + 1, tbottom, GLASS[2])                  # The glass's edges
    c.vline(tx1, ttop + 1, tbottom, GLASS[1])
    c.vline(tx0 + 1, ttop + 2, ttop + 10, GLASS[3])
    # The fist, backlit: four curled fingers stacked around the tube, each a
    # band rounded at both ends with a knuckle on the right, the pinky the
    # shortest; the thumb crosses over the top from the left.
    f0, f1, f2 = SKIN_SHADE
    fingers = ((40, 19, 43), (46, 17, 44), (52, 18, 43), (58, 21, 40))
    for (y0, x0, x1) in fingers:
        for y in range(y0, y0 + 6):
            inset = 2 if y in (y0, y0 + 5) else 1 if y in (y0 + 1, y0 + 4) else 0
            c.hline(x0 + inset, x1 - inset, y, f1)
        c.hline(x0 + 1, x1 - 2, y0, f2)                        # Lit top of the finger
        c.hline(x0 + 2, x1 - 1, y0 + 5, f0)                    # The crease below it
        c.vline(x0 + 1, y0 + 1, y0 + 4, f0)                    # Its tip curled in, in shadow
        c.fill(x1 - 1, y0 + 2, x1, y0 + 3, f2)                 # Knuckle
    for y in range(36, 43):                                    # Thumb, from the left over the index
        x0 = 12 + (42 - y) // 2
        x1 = 29 - (42 - y) // 3
        c.hline(x0, x1, y, f1)
        if y == 36:
            c.hline(x0, x1, y, f2)
    c.fill(28, 37, 30, 40, f2)                                 # Its tip on the glass
    for y in range(64, VIAL_H):                                # Wrist, narrowing, then the forearm
        half = 9 if y < 74 else 8
        cx = 31 - (y - 64) // 6
        c.hline(cx - half, cx + half, y, f1)
    for y in range(64, 68):
        cx = 31
        c.hline(cx - 10 + (y - 64), cx + 10 - (y - 64) // 2, y, f1)  # Heel of the hand
    for y in range(80, VIAL_H):                                # Her jacket's cuff
        cx = 31 - (y - 64) // 6
        c.hline(cx - 11, cx + 11, y, LAB[1])
    c.hline(31 - 2 - 11, 31 - 2 + 11, 80, LAB[3])
    c.hline(31 - 2 - 11, 31 - 2 + 11, 81, LAB[2])
    # The flashlight catches the right-hand edges
    for y in range(VIAL_H):
        for x in range(VIAL_W - 1, 0, -1):
            col = img.get(x, y)
            if col[3] == 255 and col in (f0, f1, f2, LAB[1], LAB[2], LAB[3]):
                img.set(x, y, RIM)
                if img.get(x - 1, y) in (f1, LAB[1]):
                    img.set(x - 1, y, f2 if col in (f0, f1, f2) else LAB[3])
                break
            if col[3] == 255:
                break
    from support_finishes import finish_vial
    return finish_vial(img, SKIN_SHADE, LAB, GLASS, VIAL, RIM)


# --- The ambulance ---------------------------------------------------------------

VAN_W, VAN_H, VAN_FRAMES = 72, 34, 4


def wheel(c: Canvas, cx: int, cy: int, f: int) -> None:
    c.disc(cx + 0.5, cy + 0.5, 5, 5, TYRE[0])
    c.disc(cx + 0.5, cy + 0.5, 4, 4, TYRE[1])
    c.disc(cx + 0.5, cy + 0.5, 2.5, 2.5, TYRE[3])
    c.disc(cx + 0.5, cy + 0.5, 1.2, 1.2, TYRE[2])
    for k in range(3):                                         # Lug nuts turning
        a = k * 2 * math.pi / 3 + f * math.pi / 6
        c.px(cx + round(math.cos(a) * 2), cy + round(math.sin(a) * 2), TYRE[1])
    c.hline(cx - 3, cx + 3, cy - 5, TYRE[2])                   # The tyre's lit top


def make_ambulance() -> Image:
    img = Image(VAN_W * VAN_FRAMES, VAN_H)
    for f in range(VAN_FRAMES):
        c = Canvas(img, f * VAN_W, VAN_W)
        ground = VAN_H - 1
        # The box (rear, left) and the cab (front, right), facing right
        bx0, bx1, btop, bbot = 2, 46, 5, 26
        c.fill(bx0, btop, bx1, bbot, VAN[2])
        c.hline(bx0, bx1, btop, VAN[4])
        c.vline(bx0, btop, bbot, VAN[3])
        c.hline(bx0, bx1, bbot, VAN[0])
        c.vline(bx1, btop, bbot, VAN[1])
        c.fill(bx0 + 1, btop + 1, bx1 - 1, btop + 2, VAN[3])
        c.fill(46, 11, 66, 26, VAN[2])                         # Cab
        for y in range(11, 17):                                # Windshield slope
            for x in range(66 - (16 - y) // 2, 69):
                c.px(x, y, CLEAR)
        c.fill(47, 9, 60, 11, VAN[2])                          # Cab roof
        c.hline(47, 60, 9, VAN[4])
        c.fill(64, 17, 69, 26, VAN[2])                         # Hood and front
        c.hline(64, 69, 17, VAN[3])
        c.vline(69, 17, 26, VAN[0])
        c.fill(51, 12, 63, 17, WINDOW[0])                      # Side window
        for k in range(4):
            c.px(53 + k, 16 - k, WINDOW[2])
            c.px(54 + k, 16 - k, WINDOW[1])
        for y in range(12, 17):                                # Windshield
            c.hline(64 - (16 - y) // 3, 66 - (16 - y) // 2, y, WINDOW[1])
        c.vline(50, 11, 26, VAN[0])                            # Cab door seam
        c.fill(61, 18, 62, 18, VAN[0])                         # Handle
        c.fill(68, 20, 69, 21, AMBER[3])                       # Headlight
        c.fill(68, 24, 70, 26, TYRE[2])                        # Bumper
        c.fill(bx0, 17, 69, 19, STRIPE[1])                     # The red stripe
        c.hline(bx0, 69, 17, STRIPE[2])
        c.hline(bx0, 69, 19, STRIPE[0])
        c.fill(8, 8, 20, 15, WINDOW[0])                        # Rear box window
        c.hline(9, 19, 9, WINDOW[2])
        c.vline(30, btop + 1, bbot - 1, VAN[1])                # Side door
        c.vline(31, btop + 1, bbot - 1, VAN[3])
        c.px(33, 15, VAN[0])
        c.fill(bx0 - 1, 22, bx0, 25, SIREN_RED[1])             # Tail light
        c.fill(4, 27, 66, 27, TYRE[0])                         # Underside shadow
        for wx in (13, 57):                                    # Wheel arches
            c.disc(wx + 0.5, 27.5, 7, 5, TYRE[0])
            wheel(c, wx, 28, f)
        # Light bars: on the box's front corner and the cab, alternating
        lit_red = f % 2 == 0
        reds, blues = (SIREN_RED, SIREN_BLUE)
        c.fill(40, 2, 45, 4, reds[2] if lit_red else reds[0])
        c.fill(34, 2, 39, 4, blues[0] if lit_red else blues[2])
        c.hline(34, 45, 4, TYRE[1])
        c.fill(52, 7, 55, 8, reds[1] if lit_red else reds[0])
        c.fill(56, 7, 59, 8, blues[0] if lit_red else blues[1])
        # Outline
        solid = {(x, y) for y in range(VAN_H) for x in range(VAN_W) if c.get(x, y)[3]}
        for (x, y) in solid:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in solid and 0 <= x + dx < VAN_W and 0 <= y + dy < VAN_H:
                    c.px(x + dx, y + dy, rgb(0x231a14))
        _ = ground
    return img


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'assets'
    outputs = {
        'cinematics/lab/corridor.png': make_corridor(),
        'cinematics/lab/monitors.png': make_monitors(),
        'cinematics/lab/alarm.png': make_alarm(),
        'sprites/mercenary/walk.png': make_mercenary(assets),
        'sprites/mercenary/aim.png': make_mercenary_front(),
        'sprites/vial/held.png': make_vial(),
        'sprites/ambulance/drive.png': make_ambulance(),
    }
    for name, image in outputs.items():
        image.save(assets / name)
        print(f'{name}: {image.width} x {image.height}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
