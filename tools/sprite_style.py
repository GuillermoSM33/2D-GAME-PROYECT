#!/usr/bin/env python3
"""Compare a sprite sheet's level of detail with the cowgirl's walk sheet.

Usage: tools/sprite_style.py SHEET.png FRAME_WIDTH

Per frame it reports the visible area, the bounding box and the share of
"loose" pixels (no orthogonal neighbor of the same color). Too many make the
art look grainy at 4x; too few make it look flat and unfinished. It also checks
the value balance: the cowgirl is a dark mass with a few bright accents.
Uses only the standard library.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402

REFERENCE = Path(__file__).resolve().parent.parent / 'assets/sprites/player/walk.png'
REFERENCE_FRAME_W = 42

# Ranges for an enemy of the same style, around the cowgirl's own numbers
# (16 colors, 15% loose pixels, ~920 visible px, 85% dark and 14% bright).
COLORS = (13, 16)
LOOSE = (0.11, 0.17)
AREA_RATIO = (0.9, 1.25)
DARK = (0.65, 0.90)   # Luminance below DARK_LUMA: the body's mass
BRIGHT = (0.08, 0.20)  # Luminance above BRIGHT_LUMA: skin, eyes, highlights
DARK_LUMA = 85
BRIGHT_LUMA = 120


def frames(path: Path, frame_w: int):
    width, height, rgba = decode_png_rgba(path)
    if width % frame_w:
        raise SystemExit(f'{path}: el ancho {width} no es múltiplo de {frame_w}')
    for k in range(width // frame_w):
        pixels = {}
        for y in range(height):
            for x in range(frame_w):
                i = (y * width + k * frame_w + x) * 4
                if rgba[i + 3]:
                    pixels[(x, y)] = rgba[i:i + 3]
        yield pixels


def luma(c: bytes) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def stats(pixels: dict) -> tuple[int, int, int, float]:
    loose = sum(
        1 for (x, y), c in pixels.items()
        if all(pixels.get(q) != c for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))))
    xs = [x for x, _ in pixels]
    ys = [y for _, y in pixels]
    return len(pixels), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, loose / len(pixels)


def sheet_report(path: Path, frame_w: int) -> dict:
    colors = set()
    areas, looses = [], []
    dark = bright = total = 0
    for k, pixels in enumerate(frames(path, frame_w)):
        colors.update(pixels.values())
        lumas = [luma(c) for c in pixels.values()]
        dark += sum(1 for v in lumas if v < DARK_LUMA)
        bright += sum(1 for v in lumas if v > BRIGHT_LUMA)
        total += len(lumas)
        area, w, h, loose = stats(pixels)
        areas.append(area)
        looses.append(loose)
        print(f'  cuadro {k}: {area:5d} px visibles, caja {w} × {h}, sueltos {loose:4.0%}')
    return {
        'colors': len(colors),
        'area': sum(areas) / len(areas),
        'loose': sum(looses) / len(looses),
        'dark': dark / total,
        'bright': bright / total,
    }


def in_range(value: float, bounds: tuple[float, float]) -> str:
    if value < bounds[0]:
        return 'POCO '
    if value > bounds[1]:
        return 'MUCHO'
    return 'OK   '


def percent(bounds: tuple[float, float]) -> str:
    return f'{bounds[0]:.0%}–{bounds[1]:.0%}'


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    print(f'Referencia: {REFERENCE.name} (vaquera)')
    ref = sheet_report(REFERENCE, REFERENCE_FRAME_W)
    path = Path(sys.argv[1])
    print(f'\nHoja: {path}')
    got = sheet_report(path, int(sys.argv[2]))

    area_range = (ref['area'] * AREA_RATIO[0], ref['area'] * AREA_RATIO[1])
    checks = [
        (in_range(got['colors'], COLORS),
         f"Colores: {got['colors']} (vaquera {ref['colors']}, rango {COLORS[0]}–{COLORS[1]})"),
        (in_range(got['loose'], LOOSE),
         f"Píxeles sueltos: {got['loose']:.0%} (vaquera {ref['loose']:.0%}, rango {percent(LOOSE)})"),
        (in_range(got['area'], area_range),
         f"Área media: {got['area']:.0f} px (vaquera {ref['area']:.0f}, "
         f"rango {area_range[0]:.0f}–{area_range[1]:.0f})"),
        (in_range(got['dark'], DARK),
         f"Tonos oscuros: {got['dark']:.0%} (vaquera {ref['dark']:.0%}, rango {percent(DARK)})"),
        (in_range(got['bright'], BRIGHT),
         f"Acentos claros: {got['bright']:.0%} (vaquera {ref['bright']:.0%}, rango {percent(BRIGHT)})"),
    ]
    print()
    for verdict, text in checks:
        print(f'{verdict} {text}')
    return 0 if all(v.startswith('OK') for v, _ in checks) else 1


if __name__ == '__main__':
    sys.exit(main())
