"""Unit tests for domain models using Python unittest."""

import unittest
from wled_app.domain.channel import ChannelConfig, layout_channels
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig, ProtocolType, validate_ip_or_host
from wled_app.domain.frame import FrameBuffer


class TestColor(unittest.TestCase):
    def test_color_creation_and_bounds(self) -> None:
        c = Color(10, 20, 30)
        self.assertEqual(c.r, 10)
        self.assertEqual(c.g, 20)
        self.assertEqual(c.b, 30)
        self.assertEqual(c.to_bytes(), bytes((10, 20, 30)))
        self.assertEqual(c.to_hex(), "#0A141E")

        with self.assertRaises(ValueError):
            Color(300, 0, 0)
        with self.assertRaises(ValueError):
            Color(0, -1, 0)

    def test_color_factory_clamp(self) -> None:
        c = Color.from_rgb(300, -50, 128)
        self.assertEqual(c.r, 255)
        self.assertEqual(c.g, 0)
        self.assertEqual(c.b, 128)

    def test_from_hex(self) -> None:
        self.assertEqual(Color.from_hex("#FF8800"), Color(255, 136, 0))
        self.assertEqual(Color.from_hex("00FF00"), Color(0, 255, 0))
        self.assertEqual(Color.from_hex("F00"), Color(255, 0, 0))

        with self.assertRaises(ValueError):
            Color.from_hex("invalid")

    def test_from_hsv(self) -> None:
        red = Color.from_hsv(0.0, 1.0, 1.0)
        self.assertEqual((red.r, red.g, red.b), (255, 0, 0))

        green = Color.from_hsv(1 / 3, 1.0, 1.0)
        self.assertEqual((green.r, green.g, green.b), (0, 255, 0))

        blue = Color.from_hsv(2 / 3, 1.0, 1.0)
        self.assertEqual((blue.r, blue.g, blue.b), (0, 0, 255))

    def test_lerp_and_dim(self) -> None:
        c1 = Color(0, 0, 0)
        c2 = Color(100, 200, 50)
        mid = c1.lerp(c2, 0.5)
        self.assertEqual(mid, Color(50, 100, 25))

        dimmed = c2.dim(0.1)
        self.assertEqual(dimmed, Color(10, 20, 5))


class TestChannelConfig(unittest.TestCase):
    def test_channel_layout(self) -> None:
        specs = [
            (1, 60, "Front Left"),
            (2, 30, "Front Right"),
            (3, 144, "Rear Strip"),
            (4, 0, "Unused"),
        ]
        channels = layout_channels(specs)
        self.assertEqual(len(channels), 4)

        ch1, ch2, ch3, ch4 = channels
        self.assertEqual((ch1.start_index, ch1.length, ch1.end_index), (0, 60, 60))
        self.assertEqual((ch2.start_index, ch2.length, ch2.end_index), (60, 30, 90))
        self.assertEqual((ch3.start_index, ch3.length, ch3.end_index), (90, 144, 234))
        self.assertEqual((ch4.start_index, ch4.length, ch4.is_active), (234, 0, False))

    def test_serialization(self) -> None:
        ch = ChannelConfig(1, 60, 0, "Strip 1")
        d = ch.to_dict()
        self.assertEqual(d["channel_id"], 1)
        self.assertEqual(d["length"], 60)
        restored = ChannelConfig.from_dict(d)
        self.assertEqual(restored, ch)


