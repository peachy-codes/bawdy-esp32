"""Device configuration domain models and protocol types."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import ipaddress
import re
import uuid

from wled_app.domain.channel import ChannelConfig, layout_channels


class ProtocolType(str, Enum):
    """Supported WLED UDP protocols."""

    DDP = "ddp"
    DRGB = "drgb"
    DNRGB = "dnrgb"
    WARLS = "warls"

    @property
    def default_port(self) -> int:
        """Default UDP port for the protocol."""
        if self == ProtocolType.DDP:
            return 4048
        return 21324

    @property
    def display_name(self) -> str:
        """Friendly name with default port."""
        if self == ProtocolType.DDP:
            return "DDP (Distributed Display Protocol, Port 4048)"
        if self == ProtocolType.DRGB:
            return "DRGB (Direct RGB, Port 21324)"
        if self == ProtocolType.DNRGB:
            return "DNRGB (Direct Numbered RGB, Port 21324)"
        if self == ProtocolType.WARLS:
            return "WARLS (WLED Audio Reactive LED Strip, Port 21324)"
        return self.value.upper()


def validate_ip_or_host(host_str: str) -> str:
    """Validate and sanitize an IP address or hostname.

    Raises:
        ValueError: If host_str is not a valid IPv4/IPv6 address or hostname.
    """
    clean_host = host_str.strip()
    if not clean_host:
        raise ValueError("Host/IP address cannot be empty")

    try:
        ipaddress.ip_address(clean_host)
        return clean_host
    except ValueError:
        pass

    # If it is formatted like an IPv4 address (digits and dots), it failed ip_address so it's invalid
    if re.fullmatch(r"^\d+(\.\d+)+$", clean_host):
        raise ValueError(f"Invalid IP address: '{host_str}'")

    # Hostname pattern (RFC 1123): TLD must not be all-numeric
    labels = clean_host.split(".")
    if any(not (1 <= len(label) <= 63) for label in labels):
        raise ValueError(f"Invalid hostname label length: '{host_str}'")
    if labels[-1].isdigit():
        raise ValueError(f"Hostname TLD cannot be all-numeric: '{host_str}'")

    label_regex = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?$")
    if not all(label_regex.match(label) for label in labels) or len(clean_host) > 253:
        raise ValueError(f"Invalid hostname: '{host_str}'")

    return clean_host


@dataclass(frozen=True, slots=True)
class DeviceConfig:
    """Aggregate root representing an addressable WLED controller device.

    Attributes:
        id: Unique identifier for the device (UUID or alphanumeric slug).
        name: Human-friendly name (e.g. 'Athom-ESP32-LivingRoom').
        ip: Target IPv4/IPv6 address or hostname.
        port: UDP destination port (1..65535).
        protocol: WLED realtime protocol type.
        channels: Configured LED channels.
        description: Optional notes/metadata.
    """

    id: str
    name: str
    ip: str
    port: int
    protocol: ProtocolType
    channels: list[ChannelConfig] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Device ID cannot be empty")
        if not self.name.strip():
            raise ValueError("Device name cannot be empty")
        validate_ip_or_host(self.ip)
        if not (1 <= self.port <= 65535):
            raise ValueError(f"UDP port must be between 1 and 65535, got {self.port}")

    @property
    def total_leds(self) -> int:
        """Sum of LEDs across all active channels."""
        return sum(ch.length for ch in self.channels if ch.is_active)

    @property
    def active_channels(self) -> list[ChannelConfig]:
        """List of active channels (length > 0)."""
        return [ch for ch in self.channels if ch.is_active]

    def get_channel(self, channel_id: int) -> ChannelConfig | None:
        """Find channel by ID."""
        for ch in self.channels:
            if ch.channel_id == channel_id:
                return ch
        return None

    def update(
        self,
        name: str | None = None,
        ip: str | None = None,
        port: int | None = None,
        protocol: ProtocolType | None = None,
        channels: list[ChannelConfig] | None = None,
        description: str | None = None,
    ) -> DeviceConfig:
        """Create a new DeviceConfig instance with updated attributes, preserving the same ID."""
        return DeviceConfig(
            id=self.id,
            name=(name if name is not None else self.name).strip(),
            ip=validate_ip_or_host(ip if ip is not None else self.ip),
            port=port if port is not None else self.port,
            protocol=protocol if protocol is not None else self.protocol,
            channels=channels if channels is not None else self.channels,
            description=(description if description is not None else self.description).strip(),
        )

    @classmethod
    def create(
        cls,
        name: str,
        ip: str,
        channel_lengths: list[int | tuple[int, int] | tuple[int, int, str]],
        protocol: ProtocolType = ProtocolType.DDP,
        port: int | None = None,
        device_id: str | None = None,
        description: str = "",
    ) -> DeviceConfig:
        """Smart factory to build and validate a new DeviceConfig.

        Args:
            name: Human friendly device name.
            ip: Destination IP or hostname.
            channel_lengths: Either list of lengths [ch1_len, ch2_len, ...]
                             or list of tuples [(ch_id, len), ...].
            protocol: ProtocolType (defaults to DDP).
            port: UDP port (defaults to protocol.default_port if None).
            device_id: Optional ID (generates UUID if omitted).
            description: Optional notes.
        """
        clean_ip = validate_ip_or_host(ip)
        actual_port = port if port is not None else protocol.default_port

        specs: list[tuple[int, int, str]] = []
        for idx, item in enumerate(channel_lengths, start=1):
            if isinstance(item, int):
                specs.append((idx, max(0, item), f"Channel {idx}"))
            elif isinstance(item, tuple):
                ch_id = item[0]
                length = max(0, item[1])
                ch_name = item[2] if len(item) > 2 else f"Channel {ch_id}"
                specs.append((ch_id, length, ch_name))

        channels = layout_channels(specs)
        actual_id = device_id or str(uuid.uuid4())[:8]

        return cls(
            id=actual_id,
            name=name.strip(),
            ip=clean_ip,
            port=actual_port,
            protocol=protocol,
            channels=channels,
            description=description.strip(),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize device to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "protocol": self.protocol.value,
            "channels": [ch.to_dict() for ch in self.channels],
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> DeviceConfig:
        """Deserialize device from a dictionary."""
        protocol_str = str(data.get("protocol", ProtocolType.DDP.value)).lower()
        protocol = ProtocolType(protocol_str)

        raw_channels = data.get("channels", [])
        channels = [
            ChannelConfig.from_dict(ch)
            for ch in raw_channels  # type: ignore[arg-type]
        ]

        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            ip=validate_ip_or_host(str(data["ip"])),
            port=int(data.get("port", protocol.default_port)),
            protocol=protocol,
            channels=channels,
            description=str(data.get("description", "")),
        )
