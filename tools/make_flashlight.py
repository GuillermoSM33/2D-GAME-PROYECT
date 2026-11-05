#!/usr/bin/env python3
"""Make the cowgirl's flashlight: its own little sprite and clipping it on.

Usage: tools/make_flashlight.py

Writes in assets/sprites/characters/cowgirl/ (81 x 80 frames, the shoot template):
  light.png, light_dual.png  16 frames: her far hand fetches the flashlight from
      her belt and clips it under the barrel, and it lights
      (with the duals she first puts one pistol in her belt, and takes it back
      after); the last is held while it stays on. Played backwards to take it off.
  shoot_dual.png, shoot_dual_b.png  16 frames each, the shoot template: the two
      guns taking turns: the near one fires from her shoulder and kicks up, held high,
      as the far one swings up from beside her leg and fires from her hip.
  shoot_dual_lit.png, shoot_dual_b_lit.png  The same turns with the flashlight on: its
      gun stays up, lit, and the other swings up and fires from her hip.
  shoot.png  Her draw and holster frames redrawn with her own arm turned.
  melee.png  7 frames: the blow with the gun (poses in make_melee), her other hand on her hip.
  melee_dual.png  7 frames: the blow with her near gun, as on melee.png; her far arm
      apart from it, its pistol down by her own leg, pulling back against the swing.
  melee_lit.png, melee_dual_lit.png  The same blows with the flashlight on the gun,
      ending on the held pose. Its lens is printed: player_light_kick follows it.
  ricochet.png, ricochet_dual.png, and _lit  8 frames: both hands together, firing two bullets.
  swap.png, swap_lit.png  12 frames: her far hand takes the second pistol from
      the holster, down clear of her leg as at the duals' rest, and puts it back (lit:
      the flashlight shining on the first gun). Played backwards to put it away.
  flashlight.png  8 frames, only the flashlight: drawn over shoot.png or
      shoot_dual.png, following the gun, while it is on.
And for both characters, each gun, after tools/make_swat.py:
  light_walk*.png  12 frames: walking with it up, the gun held level (the last
      frame of its light sheet) on the legs of walk.png, moving as one piece with
      each step; then 4 stood still, breathing.

The SWAT's light is on his guns (tools/make_swat.py). Standard library only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cowgirl_arm import arm_limb as bent_arm, glove, pistol_muzzle, pistol_pointing, turned  # noqa: E402
from make_melee import AIM, HOLSTER, LOW, POSES, SHOULDER, body_without_arm, frame, no_holes, sleeve, striking_arm  # noqa: E402
from make_powers import FAR_ARM_INSIDE, INK, SKIN, load  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402
from rework_cowgirl import FAR_HOLSTER, draw_arm, dressed_sheet, holster as belt_holster, walk_arms  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets/sprites/characters/cowgirl'
W, H = 81, 80
BODY = [rgb(0x2a2a30), rgb(0x4a4a54), rgb(0x74747e)]
BRASS = rgb(0xd0a848)
LENS_OFF, LENS_ON = rgb(0x9aa0a8), rgb(0xfff6dc)
LENGTH = 6
CLAMP_AT = (1, 2)                 # Along it, and rows above it, of the clamp holding it to the barrel
CLAMP_ROWS = (-2, -3)
AIM_LENS_TAIL = (58.0, 40.3)      # Its tail, clipped under the barrel on the aim; lens at x 64, y 41 (light_rows in weapons.c)


def flashlight(tail: tuple, angle: float, lit: bool) -> dict:
    """A short metal torch from tail along angle (radians, y down), a brass band,
    the lens at its end, outlined."""
    ux, uy = math.cos(angle), math.sin(angle)
    vx, vy = -uy, ux
    out = {}
    for a in range(LENGTH + 1):
        for b in range(3):
            x = round(tail[0] + ux * a + vx * b)
            y = round(tail[1] + uy * a + vy * b)
            if a == LENGTH:
                c = LENS_ON if lit else LENS_OFF
            elif a == LENGTH - 2:
                c = BRASS
            else:
                c = BODY[2 - b]
            out[(x, y)] = c
    edged = dict(out)
    for (x, y) in out:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in out:
                edged[(x + dx, y + dy)] = INK
    for a in CLAMP_AT:                                   # Its clamp, up to the barrel
        for b in CLAMP_ROWS:
            edged[(round(tail[0] + ux * a + vx * b), round(tail[1] + uy * a + vy * b))] = BRASS if b == CLAMP_ROWS[-1] else BODY[0]
    return edged


def put(img: Image, f: int, px: dict) -> None:
    for (x, y), c in no_holes(px).items():
        if 0 <= x < W and 0 <= y < H:
            img.set(f * W + x, y, c)


RISING = 2                        # Shoot frame: the gun coming up
FRAMES = 16                       # PLAYER_LIGHT_FRAMES: the first and last are her own art
BEHIND_FROM = 35                  # Far hand this far forward: the arm passes behind her
FAR_ARM = (7.5, 7.5)              # Its lengths, shoulder to elbow to hand: it never stretches
HIP = (30, 46)                    # Where her far hand rests, when she has it on her hip
SHOOT_BUCKLE, SHOOT_BELT = 34, 49 # Her buckle's middle column and row, on the shoot template
FAR_TOP = (25, 37)                # Her far shoulder, on it
AT_HOLSTER = (26, 48)             # Her far hand on the holster's butt
GUN_DOWN = (17, 49)               # ...and with the pistol out, down clear of her leg, as on the duals' rest


def two_bones(top: tuple, at: tuple, lengths: tuple) -> tuple[tuple, tuple]:
    """Where the elbow goes, the hand held to what the arm can reach, the elbow
    on the side below the line. Returns the elbow and the hand."""
    upper, fore = lengths
    dx, dy = at[0] - top[0], at[1] - top[1]
    d = max(math.hypot(dx, dy), 1.0)
    reach = upper + fore - 0.5
    if d > reach:
        at = (top[0] + dx * reach / d, top[1] + dy * reach / d)
        dx, dy, d = at[0] - top[0], at[1] - top[1], reach
    along = (upper * upper - fore * fore + d * d) / (2.0 * d)
    out = math.sqrt(max(0.0, upper * upper - along * along))
    ux, uy = dx / d, dy / d
    side = -1.0 if uy > abs(ux) or ux >= 0 else 1.0      # Hanging down, the elbow out from her body
    elbow = (top[0] + ux * along + uy * out * side, top[1] + uy * along + abs(ux) * out)
    return (round(elbow[0]), round(elbow[1])), (round(at[0]), round(at[1]))


GUN_HAND = (11.5, 3.0)            # Her gun hand on the aim, from her shoulder: the muzzle comes to where the bullet starts
GUN_LIGHT = (7.5, 1.3)            # Where the flashlight's tail sits on a gun, from the hand
NEAR_FLASH = 2                    # Columns her near muzzle's flash is past the base art's


def held_gun(bend: tuple) -> tuple[dict, tuple, float]:
    """Her gun arm: the same arm, glove and pistol as her other, the arm turned about the
    shoulder and the gun about the hand (degrees, + raises them). Returns its pixels and where
    the flashlight sits on the gun."""
    upper_angle, fore_angle = bend
    rx, ry = turned(GUN_HAND, upper_angle)
    hand = (round(SHOULDER[0] + rx), round(SHOULDER[1] + ry))
    px = sleeve(SHOULDER, hand)
    px.update(pistol_pointing(hand, fore_angle))
    px.update(glove(hand, SHOULDER))
    lx, ly = turned(GUN_LIGHT, fore_angle)
    return px, (hand[0] + lx, hand[1] + ly), -math.radians(fore_angle)


def blend(keys: list, k: float) -> tuple:
    """A key pose at k (0..1 along the keys): positions eased between its two
    neighbours; what she holds is the earlier key's."""
    n = len(keys) - 1
    i = min(int(k * n), n - 1)
    t = k * n - i
    t = t * t * (3.0 - 2.0 * t)                          # Ease in and out: no jerks
    (h0, a0, f0, *state), (h1, a1, f1, *_) = keys[i], keys[i + 1]
    hand_from = (h0[0] + (h1[0] - h0[0]) * t, h0[1] + (h1[1] - h0[1]) * t)
    return (hand_from, a0 + (a1 - a0) * t, (f0[0] + (f1[0] - f0[0]) * t, f0[1] + (f1[1] - f0[1]) * t), *state)


