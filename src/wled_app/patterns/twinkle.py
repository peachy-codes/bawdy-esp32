"""Twinkle and Sparkle pattern generator."""

from __future__ import annotations
import math
import random
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import PatternConfig


class TwinklePattern:
    """Softly twinkling and sparkling stars across the strips."""

    def __init__(self) -> None:
        # channel_id -> list of (phase, speed, color) per pixel
        self._pixels_state: dict[int, list[tuple[float, float, Color]]] = {}

    @property
    def id(self) -> str:
        return "twinkle"

    @property
    def name(self) -> str:
        return "Twinkle Stars"

    @property
    def description(self) -> str:
        return "Softly breathing and sparkling stars on a dark background."

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

            # Deterministic pseudo-random twinkling based on tick and index
            channel_pixels: list[Color] = []
            for i in range(length):
                # Unique phase and frequency per LED
                freq = 0.05 * config.speed * ((i % 5) + 1)
                phase = (tick * freq) + (i * 0.73)
                # Sine wave pulse [0..1]
                val = 0.5 * (1.0 + math.sin(phase))

                # Non-linear exponent to make stars sharp and brief
                sparkle = math.pow(val, 4.0)
                color = secondary.lerp(primary, sparkle)
                channel_pixels.append(color)

            frame.set_channel_pixels(channel, channel_pixels)
