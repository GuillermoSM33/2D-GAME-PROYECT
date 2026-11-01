#!/usr/bin/env python3
"""Generate the game's 8-bit style sound effects as WAV files.

Usage: tools/make_sfx.py [assets_dir]   (default: assets)

Writes assets/sounds/player/*.wav: 22050 Hz, mono, 8-bit unsigned PCM, the format of
old consoles. The sounds are synthesized like a chiptune sound chip does: a
noise channel from a 15-bit LFSR plus square waves, each with its own volume
envelope and pitch slide. Deterministic, so re-running gives the same files.
Uses only the standard library.
"""
from __future__ import annotations

import math
import struct
import sys
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


SOUNDS = {
    'shot': shot,
    'reload': reload,
}


def write_wav(path: Path, samples: list[float]) -> None:
    pcm = bytes(max(0, min(255, round(128 + s * 127))) for s in samples)
    header = struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 36 + len(pcm), b'WAVE',
                         b'fmt ', 16, 1, 1, RATE, RATE, 1, 8, b'data', len(pcm))
    path.write_bytes(header + pcm)


def main() -> int:
    assets_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('assets')
    out_dir = assets_dir / 'sounds' / 'player'
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, make in SOUNDS.items():
        samples = make()
        write_wav(out_dir / f'{name}.wav', samples)
        print(f'make_sfx: {out_dir / name}.wav ({len(samples) / RATE:.2f} s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