# Her gun arm through a shot: drawn up, fired, kicked and put away, the same arm as
# in all her other poses.
DRAWN = {0: (-58, -66), 1: (-42, -46), 2: (-16, -14), AIM: (0, 0), AIM + 1: (0, 0), 5: (0, 14), 6: (-4, 4),
         HOLSTER: (-28, -26)}
FLASH_FROM_X = 64                 # Column of the base art's muzzle flash, on the fire frame
NEAR_MUZZLE_ROW = 32              # ...and the row of its middle


def arm_frame(shoot: Image, f: int) -> dict:
    """Shoot frame f: her body and arm in its pose, and on the fire frame, its flash."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    body = body_without_arm(aim, low, rest)
    px = dict(body)
    px.update(held_gun(DRAWN[f])[0])
    if f == AIM + 1:
        px.update(muzzle_flash(shoot, NEAR_FLASH, 0))
    return px


def muzzle_flash(shoot: Image, ox: float, oy: float) -> dict:
    """The base art's flash, moved with the muzzle, clear of the frame's edge."""
    moved = {(round(x + ox), round(y + oy)): c for (x, y), c in frame(shoot, AIM + 1).items() if x >= FLASH_FROM_X}
    return {p: c for p, c in moved.items() if p[0] < W - 1}


def make_shoot(shoot: Image) -> Image:
    img = Image(W * 8, H)
    for f in range(8):
        put(img, f, arm_frame(shoot, f))
    return img


def posed(shoot: Image, key: tuple) -> dict:
    """One frame: her, the gun in its pose, her far hand where the key says."""
    bend, _, far, on_hip, held, clipped, holstered = key
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    body = body_without_arm(aim, low, rest)
    gun, tail, turned = held_gun(bend)
    if on_hip:
        px = dict(body)
        px.update(gun)
    else:
        free, shoulder = body_without_arm(aim, low, rest, False), FAR_TOP
        behind = far[0] >= BEHIND_FROM                   # Reaching forward: past her, not across her
        top = (shoulder[0] + FAR_ARM_INSIDE[0], shoulder[1] + FAR_ARM_INSIDE[1]) if behind else shoulder
        elbow, at = two_bones(top, far, FAR_ARM)
        limb = bent_arm(top, elbow, at)
        px = dict(limb) if behind else {}
        px.update(free)
        px.update(gun)
        if holstered:
            px.update(holster())
        if not behind:
            px.update(limb)
    if clipped:
        px.update(flashlight(tail, turned, clipped == 'lit'))
    if not on_hip:
        if held == 'light':
            px.update(flashlight((at[0] + 1.0, at[1] - 1.0), -0.6, False))
        elif held == 'pistol':                           # Down outside her leg, never across her
            px.update(pistol_pointing(at, FAR_REST[2]))
        px.update(glove(at, elbow))
    return px


# Her gun arm: how far the sleeve and the glove with the gun are turned (degrees).
READY = ((-30, -22), 0)
HALF = ((-44, -6), 0)
CLOSE = ((-52, 4), 0)             # Her elbow in, the gun low before her, where her other hand gets to it
LEVEL = ((-8, 6), 0)              # Nearly back on the aim


def make_light(shoot: Image) -> Image:
    """She brings the gun in to her chest, her far hand fetches the flashlight
    from the belt and clips it on; the hand goes back and the gun comes up, lit.
    The keys are in-betweened, so it flows."""
    keys = [((-14, -12), 0, HIP, True, None, False, False),   # Gun coming in
            (*READY, HIP, True, None, False, False),
            (*READY, (31, 47), False, None, False, False),  # Hand to the belt
            (*READY, (31, 47), False, 'light', False, False),
            (*HALF, (34, 47), False, 'light', False, False),  # Coming up
            (*CLOSE, (37, 46), False, 'light', False, False),
            (*CLOSE, (39, 46), False, None, True, False),   # Clipped: click
            (*CLOSE, (36, 47), False, None, True, False),   # The hand comes away
            (*HALF, (32, 46), False, None, True, False),
            (*LEVEL, HIP, True, None, True, False)]         # Back on her hip, gun rising
    img = Image(W * FRAMES, H)
    put(img, 0, arm_frame(shoot, RISING))
    for f in range(1, FRAMES - 1):
        put(img, f, posed(shoot, blend(keys, (f - 1) / (FRAMES - 3))))
    px = arm_frame(shoot, AIM)
    px.update(flashlight(*drawn_lens(shoot, AIM), True))
    put(img, FRAMES - 1, px)
    return img


def holster() -> dict:
    """It in the belt: the small holster on her far hip, the same as walking."""
    px = belt_holster(SHOOT_BUCKLE - FAR_HOLSTER, SHOOT_BELT)
    edged = dict(px)
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in px:
                edged[(x + dx, y + dy)] = INK
    return edged


# The two guns take turns: the near one fires from her shoulder and kicks on up, held high,
# as the far one swings up from beside her leg and fires from her hip: no arm across her
# neckline, the guns never on each other. Each arm swings all along two turns: the frames of
# both, in one count from the first of the near gun's. Near arm: how far the sleeve and the
# glove with the gun are turned (degrees, + raises them).
DUAL_FRAMES = 16                  # PLAYER_PISTON_FRAMES, each turn
DUAL_FIRE = 8                     # Twice PLAYER_SHOOT_FIRE_FRAME
DUAL_AIM = 7                      # Her near gun on the aim, the far at rest
DUAL_ENDS = 14                    # ...and coming off it
NEAR_SWING = ((0, (2, 34)), (4, (-3, 10)), (7, (0, 0)), (9, (0, 0)), (11, (0, 14)), (14, (-2, 8)), (16, (2, 20)),
              (20, (10, 44)), (24, (14, 52)), (28, (14, 52)))
# With the flashlight up, its gun stays on the aim and only kicks (player_light_kick).
NEAR_LIT = ((0, (0, 0)), (9, (0, 0)), (10, (0, 14)), (11, (0, 14)), (12, (-4, 4)), (13, (-4, 4)), (15, (-1, 0)), (17, (0, 0)))
# Far arm, from her own shoulder: where the hand is and the gun's angle. Down clear of her leg
# at rest, angled away from it: along it, it is a third leg. PLAYER_FAR_GUN_ROWS.
FAR_REST = (17, 49, -150)
FAR_SWING = ((0, (25, 49, -105)), (3, (20, 49, -135)), (6, FAR_REST), (16, FAR_REST), (19, (21, 49, -125)), (21, (27, 49, -50)),
             (22, (29, 49, -15)), (24, (31, 49, 0)), (25, (31, 49, 0)), (26, (31, 47, 12)), (28, (31, 49, -2)), (30, (29, 49, -40)), (31, (27, 49, -80)))
ARM_LENGTHS = FAR_ARM             # Her far arm, shoulder to elbow to hand: always these
ALL_TURNS = 2 * DUAL_FRAMES


def along(keys: tuple, f: int) -> tuple:
    """A swing's values at frame f of the two turns, straight between its keys, round to the first."""
    for (f0, v0), (f1, v1) in zip(keys, keys[1:] + ((keys[0][0] + ALL_TURNS, keys[0][1]),)):
        if f0 <= f <= f1:
            k = (f - f0) / (f1 - f0)
            return tuple(a + (b - a) * k for a, b in zip(v0, v1))
    return keys[-1][1]


