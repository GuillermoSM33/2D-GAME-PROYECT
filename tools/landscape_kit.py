"""What the landscape's generators share (make_landscape.py, make_props.py,
make_houses.py): colors, repeatable noise, a canvas that can tile, and the
few shapes pixel art is built from.

Everything is deterministic: the same call gives the same pixels on every
machine, so regenerating never changes a file that did not need to. Standard
library only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_sprites import Image  # noqa: E402

RGB = tuple[int, int, int]

# The view (src/config.h): 480 x 270 art px, the ground line on row 240.
VIEW_W, VIEW_H, GROUND_ROW = 480, 270, 240
# name: (width, height, top row, repeats). src/game/themes.c has the same table.
LAYERS = {
    'sky': (480, 180, 0, False),
    'far': (720, 72, 104, True),
    'hills_far': (720, 70, 140, True),
    'hills_near': (720, 64, 176, True),
    'ground': (480, 30, 240, True),
    'fog': (480, 48, 216, True),
}
LIGHT_ALPHA = 254   # A pixel that is a light: the game keeps its color (ASSETS_LIGHT_ALPHA)


def hx(value) -> RGB:
    """0xRRGGBB as (r, g, b); a color that already is one stays as it is."""
    if isinstance(value, tuple):
        return value
    return (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF


def mix(a: RGB, b: RGB, t: float) -> RGB:
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t), round(a[2] + (b[2] - a[2]) * t))


def lum(c: RGB) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def shade(c: RGB, k: float) -> RGB:
    """Darker (k < 1) or lighter (k > 1), clamped."""
    return (min(255, round(c[0] * k)), min(255, round(c[1] * k)), min(255, round(c[2] * k)))


def ramp(colors: list, steps: int) -> list:
    """steps colors spread evenly along a list of stops (each 0xRRGGBB or RGB)."""
    stops = [hx(c) if isinstance(c, int) else c for c in colors]
    out = []
    for i in range(steps):
        f = i * (len(stops) - 1) / max(1, steps - 1)
        k = min(len(stops) - 2, int(f))
        out.append(mix(stops[k], stops[k + 1], f - k))
    return out


# ---- Repeatable randomness ---------------------------------------------------------

class Rng:
    def __init__(self, seed: int) -> None:
        self.state = (seed * 2654435761 + 12345) & 0x7FFFFFFF

    def next(self) -> int:
        self.state = (self.state * 1103515245 + 12345) & 0x7FFFFFFF
        return self.state >> 8

    def range(self, lo: int, hi: int) -> int:
        """lo..hi inclusive."""
        return lo + self.next() % (hi - lo + 1)

    def unit(self) -> float:
        return (self.next() % 100000) / 100000.0

    def chance(self, p: float) -> bool:
        return self.unit() < p

    def pick(self, items):
        return items[self.next() % len(items)]


def seed_of(name: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate(name)) * 7919 % 1000003


def hash2(x: int, y: int, seed: int = 0) -> float:
    """0..1 for an integer point: the same everywhere, no pattern to the eye."""
    h = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777216.0


def _smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


def noise2(x: float, y: float, seed: int = 0, wrap: int = 0) -> float:
    """Smooth value noise, 0..1. wrap: the lattice repeats every wrap cells in x
    (so a layer whose width is wrap cells tiles)."""
    x0, y0 = math.floor(x), math.floor(y)
    fx, fy = _smooth(x - x0), _smooth(y - y0)
    xa, xb = (x0, x0 + 1) if not wrap else (x0 % wrap, (x0 + 1) % wrap)
    top = hash2(xa, y0, seed) + (hash2(xb, y0, seed) - hash2(xa, y0, seed)) * fx
    bottom = hash2(xa, y0 + 1, seed) + (hash2(xb, y0 + 1, seed) - hash2(xa, y0 + 1, seed)) * fx
    return top + (bottom - top) * fy


def fbm(x: float, y: float, seed: int = 0, octaves: int = 4, wrap: int = 0) -> float:
    """Noise with detail at several sizes, 0..1."""
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += noise2(x * (1 << o), y * (1 << o), seed + o * 101, wrap * (1 << o)) * amp
        norm += amp
        amp *= 0.5
    return total / norm


def wave(x: float, period: int, seed: int, terms: int = 5, base: int = 1) -> float:
    """A rolling line that repeats exactly every period: -1..1."""
    rng = Rng(seed)
    total, norm = 0.0, 0.0
    for k in range(terms):
        freq = base + k + rng.range(0, 1) * (k > 0)
        amp = 1.0 / (1 + k * 0.9)
        total += amp * math.sin(x * math.tau * freq / period + rng.unit() * math.tau)
        norm += amp
    return total / norm


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither(x: int, y: int, t: float) -> bool:
    """True for a share t of the pixels, in an even ordered pattern."""
    return t * 16 > BAYER[y & 3][x & 3] + 0.5


# ---- A canvas -----------------------------------------------------------------------

class Canvas:
    """Pixels to draw on; None is transparent. With period set, x wraps: what
    is drawn across the right edge comes back in on the left, so it tiles."""

    def __init__(self, w: int, h: int, period: int = 0) -> None:
        self.w, self.h, self.period = w, h, period
        self.px: list = [None] * (w * h)
        self.lights: set = set()   # Pixels kept as drawn by the game's grading

    def _x(self, x: int) -> int:
        return x % self.period if self.period else x

    def inside(self, x: int, y: int) -> bool:
        return 0 <= y < self.h and (self.period or 0 <= x < self.w)

    def get(self, x: int, y: int):
        x = self._x(x)
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y * self.w + x]
        return None

    def set(self, x: int, y: int, c) -> None:
        x = self._x(x)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = c
            self.lights.discard((x, y))

    def light(self, x: int, y: int, c) -> None:
        """A pixel that shines by itself (a lit window): never graded."""
        self.set(x, y, c)
        x = self._x(x)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.lights.add((x, y))

    def clear(self, x: int, y: int) -> None:
        self.set(x, y, None)

    def fill(self, x0: int, y0: int, x1: int, y1: int, c) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def hline(self, x0: int, x1: int, y: int, c) -> None:
        for x in range(x0, x1 + 1):
            self.set(x, y, c)

    def vline(self, x: int, y0: int, y1: int, c) -> None:
        for y in range(y0, y1 + 1):
            self.set(x, y, c)

    def line(self, x0: float, y0: float, x1: float, y1: float, c, width: int = 1) -> None:
        n = max(abs(round(x1) - round(x0)), abs(round(y1) - round(y0)), 1)
        for i in range(n + 1):
            x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
            for d in range(width):
                self.set(x + d, y, c)

    def disc(self, cx: float, cy: float, rx: float, c, ry: float | None = None) -> None:
        ry = rx if ry is None else ry
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.set(x, y, c)

    def poly(self, points: list, c) -> None:
        """A filled polygon (even-odd), its edges included."""
        ys = [p[1] for p in points]
        for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
            xs = []
            for i, (xa, ya) in enumerate(points):
                xb, yb = points[(i + 1) % len(points)]
                if ya == yb:
                    continue
                if min(ya, yb) <= y < max(ya, yb):
                    xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for a, b in zip(xs[0::2], xs[1::2]):
                self.hline(int(math.ceil(a - 0.5)), int(math.floor(b + 0.5)), y, c)

    def solid(self, x: int, y: int) -> bool:
        return self.get(x, y) is not None

    def top(self, x: int):
        """The first solid row of column x, or None."""
        for y in range(self.h):
            if self.get(x, y) is not None:
                return y
        return None

    def paste(self, other: 'Canvas', ox: int, oy: int) -> None:
        for y in range(other.h):
            for x in range(other.w):
                c = other.px[y * other.w + x]
                if c is not None:
                    if (x, y) in other.lights:
                        self.light(ox + x, oy + y, c)
                    else:
                        self.set(ox + x, oy + y, c)

    def image(self, alpha=None) -> Image:
        """The PNG: opaque where drawn. alpha(x, y) gives another opacity (fog)."""
        img = Image(self.w, self.h)
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y * self.w + x]
                if c is None:
                    continue
                a = LIGHT_ALPHA if (x, y) in self.lights else 255
                if alpha is not None:
                    a = alpha(x, y)
                img.set(x, y, (c[0], c[1], c[2], a))
        return img


def sheet(frames: list) -> Image:
    """Frames of the same size side by side, in a row."""
    w, h = frames[0].w, frames[0].h
    out = Canvas(w * len(frames), h)
    for i, f in enumerate(frames):
        assert (f.w, f.h) == (w, h), 'frames of a sheet are all the same size'
        out.paste(f, i * w, 0)
    return out.image()


def save_all(assets: Path, out: dict, tool: str) -> None:
    for name, img in out.items():
        path = assets / name
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        print(f'{tool}: {name} ({img.width} x {img.height})')


# ---- Shading shared by the scenery ---------------------------------------------------

def edge_light(c: Canvas, lit, dark=None, x0: int = 0, x1: int | None = None) -> None:
    """Light from the upper left on whatever is drawn: the pixels with nothing
    above or to the left of them take lit; those with nothing below or to the
    right, dark."""
    x1 = c.w - 1 if x1 is None else x1
    marks = []
    for y in range(c.h):
        for x in range(x0, x1 + 1):
            if not c.solid(x, y):
                continue
            if not c.solid(x, y - 1) or not c.solid(x - 1, y):
                marks.append((x, y, lit))
            elif dark is not None and (not c.solid(x, y + 1) or not c.solid(x + 1, y)):
                marks.append((x, y, dark))
    for x, y, col in marks:
        if col is not None:
            c.set(x, y, col)


def speckle(c: Canvas, colors: list, seed: int, share: float, where=None) -> None:
    """Grain: a share of the drawn pixels (where(x, y, color) if given) nudged
    to one of colors, in short runs of two so it reads as texture, not noise."""
    for y in range(c.h):
        for x in range(0, c.w, 2):
            old = c.get(x, y)
            if old is None or hash2(x, y, seed) >= share:
                continue
            if where is not None and not where(x, y, old):
                continue
            col = colors[int(hash2(x, y, seed + 7) * len(colors)) % len(colors)]
            c.set(x, y, col)
            if c.get(x + 1, y) == old:
                c.set(x + 1, y, col)
