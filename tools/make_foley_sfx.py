#!/usr/bin/env python3
"""Edit recorded CC0 foley into the game's physical actions (no oscillators).

python3 tools/make_foley_sfx.py --download
python3 tools/make_foley_sfx.py [assets_dir] [--only world/hit_wood ...]

Source archives stay in ignored recordings/cc0_foley. FFmpeg is needed only
while authoring; final WAVs are embedded by the ordinary game build.
"""
from __future__ import annotations

import argparse
import array
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import math
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import wave
import zipfile

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'recordings' / 'cc0_foley'
RATE = 22050

# All three are recorded foley, CC0; licence evidence and exact recipe table
# are in docs/AUDIO_FOLEY_SOURCES.md. The hashes reject HTML/error downloads.
PACKS = {
    'wm': ('100-CC0-wood-metal-SFX.zip',
           'https://opengameart.org/sites/default/files/100-CC0-wood-metal-SFX.zip',
           'be6eba63b03409ac0c77787a956b1503a7c186403d04aef9725c52644a4b7878'),
    'v2': ('sfx_100_v2.zip',
           'https://opengameart.org/sites/default/files/sfx_100_v2.zip',
           '0fc61b4494e2e893c0c015ced4877b3f689c7d84a48cb61daecd7ddb52db797b'),
    'step': ('footsteps.zip',
             'https://opengameart.org/sites/default/files/footsteps.zip',
             '94b5155d119d9378315c2b4457c00098d78a36f2a2c436d5145687d1d3bad257'),
}


@dataclass(frozen=True)
class Layer:
    pack: str
    name: str
    at: float = 0.0
    gain: float = 1.0
    speed: float = 1.0
    start: float = 0.0
    length: float | None = None


def wood(name: str, **kw: float) -> Layer:
    return Layer('wm', name, **kw)


def field(name: str, **kw: float) -> Layer:
    return Layer('v2', f'sfx100v2_{name}', **kw)


def cloth(n: int = 1, **kw: float) -> Layer:
    return Layer('step', f'footsteps/step_cloth{n}', **kw)


def leather(n: int = 1, **kw: float) -> Layer:
    return Layer('step', f'footsteps/step_lth{n}', **kw)


