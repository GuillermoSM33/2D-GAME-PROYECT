"""Art direction for the lab shots, in native pixels and material clusters.

The lab shares the scenery's worn iron, ivory paint, glass and warm practical
lights. Each set is dressed separately; screen data and animation stay in
make_cinematics.py. No random grain, resampling or external dependencies.
"""
from make_sprites import rgb


IRON = [rgb(v) for v in (0x101719, 0x202b2e, 0x344246, 0x506061, 0x788780, 0xaab3a0)]
PAINT = [rgb(v) for v in (0x303a38, 0x48524b, 0x60695b, 0x808773, 0xa4aa8d)]
RUST = [rgb(v) for v in (0x322823, 0x574033, 0x805c40)]
PAPER = [rgb(v) for v in (0x6c6e59, 0x96977a, 0xbabd9b)]
LAMP = [rgb(v) for v in (0x4c4937, 0x7d7857, 0xbdb58a, 0xe1dbb3)]
GLASS = [rgb(v) for v in (0x172b2e, 0x2c4547, 0x476362, 0x73918a)]


def grade(c):
    """Finite material ramps keep the architecture in the game's palette."""
    ramps = (
        ((0x0e1115, 0x14181d, 0x1b2026, 0x242a32, 0x323a45, 0x4a5562), IRON),
        ((0x0c2222, 0x123636, 0x1c5250, 0x2f7a72, 0x6cc4b4),
         [rgb(v) for v in (0x172b2a, 0x29443e, 0x416257, 0x6a8972, 0xa5b997)]),
        ((0x08201a, 0x0f3a2e, 0x1e6a50, 0x48b088, 0xa8ecc8),
         [rgb(v) for v in (0x102321, 0x20443b, 0x3b6c54, 0x80af83, 0xc9dbab)]),
    )
    mapping = {rgb(old): new for source, target in ramps for old, new in zip(source, target)}
    for y in range(c.h):
        for x in range(c.w):
            color = c.get(x, y)
            if color in mapping:
                c.px(x, y, mapping[color])


def pipe(c, x0, x1, y):
    c.fill(x0, y, x1, y + 3, IRON[0])
    c.hline(x0, x1, y, IRON[3])
    c.hline(x0, x1, y + 1, IRON[2])
    for x in range(x0 + 17, x1, 58):
        c.fill(x, y - 1, x + 2, y + 4, IRON[1])
        c.vline(x, y - 1, y + 3, IRON[4])
        c.px(x + 1, y - 1, IRON[5])


def vent(c, x, y, w):
    c.fill(x, y, x + w, y + 10, IRON[0])
    c.frame(x, y, x + w, y + 10, IRON[3], IRON[0])
    for row in range(y + 3, y + 9, 2):
        c.hline(x + 3, x + w - 3, row, IRON[2])
    c.px(x + 1, y + 1, IRON[4])
    c.px(x + w - 1, y + 9, IRON[2])


def practical_light(c, sources):
    """Stepped pools light the physical surfaces; emissive data stays intact.

    Sources are (x, y, radius_x, radius_y). Cache the small number of resulting
    material shades so the falloff remains clean clusters of native pixels.
    """
    surfaces = set(IRON + PAINT + RUST + PAPER + LAMP + GLASS)
    surfaces.update(rgb(v) for v in (0x34403e, 0x2a3535, 0x222c2f, 0x192326))
    shades = {}
    for y in range(c.h):
        for x in range(c.w):
            color = c.get(x, y)
            if color not in surfaces:
                continue
            power = max(max(0, 1 - ((x - sx) / rx) ** 2 - ((y - sy) / ry) ** 2)
                        for sx, sy, rx, ry in sources)
            band = min(4, int(power * 5))
            key = color, band
            if key not in shades:
                # Warm ivory in the lit planes, cool iron in their shadows.
                gain = (.64, .78, .94, 1.10, 1.24)[band]
                warmth = (0, 0, 1, 3, 5)[band]
                shades[key] = (min(255, round(color[0] * gain) + warmth),
                               min(255, round(color[1] * gain)),
                               min(255, round(color[2] * gain) - warmth), 255)
            c.px(x, y, shades[key])


