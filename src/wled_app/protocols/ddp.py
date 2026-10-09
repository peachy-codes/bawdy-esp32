"""Distributed Display Protocol (DDP) UDP packet encoder for WLED.

Standard DDP specification:
- Port: 4048
- Header: 10 bytes
  - Byte 0: Flags 1 (0x40 version 1, 0x01 push flag)
  - Byte 1: Sequence number (1..15)
  - Byte 2: Data type (0x01 = RGB)
  - Byte 3: Destination ID (0x01 = default display)
  - Bytes 4-7: Channel offset in bytes (32-bit big-endian, start_led * 3)
  - Bytes 8-9: Data length in bytes (16-bit big-endian, led_count * 3)
- Followed by contiguous RGB payload.
"""

from __future__ import annotations
import struct

from wled_app.domain.device import ProtocolType
from wled_app.domain.frame import FrameBuffer


class DdpEmitter:
    """Encodes FrameBuffers into Distributed Display Protocol (DDP) datagrams."""

    MAX_LEDS_PER_PACKET = 480  # 480 * 3 = 1440 bytes payload + 10 header = 1450 <= 1500 MTU

    def __init__(self, max_leds_per_packet: int = MAX_LEDS_PER_PACKET) -> None:
        self.max_leds_per_packet = max_leds_per_packet
        self._sequence: int = 1

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.DDP

    @property
    def default_port(self) -> int:
        return 4048

    def _next_sequence(self) -> int:
        seq = self._sequence
        self._sequence = (self._sequence % 15) + 1
        return seq

    def encode_raw_bytes(
        self,
        raw_bytes: bytes | bytearray,
        push: bool = True,
    ) -> list[bytes]:
        """Encode contiguous RGB bytes directly into DDP datagrams without object allocation."""
        total_bytes = len(raw_bytes)
        if total_bytes == 0:
            return []

        chunk_bytes = self.max_leds_per_packet * 3
        packets: list[bytes] = []

        for start_byte in range(0, total_bytes, chunk_bytes):
            end_byte = min(start_byte + chunk_bytes, total_bytes)
            payload = raw_bytes[start_byte:end_byte]
            is_last_chunk = end_byte >= total_bytes
            flags1 = 0x41 if (is_last_chunk and push) else 0x40
            seq = self._next_sequence()

            header = struct.pack(
                ">BBBB I H",
                flags1,
                seq,
                0x01,  # data_type = RGB
                0x01,  # dest_id = default display
                start_byte,
                len(payload),
            )
            packets.append(header + payload)

        return packets

    def encode_frame(
        self,
        frame: FrameBuffer,
        timeout_sec: int = 2,
        push: bool = True,
    ) -> list[bytes]:
        """Encode frame into one or more DDP UDP packets."""
        if len(frame) == 0:
            return []
        return self.encode_raw_bytes(frame.to_rgb_bytes(), push=push)

    @staticmethod
    def encode_sync_packet(seq: int = 1) -> bytes:
        """Encode a 10-byte zero-payload DDP Broadcast Sync packet with PUSH flag set.

        Transmitting this packet to the broadcast subnet triggers all listening
        controllers to latch and output their buffered frame simultaneously.
        """
        return struct.pack(">BBBB I H", 0x41, max(1, seq % 16), 0x01, 0x01, 0, 0)

