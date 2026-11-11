#!/usr/bin/env python3
"""Edit recorded CC0 sound for THE MIRACLE's story; never touch older WAVs.

python3 tools/make_cinematic_sfx.py [assets_dir] [--only cinematic/heartbeat]
python3 tools/make_cinematic_sfx.py --fetch --manifest docs/AUDIO_CINEMATIC_MANIFEST.json

Only --fetch accesses the network. Sources keep their original speed/pitch;
no oscillator, generated noise, synthesized heartbeat or spoken track is used.
FFmpeg is an authoring dependency only. See docs/AUDIO_CINEMATIC_SOURCES.md.
"""
from __future__ import annotations

import argparse
import array
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
CACHE = ROOT / 'recordings' / 'cc0_cinematic'
RATE = foley.RATE
SOURCES = {
    'breath': {
        'filename': 'breath.mp3', 'title': 'Breath_Woman.wav', 'author': 'audione',
        'page': 'https://freesound.org/people/audione/sounds/108160/',
        'url': 'https://cdn.freesound.org/previews/108/108160_631427-hq.mp3',
        'sha256': '4f097a9146f131fbae3d22da41a1801576d9d70bd6e6288476c1966f48440350',
        'license': 'CC0-1.0', 'recording': 'A woman breathing; no spoken narration.',
    },
    'heartbeat': {
        'filename': 'heartbeat.mp3',
        'title': 'Real Heartbeat (DIY Stethoscope recording)', 'author': 'modusmogulus',
        'page': 'https://freesound.org/people/modusmogulus/sounds/831630/',
        'url': 'https://cdn.freesound.org/previews/831/831630_15956618-hq.mp3',
        'sha256': '359e09aa506c6add034980a8c09fb4a73612334545d921f68c3e9db98997f479',
        'license': 'CC0-1.0', 'recording': 'The author\'s actual heartbeat, DIY stethoscope.',
    },
    'radio': {
        'filename': 'radio.mp3', 'title': 'Walkie Talkie radio static', 'author': 'SEF7',
        'page': 'https://freesound.org/people/SEF7/sounds/701330/',
        'url': 'https://cdn.freesound.org/previews/701/701330_15203576-hq.mp3',
        'sha256': 'c790c33bc45f8d438eab03b9e26a55fb22c60ce8b40b8fb56de5e9b0877c4703',
        'license': 'CC0-1.0', 'recording': 'Cobra walkie-talkie static, Zoom H4n.',
    },
    'ambulance': {
        'filename': 'ambulance.mp3', 'title': 'Ambulance siren', 'author': 'stereobrother',
        'page': 'https://freesound.org/people/stereobrother/sounds/445344/',
        'url': 'https://cdn.freesound.org/previews/445/445344_1601280-hq.mp3',
        'sha256': '57c0581d5b93cb4d175da5cc9d3078d4ac1fc8e0b6cb20387d7beeffeb5dffec',
        'license': 'CC0-1.0', 'recording': 'Manhattan ambulance recorded with Zoom H2n.',
    },
    'alarm': {
        'filename': 'alarm.mp3', 'title': 'Fire alarm', 'author': 'pushkin',
        'page': 'https://freesound.org/people/pushkin/sounds/319413/',
        'url': 'https://cdn.freesound.org/previews/319/319413_336074-hq.mp3',
        'sha256': '0a89258cb93066e9d12d58e44d85aac0c28a073b95a734a2daac4040ef66438e',
        'license': 'CC0-1.0', 'recording': 'A real building fire alarm.',
    },
    'book': {
        'filename': 'book.mp3', 'title': 'Book Page Turn', 'author': 'Kodack',
        'page': 'https://freesound.org/people/Kodack/sounds/256475/',
        'url': 'https://cdn.freesound.org/previews/256/256475_2276808-hq.mp3',
        'sha256': '99c0ffb127dfc64214c6ecd5d30f2a5deb3f2419328e5a54f7c070f2e341cd71',
        'license': 'CC0-1.0', 'recording': 'Book pages recorded with Sony HDR PJ260V; existing source.',
    },
}

