"""Layer representation and per-layer compositing logic."""

from __future__ import annotations
from dataclasses import dataclass, field
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import Pattern, PatternConfig
from wled_engine.blend import BlendMode, blend_pixel


@dataclass
class OpacityTween:
    """Manages smooth temporal transitions of layer opacity."""
    start_opacity: float
    target_opacity: float
    duration_sec: float
    elapsed_sec: float = 0.0

    @property
    def is_finished(self) -> bool:
        return self.elapsed_sec >= self.duration_sec

    def update(self, dt: float) -> float:
        """Advance tween by dt seconds and return interpolated opacity."""
        if self.duration_sec <= 0.0:
            return self.target_opacity

        self.elapsed_sec = min(self.duration_sec, self.elapsed_sec + dt)
        progress = self.elapsed_sec / self.duration_sec
        # Smooth ease-in-out cosine curve
        import math
        t = (1.0 - math.cos(progress * math.pi)) / 2.0
        return self.start_opacity + (self.target_opacity - self.start_opacity) * t


class Layer:
    """An individual compositing layer in the engine's 0-9 layer stack.

    Layers are composited in ascending order (Layer 0 at bottom -> Layer 9 at top).
    """

    def __init__(
        self,
        index: int,
        name: str | None = None,
        pattern: Pattern | None = None,
        pattern_config: PatternConfig | None = None,
        opacity: float = 1.0,
        blend_mode: BlendMode = BlendMode.ALPHA_BLEND,
        channel_ids: set[int] | None = None,
        enabled: bool = True,
    ) -> None:
        if not (0 <= index <= 9):
            raise ValueError(f"Layer index must be between 0 and 9, got {index}")

        self.index = index
        self.name = name or f"Layer {index}"
        self.pattern = pattern
        self.pattern_config = pattern_config or PatternConfig()
        self._opacity = max(0.0, min(1.0, opacity))
        self.blend_mode = blend_mode
        self.channel_ids = channel_ids
        self.enabled = enabled

        self._tween: OpacityTween | None = None

    @property
    def opacity(self) -> float:
        return self._opacity

    @opacity.setter
    def opacity(self, val: float) -> None:
        self._opacity = max(0.0, min(1.0, val))
        self._tween = None

    def fade_to(self, target_opacity: float, duration_sec: float) -> None:
        """Initiate smooth temporal fade transition to target opacity."""
        target = max(0.0, min(1.0, target_opacity))
        if duration_sec <= 0.0:
            self._opacity = target
            self._tween = None
            return

        self._tween = OpacityTween(
            start_opacity=self._opacity,
            target_opacity=target,
            duration_sec=duration_sec,
        )

    def reset(self) -> None:
        """Atomically reset layer state, disabling it and cancelling tweens."""
        self.pattern = None
        self.enabled = False
        self._opacity = 0.0
        self._tween = None

    def update(self, dt: float) -> None:
        """Advance layer animations and active opacity tweens."""
        if self._tween is not None:
            self._opacity = self._tween.update(dt)
            if self._tween.is_finished:
                self._tween = None

    def composite_into(
        self,
        tick: int,
        device: DeviceConfig,
        out_frame: FrameBuffer,
        scratch_frame: FrameBuffer,
    ) -> None:
        """Render pattern to scratch buffer and blend into destination out_frame.

        Skips execution if disabled, opacity is 0, or no pattern is set.
        """
        if not self.enabled or self._opacity <= 0.0 or self.pattern is None:
            return

        total_leds = device.total_leds
        if total_leds == 0:
            return

        # Ensure scratch frame matches size
        if len(scratch_frame) != total_leds:
            scratch_frame.pixels = [Color.black() for _ in range(total_leds)]
        else:
            scratch_frame.clear()
        self.pattern.render(tick, device, scratch_frame, self.pattern_config)

        # Build mask of allowed LED indices if channel_ids is specified
        allowed_indices: set[int] | None = None
        if self.channel_ids is not None:
            allowed_indices = set()
            for ch in device.channels:
                if ch.channel_id in self.channel_ids:
                    allowed_indices.update(range(ch.start_index, ch.end_index))

        # Composite pixel by pixel
        for i in range(total_leds):
            if allowed_indices is not None and i not in allowed_indices:
                continue

            src_pixel = scratch_frame[i]
            # Optimization: Skip blending black source pixels in ADDITIVE or MAX modes
            if self.blend_mode in (BlendMode.ADDITIVE, BlendMode.MAX) and src_pixel.is_black():
                continue

            dst_pixel = out_frame[i]
            blended = blend_pixel(dst_pixel, src_pixel, self._opacity, self.blend_mode)
            out_frame[i] = blended
