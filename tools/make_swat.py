#!/usr/bin/env python3
"""Make all 23 SWAT sheets in the sheriff's compact pixel-art style.

Usage: tools/make_swat.py

docs/templates/swat/game_style_walk.png is the compact eight-frame walk.
The original frames supply the legs. Idle, walking and aiming share one
body, neck and helmet; the upper half moves together with each footfall.
The same sleeves hang relaxed or hold the gun. Everything follows the cowgirl's template (docs/CHARACTERS.md):
same frames, pivots, ground rows and muzzle.

The command delegates to rebuild_swat.py, including sitting, fainting,
planting dynamite and walking with either flashlight. Standard library only.
"""
from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402
from swat_materials import CLOTH, GLOVE  # noqa: E402
from swat_body import FAR_SHOULDER, NEAR_SHOULDER, WAIST, UPPER_ARM, FOREARM, proportions  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs/templates/swat/game_style_walk.png'
BODY_SOURCE = ROOT / 'docs/templates/swat/game_style_body.png'
OUT_DIR = ROOT / 'assets/sprites/characters/swat'

INK = rgb(0x252018)
SLEEVE = [rgb(c) for c in (0x29343b, 0x41494a, 0x5d6870, 0x697174)]
SLEEVE_FAR = [rgb(c) for c in (0x252018, 0x29343b, 0x41494a, 0x5d6870)]
PAD = [rgb(c) for c in (0x29343b, 0x5d6870, 0x77807b)]
SKIN = [rgb(0xb98f71), rgb(0xedc09e)]
SHELL = [rgb(0xb83c28), rgb(0xe8684a), rgb(0xf0c860)]  # Red hull, its light, brass base
METAL = {'1': rgb(0x2c2c2c), '2': rgb(0x424242), '3': rgb(0x505050), '4': rgb(0x868689),
         '5': rgb(0xa7a8a8), 'b': rgb(0x1c1c1c)}
FLASH = {'W': rgb(0xfff6dc), 'Y': rgb(0xffd23c), 'o': rgb(0xf08a24), 'r': rgb(0xc84a14)}

FRAMES = 8
WALK_W, WALK_H = 42, 67
JUMP_W, JUMP_H = 54, 82
SHOOT_W, SHOOT_H = 81, 80
# Where a point of the walk frame lands on the jump and shoot frames: their
# pivots and ground rows differ by these (player.c).
JUMP_SHIFT = (6, 8)
SHOOT_SHIFT = (12, 7)


# --- Images and layers ----------------------------------------------------------

def load(path: Path) -> Image:
    w, h, px = decode_png_rgba(path)
    img = Image(w, h)
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            img.set(x, y, tuple(px[i:i + 4]))
    return img


def crop(img: Image, x0: int, y0: int, x1: int, y1: int) -> Image:
    out = Image(x1 - x0, y1 - y0)
    for y in range(y0, y1):
        for x in range(x0, x1):
            out.set(x - x0, y - y0, img.get(x, y))
    return out


def paste(dst: Image, src: Image, ox: int, oy: int) -> None:
    """Copies the opaque pixels of src (the art has no partial alpha)."""
    for y in range(src.height):
        for x in range(src.width):
            c = src.get(x, y)
            if c[3]:
                dst.set(x + ox, y + oy, c)


class Layer:
    """Loose pixels of one part, outlined on its own so parts read apart."""

    def __init__(self) -> None:
        self.px: dict[tuple[int, int], tuple] = {}

    def put(self, x: float, y: float, c: tuple) -> None:
        self.px[(int(x), int(y))] = c

    def outlined(self) -> 'Layer':
        out = Layer()
        for (x, y) in self.px:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in self.px:
                    out.px[(x + dx, y + dy)] = INK
        out.px.update(self.px)
        return out


def compose(w: int, h: int, parts: list) -> Image:
    """Back to front: Layers, or (Image, x, y) to paste."""
    img = Image(w, h)
    for part in parts:
        if isinstance(part, tuple):
            paste(img, *part)
        else:
            for (x, y), c in part.px.items():
                img.set(x, y, c)
    return img


# --- Limbs ------------------------------------------------------------------------

def ik(start: tuple, end: tuple, l1: float, l2: float, bend: int) -> tuple:
    """Middle joint (elbow, knee) of a two-bone limb. bend +1 puts it behind a
    hanging limb (elbows), -1 ahead of it (knees)."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    d = max(1e-3, math.hypot(dx, dy))
    if d > l1 + l2 + 1e-6 or d < abs(l1 - l2) - 1e-6:
        raise ValueError(f'Unreachable arm target: {start} -> {end}, length {d:.3f}')
    reach = d
    a = (l1 * l1 - l2 * l2 + reach * reach) / (2 * reach)
    k = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / d, dy / d
    return (start[0] + a * ux - bend * k * uy, start[1] + a * uy + bend * k * ux)


LIGHT = (-0.55, -0.83)  # The sheriff's fixed upper-left light


def tube(layer: Layer, a: tuple, b: tuple, r: float, ramp: list) -> None:
    """A limb segment: the pixels within r of a-b, shaded across its width."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    ll = vx * vx + vy * vy or 1e-6
    for y in range(int(min(a[1], b[1]) - r - 1), int(max(a[1], b[1]) + r + 2)):
        for x in range(int(min(a[0], b[0]) - r - 1), int(max(a[0], b[0]) + r + 2)):
            cx, cy = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((cx - a[0]) * vx + (cy - a[1]) * vy) / ll))
            ox, oy = cx - (a[0] + t * vx), cy - (a[1] + t * vy)
            if ox * ox + oy * oy > r * r:
                continue
            lit = (ox * LIGHT[0] + oy * LIGHT[1]) / r
            shade = 3 if lit > 0.55 else 2 if lit > 0.1 else 1 if lit > -0.45 else 0
            layer.put(x, y, ramp[min(shade, len(ramp) - 1)])


