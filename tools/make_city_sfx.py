#!/usr/bin/env python3
"""The second route's sounds: a patrol car's siren, a horde coming, sparrows.

python3 tools/make_city_sfx.py [assets_dir] [--only world/siren sparrow/chirp]

  world/siren     A siren's wail, two rises and falls (4 s), looped while it
                  sounds (stage.c fades it with distance)
  world/horde     A horde coming: many of the game's own zombie voices
                  (sounds/zombie, protected originals, only read), pitched and
                  spread over three seconds, over a low shuffle of feet
  world/flare     A burning drum going over: a clang, then its fire whooshing up
  world/hydrant   A fire hydrant bursting: a bang, then its water under pressure
  world/city      The dead town's air, looped under its stages: mains hum, a
                  far car alarm, a loose shutter banging, a dog a long way off
  sparrow/chirp   A flock of sparrows taking off: quick chirps and a flutter
  sparrow/death   A sparrow shot: a squeak and a soft fall

Synthesized here (the horde layers the game's own originals), so they carry no
third-party rights. Mono PCM16 at 22050 Hz like every effect
(tools/check_audio.py). Deterministic; standard library only.
"""
from __future__ import annotations

import argparse
import array
import math
import random
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RATE = 22050
OUTPUTS = ['world/siren', 'world/horde', 'world/flare', 'world/city', 'world/hydrant', 'sparrow/chirp', 'sparrow/death']


def fade(samples: list[float], attack: float = .006, release: float = .02) -> list[float]:
    n = len(samples)
    a, r = max(1, int(attack * RATE)), max(1, int(release * RATE))
    for i in range(min(a, n)):
        samples[i] *= i / a
    for i in range(min(r, n)):
        samples[n - 1 - i] *= i / r
    samples[0] = samples[-1] = 0.0
    return samples


def normalize(samples: list[float], peak: float) -> list[float]:
    mean = sum(samples) / len(samples)
    samples = [v - mean for v in samples]
    top = max(abs(v) for v in samples) or 1.0
    return [v * peak / top for v in samples]


def siren() -> list[float]:
    """Two wails: up from 620 Hz to 1320 and back down, a square-ish tone
    through a horn (odd harmonics), with a short slap of echo off buildings."""
    n = int(4.0 * RATE)
    out, phase = [0.0] * n, 0.0
    for i in range(n):
        t = i / RATE
        cycle = (t % 2.0) / 2.0
        sweep = math.sin(math.pi * cycle) ** 1.4
        freq = 620 + 700 * sweep
        phase += math.tau * freq / RATE
        tone = math.sin(phase) + .33 * math.sin(3 * phase) + .16 * math.sin(5 * phase) + .08 * math.sin(7 * phase)
        out[i] = tone
    echo = int(.11 * RATE)
    mixed = [out[i] + (.32 * out[i - echo] if i >= echo else 0.0) for i in range(n)]
    return fade(normalize(mixed, .72), .01, .01)


def read_wav(path: Path) -> list[float]:
    with wave.open(str(path), 'rb') as src:
        raw = src.readframes(src.getnframes())
        rate, width = src.getframerate(), src.getsampwidth()
    pcm = array.array('h', raw)
    if sys.byteorder == 'big':
        pcm.byteswap()
    samples = [v / 32768 for v in pcm]
    if rate != RATE:
        samples = resample(samples, rate / RATE)
    return samples


def resample(samples: list[float], step: float) -> list[float]:
    """Read at step source samples per output sample (linear): > 1 higher."""
    out, pos = [], 0.0
    while pos < len(samples) - 1:
        i = int(pos)
        k = pos - i
        out.append(samples[i] * (1 - k) + samples[i + 1] * k)
        pos += step
    return out