def make_dual(shoot: Image, far_fires: bool, lit: bool = False) -> Image:
    """One turn: one gun firing, the other on its way. The near arm and gun are her real ones
    off the aim frame, turned; the far arm comes from her far shoulder, in front of her, with
    its pistol drawn the same all the way round. Lit: the near gun stays up with the flashlight."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    body = body_without_arm(aim, low, rest)
    free, shoulder = body_without_arm(aim, low, rest, False), FAR_TOP
    img = Image(W * DUAL_FRAMES, H)
    start = DUAL_FRAMES if far_fires else 0
    for f in range(DUAL_FRAMES):
        count = f + start
        near, tail, turned = held_gun(along(NEAR_LIT if lit else NEAR_SWING, count))
        px = dict(free)
        top = shoulder                                   # It turns about her shoulder: that never slides
        hx, hy, angle = along(FAR_SWING, count)
        elbow, at = two_bones(top, (hx, hy), ARM_LENGTHS)
        px.update(bent_arm(top, elbow, at))
        px.update(pistol_pointing(at, angle))
        px.update(glove(at, elbow))
        px.update(near)
        if lit:
            px.update(flashlight(tail, turned, True))
        if f in (DUAL_FIRE, DUAL_FIRE + 1):
            tip = pistol_muzzle(at, angle)
            ox, oy = (round(tip[0]) + 1 - FLASH_FROM_X, round(tip[1]) - NEAR_MUZZLE_ROW) if far_fires else (NEAR_FLASH, 0)
            px.update(muzzle_flash(shoot, ox, oy))
            if far_fires and f == DUAL_FIRE:
                print(f'make_flashlight: {"lit " if lit else ""}far gun, fire frame: {NEAR_FLASH - ox:+.0f} back, {oy:+.0f} down')
        put(img, f, px)
    return img


# The ricochet, the shoot template's frames: both hands come together before her and she fires
# two bullets. Per frame: her near hand, her far hand, how far both guns are raised. Her near elbow
# goes out, her far arm comes across under her chest. PLAYER_POWER_* holds the muzzles.
NEAR_TOP = (42, 37)
POWER_BONE = 6.5
POWER_DUAL = (((47, 47), (19, 49), -40), ((44, 47), (27, 48), -20), ((42, 47), (35, 45), -6), ((41, 48), (38, 44), 0),
              ((41, 48), (38, 44), 0), ((41, 47), (38, 43), 10), ((41, 48), (38, 44), 4), ((43, 47), (31, 46), -12))
POWER_ONE = (((47, 47), (27, 47), -40), ((44, 47), (32, 47), -20), ((42, 47), (36, 47), -6), ((41, 48), (38, 49), 0),
             ((41, 48), (38, 49), 0), ((41, 47), (38, 48), 10), ((41, 48), (38, 49), 4), ((43, 47), (34, 47), -12))
POWER_LIGHT = (7.5, -1.7)         # The flashlight on her ricochet, snug under the barrel: she holds it close, in sight


def near_bent(hand: tuple) -> tuple:
    """Her near arm's elbow, out to her front, the hand drawn in close."""
    dx, dy = hand[0] - NEAR_TOP[0], hand[1] - NEAR_TOP[1]
    d = max(math.hypot(dx, dy), 1.0)
    out = math.sqrt(max(0.0, POWER_BONE * POWER_BONE - d * d / 4.0))
    px, py = -dy / d, dx / d
    if px < 0:
        px, py = -px, -py
    return NEAR_TOP[0] + dx / 2 + px * out, NEAR_TOP[1] + dy / 2 + py * out