# Exact, source-time cuts. Archive files are decoded without the older
# foley generator's silence trimming, so these times remain reproducible.
# A layer is (source key, start seconds, end seconds, placement, gain).
RECIPES = {
    'cinematic/breath': {
        'seconds': 5.8, 'rms': .035, 'peak': .22,
        'filter': 'highpass=f=80,lowpass=f=4200',
        'cuts': [('breath', 0.0, 5.8, 0.0, 1.0)],
    },
    'cinematic/lab_hum': {
        'seconds': 12.0, 'rms': .045, 'peak': .30,
        'filter': 'highpass=f=50,lowpass=f=1800',
        'cuts': [('v2:sfx100v2_loop_machine_01.ogg', .35, 7.35, 0.0, 1.0),
                 ('v2:sfx100v2_loop_machine_01.ogg', .35, 7.35, 6.0, 1.0)],
    },
    'cinematic/heartbeat': {
        'seconds': 12.0, 'rms': .060, 'peak': .35,
        'filter': 'highpass=f=22,lowpass=f=950',
        'cuts': [('heartbeat', 4.0, 17.0, 0.0, 1.0)],
    },
    'cinematic/lab_alarm': {
        'seconds': 12.0, 'rms': .060, 'peak': .35,
        'filter': 'highpass=f=110,lowpass=f=5000',
        'cuts': [('alarm', 4.0, 17.0, 0.0, 1.0)],
    },
    'cinematic/radio_static': {
        'seconds': 1.4, 'rms': .045, 'peak': .32,
        'filter': 'highpass=f=300,lowpass=f=4200',
        'cuts': [('radio', .25, 1.65, 0.0, 1.0)],
    },
    'cinematic/camera_static': {
        'seconds': 2.6, 'rms': .055, 'peak': .38,
        'filter': 'highpass=f=200,lowpass=f=5200',
        'cuts': [('radio', .4, 3.0, 0.0, 1.0)],
    },
    'cinematic/ambulance_siren': {
        'seconds': 8.0, 'rms': .070, 'peak': .46,
        'filter': 'highpass=f=180,lowpass=f=3800',
        'cuts': [('ambulance', 13.7, 21.7, 0.0, 1.0)],
    },
    'ui/stamp': {
        'seconds': .24, 'rms': .050, 'peak': .40,
        'filter': 'highpass=f=75,lowpass=f=4200',
        'cuts': [('wm:wood_hit_06.ogg', 0.0, .15, .025, 1.0),
                 ('book', 6.02, 6.20, 0.0, .12)],
    },
}
OUTPUTS = tuple(RECIPES)
LOOPS = {'cinematic/lab_hum', 'cinematic/heartbeat', 'cinematic/lab_alarm'}


def dependencies(names: list[str]) -> set[str]:
    return {cut[0] for name in names for cut in RECIPES[name]['cuts']}


def verified(path: Path, digest: str) -> None:
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise RuntimeError(f'SHA-256 distinto: {path}; no se usará una fuente alterada.')


