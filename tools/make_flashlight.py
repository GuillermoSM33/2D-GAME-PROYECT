#!/usr/bin/env python3
"""Make the cowgirl's flashlight: its own little sprite and clipping it on.

Usage: tools/make_flashlight.py

Writes in assets/sprites/characters/cowgirl/ (81 x 80 frames, the shoot template):
  light.png, light_dual.png  16 frames: her far hand fetches the flashlight from
      her belt and clips it under the barrel, and it lights
      (with the duals she first puts one pistol in her belt, and takes it back
      after); the last is held while it stays on. Played backwards to take it off.
  shoot_dual.png, shoot_dual_b.png  8 frames each, the shoot template: the two
      guns taking turns like a piston, one firing and starting down as the other
      comes up from her thigh.
  shoot_dual_lit.png, shoot_dual_b_lit.png  The same turns with the flashlight on: its
      gun stays up, lit, and the other comes up from her thigh and fires from the hip.
  shoot.png  Her draw and holster frames redrawn with her own arm turned.
  melee.png  7 frames: the blow with the gun (poses in make_melee), her other hand on her hip.
  melee_dual.png  7 frames: the blow with her near gun, as on melee.png; her far arm
      apart from it, its pistol down by her own leg, pulling back against the swing.
  melee_lit.png, melee_dual_lit.png  The same blows with the flashlight on the gun,
      ending on the held pose. Its lens is printed: player_light_kick follows it.
  swap.png, swap_lit.png  12 frames: her far hand takes the second pistol from
      the holster and brings it up under the first (lit: the flashlight shining on
      that first gun). Played backwards to put it away.
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
from make_care import bent_arm  # noqa: E402
from make_melee import AIM, BARREL_CUT, ELBOW_AT, GUN_FROM_X, HAND, HOLSTER, LOW, POSES, SHOULDER, body_without_arm, frame, gun_with_glove, no_holes, shorter_gun, sleeve, striking_arm, turn  # noqa: E402
from make_powers import FAR_ARM_INSIDE, INK, SKIN, load, without_hip_arm  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets/sprites/characters/cowgirl'
W, H = 81, 80
BODY = [rgb(0x2a2a30), rgb(0x4a4a54), rgb(0x74747e)]
BRASS = rgb(0xd0a848)
LENS_OFF, LENS_ON = rgb(0x9aa0a8), rgb(0xfff6dc)
LENGTH = 6
CLAMP_AT = (1, 2)                 # Along it, and rows above it, of the clamp holding it to the barrel
CLAMP_ROWS = (-2, -3)
CLIPPED = (53.0, 38.0)            # Its tail, clipped under the barrel; lens, with her arm's reach, at x 64, y 41 (light_rows in weapons.c)


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
THICK = 0.1                       # Her far arm, slim as the one on her hip
BEHIND_FROM = 35                  # Far hand this far forward: the arm passes behind her
FAR_ARM = (7.5, 7.5)              # Its lengths, shoulder to elbow to hand: it never stretches
SKIN_COLORS = (rgb(0x684833), rgb(0x463322))      # Her glove, the same as on the other hand
HIP = (30, 46)                    # Where her far hand rests, when she has it on her hip


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


NEAR_REACH = 5                    # Art px her gun arm is longer than her art's: 15, the length of them all
BARREL_LESS = BARREL_CUT[1] - BARREL_CUT[0]


def held_gun(aim: dict, body: dict, bend: tuple) -> tuple[dict, tuple, float]:
    """Her sleeve from the shoulder and, on it, her own glove and gun off the aim frame,
    turned about the elbow (degrees, + raises them). Returns its pixels and where
    the flashlight sits on the gun."""
    upper_angle, fore_angle = bend
    moving = {p: c for p, c in aim.items() if body.get(p) != c and p[0] >= 36 and p[1] <= 43 and c[:3] not in SKIN}
    fore_part = shorter_gun({p: c for p, c in moving.items() if p[0] >= ELBOW_AT[0]})
    a = math.radians(upper_angle)
    lx, ly = ELBOW_AT[0] - SHOULDER[0], ELBOW_AT[1] - SHOULDER[1]
    grow = (math.hypot(lx, ly) + NEAR_REACH) / math.hypot(lx, ly)
    elbow = (SHOULDER[0] + grow * (lx * math.cos(a) + ly * math.sin(a)), SHOULDER[1] + grow * (-lx * math.sin(a) + ly * math.cos(a)))
    px = sleeve(SHOULDER, (round(elbow[0]), round(elbow[1])))
    px.update(turn(fore_part, ELBOW_AT, fore_angle, elbow))
    b = math.radians(fore_angle)
    lx, ly = CLIPPED[0] - ELBOW_AT[0], CLIPPED[1] - ELBOW_AT[1]
    tail = (elbow[0] + lx * math.cos(b) + ly * math.sin(b), elbow[1] - lx * math.sin(b) + ly * math.cos(b))
    return px, tail, -b


def skin_hand(at: tuple) -> dict:
    """Her bare hand, as on her hip."""
    x, y = at
    out = {(x + a, y + b): SKIN_COLORS[b > 0] for a in (0, 1) for b in (0, 1)}
    edged = dict(out)
    for (px, py) in out:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (px + dx, py + dy) not in out:
                edged[(px + dx, py + dy)] = INK
    return edged


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


BACK_LINE = {41: 26, 42: 26, 43: 27, 44: 28, 45: 28, 46: 28, 47: 27}  # Shoot-frame rows of her back, and its column
BELT_BACK = {48: 26, 49: 25, 50: 25}  # Her belt's end, as wide as her hips
CORSET_FILL = rgb(0x2c363c)
BELT_FILL = {48: rgb(0x6c4626), 49: rgb(0x4a2e18), 50: rgb(0x4a2e18)}


def clean_back(free: dict) -> dict:
    """With her far arm off in front, nothing covers where it lay: her back as one
    clean line, a V down to the belt; the corset up to it, no lace past it."""
    out = dict(free)
    for y, edge in BACK_LINE.items():
        for x in [x for (x, yy) in out if yy == y and x < edge]:
            del out[(x, y)]
        for x in range(edge + 1, edge + 9):
            c = out.get((x, y))
            if c is None or c[:3] == INK[:3]:
                out[(x, y)] = CORSET_FILL
            else:
                break
        out[(edge, y)] = INK
    for y, edge in BELT_BACK.items():
        for x in [x for (x, yy) in out if yy == y and x < edge]:
            del out[(x, y)]
        for x in range(edge + 1, edge + 9):
            c = out.get((x, y))
            if c is None or c[:3] == INK[:3]:
                out[(x, y)] = BELT_FILL[y]
            else:
                break
        out[(edge, y)] = INK
    return out


# Her gun arm through a shot: drawn up, fired, kicked and put away, the same arm as
# in all her other poses.
DRAWN = {0: (-58, -66), 1: (-42, -46), 2: (-16, -14), AIM: (0, 0), AIM + 1: (0, 0), 5: (0, 14), 6: (-4, 4),
         HOLSTER: (-28, -26)}
FLASH_FROM_X = 64                 # Column of the base art's muzzle flash, on the fire frame


def arm_frame(shoot: Image, f: int) -> dict:
    """Shoot frame f: her body and arm in its pose, and on the fire frame, its flash."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    body = body_without_arm(aim, low, rest)
    px = dict(body)
    px.update(held_gun(aim, body, DRAWN[f])[0])
    if f == AIM + 1:
        px.update(muzzle_flash(shoot, NEAR_REACH - BARREL_LESS, 0))
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
    gun, tail, turned = held_gun(aim, body, bend)
    if on_hip:
        px = dict(body)
        px.update(gun)
    else:
        free, shoulder = without_hip_arm(body)
        free = clean_back(free)
        behind = far[0] >= BEHIND_FROM                   # Reaching forward: past her, not across her
        top = (shoulder[0] + FAR_ARM_INSIDE[0], shoulder[1] + FAR_ARM_INSIDE[1]) if behind else shoulder
        elbow, at = two_bones(top, far, FAR_ARM)
        limb = bent_arm(top, elbow, at, THICK)
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
        elif held == 'pistol':
            px.update(second_pistol(aim, at, -70))
        elif held == 'aiming':
            px.update(second_pistol(aim, at, -40))
        px.update(skin_hand(at))
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


