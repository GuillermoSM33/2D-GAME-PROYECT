"""The protective suit's loose trousers, on the very joints of the sheriff's own legs.

Running, the legs under another action, standing, pulling up, jumping and kneeling use the
chains her normal sheets are drawn on (cowgirl_pose, rework_cowgirl, make_plant), so the
suit never walks on a second rig. Its cloth is cowgirl_legs' trouser leg, fuller all round,
in the suit's colours, with leather boots. Standard library only.
"""
import math

import cowgirl_legs as legs
import cowgirl_pose as pose

FULLER = .45                      # Px more cloth all round than her trousers
BOOT_AT = .62                     # ...and down to here on the calf, over the boot
SHOOT = (12, 7)                   # A walk-grid point on the shoot grid
# Standing: hip, knee, ankle, foot; the near leg and the far one (walk grid).
STAND = (((17.7, 45.0), (17.4, 50.2), (16.9, 56.4), 6), ((24.3, 45.0), (24.7, 50.2), (25.2, 56.4), 4))


def running(sheet, frame):
    """The whole running body; the legs under another action keep the hips she stands with."""
    return sheet in ('walk', 'walk_dual') or sheet.startswith('light_walk') and frame < pose.FRAMES


def moved(chain, dx, dy):
    hip, kn, ankle, foot = chain
    return (hip[0] + dx, hip[1] + dy), (kn[0] + dx, kn[1] + dy), (ankle[0] + dx, ankle[1] + dy), foot


def upright(sheet, frame):
    """Far and near chains of a sheet drawn on her own rig, in its frame, and the middle and
    belt of her hips."""
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
    else:                                                # On the shoot grid, stood to it
        dx, dy = SHOOT
        pair = list(STAND)[::-1]
        middle, belt = 20.9, pose.BELT + .4
    return [moved(c, dx, dy) for c in pair], middle + dx, belt + dy


def frame_width(sheet):
    from detail_cowgirl import WIDTHS
    return WIDTHS.get(sheet, 81)


def suit_tones(cloth, boots):
    """The suit's ramps as cowgirl_legs paints: light, base, shade, fold."""
    solid = lambda c: c[:3] + (255,)  # noqa: E731
    return tuple(solid(cloth[k]) for k in (4, 3, 2, 1)), tuple(solid(c) for c in boots)


def lower(sheet, frame, cloth, boots, ink):
    """Her lower half in the suit on a sheet of her own rig, in the sheet's pixels."""
    pair, middle, belt = upright(sheet, frame)
    tones, hide = suit_tones(cloth, boots)
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
