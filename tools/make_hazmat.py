#!/usr/bin/env python3
"""The laboratory train's hazmat suit (2-3) on the sheriff and the SWAT.

Usage: python3 tools/make_hazmat.py [--verify]

Writes assets/sprites/characters/<id>/suit/<sheet>.png for every sheet of the
cowgirl and the SWAT, same size and frames as the sheet it comes from: the
game draws these while she wears one of car 01's suits (train.suit). Every
animation keeps its joints, pivots and held equipment:

  * clothes, hat, hair and hood become the suit's hazard yellow, each material
    keeping its own light and shade (the light from the upper left);
  * leather (gloves, boots, belt, holster) becomes black rubber, brass and
    lace the grey of its reflective tape;
  * the sheriff's full-face shield is dark blue, the SWAT's orange;
  * the sheriff's hat and long hair give way to a round hood: the brim and the
    feather and all exposed hair go. Loose overalls cover the fitted waist,
    chest and hips, with broader trousers, a compact pack and dark straps;
  * the SWAT keeps the extra plate carrier, shoulder/elbow and knee guards,
    air bottle and reinforced collar over the yellow protective garment;
  * guns stay exactly as drawn. The SWAT's are known exactly: its generator is
    run again with every weapon layer tagged. The sheriff's are found by their
    metal: small regions closed by their own outline that hold the steel's
    highlight, with their grips.

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

ROOT = TOOLS.parent
CHARS = ROOT / 'assets/sprites/characters'


def hx(v):
    return (v >> 16) & 255, (v >> 8) & 255, v & 255


def lum(c):
    return .299 * c[0] + .587 * c[1] + .114 * c[2]


INK = hx(0x252018)
SUIT = [hx(c) for c in (0x5a4410, 0x86661c, 0xb08a2c, 0xd2ab3c, 0xe8c454, 0xf6dc86)]
RUBBER = [hx(c) for c in (0x15160f, 0x24251f, 0x34352e, 0x4a4b43, 0x66675e)]
VISOR = [hx(c) for c in (0x101c23, 0x23444f, 0x416577, 0x8ca6b3, 0xc9d8d8)]
AMBER_VISOR = [hx(c) for c in (0x142b32, 0x74301a, 0xad4018, 0xd45c22, 0xe5a56c)]
ARMOR = [hx(c) for c in (0x171923, 0x272a38, 0x3b3e4e, 0x555969, 0x777e8c)]
TAPE = [hx(c) for c in (0x5c625c, 0x8a918a, 0xb9c0b6, 0xdfe5dc)]


def ramp_map(colors, ramp, lo=1, hi=None):
    """Each colour onto the ramp by its brightness within its own material."""
    colors = [hx(c) if isinstance(c, int) else c for c in colors]
    hi = len(ramp) - 1 if hi is None else hi
    ls = [lum(c) for c in colors]
    a, b = min(ls), max(ls)
    out = {}
    for c, l in zip(colors, ls):
        t = 0 if b == a else (l - a) / (b - a)
        out[c] = ramp[lo + round(t * (hi - lo))]
    return out


# ---------------------------------------------------------------- the sheriff

COW_HAIR = [0x6b333a, 0x902004, 0xd03305]
COW_HAT = [0x4a4033, 0x75654d, 0x45382e, 0x36271d]
COW_SKIN = [0xebc1a4, 0xd7a786, 0xbf8964, 0xa87057, 0xc59174, 0x8f5c4f]
COW_CLOTH = {
    'wine': [0x6f2638, 0x924657, 0x743044, 0x995367, 0x441c2a, 0x4c2633],
    'slate': [0x4b464b, 0x777174, 0x625c61, 0x39353a, 0x605d74, 0x2a2a30, 0x4a4a54, 0x74747e, 0x1e1a20],
    'grey': [0x5d6870, 0x4c535b, 0x30343b, 0x364149, 0x29343b, 0x777e85, 0x404c53, 0x727f86, 0x9aa0a8],
}
COW_LEATHER = [0x483326, 0x6f4d33, 0x35271d, 0x60432e, 0x70462c, 0x8a6448, 0x96745a, 0xa27248, 0x916c48, 0x80633f,
               0x9a643a, 0x2c2c2c, 0x424242]
COW_BRASS = [0x9e7c42, 0xa27d43, 0xb59050, 0xb6985c, 0xc2a66e, 0xc9ab6d, 0xdbc58d, 0xb99a62, 0x77603c]
COW_LACE = [0xe0dbc9, 0xbdbbb1, 0x96948b, 0xd8d0c0, 0xe6dcc0, 0xf0ecdc, 0xb8ac94, 0x9a9488]
# The gun: its steel (shared with her trousers' greys) and its grip.
COW_GUN_STEEL = {hx(c) for c in (0x30343b, 0x4c535b, 0x777e85, 0xb3b8b6, 0xa1aaa9, 0x747b77)}
COW_GUN_SHINE = {hx(c) for c in (0xb3b8b6, 0xa1aaa9, 0x747b77)}
COW_GUN_GRIP = {hx(c) for c in (0xa27248, 0x70462c, 0xb59050, 0xe0dbc9)}


def cowgirl_palette():
    m = {}
    for colors in COW_CLOTH.values():
        m.update(ramp_map(colors, SUIT, 0, 5))
    m.update(ramp_map(COW_HAIR, SUIT, 1, 4))
    m.update(ramp_map(COW_HAT, SUIT, 1, 4))
    m.update(ramp_map(COW_LEATHER, RUBBER, 0, 4))
    m.update(ramp_map(COW_BRASS, TAPE, 0, 3))
    m.update(ramp_map(COW_LACE, SUIT, 3, 5))
    m.update(ramp_map(COW_SKIN, SUIT, 2, 5))   # Neck and chest: the suit over them
    return m


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


def cowgirl_guns(px):
    """Her revolvers: small regions of steel closed by their own outline that
    hold the steel's highlight, and the grip pieces touching them."""
    steel = [p for p, c in px.items() if c[:3] in COW_GUN_STEEL]
    gun = set()
    for g in components(steel, COW_GUN_STEEL, px):
        if 3 <= len(g) <= 90 and any(px[p][:3] in COW_GUN_SHINE for p in g):
            gun.update(g)
    near = set()                                 # Steel shapes beside a gun are of the gun
    for g in components(steel, COW_GUN_STEEL, px):
        if set(g) & gun or len(g) > 14: continue
        if any((x + dx, y + dy) in gun for x, y in g for dx in range(-2, 3) for dy in range(-2, 3)):
            near.update(g)
    gun |= near
    grip = [p for p, c in px.items() if c[:3] in COW_GUN_GRIP]
    for g in components(grip, COW_GUN_GRIP, px):
        if len(g) <= 12 and any((x + dx, y + dy) in gun for x, y in g for dx, dy in
                                ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2))):
            gun.update(g)
    return gun


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


