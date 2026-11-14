"""Compose the painted sleeves and weapons with shared head and moving legs.

No limb stretching or per-frame head replacement in the renderer. The native
paintings are committed sources; this deterministic build needs no Pillow.
"""
from make_sprites import Image, rgb
from make_swat import (ROOT, load, crop, paste, FLASH, RIFLE_FLASH, SHOTGUN_FLASH,
                       JUMP_POSES, fold_legs)
from swat_walk import BODY_MOTION

SOURCE = ROOT / 'docs/templates/swat/authored'
WAIST = 51  # action row; walk row 44, seven rows higher
W, H = 81, 80
BREATH = (0, -1, -1, 0)


def frame(sheet, f):
    return crop(sheet, f * W, 0, (f + 1) * W, H)


def atlas(frames):
    out = Image(W * len(frames), H)
    for f, drawing in enumerate(frames):
        paste(out, drawing, f * W, 0)
    return out


def replace_rows(dst, src, y0, y1):
    for y in range(y0, y1):
        for x in range(W):
            dst.set(x, y, src.get(x, y))


def canonical_head(base):
    head = crop(base, 0, 0, W, 32)
    # Preserve three distinct lenses on the tiny game grid, including a dark
    # pixel between adjacent tubes. They follow the whole upper-body layer.
    for x, y, width in ((34, 16, 3), (39, 16, 2), (43, 17, 2)):
        for py in range(y - 1, y + 3):
            for px in range(x - 1, x + width + 1):
                edge = px in (x - 1, x + width) or py in (y - 1, y + 2)
                head.set(px, py, rgb(0x272c2d) if edge else rgb(0x93ae36))
        head.set(x, y, rgb(0xd4d990))
    return head


def normalized(sheet, base, head, foreground=None):
    frames = []
    for f in range(8):
        drawing = frame(sheet, f)
        lower = crop(drawing, 0, WAIST, W, H)
        replace_rows(drawing, base, WAIST, H)
        if foreground and f in foreground:
            left, top, right, bottom = foreground[f]
            for y in range(max(top, WAIST), bottom):
                for x in range(left, right):
                    c = lower.get(x, y - WAIST)
                    if c[3]:
                        drawing.set(x, y, c)
        # The recoiling barrel rises beside the face. Replace only the head's
        # columns, otherwise the shared-head crop would erase that barrel.
        for y in range(32):
            for x in range(46):
                drawing.set(x, y, head.get(x, y))
        frames.append(drawing)
    return frames


def walking(held, legs):
    frames = []
    for f in range(12):
        out = Image(W, H)
        if f < 8:
            paste(out, crop(legs, f * 42, 44, (f + 1) * 42, 67), 12, WAIST)
            dx, dy = BODY_MOTION[f]
        else:
            paste(out, crop(held, 0, WAIST, W, H), 0, WAIST)
            dx, dy = 0, BREATH[f - 8]
        paste(out, crop(held, 0, 0, W, WAIST), dx, dy)
        frames.append(out)
    return atlas(frames)


def muzzle(drawing):
    """Rightmost barrel pixel (the head and arms are well left of this)."""
    points = [(x, y) for y in range(25, 51) for x in range(48, W) if drawing.get(x, y)[3]]
    x = max(p[0] for p in points)
    ys = [p[1] for p in points if p[0] == x]
    return x, round(sum(ys) / len(ys))


