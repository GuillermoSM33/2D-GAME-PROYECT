#!/usr/bin/env python3
"""Make the art of the characters' level-3 powers.

Usage: tools/make_powers.py

Writes:
  assets/sprites/weapons/grenade.png  The SWAT's hand grenade, tumbling
      (4 frames of 8 x 8): olive body, its lever and the pin's ring.

Her duals are made by tools/make_flashlight.py, the SWAT's throwing sheet with his other sheets (tools/make_swat.py).
Uses only the standard library.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SHOOT_W, SHOOT_H, FRAMES = 81, 80, 8
NEAR_FROM_X = 38            # Shoot-frame columns from here: her near (gun) arm and its gun
GUN_FROM_X = 46             # ...and from here, the gun alone (and its flash)
SHOULDER_SLEEVE_TO = 38      # Shoot-frame row where that sleeve ends
FAR_ARM_INSIDE = (7, 3)      # Where an arm passing behind her starts, from the shoulder: inside her
TORSO_ROWS = (38, 46)        # Shoot-frame rows of her chest and waist
GREY_ARM = {(0x6c, 0x7a, 0x84), (0x50, 0x5c, 0x66), (0x38, 0x42, 0x4a)}
SKIN = {(0xfe, 0xdc, 0xa3), (0xd9, 0x9a, 0x5b), (0x89, 0x41, 0x1f), (0x8a, 0x43, 0x22)}  # And its shadows
GLOVE = {(0x69, 0x68, 0x67), (0x99, 0x9a, 0x9c)}
INK = rgb(0x252018)
SLEEVE = [rgb(0x6c7a84), rgb(0x505c66), rgb(0x38424a)]   # Her grey sleeve, light to dark
CORSET = rgb(0x2c363c)


def load(path: Path) -> Image:
    w, h, px = decode_png_rgba(path)
    img = Image(w, h)
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            img.set(x, y, tuple(px[i:i + 4]))
    return img


def frame_pixels(sheet: Image, f: int) -> dict:
    out = {}
    for y in range(SHOOT_H):
        for x in range(SHOOT_W):
            c = sheet.get(f * SHOOT_W + x, y)
            if c[3]:
                out[(x, y)] = c
    return out


def sleeve(shoulder: tuple, hand: tuple) -> dict:
    """Her grey puffed sleeve from the shoulder to the hand, as on her art: a
    round puff over the shoulder, the sleeve narrowing to the wrist, lit on
    top and shaded under, outlined."""
    (sx, sy), (hx, hy) = shoulder, hand
    n = max(abs(hx - sx), abs(hy - sy), 1)
    px = {}

    def paint(x: int, y: int, cy: float, r: float) -> None:
        k = (y - cy) / max(r, 0.5)
        px[(x, y)] = SLEEVE[0] if k < -0.35 else SLEEVE[1] if k < 0.45 else SLEEVE[2]

    for t in range(n + 1):
        cx = sx + (hx - sx) * t / n
        cy = sy + (hy - sy) * t / n
        r = 2.6 - 1.2 * t / n                                  # Thick at the shoulder, thin at the wrist
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    paint(x, y, cy, r)
    for y in range(sy - 4, sy + 4):                            # The puff over the shoulder
        for x in range(sx - 4, sx + 4):
            if (x + 0.5 - sx) ** 2 + (y + 0.5 - sy) ** 2 <= 3.4 ** 2:
                paint(x, y, sy, 3.4)
    out = dict(px)
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in px:
                out[(x + dx, y + dy)] = INK
    return out


NECKLINE_BOTTOM = 40              # Shoot-frame row of her lace's lowest point: the skin above it is her chest


def without_hip_arm(px: dict) -> tuple[dict, tuple]:
    """A shoot frame's pixels without her far arm (the grey sleeve on her hip
    and the hand under it), her clothes carried on where it lay. Returns them
    and where that arm's shoulder is."""
    # Her arm on the hip: the grey sleeve and the hand under it, left of her gun arm.
    # Its hand lay on her waist: no skin left below her chest there either.
    # The sleeve over her shoulder stays where it is: only the arm below it goes.
    arm = {(x, y) for (x, y), c in px.items()
           if (x < 32 and y >= SHOULDER_SLEEVE_TO and c[:3] in GREY_ARM) or
           (x < NEAR_FROM_X and y >= NECKLINE_BOTTOM and c[:3] in SKIN) or
           (x < GUN_FROM_X and y >= 49 and c[:3] in SKIN)}
    greys = sorted((y, x) for (x, y) in arm if px[(x, y)][:3] in GREY_ARM)
    shoulder = (greys[0][1] + 1, greys[0][0] + 1) if greys else (26, 37)
    base = dict(px)
    removed = set(arm)
    for xy in arm:
        del base[xy]
    for (x, y), c in list(base.items()):                  # Its outline, left alone
        if c[:3] == INK[:3] and not any((x + a, y + b) in base and base[(x + a, y + b)][:3] != INK[:3]
                                        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            del base[(x, y)]
            removed.add((x, y))
    # Where it lay on her (the hand on her hip): her clothes carry on there,
    # copied from the nearest pixel on the right in the same row.
    for (x, y) in sorted(removed, key=lambda xy: -xy[0]):
        row = [xx for (xx, yy) in base if yy == y]
        if not row or not min(row) < x < max(row):
            continue
        right = next((base[(xx, y)] for xx in range(x + 1, max(row) + 1)
                      if (xx, y) in base and base[(xx, y)][:3] != INK[:3]), CORSET)
        base[(x, y)] = right
    # Her side, under where the arm was: an outline straight from the
    # shoulder down to the waist, her clothes filled in up to it.
    rows = sorted({y for (_, y) in arm if y < 50})
    if rows:
        def leftmost(y):
            xs = [x for (x, yy) in base if yy == y and x < NEAR_FROM_X]
            return min(xs) if xs else None
        y0, y1 = rows[0] - 1, rows[-1] + 1
        while y1 < SHOOT_H - 1 and leftmost(y1) is None:
            y1 += 1
        top, bottom = leftmost(y0), leftmost(y1)
        if top is not None and bottom is not None:
            for y in range(y0 + 1, y1):
                edge = round(top + (bottom - top) * (y - y0) / (y1 - y0))
                inner = leftmost(y)
                if inner is None or inner <= edge:
                    continue
                fill = next((base[(xx, y)] for xx in range(inner, NEAR_FROM_X)
                             if (xx, y) in base and base[(xx, y)][:3] != INK[:3]), CORSET)
                for x in range(edge + 1, inner):
                    base[(x, y)] = fill
                base[(edge, y)] = INK
    return turned_a_little(base), shoulder


def turned_a_little(px: dict) -> dict:
    """Her torso seen a little from the side, as her arm's off it: narrower at the
    back, more at the waist, so it doesn't read as a box."""
    out = dict(px)
    for y in range(TORSO_ROWS[0], TORSO_ROWS[1] + 1):
        row = sorted(x for (x, yy) in px if yy == y and x < NEAR_FROM_X)
        if not row:
            continue
        cut = 2 if y < TORSO_ROWS[1] - 4 else 3
        for x in range(row[0], row[0] + cut):
            out.pop((x, y), None)
        out[(row[0] + cut, y)] = INK
    return out


GRENADE = [rgb(0x2a2c1a), rgb(0x4a5030), rgb(0x6a7444), rgb(0x8e9a5c)]
LEVER = rgb(0xa7a8a8)
GRENADE_INK = rgb(0x140e0e)


def make_grenade() -> Image:
    """4 frames of 8 x 8, a quarter turn each."""
    body = [
        "..ooo...",
        ".oLLso..",
        "o3332o..",
        "o3221o..",
        "o3221o..",
        "o2211o..",
        ".o11o...",
        "..oo....",
    ]
    keys = {'o': GRENADE_INK, '1': GRENADE[0], '2': GRENADE[1], '3': GRENADE[2], 'L': LEVER, 's': GRENADE[3]}
    img = Image(8 * 4, 8)
    for f in range(4):
        for y, row in enumerate(body):
            for x, k in enumerate(row):
                if k == '.':
                    continue
                # A quarter turn per frame about the middle.
                rx, ry = x - 3.5, y - 3.5
                for _ in range(f):
                    rx, ry = -ry, rx
                tx, ty = int(round(rx + 3.5)), int(round(ry + 3.5))
                if 0 <= tx < 8 and 0 <= ty < 8:
                    img.set(f * 8 + tx, ty, keys[k])
    return img


def main() -> int:
    out = {
        'assets/sprites/weapons/grenade.png': make_grenade(),
    }
    for name, img in out.items():
        img.save(ROOT / name)
        print(f'make_powers: {name} ({img.width} x {img.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