HOOD_R = 7.3


def hood(px, out, w, h, gun):
    """The sheriff's head in a round hood. Her hat (crown, brim, band and
    feather, whatever their colours) goes wherever it lies outside the hood;
    the hood closes round where her head was, lit from the upper left, with
    the visor where her face looks out; hair on her shoulders stays as the
    hood's cape (already yellow in out)."""
    hat_cols = {hx(c) for c in COW_HAT}
    hair_cols = {hx(c) for c in COW_HAIR}
    skin_cols = {hx(c) for c in COW_SKIN}
    leather = {hx(c) for c in COW_LEATHER}
    hat = [p for p, c in px.items() if c[:3] in hat_cols]
    removed = set()
    heads = []
    for head in clusters(hat, 3):
        if len(head) < 12: continue
        hs = set(head)
        hcx = sum(p[0] for p in head) / len(head)
        hcy = sum(p[1] for p in head) / len(head)
        box = [(x, y) for y in range(int(hcy) - 18, int(hcy) + 19) for x in range(int(hcx) - 18, int(hcx) + 19)
               if (x, y) in px]
        near = [p for p in box if px[p][:3] in skin_cols and
                any((p[0] + dx, p[1] + dy) in hs for dx in range(-6, 7) for dy in range(-6, 7)
                    if abs(dx) + abs(dy) <= 6)]
        if near:                                       # Her face: the skin by the hat, then all of it round there
            fx = sum(p[0] for p in near) / len(near)
            fy = sum(p[1] for p in near) / len(near)
            face = [p for p in box if px[p][:3] in skin_cols and math.hypot(p[0] - fx, p[1] - fy) <= 6]
            fx = sum(p[0] for p in face) / len(face)
            fy = sum(p[1] for p in face) / len(face)
            cx, cy = fx + .38 * (hcx - fx), fy + .38 * (hcy - fy)
        else:
            fx, fy = hcx, hcy + 4
            cx, cy = hcx, hcy + 3
        r = HOOD_R
        up = ((hcx - fx), (hcy - fy))                  # Toward the crown, however she lies
        n = math.hypot(*up) or 1.0
        up = (up[0] / n, up[1] / n)
        heads.append((cx, cy))

        def outside(q):
            return math.hypot(q[0] + .5 - cx, q[1] + .5 - cy) > r + .5

        def high(q):                                   # On the crown's side of her head
            return (q[0] + .5 - cx) * up[0] + (q[1] + .5 - cy) * up[1] > r * .2

        def hat_stuff(q):
            c = px[q][:3]
            if q in gun or not outside(q) or math.hypot(q[0] - cx, q[1] - cy) > r + 17:
                return False
            return c in hat_cols or c in leather or c == INK or (c in hair_cols and high(q))

        todo = [q for q in head if outside(q)]
        gone = set(todo)
        while todo:
            x, y = todo.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in px and q not in gone and hat_stuff(q):
                    gone.add(q)
                    todo.append(q)
        for q in gone:
            out.pop(q, None)
        removed |= gone
        # The hood itself, over what was head.
        head_stuff = hat_cols | hair_cols | skin_cols | {INK} | leather
        vx, vy = fx + .15 * (fx - cx), fy + .15 * (fy - cy)   # The visor, where she looks out
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if not (0 <= x < w and 0 <= y < h) or (x, y) in gun: continue
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if d > r + .5: continue
                c = px.get((x, y), (0, 0, 0, 0))
                if c[3] and c[:3] not in head_stuff and (x, y) not in removed:
                    continue                                  # Her collar and shoulders stay in front
                if d > r - .5:
                    out[(x, y)] = INK + (255,)
                    continue
                # A face shield closes around her whole face, rather than the
                # narrow eye slit of the old recoloured cowboy hat.
                e = ((x + .5 - vx) / 4.9) ** 2 + ((y + .5 - vy) / 5.5) ** 2
                if e <= 1 and d <= r - 1.5:
                    t = (y + .5 - (vy - 5.5)) / 11
                    col = VISOR[2] if t < .35 else VISOR[1] if t < .72 else VISOR[0]
                    if e > .70: col = VISOR[0]                        # Rubber seal, blue glass edge
                    out[(x, y)] = col + (255,)
                    continue
                nx, ny = (x + .5 - cx) / r, (y + .5 - cy) / r
                k = -.62 * nx - .78 * ny                              # Light from the upper left
                idx = 5 if k > .55 else 4 if k > .2 else 3 if k > -.2 else 2 if k > -.55 else 1
                out[(x, y)] = SUIT[idx] + (255,)
        # The light on the visor: a short streak at its upper left.
        gx, gy = round(vx - 2.2), round(vy - 1.4)
        for q, col in (((gx, gy), VISOR[4]), ((gx + 1, gy), VISOR[3]), ((gx - 1, gy + 1), VISOR[3])):
            if q in out and out[q][:3] in VISOR:
                out[q] = col + (255,)
    # Close the outline where the hat came away.
    for (x, y) in removed:
        if (x, y) in out: continue
        if any((x + dx, y + dy) in out and out[(x + dx, y + dy)][:3] != INK
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            out[(x, y)] = INK + (255,)
    return heads


def cowgirl_coveralls(px, out, heads, gun, sheet, w, h):
    """Loose neutral overalls replace the fitted outfit's body and trousers.

    The original moving legs and sleeves provide the motion, not the corset,
    waist or chaps. Added fabric has the same volume at chest, waist and hip.
    """
    hair = {hx(c) for c in COW_HAIR}
    wine = {hx(c) for c in (0x6f2638, 0x924657, 0x441c2a)}   # Her sleeves, not her sash
    protected = gun | {p for p, c in px.items() if c[:3] == INK and
                       any((p[0] + dx, p[1] + dy) in gun for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    for cx, cy in heads:
        frame = int(cx) // 80 if sheet == 'faint' else 0
        angle = (0, 0, 0, 0, 30, 60, 90, 90)[frame] if sheet == 'faint' else 0
        a = math.radians(angle)
        ux, uy, dx, dy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)

        def local(p):
            return (p[0] - cx) * ux + (p[1] - cy) * uy, (p[0] - cx) * dx + (p[1] - cy) * dy

        def world(u, v):
            return round(cx + u * ux + v * dx), round(cy + u * uy + v * dy)

        nearby = {p: c for p, c in px.items() if abs(local(p)[0]) < 23 and -11 < local(p)[1] < 48}
        # The old hair and shoulder cape are not part of the sealed suit.
        for p, c in nearby.items():
            if p in protected: continue
            is_hair_edge = c[:3] == INK and any(px.get((p[0] + x, p[1] + y), (0, 0, 0, 0))[:3] in hair
                for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if (c[:3] in hair or is_hair_edge) and math.hypot(p[0] + .5 - cx, p[1] + .5 - cy) > HOOD_R + .5:
                out.pop(p, None)
        # Brown hat/neck remnants were mapped to black rubber before the
        # hood was rebuilt. They are neither gloves nor the hood's own rim.
        collar_materials = hair | {hx(c) for c in COW_LEATHER} | {hx(0x1e1a20)}
        remnants = {p for p, c in nearby.items() if 3 <= local(p)[1] <= 9 and
                    c[:3] in collar_materials and p not in protected and
                    math.hypot(p[0] + .5 - cx, p[1] + .5 - cy) > HOOD_R + .5}
        for p, c in nearby.items():
            if p in protected or math.hypot(p[0] + .5 - cx, p[1] + .5 - cy) <= HOOD_R + .5:
                continue
            if p in remnants or c[:3] == INK and any((p[0] + dx, p[1] + dy) in remnants
                                                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.pop(p, None)
        # Rebuild legs on hip/knee/ankle chains. Copying and thickening chaps
        # retained their triangular stance, holster spikes and knee bulges.
        from hazmat_legs import frame_width, raster, rig, trousers
        pose = int(cx) // frame_width(sheet)
        pelvis, chains = rig(sheet, pose, cx, cy, local, world)
        hip_u, hip_v = local(pelvis)
        for p in nearby:
            if local(p)[1] >= min(23, hip_v - 1) and p not in protected:
                out.pop(p, None)
        pants = trousers(pelvis, chains, local, world, INK, SUIT, RUBBER)
        out.update({p: c for p, c in pants.items() if p not in protected})
        # Compact air pack behind the shoulders, with two retaining straps.
        pack = {}
        for v in range(9, 25):
            for u in range(-11, -7):
                edge = u in (-11, -8) or v in (9, 24)
                col = RUBBER[0] if edge else RUBBER[3] if u == -10 else RUBBER[1]
                if v in (13, 21): col = RUBBER[0]
                pack[u, v] = col + (255,)
        out.update({p: c for p, c in raster(pack, local, world).items() if p not in protected})
        # One continuous baggy torso: no narrowing waist or bust planes.
        end = max(14, round(hip_v + 3)) if sheet.startswith('car') else 27
        torso = {}
        for v in range(7, end):
            half = 5 if v == 7 else 7 if v == 8 else 8
            bend = hip_u * max(0, min(1, (v - 8) / max(1, end - 10)))
            for u in range(-half, half + 1):
                col = INK if abs(u) == half else SUIT[4 if u < -2 else 3 if u < 4 else 2]
                if 11 <= v <= 25 and u in (-6, -5, 5, 6): col = RUBBER[2 if u < 0 else 1]
                if 12 <= v <= 26 and u == 1: col = SUIT[1]  # Closed zip, no rigid corset panel.
                if v in (20, 21) and -5 <= u <= 5: col = RUBBER[1]
                if (v, u) in ((16, -3), (17, -2), (17, -1), (24, 3), (25, 4), (26, -3)):
                    col = SUIT[2]  # Small fabric creases, never a fitted waist.
                torso[round(u + bend), v] = col + (255,)
        out.update({p: c for p, c in raster(torso, local, world).items() if p not in protected})
        # Sleeves and working gloves stay in front of the loose torso.
        # The jacket's front lapels stay covered; its outer sleeves still act.
        for p, c in nearby.items():
            u, v = local(p)
            sleeve = c[:3] in wine and (abs(u) >= 7 or v < 11)
            glove = c[:3] in {hx(c) for c in COW_LEATHER} and 10 <= v < 25 and abs(u) > 5
            if (sleeve or glove) and p not in protected:
                out[p] = (RUBBER[2] if glove else SUIT[4 if lum(c) > 90 else 2]) + (255,)
        for p in protected:
            if p in px: out[p] = px[p]


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
    """A sheet of hers in the suit: composed on her own poses (hazmat_figure) or, sitting,
    fainting and in a car, made from the sheet itself."""
    import hazmat_figure
    if sheet in hazmat_figure.UPRIGHT + hazmat_figure.ARMS_ONLY:
        out = hazmat_figure.sheet_pixels(sheet, SUIT, RUBBER, VISOR)
        out = {p: c for p, c in out.items() if 0 <= p[0] < w and 0 <= p[1] < h}   # Of the sheet asked for
        if sheet in hazmat_figure.UPRIGHT:
            close_outline(out, w, h, hazmat_figure.hazmat_legs.frame_width(sheet))
            drop_floating_ink(out)
        else:                                            # Exactly what her own sheet covers, its outline too
            out = {p: out.get(p, INK + (255,)) for p in px}
        return out
    if sheet == 'flashlight':
        return dict(px)
    if sheet == 'car':                                   # Her own joints through the car, the suit's parts
        from make_car_passage import Figure, character_sheet
        image = character_sheet(Figure('cowgirl', suit=(SUIT, RUBBER, VISOR)))
        out = {(i % w, i // w): c for i, c in enumerate(image.px) if c[3]}
        drop_floating_ink(out)
        return out
    if sheet == 'faint':                                 # Her suited stance, falling as she does
        from make_faint import make
        fallen = make(to_image(42, 67, suit_cowgirl({}, 42, 67, 'stand')))
        out = {(i % w, i // w): c for i, c in enumerate(fallen.px) if c[3]}
        drop_floating_ink(out)
        return out
    # These sheets can still carry the author's pre-finish colour tags.
    # Normalize their material labels in memory; never fall back to the normal
    # hat or bare face when an action uses that older source palette.
    legacy_skin = {hx(v) for v in (0xfedca3, 0xd99a5b, 0x89411f, 0x8a4322)}
    if any(c[:3] in legacy_skin for c in px.values()):
        from detail_cowgirl import finish, WIDTHS
        fw = WIDTHS.get(sheet, 81)
        normalized = {}
        for frame in range(w // fw):
            part = {(x - frame * fw, y): c for (x, y), c in px.items() if x // fw == frame}
            normalized.update({(x + frame * fw, y): c for (x, y), c in finish(part, sheet).items()})
        px = normalized
    pal = cowgirl_palette()
    gun = cowgirl_guns(px)
    out = {p: c if p in gun else pal.get(c[:3], c[:3]) + (c[3],) for p, c in px.items()}
    heads = hood(px, out, w, h, gun)
    cowgirl_coveralls(px, out, heads, gun, sheet, w, h)
    drop_floating_ink(out)
    return out


def close_outline(out, w, h, width):
    """An outline where the suit's own cloth or rubber meets nothing."""
    own = {c for c in SUIT + RUBBER}
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
SWAT_SKIN = [0xedc09e, 0xb98f71, 0xebc1a4, 0xd7a786, 0xbf8964]
SWAT_LENS = [0x93ae36, 0xd4d990, 0x8fa83e, 0xb6ca64, 0xb5ca5a, 0xd3df97, 0x485222, 0x435327, 0x93996d,
             0x4d5c3b, 0x2e3d2c, 0xb9c4ad]
SWAT_STRAP = [0xc2a66c, 0xd5d0b9, 0xb4b09a]


def swat_palette():
    m = {}
    m.update(ramp_map(SWAT_CLOTH, SUIT, 1, 5))       # Its dark uniform: no deeper than her shade
    m.update(ramp_map(SWAT_LEATHER, RUBBER, 0, 4))
    m.update(ramp_map(SWAT_SKIN, VISOR, 0, 2))
    m.update(ramp_map(SWAT_LENS, VISOR, 1, 4))
    m.update(ramp_map(SWAT_STRAP, TAPE, 1, 3))
    return m


TAG, ARM_TAG, PLATE_TAG, PACK_TAG, GLOVE_TAG = 253, 252, 251, 250, 249


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
                if c[3]: body.set(x, y, c[:3] + (GLOVE_TAG,))
        # Segmented carrier on the chest; the sleeves are composed later.
        for y in range(27 + dy, 40 + dy):
            for x in range(14 + dx, 28 + dx):
                c = body.get(x, y)
                if c[3]: body.set(x, y, c[:3] + (PLATE_TAG,))
        # Air bottle with a dark protective cradle behind the left shoulder.
        for y in range(26 + dy, 44 + dy):
            for x in range(7 + dx, 14 + dx):
                u, v = x - dx, y - dy
                if (u in (7, 13) and v in (26, 43)) or body.get(x, y)[3]: continue
                col = ARMOR[0] if u in (7, 13) or v in (26, 43) else ARMOR[3] if u == 8 else ARMOR[1]
                if v in (30, 39): col = ARMOR[4] if u == 8 else ARMOR[2]
                body.set(x, y, col + (PACK_TAG,))
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
                if c[3]: body.set(x, y, c[:3] + (GLOVE_TAG,))
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
                                if rgba[i * 4 + 3] in (TAG, ARM_TAG, PLATE_TAG, PACK_TAG, GLOVE_TAG)}
            # Passage poses are generated separately from the normal actions.
            # In particular their slung rifle still has its original material.
            for name, kind in (('car', 'rifle'), ('car_shotgun', 'shotgun')):
                figure = make_car_passage.Figure('swat', kind)
                figure.boot = {key: c[:3] + (GLOVE_TAG,) for key, c in figure.boot.items()}
                for p, c in list(figure.torso.items()):
                    if 26 <= p[0] <= 39 and 34 <= p[1] <= 46:
                        figure.torso[p] = c[:3] + (PLATE_TAG,)
                img = make_car_passage.character_sheet(figure)
                sheets[name] = {(i % img.width, i // img.width): c for i, c in enumerate(img.px)
                                if c[3] in (TAG, ARM_TAG, PLATE_TAG, PACK_TAG, GLOVE_TAG)}
            return sheets
    finally:
        for module, name, value in reversed(patches):
            setattr(module, name, value)


def swat_hood(px, out, masks, sheet):
    """Sealed hood with a single full-face shield, without night-vision tubes."""
    lens_cols = {hx(c) for c in SWAT_LENS}
    lenses = [p for p, c in px.items() if c[:3] in lens_cols and masks.get(p, (0, 0, 0, 0))[3] != TAG]
    for group in clusters(lenses, 5):
        if len(group) < 6: continue
        lx, ly = (sum(p[i] for p in group) / len(group) for i in (0, 1))
        angle = 0
        if sheet == 'faint':
            angle = (0, 0, 0, 0, 30, 60, 90, 90)[int(lx) // 80]
        a = math.radians(angle)
        ux, uy, dx, dy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        cx, cy = lx - 6 * ux + 5 * dx, ly - 6 * uy + 5 * dy
        protected = {p for p, c in masks.items() if c[3] in (TAG, ARM_TAG, GLOVE_TAG, PLATE_TAG)}
        # Remove the helmet shell, mask and protruding optical tubes together.
        for p in list(out):
            u = (p[0] + .5 - cx) * ux + (p[1] + .5 - cy) * uy
            v = (p[0] + .5 - cx) * dx + (p[1] + .5 - cy) * dy
            if -17 <= u <= 18 and -15 <= v <= 11 and p not in protected:
                out.pop(p)
        for y in range(round(cy - 15), round(cy + 16)):
            for x in range(round(cx - 15), round(cx + 16)):
                if (x, y) in protected: continue
                u, v = (x + .5 - cx) * ux + (y + .5 - cy) * uy, (x + .5 - cx) * dx + (y + .5 - cy) * dy
                e = (u / 9) ** 2 + (v / 11) ** 2
                if e > 1: continue
                col = INK
                if e < .84:
                    k = -.55 * u / 9 - .83 * v / 11
                    col = SUIT[5 if k > .5 else 4 if k > .15 else 3 if k > -.3 else 2 if k > -.65 else 1]
                    shield = ((u - 3) / 5.3) ** 2 + ((v - 1) / 7) ** 2
                    if shield < 1:
                        col = AMBER_VISOR[0] if shield > .72 else AMBER_VISOR[3] if v < -1 else AMBER_VISOR[2] if v < 3 else AMBER_VISOR[1]
                        if -1 <= u <= 0 and -4 <= v <= 0 and shield < .6: col = AMBER_VISOR[4]
                    # Reinforced collar on the lower edge, joined to carrier.
                    if v > 8: col = ARMOR[2] if v < 9 else ARMOR[0]
                out[x, y] = col + (255,)


def suit_swat(px, masks, sheet=''):
    pal = swat_palette()
    plate_map = ramp_map(SWAT_CLOTH + SWAT_LEATHER, ARMOR, 0, 4)
    out = {}
    for p, c in px.items():
        tag = masks.get(p, (0, 0, 0, 0))[3]
        if tag == TAG: out[p] = c
        elif tag == PLATE_TAG: out[p] = plate_map.get(c[:3], ARMOR[1]) + (c[3],)
        elif tag == GLOVE_TAG: out[p] = RUBBER[1 if lum(c) < 75 else 3] + (c[3],)
        else: out[p] = pal.get(c[:3], c[:3]) + (c[3],)
    for p, c in masks.items():
        if c[3] == PACK_TAG: out[p] = c[:3] + (255,)
    # The existing knee pads move with the source legs, including the folded
    # jump and seated poses. Their light planes locate each pad without a
    # fixed rectangle pinned to the screen while the knee moves.
    knee_shine = {hx(v) for v in (0x77807b, 0x909d97, 0x727678)}
    frame_h = 82 if sheet.startswith('jump') else 80 if sheet.startswith('car') or max((p[1] for p in px), default=0) >= 67 else 67
    seeds = [p for p, c in px.items() if c[:3] in knee_shine and p[1] % frame_h >= frame_h - 25
             and masks.get(p, (0, 0, 0, 0))[3] not in (TAG, ARM_TAG, GLOVE_TAG)]
    for group in clusters(seeds, 1):
        if len(group) < 4: continue
        x0, x1 = min(p[0] for p in group) - 1, max(p[0] for p in group) + 2
        y0, y1 = min(p[1] for p in group) - 1, max(p[1] for p in group) + 1
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                p = x, y
                if p in px and px[p][:3] in plate_map and masks.get(p, (0, 0, 0, 0))[3] not in (TAG, ARM_TAG, GLOVE_TAG):
                    out[p] = plate_map[px[p][:3]] + (255,)
    swat_hood(px, out, masks, sheet)
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