def make_power(shoot: Image, both_guns: bool, lit: bool) -> Image:
    """The ricochet shot: one gun in both hands, or the two side by side."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    free = body_without_arm(aim, low, rest, False)
    img = Image(W * 8, H)
    for f, (near_hand, far_hand, raised) in enumerate(POWER_DUAL if both_guns else POWER_ONE):
        px = dict(free)
        elbow, at = two_bones(FAR_TOP, far_hand, FAR_ARM)
        px.update(bent_arm(FAR_TOP, elbow, at))
        if both_guns:
            px.update(pistol_pointing(at, raised))
        px.update(glove(at, elbow))
        px.update(bent_arm(NEAR_TOP, near_bent(near_hand), near_hand))
        px.update(pistol_pointing(near_hand, raised))
        px.update(glove(near_hand, near_bent(near_hand)))
        if lit:
            lx, ly = turned(POWER_LIGHT, raised)
            tail = (near_hand[0] + lx, near_hand[1] + ly)
            px.update(flashlight(tail, -math.radians(raised), True))
            lens = (tail[0] + LENGTH * math.cos(-math.radians(raised)), tail[1] + LENGTH * math.sin(-math.radians(raised)))
            print(f'make_flashlight: {"dual " if both_guns else ""}ricochet {f}: lens {lens[0] - 64:+.1f}, {lens[1] - AIM_LENS_TAIL[1]:+.1f}')
        if f == AIM + 1:
            muzzles = [pistol_muzzle(near_hand, raised)]
            if both_guns:
                muzzles.append(pistol_muzzle(at, raised))
            for tip in muzzles:
                px.update(muzzle_flash(shoot, round(tip[0]) + 1 - FLASH_FROM_X, round(tip[1]) - NEAR_MUZZLE_ROW))
                print(f'make_flashlight: {"dual " if both_guns else ""}ricochet muzzle: {NEAR_FLASH - (round(tip[0]) + 1 - FLASH_FROM_X):+d} back, {round(tip[1]) - NEAR_MUZZLE_ROW:+d} down')
        put(img, f, px)
    return img


# Her far hand and pistol through the blow (make_melee.POSES): back on the wind-up,
# and down again as the other swings.
FAR_IN_BLOW = (((19, 49), -145), ((18, 48), -142), ((18, 49), -146), ((17, 49), -150), ((17, 49), -150), ((18, 49), -148))


def on_the_blow(pose: tuple) -> tuple:
    """Where the flashlight is on the gun in a blow's pose: its tail and angle."""
    (hx, hy), angle, _ = pose
    lx, ly = turned(GUN_LIGHT, angle)
    return (SHOULDER[0] + hx + lx, SHOULDER[1] + hy + ly), -math.radians(angle)


