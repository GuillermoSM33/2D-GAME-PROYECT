#!/usr/bin/env python3
"""Edit recorded CC0 weapon foley; originals are never overwritten.

Usage: python3 tools/make_weapon_foley.py [assets_dir] [--only paths ...] [--fetch]
Source provenance, precise edits and limits: docs/AUDIO_WEAPON_SOURCES.md.
Requires ffmpeg only when regenerating; the game embeds the finished WAVs.
"""
from __future__ import annotations

import argparse
import array
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
SOURCE = ROOT / 'recordings/cc0_weapons'
RATE = 22050
OUTPUTS = (
    'weapons/rifle_shot', 'weapons/rifle_reload', 'weapons/rifle_empty',
    'weapons/shotgun_shot', 'weapons/shotgun_reload', 'weapons/shotgun_cycle',
    'weapons/shotgun_empty', 'weapons/dual_shot', 'weapons/dual_reload',
    'weapons/dual_empty', 'weapons/switch', 'weapons/grenade_throw', 'player/empty',
)
SOURCES = {
    'shotgunsounds.zip': 'https://opengameart.org/sites/default/files/shotgunsounds.zip',
    'assaultriflereload1.wav': 'https://opengameart.org/sites/default/files/assaultriflereload1.wav',
    'shotguncock.wav': 'https://opengameart.org/sites/default/files/shotguncock.wav',
    'clipload1.wav': 'https://opengameart.org/sites/default/files/clipload1.wav',
    'singlebullet1.wav': 'https://opengameart.org/sites/default/files/singlebullet1.wav',
    '427595.mp3': 'https://cdn.freesound.org/previews/427/427595_3094998-hq.mp3',
    '427596.mp3': 'https://cdn.freesound.org/previews/427/427596_3094998-hq.mp3',
    '427603.mp3': 'https://cdn.freesound.org/previews/427/427603_3094998-hq.mp3',
}


SOURCE_SHA256 = {
    'shotgunsounds.zip': '31128a93eee729cadcd1cdeabca6b6b1f655578101109b59c0fb5dd4b96e6079',
    'assaultriflereload1.wav': 'efb2d724d634eabe6ba8d3065686abca848bb7497d4d43a5e4aed5e5ea23016f',
    'shotguncock.wav': '33e007321ba83301c861aef573f2c40b70bc62f8f24c0164877e6dd123e24371',
    'clipload1.wav': '1cdc10c50a26834ce7562a5f2925b9aa1118e3bb58a86fea80f34558bf2c5101',
    'singlebullet1.wav': '422bb2b92072cf8ecb77fda83e70d27bdcb7fa8cee33415ef66985a8cc14dde2',
    '427595.mp3': '97a8f4893b910e3f43f3ccfcc5ea872af1da917937346f14b4114a74f1974c46',
    '427596.mp3': '000843aa0f9909d0edadeb48d4107e6ecb00842689f339e27c38399b7290d211',
    '427603.mp3': '8b8059190780c123f4452d10bada5a3a8504326a9fc28fec96a277d5ac4727eb',
    'First Shell.mp3': '0e3a8da11bb98a92700b30b809e939bfd2002a629176269ce24b8a9291bdd095',
    'Subsequent Shells.mp3': '47bae369718bfe74979dbc419ee11c561b53a66385c9b0281a0a3d588719ca1e',
    'Rack.mp3': 'c97f10056f123dce481e249457263329aa95237ecd7a77ee1fa96f8eaed0bf91',
}


def verify_sources() -> None:
    for name, expected in SOURCE_SHA256.items():
        path = SOURCE / name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"Missing or changed CC0 source: {path}. Use --fetch; see docs/AUDIO_WEAPON_SOURCES.md.")


