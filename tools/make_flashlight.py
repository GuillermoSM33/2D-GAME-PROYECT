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
  shoot.png  Draw (0-2), aim (3), fire (4), recoil (5-6), lowered (7): the gun arm is her
      far one, behind her far lapel. The shot throws the arm up and her shoulders back, and
      she comes back to it, as in the reference (objetivo/shoot_v2.gif, apuntar.gif).
  reload.png  Eight frames: open, eject, speedload, close the single revolver.
  reload_dual.png, reload_dual_b.png  48 frames per hand: 24 for one cylinder,
      24 for the second of a pair; hands work low at the belt, shoulders stay fixed.
  reload_dual_lower.png, reload_dual_b_lower.png  Arms, hands and guns over walking legs.
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
And for the sheriff, each gun:
  light_walk*.png  24 frames: 20 running with it up, the gun held level by her far arm over
      the whole running body; then 4 stood still, breathing.

The SWAT's light poses and breathing are authored by rebuild_swat.py; rebuilding
the sheriff must not overwrite those finished sheets. Standard library only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cowgirl_arm import arm_limb as bent_arm, glove, pistol_muzzle, pistol_pointing, turned  # noqa: E402
from make_melee import (AIM, HOLSTER, LOW, POSES, SHOULDER, behind, body_at, body_without_arm, frame, no_holes,  # noqa: E402
                        sleeve, striking_arm)
from make_powers import INK, load  # noqa: E402
from make_sprites import Image, rgb  # noqa: E402
from rework_cowgirl import (FAR_TONES, WALK_FRAMES, arm_pixels, behind_arm, stride_bob, walk_arms,  # noqa: E402
                            walking_body)
import cowgirl_pose as pose  # noqa: E402
import cowgirl_torso as figure  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets/sprites/characters/cowgirl'
W, H = 81, 80
BODY = [rgb(0x2a2a30), rgb(0x4a4a54), rgb(0x74747e)]
BRASS = rgb(0xd0a848)
LENS_OFF, LENS_ON = rgb(0x9aa0a8), rgb(0xfff6dc)
LENGTH = 6
CLAMP_AT = (1, 2)                 # Along it, and rows above it, of the clamp holding it to the barrel
CLAMP_ROWS = (-2, -3)
AIM_LENS_TAIL = (58.0, 40.3)      # Shared reference for the action lens offsets


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
# "Far" in these sheets is the arm away from the aim, the left of the picture: in three
# quarters it is the one nearest to us, so it is drawn in front of her. Her gun arm, on the
# right, is behind her far lapel.
FAR_ARM = (7.5, 7.5)              # Its lengths, shoulder to elbow to hand: it never stretches
HIP = (27, 47)                    # Where her far hand rests, when she has it on her hip
SHOOT_BUCKLE, SHOOT_BELT = 34, 49 # Her buckle's middle column and row, on the shoot template
FAR_TOP = (27, 37)                # Her far shoulder, on it
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


GUN_HAND = (12.8, 0.0)            # Her gun hand on the aim, from her shoulder: the muzzle comes to where the bullet starts
GUN_LIGHT = (7.5, 1.3)            # Where the flashlight's tail sits on a gun, from the hand
HELD_LIGHT = (4.5, 1.2)           # On the level arm: lens centre stays at (64,41), as in runtime
GUN_PITCH = -10.0                # Aim muzzle at (69,33), matching the runtime bullet origin
NEAR_FLASH = 6                    # Flash begins at x70, just beyond the muzzle


def held_gun(bend: tuple, shoulder: tuple = SHOULDER) -> tuple[dict, tuple, float]:
    """Her gun arm: the same arm, glove and pistol as her other, the arm turned about the
    shoulder and the gun about the hand (degrees, + raises them). Returns its pixels and where
    the flashlight sits on the gun."""
    upper_angle, fore_angle = bend
    fore_angle += GUN_PITCH
    rx, ry = turned(GUN_HAND, upper_angle)
    hand = (round(shoulder[0] + rx), round(shoulder[1] + ry))
    px = sleeve(shoulder, hand)
    px.update(pistol_pointing(hand, fore_angle))
    px.update(glove(hand, shoulder))
    lx, ly = turned(HELD_LIGHT, fore_angle)
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