def horde(assets: Path) -> list[float]:
    rng = random.Random(4207)
    voices = [read_wav(assets / 'sounds' / 'zombie' / f'{name}.wav') for name in ('idle', 'spawn', 'death')]
    n = int(3.2 * RATE)
    out = [0.0] * n
    for k in range(16):                              # Voices near and far, left to the crowd
        voice = voices[k % len(voices)]
        pitch = rng.uniform(.72, 1.12)
        shifted = resample(voice, pitch)
        start = int(rng.uniform(0, 2.2) * RATE)
        gain = rng.uniform(.35, .9) * (1 - .4 * (k / 16))
        for i, v in enumerate(shifted):
            if start + i < n:
                out[start + i] += v * gain
    low = 0.0
    for i in range(n):                               # Feet shuffling, a low rumble swelling in
        t = i / RATE
        low += .02 * (rng.uniform(-1, 1) - low)
        step = .5 + .5 * math.sin(math.tau * 2.3 * t) * math.sin(math.tau * 1.7 * t + 1)
        out[i] += low * 2.6 * step * min(1.0, t / 1.2)
    return fade(normalize(out, .85), .02, .25)


def flare() -> list[float]:
    rng = random.Random(907)
    n = int(1.1 * RATE)
    out, low, phase = [0.0] * n, 0.0, 0.0
    for i in range(n):
        t = i / RATE
        low += (.04 + .25 * math.exp(-t * 3)) * (rng.uniform(-1, 1) - low)   # The whoosh: bright, then dull
        swell = min(1.0, t / .08) * math.exp(-t * 3.2)
        out[i] = low * 3.0 * swell
        if t < .25:                                  # The drum hitting the road
            phase += math.tau * (210 - 200 * t) / RATE
            ring = math.sin(phase) + .5 * math.sin(phase * 2.76) + .3 * math.sin(phase * 5.4)
            out[i] += ring * .5 * math.exp(-t * 16)
    return fade(normalize(out, .8), .002, .1)


def hydrant() -> list[float]:
    """A hydrant bursting: a bang of metal, then two seconds of water under pressure."""
    rng = random.Random(4441)
    n = int(2.3 * RATE)
    out, last, low, phase = [0.0] * n, 0.0, 0.0, 0.0
    for i in range(n):
        t = i / RATE
        white = rng.uniform(-1, 1)
        hiss = white - .7 * last                      # Bright: spray
        last = white
        low += .05 * (white - low)                    # Dull: the column
        swell = min(1.0, t / .05) * (1.0 if t < 1.9 else max(0.0, 1 - (t - 1.9) / .4))
        out[i] = (hiss * .5 + low * 4.0) * swell * (.85 + .15 * math.sin(math.tau * 9 * t))
        if t < .2:
            phase += math.tau * (640 - 1800 * t) / RATE
            out[i] += (math.sin(phase) + .6 * math.sin(phase * 2.4)) * .9 * math.exp(-t * 22)
    return fade(normalize(out, .8), .002, .05)


def city() -> list[float]:
    """Twelve seconds that loop: every part is periodic in the loop."""
    rng = random.Random(1213)
    n = 12 * RATE
    out = [0.0] * n
    for i in range(n):
        t = i / RATE
        hum = .5 * math.sin(math.tau * 60 * t) + .3 * math.sin(math.tau * 120 * t) + .12 * math.sin(math.tau * 180 * t)
        out[i] = hum * (.75 + .25 * math.sin(math.tau * t / 6))
    air, noise = 0.0, [rng.uniform(-1, 1) for _ in range(n)]
    for i in range(2 * n):                           # Air moving between buildings: two passes so it wraps
        air += .006 * (noise[i % n] - air)
        if i >= n:
            out[i - n] += air * 9.0 * (.6 + .4 * math.sin(math.tau * (i - n) / RATE / 12))
    for k in range(6):                               # A car alarm, far off, for three seconds
        start = int((2.0 + k * .5) * RATE)
        for i in range(int(.3 * RATE)):
            u = i / (.3 * RATE)
            out[start + i] += .16 * math.sin(math.tau * (900 + 500 * u) * i / RATE) * math.sin(math.pi * u)
    for at in (6.4, 6.9, 9.8):                       # A loose shutter banging
        start = int(at * RATE)
        low = 0.0
        for i in range(int(.25 * RATE)):
            low += .3 * (rng.uniform(-1, 1) - low)
            out[start + i] += low * .9 * math.exp(-i / (.03 * RATE))
    for at, pitch in ((8.2, 420), (8.55, 380)):      # A dog, a long way off
        start = int(at * RATE)
        for i in range(int(.16 * RATE)):
            u = i / (.16 * RATE)
            out[start + i] += .12 * math.sin(math.tau * pitch * (1 - .3 * u) * i / RATE) * math.sin(math.pi * u) ** .5
    out = normalize(out, .5)
    out[-1] = out[0]
    return out


