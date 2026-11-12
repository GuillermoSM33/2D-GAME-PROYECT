#!/usr/bin/env python3
"""Rebuild ui, vial, mercenary, chest, bat, clues and crow, or verify them.

Usage: python3 tools/rebuild_support_art.py [assets_dir] [--verify]
Native RGBA art; standard library only. Does not regenerate scenery, characters
or audio. The font remains the renderer's white tint mask, with identical metrics.
"""
from pathlib import Path
import argparse
import tempfile

import make_ui as ui
import make_sprites as sprites
import make_clues as clues
import make_cinematics as cinematic
import make_terrain as terrain
from make_chest import make_chest
from support_finishes import finish_ui

ROOT = Path(__file__).resolve().parent.parent


def generate(destination):
    images = {
        'ui/font': ui.make_font(), 'ui/panel': ui.make_panel(), 'ui/button': ui.make_button(),
        'ui/key': ui.make_key(), 'ui/pip': ui.make_pip(), 'ui/bar': ui.make_bar(),
        'ui/icons': ui.make_icons(), 'ui/icons_hd': ui.make_icons_hd(),
        'ui/weapons': ui.make_weapons(), 'ui/weapons_hd': ui.make_weapons_hd(),
        'ui/notice_dev': ui.make_notice_dev(),
        'ui/badge_player': sprites.make_badge(sprites.BADGE_STYLES['player']),
        'ui/badge_zombie': sprites.make_badge(sprites.BADGE_STYLES['zombie']),
        'vial/held': cinematic.make_vial(),
        'mercenary/walk': cinematic.make_mercenary(ROOT / 'assets'),
        'mercenary/aim': cinematic.make_mercenary_front(),
        'chest/open': make_chest(), 'chest/sparks': sprites.make_sparks(),
        'bat/bat': terrain.make_bat(), 'crow/crow': terrain.make_crow(),
        'clues/clues': clues.make_clues(), 'clues/stamp': clues.make_stamp(),
    }
    for name, image in images.items():
        if name.startswith('ui/'):
            finish_ui(image, name.split('/')[1])
        image.save(destination / 'sprites' / (name + '.png'))
    return list(images)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify:
        names = generate(args.assets_dir)
        print(f'support art: {len(names)} sheets rebuilt')
        return 0
    with tempfile.TemporaryDirectory(prefix='themiracle-support-') as temp:
        generated = Path(temp)
        names = generate(generated)
        bad = [name for name in names if not (args.assets_dir / 'sprites' / (name + '.png')).is_file()
               or (generated / 'sprites' / (name + '.png')).read_bytes() !=
                  (args.assets_dir / 'sprites' / (name + '.png')).read_bytes()]
        for name in bad: print('FALLO:', name)
        print(f'support art: {len(names)} sheets; {len(bad)} differences')
        return bool(bad)


if __name__ == '__main__':
    raise SystemExit(main())
