#!/usr/bin/env python3
"""The laboratory train's hazmat suit (2-3) on the sheriff and the SWAT.

Usage: python3 tools/make_hazmat.py [--verify]

Writes assets/sprites/characters/<id>/suit/<sheet>.png for every sheet of the
cowgirl and the SWAT, same size and frames as the sheet it comes from: the
game draws these while she wears one of car 01's suits (train.suit). Every
animation keeps its joints, pivots and held equipment. The pieces are
hazmat_art.py's, with the proportions measured on the user's reference:

  * the sheriff is composed on her own poses (hazmat_figure.py): a draped hood
    with a blue-lit window over a respirator, a loose coverall with her star on
    a patch, long blue gloves, a belt with pouches, leather boots, an air bottle;
  * the SWAT's generator is run again with every layer tagged, so each material
    goes to its own: sleeves and trousers of the same cloth, blue gloves,
    leather boots, a carrier drawn on its body, dark pads, its own helmet with
    amber goggles up over a sealed hood, the respirator and the bottle;
  * guns stay exactly as drawn.

--verify rebuilds into memory and compares with the installed files.
Standard library only.
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from embed_assets import decode_png_rgba  # noqa: E402
from make_sprites import Image  # noqa: E402
import hazmat_art  # noqa: E402

ROOT = TOOLS.parent
CHARS = ROOT / 'assets/sprites/characters'


def hx(v):
    return (v >> 16) & 255, (v >> 8) & 255, v & 255


def lum(c):
    return .299 * c[0] + .587 * c[1] + .114 * c[2]


INK = hx(0x252018)
# ---------------------------------------------------------------- the sheriff

def components(points, colors_ok, px, conn=4):
    """Connected groups of points whose colour is in colors_ok."""
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (1, -1), (-1, 1), (-1, -1)) if conn == 8 else ())
    seen, groups = set(), []
    for p in points:
        if p in seen: continue
        group, todo = [], [p]
        seen.add(p)
        while todo:
            x, y = todo.pop()
            group.append((x, y))
            for dx, dy in steps:
                q = (x + dx, y + dy)
                if q not in seen and q in px and px[q][:3] in colors_ok:
                    seen.add(q)
                    todo.append(q)
        groups.append(group)
    return groups


def clusters(points, reach=3):
    """Points grouped by distance (a head each)."""
    left = set(points)
    out = []
    while left:
        seed = left.pop()
        group, todo = [seed], [seed]
        while todo:
            x, y = todo.pop()
            for dy in range(-reach, reach + 1):
                for dx in range(-reach, reach + 1):
                    q = (x + dx, y + dy)
                    if q in left:
                        left.discard(q)
                        group.append(q)
                        todo.append(q)
        out.append(group)
    return out


def drop_floating_ink(out, largest=4):
    """Outline specks left in the air once hat, hair and chaps are gone.

    An outline always borders some material. A small group of outline
    pixels touching none (8-neighbourhood) read as dirt round the hood.
    """
    ink = {p for p, c in out.items() if c[:3] == INK and c[3]}
    around = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
    seen = set()
    for start in ink:
        if start in seen: continue
        group, todo = [start], [start]
        seen.add(start)
        while todo:
            x, y = todo.pop()
            for dx, dy in around:
                q = (x + dx, y + dy)
                if q in ink and q not in seen:
                    seen.add(q)
                    group.append(q)
                    todo.append(q)
        if len(group) > largest: continue
        if not any((x + dx, y + dy) in out and out[(x + dx, y + dy)][:3] != INK
                   for x, y in group for dx, dy in around):
            for p in group:
                del out[p]


def suit_cowgirl(px, w, h, sheet=''):
    """A sheet of hers in the suit, composed on her own poses (hazmat_figure)."""
    import hazmat_figure
    if sheet == 'flashlight':
        return dict(px)
    if sheet == 'car':                                   # Her own joints through the car, the suit's parts
        from make_car_passage import Figure, character_sheet
        image = character_sheet(Figure('cowgirl', suit=True))
        out = {(i % w, i // w): c for i, c in enumerate(image.px) if c[3]}
        floor = {}                                       # The car's, where each cell is cut
        for x, y in out:
            floor[x // 81, y // 80] = max(y, floor.get((x // 81, y // 80), 0))
        cloth = hazmat_art.cloth_tones()
        for group in components([p for p, c in out.items() if c[:3] in cloth], cloth, out):
            if len(group) < 3:                           # A shoulder's corner left out past her back
                for p in group:
                    del out[p]
        close_outline(out, w, h, 81)
        out = {(x, y): c for (x, y), c in out.items() if y <= floor.get((x // 81, y // 80), -1)}
    elif sheet == 'faint':                               # Her suited stance, falling as she does
        from make_faint import make
        fallen = make(to_image(42, 67, suit_cowgirl({}, 42, 67, 'stand')))
        out = {(i % w, i // w): c for i, c in enumerate(fallen.px) if c[3]}
    else:
        out = {p: c for p, c in hazmat_figure.sheet_pixels(sheet).items() if 0 <= p[0] < w and 0 <= p[1] < h}
        if sheet in hazmat_figure.ARMS_ONLY:             # Exactly what her own sheet covers, its outline too
            return {p: out.get(p, INK + (255,)) for p in px}
        close_outline(out, w, h, hazmat_figure.hazmat_legs.frame_width(sheet))
    drop_floating_ink(out)
    return out


def close_outline(out, w, h, width):
    """An outline where the suit's own cloth or rubber meets nothing."""
    own = hazmat_art.OWN
    for (x, y), c in list(out.items()):
        if c[:3] not in own:
            continue
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = x + a, y + b
            if q not in out and 0 <= q[0] < w and 0 <= q[1] < h and q[0] // width == x // width:
                out[q] = INK + (255,)


