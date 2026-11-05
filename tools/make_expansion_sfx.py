#!/usr/bin/env python3
"""Edit recorded CC0 foley for the newer game actions; never rewrite old WAVs.

python3 tools/make_expansion_sfx.py --fetch
python3 tools/make_expansion_sfx.py [assets_dir] --only ui/book_page
python3 tools/make_expansion_sfx.py --review build/expansion_review

Only --fetch accesses the network. Python's standard library and FFmpeg are
needed for authoring, with no new runtime dependency. See
docs/AUDIO_EXPANSION_SOURCES.md for source credits and the limits of review.
"""
from __future__ import annotations

import argparse
import array
from dataclasses import asdict
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile

import make_foley_sfx as foley
from make_nature_sfx import balance, fade, layer, loop

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'recordings' / 'cc0_expansion'
RATE = foley.RATE
SOURCES = {
    'book': {
        'filename': 'book.mp3', 'title': 'Book Page Turn', 'author': 'Kodack',
        'page': 'https://freesound.org/people/Kodack/sounds/256475/',
        'url': 'https://cdn.freesound.org/previews/256/256475_2276808-hq.mp3',
        'sha256': '99c0ffb127dfc64214c6ecd5d30f2a5deb3f2419328e5a54f7c070f2e341cd71',
        'license': 'CC0-1.0',
    },
    'sparks': {
        'filename': 'sparks.mp3', 'title': 'Electric Sparks.wav', 'author': 'kev_durr',
        'page': 'https://freesound.org/people/kev_durr/sounds/396470/',
        'url': 'https://cdn.freesound.org/previews/396/396470_5415774-hq.mp3',
        'sha256': '11d14640af7799238736ed289138cd88fc632464b6a99aebd07c65581793225c',
        'license': 'CC0-1.0',
    },
    'fireplace': {
        'filename': 'fireplace.wav', 'title': 'Fireplace Sound loop', 'author': 'PagDev',
        'page': 'https://opengameart.org/content/fireplace-sound-loop',
        'url': 'https://opengameart.org/sites/default/files/fire.wav',
        'sha256': '85ca0cc60d0c037fff8b185e31ad1fcdbda6ce45eee17c3ee1318d1b8f59e330',
        'license': 'CC0-1.0',
    },
}

for number, member_hash in (
    ('01', '71dd6dac86d9cd74480f78b521021a22d5ec4d3f7151caa7536ed2da6acf21ee'),
    ('02', '72d1705f4e12b1dfb7d19cc9091bb8c7f11c5aaf80154342c3a31c817cdc2a1b'),
    ('03', 'bc7f1ac5f52fa87f33eff62e4ecb9b7e0fe42164b5830f24a4ce6471ae4d2a01'),
):
    SOURCES['bat_' + number] = {
        'filename': 'bat.zip', 'title': 'Bat Screeches',
        'author': 'polymorpheva; isolated and denoised by AntumDeluge',
        'page': 'https://opengameart.org/content/bat-screeches',
        'original_page': 'https://freesound.org/people/polymorpheva/sounds/104205/',
        'url': 'https://opengameart.org/sites/default/files/bat.zip',
        'sha256': '8a41cfeca5a3b184f4cf171d45faf0041715b6f9d402dcfe04c53369c05e0ab3',
        'member': f'flac/bat_{number}.flac', 'member_sha256': member_hash,
        'license': 'CC0-1.0',
    }

