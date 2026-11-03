#!/usr/bin/env python3
"""Edit recorded CC0 nature/foley and dog voices, without synthesis.

python3 tools/make_nature_sfx.py [assets_dir] [--only player/drink crow/caw]
python3 tools/make_nature_sfx.py --fetch --review build/nature_review

Only --fetch accesses the network. Source recordings are cached outside the
embedded assets, in recordings/cc0_nature, and verified with SHA256. Requires
ffmpeg (apt or MSYS2 UCRT64); fetching the dog pack also needs bsdtar.
See docs/AUDIO_NATURE_SOURCES.md for credits,
cuts, processing and the limits of the technical review.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import html
import math
import shutil
import subprocess
import sys
import urllib.request
import wave
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = ROOT / 'recordings' / 'cc0_nature'
RATE = 22050
OUTPUTS = [
    'player/drink', 'crow/caw', 'crow/death',
    'weather/wind', 'weather/rain', 'weather/thunder',
    'dog/spawn', 'dog/idle', 'dog/death',
]

# Every linked primary page explicitly lists Creative Commons 0 / CC0 1.0.
# Freesound downloads are public HQ previews; OGA files are the uploaded masters.
SOURCES = {
    'drink': {
        'title': 'Drinking Water.wav', 'author': 'thatkellytrna',
        'page': 'https://freesound.org/people/thatkellytrna/sounds/425772/',
        'url': 'https://cdn.freesound.org/previews/425/425772_7179420-hq.mp3',
        'sha256': '59be338015ad9bbc5bc32eb72d8f26949ef5e6dfa64966e7be42ebf7292e5b6d',
    },
    'flask': {
        'title': 'Water Bottle Gulp', 'author': 'qubodup',
        'page': 'https://freesound.org/people/qubodup/sounds/792933/',
        'url': 'https://cdn.freesound.org/previews/792/792933_71257-hq.mp3',
        'sha256': '6d35ba6f2c7af4fb285473fe1b082bf57d7921cc140d793dc7c5de713306f688',
    },
    'crow': {
        'title': 'Caw.ogg', 'author': 'egomassive; original recording Nigel Coop',
        'page': 'https://freesound.org/people/egomassive/sounds/536732/',
        'url': 'https://cdn.freesound.org/previews/536/536732_1415754-hq.mp3',
        'sha256': '1434dfd0a9233378ac96a80f52a2722e1efc124c2e1997bfc61aa14d55f5d26a',
    },
    'wings': {
        'title': 'wings.wav', 'author': 'Godowan',
        'page': 'https://freesound.org/people/Godowan/sounds/240476/',
        'url': 'https://cdn.freesound.org/previews/240/240476_1662097-hq.mp3',
        'sha256': 'd2c5c97861235020862bb78735f48b033c48c21f283bbb0338bc0f1d805f2ad7',
    },
    'wind': {
        'title': 'Wind Blowing Leaves in Tree', 'author': 'naturenotesuk',
        'page': 'https://freesound.org/people/naturenotesuk/sounds/442824/',
        'url': 'https://cdn.freesound.org/previews/442/442824_7455632-hq.mp3',
        'sha256': '8237bcecab07ddfdc418d37a34e2fb02e69c560fa977db175b9ddc9d6b867c54',
    },
    'rain': {
        'title': 'Clean rain in a courtyard', 'author': 'xkeril',
        'page': 'https://freesound.org/people/xkeril/sounds/612817/',
        'url': 'https://cdn.freesound.org/previews/612/612817_13504080-hq.mp3',
        'sha256': 'f81c3852b38a209aeb83dece3788fd9e5c7d8e9594be393e755a3fb67d85fb59',
    },
    'thunder': {
        'title': 'thunder dry crack rumble.wav', 'author': 'cognito perceptu',
        'page': 'https://freesound.org/people/cognito%20perceptu/sounds/536903/',
        'url': 'https://cdn.freesound.org/previews/536/536903_57789-hq.mp3',
        'sha256': '23f8f5ce29b8e554316a103725258307e8eb06fccedfc8720e4ad31939f6c3a7',
    },
    'dog_bark': {
        'title': 'Dog sounds — Dog Bark 2.wav', 'author': 'pauliuw',
        'page': 'https://opengameart.org/content/dog-sounds',
        'filename': 'dog_bark_source.wav', 'archive': 'dogs',
        'member': 'Dog/Dog Bark 2.wav',
        'sha256': '7fa8fdcab7c2b7468d9838dd9d4c82b0cd9b7c7575f2a697b269bb083ac6f7e6',
    },
    'dog_growl': {
        'title': 'Dog Growl', 'author': 'bonebrah',
        'page': 'https://opengameart.org/content/dog-growl',
        'url': 'https://opengameart.org/sites/default/files/dog-growl.ogg',
        'filename': 'dog_growl_source.ogg',
        'sha256': '75655fe1bb7415dcd5af93fee82224544bdb03580e710b35e7547388281ab3d5',
    },
    'dog_whine': {
        'title': 'Dog sounds — Sad Dog 1.wav', 'author': 'pauliuw',
        'page': 'https://opengameart.org/content/dog-sounds',
        'filename': 'dog_whine_source.wav', 'archive': 'dogs',
        'member': 'Dog/Sad Dog 1.wav',
        'sha256': '6a7d8d6664b10e265180d68bfe28253e27c118fdfc0d8e2a1d401a932f9ef498',
    },
}
ARCHIVES = {
    'dogs': {
        'filename': 'dog.7z',
        'url': 'https://opengameart.org/sites/default/files/dog.7z',
        'sha256': 'ecee65b849048790e963952dd15c74889c89d7c948a629e041caa631886d7662',
    },
}
LICENSE_URL = 'https://creativecommons.org/publicdomain/zero/1.0/'


def ffmpeg() -> str:
    found = shutil.which('ffmpeg')
    if found is None and sys.platform == 'win32':
        found = shutil.which('ffmpeg', path='C:/msys64/ucrt64/bin')
    if found is None:
        raise RuntimeError('Falta ffmpeg: apt install ffmpeg / pacman -S mingw-w64-ucrt-x86_64-ffmpeg')
    return found


def source_file(key: str) -> Path:
    return SOURCES_DIR / SOURCES[key].get('filename', f'{key}_source.mp3')


def check_source(key: str) -> Path:
    path = source_file(key)
    if not path.exists():
        raise RuntimeError(f'Falta {path}. Ejecuta con --fetch para descargar la fuente CC0.')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != SOURCES[key]['sha256']:
        raise RuntimeError(f'SHA256 diferente para {path}; no se usará una fuente modificada.')
    return path


def bsdtar() -> str:
    found = shutil.which('bsdtar')
    if found is None and sys.platform == 'win32':
        found = shutil.which('bsdtar', path='C:/msys64/usr/bin')
    if found is None:
        raise RuntimeError('Falta bsdtar para abrir el paquete CC0: '
                           'apt install libarchive-tools / pacman -S libarchive')
    return found


def fetch_verified(spec: dict[str, str], path: Path) -> None:
    if path.exists():
        data = path.read_bytes()
    else:
        request = urllib.request.Request(spec['url'], headers={'User-Agent': 'Vaquera2D-CC0-audio/1.0'})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
    if hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise RuntimeError(f'SHA256 diferente para {path}; no se usará una fuente modificada.')
    if not path.exists():
        path.write_bytes(data)


def fetch_sources(keys: set[str]) -> None:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    for key in sorted(keys):
        path = source_file(key)
        if path.exists():
            check_source(key)
            continue
        spec = SOURCES[key]
        if 'archive' in spec:
            archive = ARCHIVES[spec['archive']]
            archive_path = SOURCES_DIR / archive['filename']
            fetch_verified(archive, archive_path)
            # Read only the named member into memory: no archive-supplied paths
            # are ever extracted to disk, and its own hash must also match.
            result = subprocess.run([bsdtar(), '-xOf', str(archive_path), '--', spec['member']],
                                    check=True, capture_output=True)
            if hashlib.sha256(result.stdout).hexdigest() != spec['sha256']:
                raise RuntimeError(f'SHA256 diferente para {spec["member"]}; no se usará ese recorte.')
            path.write_bytes(result.stdout)
        else:
            fetch_verified(spec, path)
        print(f'CC0: {spec["author"]} / {spec["title"]}: {path}')


@lru_cache(maxsize=32)
def clip(key: str, start: float, end: float, filters: str = '') -> list[float]:
    """Decode exact source-time cuts. FFmpeg does antialiasing on resampling."""
    command = [ffmpeg(), '-nostdin', '-v', 'error', '-ss', str(start),
               '-i', str(check_source(key)), '-t', str(end - start), '-vn', '-ac', '1']
    if filters:
        command += ['-af', filters]
    command += ['-ar', str(RATE), '-f', 'f32le', '-']
    result = subprocess.run(command, check=True, capture_output=True)
    values = array.array('f')
    values.frombytes(result.stdout)
    if sys.byteorder == 'big':
        values.byteswap()
    if not values:
        raise RuntimeError(f'El recorte de {key} está vacío.')
    return list(values)


def fade(samples: list[float], attack: float = 0.006,
         release: float = 0.06) -> list[float]:
    length = len(samples)
    return [sample * min(1.0, i / max(1, RATE * attack),
                         (length - 1 - i) / max(1, RATE * release))
            for i, sample in enumerate(samples)]


def balance(samples: list[float], rms_target: float = 0.12,
            peak_limit: float = 0.76) -> list[float]:
    peak = max(abs(s) for s in samples)
    rms = math.sqrt(sum(s * s for s in samples) / len(samples))
    gain = min(peak_limit / max(peak, 1e-9), rms_target / max(rms, 1e-9))
    return [sample * gain for sample in samples]


def layer(out: list[float], samples: list[float], at: float, gain: float) -> None:
    start = int(at * RATE)
    for i in range(min(len(samples), len(out) - start)):
        out[start + i] += samples[i] * gain


def loop(samples: list[float], length: float = 12.0,
         overlap: float = 1.0) -> list[float]:
    """Last overlap second leads naturally into the sample before the loop head."""
    count, cross = int(length * RATE), int(overlap * RATE)
    if len(samples) < count + cross:
        raise RuntimeError('La fuente es demasiado corta para este bucle.')
    out = samples[cross:cross + count]
    for i in range(cross):
        u = i / max(1, cross - 1)
        # Complementary curves preserve a constant correlated-noise level.
        blend = 0.5 - 0.5 * math.cos(math.pi * u)
        pos = count - cross + i
        out[pos] = out[pos] * (1.0 - blend) + samples[i] * blend
    out[-1] = out[0]
    return out


def render(name: str, processed: bool = True) -> list[float]:
    """Assembly uses only recorded sources. No oscillators, noise or chip layer."""
    clean = 'highpass=f=75,lowpass=f=6500' if processed else ''
    if name == 'player/drink':
        out = [0.0] * int(1.18 * RATE)
        water = balance(fade(clip('flask', 0.0, 0.202, clean), 0.005, 0.025), 0.18, 0.62)
        for at, gain in ((0.065, 0.78), (0.405, 0.69), (0.755, 0.60)):
            layer(out, water, at, gain)
        throat_filter = ('highpass=f=110,lowpass=f=3000,'
                         'agate=threshold=0.004:ratio=2.5:attack=8:release=80') if processed else ''
        for start, end, at, gain in ((7.08, 7.40, 0.25, 0.32),
                                     (17.08, 17.35, 0.83, 0.26)):
            swallow = balance(fade(clip('drink', start, end, throat_filter), 0.012, 0.055), 0.15, 0.52)
            layer(out, swallow, at, gain)
        return balance(fade(out, 0.006, 0.07), 0.12, 0.70)
    if name == 'crow/caw':
        # Both complete recorded calls, including the breath between them.
        return balance(fade(clip('crow', 0.035, 1.87, clean), 0.008, 0.075), 0.12, 0.66)
    if name == 'crow/death':
        out = [0.0] * int(0.98 * RATE)
        # A naturally sharper second call, shortened before its normal ending.
        startled = balance(fade(clip('crow', 1.19, 1.64, clean), 0.005, 0.045), 0.16, 0.65)
        flutter_filter = 'highpass=f=85,lowpass=f=4800' if processed else ''
        flutter = balance(fade(clip('wings', 0.035, 0.925, flutter_filter), 0.008, 0.14), 0.11, 0.48)
        layer(out, startled, 0.005, 0.90)
        layer(out, flutter, 0.075, 0.70)
        return balance(fade(out, 0.006, 0.10), 0.14, 0.72)
    if name == 'weather/wind':
        filtering = 'highpass=f=85,lowpass=f=5300' if processed else ''
        return balance(loop(clip('wind', 40.0, 53.0, filtering)), 0.080, 0.36)
    if name == 'weather/rain':
        filtering = 'highpass=f=110,lowpass=f=6200' if processed else ''
        return balance(loop(clip('rain', 20.0, 33.0, filtering)), 0.080, 0.36)
    if name == 'weather/thunder':
        filtering = 'highpass=f=38,lowpass=f=6100' if processed else ''
        return balance(fade(clip('thunder', 2.18, 9.85, filtering), 0.007, 0.9), 0.15, 0.76)
    if name.startswith('dog/'):
        # These are three separately identified canine recordings, not edits
        # of the protected human zombie voices. Preserve their natural pitch.
        filtering = ('highpass=f=65,lowpass=f=6700,'
                     'agate=threshold=0.004:ratio=1.5:attack=5:release=65') if processed else ''
        if name == 'dog/spawn':
            return balance(fade(clip('dog_bark', 0.0, 0.333, filtering), 0.006, 0.045), 0.14, 0.70)
        if name == 'dog/idle':
            return balance(fade(clip('dog_growl', 0.0, 0.608, filtering), 0.009, 0.075), 0.10, 0.60)
        if name == 'dog/death':
            # An ordinary whine that decays into rest; not a recorded death.
            return balance(fade(clip('dog_whine', 0.94, 1.66, filtering), 0.009, 0.150), 0.10, 0.62)
    raise ValueError(name)


DEPENDENCIES = {
    'player/drink': {'drink', 'flask'}, 'crow/caw': {'crow'},
    'crow/death': {'crow', 'wings'}, 'weather/wind': {'wind'},
    'weather/rain': {'rain'}, 'weather/thunder': {'thunder'},
    'dog/spawn': {'dog_bark'}, 'dog/idle': {'dog_growl'}, 'dog/death': {'dog_whine'},
}


def write_wav(path: Path, samples: list[float]) -> None:
    values = array.array('h', (round(max(-1.0, min(1.0, s)) * 32767.0) for s in samples))
    if sys.byteorder == 'big':
        values.byteswap()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(values.tobytes())


def generate(assets_dir: Path, only: list[str] | None = None) -> None:
    selected = OUTPUTS if only is None else only
    for name in selected:
        if name not in OUTPUTS:
            raise ValueError(f'Efecto desconocido: {name}')
        path = assets_dir / 'sounds' / (name + '.wav')
        samples = render(name)
        write_wav(path, samples)
        print(f'nature_sfx: {path} ({len(samples) / RATE:.3f}s, PCM16 mono {RATE}Hz)')


def review(directory: Path, selected: list[str]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    sections = []
    for name in selected:
        raw, final = render(name, False), render(name)
        filename = name.replace('/', '_') + '_source_then_final.wav'
        write_wav(directory / filename, raw + [0.0] * int(0.7 * RATE) + final)
        sections.append(f'<h2>{html.escape(name)}</h2><p>Primero: recorte/mezcla de grabaciones. '
                        'Pausa de 0.7 s. Después: efecto final con edición.</p>'
                        f'<audio controls preload="none" src="{filename}"></audio>')
    document = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                '<title>Vaquera 2D — revisión de naturaleza, beber y voces caninas</title>'
                '<style>body{font:18px/1.5 system-ui;max-width:900px;margin:40px auto;'
                'padding:0 20px;background:#191614;color:#f0e4d1}audio{width:100%}</style>'
                '<h1>Comparación de grabaciones y efectos finales</h1>'
                '<p>Estas comparaciones permiten una revisión auditiva humana. La validación '
                'de formato, picos y bucles no certifica que un efecto suene convincente.</p>'
                + ''.join(sections) + '</html>')
    (directory / 'index.html').write_text(document, encoding='utf-8', newline='\n')
    print(f'Revisión para escuchar: {directory / "index.html"}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--only', nargs='+', choices=OUTPUTS)
    parser.add_argument('--fetch', action='store_true', help='download missing verified CC0 recordings')
    parser.add_argument('--review', type=Path, help='write source/final comparisons outside assets')
    args = parser.parse_args()
    selected = args.only or OUTPUTS
    if args.fetch:
        fetch_sources(set().union(*(DEPENDENCIES[name] for name in selected)))
    generate(args.assets_dir, selected)
    if args.review:
        review(args.review, selected)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.CalledProcessError, OSError) as error:
        sys.exit(str(error))
