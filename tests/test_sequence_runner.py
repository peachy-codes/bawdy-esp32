"""Tests for the server-side SequenceRunner and REST daemon sequence endpoints."""

from __future__ import annotations
import unittest
from wled_engine.core import LightingEngine
from wled_engine.adapters.rest_daemon import handle_rest_request


class TestSequenceRunner(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = LightingEngine(target_fps=30.0, dry_run=True)
        self.seq_data = {
            "name": "Test Show",
            "loop_mode": "infinite",
            "time_dilation": 1.0,
            "steps": [
                {
                    "id": "s1",
                    "name": "Intro Wash",
                    "target_layer": 0,
                    "start_time_sec": 0.0,
                    "duration_sec": 5.0,
                    "stop_time_sec": 5.0,
                    "pattern_id": "wave",
                    "target_opacity": 1.0,
                    "transition_sec": 1.0,
                    "fade_out_sec": 1.0,
                },
                {
                    "id": "s2",
                    "name": "Mid Overlay",
                    "target_layer": 1,
                    "start_time_sec": 2.0,
                    "duration_sec": 4.0,
                    "stop_time_sec": 6.0,
                    "pattern_id": "chase",
                    "target_opacity": 0.8,
                    "transition_sec": 0.5,
                    "fade_out_sec": 0.5,
                },
            ],
        }

    def tearDown(self) -> None:
        self.engine.close()

    def test_sequence_playback_and_stepping(self) -> None:
        self.engine.sequence.play(self.seq_data)
        self.assertTrue(self.engine.sequence.is_playing)
        self.assertFalse(self.engine.sequence.is_paused)

        # Initial evaluation at t=0
        self.assertIn("s1", self.engine.sequence.active_cue_ids)
        self.assertNotIn("s2", self.engine.sequence.active_cue_ids)
        self.assertTrue(self.engine.layer(0).enabled)
        self.assertFalse(self.engine.layer(1).enabled)

        # Advance 2.5 seconds (at t=2.5: both s1 and s2 active)
        self.engine.step(custom_dt=2.5, tick=1)
        self.assertIn("s1", self.engine.sequence.active_cue_ids)
        self.assertIn("s2", self.engine.sequence.active_cue_ids)
        self.assertTrue(self.engine.layer(0).enabled)
        self.assertTrue(self.engine.layer(1).enabled)

        # Advance another 3.0 seconds (t=5.5: s1 ended, s2 active)
        self.engine.step(custom_dt=3.0, tick=2)
        self.assertNotIn("s1", self.engine.sequence.active_cue_ids)
        self.assertIn("s2", self.engine.sequence.active_cue_ids)
        self.assertFalse(self.engine.layer(0).enabled)
        self.assertTrue(self.engine.layer(1).enabled)

    def test_smooth_seeking(self) -> None:
        self.engine.sequence.load_sequence(self.seq_data)
        self.engine.sequence.seek(3.0)
        status = self.engine.sequence.get_status()
        self.assertEqual(status["elapsed_time"], 3.0)
        self.assertEqual(status["active_cues"], ["s1", "s2"])

        # Layers are rendered immediately on seek without needing play
        self.assertTrue(self.engine.layer(0).enabled)
        self.assertTrue(self.engine.layer(1).enabled)

    def test_atomic_blackout(self) -> None:
        self.engine.sequence.play(self.seq_data)
        self.engine.step(custom_dt=2.0)
        self.assertTrue(self.engine.layer(0).enabled)

        self.engine.blackout()
        self.assertFalse(self.engine.sequence.is_playing)
        for i in range(10):
            self.assertFalse(self.engine.layer(i).enabled)
            self.assertEqual(self.engine.layer(i).opacity, 0.0)

    def test_rest_capabilities_and_sequence_endpoints(self) -> None:
        # GET /api/capabilities
        code, resp = handle_rest_request(self.engine, "GET", "/api/capabilities")
        self.assertEqual(code, 200)
        self.assertIn("patterns", resp)
        self.assertIn("palettes", resp)
        self.assertIn("wave", resp["patterns"])
        self.assertIn("fire", resp["palettes"])

        # POST /api/sequence/play
        code, resp = handle_rest_request(self.engine, "POST", "/api/sequence/play", {"sequence": self.seq_data})
        self.assertEqual(code, 200)
        self.assertTrue(resp["playing"])

        # GET /api/sequence/status
        code, resp = handle_rest_request(self.engine, "GET", "/api/sequence/status")
        self.assertEqual(code, 200)
        self.assertTrue(resp["playing"])

        # POST /api/sequence/seek
        code, resp = handle_rest_request(self.engine, "POST", "/api/sequence/seek", {"time": 2.5})
        self.assertEqual(code, 200)
        self.assertEqual(resp["seek"], 2.5)

        # POST /api/sequence/pause
        code, resp = handle_rest_request(self.engine, "POST", "/api/sequence/pause")
        self.assertEqual(code, 200)
        self.assertTrue(resp["paused"])

        # POST /api/blackout
        code, resp = handle_rest_request(self.engine, "POST", "/api/blackout")
        self.assertEqual(code, 200)
        self.assertTrue(resp["blackout"])


if __name__ == "__main__":
    unittest.main()
