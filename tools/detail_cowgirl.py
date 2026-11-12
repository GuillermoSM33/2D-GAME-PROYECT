#!/usr/bin/env python3
"""Finish every sheriff pose with a wine jacket and the original red hair.

Run last in rebuild_cowgirl.py, after geometry/outline construction. Material
membership comes from the authoring palette; details follow each part's own
surfaces, so diffuse shading moves with the limbs. No random noise, blur, dependencies,
new frame dimensions or changes to the runtime anchors.
"""
from __future__ import annotations

from pathlib import Path

from make_powers import load
from make_sprites import rgb
from rework_cowgirl import JACKET, JACKET_BUTTON

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets/sprites/characters/cowgirl'
WIDTHS = {'walk': 42, 'walk_dual': 42, 'stand': 42, 'stand_dual': 42,
          'legs': 42, 'legs_dual': 42, 'jump': 54, 'jump_dual': 54,
          'sit': 72, 'faint': 80}


def tones(*values: int) -> set:
    return {rgb(value) for value in values}


SKIN = tones(0xfedca3, 0xd99a5b, 0x89411f, 0x8a4322)
HAIR = tones(0x6b333a, 0x902004, 0xd03305)
CLOTH = tones(0x6c7a84, 0x505c66, 0x38424a)
JACKET_TAGS = set(JACKET)
BUTTON_TAGS = set(JACKET_BUTTON)
CORSET = tones(0x2c363c, 0x48565e, 0x38444a, 0x242c32)
PANTS = tones(0x5e5650, 0x48423e, 0x423c38, 0x322e2c, 0x4c4640, 0x3a3532, 0x6e6660, 0x585250)
LEATHER = tones(0x463322, 0x684833, 0x4a2e18, 0x6c4626, 0x8a6a3e)
HAT = tones(0x2c2c2c, 0x424242, 0x505050, 0x868689, 0xa7a8a8, 0x9c8526)
SASH = tones(0x64182a, 0x8a2438, 0x46101e)
LACE = tones(0xece6d6, 0xbcb6a6)
BADGE = tones(0xf6dc86, 0xd0a848, 0x8e6c28)
BRASS = tones(0xb8903a, 0xecc868, 0x9c8526)
CORD = tones(0x6a6a68)
PANTS_LIT = tones(0x5e5650, 0x48423e, 0x6e6660, 0x585250)
PANTS_STRIPE = tones(0x48423e, 0x322e2c, 0x3a3532, 0x585250)
LEATHER_LIT = tones(0x684833, 0x6c4626, 0x8a6a3e)

# A short open wine jacket replaces the blue. Keep the charcoal/slate corset,
# two-grey trousers and dark brown leather. Clothing has diffuse planes;
# the original hair palette is preserved exactly, without recolouring its lights.
WINE = 0x6f2638
SKIN_LIGHT, SKIN_BASE, SKIN_SHADE = 0xebc1a4, 0xd7a786, 0xa87057
CLOTH_LIGHT, CLOTH_BASE, CLOTH_SHADE = 0x924657, WINE, 0x441c2a
CORSET_LIGHT, CORSET_BASE, CORSET_SHADE, STITCH = 0x5d6870, 0x404c53, 0x29343b, 0x747b77
# Two greys follow the original vertical stripes; no pale edging or blue stripe.
PANTS_LIGHT, PANTS_SHADE = 0x777174, 0x4b464b
PANTS_BASE = PANTS_LIGHT
LEATHER_LIGHT, LEATHER_BASE, LEATHER_SHADE = 0x916c48, 0x6f4d33, 0x483326