def block(layer: Layer, cx: int, cy: int, w: int, h: int, ramp: list) -> None:
    """A small plate with cut corners, lit on top and front."""
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) and y in (0, h - 1) and w > 2 and h > 2:
                continue
            c = ramp[1]
            if y == 0 or (x == w - 1 and y < h - 1):
                c = ramp[-1]
            if y == h - 1:
                c = ramp[0]
            layer.put(cx - w // 2 + x, cy - h // 2 + y, c)


def square(layer: Layer, x: int, y: int, w: int, h: int, top: tuple, rest: tuple) -> None:
    for dy in range(h):
        for dx in range(w):
            layer.put(x + dx, y + dy, top if dy == 0 else rest)


def arm(shoulder: tuple, hand: tuple, near: bool, upper: float = UPPER_ARM, fore: float = FOREARM,
        elbow: tuple = None) -> Layer:
    """The same fitted sleeve in relaxed, walking and weapon poses."""
    lay = Layer()
    elbow = elbow if elbow is not None else ik(shoulder, hand, upper, fore, 1)
    lay.joints = (shoulder, elbow, hand)
    ramp = SLEEVE if near else SLEEVE_FAR
    # Use the sheriff's continuous sleeve stroke and blend the shoulder into
    # the carrier, rather than outlining two long tubes over the chest.
    from cowgirl_arm import arm_limb, glove, SLEEVE as TAGS, GLOVE as HAND_TAGS, INK as EDGE
    shades = dict(zip(TAGS, (ramp[3], ramp[2], ramp[0])))
    shades[EDGE] = INK
    sleeve = arm_limb(shoulder, elbow, hand, shoulder_radius=2.6, wrist_radius=1.9)
    lay.px.update({p: shades.get(c, c) for p, c in sleeve.items()})
    hand_colors = dict(zip(HAND_TAGS, (GLOVE[1], GLOVE[0])))
    hand_colors[EDGE] = INK
    lay.px.update({p: hand_colors.get(c, c) for p, c in glove(hand, elbow, radius=1.85).items()})
    if near:
        block(lay, round(shoulder[0] + .18 * (elbow[0] - shoulder[0])),
              round(shoulder[1] + .18 * (elbow[1] - shoulder[1])), 4, 3, PAD)
        # A fabric patch and articulated elbow guard move with the sleeve.
        square(lay, round(shoulder[0] + (elbow[0] - shoulder[0]) * 0.55),
               round(shoulder[1] + (elbow[1] - shoulder[1]) * 0.55), 2, 1, PAD[1], PAD[0])
        block(lay, round(elbow[0]), round(elbow[1]), 3, 3, [CLOTH[0], CLOTH[1], CLOTH[2]])
    # The sheriff's stroke suppresses the outline at the shoulder to blend
    # into her jacket. Close only the edges outside this carrier's silhouette,
    # so a raised sleeve cannot leave a pale tab floating beside the neck.
    joint = NEAR_SHOULDER if near else FAR_SHOULDER
    ox, oy = shoulder[0] - joint[0], shoulder[1] - joint[1]
    body = standing_body()
    edge = {}
    for x, y in lay.px:
        if math.hypot(x - shoulder[0], y - shoulder[1]) > 4:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p not in lay.px and not body.get(round(p[0] - ox), round(p[1] - oy))[3]:
                edge[p] = INK
    edge.update(lay.px)
    lay.px = edge
    return lay


def hand(at: tuple, coming_from: tuple = None) -> Layer:
    """The far hand alone, on the handguard in front of the gun."""
    lay = Layer()
    from cowgirl_arm import glove, GLOVE as TAGS, INK as EDGE
    if coming_from is None:
        joint = FAR_SHOULDER[0] + SHOOT_SHIFT[0], FAR_SHOULDER[1] + SHOOT_SHIFT[1]
        coming_from = ik(joint, at, UPPER_ARM, FOREARM, 1)
    shades = dict(zip(TAGS, (GLOVE[1], GLOVE[0])))
    shades[EDGE] = INK
    lay.px.update({p: shades.get(c, c) for p, c in glove(at, coming_from, radius=1.85).items()})
    return lay


# --- His body -----------------------------------------------------------------

# Rig landmarks live in swat_body.py; the full torso is BODY_SOURCE.


def frame(source: Image, i: int) -> Image:
    return crop(source, i * WALK_W, 0, (i + 1) * WALK_W, WALK_H)


def load_source() -> Image:
    return load(SOURCE)


@lru_cache(maxsize=1)
def _body() -> Image:
    source = load(BODY_SOURCE)
    # A fragment of the old hanging shoulder was included in the head crop.
    # It is outside the neck and belongs to the sleeve now drawn by the rig.
    for y in range(24, 28):
        for x in range(13):
            source.set(x, y, (0, 0, 0, 0))
    # Restore the side fabric removed with the old source sleeve. This small
    # ribcage plane stays behind the arm in every pose, including aiming.
    for y, left in enumerate((12, 11, 11, 11, 11, 12, 12, 12, 12, 13), 28):
        for x in range(left, 14):
            source.set(x, y, INK if x == left else CLOTH[0] if x == left + 1 else CLOTH[1])
    from swat_optics import mount
    return mount(proportions(source))


def standing_body(source: Image = None) -> Image:
    """Shared anatomical torso, with the same relaxed legs as the idle pose."""
    return _body()


# --- Jump -----------------------------------------------------------------------

# Whole frames of his walk, like the cowgirl's jump: the body drops on the
# crouch and the landing, and the legs fold (rows taken out of them) on the
# way up. Her sheet's head and feet rows, frame by frame, give the numbers.
# Per frame: walk frame, body drop, leg rows taken out.
JUMP_POSES = [
    (0, 4, 4),    # Crouch
    (7, 1, 1),    # Launch
    (2, 1, 4),    # Rise, feet up
    (6, -1, 5),   # Tuck
    (6, -1, 6),
    (2, 0, 3),    # Falling
    (0, 5, 5),    # Land
    (7, 0, 0),    # Recover
]
LEG_FOLD = (52, 48, 55, 50, 46, 53)  # Rows taken out, first to last: shins and thighs


def fold_legs(f: Image, rows: int) -> Image:
    """The frame with `rows` leg rows taken out, feet kept on the ground row."""
    drop = set(LEG_FOLD[:rows])
    out = Image(WALK_W, WALK_H)
    keep = [y for y in range(WALK_H) if y not in drop]
    for j, y in enumerate(keep):
        for x in range(WALK_W):
            out.set(x, j + rows, f.get(x, y))
    return out


def make_jump(source: Image) -> Image:
    jx, jy = JUMP_SHIFT
    sheet = Image(JUMP_W * FRAMES, JUMP_H)
    for i, (src, drop, fold) in enumerate(JUMP_POSES):
        f = fold_legs(frame(source, src), fold)
        # Folded rows lower the head; a body drop below fold lifts the feet.
        paste(sheet, f, i * JUMP_W + jx, jy + drop - fold)
    return sheet


# --- Guns -----------------------------------------------------------------------

MUZZLE_LOCAL = (28, 3)  # Last barrel pixel of both guns, in gun coordinates
MUZZLE = (63, 32)       # ...on the shoot frame: the bullet starts at x 64, y 32.5


def rect(t: dict, x0: int, y0: int, x1: int, y1: int, c: str) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t[(x, y)] = c


BAYONET = {(28, 4): '1', (29, 4): '3', (30, 4): '4', (31, 4): '4', (32, 4): '4', (33, 4): '4',
           (34, 4): '5', (35, 4): '5', (30, 5): '3', (31, 5): '3', (32, 5): '3', (33, 5): '2'}


def mounted_light(t: dict) -> None:
    """The flashlight fixed under the barrel of both his guns, off: lit by
    light_lens. Its lens is at LENS_LOCAL."""
    rect(t, 22, 5, 26, 6, '1')
    rect(t, 22, 5, 25, 5, '2')
    t[(24, 6)] = '3'                  # The switch
    t[(26, 5)] = t[(26, 6)] = '4'


def rifle(magazine: bool = True) -> tuple[dict, tuple, tuple]:
    """Short rifle, folded stock, small optic, its flashlight and bayonet fixed.
    Pixels (METAL keys), grip and handguard, in gun coordinates (x along the
    barrel); without the magazine while it is being changed."""
    t: dict = {}
    rect(t, -7, 2, -3, 3, '1')        # Stock meets the shoulder, not the wrist
    rect(t, -7, 4, -6, 7, '1')       # Butt seated against the shoulder pocket
    rect(t, -1, 1, 10, 5, '2')        # Receiver sits over the broad chest
    rect(t, -1, 1, 10, 1, '3')
    rect(t, -1, 5, 10, 5, '1')
    rect(t, 2, -1, 7, 0, '1')         # Optic
    t[(6, -1)] = '4'
    t[(7, -1)] = '5'
    rect(t, -1, 6, 0, 7, '1')         # Trigger behind the receiver, below the cheek
    t[(-2, 8)] = t[(-1, 8)] = '1'
    if magazine:
        rect(t, 5, 6, 7, 8, '2')      # Magazine
        rect(t, 6, 9, 8, 9, '2')
        t[(5, 6)] = '3'
    rect(t, 11, 2, 23, 4, '1')        # Handguard
    rect(t, 11, 2, 23, 2, '2')
    rect(t, 24, 3, 28, 3, '2')        # Barrel
    rect(t, 26, 2, 27, 4, '1')        # Muzzle brake
    for x in (1, 2, 3):               # Highlight stroke
        t[(x, 1)] = '4'
    t[(4, 1)] = '5'
    mounted_light(t)
    t.update(BAYONET)
    return t, (-.5, 6.5), (13.5, 4.5)


def shotgun(pump_back: int = 0) -> tuple[dict, tuple, tuple]:
    """Pump shotgun: full stock, long barrel over the tube, ribbed pump
    (pump_back px toward the stock while it is racked)."""
    t: dict = {}
    rect(t, -9, 3, -3, 5, 'b')        # Stock seated against shoulder
    rect(t, -9, 2, -5, 2, '1')
    rect(t, -10, 3, -10, 6, '1')
    rect(t, -9, 6, -6, 6, 'b')
    rect(t, -2, 2, 7, 5, '2')         # Receiver
    rect(t, -2, 2, 7, 2, '3')
    rect(t, -2, 5, 7, 5, '1')
    rect(t, -3, 6, -2, 7, 'b')       # Grip
    t[(-4, 8)] = t[(-3, 8)] = 'b'
    rect(t, 8, 2, 28, 3, '2')         # Barrel
    rect(t, 8, 2, 28, 2, '3')
    rect(t, 8, 4, 24, 4, '1')         # Magazine tube
    rect(t, 11 - pump_back, 4, 17 - pump_back, 5, 'b')  # Pump
    for x in (12, 14, 16):
        t[(x - pump_back, 5)] = '1'
    t[(27, 1)] = '4'                  # Bead sight
    for x in (1, 2, 3):
        t[(x, 2)] = '4'
    t[(16, 2)] = t[(17, 2)] = '5'
    mounted_light(t)
    return t, (-2.5, 6.5), (14.0 - pump_back, 5.0)


def gun_layer(gun: dict, angle: float, pivot: tuple, at: tuple):
    """The gun turned by angle degrees (+ raises the muzzle) about pivot (gun
    coordinates) placed at `at`. Returns the layer and a gun-to-frame mapper."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def to_frame(p: tuple) -> tuple:
        lx, ly = p[0] - pivot[0], p[1] - pivot[1]
        return (at[0] + lx * ca + ly * sa, at[1] - lx * sa + ly * ca)

    lay = Layer()
    if angle == 0:  # Exact, so the muzzle lands on its pixel
        for (x, y), c in gun.items():
            lay.put(x - pivot[0] + at[0], y - pivot[1] + at[1], METAL[c])
        return lay.outlined(), to_frame
    corners = [to_frame(p) for p in gun]
    for y in range(int(min(p[1] for p in corners)) - 2, int(max(p[1] for p in corners)) + 3):
        for x in range(int(min(p[0] for p in corners)) - 2, int(max(p[0] for p in corners)) + 3):
            # Each frame pixel takes the gun pixel under its center.
            fx, fy = x + 0.5 - at[0], y + 0.5 - at[1]
            key = (math.floor(fx * ca - fy * sa + pivot[0]), math.floor(fx * sa + fy * ca + pivot[1]))
            if key in gun:
                lay.put(x, y, METAL[gun[key]])
    return lay.outlined(), to_frame


# Muzzle flashes, from x 64 forward and centered on the barrel row.
RIFLE_FLASH = [  # Short and dry
    '....Y.....',
    '.Y..YY....',
    '..YWWY.Y..',
    'YWWWWWWYY.',
    '..YWWY.Y..',
    '.Y..YY....',
    '....Y.....',
]
SHOTGUN_FLASH = [  # Bigger, orange, fanned out
    '.....o.........',
    '..o..oY....o...',
    '...oYYYo..o....',
    '.oYYWWWYYoo..r.',
    'oYWWWWWWWWYYoor',
    '.oYYWWWYYoo..r.',
    '...oYYYo..o....',
    '..o..oY....o...',
    '.....o.........',
]


def flash_layer(rows: list[str]) -> Layer:
    lay = Layer()
    for j, line in enumerate(rows):
        for i, ch in enumerate(line):
            if ch != '.':
                lay.put(MUZZLE[0] + 1 + i, MUZZLE[1] - len(rows) // 2 + j, FLASH[ch])
    return lay


def shoot_frames(body: Image, gun_def, flash: list[str], kick: int):
    """One pose definition for the full sprite, separated art and joint checks."""
    gun, grip, guard = gun_def
    # Aimed (frames 3 and 4): the muzzle on its mark. The other frames turn
    # the gun about the grip: raised from low ready, recoil, lowered.
    aimed = (MUZZLE[0] - (MUZZLE_LOCAL[0] - grip[0]), MUZZLE[1] - (MUZZLE_LOCAL[1] - grip[1]))
    poses = [  # Angle, grip offset
        (-35, (-2, 8)),                       # 0 Low ready, forearms away from the collar
        (-22, (-1, 5)),                       # 1 Raising
        (-8, (0, 2)),                         # 2
        (0, (0, 0)),                          # 3 Aim
        (0, (0, 0)),                          # 4 Fire
        (6 + 3 * (kick - 2), (-kick, -1)),    # 5 The shoulder absorbs recoil
        (0, (-1, 0)),                         # 6 Settling level at the shoulder
        (-10, (-1, 1)),                       # 7 A small lowering step, without an elbow snap
    ]
    sx, sy = SHOOT_SHIFT

    def at(p: tuple) -> tuple:
        return (p[0] + sx, p[1] + sy)

    for i, (angle, (gx, gy)) in enumerate(poses):
        if angle:
            layer, to_frame = gun_layer(gun, angle, grip, (aimed[0] + gx + 0.5, aimed[1] + gy + 0.5))
            g = to_frame(grip)
        else:
            layer, to_frame = gun_layer(gun, 0, grip, (aimed[0] + gx, aimed[1] + gy))
            g = (aimed[0] + gx, aimed[1] + gy)
        h = to_frame(guard)
        near_hand, far_hand = (g[0] - 0.5, g[1] - 0.5), (h[0] - 0.5, h[1] - 0.5)
        far_arm = arm(at(FAR_SHOULDER), far_hand, near=False)
        near_arm = arm(at(NEAR_SHOULDER), near_hand, near=True)
        weapon_parts = [layer, hand(far_hand, far_arm.joints[1])]
        if i == 4:
            weapon_parts.append(flash_layer(flash))
        weapon = compose(SHOOT_W, SHOOT_H, weapon_parts)
        posed = compose(SHOOT_W, SHOOT_H, [far_arm, (body, sx, sy), (weapon, 0, 0), near_arm])
        yield posed, near_arm, far_arm, weapon


def make_shoot(body: Image, gun_def, flash: list[str], kick: int) -> Image:
    sheet = Image(SHOOT_W * FRAMES, SHOOT_H)
    for i, (posed, _, _, _) in enumerate(shoot_frames(body, gun_def, flash, kick)):
        paste(sheet, posed, i * SHOOT_W, 0)
    return sheet


# --- Reload ---------------------------------------------------------------------

# Where the near hand fetches a new magazine or shells: the vest's pouches, on
# the walk frame.
POUCH_AT = (20.0, 41.0)


def magazine_layer(at: tuple) -> Layer:
    """A loose magazine hanging from the hand at `at`, curved forward, lit
    on its front so it reads against the vest."""
    lay = Layer()
    x, y = round(at[0]), round(at[1]) + 1
    for dy in range(5):
        for dx in range(3):
            c = METAL['4'] if dx == 2 else METAL['3'] if dy == 0 else METAL['2']
            lay.put(x + dx + dy // 3, y + dy, c)
    return lay.outlined()


def shell_layer(at: tuple) -> Layer:
    """One shell between the fingers at `at`: brass base, red hull."""
    lay = Layer()
    x, y = round(at[0]) + 1, round(at[1]) - 1
    for dy in range(2):
        lay.put(x, y + dy, SHELL[2])
        for dx in (1, 2, 3):
            lay.put(x + dx, y + dy, SHELL[1] if dy == 0 else SHELL[0])
    return lay.outlined()


def make_reload(body: Image, kind: str, lower_only: bool = False) -> Image:
    """8 frames over the gun's magazine reload (shoot.c), from the recoil's
    settled pose back to ready. The far hand keeps the gun up by the
    handguard; the near hand does the work. Rifle: magazine out, a new one
    from the vest, in, charging handle. Shotgun: three shells from the vest
    into the tube under the receiver, then the pump racked."""
    sx, sy = SHOOT_SHIFT

    def at(p: tuple) -> tuple:
        return (p[0] + sx, p[1] + sy)

    pouch = at(POUCH_AT)
    base_grip = rifle()[1] if kind == 'rifle' else shotgun()[1]
    if kind == 'rifle':
        well = (6.0, 7.0)     # Magazine well, gun coordinates
        handle = (0.0, 1.0)   # Charging handle
        # Angle, magazine in the gun, near hand on ('gun', point) or at
        # ('frame', point), what it holds.
        frames = [
            (-14, True, ('gun', base_grip), None),
            (-24, True, ('gun', well), None),
            (-24, False, ('gun', (well[0], well[1] + 5)), 'mag'),
            (-24, False, ('frame', pouch), 'mag'),
            (-24, False, ('gun', (well[0] - 1, well[1] + 7)), 'mag'),
            (-24, True, ('gun', well), None),
            (-16, True, ('gun', handle), None),
            (-8, True, ('gun', base_grip), None),
        ]
    else:
        port = (5.0, 6.0)     # Loading port, under the receiver
        # Angle, pump back, near hand, what it holds.
        frames = [
            (-12, 0, ('gun', base_grip), None),
            (-18, 0, ('frame', pouch), 'shell'),
            (-18, 0, ('gun', port), 'shell'),
            (-18, 0, ('frame', pouch), 'shell'),
            (-18, 0, ('gun', port), 'shell'),
            (-18, 0, ('frame', pouch), 'shell'),
            (-14, 4, ('gun', base_grip), None),   # Racked: pump back
            (-8, 0, ('gun', base_grip), None),
        ]
    aimed = (MUZZLE[0] - (MUZZLE_LOCAL[0] - base_grip[0]), MUZZLE[1] - (MUZZLE_LOCAL[1] - base_grip[1]))
    sheet = Image(SHOOT_W * FRAMES, SHOOT_H)
    for i, (angle, state, target, held) in enumerate(frames):
        gun, grip, guard = rifle(magazine=state) if kind == 'rifle' else shotgun(pump_back=state)
        layer, to_frame = gun_layer(gun, angle, grip, (aimed[0] - 1.5, aimed[1] + 2.5))
        h = to_frame(guard)
        far_hand = (h[0] - 0.5, h[1] - 0.5)
        space, point = target
        g = to_frame(point) if space == 'gun' else point
        near_hand = (g[0] - 0.5, g[1] - 0.5)
        parts = [
            arm(at(FAR_SHOULDER), far_hand, near=False),
            (body, sx, sy),
            layer,
            hand(far_hand),
            arm(at(NEAR_SHOULDER), near_hand, near=True),
        ]
        # In front of the hand, or the fist hides it.
        if held == 'mag':
            parts.append(magazine_layer(near_hand))
        elif held == 'shell':
            parts.append(shell_layer(near_hand))
        if lower_only:
            # Keep the moving hands, magazine and shells over the animated
            # thighs, without reintroducing the standing body's legs.
            parts = [part for part in parts if not isinstance(part, tuple)]
            posed = compose(SHOOT_W, SHOOT_H, parts)
            seam = (WAIST + sy) * SHOOT_W
            posed.px[:seam] = [(0, 0, 0, 0)] * seam
        else:
            posed = compose(SHOOT_W, SHOOT_H, parts)
        paste(sheet, posed, i * SHOOT_W, 0)
    return sheet


# --- Grenade throw (level 3) ------------------------------------------------------

GRENADE = [rgb(0x2a2c1a), rgb(0x4a5030), rgb(0x6a7444)]


def grenade_layer(at: tuple) -> Layer:
    """The grenade in the hand at `at`: olive body, its lever."""
    lay = Layer()
    x, y = round(at[0]), round(at[1]) - 3
    for dy in range(4):
        for dx in range(3):
            lay.put(x + dx, y + dy, GRENADE[2] if dx == 0 else GRENADE[1] if dy < 3 else GRENADE[0])
    lay.put(x + 1, y - 1, METAL['5'])
    return lay.outlined()


def ring_layer(at: tuple) -> Layer:
    """The pin's ring, pulled, in the far hand."""
    lay = Layer()
    x, y = round(at[0]) + 2, round(at[1]) - 2
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 2), (2, 1)):
        lay.put(x + dx, y + dy, METAL['5'])
    return lay.outlined()


