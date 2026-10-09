"""Unit tests for multi-stage venue presets, catalog discovery, and preset loading."""

from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from wled_engine.spatial.venue import (
    create_demo_venue,
    create_concert_hall_venue,
    create_warehouse_rave_venue,
    create_festival_amphitheater_venue,
    create_art_gallery_venue,
    get_preset_venue,
    list_preset_names,
    save_all_preset_files,
    save_default_venue_files,
    VENUE_PRESETS,
)


class TestVenuePresets(unittest.TestCase):
    def test_concert_hall_preset(self) -> None:
        uni, patch = create_concert_hall_venue()
        self.assertEqual(uni.name, "Metro Concert Hall & Lounge")
        self.assertEqual(len(uni.fixtures), 28)
        self.assertEqual(uni.total_pixels, 5153)
        self.assertEqual(len(patch.get_controllers()), 20)
        self.assertEqual(patch.validate(), [])
        self.assertIn("trusses", uni.groups)
        self.assertIn("festoon", uni.groups)
        self.assertIn("panels", uni.groups)

    def test_warehouse_rave_preset(self) -> None:
        uni, patch = create_warehouse_rave_venue()
        self.assertEqual(uni.name, "Warehouse Rave & Boiler Stage")
        self.assertEqual(len(uni.fixtures), 26)
        self.assertEqual(uni.total_pixels, 4197)
        self.assertEqual(len(patch.get_controllers()), 16)
        self.assertEqual(patch.validate(), [])
        self.assertIn("dj_cage", uni.groups)
        self.assertIn("strobes", uni.groups)
        self.assertIn("matrices", uni.groups)
        self.assertIn("totems", uni.groups)

    def test_festival_amphitheater_preset(self) -> None:
        uni, patch = create_festival_amphitheater_venue()
        self.assertEqual(uni.name, "Outdoor Amphitheater & Lawn")
        self.assertEqual(len(uni.fixtures), 24)
        self.assertEqual(uni.total_pixels, 3805)
        self.assertEqual(len(patch.get_controllers()), 16)
        self.assertEqual(patch.validate(), [])
        self.assertIn("proscenium", uni.groups)
        self.assertIn("canopy", uni.groups)
        self.assertIn("imag_screens", uni.groups)
        self.assertIn("foh_booth", uni.groups)

    def test_art_gallery_preset(self) -> None:
        uni, patch = create_art_gallery_venue()
        self.assertEqual(uni.name, "Immersive Art Gallery & Studio")
        self.assertEqual(len(uni.fixtures), 22)
        self.assertEqual(uni.total_pixels, 2821)
        self.assertEqual(len(patch.get_controllers()), 12)
        self.assertEqual(patch.validate(), [])
        self.assertIn("ceiling_halos", uni.groups)
        self.assertIn("wall_blades", uni.groups)
        self.assertIn("sculpture", uni.groups)
        self.assertIn("floor_tracks", uni.groups)

    def test_preset_lookup_and_fuzzy_aliases(self) -> None:
        # Exact keys
        for key in ["concert_hall", "warehouse_rave", "festival_amphitheater", "art_gallery"]:
            u, p = get_preset_venue(key)
            self.assertIsNotNone(u)
            self.assertEqual(p.validate(), [])

        # Fuzzy aliases
        u1, _ = get_preset_venue("Rave")
        self.assertEqual(u1.name, "Warehouse Rave & Boiler Stage")

        u2, _ = get_preset_venue("festival")
        self.assertEqual(u2.name, "Outdoor Amphitheater & Lawn")

        u3, _ = get_preset_venue("art-gallery")
        self.assertEqual(u3.name, "Immersive Art Gallery & Studio")

        u4, _ = get_preset_venue("metro concert")
        self.assertEqual(u4.name, "Metro Concert Hall & Lounge")

        # Unknown raises KeyError
        with self.assertRaises(KeyError):
            get_preset_venue("nonexistent_preset_xyz")

    def test_list_preset_names_catalog(self) -> None:
        catalog = list_preset_names()
        self.assertEqual(len(catalog), 4)
        ids = [p["id"] for p in catalog]
        self.assertIn("concert_hall", ids)
        self.assertIn("warehouse_rave", ids)
        self.assertIn("festival_amphitheater", ids)
        self.assertIn("art_gallery", ids)
        for item in catalog:
            self.assertGreater(item["fixtures"], 0)
            self.assertGreater(item["total_pixels"], 0)
            self.assertGreater(item["controllers"], 0)
            self.assertGreater(len(item["groups"]), 0)

    def test_save_all_presets_and_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            res = save_all_preset_files(base_dir=td)
            self.assertEqual(len(res), 4)
            for pid, (u_path, p_path) in res.items():
                self.assertTrue(u_path.exists())
                self.assertTrue(p_path.exists())


if __name__ == "__main__":
    unittest.main()
