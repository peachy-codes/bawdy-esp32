"""Flowing Rainbow color cycle pattern generator."""

from __future__ import annotations
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import PatternConfig


class RainbowPattern:
    """Smooth flowing rainbow color spectrum across the LEDs."""

    @property
    def id(self) -> str:
        return "rainbow"

    @property
    def name(self) -> str:
        return "Flowing Rainbow"

    @property
    def description(self) -> str:
        return "Continuous HSV color wave flowing smoothly along the strip."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        cycles = float(config.extra.get("cycles", 1.0))
        speed_factor = 0.02 * config.speed * (1 if config.direction >= 0 else -1)
        phase_offset = tick * speed_factor

        if config.sync_channels:
            # Each channel has its own mapped rainbow cycle
            for channel in device.active_channels:
                if channel.length == 0:
                    continue

                channel_pixels: list[Color] = []
                for i in range(channel.length):
                    # Normalized position in channel
                    pos_norm = (i / channel.length) * cycles
                    hue = (pos_norm + phase_offset) % 1.0
                    color = Color.from_hsv(hue, 1.0, config.brightness)
                    channel_pixels.append(color)

                frame.set_channel_pixels(channel, channel_pixels)
        else:
            # Continuous rainbow across all total LEDs
            total_leds = device.total_leds
            if total_leds == 0:
                return

            for i in range(total_leds):
                pos_norm = (i / total_leds) * cycles
                hue = (pos_norm + phase_offset) % 1.0
                color = Color.from_hsv(hue, 1.0, config.brightness)
                frame.set_pixel(i, color)
