#!/usr/bin/env python3
"""Dress the cowgirl: her costume over her base sheets, frame by frame.

Usage: tools/rebuild_cowgirl.py runs this and all that build on it, in order.

Reads docs/templates/cowgirl/{walk,shoot,jump}.png and writes the same
names to assets/sprites/characters/cowgirl/. Her hat and her guns stay. Over the
rest: long red hair falling down her back, a neckline curving up to her shoulders
with a lace edge, dark slate puffed sleeves covering them, a slate corset, a wide leather belt with
a brass buckle, a dark red sash hanging from it, striped trousers. Standard
library only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_powers import load  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs/templates/cowgirl'
OUT = ROOT / 'assets/sprites/characters/cowgirl'
SHEETS = {'walk': 42, 'shoot': 81, 'jump': 54}
ARMED = {'walk', 'jump'}          # Her gun in its holster; in the others, it is in her hand

INK = (0x25, 0x20, 0x18)
BELT_GOLD = (0x9c, 0x85, 0x26)
SKIN = {(0xfe, 0xdc, 0xa3), (0xd9, 0x9a, 0x5b), (0x89, 0x41, 0x1f), (0x8a, 0x43, 0x22)}
HAIR = [rgb(0x6b333a), rgb(0x902004), rgb(0xd03305)]
# Sleeves, everywhere: her greys to slate.
SLEEVES = {(0xa7, 0xa8, 0xa8): rgb(0x6c7a84), (0x99, 0x9a, 0x9c): rgb(0x6c7a84),
           (0x86, 0x86, 0x89): rgb(0x505c66), (0x50, 0x50, 0x50): rgb(0x38424a)}
CORSET = {(0x46, 0x33, 0x22): rgb(0x2c363c), (0x68, 0x48, 0x33): rgb(0x48565e),
          (0x42, 0x42, 0x42): rgb(0x38444a), (0x2c, 0x2c, 0x2c): rgb(0x242c32)}
TROUSERS = {(0x42, 0x42, 0x42): (rgb(0x5e5650), rgb(0x48423e)), (0x2c, 0x2c, 0x2c): (rgb(0x423c38), rgb(0x322e2c)),
            (0x46, 0x33, 0x22): (rgb(0x4c4640), rgb(0x3a3532)), (0x68, 0x48, 0x33): (rgb(0x6e6660), rgb(0x585250))}
LACE = [rgb(0xece6d6), rgb(0xbcb6a6)]
CORSET_TOP = rgb(0x2c363c)
LEATHER = [rgb(0x4a2e18), rgb(0x6c4626)]
HOLSTER = [rgb(0x6c4626), rgb(0x4a2e18)]
CORD = rgb(0x6a6a68)
CORSET_TONES = {(0x2c, 0x36, 0x3c), (0x48, 0x56, 0x5e), (0x38, 0x44, 0x4a), (0x24, 0x2c, 0x32)}
HIP_CURVE = (8, 8, 8, 7, 7, 6)    # Art columns from her belt's middle to her hip, rows down from the belt
HIP_MOST = 2                      # ...and at most this much on what the leg already is
STRAP_UNDER_BELT = 9              # Art rows from her belt to the strap on her thigh
LACING_ROWS = 4
GLOVE = [rgb(0x684833), rgb(0x463322)]
GLOVES_FROM = 7                   # Art rows over the belt where her chest has ended
GUN_BUTT = rgb(0x8a6a3e)
BRASS = [rgb(0xb8903a), rgb(0xecc868)]
SASH = [rgb(0x64182a), rgb(0x8a2438), rgb(0x46101e)]
TORSO_HALF = 9                    # Art columns from her middle, and rows up from the belt, of her torso
TORSO_ROWS = 14
SASH_ROWS = 8                     # Down her thigh, clear of the boots
BELT_UNDER_FACE = 22              # Rows from the top of her face to her belt, in every upright frame
BROWN_SKIN = {(0x89, 0x41, 0x1f), (0x8a, 0x43, 0x22)}
CHOKER = rgb(0x1e1a20)
# The blouse's neckline, a smile: rows under the choker its lace runs at, by art
# columns from the middle of her neck. High at her shoulders, lowest on her chest.
LACE_SMILE = (5, 5, 5, 4, 4, 3, 3, 2)
BARE_WIDTH = {1: 2, 2: 3, 3: 4, 4: 2}  # Rows under the choker: bare columns each side of her neck
CORSET_HALF = 8                   # Art columns from her belt's middle that are her corset
TRAPEZIUS_WIDEST = 5              # Art columns from the middle of her neck that the bare slope reaches
NEAR_HOLSTER, FAR_HOLSTER = 5, 8  # Art columns from her belt's middle to each
CHOKER_UNDER_FACE = 8             # Rows from the top of her face to it
COLLAR_FROM = 5                   # Art columns from the middle of her neck that the chest's shading is evened over


def over_arm(out: dict, x: int, y: int) -> bool:
    """On one of her sleeves, or the outline around it."""
    sleeve = {c[:3] for c in SLEEVES.values()}
    c = out.get((x, y))
    if c is None:
        return False
    if c[:3] in sleeve:
        return True
    return c[:3] == INK and any(out.get((x + a, y + b), (0, 0, 0, 0))[:3] in sleeve
                                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def outlined(px: dict, over: dict) -> None:
    """Puts px in over, with an outline only on what is empty around it."""
    for (x, y), c in px.items():
        over[(x, y)] = c
    for (x, y) in px:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + a, y + b) not in over:
                over[(x + a, y + b)] = INK + (255,)


def arm_in_front(px: dict, moved: set, x: int, y: int) -> bool:
    """A sleeve that has swung over her chest in this frame, or the outline around
    it: the outline between corset and sleeve goes under. An arm leaves from her
    shoulder, so the neckline itself stays whole over the top of it."""
    def sleeve(a: int, b: int) -> bool:
        return px.get((a, b), (0, 0, 0, 0))[:3] in SLEEVES
    if (x, y) not in moved:
        return False
    return sleeve(x, y) or (px[(x, y)][:3] == INK and any(sleeve(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))))


def neckline(px: dict, moved: set, out: dict, neck_x: float, choker: int) -> None:
    """Skin in a scoop under the choker, its lace edge curving up to her shoulders
    like a smile, the corset up to the lace, an outline parting it from her sleeves.
    Only on her body: never past her outline."""
    def body(x: int, y: int) -> bool:
        return all((x + a, y + b) in out for a, b in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)))

    middle = round(neck_x)
    half = len(LACE_SMILE) - 1
    bottom = choker + max(LACE_SMILE) + 1
    for dx in range(-half - 1, half + 2):
        x = middle + dx
        if abs(dx) > half:                               # Where the corset meets the sleeve
            for y in range(choker + LACE_SMILE[-1] + 1, bottom + 1):
                if body(x, y) and not arm_in_front(px, moved, x, y):
                    out[(x, y)] = INK + (255,)
            continue
        lace_y = choker + LACE_SMILE[abs(dx)]
        for y in range(choker + 1, bottom + 1):
            if not body(x, y):
                continue
            if y < lace_y:
                bare = BARE_WIDTH.get(y - choker, 0)
                if abs(dx) <= bare:
                    out[(x, y)] = rgb(0xd99a5b) if abs(dx) == bare or y == lace_y - 1 else rgb(0xfedca3)
                else:
                    out[(x, y)] = rgb(0x6c7a84) if abs(dx) <= bare + 1 else rgb(0x505c66)
            elif y == lace_y:
                out[(x, y)] = LACE[0]
            elif y == lace_y + 1 and abs(dx) % 2 == 0:
                out[(x, y)] = LACE[1]
            else:
                out[(x, y)] = CORSET_TOP
    if (middle, choker + 1) in out:
        out[(middle, choker + 1)] = rgb(0xb8903a)        # The pendant, over the skin


def outlined_on(out: dict, px: dict) -> None:
    """px over out, with an outline where it meets nothing."""
    out.update(px)
    for (x, y) in px:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + a, y + b) not in out:
                out[(x + a, y + b)] = INK + (255,)


def holster(x0: int, belt: int) -> dict:
    """A small holster on the belt, close to her leg, the gun's butt showing above it."""
    px = {(x0 + i, belt + 2 + j): HOLSTER[i == 1 or j == 3] for i in (0, 1) for j in range(4)}
    px.update({(x0 + i, belt + j): GUN_BUTT for i in (0, 1) for j in (0, 1)})
    return px


