"""Cylon / Knight Rider scanner pattern generator."""

from __future__ import annotations
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import PatternConfig


class CylonPattern:
    """Knight Rider bouncing scanner eye with trailing red glow."""

    @property
    def id(self) -> str:
        return "cylon"

    @property
    def name(self) -> str:
        return "Cylon (Knight Rider)"

    @property
    def description(self) -> str:
        return "Bouncing eye travelling smoothly back and forth with glowing tail."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        eye_size = int(config.extra.get("eye_size", 2))
        eye_size = max(1, eye_size)
        primary = config.primary_color.dim(config.brightness)
        secondary = config.secondary_color.dim(config.brightness)

        for channel in device.active_channels:
            length = channel.length
            if length <= 1:
                continue

            cycle_len = (length - 1) * 2
            step = int(tick * config.speed) % cycle_len

            # Triangular bounce position
            pos = step if step < length else cycle_len - step

            channel_pixels: list[Color] = []
            for i in range(length):
                dist = abs(i - pos)
                if dist < eye_size:
                    channel_pixels.append(primary)
                elif dist < eye_size + 4:
                    fade = 1.0 - ((dist - eye_size + 1) / 5.0)
                    channel_pixels.append(secondary.lerp(primary, max(0.0, fade)))
                else:
                    channel_pixels.append(secondary)

            frame.set_channel_pixels(channel, channel_pixels)