def dress_corridor(c):
    grade(c)
    # Broad painted wall panels, aged along their seams rather than speckled.
    for x0, x1 in ((2, 89), (128, 147), (255, 297), (336, 349), (447, 479)):
        c.fill(x0, 33, x1, 101, PAINT[0])
        c.hline(x0, x1, 33, PAINT[1])
        c.vline(x0, 34, 101, IRON[1])
        for x in range(x0 + 17, x1, 24):
            c.vline(x, 34, 101, IRON[1])
            c.vline(x + 1, 35, 65, PAINT[1])
            c.fill(x - 2, 92, x, 93, RUST[0])
        # Chipped enamel at the bottom, in short connected flakes.
        for x in range(x0 + 5, x1 - 3, 31):
            c.hline(x, x + 3, 100, IRON[2])
            c.hline(x + 2, x + 5, 99, PAINT[1])
    pipe(c, 0, c.w - 1, 26)
    c.hline(0, c.w - 1, 10, IRON[0])
    for x in range(8, c.w, 24):
        c.hline(x, x + 12, 8, IRON[1])
    vent(c, 14, 76, 44)
    vent(c, 260, 43, 27)
    vent(c, 451, 78, 24)
    # A hanging cable leads to a badge reader and a small service panel.
    c.line(78, 30, 78, 62, IRON[0])
    c.line(78, 62, 84, 68, IRON[0])
    c.fill(80, 68, 87, 83, IRON[0])
    c.frame(80, 68, 87, 83, IRON[3], IRON[0])
    c.fill(82, 71, 85, 74, GLASS[1])
    c.px(83, 72, LAMP[2])
    c.hline(82, 85, 79, IRON[3])
    # Door leaves: directional brushed steel, reinforced hinges and lock blocks.
    for x in (92, 300):
        c.fill(x + 4, 78, x + 29, 102, IRON[2])
        c.vline(x + 4, 50, 127, IRON[4])
        for yy in (54, 113):
            c.fill(x + 1, yy, x + 4, yy + 5, IRON[0])
            c.vline(x + 2, yy, yy + 4, IRON[4])
        for xx, yy, length in ((7, 80, 8), (12, 94, 12), (6, 108, 5)):
            c.hline(x + xx, x + xx + length, yy, IRON[3])
            c.hline(x + xx + 2, x + xx + length, yy + 1, IRON[1])
        c.fill(x + 24, 87, x + 29, 95, IRON[0])
        c.fill(x + 25, 89, x + 28, 91, LAMP[1])
        c.hline(x + 25, x + 28, 89, LAMP[3])
        c.fill(x + 7, 109, x + 26, 120, IRON[1])
        for yy in range(111, 119, 2):
            c.hline(x + 9, x + 24, yy, IRON[3])
        # Light from the room beyond the glass, slit by a blind.
        c.fill(x + 12, 58, x + 21, 71, GLASS[1])
        for yy in range(59, 72, 4):
            c.hline(x + 12, x + 21, yy, GLASS[2])
        c.line(x + 12, 69, x + 19, 59, GLASS[3])
        c.vline(x + 10, 56, 72, IRON[4])
    # Recessed cabinets: thick glass, metal latches, reflected light strips.
    for x0, x1 in ((150, 252), (352, 444)):
        for xx in (x0 + 2, x1 - 2):
            c.vline(xx, 53, 95, IRON[2])
        c.vline(x0 + 48, 52, 96, IRON[3])
        c.fill(x0 + 45, 75, x0 + 46, 80, IRON[4])
        for xx in (x0 + 7, x0 + 60):
            for yy in range(55, 94):
                dx = (94 - yy) // 3
                if c.get(xx + dx, yy) == IRON[0]:
                    c.px(xx + dx, yy, GLASS[1])
        c.hline(x0 + 3, x1 - 3, 51, IRON[4])
    # The warning remains above the wall finish, next to a curled service note.
    c.fill(267, 70, 286, 85, RUST[0])
    c.fill(268, 70, 284, 83, LAMP[1])
    c.frame(268, 70, 284, 83, LAMP[2], RUST[1])
    for j in range(9):
        half = j * 6 // 8
        c.hline(276 - half, 276 + half, 73 + j, IRON[0])
        if j > 2:
            c.hline(277 - half, 275 + half, 73 + j, LAMP[2])
    c.vline(276, 76, 78, IRON[0])
    c.px(276, 80, IRON[0])
    c.fill(39, 44, 54, 62, IRON[0])
    c.fill(40, 43, 53, 60, PAPER[0])
    c.hline(41, 52, 44, PAPER[1])
    for yy, length in ((48, 7), (51, 9), (54, 5)):
        c.hline(42, 42 + length, yy, IRON[2])
    c.fill(48, 43, 51, 44, LAMP[1])
    # Perspective tile joints and scuffed reflections follow the floor plane.
    for y in range(131, 180):
        for x in range(c.w):
            old = c.get(x, y)
            if old in IRON[:4]:
                band = (y - 131) // 16
                color = (rgb(0x34403e), rgb(0x2a3535), rgb(0x222c2f), rgb(0x192326))[min(band, 3)]
                c.px(x, y, IRON[0] if y in (136, 146, 160, 176) else color)
    for base in range(-80, c.w + 80, 70):
        c.line(base, 131, base + (base - c.w // 2) // 3, 179, IRON[1])
    for x in range(12, c.w, 47):
        y = 139 + (x * 7) % 31
        c.hline(x, x + 10, y, IRON[3])
        c.hline(x + 4, x + 14, y + 1, IRON[1])
    # Practical fluorescent lights and their broken, widening reflections.
    for x in (30, 150, 270, 390):
        c.fill(x, 14, x + 39, 17, IRON[1])
        c.hline(x + 2, x + 36, 15, LAMP[1])
        c.hline(x + 3, x + 35, 16, LAMP[3])
        c.hline(x + 7, x + 31, 17, LAMP[2])
        for y in (138, 143, 153, 168):
            half = 11 + (y - 138) // 3
            c.hline(x + 20 - half, x + 20 + half, y, IRON[3])
            c.hline(x + 22 - half, x + 17 + half, y + 1, IRON[2])
    # Low emergency lamps sit against stained enamel, with red floor glints.
    for x in (60, 236, 420):
        c.fill(x - 1, 23, x + 6, 28, IRON[0])
        c.hline(x, x + 5, 24, rgb(0x9b4936))
        c.hline(x + 1, x + 4, 25, rgb(0xe59c69))
        c.hline(x, x + 5, 27, RUST[1])
        c.hline(x - 3, x + 8, 141, RUST[1])
        c.hline(x - 6, x + 10, 155, RUST[0])
    practical_light(c, [(50 + k * 120, 31, 83, 118) for k in range(4)] +
                      [(50 + k * 120, 144, 52, 39) for k in range(4)])
    return c.img


def dress_monitors(c, frame):
    grade(c)
    pipe(c, 0, 319, 31)
    vent(c, 12, 45, 50)
    # The workstation belongs to a working laboratory: patched walls, conduit,
    # a server rack, paper records, cables and reflections on scratched steel.
    for x in (2, 98, 214, 316):
        c.vline(x, 38, 140, IRON[1])
        c.vline(x + 1, 39, 61, IRON[2])
    c.fill(240, 38, 298, 61, IRON[0])
    c.frame(240, 38, 298, 61, IRON[3], IRON[0])
    for y in range(42, 59, 5):
        c.hline(244, 287, y, IRON[2])
        c.px(292, y, LAMP[2] if (frame + y) % 3 else GLASS[3])
    # Ivory asset tags and controls on the monitor bezels, clear of the data.
    for x0, y0, w, h in ((6, 66, 96, 62), (106, 40, 108, 82), (218, 66, 96, 62)):
        c.fill(x0 + 5, y0 + h - 3, x0 + 17, y0 + h - 2, PAPER[0])
        c.hline(x0 + 7, x0 + 13, y0 + h - 3, PAPER[2])
        c.px(x0 + w - 7, y0 + h - 2, rgb(0xa6c08d))
        c.hline(x0 + w - 15, x0 + w - 12, y0 + h - 2, IRON[3])
        c.hline(x0 + 2, x0 + w - 3, y0 + 1, IRON[4])
        for k in (0, 1):
            c.line(x0 + 25 + k * 2, y0 + h, x0 + 18 + k * 2, 143, IRON[0])
    # A shaded brushed-steel counter and dark drawers under its lip.
    c.hline(0, 319, 146, IRON[4])
    c.hline(0, 319, 152, IRON[0])
    c.hline(0, 319, 154, IRON[3])
    for x in (8, 87, 236):
        c.frame(x, 159, x + 66, 179, IRON[2], IRON[0])
        c.fill(x + 20, 162, x + 45, 165, IRON[0])
        c.hline(x + 22, x + 43, 163, IRON[4])
    # Foreground clipboard and a test-tube rack, warm accents against screens.
    c.fill(233, 137, 267, 145, RUST[0])
    c.fill(235, 137, 265, 143, PAPER[1])
    c.hline(237, 138, 138, PAPER[2])
    for y in (139, 141):
        c.hline(240, 261 - (y % 3), y, IRON[2])
    c.fill(247, 136, 253, 138, IRON[3])
    c.hline(247, 253, 136, IRON[5])
    c.fill(274, 139, 301, 145, IRON[2])
    c.hline(275, 300, 139, IRON[4])
    for x in (278, 285, 292):
        c.fill(x, 132, x + 2, 140, GLASS[1])
        c.vline(x, 132, 138, GLASS[3])
        c.hline(x, x + 2, 131, LAMP[2])
        c.fill(x + 1, 136, x + 2, 140, rgb(0x7c9160))
    for x, y in ((11, 149), (44, 147), (211, 150), (283, 151)):
        c.hline(x, x + 12, y, IRON[2])
    practical_light(c, [(158, 104, 135, 100), (40, 121, 64, 55), (277, 121, 64, 55)])
    return c.img


def dress_alarm(c, frame):
    grade(c)
    # Heavy worn monitor housing, screws, amber keys and a separate data rail.
    c.fill(0, 0, 319, 9, IRON[1])
    c.hline(3, 316, 2, IRON[3])
    c.hline(4, 315, 9, IRON[0])
    c.fill(0, 170, 319, 179, IRON[1])
    c.hline(4, 315, 170, IRON[3])
    for x in (6, 312):
        for y in (5, 174):
            c.fill(x - 1, y - 1, x + 1, y + 1, IRON[3])
            c.hline(x - 1, x + 1, y, IRON[0])
    for x in range(232, 297, 12):
        c.fill(x, 173, x + 7, 176, IRON[0])
        c.hline(x + 1, x + 6, 174, LAMP[1])
    c.fill(24, 173, 51, 176, PAPER[0])
    c.text(28, 173, 'MRC-1', IRON[0])
    # Measurement reticle and red density bars stay outside the dividing cells.
    muted, bright = rgb(0x68372d), rgb(0xd38a66)
    for x in range(104, 218, 8):
        c.vline(x, 29, 31 if x % 16 else 33, muted)
        c.vline(x, 153, 155 if x % 16 else 157, muted)
    for y in range(44, 145, 10):
        c.hline(95, 97 if y % 20 else 100, y, muted)
        c.hline(221, 224, y, muted)
    c.text(244, 55, 'MRC-1', bright)
    for k in range(7):
        c.hline(243, 292, 70 + k * 9, muted)
        c.hline(243, 249 + min(42, frame * 4 + k * 2), 71 + k * 9, bright)
    c.text(245, 142, str(12 + frame * 12) + '%', bright)
    # The microscope image contains translucent interior folds and granules,
    # with arcs of membrane rather than identical flat orange discs.
    reds = {rgb(0x66140f), rgb(0xa8281a)}
    for y in range(37, 148):
        for x in range(105, 216):
            color = c.get(x, y)
            if color in reds:
                if (x + y // 3) % 13 in (0, 1) and (y + x // 5) % 9 < 3:
                    c.px(x, y, rgb(0xbb5031) if color == rgb(0xa8281a) else rgb(0x843323))
                elif (x * 3 + y) % 19 == 0 and c.get(x - 1, y) == color:
                    c.hline(x - 1, x, y, rgb(0x57251d))
    return c.img
