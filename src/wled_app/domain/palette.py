"""Color Palettes and Gradient Samplers for addressable LED patterns."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from wled_app.domain.color import Color


@dataclass(frozen=True, slots=True)
class ColorPalette:
    """Named sequence of color stops forming a continuous gradient."""

    name: str
    stops: tuple[Color, ...]

    def sample(self, t: float) -> Color:
        """Sample a color along the palette at normalized position t in [0.0, 1.0]."""
        if not self.stops:
            return Color.black()
        if len(self.stops) == 1:
            return self.stops[0]

        # Wrap t into [0.0, 1.0]
        pos = t % 1.0
        n_segments = len(self.stops) - 1
        segment_float = pos * n_segments
        idx = int(segment_float)
        frac = segment_float - idx

        idx = min(idx, n_segments - 1)
        c1 = self.stops[idx]
        c2 = self.stops[idx + 1]
        return c1.lerp(c2, frac)


# Predefined high-quality LED palettes
PALETTES: dict[str, ColorPalette] = {
    "fire": ColorPalette(
        name="Fire & Flame",
        stops=(
            Color(0, 0, 0),        # Unlit / black
            Color(180, 15, 0),     # Deep ember red
            Color(255, 60, 0),     # Hot orange
            Color(255, 180, 0),    # Bright amber
            Color(255, 255, 50),   # Yellow
            Color(255, 255, 255),  # White-hot core
        ),
    ),
    "cyberpunk": ColorPalette(
        name="Cyberpunk Neon",
        stops=(
            Color(0, 245, 255),    # Electric Cyan
            Color(120, 0, 255),    # Neon Violet
            Color(255, 0, 140),    # Hot Magenta
            Color(0, 245, 255),    # Loop to Cyan
        ),
    ),
    "sunset": ColorPalette(
        name="Tropical Sunset",
        stops=(
            Color(40, 0, 80),      # Night sky indigo
            Color(160, 0, 120),    # Sunset purple
            Color(255, 50, 60),    # Coral red
            Color(255, 140, 20),   # Warm orange
            Color(255, 220, 80),   # Golden horizon
            Color(40, 0, 80),      # Loop
        ),
    ),
    "ocean": ColorPalette(
        name="Deep Ocean",
        stops=(
            Color(0, 5, 40),       # Abyss navy
            Color(0, 40, 160),     # Deep blue
            Color(0, 140, 220),    # Azure
            Color(0, 240, 190),    # Seafoam aqua
            Color(180, 255, 240),  # White crest
            Color(0, 5, 40),       # Loop
        ),
    ),
    "forest": ColorPalette(
        name="Emerald Forest",
        stops=(
            Color(0, 30, 10),      # Dark foliage
            Color(0, 120, 30),     # Forest green
            Color(30, 220, 50),    # Lime emerald
            Color(0, 240, 160),    # Mint aurora
            Color(0, 30, 10),      # Loop
        ),
    ),
    "police": ColorPalette(
        name="Police Strobe",
        stops=(
            Color(255, 0, 0),      # Pure red
            Color(0, 0, 0),
            Color(0, 0, 255),      # Pure blue
            Color(0, 0, 0),
            Color(255, 0, 0),
        ),
    ),
    "party": ColorPalette(
        name="Party Confetti",
        stops=(
            Color(255, 0, 0),
            Color(255, 200, 0),
            Color(0, 255, 0),
            Color(0, 220, 255),
            Color(160, 0, 255),
            Color(255, 0, 150),
            Color(255, 0, 0),
        ),
    ),
}


def get_palette(name: str) -> ColorPalette:
    """Retrieve palette by name, case-insensitive."""
    key = name.strip().lower()
    if key in PALETTES:
        return PALETTES[key]
    raise ValueError(f"Unknown palette '{name}'. Available: {list(PALETTES.keys())}")


def list_palettes() -> list[ColorPalette]:
    """List all available palettes."""
    return list(PALETTES.values())
