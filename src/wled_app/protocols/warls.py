"""WARLS (WLED Audio Reactive LED Strip) packet encoder for WLED.

WLED Realtime specification (Port 21324):
- Byte 0: 1 (WARLS ID)
- Byte 1: Timeout (seconds, 1..255)
- Bytes 2+: 4 bytes per LED: [led_index, red, green, blue]
"""

from __future__ import annotations

from wled_app.domain.device import ProtocolType
from wled_app.domain.frame import FrameBuffer


class WarlsEmitter:
    """Encodes FrameBuffers into WARLS packets with per-pixel index addressing."""

    MAX_LEDS_PER_PACKET = 256  # WARLS index is 1 byte (0..255)

    def __init__(self, max_leds: int = MAX_LEDS_PER_PACKET) -> None:
        self.max_leds = max_leds

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.WARLS

    @property
    def default_port(self) -> int:
        return 21324

    def encode_frame(
        self,
        frame: FrameBuffer,
        timeout_sec: int = 2,
    ) -> list[bytes]:
        """Encode frame into WARLS packet."""
        total_leds = min(len(frame), self.max_leds)
        if total_leds == 0:
            return []

        timeout = max(1, min(255, timeout_sec))
        payload = bytearray(2 + total_leds * 4)
        payload[0] = 1  # WARLS protocol ID
        payload[1] = timeout

        offset = 2
        for idx in range(total_leds):
            color = frame[idx]
            payload[offset] = idx
            payload[offset + 1] = color.r
            payload[offset + 2] = color.g
            payload[offset + 3] = color.b
            offset += 4

        return [bytes(payload)]