def second_pistol(aim: dict, at: tuple, angle: float) -> dict:
    """Her other pistol in that hand: the gun off her own art, without its butt
    (the hand has it), a shade darker, as on her duals."""
    gun = shorter_gun({p: tuple(round(v * 0.86) for v in c[:3]) + (255,) for p, c in aim.items()
                       if p[0] >= GUN_FROM_X and p[1] in range(26, 42) and not (p[0] <= HAND[0] + 1 and p[1] > HAND[1] + 2)})
    return turn(gun, HAND, angle, at)


def holster() -> dict:
    """It in the belt: a leather holster at her hip, the butt showing."""
    leather, dark, wood = rgb(0x5a3e22), rgb(0x3e2a16), rgb(0x8a6a3e)
    px = {(x, y): (leather if x < 30 else dark) for y in range(45, 52) for x in range(27, 31)}
    px.update({(x, y): wood for y in (42, 43, 44) for x in (28, 29)})
    edged = dict(px)
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in px:
                edged[(x + dx, y + dy)] = INK
    return edged




# The two guns work like a piston, each down by its own leg. Near arm: how far the
# sleeve and the glove with the gun are turned (degrees, + raises them). The gun on
# its turn comes up, fires on frame 4, kicks and starts down.
NEAR_FIRING = ((-34, -70), (-20, -40), (-6, -6), (0, 0), (0, 0), (0, 14), (-4, 4), (-20, -22))
# Her body turns into the other's shot: this arm goes behind her, its pistol down outside
# her leg, there before the other comes up past it.
NEAR_RESTING = ((-36, -56), (-38, -58), (-38, -60), (-38, -60), (-38, -60), (-38, -60), (-38, -60), (-37, -58))
# Far arm, from her own shoulder, swinging nearly straight like a pendulum, not folding
# over her belly: where the hand is, the gun's angle. Under the lace (PLAYER_FAR_GUN_ROWS).
# Passing her hips the pistol points forward or back, never down across her legs.
FAR_FIRING = (((27, 49), -135), ((37, 46), -22), ((44, 43), -12), ((49, 41), 0),
              ((49, 41), 0), ((47, 38), 14), ((45, 42), -4), ((37, 46), -22))
