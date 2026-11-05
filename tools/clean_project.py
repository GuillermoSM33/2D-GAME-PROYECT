#!/usr/bin/env python3
"""Remove generated build files and Python/OS caches; keep dist and sources.

python3 tools/clean_project.py --dry-run
python3 tools/clean_project.py

Uses the same Python standard library on Linux and Windows. Recordings,
templates, art tools, editor settings and the shipped game are not caches.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent


def targets() -> list[Path]:
    result = []
    build = ROOT / 'build'
    if build.exists() or build.is_symlink():
        result.append(build)
    for folder in ('tools', 'tests', 'src', 'assets', 'docs', 'recordings'):
        base = ROOT / folder
        if not base.exists():
            continue
        for path in base.rglob('*'):
            if path.name == '__pycache__' or path.name in {'.DS_Store', 'Thumbs.db'} or path.suffix in {'.pyc', '.pyo'}:
                if not any(parent in result for parent in path.parents):
                    result.append(path)
    for name in ('.DS_Store', 'Thumbs.db'):
        if (ROOT / name).exists():
            result.append(ROOT / name)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    for path in targets():
        print(('Would remove: ' if args.dry_run else 'Removing: ') + path.relative_to(ROOT).as_posix())
        if not args.dry_run:
            if path.is_symlink() or path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