# ---------------------------------------------------------------- the SWAT

SWAT_CLOTH = [0x29343b, 0x41494a, 0x5d6870, 0x697174, 0x272c2d, 0x363d40, 0x373b3d, 0x505355, 0x50595e,
              0x25282a, 0x727678, 0x77807b, 0x909d97, 0x96948b, 0x41494a]
SWAT_LEATHER = [0x73553e, 0x5a4638, 0x443931, 0x39312c, 0x967353, 0x6a594e, 0x483326, 0x6f4d33, 0x916c48]
# The lenses of its helmet (its grenades are other greens), and those of the earlier helmet that
# bandaging, planting and fainting still have, a column and half a row further on.
SWAT_LENSES = {hx(c) for c in (0x93ae36, 0xd4d990)}
SWAT_OLD_LENSES = {hx(c) for c in (0x8fa83e, 0xb6ca64, 0xd3df97, 0x435327)}


# The last is of what is drawn in its final colours.
TAG, ARM_TAG, PLATE_TAG, PACK_TAG, GLOVE_TAG, BOOT_TAG, DRAWN_TAG = 253, 252, 251, 250, 249, 248, 247
TAGS = (TAG, ARM_TAG, PLATE_TAG, PACK_TAG, GLOVE_TAG, BOOT_TAG, DRAWN_TAG)


