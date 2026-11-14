"""Seated poses keep the compact operator's helmet, mask and carrier pixels."""
from make_sprites import Image
from swat_body import NEAR_SHOULDER, FAR_SHOULDER, WAIST


def make(gun, kind):
    from make_swat import load_source, standing_body, arm, paste, compose, crop
    from make_sit import W, H, CHARS, legs, reload_step, zs
    from make_ui import make_weapons
    from support_finishes import finish_ui
    body = standing_body(load_source())
    upper = crop(body, 0, 0, 42, WAIST)
    # Read the gun definitions directly, so a changed rifle never needs a
    # second regeneration after rebuilding its HUD icon.
    weapons = finish_ui(make_weapons(), 'weapons')
    char = CHARS['swat']
    sheet = Image(W * 14, H)
    for f in range(14):
        dy = -3 if f == 0 else -1 if f == 2 else 0
        nod = {10: 1, 11: 2, 12: 3, 13: 2}.get(f, 0)
        reloading = 4 <= f <= 9
        xoff, yoff = 15, 8 + dy
        posed = Image(W, H)
        legs(posed, 0, char, 1 if f == 0 else 0)
        # The head nods over the same collar instead of changing helmet shape.
        torso = Image(42, WAIST)
        for y in range(WAIST):
            for x in range(42):
                torso.set(x, y + (nod if y < 27 else 0), upper.get(x, y))
        def at(p):
            return p[0] + xoff, p[1] + yoff
        far_hand = (44, 47) if reloading else (43, 50)
        near_hand = (25, 47) if reloading else (28, 50)
        parts = [arm(at(FAR_SHOULDER), far_hand, False),
                 (torso, xoff, yoff), arm(at(NEAR_SHOULDER), near_hand, True)]
        paste(posed, compose(W, H, parts), 0, 0)
        if reloading:
            reload_step(posed, 0, weapons, char, gun, kind, f - 4)
        if f >= 12:
            zs(posed, 0, 1 if f == 12 else 2, char['ink'])
        paste(sheet, posed, f * W, 0)
    return sheet