# Her gun arm through a shot: drawn up, fired, kicked and put away, the same arm as in all her
# other poses. How far the arm and the gun are turned (degrees, + raises them).
DRAWN = {0: (-58, -66), 1: (-42, -46), 2: (-16, -14), AIM: (0, 0), AIM + 1: (0, 0), 5: (15, 32), 6: (4, 11),
         HOLSTER: (-28, -26)}
# ...and her body with it: columns she leans at her head, rows her covered chest is off her.
SWAY = {2: (0, 0), AIM: (0, 0), AIM + 1: (0, 0), 5: (-2, -1), 6: (-1, 1), HOLSTER: (0, 0)}
FLASH_FROM_X = 64                 # Column of the base art's muzzle flash, on the fire frame
NEAR_MUZZLE_ROW = 32              # ...and the row of its middle


def thrown_back(f: int) -> tuple:
    """Where her gun shoulder is on shoot frame f: back a column or so as she leans."""
    lean = SWAY.get(f, (0, 0))[0]
    return SHOULDER[0] + round(lean / 2), SHOULDER[1]


def arm_frame(shoot: Image, f: int) -> dict:
    """Shoot frame f: her body and arm in its pose, and on the fire frame, its flash."""
    lean, chest = SWAY.get(f, (0, 0))
    body = body_without_arm({}, {}, {}, lean=lean, chest=chest)
    px = behind(held_gun(DRAWN[f], thrown_back(f))[0], body)
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


def make_reload(shoot: Image) -> Image:
    """Upright cylinder reload, returning to the exact shared aiming pose."""
    from cowgirl_reload import single_reload_frames
    body = body_at()
    image = Image(W * 8, H)
    for f, pixels in enumerate(single_reload_frames(body, arm_frame(shoot, AIM))):
        put(image, f, pixels)
    return image


DUAL_RELOAD_FRAMES = 24            # PLAYER_DUAL_RELOAD_FRAMES; 50 ms per pose
DUAL_RELOAD_HANDOFF = 18           # Loaded gun down at the belt, before drawing the spare
RELOAD_REST = ((49, 48), (18, 49))
RELOAD_BELT = ((40, 49), (26, 49))
RELOAD_HELD = ((39, 50), (30, 50)) # Under the shared shoulder; the wrist follows its forearm.
RELOAD_ANGLE = (-80, -65)          # Barrels low; no wrist folded back toward the shoulder.
RELOAD_REST_ANGLE = (-80, -110)


def toward(a: tuple, b: tuple, k: float) -> tuple:
    k = k * k * (3.0 - 2.0 * k)
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def turn_toward(a: float, b: float, k: float) -> float:
    """Use the short arc; a holster gesture must not spin the wrist backwards."""
    return a + ((b - a + 180) % 360 - 180) * k


def reload_bones(top: tuple, want: tuple, lengths: tuple, side: int = -1) -> tuple:
    """Stable elbows, hanging below fixed shoulders; rasterize only at the end."""
    upper, fore = lengths
    dx, dy = want[0] - top[0], want[1] - top[1]
    distance = max(math.hypot(dx, dy), 1e-6)
    ux, uy = dx / distance, dy / distance
    reach = min(upper + fore - .5, max(abs(upper - fore) + .5, distance))
    wrist = (top[0] + ux * reach, top[1] + uy * reach)
    along = (upper * upper - fore * fore + reach * reach) / (2 * reach)
    out = math.sqrt(max(0.0, upper * upper - along * along))
    return (top[0] + ux * along + side * uy * out,
            top[1] + uy * along - side * ux * out), wrist


def reload_reach(hand: int, a: tuple, b: tuple, k: float) -> tuple:
    """Interpolate the two bone rotations, so the elbow travels in a steady arc.

    Interpolating the hand alone made the elbow whip sideways halfway through
    fetching the loader, despite each isolated pose having valid bone lengths.
    """
    top, lengths, side = (FAR_TOP, FAR_ARM, -1) if hand else (SHOULDER, (7, 7), 1)
    ea, wa = reload_bones(top, a, lengths, side)
    eb, wb = reload_bones(top, b, lengths, side)
    upper_a = math.degrees(math.atan2(ea[1] - top[1], ea[0] - top[0]))
    upper_b = math.degrees(math.atan2(eb[1] - top[1], eb[0] - top[0]))
    fore_a = math.degrees(math.atan2(wa[1] - ea[1], wa[0] - ea[0]))
    fore_b = math.degrees(math.atan2(wb[1] - eb[1], wb[0] - eb[0]))
    upper = math.radians(turn_toward(upper_a, upper_b, k))
    fore = math.radians(turn_toward(fore_a, fore_b, k))
    return (top[0] + lengths[0] * math.cos(upper) + lengths[1] * math.cos(fore),
            top[1] + lengths[0] * math.sin(upper) + lengths[1] * math.sin(fore))