# (peak ceiling, layers). Times refer to trimmed source recordings; speed
# affects pitch and duration together, like tape. No synthetic pitch sweeps.
RECIPES = {
    'world/hit_wood': (.66, [wood('wood_hit_06'), wood('wood_cracking_01', at=.025, gain=.22)]),
    'world/hit_metal': (.66, [wood('metal_hit_03', gain=.9), wood('metal_sheet_01', at=.018, gain=.22, length=.18)]),
    'world/hit_stone': (.66, [field('stones_02'), field('hit_01', gain=.35, speed=.9, length=.12)]),
    'world/hit_sand': (.57, [field('footstep_01', gain=.75, speed=.8), cloth(3, gain=.75)]),
    'world/hit_wire': (.60, [wood('metal_sheet_01', speed=1.25, length=.19), wood('metal_hit_03', gain=.3, speed=1.5, length=.16)]),
    'world/wire': (.53, [wood('metal_sheet_01', speed=.85, length=.28), cloth(2, at=.035, gain=.55)]),
    'world/rope': (.54, [cloth(1, speed=.7), leather(2, at=.07, speed=.8, gain=.7), cloth(3, at=.2, gain=.45)]),
    'world/trap_escape': (.62, [wood('wood_cracking_01', gain=.7), cloth(4, at=.04), field('footstep_01', at=.12, gain=.5)]),
    'world/footstep': (.30, [field('footstep_01'), leather(2, gain=.35)]),
    'world/run_step': (.36, [field('footstep_02', speed=1.12), leather(1, gain=.45, speed=1.2)]),
    'world/sit': (.36, [cloth(1, speed=.8), wood('wood_squeak_01', at=.07, gain=.3, length=.24), leather(2, at=.12, gain=.3)]),
    'world/stand': (.34, [cloth(2, gain=.7), wood('wood_squeak_01', gain=.2, length=.16, speed=1.2), leather(1, at=.08, gain=.5)]),
    'effects/hit_flesh': (.64, [field('hit_01', speed=.83, length=.23), cloth(4, at=.01, gain=.5), field('footstep_wet_03', at=.015, gain=.24, length=.15)]),
    'effects/hit_armor': (.63, [wood('metal_hit_03', length=.24), leather(1, gain=.8), field('hit_01', gain=.3, length=.13)]),
    'player/melee': (.47, [field('air_02', speed=1.4, length=.29), leather(1, gain=.65), wood('wood_hit_06', at=.16, gain=.18, length=.12)]),
    'weapons/dual_melee': (.47, [field('air_02', speed=1.55, length=.24), leather(2, gain=.65), wood('metal_sheet_01', at=.12, gain=.16, length=.08)]),
    'weapons/rifle_melee': (.49, [field('air_02', speed=1.18, length=.32), cloth(2, gain=.65), wood('metal_hit_03', at=.19, gain=.16, length=.11)]),
    'weapons/shotgun_melee': (.51, [field('air_02', speed=.96, length=.34), leather(1, gain=.7), wood('wood_hit_06', at=.21, gain=.2, speed=.8, length=.12)]),
    'weapons/plasma_melee': (.48, [field('air_02', speed=1.08, length=.3), leather(2, gain=.7), wood('metal_sheet_01', at=.18, gain=.18, speed=.8, length=.12)]),
    'player/bandage': (.40, [cloth(1, gain=.8), cloth(3, at=.45, gain=.8, speed=.85), cloth(4, at=1.0, gain=.6)]),
    'player/hurt': (.57, [field('hit_01', length=.18, speed=.85), cloth(4, gain=.65), field('air_02', gain=.1, length=.15)]),
    'player/jump': (.37, [leather(1, speed=1.2), cloth(3, at=.015, gain=.75), field('air_02', at=.025, gain=.18, length=.16, speed=1.4)]),
    'player/land': (.45, [field('footstep_02', speed=.85), cloth(1, gain=.6), field('hit_01', gain=.22, length=.13)]),
    'player/death': (.58, [cloth(1, speed=.8), field('hit_02', at=.10, gain=.8, speed=.72, length=.32), leather(1, at=.28, gain=.5), cloth(4, at=.35, gain=.45)]),
    'player/faint': (.48, [cloth(2, speed=.65), leather(2, at=.15, speed=.7, gain=.5), field('hit_01', at=.30, speed=.65, gain=.65, length=.25), cloth(4, at=.47, gain=.45)]),
}

OUTPUTS = tuple(RECIPES)


def ffmpeg() -> str:
    found = shutil.which('ffmpeg')
    if not found:
        path = Path('C:/msys64/ucrt64/bin/ffmpeg.exe')
        found = str(path) if path.exists() else None
    if not found:
        raise RuntimeError('Falta ffmpeg (apt install ffmpeg / pacman -S mingw-w64-ucrt-x86_64-ffmpeg)')
    return found


def prepare_sources(download: bool = False) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for filename, url, expected in PACKS.values():
        path = CACHE / filename
        if not path.exists():
            if not download:
                raise RuntimeError(f'Falta {path}; ejecuta tools/make_foley_sfx.py --download')
            request = urllib.request.Request(url, headers={'User-Agent': 'Vaquera2D foley authoring'})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != expected:
                raise RuntimeError(f'Descarga distinta del original CC0 verificado: {url}')
            path.write_bytes(data)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'La fuente cambió o no es un ZIP: {path}')


