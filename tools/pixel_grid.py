#!/usr/bin/env python3
"""The pixel chart of any reference, and of our sprites beside it: where a design change starts.

Optional review utility, needs Pillow (python3 -m pip install pillow): build.sh never runs it
and it changes no sheet. It finds how big a pixel of the reference is in the image (enlarged,
resampled or a GIF), brings it back to its native grid, cuts its figures out and charts them
with their coordinates, one cell a pixel. Nothing is resized to fit. What is taken from a
reference is its measures (proportions, where each piece is and how thick), never its pixels.

Usage: python3 tools/pixel_grid.py reference.png [--output build/cuadricula]
       ... --ours assets/sprites/characters/cowgirl/suit/stand.png:42:0   one of our frames
           beside them (sheet:frame width:frame), as many as wanted
       ... --figures 1 5      only these of the reference's figures (as numbered without it)
Writes:
  figura_N.png   each figure on its native grid, charted
  nuestra_N.png  each of our frames, charted the same way
  comparacion.png  all of them at one scale, their feet on one line
  tabla.csv      every run of one colour, row by row
  medidas.csv    each figure's size and, row by row, its first and last column
  paleta.csv     its colours and how many pixels each has
"""
from __future__ import annotations

import argparse
import cmath
import csv
import math
import sys
from collections import Counter
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
except ImportError:
    raise SystemExit('Para la cuadrícula: python3 -m pip install pillow') from None

ROOT = Path(__file__).resolve().parent.parent
CELL, BACK, LINE, MARK = 14, (70, 78, 88), (104, 116, 130), (233, 185, 88)
SMALLEST = 60                     # Pixels: less than this is not a figure


def profile(image: Image.Image, axis: int) -> list:
    """How much the image changes at each column (axis 0) or row (1)."""
    moved = ImageChops.offset(image, *((1, 0) if axis == 0 else (0, 1)))
    change = ImageChops.difference(image, moved).convert('L')
    size = (image.width, 1) if axis == 0 else (1, image.height)
    line = list(change.resize(size, Image.Resampling.BOX).getdata())
    line[0] = 0                                           # It wrapped round
    return line


def pixel_size(line: list) -> tuple:
    """(size, offset) of a native pixel along an axis: the comb its edges fall on."""
    mean = sum(line) / len(line)
    level = [v - mean for v in line]
    total = sum(abs(v) for v in level) or 1.
    best = (0., 1., 0j)
    for k in range(int((min(24, len(line) / 4) - 1.6) / .01)):
        size = 1.6 + k * .01
        wave = sum(v * cmath.exp(-2j * math.pi * i / size) for i, v in enumerate(level))
        if abs(wave) > best[0]:
            best = (abs(wave), size, wave)
    if best[0] < .35 * total:                             # No comb: it is native already
        return 1., 0.
    size = best[1]
    return size, (-cmath.phase(best[2]) / (2 * math.pi) * size) % size


def native(image: Image.Image) -> Image.Image:
    """The image one pixel a pixel."""
    image = image.convert('RGBA')
    flat = Image.new('RGB', image.size, BACK)
    flat.paste(image, (0, 0), image)
    (sx, ox), (sy, oy) = (pixel_size(profile(flat, axis)) for axis in (0, 1))
    if sx < 1.5 and sy < 1.5:
        return image
    if abs(sx - round(sx)) < .02 and abs(sy - round(sy)) < .02 and round(sx) == round(sy):
        soft = image                                      # Enlarged by a whole number: exact
    else:
        soft = image.filter(ImageFilter.MedianFilter(3))
    columns = [x for x in (ox - sx / 2 + k * sx for k in range(int(image.width / sx) + 3)) if 0 <= x < image.width]
    rows = [y for y in (oy - sy / 2 + k * sy for k in range(int(image.height / sy) + 3)) if 0 <= y < image.height]
    out = Image.new('RGBA', (len(columns), len(rows)))
    for j, y in enumerate(rows):
        for i, x in enumerate(columns):
            out.putpixel((i, j), soft.getpixel((int(x), int(y))))
    return out