def dress(px: dict, moved: set = frozenset(), armed: bool = False) -> dict:
    """One frame. Lying or fallen frames (no belt under a face) get colours only."""
    faces = [y for (_, y), c in px.items() if c[:3] == (0xfe, 0xdc, 0xa3)]
    out = dict(px)
    for p, c in px.items():
        if c[:3] in SLEEVES:
            out[p] = SLEEVES[c[:3]]
    if not faces:
        return out
    face = min(faces)
    # Her belt's buckle is always this far under her face; without it, she has
    # fallen and only the colours change.
    belt = face + BELT_UNDER_FACE
    belt_x = [x for (x, y), c in px.items() if c[:3] == BELT_GOLD and y == belt]
    if not belt_x:
        return out
    mid = sum(belt_x) // len(belt_x)
    neck = face + 9
    # Corset, between her chest and the belt
    for (x, y), c in px.items():
        if neck <= y < belt and c[:3] in CORSET and abs(x - mid) <= CORSET_HALF:  # Not her glove, nor the gun
            out[(x, y)] = CORSET[c[:3]]
    # Trousers striped, down to the boots
    feet = max(y for (_, y) in px)
    boots = feet - 7
    for (x, y), c in px.items():
        if belt < y < boots and c[:3] in TROUSERS:
            out[(x, y)] = TROUSERS[c[:3]][1 if x % 3 == 0 else 0]
    # The middle of her neck, which needn't be over the belt's
    chin = [x for (x, y), c in px.items() if y == face + 3 and c[:3] == (0xfe, 0xdc, 0xa3)]
    neck_x = sum(chin) / len(chin) if chin else float(mid)
    # Bare only along the upper trapezius: the skin opens from her neck down the
    # slope to her shoulders, and the sleeves cover all the rest, following it.
    choker = face + CHOKER_UNDER_FACE
    collar = {}
    for (x, y), c in px.items():
        if choker <= y < belt - 4 and c[:3] in SKIN and x < neck_x:
            opening = min(TRAPEZIUS_WIDEST, 2 + y - choker)
            gap = neck_x - x - 0.5
            if gap > opening:
                collar[(x, y)] = rgb(0x6c7a84) if gap <= opening + 1 else rgb(0x505c66)
    # Her far shoulder, the same; not with that arm out of the frame
    has_far_arm = any(c[:3] in SLEEVES and x > neck_x and y <= choker + max(LACE_SMILE) for (x, y), c in px.items())
    if has_far_arm:
        for (x, y), c in list(collar.items()):
            collar[(round(2 * neck_x - x), y)] = c
    out.update(collar)
    # A dark choker with a little gold pendant, on her neck, bare skin below it
    for (x, y), c in px.items():
        if choker < y < belt - 4 and c[:3] in BROWN_SKIN and (x, y) not in collar and abs(x - neck_x) <= COLLAR_FROM:
            out[(x, y)] = rgb(0xd99a5b)
    for dx in range(-2, 3):
        x = round(neck_x) + dx
        if (x, choker) in out:
            out[(x, choker)] = CHOKER
    hair_tones = {h[:3] for h in HAIR}
    for dx in (-3, 3):                                   # Past its ends, the sleeve
        x = round(neck_x) + dx
        if (x, choker) in out:
            out[(x, choker)] = rgb(0x505c66)
        if out.get((x, choker + 1), (0, 0, 0, 0))[:3] in hair_tones:
            out[(x, choker + 1)] = rgb(0x505c66)
    out[(round(neck_x), choker)] = rgb(0xecc868)
    out[(round(neck_x), choker + 1)] = rgb(0xb8903a)
    neckline(px, moved, out, neck_x, choker)
    # Below her chest there is no bare skin: what is left of her hands has its gloves
    for (x, y), c in list(out.items()):
        if y >= belt - GLOVES_FROM and c[:3] in SKIN:
            # Lower down it was only ever a stain on her leg
            out[(x, y)] = TROUSERS[(0x2c, 0x2c, 0x2c)][0] if y > belt + 1 else GLOVE[c[:3] != (0xfe, 0xdc, 0xa3)]
    # A wide belt with a brass buckle
    for x in range(mid - 9, mid + 10):
        for y in (belt - 1, belt, belt + 1):
            if (x, y) in px and px[(x, y)][:3] != INK:
                out[(x, y)] = LEATHER[y == belt - 1]
    for y in (belt - 1, belt, belt + 1):
        for x in (mid - 1, mid, mid + 1, mid + 2):
            out[(x, y)] = BRASS[y == belt - 1]
    out[(mid, belt)] = LEATHER[0]
    out[(mid + 1, belt)] = LEATHER[0]
    # Her hips: the leg meets the belt in a curve, no step down from it to a thin thigh
    for k, reach in enumerate(HIP_CURVE):
        y = belt + 2 + k
        row = [x for (x, yy) in out if yy == y and x > mid]
        if not row:
            continue
        edge = max(row)
        side = min(mid + reach, edge + HIP_MOST)          # A leg swung in keeps its own shape, no bulge beside it
        for x in range(edge, side + 1):
            out[(x, y)] = TROUSERS[(0x42, 0x42, 0x42)][1 if x % 3 == 0 else 0]
        if edge <= side:
            out[(side + 1, y)] = INK + (255,)
    # The strap round her near thigh
    for y in (belt + STRAP_UNDER_BELT, belt + STRAP_UNDER_BELT + 1):
        for x in [x for (x, yy) in out if yy == y and x > mid + 1]:
            if out[(x, y)][:3] != INK:
                out[(x, y)] = LEATHER[y != belt + STRAP_UNDER_BELT]
    # The corset's lacing, crossing up its middle
    lace_x = round(neck_x)
    for y in range(belt - LACING_ROWS - 1, belt - 1):
        for x in ((lace_x,) if (y - belt) % 2 else (lace_x - 1, lace_x + 1)):
            if out.get((x, y), (0, 0, 0, 0))[:3] in CORSET_TONES:
                out[(x, y)] = CORD
    # The gun in its holster on her near hip, when it isn't in her hand
    if armed:
        outlined_on(out, holster(mid + NEAR_HOLSTER, belt))
    # The sash, from the belt at her back, ragged at its end
    back = min(x for (x, y) in px if y == belt + 1)
    sash = {}
    for i in range(SASH_ROWS):
        width = 5 - i // 3
        for w in range(width):
            x = back + 1 + w - (i // 5)
            if i == SASH_ROWS - 1 and w % 2:
                continue
            sash[(x, belt + 1 + i)] = SASH[(w + i // 3) % 2] if w else SASH[2]
    outlined(sash, out)
    # Her hair, in waves over her shoulder and down her back, to the waist
    hair = [(x, y) for (x, y), c in px.items() if c[:3] in {h[:3] for h in HAIR}]
    if hair:
        lowest = max(y for _, y in hair)
        left = min(x for x, y in hair if y >= lowest - 4)
        for y in range(lowest - 2, belt - 3):
            k = y - (lowest - 2)
            wave = (k // 3) % 3 - 1
            width = max(2, 4 - k // 6)
            x0 = left + 1 + wave
            if all(over_arm(out, x0 + w, y) for w in range(width)):
                break                                    # Her arm hides it here: no loose end past it
            for w in range(width):                       # Behind her arm: only where it isn't
                if not over_arm(out, x0 + w, y):
                    out[(x0 + w, y)] = HAIR[2] if w == 1 and k % 4 == 0 else HAIR[1] if w < width - 1 else HAIR[0]
            for x in (x0 - 1, x0 + width):
                if (x, y) not in out:
                    out[(x, y)] = INK + (255,)
    return out


def landmarks(px: dict) -> tuple | None:
    """Her belt's row and middle, if she is upright."""
    faces = [y for (_, y), c in px.items() if c[:3] == (0xfe, 0xdc, 0xa3)]
    if not faces:
        return None
    belt = min(faces) + BELT_UNDER_FACE
    golds = [x for (x, y), c in px.items() if c[:3] == BELT_GOLD and y == belt]
    return (belt, sum(golds) // len(golds)) if golds else None


def whole_torso(dressed: dict, here: tuple, reference: dict, there: tuple) -> dict:
    """Where her swinging arm has left a gap there was never any body drawn, its
    place always covered: her torso from the reference frame fills it."""
    sleeve = {c[:3] for c in SLEEVES.values()}
    out = dict(dressed)
    dx, dy = here[1] - there[1], here[0] - there[0]
    added = []
    for (x, y), c in reference.items():
        mx, my = x + dx, y + dy
        near = abs(x - there[1]) <= TORSO_HALF and there[0] - TORSO_ROWS <= y < there[0]
        if near and (mx, my) not in out and c[:3] not in sleeve and c[:3] != INK:
            out[(mx, my)] = c
            added.append((mx, my))
    for (x, y) in added:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + a, y + b) not in out:
                out[(x + a, y + b)] = INK + (255,)
    return out


def main() -> int:
    for name, w in SHEETS.items():
        source = load(SOURCE / f'{name}.png')
        img = Image(source.width, source.height)
        first = {(x, y): source.get(x, y) for y in range(source.height) for x in range(w) if source.get(x, y)[3]}
        reference, there = dress(first, armed=name in ARMED), landmarks(first)
        for f in range(source.width // w):
            px = {(x, y): source.get(f * w + x, y) for y in range(source.height) for x in range(w)
                  if source.get(f * w + x, y)[3]}
            here = landmarks(px)
            moved = set()
            if here and there:                           # What isn't where it is on the first frame
                dx, dy = here[1] - there[1], here[0] - there[0]
                moved = {(x, y) for (x, y), c in px.items() if first.get((x - dx, y - dy)) != c}
            dressed = dress(px, moved, name in ARMED)
            if here and there:
                dressed = whole_torso(dressed, here, reference, there)
            for (x, y), c in dressed.items():
                if 0 <= x < w and 0 <= y < source.height:
                    img.set(f * w + x, y, c)
        img.save(OUT / f'{name}.png')
        print(f'rework_cowgirl: {name} ({img.width} x {img.height})')
        if name in ARMED:                                # With the duals, the second on her far hip
            for f in range(source.width // w):
                frame_px = {(x, y): source.get(f * w + x, y) for y in range(source.height) for x in range(w)
                            if source.get(f * w + x, y)[3]}
                at = landmarks(frame_px)
                if at:
                    belt, mid = at
                    drawn = {(x, y): img.get(f * w + x, y) for y in range(source.height) for x in range(w)
                             if img.get(f * w + x, y)[3]}
                    outlined_on(drawn, holster(mid - FAR_HOLSTER, belt))
                    for (x, y), c in drawn.items():
                        if 0 <= x < w and 0 <= y < source.height:
                            img.set(f * w + x, y, c)
            img.save(OUT / f'{name}_dual.png')
    return 0


if __name__ == '__main__':
    sys.exit(main())