def make_blow(shoot: Image, last: dict, both_guns: bool, lit: bool) -> Image:
    """The blow with her near gun: her other hand on her hip, or its pistol down by
    her leg; the flashlight on the gun, lit; last is the frame she ends on."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    body = body_without_arm(aim, low, rest)
    if both_guns:
        free, shoulder = body_without_arm(aim, low, rest, False), FAR_TOP
    img = Image(W * len(POSES), H)
    for f, pose in enumerate(POSES):
        if pose is None:
            put(img, f, last)
            continue
        px = dict(body)
        if both_guns:
            px = dict(free)
            want, angle = FAR_IN_BLOW[f]
            elbow, at = two_bones(shoulder, want, ARM_LENGTHS)
            px.update(bent_arm(shoulder, elbow, at))
            px.update(pistol_pointing(at, angle))
            px.update(glove(at, elbow))
        striking_arm(px, f)
        if lit:
            px.update(flashlight(*on_the_blow(pose), True))
        put(img, f, px)
    return img


def far_part(shoot: Image, key: tuple) -> dict:
    """Only her far arm, hand and pistol, of a pose that has the pistol in that hand."""
    _, _, far, on_hip, held, _, _ = key
    if on_hip or held != 'pistol':
        return {}
    elbow, at = two_bones(FAR_TOP, far, FAR_ARM)
    px = bent_arm(FAR_TOP, elbow, at)
    px.update(pistol_pointing(at, FAR_REST[2]))
    px.update(glove(at, elbow))
    return px


def make_light_dual(shoot: Image, dual: Image, far_only: bool = False) -> Image:
    """With both hands full: she slides one pistol into the belt; her free hand
    takes the flashlight and clips it on the other, by her chest; it goes back
    for the pistol and both come up again, lit. In-betweened, like the other."""
    keys = [((-10, -6), 0, GUN_DOWN, False, 'pistol', False, False),  # From down by her leg
            (*READY, (25, 49), False, 'pistol', False, False),   # Bringing it to the belt
            (*READY, AT_HOLSTER, False, None, False, True),      # In it, the hand free
            (*READY, (31, 47), False, 'light', False, True),     # It has the flashlight
            (*HALF, (34, 47), False, 'light', False, True),      # Coming up
            (*CLOSE, (37, 46), False, 'light', False, True),
            (*CLOSE, (39, 46), False, None, True, True),         # Clipped: click
            (*CLOSE, (34, 48), False, None, True, True),
            (*HALF, AT_HOLSTER, False, None, True, True),        # Back to the pistol at her hip
            (*HALF, (25, 49), False, 'pistol', True, False),     # It in hand
            (*LEVEL, GUN_DOWN, False, 'pistol', True, False)]    # One rising, the other down again
    img = Image(W * FRAMES, H)
    if far_only:
        for f in range(1, FRAMES - 1):
            part = far_part(shoot, blend(keys, (f - 1) / (FRAMES - 3)))
            if part:
                put(img, f, part)
        return img
    put(img, 0, frame(dual, DUAL_AIM))
    for f in range(1, FRAMES - 1):
        put(img, f, posed(shoot, blend(keys, (f - 1) / (FRAMES - 3))))
    px = frame(dual, DUAL_AIM)
    px.update(flashlight(*drawn_lens(shoot, AIM), True))
    put(img, FRAMES - 1, px)
    return img


def make_swap(shoot: Image, dual: Image, lit: bool, far_only: bool = False) -> Image:
    """Her far hand off her hip, to the holster at the belt; the second pistol out,
    down clear of her leg as the duals have it; and with no shot to fire, back in the
    holster and her hand on her hip. Lit: with the flashlight on, shining, on the first
    gun all through, which stays up. In-betweened."""
    light = 'lit' if lit else False
    end = (-14, -12) if not lit else (-1, 0)
    keys = [((-14, -12), 0, HIP, True, None, light, False),        # Her gun held as it comes up
            ((-8, -4), 0, AT_HOLSTER, False, None, light, True),   # Hand to the holster
            ((-6, -2), 0, (25, 49), False, 'pistol', light, False),  # It has it
            ((-4, -1), 0, GUN_DOWN, False, 'pistol', light, False),  # Down clear of her leg
            ((-6, -6), 0, (25, 49), False, 'pistol', light, False),  # And back
            ((-8, -8), 0, AT_HOLSTER, False, None, light, True),   # Put away
            (end, 0, HIP, True, None, light, False)]
    img = Image(W * 12, H)
    if far_only:
        for f in range(1, 11):
            part = far_part(shoot, blend(keys, (f - 1) / 9))
            if part:
                put(img, f, part)
        return img
    first = arm_frame(shoot, RISING)
    if lit:
        first.update(flashlight(*drawn_lens(shoot, RISING), True))
    put(img, 0, first)
    for f in range(1, 11):
        put(img, f, posed(shoot, blend(keys, (f - 1) / 9)))
    last = arm_frame(shoot, AIM if lit else HOLSTER)
    if lit:
        last.update(flashlight(*drawn_lens(shoot, AIM), True))
    put(img, 11, last)
    return img


def drawn_lens(shoot: Image, f: int) -> tuple:
    """Where the flashlight sits on a drawn frame's gun: its tail and angle."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    _, tail, turned = held_gun(DRAWN[f])
    return tail, turned


