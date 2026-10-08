"""Asynchronous UDP socket listener for WLED network datagrams."""

from __future__ import annotations
import asyncio
from typing import Callable
from wled_simulator.protocol_parser import ProtocolParser
from wled_simulator.state_machine import WledStateMachine


class WledDatagramProtocol(asyncio.DatagramProtocol):
    """Asyncio UDP protocol handler receiving WLED realtime packets."""

    def __init__(self, state_machine: WledStateMachine) -> None:
        super().__init__()
        self.state_machine = state_machine

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle incoming UDP datagram from the network."""
        # Try DDP first (10+ bytes with DDP header structure)
        ddp = ProtocolParser.parse_ddp(data)
        if ddp is not None:
            self.state_machine.process_ddp(ddp)
            return

        # Fallback to DRGB / DNRGB / WARLS
        drgb = ProtocolParser.parse_drgb(data)
        if drgb is not None:
            self.state_machine.process_drgb(drgb)


class UdpReceiver:
    """Manages the lifecycle of the async UDP listening socket."""

    def __init__(
        self,
        state_machine: WledStateMachine,
        host: str = "0.0.0.0",
        port: int = 4048,
    ) -> None:
        self.state_machine = state_machine
        self.host = host
        self.port = port
        self.transport: asyncio.DatagramTransport | None = None

    async def start(self) -> None:
        """Bind socket and begin receiving UDP datagrams."""
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: WledDatagramProtocol(self.state_machine),
            local_addr=(self.host, self.port),
        )
        self.transport = transport

    def stop(self) -> None:
        """Close UDP socket transport."""
        if self.transport is not None:
            self.transport.close()
            self.transport = None
