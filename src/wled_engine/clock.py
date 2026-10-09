"""High-precision drift-free monotonic frame clock."""

from __future__ import annotations
import time


class FrameClock:
    """Provides microsecond-accurate frame pacing and FPS measurement."""

    def __init__(self, target_fps: float = 30.0) -> None:
        self.target_fps = max(1.0, min(120.0, target_fps))
        self.frame_interval = 1.0 / self.target_fps

        self._last_time = time.perf_counter()
        self._fps_timer = self._last_time
        self._fps_counter = 0
        self._actual_fps = self.target_fps

    @property
    def actual_fps(self) -> float:
        return self._actual_fps

    def tick(self) -> float:
        """Call at the start of a frame loop. Returns delta time dt in seconds."""
        now = time.perf_counter()
        dt = max(0.0001, now - self._last_time)
        self._last_time = now

        # Update FPS counter every 0.5s
        self._fps_counter += 1
        elapsed_fps = now - self._fps_timer
        if elapsed_fps >= 0.5:
            self._actual_fps = self._fps_counter / elapsed_fps
            self._fps_counter = 0
            self._fps_timer = now

        return dt

    def sleep_until_next_frame(self, loop_start_time: float) -> None:
        """Sleep remaining time in frame budget to maintain exact target FPS."""
        now = time.perf_counter()
        compute_time = now - loop_start_time
        sleep_time = self.frame_interval - compute_time

        if sleep_time > 0.002:
            # Coarse sleep for the bulk of the duration
            time.sleep(sleep_time - 0.001)
            # Fine spin-wait for remaining microsecond precision
            while time.perf_counter() - loop_start_time < self.frame_interval:
                pass
        elif sleep_time > 0:
            while time.perf_counter() - loop_start_time < self.frame_interval:
                pass
