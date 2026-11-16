"""SWAT actions on one complete body, with continuous sleeves and held props.

Native pixel drawings, shared equipment and authored projected arms. Source paintings
provide the helmet, collar, belt and boots; no horizontal crop replaces an arm
or a recoiling weapon with transparent pixels from another pose.
"""
import math

from make_sprites import Image, rgb
from make_swat import (ROOT, load, crop, paste, compose, Layer, ik, gun_layer,
                       rifle, shotgun, RIFLE_FLASH, SHOTGUN_FLASH, FLASH,
                       magazine_layer, shell_layer, jug_layer, JUMP_POSES, fold_legs)
from swat_materials import finish

W, H, WAIST = 81, 80, 51
NEAR, FAR = (24.0, 35.5), (39.0, 35.5)
UPPER, FORE = 8.5, 9.5
INK = rgb(0x252018)
CLOTH = [rgb(c) for c in (0x29343b, 0x363d40, 0x41494a, 0x5d6870, 0x697174)]
METAL = [rgb(c) for c in (0x272c2d, 0x41494a, 0x5d6870, 0x77807b)]
LENS = rgb(0xd4d990)
SOURCE = ROOT / 'docs/templates/swat/authored'


def polygon(image, points, color):
    """Fill a native-grid shape without antialiasing or partial alpha."""
    for y in range(math.floor(min(p[1] for p in points)), math.ceil(max(p[1] for p in points))):
        for x in range(math.floor(min(p[0] for p in points)), math.ceil(max(p[0] for p in points))):
            inside = False
            for a, b in zip(points, points[1:] + points[:1]):
                if (a[1] > y + .5) != (b[1] > y + .5):
                    cross = a[0] + (y + .5 - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                    if x + .5 < cross:
                        inside = not inside
            if inside:
                image.set(x, y, color)


def body_from_painting(base, head):
    body = Image(W, H)
    paste(body, head, 0, 0)
    # Complete ribcage behind BOTH sleeves, present even when the arms lift.
    polygon(body, [(25, 31), (38, 31), (42, 35), (43, 44), (41, 51),
                   (22, 51), (20, 43), (21, 36)], INK)
    polygon(body, [(25, 32), (37, 32), (40, 35), (41, 44), (39, 49),
                   (24, 49), (22, 43), (23, 36)], CLOTH[1])
    polygon(body, [(26, 34), (37, 34), (40, 37), (39, 45), (26, 46), (24, 40)], CLOTH[2])
    polygon(body, [(27, 35), (37, 35), (39, 37), (38, 40), (26, 40)], CLOTH[3])
    polygon(body, [(27, 36), (37, 36), (38, 38), (27, 38)], CLOTH[2])
    polygon(body, [(26, 41), (38, 41), (38, 44), (27, 44)], CLOTH[1])
    # Fabric seams, plate edge and a restrained upper-left highlight.
    for x in range(27, 37):
        body.set(x, 35, CLOTH[4] if x < 32 else CLOTH[3])
        body.set(x, 45, CLOTH[0])
    for y in range(35, 47):
        body.set(24, y, rgb(0x39312c))
        body.set(25, y, rgb(0x73553e) if y % 4 != 0 else rgb(0x967353))
    # Keep the painted collar, pouches, pelvis and soles, not a second stance.
    for y in range(30, 35):
        for x in range(27, 39):
            if base.get(x, y)[3]:
                body.set(x, y, base.get(x, y))
    for y in range(47, WAIST):
        for x in range(19, 43):
            body.set(x, y, base.get(x, y))
    paste(body, crop(base, 0, WAIST, W, H), 0, WAIST)
    # Far-hip bottle pouch, shared by every pose. The left hand can retrieve
    # its bottle on this side without crossing through the trigger arm.
    for y in range(46, 52):
        for x in range(38, 44):
            edge = x in (38, 43) or y in (46, 51)
            body.set(x, y, INK if edge else rgb(0x967353 if y == 47 else 0x73553e))
    return body


def sleeve(shoulder, wrist, near, elbow=None, *, corner_radius=0):
    from cowgirl_arm import arm_limb, glove, SLEEVE, GLOVE, INK as EDGE
    # Both IK solutions preserve bone lengths. Keep the elbow below the
    # shoulder when the support hand crosses back to a pouch or the bolt;
    # a fixed bend sign otherwise flips it up alongside the operator's face.
    if elbow is None:
        elbow = max((ik(shoulder, wrist, UPPER, FORE, bend) for bend in (-1, 1)), key=lambda p: p[1])
    # Broad upper sleeve, relaxed fabric at the elbow, fitted cuff. The same
    # cross-section is used in melee, reload, light and drinking poses.
    colors = (CLOTH[3], CLOTH[2], CLOTH[0]) if near else (CLOTH[2], CLOTH[1], CLOTH[0])
    mapping = dict(zip(SLEEVE, colors))
    mapping[EDGE] = INK
    pixels = arm_limb(shoulder, elbow, wrist, shoulder_radius=3.15, wrist_radius=2.15,
                      corner_radius=corner_radius)
    layer = Layer()
    layer.joints = shoulder, elbow, wrist
    layer.px = {p: mapping.get(c, c) for p, c in pixels.items()}
    # Two small fabric folds follow the upper arm, rather than a rigid ring.
    for t in (.30, .56):
        x = round(shoulder[0] + (elbow[0] - shoulder[0]) * t)
        y = round(shoulder[1] + (elbow[1] - shoulder[1]) * t)
        for dx, dy in ((-1, 0), (0, 0), (1, -1)):
            if (x + dx, y + dy) in layer.px:
                layer.px[x + dx, y + dy] = colors[0 if dy < 0 else 2]
    hand = Layer()
    mapping = {GLOVE[0]: CLOTH[2], GLOVE[1]: CLOTH[0], EDGE: INK}
    hand.px = {p: mapping.get(c, c) for p, c in glove(wrist, elbow, radius=2.05).items()}
    return layer, hand


def working_elbow(wrist, shoulder=FAR):
    """An authored projected elbow below the outside shoulder, not the chest.

    Perspective shortens the projected forearm when the hand comes towards
    the viewer. Forcing two fixed 2D bone lengths made that elbow flip above
    the shoulder or across the carrier during a reload.
    """
    return max(42.0, min(45.0, wrist[0] + 4)), min(46.5, max(39.5, wrist[1] + 3))


def forearm_front(arm):
    """Only the distal sleeve crosses in front of the carrier, never its root."""
    shoulder, elbow, wrist = arm.joints
    def distance(point, a, b):
        vx, vy = b[0] - a[0], b[1] - a[1]
        t = max(0, min(1, ((point[0] - a[0]) * vx + (point[1] - a[1]) * vy) / (vx * vx + vy * vy)))
        return (point[0] - a[0] - t * vx) ** 2 + (point[1] - a[1] - t * vy) ** 2
    front = Layer()
    front.px = {p: c for p, c in arm.px.items()
                if distance(p, elbow, wrist) < distance(p, shoulder, elbow)}
    return front


def equipment(kind, magazine=True, pump=0):
    pixels, grip, guard = rifle(magazine) if kind == 'rifle' else shotgun(pump)
    # A compact weapon on the original character's grid. Its receiver, stock,
    # handguard and rail light remain one rigid drawing in every action.
    scale = .75
    reduced = {}
    for y in range(-1, 11):
        for x in range(-9, 29):
            key = (math.floor((x + .5) / scale), y)
            if key in pixels:
                reduced[x, y] = pixels[key]
    return reduced, (grip[0] * scale, grip[1]), (guard[0] * scale, guard[1])


def weapon_pose(kind, grip_at, angle=0, magazine=True, pump=0, lit=False):
    pixels, grip, guard = equipment(kind, magazine, pump)
    weapon, point = gun_layer(pixels, angle, grip, grip_at)
    weapon.px = {p: finish_color(c) for p, c in weapon.px.items()}
    lens_at = point((19.5, 5.5))
    if lit:
        weapon.put(round(lens_at[0]), round(lens_at[1]), LENS)
    return weapon, point(guard), lens_at, point


def finish_color(color):
    from swat_materials import PALETTE
    return PALETTE.get(color, color)


def posed(body, kind, grip, angle, *, support=None, magazine=True, pump=0, lit=False, prop=None,
          support_elbow=None, shoulders=(NEAR, FAR)):
    weapon, guard, _, _ = weapon_pose(kind, grip, angle, magazine, pump, lit)
    wrist = support or guard
    if support_elbow is None and angle <= -12 and wrist[1] >= 39:
        support_elbow = working_elbow(wrist, shoulders[1])
    near, near_hand = sleeve(shoulders[0], grip, True)
    far, far_hand = sleeve(shoulders[1], wrist, False, support_elbow)
    parts = [far, (body, 0, 0), weapon, forearm_front(far), far_hand, near, near_hand]
    if prop:
        parts.append(prop)
    return compose(W, H, parts)


def atlas(frames):
    sheet = Image(W * len(frames), H)
    for f, drawing in enumerate(frames):
        paste(sheet, drawing, f * W, 0)
    return sheet


READY = ((34.0, 41.0), -18)
AIM = ((34.0, 36.0), 0)


def shots(body, kind, lit=False):
    poses = (READY, ((34, 39.5), -12), ((34, 37.5), -5), AIM, AIM,
             ((33, 36), 3 if kind == 'rifle' else 5), ((33, 36), 1), ((34, 39), -10))
    if lit:
        poses = (AIM, AIM, AIM, AIM, AIM, poses[5], poses[6], AIM)
    frames = [posed(body, kind, grip, angle, lit=lit) for grip, angle in poses]
    _, _, _, point = weapon_pose(kind, *AIM)
    # Flash and bullet leave the barrel, not the bayonet below it.
    origin = point((21.0, 3.0))
    mx, my = round(origin[0]) + 1, round(origin[1])
    flash = RIFLE_FLASH if kind == 'rifle' else SHOTGUN_FLASH
    for y, row in enumerate(flash):
        for x, c in enumerate(row):
            if c != '.':
                frames[4].set(mx + x, my - len(flash) // 2 + y, FLASH[c])
    return frames, (mx, my)


def reload(body, kind, ready):
    # Right hand stays on the trigger grip. The left support hand works below
    # the receiver, with its elbow on the same side throughout the sequence.
    grip, angle = READY
    _, guard, _, point = weapon_pose(kind, grip, angle)
    if kind == 'rifle':
        well = point((4.5, 8))
        hand_positions = (guard, well, (well[0], well[1] + 5), (32, 47),
                          (well[0], well[1] + 3), well, (well[0], well[1] - 2), guard)
        present = (True, True, False, False, False, True, True, True)
        held = (False, False, True, True, True, False, False, False)
    else:
        port = point((3.5, 6.5))
        hand_positions = (guard, (32, 47), port, (32, 47), port,
                          (32, 47), point((8, 5)), guard)
        present = (True,) * 8
        held = (False, True, True, True, True, True, False, False)
    frames, lower = [], []
    for f, wrist in enumerate(hand_positions):
        prop = None
        if held[f]:
            prop = magazine_layer(wrist) if kind == 'rifle' else shell_layer(wrist)
            prop.px = {p: finish_color(c) for p, c in prop.px.items()}
        drawing = posed(body, kind, grip, angle, support=wrist, magazine=present[f],
                        pump=3 if kind == 'shotgun' and f == 6 else 0, prop=prop,
                        support_elbow=working_elbow(wrist))
        foreground = Image(W, H)
        far, glove = sleeve(FAR, wrist, False, working_elbow(wrist))
        # Only the hand/forearm and held object cross the moving belt. Never
        # copy the planted pelvis or thigh into a walking reload.
        for part in (far, glove, prop):
            if part:
                for (x, y), c in part.px.items():
                    if y >= WAIST:
                        foreground.set(x, y, c)
        if f in (0, 7):
            drawing = crop(ready, 0, 0, W, H)
            foreground = Image(W, H)
        frames.append(drawing)
        lower.append(foreground)
    return frames, lower


MELEE_POSES = ((READY[0], READY[1], 0), ((31, 40), 12, -1), ((38, 38), 4, 1),
               ((44, 38), -4, 4), ((42, 40), -12, 3), ((36, 41), -10, 1),
               (READY[0], READY[1], 0))


def leaning(body, shift):
    """Transfer weight from the planted pelvis, preserving a continuous waist."""
    out = Image(W, H)
    for y in range(H):
        dx = round(shift * max(0, min(1, (WAIST - y) / 12)))
        for x in range(W):
            out.set(x + dx, y, body.get(x, y))
    return out


def melee(body, kind, ready):
    # Pull back, drive BOTH hands towards the opponent, follow through and
    # recover. The muzzle always points away from the head and chest.
    frames = []
    for grip, angle, shift in MELEE_POSES:
        shoulders = ((NEAR[0] + shift, NEAR[1]), (FAR[0] + shift, FAR[1]))
        frames.append(posed(leaning(body, shift), kind, grip, angle, shoulders=shoulders))
    frames[0] = crop(ready, 0, 0, W, H)
    frames[-1] = crop(ready, 0, 0, W, H)
    return frames


def light(body, kind):
    # Raise, move the support thumb to the rail switch, press it, return to
    # the handguard. The light comes on in frame 14, matching LIGHT_CLICK.
    frames = []
    for f in range(16):
        t = min(1, f / 6)
        t = t * t * (3 - 2 * t)
        grip = (34, 41 - 5 * t)
        angle = -18 * (1 - t)
        _, guard, lens, point = weapon_pose(kind, grip, angle)
        reach = (0, 0, 0, 0, 0, 0, 0, .25, .5, .75, 1, 1, 1, 1, .5, 0)[f]
        switch = point((17, 6))
        wrist = (guard[0] + (switch[0] - guard[0]) * reach,
                 guard[1] + (switch[1] - guard[1]) * reach)
        frames.append(posed(body, kind, grip, angle, support=wrist, lit=f >= 14))
    return frames


# Gun grip, gun angle, RIGHT wrist (None = trigger), LEFT wrist (None =
# handguard), bottle tilt (None = no bottle). Right hangs the rifle; left
# fetches the bottle; right removes the cap then returns to the rifle; left
# drinks/stows; right lifts the rifle and the two-handed hold returns.
DRINK_POSES = ((READY[0], READY[1], None, None, None),
               ((34, 42), -35, None, None, None),
               ((33, 41), -55, None, (41, 46), None),
               ((33, 40), -70, None, (40, 50), 0),
               ((33, 40), -70, (38, 41), (41, 45), 0),
               ((33, 40), -70, (40, 36), (41, 42), 0),
               ((33, 40), -70, (40, 32), (41, 42), 0),
               ((33, 40), -70, (37, 39), (42, 37), 25),
               ((33, 40), -70, None, (42, 32), 65),
               ((33, 40), -70, None, (40, 30), 100),
               ((33, 40), -70, None, (40, 30), 100),
               ((33, 40), -70, None, (43, 36), 45),
               ((33, 40), -70, None, (42, 43), 10),
               ((33, 40), -70, None, (40, 50), 0),
               ((34, 42), -40, None, (43, 44), None),
               (READY[0], READY[1], None, None, None))

DRINK_FRAME_COUNT = 2 * len(DRINK_POSES) - 1


def drink_samples(kind):
    """In-betweens keep wrist, held bottle and rifle on continuous paths."""
    def mix(a, b, t):
        if isinstance(a, tuple):
            return tuple(x + (y - x) * t for x, y in zip(a, b))
        return a + (b - a) * t
    for index in range(DRINK_FRAME_COUNT):
        phase = index / 2
        first = min(int(phase), len(DRINK_POSES) - 1)
        last = min(first + 1, len(DRINK_POSES) - 1)
        t = phase - first
        a, b = DRINK_POSES[first], DRINK_POSES[last]
        grip, angle = mix(a[0], b[0], t), mix(a[1], b[1], t)
        _, guard_a, _, _ = weapon_pose(kind, a[0], a[1])
        _, guard_b, _, _ = weapon_pose(kind, b[0], b[1])
        right = None if a[2] is None and b[2] is None else mix(a[2] or a[0], b[2] or b[0], t)
        left = None if a[3] is None and b[3] is None else mix(a[3] or guard_a, b[3] or guard_b, t)
        tilt = mix(a[4] or 0, b[4] or 0, t) if 2.5 <= phase <= 13.5 else None
        yield phase, grip, angle, right, left, tilt


def drink(body, kind, ready):
    frames, lower = [], []
    for f, grip, angle, right, left, tilt in drink_samples(kind):
        if left is None:
            frame = posed(body, kind, grip, angle)
            foreground = posed(Image(W, H), kind, grip, angle)
            frames.append(frame)
            lower.append(foreground)
            continue
        drawing = crop(body, 0, 0, W, H)
        # The rifle is now supported by its sling. Only the distal part of
        # the LEFT arm emerges in front of the body to fetch/lift the bottle.
        weapon, _, _, point = weapon_pose(kind, grip, angle)
        wrist = right or grip
        # The bottle arm stays outside the receiver's silhouette. Its elbow
        # rises as the wrist rises, so the forearm remains visible up to the
        # bottle instead of disappearing behind the trigger arm.
        elbow = (max(42, min(47, left[0] + 7)),
                 min(46.5, max(37.5, left[1] + 7.5)))
        far, far_glove = sleeve(FAR, left, False, elbow)
        near, glove = sleeve(NEAR, wrist, True, ik(NEAR, wrist, UPPER, FORE, 1))
        sling = Layer()
        attachment = point((-4, 4))
        for step in range(25):
            t = step / 24
            sling.put(round(27 + (attachment[0] - 27) * t),
                      round(34 + (attachment[1] - 34) * t), rgb(0x73553e))
        back = [far]
        props = [sling, weapon, near, glove, forearm_front(far)]
        if tilt is not None:
            at = (left[0] + 1, left[1] - 2)
            if f in (2.5, 13.5):
                at = (41, 49.5) # Neck emerges from / sinks behind the same pouch.
            bottle = jug_layer(at, tilt)
            opened = 5.5 <= f <= 13.5
            bottle.px = {p: rgb(0x9fb8b5) if c == rgb(0x9a643a) and opened
                         else finish_color(c) for p, c in bottle.px.items()}
            props.append(bottle)
        # Fingers close OVER the bottle's lower edge. Rendering the whole
        # bottle after this hand hid the contact and made it look suspended.
        props.append(far_glove)
        if 8 <= f <= 11:
            for x in (37, 38):
                drawing.set(x, 28, rgb(0xb98f71))
                drawing.set(x, 29, rgb(0xb98f71))
        frame = compose(W, H, [*back, (drawing, 0, 0), *props])
        if 5.5 <= f <= 8:
            # The detached cap stays visibly in the RIGHT hand as it lowers.
            frame.set(round(wrist[0] + 1), round(wrist[1] - 2), rgb(0x967353))
            frame.set(round(wrist[0] + 2), round(wrist[1] - 2), rgb(0x73553e))
        if 2.5 <= f <= 3 or 13 <= f <= 13.5:
            for y in range(47, WAIST):
                for x in range(38, 44):
                    if body.get(x, y)[3]:
                        frame.set(x, y, body.get(x, y))
        frames.append(frame)
        lower.append(compose(W, H, [*back, *props]))
    for foreground in lower:
        for y in range(WAIST):
            for x in range(W):
                foreground.set(x, y, (0, 0, 0, 0))
    return frames, lower


def jumping(body, kind, legs):
    # The jump template is narrower than an action frame. Tuck the rigid
    # weapon down and compose each cell separately so its barrel can never
    # leak into the next frame of the atlas.
    upper = posed(crop(body, 0, 0, W, WAIST), kind, (33, 40), -30)
    sheet = Image(54 * 8, 82)
    for f, (leg_frame, drop, fold) in enumerate(JUMP_POSES):
        tile = Image(54, 82)
        lower = fold_legs(crop(legs, leg_frame * 42, 0, (leg_frame + 1) * 42, 67), fold)
        paste(tile, crop(lower, 0, 44 + fold, 42, 67), 6, 52 + drop)
        paste(tile, upper, -6, 1 + drop)
        paste(sheet, tile, f * 54, 0)
    return sheet


def make(legs):
    from swat_authored import canonical_head, walking, connected_legs
    source = load(SOURCE / 'rifle.png')
    base = crop(source, 0, 0, W, H)
    head = canonical_head(base)
    # The head ends at the collar; all arms/weapons are drawn afterwards.
    head = crop(head, 0, 0, W, 32)
    body = body_from_painting(base, head)
    palette = sorted({c for c in source.px if c[3]})
    recolored = Image(legs.width, legs.height)
    for i, c in enumerate(legs.px):
        if c[3]:
            recolored.px[i] = min(palette, key=lambda p: sum((a - b) ** 2 for a, b in zip(c[:3], p[:3])))
    recolored = connected_legs(recolored, body)
    result = {'legs': recolored}
    parts = {'head_neck_authored': head, 'legs_authored': recolored, 'body_actions': body}
    origins = {}
    from swat_aux import throw_frames
    for kind, suffix in (('rifle', ''), ('shotgun', '_shotgun')):
        fire, origin = shots(body, kind)
        ready = fire[0]
        origins[kind] = origin
        result['shoot' + suffix] = atlas(fire)
        result['shoot' + suffix + '_lit'] = atlas(shots(body, kind, True)[0])
        result['carry' + suffix] = walking(ready, recolored)
        for prefix, rows in (('upper_', (0, WAIST)), ('lower_', (WAIST, H))):
            layers = []
            for pose in fire:
                layer = Image(W, H)
                paste(layer, crop(pose, 0, rows[0], W, rows[1]), 0, rows[0])
                layers.append(layer)
            parts[prefix + kind] = atlas(layers)
        reloading, lower = reload(body, kind, ready)
        result['reload' + suffix] = atlas(reloading)
        result['reload' + suffix + '_lower'] = atlas(lower)
        parts['reload_upper_' + kind] = atlas([crop(p, 0, 0, W, WAIST) for p in reloading])
        result['melee' + suffix] = atlas(melee(body, kind, ready))
        lights = light(body, kind)
        result['light' + suffix] = atlas(lights)
        result['light_walk' + suffix] = walking(lights[-1], recolored)
        drinks, drink_lower = drink(body, kind, ready)
        result['drink_' + kind] = atlas(drinks)
        result['drink_' + kind + '_lower'] = atlas(drink_lower)
        if kind == 'rifle':
            result['drink'] = atlas([drinks[f * 2] for f in (0, 4, 6, 9, 13, 15)])
        result['jump' + suffix] = jumping(body, kind, recolored)
        result['throw' + suffix] = atlas(throw_frames(body, kind, ready))
    carry = result['carry']
    result['stand'] = crop(carry, 8 * W + 12, 7, 8 * W + 54, 74)
    narrow = Image(336, 67)
    for f in range(8):
        paste(narrow, crop(carry, f * W + 12, 7, f * W + 54, 74), 42 * f, 0)
    result['walk'] = narrow
    return result, parts, origins
