"""Blink, Pulse, and Alternating Channel pattern generator."""

from __future__ import annotations
import math
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import PatternConfig


class BlinkPattern:
    """Multi-channel blink, pulse, and alternating strobe pattern."""

    @property
    def id(self) -> str:
        return "blink"

    @property
    def name(self) -> str:
        return "Blink & Pulse"

    @property
    def description(self) -> str:
        return "Alternating or synchronized multi-channel flash and pulsing effect."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        mode = str(config.extra.get("mode", "pulse")).lower()  # "pulse" or "hard"
        alternate_channels = bool(config.extra.get("alternate_channels", False))
        period = max(2, int(20 / max(0.1, config.speed)))

        primary = config.primary_color.dim(config.brightness)
        secondary = config.secondary_color.dim(config.brightness)

        phase = (tick % period) / period  # 0.0 to 1.0

        if mode == "hard":
            # Square wave
            is_on = phase < 0.5
            factor = 1.0 if is_on else 0.0
        else:
            # Smooth sine pulse
            factor = 0.5 * (1.0 + math.sin(phase * 2.0 * math.pi - math.pi / 2.0))

        color_a = secondary.lerp(primary, factor)
        color_b = secondary.lerp(primary, 1.0 - factor) if alternate_channels else color_a

        if alternate_channels:
            for idx, channel in enumerate(device.active_channels):
                # Odd channels use color_a, even channels use color_b
                active_color = color_a if (idx % 2 == 0) else color_b
                frame.fill_channel(channel, active_color)
        else:
            frame.fill(color_a)
