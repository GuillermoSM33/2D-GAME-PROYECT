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
    """A reinforced petroleum-blue field case, navy lining and copper fittings.

    Drawn at native 440 x 240; the inventory uses its exact integer 2x size.
    Pocket rims, folded gussets and broad light planes give the materials
    volume without bright outlines or a flat military-green canvas fill.
    """
    img = Image(440, 240)
    box(img, 7, 1, 432, 238, 0x07101a)
    box(img, 1, 8, 438, 231, 0x07101a)
    box(img, 5, 5, 434, 234, 0x294756)
    rim(img, 6, 6, 433, 233, 0x7b9ea6, 0x0b1a27)
    rim(img, 8, 8, 431, 231, 0x476b7a, 0x101f2d)
    # The aluminium shell is lit on its upper and left planes. Copper trim
    # lies in a recessed channel rather than around every pixel-art object.
    for y, color in ((9, 0x547e8c), (10, 0x3f697b), (11, 0x284e62)):
        box(img, 11, y, 428, y, color)
    box(img, 10, 13, 12, 227, 0x476d7b)
    box(img, 427, 13, 430, 227, 0x132c3d)
    rim(img, 13, 31, 426, 225, 0x9a704d, 0x302b29)
    box(img, 14, 32, 425, 224, 0x0d1c2c)
    # The padded navy apron uses wide shade bands and occasional diagonal
    # stitches; the surface behind item names stays quiet and dark.
    for y in range(33, 224):
        color = 0x132b3b if y < 95 else 0x102535 if y < 164 else 0x0c1e2e
        box(img, 15, y, 424, y, color)
        for x in range(16, 424):
            if (x + y) % 17 == 0 and x < 111:
                img.set(x, y, rgb(0x1b3546))
    # Broad, recessed seams separate the portrait pocket and item apron.
    box(img, 110, 33, 113, 224, 0x081726)
    box(img, 110, 33, 110, 223, 0x355463)
    box(img, 114, 34, 115, 224, 0x284a5d)
    # Title plate: dark enamel held in a thin copper frame, not a label
    # printed onto the canvas. The runtime places its title inside it.
    box(img, 143, 10, 296, 29, 0x091724)
    rim(img, 144, 11, 295, 28, 0xb88859, 0x3c312b)
    box(img, 146, 13, 293, 26, 0x173746)
    box(img, 147, 13, 292, 14, 0x2c5361)
    # Portrait pocket and its folded side walls; the portrait renderer lays
    # its own inner frame over this well and keeps the buckles outside it.
    box(img, 12, 32, 107, 150, 0x071522)
    rim(img, 13, 33, 106, 149, 0x60818b, 0x0b1b2a)
    for x in (15, 101):
        box(img, x, 35, x + 4, 146, 0x263e50)
        box(img, x, 35, x + 1, 145, 0x496575)
        box(img, x + 3, 36, x + 4, 147, 0x142839)
        for y in (43, 132):
            box(img, x - 1, y, x + 5, y + 8, 0xa97850)
            rim(img, x, y + 1, x + 4, y + 7, 0xe0b17b, 0x4e3e32)
            box(img, x + 1, y + 3, x + 3, y + 5, 0x1e3442)
    box(img, 14, 151, 106, 157, 0x1b3546)
    box(img, 14, 151, 106, 151, 0x496a76)
    # The detail pocket has a raised opening and a bevel along its gusset.
    box(img, 12, 159, 107, 214, 0x091826)
    rim(img, 13, 160, 106, 213, 0x63828b, 0x0c1a27)
    box(img, 15, 162, 104, 211, 0x102536)
    box(img, 15, 162, 104, 163, 0x2f5061)
    # A metal rail under the action button and inset rubber closing controls.
    box(img, 117, 216, 426, 235, 0x091a28)
    rim(img, 118, 217, 425, 234, 0x6a8790, 0x102331)
    box(img, 13, 218, 106, 235, 0x142d3d)
    box(img, 14, 218, 105, 218, 0x3d6071)
    # Corner protectors, hinges, stitching and worn screw heads provide the
    # case's silhouette at native size. No uniform shiny edging.
    for x in (7, 416):
        for y in (7, 219):
            box(img, x, y, x + 16, y + 13, 0x142a39)
            rim(img, x + 1, y + 1, x + 15, y + 12, 0x4d6c7a, 0x091624)
            box(img, x + 6, y + 4, x + 10, y + 8, 0xb3845b)
            box(img, x + 7, y + 4, x + 8, y + 7, 0xe6b985)
            box(img, x + 8, y + 5, x + 8, y + 8, 0x3f3a31)
    for y in (48, 180):
        for x in (1, 433):
            box(img, x, y, x + 5, y + 27, 0x102535)
            rim(img, x + 1, y + 1, x + 4, y + 25, 0x6e9099, 0x081522)
            box(img, x + 2, y + 8, x + 3, y + 17, 0xa47451)
    for x in range(29, 411, 9):
        for y in (8, 231): box(img, x, y, x + 2, y, 0x9b8369)
    for y in range(28, 214, 9):
        for x in (8, 431): box(img, x, y, x, y + 2, 0x8c806d)
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