def fetch() -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        path = SOURCE / name
        if not path.exists():
            request = urllib.request.Request(url, headers={'User-Agent': 'Vaquera2D audio tools'})
            with urllib.request.urlopen(request, timeout=45) as response:
                path.write_bytes(response.read())
    with zipfile.ZipFile(SOURCE / 'shotgunsounds.zip') as archive:
        for name in archive.namelist():
            if name.lower().endswith('.mp3'):
                # Extract basenames only; never trust archive paths.
                (SOURCE / Path(name).name).write_bytes(archive.read(name))


def ffmpeg() -> str:
    exe = shutil.which('ffmpeg')
    if not exe and sys.platform == 'win32':
        candidate = Path('C:/msys64/ucrt64/bin/ffmpeg.exe')
        exe = str(candidate) if candidate.exists() else None
    if not exe:
        raise SystemExit('Falta ffmpeg. Instala ffmpeg en Linux o MSYS2 UCRT64.')
    return exe


def decode(path: Path) -> list[float]:
    if not path.exists():
        raise SystemExit(f'Falta {path}. Descarga las fuentes con --fetch; ver docs/AUDIO_WEAPON_SOURCES.md.')
    result = subprocess.run([ffmpeg(), '-v', 'error', '-i', str(path), '-ac', '1',
                             '-ar', str(RATE), '-f', 's16le', '-'],
                            capture_output=True, check=True)
    samples = array.array('h', result.stdout)
    if sys.byteorder == 'big':
        samples.byteswap()
    return [s / 32768.0 for s in samples]


def fade(samples: list[float], attack: float = .002, release: float = .020) -> list[float]:
    n = len(samples)
    return [s * min(1.0, i / max(1.0, RATE * attack),
                    (n - 1 - i) / max(1.0, RATE * release)) for i, s in enumerate(samples)]


def clip(samples: list[float], start: float, end: float) -> list[float]:
    return fade(samples[int(start * RATE):int(end * RATE)])


def put(out: list[float], samples: list[float], at: float, gain: float = 1.0) -> None:
    offset = int(at * RATE)
    for i in range(min(len(samples), len(out) - offset)):
        out[offset + i] += gain * samples[i]


def pitch(samples: list[float], speed: float) -> list[float]:
    out = []
    for i in range(int(len(samples) / speed)):
        position = i * speed
        index = int(position)
        frac = position - index
        out.append(samples[index] * (1.0 - frac) + samples[min(index + 1, len(samples) - 1)] * frac)
    return out


def soften(samples: list[float]) -> list[float]:
    # Natural air and friction stay; only subsonic handling and very bright
    # recording noise are removed. No oscillators or sample-and-hold crushing.
    hp = math.exp(-2.0 * math.pi * 65.0 / RATE)
    lp = 1.0 - math.exp(-2.0 * math.pi * 6700.0 / RATE)
    previous, high, low, out = 0.0, 0.0, 0.0, []
    for s in samples:
        high = hp * (high + s - previous)
        previous = s
        low += lp * (high - low)
        out.append(low)
    return fade(out)


def write(path: Path, samples: list[float], target: float, peak: float = .90) -> None:
    samples = soften(samples)
    rms = math.sqrt(sum(s * s for s in samples) / max(1, len(samples)))
    loudest = max((abs(s) for s in samples), default=1.0)
    gain = min(peak / max(loudest, 1e-9), target / max(rms, 1e-9))
    pcm = array.array('h', (max(-32767, min(32767, round(s * gain * 32767))) for s in samples))
    if sys.byteorder == 'big':
        pcm.byteswap()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as output:
        output.setparams((1, 2, RATE, len(pcm), 'NONE', 'not compressed'))
        output.writeframes(pcm.tobytes())
    print(f'weapon_foley: {path} ({len(samples) / RATE:.2f}s, recorded layers, peak {loudest * gain:.2f})')


