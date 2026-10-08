"""Unit tests for pattern algorithms and color palettes."""

import unittest
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig, ProtocolType
from wled_app.domain.frame import FrameBuffer
from wled_app.domain.palette import PALETTES, get_palette, list_palettes
from wled_app.patterns.base import PatternConfig
from wled_app.patterns.blink import BlinkPattern
from wled_app.patterns.chase import ChasePattern
from wled_app.patterns.color_wipe import ColorWipePattern
from wled_app.patterns.cylon import CylonPattern
from wled_app.patterns.fire import FirePattern
from wled_app.patterns.gradient import GradientPattern
from wled_app.patterns.meteor import MeteorPattern
from wled_app.patterns.rainbow import RainbowPattern
from wled_app.patterns.solid import SolidPattern
from wled_app.patterns.twinkle import TwinklePattern
from wled_app.patterns.wave import WavePattern
from wled_app.patterns.registry import get_pattern, list_patterns


class TestPatterns(unittest.TestCase):
    def setUp(self) -> None:
        self.device = DeviceConfig.create(
            name="TestDevice",
            ip="192.168.1.50",
            channel_lengths=[30, 20],
            protocol=ProtocolType.DDP,
        )
        self.frame = FrameBuffer(self.device.total_leds)

    def test_list_and_get_all_patterns(self) -> None:
        patterns = list_patterns()
        self.assertEqual(len(patterns), 11)

        expected_ids = [
            "rainbow", "chase", "fire", "meteor", "cylon",
            "twinkle", "wave", "gradient", "blink", "wipe", "solid",
        ]
        for pid in expected_ids:
            pat = get_pattern(pid)
            self.assertEqual(pat.id, pid)

        with self.assertRaises(ValueError):
            get_pattern("non_existent")

    def test_palette_sampling(self) -> None:
        palettes = list_palettes()
        self.assertGreaterEqual(len(palettes), 5)

        cyber = get_palette("cyberpunk")
        c_start = cyber.sample(0.0)
        self.assertEqual(c_start, Color(0, 245, 255))
        c_mid = cyber.sample(0.5)
        self.assertIsInstance(c_mid, Color)

    def test_chase_pattern(self) -> None:
        chase = ChasePattern()
        config = PatternConfig(
            speed=1.0,
            primary_color=Color.red(),
            secondary_color=Color.black(),
            sync_channels=True,
            extra={"tail_length": 3},
        )
        chase.render(tick=0, device=self.device, frame=self.frame, config=config)
        ch1_pixels = self.frame.get_channel_pixels(self.device.channels[0])
        self.assertEqual(ch1_pixels[0], Color.red())

    def test_rainbow_pattern(self) -> None:
        rainbow = RainbowPattern()
        config = PatternConfig(speed=1.0, sync_channels=True)
        rainbow.render(tick=5, device=self.device, frame=self.frame, config=config)
        self.assertFalse(all(p.is_black() for p in self.frame.pixels))
        self.assertNotEqual(self.frame[0], self.frame[10])

    def test_fire_pattern(self) -> None:
        fire = FirePattern()
        config = PatternConfig(speed=1.0, extra={"sparking": 1.0})
        fire.render(tick=0, device=self.device, frame=self.frame, config=config)
        fire.render(tick=1, device=self.device, frame=self.frame, config=config)
        # Should have generated warm fire colors
        ch1_pixels = self.frame.get_channel_pixels(self.device.channels[0])
        self.assertFalse(all(p.is_black() for p in ch1_pixels))

    def test_meteor_pattern(self) -> None:
        meteor = MeteorPattern()
        config = PatternConfig(speed=1.0, primary_color=Color.blue(), extra={"meteor_size": 2})
        meteor.render(tick=2, device=self.device, frame=self.frame, config=config)
        self.assertFalse(all(p.is_black() for p in self.frame.pixels))

    def test_cylon_pattern(self) -> None:
        cylon = CylonPattern()
        config = PatternConfig(speed=1.0, primary_color=Color.red())
        cylon.render(tick=0, device=self.device, frame=self.frame, config=config)
        ch1_pixels = self.frame.get_channel_pixels(self.device.channels[0])
        self.assertEqual(ch1_pixels[0], Color.red())

    def test_twinkle_pattern(self) -> None:
        twinkle = TwinklePattern()
        config = PatternConfig(speed=1.0, primary_color=Color.yellow())
        twinkle.render(tick=10, device=self.device, frame=self.frame, config=config)
        self.assertFalse(all(p.is_black() for p in self.frame.pixels))

    def test_wave_pattern(self) -> None:
        wave = WavePattern()
        config = PatternConfig(speed=1.0)
        wave.render(tick=3, device=self.device, frame=self.frame, config=config)
        self.assertFalse(all(p.is_black() for p in self.frame.pixels))

    def test_gradient_pattern(self) -> None:
        gradient = GradientPattern()
        config = PatternConfig(speed=1.0, extra={"palette": "cyberpunk"})
        gradient.render(tick=0, device=self.device, frame=self.frame, config=config)
        self.assertFalse(all(p.is_black() for p in self.frame.pixels))

    def test_wipe_pattern(self) -> None:
        wipe = ColorWipePattern()
        config = PatternConfig(speed=1.0, primary_color=Color.green(), secondary_color=Color.black())
        wipe.render(tick=5, device=self.device, frame=self.frame, config=config)
        ch1_pixels = self.frame.get_channel_pixels(self.device.channels[0])
        self.assertEqual(ch1_pixels[0], Color.green())
        self.assertEqual(ch1_pixels[5], Color.green())
        self.assertEqual(ch1_pixels[6], Color.black())

    def test_solid_pattern(self) -> None:
        solid = SolidPattern()
        config = PatternConfig(primary_color=Color.purple())
        solid.render(tick=0, device=self.device, frame=self.frame, config=config)
        self.assertTrue(all(p == Color.purple() for p in self.frame.pixels))


if __name__ == "__main__":
    unittest.main()
