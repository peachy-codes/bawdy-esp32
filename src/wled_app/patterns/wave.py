"""Harmonic Wave and Ocean Ripple pattern generator."""

from __future__ import annotations
import math
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.domain.palette import PALETTES
from wled_app.patterns.base import PatternConfig


class WavePattern:
    """Harmonic undulating sine waves simulating ocean water ripples."""

    def __init__(self) -> None:
        self._palette = PALETTES["ocean"]

    @property
    def id(self) -> str:
        return "wave"

    @property
    def name(self) -> str:
        return "Ocean Waves"

    @property
    def description(self) -> str:
        return "Harmonic undulating sine ripples flowing across the channels."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        use_palette = bool(config.extra.get("use_palette", True))
        speed_factor = 0.05 * config.speed * (1 if config.direction >= 0 else -1)

        for channel in device.active_channels:
            length = channel.length
            if length == 0:
                continue

            channel_pixels: list[Color] = []
            for i in range(length):
                # Dual harmonic wave: spatial freq 1 + spatial freq 2
                wave1 = math.sin((i / max(1, length)) * 4.0 * math.pi + (tick * speed_factor))
                wave2 = math.cos((i / max(1, length)) * 6.0 * math.pi - (tick * speed_factor * 0.7))
                combined = 0.5 * (1.0 + (0.6 * wave1 + 0.4 * wave2))

                if use_palette:
                    color = self._palette.sample(combined).dim(config.brightness)
                else:
                    color = config.secondary_color.lerp(config.primary_color, combined).dim(config.brightness)

                channel_pixels.append(color)

            frame.set_channel_pixels(channel, channel_pixels)
