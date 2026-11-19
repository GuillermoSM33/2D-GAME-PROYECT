#!/usr/bin/env python3
"""Through a car across the road (N): her poses and the car's doors.

The steps, frames and distances are src/game/car_pass.h's (read from it):
she walks to a door, takes its handle at arm's length and opens it (or
hammers her fist through its glass and lifts the lock through it), steps on
the sill, ducks in and sits on the floor under the roof, shoves herself across
out of sight, pushes the other door open, puts a leg out, stands up and walks
on as it shuts. The cars are bigger than life beside her (make_city.CAR_SCALE).

Each character sheet is CAR_PASS_FRAMES cells of 81 x 80 in two rows: row 0
what of her is out of the car (drawn over it), row 1 what is in it (drawn
under its panels and doors). She is built from parts on one skeleton: the
torso turns about her hips, her head stays upright on her neck, her legs and
arms are drawn from their joints to where her feet and hands are put. No
pose turns the whole sprite, and no arm folds up on itself (MIN_REACH).

The car's layers (terrain/car_passage{,_damaged}{,_front}): for each look,
its glass (whole, the rear door's broken, the front's) times its doors (shut,
rear ajar, rear open, front ajar, front open). The body goes under her, the
front (body less open doorways and broken glass, with the open door leaves)
over what of her is inside, its glass (whole or broken) as well.

Deterministic, standard library only.
"""
import argparse
import math
import re
import sys
from pathlib import Path

from make_sprites import Image, rgb
from make_swat import load, paste, ik
from make_plant import leg, edged, TROUSER, FAR_TROUSER, BOOT
from cowgirl_arm import arm_limb, glove, INK
from landscape_kit import Canvas, hx, mix, sheet
from swat_actions import sleeve, weapon_pose, finish_color
import make_city as city

ROOT = Path(__file__).resolve().parent.parent
HEADER = ROOT / 'src/game/car_pass.h'


def c_numbers(text=None):
    """Every integer CAR_* macro of car_pass.h."""
    text = HEADER.read_text(encoding='utf-8') if text is None else text
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r'#define (CAR_\w+) \(?(-?\d+)\)?(?![.\d])', text)}


C = c_numbers()
W, H, FRAMES = C['CAR_FRAME_W'], C['CAR_FRAME_H'], C['CAR_PASS_FRAMES']
ANCHOR = 31.5                    # Her x in the frame (SHOOT_ANCHOR_X)
GROUND = 66                      # Her feet's top row standing (the soles below)
# The car, drawn bigger than life (make_city.CAR_SCALE). Its geometry below is
# in make_city's 1x units: CX(x) is its column, CY(y) its row, at that scale.
CAR_W, CAR_H, CAR_TOP = city.CAR_W, city.CAR_H, 68 - city.CAR_H   # Its top row is her row CAR_TOP
CAR_S = city.scaler(city.CAR_SCALE)


def CX(x):
    return CAR_S(x)


def CY(y):
    """A 1x row of the car (its wheels' row 45) at its scale."""
    return CAR_H - 1 - CAR_S(45 - y)


SILL = CY(35) + CAR_TOP          # A foot on the car's sill, in her rows
FLOOR = CY(37) + CAR_TOP         # Her lowest row in the car: its floor
PARTS = ('back_arm', 'far_leg', 'near_leg', 'torso', 'head', 'front_arm', 'front_hand', 'back_hand', 'gun', 'shards')


