"""Native art and animation contracts; no network or image-generation calls."""
from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))

from embed_assets import decode_png_rgba
from make_sprites import Image
from make_zombies import (
    ACTIONS, FRAME, IDS, ORIGINAL_HASHES, PALETTE, SKIN_RGB, bounds,
    compose_walk_uniform, export_family, face_box, from_rgba, garment_pixel,
    original_frame, original_path, original_walk_frame, palette_color,
    protected_pixel, sheet_frames, verify_assets, BodyMap, on_face,
)


def load_sheet(path: Path) -> Image:
    return from_rgba(*decode_png_rgba(path))


class TemporaryDirectory(tempfile.TemporaryDirectory):
    """Keep fixtures in build and tolerate a brief Windows indexer lock.

    A persistent failure still fails the test. No cleanup error is ignored.
    """
    def __init__(self):
        directory = ROOT / 'build'
        directory.mkdir(exist_ok=True)
        super().__init__(prefix='zombie-assets-', dir=directory)

    def cleanup(self):
        for attempt in range(8):
            try:
                super().cleanup()
                return
            except PermissionError:
                if attempt == 7:
                    raise
                time.sleep(.03 * (attempt + 1))


class ZombieClothingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ROOT / 'docs/templates/zombies/soldier_walk_clothes_source.png'
        cls.output = compose_walk_uniform(cls.source)
        cls.originals = [original_walk_frame(index) for index in range(8)]
        cls.temporary = TemporaryDirectory()
        cls.assets = Path(cls.temporary.name) / 'assets'
        cls.paths = export_family('soldier', assets_dir=cls.assets)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_native_walk_format_and_all_eight_original_alpha_masks(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'walk.png'
            self.output.save(path)
            self.assertEqual(struct.unpack('>IIBBBBB', path.read_bytes()[16:29]),
                             (576, 72, 8, 6, 0, 0, 0))
        for index, original in enumerate(self.originals):
            for y in range(FRAME):
                for x in range(FRAME):
                    actual = self.output.get(index * FRAME + x, y)
                    self.assertEqual(actual[3], original.get(x, y)[3], (index, x, y))

    def test_actual_olive_skin_face_hands_boots_and_outline_stay_exact(self):
        # These are measured RGBs in the original PNG, not the old design-doc
        # green ramp. This catches the cream-hand regression in civilian art.
        self.assertEqual(SKIN_RGB, {(74, 82, 64), (111, 122, 92), (154, 163, 126)})
        skin_pixels = face_pixels = 0
        for index, original in enumerate(self.originals):
            fx0, fy0, fx1, fy1 = face_box(original)
            for y in range(FRAME):
                for x in range(FRAME):
                    expected = original.get(x, y)
                    face = fx0 <= x < fx1 and fy0 <= y < fy1
                    border = expected[3] and any(not original.get(x + dx, y + dy)[3]
                                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    if expected[:3] in SKIN_RGB or face or y >= 60 or border:
                        self.assertEqual(self.output.get(index * FRAME + x, y), expected,
                                         (index, x, y))
                    skin_pixels += expected[3] and expected[:3] in SKIN_RGB
                    face_pixels += face and expected[3] != 0
        self.assertGreater(skin_pixels, 800)
        self.assertGreater(face_pixels, 300)

    def test_uniform_keeps_material_shadows_and_cream_does_not_become_green(self):
        for index, original in enumerate(self.originals):
            changed = []
            for y in range(FRAME):
                for x in range(FRAME):
                    actual = self.output.get(index * FRAME + x, y)
                    if actual != original.get(x, y):
                        self.assertTrue(garment_pixel(original, x, y))
                        self.assertIn(actual, PALETTE)
                        changed.append(actual)
            self.assertGreater(len(changed), 30)
            self.assertGreaterEqual(len(set(changed)), 4)
        for color in ((245, 219, 164), (188, 185, 157), (210, 198, 169)):
            actual = palette_color(*color)
            self.assertGreaterEqual(actual[0], actual[1], (color, actual))
            self.assertGreater(actual[1], actual[2], (color, actual))

    def test_attack_recoil_and_death_keep_the_native_body_and_hit_timing(self):
        for action in ('attack', 'hurt', 'death'):
            frames = sheet_frames(load_sheet(self.paths[action]))
            for index, actual in enumerate(frames):
                original = original_frame(action, index)
                mapping = BodyMap(original)
                for y in range(FRAME):
                    for x in range(FRAME):
                        self.assertEqual(actual.get(x, y)[3], original.get(x, y)[3])
                        if protected_pixel(original, x, y, mapping) and not on_face(original, x, y):
                            self.assertEqual(actual.get(x, y), original.get(x, y), (action, index, x, y))
        attack = sheet_frames(load_sheet(self.paths['attack']))
        skin_reach = lambda frame: max(x for y in range(FRAME) for x in range(FRAME)
                                      if frame.get(x, y)[:3] in SKIN_RGB)
        self.assertGreater(skin_reach(attack[2]), skin_reach(attack[0]))
        corpse = sheet_frames(load_sheet(self.paths['death']))[-1]
        self.assertLess(bounds(corpse)[3] - bounds(corpse)[1], 20)

    def test_derived_actions_are_distinct_and_only_riot_keeps_legacy_bytes(self):
        export_family('riot', assets_dir=self.assets)
        export_family('elite', assets_dir=self.assets)
        result = verify_assets(self.assets, ['soldier', 'riot', 'elite'])
        self.assertEqual(result, {'families': 3, 'sheets': 21})
        for action, expected in ORIGINAL_HASHES.items():
            actual = self.assets / 'sprites/zombies' / 'riot' / f'{action}.png'
            self.assertEqual(hashlib.sha256(actual.read_bytes()).hexdigest(), expected)
            self.assertEqual(hashlib.sha256(original_path(action).read_bytes()).hexdigest(), expected)
        self.assertNotEqual(
            hashlib.sha256((self.assets / 'sprites/zombies/elite/walk.png').read_bytes()).hexdigest(),
            ORIGINAL_HASHES['walk'])
        walking = load_sheet(self.paths['walk'])
        for action in ('idle', 'run', 'caught'):
            frames = sheet_frames(load_sheet(self.paths[action]))
            self.assertEqual(len({tuple(frame.px) for frame in frames}), ACTIONS[action])
            if action == 'run':
                self.assertNotEqual(frames[0].px, sheet_frames(walking)[0].px)
                feet = [bounds(frame)[3] for frame in frames]
                self.assertLess(min(feet), max(feet))

    def test_every_family_keeps_the_riot_slash_attack_effect(self):
        riot_effect = {(0xfb, 0xaa, 0x38), (0xd0, 0x33, 0x05)}
        for identifier in ('soldier', 'police', 'civil_male_1', 'riot_shield', 'elite'):
            export_family(identifier, assets_dir=self.assets)
            frames = sheet_frames(load_sheet(self.assets / 'sprites/zombies' / identifier / 'attack.png'))
            self.assertTrue(any(pixel[:3] in riot_effect for pixel in frames[2].px), identifier)

    def test_generated_faces_are_visible_and_not_riot_mask_panels(self):
        mask_colors = {(0xa7, 0xa8, 0xa8), (0x5a, 0x62, 0x72),
                       (0x3c, 0x42, 0x50), (0x2a, 0x2e, 0x38), (0x2c, 0x2c, 0x2c)}
        for identifier in ('soldier', 'police', 'civil_male_1', 'riot_shield', 'elite'):
            export_family(identifier, assets_dir=self.assets)
            frames = sheet_frames(load_sheet(self.assets / 'sprites/zombies' / identifier / 'walk.png'))
            for index, frame in enumerate(frames):
                x0, y0, x1, y1 = face_box(original_walk_frame(index))
                face = [frame.get(x, y)[:3] for y in range(y0, y1)
                        for x in range(x0, x1) if frame.get(x, y)[3]]
                self.assertGreater(sum(color in SKIN_RGB for color in face), 40, identifier)
                self.assertLess(sum(color in mask_colors for color in face), 4, identifier)

    def test_dog_keeps_its_own_attack(self):
        export_family('dog', assets_dir=self.assets)
        dog = load_sheet(self.assets / 'sprites/zombies' / 'dog/attack.png')
        riot = load_sheet(self.assets / 'sprites/zombies' / 'riot/attack.png')
        self.assertNotEqual(dog.px, riot.px)
        self.assertFalse(any(pixel[:3] in {(0xfb, 0xaa, 0x38), (0xd0, 0x33, 0x05)}
                             for pixel in sheet_frames(dog)[2].px))

    def test_sources_are_required_and_transparency_cannot_erase_the_body(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, 'Missing approved source'):
                export_family('police', source_dir=root, assets_dir=root / 'output')
            self.assertFalse((root / 'output').exists())
            path = root / 'empty.png'
            Image(576, 72).save(path)
            with self.assertRaisesRegex(ValueError, 'falta el cuadro'):
                compose_walk_uniform(path)
            sparse = Image(576, 72)
            for index in range(8):
                sparse.set(index * FRAME + 25, 40, PALETTE[15])
            sparse.save(path)
            actual = compose_walk_uniform(path)
            for index, original in enumerate(self.originals):
                for y in range(FRAME):
                    for x in range(FRAME):
                        self.assertEqual(actual.get(index * FRAME + x, y)[3], original.get(x, y)[3])


class ShippedZombieAssetsTests(unittest.TestCase):
    def test_all_twenty_five_families_ship_seven_valid_native_actions(self):
        # This deliberately fails when final art is missing: --verify/build
        # must not silently publish old-body fallbacks or incomplete families.
        self.assertEqual(verify_assets(), {'families': 25, 'sheets': 175})

    def test_special_bodies_and_profession_identities_are_not_riot_copies(self):
        root = ROOT / 'assets/sprites/zombies'
        riot = load_sheet(root / 'riot/walk.png')
        dog = sheet_frames(load_sheet(root / 'dog/walk.png'))
        self.assertLessEqual(max(bounds(frame)[3] - bounds(frame)[1] for frame in dog), 40)
        self.assertNotEqual(dog[0].px, sheet_frames(riot)[0].px)
        skeleton = load_sheet(root / 'skeleton/walk.png')
        self.assertNotEqual([c[3] for c in skeleton.px], [c[3] for c in riot.px])
        hashes = []
        for identifier in IDS:
            if identifier in ('riot', 'elite'):
                continue
            image = load_sheet(root / identifier / 'walk.png')
            self.assertNotEqual(image.px, riot.px, identifier)
            hashes.append(hashlib.sha256(bytes(v for color in image.px for v in color)).hexdigest())
        self.assertEqual(len(set(hashes)), len(hashes), 'Two professions are identical raster copies')


if __name__ == '__main__':
    unittest.main()
