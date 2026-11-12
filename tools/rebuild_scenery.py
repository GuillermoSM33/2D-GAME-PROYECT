#!/usr/bin/env python3
"""Rebuild the map art from its sources without touching characters or audio.

Usage: python3 tools/rebuild_scenery.py [assets_dir] [--objects-only]
       python3 tools/rebuild_scenery.py --verify [--objects-only]

--verify renders to a temporary directory and compares PNG bytes, leaving the
assets untouched. --objects-only keeps the already approved background art.
Only the Python standard library is needed on Windows and Linux.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent


def generate(destination: Path, objects_only: bool) -> None:
    scripts = ['make_props.py', 'make_houses.py', 'refine_terrain.py']
    if not objects_only:
        scripts.insert(0, 'make_landscape.py')
    for script in scripts:
        subprocess.run([sys.executable, str(ROOT / 'tools' / script), str(destination)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--objects-only', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify:
        generate(args.assets_dir, args.objects_only)
        return 0
    with tempfile.TemporaryDirectory(prefix='themiracle-scenery-') as directory:
        generated = Path(directory)
        generate(generated, args.objects_only)
        failures = []
        count = 0
        for candidate in sorted(generated.rglob('*.png')):
            relative = candidate.relative_to(generated)
            target = args.assets_dir / relative
            count += 1
            if not target.is_file() or candidate.read_bytes() != target.read_bytes():
                failures.append(str(relative))
        for name in failures:
            print(f'FALLO: recurso ausente o distinto del generador: {name}', file=sys.stderr)
        print(f'scenery: {count} hojas; {len(failures)} diferencias')
        return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
