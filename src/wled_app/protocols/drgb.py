"""DRGB (Direct RGB) and DNRGB (Direct Numbered RGB) packet encoders for WLED.

WLED Realtime specification (Port 21324):
DRGB (ID 2):
- Byte 0: 2 (DRGB ID)
- Byte 1: Timeout (seconds, 1..255)
- Bytes 2+: Contiguous RGB data for LEDs starting from index 0

DNRGB (ID 4):
- Byte 0: 4 (DNRGB ID)
- Byte 1: Timeout (seconds, 1..255)
- Bytes 2-3: 16-bit big-endian start LED index
- Bytes 4+: Contiguous RGB data for LEDs starting from start index
"""

from __future__ import annotations
import struct

from wled_app.domain.device import ProtocolType
from wled_app.domain.frame import FrameBuffer


class DrgbEmitter:
    """Encodes FrameBuffers into DRGB (Direct RGB) packets."""

    MAX_LEDS = 490  # 490 * 3 = 1470 bytes + 2 header = 1472 <= 1500 MTU

    def __init__(self, max_leds: int = MAX_LEDS) -> None:
        self.max_leds = max_leds

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.DRGB

    @property
    def default_port(self) -> int:
        return 21324

    def encode_frame(
        self,
        frame: FrameBuffer,
        timeout_sec: int = 2,
    ) -> list[bytes]:
        """Encode frame into DRGB packet."""
        if len(frame) == 0:
            return []

        timeout = max(1, min(255, timeout_sec))
        raw_bytes = frame.to_rgb_bytes()
        # DRGB sends single packet from index 0 up to max_leds
        limit = min(len(frame), self.max_leds) * 3
        payload = raw_bytes[:limit]

        header = bytes((2, timeout))
        return [header + payload]


class DnrgbEmitter:
    """Encodes FrameBuffers into DNRGB (Direct Numbered RGB) packets with chunking."""

    MAX_LEDS_PER_PACKET = 480

    def __init__(self, max_leds_per_packet: int = MAX_LEDS_PER_PACKET) -> None:
        self.max_leds_per_packet = max_leds_per_packet

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.DNRGB

    @property
    def default_port(self) -> int:
        return 21324

    def encode_frame(
        self,
        frame: FrameBuffer,
        timeout_sec: int = 2,
    ) -> list[bytes]:
        """Encode frame into one or more DNRGB packets with offset headers."""
        total_leds = len(frame)
        if total_leds == 0:
            return []

        timeout = max(1, min(255, timeout_sec))
        raw_bytes = frame.to_rgb_bytes()
        packets: list[bytes] = []

        chunk_size = self.max_leds_per_packet
        total_chunks = (total_leds + chunk_size - 1) // chunk_size

        for chunk_idx in range(total_chunks):
            start_led = chunk_idx * chunk_size
            end_led = min(start_led + chunk_size, total_leds)
            payload = raw_bytes[start_led * 3 : end_led * 3]

            # Header: [0x04, timeout, start_led_high, start_led_low]
            header = struct.pack(">BBH", 4, timeout, start_led)
            packets.append(header + payload)

        return packets
