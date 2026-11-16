"""Equipment handling with the same body, sleeves and guns as SWAT's main actions."""
from make_sprites import Image, rgb
from make_swat import Layer, compose, crop, paste, magazine_layer, shell_layer, ring_layer
from swat_actions import (W, H, NEAR, FAR, READY, sleeve, forearm_front,
                          weapon_pose, working_elbow, leaning, polygon, INK, CLOTH, finish_color)


# Right wrist, left wrist (None = weapon grip/handguard), body lean.
THROW_HANDS = ((None, None, 0), (None, None, 0), (None, None, 0), (None, (43, 45), 0),
               ((35, 43), None, 0), ((28, 46), None, 0), ((23, 47), None, 0),
               ((26, 43), (33, 39), 0), ((28, 39), (31, 36), 0),
               ((28, 38), (35, 35), 0), ((25, 39), (38, 40), -1),
               ((19, 43), None, -1), ((17, 45), None, -2),
               ((23, 47), None, -1), ((35, 43), None, 0),
               ((45, 34), None, 3), ((45, 29), None, 4),
               ((42, 33), None, 2), ((37, 39), None, 1), ((36, 42), None, 0),
               (None, None, 0), (None, None, 0), (None, None, 0), (None, None, 0))
THROW_RELEASE = 15


def held_grenade(wrist):
    """Olive body above the palm; the glove closes on its lower edge."""
    from ui_icons import grenade_frames
    cx, cy = wrist[0] + 1, wrist[1] - 2
    layer = Layer()
    layer.px = {(x + round(cx - 4), y + round(cy - 4)): c
                for (x, y), c in grenade_frames()[0].items()}
    return layer


def throw_frames(body, kind, ready):
    frames = []
    for f, (right, left, shift) in enumerate(THROW_HANDS):
        grip, angle = ((40, 42), -70)
        if f < 4:
            grip, angle = (((34, 41), -18), ((35, 41), -28),
                           ((38, 42), -45), ((40, 42), -60))[f]
        elif f >= 21:
            grip, angle = (((38, 42), -50), ((35, 41), -32), READY)[f - 21]
        weapon, guard, _, point = weapon_pose(kind, grip, angle)
        right, left = right or grip, left or (guard if f < 4 or f >= 21 else grip)
        shoulders = ((NEAR[0] + shift, NEAR[1]), (FAR[0] + shift, FAR[1]))
        if f == 19:
            left = tuple((a + b) / 2 for a, b in zip(grip, guard))
        elif f == 20:
            left = guard
        elbows = {11: (15, 37), 12: (14, 38), 13: (17, 42),
                  14: (27, 42), 15: (36, 36), 16: (35, 31)}
        near, glove = sleeve(shoulders[0], right, True, elbows.get(f))
        far, far_glove = sleeve(shoulders[1], left, False, working_elbow(left))
        sling = Layer()
        attachment = point((-4, 4))
        for n in range(25):
            t = n / 24
            sling.put(round(27 + (attachment[0] - 27) * t),
                      round(34 + (attachment[1] - 34) * t), rgb(0x73553e))
        parts = [far, (leaning(body, shift), 0, 0)]
        if 3 <= f <= 21:
            parts.append(sling)
        parts += [weapon, forearm_front(far), far_glove, near]
        parts.append(glove)
        if 6 <= f < THROW_RELEASE:
            parts.append(held_grenade(right))
            fingers = Layer()
            fingers.px = {p: c for p, c in glove.px.items()
                          if p[1] >= round(right[1] - 1) and right[0] - 1 <= p[0] <= right[0] + 2}
            parts.append(fingers)
        if f in (9, 10):
            parts.append(ring_layer(left))
        frame = compose(W, H, parts)
        # The grenade emerges from the near belt pouch; it never appears at
        # chest height or gets baked into a frame after the real release.
        if f == 6:
            for y in range(46, 51):
                for x in range(19, 26):
                    if body.get(x, y)[3]:
                        frame.set(x, y, body.get(x, y))
        frames.append(frame)
    frames[0] = crop(ready, 0, 0, W, H)
    frames[-1] = crop(ready, 0, 0, W, H)
    return frames


SIT_DOWN_FRAMES, SIT_RELOAD_FRAMES = 8, 24
SIT_W, SIT_H = 72, 67
PARK = {'rifle': ((12, 39), -55), 'shotgun': ((60, 38), -125)}
LAP = ((31, 45), -5)