def make_overlay(shoot: Image) -> Image:
    """The flashlight alone, on each shoot frame: it keeps its place on the gun."""
    img = Image(W * 8, H)
    for f in range(8):
        put(img, f, flashlight(*drawn_lens(shoot, f), True))
    return img


WALK_W, WALK_H = 42, 67
WALK_SHIFT = (12, 7)              # A walk-frame point on the shoot template (player.c)
LEGS_FROM = 47                    # Walk-frame row where its legs start


# Rows the whole upper body is off its mark (+ down), lens included: as
# player_light_sway in player.c. Lowest as a leg passes under her, level as a
# foot lands; on the breath, the chest lifting.
STRIDE = (0, 0, 1, 0, 0, 0, 1, 0)
BREATH = (0, -1, -1, 0)


def arm_free(shoot: Image) -> tuple:
    """Her body with no hand on her hip, and apart from it her gun arm with the flashlight lit."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    body = body_without_arm(aim, low, rest)
    free = body_without_arm(aim, low, rest, False)
    gun = dict(held_gun(DRAWN[AIM])[0])
    gun.update(flashlight(*drawn_lens(shoot, AIM), True))
    return free, gun


def far_gun_at_rest(shoot: Image) -> dict:
    """Her far pistol and hand as the duals' aim frame has them, down by her leg."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    elbow, at = two_bones(FAR_TOP, FAR_REST[:2], ARM_LENGTHS)
    px = pistol_pointing(at, FAR_REST[2])
    px.update(glove(at, elbow))
    return px


