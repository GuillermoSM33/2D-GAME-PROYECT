#!/usr/bin/env python3
"""Make the characters' sitting sheets: on a bench, facing the viewer.

Usage: tools/make_sit.py

Writes assets/sprites/characters/<id>/sit.png for the cowgirl (her revolver)
and the SWAT (his rifle), and sit_shotgun.png for the SWAT's shotgun: 14
frames of 72 x 67, the body centered on x 35.5 (the pivot), ground row 61.
Sat on a bench they face the front, knees toward the viewer, shins down to
the boots:

  0      sitting down
  1-3    sat, breathing (1, 2, 1, 3)
  4-9    reloading sat, the gun across the lap. Rifle: hand on the handguard,
         on the magazine, pulling it out, a fresh one from the vest's pouch,
         pushing it in, working the charging handle. Shotgun: a shell from the
         pouch into the loading port, twice, then the pump. Revolver: the
         empties fall, rounds in, the cylinder shut
  10-13  dozing off: the head drops bit by bit, with a z or two over it

The cowgirl's walk is drawn nearly from the front, so her upper half is her
own walk frame 0 turned to the front: head and corset made symmetric, and
her arms (grey puffed sleeves, bare forearms) hanging by her sides, hands on
her thighs. The SWAT uses his approved tactical bitmap in swat_sit.py,
with the same helmet, mask and carrier as the standing poses; reloading,
his forearms reach from the elbows to the gun, magazine or pouch. The legs
use each character's trouser and boot colors. The gun on the lap is the in-play gun of
assets/sprites/ui/weapons.png (run tools/make_ui.py first). Uses only the
standard library.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402
from rework_cowgirl import (BADGE, BADGE_TONES, BADGE_UNDER_FACE, BADGE_X, BARE_WIDTH, CHOKER, CHOKER_UNDER_FACE,  # noqa: E402
                            BELT_UNDER_FACE, CORSET_TONES, HAIR, JACKET_TONES, LACE, LACE_SMILE,
                            corset_bust, cropped_jacket, jacket_buttons)

ROOT = Path(__file__).resolve().parent.parent
W, H = 72, 67          # Frame
CX = 36                # The body's middle: columns CX-1 and CX mirror each other
WALK_PIVOT = 19.5      # Walk frame's pivot (its body's middle)
WAIST = 44             # Walk-frame rows 0..WAIST are the cowgirl's upper half
DROP = 6               # Rows the upper half sinks when sat
LAP = WAIST + DROP + 1  # First row of the legs (the lap and knees)
LAP_RISE = 6           # Rows the lap reaches up behind the torso
FEET = 59              # Last row of the boots (the walk's)
WEAPON_W, WEAPON_H = 36, 14

SEATED_ELBOW_ROW = 47
# The cowgirl's walk is drawn nearly from the front: her sat front is its
# upper half, her own pixels, so she keeps her art. Only her head is turned:
# its rows are made symmetric about her face's middle (the columns left of
# column COWGIRL_FACE kept and mirrored); hat and body stay as drawn.
COWGIRL_FACE_ROWS = (18, 30)   # Face, hair, neck
COWGIRL_FACE = 22              # First column right of her face's middle
COWGIRL_EAR_ROWS = (20, 24)    # Walk rows: long side locks cover the ears from the front
# Below, her corset is made symmetric about the pivot from her right side
# (its brown and gold); her arms are drawn on it from COWGIRL_ARM_ROWS, the
# left one (column 0 the outer edge, at COWGIRL_ARM_OUTER columns from the
# middle) and its mirror, coming out of her shoulders, as wide as them.
COWGIRL_BODY_ROWS = (31, WAIST)
COWGIRL_BODY = 22              # First column right of her middle, on her neck and buckle
COWGIRL_ARM_ROWS = [           # Her walk rows 29..: the sleeve down to the wrist, her glove
    "..omno.",
    ".ommnno",
    ".ommnno",
    "omnnnpo",
    "omnnnpo",
    "omnnnpo",
    ".omnnpo",
    ".onnppo",
    ".oppppo",
    ".omnno.",
    ".omnno.",
    "..omnno",
    "..omnno",
    "..oggGo",
    "..ogGGo",
    "...ooo.",
]
COWGIRL_ARM_TOP = 29
COWGIRL_ARM_OUTER = 12
COWGIRL_ARM_COLORS = {
    'o': rgb(0x252018), 'm': rgb(0x6c7a84), 'n': rgb(0x505c66), 'p': rgb(0x38424a),
    'g': rgb(0x684833), 'G': rgb(0x463322),
}
COWGIRL_HEAD_ROWS = 30         # Walk rows up to here nod with the head
COWGIRL_WAIST_SKIN = 36        # From this walk row on, skin on her body is that hand
COWGIRL_SKIN = {(0xfe, 0xdc, 0xa3), (0xd9, 0x9a, 0x5b), (0x89, 0x41, 0x1f), (0x8a, 0x43, 0x22)}
COWGIRL_CORSET = rgb(0x2c363c)

# Trousers dark to light, boots dark to light, outline, gloves; and her guns:
# (sheet, weapons.png frame, kind of reload).
CHARS = {
    'cowgirl': {
        'trousers': [rgb(0x322e2c), rgb(0x48423e), rgb(0x5e5650)],
        'boots': [rgb(0x463322), rgb(0x684833), rgb(0x8a6448)],
        'ink': rgb(0x252018),
        'hand': rgb(0x684833),
        'slim': 2,
        'guns': [('sit', 0, 'revolver')],
    },
    'swat': {
        'trousers': [rgb(c) for c in (0x29343b, 0x41494a, 0x697174)],
        'boots': [rgb(c) for c in (0x252018, 0x29343b, 0x41494a)],
        'ink': rgb(0x252018),
        'hand': rgb(0x5d6870),
        'sleeve': (rgb(0x697174), rgb(0x41494a)),
        'slim': 1,
        'guns': [('sit', 1, 'rifle'), ('sit_shotgun', 2, 'shotgun')],
    },
}
RIFLE_MAGAZINE = (8, 12, 8)    # Updated receiver: columns and first magazine row on the icon
SHELL = [rgb(0x8a2a1c), rgb(0xc84a32), rgb(0xf0c860)]


def load(path: Path) -> Image:
    w, h, px = decode_png_rgba(path)
    img = Image(w, h)
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            img.set(x, y, tuple(px[i:i + 4]))
    return img


def lighten(c: tuple, k: float) -> tuple:
    return tuple(min(255, round(v + (255 - v) * k)) for v in c[:3]) + (255,)


def put(img: Image, ox: int, x: int, y: int, c) -> None:
    if 0 <= x < W and 0 <= y < H:
        img.set(ox + x, y, c)


def outlined(px: dict, ink: tuple) -> dict:
    out = dict(px)
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in px:
                out[(x + dx, y + dy)] = ink
    return out


def leg(trousers: list, boots: list, knee_lift: int, slim: int) -> dict:
    """The viewer's left leg from the front, as (x, y) -> color: the lap and a
    rounded knee coming at the viewer, the shin down to a boot with its toe
    toward us; slim narrows it from the outside. The other leg is its mirror,
    a gap between them."""
    px: dict = {}
    light = lighten(trousers[2], 0.2)
    top = LAP - knee_lift
    x0, x1 = CX - 9 + slim, CX - 2                        # Knee, a gap at the middle
    for y in range(top, LAP + 4):                         # Thigh end and knee
        for x in range(x0, x1 + 1):
            if y == top and x in (x0, x1):
                continue                                  # Rounded
            c = trousers[1]
            if y <= top + 1 and x0 + 1 <= x <= x1 - 2:
                c = light                                 # Light on the kneecap
            elif x in (x0, x1) or y == LAP + 3:
                c = trousers[0]
            px[(x, y)] = c
    for y in range(LAP + 4, FEET - 3):                    # Shin
        for x in range(x0 + 1, x1):
            px[(x, y)] = trousers[2] if x == x0 + 1 else trousers[0] if x == x1 - 1 else trousers[1]
    for y in range(FEET - 3, FEET + 1):                   # Boot: cuff, toe toward us, sole
        for x in range(x0 - (1 if y >= FEET - 1 else 0), x1 + 1):
            c = boots[1]
            if y == FEET - 3:
                c = lighten(boots[2], 0.1)
            elif y == FEET:
                c = boots[0]
            elif x <= x0 + 1 and y == FEET - 1:
                c = boots[2]                              # Toe cap
            px[(x, y)] = c
    return px


def lap(char: dict, knee_lift: int) -> dict:
    """Her hips and the tops of her thighs, whole: rising under the torso so no
    breath or stoop parts them, and closing the gap between the knees."""
    trousers, slim = char['trousers'], char['slim']
    px: dict = {}
    for y in range(LAP - LAP_RISE - knee_lift, LAP + 3 - knee_lift):
        for x in range(CX - 8 + slim, CX + 8 - slim):
            crease = x in (CX - 1, CX) and y >= LAP - knee_lift
            px[(x, y)] = trousers[0] if crease else trousers[1]
    return px


def legs(img: Image, ox: int, char: dict, knee_lift: int) -> None:
    left = outlined(leg(char['trousers'], char['boots'], knee_lift, char['slim']), char['ink'])
    for (x, y), c in left.items():
        put(img, ox, x, y, c)
        put(img, ox, 2 * CX - 1 - x, y, c)
    for (x, y), c in lap(char, knee_lift).items():
        put(img, ox, x, y, c)


def upper(img: Image, ox: int, half: list, colors: dict, bottom: int, head_rows: int,
          dy: int, nod: int) -> None:
    """A front template, mirrored about CX, its last row on frame row bottom."""
    top = bottom + 1 - len(half)
    for r, row in enumerate(half):
        y = top + dy + r + (nod if r < head_rows else 0)
        for i, key in enumerate(row):
            if key == '.':
                continue
            c = colors[key]
            put(img, ox, CX - 14 + i, y, c)
            put(img, ox, CX + 13 - i, y, c)


def cowgirl_upper(img: Image, ox: int, walk: Image, dy: int, nod: int, arm: tuple) -> None:
    """Her walk frame 0's upper half centered on CX and turned to the front:
    the head symmetric from its left side (the long hair), the body from her
    right side's corset and her left arm, mirrored."""
    base = DROP + dy
    shift = round(CX - 0.5 - WALK_PIVOT)
    face0, face1 = COWGIRL_FACE_ROWS
    body0, body1 = COWGIRL_BODY_ROWS
    for y in range(WAIST + 1):
        ry = y + base + (nod if y <= COWGIRL_HEAD_ROWS else 0)
        if face0 <= y <= face1:
            for d in range(COWGIRL_FACE):
                c = walk.get(COWGIRL_FACE - 1 - d, y)
                if COWGIRL_EAR_ROWS[0] <= y <= COWGIRL_EAR_ROWS[1] and d >= 5 and c[:3] in COWGIRL_SKIN:
                    c = HAIR[1]  # Her hair falls in front of both ears, including while nodding
                if c[3]:
                    put(img, ox, CX - 1 - d, ry, c)
                    put(img, ox, CX + d, ry, c)
        elif body0 <= y <= body1:
            for d in range(42 - COWGIRL_BODY):
                c = walk.get(COWGIRL_BODY + d, y)
                if c[3] and y >= COWGIRL_WAIST_SKIN and c[:3] in COWGIRL_SKIN:
                    c = COWGIRL_CORSET  # Her hand off the hip: not mirrored down her middle
                if c[3] and c[:3] not in ((0x6c, 0x7a, 0x84), (0x50, 0x5c, 0x66), (0x38, 0x42, 0x4a)):
                    put(img, ox, CX - 1 - d, ry, c)
                    put(img, ox, CX + d, ry, c)
        else:
            for x in range(42):
                c = walk.get(x, y)
                if c[3]:
                    put(img, ox, x + shift, ry, c)
    # Her arms by her sides, hands on her thighs, breathing with her: arm is
    # (columns out, rows down) for this frame.
    out, down = arm
    for r, row in enumerate(COWGIRL_ARM_ROWS):
        ry = COWGIRL_ARM_TOP + r + base + down
        for i, key in enumerate(row):
            if key == '.':
                continue
            d = COWGIRL_ARM_OUTER - i + out
            put(img, ox, CX - 1 - d, ry, COWGIRL_ARM_COLORS[key])
            put(img, ox, CX + d, ry, COWGIRL_ARM_COLORS[key])