def make_throw(body: Image) -> Image:
    """8 frames on the shoot template (81 x 80): the gun slung, the pin pulled
    by the far hand, the near arm wound back over the shoulder, the throw
    (the grenade leaves on frame 4), the follow-through and back to ready."""
    sx, sy = SHOOT_SHIFT

    def at(p: tuple) -> tuple:
        return (p[0] + sx, p[1] + sy)

    # Near hand, far hand, grenade in hand, ring in the far hand (walk-frame points).
    poses = [
        ((19, 30), (25, 30), True, False),
        ((19, 30), (29, 27), True, True),
        ((8, 22), (27, 28), True, True),
        ((9, 14), (27, 29), True, False),
        ((28, 22), (26, 31), False, False),
        ((27, 29), (25, 35), False, False),
        ((21, 36), (24, 37), False, False),
        ((16, 38), (23, 38), False, False),
    ]
    sheet = Image(SHOOT_W * FRAMES, SHOOT_H)
    for i, (near, far, holding, ring) in enumerate(poses):
        near_hand, far_hand = at(near), at(far)
        parts = [
            arm(at(FAR_SHOULDER), far_hand, near=False),
            (body, sx, sy),
            arm(at(NEAR_SHOULDER), near_hand, near=True),
        ]
        if holding:
            parts.append(grenade_layer(near_hand))
        if ring:
            parts.append(ring_layer(far_hand))
        if i == 4:                                   # Just let go, ahead of the hand
            parts.append(grenade_layer((near_hand[0] + 4, near_hand[1] - 3)))
        paste(sheet, compose(SHOOT_W, SHOOT_H, parts), i * SHOOT_W, 0)
    return sheet




