#!/usr/bin/env python3
"""Check a landscape theme's layers against docs/LANDSCAPE.md before using them.

Usage: tools/check_landscape.py THEME_DIR [THEME_DIR...]
       e.g. tools/check_landscape.py assets/backgrounds/noche

For every layer (sky, far, hills_far, hills_near, ground and, if present, fog):
format (8-bit RGBA, non-interlaced), exact size, opaque or truly transparent
where it must be, seamless tiling, the fog's alpha, and the value rules per
screen zone. Prints one line per check, OK / AVISO / FALLO, and exits non-zero
on any FALLO. AVISO is for things worth a look that may be fine on purpose.
Uses only the standard library.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from landscape_kit import LAYERS as GEOMETRY  # noqa: E402

# name: (width, height, top screen row, repeats, kind)
LAYERS = {name: (*geometry, 'opaque' if name in ('sky', 'ground') else
                 'fog' if name == 'fog' else 'cutout')
          for name, geometry in GEOMETRY.items()}
REQUIRED = ('sky', 'far', 'hills_far', 'hills_near', 'ground')

# Value rules (luminance 0-255), by screen row; see docs/LANDSCAPE.md.
HUD_ROWS, HUD_MAX = range(0, 68), 55
BODY_ROWS, BODY_MAX = range(184, 240), 62
LINE_MAX = 120         # 1-px light lines (crests, edges)
LIGHT_MAX = 220        # Sun or moon
FOG_ALPHA = (30, 100)
LOOSE_MAX = 0.04       # Lone pixels: above this it looks dithered or noisy


def lum(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


class Report:
    def __init__(self) -> None:
        self.failures = 0

    def line(self, level: str, layer: str, text: str) -> None:
        if level == 'FALLO':
            self.failures += 1
        print(f'  {level:5s} {layer:10s} {text}')


def png_header_ok(path: Path) -> tuple[bool, str]:
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return False, 'no es PNG'
    depth, color, interlace = data[24], data[25], data[28]
    if depth != 8 or color != 6 or interlace != 0:
        return False, f'debe ser RGBA de 8 bits sin entrelazar (depth={depth}, color={color}, interlace={interlace})'
    return True, 'RGBA 8 bits'


def check_layer(rep: Report, path: Path, name: str) -> None:
    width, height, top, repeats, kind = LAYERS[name]
    ok, msg = png_header_ok(path)
    if not ok:
        rep.line('FALLO', name, msg)
        return
    w, h, px = decode_png_rgba(path)
    if (w, h) != (width, height):
        rep.line('FALLO', name, f'mide {w}x{h}; debe medir {width}x{height}')
        return

    def at(x: int, y: int) -> tuple[int, int, int, int]:
        i = (y * w + x) * 4
        return px[i], px[i + 1], px[i + 2], px[i + 3]

    alphas = [px[i + 3] for i in range(0, len(px), 4)]
    if kind == 'opaque':
        bad = sum(1 for a in alphas if a != 255)
        rep.line('FALLO' if bad else 'OK', name, f'opaca ({bad} px no opacos)' if bad else f'{w}x{h}, opaca')
    elif kind == 'cutout':
        partial = sum(1 for a in alphas if 0 < a < 255)
        rep.line('FALLO' if partial else 'OK', name,
                 f'{partial} px semitransparentes: debe ser opaco o alfa 0' if partial else f'{w}x{h}, recorte limpio')
    else:
        used = sorted({a for a in alphas if a})
        empty = alphas.count(0) / len(alphas)
        bad = [a for a in used if not FOG_ALPHA[0] <= a <= FOG_ALPHA[1]]
        level = 'FALLO' if bad or len(used) > 2 else 'OK'
        rep.line(level, name, f'alfa {used} (pide {FOG_ALPHA[0]}-{FOG_ALPHA[1]}, 2 niveles como máx.), '
                              f'{empty:.0%} vacía')
        colors = {at(x, y)[:3] for y in range(h) for x in range(w) if at(x, y)[3]}
        rep.line('OK' if len(colors) == 1 else 'AVISO', name, f'{len(colors)} color(es) (pide uno solo)')

    if repeats:
        seam = sum(1 for y in range(h) if at(0, y) != at(w - 1, y))
        rep.line('OK' if seam == 0 else 'AVISO', name,
                 'costura exacta (columna 0 = última)' if seam == 0 else
                 f'{seam} filas distintas entre la columna 0 y la última: revisa la unión')

    # Lone pixels: no orthogonal neighbor of the same color (dithering or noise).
    opaque = [(x, y) for y in range(h) for x in range(w) if at(x, y)[3]]
    if opaque and kind != 'fog':
        loose = 0
        for x, y in opaque:
            c = at(x, y)
            if all(at(nx % w, ny)[:4] != c for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                   if 0 <= ny < h):
                loose += 1
        share = loose / len(opaque)
        rep.line('OK' if share <= LOOSE_MAX else 'AVISO', name,
                 f'{share:.1%} píxeles sueltos (<= {LOOSE_MAX:.0%}: sin difuminado)')

    if kind == 'fog':
        return
    # Value rules by screen row.
    hud = sky = body = light = 0.0
    body_over = 0
    for y in range(h):
        row = top + y
        for x in range(w):
            r, g, b, a = at(x, y)
            if not a:
                continue
            L = lum(r, g, b)
            if row in HUD_ROWS:
                hud = max(hud, L)
            elif row in BODY_ROWS:
                if L > BODY_MAX:
                    body_over += 1
                body = max(body, L)
            else:
                sky = max(sky, L)
            light = max(light, L)
    if top == 0:
        rep.line('OK' if hud <= HUD_MAX else 'AVISO', name, f'banda del HUD: luminancia máx. {hud:.0f} (<= {HUD_MAX})')
        rep.line('OK' if light <= LIGHT_MAX else 'AVISO', name, f'lo más claro (luna o sol): {light:.0f} (recomendado <= {LIGHT_MAX})')
    if any(top + y in BODY_ROWS for y in range(h)):
        level = 'OK' if body <= LINE_MAX else 'AVISO'
        rep.line(level, name, f'detrás de los cuerpos: máx. {body:.0f}; {body_over} px sobre {BODY_MAX} '
                              f'(solo líneas de luz de 1 px, hasta {LINE_MAX})')


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    rep = Report()
    for arg in sys.argv[1:]:
        folder = Path(arg)
        print(f'{folder}')
        for name in LAYERS:
            path = folder / f'{name}.png'
            if not path.exists():
                if name in REQUIRED:
                    rep.line('FALLO', name, 'falta')
                continue
            check_layer(rep, path, name)
        extra = sorted(p.name for p in folder.iterdir() if p.stem not in LAYERS)
        if extra:
            rep.line('FALLO', '-', f'archivos de más: {", ".join(extra)}')
    print('Resultado:', 'FALLO' if rep.failures else 'OK')
    return 1 if rep.failures else 0


if __name__ == '__main__':
    sys.exit(main())
