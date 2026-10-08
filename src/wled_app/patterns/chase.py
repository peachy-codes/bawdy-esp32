"""Chase / Theater Scanner pattern generator."""

from __future__ import annotations
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import PatternConfig


class ChasePattern:
    """Running beam/dot chase with fading tail."""

    @property
    def id(self) -> str:
        return "chase"

    @property
    def name(self) -> str:
        return "Theater Chase"

    @property
    def description(self) -> str:
        return "A moving light dot with fading tail travelling along the strip."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        tail_length = int(config.extra.get("tail_length", 5))
        tail_length = max(1, tail_length)

        primary = config.primary_color.dim(config.brightness)
        secondary = config.secondary_color.dim(config.brightness)

        if config.sync_channels:
            # Render chase on each active channel independently
            for channel in device.active_channels:
                if channel.length == 0:
                    continue
                step = int(tick * config.speed)
                dir_factor = 1 if config.direction >= 0 else -1
                pos = (step * dir_factor) % channel.length

                channel_pixels: list[Color] = []
                for i in range(channel.length):
                    # Distance from head behind in direction of travel
                    dist = (pos - i) if dir_factor == 1 else (i - pos)
                    if dist < 0:
                        dist += channel.length

                    if dist == 0:
                        channel_pixels.append(primary)
                    elif dist < tail_length:
                        fade = 1.0 - (dist / tail_length)
                        channel_pixels.append(secondary.lerp(primary, fade))
                    else:
                        channel_pixels.append(secondary)

                frame.set_channel_pixels(channel, channel_pixels)
        else:
            # Linear flow through the entire device
            total_leds = device.total_leds
            if total_leds == 0:
                return

            step = int(tick * config.speed)
            dir_factor = 1 if config.direction >= 0 else -1
            pos = (step * dir_factor) % total_leds

            for i in range(total_leds):
                dist = (pos - i) if dir_factor == 1 else (i - pos)
                if dist < 0:
                    dist += total_leds

                if dist == 0:
                    frame.set_pixel(i, primary)
                elif dist < tail_length:
                    fade = 1.0 - (dist / tail_length)
                    frame.set_pixel(i, secondary.lerp(primary, fade))
                else:
                    frame.set_pixel(i, secondary)
