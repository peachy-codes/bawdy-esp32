"""Unit tests for VisualizerAdapter in wled_engine."""

import unittest
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig, ProtocolType
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.solid import SolidPattern
from wled_engine.adapters.visualizer_adapter import VisualizerAdapter
from wled_engine.core import LightingEngine


class TestVisualizerAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.device = DeviceConfig.create(
            name="VisDev",
            ip="127.0.0.1",
            channel_lengths=[10],
            protocol=ProtocolType.DDP,
        )
        self.engine = LightingEngine(dry_run=True)
        self.engine.add_device(self.device)
        self.adapter = VisualizerAdapter(self.engine)

    def tearDown(self) -> None:
        self.engine.close()

    def test_sink_receives_dispatched_frames(self) -> None:
        received: list[tuple[str, int]] = []

        def on_vis_frame(dev: DeviceConfig, fb: FrameBuffer, fps: float, tick: int) -> None:
            received.append((dev.id, tick))

        sink = self.adapter.add_sink(on_vis_frame)
        self.engine.step()
        self.engine.step()

        self.assertEqual(len(received), 2)
        self.assertEqual(received[0], (self.device.id, 0))
        self.assertEqual(received[1], (self.device.id, 1))

        # Test remove sink
        self.assertTrue(self.adapter.remove_sink(sink))
        self.engine.step()
        self.assertEqual(len(received), 2)

    def test_ascii_canvas_rendering(self) -> None:
        canvas = self.adapter.attach_ascii_canvas(self.device.id, max_strip_width=40, use_color=False)
        self.engine.set_layer_pattern(0, SolidPattern())
        frames = self.engine.step()

        frame = frames[self.device.id]
        rendered = self.adapter.render_ascii(self.device, frame)
        self.assertIn("CH1", rendered)


if __name__ == "__main__":
    unittest.main()
