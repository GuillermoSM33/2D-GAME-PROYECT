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
import hazmat_art as art
import hazmat_legs
from cowgirl_arm import GLOVE, SLEEVE

INK = (0x25, 0x20, 0x18)
HEAD = (20.4, 19.1)               # The middle of her head, where it stands on the walk grid
# Brass still in the authors' colours: a band on the flashlight, a cartridge
OTHERS = {(0xd0, 0xa8, 0x48): (0xb6, 0x98, 0x5c, 255), (0xb8, 0x90, 0x3a): (0x9e, 0x7c, 0x42, 255)}
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
    for name, nothing in (('HOLSTER', {}), ('NEAR_HOLSTER', ())):
        kept.append((cowgirl_torso, name, getattr(cowgirl_torso, name)))
        setattr(cowgirl_torso, name, nothing)
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


def recoloured(px, far=False):
    """Her arms in the suit's sleeves and gloves; guns, shells and light as they are."""
    return {p: OTHERS.get(c[:3], c) for p, c in art.worn(px, SLEEVE, GLOVE, far).items()}


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


def suited(sheet, frame):
    """One frame of a sheet in the suit, in the frame's pixels."""
    back, front = layers(sheet)[frame]
    if sheet in ARMS_ONLY:
        return recoloured(front)
    cx, cy = place(sheet, frame)
    _, middle, belt = hazmat_legs.upright(sheet, frame)
    lower = {(x - hazmat_legs.frame_width(sheet) * frame, y): c
             for (x, y), c in hazmat_legs.lower(sheet, frame, art.CLOTH, art.LEATHER, INK).items()}
    out = recoloured(back, True)
    if not sheet.startswith('legs'):
        out.update(art.tank(cx, cy))
    out.update(lower)
    out.update(art.torso(cx, cy, middle, math.floor(belt) - 1))
    out.update(art.hood(cx, cy))
    if sheet == 'bandage':
        from make_care import BIND, wraps
        out.update(wraps({p: c for p, c in lower.items()}, frame + 2, frame == len(BIND) - 1))
    sleeves = {c[:3] for c in SLEEVE}
    out = art.no_slivers(art.edged(art.whole_patch(out, front), front, sleeves), front)
    out.update(recoloured(front))
    out.update(art.shoulder_patch(front, sleeves, (cx - 6.0, cy + 14.0)))
    return out


def seated():
    """Her on the bench, facing us, in the suit: fourteen frames of make_sit's, with its legs,
    its arms and what it lays on her lap; the pixels of the whole sheet."""
    import make_sit as bench
    from make_sprites import Image
    char = dict(bench.CHARS['cowgirl'], trousers=list(art.CLOTH[1:4]), boots=list(art.LEATHER[1:][::-1]),
                hand=art.BLUE[1])
    rows = bench.COWGIRL_ARM_ROWS
    tones = dict(zip('omnp', (art.INK, art.CLOTH[4], art.CLOTH[3], art.CLOTH[2])))
    glove = dict(zip('omnpgG', (art.INK, art.BLUE[2], art.BLUE[1], art.BLUE[0], art.BLUE[2], art.BLUE[1])))
    weapons = bench.load(bench.ROOT / 'assets/sprites/ui/weapons.png')
    width, middle = bench.W, bench.CX
    out = {}
    for frame in range(14):
        dy = -3 if frame == 0 else -1 if frame == 2 else 0
        nod = {10: 1, 11: 2, 12: 3, 13: 2}.get(frame, 0)
        spread, down = {2: (1, 0), 3: (0, 1)}.get(frame, (0, (nod + 1) // 2 if frame >= 10 else 0))
        cell = Image(width, bench.H)
        px = dict(art.pixels(art.TANK, middle - 16 - spread, 32 + dy))
        bench.legs(cell, 0, char, 1 if frame == 0 else 0)
        px.update({(x, y): cell.get(x, y) for y in range(bench.H) for x in range(width) if cell.get(x, y)[3]})
        hood = art.pixels(art.HOOD_FRONT, middle - 11, 15 + dy + nod)
        px.update(art.whole_patch(art.pixels(art.TORSO_FRONT, middle - 8, 37 + dy), hood, .8))
        for r, row in enumerate(rows):
            for i, key in enumerate(row):
                if key == '.':
                    continue
                d = bench.COWGIRL_ARM_OUTER - i + spread
                y = bench.COWGIRL_ARM_TOP + r + bench.DROP + dy + down
                colour = (glove if r >= len(rows) - 7 else tones).get(key)
                px[middle - 1 - d, y] = px[middle + d, y] = art.BLUE[0] if r == len(rows) - 7 and key != 'o' else colour
        px.update(hood)
        action = Image(width, bench.H)
        if 4 <= frame <= 9:
            bench.reload_step(action, 0, weapons, char, 0, 'revolver', frame - 4)
        if frame >= 12:
            bench.zs(action, 0, 1 if frame == 12 else 2, char['ink'])
        px.update({(x, y): action.get(x, y) for y in range(bench.H) for x in range(width) if action.get(x, y)[3]})
        out.update({(x + frame * width, y): c for (x, y), c in px.items() if 0 <= x < width and 0 <= y < bench.H})
    return out


def sheet_pixels(sheet):
    if sheet == 'sit':
        return seated()
    width = hazmat_legs.frame_width(sheet)
    out = {}
    for frame in range(len(layers(sheet))):
        out.update({(x + frame * width, y): c for (x, y), c in suited(sheet, frame).items() if 0 <= x < width})
    return out
