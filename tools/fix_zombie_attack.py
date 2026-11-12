#!/usr/bin/env python3
"""Rebuild the lunge of every generated zombie family's attack.

Usage: tools/fix_zombie_attack.py [assets_dir]   (default: assets)

tools/make_zombies.py maps each family onto the riot zombie's poses. In its
attack the riot leans its helmet forward for two frames (2 and 3): there the
mapping left the helmet and visor standing, dyed like hair with the riot's
eye in it, beside the family's own head: two heads. This rebuilds those two
frames from the family's own clean frame after them (4, the arm already
out), leaned into the blow, and puts the shared slash back over it. Run it
after make_zombies.py exports a family; tools/make_city_zombies.py dyes the
city's family from the fixed sheets. Idempotent; standard library only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image  # noqa: E402
from make_zombies import FRAME, IDS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKIP = {'riot', 'elite', 'riot_shield', 'dog'}   # The originals; a shield bash and a dog of their own
LUNGE = {2: (3, 1), 3: (2, 0)}                    # Frame: how far frame 4's body leans into it (dx, dy)
CLEAN = 4


def load(path: Path) -> Image:
    width, height, rgba = decode_png_rgba(path)
    img = Image(width, height)
    img.px = [tuple(rgba[i:i + 4]) for i in range(0, len(rgba), 4)]
    return img


def slash_mask(riot: Image, frame: int) -> set:
    """Where the shared slash is drawn: the riot's own frame has nothing else
    red or dark red out in front of its arm."""
    cells = set()
    for y in range(FRAME):
        for x in range(44, FRAME):
            r, g, b, a = riot.get(frame * FRAME + x, y)
            if a and r > g + 40 and r > b + 30:
                cells.add((x, y))
    return cells


def fix(sheet: Image, riot: Image) -> bool:
    before = list(sheet.px)
    clean = [[sheet.get(CLEAN * FRAME + x, y) for x in range(FRAME)] for y in range(FRAME)]
    for frame, (dx, dy) in LUNGE.items():
        mask = slash_mask(riot, frame)
        slash = {cell: sheet.get(frame * FRAME + cell[0], cell[1]) for cell in mask}
        for y in range(FRAME):
            for x in range(FRAME):
                sx, sy = x - dx, y - dy
                inside = 0 <= sx < FRAME and 0 <= sy < FRAME
                sheet.set(frame * FRAME + x, y, clean[sy][sx] if inside else (0, 0, 0, 0))
        for (x, y), color in slash.items():
            if color[3]:
                sheet.set(frame * FRAME + x, y, color)
    return sheet.px != before


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'assets'
    riot = load(ROOT / 'assets/sprites/zombies/riot/attack.png')
    for identifier in IDS:
        if identifier in SKIP:
            continue
        path = assets / 'sprites/zombies' / identifier / 'attack.png'
        sheet = load(path)
        changed = fix(sheet, riot)
        if changed:
            sheet.save(path)
        print(f'fix_zombie_attack: {identifier}: {"rebuilt" if changed else "already clean"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
