#!/usr/bin/env python3
"""Native pixel art for the field inventory, train tablet and room diagrams.

Runtime text, counts and markers sit over these surfaces at an integer 2x.
Standard library only; --verify compares the installed PNGs without edits.
"""
import argparse
from pathlib import Path
import tempfile

from make_sprites import Image

ROOT = Path(__file__).resolve().parents[1]


def rgb(value):
    return (value >> 16 & 255, value >> 8 & 255, value & 255, 255)


def box(img, x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            img.set(x, y, rgb(color))


def rim(img, x0, y0, x1, y1, light, dark):
    box(img, x0, y0, x1, y0, light)
    box(img, x0, y0, x0, y1, light)
    box(img, x0, y1, x1, y1, dark)
    box(img, x1, y0, x1, y1, dark)


def tablet():
    img = Image(448, 252)
    box(img, 6, 1, 441, 250, 0x090e10)
    box(img, 1, 6, 446, 245, 0x090e10)
    box(img, 4, 4, 443, 247, 0x253132)
    rim(img, 5, 5, 442, 246, 0x59655f, 0x10191b)
    rim(img, 7, 7, 440, 244, 0x36433e, 0x152023)
    # Reinforced rubber bumpers with shallow ribs and worn screw heads.
    for x in (7, 425):
        for y in (7, 231):
            box(img, x, y, x + 15, y + 13, 0x172124)
            for k in range(3): box(img, x + 2, y + 2 + k * 4, x + 12, y + 3 + k * 4, 0x303d3c)
            box(img, x + 6, y + 5, x + 9, y + 8, 0x7a8275)
            box(img, x + 7, y + 5, x + 7, y + 8, 0x1c292c)
    # Screen inset. A sparse drafting grid belongs to the tablet, not the world.
    box(img, 12, 12, 435, 239, 0x070e12)
    box(img, 14, 14, 433, 237, 0x10292d)
    for y in range(15, 237):
        if y % 3 == 0: box(img, 15, y, 432, y, 0x0e2429)
        if y % 12 == 0: box(img, 15, y, 432, y, 0x183337)
    for x in range(18, 433, 12): box(img, x, 15, x, 236, 0x163135)
    rim(img, 13, 13, 434, 238, 0x060d10, 0x63776c)
    # Speaker, camera and three physical keys, all outside the screen.
    for x in range(174, 266, 4): box(img, x, 7, x + 1, 8, 0x0b1317)
    box(img, 272, 6, 276, 10, 0x0a161d)
    box(img, 273, 7, 274, 8, 0x557d8a)
    for y in (73, 118, 163):
        box(img, 437, y, 441, y + 20, 0x0c171a)
        rim(img, 438, y + 1, 440, y + 18, 0x45544f, 0x172226)
    return img


def inventory():
    img = Image(360, 215)
    box(img, 5, 5, 354, 211, 0x141a18)
    box(img, 1, 10, 358, 206, 0x141a18)
    box(img, 6, 6, 353, 208, 0x4a4938)
    rim(img, 7, 7, 352, 207, 0x77735a, 0x242a24)
    box(img, 12, 23, 347, 201, 0x282d27)
    # Canvas apron, restrained diagonal weave, leather binding and stitching.
    for y in range(24, 201):
        for x in range(13, 347):
            if (x + y) % 8 == 0: img.set(x, y, rgb(0x30352b))
    for y in range(14, 204, 5):
        for x in (9, 349): box(img, x, y, x, y + 1, 0x999074)
    for x in range(15, 346, 5):
        for y in (10, 204): box(img, x, y, x + 1, y, 0x999074)
    # Name strip and the portrait's secured equipment pocket.
    box(img, 107, 10, 253, 24, 0x1c2521)
    rim(img, 108, 11, 252, 23, 0x6a7158, 0x111a17)
    box(img, 12, 27, 94, 164, 0x111a18)
    rim(img, 13, 28, 93, 163, 0x777760, 0x171d17)
    for x in (17, 86):
        box(img, x, 30, x + 4, 158, 0x4c4534)
        box(img, x + 1, 31, x + 2, 157, 0x71624a)
        for y in (40, 142):
            box(img, x - 1, y, x + 5, y + 8, 0x9c9576)
            box(img, x, y + 2, x + 4, y + 6, 0x33392e)
    # Side binding, hinges and carrying latches give the board its own silhouette.
    for y in (45, 150):
        box(img, 1, y, 6, y + 24, 0x232e2a)
        rim(img, 2, y + 1, 5, y + 22, 0x6d7866, 0x0f1917)
        box(img, 353, y, 358, y + 24, 0x232e2a)
        rim(img, 354, y + 1, 357, y + 22, 0x6d7866, 0x0f1917)
    for x in (20, 330):
        box(img, x, 2, x + 9, 11, 0x252d26)
        rim(img, x + 1, 3, x + 8, 10, 0x8d8769, 0x151d18)
    return img


def rooms():
    img = Image(44 * 15, 22)
    for room in range(15):
        ox = room * 44
        box(img, ox, 9, ox + 43, 12, 0x365e60)  # Couplings join each little car.
        for x in (6, 30):
            box(img, ox + x, 0, ox + x + 7, 2, 0x092125)
            box(img, ox + x, 19, ox + x + 7, 21, 0x092125)
        box(img, ox + 3, 2, ox + 40, 19, 0x80aca7)
        box(img, ox + 4, 3, ox + 39, 18, 0x1e4c51)
        rim(img, ox + 5, 4, ox + 38, 17, 0x537d7b, 0x0a292e)
        box(img, ox + 6, 5, ox + 37, 16, 0x163d43)
        for x in range(9, 37, 7): box(img, ox + x, 5, ox + x, 16, 0x21484c)
        # Furniture as a cutaway plan: silhouettes stay distinct at native size.
        if room == 0:  # Decontamination cell, hooks, locker.
            box(img, ox + 7, 6, ox + 14, 15, 0x649b94)
            box(img, ox + 8, 7, ox + 13, 14, 0x224c56)
            for x in (20, 25): box(img, ox + x, 7, ox + x + 2, 13, 0xb5ae64)
            box(img, ox + 32, 6, ox + 36, 15, 0x587f78)
        elif room in (3, 10):  # Beds, curtains, trolley.
            for x in (8, 25):
                box(img, ox + x, 7, ox + x + 9, 14, 0x91aaa0)
                box(img, ox + x + 1, 8, ox + x + 2, 13, 0xcee0c8)
            box(img, ox + 20, 5, ox + 20, 15, 0x4b8b8c)
        elif room in (2, 6):  # Culture/cryo cylinders.
            for x in (8, 16, 24, 32):
                box(img, ox + x, 7, ox + x + 4, 14, 0x7caca2)
                box(img, ox + x + 1, 8, ox + x + 3, 13, 0x306d73 if room == 6 else 0x67965e)
        elif room == 8:  # Bunks, separate aisle.
            for x in (8, 19, 30):
                box(img, ox + x, 6, ox + x + 7, 9, 0x8b9c7c)
                box(img, ox + x, 12, ox + x + 7, 15, 0x657e6e)
        elif room == 9:  # Galley and mess table.
            box(img, ox + 7, 6, ox + 12, 15, 0xabbcaf)
            box(img, ox + 15, 6, ox + 22, 9, 0x5c8782)
            box(img, ox + 26, 8, ox + 36, 13, 0xb19e6b)
            box(img, ox + 27, 6, ox + 35, 6, 0x6b8975)
            box(img, ox + 27, 15, ox + 35, 15, 0x6b8975)
        elif room == 13:  # Diesel block and flywheel.
            box(img, ox + 8, 6, ox + 27, 15, 0x718f81)
            for x in range(11, 27, 4): box(img, ox + x, 7, ox + x + 1, 14, 0x2b5352)
            box(img, ox + 31, 8, ox + 35, 13, 0x93aa8b)
        elif room == 14:  # Console and forward cab windows.
            box(img, ox + 10, 6, ox + 19, 14, 0x748f78)
            box(img, ox + 11, 7, ox + 18, 9, 0xd5b96e)
            box(img, ox + 32, 5, ox + 37, 8, 0x7eb2b0)
            box(img, ox + 32, 13, ox + 37, 16, 0x7eb2b0)
        else:
            for x in (8, 26):
                box(img, ox + x, 6, ox + x + 9, 10, 0x7da298)
                for k in range(3): box(img, ox + x + 1 + k * 3, 7, ox + x + 2 + k * 3, 9, 0x2e6262)
            if room in (1, 7, 11, 12):
                box(img, ox + 12, 13, ox + 32, 15, 0x597d73)
    return img


def build():
    return {'field_tablet': tablet(), 'field_inventory': inventory(), 'train_map_rooms': rooms()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    differences = 0
    with tempfile.TemporaryDirectory() as temporary:
        for name, img in build().items():
            target = ROOT / 'assets/sprites/ui' / (name + '.png')
            if args.verify:
                probe = Path(temporary) / 'sheet.png'
                img.save(probe)
                differences += not target.is_file() or target.read_bytes() != probe.read_bytes()
            else:
                img.save(target)
    print(f'field UI: 3 sheets; {differences} differences')
    return bool(differences)


if __name__ == '__main__':
    raise SystemExit(main())
