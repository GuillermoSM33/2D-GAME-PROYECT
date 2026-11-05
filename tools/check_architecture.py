#!/usr/bin/env python3
"""Check application/engine/game boundaries and pure-logic dependencies.

Read-only, standard library only. No source generation or network access.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
INCLUDE = re.compile(r'^\s*#\s*include\s*[<"]([^>"\n]+)[>"]', re.M)


def sources(variable: str) -> list[str]:
    makefile = (ROOT / 'Makefile').read_text(encoding='utf-8').replace('\\\n', ' ')
    match = re.search(r'^' + variable + r'\s*:=\s*(.+)$', makefile, re.M)
    if not match:
        raise ValueError(f'Missing {variable} catalogue in Makefile')
    return match[1].split()


def audit() -> list[str]:
    errors = []
    files = {p.relative_to(SRC).as_posix(): p for p in SRC.rglob('*')
             if p.suffix in {'.c', '.h'}}
    core, app = sources('CORE_SRC'), sources('APP_SRC')
    listed = core + app
    actual = {'src/' + name for name in files if name.endswith('.c')}
    for name in sorted(actual - set(listed)):
        errors.append(f'{name}: source absent from Makefile')
    for name in sorted(set(listed) - actual):
        errors.append(f'{name}: Makefile references a missing source')
    for name, count in Counter(listed).items():
        if count > 1:
            errors.append(f'{name}: listed {count} times in Makefile')
    graph: dict[str, list[str]] = {}
    sdl = set()
    for name, path in files.items():
        graph[name] = []
        for target in INCLUDE.findall(path.read_text(encoding='utf-8')):
            if target.endswith('.c'):
                errors.append(f'{name}: includes implementation {target}; include its header and link it')
            local = target if target in files else (Path(name).parent / target).as_posix()
            if local in files:
                graph[name].append(local)
                if name.startswith('engine/') and local.startswith(('game/', 'app/')):
                    errors.append(f'{name}: engine depends on {local}')
                if name.startswith('game/') and local.startswith('app/'):
                    errors.append(f'{name}: game depends on application {local}')
                if name == 'main.c' and not local.startswith('app/'):
                    errors.append(f'main.c: entry point depends directly on {local}')
            if Path(target).name.startswith('SDL'):
                sdl.add(name)
    for origin in core:
        pending = [(origin.removeprefix('src/'), [])]
        seen = set()
        while pending:
            node, chain = pending.pop()
            if node in seen:
                continue
            seen.add(node)
            if node in sdl or node.startswith('app/'):
                errors.append(f'{origin}: pure logic depends on ' + ' -> '.join(chain + [node]))
                break
            pending.extend((child, chain + [node]) for child in graph.get(node, []))
    for path in (ROOT / 'tests').glob('*.c'):
        for target in INCLUDE.findall(path.read_text(encoding='utf-8')):
            if target.endswith('.c'):
                errors.append(f'{path.relative_to(ROOT)}: includes implementation {target}')
    return errors


def main() -> int:
    try:
        errors = audit()
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print('FAIL:', error)
    if not errors:
        print('architecture: OK: all C sources catalogued; layer boundaries and pure logic checked')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