# Reloading sat, six steps per kind of gun: where the free hand is (a point on
# the gun's icon, or 'pouch'), what it holds, the magazine's state.
RELOAD_STEPS = {
    'rifle': [
        {'hand': (17, 7)},                                   # On the handguard
        {'hand': (9, 9)},                                    # On the magazine
        {'hand': (9, 12), 'mag': 'pulled'},                  # Pulling it out
        {'hand': 'pouch', 'mag': 'gone', 'hold': 'mag'},     # A fresh one from the vest
        {'hand': (9, 11)},                                   # Pushed in
        {'hand': (3, 3), 'jolt': True},                      # The charging handle: click
    ],
    'shotgun': [
        {'hand': (22, 6)},                                   # On the pump
        {'hand': 'pouch', 'hold': 'shell'},                  # A shell from the vest
        {'hand': (13, 8), 'hold': 'shell'},                  # Into the loading port
        {'hand': 'pouch', 'hold': 'shell'},
        {'hand': (13, 8), 'hold': 'shell'},
        {'hand': (18, 6), 'jolt': True},                     # The pump racked back: click
    ],
    'revolver': [
        {},
        {'empties': 1},                                      # The empties falling
        {'empties': 2},
        {'rounds': True},                                    # Rounds going in
        {'rounds': True},
        {'jolt': True},                                      # The cylinder shut: click
    ],
}


