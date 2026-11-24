"""The sheriff's legs on measured joints: one trouser leg and one boot for every pose.

A leg is a curve of round sections from the hip to the toe, as thick as measured on
the reference plus a pixel (she is fuller than it). Nothing is copied from a template
or squeezed between two poses: the same sections turn with the bones, so a leg keeps
its thickness in every frame. Cloth and leather are worked as finely as the
reference's: dark seams along both edges, a lit band, folds at the hip, behind the
knee and over the boot. Finished colours (detail_cowgirl leaves them alone).
Standard library only.
"""
from __future__ import annotations

import math

INK = (0x25, 0x20, 0x18, 255)


def _rgb(value: int) -> tuple:
    return value >> 16, (value >> 8) & 255, value & 255, 255


TONES = (_rgb(0x777174), _rgb(0x625c61), _rgb(0x4b464b), _rgb(0x39353a))   # Trousers: light, base, shade, fold
HIDE = (_rgb(0x916c48), _rgb(0x6f4d33), _rgb(0x483326), _rgb(0x35271d))    # Boots, the same
SIDES = ((1, 0), (-1, 0), (0, 1), (0, -1))
# Half the thickness inside the outline, down the thigh, the calf and the boot.
THIGH = ((0, 3.25), (.35, 2.95), (.7, 2.45), (1, 2.15))
CALF = ((0, 2.15), (.28, 2.15), (.6, 1.85), (1, 1.6))
BOOT = ((0, 1.95), (.5, 1.75), (1, 1.6))
BOOT_AT = .48                     # How far down the calf its boot begins
QUAD, HAM = .35, -.3              # How much the thigh bows forward and the calf back


def _along(points: tuple, t: float) -> float:
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return points[-1][1]


def _curve(a: tuple, b: tuple, bulge: float, n: int = 28):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1
    c = ((a[0] + b[0]) / 2 + dy / length * bulge * 2, (a[1] + b[1]) / 2 - dx / length * bulge * 2)
    for i in range(n + 1):
        t = i / n
        yield t, tuple((1 - t) ** 2 * a[k] + 2 * t * (1 - t) * c[k] + t * t * b[k] for k in (0, 1))


def sections(chain: tuple, fuller: float = 0., boot_at: float = BOOT_AT) -> list:
    """The leg's round sections: material, centre and radius. fuller: px more cloth all round.
    boot_at: how far down the calf the boot begins."""
    hip, knee, ankle, angle = chain
    out = [('cloth', q[0], q[1], _along(THIGH, t) + fuller) for t, q in _curve(hip, knee, QUAD)]
    for t, q in _curve(knee, ankle, HAM):
        if t <= boot_at:
            out.append(('cloth', q[0], q[1], _along(CALF, t) + fuller))
        else:
            out.append(('boot', q[0], q[1], _along(BOOT, (t - boot_at) / (1 - boot_at))))
    a = math.radians(angle)
    along, down = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    heel = tuple(ankle[k] - along[k] * .5 + down[k] * .8 for k in (0, 1))
    ball = tuple(ankle[k] + along[k] * 2.3 + down[k] for k in (0, 1))
    for t, q in _curve(heel, ball, 0, 14):
        out.append(('boot', q[0], q[1], 1.3 - .2 * t))
    return out


def covered(parts: list):
    """The pixels at least half inside the sections."""
    x0 = math.floor(min(p[1] - p[3] for p in parts)) - 1
    x1 = math.ceil(max(p[1] + p[3] for p in parts)) + 1
    y0 = math.floor(min(p[2] - p[3] for p in parts)) - 1
    y1 = math.ceil(max(p[2] + p[3] for p in parts)) + 1
    steps = (.125, .375, .625, .875)
    for y in range(y0, y1):
        for x in range(x0, x1):
            near = [p for p in parts if abs(x + .5 - p[1]) < p[3] + 1 and abs(y + .5 - p[2]) < p[3] + 1]
            if sum(any((x + sx - p[1]) ** 2 + (y + sy - p[2]) ** 2 <= p[3] * p[3] for p in near)
                   for sy in steps for sx in steps) >= 8:
                yield x, y