def dual_reload_pose(other: bool, f: int, second: bool) -> tuple:
    """Hands, barrel angles and held guns. The second block starts with the
    previous loaded gun still in hand, and the next one in its own holster.
    First block 18 and second block 0 are the same low handoff pose.
    """
    target, helper = int(other), int(not other)
    hands = list(RELOAD_REST)
    angles, held = list(RELOAD_REST_ANGLE), [True, True]
    if f <= 5:
        k = f / 5
        if second:
            hands[helper] = toward(RELOAD_HELD[helper], RELOAD_BELT[helper], k)
            hands[target] = toward(RELOAD_BELT[target], RELOAD_HELD[target], k)
            angles[helper] = turn_toward(RELOAD_ANGLE[helper], -90, k)
            angles[target] = turn_toward(-90, RELOAD_ANGLE[target], k)
            held[target] = f > 0
        else:
            hands[helper] = toward(RELOAD_REST[helper], RELOAD_BELT[helper], k)
            hands[target] = toward(RELOAD_REST[target], RELOAD_HELD[target], k)
            angles[helper] = turn_toward(angles[helper], -90, k)
            angles[target] = turn_toward(angles[target], RELOAD_ANGLE[target], k)
        held[helper] = f < 5
    elif f <= DUAL_RELOAD_HANDOFF:
        hands[target], angles[target] = RELOAD_HELD[target], RELOAD_ANGLE[target]
        held[helper] = False
        # Unlock/eject, fetch a speedloader at the helper's belt, load, close.
        at_cylinder = (36, 49)
        path = ((5, RELOAD_BELT[helper]), (8, at_cylinder), (11, RELOAD_BELT[helper]),
                (14, at_cylinder), (15, at_cylinder), (18, RELOAD_BELT[helper]))
        for (start, a), (end, b) in zip(path, path[1:]):
            if start <= f <= end:
                hands[helper] = reload_reach(helper, a, b, (f - start) / (end - start))
                break
    else:
        k = (f - DUAL_RELOAD_HANDOFF) / (DUAL_RELOAD_FRAMES - 1 - DUAL_RELOAD_HANDOFF)
        hands[target] = toward(RELOAD_HELD[target], RELOAD_REST[target], k)
        hands[helper] = toward(RELOAD_BELT[helper], RELOAD_REST[helper], k)
        angles[target] = turn_toward(RELOAD_ANGLE[target], RELOAD_REST_ANGLE[target], k)
        angles[helper] = turn_toward(-90, RELOAD_REST_ANGLE[helper], k)
    return hands, angles, held


