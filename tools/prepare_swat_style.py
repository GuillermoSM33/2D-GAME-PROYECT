#!/usr/bin/env python3
"""Import the compact SWAT sheet into the sheriff's native art grid.

Optional authoring command, requires Pillow. Rebuilding the game uses only
the resulting PNG files and Python's standard library. Sources stay intact.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / 'docs/templates/swat'
CELL = 362
PALETTE = [0x252018, 0x29343b, 0x41494a, 0x5d6870, 0x697174, 0x77807b,
           0x483326, 0x6f4d33, 0x916c48, 0xbf8964, 0xd7a786, 0xebc1a4,
           0x354029, 0x607536, 0x9daf50]


def main():
    source = Image.open(ART / 'game_style_source.png').convert('RGBA')
    if source.size != (CELL * 4, CELL * 3):
        raise ValueError('Expected the 1448 x 1086 style sheet, four columns and three rows')
    colors = [tuple((c >> shift) & 255 for shift in (16, 8, 0)) for c in PALETTE]
    def nearest(color, choices):
        return min(choices, key=lambda c: sum((c[k] - color[k]) ** 2 for k in range(3)))
    frames = []
    for f in range(12):
        x, y = f % 4, f // 4
        cell = source.crop((x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL))
        cell.putalpha(cell.getchannel('A').point(lambda a: 255 if a >= 160 else 0))
        bounds = cell.getbbox()
        scale = 56 / (bounds[3] - bounds[1])
        # Align by the helmet, so swinging hands and long guns cannot shift
        # the body. Normalize the whole figure, without separate limb warps.
        head = cell.crop((0, bounds[1], CELL, bounds[1] + 90)).getbbox()
        center = (head[0] + head[2]) / 2
        cell = cell.crop(bounds).resize((round((bounds[2] - bounds[0]) * scale), 56),
                                       Image.Resampling.LANCZOS)
        pixels = []
        for p in range(cell.width * cell.height):
            r, g, b, a = cell.getpixel((p % cell.width, p // cell.width))
            row = p // cell.width
            if a < 128:
                pixels.append((0, 0, 0, 0))
                continue
            if g > r * 1.02 and g > b * 1.25:
                color = nearest((r, g, b), colors[12:])
            elif r - g > 10 and g - b > 8:
                color = nearest((r, g, b), colors[9:12] if row < 23 and r > 130 else colors[6:9])
            else:
                light = .299 * r + .587 * g + .114 * b
                value = light if light < 35 else min(255, light * 1.12 + 5)
                color = nearest((value, value, value), colors[:6])
            pixels.append(color + (255,))
        cell.putdata(pixels)
        # Action references keep the same pivot/ground offset as the game.
        wide = f >= 10
        frame = Image.new('RGBA', (81, 80) if wide else (42, 67))
        ox = round(21 - (center - bounds[0]) * scale) + (12 if wide else 0)
        frame.alpha_composite(cell, (ox, 11 if wide else 4))
        frames.append(frame)
    # One helmet/face for the whole rig, as with the sheriff's shared head.
    head = frames[8].crop((0, 0, 42, 27))
    for cell in frames[:10]:
        cell.paste((0, 0, 0, 0), (0, 0, 42, 27))
        cell.alpha_composite(head)
    # Remove the residual sleeve cap, preserving the full 19-pixel ribcage
    # and belt-side pouch. The shared posed sleeve supplies the shoulder.
    for y in range(26, 38):
        for x in range(13):
            frames[9].putpixel((x, y), (0, 0, 0, 0))
    walk = Image.new('RGBA', (336, 67))
    for f, cell in enumerate(frames[:8]):
        walk.alpha_composite(cell, (f * 42, 0))
    walk.save(ART / 'game_style_walk.png')
    frames[8].save(ART / 'game_style_stand.png')
    frames[9].save(ART / 'game_style_body.png')
    for f, name in ((10, 'rifle'), (11, 'shotgun')):
        frames[f].save(ART / ('game_style_' + name + '_reference.png'))
    print('SWAT style imported: walk, stand, arm-free body and two aiming references')


if __name__ == '__main__':
    main()
