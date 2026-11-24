"""The protective suit's loose trousers, on the very joints of the sheriff's own legs.

Running, the legs under another action, standing, pulling up, jumping and kneeling use the
chains her normal sheets are drawn on (cowgirl_pose, rework_cowgirl, make_plant), so the
suit never walks on a second rig. Its cloth is cowgirl_legs' trouser leg, fuller all round,
in the suit's colours, with rubber boots. Lying, sitting and crossing a car keep chains of
their own, placed from her head. Standard library only.
"""
from functools import lru_cache
import math

import cowgirl_legs as legs
import cowgirl_pose as pose

FULLER = .45                      # Px more cloth all round than her trousers
BOOT_AT = .74                     # ...and down to here on the calf, over the boot
SHOOT = (12, 7)                   # A walk-grid point on the shoot grid
# Standing: hip, knee, ankle, foot; the near leg and the far one (walk grid).
STAND = (((17.7, 45.0), (17.4, 50.2), (16.9, 56.4), 6), ((24.3, 45.0), (24.7, 50.2), (25.2, 56.4), 4))
SITTING_KNEE, SITTING_FOOT = 53, 56


def raster(pixels, local, world):
    """Inverse nearest sampling keeps a turned native-pixel garment whole."""
    if not pixels: return {}
    xs, ys = [p[0] for p in pixels], [p[1] for p in pixels]
    corners = [world(x, y) for x in (min(xs) - 1, max(xs) + 1) for y in (min(ys) - 1, max(ys) + 1)]
    out = {}
    for y in range(min(p[1] for p in corners) - 1, max(p[1] for p in corners) + 2):
        for x in range(min(p[0] for p in corners) - 1, max(p[0] for p in corners) + 2):
            u, v = local((x, y))
            c = pixels.get((round(u), round(v)))
            if c is not None: out[x, y] = c
    return out


def knee(hip, ankle, straight=False, projection=1., toward=1):
    """Two equal projected bones, bending toward the direction of travel."""
    x, y = ankle[0] - hip[0], ankle[1] - hip[1]
    distance = max(.01, math.hypot(x, y))
    if straight:
        return (hip[0] + x * .5, hip[1] + y * .5)
    half = distance * .5
    bend = math.sqrt(max(0, 7.5 ** 2 - half ** 2)) * projection * toward
    return hip[0] + x * .5 + y / distance * bend, hip[1] + y * .5 - x / distance * bend


@lru_cache(maxsize=1)
def car_poses():
    from make_car_passage import Figure, poses
    return poses(Figure('cowgirl'))


def running(sheet, frame):
    """The whole running body; the legs under another action keep the hips she stands with."""
    return sheet in ('walk', 'walk_dual') or sheet.startswith('light_walk') and frame < pose.FRAMES


def moved(chain, dx, dy):
    hip, kn, ankle, foot = chain
    return (hip[0] + dx, hip[1] + dy), (kn[0] + dx, kn[1] + dy), (ankle[0] + dx, ankle[1] + dy), foot


def upright(sheet, frame):
    """Far and near chains of a sheet drawn on her own rig, in its frame, and the middle and
    belt of her hips; None for the sheets placed from her head."""
    import rework_cowgirl as her
    if running(sheet, frame):
        dx, dy = (0, 0) if sheet.startswith('walk') else SHOOT
        pair = [pose.leg_chain(frame, far) for far in (True, False)]
        middle, belt = pose.hips(frame), pose.BELT + pose.drop(frame)
    elif sheet in ('legs', 'legs_dual'):
        dx, dy = 0, 0
        pair = []
        for far in (True, False):
            (_, kn, ankle, foot), side = pose.leg_chain(frame, far), 1 if far else -1
            pair.append(((20.8 + side * 2.9, 45.0), kn, ankle, foot))
        middle, belt = 20.9, pose.BELT + .4
    elif sheet in ('stand', 'stand_dual'):
        dx, dy = 0, 0
        settle = frame == her.STAND_BREATHS
        pair = list(her.SETTLE_LEGS if settle else STAND)[::-1]
        middle, belt = 20.9, pose.BELT + .4 + settle
    elif sheet in ('jump', 'jump_dual'):
        dx, dy = her.JUMP_MID, her.JUMP_DROP
        down, _, _, _, near, far, *_ = her.JUMP[frame]
        pair = [((20.9 + side * 2.5, 45.0 + down), (kx, ky), (ax, ay), foot)
                for side, (kx, ky, ax, ay, foot) in ((1, far), (-1, near))]
        middle, belt = 20.9, pose.BELT + .4 + down
    elif sheet == 'plant':
        from make_plant import COWGIRL, FAR_LEG, KNEEL_DROP, NEAR_LEG, between
        dx, dy = 0, 0
        drop = COWGIRL[frame][3]
        pair = [between(*table, drop / KNEEL_DROP) for table in (FAR_LEG, NEAR_LEG)]
        middle, belt = 33 + drop // 4, 49.4 + drop
    elif sheet in ('sit', 'faint') or sheet.startswith('car'):
        return None
    else:                                                # On the shoot grid, stood to it
        dx, dy = SHOOT
        pair = list(STAND)[::-1]
        middle, belt = 20.9, pose.BELT + .4
    return [moved(c, dx, dy) for c in pair], middle + dx, belt + dy