@lru_cache(maxsize=None)
def recording(pack: str, name: str) -> tuple[float, ...]:
    with zipfile.ZipFile(CACHE / PACKS[pack][0]) as archive:
        original = archive.read(f'{name}.ogg')
    result = subprocess.run([ffmpeg(), '-v', 'error', '-i', 'pipe:0', '-ac', '1',
                             '-ar', str(RATE), '-f', 's16le', 'pipe:1'],
                            input=original, capture_output=True, check=True)
    pcm = array.array('h', result.stdout)
    if sys.byteorder == 'big':
        pcm.byteswap()
    samples = [x / 32768.0 for x in pcm]
    peak = max(map(abs, samples), default=0.0)
    if peak <= 0:
        raise RuntimeError(f'Fuente silenciosa: {pack}/{name}')
    # Trim only real dead air. Keep a little room around the transient.
    active = [i for i, x in enumerate(samples) if abs(x) > peak * .025]
    pad = int(.003 * RATE)
    samples = samples[max(0, active[0] - pad):min(len(samples), active[-1] + pad + 1)]
    return tuple(x * .75 / peak for x in samples)


def layer_samples(layer: Layer) -> list[float]:
    source = recording(layer.pack, layer.name)
    start = int(layer.start * RATE)
    stop = len(source) if layer.length is None else min(len(source), start + int(layer.length * RATE))
    out = []
    for i in range(max(0, int((stop - start - 1) / layer.speed))):
        pos = start + i * layer.speed
        j = int(pos)
        frac = pos - j
        x = source[j] + (source[j + 1] - source[j]) * frac
        edge = min(1.0, i / (.0015 * RATE), (stop - pos) / (.014 * RATE))
        out.append(x * layer.gain * edge)
    return out


def render(layers: list[Layer], ceiling: float) -> list[float]:
    pieces = [(int(layer.at * RATE), layer_samples(layer)) for layer in layers]
    out = [0.0] * (max(at + len(part) for at, part in pieces) + int(.035 * RATE))
    for at, part in pieces:
        for i, x in enumerate(part):
            out[at + i] += x
    # Remove DC and very low handling rumble; soft two-pole top rolloff gives
    # every physical action one palette while retaining recognizable foley.
    hp = math.exp(-2 * math.pi * 65.0 / RATE)
    lp = 1.0 - math.exp(-2 * math.pi * 5900.0 / RATE)
    prev_x = prev_y = low1 = low2 = 0.0
    for i, x in enumerate(out):
        prev_y = hp * (prev_y + x - prev_x)
        prev_x = x
        low1 += lp * (prev_y - low1)
        low2 += lp * (low1 - low2)
        # Gentle 2:1 compression catches isolated recording transients so
        # cloth, gravel and metal tails remain audible at comparable peaks.
        magnitude = abs(low2)
        out[i] = math.copysign(.2 + (magnitude - .2) * .5, low2) if magnitude > .2 else low2
    gain = ceiling / max(map(abs, out))
    for i, x in enumerate(out):
        edge = min(1.0, i / (.002 * RATE), (len(out) - 1 - i) / (.028 * RATE))
        out[i] = x * gain * edge
    return out


def write_wav(path: Path, samples: list[float]) -> None:
    pcm = array.array('h', (round(max(-1.0, min(1.0, x)) * 32767) for x in samples))
    if sys.byteorder == 'big':
        pcm.byteswap()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as wav:
        wav.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        wav.writeframes(pcm.tobytes())


def generate(assets_dir: Path = ROOT / 'assets', only: list[str] | None = None) -> int:
    prepare_sources()
    names = list(RECIPES) if only is None else [name for name in only if name in RECIPES]
    for name in names:
        ceiling, layers = RECIPES[name]
        samples = render(layers, ceiling)
        write_wav(Path(assets_dir) / 'sounds' / f'{name}.wav', samples)
        rms = math.sqrt(sum(x*x for x in samples) / len(samples))
        print(f'foley: {name} ({len(samples)/RATE:.3f}s, peak {ceiling:.2f}, RMS {rms:.3f})')
    return len(names)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--only', nargs='+', choices=sorted(RECIPES))
    parser.add_argument('--download', '--fetch', dest='download', action='store_true',
                        help='descarga originales CC0 si faltan')
    args = parser.parse_args()
    prepare_sources(args.download)
    generate(args.assets_dir, args.only)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
