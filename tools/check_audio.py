#!/usr/bin/env python3
"""Validate shipped sound coverage, PCM integrity and protected originals.

python3 tools/check_audio.py [--assets-dir assets] [--report build/audio_check.json]

Read-only by default. Uses only Python's standard library, needs neither
FFmpeg nor downloaded source recordings. This checks technical properties,
not subjective sound quality or whether a gameplay branch is reachable.
"""
from __future__ import annotations

import argparse
import array
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import wave

import make_sfx

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / 'docs' / 'AUDIO_LEGACY_SHA256.json'
LOOPS = {'weather/wind', 'weather/rain', 'world/river', 'world/fire', 'world/city',
         'cinematic/lab_hum', 'cinematic/heartbeat', 'cinematic/lab_alarm'}
OUTPUT_MANIFESTS = {
    'make_designed_sfx': 'AUDIO_DESIGNED_MANIFEST.json',
    'make_expansion_sfx': 'AUDIO_EXPANSION_MANIFEST.json',
    'make_cinematic_sfx': 'AUDIO_CINEMATIC_MANIFEST.json',
}
RATE = 22050


def rms(values: list[int] | array.array) -> float:
    return math.sqrt(sum(x*x for x in values) / max(1, len(values))) / 32768.0


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Audit:
    def __init__(self, assets: Path) -> None:
        self.assets = assets
        self.errors: list[str] = []
        self.metrics: dict[str, dict] = {}
        self.checks = 0

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.errors.append(message)

    def wav(self, name: str) -> None:
        path = self.assets / 'sounds' / f'{name}.wav'
        if not path.exists():
            self.check(False, f'{name}: missing WAV')
            return
        try:
            with wave.open(str(path), 'rb') as sound:
                params = (sound.getnchannels(), sound.getsampwidth(), sound.getframerate(), sound.getcomptype())
                self.check(params == (1, 2, RATE, 'NONE'),
                           f'{name}: expected mono PCM16/{RATE}Hz, got {params}')
                if params != (1, 2, RATE, 'NONE'):
                    return
                expected_bytes = sound.getnframes() * 2
                raw = sound.readframes(sound.getnframes())
                self.check(len(raw) == expected_bytes, f'{name}: truncated PCM data')
        except (OSError, EOFError, wave.Error) as error:
            self.check(False, f'{name}: invalid WAV ({error})')
            return
        if not raw or len(raw) % 2:
            self.check(False, f'{name}: empty or incomplete sample data')
            return
        pcm = array.array('h', raw)
        if sys.byteorder == 'big':
            pcm.byteswap()
        seconds = len(pcm) / RATE
        peak = max(map(abs, pcm)) / 32768.0
        energy = rms(pcm)
        dc = abs(sum(pcm) / len(pcm)) / 32768.0
        self.metrics[name] = {'seconds': round(seconds, 6), 'peak': round(peak, 6),
                              'rms': round(energy, 6), 'dc': round(dc, 8),
                              'sha256': digest(path)}
        self.check(seconds >= .04, f'{name}: shorter than 40ms ({seconds:.4f}s)')
        self.check(energy > .001, f'{name}: silence or effectively inaudible RMS ({energy:.6f})')
        self.check(peak < .99, f'{name}: clipping or insufficient headroom (peak={peak:.6f})')
        self.check(dc < .002, f'{name}: excessive DC ({dc:.6f})')
        if name in LOOPS:
            seam = abs(pcm[0] - pcm[-1]) / 32768.0
            self.metrics[name]['seam_delta'] = round(seam, 8)
            self.check(seam <= 2.0 / 32768, f'{name}: discontinuity at loop seam ({seam:.6f})')
            self.check(abs(seconds - 12.0) <= 1.0 / RATE,
                       f'{name}: expected 12s continuous ambience, got {seconds:.3f}s')
            window = int(.05 * RATE)
            self.check(min(rms(pcm[:window]), rms(pcm[-window:])) > energy * .12,
                       f'{name}: quiet gap at loop boundary')
        else:
            edge = max(abs(pcm[0]), abs(pcm[-1])) / 32768.0
            self.check(edge <= 2.0 / 32768, f'{name}: unclean first/last sample ({edge:.6f})')

    def legacy(self) -> set[str]:
        data = json.loads(BASELINE.read_text(encoding='utf-8'))
        originals = data['files']
        self.check(len(originals) == 11, 'legacy baseline must contain the 11 original files')
        for name, expected in originals.items():
            relative = Path(name).relative_to('assets')
            path = self.assets / relative
            self.check(path.exists() and digest(path) == expected,
                       f'{name}: protected original missing or modified')
        # The portable, committed manifest must match the capture made before
        # this task. The capture is optional after clean checkout/build.
        before = ROOT / 'build' / 'audio_protected_before.json'
        if before.exists():
            captured = {}
            for row in json.loads(before.read_text(encoding='utf-8-sig')):
                absolute = row['Path'].replace('\\', '/')
                key = 'assets/' + absolute.split('/assets/', 1)[1]
                captured[key] = row['Hash'].lower()
            self.check(originals == captured, 'legacy manifest differs from the original pre-change capture')
        return {str(Path(path).relative_to('assets/sounds').with_suffix('')).replace('\\', '/')
                for path in originals}

    def source_coverage(self, names: set[str], originals: set[str]) -> None:
        # Only sound prefixes are accepted; art uses a distinct sprites/... root.
        code = '\n'.join(path.read_text(encoding='utf-8')
                         for path in sorted((ROOT / 'src').rglob('*'))
                         if path.suffix in {'.c', '.h'})
        pattern = r'"(?:sounds/)?((?:player|weapons|world|crow|sparrow|bat|dog|zombie|weather|ui|effects|cinematic)/[a-z0-9_]+)"'
        references = set(re.findall(pattern, code))
        expected = names | originals
        self.check(not references - expected, f'unknown C sound references: {sorted(references - expected)}')
        self.check(not expected - references, f'WAVs without a C reference: {sorted(expected - references)}')
        actual = {path.relative_to(self.assets / 'sounds').with_suffix('').as_posix()
                  for path in (self.assets / 'sounds').rglob('*')
                  if path.is_file() and path.suffix.lower() in {'.wav', '.ogg', '.mp3', '.flac'}}
        self.check(actual == expected, f'asset coverage mismatch; missing={sorted(expected-actual)}, orphan={sorted(actual-expected)}')

    def weapon_timings(self) -> None:
        code = (ROOT / 'src/game/weapons.c').read_text(encoding='utf-8')
        blocks = re.findall(r'\[(WEAPON_[A-Z_]+)\]\s*=\s*\{(.*?)\n\s*\}', code, re.S)
        checked = 0
        for weapon, block in blocks:
            for sound_field, time_field in (('reload_sound', 'magazine_reload'), ('cycle_sound', 'reload_time')):
                sound = re.search(r'\.' + sound_field + r'\s*=\s*"([^"]+)"', block)
                duration = re.search(r'\.' + time_field + r'\s*=\s*([0-9.]+)f', block)
                if sound and duration and sound[1] in self.metrics:
                    measured = self.metrics[sound[1]]['seconds']
                    target = float(duration[1])
                    self.check(abs(measured - target) < .03,
                               f'{weapon}: {sound[1]} lasts {measured:.3f}s, {time_field} is {target:.3f}s')
                    checked += 1
        self.check(checked >= 4, 'could not verify rifle/shotgun magazine and shotgun/plasma cycle timings from C')

    def output_manifests(self, builders: dict[str, tuple[str, ...]]) -> None:
        for builder, filename in OUTPUT_MANIFESTS.items():
            if builder not in builders:
                continue
            path = ROOT / 'docs' / filename
            if not path.exists():
                self.check(False, f'missing sound source/output manifest: {filename}')
                continue
            manifest = json.loads(path.read_text(encoding='utf-8'))
            documented = manifest.get('outputs', {})
            self.check(set(documented) == set(builders[builder]),
                       f'{filename}: output manifest does not cover its builder catalogue')
            for name, entry in documented.items():
                if name in self.metrics:
                    self.check(entry['sha256'] == self.metrics[name]['sha256'],
                               f'{name}: documentation output hash is stale')

    def music(self) -> None:
        """The menu and every stage name a track, and each track is the composed one shipped."""
        manifest = json.loads((ROOT / 'docs' / 'AUDIO_MUSIC_MANIFEST.json').read_text(encoding='utf-8'))['tracks']
        code = (ROOT / 'src/game/stages.c').read_text(encoding='utf-8')
        named = re.findall(r'"music/([a-z0-9_]+)"', code)
        self.check(len(named) == len(set(named)), 'two stages share one music track')
        self.check('MENU_MUSIC "music/menu"' in (ROOT / 'src/config.h').read_text(encoding='utf-8'),
                   'the menu no longer plays music/menu')
        self.check(set(named) | {'menu', 'menu_2'} == set(manifest), f'music differs from the manifest: {sorted(named)}')
        for name, entry in manifest.items():
            path = self.assets / 'music' / f'{name}.ogg'
            if not path.exists():
                self.check(False, f'music/{name}: missing OGG')
                continue
            self.check(path.read_bytes()[:4] == b'OggS', f'music/{name}: not an OGG file')
            self.check(digest(path) == entry['sha256'], f'music/{name}: differs from its manifest')

    def run(self) -> dict:
        originals = self.legacy()
        builders = make_sfx.catalog()
        flat = [name for names in builders.values() for name in names]
        duplicates = [name for name, count in Counter(flat).items() if count != 1]
        self.check(not duplicates, f'overlapping generator outputs: {duplicates}')
        self.check(bool(flat), 'sound generator catalogue is empty')
        self.check(not set(flat) & originals, 'a generator would overwrite a protected original')
        for name in sorted(flat):
            self.wav(name)
        self.source_coverage(set(flat), originals)
        self.weapon_timings()
        self.output_manifests(builders)
        self.music()
        return {'passed': not self.errors, 'checks': self.checks, 'new_effects': len(flat),
                'protected_originals': len(originals),
                'builders': {name: len(outputs) for name, outputs in builders.items()},
                'subjective_listening_verified': False,
                'limits': 'Technical waveform, catalogue, static-reference and hash validation only.',
                'errors': self.errors, 'sounds': self.metrics}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-dir', type=Path, default=ROOT / 'assets')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    audit = Audit(args.assets_dir)
    try:
        report = audit.run()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f'check_audio: FAIL: {error}', file=sys.stderr)
        return 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for error in report['errors']:
        print(f'FAIL: {error}', file=sys.stderr)
    state = 'OK' if report['passed'] else 'FAIL'
    print(f'check_audio: {state}: {report["new_effects"]} effects, '
          f'{report["protected_originals"]} protected originals, {report["checks"]} technical checks')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