class TestDeviceConfig(unittest.TestCase):
    def test_device_validation_and_creation(self) -> None:
        dev = DeviceConfig.create(
            name="Test Controller",
            ip="192.168.1.100",
            channel_lengths=[60, 30, 0, 0],
            protocol=ProtocolType.DDP,
        )
        self.assertEqual(dev.total_leds, 90)
        self.assertEqual(len(dev.active_channels), 2)
        self.assertEqual(dev.port, 4048)
        self.assertEqual(dev.ip, "192.168.1.100")

    def test_invalid_ip_raises(self) -> None:
        with self.assertRaises(ValueError):
            validate_ip_or_host("999.999.999.999")
        with self.assertRaises(ValueError):
            validate_ip_or_host("")

    def test_serialization_roundtrip(self) -> None:
        channels = layout_channels([(1, 60), (2, 30)])
        dev = DeviceConfig(
            id="dev-test",
            name="Athom-LivingRoom",
            ip="192.168.1.150",
            port=4048,
            protocol=ProtocolType.DDP,
            channels=channels,
            description="Athom Ethernet ESP32 WLED Controller",
        )
        d = dev.to_dict()
        restored = DeviceConfig.from_dict(d)
        self.assertEqual(restored.id, dev.id)
        self.assertEqual(restored.name, dev.name)
        self.assertEqual(restored.ip, dev.ip)
        self.assertEqual(restored.port, dev.port)
        self.assertEqual(restored.protocol, dev.protocol)
        self.assertEqual(restored.total_leds, dev.total_leds)
        self.assertEqual(len(restored.channels), len(dev.channels))

    def test_device_update(self) -> None:
        dev = DeviceConfig.create(
            name="Original-Name",
            ip="192.168.1.100",
            channel_lengths=[60, 30],
            protocol=ProtocolType.DDP,
            description="Initial description",
        )
        orig_id = dev.id

        new_channels = layout_channels([(1, 120), (2, 60)])
        updated = dev.update(
            name="Renamed-Controller",
            ip="192.168.1.200",
            port=21324,
            protocol=ProtocolType.DRGB,
            channels=new_channels,
            description="Updated notes",
        )

        # ID must remain identical
        self.assertEqual(updated.id, orig_id)
        self.assertEqual(updated.name, "Renamed-Controller")
        self.assertEqual(updated.ip, "192.168.1.200")
        self.assertEqual(updated.port, 21324)
        self.assertEqual(updated.protocol, ProtocolType.DRGB)
        self.assertEqual(updated.total_leds, 180)
        self.assertEqual(updated.description, "Updated notes")

        # Partial update leaves untouched fields unchanged
        partial = updated.update(name="Partial-Name")
        self.assertEqual(partial.id, orig_id)
        self.assertEqual(partial.name, "Partial-Name")
        self.assertEqual(partial.ip, "192.168.1.200")
        self.assertEqual(partial.total_leds, 180)


class TestFrameBuffer(unittest.TestCase):
    def test_frame_buffer_channel_operations(self) -> None:
        channels = layout_channels([
            (1, 60, "Front Left"),
            (2, 30, "Front Right"),
            (3, 144, "Rear Strip"),
            (4, 0, "Unused"),
        ])
        fb = FrameBuffer(234)
        ch1, ch2, ch3, ch4 = channels

        # Fill channel 1 with RED
        fb.fill_channel(ch1, Color.red())
        # Fill channel 2 with BLUE
        fb.fill_channel(ch2, Color.blue())

        ch1_pixels = fb.get_channel_pixels(ch1)
        self.assertEqual(len(ch1_pixels), 60)
        self.assertTrue(all(p == Color.red() for p in ch1_pixels))

        ch2_pixels = fb.get_channel_pixels(ch2)
        self.assertEqual(len(ch2_pixels), 30)
        self.assertTrue(all(p == Color.blue() for p in ch2_pixels))

        ch3_pixels = fb.get_channel_pixels(ch3)
        self.assertEqual(len(ch3_pixels), 144)
        self.assertTrue(all(p == Color.black() for p in ch3_pixels))

        raw = fb.to_rgb_bytes()
        self.assertEqual(len(raw), 234 * 3)
        # First 60 leds are red: 255, 0, 0
        self.assertEqual(raw[0:3], bytes((255, 0, 0)))
        self.assertEqual(raw[59 * 3 : 60 * 3], bytes((255, 0, 0)))
        # Next 30 leds are blue: 0, 0, 255
        self.assertEqual(raw[60 * 3 : 60 * 3 + 3], bytes((0, 0, 255)))


if __name__ == "__main__":
    unittest.main()
