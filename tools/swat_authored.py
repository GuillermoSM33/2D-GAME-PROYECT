"""Shared painted head and locomotion for the SWAT's native action drawings.

The body, sleeves, weapons and props are composed by swat_actions.py. Large
source paintings are preserved; normal rebuilding needs no image libraries.
"""
from make_sprites import Image, rgb
from make_swat import crop, paste
from swat_walk import BODY_MOTION

WAIST, W, H = 51, 81, 80
BREATH = (0, -1, -1, 0)


def connected_legs(legs, standing):
    """Share the pelvis under the belt; blend only the upper trouser rows.

    The old gait was attached at its changing thigh silhouette. Its hip
    center moved several pixels sideways independently of the belt. Knees,
    planted boots and the lower leg drawings stay in their original cells.
    """
    out = Image(legs.width, legs.height)
    out.px = list(legs.px)
    for f in range(8):
        for y in range(44, 50):
            old = [legs.get(f * 42 + x, y) for x in range(42)]
            base = [standing.get(x + 12, y + 7) for x in range(42)]
            old_x = [x for x, c in enumerate(old) if c[3]]
            base_x = [x for x, c in enumerate(base) if c[3]]
            if not old_x or not base_x:
                continue
            t = max(0, (y - 45) / 4)
            left = round(min(base_x) * (1 - t) + min(old_x) * t)
            right = round(max(base_x) * (1 - t) + max(old_x) * t)
            for x in range(42):
                color = (0, 0, 0, 0)
                if left <= x <= right:
                    source = base if t < .5 else old
                    bounds = base_x if t < .5 else old_x
                    u = (x - left) / max(1, right - left)
                    sx = round(min(bounds) + u * (max(bounds) - min(bounds)))
                    color = source[sx]
                out.set(f * 42 + x, y, color)
    return out


def canonical_head(base):
    head = crop(base, 0, 0, W, 32)
    for x, y, width in ((34, 16, 3), (39, 16, 2), (43, 17, 2)):
        for py in range(y - 1, y + 3):
            for px in range(x - 1, x + width + 1):
                edge = px in (x - 1, x + width) or py in (y - 1, y + 2)
                head.set(px, py, rgb(0x272c2d) if edge else rgb(0x93ae36))
        head.set(x, y, rgb(0xd4d990))
    return head


def walking(held, legs):
    out = Image(W * 12, H)
    for f in range(12):
        frame = Image(W, H)
        if f < 8:
            paste(frame, crop(legs, f * 42, 44, (f + 1) * 42, 67), 12, WAIST)
            dx, dy = BODY_MOTION[f]
        else:
            # One belt row overlaps the breathing torso. Moving the upper
            # half up without this leaves a transparent cut at the waist.
            paste(frame, crop(held, 0, WAIST - 1, W, H), 0, WAIST - 1)
            dx, dy = 0, BREATH[f - 8]
        paste(frame, crop(held, 0, 0, W, WAIST), dx, dy)
        paste(out, frame, f * W, 0)
    return out


def make(legs):
    from swat_actions import make as actions
    return actions(legs)