BUCKLE = {(0xb8, 0x90, 0x3a), (0xec, 0xc8, 0x68)}
BUCKLE_WIDE = 3
UNDER_BELT = 3                    # Rows from the top of her buckle to where her legs start
CHEST_ENDS = 45                   # Shoot-frame row: above it her chest lifts on the breath


def buckle_at(px: dict) -> tuple:
    """Her buckle: the row it starts on and its middle column. Not her pendant, of the
    same brass: that is never this wide."""
    rows = {}
    for (x, y), c in px.items():
        if c[:3] in BUCKLE:
            rows.setdefault(y, []).append(x)
    top = min(y for y, xs in rows.items() if len(xs) >= BUCKLE_WIDE)
    return top, min(rows[top]) + 1


def make_light_walk(walk: Image, light: Image, front: dict = {}, bare: Image = None, free_arm: tuple = None) -> Image:
    """Each walk frame's legs under the held pose's upper body, then that pose
    breathing on still legs. Torso, arm and gun move as one piece, and only up
    and down: whatever the legs do, the gun stays steady. front is what hangs below
    the waist and stays over the legs: her other pistol. bare is the walk with no
    gun in its holster: then her legs join her at the belt, buckle over buckle, with
    no step at her hips; without it, at the fixed row. free_arm is her body and her gun arm
    apart, when her other arm is free to swing as she walks."""
    held = frame(light, light.width // W - 1)            # The held pose: its last frame
    sx, sy = WALK_SHIFT
    join = LEGS_FROM + sy

    def walk_px(i: int, sheet: Image = walk) -> dict:
        return {(x, y): sheet.get(i * WALK_W + x, y) for y in range(WALK_H) for x in range(WALK_W)
                if sheet.get(i * WALK_W + x, y)[3]}

    def hips(px: dict, row: int, shift: int) -> float:
        xs = [x + shift for (x, y) in px if y == row]
        return sum(xs) / max(1, len(xs))

    def upper(out: dict, dx: int, dy: int, until: int) -> None:
        for (x, y), c in held.items():
            if y < until:
                out[(x + dx, y + dy)] = c

    # One sideways place for all the frames: on the legs' average.
    her_own = {p: c for p, c in held.items() if p not in front}
    # Hers has one column for all of it, as her other sheets.
    dx = 0 if bare else round(sum(hips(walk_px(i), LEGS_FROM, sx) for i in range(8)) / 8 - hips(her_own, join, 0))
    img = Image(W * (8 + len(BREATH)), H)
    for i in range(8):
        if bare:
            top, middle = buckle_at(walk_px(i, bare))
            held_top, held_middle = buckle_at(held)
            until = held_top + UNDER_BELT
            legs = {p: c for p, c in walk_px(i, bare).items() if p[1] >= top + UNDER_BELT}
            at = (held_middle + dx - middle, held_top + STRIDE[i] - top)
        else:
            until = join
            legs = {p: c for p, c in walk_px(i).items() if p[1] >= LEGS_FROM - 3}
            at = (sx, sy)
        for (x, y) in sorted(p for p, c in legs.items() if c[:3] in SKIN):
            # The hand that hung here in the plain walk: its trousers carry on instead.
            cloth = next((legs[(x - d, y)] for d in range(1, 8)
                          if (x - d, y) in legs and legs[(x - d, y)][:3] not in SKIN and legs[(x - d, y)][:3] != INK[:3]), None)
            if cloth:
                legs[(x, y)] = cloth
            else:
                del legs[(x, y)]
        out = {(x + at[0], y + at[1]): c for (x, y), c in legs.items()}
        if free_arm:
            body_free, gun_arm = free_arm
            out.update({(x + dx, y + STRIDE[i]): c for (x, y), c in body_free.items() if y < until})
            draw_arm(out, walk_arms(i)[0], SHOOT_BELT + STRIDE[i], SHOOT_BUCKLE + dx)
            out.update({(x + dx, y + STRIDE[i]): c for (x, y), c in gun_arm.items()})
        else:
            upper(out, dx, STRIDE[i], until)
        out.update({(x + dx, y + STRIDE[i]): c for (x, y), c in front.items()})
        put(img, i, out)
    for i, sway in enumerate(BREATH):                    # Stood still: the chest rising
        if bare:                                         # Her belt stays where it is
            out = dict(held)
            upper(out, 0, sway, CHEST_ENDS)
        else:
            out = {p: c for p, c in held.items() if p[1] >= join - 3}
            upper(out, 0, sway, join)
        put(img, 8 + i, out)
    return img


def main() -> int:
    shoot = load(OUT / 'shoot.png')                      # As dressed: it is rewritten last
    dual = make_dual(shoot, False)
    dual.save(OUT / 'shoot_dual.png')
    make_dual(shoot, True).save(OUT / 'shoot_dual_b.png')
    make_dual(shoot, False, True).save(OUT / 'shoot_dual_lit.png')
    make_dual(shoot, True, True).save(OUT / 'shoot_dual_b_lit.png')
    light, light_dual = make_light(shoot), make_light_dual(shoot, dual)
    held, held_dual = frame(light, FRAMES - 1), frame(light_dual, FRAMES - 1)
    for name, img in (('melee', make_blow(shoot, arm_frame(shoot, HOLSTER), False, False)),
                      ('melee_dual', make_blow(shoot, frame(dual, DUAL_ENDS), True, False)),
                      ('melee_lit', make_blow(shoot, held, False, True)),
                      ('melee_dual_lit', make_blow(shoot, held_dual, True, True)),
                      ('light', light), ('light_dual', light_dual),
                      ('swap', make_swap(shoot, dual, False)), ('swap_lit', make_swap(shoot, dual, True)),
                      ('ricochet', make_power(shoot, False, False)), ('ricochet_lit', make_power(shoot, False, True)),
                      ('ricochet_dual', make_power(shoot, True, False)), ('ricochet_dual_lit', make_power(shoot, True, True)),
                      ('swap_far', make_swap(shoot, dual, False, True)), ('light_dual_far', make_light_dual(shoot, dual, True)),
                      ('flashlight', make_overlay(shoot))):
        img.save(OUT / f'{name}.png')
        print(f'make_flashlight: {name} ({img.width} x {img.height})')
    for f, pose in enumerate(POSES):                     # For player_light_kick
        if pose:
            (x, y), a = on_the_blow(pose)
            print(f'make_flashlight: blow {f}: lens {x + LENGTH * math.cos(a) - AIM_LENS_TAIL[0] - LENGTH:+.1f}, '
                  f'{y + LENGTH * math.sin(a) - AIM_LENS_TAIL[1]:+.1f}')
    swat = OUT.parent / 'swat'
    bare = dressed_sheet('walk', False, no_arms=True)
    for folder, gun in ((OUT, ''), (OUT, '_dual'), (swat, ''), (swat, '_shotgun')):
        front = far_gun_at_rest(shoot) if gun == '_dual' else {}
        free_arm = arm_free(shoot) if folder == OUT and gun == '' else None
        img = make_light_walk(load(folder / 'walk.png'), load(folder / f'light{gun}.png'), front, bare if folder == OUT else None, free_arm)
        img.save(folder / f'light_walk{gun}.png')
        print(f'make_flashlight: {folder.name}/light_walk{gun} ({img.width} x {img.height})')
    make_shoot(shoot).save(OUT / 'shoot.png')            # Last: the others read it as dressed
    return 0


if __name__ == '__main__':
    sys.exit(main())
