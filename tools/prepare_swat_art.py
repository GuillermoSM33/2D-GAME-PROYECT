#!/usr/bin/env python3
"""Prepare the approved generated SWAT walk for the native sprite grid.

Optional authoring step: python3 tools/prepare_swat_art.py (requires Pillow).
The regular rebuild and game build only read the resulting RGBA PNG and use
the standard library. The generated source and original hand drawing stay intact.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs/templates/swat/tactical_walk_source.png'
OUTPUT = ROOT / 'docs/templates/swat/tactical_walk_native.png'
CELL = (362, 543)
SCALE = 56 / 418


def main():
    source = Image.open(SOURCE).convert('RGBA')
    if source.size != (CELL[0] * 4, CELL[1] * 2):
        raise ValueError('Expected the approved 4 x 2 sheet at 1448 x 1086')
    frames = []
    for f in range(8):
        x, y = f % 4, f // 4
        cell = source.crop((x * CELL[0], y * CELL[1], (x + 1) * CELL[0], (y + 1) * CELL[1]))
        # Ignore faint source alpha outside the actual cutouts. The whole
        # sheet uses one uniform scale and one fixed origin, never limb scaling.
        cell.putalpha(cell.getchannel('A').point(lambda a: 255 if a >= 160 else 0))
        cell = cell.resize((round(CELL[0] * SCALE), round(CELL[1] * SCALE)), Image.Resampling.LANCZOS)
        cell.putalpha(cell.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
        frame = Image.new('RGBA', (42, 67))
        frame.alpha_composite(cell, (-6, -5))
        frames.append(frame)
    sheet = Image.new('RGBA', (336, 67))
    for f, frame in enumerate(frames):
        sheet.alpha_composite(frame, (f * 42, 0))
    # One palette for the complete cycle prevents frame-by-frame color changes.
    sheet = sheet.quantize(colors=32, method=Image.Quantize.FASTOCTREE,
                           dither=Image.Dither.NONE).convert('RGBA')
    sheet.save(OUTPUT)
    print(f'Prepared {OUTPUT.relative_to(ROOT)}: 8 frames of 42 x 67')


if __name__ == '__main__':
    main()
