"""Base interfaces and configuration for pattern generators."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from wled_app.domain.channel import ChannelConfig
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer


@dataclass
class PatternConfig:
    """Configurable runtime parameters for a pattern generator.

    Attributes:
        speed: Speed multiplier (1.0 = standard speed, 2.0 = double, etc.).
        brightness: Master brightness scaling (0.0 to 1.0).
        primary_color: Main effect color.
        secondary_color: Background or accent color.
        direction: 1 for forward, -1 for reverse.
        sync_channels: True to mirror pattern across channels, False for linear flow.
        extra: Additional pattern-specific parameters.
    """

    speed: float = 1.0
    brightness: float = 1.0
    primary_color: Color = field(default_factory=Color.red)
    secondary_color: Color = field(default_factory=Color.black)
    direction: int = 1
    sync_channels: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration parameters to dictionary."""
        return {
            "speed": self.speed,
            "brightness": self.brightness,
            "primary_color": self.primary_color.to_hex(),
            "secondary_color": self.secondary_color.to_hex(),
            "direction": self.direction,
            "sync_channels": self.sync_channels,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PatternConfig:
        """Deserialize configuration parameters from dictionary."""
        prim_str = str(data.get("primary_color", "#FF0000"))
        sec_str = str(data.get("secondary_color", "#000000"))
        return cls(
            speed=float(data.get("speed", 1.0)),
            brightness=float(data.get("brightness", 1.0)),
            primary_color=Color.from_hex(prim_str),
            secondary_color=Color.from_hex(sec_str),
            direction=int(data.get("direction", 1)),
            sync_channels=bool(data.get("sync_channels", True)),
            extra=dict(data.get("extra", {})),
        )


@runtime_checkable
class Pattern(Protocol):
    """Protocol for animation pattern generators."""

    @property
    def id(self) -> str:
        """Unique identifier (e.g. 'rainbow', 'chase', 'blink')."""
        ...

    @property
    def name(self) -> str:
        """Human-readable display name."""
        ...

    @property
    def description(self) -> str:
        """Short description of the visual effect."""
        ...

    def render(
        self,
        tick: int,
        device: DeviceConfig,
        frame: FrameBuffer,
        config: PatternConfig,
    ) -> None:
        """Render a frame for the given device at animation tick into the FrameBuffer.

        Args:
            tick: Monotonically increasing animation frame count.
            device: Target device configuration.
            frame: Mutable FrameBuffer to populate.
            config: Runtime parameters and color settings.
        """
        ...
