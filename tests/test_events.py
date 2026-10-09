"""Unit tests for EventBus and reactive trigger rules in wled_engine."""

import unittest
from wled_app.domain.device import DeviceConfig, ProtocolType
from wled_engine.blend import BlendMode
from wled_engine.core import LightingEngine
from wled_engine.events import Event, EventBus, EventRule


class TestEventBus(unittest.TestCase):
    def setUp(self) -> None:
        self.device = DeviceConfig.create(
            name="EventDev",
            ip="127.0.0.1",
            channel_lengths=[30],
            protocol=ProtocolType.DDP,
        )
        self.engine = LightingEngine(dry_run=True)
        self.engine.add_device(self.device)

    def tearDown(self) -> None:
        self.engine.close()

    def test_custom_handler_subscription(self) -> None:
        bus = self.engine.events
        received_events: list[Event] = []

        def on_alert(evt: Event, eng: LightingEngine) -> None:
            received_events.append(evt)

        bus.subscribe("alert", on_alert)
        bus.publish("alert", severity="high")

        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].name, "alert")
        self.assertEqual(received_events[0].data["severity"], "high")

        # Unsubscribe
        self.assertTrue(bus.unsubscribe("alert", on_alert))
        bus.publish("alert")
        self.assertEqual(len(received_events), 1)

    def test_wildcard_subscription(self) -> None:
        bus = self.engine.events
        caught: list[str] = []

        def on_all(evt: Event, eng: LightingEngine) -> None:
            caught.append(evt.name)

        bus.subscribe("*", on_all)
        bus.publish("door_opened")
        bus.publish("sun_set")

        self.assertEqual(caught, ["door_opened", "sun_set"])

    def test_reactive_rule_fade_layer(self) -> None:
        bus = self.engine.events
        # Configure Layer 3 starting with opacity 0.0
        self.engine.layer(3).opacity = 0.0

        # Rule: When 'motion' happens, fade Layer 3 to 1.0
        rule = EventRule(
            event_name="motion",
            action="fade_layer",
            params={"layer": 3, "target_opacity": 1.0, "duration_sec": 0.5},
        )
        bus.add_rule(rule)

        actions = bus.publish("motion")
        self.assertIn("fade_layer", actions)
        self.assertIsNotNone(self.engine.layer(3)._tween)

    def test_reactive_rule_set_opacity_and_enabled(self) -> None:
        bus = self.engine.events
        self.engine.layer(5).opacity = 0.2
        self.engine.layer(5).enabled = True

        bus.add_rule(EventRule("disable_l5", "set_layer_enabled", {"layer": 5, "enabled": False}))
        bus.add_rule(EventRule("mute_l5", "set_layer_opacity", {"layer": 5, "opacity": 0.0}))

        bus.publish("disable_l5")
        self.assertFalse(self.engine.layer(5).enabled)

        bus.publish("mute_l5")
        self.assertEqual(self.engine.layer(5).opacity, 0.0)

    def test_reactive_rule_master_brightness(self) -> None:
        bus = self.engine.events
        bus.add_rule(EventRule("dim_all", "master_brightness", {"brightness": 0.25}))
        bus.publish("dim_all")
        self.assertAlmostEqual(self.engine.master_brightness, 0.25)

    def test_reactive_rule_cue_transition(self) -> None:
        # Save a cue
        self.engine.layer(0).opacity = 0.8
        self.engine.save_cue("Night")

        # Change opacity
        self.engine.layer(0).opacity = 0.1

        # Publish rule triggering transition
        bus = self.engine.events
        bus.add_rule(EventRule("goodnight", "transition_cue", {"cue": "Night", "duration_sec": 1.0}))
        bus.publish("goodnight")

        # Layer 0 should be tweening back to 0.8
        self.assertIsNotNone(self.engine.layer(0)._tween)
        self.assertEqual(self.engine.layer(0)._tween.target_opacity, 0.8)


if __name__ == "__main__":
    unittest.main()
