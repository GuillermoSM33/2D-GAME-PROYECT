#!/usr/bin/env python3
"""Rebuild the road's objects with weathered, material-specific pixel detail.

Usage: python3 tools/refine_terrain.py [assets_dir] [--preview PATH]

The geometry and animation come from make_terrain and make_city. Every run
starts with those drawings in memory, never with a previously refined PNG.
Wood has long fibres and end grain, metal has seams, rivets and clustered
corrosion, masonry has mortar and broken faces, canvas has folds and stitching.
The masks, frame sizes, warning markings and animation order are preserved.
Only the standard library is used.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import make_terrain as west
import make_city as city
import city_terrain as urban
from landscape_kit import hash2, seed_of
from make_sprites import Image, rgb


def source_assets() -> dict[str, Image]:
    """The original geometry, without writing houses, backgrounds or effects."""
    urban_barricades = Image(68 * 3 * len(urban.URBAN_BARRICADES), 26 + west.RAISE)
    for kind, draw in enumerate(urban.URBAN_BARRICADES):
        for state in range(3):
            frame = west.Frame(urban_barricades, (kind * 3 + state) * 68, 68, west.RAISE)
            draw(frame, state)
            frame.outline()
    out = {
        'barricade': west.clear_beside(west.join(west.make_barricade(), urban_barricades), 68,
                                      2, 5, 8, 11, 14, 17, 20, 23, 26),
        'barrel': west.make_barrel(), 'wall': west.clear_beside(west.make_wall(), 44, 2),
        'wall_ruins': west.make_wall_ruins(), 'facades': west.make_facades(),
        'door': west.join(west.make_door(), urban.make_urban_doors(west.DOOR_W, west.DOOR_H)),
        'dynamite': west.make_dynamite(), 'charge': west.make_charge(),
        'crate': west.clear_beside(west.make_crate(), 32, 10),
        'wire': west.clear_beside(west.make_wire(), 112, 2),
        'net': west.make_net(), 'snare': west.make_snare(), 'spikes': west.make_spikes(),
        'river': west.make_river(), 'river_front': west.make_river_front(),
        'puddle': west.make_puddle(), 'sign': west.make_sign(), 'bottles': west.make_bottles(),
        'trap': west.clear_beside(west.make_trap(), 48, 2), 'coffin': west.make_coffin(),
        'lamp': west.clear_beside(west.make_lamp(), 14, 1), 'fire': west.make_fire(),
        'bench': west.make_bench(),
        'campfire': west.join(west.make_campfire(), urban.make_campfire_barrel(48, 56, 0)),
        'supply': west.make_supply(), 'goal': west.make_goal(),
        'burner': city.make_burner(), 'hydrant': city.make_hydrant(),
        'siren_car': city.make_siren_car(), 'car_wreck': city.make_car_wreck(),
        'vehicles': city.make_vehicles(), 'supply_truck': city.make_supply_truck(),
        'outpost': city.make_outpost(), 'city_fronts': city.make_city_fronts(),
        'train': city.make_train(),
    }
    return {f'sprites/terrain/{name}.png': image for name, image in out.items()}


# Frame widths are art pixels, not world coordinates. A material's grain stays
# in the same place in all states of an object, including its damaged states.
FRAME_WIDTH = {
    'barricade': 68, 'barrel': 26, 'wall': 44, 'wall_ruins': 180, 'facades': 180,
    'door': 44, 'dynamite': 24, 'charge': 14, 'crate': 32, 'wire': 112,
    'net': 84, 'snare': 72, 'spikes': 40, 'river': 200, 'river_front': 200,
    'puddle': 64, 'sign': 22, 'bottles': 40, 'trap': 48, 'coffin': 32,
    'lamp': 14, 'fire': 32, 'bench': 76, 'campfire': 48, 'supply': 100,
    'goal': 108, 'burner': 40, 'hydrant': 20, 'siren_car': 136, 'car_wreck': 136,
    'vehicles': 184, 'supply_truck': 184, 'outpost': 168, 'city_fronts': 240,
    'train': 300,
}

WOOD = set(west.WOOD + west.GREY_WOOD + west.ROAD_PAL['wood'])
IRON = set(west.IRON + urban.IRON + city.IRON)
IRON.update(rgb(value) for value in (0x34343c, 0x54545e, 0xc8c8d0, 0x3a3a42, 0x4c4c56, 0x62626c))
FABRIC = set(west.CANVAS + west.SAND + west.OLIVE)
MASONRY = set(urban.CONCRETE + urban.BRICK)
for key in ('stone',):
    MASONRY.update(west.ROAD_PAL.get(key, []))
PAINT = set(west.RED + urban.OLIVE + urban.BLUE + urban.CAR_PAINT)
for ramp in city.PAINTS.values():
    PAINT.update(ramp)
GLASS = set(urban.GLASS + city.GLASS)
FLAME = set(west.FLAME.values())
LIGHTS = set(west.ROAD_PAL['glow'] + west.LAMP + city.GLOW)


def tone(color, amount: int, warm: int = 0):
    """Small discrete shifts retain the original object's readable palette."""
    r, g, b, a = color
    return (max(0, min(255, r + amount + warm)), max(0, min(255, g + amount)),
            max(0, min(255, b + amount - warm)), a)


