"""UDP Client and MockUDPClient for WLED network packet transmission."""

from __future__ import annotations
import socket
from typing import Protocol, Sequence, runtime_checkable


@runtime_checkable
class UdpSender(Protocol):
    """Interface for sending UDP datagrams."""

    def send_packet(self, ip: str, port: int, packet: bytes) -> int:
        """Send a single packet. Returns number of bytes sent."""
        ...

    def send_packets(self, ip: str, port: int, packets: Sequence[bytes]) -> int:
        """Send multiple packets. Returns total bytes sent."""
        ...

    def close(self) -> None:
        """Close client resources."""
        ...


class UdpClient:
    """Standard UDP network client using BSD sockets."""

    def __init__(self, broadcast: bool = False, timeout: float = 1.0) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if broadcast:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socket.settimeout(timeout)
        self._closed = False

    def send_packet(self, ip: str, port: int, packet: bytes) -> int:
        if self._closed:
            raise RuntimeError("UdpClient is closed")
        return self._socket.sendto(packet, (ip, port))

    def send_packets(self, ip: str, port: int, packets: Sequence[bytes]) -> int:
        total = 0
        for pkt in packets:
            total += self.send_packet(ip, port, pkt)
        return total

    def close(self) -> None:
        if not self._closed:
            self._socket.close()
            self._closed = True

    def __enter__(self) -> UdpClient:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()


class MockUdpClient:
    """In-memory fake UDP client for hermetic testing and dry-run preview mode."""

    def __init__(self) -> None:
        self.sent_packets: list[tuple[str, int, bytes]] = []
        self._closed = False

    def send_packet(self, ip: str, port: int, packet: bytes) -> int:
        if self._closed:
            raise RuntimeError("MockUdpClient is closed")
        self.sent_packets.append((ip, port, packet))
        return len(packet)

    def send_packets(self, ip: str, port: int, packets: Sequence[bytes]) -> int:
        total = 0
        for pkt in packets:
            total += self.send_packet(ip, port, pkt)
        return total

    def clear(self) -> None:
        self.sent_packets.clear()

    def close(self) -> None:
        self._closed = True

    def __enter__(self) -> MockUdpClient:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()
