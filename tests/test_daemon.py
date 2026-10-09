"""Unit tests for REST Daemon Adapter in wled_engine."""

import unittest
from wled_app.domain.device import DeviceConfig, ProtocolType
from wled_engine.adapters.rest_daemon import EngineDaemon, handle_rest_request
from wled_engine.blend import BlendMode
from wled_engine.core import LightingEngine
from wled_engine.events import EventRule


class TestRestDaemon(unittest.TestCase):
    def setUp(self) -> None:
        self.device = DeviceConfig.create(
            name="DaemonTestDev",
            ip="127.0.0.1",
            channel_lengths=[30, 20],
            protocol=ProtocolType.DDP,
        )
        self.engine = LightingEngine(dry_run=True, target_fps=30.0)
        self.engine.add_device(self.device)

    def tearDown(self) -> None:
        self.engine.close()

    def test_status_endpoint(self) -> None:
        status, data = handle_rest_request(self.engine, "GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(len(data["devices"]), 1)
        self.assertEqual(data["devices"][0]["name"], "DaemonTestDev")
        self.assertEqual(data["devices"][0]["total_leds"], 50)

    def test_get_all_layers(self) -> None:
        status, data = handle_rest_request(self.engine, "GET", "/api/layers")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 10)
        self.assertEqual(data[0]["index"], 0)
        self.assertEqual(data[9]["index"], 9)

    def test_get_single_layer(self) -> None:
        status, data = handle_rest_request(self.engine, "GET", "/api/layers/2")
        self.assertEqual(status, 200)
        self.assertEqual(data["index"], 2)

        # Out of bounds index
        status_err, data_err = handle_rest_request(self.engine, "GET", "/api/layers/15")
        self.assertEqual(status_err, 400)
        self.assertEqual(data_err["status"], "error")

    def test_update_layer_configuration(self) -> None:
        update_payload = {
            "pattern": "rainbow",
            "opacity": 0.75,
            "blend_mode": "ADDITIVE",
            "channels": [1],
            "speed": 2.0,
        }
        status, data = handle_rest_request(self.engine, "POST", "/api/layers/1", update_payload)
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["layer"]["pattern"], "rainbow")
        self.assertEqual(data["layer"]["opacity"], 0.75)
        self.assertEqual(data["layer"]["blend_mode"], "ADDITIVE")
        self.assertEqual(data["layer"]["channel_ids"], [1])

        # Verify against engine state
        layer1 = self.engine.layer(1)
        self.assertEqual(layer1.pattern.id, "rainbow")
        self.assertEqual(layer1.opacity, 0.75)
        self.assertEqual(layer1.blend_mode, BlendMode.ADDITIVE)
        self.assertEqual(layer1.channel_ids, {1})

    def test_layer_fade(self) -> None:
        status, data = handle_rest_request(self.engine, "POST", "/api/layers/1/fade", {"target_opacity": 0.2, "duration_sec": 1.5})
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["fading"])
        self.assertIsNotNone(self.engine.layer(1)._tween)

    def test_master_brightness(self) -> None:
        status, data = handle_rest_request(self.engine, "POST", "/api/master_brightness", {"brightness": 0.45})
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertAlmostEqual(self.engine.master_brightness, 0.45)

    def test_cues_and_transition(self) -> None:
        # Save cue
        status, data = handle_rest_request(self.engine, "POST", "/api/cues", {"name": "TestCue"})
        self.assertEqual(status, 200)
        self.assertEqual(data["cue_saved"], "TestCue")

        # Transition to cue
        status, data = handle_rest_request(self.engine, "POST", "/api/cues/TestCue/transition", {"duration_sec": 0.5})
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")

        # Transition to non-existent cue
        status_err, _ = handle_rest_request(self.engine, "POST", "/api/cues/NonExistent/transition", {"duration_sec": 0.5})
        self.assertEqual(status_err, 404)

    def test_events_endpoint(self) -> None:
        self.engine.events.add_rule(
            EventRule(event_name="door_trip", action="master_brightness", params={"brightness": 0.9})
        )

        status, data = handle_rest_request(self.engine, "POST", "/api/events", {"name": "door_trip"})
        self.assertEqual(status, 200)
        self.assertEqual(data["event"], "door_trip")
        self.assertIn("master_brightness", data["executed_actions"])
        self.assertAlmostEqual(self.engine.master_brightness, 0.9)

    def test_daemon_lifecycle(self) -> None:
        daemon = EngineDaemon(engine=self.engine, host="127.0.0.1", port=0)
        self.assertFalse(daemon.is_running)
        daemon.start()
        self.assertTrue(daemon.is_running)
        daemon.stop()
        self.assertFalse(daemon.is_running)


if __name__ == "__main__":
    unittest.main()
