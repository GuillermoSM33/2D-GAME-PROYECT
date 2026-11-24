"""The sheriff's one three-quarter body, from her collar to her boots, without arms.

Drawn by hand on the native walk grid (42 x 67, belt on row 42, buckle column 22),
turned to the right as in the reference idle: a broad near lapel, the neckline, the
lacing and the buckle a column or two ahead of her middle, a narrow far lapel and the
covered chest rounding past it. Standing, aiming, reloading, jumping and running all
use it; nothing here is squeezed, rotated or resampled, so she keeps her width in
every frame. Finished colours (detail_cowgirl leaves them alone). Standard library only.
"""
from __future__ import annotations

import math

import cowgirl_legs as legs
import cowgirl_pose as pose

INK = legs.INK
_rgb = legs._rgb
COLORS = {
    '#': INK,
    'l': _rgb(0x924657), 'w': _rgb(0x6f2638), 'd': _rgb(0x441c2a),            # Wine jacket: light, base, shade
    's': _rgb(0xebc1a4), 'a': _rgb(0xd7a786),                                # Skin
    'L': _rgb(0xbdbbb1), 'm': _rgb(0x96948b),                                # Lace
    'C': _rgb(0x5d6870), 'c': _rgb(0x404c53), 'e': _rgb(0x364149), 'k': _rgb(0x29343b),   # Corset
    'x': _rgb(0x605d74),                                                     # Lacing
    '1': _rgb(0xdbc58d), '2': _rgb(0xb6985c), '3': _rgb(0x77603c),            # Her star
    '4': _rgb(0xc2a66e), '5': _rgb(0xa27d43), '6': _rgb(0x36271d),            # Snaps
    'K': _rgb(0x1e1a20), 'G': _rgb(0xc9ab6d), 'g': _rgb(0x9e7c42),            # Choker, brass
    'q': _rgb(0x916c48), 'b': _rgb(0x6f4d33), 'v': _rgb(0x483326), 'V': _rgb(0x35271d),   # Leather
    'P': legs.TONES[0], 'M': legs.TONES[1], 'p': legs.TONES[2], 'F': legs.TONES[3],       # Trousers
    'i': _rgb(0x743044), 'I': _rgb(0x995367), 'j': _rgb(0x4c2633),            # Sash
}
STAR_TONES = {COLORS[k] for k in '123'}
SNAP_TONES = {COLORS[k] for k in '456'}
SASH_TONES = {COLORS[k] for k in 'iIj'}
LEATHER_TONES = {COLORS[k] for k in 'qbvV'}
CORSET_TONES = {COLORS[k] for k in 'Ccek'}
X0 = 13
# Her torso by rows, from column X0: the near lapel, the neckline and its lace, the
# covered chest, the star on the corset, the lacing, the far lapel.
TORSO = {
    28: "..#llwwKKKGKwww#..",
    29: ".#llwwlsssgsalww#.",
    30: ".#lwwwlssssssaww#.",
    31: ".#lwwwlssssssalw#.",
    32: ".#l45wLLLssLLLww#.",
    33: ".#w56lCCmLLCmC5w#.",
    34: ".#wwwlCCCCeCCC6w#.",
    35: "..#wwl1CCceCCeww#.",
    36: "...#w11222ceekd#..",
    37: "....#d123ccxek#...",
    38: "....#22233cexk#...",
    39: "....#dc3ccxexk#...",
    40: "...#ccccccxeekk#..",
    41: "...#ccccccceekk#..",                   # Under the belt, unless it tilts
}
CHEST = (31, 35)                                # Rows of her covered chest...
CHEST_FROM = 18                                 # ...from this column on
LEAN_ROWS = (30, 35)                            # Her head and shoulders, then her chest: the rest stays
# Her hips and legs standing, measured on the reference idle and a pixel fuller.
LOWER_X0 = 11
LOWER = {
    44: "..#MMPMMpMppMpMpp#..",
    45: "..#MPPMMpppppMMpp#..",
    46: "..#MPPMpppppMMMpF#..",
    47: "..#MPPMpp##pMMMpF#..",
    48: "..#MPPMp#..#MMMpF#..",
    49: "..#MPPMp#..#pMMpF#..",
    50: "..#pPMp#...#pMMpF#..",
    51: "..#pPMp#....#MMpF#..",
    52: "..#pMpF#....#pMpF#..",
    53: "..#qbbv#....#bbvV#..",
    54: "..#bbv#.....#bvV#...",
    55: "..#bbv#.....#bvV#...",
    56: "..#bbvv#....#bvvV#..",
    57: "..#bqbvv#...#bbvvV#.",
    58: "..#vvvvv#...#vvVVV#.",
    59: "...#####.....#####..",
}
HOLSTER = {41: "q..", 42: "qq#", 43: "qqv#", 44: "bbv#", 45: "bbv#", 46: "bvv#", 47: "bv#.", 48: "##.."}
HOLSTER_X0 = 27                                  # Her gun's
# The duals' other one hangs outside her near hip, its last column against her outline: rows
# from the leather of her belt down.
NEAR_HOLSTER = ("..#q", ".#qb", "#qbb", "#qbv", "#qbv", ".#bv", "..##")
NEAR_HIP = 13                                    # Her thigh's outline, standing
BELT_ROW = 41                                   # Its upper outline; a row of leather and the lower one follow
STAND_BELT = {x: BELT_ROW for x in range(14, 28)}
STAND_BUCKLE = 23.5
SASH_LONG, SASH_WIDE = 8, 4