def fetch_file(path: Path, url: str, digest: str, fetch: bool) -> None:
    if not path.exists():
        if not fetch:
            raise RuntimeError(f'Falta {path}; usa --fetch para descargar la fuente CC0.')
        request = urllib.request.Request(url, headers={'User-Agent': 'TheMiracle-CC0-audio/1.0'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise RuntimeError(f'SHA-256 inesperado en la descarga: {url}')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    verified(path, digest)


def prepare_sources(names: list[str], fetch: bool = False) -> None:
    packs = set()
    for key in sorted(dependencies(names)):
        if ':' in key:
            packs.add(key.split(':', 1)[0])
        else:
            spec = SOURCES[key]
            fetch_file(CACHE / spec['filename'], spec['url'], spec['sha256'], fetch)
    for pack in sorted(packs):
        filename, url, digest = foley.PACKS[pack]
        fetch_file(foley.CACHE / filename, url, digest, fetch)


def decode(data: bytes, filters: str = '', raw: bool = False) -> list[float]:
    command = [foley.ffmpeg(), '-nostdin', '-v', 'error']
    if raw:
        command += ['-f', 'f32le', '-ar', str(RATE), '-ac', '1']
    command += ['-i', 'pipe:0', '-vn', '-ac', '1', '-ar', str(RATE)]
    if filters:
        command += ['-af', filters]
    command += ['-f', 'f32le', '-']
    result = subprocess.run(command, input=data, capture_output=True, check=True)
    samples = array.array('f')
    samples.frombytes(result.stdout)
    if sys.byteorder == 'big':
        samples.byteswap()
    return list(samples)


@lru_cache(maxsize=12)
def recording(key: str) -> tuple[float, ...]:
    if ':' in key:
        pack, member = key.split(':', 1)
        filename, _, digest = foley.PACKS[pack]
        path = foley.CACHE / filename
        verified(path, digest)
        with zipfile.ZipFile(path) as archive:
            data = archive.read(member)
    else:
        spec = SOURCES[key]
        path = CACHE / spec['filename']
        verified(path, spec['sha256'])
        data = path.read_bytes()
    return tuple(decode(data))


def render(name: str) -> list[float]:
    spec = RECIPES[name]
    is_loop = name in LOOPS
    out = [0.0] * round((spec['seconds'] + (1.0 if is_loop else 0.0)) * RATE)
    for index, (key, start, end, at, gain) in enumerate(spec['cuts']):
        take = list(recording(key)[round(start * RATE):round(end * RATE)])
        if len(take) < round((end - start) * RATE) - 2:
            raise RuntimeError(f'Fuente demasiado corta: {key}, {start}–{end}.')
        if name == 'cinematic/lab_hum':
            # Two seven-second takes overlap by one second with complementary
            # envelopes; the result has no pause or abrupt repeated fan start.
            take = fade(take, 1.0 if index else .001, 1.0 if index == 0 else .001)
        elif not is_loop:
            take = fade(take, .004, .025)
        layer(out, take, at, gain)
    pcm = array.array('f', out)
    if sys.byteorder == 'big':
        pcm.byteswap()
    out = decode(pcm.tobytes(), spec['filter'], raw=True)
    if is_loop:
        out = loop(out, spec['seconds'], 1.0)
        mean = sum(out) / len(out)
        out = [x - mean for x in out]
    else:
        if name == 'cinematic/ambulance_siren':
            # A real US ambulance's receding take, with extra distance gain.
            # No synthesized siren, Doppler simulation or tape-rate change.
            out = [x * (1.0 - .84 * (i / (len(out) - 1))) for i, x in enumerate(out)]
        attack = .035 if name.endswith(('siren', 'breath')) else .006
        release = 2.0 if name.endswith('siren') else .16 if name.endswith('breath') else .035
        out = fade(out, attack, release)
    return balance(out, spec['rms'], spec['peak'])


def metrics(path: Path) -> dict:
    import wave
    with wave.open(str(path), 'rb') as stream:
        samples = array.array('h', stream.readframes(stream.getnframes()))
    if sys.byteorder == 'big':
        samples.byteswap()
    return {
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'seconds': round(len(samples) / RATE, 6),
        'rms': round(math.sqrt(sum(x*x for x in samples) / len(samples)) / 32768.0, 6),
        'peak': round(max(map(abs, samples)) / 32768.0, 6),
        'dc': round(abs(sum(samples) / len(samples)) / 32768.0, 8),
        'seam_delta': round(abs(samples[-1] - samples[0]) / 32768.0, 8),
    }


def archive_manifest(names: list[str]) -> dict:
    packs: dict[str, set[str]] = {}
    for key in dependencies(names):
        if ':' in key:
            pack, member = key.split(':', 1)
            packs.setdefault(pack, set()).add(member)
    result = {}
    for pack, members in sorted(packs.items()):
        filename, url, digest = foley.PACKS[pack]
        with zipfile.ZipFile(foley.CACHE / filename) as archive:
            result[pack] = {
                'filename': filename, 'url': url, 'sha256': digest,
                'license': 'CC0-1.0', 'credits': 'docs/AUDIO_FOLEY_SOURCES.md',
                'members': {member: hashlib.sha256(archive.read(member)).hexdigest()
                            for member in sorted(members)},
            }
    return result


def generate(assets_dir: Path, names: list[str], manifest: Path | None = None) -> None:
    records = {}
    for name in names:
        path = assets_dir / 'sounds' / (name + '.wav')
        foley.write_wav(path, render(name))
        records[name] = {**metrics(path), 'recipe': RECIPES[name]}
        print(f'cinematic: {name}: {records[name]["seconds"]:.2f}s, '
              f'RMS {records[name]["rms"]:.3f}, peak {records[name]["peak"]:.3f}')
    if manifest:
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({
            'format': {'channels': 1, 'rate': RATE, 'bits': 16},
            'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'file_sources': {key: SOURCES[key] for key in sorted(dependencies(names)) if ':' not in key},
            'archives': archive_manifest(names),
            'processing': 'Natural speed and pitch; mono; source-specific filtering; 1s loop crossfade or edge fades; RMS target with peak ceiling; receding siren gain.',
            'limits': 'Freesound HQ MP3 previews, not lossless masters. Camera interference adapts real walkie-talkie static; lab ambience adapts real machine foley. No voice-over.',
            'subjective_listening_verified': False,
            'outputs': records,
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--only', nargs='+', choices=sorted(OUTPUTS))
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    names = args.only or list(OUTPUTS)
    prepare_sources(names, args.fetch)
    generate(args.assets_dir, names, args.manifest)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f'make_cinematic_sfx: {error}', file=sys.stderr)
        raise SystemExit(1)
