"""One fitted SWAT body, carried by the walk's original leg poses.

Head, neck and carrier move together. Idle and aimed poses use the same
body pixels and sleeve model; raising the rifle never changes the trunk.
"""
import math
from make_sprites import Image
from swat_body import WAIST, NEAR_SHOULDER, FAR_SHOULDER, UPPER_ARM, FOREARM, proportions

# A single native-pixel weight shift. Passing poses lift the whole upper body;
# contact poses settle it. The head is never placed independently of the neck.
BODY_MOTION = ((0, 1), (0, 0), (1, 0), (1, 1),
               (0, 1), (0, 0), (-1, 0), (-1, 1))

# The bitmap's old hands overlap the top four trouser rows. These masks
# separate those hands from the authored thighs; knees, shins and boots keep
# their original shape. Bounds are inclusive, on the unscaled source grid.
HIP_BOUNDS = (
    ((14, 29), (13, 29), (12, 30), (11, 30)),
    ((12, 27), (12, 27), (12, 27), (10, 28)),
    ((12, 29), (13, 29), (12, 28), (10, 28)),
    ((10, 30), (9, 32), (8, 33), (6, 33)),
    ((11, 30), (10, 31), (9, 32), (8, 33)),
    ((14, 26), (13, 26), (12, 27), (11, 27)),
    ((13, 27), (14, 27), (15, 29), (15, 29)),
    ((15, 29), (14, 29), (13, 29), (13, 29)),
)


def relaxed_joints(near, phase=None, offset=(0, 0)):
    joint = NEAR_SHOULDER if near else FAR_SHOULDER
    sign = 1 if near else -1
    shoulder = joint[0] + offset[0], joint[1] + offset[1]
    cycle = 0 if phase is None else 2 * math.pi * phase / 8
    swing = 0 if phase is None else -10 * sign * math.cos(cycle)
    follow = 0 if phase is None else -4 * sign * math.sin(cycle)
    if phase is None:
        # At rest the hands settle beside the belt; the same long segments
        # unfold during locomotion and when shouldering the rifle.
        upper_rest, fore_rest = (-42, 30) if near else (40, -32)
    else:
        upper_rest, fore_rest = (-34, 20) if near else (24, -12)
    upper = math.radians(upper_rest + swing)
    fore = math.radians(fore_rest + swing + follow)
    # Forward kinematics keeps both lengths invariant, with a small delayed
    # elbow flex instead of rotating one rigid sleeve from the shoulder.
    elbow = shoulder[0] + UPPER_ARM * math.sin(upper), shoulder[1] + UPPER_ARM * math.cos(upper)
    hand = elbow[0] + FOREARM * math.sin(fore), elbow[1] + FOREARM * math.cos(fore)
    return shoulder, elbow, hand


def relaxed_arm(near, phase=None, offset=(0, 0)):
    from make_swat import arm
    shoulder, elbow, hand = relaxed_joints(near, phase, offset)
    return arm(shoulder, hand, near, elbow=elbow)


def make_stand(walk=None, drawing=None):
    from make_swat import standing_body, compose
    body = standing_body()
    return compose(42, 67, [relaxed_arm(False), (body, 0, 0), relaxed_arm(True)])


def walk_layers(source):
    """Body, near sleeve and far sleeve on three aligned transparent atlases."""
    from make_swat import standing_body, crop, paste, compose
    clean = Image(source.width, source.height)
    clean.px = list(source.px)
    for f, rows in enumerate(HIP_BOUNDS):
        for y, (left, right) in enumerate(rows, WAIST):
            for x in range(42):
                if not left <= x <= right:
                    clean.set(f * 42 + x, y, (0, 0, 0, 0))
    legs = proportions(clean)
    upper = crop(standing_body(), 0, 0, 42, WAIST)
    body = Image(336, 67)
    near = Image(336, 67)
    far = Image(336, 67)
    for f, (dx, dy) in enumerate(BODY_MOTION):
        lower = crop(legs, f * 42, WAIST, (f + 1) * 42, 67)
        paste(body, compose(42, 67, [(lower, 0, WAIST), (upper, dx, dy)]), f * 42, 0)
        paste(near, compose(42, 67, [relaxed_arm(True, f, (dx, dy))]), f * 42, 0)
        paste(far, compose(42, 67, [relaxed_arm(False, f, (dx, dy))]), f * 42, 0)
    return body, near, far


def make_walk(source, no_arms=False):
    from make_swat import paste
    body, near, far = walk_layers(source)
    if no_arms:
        return body
    image = Image(336, 67)
    for part in (far, body, near):
        paste(image, part, 0, 0)
    return image


def rig_parts(source):
    """Authoring parts used in the final composition, with the same pivots."""
    from make_swat import (standing_body, compose, paste, shoot_frames, rifle, shotgun,
                           RIFLE_FLASH, SHOTGUN_FLASH)
    body = standing_body()
    head, torso = Image(42, 67), Image(42, 67)
    for y in range(WAIST):
        for x in range(42):
            (head if y < 27 else torso).set(x, y, body.get(x, y))
    walk_body, near, far = walk_layers(source)
    legs = Image(336, 67)
    for y in range(WAIST, 67):
        for x in range(336):
            legs.set(x, y, walk_body.get(x, y))
    parts = {'body': body, 'head_neck': head, 'torso': torso, 'legs_walk': legs,
             'arm_near_idle': compose(42, 67, [relaxed_arm(True)]),
             'arm_far_idle': compose(42, 67, [relaxed_arm(False)]),
             'body_walk': walk_body, 'arm_near_walk': near, 'arm_far_walk': far}
    for name, gun, flash, kick in (('rifle', rifle(), RIFLE_FLASH, 2),
                                  ('shotgun', shotgun(), SHOTGUN_FLASH, 3)):
        near_sheet, far_sheet, weapon_sheet = (Image(81 * 8, 80) for _ in range(3))
        for f, (_, near, far, weapon) in enumerate(shoot_frames(body, gun, flash, kick)):
            paste(near_sheet, compose(81, 80, [near]), f * 81, 0)
            paste(far_sheet, compose(81, 80, [far]), f * 81, 0)
            paste(weapon_sheet, weapon, f * 81, 0)
        parts.update({'arm_near_' + name: near_sheet, 'arm_far_' + name: far_sheet,
                      'weapon_' + name: weapon_sheet})
    return parts


def make_light_walk(walk, light):
    """The held gun, head and carrier share the walking weight shift."""
    from make_flashlight import BREATH
    image = Image(81 * 12, 80)
    seam = WAIST + 7
    held = {(x, y): light.get(light.width - 81 + x, y)
            for y in range(80) for x in range(81)
            if light.get(light.width - 81 + x, y)[3]}
    for f in range(12):
        if f < 8:
            lower = {(x + 12, y + 7): walk.get(f * 42 + x, y)
                     for y in range(WAIST, 67) for x in range(42)
                     if walk.get(f * 42 + x, y)[3]}
            dx, dy = BODY_MOTION[f]
        else:
            lower = {p: c for p, c in held.items() if p[1] >= seam}
            dx, dy = 0, BREATH[f - 8]
        lower.update({(x + dx, y + dy): c for (x, y), c in held.items() if y < seam})
        for (x, y), color in lower.items():
            image.set(f * 81 + x, y, color)
    return image
