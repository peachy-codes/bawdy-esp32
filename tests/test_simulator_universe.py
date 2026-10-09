"""Unit and integration tests for MultiNodeSimulatorRunner and Spatial Universe visualizer."""

import asyncio
import json
import unittest
from pathlib import Path

from wled_engine.patch.patch_table import PatchTable
from wled_engine.spatial.universe import SpatialUniverse
from wled_engine.spatial.venue import create_demo_venue
from wled_simulator.multi_node_runner import MultiNodeSimulatorRunner


class TestMultiNodeSimulator(unittest.TestCase):
    def setUp(self) -> None:
        self.universe, self.patch = create_demo_venue()

    def test_multi_node_initialization(self) -> None:
        """Verify runner creates state machines for all 20 controllers with proper channel lengths."""
        runner = MultiNodeSimulatorRunner(
            universe=self.universe,
            patch_table=self.patch,
            base_port=14048,
            web_port=18080,
        )

        self.assertEqual(len(runner._state_machines), 20)
        self.assertIn("wled_01", runner._state_machines)
        self.assertIn("wled_20", runner._state_machines)

        # Check wled_01 has 3 channels configured (600 + 200 = 800 LEDs)
        sm1 = runner._state_machines["wled_01"]
        self.assertEqual(len(sm1.channels), 3)
        self.assertEqual(sm1.channels[0].length, 300)
        self.assertEqual(sm1.channels[1].length, 300)
        self.assertEqual(sm1.channels[2].length, 200)
        self.assertEqual(sm1.total_leds, 800)

        # Total pixels in universe
        self.assertEqual(self.universe.total_pixels, 5153)

    def test_universe_visualizer_metadata_payload(self) -> None:
        """Verify WebSocket initial config dictionary format."""
        meta = self.universe.to_visualizer_dict()
        self.assertEqual(meta["name"], "Metro Concert Hall & Lounge")
        self.assertEqual(meta["total_pixels"], 5153)
        self.assertEqual(len(meta["fixtures"]), 28)

        # Check groups
        groups = meta["groups"]
        self.assertIn("trusses", groups)
        self.assertIn("festoon", groups)
        self.assertIn("panels", groups)
        self.assertIn("lamps", groups)
        self.assertIn("perimeter", groups)

        # Check fixture details
        first_fix = meta["fixtures"][0]
        self.assertEqual(first_fix["id"], "truss_roof_front")
        self.assertEqual(first_fix["pixel_count"], 600)
        self.assertEqual(first_fix["pixel_offset"], 0)
        self.assertEqual(len(first_fix["points"]), 600)

    def test_direct_fixture_colors_injection(self) -> None:
        """Verify direct software color injection into universe runner."""
        runner = MultiNodeSimulatorRunner(
            universe=self.universe,
            patch_table=self.patch,
            base_port=15048,
            web_port=19080,
        )

        from wled_app.domain.color import Color
        fixture_colors = {
            "truss_leg_front_left": [Color(255, 0, 0)] * 200,
        }

        # Should pack and not raise error
        runner.inject_fixture_colors(fixture_colors)


if __name__ == "__main__":
    unittest.main()
