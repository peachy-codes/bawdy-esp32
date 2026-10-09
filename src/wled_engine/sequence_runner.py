"""Deterministic Server-Side Sequence Runner for LightingEngine.

Executes multi-layer timed light sequences on the engine's internal frame clock
with zero network latency jitter and atomic state management.
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING, Any

from wled_app.domain.color import Color
from wled_app.patterns.base import PatternConfig
from wled_app.patterns.registry import get_pattern_by_id
from wled_engine.blend import BlendMode

if TYPE_CHECKING:
    from wled_engine.core import LightingEngine


class SequenceRunner:
    """Orchestrates sequence playback synchronously with the engine frame clock."""

    def __init__(self, engine: LightingEngine) -> None:
        self.engine = engine
        self.sequence_data: dict[str, Any] | None = None

        self.is_playing: bool = False
        self.is_paused: bool = False
        self.elapsed_time: float = 0.0
        self.current_loop_iteration: int = 1
        self.active_cue_ids: set[str] = set()

    @property
    def total_duration(self) -> float:
        if not self.sequence_data:
            return 0.0
        steps = self.sequence_data.get("steps", [])
        if not steps:
            return 0.0
        return max(
            float(s.get("stop_time_sec", float(s.get("start_time_sec", 0.0)) + float(s.get("duration_sec", 0.0))))
            for s in steps
        )

    def load_sequence(self, data: dict[str, Any]) -> None:
        """Load sequence data."""
        self.stop()
        self.sequence_data = data
        self.elapsed_time = 0.0
        self.current_loop_iteration = 1
        self.active_cue_ids.clear()

    def play(self, data: dict[str, Any] | None = None, time_dilation: float | None = None) -> None:
        """Begin or resume sequence playback."""
        if data is not None:
            self.load_sequence(data)

        if not self.sequence_data or not self.sequence_data.get("steps"):
            return

        if time_dilation is not None:
            self.sequence_data["time_dilation"] = max(0.05, float(time_dilation))

        if self.is_paused:
            self.is_paused = False
            self.is_playing = True
            return

        self.is_playing = True
        self.is_paused = False
        self._evaluate()

    def pause(self) -> None:
        """Pause sequence playback."""
        if self.is_playing:
            self.is_paused = True

    def stop(self) -> None:
        """Stop sequence playback and clear sequence layers."""
        self.is_playing = False
        self.is_paused = False
        self.elapsed_time = 0.0
        self.current_loop_iteration = 1
        self.active_cue_ids.clear()

        # Reset layers used by sequence
        for i in range(10):
            self.engine.layer(i).reset()

    def seek(self, time_sec: float) -> None:
        """Seek sequence to exact timestamp and render frame immediately."""
        max_dur = self.total_duration
        self.elapsed_time = max(0.0, min(max_dur, time_sec))
        self._evaluate()

    def get_status(self) -> dict[str, Any]:
        """Return real-time playback telemetry."""
        return {
            "playing": self.is_playing,
            "paused": self.is_paused,
            "elapsed_time": round(self.elapsed_time, 3),
            "total_duration": round(self.total_duration, 3),
            "active_cues": sorted(list(self.active_cue_ids)),
            "loop_iteration": self.current_loop_iteration,
            "sequence_name": self.sequence_data.get("name", "Untitled") if self.sequence_data else None,
        }

    def update(self, dt: float) -> None:
        """Called by LightingEngine.step() on each clock frame tick."""
        if not self.is_playing or self.is_paused or not self.sequence_data:
            return

        dilation = max(0.05, float(self.sequence_data.get("time_dilation", 1.0)))
        self.elapsed_time += dt * dilation

        total_dur = self.total_duration
        if total_dur > 0 and self.elapsed_time >= total_dur:
            self._handle_sequence_end()
            return

        self._evaluate()

    def _handle_sequence_end(self) -> None:
        mode = str(self.sequence_data.get("loop_mode", "infinite")).lower()
        loop_count = int(self.sequence_data.get("loop_count", 1))

        if mode == "infinite":
            self.elapsed_time = 0.0
            self._evaluate()
        elif mode == "count":
            self.current_loop_iteration += 1
            if self.current_loop_iteration <= loop_count:
                self.elapsed_time = 0.0
                self._evaluate()
            else:
                self.stop()
        elif mode == "once_blackout":
            self.stop()
            self.engine.blackout()
        else:
            # once_hold
            self.is_playing = False
            self.is_paused = False

    def _evaluate(self) -> None:
        """Compute active steps and interpolate layer parameters for elapsed_time."""
        if not self.sequence_data:
            return

        steps = self.sequence_data.get("steps", [])
        dilation = max(0.05, float(self.sequence_data.get("time_dilation", 1.0)))
        t = self.elapsed_time

        # Identify active steps and their claimed layers (0..9)
        new_active_cues: set[str] = set()
        layer_claims: dict[int, dict[str, Any]] = {}

        for s in steps:
            start = float(s.get("start_time_sec", 0.0))
            dur = float(s.get("duration_sec", 0.0))
            stop = float(s.get("stop_time_sec", start + dur))
            layer_idx = int(s.get("target_layer", 0))

            if start <= t < stop and 0 <= layer_idx <= 9:
                new_active_cues.add(str(s.get("id", "")))
                layer_claims[layer_idx] = s

        # Reset layers that are no longer claimed
        for i in range(10):
            if i not in layer_claims:
                layer = self.engine.layer(i)
                if layer.enabled or layer.pattern is not None:
                    layer.reset()

        # Apply active steps to layers with continuous smooth interpolation
        for layer_idx, s in layer_claims.items():
            layer = self.engine.layer(layer_idx)

            pid = s.get("pattern_id")
            if not pid or pid == "none":
                layer.reset()
                continue

            # Pattern
            if layer.pattern is None or layer.pattern.id != pid:
                p_obj = get_pattern_by_id(pid)
                if p_obj:
                    layer.pattern = p_obj

            # Config
            speed = float(s.get("speed", 1.0))
            bright = float(s.get("brightness", 1.0))
            hex_col = s.get("primary_color", "#FFFFFF")
            color = Color.from_hex(hex_col) if hex_col else Color(255, 255, 255)
            layer.pattern_config = PatternConfig(speed=speed, brightness=bright, primary_color=color)

            # Blend Mode
            bm_str = str(s.get("blend_mode", "ALPHA_BLEND")).upper()
            try:
                layer.blend_mode = BlendMode[bm_str]
            except KeyError:
                layer.blend_mode = BlendMode.ALPHA_BLEND

            # Channel Mask
            chs = s.get("channels")
            layer.channel_ids = set(chs) if chs else None

            # Smooth Interpolated Opacity (handles seeking mid-flight without jump)
            start = float(s.get("start_time_sec", 0.0))
            dur = float(s.get("duration_sec", 0.0))
            stop = float(s.get("stop_time_sec", start + dur))
            target_op = float(s.get("target_opacity", 1.0))
            trans = float(s.get("transition_sec", 0.0)) / dilation
            fade_out = float(s.get("fade_out_sec", 0.0)) / dilation

            cue_elapsed = t - start
            cue_remaining = stop - t
            op = target_op

            if trans > 0.05 and cue_elapsed < trans:
                p = max(0.0, min(1.0, cue_elapsed / trans))
                op = target_op * (1.0 - math.cos(p * math.pi)) / 2.0
            elif fade_out > 0.05 and cue_remaining < fade_out:
                p = max(0.0, min(1.0, cue_remaining / fade_out))
                op = target_op * (1.0 - math.cos(p * math.pi)) / 2.0

            layer.opacity = max(0.0, min(1.0, op))
            layer.enabled = True

        self.active_cue_ids = new_active_cues
