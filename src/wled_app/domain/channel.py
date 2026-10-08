"""Channel configuration and address offset domain models."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChannelConfig:
    """Configuration for an addressable LED channel / output strip.

    Attributes:
        channel_id: 1-based index of the channel (e.g. 1 for CH1).
        length: Number of LEDs connected to this channel (>= 0).
        start_index: Starting offset index in the controller's linear LED space.
        name: Optional human-readable name or label.
    """

    channel_id: int
    length: int
    start_index: int = 0
    name: str = ""

    def __post_init__(self) -> None:
        if self.channel_id < 1:
            raise ValueError(f"Channel ID must be >= 1, got {self.channel_id}")
        if self.length < 0:
            raise ValueError(f"Channel length cannot be negative, got {self.length}")
        if self.start_index < 0:
            raise ValueError(
                f"Channel start_index cannot be negative, got {self.start_index}"
            )

    @property
    def is_active(self) -> bool:
        """A channel is active if it has at least 1 LED configured."""
        return self.length > 0

    @property
    def end_index(self) -> int:
        """Exclusive end index in linear address space."""
        return self.start_index + self.length

    @property
    def display_name(self) -> str:
        """Formatted display name."""
        if self.name.strip():
            return f"CH{self.channel_id} ({self.name.strip()})"
        return f"CH{self.channel_id}"

    def to_dict(self) -> dict[str, int | str]:
        """Convert to JSON-serializable dictionary."""
        return {
            "channel_id": self.channel_id,
            "length": self.length,
            "start_index": self.start_index,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int | str]) -> ChannelConfig:
        """Parse from dictionary with type coercion and validation."""
        return cls(
            channel_id=int(data["channel_id"]),
            length=int(data.get("length", 0)),
            start_index=int(data.get("start_index", 0)),
            name=str(data.get("name", "")),
        )


def layout_channels(
    channel_specs: list[tuple[int, int] | tuple[int, int, str]],
) -> list[ChannelConfig]:
    """Calculate contiguous linear start offsets for a list of channel specifications.

    Args:
        channel_specs: List of (channel_id, length) or (channel_id, length, name).

    Returns:
        List of ChannelConfig objects with sequentially assigned start_index offsets.
    """
    sorted_specs = sorted(channel_specs, key=lambda s: s[0])
    configs: list[ChannelConfig] = []
    current_offset = 0

    for spec in sorted_specs:
        channel_id = spec[0]
        length = spec[1]
        name = spec[2] if len(spec) > 2 else ""

        config = ChannelConfig(
            channel_id=channel_id,
            length=length,
            start_index=current_offset if length > 0 else current_offset,
            name=name,
        )
        configs.append(config)
        if length > 0:
            current_offset += length

    return configs
