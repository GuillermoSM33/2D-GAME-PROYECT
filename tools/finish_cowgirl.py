#!/usr/bin/env python3
"""Finish the cowgirl's sheets: a closed outline, no pinholes and no specks, on every frame.

Usage: tools/finish_cowgirl.py   (the last of tools/rebuild_cowgirl.py)

Any colour touching nothing gets an outline pixel beside it; a little gap closed all
round takes the outline. A pixel or three of her star, scarf or hair left alone beside an
arm, a gun or a leg are not a detail of anything: they take what is round them. Sparks, flashes and the arcs of a blow are
light, not things: they stay as they are. Standard library only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_powers import load  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets/sprites/characters/cowgirl'
INK = (0x25, 0x20, 0x18, 255)
WIDTHS = {'walk': 42, 'walk_dual': 42, 'stand': 42, 'stand_dual': 42, 'legs': 42, 'legs_dual': 42, 'jump': 54, 'jump_dual': 54, 'sit': 72, 'faint': 80}
SKIP = {'flashlight'}             # Drawn over the others
DARK = 70                         # As good as an outline already: its brightest channel under this
SIDES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def is_light(c: tuple) -> bool:
    """A flash, a spark, a blow's arc, a drop, a dozing z."""
    r, g, b = c[:3]
    return (r > 200 and g > 90 and b < 150) or (r > 140 and abs(r - g) < 24 and abs(g - b) < 24 and r != 0xbc) or \
        (r > 225 and g > 225 and b > 190)


SLEEVES = {(0x6c, 0x7a, 0x84), (0x50, 0x5c, 0x66), (0x38, 0x42, 0x4a)}
SCRAP_PASSES = 12
BIGGEST_GAP = 4                   # Art px; an elbow's window is more than this
AROUND = SIDES + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def no_scraps(px: dict) -> dict:
    """A pixel or two of sleeve lying alone on something else, left by a turned arm or
    gun, is outline: it is a scrap of another part."""
    out = dict(px)
    for p, c in px.items():
        if c[:3] in SLEEVES and sum(px.get((p[0] + a, p[1] + b), (0, 0, 0))[:3] in SLEEVES for a, b in AROUND) <= 1:
            out[p] = INK
    return out


STAR = {(0xdb, 0xc5, 0x8d), (0xb6, 0x98, 0x5c), (0x77, 0x60, 0x3c)}
SASH = {(0x74, 0x30, 0x44), (0x99, 0x53, 0x67), (0x4c, 0x26, 0x33)}
HAIR = {(0x6b, 0x33, 0x3a), (0x90, 0x20, 0x04), (0xd0, 0x33, 0x05)}
LEAST = ((STAR, 4), (SASH, 4), (HAIR, 3))  # Fewer together than this, they are specks


def no_specks(px: dict) -> dict:
    out = dict(px)
    for tones, least in LEAST:
        left = {p for p, c in px.items() if c[:3] in tones}
        while left:
            group = {left.pop()}
            todo = list(group)
            while todo:
                x, y = todo.pop()
                for a, b in AROUND:
                    q = (x + a, y + b)
                    if q in left:
                        left.discard(q)
                        group.add(q)
                        todo.append(q)
            if len(group) >= least:
                continue
            for x, y in group:
                near = [px[(x + a, y + b)] for a, b in AROUND if (x + a, y + b) in px and (x + a, y + b) not in group]
                cloth = [c for c in near if c[:3] != INK[:3] and c[:3] not in tones]
                if any((x + a, y + b) not in px for a, b in SIDES):
                    del out[(x, y)]                      # On her edge: her outline closes behind it
                else:
                    out[(x, y)] = max(cloth, key=cloth.count) if len(cloth) >= 3 else INK
    return out


def finish(px: dict, w: int, h: int) -> dict:
    px = no_specks(px)
    for _ in range(SCRAP_PASSES):                        # A short chain goes from its ends
        cleaner = no_scraps(px)
        if cleaner == px:
            break
        px = cleaner
    out = dict(px)
    for (x, y), c in px.items():
        if max(c[:3]) < DARK or is_light(c):
            continue
        for a, b in SIDES:
            at = (x + a, y + b)
            beyond = (x + 2 * a, y + 2 * b)
            if at not in px and beyond not in px and 0 <= at[0] < w and 0 <= at[1] < h:  # A thin gap stays: the gun's rod
                out[at] = INK
    # Little closed gaps (between an arm and her side, say) read as bits missing from her
    seen = set()
    for start in ((x, y) for y in range(h) for x in range(w) if (x, y) not in out):
        if start in seen:
            continue
        gap, todo, closed = [], [start], True
        seen.add(start)
        while todo:
            x, y = todo.pop()
            gap.append((x, y))
            for a, b in SIDES:
                at = (x + a, y + b)
                if not (0 <= at[0] < w and 0 <= at[1] < h):
                    closed = False
                elif at not in out and at not in seen:
                    seen.add(at)
                    todo.append(at)
        if closed and len(gap) <= BIGGEST_GAP:
            out.update({p: INK for p in gap})
    return out


def main() -> int:
    for path in sorted(OUT.glob('*.png')):
        if path.stem in SKIP:
            continue
        img = load(path)
        w = WIDTHS.get(path.stem, 81)
        for f in range(img.width // w):
            px = {(x, y): img.get(f * w + x, y) for y in range(img.height) for x in range(w) if img.get(f * w + x, y)[3]}
            for (x, y), c in finish(px, w, img.height).items():
                img.set(f * w + x, y, c)
        img.save(path)
    print('finish_cowgirl: done')
    return 0


if __name__ == '__main__':
    sys.exit(main())
