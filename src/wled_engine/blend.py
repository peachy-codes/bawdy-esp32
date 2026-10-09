"""Color blending modes and mathematical raster operators for lighting layers."""

from __future__ import annotations
from enum import Enum
from wled_app.domain.color import Color


class BlendMode(str, Enum):
    """Mathematical operators for compositing a source layer over a destination base."""
    OVERWRITE = "overwrite"       # Direct replacement: Src * alpha + Dst * (1 - alpha)
    ALPHA_BLEND = "alpha_blend"   # Linear interpolation: Dst * (1 - alpha) + Src * alpha
    ADDITIVE = "additive"         # Light addition clamped to 255: min(255, Dst + Src * alpha)
    MULTIPLY = "multiply"         # Color filter: (Dst * Src) / 255
    MAX = "max"                   # Channel-wise maximum: max(Dst, Src * alpha)
    MASK = "mask"                 # Uses source luminance as a gating multiplier on destination


def blend_pixel(dst: Color, src: Color, opacity: float, mode: BlendMode) -> Color:
    """Blend a source pixel into a destination pixel using specified blend mode and opacity.

    Args:
        dst: Existing base pixel color.
        src: New incoming layer pixel color.
        opacity: Layer opacity multiplier (0.0 .. 1.0).
        mode: The BlendMode operation.

    Returns:
        The composited output Color.
    """
    if opacity <= 0.0:
        return dst

    # Clamp opacity to [0.0, 1.0]
    alpha = max(0.0, min(1.0, opacity))

    if mode in (BlendMode.ALPHA_BLEND, BlendMode.OVERWRITE):
        # Linear interpolation: dst + (src - dst) * alpha
        r = int(dst.r + (src.r - dst.r) * alpha)
        g = int(dst.g + (src.g - dst.g) * alpha)
        b = int(dst.b + (src.b - dst.b) * alpha)
        return Color(r, g, b)

    elif mode == BlendMode.ADDITIVE:
        # Addition clamped to 255: dst + src * alpha
        r = min(255, int(dst.r + src.r * alpha))
        g = min(255, int(dst.g + src.g * alpha))
        b = min(255, int(dst.b + src.b * alpha))
        return Color(r, g, b)

    elif mode == BlendMode.MULTIPLY:
        # Multiplicative filter: dst * (src / 255) modulated by alpha
        filter_r = (src.r / 255.0) * alpha + (1.0 - alpha)
        filter_g = (src.g / 255.0) * alpha + (1.0 - alpha)
        filter_b = (src.b / 255.0) * alpha + (1.0 - alpha)
        r = min(255, int(dst.r * filter_r))
        g = min(255, int(dst.g * filter_g))
        b = min(255, int(dst.b * filter_b))
        return Color(r, g, b)

    elif mode == BlendMode.MAX:
        # Maximum luminance per channel
        scaled_r = int(src.r * alpha)
        scaled_g = int(src.g * alpha)
        scaled_b = int(src.b * alpha)
        r = max(dst.r, scaled_r)
        g = max(dst.g, scaled_g)
        b = max(dst.b, scaled_b)
        return Color(r, g, b)

    elif mode == BlendMode.MASK:
        # Source luminance gates destination
        lum = src.luminance / 255.0
        gate = lum * alpha + (1.0 - alpha)
        r = min(255, int(dst.r * gate))
        g = min(255, int(dst.g * gate))
        b = min(255, int(dst.b * gate))
        return Color(r, g, b)

    return dst
