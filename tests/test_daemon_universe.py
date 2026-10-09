"""Tests for REST daemon spatial universe, patch, and pattern endpoints."""

import unittest
from wled_engine.core import LightingEngine
from wled_engine.adapters.rest_daemon import handle_rest_request


class TestDaemonUniverse(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = LightingEngine(dry_run=True)

    def tearDown(self) -> None:
        self.engine.close()

    def test_universe_lifecycle_via_rest(self) -> None:
        # 1. Before loading, universe is None
        code, resp = handle_rest_request(self.engine, "GET", "/api/universe")
        self.assertEqual(code, 200)
        self.assertIsNone(resp["universe"])

        # 2. Load venue preset
        code, resp = handle_rest_request(self.engine, "POST", "/api/universe", {"preset": "venue"})
        self.assertEqual(code, 200)
        self.assertEqual(resp["status"], "ok")
        self.assertIn("fixtures", resp["universe"])
        self.assertEqual(len(resp["universe"]["fixtures"]), 28)

        # 3. GET /api/universe returns visualizer dict
        code, resp = handle_rest_request(self.engine, "GET", "/api/universe")
        self.assertEqual(code, 200)
        self.assertEqual(resp["universe"]["name"], "Metro Concert Hall & Lounge")
        self.assertEqual(resp["universe"]["total_pixels"], 5153)

        # 4. GET /api/universe/fixtures
        code, resp = handle_rest_request(self.engine, "GET", "/api/universe/fixtures")
        self.assertEqual(code, 200)
        self.assertEqual(len(resp["fixtures"]), 28)

        # 5. GET /api/universe/fixtures/{fixture_id}
        code, resp = handle_rest_request(self.engine, "GET", "/api/universe/fixtures/bulb_canopy_left")
        self.assertEqual(code, 200)
        self.assertEqual(resp["fixture"]["id"], "bulb_canopy_left")
        self.assertEqual(resp["fixture"]["type"], "bulb_string")

        # 6. GET /api/patch
        code, resp = handle_rest_request(self.engine, "GET", "/api/patch")
        self.assertEqual(code, 200)
        self.assertEqual(len(resp["controllers"]), 20)
        self.assertEqual(resp["validation"], [])

        # 7. POST /api/spatial/pattern
        code, resp = handle_rest_request(self.engine, "POST", "/api/spatial/pattern", {
            "pattern": "sweep",
            "angle": 45.0,
            "speed": 1.5,
        })
        self.assertEqual(code, 200)
        self.assertEqual(resp["spatial_pattern"], "sweep")
        self.assertIsNotNone(self.engine.spatial_pattern_func)

        # 8. Step engine frame tick
        frames = self.engine.step()
        self.assertIsNotNone(frames)

        # 9. GET /api/fleet/nodes
        code, resp = handle_rest_request(self.engine, "GET", "/api/fleet/nodes")
        self.assertEqual(code, 200)
        self.assertEqual(len(resp["nodes"]), 20)
        self.assertIn("wled_01", resp["nodes"])
        self.assertGreaterEqual(resp["nodes"]["wled_01"]["frames_sent"], 1)

        # 10. POST /api/sync
        code, resp = handle_rest_request(self.engine, "POST", "/api/sync")
        self.assertEqual(code, 200)
        self.assertEqual(resp["status"], "ok")
        self.assertTrue(resp["sync_emitted"])


if __name__ == "__main__":
    unittest.main()
