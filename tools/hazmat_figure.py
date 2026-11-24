"""The sheriff in the protective suit, on every sheet drawn on her own upright body.

The suit is not her costume recoloured: its hood, loose torso, air pack and trousers are
drawn on the same places her own body has in each frame, and her arms, guns and what she
holds are the very layers her sheets are made of (rework_cowgirl, make_flashlight,
make_care, make_plant), asked for without her body. So nothing of the corset, hat or hair
is left round the edges, an arm behind her stays behind and a working hand stays in front.
Sitting, fainting and crossing a car are still made from those sheets (make_hazmat).
Standard library only.
"""
from __future__ import annotations

import math
from contextlib import contextmanager
from functools import lru_cache

import cowgirl_pose as pose
import hazmat_legs
from cowgirl_arm import GLOVE, SLEEVE

INK = (0x25, 0x20, 0x18)
HEAD = (20.4, 19.1)               # The middle of her hood, where her head stands on the walk grid
HOOD_R = 7.3
SHOOT = hazmat_legs.SHOOT
UPRIGHT = ('stand', 'stand_dual', 'walk', 'walk_dual', 'jump', 'jump_dual', 'legs', 'legs_dual', 'shoot',
           'shoot_dual', 'shoot_dual_b', 'shoot_dual_lit', 'shoot_dual_b_lit', 'light', 'light_dual', 'light_walk',
           'light_walk_dual', 'melee', 'melee_dual', 'melee_lit', 'melee_dual_lit', 'ricochet', 'ricochet_dual',
           'ricochet_lit', 'ricochet_dual_lit', 'swap', 'swap_lit', 'reload', 'reload_dual', 'reload_dual_b',
           'drink', 'bandage', 'plant')
ARMS_ONLY = ('swap_far', 'light_dual_far', 'reload_dual_lower', 'reload_dual_b_lower')
COUNT = {'stand': 6, 'walk': pose.FRAMES, 'jump': 8, 'legs': pose.FRAMES}


def solid(c):
    return c[:3] + (255,)


# ------------------------------------------------------------- her arms and what they hold

@contextmanager
def without_body():
    """Her generators with no body: what is behind it is noted, one entry per pose drawn."""
    import cowgirl_torso
    import make_care
    import make_flashlight
    import make_melee
    import make_plant
    noted = []

    def behind(far, body):
        noted.append(make_melee.no_holes(far) if far else {})
        return dict(body)

    def arm_only(aim=None, low=None, rest=None, hand_on_hip=True, standing=None, lean=0, chest=0, sway=0.):
        return make_melee.hip_arm(lean) if hand_on_hip else {}

    fakes = {'behind': behind, 'body_at': lambda *a, **k: {}, 'body_without_arm': arm_only,
             'behind_arm': lambda body, arm: dict(body)}
    kept = []
    for module in (make_melee, make_flashlight, make_care, make_plant):
        for name, fake in fakes.items():
            if hasattr(module, name):
                kept.append((module, name, getattr(module, name)))
                setattr(module, name, fake)
    kept.append((cowgirl_torso, 'HOLSTER', cowgirl_torso.HOLSTER))
    cowgirl_torso.HOLSTER = {}
    try:
        yield noted
    finally:
        for module, name, value in reversed(kept):
            setattr(module, name, value)


