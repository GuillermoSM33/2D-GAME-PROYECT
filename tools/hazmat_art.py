"""The laboratory train's protective suits, drawn: their colours and their parts.

Proportions, parts and materials follow the user's reference, measured on its native grid
with tools/pixel_grid.py (a hood over two fifths of the figure, a face window over a respirator,
long gloves, a belt with pouches, an air bottle). Every pixel here is our own: the sheriff wears a
draped hood with a blue-lit window and her star on the chest; the SWAT keeps its helmet, its
carrier and amber goggles. Maps are in art px, lit from the upper left; each letter is a
colour of COLORS. Standard library only.
"""
from __future__ import annotations

import math


def _rgb(value):
    return (value >> 16) & 255, (value >> 8) & 255, value & 255, 255


INK = _rgb(0x252018)
COLORS = {
    '#': INK,
    # Coated cloth, dark to light
    '1': _rgb(0x554520), '2': _rgb(0x7a682c), '3': _rgb(0x9f8a38), '4': _rgb(0xcfae40), '5': _rgb(0xe0c251), '6': _rgb(0xf5e396),
    # Rubber and steel, dark to light
    'a': _rgb(0x1a1b1c), 'b': _rgb(0x292b2c), 'c': _rgb(0x3c3f40), 'd': _rgb(0x575b5b), 'e': _rgb(0x7b7f7c), 'f': _rgb(0xa8aaa3),
    'g': _rgb(0xdcdcd2),
    # What shows through the window: her skin in the hood's shade, and the glass
    's': _rgb(0x553527), 't': _rgb(0x8a5743), 'u': _rgb(0xbf8964), 'v': _rgb(0xe3b592), 'w': _rgb(0xf7f5ec),
    'y': _rgb(0x56849b), 'z': _rgb(0x35566a),
    # The bottle's band
    'r': _rgb(0x8c2f22), 'R': _rgb(0xb9472f),
    # Leather and brass
    'q': _rgb(0x916c48), 'l': _rgb(0x6f4d33), 'm': _rgb(0x483326), 'n': _rgb(0x35271d), 'G': _rgb(0xc9ab6d),
    # Gloves and patches
    'B': _rgb(0x1d3d57), 'D': _rgb(0x2b6288), 'E': _rgb(0x3f86ad), 'F': _rgb(0x74b0cb),
    # The SWAT: its own helmet's greens, dark to light, and the amber of its visor
    'A': _rgb(0x29343b), 'C': _rgb(0x373b3d), 'H': _rgb(0x41494a), 'I': _rgb(0x505355), 'J': _rgb(0x5d6870), 'L': _rgb(0x697174),
    'h': _rgb(0x54220f), 'i': _rgb(0x8a3c18), 'j': _rgb(0xc25f24), 'k': _rgb(0xe39144), 'o': _rgb(0xf6d39a),
}
CLOTH = [COLORS[k] for k in '123456']
GREY = [COLORS[k] for k in 'abcdefg']
BLUE = [COLORS[k] for k in 'BDEF']
LEATHER = [COLORS[k] for k in 'qlmn']
WINDOW = {COLORS[k][:3] for k in 'stuvwyz'}
OWN = {COLORS[k][:3] for k in COLORS} - {INK[:3]}

HOOD = (                          # Its window's middle is column 13, row 12
    "........#######........",
    ".....###5555444##......",
    "....#556665554443#.....",
    "...#55666555544443#....",
    "..#5556655555444433#...",
    "..##455555554444433#...",
    ".#54##44444444444332#..",
    ".#665##33333333332aa#..",
    "#5665#abbbbbbbbbbbbba#.",
    "#5654#bcccwcccccbbba#3#",
    "#4554#bcyzzsssssbbca#4#",
    "#4544#bcyssstttssbca#3#",
    "#4443#bcttttwuuuttba#2#",
    "#3433#bbtuuuwvvvutba##.",
    "#3233#bbctuubbbbuuba#..",
    ".#333##bbbbbccbbbbbb#..",
    ".#2333#adeedabccbaea#..",
    "..#233#deffedabcbefd#..",
    "..#3322deeeedabbbeed#..",
    ".#44332adeddaabbbadd#..",
    ".#443322aaaa#aabbaa#...",
    ".##33332222###aaa##....",
    "...##########.##.......",
)
HOOD_AT = (11, 13)                # Of its map, the middle of her head (hazmat_figure.HEAD)

TORSO_X0 = 12                     # Standing, on the walk grid; its first row is 7 under her head's middle
TORSO = (
    "..#344444444432#..",
    ".#35544444444332#.",
    ".#45554444444332#.",
    ".#4565BBqBB24332#.",
    ".#4555BqGqB24332#.",
    ".#4555BBqBB24332#.",
    ".#45654444524332#.",
    ".#45544444524332#.",
    ".#45544444524332#.",
    ".#45544444523332#.",
    ".#44544443523332#.",           # From here to the belt, rows can be dropped or repeated
    ".#44453444523322#.",
    ".#44443444523322#.",
    ".#32444444523222#.",
    ".#33244444423222#.",
)
TORSO_PLAIN = 11                  # The row repeated or dropped to fit
BELT = (                          # With a pouch over each hip
    ".################.",
    "#ql#qllllfellm#lm#",
    "#lm#mmmmmcdmmn#mn#",
    "#mn############mn#",
    "####..........####",
)

