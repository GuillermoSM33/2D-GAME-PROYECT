#!/usr/bin/env python3
"""Build the game's effects from recorded CC0 foley and original layers.

Usage: tools/make_sfx.py [assets_dir] [--only folder/name ...] [--fetch]

The default uses recorded physical mechanisms, impacts, birds and weather.
It never replaces original world/zombie or player/shot,reload WAVs.
FFmpeg is needed only for authoring. Source licences: docs/AUDIO.md.
Legacy synthesis helpers remain for tools/crush_sfx.py and --legacy, which
only creates missing originals; it never overwrites an existing recording.
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
import importlib
import subprocess
from pathlib import Path

RATE = 22050


class Noise:
    """NES-style noise: a 15-bit LFSR clocked at a given rate (higher = brighter)."""

    def __init__(self) -> None:
        self.lfsr = 1
        self.phase = 0.0
        self.value = 1.0

    def step(self, clock_hz: float) -> float:
        self.phase += clock_hz / RATE
        while self.phase >= 1.0:
            self.phase -= 1.0
            bit = (self.lfsr ^ (self.lfsr >> 1)) & 1
            self.lfsr = (self.lfsr >> 1) | (bit << 14)
            self.value = 1.0 if self.lfsr & 1 else -1.0
        return self.value


class Square:
    def __init__(self, duty: float = 0.5) -> None:
        self.duty = duty
        self.phase = 0.0

    def step(self, freq_hz: float) -> float:
        self.phase = (self.phase + freq_hz / RATE) % 1.0
        return 1.0 if self.phase < self.duty else -1.0


def shot() -> list[float]:
    """Pirate hand cannon: a short crack, a heavy low boom and a rolling tail."""
    length = int(RATE * 0.55)
    noise = Noise()
    thump = Square(duty=0.5)
    out = []
    for i in range(length):
        t = i / RATE
        # Noise: starts duller than a pistol and sinks into a low rumble
        # that lingers, like black powder smoke.
        clock = 9000.0 * math.exp(-t * 18.0) + 350.0
        boom = noise.step(clock) * (0.75 * math.exp(-t * 9.0) + 0.25 * math.exp(-t * 3.5))
        # Square: a deep drop from 220 Hz to ~45 Hz is the weight of the shot.
        freq = 175.0 * math.exp(-t * 16.0) + 45.0
        body = thump.step(freq) * 0.55 * math.exp(-t * 10.0)
        # Tiny attack ramp avoids a click at the start.
        attack = min(1.0, t / 0.002)
        out.append(attack * (0.75 * boom + body))
    return out


def reload() -> list[float]:
    """Muzzle-loading between shots: ramrod scrape, ball seated, hammer cocked.

    Played together with the shot, so it starts with a pause while the boom
    rings out, and its last click lands as the reload ends (~0.38 s, see
    PLAYER_SHOOT_RELOAD_TIME in src/config.h)."""
    length = int(RATE * 0.40)
    noise = Noise()
    thunk = Square(duty=0.5)
    out = []
    for i in range(length):
        t = i / RATE
        s = 0.0
        # Ramrod: a soft scrape whose pitch rises as it slides down the barrel.
        if 0.10 <= t < 0.23:
            u = (t - 0.10) / 0.13
            scrape = noise.step(2500.0 + 5000.0 * u)
            s += 0.22 * scrape * math.sin(math.pi * u)
        # Ball seated: a short dull knock at the bottom.
        if 0.23 <= t < 0.29:
            u = t - 0.23
            s += 0.5 * thunk.step(140.0 - 600.0 * u) * math.exp(-u * 70.0)
        # Hammer cocked: two quick metallic ticks.
        for at in (0.34, 0.37):
            if at <= t < at + 0.015:
                s += 0.45 * noise.step(16000.0) * math.exp(-(t - at) * 300.0)
        out.append(s)
    return out


def explosion() -> list[float]:
    """A powder barrel going up: a hard crack, a deep boom and falling debris."""
    length = int(RATE * 1.1)
    noise = Noise()
    debris = Noise()
    thump = Square(duty=0.5)
    out = []
    for i in range(length):
        t = i / RATE
        clock = 6000.0 * math.exp(-t * 6.0) + 180.0
        boom = noise.step(clock) * (0.8 * math.exp(-t * 4.0) + 0.2 * math.exp(-t * 1.5))
        freq = 120.0 * math.exp(-t * 8.0) + 32.0
        body = thump.step(freq) * 0.6 * math.exp(-t * 5.0)
        rattle = debris.step(2500.0) * 0.18 * max(0.0, math.sin(t * 40.0)) * math.exp(-t * 3.0)             if t > 0.25 else 0.0
        attack = min(1.0, t / 0.002)
        out.append(attack * (0.7 * boom + body + rattle))
    return out


def supply() -> list[float]:
    """Supplies taken: two quick rising blips and a box being set down."""
    length = int(RATE * 0.45)
    lead = Square(duty=0.25)
    noise = Noise()
    out = []
    for i in range(length):
        t = i / RATE
        if t < 0.08:
            tone = lead.step(660.0) * 0.45
        elif t < 0.18:
            tone = lead.step(990.0) * 0.45 * math.exp(-(t - 0.08) * 8.0)
        else:
            tone = 0.0
        thud = noise.step(900.0) * 0.5 * math.exp(-(t - 0.25) * 30.0) if t >= 0.25 else 0.0
        out.append(tone + thud)
    return out


def fuse() -> list[float]:
    """A fuse lit: a match struck (a scratch and a soft whoosh as it catches),
    then the fuse burning, a thin hiss with pops at random, never repeating,
    dying down over the charge's fuse (CHARGE_FUSE in src/config.h). The
    blast is its own sound."""
    length = int(RATE * 2.4)
    scratch = Noise()
    hiss = Noise()
    pop = Noise()
    out = []
    state = 12345
    pop_left = 0
    for i in range(length):
        t = i / RATE
        # Strike: a rough scratch (0-0.08 s), then the flare catching.
        strike = 0.0
        if t < 0.08:
            strike = scratch.step(4000.0 + 30000.0 * t) * 0.55 * (1.0 - t / 0.08)
        flare = hiss.step(9000.0) * 0.45 * math.exp(-(t - 0.08) * 9.0) if t >= 0.08 else 0.0
        # Burning: a quiet hiss whose loudness wanders, dimming toward the end.
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        wander = 0.75 + 0.25 * ((state >> 16) % 1000) / 1000.0
        burn = hiss.step(14000.0) * 0.16 * wander * (1.0 - 0.5 * t / 2.4) if t >= 0.12 else 0.0
        # Pops: short random bursts, a few per second.
        if pop_left == 0 and t >= 0.15 and (state >> 8) % 1400 == 0:
            pop_left = int(RATE * 0.012)
        crackle = 0.0
        if pop_left > 0:
            crackle = pop.step(2500.0) * 0.45 * pop_left / (RATE * 0.012)
            pop_left -= 1
        fade = min(1.0, (2.4 - t) / 0.15)
        out.append(fade * (strike + flare + burn + crackle))
    return out


def glass() -> list[float]:
    """Bottles shot to bits: a bright crack and tinkling shards."""
    length = int(RATE * 0.5)
    crack = Noise()
    tinkle = Square(duty=0.125)
    out = []
    state = 99
    for i in range(length):
        t = i / RATE
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        hit = crack.step(16000.0) * 0.6 * math.exp(-t * 40.0)
        freq = 2400.0 + 1600.0 * ((state >> 16) % 7) / 7.0
        shards = tinkle.step(freq) * 0.18 * math.exp(-t * 7.0) if t > 0.03 else 0.0
        out.append(hit + shards)
    return out


def wood() -> list[float]:
    """A crate split open: a dry crack and boards clattering down."""
    length = int(RATE * 0.45)
    crack = Noise()
    knock = Square(duty=0.5)
    out = []
    for i in range(length):
        t = i / RATE
        snap = crack.step(5000.0) * 0.6 * math.exp(-t * 30.0)
        thud = knock.step(150.0 * math.exp(-t * 4.0) + 70.0) * 0.4 * math.exp(-t * 12.0)
        clatter = crack.step(1800.0) * 0.25 * abs(math.sin(t * 60.0)) * math.exp(-t * 6.0) if t > 0.12 else 0.0
        out.append(snap + thud + clatter)
    return out


def snap() -> list[float]:
    """A bear trap shutting: two iron jaws clanging together."""
    length = int(RATE * 0.35)
    clang = Square(duty=0.25)
    hit = Noise()
    out = []
    for i in range(length):
        t = i / RATE
        ring = clang.step(780.0 + 120.0 * math.sin(t * 90.0)) * 0.35 * math.exp(-t * 9.0)
        bang = hit.step(9000.0) * 0.6 * math.exp(-t * 50.0)
        out.append(ring + bang)
    return out


def write_wav(path: Path, samples: list[float]) -> None:
    pcm = bytes(max(0, min(255, round(128 + s * 127))) for s in samples)
    header = struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 36 + len(pcm), b'WAVE',
                         b'fmt ', 16, 1, 1, RATE, RATE, 1, 8, b'data', len(pcm))
    path.write_bytes(header + pcm)


# Builders have disjoint output catalogues. The discarded simple pulse/noise
# drafts cannot be restored accidentally by running the authoring command.
BUILDERS = ('make_weapon_foley', 'make_foley_sfx', 'make_nature_sfx', 'make_designed_sfx',
            'make_expansion_sfx', 'make_cinematic_sfx', 'make_city_sfx')
LEGACY_SOUNDS = {
    'player/shot': shot, 'player/reload': reload,
    'world/explosion': explosion, 'world/supply': supply, 'world/fuse': fuse,
    'world/glass': glass, 'world/wood': wood, 'world/snap': snap,
}


def catalog() -> dict[str, tuple[str, ...]]:
    result = {name: tuple(importlib.import_module(name).OUTPUTS) for name in BUILDERS}
    flat = [path for paths in result.values() for path in paths]
    if len(set(flat)) != len(flat):
        raise RuntimeError('Two sound builders write the same effect')
    return result


def main() -> int:
    builders = catalog()
    choices = sorted(path for paths in builders.values() for path in paths)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=Path('assets'))
    parser.add_argument('--only', nargs='+', choices=choices)
    parser.add_argument('--fetch', action='store_true', help='download missing verified CC0 sources')
    parser.add_argument('--legacy', action='store_true', help='also create missing legacy synth files')
    args = parser.parse_args()
    selected = set(args.only or choices)
    for module, names in builders.items():
        subset = [name for name in names if name in selected]
        if not subset:
            continue
        command = [sys.executable, str(Path(__file__).with_name(module + '.py')),
                   str(args.assets_dir), '--only', *subset]
        if args.fetch:
            command.append('--fetch')
        subprocess.run(command, check=True)
    if args.legacy:
        for name, make in LEGACY_SOUNDS.items():
            path = args.assets_dir / 'sounds' / (name + '.wav')
            if path.exists():
                print(f'make_sfx: preserved {path}')
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            write_wav(path, make())
            print(f'make_sfx: {path} (missing original recreated)')
    print(f'make_sfx: {len(selected)} recorded/designed effects; original files preserved.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
