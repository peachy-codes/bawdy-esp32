"""Async orchestrator binding UDP receiver, WLED state machine, and Web server."""

from __future__ import annotations
import asyncio
from typing import Callable

from wled_simulator.models import ChannelInfo, TelemetryData
from wled_simulator.state_machine import WledStateMachine
from wled_simulator.udp_receiver import UdpReceiver
from wled_simulator.web_server import SimulatorWebServer


class SimulatorRunner:
    """Coordinates the UDP network receiver, WLED state machine, and Web UI server."""

    def __init__(
        self,
        channels: list[ChannelInfo],
        udp_host: str = "0.0.0.0",
        udp_port: int = 4048,
        web_host: str = "127.0.0.1",
        web_port: int = 8080,
    ) -> None:
        self.channels = channels
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.web_host = web_host
        self.web_port = web_port

        self.web_server = SimulatorWebServer(
            channels=self.channels,
            udp_port=self.udp_port,
            host=self.web_host,
            web_port=self.web_port,
        )

        self.state_machine = WledStateMachine(
            channels=self.channels,
            on_frame_rendered=self._on_frame_rendered,
        )

        self.udp_receiver = UdpReceiver(
            state_machine=self.state_machine,
            host=self.udp_host,
            port=self.udp_port,
        )

        self._running = False
        self._loop: asyncio.AbstractEventLoop | None = None

    def _on_frame_rendered(self, pixels: bytes, telemetry: TelemetryData) -> None:
        """Callback invoked when WLED executes a PUSH frame update."""
        if self._loop is not None and not self._loop.is_closed():
            self._loop.create_task(self.web_server.broadcast_frame(pixels, telemetry))

    async def start(self) -> None:
        """Start both UDP listener and HTTP/WebSocket web server."""
        self._loop = asyncio.get_running_loop()
        self._running = True

        await self.web_server.start()
        await self.udp_receiver.start()

    async def stop(self) -> None:
        """Gracefully shut down servers."""
        self._running = False
        self.udp_receiver.stop()
        await self.web_server.stop()

    async def run_forever(self) -> None:
        """Run until cancelled (e.g. via Ctrl+C)."""
        await self.start()
        try:
            while self._running:
                await asyncio.sleep(1.0)
        finally:
            await self.stop()
