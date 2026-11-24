#!/usr/bin/env python3
"""The sheriff's single-cylinder reload, on the shared three-quarter body.

As in the reference (objetivo/reload.gif): the barrel comes upright beside her face on
her far arm, its root behind her far lapel; her near hand leaves her hip and crosses in
front of her to the open cylinder, from below. Both upper arms stay attached to the same
shoulders as every other pose and neither bone stretches. Native RGBA material tags,
standard library only.
"""
from __future__ import annotations

import math

from cowgirl_arm import GRIP_AT, arm_limb, glove, pistol_pointing, turned
from make_sprites import rgb


SHOULDER = (41.0, 37.0)
HELPER_SHOULDER = (27.0, 37.0)
ARM_BONE = 6.5
HELPER_BONE = 7.5
INK = rgb(0x252018)
STEEL = (rgb(0xb3b8b6), rgb(0x777e85), rgb(0x4c535b))
BRASS = (rgb(0xb59050), rgb(0x8e6c28))
# The centre of the fluted cylinder in make_revolver.GUN, before it swings out.
CYLINDER_AT = (4.5, 4.0)
CHAMBERS = ((-1, -1), (0, -1), (1, -1), (1, 0),
            (1, 1), (0, 1), (-1, 1), (-1, 0))
# Wrist, barrel angle, helper target. None reaches the cylinder from below;
# a tuple reaches the belt or moves the hand toward the action.
KEYS = (
    ((49.0, 41.0), 58.0, (27.5, 47.0)),
    ((47.5, 39.0), 76.0, (34.0, 43.0)),
    ((47.0, 38.0), 82.0, None),
    ((47.0, 38.0), 82.0, (34.0, 47.0)),
    ((47.0, 38.0), 82.0, None),
    ((47.5, 39.0), 76.0, None),
    ((50.5, 37.5), 28.0, (33.0, 46.0)),
)
DEEPER = {rgb(0x6c7a84): rgb(0x505c66), rgb(0x505c66): rgb(0x38424a)}   # Her far upper arm, away from the light


def bones(top: tuple, want: tuple, bone: float) -> tuple:
    """Two fixed-length bones, elbow consistently on the lower side.

    Keep floating point joints until rasterization. The target clamp protects
    the pose if one of the small authored reaches is adjusted later.
    """
    dx, dy = want[0] - top[0], want[1] - top[1]
    distance = max(math.hypot(dx, dy), 1e-9)
    reach = min(2 * bone - .15, max(.5, distance))
    ux, uy = dx / distance, dy / distance
    wrist = (top[0] + reach * ux, top[1] + reach * uy)
    half = reach / 2
    offset = math.sqrt(max(0.0, bone * bone - half * half))
    elbow = (top[0] + ux * half - uy * offset,
             top[1] + uy * half + ux * offset)
    return elbow, wrist


def cylinder_position(wrist: tuple, angle: float, opened: bool = True) -> tuple:
    """The real gun's cylinder, with its hinge swinging one pixel outward."""
    dx, dy = turned((CYLINDER_AT[0] - GRIP_AT[0],
                     CYLINDER_AT[1] - GRIP_AT[1]), round(angle))
    return (math.floor(wrist[0]) + dx - int(opened),
            math.floor(wrist[1]) + dy)


def joints(frame: int) -> tuple:
    """Shoulder/elbow/wrist triples and the barrel angle for a reload key."""
    want, angle, helper = KEYS[frame]
    elbow, wrist = bones(SHOULDER, want, ARM_BONE)
    cylinder = cylinder_position(wrist, angle)
    if helper is None:
        helper = (cylinder[0] - 2.5, cylinder[1] + 3.0)
    helper_elbow, helper_wrist = bones(HELPER_SHOULDER, helper, HELPER_BONE)
    return ((SHOULDER, elbow, wrist),
            (HELPER_SHOULDER, helper_elbow, helper_wrist), angle)


def open_cylinder(at: tuple, loaded: bool) -> dict:
    """A compact five-pixel cylinder face with eight chambers and an axle."""
    cx, cy = (round(value) for value in at)
    pixels = {}
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 5:
                pixels[(cx + dx, cy + dy)] = STEEL[0 if dx + dy < 0 else 2]
    for dx, dy in CHAMBERS:
        pixels[(cx + dx, cy + dy)] = BRASS[0] if loaded else INK
    pixels[(cx, cy)] = STEEL[1]
    return pixels


def single_reload_frames(body: dict, aim: dict) -> list[dict]:
    """Seven reload keys followed by the exact incoming aimed pose.

    ``body`` has no arms, but retains the shared torso, head and planted feet.
    This function only adds the arm/weapon action; it never moves that body.
    """
    from make_melee import behind, behind_arm
    frames = []
    for frame in range(len(KEYS)):
        gun_arm, helper_arm, angle = joints(frame)
        top, elbow, wrist = gun_arm
        helper_top, helper_elbow, helper_wrist = helper_arm
        # Her gun arm's root is behind her far lapel; its forearm, at her side,
        # and the gun are in front of nothing but her hair and the hat's edge.
        limb = {p: DEEPER.get(c, c) if math.dist(p, top) < 3.5 else c
                for p, c in arm_limb(top, elbow, wrist, corner_radius=1.0).items()}
        helper_limb = arm_limb(helper_top, helper_elbow, helper_wrist, corner_radius=1.0)
        pixels = behind(limb, behind_arm(body, helper_limb))
        pixels.update({p: c for p, c in limb.items() if math.dist(p, wrist) < ARM_BONE - .5})
        pixels.update(pistol_pointing(wrist, angle))
        pixels.update(glove(wrist, elbow))
        pixels.update(helper_limb)                       # Nearest to us: in front of her
        cylinder = cylinder_position(wrist, angle)
        if 1 <= frame <= 5:
            pixels.update(open_cylinder(cylinder, loaded=frame >= 4))
        if frame == 2:
            # Three spent cases fall away from the open cylinder, in separate
            # trajectories; these are the only deliberately detached pixels.
            cx, cy = (round(value) for value in cylinder)
            for dx, dy in ((2, 5), (5, 7), (7, 4)):
                pixels[(cx + dx, cy + dy)] = BRASS[0]
                pixels[(cx + dx, cy + dy + 1)] = BRASS[1]
        if frame == 4:
            # The speedloader is held at the cylinder's lower-left lip rather
            # than drawn as a second free-floating metal wheel.
            cx, cy = (round(value) for value in cylinder)
            for dx in (-2, -1, 0):
                pixels[(cx + dx, cy + 2)] = BRASS[0]
            pixels[(cx - 1, cy + 3)] = STEEL[2]
        pixels.update(glove(helper_wrist, helper_elbow))
        frames.append(pixels)
    frames.append(dict(aim))
    return frames
