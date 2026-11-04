import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('planner', ROOT / 'tools/plan-recoveries.py')
planner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planner)


class BuildPlanTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / 'devices/targets.json').read_text())

    def ready_fixture(self):
        catalog = copy.deepcopy(self.catalog)
        for device, target in catalog['targets'].items():
            target.update(build_enabled=True, validation='passed',
                          repository=f'example/android_device_xiaomi_{device}',
                          ref='validated', lunch=f'twrp_{device}-bp2a-userdebug',
                          source_lock=f'{device}-source-lock.xml', modes=['storage'])
        return catalog

    def test_current_catalog_never_builds(self):
        plan = planner.make_plan(self.catalog, 'dipper,perseus,equuleus', 'storage')
        self.assertFalse(plan['ready'])
        self.assertEqual(plan['matrix']['include'], [])
        self.assertEqual(len(plan['blocked']), 3)

    def test_no_partial_batch_when_only_one_device_is_ready(self):
        catalog = self.ready_fixture()
        catalog['targets']['equuleus']['build_enabled'] = False
        plan = planner.make_plan(catalog, 'dipper,perseus,equuleus', 'storage')
        self.assertFalse(plan['ready'])
        self.assertEqual(plan['matrix']['include'], [])

    def test_ready_devices_have_independent_sources_and_outputs(self):
        plan = planner.make_plan(self.ready_fixture(), 'dipper,perseus,equuleus', 'storage')
        self.assertTrue(plan['ready'])
        rows = plan['matrix']['include']
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({row['repository'] for row in rows}), 3)
        for row in rows:
            self.assertEqual(row['product'], row['device'])
            self.assertEqual(row['device_path'], f'device/xiaomi/{row["device"]}')

    def test_invalid_selection_and_shared_crypto_profile_are_rejected(self):
        for selection, mode in [('dipper,dipper', 'storage'), ('unknown', 'storage'),
                                ('dipper;echo', 'storage'), ('dipper', 'decrypt')]:
            with self.subTest(selection=selection, mode=mode), self.assertRaises(ValueError):
                planner.make_plan(self.catalog, selection, mode)

    def test_copying_dipper_identity_to_another_device_is_blocked(self):
        catalog = self.ready_fixture()
        catalog['targets']['perseus']['product'] = 'dipper'
        plan = planner.make_plan(catalog, 'dipper,perseus,equuleus', 'storage')
        self.assertFalse(plan['ready'])
        self.assertIn('device path/product mismatch', plan['blocked'][0]['reasons'])


if __name__ == '__main__':
    unittest.main()
