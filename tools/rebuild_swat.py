#!/usr/bin/env python3
"""Rebuild all SWAT art, or compare it without modifying the assets.

Usage: python3 tools/rebuild_swat.py [--verify]
Preserves the original source drawing, frame sizes, pivots and action timing.
Only the standard library is needed. Other characters are never regenerated.
"""
import argparse
from pathlib import Path
import tempfile

from make_swat import make_sheets, load_source, ROOT, OUT_DIR
from make_faint import make as make_faint
from swat_walk import make_light_walk, rig_parts
from make_plant import make_swat_sheet
from make_sit import make_sit
from swat_materials import finish
from swat_authored import make as make_authored


RIG_DIR = ROOT / 'docs/templates/swat/rig'


def generate(destination, rig_destination):
    sheets = make_sheets()
    # Derive every secondary pose from the same material tags before finishing.
    # In particular, the fallen body rotates the detailed helmet, not a new one.
    sheets['faint'] = make_faint(sheets['stand'])
    sheets['plant'] = make_swat_sheet()
    sheets['sit'] = make_sit('swat', 1, 'rifle')
    sheets['sit_shotgun'] = make_sit('swat', 2, 'shotgun')
    for suffix in ('', '_shotgun'):
        sheets['light_walk' + suffix] = make_light_walk(sheets['legs'], sheets['light' + suffix])
    sheets = {name: finish(sheet) for name, sheet in sheets.items()}
    authored, painted_parts, origins = make_authored(sheets['legs'])
    sheets.update(authored)
    for name, sheet in sheets.items():
        sheet.save(destination / f'{name}.png')
    parts = rig_parts(load_source())
    for name, sheet in parts.items():
        finish(sheet).save(rig_destination / f'{name}.png')
    for name, sheet in painted_parts.items():
        sheet.save(rig_destination / f'{name}.png')
    parts.update(painted_parts)
    return list(sheets), list(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify:
        names, parts = generate(OUT_DIR, RIG_DIR)
        print(f'SWAT: {len(names)} sheets and {len(parts)} rig layers rebuilt')
        return 0
    with tempfile.TemporaryDirectory(prefix='themiracle-swat-') as temp:
        generated = Path(temp)
        rig = generated / 'rig'
        names, parts = generate(generated, rig)
        bad = [name for name in names if not (OUT_DIR / f'{name}.png').is_file()
               or (generated / f'{name}.png').read_bytes() != (OUT_DIR / f'{name}.png').read_bytes()]
        for name in bad:
            print('FALLO: swat/' + name)
        bad_parts = [name for name in parts if not (RIG_DIR / f'{name}.png').is_file()
                     or (rig / f'{name}.png').read_bytes() != (RIG_DIR / f'{name}.png').read_bytes()]
        for name in bad_parts:
            print('FALLO: swat/rig/' + name)
        print(f'SWAT: {len(names)} sheets and {len(parts)} rig layers; {len(bad) + len(bad_parts)} differences')
        return bool(bad or bad_parts)


if __name__ == '__main__':
    raise SystemExit(main())