def rig(sheet, frame, cx, cy, local, world):
    """World-space pelvis and far/near (hip, knee, ankle, foot) chains, from her head for the
    sheets that turn or fold her."""
    origin = frame_width(sheet) * frame
    found = upright(sheet, frame)
    if found:
        pair, middle, belt = found
        return (middle + origin, belt + 1.), [moved(c, origin, 0) for c in pair]
    chains = []
    if sheet.startswith('car'):
        at = car_poses()[frame]
        row = 80 * (int(cy) // 80)
        pelvis = (origin + at.hip[0], row + at.hip[1])
        for side, foot in ((-1, at.far), (1, at.near)):
            hip = pelvis[0] + side * 4, pelvis[1]
            ankle = origin + foot[0], row + foot[1] - 2
            chains.append((hip, knee(hip, ankle), ankle, 4))
        return pelvis, chains
    if sheet == 'sit':
        ground = 61
        pelvis = (0., 49 - cy)
        for side in (-1, 1):
            chains.append(((side * 4., pelvis[1]), (side * 4.5, SITTING_KNEE - cy), (side * 4.5, SITTING_FOOT - cy), 90))
    else:                                                # Swaying, giving way, down
        pelvis = (0., 24.)
        for side in (-1, 1):
            hip, ankle = (side * 3.5, 24.), (side * 4., 36.6)
            chains.append((hip, knee(hip, ankle, True), ankle, 4))
    return world(*pelvis), [tuple(world(*p) for p in chain[:3]) + (chain[3],) for chain in chains]


def frame_width(sheet):
    from detail_cowgirl import WIDTHS
    return WIDTHS.get(sheet, 81)


def suit_tones(cloth, rubber):
    """The suit's ramps as cowgirl_legs paints: light, base, shade, fold."""
    solid = lambda c: c[:3] + (255,)  # noqa: E731
    return (tuple(solid(cloth[k]) for k in (4, 3, 2, 1)), tuple(solid(rubber[k]) for k in (4, 3, 1, 0)))


def lower(sheet, frame, cloth, rubber, ink):
    """Her lower half in the suit on a sheet of her own rig, in the sheet's pixels."""
    pair, middle, belt = upright(sheet, frame)
    tones, hide = suit_tones(cloth, rubber)
    seat, half, lift = 0., 6.8, 0.
    if running(sheet, frame):
        seat = pose.seat(frame)
        half = 5.5 + .75 * pose.stride(frame)
        lift = pose.belt_tilt(frame)[0]
    far, near = (legs.painted(legs.sections(c, FULLER, BOOT_AT), c, i == 0, seat, tones, hide, BOOT_AT)
                 for i, c in enumerate(pair))
    hips = legs.hips(middle, belt, half, seat, lift, tones)
    row = math.floor(belt)
    ground = {True: 59, False: 66}[frame_width(sheet) == 42]
    if sheet.startswith('jump'):
        ground = 75
    px = legs.lower_body(far, near, hips, row, ground, top=row - 3, crease=0 if seat > .4 else 4, fold=tones[3])
    origin = frame_width(sheet) * frame
    return {(x + origin, y): (ink + (255,) if c == legs.INK else c) for (x, y), c in px.items()}


def trousers(pelvis, chains, local, world, ink, cloth, rubber):
    """The folded sheets' trousers: one cloth tube through each knee, a small boot each."""
    layers = {}
    for chain in chains:
        hip, kn, ankle = (local(p) for p in chain[:3])
        pixels = {}
        for a, b, ra, rb in ((hip, kn, 2.9, 2.5), (kn, ankle, 2.5, 2.1)):
            length = max(math.dist(a, b), .1)
            for sample in range(max(2, math.ceil(length * 3)) + 1):
                t = sample / max(2, math.ceil(length * 3))
                u, v = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                radius = ra + (rb - ra) * t
                for y in range(math.floor(v - radius), math.ceil(v + radius) + 1):
                    for x in range(math.floor(u - radius), math.ceil(u + radius) + 1):
                        if (x + .5 - u) ** 2 + (y + .5 - v) ** 2 > radius ** 2: continue
                        side = (x + .5 - u) / radius
                        pixels[x, y] = cloth[4 if side < -.25 else 3 if side < .5 else 2]
        # A short diagonal fabric fold follows the knee; it adds no volume.
        for du, dv in ((-1, 0), (0, 1)):
            p = round(kn[0] + du), round(kn[1] + dv)
            if p in pixels: pixels[p] = cloth[2]
        # Boots have one ankle, a small toe and a flat sole under that foot.
        sole = math.floor(ankle[1] + 3)
        for y in range(math.floor(ankle[1]), sole + 1):
            for x in range(math.floor(ankle[0] - 2), math.ceil(ankle[0] + (3 if y >= sole - 1 else 2))):
                pixels[x, y] = ink if y == sole else rubber[3 if x < ankle[0] - .5 else 1]
        edge = {}
        for x, y in pixels:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = x + ox, y + oy
                if q not in pixels and q[1] <= sole and q[1] > hip[1] + 1:
                    edge[q] = ink
        edge.update(pixels)
        layers.update({(x, y): c + (255,) for (x, y), c in edge.items()})
    pu, pv = local(pelvis)
    # A single pelvis joins both thighs. The crotch opens below it, rather
    # than a triangular gap starting high at the waist.
    for y in range(math.floor(pv - 1), math.ceil(pv + 3)):
        half = 7 if y < pv + 2 else 6
        for x in range(round(pu - half), round(pu + half) + 1):
            layers[x, y] = cloth[4 if x < pu - 2 else 3 if x < pu + 4 else 2] + (255,)
    return raster(layers, local, world)
