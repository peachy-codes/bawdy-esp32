"""Unit tests for WLED UDP protocol encoders using Python unittest."""

import struct
import unittest
from wled_app.domain.color import Color
from wled_app.domain.device import ProtocolType
from wled_app.domain.frame import FrameBuffer
from wled_app.protocols.ddp import DdpEmitter
from wled_app.protocols.drgb import DnrgbEmitter, DrgbEmitter
from wled_app.protocols.registry import get_emitter
from wled_app.protocols.warls import WarlsEmitter


class TestDdpEmitter(unittest.TestCase):
    def test_ddp_header_structure_and_payload(self) -> None:
        emitter = DdpEmitter()
        fb = FrameBuffer(10)
        fb[0] = Color.red()
        fb[9] = Color.blue()

        packets = emitter.encode_frame(fb)
        self.assertEqual(len(packets), 1)
        pkt = packets[0]

        # Total size: 10 byte header + 10 * 3 bytes RGB = 40 bytes
        self.assertEqual(len(pkt), 40)

        header = pkt[:10]
        flags1, seq, data_type, dest_id, offset, data_len = struct.unpack(">BBBB I H", header)

        self.assertEqual(flags1, 0x41)  # DDP v1 + Push flag
        self.assertTrue(1 <= seq <= 15)
        self.assertEqual(data_type, 1)  # RGB
        self.assertEqual(dest_id, 1)  # Default display
        self.assertEqual(offset, 0)
        self.assertEqual(data_len, 30)

        # Check payload bytes
        payload = pkt[10:]
        self.assertEqual(payload[0:3], bytes((255, 0, 0)))  # pixel 0
        self.assertEqual(payload[27:30], bytes((0, 0, 255)))  # pixel 9

    def test_ddp_multi_packet_chunking(self) -> None:
        # 600 LEDs with chunk size 480 -> 2 packets
        emitter = DdpEmitter(max_leds_per_packet=480)
        fb = FrameBuffer(600)
        packets = emitter.encode_frame(fb)

        self.assertEqual(len(packets), 2)

        # Packet 1
        flags1_p1, _, _, _, offset_p1, len_p1 = struct.unpack(">BBBB I H", packets[0][:10])
        self.assertEqual(flags1_p1, 0x40)  # No push flag on intermediate packet
        self.assertEqual(offset_p1, 0)
        self.assertEqual(len_p1, 480 * 3)

        # Packet 2
        flags1_p2, _, _, _, offset_p2, len_p2 = struct.unpack(">BBBB I H", packets[1][:10])
        self.assertEqual(flags1_p2, 0x41)  # Push flag on final packet
        self.assertEqual(offset_p2, 480 * 3)
        self.assertEqual(len_p2, 120 * 3)

    def test_ddp_encode_raw_bytes(self) -> None:
        emitter = DdpEmitter(max_leds_per_packet=480)
        # 600 LEDs * 3 = 1800 raw bytes
        raw_rgb = bytearray(600 * 3)
        raw_rgb[0] = 255  # First red
        raw_rgb[1799] = 200  # Last blue

        packets = emitter.encode_raw_bytes(raw_rgb)
        self.assertEqual(len(packets), 2)

        # Check packet 1
        flags1_p1, _, _, _, offset_p1, len_p1 = struct.unpack(">BBBB I H", packets[0][:10])
        self.assertEqual(flags1_p1, 0x40)
        self.assertEqual(offset_p1, 0)
        self.assertEqual(len_p1, 480 * 3)
        self.assertEqual(packets[0][10], 255)

        # Check packet 2
        flags1_p2, _, _, _, offset_p2, len_p2 = struct.unpack(">BBBB I H", packets[1][:10])
        self.assertEqual(flags1_p2, 0x41)  # Push flag set on last chunk
        self.assertEqual(offset_p2, 480 * 3)
        self.assertEqual(len_p2, 120 * 3)
        self.assertEqual(packets[1][-1], 200)


class TestDrgbEmitter(unittest.TestCase):
    def test_drgb_header_and_data(self) -> None:
        emitter = DrgbEmitter()
        fb = FrameBuffer(5)
        fb[0] = Color.green()

        packets = emitter.encode_frame(fb, timeout_sec=3)
        self.assertEqual(len(packets), 1)
        pkt = packets[0]

        # 2 bytes header + 15 bytes RGB = 17 bytes
        self.assertEqual(len(pkt), 17)
        self.assertEqual(pkt[0], 2)  # Protocol ID 2 (DRGB)
        self.assertEqual(pkt[1], 3)  # Timeout
        self.assertEqual(pkt[2:5], bytes((0, 255, 0)))  # pixel 0 green


class TestDnrgbEmitter(unittest.TestCase):
    def test_dnrgb_offsets_and_chunking(self) -> None:
        emitter = DnrgbEmitter(max_leds_per_packet=100)
        fb = FrameBuffer(150)
        packets = emitter.encode_frame(fb, timeout_sec=2)

        self.assertEqual(len(packets), 2)

        # Packet 1
        proto1, timeout1, start1 = struct.unpack(">BBH", packets[0][:4])
        self.assertEqual(proto1, 4)  # DNRGB
        self.assertEqual(timeout1, 2)
        self.assertEqual(start1, 0)
        self.assertEqual(len(packets[0]), 4 + 100 * 3)

        # Packet 2
        proto2, timeout2, start2 = struct.unpack(">BBH", packets[1][:4])
        self.assertEqual(proto2, 4)
        self.assertEqual(timeout2, 2)
        self.assertEqual(start2, 100)
        self.assertEqual(len(packets[1]), 4 + 50 * 3)


class TestWarlsEmitter(unittest.TestCase):
    def test_warls_indexed_payload(self) -> None:
        emitter = WarlsEmitter()
        fb = FrameBuffer(3)
        fb[0] = Color.red()
        fb[1] = Color.green()
        fb[2] = Color.blue()

        packets = emitter.encode_frame(fb, timeout_sec=5)
        self.assertEqual(len(packets), 1)
        pkt = packets[0]

        # 2 bytes header + 3 * 4 bytes = 14 bytes
        self.assertEqual(len(pkt), 14)
        self.assertEqual(pkt[0], 1)  # Protocol ID 1 (WARLS)
        self.assertEqual(pkt[1], 5)  # Timeout

        # Pixel 0: index 0, 255, 0, 0
        self.assertEqual(pkt[2:6], bytes((0, 255, 0, 0)))
        # Pixel 1: index 1, 0, 255, 0
        self.assertEqual(pkt[6:10], bytes((1, 0, 255, 0)))
        # Pixel 2: index 2, 0, 0, 255
        self.assertEqual(pkt[10:14], bytes((2, 0, 0, 255)))


class TestRegistry(unittest.TestCase):
    def test_get_emitter_resolves_all(self) -> None:
        self.assertIsInstance(get_emitter(ProtocolType.DDP), DdpEmitter)
        self.assertIsInstance(get_emitter(ProtocolType.DRGB), DrgbEmitter)
        self.assertIsInstance(get_emitter(ProtocolType.DNRGB), DnrgbEmitter)
        self.assertIsInstance(get_emitter(ProtocolType.WARLS), WarlsEmitter)
        self.assertIsInstance(get_emitter("ddp"), DdpEmitter)


if __name__ == "__main__":
    unittest.main()
