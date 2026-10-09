"""Protocol output targets, color ordering, and patch segment descriptors."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any


class OutputProtocol(str, Enum):
    """Network transmission protocol for lighting controllers."""
    DDP = "ddp"
    E131 = "e131"
    ARTNET = "artnet"
    DRGB = "drgb"
    VIDEO_RASTER = "video_raster"


class ColorOrder(str, Enum):
    """LED chip color byte ordering."""
    RGB = "RGB"
    GRB = "GRB"
    BGR = "BGR"
    RGBW = "RGBW"
    GRBW = "GRBW"

    @classmethod
    def from_str(cls, s: str) -> ColorOrder:
        val = s.strip().upper()
        try:
            return cls(val)
        except ValueError:
            return cls.GRB


def permute_color(
    r: int,
    g: int,
    b: int,
    order: ColorOrder = ColorOrder.GRB,
    w: int = 0,
) -> tuple[int, ...]:
    """Reorder R, G, B, W integers into the target chip color order."""
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    w = max(0, min(255, w))

    match order:
        case ColorOrder.GRB:
            return (g, r, b)
        case ColorOrder.BGR:
            return (b, g, r)
        case ColorOrder.RGBW:
            return (r, g, b, w)
        case ColorOrder.GRBW:
            return (g, r, b, w)
        case _:
            return (r, g, b)


def unpermute_color(
    c0: int,
    c1: int,
    c2: int,
    c3: int = 0,
    order: ColorOrder = ColorOrder.GRB,
) -> tuple[int, int, int]:
    """Reconstruct (R, G, B) tuple from raw physical wire bytes according to ColorOrder."""
    match order:
        case ColorOrder.GRB:
            return (c1, c0, c2)
        case ColorOrder.BGR:
            return (c2, c1, c0)
        case ColorOrder.RGBW:
            return (c0, c1, c2)
        case ColorOrder.GRBW:
            return (c1, c0, c2)
        case _:
            return (c0, c1, c2)


@dataclass
class PatchSegment:
    """Maps a slice of a logical fixture's pixels to a physical controller channel."""
    fixture_id: str
    pixel_start: int
    pixel_count: int
    controller_id: str
    channel_index: int
    port_offset: int = 0
    reversed: bool = False
    color_order: ColorOrder = ColorOrder.GRB
    protocol: OutputProtocol = OutputProtocol.DDP
    brightness_scale: float = 1.0

    @property
    def pixel_end(self) -> int:
        return self.pixel_start + self.pixel_count

    @property
    def port_end(self) -> int:
        return self.port_offset + self.pixel_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "pixel_start": self.pixel_start,
            "pixel_count": self.pixel_count,
            "controller_id": self.controller_id,
            "channel_index": self.channel_index,
            "port_offset": self.port_offset,
            "reversed": self.reversed,
            "color_order": self.color_order.value,
            "protocol": self.protocol.value,
            "brightness_scale": round(self.brightness_scale, 3),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PatchSegment:
        return cls(
            fixture_id=str(data["fixture_id"]),
            pixel_start=int(data.get("pixel_start", 0)),
            pixel_count=int(data["pixel_count"]),
            controller_id=str(data["controller_id"]),
            channel_index=int(data.get("channel_index", 0)),
            port_offset=int(data.get("port_offset", 0)),
            reversed=bool(data.get("reversed", False)),
            color_order=ColorOrder.from_str(data.get("color_order", "GRB")),
            protocol=OutputProtocol(data.get("protocol", "ddp").lower()),
            brightness_scale=float(data.get("brightness_scale", 1.0)),
        )
