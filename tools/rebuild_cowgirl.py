#!/usr/bin/env python3
"""Rebuild all the cowgirl's sheets, in the order they build on each other.

Usage: tools/rebuild_cowgirl.py

Each tool reads what the one before wrote, from her dressed templates on. Standard
library only.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
STEPS = [['make_revolver.py'], ['make_ui.py'], ['make_ricochet.py'], ['rework_cowgirl.py'],
         ['make_faint.py', 'cowgirl'], ['make_care.py'], ['make_plant.py'],
         ['make_sit.py'], ['make_flashlight.py'], ['finish_cowgirl.py'], ['detail_cowgirl.py']]


def main() -> int:
    for step in STEPS:
        done = subprocess.run([sys.executable, str(TOOLS / step[0]), *step[1:]], stdout=subprocess.DEVNULL)
        if done.returncode:
            return done.returncode
    print('rebuild_cowgirl: done')
    return 0


if __name__ == '__main__':
    sys.exit(main())
