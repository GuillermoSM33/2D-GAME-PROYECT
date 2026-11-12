"""Six native chest poses: weathered timber, iron straps and aged brass."""
from make_sprites import Image
from make_cinematics import Canvas, poly
import ui_icons as kit


def wood(c, box, seed=0):
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            row = (y - y0) % 7
            tone = 2 if x < (x0 + x1) / 2 else 3
            if row == 0: tone = 4
            elif row == 1: tone = 1
            elif row == 4 and (x // 5 + (y - y0) // 7 + seed) % 3 == 0: tone = 3
            c.px(x, y, kit.WOOD[tone])
    c.hline(x0, x1, y0, kit.WOOD[1])


def strap(c, x, top, bottom):
    c.fill(x, top, x + 4, bottom, kit.INK)
    c.fill(x + 1, top + 1, x + 3, bottom - 1, kit.IRON[2])
    c.vline(x + 1, top + 1, bottom - 1, kit.IRON[1])
    c.vline(x + 3, top + 1, bottom - 1, kit.IRON[3])
    for y in range(top + 3, bottom - 1, 8):
        c.px(x + 2, y, kit.IRON[4]); c.px(x + 1, y - 1, kit.IRON[0])


def make_chest():
    image = Image(6 * 72, 72)
    for frame in range(6):
        c = Canvas(image, frame * 72, 72)
        # Ground, feet and the recessed box: shared between all lid poses.
        c.fill(16, 62, 57, 66, kit.INK)
        c.fill(16, 64, 22, 66, kit.IRON[3]); c.fill(50, 64, 57, 66, kit.IRON[4])
        c.fill(16, 44, 57, 64, kit.INK)
        wood(c, (18, 47, 55, 63))
        c.hline(18, 55, 46, kit.WOOD[0]); c.vline(55, 47, 63, kit.WOOD[4])
        c.hline(18, 55, 63, kit.WOOD[4])
        c.fill(18, 43, 55, 46, kit.INK)
        c.hline(20, 53, 44, kit.WOOD[4])
        if frame:
            # Small coins in the dark lining; the separate sparks animate the loot.
            for x in (25, 30, 35, 41, 46):
                c.hline(x, x + 2, 45, kit.BRASS[2] if x < 36 else kit.BRASS[3])
        for x in (19, 49): strap(c, x, 46, 64)
        c.hline(17, 56, 61, kit.IRON[3]); c.hline(18, 55, 62, kit.IRON[2])
        if frame == 0:
            poly(c, [(15, 45), (16, 33), (22, 27), (50, 27), (56, 33), (57, 45)], kit.INK)
            wood(c, (18, 34, 54, 43), 2)
            c.fill(22, 29, 50, 33, kit.WOOD[2])
            c.hline(22, 49, 29, kit.WOOD[1]); c.hline(23, 48, 31, kit.WOOD[3])
            c.hline(18, 54, 44, kit.WOOD[4])
            for x in (19, 49): strap(c, x, 29, 44)
            c.hline(24, 48, 36, kit.WOOD[1]); c.hline(25, 46, 39, kit.WOOD[3])
        else:
            top = (0, 25, 22, 19, 16, 14)[frame]
            poly(c, [(16, 44), (16, top + 3), (20, top), (53, top), (57, top + 3), (57, 44)], kit.INK)
            c.fill(18, top + 3, 55, 42, kit.WOOD[3])
            c.hline(20, 53, top + 1, kit.WOOD[1]); c.vline(18, top + 3, 42, kit.WOOD[1])
            c.fill(21, top + 5, 52, 40, kit.INK)
            c.fill(23, top + 7, 50, 38, kit.BLACK[4])
            c.hline(23, 50, 39, kit.RED[4])
            c.vline(51, top + 6, 39, kit.WOOD[4])
            for x in (19, 49):
                strap(c, x, top + 2, top + 7)
                c.fill(x, 41, x + 4, 44, kit.IRON[3])
                c.px(x + 1, 42, kit.IRON[1])
            c.fill(33, top - 1, 40, top + 3, kit.INK)
            c.fill(34, top, 39, top + 2, kit.BRASS[2]); c.hline(34, 39, top, kit.BRASS[1])
        # Lock escutcheon, inset keyhole, hinge studs and a worn lower corner.
        poly(c, [(32, 44), (40, 44), (42, 47), (41, 54), (37, 57), (32, 54), (31, 47)], kit.INK)
        poly(c, [(33, 45), (39, 45), (40, 48), (39, 53), (36, 55), (33, 53), (32, 48)], kit.BRASS[2])
        c.hline(33, 39, 45, kit.BRASS[0]); c.vline(32, 47, 52, kit.BRASS[1])
        c.fill(35, 48, 37, 50, kit.INK); c.vline(36, 50, 53, kit.INK)
        c.px(17, 63, kit.IRON[1]); c.px(55, 63, kit.IRON[2])
    return image
