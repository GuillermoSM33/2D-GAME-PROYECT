"""The sheriff's run, measured pixel by pixel on the user's reference walk.

Every number was read on the native grid of objetivo/walk.gif (ten keys, two
steps) and brought to her 42 x 67 frame: her belt is row 42, her buckle column
22, her soles row 59. Only measures come from it, never its pixels: she is drawn
by cowgirl_torso.py and cowgirl_legs.py. Twenty frames play it, the ten measured
keys and the pose half way between each two. Standard library only.

Her torso hardly turns, as in the reference: what moves is her pelvis (it turns,
her belt tilts, her seat shows as the near leg reaches forward), her legs and her
forearms. Her covered chest follows a row late and no more.
"""
from __future__ import annotations

import math

KEYS = 10
FRAMES = 20                       # PLAYER_SHERIFF_WALK_FRAMES: two per key
FIRST_KEY = 2                     # Frame 0: a foot lands, as it does on frame 10
BELT, MID, SOLE = 42, 22, 59      # Standing, on the walk grid
LEAN = 2                          # Columns her head is ahead of where it is standing

# Rows her whole upper body is off its mark, key by key of one step: the push
# off, two in flight and landing, the support, and the lowest as the legs pass.
BOB = (0, -1, -1, 0, 1)
# The middle of her hips through one step: they hang back as a foot pushes off.
HIPS = (20.2, 21.0, 21.4, 21.2, 20.4)
# Her pelvis turns with her near leg (degrees from facing us): toward us as that
# leg is behind her (keys 0-3), away from us as it reaches forward (5-8).
YAW = (24, 14, 14, 30, 52, 72, 82, 82, 70, 46)
# Rows the back end of her belt rises and the front one drops as it tilts.
BELT_LIFT = (0, 0, 0, .4, 1.3, 2.1, 2.4, 2.4, 1.6, .9)
BELT_DROP = (0, 0, 0, 0, .3, .6, .8, .8, .5, .2)
# How much of her seat is turned to us.
SEAT = (.05, 0, 0, .2, .65, .95, 1., 1., .85, .45)
# Her hip joints, columns from the middle of her hips: the near one goes forward with its leg.
NEAR_HIP = (-1.9, -2.3, -2.2, -1.4, -.1, 1.0, 1.5, 1.5, 1.0, -.5)
FAR_HIP = (2.0, 2.2, 2.1, 1.5, .5, -.4, -1.0, -1.1, -.5, .9)
# One leg through its ten keys: its knee, its ankle and the way its foot points
# (degrees under level). 0 pushing off behind her, 1-3 folding up behind, 4
# passing the other, 5 the knee high in front, 6 reaching, 7 landing, 8-9 under
# her. The far leg is five keys behind.
LEG = (
    (16.3, 49.9, 13.5, 55.4, 70),
    (17.2, 48.9, 12.9, 51.7, 118),
    (19.4, 49.6, 15.6, 53.1, 112),
    (21.4, 50.2, 17.6, 54.2, 98),
    (23.8, 50.0, 21.2, 54.7, 74),
    (27.8, 48.9, 28.2, 53.9, 58),
    (27.0, 48.9, 30.2, 54.1, 26),
    (26.5, 50.0, 28.6, 56.2, 3),
    (25.0, 50.7, 23.8, 56.5, 0),
    (20.0, 50.7, 17.8, 56.5, 4),
)
PLANTED = (7, 8, 9, 10)           # Keys (10 is 0) a foot is on the ground
# Where her hands are, per key. Her near elbow hardly moves: the forearm swings.
NEAR_HAND = ((22.4, 35.4), (23.6, 34.2), (23.4, 34.8), (22.2, 36.8), (21.2, 37.6),
             (19.6, 38.4), (19.4, 37.6), (20.8, 36.0), (22.0, 35.8), (21.8, 36.0))
FAR_HAND = ((33.2, 39.6), (33.8, 37.4), (34.0, 36.0), (34.2, 35.8), (34.2, 35.0),
            (34.4, 33.8), (34.6, 32.2), (34.6, 32.8), (34.2, 35.2), (33.6, 38.2))
