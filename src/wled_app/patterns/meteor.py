"""Meteor Rain and Shooting Star pattern generator."""

from __future__ import annotations
import random
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import PatternConfig


class MeteorPattern:
    """Shooting star / meteor with decaying sparkling tail."""

    def __init__(self) -> None:
        self._state: dict[int, list[Color]] = {}

    @property
    def id(self) -> str:
        return "meteor"

    @property
    def name(self) -> str:
        return "Meteor Rain"

    @property
    def description(self) -> str:
        return "Fast shooting star with glowing head and decaying sparkling trail."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        meteor_size = int(config.extra.get("meteor_size", 3))
        decay_factor = float(config.extra.get("decay", 0.75))

        primary = config.primary_color.dim(config.brightness)

        for channel in device.active_channels:
            length = channel.length
            if length == 0:
                continue

            # Retrieve or initialize previous trail state
            trail = self._state.get(channel.channel_id)
            if trail is None or len(trail) != length:
                trail = [Color.black() for _ in range(length)]
                self._state[channel.channel_id] = trail

            # Fade trail
            for i in range(length):
                if random.random() < 0.8:
                    trail[i] = trail[i].dim(decay_factor)

            # Draw meteor head
            step = int(tick * config.speed)
            head_pos = step % (length + meteor_size * 2) - meteor_size

            for i in range(meteor_size):
                pos = head_pos - i
                if 0 <= pos < length:
                    # Head tip is white-hot, fading into primary color
                    color = Color.white().lerp(primary, i / meteor_size)
                    trail[pos] = color.dim(config.brightness)

            frame.set_channel_pixels(channel, trail)
