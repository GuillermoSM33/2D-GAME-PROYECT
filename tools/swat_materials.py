"""Added equipment shares the compact bitmap's slate and charcoal palette.

The imported walk's pixels pass through unchanged. Only legacy item color
labels (metal, explosives and care props) are translated in the final pass.
"""
from make_sprites import rgb

INK = rgb(0x252018)
CLOTH = [rgb(c) for c in (0x29343b, 0x41494a, 0x5d6870, 0x697174)]
GLOVE = [rgb(c) for c in (0x29343b, 0x41494a)]
MATERIALS = {
    0x140e0e: 0x252018,
    0x1c1c1c: 0x29343b, 0x2c2c2c: 0x41494a, 0x424242: 0x5d6870,
    0x505050: 0x697174, 0x868689: 0x77807b, 0xa7a8a8: 0x96948b,
    0xb83c28: 0x863c2d, 0xe8684a: 0xb66843, 0xf0c860: 0xc2a66c,
    0x8a2a1c: 0x863c2d, 0xc84a32: 0xb66843,
    0x2a2c1a: 0x29343b, 0x4a5030: 0x41494a, 0x6a7444: 0x697174,
    0x9a643a: 0x6a594e, 0x2a5a86: 0x3a5253, 0x5aa0d0: 0x6f9087,
    0xd8f0fa: 0xb9c4ad, 0x9a9488: 0x858372, 0xd8d4c8: 0xb4b09a,
    0xf6f2e6: 0xd5d0b9,
}
PALETTE = {rgb(old): rgb(new) for old, new in MATERIALS.items()}


def finish(image):
    image.px = [PALETTE.get(color, color) for color in image.px]
    return image