def fitted_hold(place, angle, grip, guard):
    """Move a raised melee weapon as a rigid piece into both arms' reach.

    Aiming/fire stay on the fixed muzzle. Only the free melee swing needs
    this constraint: stretching a forearm to meet an overhead gun is invalid.
    """
    a = math.radians(angle)
    vx, vy = guard[0] - grip[0], guard[1] - grip[1]
    delta = vx * math.cos(a) + vy * math.sin(a), -vx * math.sin(a) + vy * math.cos(a)
    sx, sy = SHOOT_SHIFT
    near = NEAR_SHOULDER[0] + sx, NEAR_SHOULDER[1] + sy
    far = FAR_SHOULDER[0] + sx - delta[0], FAR_SHOULDER[1] + sy - delta[1]
    x, y = place[0] - .5, place[1] - .5
    reach = UPPER_ARM + FOREARM - .1
    for _ in range(40):
        for cx, cy in (near, far):
            dx, dy = x - cx, y - cy
            distance = math.hypot(dx, dy)
            if distance > reach:
                x, y = cx + dx * reach / distance, cy + dy * reach / distance
    return x + .5, y + .5


def make_melee(body: Image, gun_def) -> Image:
    """7 frames on the shoot template: a smash with the gun held in both
    hands, like a mace: raised, up over the helmet with the muzzle back,
    swinging down, the blow level in front (frame 3, a swoosh along the
    muzzle's path), the follow-through low, back up, low ready."""
    gun, grip, guard = gun_def
    sx, sy = SHOOT_SHIFT
    shoulder = (NEAR_SHOULDER[0] + sx, NEAR_SHOULDER[1] + sy)

    def at(p: tuple) -> tuple:
        return (p[0] + sx, p[1] + sy)

    aimed = (MUZZLE[0] - (MUZZLE_LOCAL[0] - grip[0]), MUZZLE[1] - (MUZZLE_LOCAL[1] - grip[1]))
    poses = [  # Grip (from the near shoulder), angle (+ raises the muzzle)
        ((9, -6), 55),
        ((4, -13), 105),
        ((10, -11), 50),
        ((15, -3), -10),
        ((14, 3), -40),
        ((12, 0), -15),
        ((aimed[0] - 3 - shoulder[0], aimed[1] + 5 - shoulder[1]), -50),
    ]
    tip = max(gun, key=lambda p: p[0])
    sheet = Image(SHOOT_W * 7, SHOOT_H)
    places = []
    for i, ((gx, gy), angle) in enumerate(poses):
        place = fitted_hold((shoulder[0] + gx + 0.5, shoulder[1] + gy + 0.5), angle, grip, guard)
        places.append(place)
        layer, to_frame = gun_layer(gun, angle, grip, place)
        g, h = to_frame(grip), to_frame(guard)
        near_hand, far_hand = (g[0] - 0.5, g[1] - 0.5), (h[0] - 0.5, h[1] - 0.5)
        parts = [
            arm(at(FAR_SHOULDER), far_hand, near=False),
            (body, sx, sy),
            layer,
            hand(far_hand),
            arm(at(NEAR_SHOULDER), near_hand, near=True),
        ]
        if i in (3, 4):  # The swoosh: the muzzle's path since the last pose
            trail = Layer()
            a0, start = poses[i - 1][1], places[i - 1]
            for k in range(15):
                t = k / 14
                ang = a0 + (angle - a0) * t
                p_at = (start[0] + (place[0] - start[0]) * t, start[1] + (place[1] - start[1]) * t)
                a, lx, ly = math.radians(ang), tip[0] + 1 - grip[0], tip[1] - grip[1]
                x = p_at[0] + lx * math.cos(a) + ly * math.sin(a)
                y = p_at[1] - lx * math.sin(a) + ly * math.cos(a)
                shade = SWOOSH_TONES[0] if t > 0.6 else SWOOSH_TONES[1] if t > 0.3 else SWOOSH_TONES[2]
                for w in range(2 if i == 3 and t > 0.4 else 1):
                    trail.put(round(x) + w, round(y), shade)
            parts.append(trail)
        paste(sheet, compose(SHOOT_W, SHOOT_H, parts), i * SHOOT_W, 0)
    return sheet


