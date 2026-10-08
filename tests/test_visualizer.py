"""Unit tests for ASCII terminal visualizer."""

import unittest
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig, ProtocolType
from wled_app.domain.frame import FrameBuffer
from wled_app.visualizer.ascii_canvas import AsciiCanvas


class TestAsciiCanvas(unittest.TestCase):
    def setUp(self) -> None:
        self.device = DeviceConfig.create(
            name="VisualizerTest",
            ip="192.168.1.88",
            channel_lengths=[20, 10],
            protocol=ProtocolType.DDP,
        )
        self.frame = FrameBuffer(self.device.total_leds)
        self.canvas = AsciiCanvas(max_strip_width=20, use_color=False)

    def test_resample_peak_preservation(self) -> None:
        # A single bright red dot in an otherwise dark segment
        pixels = [Color.black()] * 9 + [Color.red()]
        resampled = self.canvas._resample_pixels(pixels, 2)
        self.assertEqual(len(resampled), 2)
        # The peak red dot should be preserved in the second bucket rather than diluted into black
        self.assertEqual(resampled[1], Color.red())

    def test_render_monochrome(self) -> None:
        ch1 = self.device.channels[0]
        self.frame.fill_channel(ch1, Color.white())

        text = self.canvas.render(self.device, self.frame, title="Test Frame")
        self.assertIn("VisualizerTest", text)
        self.assertIn("CH1", text)
        self.assertIn("[ 20 LEDs]", text)
        self.assertIn("Total LEDs: 30", text)

    def test_render_color_mode(self) -> None:
        color_canvas = AsciiCanvas(max_strip_width=15, use_color=True)
        ch1 = self.device.channels[0]
        self.frame.fill_channel(ch1, Color.red())

        text = color_canvas.render(self.device, self.frame)
        # Should contain either 24-bit Truecolor red or xterm 256-color red (code 196)
        has_color = ("\033[38;2;255;0;0m" in text) or ("\033[38;5;196m" in text)
        self.assertTrue(has_color, "Rendered text should contain ANSI red escape sequence")


if __name__ == "__main__":
    unittest.main()
