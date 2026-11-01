#!/usr/bin/env python3
"""Make the character base (the mannequin) and its guides from the cowgirl.

Usage: tools/make_character_base.py

Every playable character follows the cowgirl's template (docs/CHARACTERS.md):
the same sheets, frame sizes, poses, pivots and muzzle. This writes:

  docs/templates/character_base/walk.png, jump.png, shoot.png
      Her sheets at 1x in neutral grays: the poses and shading without her
      colors, to paint a new character over (or to give a generator).
  docs/img/character_guide_walk.png, _jump.png, _shoot.png
      The base at 4x with the template's lines: ground (red), pivot (cyan),
      top of the head (green) and, on the aim and fire frames, the muzzle
      (yellow).

Re-run it if the cowgirl's sheets change. Uses only the standard library.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'assets/sprites/characters/cowgirl'
BASE_DIR = ROOT / 'docs/templates/character_base'
GUIDE_DIR = ROOT / 'docs/img'

# name: (frame width, frames, pivot x, ground row); from src/game/player.c.
SHEETS = {
    'walk': (42, 8, 19.5, 61),
    'jump': (54, 8, 25.5, 69),
    'shoot': (81, 8, 31.5, 68),
}
HEAD_HEIGHT = 57              # PLAYER_HEAD_HEIGHT: top of the head above the ground row
MUZZLE = (64, 32.5)           # Muzzle tip on the shoot frames (docs/SPRITES.md)
MUZZLE_FRAMES = (3, 4)        # Aim and fire

OUTLINE = (0x25, 0x20, 0x18)  # The cowgirl's outline: kept as is
# The revolver's neutral grays (docs/ZOMBIE.md), darkest to lightest.
GRAYS = [0x2c2c2c, 0x424242, 0x505050, 0x686868, 0x868689, 0xa7a8a8]
SCALE = 4
GUIDE = {'ground': 0xd04a3a, 'pivot': 0x4ac0d0, 'head': 0x6ac04a, 'muzzle': 0xf0d040,
         'frame': 0x3a3a46, 'back': 0x202229}


def gray_for(r: int, g: int, b: int) -> tuple[int, int, int, int]:
    """Same brightness order as her colors, on the revolver's grays."""
    if (r, g, b) == OUTLINE:
        return (*OUTLINE, 255)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    index = min(len(GRAYS) - 1, int(lum / 256 * len(GRAYS) * 1.25))
    return rgb(GRAYS[index])


def make_base(name: str) -> Image:
    w, h, px = decode_png_rgba(SOURCE / f'{name}.png')
    img = Image(w, h)
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            r, g, b, a = px[i:i + 4]
            if a:
                img.set(x, y, gray_for(r, g, b)[:3] + (a,))
    return img


def make_guide(name: str, base: Image) -> Image:
    frame_w, frames, pivot_x, ground = SHEETS[name]
    w, h = base.width * SCALE, base.height * SCALE
    img = Image(w, h)
    for y in range(h):
        for x in range(w):
            img.set(x, y, rgb(GUIDE['back']))

    def hline(x0: int, x1: int, y: int, color: int) -> None:
        for x in range(max(0, x0), min(w, x1)):
            img.set(x, y, rgb(color))

    def vline(x: int, y0: int, y1: int, color: int) -> None:
        for y in range(max(0, y0), min(h, y1)):
            img.set(x, y, rgb(color))

    for f in range(frames):
        left = f * frame_w * SCALE
        vline(left, 0, h, GUIDE['frame'])
        hline(left, left + frame_w * SCALE, ground * SCALE, GUIDE['ground'])
        hline(left, left + frame_w * SCALE, (ground - HEAD_HEIGHT) * SCALE, GUIDE['head'])
        vline(left + int(pivot_x * SCALE), 0, h, GUIDE['pivot'])
    for y in range(base.height):
        for x in range(base.width):
            c = base.get(x, y)
            if c[3]:
                for dy in range(SCALE):
                    for dx in range(SCALE):
                        img.set(x * SCALE + dx, y * SCALE + dy, c)
    if name == 'shoot':
        mx, my = MUZZLE
        for f in MUZZLE_FRAMES:
            cx, cy = int((f * frame_w + mx) * SCALE), int(my * SCALE)
            hline(cx - 10, cx + 11, cy, GUIDE['muzzle'])
            vline(cx, cy - 10, cy + 11, GUIDE['muzzle'])
    return img


def main() -> int:
    for name in SHEETS:
        base = make_base(name)
        base.save(BASE_DIR / f'{name}.png')
        make_guide(name, base).save(GUIDE_DIR / f'character_guide_{name}.png')
        print(f'make_character_base: {name} ({base.width} x {base.height}) y su guía')
    return 0


if __name__ == '__main__':
    sys.exit(main())