def figures(image: Image.Image) -> list:
    """What stands out of the background, each on its own."""
    seen = [image.getpixel((x, y)) for y in range(image.height) for x in range(image.width)]
    ground = Counter(c for c in seen).most_common(1)[0][0]

    def solid(c):
        return c[3] > 0 and (ground[3] == 0 or sum(abs(a - b) for a, b in zip(c[:3], ground[:3])) > 40)
    left = {(i % image.width, i // image.width) for i, c in enumerate(seen) if solid(c)}
    out = []
    while left:
        group, todo = {left.pop()}, []
        todo.extend(group)
        while todo:
            x, y = todo.pop()
            for q in ((x + a, y + b) for a in (-1, 0, 1) for b in (-1, 0, 1)):
                if q in left:
                    left.discard(q)
                    group.add(q)
                    todo.append(q)
        if len(group) < SMALLEST:
            continue
        x0, y0 = min(x for x, _ in group), min(y for _, y in group)
        figure = Image.new('RGBA', (max(x for x, _ in group) - x0 + 1, max(y for _, y in group) - y0 + 1), (0, 0, 0, 0))
        for x, y in group:
            figure.putpixel((x - x0, y - y0), image.getpixel((x, y)))
        out.append((y0, x0, figure))
    tall = max((f.height for _, _, f in out), default=1)
    return [f for _, _, f in sorted(out, key=lambda o: (o[0] // max(1, tall // 2), o[1]))]


def chart(image: Image.Image, label: str, first: tuple = (0, 0), cell: int = CELL) -> Image.Image:
    """One cell a pixel, with its coordinates; first: the ones of its corner."""
    canvas = Image.new('RGB', (image.width * cell + 40, image.height * cell + 48), BACK)
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 4), label, fill='white')
    for y in range(image.height):
        for x in range(image.width):
            c = image.getpixel((x, y))
            left, top = 32 + x * cell, 32 + y * cell
            draw.rectangle((left, top, left + cell, top + cell), fill=c[:3] if c[3] else BACK, outline=LINE)
        draw.text((6, 32 + y * cell), str(first[1] + y), fill=MARK if (first[1] + y) % 5 == 0 else 'white')
    for x in range(image.width):
        if (first[0] + x) % 5 == 0:
            draw.text((32 + x * cell, 18), str(first[0] + x), fill=MARK)
    return canvas


def ours(spec: str) -> tuple:
    """A frame of one of our sheets, sheet.png:width:frame, trimmed, and where it was."""
    path, width, frame = spec.rsplit(':', 2)
    with Image.open(path) as sheet:
        image = sheet.convert('RGBA').crop((int(frame) * int(width), 0, (int(frame) + 1) * int(width), sheet.height))
    box = image.getbbox()
    return f'{Path(path).parent.name}/{Path(path).stem} {frame}', image.crop(box), box[:2]


def runs(image: Image.Image, y: int) -> list:
    """Runs of one colour on a row: first column, last, colour."""
    out = []
    for x in range(image.width):
        c = image.getpixel((x, y))
        if not c[3]:
            continue
        if out and out[-1][1] == x - 1 and out[-1][2] == c[:3]:
            out[-1][1] = x
        else:
            out.append([x, x, c[:3]])
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('reference', type=Path)
    parser.add_argument('--ours', nargs='*', default=[], metavar='HOJA:ANCHO:CUADRO')
    parser.add_argument('--figures', nargs='*', type=int)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/cuadricula')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    found = []
    with Image.open(args.reference) as image:
        for frame in range(getattr(image, 'n_frames', 1)):
            image.seek(frame)
            found += figures(native(image))
    chosen = [(f'referencia {i}', f, (0, 0)) for i, f in enumerate(found) if args.figures is None or i in args.figures]
    chosen += [ours(spec) for spec in args.ours]
    scale = 6
    board = Image.new('RGB', (sum(f.width + 3 for _, f, _ in chosen) * scale, (max(f.height for _, f, _ in chosen) + 4) * scale), BACK)
    left = 0
    tables = {name: (open(args.output / f'{name}.csv', 'w', encoding='utf-8', newline='\n')) for name in ('tabla', 'medidas', 'paleta')}
    write = {name: csv.writer(f, lineterminator='\n') for name, f in tables.items()}
    write['tabla'].writerow(('figura', 'fila', 'primera_columna', 'ultima_columna', 'ancho', 'color'))
    write['medidas'].writerow(('figura', 'ancho', 'alto', 'fila', 'primera_columna', 'ultima_columna', 'ancho_de_fila'))
    write['paleta'].writerow(('figura', 'color', 'pixeles'))
    for n, (name, figure, at) in enumerate(chosen):
        mine = not name.startswith('referencia')
        chart(figure, f'{name}: {figure.width} x {figure.height}', at).save(
            args.output / (f'nuestra_{n}.png' if mine else f'figura_{name.split()[1]}.png'))
        big = figure.resize((figure.width * scale, figure.height * scale), Image.Resampling.NEAREST)
        board.paste(big, (left, board.height - big.height - 2 * scale), big)
        left += (figure.width + 3) * scale
        for y in range(figure.height):
            row = runs(figure, y)
            for first, last, colour in row:
                write['tabla'].writerow((name, at[1] + y, at[0] + first, at[0] + last, last - first + 1, '%02x%02x%02x' % colour))
            if row:
                write['medidas'].writerow((name, figure.width, figure.height, at[1] + y, at[0] + row[0][0], at[0] + row[-1][1],
                                           row[-1][1] - row[0][0] + 1))
        for colour, count in Counter(c[:3] for c in figure.getdata() if c[3]).most_common(24):
            write['paleta'].writerow((name, '%02x%02x%02x' % colour, count))
    for f in tables.values():
        f.close()
    board.save(args.output / 'comparacion.png')
    print(f'pixel_grid: {len(found)} figuras en la referencia, {len(chosen)} en {args.output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