# Down clear of her leg, angled away from it, never along it: a third leg, there.
FAR_RESTING = (((28, 49), -135), ((25, 50), -135), ((22, 50), -135), ((20, 49), -135),
               ((20, 49), -135), ((20, 49), -135), ((20, 49), -135), ((23, 50), -135))
# With the flashlight up, its gun stays on the aim: it only kicks when it fires, and the
# other fires from her hip, under the flashlight (PLAYER_LIT_FAR_GUN_ROWS).
LIT_FIRING = ((-2, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 14), (-4, 4), (-1, 0))
LIT_RESTING = ((0, 0),) * 8
FAR_LIT_FIRING = (((27, 49), -135), ((37, 48), -20), ((43, 46), -10), ((47, 45), 0),
                  ((47, 45), 0), ((46, 43), 12), ((44, 46), -2), ((37, 48), -20))
ARM_LENGTHS = FAR_ARM             # Her far arm, shoulder to elbow to hand: always these


# Her arm, turning into its shot, starts this far in along her shoulders (art px). Only the
# arm: her body keeps all its size.
TURNING = (0, 1, 2, 3, 3, 3, 3, 2)


def make_dual(shoot: Image, far_fires: bool, lit: bool = False) -> Image:
    """8 frames of one shot: one gun firing and the other on its way down by its
    own leg and up again. The near arm and gun are her real ones off the aim frame,
    turned; the far arm comes from her far shoulder, in front of her. Lit: the near
    gun stays up with the flashlight on it."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    body = body_without_arm(aim, low, rest)
    free, shoulder = without_hip_arm(body)
    free = clean_back(free)
    img = Image(W * 8, H)
    if lit:
        near_poses, far_poses = (LIT_RESTING, FAR_LIT_FIRING) if far_fires else (LIT_FIRING, FAR_RESTING)
    else:
        near_poses, far_poses = (NEAR_RESTING, FAR_FIRING) if far_fires else (NEAR_FIRING, FAR_RESTING)
    for f in range(8):
        near, tail, turned = held_gun(aim, body, near_poses[f])
        behind_her = far_fires and not lit
        px = dict(near) if behind_her else {}
        px.update(free)
        top = (shoulder[0] + (TURNING[f] if far_fires else 0), shoulder[1])
        want, angle = far_poses[f]
        elbow, at = two_bones(top, want, ARM_LENGTHS)
        px.update(bent_arm(top, elbow, at, THICK))
        px.update(second_pistol(aim, at, angle))
        px.update(skin_hand(at))
        if not behind_her:
            px.update(near)
        if lit:
            px.update(flashlight(tail, turned, True))
        if f == AIM + 1:
            ox, oy = (at[0] - HAND[0] - BARREL_LESS, at[1] - HAND[1]) if far_fires else (NEAR_REACH - BARREL_LESS, 0)
            px.update(muzzle_flash(shoot, ox, oy))
            print(f'make_flashlight: {"lit " if lit else ""}far gun, fire frame: {NEAR_REACH - BARREL_LESS - ox:+.0f} back, {oy:+.0f} down' if far_fires else '', end='\n' if far_fires else '')
        put(img, f, px)
    return img


# Her far hand and pistol through the blow (make_melee.POSES): back on the wind-up,
# and down again as the other swings.
FAR_IN_BLOW = (((23, 50), -135), ((21, 48), -130), ((22, 49), -132), ((20, 49), -135), ((20, 49), -135), ((22, 50), -135))


def on_the_blow(pose: tuple) -> tuple:
    """Where the flashlight is on the gun in a blow's pose: its tail and angle."""
    (hx, hy), angle, _ = pose
    hand = (SHOULDER[0] + hx, SHOULDER[1] + hy)
    a = math.radians(angle)
    lx, ly = CLIPPED[0] - HAND[0], CLIPPED[1] - HAND[1]
    return (hand[0] + lx * math.cos(a) + ly * math.sin(a), hand[1] - lx * math.sin(a) + ly * math.cos(a)), -a