# (duration, target RMS, peak ceiling, archive layers, file cuts).
# Archive times use the existing foley helper's silence-trimmed recordings;
# file cuts are absolute seconds. All sources retain their natural speed.
# A cut is (source key, start, end, placement, gain).
RECIPES = {
    'player/flashlight_on': (.15, .043, .30,
        [foley.field('switch_01')], []),
    'player/flashlight_off': (.15, .040, .28,
        [foley.field('switch_02')], []),
    'weapons/fire_mode': (.17, .045, .32,
        [foley.field('switch_02', gain=.85),
         foley.wood('metal_close_01', at=.015, gain=.12, length=.10)], []),
    'world/grenade_bounce': (.24, .050, .36,
        [foley.field('stones_02', gain=.65, length=.16),
         foley.wood('metal_hit_03', at=.006, gain=.18, length=.12)], []),
    'world/splash': (.48, .080, .48,
        [foley.field('footstep_wet_02', gain=.7),
         foley.field('footstep_wet_03', at=.08, gain=.45),
         foley.leather(1, gain=.10, length=.12)], []),
    # Complete, different fruit-bat calls, without bird wings, invented
    # voices, pitch shifts or ultrasound detector translations.
    'bat/flee': (1.47, .045, .40, [], [('bat_01', .0, 1.428662, .0, 1.0)]),
    'bat/death': (1.40, .055, .44, [], [('bat_03', .0, 1.361270, .0, 1.0)]),
    'bat/chirp': (1.79, .050, .42, [], [('bat_02', .0, 1.747302, .0, 1.0)]),
    'ui/book_open': (.69, .042, .32,
        [foley.leather(2, at=.015, gain=.10, length=.16)],
        [('book', .18, .77, .025, 1.0)]),
    'ui/book_close': (.64, .043, .34,
        [foley.wood('wood_hit_06', at=.40, gain=.08, length=.11)],
        [('book', 8.02, 8.56, .0, 1.0)]),
    'ui/book_page': (.59, .040, .30, [], [('book', 6.02, 6.55, .0, 1.0)]),
    'weather/lightning_warn': (1.0, .085, .48, [],
        [('sparks', 3.25, 4.25, .0, 1.0)]),
    'world/river': (12.0, .080, .36,
        [foley.field('loop_water_03', length=9.4),
         foley.field('loop_water_01', start=.4, at=8.4, length=5.1)], []),
    'world/fire': (12.0, .072, .34, [], [('fireplace', 5.0, 18.0, .0, 1.0)]),
}
OUTPUTS = tuple(RECIPES)
LOOPS = {'world/river', 'world/fire'}
COMPRESSED = {'ui/book_open', 'ui/book_close', 'ui/book_page',
              'world/splash', 'world/river', 'world/fire'}


def dependencies(names: list[str]) -> set[str]:
    return {cut[0] for name in names for cut in RECIPES[name][4]}


def prepare_sources(names: list[str], fetch: bool = False) -> None:
    if any(RECIPES[name][3] for name in names):
        foley.prepare_sources(fetch)
    for key in sorted(dependencies(names)):
        spec = SOURCES[key]
        path = CACHE / spec['filename']
        if not path.exists():
            if not fetch:
                raise RuntimeError(f'Falta {path}; ejecuta con --fetch para descargar la fuente CC0.')
            request = urllib.request.Request(spec['url'], headers={'User-Agent': 'Vaquera2D audio authoring'})
            with urllib.request.urlopen(request, timeout=45) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != spec['sha256']:
                raise RuntimeError(f'SHA256 de la descarga no coincide: {key}')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec['sha256']:
            raise RuntimeError(f'SHA256 de la fuente no coincide: {path}')


def decode(data: bytes, encoded: bool = True, lowpass: int = 6200,
           compressor: float | None = None) -> list[float]:
    command = [foley.ffmpeg(), '-nostdin', '-v', 'error']
    if not encoded:
        command += ['-f', 'f32le', '-ar', str(RATE), '-ac', '1']
    filters = f'highpass=f=75,lowpass=f={lowpass}'
    if compressor is not None:
        filters += (f',acompressor=threshold={compressor}:ratio=2:attack=1:'
                    'release=50:knee=2.8:detection=peak')
    command += ['-i', 'pipe:0', '-ac', '1', '-af', filters,
                '-ar', str(RATE), '-f', 'f32le', 'pipe:1']
    result = subprocess.run(command, input=data, capture_output=True, check=True)
    pcm = array.array('f', result.stdout)
    if sys.byteorder == 'big':
        pcm.byteswap()
    if not pcm:
        raise RuntimeError('Fuente de audio vacía')
    return list(pcm)


@lru_cache(maxsize=None)
def file_recording(key: str) -> tuple[float, ...]:
    spec = SOURCES[key]
    data = (CACHE / spec['filename']).read_bytes()
    if 'member' in spec:
        with zipfile.ZipFile(CACHE / spec['filename']) as archive:
            data = archive.read(spec['member'])
        if hashlib.sha256(data).hexdigest() != spec['member_sha256']:
            raise RuntimeError(f'SHA256 del miembro no coincide: {key}')
    return tuple(decode(data, lowpass=9800 if key.startswith('bat_') else 6200))


def filter_mix(samples: list[float], name: str, target: float, ceiling: float) -> list[float]:
    if name in COMPRESSED:
        # Give quiet paper/water/fire detail a little more room beneath its
        # loudest transient. Calls and switches retain their source dynamics.
        samples = balance(samples, target, ceiling)
    pcm = array.array('f', samples)
    if sys.byteorder == 'big':
        pcm.byteswap()
    return decode(pcm.tobytes(), encoded=False,
                  lowpass=9800 if name.startswith('bat/') else 6200,
                  compressor=ceiling * .25 if name in COMPRESSED else None)