def generate(assets_dir: Path, only: list[str] | None = None) -> None:
    verify_sources()
    recordings = {name: decode(SOURCE / name) for name in
                  ('First Shell.mp3', 'Subsequent Shells.mp3', 'Rack.mp3',
                   'assaultriflereload1.wav', 'shotguncock.wav', 'clipload1.wav',
                   'singlebullet1.wav', '427595.mp3', '427596.mp3', '427603.mp3')}
    original = decode(ROOT / 'assets/sounds/player/shot.wav')
    legacy_reload = decode(ROOT / 'assets/sounds/player/reload.wav')
    first_shell = clip(recordings['First Shell.mp3'], .32, .85)
    next_shell = clip(recordings['Subsequent Shells.mp3'], .65, 1.19)
    rack = clip(recordings['Rack.mp3'], .55, 1.07)
    dry = clip(recordings['427603.mp3'], .025, .185)
    rifle = recordings['assaultriflereload1.wav']
    pieces: dict[str, tuple[list[float], float]] = {}

    out = [0.0] * int(RATE * 1.10)
    put(out, first_shell, .01)
    put(out, next_shell, .55, .94)
    pieces['weapons/shotgun_reload'] = (out, .14)
    out = [0.0] * int(RATE * .62)
    put(out, rack, .08)
    pieces['weapons/shotgun_cycle'] = (out, .14)

    out = [0.0] * int(RATE * 1.20)
    put(out, clip(rifle, .18, .40), .015)
    put(out, clip(rifle, .94, 1.16), .51)
    put(out, clip(rifle, 1.16, 1.48), .84)
    pieces['weapons/rifle_reload'] = (out, .14)

    # A real report supplies the transient and outdoor decay; a little of
    # the hand cannon's body ties it to the existing western sound palette.
    out = [0.0] * int(RATE * .72)
    put(out, clip(recordings['427595.mp3'], .045, .765), 0.0, .85)
    put(out, pitch(original, .92), 0.0, .16)
    pieces['weapons/shotgun_shot'] = (out, .24)
    out = [0.0] * int(RATE * .26)
    put(out, clip(recordings['427596.mp3'], .06, .32), 0.0)
    pieces['weapons/rifle_shot'] = (out, .20)

    out = [0.0] * int(RATE * .60)
    put(out, original, 0.0, .60)
    put(out, pitch(original, 1.06), .023, .49)
    pieces['weapons/dual_shot'] = (out, .28)
    out = [0.0] * int(RATE * .43)
    put(out, legacy_reload, 0.0, .70)
    put(out, pitch(legacy_reload, 1.05), .022, .52)
    pieces['weapons/dual_reload'] = (out, .13)

    for name, speed, level in (('weapons/rifle_empty', 1.0, .10),
                               ('weapons/shotgun_empty', .90, .10),
                               ('player/empty', .95, .10)):
        out = [0.0] * int(RATE * .20)
        put(out, pitch(dry, speed), .005)
        pieces[name] = (out, level)
    out = [0.0] * int(RATE * .26)
    put(out, dry, .005, .65)
    put(out, pitch(dry, 1.08), .075, .52)
    pieces['weapons/dual_empty'] = (out, .10)

    out = [0.0] * int(RATE * .30)
    put(out, recordings['clipload1.wav'], .01)
    pieces['weapons/switch'] = (out, .09)
    # Ring/pin followed by release of a hand-held object. These are designed
    # from mechanical handling, not represented as a real grenade recording.
    out = [0.0] * int(RATE * .40)
    put(out, clip(recordings['singlebullet1.wav'], .02, .18), .01, .65)
    put(out, clip(recordings['shotguncock.wav'], .03, .20), .19, .28)
    pieces['weapons/grenade_throw'] = (out, .10)

    for name in only or OUTPUTS:
        samples, level = pieces[name]
        write(assets_dir / 'sounds' / f'{name}.wav', samples, level)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assets_dir', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--only', nargs='+', choices=OUTPUTS)
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    if args.fetch:
        fetch()
    generate(args.assets_dir, args.only)
    return 0


if __name__ == '__main__':
    sys.exit(main())