def make_dual_reload(shoot: Image, other: bool, lower_only: bool = False) -> Image:
    """48 frames per hand: one cylinder (0..23), then the second (24..47).
    Work stays at the belt. Runtime holds first-block frame 18 before the swap.
    """
    body = body_at()
    image = Image(W * DUAL_RELOAD_FRAMES * 2, H)
    bores = ((0, -2), (1, -1), (2, 0), (1, 1), (0, 2), (-1, 1), (-2, 0), (-1, -1))
    for second in (False, True):
        for f in range(DUAL_RELOAD_FRAMES):
            action_layer = {}
            hands, angles, held = dual_reload_pose(other, f, second)
            tops = [SHOULDER, FAR_TOP]
            elbows, wrists = [], []
            for hand in range(2):
                elbow, wrist = reload_bones(tops[hand], hands[hand], FAR_ARM if hand else (7, 7), -1 if hand else 1)
                elbows.append(elbow)
                wrists.append(wrist)
            # Her gun arm starts behind her far lapel; only its forearm comes round in
            # front of her, at the belt. The other arm, nearest to us, is all in front.
            gun_arm = gun_sleeve(tops[0], elbows[0], wrists[0])
            near_sleeve = bent_arm(tops[1], elbows[1], wrists[1])
            px = behind(gun_arm, behind_arm(body, near_sleeve))
            for hand, rows in enumerate((figure.pixels(figure.HOLSTER, figure.HOLSTER_X0), figure.second_holster())):
                # Only a holstered revolver shows its wooden grip above the case.
                for (hx, hy), color in rows.items():
                    if hy >= figure.BELT_ROW + 2 or not held[hand]:
                        px[(hx + WALK_SHIFT[0], hy + WALK_SHIFT[1])] = color
            for hand in (1, 0):
                limb = near_sleeve if hand else {p: c for p, c in gun_arm.items() if p[1] >= 44}
                px.update(limb)
                action_layer.update(limb if not hand else {p: c for p, c in limb.items() if p[1] >= 44})
                if held[hand]:
                    gun = pistol_pointing(wrists[hand], angles[hand])
                    px.update(gun)
                    action_layer.update(gun)
                mitt = glove(wrists[hand], elbows[hand])
                px.update(mitt)
                action_layer.update(mitt)
            if 7 <= f <= 16:
                cx, cy = (33, 51) if other else (39, 51)
                for y in range(-3, 4):
                    for x in range(-3, 4):
                        if x * x + y * y <= 12:
                            px[(cx + x, cy + y)] = rgb(0xa1aaa9) if x + y < -1 else rgb(0x4c535b)
                            action_layer[(cx + x, cy + y)] = px[(cx + x, cy + y)]
                for x, y in bores:
                    px[(cx + x, cy + y)] = rgb(0xb59050) if f >= 14 else INK
                    action_layer[(cx + x, cy + y)] = px[(cx + x, cy + y)]
                px[(cx, cy)] = rgb(0x727f86)
                action_layer[(cx, cy)] = px[(cx, cy)]
                if f in (8, 9):
                    for dx, dy in ((2, 6), (5, 8), (7, 5)):
                        x = cx + (-dx if other else dx)
                        px[(x, cy + dy)] = rgb(0xb59050)
                        px[(x, cy + dy + 1)] = rgb(0x8e6c28)
                        action_layer[(x, cy + dy)] = px[(x, cy + dy)]
                        action_layer[(x, cy + dy + 1)] = px[(x, cy + dy + 1)]
                helper = int(not other)
                if f in (11, 12, 13):
                    wx, wy = (round(value) for value in wrists[helper])
                    for x, y in bores:
                        px[(wx + x, wy - 2 + y)] = rgb(0xb59050)
                        action_layer[(wx + x, wy - 2 + y)] = px[(wx + x, wy - 2 + y)]
                mitt = glove(wrists[helper], elbows[helper])
                px.update(mitt)
                action_layer.update(mitt)
            # Runtime clips this action mask at the actual walking waist
            # (row 53 in the reload template). The old row-60 barrel mask
            # discarded gun grips, hands and the upper half of the low guns.
            # Keep every foreground action pixel, without static trousers;
            # the renderer chooses the cut and paints it over moving legs.
            output = action_layer if lower_only else px
            put(image, f + second * DUAL_RELOAD_FRAMES, output)
    return image


def gun_sleeve(top: tuple, elbow: tuple, wrist: tuple) -> dict:
    """Her bent gun arm: a tone deeper above the elbow, behind her."""
    px = bent_arm(top, elbow, wrist)
    return {p: FAR_TONES.get(c, c) if math.dist(p, top) < 3.5 else c for p, c in px.items()}


def posed(shoot: Image, key: tuple) -> dict:
    """One frame: her, the gun in its pose, her far hand where the key says."""
    bend, _, far, on_hip, held, clipped, holstered = key
    gun, tail, turned = held_gun(bend)
    if on_hip:
        px = behind(gun, body_without_arm({}, {}, {}))
    else:
        elbow, at = two_bones(FAR_TOP, far, FAR_ARM)
        limb = bent_arm(FAR_TOP, elbow, at)
        px = behind(gun, behind_arm(body_at(), limb))
        if holstered:
            px.update(holster())
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
    """It in the belt: the small holster on her near hip, the same as standing."""
    return {(x + WALK_SHIFT[0], y + WALK_SHIFT[1]): c for (x, y), c in figure.second_holster().items()}


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


