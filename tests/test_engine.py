"""Comprehensive unit tests for WLED Lighting Engine."""

import unittest
from wled_app.domain.channel import ChannelConfig, layout_channels
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig, ProtocolType
from wled_app.domain.frame import FrameBuffer
from wled_app.network.udp_client import MockUdpClient
from wled_app.patterns.base import Pattern, PatternConfig
from wled_engine.blend import BlendMode, blend_pixel
from wled_engine.compositor import LayerStack
from wled_engine.core import LightingEngine
from wled_engine.fleet import DeviceFleet
from wled_engine.layer import Layer


class SolidTestPattern(Pattern):
    """Test pattern filling buffer with solid color."""
    def __init__(self, color: Color) -> None:
        self.color = color

    @property
    def id(self) -> str:
        return f"solid_{self.color.to_hex()}"

    @property
    def name(self) -> str:
        return f"Solid {self.color.to_hex()}"

    @property
    def description(self) -> str:
        return "Test solid pattern"

    def render(self, tick: int, device: DeviceConfig, frame: FrameBuffer, config: PatternConfig) -> None:
        frame.fill(self.color)


class TestBlendOperators(unittest.TestCase):
    def test_alpha_blend(self) -> None:
        black = Color(0, 0, 0)
        white = Color(200, 100, 50)
        # 50% opacity
        blended = blend_pixel(black, white, 0.5, BlendMode.ALPHA_BLEND)
        self.assertEqual(blended, Color(100, 50, 25))

        # 0% opacity returns destination
        self.assertEqual(blend_pixel(black, white, 0.0, BlendMode.ALPHA_BLEND), black)

        # 100% opacity returns source
        self.assertEqual(blend_pixel(black, white, 1.0, BlendMode.ALPHA_BLEND), white)

    def test_additive_blend_clamping(self) -> None:
        c1 = Color(150, 100, 50)
        c2 = Color(150, 200, 220)
        # 150 + 150 = 300 -> clamped to 255
        blended = blend_pixel(c1, c2, 1.0, BlendMode.ADDITIVE)
        self.assertEqual(blended.r, 255)
        self.assertEqual(blended.g, 255)
        self.assertEqual(blended.b, 255)

    def test_multiply_blend(self) -> None:
        base = Color(200, 200, 200)
        half_filter = Color(128, 255, 0)  # 50% red, 100% green, 0% blue
        blended = blend_pixel(base, half_filter, 1.0, BlendMode.MULTIPLY)
        self.assertAlmostEqual(blended.r, 100, delta=2)
        self.assertEqual(blended.g, 200)
        self.assertEqual(blended.b, 0)

    def test_max_blend(self) -> None:
        base = Color(100, 200, 50)
        overlay = Color(150, 50, 250)
        blended = blend_pixel(base, overlay, 1.0, BlendMode.MAX)
        self.assertEqual(blended, Color(150, 200, 250))


class TestLayer(unittest.TestCase):
    def setUp(self) -> None:
        self.device = DeviceConfig.create(
            name="TestDev",
            ip="127.0.0.1",
            channel_lengths=[10, 10],
            protocol=ProtocolType.DDP,
        )

    def test_layer_index_bounds(self) -> None:
        # Valid: 0..9
        for i in range(10):
            Layer(index=i)

        with self.assertRaises(ValueError):
            Layer(index=-1)
        with self.assertRaises(ValueError):
            Layer(index=10)

    def test_opacity_tween(self) -> None:
        layer = Layer(index=0, opacity=0.0)
        layer.fade_to(1.0, duration_sec=1.0)

        # Midway at 0.5s
        layer.update(0.5)
        self.assertAlmostEqual(layer.opacity, 0.5, delta=0.05)

        # Complete at 1.0s
        layer.update(0.5)
        self.assertEqual(layer.opacity, 1.0)
        self.assertIsNone(layer._tween)

    def test_channel_masking(self) -> None:
        # Layer targeted ONLY to Channel 1 (indices 0..9)
        layer = Layer(
            index=1,
            pattern=SolidTestPattern(Color.red()),
            channel_ids={1},
            blend_mode=BlendMode.OVERWRITE,
        )

        out_frame = FrameBuffer(20)
        scratch_frame = FrameBuffer(20)

        layer.composite_into(tick=0, device=self.device, out_frame=out_frame, scratch_frame=scratch_frame)

        # First 10 LEDs (CH1) are Red
        for i in range(10):
            self.assertEqual(out_frame[i], Color.red())

        # Remaining 10 LEDs (CH2) are unaffected (Black)
        for i in range(10, 20):
            self.assertEqual(out_frame[i], Color.black())