def pixels(rows: dict, x0: int, dx: int = 0, dy: int = 0) -> dict:
    return {(x0 + i + dx, y + dy): COLORS[c] for y, row in rows.items() for i, c in enumerate(row) if c != '.'}


def torso(chest: int = 0, opened: bool = False) -> dict:
    """Her torso standing. chest: rows her covered chest is off it (-1..1). opened: her chest
    a column more to us, as her near shoulder is drawn back."""
    rows = {y: list(row) for y, row in TORSO.items()}
    if opened:                                            # The neckline and the lacing a column back
        for y in range(29, 41):
            row = rows[y]
            start = next(i for i, c in enumerate(row) if c not in '.#') + 1
            end = max(i for i, c in enumerate(row) if c != '.') - 1
            del row[start]
            row.insert(end - 1, row[end - 1])
    first, last = CHEST
    cut = CHEST_FROM - X0
    if chest:
        block = {y: rows[y][cut:] for y in range(first - 1, last + 2)}
        for y in range(first, last + 1):
            if first <= y + chest <= last + 1:
                rows[y + chest] = rows[y + chest][:cut] + block[y]
        if chest > 0:
            rows[first] = rows[first][:cut] + block[first - 1]
        else:
            rows[first - 1] = rows[first - 1][:cut] + block[first]
            rows[last] = rows[last][:cut] + block[last + 1]
    return pixels({y: ''.join(row) for y, row in rows.items()}, X0)