def _place(x: int, y: int, chain: tuple) -> tuple:
    """Where a pixel lies on the leg: which bone, how far down it and how many px across
    (- behind it, + in front)."""
    best = None
    for bone, (a, b) in enumerate(zip(chain, chain[1:3])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1
        ux, uy = dx / length, dy / length
        px, py = x + .5 - a[0], y + .5 - a[1]
        t = (px * ux + py * uy) / length
        across = px * uy - py * ux
        miss = max(0, -t, t - 1) * length + abs(across) * .35
        if best is None or miss < best[0]:
            best = (miss, bone, t, across)
    return best[1:]


def painted(parts: list, chain: tuple, far: bool, seat: float = 0.,
            cloth: tuple = TONES, hide: tuple = HIDE, boot_at: float = BOOT_AT) -> dict:
    """The leg's colours: dark seams along both edges, a lit band down the middle, the
    brightest over thigh and knee, folds behind the knee, at the hip and over the boot. The
    boot has a pale cuff, a lit instep and a dark sole. The far leg is a tone deeper. seat:
    how much her near buttock is turned to us (its thigh's root is round, not creased)."""
    out = {}
    for x, y in covered(parts):
        kind, cx, cy, r = min(parts, key=lambda p: math.hypot(x + .5 - p[1], y + .5 - p[2]) - p[3])
        nx, ny = (x + .5 - cx) / max(r, .5), (y + .5 - cy) / max(r, .5)
        light = -.8 * nx - .5 * ny                           # From the upper left
        bone, t, across = _place(x, y, chain)
        if kind == 'boot':
            if bone == 1 and boot_at <= t < boot_at + .2:
                tone = 0 if light > -.2 else 1               # Cuff
            else:
                tone = 1 if light > .1 else 2
            out[x, y] = hide[min(3, tone + far)]
            continue
        s = max(-1.2, min(1.2, across / max(r, .5)))
        if bone == 0:
            lit = .38 <= t <= .98 and -.45 <= s <= .5
            tone = 0 if lit and light > -.35 else 1 if -.7 <= s <= .62 else 2
            if seat > .5 and not far and t < .42 and s > -.62:
                tone = 0 if -.2 < light < .62 and t < .34 else 1 if light > -.5 else 2
            elif t < .22 and (x + y) % 2 == 0 and tone == 1:
                tone = 2                                     # Creased cloth at the hip
            if .86 <= t and s < -.3:
                tone = 3 if s < -.62 else 2                  # Behind the knee
        else:
            lit = t < .2 and -.2 <= s <= .6
            tone = 0 if lit and light > -.4 else 1 if -.2 <= s <= .55 else 2
            if boot_at - .16 <= t <= boot_at and (x - y) % 2 == 0:
                tone = min(3, tone + 1)                      # Gathered over the boot
        if light < -.78 and math.hypot(nx, ny) > .72:
            tone = max(tone, 2)
        out[x, y] = cloth[min(3, tone + far)]
    return out


def outlined(px: dict) -> dict:
    out = {(x + a, y + b): INK for x, y in px for a, b in SIDES if (x + a, y + b) not in px}
    out.update(px)
    return out


def hips(middle: float, belt: float, half: float, seat: float = 0., lift: float = 0., cloth: tuple = TONES) -> dict:
    """The hips joining both thighs under the belt. seat: how much of her seat is turned to
    us, rounder behind and higher under the belt's raised end (lift, in rows). The seam of her
    trousers between both sides is the near thigh's edge (lower_body)."""
    r = min(3.0, half)
    parts = [('cloth', middle + side * (half - r), belt + 1.4, r) for side in (-1, 1)]
    parts += [('cloth', middle - half + r + .1, belt + 2.9, r - .1), ('cloth', middle + half - r - .2, belt + 2.7, r - .2),
              ('cloth', middle, belt + 1.2, r), ('cloth', middle, belt + 2.4, r - .2)]
    out = {}
    for x, y in covered(parts):
        u = (x + .5 - middle) / half
        tone = 1 if u < -.1 else 2
        if u < -.1 and (x + y) % 3 == 0 and y > belt + 1:
            tone = 2
        out[x, y] = cloth[tone]
    if seat > .02:
        cx, cy, radius = middle - half + 2.45 - .35 * seat, belt + 2.1 - .5 * seat, 3.0 + .65 * seat
        for x, y in covered([('cloth', cx, cy, radius), ('cloth', cx + .9, cy - 1.2 - lift * .75, radius - .55)]):
            nx, ny = (x + .5 - cx) / radius, (y + .5 - cy) / radius
            light = -.75 * nx - .62 * ny
            tone = 0 if .05 < light < .72 else 1 if light > -.35 else 2
            if seat > .5 and ny > .45 and math.hypot(nx, ny) > .72:
                tone = 3                                     # The fold where the thigh leaves it
            out[x, y] = cloth[tone]
    return out


def lower_body(far: dict, near: dict, hips_px: dict, belt: int, ground: int, *, crotch: int = 6,
               top: int = None, crease: int = 4, fold: tuple = TONES[3]) -> dict:
    """Both legs and the hips between them: the near leg in front. Above the crotch a fold
    parts the thighs, from crease rows under the belt (with her seat to us, the seam between
    both sides); under it, an outline. Nothing above top or under the ground line."""
    top = belt if top is None else top
    far = {p: c for p, c in far.items() if belt < p[1] < ground}
    near = {p: c for p, c in near.items() if belt < p[1] < ground}
    base = dict(far)
    base.update(hips_px)
    out = outlined(base)
    for p, c in outlined(near).items():
        if c == INK and p in base and p not in near and p[1] < belt + crotch:
            if p[1] > belt + crease:
                out[p] = fold
        else:
            out[p] = c
    return {p: c for p, c in out.items() if top <= p[1] <= ground}