def cut(image, width=81):
    """An image's frames as pixels."""
    return [{(x, y): image.get(f * width + x, y) for y in range(image.height) for x in range(width)
             if image.get(f * width + x, y)[3]} for f in range(image.width // width)]


@lru_cache(maxsize=None)
def flash_sheet():
    from rework_cowgirl import dressed_shoot
    return dressed_shoot()


def paired(make, *args):
    """What a generator draws in front of her and behind her, frame by frame."""
    with without_body() as noted:
        front = cut(make(*args))
    back = list(noted)
    assert len(back) in (0, len(front)), (make.__name__, len(back), len(front))
    return [(back[f] if back else {}, front[f]) for f in range(len(front))]


@lru_cache(maxsize=None)
def layers(sheet):
    """(behind her, in front of her) for each frame of a sheet, in the authors' colours."""
    import make_care
    import make_flashlight as act
    import make_melee
    import make_plant
    import rework_cowgirl as her
    kind = sheet.replace('_dual', '')
    if kind in ('walk', 'stand', 'jump'):
        out = []
        for f in range(COUNT[kind]):
            down, shift = 0, (0, 0)
            if kind == 'walk':
                arms, down = her.walk_arms(f), her.stride_bob(f)
            elif kind == 'stand':
                arms = her.stand_arms(f)
            else:
                lean = her.JUMP[f][1]
                arms = [tuple((x + lean, y) for x, y in arm) for arm in her.jump_arms(f)]
                down, shift = her.JUMP[f][0], (her.JUMP_MID, her.JUMP_DROP)
            pair = [her.arm_pixels(arm, pose.BELT + down, her.WALK_COLUMN, i == 1) for i, arm in enumerate(arms)]
            out.append(tuple({(x + shift[0], y + shift[1]): c for (x, y), c in px.items()} for px in pair[::-1]))
        return out
    if kind == 'legs':
        return [({}, {})] * COUNT['legs']
    shoot = flash_sheet()
    if sheet == 'shoot':
        return paired(act.make_shoot, shoot)
    if sheet.startswith('shoot_dual'):
        return paired(act.make_dual, shoot, '_b' in sheet, sheet.endswith('_lit'))
    if sheet == 'light':
        return paired(act.make_light, shoot)
    if sheet == 'light_dual':
        made = []
        with without_body() as noted:
            image = act.make_light_dual(shoot, act.make_dual(shoot, False))
            made = cut(image)
        back = noted[act.DUAL_FRAMES:]                   # The turn it starts and ends on is drawn first
        aim = noted[act.DUAL_AIM]
        return [(aim, made[0])] + [(back[f], made[f + 1]) for f in range(len(made) - 2)] + [(aim, made[-1])]
    if sheet in ('swap', 'swap_lit'):
        return paired(act.make_swap, shoot, None, sheet.endswith('_lit'))
    if sheet == 'swap_far':
        return paired(act.make_swap, shoot, None, False, True)
    if sheet == 'light_dual_far':
        return paired(act.make_light_dual, shoot, None, True)
    if sheet.startswith('ricochet'):
        return paired(act.make_power, shoot, '_dual' in sheet, sheet.endswith('_lit'))
    if sheet.startswith('melee'):
        dual, lit = '_dual' in sheet, sheet.endswith('_lit')
        with without_body():
            made = cut(act.make_blow(shoot, {(0, 0): solid(INK)}, dual, lit))   # Its last pose is put in below
        last = (layers('light_dual' if dual else 'light')[-1] if lit else
                layers('shoot_dual')[act.DUAL_ENDS] if dual else layers('shoot')[make_melee.HOLSTER])
        return [({}, px) for px in made[:-1]] + [last]
    if sheet == 'reload':                                # The aim it ends on is drawn first
        back_first = paired(act.make_reload, shoot)
        backs = [back for back, _ in back_first]
        return [(back, front) for back, (_, front) in zip(backs[1:] + backs[:1], back_first)]
    if sheet.startswith('reload_dual'):
        other, only = sheet.startswith('reload_dual_b'), sheet.endswith('_lower')
        with without_body() as noted:
            made = cut(act.make_dual_reload(shoot, other, only))
        return [({} if only else back, px) for back, px in zip(noted, made)]
    if sheet.startswith('light_walk'):
        dual = sheet.endswith('_dual')
        held_back, held_front = layers('light_dual' if dual else 'light')[-1]
        out = [tuple(make_melee.no_holes(px) for px in act.walking_held(f, dual)) for f in range(act.WALK_FRAMES)]
        for rise in act.BREATH:
            out.append(tuple({(x, y + rise): c for (x, y), c in px.items()} for px in (held_back, held_front)))
        return out
    if sheet in ('drink', 'bandage'):
        with without_body() as noted:
            hip = make_melee.hip_arm()
            made = cut(make_care.make_drink(hip) if sheet == 'drink' else make_care.make_bandage(hip))
        return [(noted[f] if noted else {}, px) for f, px in enumerate(made)]
    if sheet == 'plant':
        with without_body() as noted:
            kept = make_plant.down_on_a_knee
            make_plant.down_on_a_knee = lambda body, drop: {(x + drop // 4, y + drop): c
                                                            for (x, y), c in make_melee.hip_arm().items()}
            try:
                made = cut(make_plant.make_cowgirl())
            finally:
                make_plant.down_on_a_knee = kept
        return [(noted[f], px) for f, px in enumerate(made)]
    raise KeyError(sheet)


def recoloured(px, suit, rubber):
    """Sleeves in the suit's cloth and gloves in rubber; guns, shells and light as they are."""
    tones = {SLEEVE[0][:3]: suit[4], SLEEVE[1][:3]: suit[2], SLEEVE[2][:3]: suit[1],
             GLOVE[0][:3]: rubber[3], GLOVE[1][:3]: rubber[1],
             (0xd0, 0xa8, 0x48): (0xb6, 0x98, 0x5c), (0xb8, 0x90, 0x3a): (0x9e, 0x7c, 0x42)}
    return {p: solid(tones.get(c[:3], c)) for p, c in px.items()}


# ------------------------------------------------------------- the suit itself

def place(sheet, frame):
    """The middle of her hood on a frame, in the frame's pixels."""
    import make_flashlight as act
    import make_melee
    import rework_cowgirl as her
    x, y = HEAD
    kind = sheet.replace('_dual', '')
    if kind == 'walk' or sheet.startswith('light_walk') and frame < pose.FRAMES:
        dx, dy = pose.LEAN, pose.bob(frame)
        if kind != 'walk':
            dx, dy = dx + SHOOT[0], dy + SHOOT[1]
    elif kind == 'stand':
        how = her.SETTLE[frame - her.STAND_BREATHS] if frame >= her.STAND_BREATHS else {}
        dx, dy = how.get('lean', 0), how.get('down', 0)
    elif kind == 'jump':
        dx, dy = her.JUMP_MID + her.JUMP[frame][1], her.JUMP_DROP + her.JUMP[frame][0]
    elif kind == 'legs':
        dx, dy = 0, 0
    else:
        dx, dy = SHOOT
        if sheet == 'shoot':
            dx += act.SWAY.get(frame, (0, 0))[0]
        elif sheet in ('shoot_dual', 'shoot_dual_b'):
            dx += act.DUAL_SWAY.get((int(sheet.endswith('_b')), frame), (0, 0))[0]
        elif sheet.startswith('ricochet'):
            dx += {5: -1}.get(frame, 0)
        elif sheet.startswith('melee') and make_melee.POSES[frame]:
            dx += make_melee.POSES[frame][2] * 2
        elif sheet == 'plant':
            from make_plant import COWGIRL
            dx, dy = dx + COWGIRL[frame][3] // 4, dy + COWGIRL[frame][3]
        elif sheet.startswith('light_walk'):
            dy += act.BREATH[frame - pose.FRAMES]
    return x + dx, y + dy


def hood(cx, cy, suit, visor):
    """A round hood lit from the upper left, the face shield where she looks out."""
    out, r = {}, HOOD_R
    vx, vy = cx + 2.1, cy + 3.2
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = math.hypot(x + .5 - cx, y + .5 - cy)
            if d > r + .5:
                continue
            if d > r - .5:
                out[x, y] = solid(INK)
                continue
            e = ((x + .5 - vx) / 4.9) ** 2 + ((y + .5 - vy) / 4.6) ** 2
            if e <= 1 and d <= r - 1.2:                      # Its rubber seal, then the blue glass
                t = (y + .5 - (vy - 4.6)) / 9.2
                out[x, y] = solid(visor[0] if e > .70 else visor[2] if t < .4 else visor[1])
                continue
            k = (-.62 * (x + .5 - cx) - .78 * (y + .5 - cy)) / r
            out[x, y] = solid(suit[5 if k > .55 else 4 if k > .2 else 3 if k > -.2 else 2 if k > -.55 else 1])
    gx, gy = round(vx - 2.4), round(vy - 1.2)                # The light on it
    for p, c in (((gx, gy), visor[4]), ((gx + 1, gy), visor[3]), ((gx - 1, gy + 1), visor[3])):
        if p in out and out[p][:3] in visor:
            out[p] = solid(c)
    return out


def torso(cx, cy, pelvis, suit, rubber, running):
    """One continuous baggy torso from the hood's collar to her hips, turned with her: the zip
    ahead of her middle, the pack's straps, a belt. No narrowing waist, no bust."""
    out = {}
    top, end = round(cy) + 6, round(pelvis[1]) + (1 if running else 2)
    for y in range(top, end + 1):
        v = y - top
        half = 4 if v == 0 else 6 if v == 1 else 7 if v == 2 or y >= end - 1 else 8
        t = max(0., min(1., (v - 2) / max(1, end - top - 4)))
        middle = round(cx + .6 + (pelvis[0] - cx - .6) * t)
        for u in range(-half, half + 1):
            col = suit[4 if u < -2 else 3 if u < 4 else 2]
            if abs(u) == half or y == end and running:
                col = INK if abs(u) == half else suit[2]
            elif 3 <= v and y < end - 6 and u in (-5, -4, 6):
                col = rubber[2 if u < 0 else 1]
            elif 4 <= v and u == 3:
                col = suit[1]                                # Closed zip
            elif y in (end - 5, end - 4):
                col = rubber[1]
            elif (v, u) in ((7, -2), (8, -1), (8, 0)) or (end - y, u) in ((2, 0), (1, 1), (1, -3)):
                col = suit[2]                                # Small creases of cloth
            out[middle + u, y] = solid(col)
    return out


def collar(cx, cy, suit):
    """Cloth joining the hood to the suit: two outlines touching would read as a cut."""
    return {(x, y): solid(suit[3 if x <= cx + .5 else 2])
            for y in range(round(cy) + 6, round(cy) + 9) for x in range(round(cx) - 1, round(cx) + 4)}


def pack(cx, cy, rubber):
    """The compact air pack behind her shoulders."""
    out = {}
    left, top = round(cx) - 11, round(cy) + 9
    for v in range(16):
        for u in range(4):
            edge = u in (0, 3) or v in (0, 15) or v in (4, 12)
            out[left + u, top + v] = solid(rubber[0] if edge else rubber[3] if u == 1 else rubber[1])
    return out


def suited(sheet, frame, suit, rubber, visor):
    """One frame of a sheet in the suit, in the frame's pixels."""
    back, front = layers(sheet)[frame]
    if sheet in ARMS_ONLY:
        return recoloured(front, suit, rubber)
    cx, cy = place(sheet, frame)
    running = hazmat_legs.running(sheet, frame)
    _, middle, belt = hazmat_legs.upright(sheet, frame)
    lower = {(x - hazmat_legs.frame_width(sheet) * frame, y): c
             for (x, y), c in hazmat_legs.lower(sheet, frame, suit, rubber, INK).items()}
    out = recoloured(back, suit, rubber)
    if not sheet.startswith('legs'):
        out.update(pack(cx, cy, rubber))
    out.update(lower)
    out.update(torso(cx, cy, (middle, belt + 1.), suit, rubber, running))
    out.update(hood(cx, cy, suit, visor))
    out.update({p: c for p, c in collar(cx, cy, suit).items() if out.get(p, (0,))[:3] not in visor})
    if sheet == 'bandage':
        from make_care import BIND, wraps
        out.update(wraps({p: c for p, c in lower.items()}, frame + 2, frame == len(BIND) - 1))
    out.update(recoloured(front, suit, rubber))
    return out


def sheet_pixels(sheet, suit, rubber, visor):
    width = hazmat_legs.frame_width(sheet)
    out = {}
    for frame in range(len(layers(sheet))):
        out.update({(x + frame * width, y): c for (x, y), c in suited(sheet, frame, suit, rubber, visor).items()
                    if 0 <= x < width})
    return out