def material(name: str, color) -> str:
    if color[3] < 250:
        return ''
    if color in FLAME or color in LIGHTS or max(color[:3]) > 235:
        return ''  # Fire, lamps, labels and safety symbols must remain clear.
    if color in GLASS:
        return 'glass'
    if name == 'barrel' and color in west.RED:
        return 'wood'
    if color in WOOD:
        return 'wood'
    if color in IRON:
        return 'iron'
    if color in MASONRY:
        return 'stone'
    if color in FABRIC:
        return 'cloth'
    if color in PAINT:
        return 'paint'
    r, g, b, _a = color
    light = (r * 3 + g * 6 + b) // 10
    if light < 28:
        return ''  # Keep outlines, joints, doorways and deep shadows intact.
    if name in ('river', 'river_front', 'puddle'):
        return ''
    if name in ('net', 'snare') and g > r * 1.06 and g > b * 1.15:
        return 'leaf'
    if name in ('wall_ruins', 'facades', 'city_fronts') and r > g * 1.08 and g > b * 1.16:
        return 'stone' if light > 75 else ''
    if name in ('campfire', 'burner') and abs(r - g) < 23 and abs(g - b) < 18:
        return 'stone'
    return ''


def refine(name: str, source: Image) -> Image:
    """Finish surfaces while leaving the original drawing's boundaries alone."""
    out = Image(source.width, source.height)
    out.px = list(source.px)
    fw = FRAME_WIDTH[name]
    assert source.width % fw == 0, (name, source.width, fw)
    kinds = [material(name, color) for color in source.px]
    seed = seed_of(name)

    def at(x: int, y: int, kind: str, frame: int) -> bool:
        return (frame * fw <= x < (frame + 1) * fw and 0 <= y < source.height
                and kinds[y * source.width + x] == kind)

    for y in range(source.height):
        for sx in range(source.width):
            i = y * source.width + sx
            kind, color = kinds[i], source.px[i]
            if not kind:
                continue
            x, frame = sx % fw, sx // fw
            # A fine detail must be inside its material: a stripe may never
            # continue over a rail, a window, a character-sized doorway or air.
            broad = all(at(sx + dx, y + dy, kind, frame) for dx, dy in
                        ((-1, 0), (1, 0), (0, -1), (0, 1)))
            if not broad:
                continue
            grain = hash2(x // 7, y // 3, seed)
            stain = hash2(x // 5, y // 8, seed + 7)
            if kind == 'wood':
                # Upright timbers and coffin staves have upright fibres; broad
                # wagon sides, bench slats and freight crates have long fibres.
                vertical = name in ('wall', 'door', 'coffin', 'net', 'goal', 'snare')
                along, across = (y, x) if vertical else (x, y)
                strand = across + round(math.sin(along * .17 + (across // 4) * 2.3))
                if strand % 6 == 0 and hash2(along // 6, across // 4, seed + 3) < .68:
                    out.px[i] = tone(color, -17, 1)
                elif strand % 6 == 1 and grain > .55:
                    out.px[i] = tone(color, 10, 2)
                # Knots are curved rings, distinct from the long fibres.
                kx, ky = (x % 23) - 11, (y % 19) - 9
                radius = (kx * kx / (3.1 if vertical else 17.0)
                          + ky * ky / (17.0 if vertical else 3.1))
                if .85 < radius < 2.05 and hash2(x // 23, y // 19, seed) > .42:
                    out.px[i] = tone(color, -21, 2)
                elif radius < .25 and hash2(x // 23, y // 19, seed) > .42:
                    out.px[i] = tone(color, -31)
                # Weathering collects at the foot and under projecting joints.
                if y > source.height - 6 and stain > .5:
                    out.px[i] = tone(out.px[i], -8, -1)
            elif kind in ('iron', 'paint'):
                # Sheets are joined, bolted, scratched and oxidized in clusters.
                panel = x % 27
                if panel == 0 and all(at(sx, y + d, kind, frame) for d in (-3, -2, 2, 3)):
                    out.px[i] = tone(color, -19)
                elif panel == 1 and y % 13 == 3:
                    out.px[i] = tone(color, 25)
                elif y % 19 == 0 and panel in (2, 24):
                    out.px[i] = tone(color, 26)
                elif y % 19 == 1 and panel in (2, 24):
                    out.px[i] = tone(color, -26)
                elif y % 11 == 3 and x % 17 in (5, 6, 7) and stain > .28:
                    out.px[i] = tone(color, 14, -2)
                elif grain > .75 and stain > .56:
                    # Brown corrosion occurs as small coherent islands, never
                    # a salt-and-pepper overlay on every flat surface.
                    r, g, b, a = color
                    out.px[i] = (min(159, (r * 2 + 124) // 3),
                                 min(108, (g * 2 + 65) // 3),
                                 min(88, (b * 2 + 38) // 3), a)
                elif stain < .13 and x % 8 < 2:
                    out.px[i] = tone(color, -12, 2)
            elif kind == 'stone':
                # Staggered joints, worn corners and a shaded fracture face.
                course = y // 7
                joint = (x + (course % 2) * 9) % 19
                if y % 7 == 0 and at(sx - 2, y, kind, frame) and at(sx + 2, y, kind, frame):
                    out.px[i] = tone(color, -22)
                elif joint == 0 and y % 7 > 1:
                    out.px[i] = tone(color, -19)
                elif y % 7 == 1 and joint > 2:
                    out.px[i] = tone(color, 11, 1)
                elif (x + y // 3) % 31 == 7 and grain > .62:
                    out.px[i] = tone(color, -22)
                elif grain > .81 and (x % 5 < 3 and y % 3 == 1):
                    out.px[i] = tone(color, 10)
            elif kind == 'cloth':
                # Linen has woven threads and discrete stitches, not gloss.
                if y % 9 == 3 and x % 3 == 0 and stain > .26:
                    out.px[i] = tone(color, -15)
                elif x % 13 in (2, 3) and y % 6 < 3:
                    out.px[i] = tone(color, -9)
                elif (x + y) % 8 == 0 and grain > .43:
                    out.px[i] = tone(color, 7)
                elif y > source.height * .65 and stain > .74:
                    out.px[i] = tone(color, -12, 2)
            elif kind == 'leaf':
                # Leaf clusters have a lit top and a shadowed underside.
                shape = (x % 7 - 3) ** 2 + (y % 6 - 3) ** 2
                if shape < 4:
                    out.px[i] = tone(color, 13, -3)
                elif y % 6 == 5:
                    out.px[i] = tone(color, -11)
            elif kind == 'glass':
                # Long reflections stay diagonal and sparse, the pane reads
                # as a plane rather than a block of shiny plastic.
                if (x + y // 2) % 29 in (4, 5) and stain > .16:
                    out.px[i] = tone(color, 16, -3)
                elif y % 23 == 9 and x % 29 < 7:
                    out.px[i] = tone(color, -8)
    construction_details(name, out, source)
    object_craft(name, out, source)
    return out


def construction_details(name: str, out: Image, source: Image) -> None:
    """Small construction features placed for the particular object, not noise."""
    fw = FRAME_WIDTH[name]
    dark, steel, shine = rgb(0x25262a), rgb(0x636366), rgb(0xa7a18f)

    def pixel(frame: int, x: int, y: int, color, allowed=None) -> None:
        sx = frame * fw + x
        old = source.get(sx, y)
        if not old[3] or old in LIGHTS or (allowed and old not in allowed):
            return
        out.set(sx, y, color)

    def line(frame: int, x0: int, y0: int, x1: int, y1: int, color, allowed=None) -> None:
        length = max(abs(x1 - x0), abs(y1 - y0), 1)
        for step in range(length + 1):
            pixel(frame, round(x0 + (x1 - x0) * step / length),
                  round(y0 + (y1 - y0) * step / length), color, allowed)

    if name == 'train':
        # Cooling shutters, individual louvers, hatch fasteners, pipe and hand
        # rails make the locomotive read as a machine at the same distance as
        # the detailed rails and industrial background.
        for x0, x1 in ((179, 199), (207, 229)):
            line(0, x0, 47, x1, 47, shine)
            line(0, x0, 48, x0, 58, dark)
            line(0, x1, 48, x1, 58, dark)
            for x in range(x0 + 2, x1 - 1, 3):
                line(0, x, 49, x, 56, dark)
                line(0, x + 1, 50, x + 1, 56, steel)
            for x in (x0, x1):
                pixel(0, x, 48, shine)
                pixel(0, x, 57, shine)
        for y in (74, 75):
            line(0, 177, y, 240, y, steel if y == 74 else dark)
        for x in (181, 204, 227):
            line(0, x, 74, x, 85, dark)
            pixel(0, x - 1, 75, shine)
        for x in range(251, 279, 5):
            line(0, x, 80, x + 3, 80, shine)
            line(0, x, 81, x + 3, 81, dark)
        # Freight-car door runners and cross braces carry scraped steel at
        # the places they slide, while the original tilt remains intact.
        for x0 in (40, 76):
            line(0, x0 + 2, 43, x0 + 20, 43, steel)
            line(0, x0 + 2, 44, x0 + 20, 44, dark)
            for y in range(48, 79, 7):
                pixel(0, x0 + 2, y, shine)
                pixel(0, x0 + 20, y, shine)
            line(0, x0 + 3, 78, x0 + 18, 50, rgb(0x52352a))
    elif name in ('vehicles', 'supply_truck', 'siren_car', 'car_wreck'):
        for frame in range(source.width // fw):
            # Stamped bodywork has shorter, grouped scratches at wheel height;
            # cabin glass, white police doors and emblems remain unobscured.
            for x0 in range(17, fw - 12, 31):
                y = source.height - 15 - (x0 // 31) % 3
                line(frame, x0, y, x0 + 8, y - 1, rgb(0x716557), PAINT)
                line(frame, x0 + 2, y + 1, x0 + 9, y, rgb(0x3d372f), PAINT)
            # Small fasteners and reflected wear on the original handles.
            for x in range(15, fw - 10, 29):
                pixel(frame, x, source.height - 23, shine, IRON)
    elif name == 'coffin':
        for frame in (0, 2):
            # Forged hinges on the left, a worn brass lock plate on the right.
            for y in (26, 49):
                line(frame, 6, y, 10, y, steel)
                pixel(frame, 6, y - 1, shine)
                pixel(frame, 9, y + 1, dark)
            for y in range(34, 40):
                for x in range(23, 25):
                    pixel(frame, x, y, rgb(0x9e814e) if x == 23 else rgb(0x55422d))
            pixel(frame, 23, 37, dark)
    elif name == 'outpost':
        for frame in (0, 1):
            # Tuning scale, speaker slots and dials on the field radio.
            for x in range(33, 39, 2):
                pixel(frame, x, 53, rgb(0xb3b18c))
            for y in range(54, 59, 2):
                line(frame, 42, y, 46, y, dark)
            pixel(frame, 34, 58, shine)
            pixel(frame, 38, 58, shine)
    elif name == 'hydrant':
        for frame in (0, 1):
            # Casting seam, a ring at the base and chips around the bolts;
            # the leaking mouth and its water retain their original colors.
            for y in range(18, 25):
                pixel(frame, 11, y, rgb(0x7a2d23), set(west.RED))
            for x in range(6, 14):
                pixel(frame, x, 23, rgb(0xa13f2b), set(west.RED))
            for x, y in ((7, 19), (8, 20), (12, 22), (6, 24), (13, 24)):
                pixel(frame, x, y, rgb(0x92705a), set(west.RED))
        for x in (6, 13):
            pixel(0, x, 5, steel)
        pixel(0, 9, 14, dark)
        pixel(0, 8, 13, shine)
    elif name in ('goal', 'supply', 'bench'):
        # Iron nails bite into the timber with a small pale abrasion beside
        # the hole. These are spaced by the joinery, not sprinkled on wood.
        for frame in range(source.width // fw):
            rows = (16, 43) if name == 'goal' else (33, 40) if name == 'supply' else (5, 19, 35)
            columns = (12, fw - 15) if name == 'goal' else (12, 30, 48, 66, 84) if name == 'supply' else (8, fw - 9)
            for y in rows:
                for x in columns:
                    pixel(frame, x, y, dark, WOOD)
                    pixel(frame, x - 1, y - 1, shine, WOOD)


def object_craft(name: str, out: Image, source: Image) -> None:
    """Joinery, equipment and wear drawn for each object at native resolution.

    These are placed construction details rather than another texture pass.
    All marks are clipped to the source object's existing material and mask.
    In particular nothing here adds a ray to a lamp or touches a flame.
    """
    fw, h = FRAME_WIDTH[name], source.height
    ink, steel, edge = rgb(0x272324), rgb(0x66666a), rgb(0xb6ac94)
    leather, stitch = rgb(0x4e3022), rgb(0x9e8765)
    sand = set(west.SAND)
    stone = set(city.STONE + urban.CONCRETE + urban.BRICK + west.ROAD_PAL['stone'])
    wood = WOOD | set(west.ROAD_PAL['paint'])
    metal = IRON | set(city.DRUM + city.RUST)

    def p(frame: int, x: int, y: int, color, allowed=None) -> None:
        if not 0 <= x < fw:
            return
        old = source.get(frame * fw + x, y)
        if not old[3] or old in LIGHTS or old in FLAME or (allowed is not None and old not in allowed):
            return
        out.set(frame * fw + x, y, color)

    def ln(frame: int, x0: int, y0: int, x1: int, y1: int, color, allowed=None) -> None:
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(n + 1):
            p(frame, round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n), color, allowed)

    def seam(frame: int, x0: int, y0: int, x1: int, y1: int, allowed) -> None:
        ln(frame, x0, y0, x1, y1, leather, allowed)
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(1, n, 3):
            p(frame, round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n), stitch, allowed)

    def rivet(frame: int, x: int, y: int, allowed=None) -> None:
        p(frame, x, y, ink, allowed)
        p(frame, x - 1, y - 1, edge, allowed)

    def sack(frame: int, x: int, y: int, w: int, tall: int, allowed=sand) -> None:
        # An individual bag's sewn fold, tied end and pressure crease.
        seam(frame, x + 2, y + tall - 3, x + w - 3, y + tall - 3, allowed)
        ln(frame, x + w - 3, y + 1, x + w - 3, y + 3, rgb(0x8a704e), allowed)
        p(frame, x + w - 4, y + 2, rgb(0xd0b68b), allowed)
        p(frame, x + 2, y + 2, rgb(0xb6a078), allowed)

    def wheel(frame: int, cx: int, cy: int, radius: float, burnt: bool = False) -> None:
        # Tread blocks curve around the sidewall. Bolt holes surround a raised
        # hub, with a small crescent of reflected light on the metal rim.
        for y in range(math.floor(cy - radius), math.ceil(cy + radius) + 1):
            for x in range(math.floor(cx - radius), math.ceil(cx + radius) + 1):
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy)
                a = math.atan2(dy, dx)
                if not radius * .72 <= d <= radius:
                    continue
                block = int((a + math.pi) * (16 if radius > 10 else 12) / math.tau)
                if block % 2 == 0:
                    p(frame, x, y, rgb(0x363638) if dy < 0 else rgb(0x151517))
                elif d < radius * .83:
                    p(frame, x, y, rgb(0x0e0d0f))
        if not burnt:
            for k in range(6):
                angle = k * math.tau / 6 - .15
                x, y = cx + round(radius * .36 * math.cos(angle)), cy + round(radius * .36 * math.sin(angle))
                p(frame, x, y, rgb(0x28272b))
                if k > 2:
                    p(frame, x - 1, y - 1, rgb(0x96918a))
            for k in range(7):
                angle = math.pi + k * math.pi / 9
                p(frame, cx + round(radius * .55 * math.cos(angle)),
                  cy + round(radius * .55 * math.sin(angle)), rgb(0x88878b))
        p(frame, cx, cy, edge)
        p(frame, cx + 1, cy + 1, ink)

    if name == 'campfire':
        for frame in range(8):
            # Each crossed log carries irregular black bark plates, split
            # heartwood and a reddish glow in the cracks nearest the fire.
            for x0, y0, x1, y1 in ((7, 48, 36, 42), (41, 48, 12, 42)):
                for k in range(2, 28, 6):
                    x = round(x0 + (x1 - x0) * k / 29)
                    y = round(y0 + (y1 - y0) * k / 29)
                    ln(frame, x, y, x + (2 if x1 > x0 else -2), y + 1, rgb(0x2c211c), WOOD)
                    p(frame, x, y + 2, rgb(0x813d25), WOOD)
                    p(frame, x - 1, y, rgb(0xc27339), WOOD)
                for x in (x0, x1):
                    p(frame, x, y0 if x == x0 else y1, rgb(0x38231c), WOOD)
            for i, x in enumerate(range(0, 48, 7)):
                y = 51 + i % 2
                # Separate upper facet, fractured face and the dark joint
                # between neighboring stones of the hearth ring.
                ln(frame, x + 1, y, x + 4, y, rgb(0xb0a396), stone)
                ln(frame, x + 4, y + 1, x + 3, y + 3, rgb(0x474143), stone)
                p(frame, x + 2, y + 2, rgb(0x807669), stone)
                p(frame, x + 5, y + 3, rgb(0x302b2c), stone)
            if frame >= 4:
                # Riveted kettle rim, a handle mount and soot on its belly.
                for x in (19, 28):
                    rivet(frame, x, 27)
                for x in range(19, 28, 3):
                    p(frame, x, 34, rgb(0x2b2626))
        for frame in range(8, 12):
            for y in (35, 45):
                for x in (15, 32):
                    rivet(frame, x, y, metal)
            ln(frame, 30, 30, 30, 50, rgb(0x28292b), metal)
            ln(frame, 31, 30, 31, 50, rgb(0x626365), metal)
    elif name == 'burner':
        for frame in range(6):
            for y in (51, 61):
                rivet(frame, 12, y, metal)
                rivet(frame, 27, y, metal)
            ln(frame, 27, 45, 27, 68, rgb(0x252529), metal)
            ln(frame, 28, 46, 28, 68, rgb(0x626266), metal)
            for x, y in ((15, 47), (16, 48), (22, 58), (23, 59), (17, 66)):
                p(frame, x, y, rgb(0x9a5b37), metal)
    elif name == 'barricade':
        # Steel corner plates and sheared edges on the freight crates.
        for frame in (0, 1):
            for x0, y0 in ((5, 5), (28, 5), (5, 31), (28, 31), (35, 19), (50, 19)):
                ln(frame, x0, y0, x0 + 3, y0, steel, WOOD | IRON)
                ln(frame, x0, y0, x0, y0 + 3, ink, WOOD | IRON)
                rivet(frame, x0 + 1, y0 + 1, WOOD | IRON)
        for frame in (1, 2):
            for x0, y0 in ((9, 19), (24, 28), (42, 24)):
                ln(frame, x0, y0, x0 + 5, y0 + 1, rgb(0xd0a16e), WOOD)
                ln(frame, x0 + 1, y0 + 1, x0 + 5, y0 + 2, rgb(0x34211b), WOOD)
        # Match the actual bag layout rather than drawing an overall weave.
        layouts = ((30, ((0, 11), (11, 14), (25, 12), (37, 15), (52, 15))),
                   (24, ((4, 13), (17, 12), (29, 15), (44, 14), (58, 8))),
                   (18, ((7, 15), (22, 13), (35, 12), (47, 14))),
                   (12, ((11, 12), (23, 14), (37, 15), (52, 7))),
                   (6, ((13, 13), (39, 14))))
        for frame in (3, 4):
            for y, bags in layouts:
                for x, w in bags:
                    sack(frame, x, y, w, 7)
        # The military jersey's sacks and concrete lips, before/after damage.
        for frame in (15, 16):
            for y, count, start in ((11, 6, 6), (6, 5, 10)):
                for i in range(count):
                    sack(frame, start + i * 9, y, 9, 6)
            for x in (9, 57):
                rivet(frame, x, 29, stone)
    elif name == 'supply':
        canvas = set(west.CANVAS)
        for frame in (0, 1):
            # Sewn canvas panels follow the hoops; leather hold-down straps
            # have buckles and stitched edges, and the bed has bolted braces.
            for x in (23, 49, 75):
                seam(frame, x + 2, 9, x + 2, 29, canvas)
            for x in (18, 42, 68):
                ln(frame, x, 24, x, 32, leather, canvas | WOOD)
                ln(frame, x + 1, 24, x + 1, 32, rgb(0x76503a), canvas | WOOD)
                ln(frame, x - 1, 28, x + 2, 28, steel, canvas | WOOD)
                p(frame, x - 1, 29, edge, canvas | WOOD)
            for x in (13, 85):
                ln(frame, x, 33, x, 40, ink, WOOD | IRON)
                rivet(frame, x, 34, WOOD | IRON)
                rivet(frame, x, 39, WOOD | IRON)
            for x in (22, 76):
                cy, radius = (44, 11) if x == 22 else (46, 9)
                # Wooden wheels retain their spokes, add segmented iron tyre
                # joints and the hub's cotter pin instead of rubber tread.
                for angle in (.4, 2.5, 4.4):
                    px, py = x + round(radius * math.cos(angle)), cy + round(radius * math.sin(angle))
                    rivet(frame, px, py, IRON | WOOD)
                ln(frame, x - 1, cy - 1, x + 1, cy + 1, ink, IRON | WOOD)
                p(frame, x - 1, cy - 1, edge, IRON | WOOD)
    elif name in ('vehicles', 'car_wreck', 'siren_car', 'supply_truck'):
        for frame in range(source.width // fw):
            burnt = name == 'car_wreck' and frame % 3 == 2 or name == 'vehicles' and frame == 2
            if name == 'vehicles' and frame == 3:
                centers, cy, radius = (62, 152), h - 13, 12.2
            elif name == 'supply_truck' or name == 'vehicles' and frame == 4:
                centers, cy, radius = (28, 52, 154), h - 11, 10.2
            else:
                ox = 24 if name == 'vehicles' else 0
                centers, cy, radius = (28 + ox, 108 + ox), h - (6 if burnt else 9), 5.2 if burnt else 8.2
            for cx in centers:
                wheel(frame, cx, cy, radius, burnt)
            if name == 'supply_truck' or name == 'vehicles' and frame == 4:
                # Truck grille, hood hinges, mirror glass and cargo-bed latches.
                for y in range(38, 50, 3):
                    ln(frame, 170, y, 174, y, ink)
                    p(frame, 170, y - 1, steel)
                for x in range(12, 124, 28):
                    ln(frame, x, 48, x + 3, 48, steel, PAINT)
                    rivet(frame, x, 51, PAINT)
                seam(frame, 10, 8, 118, 8, set(rgb(v) for v in (0x3a3c28, 0x52563a, 0x6c7050, 0x868a66)))
                ln(frame, 146, 24, 148, 24, rgb(0x899798), GLASS)
            elif not burnt:
                ox = 24 if name == 'vehicles' else 0
                belt = h - 30
                # Handles have a recessed pocket, a metallic pull and a tiny
                # keyhole. Fine wipers and an intact/broken mirror catch light.
                for x in (50 + ox, 70 + ox):
                    ln(frame, x, belt + 5, x + 5, belt + 5, ink)
                    ln(frame, x + 1, belt + 4, x + 4, belt + 4, steel)
                    p(frame, x, belt + 7, edge)
                ln(frame, 88 + ox, belt - 1, 94 + ox, belt - 5, ink, GLASS)
                ln(frame, 90 + ox, belt + 1, 95 + ox, belt + 1, edge, PAINT)
            # Underbody rocker seam and small suspension fasteners; marks
            # are clipped, so no axle appears floating between silhouettes.
            ln(frame, centers[0] + 11, h - 10, centers[-1] - 11, h - 10, ink)
            for x in (centers[0] + 13, centers[-1] - 13):
                rivet(frame, x, h - 11)
    elif name == 'outpost':
        olive = set(city.PAINTS['olive'])
        for frame in (0, 1):
            # The sagging tarp's hem, doubled seams at its supporting hoops,
            # hanging buckles and tie wraps read as cloth over a real frame.
            for x in range(12, 120):
                y = 26 + round(3 * math.sin(math.pi * ((x - 10) % 56) / 56))
                p(frame, x, y + 3, rgb(0x343b28), olive)
                if x % 3 == 0:
                    p(frame, x, y + 2, rgb(0x959274), olive)
            for x in (11, 67, 120):
                for y in range(31, 38, 2):
                    ln(frame, x - 1, y, x + 1, y, rgb(0x9a8260), WOOD)
            # Locker hinges and riveted lid, with visible tray edges when open.
            for x in (79, 104):
                ln(frame, x, 58 if frame == 0 else 49, x + 2, 58 if frame == 0 else 49, steel)
                rivet(frame, x, 60 if frame == 0 else 51, olive)
            if frame == 1:
                ln(frame, 79, 66, 104, 66, rgb(0x343a2a))
                ln(frame, 79, 76, 104, 76, rgb(0x262b20))
                for x in (80, 101):
                    ln(frame, x, 68, x, 73, rgb(0x535c42))
            # A tuning needle, separate control knobs and three speaker slots.
            ln(frame, 33, 52, 37, 52, rgb(0x858d62))
            p(frame, 35, 51, rgb(0xd1d7a4))
            for x in (33, 38):
                rivet(frame, x, 58)
            for y in (53, 55, 57):
                ln(frame, 42, y, 46, y, ink)
            for y, count, start in ((85, 13, 0), (78, 12, 6), (71, 11, 12)):
                for i in range(count):
                    if y == 71 and 5 <= i <= 8:
                        continue
                    sack(frame, start + i * 12, y, 12, 7)
            # Bolted reflector housing and the swivelling bracket, strictly
            # outside the lens at columns 137..143, rows 3..11.
            for x, y in ((136, 2), (149, 2), (136, 12), (149, 12)):
                rivet(frame, x, y, IRON)
            ln(frame, 146, 15, 147, 15, edge, IRON)
    elif name in ('facades', 'city_fronts', 'wall_ruins', 'wall', 'door'):
        frames = source.width // fw
        for frame in range(frames):
            if name == 'facades':
                # Individual roof shingles, ridge caps and missing corners,
                # placed only where the roof timber already exists.
                for y in range(5, 44, 5):
                    for x in range(3 + (y // 5 % 2) * 4, fw - 3, 9):
                        ln(frame, x, y, x + 6, y, rgb(0x503525), WOOD)
                        ln(frame, x + 1, y + 1, x + 5, y + 1, rgb(0x987149), WOOD)
                        p(frame, x + 6, y - 1, rgb(0x34241e), WOOD)
                dx, top = 68, 64
                for x in (dx - 3, dx + 46):
                    for y in range(top + 6, h - 4, 15):
                        rivet(frame, x, y, wood | stone)
                for x0, y0 in ((8, 117), (49, 111), (140, 122), (171, 104)):
                    ln(frame, x0, y0, x0 + 5, y0 + 2, rgb(0x4a3c33), stone)
                    ln(frame, x0 + 1, y0 - 1, x0 + 5, y0 + 1, rgb(0xa39583), stone)
            elif name == 'city_fronts':
                # Sills and door jambs have chipped lower corners; one short
                # settling crack runs through the masonry below each opening.
                for x0, y0 in ((18, 94), (65, 88), (176, 90), (216, 176)):
                    for k in range(9):
                        x = x0 + k // 3 + (k % 3 == 1)
                        y = y0 + k
                        p(frame, x, y, rgb(0x382f2b), stone)
                        p(frame, x - 1, y, rgb(0x9a8873), stone)
                for x in (94, 145):
                    for y in (133, 154, 178):
                        rivet(frame, x, y, stone | set(city.TRIM))
                # A lower damp line and missing plaster reveal a jagged brick
                # edge instead of a uniform unweathered rectangle at the feet.
                for x in range(6, fw - 6):
                    if x % 23 < 7:
                        y = h - 4 - x % 3
                        p(frame, x, y, rgb(0x3b332d), stone)
            elif name == 'wall':
                if frame < 2:
                    for x in (7, 21, 36):
                        for y in (28, 49):
                            rivet(frame, x, y, WOOD | IRON)
                            ln(frame, x - 2, y + 1, x + 2, y + 1, steel, IRON)
                else:
                    for x in range(5, 40, 9):
                        ln(frame, x, h - 8, x + 3, h - 5, rgb(0xc89a67), WOOD)
            elif name == 'door':
                for y in (9, 53):
                    ln(frame, 2, y, 9, y, steel, IRON)
                    ln(frame, 35, y, 41, y, steel, IRON)
                    rivet(frame, 5, y + 1, IRON)
                    rivet(frame, 38, y + 1, IRON)
            else:
                for x0, y0 in ((14, 70), (42, 57), (118, 67), (151, 48)):
                    for k in range(7):
                        p(frame, x0 + k // 3, y0 + k, rgb(0x483b32), stone)
                        p(frame, x0 + k // 3 - 1, y0 + k, rgb(0xac9275), stone)


def build_assets() -> dict[str, Image]:
    """Public generator API used by the other scenery rebuild tools."""
    return {path: refine(Path(path).stem, image) for path, image in source_assets().items()}


def preview(path: Path, original: dict[str, Image], refined: dict[str, Image]) -> None:
    """Before/after pairs at 3x; geometry and broken states can be checked."""
    names = ['goal', 'supply', 'bench', 'barrel', 'coffin', 'wall', 'barricade',
             'campfire', 'facades', 'city_fronts', 'vehicles', 'train']
    width, scale = 1900, 3
    heights = [original[f'sprites/terrain/{name}.png'].height * scale + 24 for name in names]
    image = Image(width, sum(heights))
    image.px = [rgb(0x2b2524)] * (image.width * image.height)
    top = 0
    for row, name in enumerate(names):
        key = f'sprites/terrain/{name}.png'
        for side, source in enumerate((original[key], refined[key])):
            count = min(source.width, FRAME_WIDTH[name] * (3 if name in ('barrel', 'coffin', 'wall', 'barricade') else 1))
            for y in range(source.height):
                for x in range(count):
                    c = source.get(x, y)
                    if not c[3]:
                        continue
                    for dy in range(scale):
                        for dx in range(scale):
                            image.set(side * (width // 2) + 12 + x * scale + dx,
                                      top + 8 + y * scale + dy, c)
        top += heights[row]
    image.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=Path(__file__).resolve().parent.parent / 'assets')
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    original = source_assets()
    out = {path: refine(Path(path).stem, image) for path, image in original.items()}
    for name, image in out.items():
        image.save(args.assets_dir / name)
        print(f'refine_terrain: {name} ({image.width} x {image.height})')
    if args.preview:
        preview(args.preview, original, out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
