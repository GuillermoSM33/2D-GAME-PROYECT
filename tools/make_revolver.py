#!/usr/bin/env python3
"""The sheriff's shared revolver, with a fluted cylinder and a walnut grip.

python3 tools/make_revolver.py [--audio]
Native pixel art; the grip and muzzle keep cowgirl_arm's existing anchors.
Audio edits use the already licensed, exported mechanical recordings, never
overwrite legacy WAVs, and need only the standard library on Windows/Linux.
"""
from __future__ import annotations

import argparse
import array
import math
from pathlib import Path
import sys
import wave

from make_sprites import Image, rgb

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets/sprites/characters/cowgirl/weapons/pistol.png'
OUTPUTS = ('weapons/revolver_cycle', 'weapons/revolver_reload')
PALETTE = {
    'o': 0x252018, 'd': 0x30343b, 's': 0x4c535b, 'm': 0x777e85,
    'l': 0xb3b8b6, 'h': 0xe0dbc9, 'w': 0x70462c, 'W': 0xa27248,
    'b': 0xb59050,
}
GUN = (
    '..............oo.',
    '...oo.ooooooooooo',
    '..odollhhhhllllmo',
    '..osmmmlssssssmdo',
    '..odsdsmdddddddoo',
    '..odsdmsooooooooo',
    '..oWwodmbbo......',
    '.oWWwoodoo.......',
    '.oWwwoooo........',
    'oWWwwo...........',
    'obbbbo...........',
)


def draw() -> None:
    image = Image(17, 11)
    for y, row in enumerate(GUN):
        assert len(row) == image.width
        for x, mark in enumerate(row):
            if mark != '.':
                image.set(x, y, rgb(PALETTE[mark]))
    image.save(OUT)


def audio(assets_dir: Path = ROOT / 'assets', only: list[str] | None = None) -> None:
    rate = 22050
    sounds = ROOT / 'assets/sounds'

    def read(name: str) -> list[float]:
        with wave.open(str(sounds / (name + '.wav')), 'rb') as source:
            assert source.getparams()[:3] == (1, 2, rate)
            pcm = array.array('h', source.readframes(source.getnframes()))
        if sys.byteorder == 'big':
            pcm.byteswap()
        return [s / 32768 for s in pcm]

    def excerpt(samples: list, start: float, length: float) -> list:
        chunk = samples[round(start * rate):round((start + length) * rate)]
        return [s * min(1, i / 66, (len(chunk) - 1 - i) / 220)
                for i, s in enumerate(chunk)]

    latch = excerpt(read('weapons/rifle_empty'), .01, .14)
    handling = read('weapons/shotgun_cycle')
    rounds = read('weapons/switch')
    for name, duration, cues in (
        ('revolver_cycle', .285, [(0, latch, .7)]),
        # Release / eject / speedloader / close, matching reload.png's keys.
        ('revolver_reload', 1.2, [(.01, latch, .8),
             (.22, excerpt(handling, .12, .18), .65),
             (.55, excerpt(rounds, .01, .23), .8),
             (.96, excerpt(handling, .34, .22), .9)]),
    ):
        if only is not None and f'weapons/{name}' not in only:
            continue
        samples = [0.0] * round(duration * rate)
        for at, part, gain in cues:
            offset = round(at * rate)
            for i, value in enumerate(part[:len(samples) - offset]):
                samples[offset + i] += value * gain
        rms = math.sqrt(sum(s * s for s in samples) / len(samples))
        gain = min(.88 / max(abs(s) for s in samples), .12 / max(rms, 1e-9))
        pcm = array.array('h', (round(s * gain * 32767) for s in samples))
        if sys.byteorder == 'big':
            pcm.byteswap()
        output = assets_dir / f'sounds/weapons/{name}.wav'
        output.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output), 'wb') as target:
            target.setparams((1, 2, rate, len(pcm), 'NONE', 'not compressed'))
            target.writeframes(pcm.tobytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--audio', action='store_true')
    parser.add_argument('--only', nargs='+', choices=OUTPUTS)
    parser.add_argument('--fetch', action='store_true', help='exports already included in assets; no download needed')
    args = parser.parse_args()
    if not args.only:
        draw()
    if args.audio or args.only:
        audio(args.assets_dir, args.only)
    print('make_revolver: done')