def add_flash(drawing, rows, origin):
    mx, my = origin
    for j, line in enumerate(rows):
        for i, char in enumerate(line):
            if char != '.':
                drawing.set(mx + 1 + i, my - len(rows) // 2 + j, FLASH[char])


def light_pose(drawing, on):
    out = crop(drawing, 0, 0, W, H)
    mx, my = muzzle(out)
    # Small rail-mounted light under the muzzle; the beam uses this origin.
    for x in range(mx - 4, mx):
        for y in range(my + 2, my + 4):
            out.set(x, y, rgb(0x272c2d if y == my + 3 else 0x5d6870))
    out.set(mx - 1, my + 2, rgb(0xd4d990 if on else 0x77807b))
    return out


def make(legs):
    sources = {n: load(SOURCE / (n + '.png')) for n in
               ('rifle', 'shotgun', 'rifle_reload', 'shotgun_reload')}
    base = frame(sources['rifle'], 0)
    head = canonical_head(base)
    result, parts, origins = {}, {'head_neck_authored': head}, {}
    palette = sorted({c for c in sources['rifle'].px if c[3]})
    # The existing eight planted/passing leg drawings keep their geometry.
    # Match their fabric shades to the painted upper half before composing.
    recolored = Image(legs.width, legs.height)
    for i, c in enumerate(legs.px):
        if c[3]:
            recolored.px[i] = min(palette, key=lambda p: sum((a-b)**2 for a, b in zip(c[:3], p[:3])))
    parts['legs_authored'] = recolored
    result['legs'] = recolored
    for name, suffix, flash in (('rifle', '', RIFLE_FLASH), ('shotgun', '_shotgun', SHOTGUN_FLASH)):
        poses = normalized(sources[name], base, head)
        poses[4] = crop(poses[3], 0, 0, W, H)
        poses[6] = crop(poses[3], 0, 0, W, H)
        poses[7] = crop(poses[1], 0, 0, W, H)
        origin = muzzle(poses[3])
        origins[name] = origin
        parts['upper_' + name] = atlas([crop(p, 0, 0, W, WAIST) for p in poses])
        # Export each pose's lower and upper separately on the same template.
        parts['lower_' + name] = atlas([crop(p, 0, 0, W, H) for p in poses])
        for y in range(WAIST):
            for x in range(parts['lower_' + name].width):
                parts['lower_' + name].set(x, y, (0, 0, 0, 0))
        result['carry' + suffix] = walking(poses[0], recolored)
        jump = Image(54 * 8, 82)
        for f, (leg_frame, drop, fold) in enumerate(JUMP_POSES):
            lower = fold_legs(crop(recolored, leg_frame * 42, 0, (leg_frame + 1) * 42, 67), fold)
            paste(jump, crop(lower, 0, 44 + fold, 42, 67), f * 54 + 6, 52 + drop)
            paste(jump, crop(poses[0], 0, 0, W, WAIST), f * 54 - 6, 1 + drop)
        result['jump' + suffix] = jump
        result['shoot' + suffix] = atlas(poses)
        add_flash(result['shoot' + suffix], flash, (origin[0] + 4 * W, origin[1]))
        lit_shots = [light_pose(poses[5] if f == 5 else poses[3], True) for f in range(8)]
        result['shoot' + suffix + '_lit'] = atlas(lit_shots)
        add_flash(result['shoot' + suffix + '_lit'], flash, (origin[0] + 4 * W, origin[1]))
        # The magazine in frame 2 extends beyond the hip. This tight mask
        # retains the hand/magazine only, never a static thigh over moving legs.
        foreground = {2: (40, 51, 47, 56)} if name == 'rifle' else {}
        reloads = normalized(sources[name + '_reload'], base, head, foreground)
        reloads[0] = crop(poses[0], 0, 0, W, H)
        reloads[7] = crop(poses[0], 0, 0, W, H)
        result['reload' + suffix] = atlas(reloads)
        low = Image(W * 8, H)
        for f, (left, top, right, bottom) in foreground.items():
            for y in range(top, bottom):
                for x in range(left, right):
                    low.set(f * W + x, y, reloads[f].get(x, y))
        result['reload' + suffix + '_lower'] = low
        parts['reload_upper_' + name] = atlas([crop(p, 0, 0, W, WAIST) for p in reloads])
        lit = [light_pose(poses[min(3, f // 3)], f >= 13) for f in range(16)]
        result['light' + suffix] = atlas(lit)
        result['light_walk' + suffix] = walking(lit[-1], recolored)
    # The narrow walk template remains available for utility poses and traps.
    # Normal armed locomotion is drawn from the full-width carry atlas.
    carry = result['carry']
    result['stand'] = crop(carry, 8 * W + 12, 7, 8 * W + 54, 74)
    narrow = Image(336, 67)
    for f in range(8):
        paste(narrow, crop(carry, f * W + 12, 7, f * W + 54, 74), 42 * f, 0)
    result['walk'] = narrow
    return result, parts, origins
