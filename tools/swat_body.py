"""Landmarks of the compact SWAT rig, on the sheriff's native pixel grid.

The helmet, chest, harness and trousers are sampled from the artwork. They
are never reconstructed from boxes, limb warps or another character's legs.
"""
NEAR_SHOULDER = (12.0, 30.5)
FAR_SHOULDER = (29.0, 30.5)
WAIST = 44
PIVOT = 20.0
WIDTH_SCALE = .94
UPPER_ARM = 9.0
FOREARM = 9.5


def proportions(source):
    """One narrower horizontal grid for the complete rig, preserving height.

    The same sampling applies to head, trunk, hips and both legs. Never change
    width when raising an arm; all standing poses share this exact body.
    """
    import math
    from make_sprites import Image
    out = Image(source.width, source.height)
    for f in range(source.width // 42):
        for y in range(source.height):
            for x in range(42):
                sx = math.floor((x + .5 - PIVOT) / WIDTH_SCALE + PIVOT)
                if 0 <= sx < 42:
                    out.set(f * 42 + x, y, source.get(f * 42 + sx, y))
    return out
