"""Pattern registry and factory."""

from __future__ import annotations
from wled_app.patterns.base import Pattern, PatternConfig
from wled_app.patterns.blink import BlinkPattern
from wled_app.patterns.chase import ChasePattern
from wled_app.patterns.color_wipe import ColorWipePattern
from wled_app.patterns.cylon import CylonPattern
from wled_app.patterns.fire import FirePattern
from wled_app.patterns.gradient import GradientPattern
from wled_app.patterns.meteor import MeteorPattern
from wled_app.patterns.rainbow import RainbowPattern
from wled_app.patterns.solid import SolidPattern
from wled_app.patterns.twinkle import TwinklePattern
from wled_app.patterns.wave import WavePattern

_REGISTERED_PATTERNS: dict[str, type[Pattern]] = {
    "rainbow": RainbowPattern,
    "chase": ChasePattern,
    "fire": FirePattern,
    "meteor": MeteorPattern,
    "cylon": CylonPattern,
    "twinkle": TwinklePattern,
    "wave": WavePattern,
    "gradient": GradientPattern,
    "blink": BlinkPattern,
    "wipe": ColorWipePattern,
    "solid": SolidPattern,
}


def list_patterns() -> list[Pattern]:
    """Return instances of all registered patterns."""
    return [cls() for cls in _REGISTERED_PATTERNS.values()]


def get_pattern(pattern_id: str) -> Pattern:
    """Retrieve an instantiated pattern by ID."""
    key = pattern_id.strip().lower()
    pattern_cls = _REGISTERED_PATTERNS.get(key)
    if not pattern_cls:
        available = list(_REGISTERED_PATTERNS.keys())
        raise ValueError(f"Pattern '{pattern_id}' not found. Available: {available}")
    return pattern_cls()
