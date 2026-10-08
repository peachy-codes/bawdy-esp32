"""Multi-stop Gradient Drift pattern generator."""

from __future__ import annotations
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.domain.palette import PALETTES, ColorPalette, get_palette
from wled_app.patterns.base import PatternConfig


class GradientPattern:
    """Smooth multi-stop color palette drifting continuously across the strip."""

    @property
    def id(self) -> str:
        return "gradient"

    @property
    def name(self) -> str:
        return "Gradient Drift (Cyberpunk / Sunset)"

    @property
    def description(self) -> str:
        return "Vibrant multi-stop color gradient slowly drifting along the channels."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        palette_name = str(config.extra.get("palette", "cyberpunk"))
        try:
            palette = get_palette(palette_name)
        except ValueError:
            palette = PALETTES["cyberpunk"]

        speed_factor = 0.015 * config.speed * (1 if config.direction >= 0 else -1)
        offset = tick * speed_factor

        for channel in device.active_channels:
            length = channel.length
            if length == 0:
                continue

            channel_pixels: list[Color] = []
            for i in range(length):
                pos = (i / max(1, length)) + offset
                color = palette.sample(pos).dim(config.brightness)
                channel_pixels.append(color)

            frame.set_channel_pixels(channel, channel_pixels)
