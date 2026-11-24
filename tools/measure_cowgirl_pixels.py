#!/usr/bin/env python3
"""Measure the sheriff's run pixel by pixel beside the reference it was read from.

Optional review utility, needs Pillow (python3 -m pip install pillow): build.sh never runs
it and it changes no sheet. Both stay on their native grid, one cell per pixel, the belt on
the same row; nothing is resized to fit. The grids are there to be looked at: the numbers
alone do not tell whether a leg or a step reads right.

Usage: python3 tools/measure_cowgirl_pixels.py [--reference walk.gif] [--source walk.png]
                                               [--output build/sheriff_medidas]
Writes:
  tabla.csv           every run of pixels of hips and legs, row by row, of both
  grosores.csv        each leg's thickness across its thigh, knee and calf, where it is in sight
  cuadricula_K.png    key K of the reference and the frame that plays it, gridded
  fases.png           the ten keys over the ten frames
  carrera.gif         both running, each at its own speed
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit('Para medir: python3 -m pip install pillow') from None

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cowgirl_legs as legs  # noqa: E402
import cowgirl_pose as pose  # noqa: E402
import cowgirl_torso as figure  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 42, 67
REFERENCE = ROOT / 'build/prototipo_sheriff_v2/objetivo/walk.gif'   # The user's, 4x, two characters side by side
REFERENCE_BOX, REFERENCE_AT = (0, 31, 48, 98), (6, 1)               # Hers, and where it goes for both belts to agree
HIPS, GROUND = pose.BELT + 2, 61                                    # Rows measured
OTHERS = {c[:3] for c in figure.SASH_TONES} | {(0x6b, 0x33, 0x3a), (0x90, 0x20, 0x04), (0xd0, 0x33, 0x05)}
SECTIONS = (('muslo', 0, .45), ('rodilla', 0, 1.), ('pantorrilla', 1, .5))
CELL, BACK, LINE, MARK = 14, (70, 78, 88), (104, 116, 130), (233, 185, 88)


def reference_keys(path: Path) -> list:
    """Her ten keys on their native grid, on a frame like ours."""
    out = []
    with Image.open(path) as gif:
        if gif.size != (512, 512) or gif.n_frames != pose.KEYS:
            raise SystemExit(f'{path}: se esperaba el GIF de la referencia, 512 x 512 y {pose.KEYS} cuadros')
        for key in range(pose.KEYS):
            gif.seek(key)
            native = gif.convert('RGBA').resize((128, 128), Image.Resampling.NEAREST).crop(REFERENCE_BOX)
            frame = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            frame.paste(native, REFERENCE_AT, native)
            out.append(frame)
    return out


def our_frames(path: Path) -> list:
    with Image.open(path) as sheet:
        if sheet.size != (W * pose.FRAMES, H):
            raise SystemExit(f'{path}: se esperaban {pose.FRAMES} cuadros de {W} x {H}')
        sheet = sheet.convert('RGBA')
        return [sheet.crop((f * W, 0, (f + 1) * W, H)) for f in range(pose.FRAMES)]


def frame_of(key: int) -> int:
    return (key - pose.FIRST_KEY) * 2 % pose.FRAMES


def drawn(image: Image.Image, x: int, y: int) -> bool:
    """A pixel of hips, legs or boots: not the scarf or the hair hanging beside them."""
    if not (0 <= x < W and 0 <= y < H):
        return False
    c = image.getpixel((x, y))
    return c[3] > 0 and c[:3] not in OTHERS


def runs(image: Image.Image, y: int) -> list:
    out, start = [], None
    for x in range(W + 1):
        if drawn(image, x, y) and start is None:
            start = x
        elif not drawn(image, x, y) and start is not None:
            out.append((start, x - 1))
            start = None
    return out


def thickness(image: Image.Image, chain: tuple, bone: int, t: float) -> float:
    """Across a leg at a point of it, outline included, in art px."""
    a, b = chain[bone][:2], chain[bone + 1][:2]
    at = tuple(p + (q - p) * t for p, q in zip(a, b))
    length = math.dist(a, b) or 1.
    across = (-(b[1] - a[1]) / length, (b[0] - a[0]) / length)
    total = 0.
    for sign in (-1, 1):
        d = 0.
        while d < 12 and drawn(image, round(at[0] + across[0] * d * sign), round(at[1] + across[1] * d * sign)):
            d += .25
        total += d
    return total


def grid(image: Image.Image, label: str) -> Image.Image:
    canvas = Image.new('RGB', (W * CELL + 40, (H - 34) * CELL + 48), BACK)
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 4), label, fill='white')
    for y in range(34, H):
        for x in range(W):
            c = image.getpixel((x, y))
            left, top = 32 + x * CELL, 32 + (y - 34) * CELL
            draw.rectangle((left, top, left + CELL, top + CELL), fill=c[:3] if c[3] else BACK, outline=LINE)
        draw.text((6, 32 + (y - 34) * CELL), str(y), fill='white' if y % 5 else MARK)
    for x in range(0, W, 5):
        draw.text((32 + x * CELL, 18), str(x), fill='white')
    top = 32 + (pose.BELT - 34) * CELL
    draw.line((32, top, 32 + W * CELL, top), fill=MARK)
    return canvas


def phases(keys: list, frames: list) -> Image.Image:
    scale = 6
    canvas = Image.new('RGB', (pose.KEYS * W * scale, 2 * H * scale), BACK)
    for key in range(pose.KEYS):
        for row, image in enumerate((keys[key], frames[frame_of(key)])):
            big = image.resize((W * scale, H * scale), Image.Resampling.NEAREST)
            canvas.paste(big, (key * W * scale, row * H * scale), big)
    return canvas


def running(keys: list, frames: list, path: Path) -> None:
    """One cell of 1/24 s: our cycle is 20 of them, the reference's ten keys of 100 ms are 24."""
    scale, ticks, shown = 5, 120, []
    for tick in range(ticks):
        canvas = Image.new('RGB', (2 * W * scale, H * scale), BACK)
        for col, image in enumerate((keys[int(tick / 24 * 10) % pose.KEYS], frames[tick % pose.FRAMES])):
            big = image.resize((W * scale, H * scale), Image.Resampling.NEAREST)
            canvas.paste(big, (col * W * scale, 0), big)
        shown.append(canvas)
    palette = shown[0].quantize(colors=128, dither=Image.Dither.NONE)
    shown = [image.quantize(palette=palette, dither=Image.Dither.NONE) for image in shown]
    shown[0].save(path, save_all=True, append_images=shown[1:], duration=42, loop=0, disposal=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--reference', type=Path, default=REFERENCE)
    parser.add_argument('--source', type=Path, default=ROOT / 'assets/sprites/characters/cowgirl/walk.png')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/sheriff_medidas')
    args = parser.parse_args()
    keys, frames = reference_keys(args.reference), our_frames(args.source)
    args.output.mkdir(parents=True, exist_ok=True)
    subjects = [('referencia', key, '', keys[key]) for key in range(pose.KEYS)]
    subjects += [('sheriff', pose.phase_of(f) % pose.KEYS, f, frames[f]) for f in range(pose.FRAMES)]
    with open(args.output / 'tabla.csv', 'w', encoding='utf-8', newline='\n') as out:
        table = csv.writer(out, lineterminator='\n')
        table.writerow(('quien', 'fase', 'cuadro', 'fila', 'tramo', 'primera_columna', 'ultima_columna', 'ancho'))
        for who, key, f, image in subjects:
            for y in range(HIPS, GROUND + 1):
                for i, (first, last) in enumerate(runs(image, y)):
                    table.writerow((who, key, f, y, i, first, last, last - first + 1))
    with open(args.output / 'grosores.csv', 'w', encoding='utf-8', newline='\n') as out:
        table = csv.writer(out, lineterminator='\n')
        table.writerow(('quien', 'fase', 'cuadro', 'pierna', 'tramo', 'grosor', 'nota'))
        for who, key, f, image in subjects:
            at = f if who == 'sheriff' else frame_of(key)
            for far in (False, True):
                chain = pose.leg_chain(at, far)
                for name, bone, t in SECTIONS:
                    wide = thickness(image, chain, bone, t)
                    note = 'tapada o junto a la otra pierna' if not 1 < wide < 11 else ''
                    table.writerow((who, key, f, 'lejana' if far else 'cercana', name, f'{wide:.2f}', note))
    for key in range(pose.KEYS):
        pair = [grid(keys[key], f'Referencia, clave {key}'), grid(frames[frame_of(key)], f'Sheriff, cuadro {frame_of(key)}')]
        canvas = Image.new('RGB', (pair[0].width * 2, pair[0].height), BACK)
        for col, image in enumerate(pair):
            canvas.paste(image, (col * image.width, 0))
        canvas.save(args.output / f'cuadricula_{key}.png')
    phases(keys, frames).save(args.output / 'fases.png')
    running(keys, frames, args.output / 'carrera.gif')
    print(f'measure_cowgirl_pixels: {args.output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