SWOOSH_TONES = [rgb(0xfff6dc), rgb(0xd8d0c0), rgb(0x9a9488)]

LENS_ON = [rgb(0xfff6dc), rgb(0xffd98a)]


def make_light(body: Image, gun_def) -> Image:
    """16 frames on the shoot template: turning on the flashlight of the gun he
    carries. He brings it up, level, his far hand slides along to the switch and
    thumbs it, the lens lights, the hand goes back; the last frame is held while
    it stays on. Played backwards to turn it off."""
    gun, grip, guard = gun_def
    aimed = (MUZZLE[0] - (MUZZLE_LOCAL[0] - grip[0]), MUZZLE[1] - (MUZZLE_LOCAL[1] - grip[1]))
    switch = (17.5, 6.0)  # Remote switch on the handguard
    # Eased in-betweens: up to level by frame 8, the hand to the switch by 12,
    # the lens lit at 13, the hand back by the end.
    def ease(a: float, b: float, t: float) -> float:
        t = max(0.0, min(1.0, t))
        return a + (b - a) * t * t * (3.0 - 2.0 * t)

    poses = []
    for i in range(16):
        up = i / 8.0
        reach = (i - 8) / 4.0 if i <= 12 else 1.0 - (i - 13) / 2.0
        poses.append((round(ease(-30.0, 0.0, up)), (round(ease(-2.0, 0.0, up)), round(ease(3.0, 0.0, up))),
                      (ease(guard[0], switch[0], reach), ease(guard[1], switch[1], reach))))
    sx, sy = SHOOT_SHIFT
    sheet = Image(SHOOT_W * len(poses), SHOOT_H)

    def at(p: tuple) -> tuple:
        return (p[0] + sx, p[1] + sy)

    for i, (angle, (gx, gy), far) in enumerate(poses):
        if angle:
            layer, to_frame = gun_layer(gun, angle, grip, (aimed[0] + gx + 0.5, aimed[1] + gy + 0.5))
            g = to_frame(grip)
        else:
            layer, to_frame = gun_layer(gun, 0, grip, (aimed[0] + gx, aimed[1] + gy))
            g = (aimed[0] + gx, aimed[1] + gy)
        h = to_frame(far)
        near_hand, far_hand = (g[0] - 0.5, g[1] - 0.5), (h[0] - 0.5, h[1] - 0.5)
        parts = [
            arm(at(FAR_SHOULDER), far_hand, near=False),
            (body, sx, sy),
            layer,
            hand(far_hand),
            arm(at(NEAR_SHOULDER), near_hand, near=True),
        ]
        if i >= 13:                                    # The lens lit
            lens = Layer()
            for y, c in ((5, LENS_ON[0]), (6, LENS_ON[1])):
                p = to_frame((26.0, float(y)))
                lens.put(round(p[0]), round(p[1]), c)
            parts.append(lens)
        paste(sheet, compose(SHOOT_W, SHOOT_H, parts), i * SHOOT_W, 0)
    return sheet


