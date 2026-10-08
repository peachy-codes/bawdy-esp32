"""FrameBuffer domain model representing a full multi-channel frame of RGB LEDs."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from wled_app.domain.channel import ChannelConfig
from wled_app.domain.color import Color


@dataclass
class FrameBuffer:
    """Mutable buffer holding RGB color values for a linear strip or multi-channel device."""

    pixels: list[Color]

    def __init__(self, size_or_pixels: int | Sequence[Color]) -> None:
        if isinstance(size_or_pixels, int):
            if size_or_pixels < 0:
                raise ValueError(
                    f"FrameBuffer size cannot be negative, got {size_or_pixels}"
                )
            self.pixels = [Color.black() for _ in range(size_or_pixels)]
        else:
            self.pixels = list(size_or_pixels)

    def __len__(self) -> int:
        return len(self.pixels)

    def __getitem__(self, index: int) -> Color:
        return self.pixels[index]

    def __setitem__(self, index: int, value: Color) -> None:
        self.pixels[index] = value

    @property
    def size(self) -> int:
        return len(self.pixels)

    def clone(self) -> FrameBuffer:
        """Create a deep copy of the FrameBuffer."""
        return FrameBuffer(list(self.pixels))

    def fill(self, color: Color) -> None:
        """Fill all pixels in the buffer with the given color."""
        self.pixels = [color for _ in range(len(self.pixels))]

    def clear(self) -> None:
        """Reset all pixels to black."""
        self.fill(Color.black())

    def set_pixel(self, index: int, color: Color) -> None:
        """Set a single pixel at the specified index."""
        if 0 <= index < len(self.pixels):
            self.pixels[index] = color

    def set_channel_pixels(
        self, channel: ChannelConfig, colors: Sequence[Color]
    ) -> None:
        """Write colors to a specific channel's slice in the linear address space."""
        if not channel.is_active:
            return
        start = channel.start_index
        limit = min(channel.length, len(colors))
        for i in range(limit):
            target_idx = start + i
            if 0 <= target_idx < len(self.pixels):
                self.pixels[target_idx] = colors[i]

    def get_channel_pixels(self, channel: ChannelConfig) -> list[Color]:
        """Extract the pixel colors assigned to a specific channel."""
        if not channel.is_active:
            return []
        start = channel.start_index
        end = channel.end_index
        if start >= len(self.pixels):
            return [Color.black() for _ in range(channel.length)]
        actual_end = min(end, len(self.pixels))
        slice_pixels = self.pixels[start:actual_end]
        # Pad with black if shorter than configured channel length
        if len(slice_pixels) < channel.length:
            slice_pixels.extend(
                [Color.black() for _ in range(channel.length - len(slice_pixels))]
            )
        return slice_pixels

    def fill_channel(self, channel: ChannelConfig, color: Color) -> None:
        """Fill only the pixels of a specific channel."""
        if not channel.is_active:
            return
        start = channel.start_index
        end = min(channel.end_index, len(self.pixels))
        for i in range(start, end):
            self.pixels[i] = color

    def to_rgb_bytes(self) -> bytearray:
        """Export raw contiguous RGB bytearray (3 bytes per pixel)."""
        buffer = bytearray(len(self.pixels) * 3)
        idx = 0
        for p in self.pixels:
            buffer[idx] = p.r
            buffer[idx + 1] = p.g
            buffer[idx + 2] = p.b
            idx += 3
        return buffer