def finish(px: dict, sheet: str) -> dict:
    out = dict(px)
    face_points = [p for p, c in px.items() if c in SKIN]
    face_top = min((y for x, y in face_points), default=27)
    # Upright frames share these landmarks; fainting still gets all materials,
    # with no facial marks when the head has turned onto its side.
    face = [p for p in face_points if p[1] < face_top + 7]
    left = min((x for x, y in face), default=28)
    right = max((x for x, y in face), default=40)
    middle = (left + right) // 2
    belt = face_top + 22
    upright = bool(face) and (sheet != 'faint' or max(y for x, y in face) - face_top >= 3)

    for (x, y), color in px.items():
        if color in SKIN:
            # Warm skin with the hat's cast shadow, a lit cheek and a jaw plane.
            if y < face_top + 2:
                col = 0xbf8964
            elif x < middle - 2:
                col = SKIN_SHADE
            elif x > right - 2 or y == face_top + 6:
                col = SKIN_BASE
            else:
                col = SKIN_LIGHT
        elif color in HAIR:
            continue  # Keep #6b333a / #902004 / #d03305 from the pre-rework art.
        elif color in CLOTH:
            # Wine jacket sleeves, with restrained leather-like shading.
            col = CLOTH_BASE
            if color == rgb(0x38424a):
                col = CLOTH_SHADE
            elif color == rgb(0x6c7a84):
                col = CLOTH_LIGHT
        elif color in JACKET_TAGS:
            col = {JACKET[0]: CLOTH_LIGHT, JACKET[1]: CLOTH_BASE, JACKET[2]: CLOTH_SHADE}[color]
        elif color in BUTTON_TAGS:
            col = {JACKET_BUTTON[0]: 0xc2a66e, JACKET_BUTTON[1]: 0xa27d43, JACKET_BUTTON[2]: 0x36271d}[color]
        elif color in CORSET:
            # Charcoal/slate corset visible between the open jacket panels.
            col = CORSET_BASE if x < middle else 0x364149
            if color == rgb(0x48565e):
                col = CORSET_LIGHT
            elif x == middle + 3 and (y - face_top) % 3 == 0:
                col = STITCH
            elif color == rgb(0x242c32):
                col = CORSET_SHADE
        elif color in PANTS:
            # The reference's two grey stripes, separate from the wine jacket.
            col = PANTS_BASE if color in PANTS_LIT else PANTS_SHADE
            if color in PANTS_STRIPE:
                col = PANTS_SHADE
        elif color in LEATHER:
            # Dark leather; restrained wear on the wooden grip, no glossy edging.
            col = LEATHER_BASE if color in LEATHER_LIT else LEATHER_SHADE
            if color == rgb(0x8a6a3e):
                col = LEATHER_LIGHT
        elif color in HAT and y < face_top:
            # Felt crown and leather hatband: no white brim or metallic highlights.
            col = {rgb(0x2c2c2c): 0x4a4033, rgb(0x424242): 0x75654d,
                   rgb(0x505050): 0x9c8968, rgb(0x868689): 0xb6a080,
                   rgb(0xa7a8a8): 0xc6b28e, rgb(0x9c8526): 0x60432e}[color]
        elif color in SASH:
            col = {rgb(0x64182a): 0x743044, rgb(0x8a2438): 0x995367,
                   rgb(0x46101e): 0x4c2633}[color]
        elif color in LACE:
            col = 0xbdbbb1 if color == rgb(0xece6d6) else 0x96948b
        elif color in BADGE:
            col = {rgb(0xf6dc86): 0xdbc58d, rgb(0xd0a848): 0xb6985c,
                   rgb(0x8e6c28): 0x77603c}[color]
        elif color in BRASS:
            col = 0xc9ab6d if color == rgb(0xecc868) else 0x9e7c42
        elif color in CORD:
            col = 0x605d74
        else:
            continue
        out[(x, y)] = rgb(col)

    if upright and right - left >= 5:
        # Profile eye under the brim and a small nose shadow; never on an arm.
        for at, col in (((right - 2, face_top + 2), 0x45382e),
                        ((right - 1, face_top + 4), 0xc59174),
                        ((middle + 1, face_top + 6), 0x8f5c4f)):
            if px.get(at) in SKIN:
                out[at] = rgb(col)

    # Belt cartridge loops: a few brass ends, only on exposed belt leather.
    if face and sheet != 'faint':
        for x in (middle - 6, middle - 4, middle + 5):
            if px.get((x, belt)) in LEATHER and px.get((x, belt - 1)) in LEATHER:
                out[(x, belt - 1)] = rgb(0xb99a62)
                out[(x, belt)] = rgb(0x80633f)

    return out


def main() -> None:
    for path in sorted(OUT.glob('*.png')):
        if path.stem == 'flashlight':
            continue
        image = load(path)
        width = WIDTHS.get(path.stem, 81)
        for f in range(image.width // width):
            px = {(x, y): image.get(f * width + x, y)
                  for y in range(image.height) for x in range(width)
                  if image.get(f * width + x, y)[3]}
            for (x, y), color in finish(px, path.stem).items():
                image.set(f * width + x, y, color)
        image.save(path)
    print('detail_cowgirl: done')


if __name__ == '__main__':
    main()