REVOLVER_REACH = 8     # Art columns right of her middle that the gun on her lap reaches


def reload_step(img: Image, ox: int, weapons: Image, char: dict, gun: int, kind: str, step: int) -> None:
    plan = RELOAD_STEPS[kind][step]
    ink, hand = char['ink'], char['hand']
    pixels = {}
    for y in range(WEAPON_H):
        for x in range(WEAPON_W):
            c = weapons.get(gun * WEAPON_W + x, y)
            if c[3]:
                pixels[(x, y)] = c
    xs = [x for x, _ in pixels]
    gx = CX - (min(xs) + max(xs) + 1) // 2
    gy = LAP - 6 - (1 if plan.get('jolt') else 0)          # Its body across the lap
    mag = {}
    if kind == 'rifle':
        x0, x1, y0 = RIFLE_MAGAZINE
        mag = {xy: c for xy, c in pixels.items() if x0 <= xy[0] <= x1 and xy[1] >= y0}
        if plan.get('mag') in ('pulled', 'gone'):
            for xy in mag:
                del pixels[xy]
    for (x, y), c in pixels.items():
        if kind == 'revolver' and abs(gx + x - CX) > REVOLVER_REACH:
            continue                                         # It lies between her two hands, held
        put(img, ox, gx + x, gy + y, c)
    if plan.get('mag') == 'pulled':
        for (x, y), c in mag.items():
            put(img, ox, gx + x, gy + y + 3, c)

    def glove(x: int, y: int) -> None:
        for dy in range(3):
            for dx in range(4):
                edge = dx in (0, 3) or dy == 2
                put(img, ox, x + dx, y + dy, ink if edge else hand)

    def forearm(elbow: tuple, x: int, y: int) -> None:
        """A sleeve from the elbow to a hand at (x, y), outlined."""
        (ex, ey), (tx, ty) = elbow, (x + 1, y)
        n = max(abs(tx - ex), abs(ty - ey), 1)
        cloth = {}
        for t in range(n + 1):
            px = round(ex + (tx - ex) * t / n)
            py = round(ey + (ty - ey) * t / n)
            for ddx in (0, 1, 2):
                for ddy in (0, 1):
                    cloth[(px + ddx, py + ddy)] = char['sleeve'][1 if ddy else 0]
        for (cx, cy), c in outlined(cloth, ink).items():
            put(img, ox, cx, cy, c)

    if 'sleeve' in char:                                     # His arms: one on the grip...
        elbow_y = SEATED_ELBOW_ROW
        grip = (gx + (3 if kind == 'rifle' else 6), gy + 8)
        spot = plan['hand']
        free = (CX + 1, LAP - 9) if spot == 'pouch' else (gx + spot[0], gy + spot[1])
        forearm((CX - 11, elbow_y), *grip)
        forearm((CX + 8, elbow_y), *free)                    # ...the other busy
        hold = plan.get('hold')
        if hold == 'mag':                                    # Its top out of the hand
            mx = min(x for x, _ in mag)
            my = min(y for _, y in mag)
            for (x, y), c in mag.items():
                put(img, ox, free[0] + 1 + x - mx, free[1] - 4 + y - my, c)
        elif hold == 'shell':
            for dy in range(3):
                put(img, ox, free[0] + 1, free[1] - 3 + dy, SHELL[2] if dy == 2 else SHELL[dy])
                put(img, ox, free[0] + 2, free[1] - 3 + dy, SHELL[2] if dy == 2 else SHELL[0])
        glove(*grip)
        glove(*free)
    for i in range(plan.get('empties', 0) * 2):              # Brass falling from the cylinder
        put(img, ox, gx + 13 + i * 2, gy + 9 + i * 2 + step, rgb(0xf0c860) if i % 2 else rgb(0xc89a3a))
    if plan.get('rounds'):
        for i in range(2):
            put(img, ox, gx + 14 + i * 2, gy + 4, rgb(0xf0c860))
    if plan.get('jolt'):                                     # Click
        for x, y in ((gx + 21, gy - 2), (gx + 23, gy - 1), (gx + 20, gy - 3)):
            put(img, ox, x, y, rgb(0xfff6dc))