# The SWAT's helmet with its amber goggles up, over a sealed hood and the same respirator. Its
# corner is the one of the helmet on swat/stand.png.
SWAT_HEAD = (
    "...........bb####...........",
    "..........bbHAAA#b..........",
    "......bbb#AHJHHHIb..........",
    ".....##HHHHLLICLJJ##........",
    "...bbAHHHHHHHHHHHHHHA#......",
    "...bHHHHHHHH###########.....",
    "..#AHHHHHHH#cjkkoojjjic#....",
    "..#bbbbbbbb#cjkojjjjiic#....",
    ".b#bCHHHHHH#cijjjjiiihc#....",
    "##HIHHHHHHHH############....",
    "bCJJJIHIabbbbbbbbbbbbba#....",
    "#HHJLLIHbcccwcccccbbba#.....",
    "#HHHLJHbbcjiisssssbbca#.....",
    "bACHJJH#bcjssstttssbca#.....",
    ".#AHJLC#bcttttwuuuttba#.....",
    "..#AHHbAbbtuuuwvvvutba#.....",
    "...#AAAHbbctuubbbbuuba#.....",
    "....#332#bbbbbccbbbbbb#.....",
    "....#433#adeedabccbaea#.....",
    "...#4433#deffedabcbefd#.....",
    "...#43322deeeedabbbeed#.....",
    "...#33222adeddaabbbadd#.....",
    "....####22aaaa#aabbaa#......",
)
SWAT_AT = (8, 4)
SWAT_TANK = (-4, 21)              # The bottle's corner, from the helmet's
# Its carrier on its chest, on swat/stand.png: straps, a plate with its own volume, three soft
# pouches and a skirt that narrows to the belt.
SWAT_VEST = (
    "...bccb.bccb...",
    "..bcdcbbbcdcb..",
    ".bcdedccccccbb.",
    "abcdeedddcccbba",
    "abcdedddddccbba",
    "abcddddddcccbba",
    "abbccccccccbbaa",
    ".aabbbbbbbbbaa.",
    ".bcccabcccabcb.",
    ".bddcabddcabcb.",
    ".bcccabcccabbb.",
    ".abbaaabbaaaba.",
    "..bccccccccbb..",
    "..abccccccbba..",
    "...abbbbbbba...",
)
SWAT_VEST_AT = (14, 27)

TANK = (
    "..###..",
    ".#gff#.",
    "#gffed#",
    "#gfedc#",
    "#fedcb#",
    "#aaaaa#",
    "#fedcb#",
    "#RRrrb#",
    "#RRrrb#",
    "#fedcb#",
    "#fedcb#",
    "#fedcb#",
    "#aaaaa#",
    "#edcbb#",
    "#edcbb#",
    ".#dcb#.",
    ".#gfd#.",
    ".#fe#..",
    "..##...",
)
TANK_AT = (-14, 6)                # Its corner, from her head's middle

# From the front, for the bench: two columns of it either side of the middle of her.
HOOD_FRONT = (
    ".......########.......",
    ".....##55554444##.....",
    "....#556655544443#....",
    "...#55665555444433#...",
    "..#5556555554444433#..",
    "..#4555555544444433#..",
    ".##4444444444433333##.",
    "#55#33333333333322#32#",
    "#65#abbbbbbbbbbbba#43#",
    "#65#bcccwccccccccb#43#",
    "#55#bcyzsssssssscb#43#",
    "#54#bcyssttttssscb#43#",
    "#44#bcttuwuuuuttcb#32#",
    "#44#bbtuuwvvvuutbb#32#",
    "#43#bbbuubbbbuubbb#32#",
    ".###bbbbbbccbbbbbb###.",
    "..#adeedabccbadeeda#..",
    "..#deffedabbadeffed#..",
    "..#deeedcabbacdeeed#..",
    ".##addddaabbaadddda##.",
    ".#4#aaaa#abba#aaaa#3#.",
    ".##33333##aa##33322##.",
    "...######.##.######...",
)
TORSO_FRONT = (
    "3444444524433333",
    "4444555524443332",
    "4BBqBB4524443332",
    "4BqGqB4524443332",
    "4BBqBB4524443332",
    "4445554524443332",
    "4444554524443332",
    "3444544524443322",
    "3444444524433322",
    "3344444424433222",
    "################",
    "qllllllfellllmmn",
    "mmmmmmmcdmmmmnnn",
    "################",
)


def cloth_tones() -> set:
    return {c[:3] for c in CLOTH}


def pixels(rows, x0: int, y0: int) -> dict:
    return {(x0 + i, y0 + j): COLORS[c] for j, row in enumerate(rows) for i, c in enumerate(row) if c != '.'}


def hood(cx: float, cy: float) -> dict:
    """The sheriff's, round her head's middle."""
    return pixels(HOOD, round(cx) - HOOD_AT[0], round(cy) - HOOD_AT[1])