def leaned(px: dict, amount: int, belt: int = pose.BELT) -> dict:
    """Her upper body leaning that many columns at her head, half at her chest."""
    if not amount:
        return dict(px)
    half = int(math.copysign((abs(amount) + 1) // 2 if abs(amount) > 1 else 0, amount))
    out = {}
    for (x, y), c in px.items():
        row = y - belt + pose.BELT
        out[x + (amount if row <= LEAN_ROWS[0] else half if row <= LEAN_ROWS[1] else 0), y] = c
    return out


def sash(left: int, top: int, drift: float = 0., wave: float = 0.) -> dict:
    """The sash hanging from the back of her belt, its right edge on column left. drift: how
    much it trails behind her as she runs; wave: where it is in its ripple."""
    cloth = {}
    for i in range(SASH_LONG):
        t = i / (SASH_LONG - 1)
        width = SASH_WIDE - (i >= SASH_LONG - 3)
        shift = round(drift * t * t * 2.4 + .7 * math.sin(wave - t * 2.4) * t * min(1., drift + .25))
        for w in range(width):
            if i == SASH_LONG - 1 and w == 1:
                continue                                  # Ragged at its end
            tone = 'j' if w == 0 else 'I' if w == 1 + (i // 3) % 2 else 'i'
            cloth[left - SASH_WIDE + w - shift, top + i] = COLORS[tone]
    return legs.outlined(cloth)


def belt(rows: dict, buckle: float, wide: int) -> dict:
    """One row of leather between two of outline and a small ring of a buckle. rows: its
    upper outline's row, by column; wide: how many columns of the buckle show (0-3)."""
    out = {}
    cols = sorted(rows)
    for x, y in rows.items():
        out[x, y] = INK
        out[x, y + 1] = COLORS['b' if x < buckle else 'v']
        out[x, y + 2] = INK
    for x, side in ((cols[0], -1), (cols[-1], 1)):
        out[x + side, rows[x] + 1] = INK
    first = min(round(buckle - wide / 2), cols[-1] + 1 - wide)
    for k in range(wide):
        x = first + k
        y = rows[x]
        out[x, y] = COLORS['G']
        out[x, y + 1] = COLORS['v' if 0 < k < wide - 1 else 'g']
        out[x, y + 2] = COLORS['g']
    return out


def buckle_shown(yaw: float) -> int:
    """Columns of it in sight as her pelvis turns away (degrees)."""
    return 3 if yaw < 36 else 2 if yaw < 55 else 1 if yaw < 66 else 0


def near_holster(body: dict, hip: int, belt: int, out: int = 0) -> dict:
    """The duals' other holster, hung outside her near hip: what her body leaves of it in sight,
    never over her. hip: the column of her outline; belt: the row of its upper outline; out:
    columns its end is pushed out."""
    case = {}
    for i, row in enumerate(NEAR_HOLSTER):
        for k, c in enumerate(row):
            if c != '.':
                case[hip - len(row) + k - (out if i >= 3 else 0), belt + 1 + i] = COLORS[c]
    return {p: c for p, c in case.items() if p not in body}


def second_holster() -> dict:
    """The duals' other holster as she stands."""
    return near_holster(standing()[1], NEAR_HIP, BELT_ROW)


def standing(chest: int = 0, *, armed: bool = True, dual: bool = False, legs_px: dict = None) -> tuple:
    """Her body standing from the collar down, without arms: what hangs behind her legs, and
    the rest. legs_px: other legs than the ones she stands on, from the hips down."""
    behind = sash(14, BELT_ROW + 2, .05, .6)
    out = dict(pixels(LOWER, LOWER_X0) if legs_px is None else legs_px)
    out.update(torso(chest))
    out.update(belt(STAND_BELT, STAND_BUCKLE, 3))
    if armed:
        out.update(pixels(HOLSTER, HOLSTER_X0))
    if dual:
        out.update(near_holster(out, NEAR_HIP, BELT_ROW))
    return behind, out


def running_lower(frame: float, *, level: bool = False) -> tuple:
    """Her hips and legs on a frame of the run and her belt over them: the pixels, the belt's
    rows by column. level: at the height she stands at, for the legs under another action."""
    off = -pose.bob(frame) if level else 0
    dy = pose.bob(frame)
    top = pose.BELT + dy
    middle, seat = pose.hips(frame), pose.seat(frame)
    half = 5.0 + .75 * pose.stride(frame)
    lift, drop = pose.belt_tilt(frame)
    left = math.floor(middle - half + .5) - (seat > .5)
    right = math.ceil(middle + half - .5) - 1
    rows = {x: top - 1 + round(-lift * (1 - (x - left) / (right - left)) ** 1.15 + drop * (x - left) / (right - left))
            for x in range(left, right + 1)}
    chains = [pose.leg_chain(frame, far) for far in (True, False)]
    if level:                                             # Only her hips come to the standing height
        chains = [((c[0][0], c[0][1] + off), c[1], c[2], c[3]) for c in chains]
    far, near = (legs.painted(legs.sections(c), c, i == 0, seat) for i, c in enumerate(chains))
    hips = legs.hips(middle, pose.BELT + (0 if level else pose.drop(frame)), half, seat, lift)
    lower = legs.lower_body(far, near, hips, top + off, pose.SOLE, top=top + off - 4, crease=4 if seat < .4 else 0)
    rows = {x: y + off for x, y in rows.items()}
    lower = {p: c for p, c in lower.items() if (p[1] >= rows[p[0]] if p[0] in rows else p[1] >= top + off - 2)}
    return lower, rows


def running(frame: float, *, armed: bool = False, dual: bool = False) -> tuple:
    """Her body on a frame of the run, without arms or head: what trails behind her, and the rest."""
    dy, seat = pose.bob(frame), pose.seat(frame)
    middle, yaw = pose.hips(frame), math.radians(pose.yaw(frame))
    lower, rows = running_lower(frame)
    left, right = min(rows), max(rows)
    upper = leaned(torso(pose.chest_lag(frame), seat > .6), pose.LEAN)
    out = {}
    if armed and seat < .5:                               # On her far hip: behind her as it turns away
        out.update(pixels({y - 1: row for y, row in HOLSTER.items() if y <= 46}, right - 1, 0, dy))
    out.update({(x, y + dy): c for (x, y), c in upper.items()})
    out.update(lower)
    out.update(belt(rows, middle + .4 + 5.0 * math.sin(yaw), buckle_shown(pose.yaw(frame))))
    if dual:                                              # Outside her near hip, as it turns
        hip = min(x for x, y in lower if rows[left] + 2 <= y <= rows[left] + 4)
        out.update(near_holster(out, hip, rows[left], int(seat > .5)))
    trail = sash(left + 2, rows[left] + 3, .7 + .3 * pose.stride(frame), 2 * math.pi * pose.phase_of(frame) / 5)
    return trail, out