def zs(img: Image, ox: int, count: int, ink: tuple) -> None:
    """Little z's over the head, dozing."""
    white = rgb(0xf0ecdc)
    for i in range(count):
        x0, y0 = CX + 8 + i * 5, 5 - i * 3
        for (x, y) in ((0, 0), (1, 0), (2, 0), (1, 1), (0, 2), (1, 2), (2, 2)):
            put(img, ox, x0 + x, y0 + y, white)


def tidy_cowgirl(img: Image, ox: int, dy: int, nod: int = 0) -> None:
    """What mirroring her walk leaves wrong from the front: one buckle in the
    middle of the belt, not two; her shoulders under their sleeves; no loose specks."""
    brass = {(0xb8, 0x90, 0x3a), (0xec, 0xc8, 0x68)}
    rows = [y for y in range(H) for x in range(W) if img.get(ox + x, y)[:3] in brass and img.get(ox + x, y)[3]]
    if rows:
        top, bottom = min(rows), max(rows)
        for y in range(top, bottom + 1):
            for x in range(W):
                if img.get(ox + x, y)[3] and img.get(ox + x, y)[:3] in brass or (y == top + 1 and abs(x + 0.5 - CX) < 3):
                    img.set(ox + x, y, rgb(0x4a2e18))
            for x in (CX - 2, CX - 1, CX, CX + 1):
                img.set(ox + x, y, rgb(0xecc868) if y == top else rgb(0xb8903a))
        img.set(ox + CX - 1, top + 1, rgb(0x4a2e18))
        img.set(ox + CX, top + 1, rgb(0x4a2e18))
    for y in range(H):
        for x in range(W):
            c = img.get(ox + x, y)
            if c[3] and y <= 40 + dy + nod and abs(x + 0.5 - CX) >= 8 and c[:3] in COWGIRL_SKIN:
                img.set(ox + x, y, rgb(0x6c7a84))
    neckline_front(img, ox, nod)
    for y in range(1, H - 1):                            # Outline left floating beside her sleeves
        for x in range(1, W - 1):
            c = img.get(ox + x, y)
            if c[3] and c[:3] == (0x25, 0x20, 0x18) and not any(img.get(ox + x + a, y + b)[3]
                                                                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                img.set(ox + x, y, (0, 0, 0, 0))
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if img.get(ox + x, y)[3] and not any(img.get(ox + x + a, y + b)[3] for a in (-1, 0, 1)
                                                 for b in (-1, 0, 1) if a or b):
                img.set(ox + x, y, (0, 0, 0, 0))


def badge_front(img: Image, ox: int) -> None:
    """Her sheriff's badge, as on every other pose (rework_cowgirl.sheriff_badge):
    the same star, the same place under her neckline, over her corset or jacket.
    Mirroring her walk's other side left it out. It is placed from the lace at
    the middle of her neckline, which stays put while her head nods. Sat, her
    corset is narrower than standing, so the star may lie over the dark band down
    her side too (never her sleeve, nor the lacing), or its points would be cut off."""
    laces = [y for y in range(H) if img.get(ox + CX, y)[3] and img.get(ox + CX, y)[:3] == LACE[0][:3]]
    if not laces:
        return
    face = laces[0] - LACE_SMILE[0] - CHOKER_UNDER_FACE   # The lace's middle is LACE_SMILE[0] under the choker
    under = CORSET_TONES | JACKET_TONES | {(0x25, 0x20, 0x18)}
    for j, row in enumerate(BADGE):
        for i, mark in enumerate(row):
            x, y = CX + BADGE_X + i, face + BADGE_UNDER_FACE + j
            if mark != '.' and img.get(ox + x, y)[3] and img.get(ox + x, y)[:3] in under:
                img.set(ox + x, y, BADGE_TONES[mark])


def neckline_front(img: Image, ox: int, nod: int) -> None:
    """Her neckline seen from the front, the same as standing: the scoop of skin and
    the lace curving up to both shoulders. Dozing, her head comes down over the top
    of it and the rest stays where it is."""
    chokers = [y for y in range(H) if img.get(ox + CX, y)[3] and img.get(ox + CX, y)[:3] == CHOKER[:3]]
    if not chokers:
        return
    choker = chokers[0] - nod
    for d, offset in enumerate(LACE_SMILE):
        lace_y = choker + offset
        for y in range(choker + 1 + nod, choker + max(LACE_SMILE) + 2):
            bare = BARE_WIDTH.get(y - choker, 0)
            if y < lace_y:
                c = (rgb(0xd99a5b) if d == bare or y == lace_y - 1 else rgb(0xfedca3)) if d <= bare else \
                    rgb(0x6c7a84) if d <= bare + 1 else rgb(0x505c66)
            elif y == lace_y:
                c = LACE[0]
            elif y == lace_y + 1 and d % 2 == 0:
                c = LACE[1]
            else:
                c = COWGIRL_CORSET
            for x in (CX - 1 - d, CX + d):
                if img.get(ox + x, y)[3]:
                    img.set(ox + x, y, c)
    for x in (CX - 1, CX):
        img.set(ox + x, choker + nod, rgb(0xecc868))     # The pendant, on her choker as when she stands
        img.set(ox + x, choker + 1 + nod, rgb(0xb8903a))


def make_sit(name: str, gun: int, kind: str) -> Image:
    if name == 'swat':
        from swat_sit import make
        return make(gun, kind)
    char = CHARS[name]
    weapons = load(ROOT / 'assets/sprites/ui/weapons.png')
    # Her walk with no arms: hers are drawn here, none of the swinging ones on her
    if name == 'cowgirl':
        walk = load(ROOT / 'assets/sprites/characters/cowgirl/legs.png')
        # Match dress()/landmarks(): the light face plane defines the body,
        # not the skin shadow two rows higher under the hat.
        face = min(y for y in range(walk.height) for x in range(42) if walk.get(x, y)[:3] == (0xfe, 0xdc, 0xa3))
        belt = face + BELT_UNDER_FACE + DROP
    out = Image(W * 14, H)
    for f in range(14):
        ox = f * W
        dy = -3 if f == 0 else -1 if f == 2 else 0           # Getting down; a breath in
        nod = {10: 1, 11: 2, 12: 3, 13: 2}.get(f, 0)
        reloading = 4 <= f <= 9
        legs(out, ox, char, 1 if f == 0 else 0)
        # Breathing in, her shoulders rise; dozing, the arms sag with her head.
        arm = {2: (1, 0), 3: (0, 1)}.get(f, (0, (nod + 1) // 2 if f >= 10 else 0))
        cowgirl_upper(out, ox, walk, dy, nod, arm)
        if reloading:
            reload_step(out, ox, weapons, char, gun, kind, f - 4)
        if name == 'cowgirl':
            tidy_cowgirl(out, ox, dy, nod)
            body = {(x, y): out.get(ox + x, y) for y in range(H) for x in range(W) if out.get(ox + x, y)[3]}
            corset_bust(body, belt + dy, CX - 0.5)
            cropped_jacket(body, belt + dy, CX - 0.5, front=True)
            jacket_buttons(body, belt + dy, CX - 0.5, front=True)
            for (x, y), color in body.items():
                out.set(ox + x, y, color)
            badge_front(out, ox)
        if f >= 12:
            zs(out, ox, 1 if f == 12 else 2, char['ink'])
    return out


def main() -> int:
    for name, char in CHARS.items():
        for sheet_name, gun, kind in char['guns']:
            sheet = make_sit(name, gun, kind)
            if name == 'swat':
                from swat_materials import finish
                finish(sheet)
            path = ROOT / 'assets/sprites/characters' / name / f'{sheet_name}.png'
            sheet.save(path)
            print(f'make_sit: {path.relative_to(ROOT)} ({sheet.width} x {sheet.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
