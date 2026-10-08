"""Fire and Campfire simulation pattern generator."""

from __future__ import annotations
import random
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.domain.palette import PALETTES
from wled_app.patterns.base import PatternConfig


class FirePattern:
    """Realistic flickering campfire heat simulation with spark generation."""

    def __init__(self) -> None:
        # Cache per-channel heat arrays: channel_id -> list of float heat [0..1]
        self._heat_maps: dict[int, list[float]] = {}
        self._fire_palette = PALETTES["fire"]

    @property
    def id(self) -> str:
        return "fire"

    @property
    def name(self) -> str:
        return "Fire & Campfire"

    @property
    def description(self) -> str:
        return "Realistic flickering embers and flames rising along the strips."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        cooling = float(config.extra.get("cooling", 0.15))
        sparking = float(config.extra.get("sparking", 0.65))

        for channel in device.active_channels:
            length = channel.length
            if length == 0:
                continue

            heat = self._heat_maps.get(channel.channel_id)
            if heat is None or len(heat) != length:
                heat = [0.0] * length
                self._heat_maps[channel.channel_id] = heat

            # Step 1: Cool down every cell
            for i in range(length):
                cool_amount = random.uniform(0.0, cooling * config.speed)
                heat[i] = max(0.0, heat[i] - cool_amount)

            # Step 2: Heat drifts upward from each cell
            for i in range(length - 1, 1, -1):
                heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) / 3.0

            # Step 3: Randomly ignite new sparks near the base
            if random.random() < sparking:
                spark_pos = random.randint(0, min(3, length - 1))
                heat[spark_pos] = min(1.0, heat[spark_pos] + random.uniform(0.5, 0.95))

            # Step 4: Map heat to Fire palette and set pixels
            channel_pixels: list[Color] = []
            for i in range(length):
                h = heat[i]
                color = self._fire_palette.sample(h).dim(config.brightness)
                channel_pixels.append(color)

            frame.set_channel_pixels(channel, channel_pixels)
