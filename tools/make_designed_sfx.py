#!/usr/bin/env python3
"""Layer recorded metal/wood foley over the game's original audio palette.

This pass replaces only the thirteen named explosions, rewards, UI and plasma
effects below. It never writes any original player/world/zombie WAV. Sources:
the original game sounds and rubberduck's CC0 wood/metal foley (see
docs/AUDIO_DESIGNED_SOURCES.md). Requires ffmpeg for the source OGG recordings;
all editing, filtering, resampling and mixing use Python's standard library.

Usage: python3 tools/make_designed_sfx.py [output_assets] [--only world/chest]
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import shutil
import subprocess
import sys
import urllib.request
import wave
import zipfile
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RATE = 22050
PROTECTED = (
    'player/shot', 'player/reload', 'world/explosion', 'world/wood',
    'world/glass', 'world/snap', 'world/fuse', 'world/supply',
    'zombie/spawn', 'zombie/idle', 'zombie/death',
)
FOLEY_MEMBERS = (
    'lock_open_01', 'keys_01', 'metal_close_01', 'metal_falling_01',
    'metal_hit_01', 'metal_hit_02', 'metal_spring_01', 'metal_slam_01',
    'wood_breaking_01', 'wood_falling_01', 'wood_close_01', 'wood_squeak_01',
)
SOURCE_DOWNLOADS = {
    'foley': ('https://opengameart.org/sites/default/files/100-CC0-wood-metal-SFX.zip',
              'be6eba63b03409ac0c77787a956b1503a7c186403d04aef9725c52644a4b7878'),
    'blast': ('https://cdn.freesound.org/previews/251/251401_1661766-hq.mp3',
              '03ede4462a6657fdd181fa65f9aab9d6fcc181be6cdbb2fb461ee2aa638da318'),
}


def rms(samples: list[float]) -> float:
    return math.sqrt(sum(s * s for s in samples) / max(1, len(samples)))


def fade(samples: list[float], attack: float = 0.002, release: float = 0.02) -> list[float]:
    n = len(samples)
    a, r = max(1, int(attack * RATE)), max(1, int(release * RATE))
    return [s * min(1.0, i / a, (n - 1 - i) / r) for i, s in enumerate(samples)]


def trim(samples: list[float]) -> list[float]:
    """Find the recorded gesture; retain a little space around its attack/tail."""
    win = int(RATE * 0.004)
    energy = [rms(samples[i:i + win]) for i in range(0, len(samples), win)]
    threshold = max(energy, default=0.0) * 0.035
    active = [i for i, value in enumerate(energy) if value > threshold]
    if not active:
        raise ValueError('Silent source recording')
    start = max(0, active[0] * win - int(RATE * 0.003))
    end = min(len(samples), (active[-1] + 1) * win + int(RATE * 0.025))
    samples = samples[start:end]
    mean = sum(samples) / len(samples)
    return fade([s - mean for s in samples], 0.001, 0.012)


def speed(samples: list[float], ratio: float) -> list[float]:
    """Tape resampling: changes both pitch and duration of recorded material."""
    out = []
    for i in range(max(0, int((len(samples) - 1) / ratio))):
        pos = i * ratio
        k = int(pos)
        f = pos - k
        out.append(samples[k] * (1.0 - f) + samples[k + 1] * f)
    return out


def lowpass(samples: list[float], hz: float) -> list[float]:
    a = 1.0 - math.exp(-2.0 * math.pi * hz / RATE)
    out = []
    previous = 0.0
    for value in samples:
        previous += a * (value - previous)
        out.append(previous)
    return out


def highpass(samples: list[float], hz: float) -> list[float]:
    return [s - low for s, low in zip(samples, lowpass(samples, hz))]


def band(samples: list[float], lo: float, hi: float) -> list[float]:
    return lowpass(highpass(samples, lo), hi)


def extract(samples: list[float], start: float, length: float) -> list[float]:
    at = int(start * RATE)
    return fade(samples[at:at + int(length * RATE)], 0.001, min(0.014, length * 0.16))


def peak_unit(samples: list[float]) -> list[float]:
    gain = 1.0 / max(0.00001, max((abs(s) for s in samples), default=0.0))
    return [s * gain for s in samples]


def resonance(excitation: list[float], length: float,
              modes: tuple[tuple[float, float, float], ...]) -> list[float]:
    """Damped physical modes excited by a real impact, never a tone oscillator.

    Modes are inharmonic and quickly damped, as in a shell or metal housing.
    Keeping their amplitudes small underneath foley avoids a musical bleep.
    """
    out = [0.0] * int(RATE * length)
    for hz, decay, weight in modes:
        radius = math.exp(-1.0 / (RATE * decay))
        a = 2.0 * radius * math.cos(2.0 * math.pi * hz / RATE)
        b = radius * radius
        previous = before = 0.0
        mode = []
        for i in range(len(out)):
            value = (excitation[i] if i < len(excitation) else 0.0) + a * previous - b * before
            before, previous = previous, value
            mode.append(value)
        mode = peak_unit(mode)
        for i, value in enumerate(mode):
            out[i] += value * weight
    return fade(out, 0.001, 0.025)


class Mix:
    def __init__(self, seconds: float) -> None:
        self.samples = [0.0] * int(seconds * RATE)

    def add(self, samples: list[float], at: float = 0.0, gain: float = 1.0) -> None:
        start = int(at * RATE)
        for i, value in enumerate(samples[:max(0, len(self.samples) - start)]):
            self.samples[start + i] += value * gain

    def finish(self, target: float, peak: float = 0.90) -> list[float]:
        # Original shot RMS is about .30 and reload about .118. Relative
        # levels below follow those anchors, rather than normalizing every
        # incidental click to the loudness of a gunshot.
        mean = sum(self.samples) / len(self.samples)
        samples = fade([s - mean for s in self.samples], 0.0015, 0.035)
        gain = min(target / max(0.00001, rms(samples)),
                   peak / max(0.00001, max(abs(s) for s in samples)))
        return [s * gain for s in samples]


class Sources:
    def __init__(self, assets: Path, foley_zip: Path, blast_recording: Path, ffmpeg: str) -> None:
        self.assets = assets
        self.foley_zip = foley_zip
        self.blast_recording = blast_recording
        self.ffmpeg = ffmpeg

    @lru_cache(maxsize=None)
    def game(self, name: str) -> list[float]:
        path = self.assets / 'sounds' / f'{name}.wav'
        with wave.open(str(path), 'rb') as src:
            if src.getnchannels() != 1 or src.getframerate() != RATE:
                raise ValueError(f'{path}: expected mono {RATE} Hz source')
            raw = src.readframes(src.getnframes())
            width = src.getsampwidth()
        if width == 1:
            return [(s - 128) / 128.0 for s in raw]
        if width == 2:
            pcm = array.array('h')
            pcm.frombytes(raw)
            if sys.byteorder == 'big':
                pcm.byteswap()
            return [s / 32768.0 for s in pcm]
        raise ValueError(f'{path}: unsupported source PCM width {width}')

    @lru_cache(maxsize=None)
    def foley(self, name: str) -> list[float]:
        with zipfile.ZipFile(self.foley_zip) as pack:
            encoded = pack.read(f'{name}.ogg')
        return peak_unit(trim(self.decode(encoded)))

    def decode(self, encoded: bytes) -> list[float]:
        process = subprocess.run(
            [self.ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', 'pipe:0',
             '-ac', '1', '-ar', str(RATE), '-f', 'f32le', 'pipe:1'],
            input=encoded, capture_output=True, check=True,
        )
        pcm = array.array('f')
        pcm.frombytes(process.stdout)
        if sys.byteorder == 'big':
            pcm.byteswap()
        return list(pcm)

    @lru_cache(maxsize=None)
    def field_blast(self) -> list[float]:
        # Felix Blume's real dynamite recording starts with the explosion.
        # Retain its sharp pressure front and first rocky reflections, not
        # the thirty seconds of mountain ambience following the event.
        decoded = self.decode(self.blast_recording.read_bytes())
        return peak_unit(fade(decoded[int(0.025 * RATE):int(1.90 * RATE)], 0.001, 0.045))


def grenade(s: Sources) -> list[float]:
    out = Mix(0.95)
    body = speed(s.field_blast(), 1.52)
    out.add(extract(band(body, 95.0, 6000.0), 0.0, 0.91), gain=0.95)
    out.add(extract(s.game('player/shot'), 0.0, 0.075), gain=0.18)
    # A compact blast followed by shell fragments; the original barrel has
    # neither this dry front nor this particular metal debris pattern.
    fragment = highpass(s.foley('metal_falling_01'), 700.0)
    out.add(extract(fragment, 0.44, 0.38), 0.09, 0.10)
    out.add(speed(extract(fragment, 0.16, 0.22), 1.29), 0.32, 0.055)
    out.add(extract(s.game('world/glass'), 0.04, 0.24), 0.13, 0.06)
    out.add(extract(speed(s.game('world/explosion'), 1.37), 0.0, 0.60), gain=0.14)
    return out.finish(0.255)


def dynamite(s: Sources) -> list[float]:
    out = Mix(1.65)
    original = s.game('world/explosion')
    out.add(extract(lowpass(speed(s.field_blast(), 0.94), 5900.0), 0.0, 1.60), gain=0.96)
    out.add(lowpass(speed(original, 0.78), 1800.0), gain=0.17)
    out.add(extract(s.game('player/shot'), 0.0, 0.085), gain=0.17)
    rubble = s.foley('wood_breaking_01')
    out.add(extract(speed(rubble, 0.84), 0.0, 0.88), 0.18, 0.09)
    out.add(extract(speed(s.foley('wood_falling_01'), 0.80), 0.0, 0.63), 0.62, 0.065)
    out.add(extract(s.game('world/wood'), 0.11, 0.28), 0.43, 0.06)
    out.add(extract(speed(rubble, 1.08), 0.10, 0.22), 1.17, 0.035)
    return out.finish(0.285)


def ambush(s: Sources) -> list[float]:
    out = Mix(0.80)
    # A quick scrape rising into a struck, loose metal object: tension and
    # a sudden warning, rather than a musical interval or creature voice.
    spring = speed(s.foley('metal_spring_01'), 0.62)
    scrape = extract(band(spring, 90.0, 3000.0), 0.0, 0.43)
    out.add([value * (i / max(1, len(scrape))) for i, value in enumerate(scrape)], gain=0.52)
    slam = speed(s.foley('metal_slam_01'), 0.59)
    out.add(extract(slam, 0.0, 0.49), 0.24, 0.56)
    out.add(extract(speed(s.game('world/wood'), 0.82), 0.0, 0.19), 0.25, 0.29)
    return out.finish(0.175)


def chest(s: Sources) -> list[float]:
    out = Mix(0.89)
    out.add(latch(s, 1.35), gain=0.30)
    out.add(extract(speed(s.foley('wood_squeak_01'), 1.12), 0.0, 0.43), 0.10, 0.27)
    out.add(extract(s.foley('wood_close_01'), 0.0, 0.27), 0.49, 0.36)
    out.add(extract(highpass(s.foley('keys_01'), 700.0), 0.0, 0.30), 0.54, 0.16)
    return out.finish(0.125)


def level_up(s: Sources) -> list[float]:
    out = Mix(0.90)
    # A badge/ratchet fastening, then coins settling. Recorded mechanics,
    # with loose metal ringing naturally in its own inharmonic modes.
    ratchet = latch(s, 1.12)
    out.add(extract(ratchet, 0.0, 0.25), gain=0.31)
    out.add(extract(speed(s.foley('metal_hit_01'), 1.38), 0.0, 0.28), 0.20, 0.37)
    out.add(extract(speed(s.foley('keys_01'), 0.94), 0.0, 0.50), 0.32, 0.26)
    out.add(extract(s.foley('wood_close_01'), 0.0, 0.16), 0.18, 0.12)
    return out.finish(0.145)


def victory(s: Sources) -> list[float]:
    out = Mix(1.35)
    out.add(extract(s.foley('wood_close_01'), 0.0, 0.24), gain=0.26)
    out.add(extract(speed(s.foley('metal_hit_02'), 0.83), 0.0, 0.65), 0.06, 0.34)
    out.add(latch(s, 1.22), 0.23, 0.21)
    coins = highpass(s.foley('keys_01'), 650.0)
    out.add(extract(coins, 0.0, 0.67), 0.40, 0.31)
    out.add(extract(speed(coins, 0.87), 0.12, 0.39), 0.82, 0.13)
    return out.finish(0.16)


def plasma_shot(s: Sources) -> list[float]:
    out = Mix(0.46)
    shot = s.game('player/shot')
    # The cannon still has mass. Above the familiar transient, a bright
    # distorted arc uses the original fuse/shot texture instead of a beep.
    out.add(extract(lowpass(speed(shot, 1.10), 1500.0), 0.0, 0.34), gain=0.69)
    arc = band(speed(shot, 2.30), 520.0, 5400.0)
    out.add(arc, gain=0.51)
    out.add(arc, 0.013, -0.17)
    hiss = extract(band(s.game('world/fuse'), 800.0, 5300.0), 0.078, 0.22)
    out.add([x * math.exp(-i / (RATE * 0.075)) for i, x in enumerate(hiss)], 0.012, 0.44)
    casing = extract(highpass(s.foley('metal_hit_01'), 500.0), 0.0, 0.025)
    out.add(resonance(casing, 0.27, ((410.0, 0.024, 0.10), (971.0, 0.040, 0.07),
                                          (2240.0, 0.017, 0.05))), 0.006, 0.32)
    return out.finish(0.265)


def plasma_reload(s: Sources) -> list[float]:
    out = Mix(0.62)
    out.add(extract(latch(s, 1.7), 0.0, 0.10), 0.025, 0.30)
    # Hot vent closes and the cell latches. No ascending note sequence.
    vent = extract(band(s.game('world/fuse'), 300.0, 4500.0), 0.12, 0.30)
    out.add([x * math.sin(math.pi * i / max(1, len(vent))) for i, x in enumerate(vent)], 0.11, 0.92)
    out.add(extract(speed(s.foley('metal_spring_01'), 1.8), 0.0, 0.17), 0.24, 0.19)
    out.add(extract(speed(s.foley('metal_close_01'), 1.65), 0.0, 0.15), 0.43, 0.40)
    out.add(extract(s.game('player/reload'), 0.335, 0.05), 0.53, 0.16)
    return out.finish(0.105)


def plasma_empty(s: Sources) -> list[float]:
    out = Mix(0.24)
    out.add(extract(latch(s, 1.9), 0.0, 0.065), gain=0.30)
    out.add(extract(speed(s.foley('metal_spring_01'), 1.3), 0.0, 0.12), 0.024, 0.16)
    static = extract(band(s.game('world/fuse'), 1100.0, 3600.0), 0.22, 0.085)
    out.add([x * (1.0 - i / len(static)) for i, x in enumerate(static)], 0.04, 0.65)
    return out.finish(0.070)


def ricochet(s: Sources) -> list[float]:
    out = Mix(0.31)
    hit = s.foley('metal_hit_02')
    out.add(extract(speed(hit, 1.8), 0.0, 0.075), gain=0.40)
    spring = extract(highpass(speed(s.foley('metal_spring_01'), 2.1), 900.0), 0.0, 0.24)
    out.add(spring, 0.023, 0.27)
    out.add(extract(s.game('world/glass'), 0.06, 0.18), 0.028, 0.12)
    return out.finish(0.105)


def latch(s: Sources, ratio: float) -> list[float]:
    # The recorded lock opens at 0.447 s after the keys move. Cutting the
    # first 50 ms would retain the handling noise and lose the actual latch.
    return speed(extract(s.foley('lock_open_01'), 0.38, 0.19), ratio)


def ui_move(s: Sources) -> list[float]:
    out = Mix(0.075)
    out.add(extract(latch(s, 2.1), 0.0, 0.05), gain=0.35)
    out.add(extract(s.game('player/reload'), 0.337, 0.017), 0.008, 0.12)
    return out.finish(0.040, 0.36)


def ui_confirm(s: Sources) -> list[float]:
    out = Mix(0.18)
    out.add(extract(latch(s, 1.65), 0.0, 0.066), gain=0.28)
    out.add(extract(speed(s.foley('metal_close_01'), 2.7), 0.0, 0.095), 0.045, 0.34)
    return out.finish(0.065, 0.42)


def ui_back(s: Sources) -> list[float]:
    out = Mix(0.17)
    out.add(extract(speed(s.foley('metal_close_01'), 2.2), 0.0, 0.061), gain=0.30)
    out.add(extract(latch(s, 1.65), 0.0, 0.064), 0.055, 0.24)
    return out.finish(0.060, 0.40)


SOUNDS = {
    'world/grenade_explosion': grenade,
    'world/dynamite_explosion': dynamite,
    'world/ambush': ambush,
    'world/chest': chest,
    'world/level_up': level_up,
    'world/victory': victory,
    'weapons/plasma_shot': plasma_shot,
    'weapons/plasma_reload': plasma_reload,
    'weapons/plasma_empty': plasma_empty,
    'weapons/ricochet': ricochet,
    'ui/move': ui_move,
    'ui/confirm': ui_confirm,
    'ui/back': ui_back,
}
OUTPUTS = tuple(SOUNDS)


# A review reference is deliberately a recorded source (or, for fictional
# plasma, the original game cannon), not the previous synthetic placeholder.
REFERENCES = {
    'world/grenade_explosion': ('field', ''),
    'world/dynamite_explosion': ('field', ''),
    'world/ambush': ('foley', 'metal_spring_01'),
    'world/chest': ('foley', 'wood_squeak_01'),
    'world/level_up': ('foley', 'metal_hit_01'),
    'world/victory': ('foley', 'keys_01'),
    'weapons/plasma_shot': ('game', 'player/shot'),
    'weapons/plasma_reload': ('foley', 'metal_close_01'),
    'weapons/plasma_empty': ('foley', 'lock_open_01'),
    'weapons/ricochet': ('foley', 'metal_hit_02'),
    'ui/move': ('foley', 'lock_open_01'),
    'ui/confirm': ('foley', 'metal_close_01'),
    'ui/back': ('foley', 'lock_open_01'),
}


def review_sample(sources: Sources, name: str, samples: list[float], directory: Path) -> tuple[str, float]:
    kind, reference_name = REFERENCES[name]
    reference = (sources.field_blast() if kind == 'field' else
                 sources.foley(reference_name) if kind == 'foley' else sources.game(reference_name))
    reference = fade(reference[:int(RATE * 1.9)], 0.002, 0.035)
    reference = [x * 0.72 for x in peak_unit(reference)]
    silence = [0.0] * int(RATE * 0.45)
    rendered = silence + reference + silence + samples + silence
    filename = name.replace('/', '_') + '_AB.wav'
    write_wav(directory / filename, rendered)
    return filename, (len(silence) * 2 + len(reference)) / RATE


def manifest(sources: Sources, output_assets: Path, path: Path) -> None:
    def relative(p: Path) -> str:
        try:
            return p.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return p.as_posix()

    def source_file(p: Path) -> dict[str, str | int]:
        raw = p.read_bytes()
        return {'path': relative(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

    files = [source_file(sources.assets / 'sounds' / f'{name}.wav') for name in PROTECTED]
    with zipfile.ZipFile(sources.foley_zip) as pack:
        members = {name + '.ogg': hashlib.sha256(pack.read(name + '.ogg')).hexdigest()
                   for name in FOLEY_MEMBERS}
    outputs = {}
    for name in OUTPUTS:
        p = output_assets / 'sounds' / f'{name}.wav'
        if not p.exists():
            continue
        raw = p.read_bytes()
        with wave.open(str(p), 'rb') as src:
            pcm = array.array('h')
            pcm.frombytes(src.readframes(src.getnframes()))
            if sys.byteorder == 'big':
                pcm.byteswap()
            values = [value / 32768.0 for value in pcm]
            outputs[name] = {
                'path': relative(p), 'sha256': hashlib.sha256(raw).hexdigest(),
                'seconds': round(src.getnframes() / src.getframerate(), 6),
                'sample_rate': src.getframerate(), 'bits': src.getsampwidth() * 8,
                'channels': src.getnchannels(), 'rms': round(rms(values), 6),
                'peak': round(max(abs(value) for value in values), 6),
                'dc': round(sum(values) / len(values), 8),
            }
    result = {
        'generator': 'tools/make_designed_sfx.py',
        'subjective_listening_verified': False,
        'sources': {
            'internal_protected': files,
            'foley': {**source_file(sources.foley_zip), 'author': 'rubberduck', 'license': 'CC0-1.0',
                      'page': 'https://opengameart.org/content/100-cc0-metal-and-wood-sfx',
                      'members_sha256': members},
            'field_blast': {**source_file(sources.blast_recording), 'author': 'Felix Blume',
                            'license': 'CC0-1.0', 'page': 'https://freesound.org/people/felix.blume/sounds/251401/',
                            'selected_interval_seconds': [0.025, 1.90]},
        },
        'outputs': outputs,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_wav(path: Path, samples: list[float]) -> None:
    pcm = array.array('h', (max(-32767, min(32767, round(s * 32767.0))) for s in samples))
    if sys.byteorder == 'big':
        pcm.byteswap()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())


def prepare_source(path: Path, kind: str, fetch: bool) -> None:
    url, expected = SOURCE_DOWNLOADS[kind]
    if path.is_file():
        raw = path.read_bytes()
    elif fetch:
        request = urllib.request.Request(url, headers={'User-Agent': 'Vaquera2D-audio-authoring/1.0'})
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f'{url}: unexpected source hash; download was not saved')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        print(f'Fetched verified CC0 source: {path.name}')
    else:
        raise FileNotFoundError(f'{path}: source missing; use --fetch or see docs/AUDIO_DESIGNED_SOURCES.md')
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'{path}: source hash changed; preserving it for review')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output_assets', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--source-assets', type=Path, default=ROOT / 'assets')
    parser.add_argument('--foley-zip', type=Path, default=ROOT / 'recordings/cc0_foley/100-CC0-wood-metal-SFX.zip')
    parser.add_argument('--blast-recording', type=Path, default=ROOT / 'recordings/cc0_foley/dynamite_source.mp3')
    parser.add_argument('--review', action='store_true', help='write source/result A-B WAVs under build/designed_review')
    parser.add_argument('--manifest', type=Path, help='optional JSON source and output manifest')
    parser.add_argument('--only', nargs='+', choices=sorted(SOUNDS))
    parser.add_argument('--fetch', action='store_true', help='download missing CC0 sources and verify known SHA-256 hashes')
    args = parser.parse_args()
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None and sys.platform == 'win32':
        ffmpeg = shutil.which('ffmpeg', path='C:/msys64/ucrt64/bin')
    if ffmpeg is None:
        parser.error('ffmpeg is required (apt install ffmpeg / pacman -S mingw-w64-ucrt-x86_64-ffmpeg)')
    try:
        prepare_source(args.foley_zip, 'foley', args.fetch)
        prepare_source(args.blast_recording, 'blast', args.fetch)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    protected = [args.source_assets / 'sounds' / f'{name}.wav' for name in PROTECTED]
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    sources = Sources(args.source_assets, args.foley_zip, args.blast_recording, ffmpeg)
    review_index = ['# Comparación A/B', '',
                    'Cada WAV contiene 0.45 s de silencio, la fuente de referencia A, '
                    '0.45 s de silencio y la mezcla final B. A se ajusta a un pico de 0.72; '
                    'B mantiene el volumen del juego. Esta comparación permite audición '
                    'humana: el análisis automático no confirma realismo perceptivo.', '',
                    '| Efecto | Archivo A/B | Inicio B |', '| --- | --- | --- |']
    for name in args.only or SOUNDS:
        samples = SOUNDS[name](sources)
        output = args.output_assets / 'sounds' / f'{name}.wav'
        write_wav(output, samples)
        print(f'{name}: {len(samples) / RATE:.3f}s, RMS={rms(samples):.3f}, '
              f'peak={max(abs(s) for s in samples):.3f}, PCM16')
        if args.review:
            directory = ROOT / 'build/designed_review'
            filename, result_at = review_sample(sources, name, samples, directory)
            review_index.append(f'| `{name}` | [{filename}]({filename}) | {result_at:.3f} s |')
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    if before != after:
        raise RuntimeError('A protected source sound changed during generation')
    print('Protected original player/world/zombie sources unchanged (SHA-256).')
    if args.review:
        (ROOT / 'build/designed_review/README.md').write_text('\n'.join(review_index) + '\n', encoding='utf-8')
    if args.manifest:
        manifest(sources, args.output_assets, args.manifest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
