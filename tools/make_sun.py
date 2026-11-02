#!/usr/bin/env python3
"""Paints a whole sun on the sunset skies, high over the horizon.

The skies were drawn with half a sun sitting on a band of the sky, which read
as a sun cut off by nothing. This wipes any sun from the sky (its bands are
level, so each row goes back to its first column's color) and draws a round
one higher up, in the same colors. Running it again gives the same images.

Usage: tools/make_sun.py [assets_dir]   (default: assets)
Only the standard library.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image  # noqa: E402

# Theme -> (center x, center y, radius, rim, middle, core), colors from the art.
SUNS = {
    'atardecer': (211, 38, 9, (225, 119, 39), None, (254, 217, 128)),
    'pueblo_fantasma': (196, 40, 8, (144, 32, 4), (208, 51, 5), (229, 93, 34)),
}
# Rows the old sun could be on (above the plain band at the bottom).
SUN_ROWS = range(20, 62)


def make_sky(path: Path, cx: int, cy: int, r: int, rim, middle, core) -> Image:
    w, h, px = decode_png_rgba(path)
    img = Image(w, h)
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            img.set(x, y, tuple(px[i:i + 4]))
    sun = {rim, core} | ({middle} if middle else set())
    for y in SUN_ROWS:
        band = img.get(0, y)
        for x in range(w):
            if img.get(x, y)[:3] in sun:
                img.set(x, y, band)
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d > r + 0.3:
                continue
            if d > r - 1.2:
                c = rim
            elif middle and d > r - 3.0:
                c = middle
            else:
                c = core
            img.set(x, y, c + (255,))
    return img


def main() -> int:
    assets = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('assets')
    for theme, (cx, cy, r, rim, middle, core) in SUNS.items():
        path = assets / 'backgrounds' / theme / 'sky.png'
        make_sky(path, cx, cy, r, rim, middle, core).save(path)
        print(f'{path}: sol en ({cx}, {cy}), radio {r}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
