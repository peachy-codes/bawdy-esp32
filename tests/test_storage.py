"""Unit tests for DeviceRepository and PresetRepository."""

import shutil
import tempfile
import unittest
from pathlib import Path

from wled_app.domain.device import DeviceConfig, ProtocolType
from wled_app.patterns.base import PatternConfig
from wled_app.storage.device_repository import DeviceRepository
from wled_app.storage.preset_repository import Preset, PresetRepository


class TestStorageRepositories(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.device_repo = DeviceRepository(self.temp_dir / "devices")
        self.preset_repo = PresetRepository(self.temp_dir / "presets")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_device_crud_operations(self) -> None:
        dev = DeviceConfig.create(
            name="Living Room ESP32",
            ip="192.168.1.55",
            channel_lengths=[60, 30, 144, 0],
            protocol=ProtocolType.DDP,
            description="Athom controller",
        )

        # Save
        path = self.device_repo.save(dev)
        self.assertTrue(path.exists())

        # Get by ID
        loaded = self.device_repo.get(dev.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.name, "Living Room ESP32")
        self.assertEqual(loaded.total_leds, 234)

        # Get by Name
        by_name = self.device_repo.get_by_name("living room esp32")
        self.assertIsNotNone(by_name)
        assert by_name is not None
        self.assertEqual(by_name.id, dev.id)

        # List all
        all_devs = self.device_repo.list_all()
        self.assertEqual(len(all_devs), 1)

        # Delete
        self.assertTrue(self.device_repo.delete(dev.id))
        self.assertIsNone(self.device_repo.get(dev.id))

    def test_preset_crud_operations(self) -> None:
        # Default presets should be seeded
        presets = self.preset_repo.list_all()
        self.assertGreaterEqual(len(presets), 3)

        custom = Preset(
            name="Custom Chase",
            pattern_id="chase",
            config=PatternConfig(speed=2.0),
            description="Super fast chase",
        )
        self.preset_repo.save(custom)

        loaded = self.preset_repo.get("Custom Chase")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.pattern_id, "chase")
        self.assertEqual(loaded.config.speed, 2.0)

        self.assertTrue(self.preset_repo.delete("Custom Chase"))
        self.assertIsNone(self.preset_repo.get("Custom Chase"))


if __name__ == "__main__":
    unittest.main()
