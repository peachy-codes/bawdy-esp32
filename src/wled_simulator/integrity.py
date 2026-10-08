"""Stream integrity monitoring and diagnostics for multi-packet UDP transmissions."""

from __future__ import annotations
import time
from wled_simulator.models import IntegrityStatus, TelemetryData


class StreamIntegrityMonitor:
    """Monitors packet arrival timing, sequence continuity, and frame completeness.

    Provides real-time detection of dropped chunks, reordered packets, and
    incomplete (torn) frame pushes.
    """

    def __init__(self, expected_total_bytes: int) -> None:
        self.expected_total_bytes = expected_total_bytes

        self._last_seq: int | None = None
        self._last_packet_time: float | None = None
        self._last_push_time: float | None = None

        self._frame_bytes_written: set[int] = set()
        self._packet_count: int = 0
        self._frame_count: int = 0
        self._total_bytes_received: int = 0

        # Rolling 1-second counters
        self._window_start = time.perf_counter()
        self._window_packets = 0
        self._window_frames = 0
        self._window_bytes = 0

        self._current_fps = 0.0
        self._current_pps = 0.0
        self._current_kbps = 0.0
        self._current_jitter_us = 0.0

        self._status = IntegrityStatus.HEALTHY
        self._status_msg = "Stream healthy"

    def record_chunk(
        self,
        sequence: int,
        offset: int,
        length: int,
        push: bool,
    ) -> None:
        """Record the arrival of a single DDP packet chunk."""
        now = time.perf_counter()
        self._packet_count += 1
        self._window_packets += 1
        self._total_bytes_received += length
        self._window_bytes += length

        # 1. Inter-packet arrival jitter (in microseconds)
        if self._last_packet_time is not None:
            delta_us = (now - self._last_packet_time) * 1_000_000
            # Exponential moving average for jitter
            self._current_jitter_us = (self._current_jitter_us * 0.8) + (delta_us * 0.2)
        self._last_packet_time = now

        # 2. Sequence continuity (DDP sequence cycles 1..15 or 1..255)
        if self._last_seq is not None:
            # Expected next sequence (handling 15 -> 1 or 255 -> 1 wrap)
            expected_seq_15 = (self._last_seq % 15) + 1
            expected_seq_255 = (self._last_seq % 255) + 1

            if sequence != expected_seq_15 and sequence != expected_seq_255 and sequence != self._last_seq:
                self._status = IntegrityStatus.SEQUENCE_GAP
                self._status_msg = f"Sequence jump detected: {self._last_seq} -> {sequence}"
        self._last_seq = sequence

        # 3. Track coverage of bytes in the current frame
        for b in range(offset, offset + length, 3):
            self._frame_bytes_written.add(b)

        # 4. Push flag evaluation
        if push:
            self._window_frames += 1
            self._frame_count += 1

            # Check if all LEDs up to expected total were covered
            expected_leds = self.expected_total_bytes // 3
            covered_leds = len(self._frame_bytes_written)

            if covered_leds < expected_leds and expected_leds > 0:
                missing = expected_leds - covered_leds
                self._status = IntegrityStatus.TORN_FRAME
                self._status_msg = f"Torn frame push: missing {missing} of {expected_leds} LEDs"
            else:
                if self._status != IntegrityStatus.SEQUENCE_GAP:
                    self._status = IntegrityStatus.HEALTHY
                    self._status_msg = "Stream healthy"

            # Reset coverage tracking for next frame
            self._frame_bytes_written.clear()

        # Update rolling 1-second metrics
        time_since_window = now - self._window_start
        if time_since_window >= 0.5:
            self._current_fps = self._window_frames / time_since_window
            self._current_pps = self._window_packets / time_since_window
            self._current_kbps = (self._window_bytes / 1024.0) / time_since_window

            self._window_start = now
            self._window_frames = 0
            self._window_packets = 0
            self._window_bytes = 0

    def get_telemetry(self) -> TelemetryData:
        """Produce a snapshot of current telemetry metrics."""
        return TelemetryData(
            fps=round(self._current_fps, 1),
            pps=round(self._current_pps, 1),
            kbps=round(self._current_kbps, 1),
            total_packets=self._packet_count,
            total_frames=self._frame_count,
            jitter_us=round(self._current_jitter_us, 1),
            integrity_status=self._status,
            integrity_message=self._status_msg,
            last_packet_timestamp=self._last_packet_time or 0.0,
        )