def swat_tagged():
    """Recompose the original animation with material masks in alpha.

    The masks follow the actual articulated sleeves, armour and guns through
    leaning, recoil, walking, sitting and falling. A chest plate cannot paint
    over an arm or a weapon that is in front of it.
    """
    import make_swat
    import swat_actions
    import swat_aux
    import swat_sit
    import make_car_passage
    import rebuild_swat
    original = make_swat.gun_layer
    patches = []

    def patch(module, name, replacement):
        patches.append((module, name, getattr(module, name)))
        setattr(module, name, replacement)

    def tagged_layer(layer, tag):
        layer.px = {p: c[:3] + (tag,) for p, c in layer.px.items()}
        return layer

    def equipment_body(source, action=False):
        body = Image(source.width, source.height)
        body.px = list(source.px)
        dx, dy = (12, 7) if action else (0, 0)
        for y in range(55 + dy, 62 + dy):
            for x in range(body.width):
                c = body.get(x, y)
                if c[3]: body.set(x, y, c[:3] + (BOOT_TAG,))
        # The carrier on its chest, where its body is; the sleeves are composed later.
        x0, y0 = hazmat_art.SWAT_VEST_AT
        for (x, y), c in hazmat_art.pixels(hazmat_art.SWAT_VEST, x0 + dx, y0 + dy).items():
            if 0 <= x < body.width and body.get(x, y)[3]:
                body.set(x, y, c[:3] + (DRAWN_TAG,))
        return body

    body_original = make_swat.standing_body
    painted_original = swat_actions.body_from_painting
    arm_original = make_swat.arm
    sleeve_original = swat_actions.sleeve
    hand_original = make_swat.hand
    source_original = make_swat.load_source

    def load_source():
        source = source_original()
        body = Image(source.width, source.height)
        body.px = list(source.px)
        for y in range(55, 62):
            for x in range(body.width):
                c = body.get(x, y)
                if c[3]: body.set(x, y, c[:3] + (BOOT_TAG,))
        return body

    def standing_body(*args, **kwargs):
        return equipment_body(body_original(*args, **kwargs))

    def painted_body(*args, **kwargs):
        return equipment_body(painted_original(*args, **kwargs), True)

    def mark_sleeve(layer, near):
        shoulder, elbow, hand = layer.joints
        for p, c in list(layer.px.items()):
            tag = GLOVE_TAG if math.dist(p, hand) < 2.6 else ARM_TAG
            if near and (math.dist(p, shoulder) < 2.9 or math.dist(p, elbow) < 1.9):
                tag = PLATE_TAG
            layer.px[p] = c[:3] + (tag,)
        return layer

    def arm(*args, **kwargs):
        layer = arm_original(*args, **kwargs)
        return mark_sleeve(layer, kwargs.get('near', args[2] if len(args) > 2 else False))

    def sleeve(*args, **kwargs):
        layer, hand = sleeve_original(*args, **kwargs)
        near = kwargs.get('near', args[2] if len(args) > 2 else False)
        return mark_sleeve(layer, near), tagged_layer(hand, GLOVE_TAG)

    def hand(*args, **kwargs):
        return tagged_layer(hand_original(*args, **kwargs), GLOVE_TAG)

    def tagged(*args, **kwargs):
        layer, to_frame = original(*args, **kwargs)
        layer.px = {p: c[:3] + (TAG,) for p, c in layer.px.items()}
        return layer, to_frame

    patch(make_swat, 'gun_layer', tagged)
    patch(swat_actions, 'gun_layer', tagged)
    patch(make_swat, 'standing_body', standing_body)
    patch(make_swat, 'load_source', load_source)
    patch(swat_actions, 'body_from_painting', painted_body)
    patch(swat_sit, 'body_from_painting', painted_body)
    patch(make_swat, 'arm', arm)
    patch(make_swat, 'hand', hand)
    patch(swat_actions, 'sleeve', sleeve)
    patch(swat_aux, 'sleeve', sleeve)
    patch(make_car_passage, 'sleeve', sleeve)
    try:
        import make_flashlight
        if hasattr(make_flashlight, 'gun_layer'): patch(make_flashlight, 'gun_layer', tagged)
    except ImportError:
        pass
    try:
        with tempfile.TemporaryDirectory(prefix='themiracle-hazmat-') as temp:
            out = Path(temp)
            (out / 'rig').mkdir()
            names, _ = rebuild_swat.generate(out, out / 'rig')
            sheets = {}
            for name in names:
                w, h, rgba = decode_png_rgba(out / f'{name}.png')
                sheets[name] = {(i % w, i // w): tuple(rgba[i * 4:i * 4 + 4]) for i in range(w * h)
                                if rgba[i * 4 + 3] in TAGS}
            # Passage poses are generated separately from the normal actions.
            # In particular their slung rifle still has its original material.
            for name, kind in (('car', 'rifle'), ('car_shotgun', 'shotgun')):
                figure = make_car_passage.Figure('swat', kind)
                figure.hide = tuple(c[:3] + (BOOT_TAG,) for c in figure.hide)
                x0, y0 = hazmat_art.SWAT_VEST_AT
                for p, c in hazmat_art.pixels(hazmat_art.SWAT_VEST, x0 + 12, y0 + 7).items():
                    if p in figure.torso:
                        figure.torso[p] = c[:3] + (DRAWN_TAG,)
                # Its bottle goes with its back, which leans apart from its head.
                at = [12 + hazmat_art.SWAT_AT[0] + hazmat_art.SWAT_TANK[0], 7 + hazmat_art.SWAT_AT[1] + hazmat_art.SWAT_TANK[1]]
                bottle = {p: c[:3] + (PACK_TAG,) for p, c in hazmat_art.pixels(hazmat_art.TANK, *at).items()}
                figure.torso = {**bottle, **figure.torso}
                img = make_car_passage.character_sheet(figure)
                sheets[name] = {(i % img.width, i // img.width): c for i, c in enumerate(img.px)
                                if c[3] in TAGS}
            return sheets
    finally:
        for module, name, value in reversed(patches):
            setattr(module, name, value)


def swat_heads(px, masks, sheet):
    """Where its helmet is in each frame: the middle of the lenses, and how far it is tipped."""
    for cols, (du, dv) in ((SWAT_LENSES, (0., 0.)), (SWAT_OLD_LENSES, (1., .5))):
        lenses = [p for p, c in px.items() if c[:3] in cols and masks.get(p, (0, 0, 0, 0))[3] != TAG]
        for group in clusters(lenses, 5):
            if len(group) < 6: continue
            lx, ly = (sum(p[i] for p in group) / len(group) for i in (0, 1))
            angle = ((0, 0, 0, 0, 30, 60, 90, 90)[int(lx) // 80] if sheet == 'faint' else
                     car_tilts('shotgun' in sheet)[int(lx) // 81] if sheet in CROSSING else 0)
            a = math.radians(angle)
            yield lx - du * math.cos(a) + dv * math.sin(a), ly - du * math.sin(a) - dv * math.cos(a), angle


@lru_cache(maxsize=2)
def car_tilts(shotgun):
    """How far it tips its head, frame by frame, as it crosses a car."""
    from make_car_passage import Figure, poses
    return [pose.tilt for pose in poses(Figure('swat', 'shotgun' if shotgun else 'rifle'))]


@lru_cache(maxsize=1)
def swat_lens():
    """The middle of its lenses on swat/stand.png."""
    _, _, px = read(CHARS / 'swat/stand.png')
    spots = [p for p, c in px.items() if c[:3] in SWAT_LENSES and p[0] < 42 and p[1] < 26]
    return tuple(sum(p[i] for p in spots) / len(spots) for i in (0, 1))


def swat_local(p, lens, angle):
    """A pixel of a frame, as it would be on swat/stand.png by the helmet."""
    a = math.radians(angle)
    x, y = p[0] - lens[0], p[1] - lens[1]
    at = swat_lens()
    return x * math.cos(a) + y * math.sin(a) + at[0], -x * math.sin(a) + y * math.cos(a) + at[1]


def swat_part(rows, corner, lens, angle):
    """A map of the suit, its corner given on swat/stand.png, put by the helmet and tipped as it is."""
    out, reach = {}, 44
    for y in range(int(lens[1]) - reach, int(lens[1]) + reach):
        for x in range(int(lens[0]) - reach, int(lens[0]) + reach):
            u, v = swat_local((x, y), lens, angle)
            i, j = math.floor(u - corner[0] + .5), math.floor(v - corner[1] + .5)
            if 0 <= j < len(rows) and 0 <= i < len(rows[j]) and rows[j][i] != '.':
                out[x, y] = hazmat_art.COLORS[rows[j][i]]
    return out


def by_light(c, ramp, steps):
    """A colour of its uniform on one of the suit's ramps."""
    return ramp[sum(lum(c) >= s for s in steps)]


CROSSING = ('car', 'car_shotgun')  # Through a car; carry is its walk with the gun in hand
SWAT_WIDTHS = {'stand': 42, 'walk': 42, 'legs': 42, 'jump': 54, 'jump_shotgun': 54, 'sit': 72, 'sit_shotgun': 72, 'faint': 80}
CLOTH_STEPS, BLUE_STEPS = (20, 44, 58, 76), (48, 66, 92)
BOOT_STEPS, GREY_STEPS, PAD_STEPS = (40, 62, 96), (30, 58, 84, 112), (34, 60, 104, 128)


def dress_swat(px, out, masks, sheet, width):
    """What its uniform's colours alone do not tell: cloth between the pouches is belt, a sliver
    of the far sleeve is in shade and trousers are lit from the left."""
    art = hazmat_art
    cloth, brown = art.cloth_tones(), {hx(c) for c in SWAT_LEATHER}
    known = {hx(c) for c in SWAT_CLOTH}

    def tag_of(p):
        return masks.get(p, (0, 0, 0, 0))[3]

    belts = {}
    if sheet != 'faint':
        rows = {}
        for p, c in px.items():
            if c[:3] in brown:
                rows.setdefault((p[0] // width, p[1]), []).append(p)
        for (frame, y), points in rows.items():
            if len(points) >= 5:
                belts.setdefault(frame, []).append(y)
    for frame in list(belts):                            # The belt, not the strap on its shoulder
        ys = sorted(belts[frame])
        belts[frame] = set(range(min(y for y in ys if max(ys) - y < 5), max(ys) + 1))
    for p, c in list(out.items()):
        if c[:3] not in cloth:
            continue
        frame = p[0] // width
        if not tag_of(p) and p[1] in belts.get(frame, ()):
            out[p] = art.COLORS['m'] if px[p][:3] in known else px[p][:3] + (255,)
        elif tag_of(p) == ARM_TAG and sum(out.get((p[0] + a, p[1] + b), (0,))[:3] in cloth
                                          for a in (-1, 0, 1) for b in (-1, 0, 1)) <= 4:
            out[p] = art.CLOTH[1]
        elif not tag_of(p) and frame in belts and p[1] > max(belts[frame]):
            left, right = ((p[0] + k, p[1]) for k in (-1, 1))
            if out.get(right, art.INK)[:3] not in cloth:
                out[p] = art.CLOTH[2]
            elif out.get(left, art.INK)[:3] not in cloth:
                out[p] = art.CLOTH[4]


def suit_swat(px, masks, sheet=''):
    """Its own poses in the suit: sleeves and trousers of coated cloth, long blue gloves, boots of
    leather; its carrier, pads and belt as they are, darker; the helmet with its goggles up over
    a sealed hood, a respirator and the air bottle. Guns stay exactly as drawn."""
    art = hazmat_art
    ink = {INK, hx(0x272c2d), hx(0x25282a)}
    uniform = {hx(c) for c in SWAT_CLOTH}
    width = SWAT_WIDTHS.get(sheet, 81)

    def tag_of(p):
        return masks.get(p, (0, 0, 0, 0))[3]

    hands = {p for p, c in masks.items() if c[3] == GLOVE_TAG}
    near = [(a, b) for a in range(-2, 3) for b in range(-2, 3) if math.hypot(a, b) <= 2.6]
    out = {}
    for p, c in px.items():
        tag = tag_of(p)
        if tag == TAG:
            out[p] = c
        elif tag == DRAWN_TAG:
            out[p] = masks[p][:3] + (255,)
        elif c[:3] in ink:
            out[p] = art.INK
        elif tag == GLOVE_TAG:
            out[p] = by_light(c, art.BLUE, BLUE_STEPS)
        elif tag == BOOT_TAG:
            out[p] = by_light(c, art.LEATHER[::-1], BOOT_STEPS)
        elif tag == PLATE_TAG:
            out[p] = by_light(c, art.GREY, GREY_STEPS)
        elif c[:3] not in uniform or c[:3] == hx(0x96948b):  # Leather and its clips, brass, a flash, a dozing z
            out[p] = c
        elif tag == ARM_TAG and any((p[0] + a, p[1] + b) in hands for a, b in near):
            out[p] = by_light(c, art.BLUE, (48, 80, 112))    # The glove's gauntlet
        else:
            out[p] = by_light(c, art.CLOTH, CLOTH_STEPS)
    dress_swat(px, out, masks, sheet, width)
    # Knee pads move with the source legs, including the folded jump and the seated poses:
    # their light planes say where each one is.
    frame_h = 82 if sheet.startswith('jump') else 80 if sheet in CROSSING or max((p[1] for p in px), default=0) >= 67 else 67
    knee_shine = {hx(v) for v in (0x77807b, 0x909d97, 0x727678)}
    held = (TAG, ARM_TAG, GLOVE_TAG)
    low = frame_h - (42 if sheet in CROSSING else {82: 34, 80: 30}.get(frame_h, 25))
    seeds = [p for p, c in px.items() if c[:3] in knee_shine and p[1] % frame_h >= low and tag_of(p) not in held]
    for group in clusters(seeds, 1):
        if len(group) < 4: continue
        if sheet in CROSSING:                      # Its legs there are drawn with their pads
            out.update({p: by_light(px[p], art.GREY, PAD_STEPS) for p in group})
            continue
        x0, x1 = min(p[0] for p in group) - 1, max(p[0] for p in group) + 1
        y0, y1 = min(p[1] for p in group) - 1, max(p[1] for p in group) + 1
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                p = x, y
                if p in px and not (x in (x0, x1) and y in (y0, y1)) and px[p][:3] not in ink and tag_of(p) not in held:
                    out[p] = by_light(px[p], art.GREY, PAD_STEPS)
    # Legs that walk, jump or go under an action are drawn apart, without tags: their boots
    # are their last rows.
    if sheet not in ('faint', 'sit', 'sit_shotgun') and not sheet in CROSSING:
        frames, booted = {}, {p[0] // width for p, c in masks.items() if c[3] == BOOT_TAG}
        for p in px:
            if p not in masks and p[0] // width not in booted:
                frames.setdefault(p[0] // width, []).append(p)
        for points in frames.values():
            ground = max(y for _, y in points)
            for p in points:
                if p[1] >= ground - 5 and out[p][:3] in art.cloth_tones():
                    out[p] = by_light(px[p], art.LEATHER[::-1], BOOT_STEPS)
    gloves = {c[:3] for c in art.BLUE}
    for group in components([p for p, c in out.items() if c[:3] in gloves], gloves, out, 8):
        if len(group) < 5:                               # A corner of a hand behind it: a speck
            out.update({p: art.INK for p in group})
    kept = {p for p, c in masks.items() if c[3] in held}
    for lx, ly, angle in swat_heads(px, masks, sheet):
        for p in list(out):                              # Helmet, balaclava and lenses give way
            u, v = swat_local(p, (lx, ly), angle)
            if abs(p[0] - lx) < 44 and -1.5 <= u - art.SWAT_AT[0] <= 28.5 and -1.5 <= v - art.SWAT_AT[1] <= 19.4 and p not in kept:
                del out[p]
        head = swat_part(art.SWAT_HEAD, art.SWAT_AT, (lx, ly), angle)
        out.update({p: c for p, c in head.items() if p not in kept})
        if sheet in CROSSING:
            continue
        corner = art.SWAT_AT[0] + art.SWAT_TANK[0], art.SWAT_AT[1] + art.SWAT_TANK[1]
        for p, c in swat_part(art.TANK, corner, (lx, ly), angle).items():
            out.setdefault(p, c)
    if sheet in CROSSING:
        for p, c in masks.items():
            if c[3] == PACK_TAG:
                out.setdefault(p, c[:3] + (255,))
    cloth = art.cloth_tones()
    for p in [p for p, c in out.items() if c[:3] in cloth and not tag_of(p)]:
        if sum(out.get((p[0] + a, p[1] + b), (0,))[:3] in cloth for a in (-1, 0, 1) for b in (-1, 0, 1)) <= 2:
            out[p] = art.INK                             # A crumb of cloth between two pieces of kit
    drop_floating_ink(out)
    return out


# ---------------------------------------------------------------- sheets

def read(path):
    w, h, rgba = decode_png_rgba(path)
    px = {}
    for i in range(w * h):
        a = rgba[i * 4 + 3]
        if a:
            px[(i % w, i // w)] = tuple(rgba[i * 4:i * 4 + 4])
    return w, h, px


def to_image(w, h, px):
    img = Image(w, h)
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            img.set(x, y, c)
    return img


def build():
    out = {}
    for path in sorted((CHARS / 'cowgirl').glob('*.png')):
        w, h, px = read(path)
        out[f'cowgirl/suit/{path.name}'] = to_image(w, h, suit_cowgirl(px, w, h, path.stem))
    guns = swat_tagged()
    for path in sorted((CHARS / 'swat').glob('*.png')):
        w, h, px = read(path)
        masks = guns.get(path.stem, {})
        out[f'swat/suit/{path.name}'] = to_image(w, h, suit_swat(px, masks, path.stem))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    sheets = build()
    bad = 0
    with tempfile.TemporaryDirectory(prefix='themiracle-hazmat-') as temp:
        for name, img in sheets.items():
            target = CHARS / name
            if args.verify:
                probe = Path(temp) / 'sheet.png'
                img.save(probe)
                if not target.is_file() or target.read_bytes() != probe.read_bytes():
                    print('FALLO: ' + name)
                    bad += 1
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                img.save(target)
    print(f'make_hazmat: {len(sheets)} sheets' + (f', {bad} differences' if args.verify else ''))
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
