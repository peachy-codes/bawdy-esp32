"""Color Wipe / Progressive fill pattern generator."""

from __future__ import annotations
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import PatternConfig


class ColorWipePattern:
    """Progressively fills the LEDs one by one, then clears or swaps color."""

    @property
    def id(self) -> str:
        return "wipe"

    @property
    def name(self) -> str:
        return "Color Wipe"

    @property
    def description(self) -> str:
        return "Progressively fills the strip with color, then wipes it clear."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        primary = config.primary_color.dim(config.brightness)
        secondary = config.secondary_color.dim(config.brightness)

        for channel in device.active_channels:
            length = channel.length
            if length == 0:
                continue

            cycle = length * 2
            step = int(tick * config.speed) % cycle

            channel_pixels: list[Color] = []
            if step < length:
                # Filling phase: 0..step is primary, remainder is secondary
                for i in range(length):
                    channel_pixels.append(primary if i <= step else secondary)
            else:
                # Wiping phase: 0..(step - length) is wiped back to secondary
                wipe_pos = step - length
                for i in range(length):
                    channel_pixels.append(secondary if i <= wipe_pos else primary)

            frame.set_channel_pixels(channel, channel_pixels)