def make_blow(shoot: Image, last: dict, both_guns: bool, lit: bool) -> Image:
    """The blow with her near gun: her other hand on her hip, or its pistol down by
    her leg; the flashlight on the gun, lit; last is the frame she ends on."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    body = body_without_arm(aim, low, rest)
    gun = gun_with_glove(aim, body)
    if both_guns:
        free, shoulder = without_hip_arm(body)
        free = clean_back(free)
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
            px.update(bent_arm(shoulder, elbow, at, THICK))
            px.update(second_pistol(aim, at, angle))
            px.update(skin_hand(at))
        striking_arm(px, gun, f)
        if lit:
            px.update(flashlight(*on_the_blow(pose), True))
        put(img, f, px)
    return img


def make_light_dual(shoot: Image, dual: Image) -> Image:
    """With both hands full: she slides one pistol into the belt; her free hand
    takes the flashlight and clips it on the other, by her chest; it goes back
    for the pistol and both come up again, lit. In-betweened, like the other."""
    keys = [((-10, -6), 0, (23, 50), False, 'pistol', False, False),  # From down by her leg
            (*READY, (28, 48), False, 'pistol', False, False),   # Bringing it to the belt
            (*READY, (30, 45), False, None, False, True),        # In it, the hand free
            (*READY, (31, 47), False, 'light', False, True),     # It has the flashlight
            (*HALF, (34, 47), False, 'light', False, True),      # Coming up
            (*CLOSE, (37, 46), False, 'light', False, True),
            (*CLOSE, (39, 46), False, None, True, True),         # Clipped: click
            (*CLOSE, (34, 48), False, None, True, True),
            (*HALF, (31, 45), False, None, True, True),          # Back to the pistol at her hip
            (*HALF, (30, 46), False, 'pistol', True, False),     # It in hand
            (*LEVEL, (23, 50), False, 'pistol', True, False)]    # One rising, the other down again
    img = Image(W * FRAMES, H)
    put(img, 0, frame(dual, AIM))
    for f in range(1, FRAMES - 1):
        put(img, f, posed(shoot, blend(keys, (f - 1) / (FRAMES - 3))))
    px = frame(dual, AIM)
    px.update(flashlight(*drawn_lens(shoot, AIM), True))
    put(img, FRAMES - 1, px)
    return img


def make_swap(shoot: Image, dual: Image, lit: bool) -> Image:
    """Her far hand off her hip, to the holster at the belt; the second pistol out,
    up beside the first; and with no shot to fire, both come down to rest, as after
    a single shot, her hand back on her hip. Lit: with the flashlight on, shining,
    on the first gun all through, which stays up. In-betweened."""
    light = 'lit' if lit else False
    end = (-14, -12) if not lit else (-1, 0)
    keys = [((-14, -12), 0, HIP, True, None, light, False),        # Her gun held as it comes up
            ((-8, -4), 0, (29, 45), False, None, light, True),     # Hand to the holster
            ((-6, -2), 0, (30, 48), False, 'pistol', light, False),  # It has it
            ((-4, -1), 0, (33, 48), False, 'aiming', light, False),  # Turned, low in front of her
            ((-6, -6), 0, (31, 48), False, 'pistol', light, False),  # And down again
            (end, 0, HIP, True, None, light, False)]
    img = Image(W * 12, H)
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
    _, tail, turned = held_gun(aim, body_without_arm(aim, low, rest), DRAWN[f])
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


def far_gun_at_rest(shoot: Image) -> dict:
    """Her far pistol and hand as the duals' aim frame has them, down by her leg."""
    aim, low, rest = frame(shoot, AIM), frame(shoot, LOW), frame(shoot, HOLSTER)
    _, shoulder = without_hip_arm(body_without_arm(aim, low, rest))
    want, angle = FAR_RESTING[AIM]
    _, at = two_bones(shoulder, want, ARM_LENGTHS)
    px = second_pistol(aim, at, angle)
    px.update(skin_hand(at))
    return px


