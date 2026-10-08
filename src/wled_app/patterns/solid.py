"""Solid Color Wash and Breathe Dimmer pattern generator."""

from __future__ import annotations
import math
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import PatternConfig


class SolidPattern:
    """Solid color wash with optional breathing pulse."""

    @property
    def id(self) -> str:
        return "solid"

    @property
    def name(self) -> str:
        return "Solid Wash & Breathe"

    @property
    def description(self) -> str:
        return "Clean solid color wash across channels with optional breathing pulse."

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        breathe = bool(config.extra.get("breathe", False))

        if breathe:
            period = max(10, int(60 / max(0.1, config.speed)))
            phase = (tick % period) / period
            factor = 0.5 * (1.0 + math.sin(phase * 2.0 * math.pi - math.pi / 2.0))
            # Breathe between 20% and 100% brightness
            effective_brightness = config.brightness * (0.2 + 0.8 * factor)
        else:
            effective_brightness = config.brightness

        color = config.primary_color.dim(effective_brightness)
        frame.fill(color)
