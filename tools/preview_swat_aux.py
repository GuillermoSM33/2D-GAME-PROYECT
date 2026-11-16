#!/usr/bin/env python3
"""Enlarged, numbered SWAT action boards for visual authoring (optional Pillow)."""
from pathlib import Path
import argparse
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def boards(folder, destination, tag):
    destination.mkdir(parents=True, exist_ok=True)
    for name, width in (('throw', 81), ('throw_shotgun', 81), ('sit', 72), ('sit_shotgun', 72)):
        path = folder / (name + '.png')
        if not path.exists():
            continue
        with Image.open(path) as source:
            source = source.convert('RGBA')
        count = source.width // width
        for start in range(0, count, 8):
            board = Image.new('RGB', (1296, 696), '#dfdcd4')
            draw = ImageDraw.Draw(board)
            for frame in range(start, min(count, start + 8)):
                col, row = (frame - start) % 4, (frame - start) // 4
                cell = source.crop((frame * width, 0, (frame + 1) * width, source.height))
                if name.startswith('sit'):
                    scene = Image.new('RGBA', (81, 80))
                    with Image.open(ROOT / 'assets/sprites/terrain/bench.png') as bench:
                        bench = bench.convert('RGBA').crop((0, 0, 76, 44))
                    scene.paste(bench, (0, 22), bench)
                    scene.paste(cell, (2, 5), cell)
                    cell = scene
                cell = cell.resize((cell.width * 4, cell.height * 4), Image.Resampling.NEAREST)
                board.paste(cell, (col * 324, row * 348 + 24), cell)
                draw.text((col * 324 + 12, row * 348 + 8), f'{name} / {frame:02d}', fill='#34312d')
            board.save(destination / f'{tag}-{name}-{start:02d}.png')
            if name.startswith('sit') and 16 <= start <= 24:
                detail = Image.new('RGB', (1296, 560), '#dfdcd4')
                draw = ImageDraw.Draw(detail)
                for frame in range(start, min(count, start + 8)):
                    col, row = (frame - start) % 4, (frame - start) // 4
                    cell = source.crop((frame * width + 20, 31, frame * width + 58, 59))
                    cell = cell.resize((304, 224), Image.Resampling.NEAREST)
                    detail.paste(cell, (col * 324 + 10, row * 280 + 30), cell)
                    draw.text((col * 324 + 12, row * 280 + 10), f'{name} / detalle {frame:02d}', fill='#34312d')
                detail.save(destination / f'{tag}-{name}-detalle-{start:02d}.png')


def game_review(captures):
    from preview_swat import gif, OUT
    OUT.mkdir(parents=True, exist_ok=True)
    cache = {}
    def shot(name):
        if name not in cache:
            with Image.open(captures / (name + '.bmp')) as source:
                cache[name] = source.convert('RGB').crop((380, 300, 650, 510)).resize((540, 420), Image.Resampling.NEAREST)
        return cache[name]
    frames = []
    for f in range(24):
        board = Image.new('RGB', (1080, 900), '#dfdcd4')
        draw = ImageDraw.Draw(board)
        for row, facing in enumerate(('', '_izq')):
            for col, kind in enumerate(('rifle', 'escopeta')):
                board.paste(shot(f'54_swat_{kind}{facing}_granada_{f}'), (col * 540, row * 450 + 30))
                draw.text((col * 540 + 12, row * 450 + 10), f'Granada / {kind}{facing} / {f:02d}', fill='#34312d')
        frames.append(board)
    gif(frames, 'swat_granada_juego.gif', [60, 60, 60, 70] * 6)
    sequence = [('sentarse', f) for f in range(8)]
    sequence += [('banco_rifle', f) for f in range(24)]
    sequence += [('banco_escopeta', f) for f in range(24)]
    sequence += [('reposo', None)] * 4
    frames = []
    for action, f in sequence:
        board = Image.new('RGB', (1080, 900), '#dfdcd4')
        draw = ImageDraw.Draw(board)
        for row, facing in enumerate(('', '_izq')):
            for col, kind in enumerate(('rifle', 'escopeta')):
                name = f'54_swat_{kind}{facing}_{action}' + (f'_{f}' if f is not None else '')
                board.paste(shot(name), (col * 540, row * 450 + 30))
                draw.text((col * 540 + 12, row * 450 + 10), f'Comienza con {kind}{facing} / {action}', fill='#34312d')
        frames.append(board)
    gif(frames, 'swat_banco_juego.gif', [120, 130] * 4 + [110, 120, 120] * 16 + [120] * 4)
    names = ('rifle_granada_6', 'rifle_granada_9', 'rifle_granada_15',
             'rifle_izq_granada_9', 'rifle_izq_granada_15', 'rifle_izq_granada_18',
             'rifle_sentarse_7', 'rifle_banco_rifle_8', 'rifle_banco_escopeta_7',
             'escopeta_izq_sentarse_3', 'escopeta_izq_banco_rifle_14', 'escopeta_izq_banco_escopeta_18')
    board = Image.new('RGB', (1620, 1800), '#dfdcd4')
    draw = ImageDraw.Draw(board)
    for i, name in enumerate(names):
        col, row = i % 3, i // 3
        board.paste(shot('54_swat_' + name), (col * 540, row * 450 + 30))
        draw.text((col * 540 + 12, row * 450 + 10), name, fill='#34312d')
    board.save(OUT / 'swat_aux_poses.png')
    # The initial seated reaches, enlarged in the actual scenery, for checking
    # the shoulder/elbow/wrist continuity without the rest of the action board.
    board = Image.new('RGB', (1344, 580), '#dfdcd4')
    draw = ImageDraw.Draw(board)
    for row, facing in enumerate(('', '_izq')):
        for frame in range(4):
            with Image.open(captures / f'54_swat_escopeta{facing}_sentarse_{frame}.bmp') as source:
                detail = source.convert('RGB').crop((397, 360, 565, 490))
            board.paste(detail.resize((336, 260), Image.Resampling.NEAREST), (frame * 336, row * 290 + 30))
            draw.text((frame * 336 + 12, row * 290 + 10),
                      f'Sentarse / {"izquierda" if row else "derecha"} / {frame:02d}', fill='#34312d')
    board.save(OUT / 'swat_banco_brazos_juego.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', nargs='?', type=Path, default=ROOT / 'assets/sprites/characters/swat')
    parser.add_argument('tag', nargs='?', default='review')
    parser.add_argument('--captures', type=Path)
    args = parser.parse_args()
    boards(args.folder, ROOT / 'build/swat-aux', args.tag)
    if args.captures:
        game_review(args.captures)
