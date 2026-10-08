"""Base interfaces and protocols for WLED UDP packet encoders."""

from __future__ import annotations
from typing import Protocol, runtime_checkable

from wled_app.domain.device import ProtocolType
from wled_app.domain.frame import FrameBuffer


@runtime_checkable
class ProtocolEmitter(Protocol):
    """Protocol for converting a FrameBuffer into one or more UDP datagram payloads."""

    @property
    def protocol_type(self) -> ProtocolType:
        """The protocol type represented by this emitter."""
        ...

    @property
    def default_port(self) -> int:
        """Default UDP port for this protocol."""
        ...

    def encode_frame(
        self,
        frame: FrameBuffer,
        timeout_sec: int = 2,
    ) -> list[bytes]:
        """Convert a FrameBuffer into a sequence of UDP datagram payloads.

        Args:
            frame: The frame containing pixel colors.
            timeout_sec: Realtime timeout in seconds (used by WLED protocols).

        Returns:
            List of raw byte payloads ready to be sent over UDP.
        """
        ...
