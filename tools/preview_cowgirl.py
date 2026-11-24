#!/usr/bin/env python3
"""Review the sheriff's actual sheets without rebuilding or changing assets.

Optional review utility, needs Pillow (python3 -m pip install pillow): build.sh never runs
it. Frames stay on their native grid, enlarged with nearest-neighbour sampling. To measure
her run against the reference: tools/measure_cowgirl_pixels.py.

Usage: python3 tools/preview_cowgirl.py [--output build/sheriff_review]
       ... --source other/cowgirl    sheets of somewhere else (her suit: .../cowgirl/suit)
       ... --before old/cowgirl      older sheets above them on the GIF
Writes:
  sheet.png    every pose of her main actions
  motion.gif   standing, running, pulling up from a run, shooting and reloading, slowed down
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit('Para las vistas previas: python3 -m pip install pillow') from None

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'assets/sprites/characters/cowgirl'
SCALE, CELL_W, CELL_H, BASELINE, COLUMNS = 3, 270, 250, 225, 10
BG, TEXT, LINE = '#444c56', '#eee6d9', '#68727f'
WALK_GRID = {'stand', 'walk', 'legs'}
SHEETS = (('Reposo', 'stand'), ('Carrera', 'walk'), ('Salto', 'jump'), ('Disparo', 'shoot'), ('Recarga', 'reload'),
          ('Duales', 'shoot_dual'), ('Duales / otra mano', 'shoot_dual_b'))
BREATHS = 4                       # PLAYER_STAND_BREATHS: the rest of stand.png pulls up from a run


def grid_of(name: str) -> tuple:
    """Frame size, and the column and row of her feet on it."""
    if name.replace('_dual', '') in WALK_GRID:
        return 42, 67, 19.5, 61
    return (54, 82, 25.5, 69) if name.startswith('jump') else (81, 80, 31.5, 68)


def read_sheets(directory: Path) -> dict:
    sheets = {}
    for _, name in SHEETS:
        with Image.open(directory / (name + '.png')) as image:
            sheets[name] = image.convert('RGBA')
        width, height, _, _ = grid_of(name)
        if sheets[name].width % width or sheets[name].height != height:
            raise SystemExit(f'{directory / name}.png: tamaño de hoja inesperado')
    return sheets


def count(sheets: dict, name: str) -> int:
    return sheets[name].width // grid_of(name)[0]


def place(canvas: Image.Image, sheets: dict, name: str, frame: int, col: int, row: int, label: str) -> None:
    width, height, anchor, ground = grid_of(name)
    sprite = sheets[name].crop((frame * width, 0, (frame + 1) * width, height))
    sprite = sprite.resize((width * SCALE, height * SCALE), Image.Resampling.NEAREST)
    x, y = col * CELL_W, row * CELL_H
    draw = ImageDraw.Draw(canvas)
    draw.line((x + 10, y + BASELINE, x + CELL_W - 10, y + BASELINE), fill=LINE)
    canvas.paste(sprite, (round(x + 110 - anchor * SCALE), y + BASELINE - ground * SCALE), sprite)
    draw.text((x + 12, y + 8), f'{label} / {frame:02d}', fill=TEXT)


def contact_sheet(sheets: dict, path: Path) -> None:
    cells = [(label, name, range(start, min(start + COLUMNS, count(sheets, name))))
             for label, name in SHEETS for start in range(0, count(sheets, name), COLUMNS)]
    canvas = Image.new('RGB', (COLUMNS * CELL_W, len(cells) * CELL_H), BG)
    for row, (label, name, frames) in enumerate(cells):
        for col, frame in enumerate(frames):
            place(canvas, sheets, name, frame, col, row, label)
    canvas.save(path)


def motion(sources: list, path: Path) -> None:
    shown = []
    for tick in range(120):                              # A tick is 1/12 s: half the game's speed at 24 fps
        canvas = Image.new('RGB', (5 * CELL_W, len(sources) * CELL_H), BG)
        for row, (version, sheets) in enumerate(sources):
            run, still = count(sheets, 'walk'), min(BREATHS, count(sheets, 'stand'))
            settles = count(sheets, 'stand') - still
            stop = tick % 40
            poses = [('Reposo', 'stand', tick // 9 % still), ('Carrera', 'walk', tick % run),
                     ('Frenar', 'walk', stop % run) if stop < 20 else
                     ('Frenar', 'stand', still + (stop - 20) // 2) if stop - 20 < 2 * settles else
                     ('Frenar', 'stand', 0),
                     ('Disparo', 'shoot', tick // 2 % count(sheets, 'shoot')),
                     ('Recarga', 'reload', tick // 4 % count(sheets, 'reload'))]
            for col, (label, name, frame) in enumerate(poses):
                place(canvas, sheets, name, frame, col, row, f'{version} / {label}')
        shown.append(canvas)
    # One shared palette: material colours must not flash between GIF frames.
    palette = shown[0].quantize(colors=256, dither=Image.Dither.NONE)
    shown = [image.quantize(palette=palette, dither=Image.Dither.NONE) for image in shown]
    shown[0].save(path, save_all=True, append_images=shown[1:], duration=80, loop=0, disposal=2, optimize=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/sheriff_review')
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--before', type=Path)
    args = parser.parse_args()
    current = read_sheets(args.source)
    sources = [('Antes', read_sheets(args.before))] if args.before else []
    args.output.mkdir(parents=True, exist_ok=True)
    contact_sheet(current, args.output / 'sheet.png')
    motion(sources + [('Actual', current)], args.output / 'motion.gif')
    print(f'preview_cowgirl: {args.output}')


if __name__ == '__main__':
    main()
