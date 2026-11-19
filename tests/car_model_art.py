"""Car identity survives damage, glass breakage and both moving-door layers."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import make_city as city
import make_car_passage as passage
from refine_terrain import refine


class CarModelArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = refine('car_wreck', city.make_car_wreck())
        cls.layers = passage.car_sheets()

    def test_each_base_model_keeps_its_cabin_and_cargo_silhouette_after_damage(self):
        """An enclosed long roof, a sedan and an open pickup bed stay distinct."""
        self.assertEqual(city.CAR_LOOKS, (('sedan', 'sand'), ('pickup', 'red'), ('wagon', 'blue')))
        for look, (shape, _) in enumerate(city.CAR_LOOKS):
            for state in range(3):
                origin = (look * 3 + state) * city.CAR_W
                with self.subTest(model=shape, damage=state):
                    # A wagon's cargo roof/window extends past the rear axle;
                    # neither the sedan's trunk nor the pickup's bed does.
                    for x in range(passage.CX(16), passage.CX(24)):
                        self.assertEqual(bool(self.base.get(origin + x, passage.CY(10))[3]), shape == 'wagon')
                    # The pickup's bed stays open behind its short cabin.
                    for x in range(passage.CX(48), passage.CX(55)):
                        self.assertEqual(bool(self.base.get(origin + x, passage.CY(10))[3]), shape != 'pickup')

    def test_doors_and_broken_glass_preserve_each_models_fixed_rear_structure(self):
        """Every state/layer retains the cargo window, roof and rear pillar."""
        kinds = passage.C['CAR_DOOR_KINDS']
        # Fixed regions end before each model's rear passenger door. In the
        # wagon this includes all of the cargo window and its vertical pillar.
        fixed_end = {'sedan': 25, 'pickup': 57, 'wagon': 38}
        for damage, suffix in enumerate(('', '_damaged')):
            for look, (shape, _) in enumerate(city.CAR_LOOKS):
                base_origin = (look * 3 + damage) * city.CAR_W
                for layer in ('', '_front'):
                    art = self.layers[f'sprites/terrain/car_passage{suffix}{layer}.png']
                    for glass in range(3):
                        for door in range(kinds):
                            frame = (look * 3 + glass) * kinds + door
                            with self.subTest(model=shape, damage=damage, layer=layer, glass=glass, door=door):
                                for y in range(city.CAR_H):
                                    for x in range(passage.CX(fixed_end[shape])):
                                        self.assertEqual(art.get(frame * city.CAR_W + x, y),
                                                         self.base.get(base_origin + x, y),
                                                         'Opening a door changed the fixed model structure')

    def test_wagon_has_its_own_rectangular_rear_passenger_window(self):
        wagon = 2
        for damage in range(2):
            shell, glass, hinge, latch = passage.door_shapes(wagon, 0, damage)
            self.assertEqual(shell[0][0], shell[-1][0])
            self.assertEqual(glass[0][0], glass[-1][0])
            self.assertEqual(glass[0][1], glass[1][1])
            self.assertGreater(min(x for x, _ in shell), passage.CX(38))
            self.assertEqual((hinge, latch), (passage.CX(62), passage.CX(43)))
            self.assertNotEqual(shell, passage.door_shapes(0, 0, damage)[0])

    def test_installed_body_and_door_layers_match_their_generators(self):
        assets = {'sprites/terrain/car_wreck.png': self.base, **self.layers}
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'sheet.png'
            for name, art in assets.items():
                with self.subTest(sheet=name):
                    art.save(target)
                    self.assertEqual(target.read_bytes(), (ROOT / 'assets' / name).read_bytes())


if __name__ == '__main__':
    unittest.main()