def seated_body(body, settle=1, breath=0, nod=0):
    """Hips descend onto the seat; planted boots and foreshortened thighs join them."""
    drawing = Image(SIT_W, SIT_H)
    dy = -7 + round(5 * settle)
    hip = 44 + round(5 * settle)
    # Full pelvis, then separate thighs and bent shins; the waist stays filled.
    polygon(drawing, [(26, hip - 1), (46, hip - 1), (48, 51), (44, 54), (27, 54), (24, 51)], INK)
    polygon(drawing, [(27, hip), (45, hip), (46, 51), (43, 53), (28, 53), (26, 51)], CLOTH[1])
    for x in (26, 40):
        polygon(drawing, [(x, hip + 1), (x + 7, hip + 1), (x + 8, 53),
                          (x + 5, 57), (x - 2, 57), (x - 2, 53)], INK)
        polygon(drawing, [(x + 1, hip + 2), (x + 6, hip + 2), (x + 6, 53),
                          (x + 4, 56), (x - 1, 56), (x, 53)], CLOTH[2])
        polygon(drawing, [(x + 1, 50), (x + 5, 50), (x + 6, 52),
                          (x + 4, 54), (x, 54), (x - 1, 52)], CLOTH[3])
        for px in range(x + 1, x + 5):
            drawing.set(px, 51, CLOTH[4])
    # The same boot clusters as standing, fixed on the ground through descent.
    paste(drawing, crop(body, 0, 63, W, 68), 4, 56)
    for y in range(51):
        for x in range(W):
            c = body.get(x, y)
            if c[3]:
                drawing.set(x + 4, y + dy + breath + (nod if y < 32 else 0), c)
    return drawing, ((28, 35.5 + dy + breath), (43, 35.5 + dy + breath))


def seated_elbow(shoulder, wrist, near):
    """One continuous projected bend, with the elbow hanging below its shoulder.

    Reaching past the hip opens that same bend. It never selects the other
    IK solution when a wrist crosses a column or moves above the lap.
    """
    import math
    side = -1 if near else 1
    dx, dy = wrist[0] - shoulder[0], wrist[1] - shoulder[1]
    outward = side * dx
    t = max(0, min(1, (abs(dx) - 3) / (13 if outward > 0 else 9)))
    relaxed = shoulder[0] + side * 3, shoulder[1] + 8.5
    opened = shoulder[0] + dx / 2, shoulder[1] + dy / 2 + 3
    point = tuple(a + (b - a) * t for a, b in zip(relaxed, opened))
    # Perspective may shorten a segment, but must never stretch either one.
    for _ in range(64):
        for origin, limit in ((shoulder, 9.5), (wrist, 10.0)):
            distance = math.dist(origin, point)
            if distance > limit:
                point = tuple(a + (b - a) * limit / distance for a, b in zip(origin, point))
        distance = math.dist(wrist, point)
        if 0 < distance < 6:
            point = tuple(a + (b - a) * 6 / distance for a, b in zip(wrist, point))
    return point


def seated_pose(body, poses, near_wrist, far_wrist, *, settle=1, breath=0, nod=0,
                active=None, magazine=True, pump=0, prop=None, concealed=None):
    drawing, shoulders = seated_body(body, settle, breath, nod)
    near, glove = sleeve(shoulders[0], near_wrist, True, seated_elbow(shoulders[0], near_wrist, True), corner_radius=2)
    far, far_glove = sleeve(shoulders[1], far_wrist, False, seated_elbow(shoulders[1], far_wrist, False), corner_radius=2)
    back, front = [far], []
    for kind, (grip, angle) in poses.items():
        gun, _, _, _ = weapon_pose(kind, grip, angle, magazine if kind == 'rifle' else True,
                                    pump if kind == 'shotgun' else 0)
        if concealed == kind:
            gun.px = {p: c for p, c in gun.px.items() if p[1] < 45}
        (front if kind == active else back).append(gun)
    parts = [*back, (drawing, 0, 0), *front, forearm_front(far), near, glove]
    if prop:
        parts.append(prop)
    parts.append(far_glove)
    return compose(SIT_W, SIT_H, parts)


def sit_down(body, kind):
    """Park each carried gun with a hand, then sit with both hands on the knees."""
    if kind == 'rifle':
        plans = [
            ({'rifle': ((38, 34), -18)}, (38, 34), (49, 36), 'rifle'),
            ({'rifle': ((38, 36), -25), 'shotgun': ((44, 35), -90)}, (38, 36), (44, 35), 'rifle'),
            ({'rifle': ((35, 40), -20), 'shotgun': ((50, 34), -100)}, (35, 40), (50, 34), 'rifle'),
            ({'rifle': LAP, 'shotgun': PARK['shotgun']}, LAP[0], PARK['shotgun'][0], 'rifle'),
            ({'rifle': ((22, 40), -35), 'shotgun': PARK['shotgun']}, (22, 40), (51.5, 43.5), 'rifle'),
            (PARK, PARK['rifle'][0], (43, 49), None),
            (PARK, (20.5, 44), (43, 49), None),
            (PARK, (29, 49), (43, 49), None)]
    else:
        plans = [
            ({'shotgun': ((38, 34), -18)}, (38, 34), (50, 36), 'shotgun'),
            ({'shotgun': ((39, 36), -25), 'rifle': ((26, 42), -90)}, (26, 42), (39, 36), 'shotgun'),
            ({'shotgun': ((50, 37), -125), 'rifle': ((20, 40), -45)}, (20, 40), (50, 37), None),
            (PARK, PARK['rifle'][0], PARK['shotgun'][0], None),
            (PARK, (20.5, 44), (51.5, 43.5), None),
            (PARK, (29, 49), (43, 49), None),
            (PARK, (29, 49), (43, 49), None),
            (PARK, (29, 49), (43, 49), None)]
    return [seated_pose(body, poses, near, far, settle=min(1, f / 4), active=active,
                        concealed=('shotgun' if kind == 'rifle' else 'rifle') if f == 1 else None)
            for f, (poses, near, far, active) in enumerate(plans)]


