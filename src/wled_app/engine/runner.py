"""Animation Runner engine coordinating pattern generation, UDP transmission, and frame callbacks."""

from __future__ import annotations
import threading
import time
from typing import Callable

from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.network.udp_client import MockUdpClient, UdpClient, UdpSender
from wled_app.patterns.base import Pattern, PatternConfig
from wled_app.protocols.base import ProtocolEmitter
from wled_app.protocols.registry import get_emitter


class AnimationRunner:
    """Coordinates real-time rendering, packet encoding, and UDP transmission."""

    def __init__(
        self,
        device: DeviceConfig,
        pattern: Pattern,
        pattern_config: PatternConfig | None = None,
        emitter: ProtocolEmitter | None = None,
        sender: UdpSender | None = None,
        target_fps: float = 30.0,
        dry_run: bool = False,
        on_frame: Callable[[FrameBuffer, float, int], None] | None = None,
    ) -> None:
        self.device = device
        self.pattern = pattern
        self.pattern_config = pattern_config or PatternConfig()
        self.emitter = emitter or get_emitter(device.protocol)
        self.dry_run = dry_run
        self.target_fps = max(1.0, min(120.0, target_fps))
        self.on_frame = on_frame

        if sender is not None:
            self.sender = sender
            self._owns_sender = False
        else:
            self.sender = MockUdpClient() if dry_run else UdpClient()
            self._owns_sender = True

        self.frame = FrameBuffer(device.total_leds)
        self._tick = 0
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._actual_fps: float = target_fps

    @property
    def is_running(self) -> bool:
        return not self._stop_event.is_set() and (
            self._thread is not None and self._thread.is_alive()
        )

    @property
    def current_tick(self) -> int:
        return self._tick

    @property
    def actual_fps(self) -> float:
        return self._actual_fps

    def step(self, tick: int | None = None) -> FrameBuffer:
        """Execute a single animation frame."""
        current_tick = self._tick if tick is None else tick
        self.pattern.render(current_tick, self.device, self.frame, self.pattern_config)

        # Transmit UDP packets only if total_leds > 0
        if self.device.total_leds > 0:
            packets = self.emitter.encode_frame(self.frame)
            self.sender.send_packets(self.device.ip, self.device.port, packets)

        if self.on_frame:
            self.on_frame(self.frame, self._actual_fps, current_tick)

        if tick is None:
            self._tick += 1

        return self.frame

    def run(self, max_frames: int | None = None) -> None:
        """Run the animation loop synchronously until stopped or max_frames reached."""
        self._stop_event.clear()
        frame_interval = 1.0 / self.target_fps
        frame_count = 0
        last_time = time.perf_counter()
        fps_timer = last_time
        fps_counter = 0

        try:
            while not self._stop_event.is_set():
                if max_frames is not None and frame_count >= max_frames:
                    break

                loop_start = time.perf_counter()
                self.step()
                frame_count += 1
                fps_counter += 1

                # Calculate actual FPS every second
                now = time.perf_counter()
                elapsed_fps = now - fps_timer
                if elapsed_fps >= 0.5:
                    self._actual_fps = fps_counter / elapsed_fps
                    fps_counter = 0
                    fps_timer = now

                # Sleep to maintain target FPS
                compute_time = now - loop_start
                sleep_time = frame_interval - compute_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

        finally:
            self.close()

    def start_background(self) -> None:
        """Start animation loop in a background daemon thread."""
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """Signal the animation loop to stop and wait for completion."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._thread = None
        self.close()

    def close(self) -> None:
        """Clean up resources."""
        if self._owns_sender:
            self.sender.close()
