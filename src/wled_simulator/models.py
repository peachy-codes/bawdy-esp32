"""Domain models and data structures for the standalone WLED ESP32 Simulator."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class IntegrityStatus(str, Enum):
    """Integrity health of incoming multi-packet stream."""
    HEALTHY = "healthy"
    SEQUENCE_GAP = "sequence_gap"
    OUT_OF_ORDER = "out_of_order"
    TORN_FRAME = "torn_frame"
    TIMEOUT = "timeout"


@dataclass(slots=True, frozen=True)
class DdpDatagram:
    """Parsed Distributed Display Protocol (DDP) datagram."""
    flags: int
    sequence: int
    data_type: int
    dest_id: int
    offset: int
    length: int
    payload: bytes
    push: bool
    version: int = 1


@dataclass(slots=True, frozen=True)
class DrgbDatagram:
    """Parsed Direct RGB (DRGB) datagram."""
    command: int
    timeout: int
    payload: bytes
    start_led: int = 0


@dataclass(slots=True)
class ChannelInfo:
    """Metadata for a single LED channel on the simulated device."""
    channel_id: int
    length: int
    start_index: int
    name: str = ""

    @property
    def end_index(self) -> int:
        return self.start_index + self.length


@dataclass(slots=True)
class TelemetryData:
    """Real-time network and stream performance metrics."""
    fps: float = 0.0
    pps: float = 0.0
    kbps: float = 0.0
    total_packets: int = 0
    total_frames: int = 0
    jitter_us: float = 0.0
    integrity_status: IntegrityStatus = IntegrityStatus.HEALTHY
    integrity_message: str = "Stream healthy"
    last_packet_timestamp: float = 0.0
    active_channels: list[ChannelInfo] = field(default_factory=list)