# Her body through the two turns: a column back and her chest a row late on each shot.
DUAL_SWAY = {(0, 9): (-1, -1), (0, 10): (-1, -1), (0, 11): (-1, 0), (0, 12): (0, 1), (0, 13): (0, 1),
             (1, 9): (-1, -1), (1, 10): (-1, -1), (1, 11): (-1, 0), (1, 12): (0, 1), (1, 13): (0, 1)}


def make_dual(shoot: Image, far_fires: bool, lit: bool = False) -> Image:
    """One turn: one gun firing, the other on its way. Her gun arm, turned about its shoulder
    behind her far lapel; the far arm comes from her other shoulder, in front of her, with
    its pistol drawn the same all the way round: it fires from her hip (objetivo/
    shoot_cadera.gif). Lit: the near gun stays up with the flashlight."""
    img = Image(W * DUAL_FRAMES, H)
    start = DUAL_FRAMES if far_fires else 0
    for f in range(DUAL_FRAMES):
        count = f + start
        lean, chest = (0, 0) if lit else DUAL_SWAY.get((int(far_fires), f), (0, 0))
        near, tail, turned = held_gun(along(NEAR_LIT if lit else NEAR_SWING, count))
        hx, hy, angle = along(FAR_SWING, count)
        elbow, at = two_bones(FAR_TOP, (hx, hy), ARM_LENGTHS)
        limb = bent_arm(FAR_TOP, elbow, at)
        px = behind(near, behind_arm(body_at(lean, chest), limb))
        px.update(limb)
        px.update(pistol_pointing(at, angle))
        px.update(glove(at, elbow))
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
    img = Image(W * 8, H)
    for f, (near_hand, far_hand, raised) in enumerate(POWER_DUAL if both_guns else POWER_ONE):
        elbow, at = two_bones(FAR_TOP, far_hand, FAR_ARM)
        near_elbow = near_bent(near_hand)
        gun_arm = gun_sleeve(NEAR_TOP, near_elbow, near_hand)
        limb = bent_arm(FAR_TOP, elbow, at)
        lean, chest = {5: (-1, -1), 6: (0, 1)}.get(f, (0, 0))
        px = behind(gun_arm, behind_arm(body_at(lean, chest), limb))
        # Her gun arm's upper half stays behind her; its forearm comes round in front
        px.update({p: c for p, c in gun_arm.items() if math.dist(p, near_hand) < math.dist(p, NEAR_TOP) - 1})
        px.update(limb)
        if both_guns:
            px.update(pistol_pointing(at, raised))
        px.update(glove(at, elbow))
        px.update(pistol_pointing(near_hand, raised))
        px.update(glove(near_hand, near_elbow))
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
    img = Image(W * len(POSES), H)
    for f, at_pose in enumerate(POSES):
        if at_pose is None:
            put(img, f, last)
            continue
        lean = at_pose[2] * 2                            # Back on the wind-up, into the blow
        if both_guns:
            want, angle = FAR_IN_BLOW[f]
            elbow, at = two_bones(FAR_TOP, want, ARM_LENGTHS)
            limb = bent_arm(FAR_TOP, elbow, at)
            px = behind_arm(body_at(lean), limb)
            px.update(limb)
            px.update(pistol_pointing(at, angle))
            px.update(glove(at, elbow))
        else:
            px = body_without_arm({}, {}, {}, lean=lean)
        striking_arm(px, f)
        if lit:
            px.update(flashlight(*on_the_blow(at_pose), True))
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
    _, tail, turned = held_gun(DRAWN[f], thrown_back(f))
    return tail, turned


def make_overlay(shoot: Image) -> Image:
    """The flashlight alone, on each shoot frame: it keeps its place on the gun."""
    img = Image(W * 8, H)
    for f in range(8):
        put(img, f, flashlight(*drawn_lens(shoot, f), True))
    return img


WALK_SHIFT = (12, 7)              # A walk-frame point on the shoot template (player.c)
CHEST_ENDS = 45                   # Shoot-frame row: above it her chest lifts on the breath


# Rows the whole upper body is off its mark (+ down), lens included: as
# player_light_sway in player.c. Lowest as a leg passes under her, level as a
# foot lands; on the breath, the chest lifting.
STRIDE = tuple(stride_bob(i) for i in range(WALK_FRAMES))
BREATH = (0, -1, -1, 0)


