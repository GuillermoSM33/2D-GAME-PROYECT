"""Regression checks for layer boundaries and non-destructive build cleanup."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import check_architecture as architecture
import clean_project as cleanup
from embed_assets import write_asset_list


class ProjectToolsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='vaquera-project-tools-')
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def write(self, name, content=''):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def fixture(self):
        self.write('Makefile', 'CORE_SRC := src/game/rules.c\nAPP_SRC := src/main.c\n')
        self.write('src/main.c', 'int main(void) { return 0; }\n')
        self.write('src/game/rules.c', '#include "game/rules.h"\n')
        self.write('src/game/rules.h')

    def audit(self):
        with patch.object(architecture, 'ROOT', self.root), patch.object(architecture, 'SRC', self.root / 'src'):
            return architecture.audit()

    def test_pure_graph_passes_and_transitive_sdl_fails(self):
        self.fixture()
        self.assertEqual(self.audit(), [])
        self.write('src/game/rules.h', '#include "engine/view.h"\n')
        self.write('src/engine/view.h', '#include <SDL.h>\n')
        self.assertTrue(any('pure logic' in error for error in self.audit()))

    def test_reverse_layer_dependency_is_rejected(self):
        self.fixture()
        self.write('src/engine/input.h', '#include "game/rules.h"\n')
        self.assertTrue(any('engine depends on' in error for error in self.audit()))

    def test_uncatalogued_sources_and_including_implementations_fail(self):
        self.fixture()
        self.write('src/game/forgotten.c')
        self.write('tests/bad.c', '#include "../src/main.c"\n')
        errors = self.audit()
        self.assertTrue(any('absent from Makefile' in error for error in errors))
        self.assertTrue(any('includes implementation' in error for error in errors))

    def test_cleanup_preserves_distribution_and_authoring_sources(self):
        self.write('build/debug/game')
        cache = self.write('tools/__pycache__/tool.pyc')
        keep = [self.write(name) for name in ('dist/Vaquera2D', 'tools/tool.py',
                'assets/sounds/bat/chirp.wav', 'recordings/bat.zip', 'docs/templates/source.png')]
        with patch.object(cleanup, 'ROOT', self.root):
            targets = cleanup.targets()
            self.assertIn(self.root / 'build', targets)
            self.assertIn(cache.parent, targets)
            for path in keep:
                self.assertFalse(any(path == item or item in path.parents for item in targets))

    def test_asset_manifest_tracks_deletions_and_otf_without_rewriting_unchanged(self):
        asset = self.write('assets/font.otf')
        manifest = self.root / 'generated/assets.list'
        write_asset_list(self.root / 'assets', manifest)
        self.assertIn('font.otf', manifest.read_text())
        stamp = manifest.stat().st_mtime_ns
        write_asset_list(self.root / 'assets', manifest)
        self.assertEqual(stamp, manifest.stat().st_mtime_ns)
        asset.unlink()
        write_asset_list(self.root / 'assets', manifest)
        self.assertNotIn('font.otf', manifest.read_text())


if __name__ == '__main__':
    unittest.main()