class Figure:
    """One character standing, cut into parts at fixed joints."""

    def __init__(self, who, kind='rifle'):
        self.who, self.kind = who, kind
        if who == 'cowgirl':
            from rework_cowgirl import dressed_sheet, stand_sheet
            from make_melee import body_without_arm, frame, AIM, LOW, HOLSTER
            from detail_cowgirl import HAIR
            cow = dressed_sheet('shoot', True)
            body = body_without_arm(frame(cow, AIM), frame(cow, LOW), frame(cow, HOLSTER),
                                    hand_on_hip=False, standing=stand_sheet(False))
            hair = set(HAIR)
            hanging = {rgb(c) for c in (0x46101e, 0x8a2438, 0x64182a, 0x6c4626, 0x4a2e18)}
            self.head = self._head(body, 33, hair)
            self.torso = {p: c for p, c in body.items() if p not in self.head and p[1] <= 50}
            # The sash and holster below her belt hang from it: they do not lean with her back.
            self.hanging = {p: c for p, c in body.items() if 50 < p[1] <= 59 and
                            (c in hanging or self._edge_of(body, p, hanging))}
            self.hip, self.neck = (32, 50), (33, 34)
            self.front, self.back, self.front_over = (40, 38), (26, 38), True
            self.leg_hip = {'near': (36, 50), 'far': (28, 50)}
            self.cloth = {'near': TROUSER, 'far': FAR_TROUSER}
            self.boot = None
            from rework_cowgirl import ARM_BONE
            self.bones = (ARM_BONE, ARM_BONE)       # Her own arm, as in all her sheets
            self.duck = (0, 0)
            self.reach_up = (0, 0)                  # Her hand to the window as drawn
        else:
            sw = load(ROOT / 'docs/templates/swat/rig/body_actions.png')
            body = {(x, y): sw.get(x, y) for y in range(H) for x in range(W) if sw.get(x, y)[3]}
            self.head = {p: c for p, c in body.items() if p[1] <= 29}
            self.torso = {p: c for p, c in body.items() if 29 < p[1] <= 51}
            self.hanging = {}
            self.hip, self.neck = (31, 51), (33, 30)
            self.front, self.back, self.front_over = (39, 35.5), (24, 35.5), False
            self.leg_hip = {'near': (36, 51), 'far': (27, 51)}
            self.cloth = {'near': [rgb(0x5d6870), rgb(0x41494a), rgb(0x29343b)],
                          'far': [rgb(0x41494a), rgb(0x363d40), rgb(0x29343b)]}
            self.boot = dict(zip(BOOT, [rgb(0x41494a), rgb(0x29343b), rgb(0x25282a)]))
            self.bones = (8.5, 9.5)
            self.duck = (0, 0)
            # Taller and longer in the arm, he reaches the window further on
            # (nearer, his arm would fold up on itself).
            self.reach_up = (4, -2)

    @staticmethod
    def _edge_of(body, p, colors):
        return body[p][:3] == INK[:3] and any(body.get((p[0] + a, p[1] + b)) in colors
                                              for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    @staticmethod
    def _head(body, chin, hair):
        """Her head: everything to her chin, and her hair (with its edge) below it."""
        head = {p: c for p, c in body.items() if p[1] <= chin}
        for p, c in body.items():
            if p[1] > chin and p[0] <= 26 and (c in hair or Figure._edge_of(body, p, hair)):
                head[p] = c
        return head


def turned(pixels, angle, pivot, at):
    """Pixels turned by angle degrees about pivot (the top goes forward) and
    put with the pivot at `at`: each frame pixel takes the one under it."""
    if not pixels:
        return {}
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    if abs(angle) < .01:
        dx, dy = round(at[0] - pivot[0]), round(at[1] - pivot[1])
        return {(x + dx, y + dy): c for (x, y), c in pixels.items()}
    corners = [forward(p, angle, pivot, at) for p in pixels]
    out = {}
    for y in range(math.floor(min(p[1] for p in corners)) - 2, math.ceil(max(p[1] for p in corners)) + 3):
        for x in range(math.floor(min(p[0] for p in corners)) - 2, math.ceil(max(p[0] for p in corners)) + 3):
            fx, fy = x + .5 - at[0], y + .5 - at[1]
            key = (math.floor(pivot[0] + fx * ca + fy * sa), math.floor(pivot[1] - fx * sa + fy * ca))
            if key in pixels:
                out[x, y] = pixels[key]
    return out


def forward(p, angle, pivot, at):
    a = math.radians(angle)
    dx, dy = p[0] - pivot[0], p[1] - pivot[1]
    return (at[0] + dx * math.cos(a) - dy * math.sin(a), at[1] + dx * math.sin(a) + dy * math.cos(a))


class Arm:
    """A hand put from its shoulder: the way the arm points (degrees, 0 ahead
    of her, 90 straight down) and how far it reaches (1 straight)."""

    def __init__(self, angle, reach=.92):
        self.angle, self.reach = angle, reach

    def hand(self, shoulder, bones):
        a = math.radians(self.angle)
        d = (bones[0] + bones[1]) * self.reach
        return (shoulder[0] + d * math.cos(a), shoulder[1] + d * math.sin(a))


class Chain:
    """An arm put by its two bones: the way the upper arm points and the way
    the forearm points (degrees as for Arm). The forearm may only turn up
    from the upper arm, as an elbow bends (or go on straight)."""

    def __init__(self, upper, fore):
        assert -165 <= fore - upper <= 5, 'an elbow does not bend that way'
        self.upper, self.fore = upper, fore

    def joints(self, shoulder, bones):
        a, b = math.radians(self.upper), math.radians(self.fore)
        elbow = (shoulder[0] + bones[0] * math.cos(a), shoulder[1] + bones[0] * math.sin(a))
        return elbow, (elbow[0] + bones[1] * math.cos(b), elbow[1] + bones[1] * math.sin(b))


class Pose:
    """Where her parts go in one frame. Points are frame px; a hand is a
    point, an Arm or a Chain; `inside` names the parts in the car. `knob` is
    the top of the door's lock post, on the sill of the window she broke."""

    def __init__(self, hip, lean=0.0, near=(39, GROUND), far=(25, GROUND), front=None, back=None,
                 head=(0, 0), toes=(3, -2), inside=(), sling=1.0, shards=(), tilt=0.0, knob=None,
                 knee_up=False):
        self.hip, self.lean, self.near, self.far = hip, lean, near, far
        self.front, self.back, self.head, self.toes = front, back, head, toes
        self.inside = set(inside)
        self.sling, self.shards, self.tilt = sling, shards, tilt
        self.knob = knob
        self.knee_up = knee_up            # Sat down, her near knee up in front of her body


# How far a hand may come in to its shoulder: nearer, the arm folds up on
# itself and reads as broken (a fist drawn back to strike may come nearer).
MIN_REACH = .62


def elbow_for(shoulder, wrist, bones):
    """Her elbow, always on the side an elbow bends (behind a hanging arm,
    under one held out): it never flips over from frame to frame."""
    upper, fore = bones
    d = math.dist(shoulder, wrist)
    reach = upper + fore - .05
    if d > reach:
        wrist = tuple(a + (b - a) * reach / d for a, b in zip(shoulder, wrist))
    if d < abs(upper - fore) + .1:
        wrist = (shoulder[0], shoulder[1] + upper + fore - 1)
    return ik(shoulder, wrist, upper, fore, 1), wrist


def draw_arm(fig, shoulder, wrist, front, elbow=None):
    """The arm and hand: sleeve, glove; for the SWAT his own sleeve."""
    if elbow is None:
        elbow, wrist = elbow_for(shoulder, wrist, fig.bones)
    if fig.who == 'cowgirl':
        arm = arm_limb(shoulder, elbow, wrist, corner_radius=2)
        hand = glove(wrist, elbow)
    else:
        layer, mitt = sleeve(shoulder, wrist, not front, elbow=elbow, corner_radius=2)
        arm = {p: finish_color(c) for p, c in layer.px.items()}
        hand = {p: finish_color(c) for p, c in mitt.px.items()}
    return arm, hand, elbow, wrist


def split_forearm(arm, shoulder, elbow, wrist):
    """The arm's pixels nearer its forearm than its upper arm."""
    def distance(point, a, b):
        vx, vy = b[0] - a[0], b[1] - a[1]
        t = max(0, min(1, ((point[0] + .5 - a[0]) * vx + (point[1] + .5 - a[1]) * vy) / max(vx * vx + vy * vy, 1e-6)))
        return (point[0] + .5 - a[0] - t * vx) ** 2 + (point[1] + .5 - a[1] - t * vy) ** 2
    fore = {p: c for p, c in arm.items() if distance(p, elbow, wrist) < distance(p, shoulder, elbow)}
    return {p: c for p, c in arm.items() if p not in fore}, fore


def slung_gun(fig):
    """The SWAT's gun slung on his back, muzzle down behind him, its strap over his chest."""
    gun, _, _, _ = weapon_pose(fig.kind, (22, 36), -75)
    px = dict(gun.px)
    for k in range(15):
        at = (25 + round(k * .75), 33 + k)
        px[at] = rgb(0x665942 if k % 4 else 0x82725a)
    return px


def held_gun(fig, grip, angle):
    gun, guard, _, _ = weapon_pose(fig.kind, grip, angle)
    return gun.px, guard


def render(fig, pose):
    """(out, inside): her pixels out of the car and in it, finished."""
    hip0 = fig.hip
    hip = pose.hip
    a = pose.lean
    group = dict(fig.torso)
    swat_held = fig.who == 'swat' and pose.sling < .5
    if fig.who == 'swat' and not swat_held:
        back = slung_gun(fig)
        back.update(group)                        # The torso over the gun on his back
        group = back
    torso = turned(fig.hanging, 0, hip0, hip)
    torso.update(turned(group, a, hip0, hip))
    neck = forward(fig.neck, a, hip0, hip)
    # Her head on her neck, bowed a little only as she ducks under the roof.
    head = turned(fig.head, pose.tilt, fig.neck, (neck[0] + pose.head[0], neck[1] + pose.head[1]))
    front_sh = forward(fig.front, a, hip0, hip)
    back_sh = forward(fig.back, a, hip0, hip)
    legs = {}
    for side, foot, toe in (('far', pose.far, pose.toes[1]), ('near', pose.near, pose.toes[0])):
        top = forward(fig.leg_hip[side], 0, hip0, hip)       # She bends at the waist: her hips stay
        drawn = edged(leg(top, (round(foot[0]), round(foot[1])), fig.cloth[side], toe,
                          strap=fig.who == 'cowgirl' and side == 'near'))
        if fig.boot:
            drawn = {p: fig.boot.get(c, c) for p, c in drawn.items()}
        legs[side] = drawn
    gun, guard = {}, None
    if swat_held:
        gun, guard = held_gun(fig, (back_sh[0] + 6, back_sh[1] + 10), -28)
    fw = pose.front or (guard if swat_held else REST_FRONT)
    bw = pose.back or ((back_sh[0] + 6, back_sh[1] + 10) if swat_held else REST_BACK)
    def joints(spec, shoulder):
        if isinstance(spec, Chain):
            return spec.joints(shoulder, fig.bones)
        return None, spec.hand(shoulder, fig.bones) if isinstance(spec, Arm) else spec
    felbow, fw = joints(fw, front_sh)
    belbow, bw = joints(bw, back_sh)
    farm, fhand, felbow, fw = draw_arm(fig, front_sh, fw, True, felbow)
    barm, bhand, belbow, bw = draw_arm(fig, back_sh, bw, False, belbow)
    knob = {}
    if pose.knob:                                 # The lock's post on the sill, in the car
        kx, ky = pose.knob
        knob = {(kx, ky + k): rgb(0xc9c2a6 if k < 2 else 0x8d8a78) for k in range(3)}
        knob.update({(kx + 1, ky + k): rgb(0x3b3f3a) for k in range(3)})
    # Back to front. Each part keeps its name for its layer.
    order = []
    if fig.front_over:
        order += [('back_arm', barm), ('back_hand', bhand)]
    else:
        order += [('front_arm', farm), ('front_hand', fhand)]
    order += [('far_leg', legs['far'])]
    order += ([('torso', torso), ('head', head), ('near_leg', legs['near'])] if pose.knee_up else
              [('near_leg', legs['near']), ('torso', torso), ('head', head)])
    if swat_held:
        order += [('gun', gun), ('front_arm', split_forearm(farm, front_sh, felbow, fw)[1]),
                  ('front_hand', fhand)]
    if fig.front_over:
        order += [('front_arm', farm), ('front_hand', fhand)]
    else:
        order += [('back_arm', barm), ('back_hand', bhand)]
    owner, colors = {}, {}
    for name, px in order:
        for p, c in px.items():
            colors[p], owner[p] = c, name
    colors = {p: c for p, c in colors.items() if 0 <= p[0] < W and 0 <= p[1] < H}
    if fig.who == 'cowgirl':
        from finish_cowgirl import finish as outline
        from detail_cowgirl import finish as material
        colors = material(outline(colors, W, H), 'car')
    out, inside = {}, {}
    for p, c in colors.items():
        name = owner.get(p)
        if name is None:                          # An edge the finish added: its neighbour's layer
            near = [owner.get((p[0] + dx, p[1] + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            near = [n for n in near if n]
            name = next((n for n in near if n not in pose.inside), near[0] if near else 'torso')
        if name in pose.inside:
            if p[1] <= FLOOR:
                inside[p] = c
        else:
            out[p] = c
    # Drawn as they are, not outlined: the lock's post under her hand, the
    # glass bits over all.
    out.update({p: c for p, c in knob.items() if p not in colors})
    out.update({p: rgb(SHARD[k % 3 == 0]) for k, p in enumerate(pose.shards)})
    pose.reaches = (math.dist(front_sh, fw) / sum(fig.bones), math.dist(back_sh, bw) / sum(fig.bones))
    return out, inside


# ---- The poses, step by step (frame px; she faces right) ----
#
# Every hand is put where an arm can hold it without folding up (MIN_REACH),
# as an Arm from its shoulder or a Chain of its two bones, and every elbow
# bends the one way an elbow does. Each step reads at a glance: she grips
# the handle at arm's length, yanks the door, steps on the sill and ducks in,
# sits on the floor and shoves herself across out of sight, and comes
# out of the far door one leg first, standing up with her arms at her sides.

REST_FRONT, REST_BACK = Arm(80, .94), Arm(97, .94)    # Her arms down at her sides
HANDLE = (ANCHOR + C['CAR_REACH'], CY(21) + CAR_TOP)  # The handle, at shoulder height and arm's length
INSIDE = C['CAR_INSIDE_AT']


def walk(fig):
    """Eight frames, two steps of CAR_STRIDE: the planted foot goes back as
    far as the body goes on, so it holds the ground. Her arms swing as in her
    own walk (rework_cowgirl.walk_arms): a few degrees from the shoulder,
    hands a little ahead of it, elbows held."""
    stride = C['CAR_STRIDE']
    cowgirl = fig.who == 'cowgirl'
    poses = []
    for i in range(C['CAR_WALK_FRAMES']):
        phase = i / C['CAR_WALK_FRAMES']
        feet = []
        for offset in (0.0, .5):
            p = (phase + offset) % 1
            if p < .5:
                x, lift = stride / 4 - stride * p, 0
            else:
                x, lift = -stride / 4 + stride * (p - .5), round(3 * math.sin(math.pi * (p - .5) / .5))
            feet.append((round(32 + x), GROUND - lift))
        bob = 1 if i % 4 == 0 else 0
        swing = math.cos(phase * math.tau)        # Her near foot ahead: her near arm behind
        hip = (32, 50 + bob + (0 if cowgirl else 1))
        poses.append(Pose(hip, 3, near=feet[0], far=feet[1], toes=(3, 2), sling=0.0,
                          front=Arm(77 + 5 * swing, .97) if cowgirl else None,
                          back=Arm(103 - 5 * swing, .97) if cowgirl else None))
    return poses


def standing(fig, **kw):
    hip = kw.pop('hip', (32, 50 if fig.who == 'cowgirl' else 51))
    return Pose(hip, kw.pop('lean', 2), near=kw.pop('near', (38, GROUND)), far=kw.pop('far', (25, GROUND)), **kw)


def settle(fig):
    if fig.who == 'swat':                         # The gun up over his shoulder, onto his back
        return [standing(fig, sling=0.0, front=(44, 31), back=(32, 36)),
                standing(fig, sling=1.0, front=(42, 46), back=(26, 48))]
    return [standing(fig, front=Arm(82), back=Arm(96)), standing(fig, front=REST_FRONT, back=REST_BACK)]


def reach(fig):
    """Her near arm comes up to the handle, nearly straight."""
    return [standing(fig, lean=3, front=Arm(55, .9)),
            standing(fig, lean=5, front=Arm(25, .88)),
            standing(fig, lean=6, front=HANDLE)]


# The glass she breaks: her fist hits its lower part, just ahead of her and
# above her shoulder; its bits land on the road under it, where the game then
# keeps them (terrain/car_glass: handle-relative x, the car's rows).
GLASS_HIT = (47, CY(13) + CAR_TOP)
BURST = ((0, -2), (2, -1), (-1, 0), (3, 1), (1, 2), (-2, 2), (4, 3), (2, 4))
LANDED = ((-6, CAR_H - 1), (-4, CAR_H - 2), (-1, CAR_H - 1), (0, CAR_H - 1), (2, CAR_H - 2),
          (4, CAR_H - 1), (6, CAR_H - 1), (8, CAR_H - 2))
SHARD = (0x8fb2b4, 0xd6e6e2)     # A bit of glass, and one catching the light
# The lock post on the window's sill, down (its top; 3 px tall). It and her
# hand stay in the broken window (its lowest row, CY(14), is her row 30, and
# columns 46-58 are in it on every car and door), so her arm is drawn whole
# over the car: it reaches into the hole, never cut off nor in the car's row
# of her sheet.
KNOB = (48, CY(14) + CAR_TOP - 2)


def shards_at(t, hit=GLASS_HIT):
    """The glass bits t of the way from the burst to the road (falling faster)."""
    out = []
    for (bx, by), (u, row) in zip(BURST, LANDED):
        sx, sy = hit[0] + bx, hit[1] + by
        ex, ey = HANDLE[0] - .5 + u, row + CAR_TOP
        out.append((round(sx + (ex - sx) * t), round(sy + (ey - sy) * t * t)))
    return tuple(out)


def strike(fig):
    """Her forearm cocked up by her head, then her fist up into the glass, the
    bits falling to the road."""
    hit = (GLASS_HIT[0] + fig.reach_up[0], GLASS_HIT[1] + fig.reach_up[1])
    made = [standing(fig, lean=-2, front=Chain(-20, -88)),
            standing(fig, lean=-4, front=Chain(-38, -112), near=(37, GROUND)),
            standing(fig, lean=6, front=hit, near=(40, GROUND), shards=shards_at(0, hit)),
            standing(fig, lean=5, front=(hit[0] - 1, hit[1] + 1), near=(40, GROUND), shards=shards_at(.35, hit)),
            standing(fig, lean=4, front=Arm(70, .9), near=(39, GROUND), shards=shards_at(.7, hit)),
            standing(fig, lean=3, front=Arm(80, .92), near=(39, GROUND), shards=shards_at(1, hit))]
    assert len(made) - 1 == C['CAR_STRIKE_LAND']      # They land as the road gets them
    return made


def unlock(fig):
    """Her hand in through the broken window to the lock's post on the sill,
    which she pulls up."""
    dx = fig.reach_up[0]
    knob = (KNOB[0] + dx, KNOB[1])
    return [standing(fig, lean=6, front=(45.5 + dx * 1.4, knob[1] + 2), knob=knob),
            standing(fig, lean=6, front=(47.5 + dx, knob[1] + 1), knob=knob),
            standing(fig, lean=6, front=(47.5 + dx, knob[1] - .5), knob=(knob[0], knob[1] - 2))]


def pull(fig):
    """She grips the handle and yanks the door open, leaning back; it swings
    on and she lets it go."""
    return [standing(fig, lean=4, front=HANDLE),
            standing(fig, lean=-4, front=(HANDLE[0] - 2, HANDLE[1] + 1), near=(36, GROUND)),
            standing(fig, lean=-1, front=Arm(42, .9), near=(37, GROUND)),
            standing(fig, lean=6, hip=(32, 51), front=Arm(20, .9), near=(38, GROUND))]


def door_frame(step, k):
    """The anchor of frame k of a step that moves her, from where it began
    (art px): her way spread evenly over the step's time."""
    if step == 'in':
        way, count = C['CAR_REACH'] + INSIDE, C['CAR_STEP_IN_FRAMES']
    else:
        way, count = C['CAR_OUT_SHIFT'], C['CAR_STEP_OUT_FRAMES']
    return way * (k + .5) / count


# The way in and out, keyed relative to the handle of the door (x) and in her
# rows: hips, lean, near foot, far foot, front hand, back hand, what is in the
# car, the head's drop (she ducks under the roof) and its bow.
ALL = frozenset(PARTS)


def key(hip, lean, near, far, front, back, inside, head=(0, 0), toes=(3, 2), tilt=0, knee_up=False):
    return dict(hip=hip, lean=lean, near=near, far=far, front=front, back=back, inside=set(inside),
                head=head, toes=toes, tilt=tilt, knee_up=knee_up)


def posed(fig, k, anchor):
    """A key put in the frame of an anchor (handle-relative x)."""
    to = lambda p: p if p is None or isinstance(p, (Arm, Chain)) else (round(ANCHOR + p[0] - anchor), p[1])  # noqa: E731
    lift = 0 if fig.who == 'cowgirl' else 1
    hip = to(k['hip'])
    lean, head = k['lean'], k['head']
    if 'head' in k['inside']:
        lean, head = lean - fig.duck[0], (head[0], head[1] + fig.duck[1])
    return Pose((hip[0], hip[1] + lift), lean, near=to(k['near']), far=to(k['far']),
                front=to(k['front']), back=to(k['back']), head=head, inside=k['inside'],
                toes=k['toes'], tilt=k['tilt'], knee_up=k['knee_up'])


def seated(x, s=0.0, lean=14):
    """Sat on the car's floor under the roof, nearly upright: her near knee up
    in front of her, her hands on the floor either side, shoving her along.
    Her head stays on her neck and her back hardly turns (a sprite turned
    far, or a head sunk in its shoulders, reads as broken). s in -1..1 is the
    shove."""
    return key((x, FLOOR - 1), lean, (x + 11, FLOOR), (x + 8, FLOOR),
               Arm(78 - 4 * s, .85), Arm(100 + 6 * s, .85), ALL, (1, 1), (3, 2), knee_up=True)


def in_anchor(k):
    return -C['CAR_REACH'] + door_frame('in', k)


# Every frame has all of her in one row of the sheet: out of the car (over
# it) or in it (under its panels and doors), never a leg or an arm alone.
IN_KEYS = [
    # A knee up to the sill, her near arm out to the doorway
    key((-19, 51), 6, (-10, 61), (-26, GROUND), Arm(30, .9), Arm(100, .92), (), (0, 0)),
    # A foot on the sill, her hand on the door's frame
    key((-15, 51), 10, (-5, SILL), (-24, GROUND), Arm(10, .9), Arm(95, .9), (), (1, 1)),
    # Crouching down into the doorway
    key((-11, 53), 18, (-3, SILL), (-19, GROUND - 1), Arm(35, .88), Arm(85, .88), (), (1, 2), (3, 1)),
    # In: sitting down on the floor
    dict(seated(INSIDE - 1, lean=16)),
] + [seated(INSIDE, s) for s in (-.5, .5, 0, 0)]       # ...as the door shuts


def step_in(fig):
    """She steps up on the sill, crouches into the doorway and sits in it."""
    return [posed(fig, IN_KEYS[k], in_anchor(k)) for k in range(C['CAR_STEP_IN_FRAMES'])]


def crawl(fig):
    """Shoving herself along the floor, out of sight."""
    return [posed(fig, seated(INSIDE, math.cos(k / C['CAR_CRAWL_FRAMES'] * math.tau)), INSIDE)
            for k in range(C['CAR_CRAWL_FRAMES'])]


OUT = INSIDE + C['CAR_OUT_SHIFT']   # Where she stands out of the far door
PUSH_KEYS = [  # Her near hand out to the door, pushing it open
    dict(seated(INSIDE), front=Arm(5, .9)),
    dict(seated(INSIDE), front=Arm(-8, .92)),
    dict(seated(INSIDE), front=Arm(5, .9), near=(INSIDE + 13, FLOOR)),
]
OUT_KEYS = [  # ...her near foot to the sill, out on the road, and she stands up
    dict(seated(INSIDE + 1, lean=16), near=(INSIDE + 13, SILL), front=Arm(20, .9)),
    key((INSIDE + 4, 54), 16, (OUT + 6, GROUND), (INSIDE + 9, SILL), Arm(60, .9), Arm(100, .88), (), (1, 1)),
    key((INSIDE + 6, 52), 11, (OUT + 6, GROUND), (OUT - 3, 62), Arm(68, .92), Arm(100, .9), (), (1, 1)),
    key((OUT - 3, 51), 7, (OUT + 6, GROUND), (OUT - 7, GROUND), Arm(72, .93), Arm(100, .92), (), (0, 1)),
    key((OUT - 2, 50), 5, (OUT + 6, GROUND), (OUT - 7, GROUND), Arm(76, .94), Arm(98, .93), (), (0, 0)),
    key((OUT - 1, 50), 4, (OUT + 6, GROUND), (OUT - 7, GROUND), REST_FRONT, REST_BACK, (), (0, 0)),
    key((OUT - .5, 50), 3, (OUT + 6, GROUND), (OUT - 7, GROUND), REST_FRONT, REST_BACK, (), (0, 0)),
    key((OUT - .1, 50), 2, (OUT + 6, GROUND), (OUT - 7, GROUND), REST_FRONT, REST_BACK, (), (0, 0)),
]


def push(fig):
    return [posed(fig, k, INSIDE) for k in PUSH_KEYS]


def step_out(fig):
    return [posed(fig, k, INSIDE + door_frame('out', i)) for i, k in enumerate(OUT_KEYS)]


def ready(fig):
    """The door swings shut behind her as she settles (the SWAT takes his gun again)."""
    if fig.who == 'swat':
        return [standing(fig), standing(fig, front=(44, 40), back=(30, 42)),
                standing(fig, sling=0.0, front=(44, 31), back=(32, 36)), standing(fig, sling=0.0)]
    return [standing(fig, lean=3, front=Arm(78), back=Arm(96)), standing(fig, front=REST_FRONT, back=REST_BACK),
            standing(fig, front=REST_FRONT, back=REST_BACK, near=(37, GROUND)),
            standing(fig, front=REST_FRONT, back=REST_BACK)]


STEPS = (('WALK', walk), ('SETTLE', settle), ('REACH', reach), ('STRIKE', strike), ('UNLOCK', unlock),
         ('PULL', pull), ('STEP_IN', step_in), ('CRAWL', crawl), ('PUSH', push), ('STEP_OUT', step_out),
         ('READY', ready))


def poses(fig):
    out = []
    for name, make in STEPS:
        made = make(fig)
        assert len(made) == C[f'CAR_{name}_FRAMES'], name
        assert len(out) == C[f'CAR_{name}_FIRST'], name
        out += made
    assert len(out) == FRAMES
    return out


def character_sheet(fig):
    out = Image(W * FRAMES, 2 * H)
    for i, pose in enumerate(poses(fig)):
        outside, inside = render(fig, pose)
        for row, px in ((0, outside), (1, inside)):
            for (x, y), c in px.items():
                if 0 <= x < W and 0 <= y < H:
                    out.set(i * W + x, row * H + y, c)
    return out


def character_sheets():
    return {'sprites/characters/cowgirl/car.png': character_sheet(Figure('cowgirl')),
            'sprites/characters/swat/car.png': character_sheet(Figure('swat', 'rifle')),
            'sprites/characters/swat/car_shotgun.png': character_sheet(Figure('swat', 'shotgun'))}


# ---- The car ----

OPEN, AJAR = .22, .66            # How wide a door's leaf still shows, open and ajar


def door_shapes(look, side, damage):
    """The window surround and lower panel form one hinged metal shell (the
    car's 1x geometry at its scale): shell, glass, hinge column, latch column."""
    sag = damage
    at = lambda pts: [(CX(x), CY(y)) for x, y in pts]   # noqa: E731
    shape = city.CAR_LOOKS[look][0]
    if side == 0 and shape == 'wagon':
        # The wagon's cargo window and rear pillar are fixed. Its passenger
        # door is rectangular under the long roof, rather than the sedan's
        # diagonal rear surround which cut into that third window.
        shell = at([(39, 2 + sag), (62, 2 + sag), (62, 36), (39, 36)])
        glass = at([(41, 4 + sag), (60, 4 + sag), (60, 14 + sag), (41, 14 + sag)])
        return shell, glass, CX(62), CX(43)
    if side == 0 and shape == 'sedan':
        shell = at([(31, 16 + sag), (44, 2 + sag), (62, 2 + sag), (62, 36), (43, 36), (43, 18 + sag)])
        glass = at([(34, 14 + sag), (45, 4 + sag), (60, 4 + sag), (60, 14 + sag)])
        return shell, glass, CX(62), CX(43)
    shell = at([(65, 2 + sag), (81, 2 + sag), (96, 16 + sag), (94, 36), (65, 36)])
    glass = at([(67, 4 + sag), (80, 4 + sag), (91, 14 + sag), (67, 14 + sag)])
    return shell, glass, CX(94), CX(65)


def broken_glass(canvas, glass):
    """A window broken out: the cabin dark through it, splinters left in its frame."""
    canvas.poly(glass, hx(0x182329))
    xs = [p[0] for p in glass]
    ys = [p[1] for p in glass]
    for k, (x, y) in enumerate(((min(xs) + 1, max(ys) - 1), (min(xs) + 3, max(ys) - 1),
                                (min(xs) + 6, max(ys) - 2), (max(xs) - 2, min(ys) + 1),
                                (max(xs) - 1, max(ys) - 2), (max(xs) - 4, min(ys) + 2))):
        canvas.set(x, y, hx(0x7b9899 if k % 2 else 0x5c7c80))
    canvas.line(min(xs) + 1, max(ys) - 2, min(xs) + 3, max(ys) - 5, hx(0x7b9899))


def door_leaf(look, side, damage, partial, broken=False):
    shell, glass, hinge, latch = door_shapes(look, side, damage)
    leaf = Canvas(CAR_W, CAR_H)
    paint = city.PAINTS[city.CAR_LOOKS[look][1]][3][:3]
    leaf.poly(shell, mix(paint, hx(0x192327), .4))
    for a, b in zip(shell, shell[1:] + shell[:1]):
        leaf.line(*a, *b, paint)
    if broken:
        broken_glass(leaf, glass)
    else:
        leaf.poly(glass, hx(0x35525c))
        leaf.line(glass[0][0] + 1, glass[0][1] + 1, glass[1][0] + CX(5), glass[1][1] + 1, hx(0x789491))
    for a, b in zip(glass, glass[1:] + glass[:1]):
        leaf.line(*a, *b, hx(0x17272d))
    # Its inside: weather seal, padded armrest, handle, speaker and pocket.
    leaf.fill(latch + 2, CY(19 + damage), hinge - 2, CY(33), hx(0x39433f))
    leaf.hline(latch + 2, hinge - 2, CY(18 + damage), mix(paint, hx(0xc0c4ad), .35))
    leaf.hline(latch + 3, hinge - 3, CY(25), hx(0x8b9180))
    leaf.hline(latch + 3, hinge - 3, CY(25) + 1, hx(0x172524))
    leaf.fill(latch + CX(4), CY(29), hinge - CX(4), CY(32), hx(0x192a2b))
    leaf.line(latch + CX(4), CY(21), latch + CX(8), CY(21), hx(0xb7b9a5))
    leaf.disc(hinge - CX(5), CY(30), CX(2), hx(0x172524))
    projected = Canvas(CAR_W, CAR_H)
    factor = AJAR if partial else OPEN
    for y in range(CY(2), CY(38) + 1):           # Each row sampled back, so the leaf never has holes
        for x in range(CAR_W):
            sx = round(hinge + (x - hinge) / factor)
            sy = y - round(abs(sx - hinge) * (.035 if partial else .07))
            if leaf.solid(sx, sy):
                projected.set(x, y, leaf.get(sx, sy))
    return projected


def car_state(look, damage, broken, doors, base):
    """Body and front of one state: broken 0 whole glass, 1 the rear door's,
    2 the front's; doors 0 shut, 1-2 the rear ajar/open, 3-4 the front ajar/open."""
    c = Canvas(CAR_W, CAR_H)
    for y in range(CAR_H):
        for x in range(CAR_W):
            color = base.get((look * 3 + damage) * CAR_W + x, y)
            if color[3]:
                c.set(x, y, color[:3])
    side = None if doors == 0 else (doors - 1) // 2
    partial = doors in (1, 3)
    holes = []
    for s in range(2):
        shell, glass, hinge, latch = door_shapes(look, s, damage)
        hole = Canvas(CAR_W, CAR_H)
        if s == side:
            hole.poly(shell, hx(0x182329))
            c.paste(hole, 0, 0)
            c.fill(latch + CX(3), CY(24), hinge - CX(3), CY(32), hx(0x303a37))   # The seat inside
            c.hline(latch + 2, hinge - 2, CY(35), hx(0x7c8979))                 # ...and the sill
            holes.append(hole)
        elif glass_broken(look, glass_side(broken), s):
            broken_glass(c, glass)
    # The front: all of the body but the open doorway. Its glass, whole or
    # broken out (the cabin dark through it), is drawn over her: in the car
    # she is out of sight but in an open door (the user saw her hat through
    # the windows as if it were outside the car).
    cover = Canvas(CAR_W, CAR_H)
    for y in range(CAR_H):
        for x in range(CAR_W):
            if c.solid(x, y) and not any(h.solid(x, y) for h in holes):
                cover.set(x, y, c.get(x, y))
    if side is not None:
        leaf = door_leaf(look, side, damage, partial, glass_broken(look, glass_side(broken), side))
        c.paste(leaf, 0, 0)
        cover.paste(leaf, 0, 0)
    return c, cover


def glass_on_road():
    """terrain/car_glass: the bits of a broken window on the road under its
    door, for each look, broken coming from the left (its rear door, or the
    pickup's one) and from the right. The game draws them once they have
    fallen (CAR_STRIKE_LAND), where her falling bits land."""
    frames = []
    for look in range(3):
        for side, facing in ((0, 1), (1, -1)):
            c = Canvas(CAR_W, CAR_H)
            for k, (u, row) in enumerate(LANDED):
                c.set(handle_of(look, side) + facing * u, row, hx(SHARD[k % 3 == 0]))
            frames.append(c)
    return sheet(frames)


def handle_of(look, side):
    if look == C['CAR_PICKUP_LOOK']:
        return C['CAR_CAB_HANDLE']
    return C['CAR_FRONT_HANDLE'] if side else C['CAR_REAR_HANDLE']


def glass_side(broken):
    return {0: None, 1: 0, 2: 1}[broken]


def glass_broken(look, broken, side):
    """The pickup's rear and front door are its one door."""
    if broken is None:
        return False
    if look == C['CAR_PICKUP_LOOK']:
        return True
    return broken == side


def car_sheets(base_path=None):
    base = load(base_path or ROOT / 'assets/sprites/terrain/car_wreck.png')
    assert (base.width, base.height) == (CAR_W * 9, CAR_H), 'car_wreck is not at the cars\' scale'
    bodies, covers = [[], []], [[], []]
    for damage in range(2):
        for look in range(3):
            for broken in range(3):
                for doors in range(C['CAR_DOOR_KINDS']):
                    body, cover = car_state(look, damage, broken, doors, base)
                    bodies[damage].append(body)
                    covers[damage].append(cover)
    # One row each, under the 8192 px a texture may be on Windows' SDL renderer.
    return {f'sprites/terrain/car_passage{suffix}.png': sheet(bodies[damage])
            for damage, suffix in enumerate(('', '_damaged'))} | {
            f'sprites/terrain/car_passage{suffix}_front.png': sheet(covers[damage])
            for damage, suffix in enumerate(('', '_damaged'))} | {
            'sprites/terrain/car_glass.png': glass_on_road()}


def build_assets():
    return {**character_sheets(), **car_sheets()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--cars-only', action='store_true', help='Only the door/body layers, after rebuilding scenery')
    args = parser.parse_args()
    bad = []
    images = car_sheets(args.assets_dir / 'sprites/terrain/car_wreck.png') if args.cars_only else build_assets()
    for name, img in images.items():
        target = args.assets_dir / name
        if args.verify:
            import tempfile
            with tempfile.TemporaryDirectory() as temp:
                p = Path(temp) / 'art.png'
                img.save(p)
                if not target.is_file() or p.read_bytes() != target.read_bytes():
                    bad.append(name)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            img.save(target)
        print(name)
    for name in bad:
        print('FALLO: ' + name)
    return bool(bad)


if __name__ == '__main__':
    sys.exit(main())
