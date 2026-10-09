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

    def encode_frame(
        self,
        frame: FrameBuffer,
        timeout_sec: int = 2,
        push: bool = True,
    ) -> list[bytes]:
        """Encode frame into one or more DDP UDP packets.

        Args:
            frame: FrameBuffer to encode.
            timeout_sec: Compatibility timeout parameter.
            push: If True, sets PUSH bit on final chunk to latch frame immediately.
                  If False, buffers in receiver memory waiting for a DDP Sync packet.
        """
        total_leds = len(frame)
        if total_leds == 0:
            return []

        raw_bytes = frame.to_rgb_bytes()
        packets: list[bytes] = []

        chunk_size_leds = self.max_leds_per_packet
        total_chunks = (total_leds + chunk_size_leds - 1) // chunk_size_leds

        for chunk_idx in range(total_chunks):
            start_led = chunk_idx * chunk_size_leds
            end_led = min(start_led + chunk_size_leds, total_leds)
            chunk_led_count = end_led - start_led

            start_byte = start_led * 3
            end_byte = end_led * 3
            payload = raw_bytes[start_byte:end_byte]

            is_last_chunk = chunk_idx == total_chunks - 1
            # 0x40 = DDP v1; 0x01 = PUSH flag
            flags1 = 0x41 if (is_last_chunk and push) else 0x40
            seq = self._next_sequence()
            data_type = 0x01  # RGB
            dest_id = 0x01  # Default display ID

            # Pack 10-byte header:
            # B: flags1 (1 byte)
            # B: sequence (1 byte)
            # B: data_type (1 byte)
            # B: dest_id (1 byte)
            # >I: offset in bytes (4 bytes big-endian)
            # >H: length in bytes (2 bytes big-endian)
            header = struct.pack(
                ">BBBB I H",
                flags1,
                seq,
                data_type,
                dest_id,
                start_byte,
                len(payload),
            )

            packets.append(header + payload)

        return packets

    @staticmethod
    def encode_sync_packet(seq: int = 1) -> bytes:
        """Encode a 10-byte zero-payload DDP Broadcast Sync packet with PUSH flag set.

        Transmitting this packet to the broadcast subnet triggers all listening
        controllers to latch and output their buffered frame simultaneously.
        """
        return struct.pack(">BBBB I H", 0x41, max(1, seq % 16), 0x01, 0x01, 0, 0)

