#!/usr/bin/env python3
"""Import the selected transparent paintings onto the game's native grid.

Authoring only: needs Pillow. Normal builds consume the committed native PNGs
with the standard-library compositor in swat_authored.py. The large originals
and their alpha channels are preserved unchanged.
"""
from pathlib import Path
from statistics import median
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/templates/swat'
DEST = SOURCE / 'authored'
NAMES = ('rifle', 'shotgun', 'rifle_reload', 'shotgun_reload')


def import_frames(name):
    source = Image.open(SOURCE / (name + '_authored_source.png')).convert('RGBA')
    cells = []
    for f in range(8):
        col, row = f % 4, f // 4
        cell = source.crop((round(col * source.width / 4), round(row * source.height / 2),
                            round((col + 1) * source.width / 4), round((row + 1) * source.height / 2)))
        cell.putalpha(cell.getchannel('A').point(lambda a: 255 if a >= 160 else 0))
        cells.append(cell)
    # One uniform scale, never independent limb or width fitting.
    scale = 56 / median(c.getbbox()[3] - c.getbbox()[1] for c in cells)
    frames = []
    for cell in cells:
        box = cell.getbbox()
        # Helmet, not the long gun, determines the horizontal body anchor.
        head = cell.crop((0, box[1], cell.width, box[1] + round((box[3] - box[1]) * .34)))
        hb = head.getbbox()
        center = (hb[0] + hb[2]) / 2
        reduced = cell.resize((round(cell.width * scale), round(cell.height * scale)), Image.Resampling.NEAREST)
        frame = Image.new('RGBA', (81, 80))
        frame.alpha_composite(reduced, (round(32 - center * scale), round(67 - box[3] * scale)))
        frames.append(frame)
    return frames


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    frames = {name: import_frames(name) for name in NAMES}
    # A single restrained palette for both weapons and every hand pose.
    # Explicit skin and optical greens cannot be lost to the much larger area
    # of slate fabric when reducing the palette.
    colors = (0x252018, 0x272c2d, 0x29343b, 0x363d40, 0x41494a, 0x50595e,
              0x5d6870, 0x697174, 0x77807b, 0x96948b, 0x39312c, 0x443931,
              0x5a4638, 0x73553e, 0x967353, 0xb98f71, 0xedc09e,
              0x485222, 0x6b812a, 0x93ae36, 0xb5ca5a, 0xd4d990,
              0x373b3d, 0x505355, 0x727678, 0x969b99, 0x863c2d, 0xc2a66c)
    palette = Image.new('P', (1, 1))
    rgb = [(c >> 16, (c >> 8) & 255, c & 255) for c in colors]
    palette.putpalette([v for c in rgb + [rgb[0]] * (256 - len(rgb)) for v in c])
    for name, sequence in frames.items():
        sheet = Image.new('RGBA', (648, 80))
        for f, frame in enumerate(sequence):
            alpha = frame.getchannel('A')
            frame = frame.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE).convert('RGBA')
            frame.putalpha(alpha)
            # Transparent pixels are canonical zeros for byte-exact rebuilds.
            frame.putdata([p if p[3] else (0, 0, 0, 0) for p in frame.getdata()])
            sheet.alpha_composite(frame, (81 * f, 0))
        sheet.save(DEST / (name + '.png'))
    print('Imported four SWAT pose atlases; originals preserved.')


if __name__ == '__main__':
    main()