def tank(cx: float, cy: float) -> dict:
    """The air bottle down her back."""
    return pixels(TANK, round(cx) + TANK_AT[0], round(cy) + TANK_AT[1])


def torso(cx: float, cy: float, middle: float, belt: int) -> dict:
    """The loose coverall from under her hood to her belt, whose upper outline is on row belt;
    middle: the column of her hips. Her shoulders stay under her head and her belt on her hips."""
    top = round(cy) + 7
    rows = list(TORSO)
    while len(rows) > max(6, belt - top):
        del rows[min(TORSO_PLAIN, len(rows) - 1)]
    while len(rows) < belt - top:
        rows.insert(TORSO_PLAIN, TORSO[TORSO_PLAIN + (len(rows) % 2)])
    rows += BELT
    out = {}
    for j, row in enumerate(rows):
        t = min(1., j / max(1, belt - top))
        out.update(pixels((row,), round(TORSO_X0 + (cx - 20.4) * (1 - t) + (middle - 20.9) * t), top + j))
    return out


def edged(body: dict, arm: dict, sleeves: set) -> dict:
    """Her body with an outline round the sleeves in front of it: cloth on cloth, an arm would
    be lost. sleeves: the colours the arm's cloth is drawn in."""
    out = dict(body)
    cloth = cloth_tones()
    for (x, y), c in arm.items():
        if c[:3] in sleeves:
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q not in arm and q in body and body[q][:3] in cloth:
                    out[q] = INK
    return out


def no_slivers(body: dict, arm: dict, least: int = 5) -> dict:
    """Bits of cloth an arm leaves between itself and an edge, too small to read: outline."""
    out = dict(body)
    cloth = cloth_tones()
    left = {p for p, c in body.items() if c[:3] in cloth and p not in arm}
    beside = {(x, y) for x, y in arm if any(q not in arm for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))}
    while left:
        group, todo = {left.pop()}, []
        todo.extend(group)
        while todo:
            x, y = todo.pop()
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in left:
                    left.discard(q)
                    group.add(q)
                    todo.append(q)
        if len(group) < least and any(abs(x - a) + abs(y - b) < 3 for x, y in group for a, b in beside):
            out.update({p: INK for p in group})
    return out


def whole_patch(body: dict, arm: dict, least: float = .6) -> dict:
    """Her body without the patch on its chest where an arm leaves only bits of it."""
    spots = {p for p, c in body.items() if c in (COLORS['B'], COLORS['q'], COLORS['G']) and
             any(body.get((p[0] + a, p[1] + b)) == COLORS['B'] for a in (-1, 0, 1) for b in (-1, 0, 1))}
    if not spots or sum(p not in arm for p in spots) >= least * len(spots):
        return body
    return {p: COLORS['4'] if p in spots else c for p, c in body.items()}


def shoulder_patch(arm: dict, sleeves: set, at: tuple) -> dict:
    """A patch on her near sleeve, just under the shoulder: at."""
    cloth = {p for p, c in arm.items() if c[:3] in sleeves}
    blocks = [((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)) for x, y in cloth]
    blocks = [b for b in blocks if all(q in cloth for q in b)]
    if not blocks:
        return {}
    best = min(blocks, key=lambda b: (math.dist((b[0][0] + 1, b[0][1] + 1), at), b))
    if math.dist((best[0][0] + 1, best[0][1] + 1), at) > 3.5:
        return {}
    return dict(zip(best, (COLORS[c] for c in 'EDDB')))


def worn(px: dict, sleeve: tuple, glove: tuple, far: bool = False) -> dict:
    """Her arms in the suit: sleeves of its cloth, long blue gloves, and what she holds as it is.
    sleeve, glove: the colours her sleeves (light, base, shade) and gloves (light, shade) are
    drawn in. far: the arm behind her, a tone deeper."""
    cloth = dict(zip((c[:3] for c in sleeve), CLOTH[1:4][::-1] if far else CLOTH[2:5][::-1]))
    long = dict(zip((c[:3] for c in sleeve), BLUE[:2][::-1] + BLUE[:1] if far else BLUE[:3][::-1]))
    hand = dict(zip((c[:3] for c in glove), BLUE[:2][::-1] if far else BLUE[1:3][::-1]))
    hands = {p for p, c in px.items() if c[:3] in hand}
    out, cuffs = {}, set()
    for p, c in px.items():
        if c[:3] in hand:
            out[p] = hand[c[:3]]
        elif c[:3] in cloth:
            near = min((math.dist(p, q) for q in hands if abs(p[0] - q[0]) < 4 and abs(p[1] - q[1]) < 4), default=9)
            # The gauntlet, up to its turned cuff
            out[p] = cloth[c[:3]] if near > 3.2 else BLUE[0] if near > 2.3 else long[c[:3]]
            if near <= 2.3:
                cuffs.add(p)
        else:
            out[p] = c[:3] + (255,)
    for p, c in px.items():                              # One glove, not a cuff and a hand apart
        x, y = p
        sides = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if c[:3] == INK[:3] and any(q in hands for q in sides) and any(q in cuffs for q in sides):
            out[p] = BLUE[0]
    return out
