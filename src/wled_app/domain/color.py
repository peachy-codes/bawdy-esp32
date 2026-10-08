"""RGB Color Value Object with strict validation and color utilities."""

from __future__ import annotations
import colorsys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Color:
    """Immutable RGB Color representation.

    Guarantees r, g, b values remain in the valid range [0, 255].
    """

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        if not (0 <= self.r <= 255 and 0 <= self.g <= 255 and 0 <= self.b <= 255):
            raise ValueError(
                f"Color channels must be in range [0, 255], got ({self.r}, {self.g}, {self.b})"
            )

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> Color:
        """Create a Color instance, clamping out-of-range values."""
        clamped_r = max(0, min(255, int(r)))
        clamped_g = max(0, min(255, int(g)))
        clamped_b = max(0, min(255, int(b)))
        return cls(clamped_r, clamped_g, clamped_b)

    @classmethod
    def from_hex(cls, hex_code: str) -> Color:
        """Parse hex string like '#RRGGBB' or 'RRGGBB' into Color."""
        cleaned = hex_code.strip().lstrip("#")
        if len(cleaned) == 3:
            cleaned = "".join(ch * 2 for ch in cleaned)
        if len(cleaned) != 6:
            raise ValueError(f"Invalid hex color format: '{hex_code}'")
        try:
            r = int(cleaned[0:2], 16)
            g = int(cleaned[2:4], 16)
            b = int(cleaned[4:6], 16)
            return cls(r, g, b)
        except ValueError as exc:
            raise ValueError(f"Failed to parse hex color '{hex_code}': {exc}") from exc

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> Color:
        """Create a Color from HSV values (h in [0, 1], s in [0, 1], v in [0, 1])."""
        h_norm = h % 1.0
        s_norm = max(0.0, min(1.0, float(s)))
        v_norm = max(0.0, min(1.0, float(v)))
        r_f, g_f, b_f = colorsys.hsv_to_rgb(h_norm, s_norm, v_norm)
        return cls(int(round(r_f * 255)), int(round(g_f * 255)), int(round(b_f * 255)))

    @classmethod
    def black(cls) -> Color:
        return cls(0, 0, 0)

    @classmethod
    def white(cls) -> Color:
        return cls(255, 255, 255)

    @classmethod
    def red(cls) -> Color:
        return cls(255, 0, 0)

    @classmethod
    def green(cls) -> Color:
        return cls(0, 255, 0)

    @classmethod
    def blue(cls) -> Color:
        return cls(0, 0, 255)

    @classmethod
    def yellow(cls) -> Color:
        return cls(255, 255, 0)

    @classmethod
    def cyan(cls) -> Color:
        return cls(0, 255, 255)

    @classmethod
    def magenta(cls) -> Color:
        return cls(255, 0, 255)

    @classmethod
    def orange(cls) -> Color:
        return cls(255, 128, 0)

    @classmethod
    def purple(cls) -> Color:
        return cls(128, 0, 255)

    def to_bytes(self) -> bytes:
        """Return 3-byte RGB representation."""
        return bytes((self.r, self.g, self.b))

    def to_tuple(self) -> tuple[int, int, int]:
        """Return (r, g, b) tuple."""
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        """Return hex representation #RRGGBB."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}".upper()

    def dim(self, factor: float) -> Color:
        """Dim color by a factor in range [0.0, 1.0]."""
        f = max(0.0, min(1.0, factor))
        return Color.from_rgb(
            int(round(self.r * f)),
            int(round(self.g * f)),
            int(round(self.b * f)),
        )

    def lerp(self, other: Color, t: float) -> Color:
        """Linearly interpolate between self and other (t in [0.0, 1.0])."""
        clamped_t = max(0.0, min(1.0, t))
        return Color.from_rgb(
            int(round(self.r + (other.r - self.r) * clamped_t)),
            int(round(self.g + (other.g - self.g) * clamped_t)),
            int(round(self.b + (other.b - self.b) * clamped_t)),
        )

    def is_black(self) -> bool:
        return self.r == 0 and self.g == 0 and self.b == 0