def render(name: str) -> list[float]:
    duration, target, ceiling, layers, cuts = RECIPES[name]
    # Loops reserve an extra second for the wrap crossfade. Never fade a
    # loop to silence at its ends: the mixer repeats it continuously.
    out = [0.0] * round((duration + (1.0 if name in LOOPS else 0.0)) * RATE)
    for item in layers:
        samples = foley.layer_samples(item)
        if name == 'world/river':
            # Two different recorded water takes, joined with a full-second
            # crossfade rather than duplicating a short passage four times.
            samples = fade(samples, 1.0 if item.at else .005,
                           1.0 if not item.at else .005)
        layer(out, samples, item.at, 1.0)
    for key, start, end, at, gain in cuts:
        samples = list(file_recording(key)[round(start * RATE):round(end * RATE)])
        if len(samples) < round((end - start) * RATE) - 2:
            raise RuntimeError(f'Fuente demasiado corta: {key} {start}–{end}')
        layer(out, samples if name in LOOPS else fade(samples), at, gain)
    if name not in LOOPS:
        out = filter_mix(out, name, target, ceiling)
        out = fade(out, .004, .035)
    else:
        out = filter_mix(out, name, target, ceiling)
        out = loop(out, duration, 1.0)
    return balance(out, target, ceiling)


def metrics(path: Path, samples: list[float]) -> dict:
    return {
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'seconds': round(len(samples) / RATE, 6),
        'rms': round(math.sqrt(sum(x*x for x in samples) / len(samples)), 6),
        'peak': round(max(map(abs, samples)), 6),
    }


def archive_manifest(names: list[str]) -> dict:
    members: dict[str, set[str]] = {}
    for name in names:
        for item in RECIPES[name][3]:
            members.setdefault(item.pack, set()).add(item.name + '.ogg')
    result = {}
    for pack, selected in sorted(members.items()):
        filename, url, digest = foley.PACKS[pack]
        with zipfile.ZipFile(foley.CACHE / filename) as archive:
            result[pack] = {
                'filename': filename, 'url': url, 'sha256': digest,
                'license': 'CC0-1.0', 'credits': 'docs/AUDIO_FOLEY_SOURCES.md',
                'members': {member: hashlib.sha256(archive.read(member)).hexdigest()
                            for member in sorted(selected)},
            }
    return result


def generate(assets_dir: Path, names: list[str], manifest: Path | None,
             review: Path | None) -> None:
    records = {}
    if review:
        review.mkdir(parents=True, exist_ok=True)
    for name in names:
        samples = render(name)
        path = assets_dir / 'sounds' / (name + '.wav')
        foley.write_wav(path, samples)
        records[name] = metrics(path, samples)
        records[name]['archive_layers'] = [asdict(item) for item in RECIPES[name][3]]
        records[name]['file_cuts'] = RECIPES[name][4]
        print(f'expansion: {name} ({records[name]["seconds"]:.3f}s, '
              f'RMS {records[name]["rms"]:.3f}, peak {records[name]["peak"]:.3f})')
        if review:
            # Compare an unassembled source gesture with the resulting mix,
            # separated by 350ms. This prepares a listening aid, not a claim
            # that an automated technical check has listened to the clip.
            sources, cuts = RECIPES[name][3:]
            if cuts:
                key, start, end, _, _ = cuts[0]
                raw = list(file_recording(key)[round(start*RATE):round(end*RATE)])
            else:
                raw = foley.layer_samples(sources[0])
            preview = fade(balance(raw, .08, .5)) + [0.0] * round(.35*RATE) + fade(samples)
            foley.write_wav(review / (name.replace('/', '_') + '_AB.wav'), preview)
    if review:
        (review / 'index.json').write_text(json.dumps({
            'order': 'source gesture, 350ms silence, game mix',
            'listening_verified': False, 'outputs': records,
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if manifest:
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({
            'format': {'channels': 1, 'rate': RATE, 'bits': 16},
            'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'file_sources': {key: SOURCES[key] for key in sorted(dependencies(names))},
            'archives': archive_manifest(names),
            'processing': 'Natural speed; mono; HP75/LP6200 (bat LP9800); selective 2:1 compression of paper/water/fire; RMS target with peak ceiling; fades or 1s loop crossfade.',
            'subjective_listening_verified': False,
            'outputs': records,
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--only', nargs='+', choices=sorted(OUTPUTS))
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--manifest', type=Path, help='write provenance/output hashes for the selected outputs')
    parser.add_argument('--review', type=Path, help='write source/result A/B comparisons outside assets/')
    args = parser.parse_args()
    names = args.only or list(OUTPUTS)
    prepare_sources(names, args.fetch)
    generate(args.assets_dir, names, args.manifest, args.review)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f'make_expansion_sfx: {error}', file=sys.stderr)
        raise SystemExit(1)