LIGHT_HAND = (50., 37.)           # Her gun hand as she runs with it up: the lens is four columns nearer than aiming


def walking_held(frame_index: int, both_guns: bool = False) -> tuple:
    """Her gun arm held level from her running shoulder, behind her, and with the duals her
    other arm and its pistol, in front. The hand only rises and falls with her."""
    top, _, _ = pose.arm(frame_index, True)
    top = (top[0] + WALK_SHIFT[0], top[1] + WALK_SHIFT[1])
    elbow, wrist = reload_bones(top, (LIGHT_HAND[0], LIGHT_HAND[1] + STRIDE[frame_index]), ARM_LENGTHS)
    gun = gun_sleeve(top, elbow, wrist)
    gun.update(pistol_pointing(wrist, GUN_PITCH))
    gun.update(glove(wrist, elbow))
    lx, ly = turned(HELD_LIGHT, GUN_PITCH)
    gun.update(flashlight((wrist[0] + lx, wrist[1] + ly), -math.radians(GUN_PITCH), True))
    at = SHOOT_BELT + STRIDE[frame_index]
    near = walk_arms(frame_index)[0]
    front = arm_pixels(near, at, SHOOT_BUCKLE)
    if both_guns:
        (_, _), (ex, ey), (hx, hy) = near
        elbow, wrist = (ex + SHOOT_BUCKLE, ey + at), (hx + SHOOT_BUCKLE, hy + at)
        front.update(pistol_pointing(wrist, -28))
        front.update(glove(wrist, elbow))
    return gun, front


def make_light_walk(light: Image, dual: bool) -> Image:
    """Her whole running body with the gun held level by its arm, then the held pose breathing
    on still legs."""
    held = frame(light, light.width // W - 1)            # The held pose: its last frame
    img = Image(W * (WALK_FRAMES + len(BREATH)), H)
    for i in range(WALK_FRAMES):
        body = {(x + WALK_SHIFT[0], y + WALK_SHIFT[1]): c for (x, y), c in walking_body(i, dual=False).items()}
        gun, front = walking_held(i, dual)
        px = behind(gun, behind_arm(body, front))
        px.update(front)
        put(img, i, px)
    for i, rise in enumerate(BREATH):                    # Stood still: her chest rising, her belt where it is
        out = dict(held)
        out.update({(x, y + rise): c for (x, y), c in held.items() if y < CHEST_ENDS})
        put(img, WALK_FRAMES + i, out)
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
                      ('flashlight', make_overlay(shoot)), ('reload', make_reload(shoot)),
                      ('reload_dual', make_dual_reload(shoot, False)), ('reload_dual_b', make_dual_reload(shoot, True)),
                      ('reload_dual_lower', make_dual_reload(shoot, False, True)),
                      ('reload_dual_b_lower', make_dual_reload(shoot, True, True))):
        img.save(OUT / f'{name}.png')
        print(f'make_flashlight: {name} ({img.width} x {img.height})')
    for f in (5, 6):                                     # For player_light_kick: the recoil
        (x, y), a = drawn_lens(shoot, f)
        (x0, y0), a0 = drawn_lens(shoot, AIM)
        print(f'make_flashlight: recoil {f}: lens {x + LENGTH * math.cos(a) - x0 - LENGTH * math.cos(a0):+.1f}, '
              f'{y + LENGTH * math.sin(a) - y0 - LENGTH * math.sin(a0):+.1f}, tilt {a - a0:+.2f}')
    for f, at_pose in enumerate(POSES):                  # ...and the blow
        if at_pose:
            (x, y), a = on_the_blow(at_pose)
            print(f'make_flashlight: blow {f}: lens {x + LENGTH * math.cos(a) - AIM_LENS_TAIL[0] - LENGTH:+.1f}, '
                  f'{y + LENGTH * math.sin(a) - AIM_LENS_TAIL[1]:+.1f}')
    for gun in ('', '_dual'):
        img = make_light_walk(load(OUT / f'light{gun}.png'), bool(gun))
        img.save(OUT / f'light_walk{gun}.png')
        print(f'make_flashlight: light_walk{gun} ({img.width} x {img.height})')
    make_shoot(shoot).save(OUT / 'shoot.png')            # Last: the others read it as dressed
    return 0


if __name__ == '__main__':
    sys.exit(main())