def chirp(rng: random.Random, seconds: float, low: float, high: float) -> list[float]:
    n = int(seconds * RATE)
    out, phase = [0.0] * n, 0.0
    trill = rng.uniform(55, 90)
    for i in range(n):
        u = i / n
        freq = low + (high - low) * math.sin(math.pi * u) + 260 * math.sin(math.tau * trill * i / RATE)
        phase += math.tau * freq / RATE
        env = math.sin(math.pi * u) ** .7
        out[i] = env * (math.sin(phase) + .18 * math.sin(2 * phase))
    return out


def flutter(rng: random.Random, seconds: float) -> list[float]:
    """Wings: bursts of soft noise at the wingbeat."""
    n = int(seconds * RATE)
    out, last = [0.0] * n, 0.0
    for i in range(n):
        t = i / RATE
        white = rng.uniform(-1, 1)
        band = white - last
        last = white * .6
        beat = max(0.0, math.sin(math.tau * 19 * t)) ** 3
        out[i] = band * beat * (1 - t / seconds) * .5
    return out


def sparrow_chirp() -> list[float]:
    rng = random.Random(311)
    n = int(.9 * RATE)
    out = [0.0] * n
    at = 0.0
    for k in range(7):                               # Several birds, overlapping
        piece = chirp(rng, rng.uniform(.045, .085), rng.uniform(3800, 4600), rng.uniform(5600, 7200))
        start = int(at * RATE)
        gain = rng.uniform(.5, 1.0)
        for i, v in enumerate(piece):
            if start + i < n:
                out[start + i] += v * gain
        at += rng.uniform(.05, .11)
    wings = flutter(rng, .7)
    for i, v in enumerate(wings):
        out[i + int(.05 * RATE)] += v
    return fade(normalize(out, .62), .003, .08)


def sparrow_death() -> list[float]:
    rng = random.Random(733)
    n = int(.4 * RATE)
    out = [0.0] * n
    squeak = chirp(rng, .07, 5200, 6800)
    for i, v in enumerate(squeak):
        out[i] += v
    low = 0.0
    thud = int(.26 * RATE)
    for i in range(int(.08 * RATE)):                 # It lands
        low += .25 * (rng.uniform(-1, 1) - low)
        out[thud + i] += low * 1.6 * math.exp(-i / (.015 * RATE))
    return fade(normalize(out, .55), .003, .03)


def write_wav(path: Path, samples: list[float]) -> None:
    pcm = array.array('h', (round(max(-1.0, min(1.0, v)) * 32767) for v in samples))
    if sys.byteorder == 'big':
        pcm.byteswap()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('assets', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--only', nargs='+', choices=OUTPUTS)
    parser.add_argument('--fetch', action='store_true', help='ignored: nothing to download')
    args = parser.parse_args()
    makers = {'world/siren': siren, 'world/horde': lambda: horde(ROOT / 'assets'),
              'world/flare': flare, 'world/city': city, 'world/hydrant': hydrant,
              'sparrow/chirp': sparrow_chirp, 'sparrow/death': sparrow_death}
    for name in args.only or OUTPUTS:
        samples = makers[name]()
        write_wav(args.assets / 'sounds' / f'{name}.wav', samples)
        print(f'make_city_sfx: sounds/{name}.wav ({len(samples) / RATE:.2f} s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