JUG = ['.cc.', 'bccb', 'BBBB', 'BwBB', 'BwBB', 'BBBB', 'bbbb']
JUG_COLORS = {'c': rgb(0x9a643a), 'b': rgb(0x2a5a86), 'B': rgb(0x5aa0d0), 'w': rgb(0xd8f0fa)}
BANDAGE = [rgb(0x9a9488), rgb(0xd8d4c8), rgb(0xf6f2e6)]


def jug_layer(at: tuple, tilt: float) -> Layer:
    """A jug of water held about its middle at `at`, tipped tilt degrees (its
    mouth toward his lips)."""
    a = math.radians(tilt)
    ca, sa = math.cos(a), math.sin(a)
    lay = Layer()
    for y in range(int(at[1]) - 6, int(at[1]) + 7):
        for x in range(int(at[0]) - 6, int(at[0]) + 7):
            fx, fy = x + 0.5 - at[0], y + 0.5 - at[1]
            jx, jy = math.floor(fx * ca - fy * sa + 2.0), math.floor(fx * sa + fy * ca + 3.5)
            if 0 <= jy < len(JUG) and 0 <= jx < 4 and JUG[jy][jx] != '.':
                lay.put(x, y, JUG_COLORS[JUG[jy][jx]])
    return lay.outlined()