def make_light_walk(walk: Image, light: Image, front: dict = {}) -> Image:
    """Each walk frame's legs under the held pose's upper body, then that pose
    breathing on still legs. Torso, arm and gun move as one piece, and only up
    and down: whatever the legs do, the gun stays steady. front is what hangs below
    the waist and stays over the legs: her other pistol."""
    held = frame(light, light.width // W - 1)            # The held pose: its last frame
    sx, sy = WALK_SHIFT
    join = LEGS_FROM + sy

    def walk_px(i: int) -> dict:
        return {(x, y): walk.get(i * WALK_W + x, y) for y in range(WALK_H) for x in range(WALK_W)
                if walk.get(i * WALK_W + x, y)[3]}

    def hips(px: dict, row: int, shift: int) -> float:
        xs = [x + shift for (x, y) in px if y == row]
        return sum(xs) / max(1, len(xs))

    def upper(out: dict, dx: int, dy: int) -> None:
        for (x, y), c in held.items():
            if y < join:
                out[(x + dx, y + dy)] = c

    # One sideways place for all the frames: on the legs' average.
    her_own = {p: c for p, c in held.items() if p not in front}
    dx = round(sum(hips(walk_px(i), LEGS_FROM, sx) for i in range(8)) / 8 - hips(her_own, join, 0))
    img = Image(W * (8 + len(BREATH)), H)
    for i in range(8):
        legs = {p: c for p, c in walk_px(i).items() if p[1] >= LEGS_FROM - 3}
        for (x, y) in sorted(p for p, c in legs.items() if c[:3] in SKIN):
            # The hand that hung here in the plain walk: its trousers carry on instead.
            cloth = next((legs[(x - d, y)] for d in range(1, 8)
                          if (x - d, y) in legs and legs[(x - d, y)][:3] not in SKIN and legs[(x - d, y)][:3] != INK[:3]), None)
            if cloth:
                legs[(x, y)] = cloth
            else:
                del legs[(x, y)]
        out = {(x + sx, y + sy): c for (x, y), c in legs.items()}
        upper(out, dx, STRIDE[i])
        out.update({(x + dx, y + STRIDE[i]): c for (x, y), c in front.items()})
        put(img, i, out)
    for i, sway in enumerate(BREATH):                    # Stood still: the chest rising
        out = {p: c for p, c in held.items() if p[1] >= join - 3}
        upper(out, 0, sway)
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
                      ('melee_dual', make_blow(shoot, frame(dual, HOLSTER), True, False)),
                      ('melee_lit', make_blow(shoot, held, False, True)),
                      ('melee_dual_lit', make_blow(shoot, held_dual, True, True)),
                      ('light', light), ('light_dual', light_dual),
                      ('swap', make_swap(shoot, dual, False)), ('swap_lit', make_swap(shoot, dual, True)),
                      ('flashlight', make_overlay(shoot))):
        img.save(OUT / f'{name}.png')
        print(f'make_flashlight: {name} ({img.width} x {img.height})')
    for f, pose in enumerate(POSES):                     # For player_light_kick
        if pose:
            (x, y), a = on_the_blow(pose)
            print(f'make_flashlight: blow {f}: lens {x + LENGTH * math.cos(a) - CLIPPED[0] - LENGTH - NEAR_REACH:+.1f}, '
                  f'{y + LENGTH * math.sin(a) - CLIPPED[1]:+.1f}')
    swat = OUT.parent / 'swat'
    for folder, gun in ((OUT, ''), (OUT, '_dual'), (swat, ''), (swat, '_shotgun')):
        front = far_gun_at_rest(shoot) if gun == '_dual' else {}
        img = make_light_walk(load(folder / 'walk.png'), load(folder / f'light{gun}.png'), front)
        img.save(folder / f'light_walk{gun}.png')
        print(f'make_flashlight: {folder.name}/light_walk{gun} ({img.width} x {img.height})')
    make_shoot(shoot).save(OUT / 'shoot.png')            # Last: the others read it as dressed
    return 0


if __name__ == '__main__':
    sys.exit(main())