def seated_reload(body, kind):
    frames = []
    grip, angle = LAP
    _, guard, _, point = weapon_pose(kind, grip, angle)
    well = point((4.5, 8) if kind == 'rifle' else (3.5, 6.5))
    if kind == 'shotgun':
        well = well[0], well[1] + 2 # Palm below the port; cartridge lies above the fingers.
    pouch = (39, 46) if kind == 'rifle' else (43, 48)
    if kind == 'rifle':
        left = {5: well, 6: (well[0], well[1] + 1.5), 7: (well[0], well[1] + 2.5),
                8: (38, 48), 9: pouch, 10: (40, 45), 11: (38, 44),
                12: (well[0], well[1] + 2.5), 13: (well[0], well[1] + 1),
                14: well, 15: well, 16: point((2, 3)), 17: point((0, 3)), 18: point((2, 3))}
    else:
        left = {5: pouch, 6: pouch, 7: well, 8: well, 9: pouch, 10: pouch,
                11: well, 12: well, 13: pouch, 14: pouch, 15: well,
                16: well, 17: guard, 18: (guard[0] - 3, guard[1]), 19: guard}
    for f in range(SIT_RELOAD_FRAMES):
        poses = dict(PARK)
        near, far = (29, 49), (43, 49)
        active = None
        if f == 1:
            near, far = ((20.5, 44), far) if kind == 'rifle' else (near, (51.5, 43.5))
        elif f == 2:
            near, far = (PARK[kind][0], (42, 45)) if kind == 'rifle' else ((31, 46), PARK[kind][0])
        elif f == 3:
            poses[kind] = (((22, 40), -35) if kind == 'rifle' else ((43, 40), -35))
            near, far = ((22, 40), (38, 44)) if kind == 'rifle' else ((31, 46), (43, 40))
            active = kind
        elif 4 <= f <= 19:
            poses[kind] = LAP
            near, far = grip, left.get(f, guard)
            active = kind
        elif f == 20:
            poses[kind] = (((22, 40), -35) if kind == 'rifle' else ((43, 40), -35))
            near, far = ((22, 40), (40, 46)) if kind == 'rifle' else ((31, 46), (43, 40))
            active = kind
        elif f == 21:
            near, far = (PARK[kind][0], (43, 49)) if kind == 'rifle' else ((29, 49), PARK[kind][0])
        elif f == 22:
            near, far = ((20.5, 44), (43, 49)) if kind == 'rifle' else ((29, 49), (51.5, 43.5))
        prop = None
        if kind == 'rifle' and f in (6, 7, 8, 9, 11, 12, 13):
            prop = magazine_layer(far)
        elif kind == 'shotgun' and f in (6, 7, 10, 11, 14, 15):
            prop = shell_layer((far[0], far[1] - 2))
        if prop:
            prop.px = {p: finish_color(c) for p, c in prop.px.items()}
        frame = seated_pose(body, poses, near, far, active=active, nod=1 if 4 <= f <= 19 else 0,
                            magazine=not (kind == 'rifle' and 6 <= f <= 13),
                            pump=3 if kind == 'shotgun' and f == 18 else 0, prop=prop)
        if kind == 'rifle' and f in (9, 11):
            # Pouch/hip in front of the stored magazine. A fresh magazine's
            # upper edge is already visible above that same opening in f11.
            front, _ = seated_body(body, nod=1)
            for y in range(47, 55):
                for x in range(37, 44):
                    if front.get(x, y)[3]:
                        frame.set(x, y, front.get(x, y))
        frames.append(frame)
    return frames


def seated_frames(body, kind):
    from make_sit import zs
    rest = [seated_pose(body, PARK, (29, 49), (43, 49), breath=b) for b in (0, -1, 0, 1)]
    doze = [seated_pose(body, PARK, (29, 49), (43, 49), nod=n) for n in (1, 2, 3, 2)]
    for i in (2, 3):
        zs(doze[i], 0, i - 1, INK)
    return sit_down(body, kind) + rest + seated_reload(body, kind) + doze


def seated_sheet(body, kind):
    frames = seated_frames(body, kind)
    sheet = Image(SIT_W * len(frames), SIT_H)
    for f, frame in enumerate(frames):
        paste(sheet, frame, f * SIT_W, 0)
    return sheet
