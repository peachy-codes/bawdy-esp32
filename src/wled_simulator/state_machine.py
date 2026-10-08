"""WLED ESP32 hardware frame assembly state machine and memory buffer."""

from __future__ import annotations
import time
from typing import Callable
from wled_simulator.integrity import StreamIntegrityMonitor
from wled_simulator.models import ChannelInfo, DdpDatagram, DrgbDatagram, TelemetryData


class WledStateMachine:
    """Emulates WLED's realtime display engine.

    Manages physical LED memory, chunk accumulation, sequence verification,
    and PUSH flag frame execution (equivalent to WLED's strip.show()).
    """

    def __init__(
        self,
        channels: list[ChannelInfo],
        timeout_seconds: float = 2.5,
        on_frame_rendered: Callable[[bytes, TelemetryData], None] | None = None,
    ) -> None:
        self.channels = channels
        self.timeout_seconds = timeout_seconds
        self.on_frame_rendered = on_frame_rendered

        self.total_leds = sum(ch.length for ch in self.channels)
        self.total_bytes = self.total_leds * 3

        # Contiguous bytearray representing virtual WS2812B pixel memory
        self._buffer = bytearray(self.total_bytes)
        self.integrity_monitor = StreamIntegrityMonitor(self.total_bytes)
        self._last_activity = time.perf_counter()

    def process_ddp(self, packet: DdpDatagram) -> bool:
        """Process an incoming DDP datagram.

        Copies chunk into virtual strip memory and evaluates PUSH flag.
        Returns True if a frame update was triggered (PUSH=True).
        """
        self._last_activity = time.perf_counter()

        # Write payload slice to memory buffer
        start = packet.offset
        end = min(start + packet.length, self.total_bytes)
        if start < self.total_bytes:
            valid_len = end - start
            self._buffer[start:end] = packet.payload[:valid_len]

        # Record packet telemetry
        self.integrity_monitor.record_chunk(
            sequence=packet.sequence,
            offset=packet.offset,
            length=packet.length,
            push=packet.push,
        )

        # WLED executes strip.show() when PUSH flag is set
        if packet.push:
            if self.on_frame_rendered:
                telemetry = self.get_telemetry()
                self.on_frame_rendered(bytes(self._buffer), telemetry)
            return True

        return False

    def process_drgb(self, packet: DrgbDatagram) -> bool:
        """Process incoming DRGB / DNRGB datagram."""
        self._last_activity = time.perf_counter()

        start = packet.start_led * 3
        end = min(start + len(packet.payload), self.total_bytes)
        if start < self.total_bytes:
            valid_len = end - start
            self._buffer[start:end] = packet.payload[:valid_len]

        # DRGB packets are self-contained frames (implicit push)
        self.integrity_monitor.record_chunk(
            sequence=1,
            offset=start,
            length=len(packet.payload),
            push=True,
        )

        if self.on_frame_rendered:
            telemetry = self.get_telemetry()
            self.on_frame_rendered(bytes(self._buffer), telemetry)
        return True

    def get_telemetry(self) -> TelemetryData:
        """Fetch current telemetry and attach active channel metadata."""
        telemetry = self.integrity_monitor.get_telemetry()
        telemetry.active_channels = list(self.channels)
        return telemetry

    def get_pixel_bytes(self) -> bytes:
        """Get immutable copy of current pixel memory buffer."""
        return bytes(self._buffer)

    def check_timeout(self) -> bool:
        """Check if realtime connection has timed out.

        Returns True if timeout occurred.
        """
        if time.perf_counter() - self._last_activity > self.timeout_seconds:
            return True
        return False
