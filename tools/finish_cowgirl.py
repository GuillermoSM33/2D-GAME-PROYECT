#!/usr/bin/env python3
"""Finish the cowgirl's sheets: a closed outline and no pinholes, on every frame.

Usage: tools/finish_cowgirl.py   (the last of tools/rebuild_cowgirl.py)

Any colour touching nothing gets an outline pixel beside it; a little gap closed all
round takes the outline. Sparks, flashes and the arcs of a blow are
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


def finish(px: dict, w: int, h: int) -> dict:
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