def make_drink(body: Image) -> Image:
    """6 frames on the shoot template: the gun slung, a jug of water brought
    up to his lips, tipped, tipped right up, back, lowered."""
    sx, sy = SHOOT_SHIFT

    def at(p: tuple) -> tuple:
        return (p[0] + sx, p[1] + sy)

    poses = [((24, 39), 0), ((24, 30), 20), ((26, 25), 65), ((26, 25), 110), ((26, 25), 65), ((24, 38), 10)]
    sheet = Image(SHOOT_W * 6, SHOOT_H)
    for i, (near, tilt) in enumerate(poses):
        near_hand = at(near)
        parts = [
            arm(at(FAR_SHOULDER), at((30, 44)), near=False),
            (body, sx, sy),
            jug_layer((near_hand[0] + 1, near_hand[1] - 1), tilt),
            arm(at(NEAR_SHOULDER), near_hand, near=True),
        ]
        paste(sheet, compose(SHOOT_W, SHOOT_H, parts), i * SHOOT_W, 0)
    return sheet


def make_bandage(body: Image) -> Image:
    """6 frames on the shoot template: his hand winding a bandage round his
    near thigh, a turn more each frame (round the back on odd frames); the
    last, done, blood showing through."""
    sx, sy = SHOOT_SHIFT

    def at(p: tuple) -> tuple:
        return (p[0] + sx, p[1] + sy)

    thigh = (25, 31, 54, 59)                          # x0, x1, y0, y1 on the frame
    hands = [(18, 44), (16, 44), (19, 43), (16, 43), (19, 44), (18, 44)]
    sheet = Image(SHOOT_W * 6, SHOOT_H)
    for i, near in enumerate(hands):
        done = i == 5
        behind = not done and i % 2 == 1
        wrap = Layer()
        x0, x1, y0, y1 = thigh
        for t in range(min(i + 1, 5)):
            y = y1 - t * 2
            for x in range(x0, x1 + 1):
                wrap.put(x, y + (x - x0) // 4 - 1, BANDAGE[2] if x < x1 - 1 else BANDAGE[1])
        if done:
            wrap.put(x0 + 3, y1 - 4, rgb(0x9c3424))
            wrap.put(x0 + 4, y1 - 4, rgb(0x9c3424))
        near_arm = arm(at(NEAR_SHOULDER), at(near), near=True)
        parts = [arm(at(FAR_SHOULDER), at((30, 44)), near=False), (body, sx, sy)]
        parts += [near_arm, wrap] if behind else [wrap, near_arm]
        if not behind and not done:                   # The roll in his hand
            roll = Layer()
            hx, hy = at(near)
            for dx in (2, 3):
                for dy in (0, 1):
                    roll.put(hx + dx, hy + dy, BANDAGE[2 - dy])
            parts.append(roll.outlined())
        paste(sheet, compose(SHOOT_W, SHOOT_H, parts), i * SHOOT_W, 0)
    return sheet


def make_sheets() -> dict[str, Image]:
    from swat_walk import make_stand, make_walk
    drawing = load_source()
    source = make_walk(drawing)
    stand = make_stand(source, drawing)
    body = standing_body(drawing)
    return {
        'walk': source,
        'stand': stand,
        'legs': make_walk(drawing, no_arms=True),
        'jump': make_jump(source),
        'shoot': make_shoot(body, rifle(), RIFLE_FLASH, kick=2),
        'shoot_shotgun': make_shoot(body, shotgun(), SHOTGUN_FLASH, kick=3),
        'reload': make_reload(body, 'rifle'),
        'reload_shotgun': make_reload(body, 'shotgun'),
        'reload_lower': make_reload(body, 'rifle', lower_only=True),
        'reload_shotgun_lower': make_reload(body, 'shotgun', lower_only=True),
        'throw': make_throw(body),
        'melee': make_melee(body, rifle()),
        'melee_shotgun': make_melee(body, shotgun()),
        'light': make_light(body, rifle()),
        'light_shotgun': make_light(body, shotgun()),
        'drink': make_drink(body),
        'bandage': make_bandage(body),
    }


def main() -> int:
    from rebuild_swat import main as rebuild
    return rebuild()


if __name__ == '__main__':
    sys.exit(main())
