#!/usr/bin/env python3
"""Make the SWAT's sheets from his drawing.

Usage: tools/make_swat.py

docs/templates/swat/walk_source.png is his hand-drawn walk; it is the walk
sheet as is. The jump is made of its whole frames, raised, lowered and with
the legs folded on the cowgirl's timing. The shoot frames are frame 0 without
its arm, with arms (shoulder-elbow-hand) holding a gun drawn here, plus the
muzzle flash. Everything follows the cowgirl's template (docs/CHARACTERS.md):
same frames, pivots, ground rows and muzzle.

Writes assets/sprites/characters/swat/walk.png, jump.png, shoot.png (rifle),
shoot_shotgun.png, and the magazine reloads reload.png (rifle) and
reload_shotgun.png, and his grenade throw (level 3) throw.png. Uses only the
standard library.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs/templates/swat/walk_source.png'
OUT_DIR = ROOT / 'assets/sprites/characters/swat'

INK = rgb(0x140e0e)  # Outline
SLEEVE = [rgb(0x2e2426), rgb(0x3e3233), rgb(0x4d3e3b), rgb(0x594845)]
SLEEVE_FAR = [rgb(0x211919), rgb(0x2e2426), rgb(0x392c2b), rgb(0x3e3233)]
PAD = [rgb(0x494649), rgb(0x615e5e), rgb(0x7f7b78)]
PATCH = [rgb(0x795f4f), rgb(0xb98f71)]
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
    reach = min(d, l1 + l2 - 0.05)
    a = (l1 * l1 - l2 * l2 + reach * reach) / (2 * reach)
    k = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / d, dy / d
    return (start[0] + a * ux - bend * k * uy, start[1] + a * uy + bend * k * ux)


LIGHT = (0.55, -0.83)  # From the front and above, like the drawing's highlights


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


def arm(shoulder: tuple, hand: tuple, near: bool, upper: float = 7.0, fore: float = 7.0) -> Layer:
    """Sleeve and bare hand; the near arm also has the shoulder pad and patch."""
    lay = Layer()
    elbow = ik(shoulder, hand, upper, fore, 1)
    ramp = SLEEVE if near else SLEEVE_FAR
    tube(lay, shoulder, elbow, 2.3, ramp)
    tube(lay, elbow, hand, 2.0, ramp)
    hx, hy = round(hand[0]), round(hand[1])
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (-1, 1)):
        lay.put(hx + dx, hy + dy, SKIN[1] if dy == 0 and dx >= 0 else SKIN[0])
    if near:
        block(lay, round(shoulder[0]), round(shoulder[1]) - 1, 5, 3, PAD)
        square(lay, round(shoulder[0] + (elbow[0] - shoulder[0]) * 0.55),
               round(shoulder[1] + (elbow[1] - shoulder[1]) * 0.55), 2, 2, PATCH[1], PATCH[0])
    return lay.outlined()


def hand(at: tuple) -> Layer:
    """The far hand alone, on the handguard in front of the gun."""
    lay = Layer()
    square(lay, round(at[0]), round(at[1]), 2, 2, SKIN[1], SKIN[0])
    return lay.outlined()


# --- His body -----------------------------------------------------------------

# Joints on the walk frame (frame 0 of the drawing), for the arms that hold the gun.
NEAR_SHOULDER = (16.5, 27.5)
FAR_SHOULDER = (26.5, 27.5)
PANTS_FILL = rgb(0x2e2426)  # Thigh under the hand that is taken away
BACK = [rgb(0x271e1f), rgb(0x323226)]  # Back of the vest, under the sleeve


# --- Face and visor detail ------------------------------------------------------

HELMET_EDGE = rgb(0x271e1f)
LENS = [rgb(0x3b4352), rgb(0x50596a), rgb(0x7d8794), rgb(0xb7bec8), rgb(0xeef3f8)]
FACE_ROWS = range(14, 27)  # Below the helmet, above the shoulders (skin lower down is the hands)


def detail_head(source: Image) -> None:
    """On every frame: the visor's lens shaded top to bottom with one glint at
    the same spot of the lens (the drawing's glint moves from frame to frame),
    and the face with the cheek in shadow at the back and the jaw shaded."""
    glass = {c[:3] for c in LENS[1:4]}
    skin_keys = {c[:3] for c in SKIN}
    for i in range(source.width // WALK_W):
        ox = i * WALK_W

        def pixels(rows, keys):
            return {(x, y) for y in rows for x in range(ox, ox + WALK_W)
                    if source.get(x, y)[3] and source.get(x, y)[:3] in keys}

        drawn = pixels(range(20), glass)
        lens = largest_patch(drawn)
        for x, y in drawn - lens:  # Blue strips off the lens, past the helmet's edge
            source.set(x, y, HELMET_EDGE)
        if lens:
            x0 = min(x for x, _ in lens)
            y0, y1 = min(y for _, y in lens), max(y for _, y in lens)
            for x, y in lens:
                c = LENS[2] if y == y0 else LENS[0] if y == y1 or x == x0 else LENS[1]
                source.set(x, y, c)
            for (x, y), c in (((x0 + 4, y0), LENS[4]), ((x0 + 3, y0 + 1), LENS[3]),
                              ((x0 + 4, y0 + 1), LENS[3]), ((x0 + 2, y0 + 2), LENS[2])):
                if (x, y) in lens:
                    source.set(x, y, c)
        face = pixels(FACE_ROWS, skin_keys)
        if not face:
            continue
        bottom = max(y for _, y in face)
        for x, y in face:
            row = [fx for fx, fy in face if fy == y]
            if x == min(row) or (y == bottom and x < max(row)):
                source.set(x, y, SKIN[0])


def largest_patch(points: set) -> set:
    """The biggest group of touching points: the lens, without stray pixels."""
    best: set = set()
    left = set(points)
    while left:
        todo = [left.pop()]
        patch = set(todo)
        while todo:
            x, y = todo.pop()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in left:
                    left.remove(n)
                    patch.add(n)
                    todo.append(n)
        if len(patch) > len(best):
            best = patch
    return best


def frame(source: Image, i: int) -> Image:
    return crop(source, i * WALK_W, 0, (i + 1) * WALK_W, WALK_H)


def without_arm(f0: Image) -> Image:
    """Frame 0 of the drawing without its near arm: the shoot frames draw the
    arms holding the gun."""
    body = Image(WALK_W, WALK_H)
    for y in range(WALK_H):
        for x in range(WALK_W):
            c = f0.get(x, y)
            if not c[3]:
                continue
            if 24 <= y <= 37 and x <= 17:   # Sleeve, in front of the torso
                continue
            if 38 <= y <= 41 and x <= 12:   # Hand reaching past the thigh
                continue
            if 38 <= y <= 41 and c[:3] in (SKIN[0][:3], SKIN[1][:3]):
                c = PANTS_FILL
            body.set(x, y, c)
    # The sleeve hid the back: fill it in, sloping from the shoulder to the hip.
    for y in range(26, 38):
        back = round(14 - (y - 26) / 11)
        for x in range(back, 18):
            if not body.get(x, y)[3]:
                body.set(x, y, BACK[0] if x == back else BACK[1])
    # Close the cut with outline.
    for y in range(24, 42):
        for x in range(1, WALK_W):
            if body.get(x, y)[3] and not body.get(x - 1, y)[3]:
                body.set(x - 1, y, INK)
    return body


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


def rifle(magazine: bool = True) -> tuple[dict, tuple, tuple]:
    """Short rifle, folded stock, small optic. Pixels (METAL keys), grip and
    handguard, in gun coordinates (x along the barrel); without the magazine
    while it is being changed."""
    t: dict = {}
    rect(t, 0, 2, 4, 3, '1')          # Folded stock
    rect(t, 0, 4, 1, 5, '1')
    rect(t, 5, 1, 16, 5, '2')         # Receiver
    rect(t, 5, 1, 16, 1, '3')
    rect(t, 5, 5, 16, 5, '1')
    rect(t, 8, -1, 13, 0, '1')        # Optic
    t[(12, -1)] = '4'
    t[(13, -1)] = '5'
    rect(t, 7, 6, 8, 7, '1')          # Grip
    t[(6, 8)] = t[(7, 8)] = '1'
    if magazine:
        rect(t, 11, 6, 13, 8, '2')    # Magazine
        rect(t, 12, 9, 14, 9, '2')
        t[(11, 6)] = '3'
    rect(t, 17, 2, 23, 4, '1')        # Handguard
    rect(t, 17, 2, 23, 2, '2')
    rect(t, 24, 3, 28, 3, '2')        # Barrel
    rect(t, 26, 2, 27, 4, '1')        # Muzzle brake
    for x in (7, 8, 9):               # Highlight stroke
        t[(x, 1)] = '4'
    t[(10, 1)] = '5'
    return t, (7.5, 6.5), (20.0, 4.5)


def shotgun(pump_back: int = 0) -> tuple[dict, tuple, tuple]:
    """Pump shotgun: full stock, long barrel over the tube, ribbed pump
    (pump_back px toward the stock while it is racked)."""
    t: dict = {}
    rect(t, -3, 3, 4, 5, 'b')         # Stock
    rect(t, -3, 2, 1, 2, '1')
    rect(t, -4, 3, -4, 6, '1')
    rect(t, -3, 6, 0, 6, 'b')
    rect(t, 5, 2, 12, 5, '2')         # Receiver
    rect(t, 5, 2, 12, 2, '3')
    rect(t, 5, 5, 12, 5, '1')
    rect(t, 5, 6, 6, 7, 'b')          # Grip
    t[(4, 8)] = t[(5, 8)] = 'b'
    rect(t, 13, 2, 28, 3, '2')        # Barrel
    rect(t, 13, 2, 28, 2, '3')
    rect(t, 13, 4, 24, 4, '1')        # Magazine tube
    rect(t, 15 - pump_back, 4, 21 - pump_back, 5, 'b')  # Pump
    for x in (16, 18, 20):
        t[(x - pump_back, 5)] = '1'
    t[(27, 1)] = '4'                  # Bead sight
    for x in (7, 8, 9):
        t[(x, 2)] = '4'
    t[(16, 2)] = t[(17, 2)] = '5'
    return t, (5.5, 6.5), (18.0 - pump_back, 5.0)


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


def make_shoot(body: Image, gun_def, flash: list[str], kick: int) -> Image:
    gun, grip, guard = gun_def
    # Aimed (frames 3 and 4): the muzzle on its mark. The other frames turn
    # the gun about the grip: raised from low ready, recoil, lowered.
    aimed = (MUZZLE[0] - (MUZZLE_LOCAL[0] - grip[0]), MUZZLE[1] - (MUZZLE_LOCAL[1] - grip[1]))
    poses = [  # Angle, grip offset
        (-50, (-3, 5)),                       # 0 Low ready
        (-32, (-2, 3)),                       # 1 Raising
        (-12, (-1, 1)),                       # 2
        (0, (0, 0)),                          # 3 Aim
        (0, (0, 0)),                          # 4 Fire
        (14 + 4 * (kick - 2), (-kick, -1)),   # 5 Recoil
        (6, (-1, 0)),                         # 6 Settling, held while reloading
        (-30, (-2, 3)),                       # 7 Lowering
    ]
    sx, sy = SHOOT_SHIFT
    sheet = Image(SHOOT_W * FRAMES, SHOOT_H)

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
        parts = [
            arm(at(FAR_SHOULDER), far_hand, near=False, upper=7.5, fore=8.0),
            (body, sx, sy),
            layer,
            hand(far_hand),
            arm(at(NEAR_SHOULDER), near_hand, near=True, upper=7.5, fore=8.0),
        ]
        if i == 4:
            parts.append(flash_layer(flash))
        paste(sheet, compose(SHOOT_W, SHOOT_H, parts), i * SHOOT_W, 0)
    return sheet


# --- Reload ---------------------------------------------------------------------

# Where the near hand fetches a new magazine or shells: the vest's pouches, on
# the walk frame.
POUCH_AT = (22.0, 38.0)


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


def make_reload(body: Image, kind: str) -> Image:
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
        well = (12.0, 7.0)    # Magazine well, gun coordinates
        handle = (6.0, 1.0)   # Charging handle
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
        port = (11.0, 6.0)    # Loading port, under the receiver
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
            arm(at(FAR_SHOULDER), far_hand, near=False, upper=7.5, fore=8.0),
            (body, sx, sy),
            layer,
            hand(far_hand),
            arm(at(NEAR_SHOULDER), near_hand, near=True, upper=7.5, fore=8.0),
        ]
        # In front of the hand, or the fist hides it.
        if held == 'mag':
            parts.append(magazine_layer(near_hand))
        elif held == 'shell':
            parts.append(shell_layer(near_hand))
        paste(sheet, compose(SHOOT_W, SHOOT_H, parts), i * SHOOT_W, 0)
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
        ((22, 35), (27, 35), True, False),
        ((22, 35), (32, 30), True, True),
        ((10, 25), (31, 31), True, True),
        ((11, 17), (31, 32), True, False),
        ((29, 20), (30, 34), False, False),
        ((30, 32), (29, 37), False, False),
        ((25, 39), (28, 39), False, False),
        ((21, 41), (27, 40), False, False),
    ]
    sheet = Image(SHOOT_W * FRAMES, SHOOT_H)
    for i, (near, far, holding, ring) in enumerate(poses):
        near_hand, far_hand = at(near), at(far)
        parts = [
            arm(at(FAR_SHOULDER), far_hand, near=False, upper=7.5, fore=8.0),
            (body, sx, sy),
            arm(at(NEAR_SHOULDER), near_hand, near=True, upper=7.5, fore=8.0),
        ]
        if holding:
            parts.append(grenade_layer(near_hand))
        if ring:
            parts.append(ring_layer(far_hand))
        if i == 4:                                   # Just let go, ahead of the hand
            parts.append(grenade_layer((near_hand[0] + 4, near_hand[1] - 3)))
        paste(sheet, compose(SHOOT_W, SHOOT_H, parts), i * SHOOT_W, 0)
    return sheet


def main() -> int:
    source = load(SOURCE)
    detail_head(source)
    body = without_arm(frame(source, 0))
    sheets = {
        'walk': source,
        'jump': make_jump(source),
        'shoot': make_shoot(body, rifle(), RIFLE_FLASH, kick=2),
        'shoot_shotgun': make_shoot(body, shotgun(), SHOTGUN_FLASH, kick=3),
        'reload': make_reload(body, 'rifle'),
        'reload_shotgun': make_reload(body, 'shotgun'),
        'throw': make_throw(body),
    }
    for name, sheet in sheets.items():
        sheet.save(OUT_DIR / f'{name}.png')
        print(f'make_swat: {name} ({sheet.width} x {sheet.height})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