ARM_BONE = 6.5                    # Shoulder to elbow and elbow to hand, as on all her sheets
NEAR_SHOULDER = (16.2, 30.6)      # Leaning; the bob is added
FAR_SHOULDER = (27.0, 31.0)
# Rows her covered chest is off the rest of her torso, key by key of one step.
CHEST = (0, 1, 0, -1, 0)


def sample(values: tuple, phase: float) -> float:
    """Between the keys on a closed curve, exact on them."""
    n = len(values)
    key = math.floor(phase)
    t = phase - key
    a, b, c, d = (values[(key + i) % n] for i in (-1, 0, 1, 2))
    return .5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t * t * t)


def whole(value: float) -> int:
    """To a row, halves away from zero: the same on every frame of both steps."""
    return int(math.copysign(math.floor(abs(value) + .5), value))


def phase_of(frame: float) -> float:
    return (frame % FRAMES) * KEYS / FRAMES + FIRST_KEY


def bob(frame: float) -> int:
    """Rows her upper body is off its mark on this frame, + down."""
    return whole(sample(BOB, phase_of(frame) % 5))


def drop(frame: float) -> float:
    """The same, before it is put on a row: her hip joints move by it."""
    return sample(BOB, phase_of(frame) % 5)


def chest_lag(frame: float) -> int:
    return whole(sample(CHEST, phase_of(frame) % 5))


def stride(frame: float) -> float:
    """1 with her feet wide apart, 0 as her legs pass."""
    return .5 + .5 * math.cos(math.radians(72 * (phase_of(frame) - 1.)))


def hips(frame: float) -> float:
    return sample(HIPS, phase_of(frame) % 5)


def seat(frame: float) -> float:
    return max(0., min(1., sample(SEAT, phase_of(frame))))


def yaw(frame: float) -> float:
    return sample(YAW, phase_of(frame))


def belt_tilt(frame: float) -> tuple:
    """Rows the back end of her belt is up, and the front end down."""
    phase = phase_of(frame)
    return max(0., sample(BELT_LIFT, phase)), max(0., sample(BELT_DROP, phase))


def own_phase(frame: float, far: bool) -> float:
    return (phase_of(frame) + (5 if far else 0)) % KEYS


def planted(frame: float, far: bool) -> bool:
    """That foot is on the ground."""
    own = own_phase(frame, far)
    return any(abs(own - key % KEYS) < .01 or PLANTED[0] <= own <= KEYS for key in PLANTED)


def leg_chain(frame: float, far: bool) -> tuple:
    """Hip, knee, ankle and the foot's angle, on the walk grid."""
    phase, own = phase_of(frame), own_phase(frame, far)
    v = [sample(tuple(k[j] for k in LEG), own) for j in range(5)]
    hip = (hips(frame) + sample(FAR_HIP if far else NEAR_HIP, phase), 44.9 + drop(frame))
    dx = .6 if far else 0.
    return hip, (v[0] + dx, v[1]), (v[2] + dx, v[3]), v[4]


def bent(top: tuple, hand: tuple, bone: float = ARM_BONE) -> tuple:
    """An arm of two bones of one length, its elbow hanging behind and under the line to the hand."""
    dx, dy = hand[0] - top[0], hand[1] - top[1]
    length = max(math.hypot(dx, dy), 1e-6)
    reach = min(length, 2 * bone - .05)
    ux, uy = dx / length, dy / length
    hand = (top[0] + ux * reach, top[1] + uy * reach)
    out = math.sqrt(bone * bone - reach * reach / 4)
    return top, (top[0] + ux * reach / 2 - uy * out, top[1] + uy * reach / 2 + ux * out), hand


def arm(frame: float, far: bool) -> tuple:
    """Shoulder, elbow and hand on the walk grid, bob included."""
    phase = phase_of(frame)
    hand = tuple(sample(tuple(k[i] for k in (FAR_HAND if far else NEAR_HAND)), phase) for i in (0, 1))
    top = FAR_SHOULDER if far else NEAR_SHOULDER
    return bent((top[0], top[1] + bob(frame)), hand)
