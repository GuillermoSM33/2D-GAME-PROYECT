#!/usr/bin/env python3
"""Regression tests for corrupt authoring/export output; no source downloads."""
from __future__ import annotations

import array
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import wave

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from check_audio import Audit, RATE  # noqa: E402
import make_nature_sfx as nature  # noqa: E402


class AudioExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix='audio-test-', dir=ROOT / 'build')
        self.assets = Path(self.directory.name) / 'assets'

    def tearDown(self) -> None:
        target = Path(self.directory.name).resolve()
        if not target.is_relative_to((ROOT / 'build').resolve()) or not target.name.startswith('audio-test-'):
            raise RuntimeError('Unexpected test cleanup path')
        # Windows virus scanners can briefly keep a newly written WAV's
        # directory open after Python has closed it. Retry that transient
        # lock without ignoring persistent failures or leaving test files.
        for attempt in range(8):
            try:
                self.directory.cleanup()
                return
            except PermissionError:
                if attempt == 7:
                    raise
                time.sleep(.03 * (attempt + 1))

    def write(self, name: str, samples: list[int], width: int = 2) -> None:
        path = self.assets / 'sounds' / (name + '.wav')
        path.parent.mkdir(parents=True, exist_ok=True)
        values = array.array('h', samples)
        if sys.byteorder == 'big':
            values.byteswap()
        with wave.open(str(path), 'wb') as output:
            output.setparams((1, width, RATE, 0, 'NONE', 'not compressed'))
            output.writeframes(values.tobytes() if width == 2 else bytes([128] * len(samples)))

    def audit(self, name: str) -> list[str]:
        result = Audit(self.assets)
        result.wav(name)
        return result.errors

    @staticmethod
    def gesture() -> list[int]:
        # A small clean fixture; individual tests damage one relevant property.
        samples = [int(8000 * math.sin(i * .08) * math.sin(math.pi * i / 2204)) for i in range(2205)]
        samples[0] = samples[-1] = 0
        return samples

    def test_valid_export_is_accepted(self) -> None:
        self.write('player/jump', self.gesture())
        self.assertEqual(self.audit('player/jump'), [])

    def test_silence_is_rejected(self) -> None:
        self.write('player/jump', [0] * 2205)
        self.assertTrue(any('silence' in error for error in self.audit('player/jump')))

    def test_wrong_export_depth_is_rejected(self) -> None:
        self.write('player/jump', self.gesture(), width=1)
        self.assertTrue(any('PCM16' in error for error in self.audit('player/jump')))

    def test_clipped_attack_is_rejected(self) -> None:
        samples = self.gesture()
        samples[100] = 32767
        self.write('player/jump', samples)
        self.assertTrue(any('clipping' in error for error in self.audit('player/jump')))

    def test_cut_tail_is_rejected(self) -> None:
        samples = self.gesture()
        samples[-1] = 15000
        self.write('player/jump', samples)
        self.assertTrue(any('last sample' in error for error in self.audit('player/jump')))

    def test_ambience_seam_damage_is_rejected(self) -> None:
        samples = [int(3000 * math.sin(i * 2 * math.pi / 147)) for i in range(RATE * 12)]
        samples[-1] = 12000
        self.write('weather/rain', samples)
        self.assertTrue(any('seam' in error for error in self.audit('weather/rain')))

    def test_changed_original_is_rejected(self) -> None:
        baseline = json.loads((ROOT / 'docs/AUDIO_LEGACY_SHA256.json').read_text(encoding='utf-8'))
        for name in baseline['files']:
            relative = Path(name).relative_to('assets')
            target = self.assets / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        result = Audit(self.assets)
        self.assertEqual(len(result.legacy()), 11)
        self.assertEqual(result.errors, [])
        path = self.assets / 'sounds/player/shot.wav'
        data = bytearray(path.read_bytes())
        data[-1] ^= 1
        path.write_bytes(data)
        result = Audit(self.assets)
        result.legacy()
        self.assertTrue(any('player/shot.wav' in error for error in result.errors))

    @contextmanager
    def dog_source_fixture(self, member: bytes, archive: bytes = b'pack'):
        directory = Path(self.directory.name) / 'sources'
        directory.mkdir()
        archive_path = directory / 'dog.7z'
        archive_path.write_bytes(archive)
        source_spec = {
            'filename': 'dog_bark_source.wav', 'archive': 'dogs',
            'member': 'Dog/Dog Bark 2.wav', 'title': 'Bark', 'author': 'Fixture',
            'sha256': hashlib.sha256(b'expected-source').hexdigest(),
        }
        archive_spec = {
            'filename': 'dog.7z', 'url': 'https://invalid.example/no-network',
            'sha256': hashlib.sha256(b'pack').hexdigest(),
        }
        completed = subprocess.CompletedProcess([], 0, stdout=member, stderr=b'')
        with patch.object(nature, 'SOURCES_DIR', directory), \
             patch.dict(nature.SOURCES, {'dog_bark': source_spec}), \
             patch.dict(nature.ARCHIVES, {'dogs': archive_spec}), \
             patch.object(nature, 'bsdtar', return_value='bsdtar-fixture'), \
             patch.object(nature.subprocess, 'run', return_value=completed) as extract, \
             patch.object(nature.urllib.request, 'urlopen') as network:
            yield directory, archive_path, extract, network

    def test_dog_pack_reads_only_verified_named_member_to_stdout(self) -> None:
        with self.dog_source_fixture(b'expected-source') as (directory, archive, extract, network):
            nature.fetch_sources({'dog_bark'})
            self.assertEqual((directory / 'dog_bark_source.wav').read_bytes(), b'expected-source')
            self.assertEqual(sorted(p.name for p in directory.iterdir()),
                             ['dog.7z', 'dog_bark_source.wav'])
            extract.assert_called_once_with(
                ['bsdtar-fixture', '-xOf', str(archive), '--', 'Dog/Dog Bark 2.wav'],
                check=True, capture_output=True)
            network.assert_not_called()

    def test_changed_dog_archive_is_rejected_before_extraction(self) -> None:
        with self.dog_source_fixture(b'expected-source', b'changed-pack') as fixture:
            directory, _, extract, network = fixture
            with self.assertRaisesRegex(RuntimeError, 'SHA256'):
                nature.fetch_sources({'dog_bark'})
            self.assertFalse((directory / 'dog_bark_source.wav').exists())
            extract.assert_not_called()
            network.assert_not_called()

    def test_changed_dog_member_is_rejected_without_writing_source(self) -> None:
        with self.dog_source_fixture(b'wrong-member') as fixture:
            directory, _, extract, network = fixture
            with self.assertRaisesRegex(RuntimeError, 'SHA256'):
                nature.fetch_sources({'dog_bark'})
            self.assertFalse((directory / 'dog_bark_source.wav').exists())
            extract.assert_called_once()
            network.assert_not_called()


if __name__ == '__main__':
    unittest.main()