class TestLayerStack(unittest.TestCase):
    def setUp(self) -> None:
        self.device = DeviceConfig.create(
            name="TestDev",
            ip="127.0.0.1",
            channel_lengths=[10],
            protocol=ProtocolType.DDP,
        )

    def test_layer_stack_indexing(self) -> None:
        stack = LayerStack()
        self.assertEqual(len(stack._layers), 10)

        layer3 = stack.get_layer(3)
        self.assertEqual(layer3.index, 3)

        with self.assertRaises(IndexError):
            stack.get_layer(10)
        with self.assertRaises(IndexError):
            stack.get_layer(-1)

    def test_multi_layer_compositing_order(self) -> None:
        stack = LayerStack()

        # Layer 0 (Bottom): Solid Red
        stack.set_layer(0, pattern=SolidTestPattern(Color.red()), opacity=1.0)

        # Layer 1 (Top): Solid Blue with 50% opacity (Alpha Blend)
        stack.set_layer(1, pattern=SolidTestPattern(Color.blue()), opacity=0.5, blend_mode=BlendMode.ALPHA_BLEND)

        out_frame = FrameBuffer(10)
        stack.composite(tick=0, dt=0.033, device=self.device, out_frame=out_frame)

        # 50% Red + 50% Blue = Purple (127, 0, 127)
        for i in range(10):
            pixel = out_frame[i]
            self.assertAlmostEqual(pixel.r, 127, delta=2)
            self.assertEqual(pixel.g, 0)
            self.assertAlmostEqual(pixel.b, 127, delta=2)

    def test_master_dimmer(self) -> None:
        stack = LayerStack()
        stack.set_layer(0, pattern=SolidTestPattern(Color(200, 100, 50)), opacity=1.0)
        stack.master_brightness = 0.5  # 50% master dimmer

        out_frame = FrameBuffer(10)
        stack.composite(tick=0, dt=0.033, device=self.device, out_frame=out_frame)

        for i in range(10):
            self.assertEqual(out_frame[i], Color(100, 50, 25))


class TestLightingEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.device = DeviceConfig.create(
            name="EngineDev",
            ip="127.0.0.1",
            channel_lengths=[20],
            protocol=ProtocolType.DDP,
        )

    def test_engine_single_step_and_fleet(self) -> None:
        mock_sender = MockUdpClient()
        engine = LightingEngine(target_fps=30.0, dry_run=True)
        engine.add_device(self.device, sender=mock_sender)

        # Configure Layer 0 with Green
        engine.layer(0).pattern = SolidTestPattern(Color.green())
        engine.layer(0).opacity = 1.0
        engine.layer(0).enabled = True

        engine.step()

        self.assertEqual(engine.current_tick, 1)
        self.assertEqual(len(mock_sender.sent_packets), 1)

        # Verify pixel payload is Green
        packet = mock_sender.sent_packets[0][2]
        payload = packet[10:]  # Skip 10-byte DDP header
        self.assertEqual(payload[:3], bytes((0, 255, 0)))

    def test_cue_snapshot_and_transition(self) -> None:
        engine = LightingEngine(dry_run=True)
        engine.add_device(self.device)

        # Scene 1: Layer 0 active, Layer 1 off
        engine.layer(0).opacity = 1.0
        engine.layer(1).opacity = 0.0
        engine.save_cue("Day")

        # Scene 2: Layer 0 off, Layer 1 active
        engine.layer(0).opacity = 0.0
        engine.layer(1).opacity = 1.0
        engine.save_cue("Night")

        # Reset both to 0 and transition to "Night"
        engine.layer(0).opacity = 0.0
        engine.layer(1).opacity = 0.0

        success = engine.transition_to_cue("Night", duration_sec=1.0)
        self.assertTrue(success)

        # Midway at 0.5s
        engine.step(custom_dt=0.5)
        self.assertAlmostEqual(engine.layer(1).opacity, 0.5, delta=0.05)


if __name__ == "__main__":
    unittest.main()
