"""Readable mounted night-vision optics, shared by every SWAT head pose."""
from make_sprites import rgb

INK = rgb(0x252018)
CASING = rgb(0x29343b)
RIM = rgb(0x697174)
GLASS = rgb(0x8fa83e)
LIGHT = rgb(0xb6ca64)
GLINT = rgb(0xd3df97)
SHADE = rgb(0x435327)


def mount(image):
    """Three separate tubes with dark rims and brighter olive glass.

    Native coordinates on the helmet, before any posing. The face and the
    helmet silhouette stay intact; all animations inherit the same optics.
    """
    for x in range(23, 32):
        image.set(x, 7, CASING)
    for x in range(24, 30):
        image.set(x, 7, RIM if x < 27 else CASING)
    # left, top, glass width, glass height; the last tube recedes in profile.
    for i, (x, y, w, h) in enumerate(((23, 9, 3, 3), (28, 9, 2, 3), (32, 10, 2, 3))):
        for py in range(y - 1, y + h + 1):
            for px in range(x - 1, x + w + 1):
                edge = px in (x - 1, x + w) or py in (y - 1, y + h)
                color = INK if edge else SHADE if py == y + h - 1 else GLASS
                if py == y - 1 and x <= px < x + w:
                    color = RIM
                image.set(px, py, color)
        image.set(x, y, GLINT if i == 0 else LIGHT)
        image.set(x, y + 1, LIGHT)
    return image
