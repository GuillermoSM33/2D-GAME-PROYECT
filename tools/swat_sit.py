"""Seated SWAT handling, using the current action body and full-size equipment."""
from make_swat import load, crop
from swat_actions import SOURCE, W, H, body_from_painting
from swat_authored import canonical_head
from swat_aux import seated_sheet


def make(gun, kind):
    base = crop(load(SOURCE / 'rifle.png'), 0, 0, W, H)
    body = body_from_painting(base, crop(canonical_head(base), 0, 0, W, 32))
    return seated_sheet(body, kind)
