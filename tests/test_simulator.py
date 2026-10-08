"""Unit tests for standalone WLED simulator core components."""

import struct
import unittest
from wled_simulator.integrity import StreamIntegrityMonitor
from wled_simulator.models import ChannelInfo, IntegrityStatus
from wled_simulator.protocol_parser import ProtocolParser
from wled_simulator.state_machine import WledStateMachine


class TestSimulatorProtocolParser(unittest.TestCase):
    def test_parse_valid_ddp(self) -> None:
        payload = bytes([255, 0, 0, 0, 255, 0])  # 2 LEDs: Red, Green
        # Flags: 0x41 (version 1, PUSH=1), Seq: 3, Type: 1 (RGB), Dest: 1, Offset: 0, Len: 6
        header = struct.pack(">BBBB I H", 0x41, 3, 1, 1, 0, len(payload))
        raw = header + payload

        pkt = ProtocolParser.parse_ddp(raw)
        self.assertIsNotNone(pkt)
        assert pkt is not None
        self.assertTrue(pkt.push)
        self.assertEqual(pkt.sequence, 3)
        self.assertEqual(pkt.offset, 0)
        self.assertEqual(pkt.length, 6)
        self.assertEqual(pkt.payload, payload)

    def test_parse_ddp_no_push(self) -> None:
        payload = bytes([0, 0, 255])
        header = struct.pack(">BBBB I H", 0x40, 7, 1, 1, 300, len(payload))
        raw = header + payload

        pkt = ProtocolParser.parse_ddp(raw)
        self.assertIsNotNone(pkt)
        assert pkt is not None
        self.assertFalse(pkt.push)
        self.assertEqual(pkt.offset, 300)

    def test_parse_short_ddp_returns_none(self) -> None:
        self.assertIsNone(ProtocolParser.parse_ddp(b"short"))

    def test_parse_drgb(self) -> None:
        # Command 2 (DRGB), timeout 2s, RGB payload
        raw = bytes([2, 2, 255, 255, 255])
        pkt = ProtocolParser.parse_drgb(raw)
        self.assertIsNotNone(pkt)
        assert pkt is not None
        self.assertEqual(pkt.command, 2)
        self.assertEqual(pkt.start_led, 0)
        self.assertEqual(pkt.payload, bytes([255, 255, 255]))

    def test_parse_dnrgb(self) -> None:
        # Command 4 (DNRGB), timeout 1s, Start LED 100 (0x0064), payload
        raw = bytes([4, 1, 0, 100, 10, 20, 30])
        pkt = ProtocolParser.parse_drgb(raw)
        self.assertIsNotNone(pkt)
        assert pkt is not None
        self.assertEqual(pkt.command, 4)
        self.assertEqual(pkt.start_led, 100)
        self.assertEqual(pkt.payload, bytes([10, 20, 30]))


class TestSimulatorStateMachine(unittest.TestCase):
    def test_multi_packet_assembly_and_push(self) -> None:
        channels = [
            ChannelInfo(1, length=10, start_index=0, name="Strip 1"),
            ChannelInfo(2, length=10, start_index=10, name="Strip 2"),
        ]
        # Total 20 LEDs = 60 bytes

        rendered_frames: list[bytes] = []

        def on_render(buffer: bytes, telemetry: object) -> None:
            rendered_frames.append(buffer)

        sm = WledStateMachine(channels=channels, on_frame_rendered=on_render)

        # Chunk 1: LEDs 0..9 (30 bytes), Red, PUSH=0
        chunk1_payload = bytes([255, 0, 0] * 10)
        chunk1 = ProtocolParser.parse_ddp(
            struct.pack(">BBBB I H", 0x40, 1, 1, 1, 0, len(chunk1_payload)) + chunk1_payload
        )
        assert chunk1 is not None

        pushed1 = sm.process_ddp(chunk1)
        self.assertFalse(pushed1)
        self.assertEqual(len(rendered_frames), 0)  # No render yet

        # Chunk 2: LEDs 10..19 (30 bytes), Blue, PUSH=1
        chunk2_payload = bytes([0, 0, 255] * 10)
        chunk2 = ProtocolParser.parse_ddp(
            struct.pack(">BBBB I H", 0x41, 2, 1, 1, 30, len(chunk2_payload)) + chunk2_payload
        )
        assert chunk2 is not None

        pushed2 = sm.process_ddp(chunk2)
        self.assertTrue(pushed2)
        self.assertEqual(len(rendered_frames), 1)  # Frame rendered!

        final_frame = rendered_frames[0]
        self.assertEqual(len(final_frame), 60)
        # First 30 bytes are RED
        self.assertEqual(final_frame[:30], bytes([255, 0, 0] * 10))
        # Second 30 bytes are BLUE
        self.assertEqual(final_frame[30:], bytes([0, 0, 255] * 10))


class TestStreamIntegrityMonitor(unittest.TestCase):
    def test_sequence_gap_detection(self) -> None:
        monitor = StreamIntegrityMonitor(expected_total_bytes=60)
        monitor.record_chunk(sequence=1, offset=0, length=30, push=False)
        self.assertEqual(monitor.get_telemetry().integrity_status, IntegrityStatus.HEALTHY)

        # Gap from seq 1 -> 5
        monitor.record_chunk(sequence=5, offset=30, length=30, push=True)
        self.assertEqual(monitor.get_telemetry().integrity_status, IntegrityStatus.SEQUENCE_GAP)

    def test_torn_frame_detection(self) -> None:
        monitor = StreamIntegrityMonitor(expected_total_bytes=60)  # expects 20 LEDs (60 bytes)
        # Only sends 5 LEDs (15 bytes) and immediately sets PUSH=1
        monitor.record_chunk(sequence=1, offset=0, length=15, push=True)
        self.assertEqual(monitor.get_telemetry().integrity_status, IntegrityStatus.TORN_FRAME)


if __name__ == "__main__":
    unittest.main()
