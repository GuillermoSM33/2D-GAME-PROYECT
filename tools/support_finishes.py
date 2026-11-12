"""Material finishes for the supporting cast and small objects.

Native pixels, deterministic, standard library only. Preserve the silhouette,
frame layout and semantic colors; details belong to cloth, paper, metal or
feathers instead of uniform noise across the whole sprite.
"""
from make_sprites import rgb
import ui_icons as kit


def finish_ui(image, name):
    if name == 'font':
        return image  # White glyph coverage is the text renderer's tint mask.
    if name in ('badge_player', 'badge_zombie'):
        return image  # Their facets and inset bands already have material detail.
    wood = set(kit.WOOD)
    for y in range(image.height):
        for x in range(image.width):
            color = image.get(x, y)
            if color not in wood:
                continue
            if name == 'panel' and 8 <= x < 16 and 8 <= y < 16:
                continue
            if name == 'button' and 5 <= x % 16 < 11 and 5 <= y < 11:
                continue
            if color in (kit.WOOD[1], kit.WOOD[2]) and y % 5 == 3 and (x // 4 + y // 5) % 3 == 0:
                image.set(x, y, kit.WOOD[3])
            elif color == kit.WOOD[2] and y % 5 == 1 and x % 8 in (2, 3):
                image.set(x, y, kit.WOOD[1])
    return image


def finish_clues(image, paper):
    # Sparse folds and aged paper fibers; printed words and clue marks survive.
    for f in range(image.width // 24):
        for y in range(3, 22):
            for x in range(3, 21):
                px = f * 24 + x
                color = image.get(px, y)
                if color == paper[2] and (y + f % 3) % 11 == 7 and 5 <= x <= 16:
                    if (x // 3 + f) % 3 != 0:
                        image.set(px, y, paper[1])
                elif color == paper[3] and x % 7 == 3 and (y // 3 + f) % 5 == 0:
                    image.set(px, y, paper[2])
    return image


def finish_bird(image, kind):
    if kind == 'crow':
        colors = {0x101014: 0x202b2d, 0x22242c: 0x394749, 0x3a4256: 0x64726d,
                  0x6c6c70: 0x939780, 0xc8c8c8: 0xb9bba3, 0x8a1e1e: 0x713a2e}
    else:
        colors = {0x18141a: 0x242a26, 0x2c2430: 0x45483c, 0x564658: 0x7a5a47,
                  0x3a2e3c: 0x4e3e32, 0xe0d8b0: 0xb8a274, 0x8a1e1e: 0x713a2e}
    original = list(image.px)
    for y in range(image.height):
        for x in range(image.width):
            color = original[y * image.width + x]
            value = color[0] << 16 | color[1] << 8 | color[2]
            if not color[3] or value not in colors:
                continue
            col = colors[value]
            local, frame = x % 16, x // 16
            if kind == 'crow' and value in (0x22242c, 0x3a4256):
                # Short overlapping barbs follow the wing, with a few lit shafts.
                if 3 <= local <= 10 and (local + y * 2 + frame // 2) % 5 == 0:
                    col = 0x4f6060
                elif local <= 9 and image.get(x, y - 1)[3] == 0:
                    col = 0x78847b
            elif kind == 'bat' and value == 0x564658:
                if (local + y * 2) % 6 == 0:
                    col = 0x9a7f5d  # Fine finger bones across the warm leather membrane.
                elif local > 8:
                    col = 0x654b3c
            image.set(x, y, rgb(col))
    return image


def finish_mercenary(image, width, lab, gun, glass, teal, ink, rim):
    cloth = [rgb(v) for v in (0x101816, 0x1c2823, 0x2a3930, 0x3b4a3d, 0x4e5c4b, 0x65715c)]
    steel = [rgb(v) for v in (0x182522, 0x2c3b34, 0x48594c, 0x6c7b68, 0x96a18a)]
    mapping = dict(zip(lab, cloth))
    mapping.update(zip(gun, steel))
    mapping.update(zip(glass, (rgb(0x203333), rgb(0x526b60), rgb(0x94aaa0), rgb(0xccd6bb))))
    mapping.update(zip(teal, (rgb(0x142a26), rgb(0x294439), rgb(0x4b6c56), rgb(0x728f71), rgb(0xa5b99b))))
    mapping[ink] = rgb(0x0d1513)
    mapping[rim] = cloth[5]
    original = list(image.px)
    for y in range(image.height):
        for x in range(image.width):
            col = original[y * image.width + x]
            if col in mapping:
                out = mapping[col]
                if col == rim and (x + y) % 5 == 0:
                    out = cloth[3]  # Broken light on worn edges, rather than a neon rim.
                image.set(x, y, out)
    if width == 110:
        poses = ((0, 0), (0, 1), (2, 0), (1, 0))
        for f, (lift, breathe) in enumerate(poses):
            ox = f * width
            # Plate-carrier webbing, folded pocket flaps and bar-tack seams.
            for y in (58 - lift, 66 - lift, 87 - lift, 95 - lift):
                for x in range(38, 73):
                    if image.get(ox + x, y) in cloth[1:4]:
                        image.set(ox + x, y, cloth[3] if x % 7 in (0, 1) else cloth[1])
            for x in (37, 49, 61, 73):
                for y in range(55 - lift, 127, 4):
                    if image.get(ox + x, y) in cloth[1:4]:
                        image.set(ox + x, y, cloth[3])
    else:
        # The walking silhouette stays anonymous; readable fabric and equipment,
        # not skin or identifying insignia, carry the extra detail.
        for f in range(image.width // width):
            for y in range(39, 57):
                for x in range(27, 42):
                    at = f * width + x
                    if image.get(at, y) in cloth[1:4] and x in (30, 37) and y % 4 == 1:
                        image.set(at, y, cloth[3])
    return image


def finish_vial(image, skin, lab, glass, liquid, rim):
    flesh = [rgb(v) for v in (0x241c19, 0x463025, 0x70513b)]
    coat = [rgb(v) for v in (0x182724, 0x263831, 0x3b4c40, 0x576655, 0x788470, 0xa5ad92)]
    glass_new = [rgb(v) for v in (0x283a3b, 0x4c6563, 0x8baba0, 0xbacdc0)]
    fluid = [rgb(v) for v in (0x203f2d, 0x3e6945, 0x60885a, 0x88a676, 0xc4ce9b)]
    mapping = dict(zip(skin, flesh)); mapping.update(zip(lab, coat))
    mapping.update(zip(glass, glass_new)); mapping.update(zip(liquid, fluid))
    mapping[rim] = rgb(0x899781)
    original = list(image.px)
    for y in range(image.height):
        for x in range(image.width):
            color = original[y * image.width + x]
            if 0 < color[3] < 255:
                image.set(x, y, (94, 137, 83, max(1, round(color[3] * .6))))
            elif color in mapping:
                image.set(x, y, mapping[color])
    # Knurled cap, graduation marks and a narrow glass reflection.
    for x in (27, 29, 31, 33, 35):
        for y in range(4, 8): image.set(x, y, coat[2] if x % 4 else coat[4])
    for y in range(14, 39, 5):
        for x in (33, 34): image.set(x, y, glass_new[1])
    for y in range(10, 19):
        image.set(28, y, glass_new[2] if y % 4 else glass_new[3])
    # Curled knuckles and tendons, not four uniformly flat finger bands.
    for y in (41, 47, 53, 59):
        for x in range(24, 39):
            if image.get(x, y) == flesh[1]: image.set(x, y, flesh[2])
        if image.get(37, y + 3) in flesh: image.set(37, y + 3, flesh[0])
    for y0, x0, x1 in ((40, 19, 43), (46, 17, 44), (52, 18, 43), (58, 21, 40)):
        # The near knuckle rolls into shadow toward each fingertip.
        for y in range(y0 + 1, y0 + 5):
            for x in range(x0 + 3, x1 - 1):
                if image.get(x, y) not in flesh:
                    continue
                if y == y0 + 1 and x >= x1 - 7:
                    image.set(x, y, flesh[2])
                elif y >= y0 + 3 and x < x0 + 8:
                    image.set(x, y, flesh[0])
        for x in (x1 - 6, x1 - 5):
            if image.get(x, y0 + 3) in flesh:
                image.set(x, y0 + 3, flesh[0])
    for y in range(68, 79):
        for x in (26, 33):
            if image.get(x, y) == flesh[1]: image.set(x, y, flesh[0] if x == 33 else flesh[2])
    for x in range(19, 39, 3):
        if image.get(x, 84) in coat: image.set(x, 84, coat[3])
    for y in range(86, image.height):
        for x in range(15, 39):
            if image.get(x, y) not in coat:
                continue
            if 20 <= x <= 22 + (y - 86) // 6:
                image.set(x, y, coat[2])
            elif x == 33 - (y - 86) // 4:
                image.set(x, y, coat[0])
    return image
