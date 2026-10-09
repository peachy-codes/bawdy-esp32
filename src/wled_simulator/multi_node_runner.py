"""Multi-node orchestrator managing 20+ virtual WLED ESP32 boards and the Spatial Universe."""

from __future__ import annotations
import asyncio
import time
from typing import Any, Callable

from wled_app.domain.color import Color
from wled_engine.patch.patch_table import PatchTable
from wled_engine.spatial.universe import SpatialUniverse
from wled_simulator.models import ChannelInfo, TelemetryData, IntegrityStatus
from wled_simulator.state_machine import WledStateMachine
from wled_simulator.udp_receiver import UdpReceiver
from wled_simulator.web_server import SimulatorWebServer


class MultiNodeSimulatorRunner:
    """Manages an aggregate fleet of virtual WLED ESP32 controllers mapped to a 3D Spatial Universe.

    Simulates multiple hardware boards on distinct UDP ports (e.g. 4048..4067) or shared subnet,
    re-assembles physical WS2812B wire buffers according to the PatchTable, and streams the
    composite venue canvas over WebSockets to the HTML5 visualizer.
    """

    def __init__(
        self,
        universe: SpatialUniverse,
        patch_table: PatchTable,
        base_port: int = 4048,
        controller_ports: dict[str, int] | None = None,
        web_host: str = "127.0.0.1",
        web_port: int = 8080,
        sync_port: int = 4048,
    ) -> None:
        self.universe = universe
        self.patch_table = patch_table
        self.base_port = base_port
        self.controller_ports = controller_ports or {}
        self.web_host = web_host
        self.web_port = web_port
        self.sync_port = sync_port

        # Initialize web server with universe & patch metadata
        self.web_server = SimulatorWebServer(
            channels=[],
            udp_port=self.sync_port,
            host=self.web_host,
            web_port=self.web_port,
            universe_meta=self.universe.to_visualizer_dict(),
            patch_meta=self.patch_table.to_dict(),
        )

        self._state_machines: dict[str, WledStateMachine] = {}
        self._receivers: list[UdpReceiver] = []
        self._node_buffers: dict[str, bytes] = {}
        self._node_telemetries: dict[str, TelemetryData] = {}
        self._node_ports: dict[str, int] = {}

        self._running = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._last_universe_frame_time = 0.0
        self._frame_count = 0
        self._fps = 0.0

        self._init_controllers()

    def _init_controllers(self) -> None:
        """Create a virtual WLED ESP32 state machine and UDP receiver for each controller in the patch."""
        controllers = self.patch_table.get_controllers()
        if not controllers:
            controllers = ["wled_node_01"]

        # Track ports already bound to handle shared port cases
        port_to_machines: dict[int, list[WledStateMachine]] = {}

        for idx, cid in enumerate(controllers):
            port = self.controller_ports.get(cid, self.base_port + idx)
            self._node_ports[cid] = port

            # Discover channels for this controller
            ch_indices = self.patch_table.get_channel_indices(cid)
            if not ch_indices:
                ch_indices = [0]

            channels: list[ChannelInfo] = []
            current_offset = 0
            for ch in ch_indices:
                length = self.patch_table.get_channel_pixel_length(cid, ch)
                if length <= 0:
                    length = 270  # Default fallback length
                channels.append(
                    ChannelInfo(
                        channel_id=ch + 1,
                        length=length,
                        start_index=current_offset,
                        name=f"{cid}_ch{ch}",
                    )
                )
                current_offset += length

            sm = WledStateMachine(
                channels=channels,
                on_frame_rendered=lambda pixels, tel, c=cid: self._on_node_frame(c, pixels, tel),
            )
            self._state_machines[cid] = sm
            self._node_buffers[cid] = sm.get_pixel_bytes()
            self._node_telemetries[cid] = sm.get_telemetry()

            port_to_machines.setdefault(port, []).append(sm)

        # Create UDP receivers for all bound ports
        for port, sms in port_to_machines.items():
            primary_sm = sms[0]
            # Receiver dispatches to primary state machine (or multiplexes)
            recv = UdpReceiver(
                state_machine=primary_sm,
                host="0.0.0.0",
                port=port,
            )
            self._receivers.append(recv)

    def _on_node_frame(self, controller_id: str, pixels: bytes, telemetry: TelemetryData) -> None:
        """Invoked when an individual virtual board completes a frame."""
        self._node_buffers[controller_id] = pixels
        self._node_telemetries[controller_id] = telemetry

        if self._loop is not None and not self._loop.is_closed():
            self._render_universe_and_broadcast()

    def _render_universe_and_broadcast(self) -> None:
        """Unpack all controller wire buffers into unified universe pixels and broadcast to WebSocket."""
        now = time.perf_counter()
        if now - self._last_universe_frame_time < 0.010:  # Throttle to max 100 FPS
            return
        dt = now - self._last_universe_frame_time
        self._last_universe_frame_time = now
        if dt > 0:
            self._fps = 0.9 * self._fps + 0.1 * (1.0 / dt)

        # Unpack wire bytes to fixture colors
        fixture_bytes = self.patch_table.unpack_controller_buffers_to_fixtures(self._node_buffers)

        # Assemble global universe bytearray in fixture order
        universe_frame = bytearray()
        for fixture in self.universe.fixtures:
            fb = fixture_bytes.get(fixture.id)
            needed_bytes = fixture.pixel_count * 3
            if fb is not None and len(fb) >= needed_bytes:
                universe_frame.extend(fb[:needed_bytes])
            elif fb is not None:
                universe_frame.extend(fb)
                universe_frame.extend(b"\x00" * (needed_bytes - len(fb)))
            else:
                universe_frame.extend(b"\x00" * needed_bytes)

        # Compute aggregate telemetry
        total_pps = sum(t.pps for t in self._node_telemetries.values())
        total_kbps = sum(t.kbps for t in self._node_telemetries.values())
        node_stats = {
            cid: {
                "port": self._node_ports.get(cid, 0),
                "fps": round(t.fps, 1),
                "pps": round(t.pps, 1),
                "kbps": round(t.kbps, 1),
                "status": t.integrity_status.value,
            }
            for cid, t in self._node_telemetries.items()
        }

        telemetry_dict = {
            "fps": round(self._fps, 1),
            "pps": round(total_pps, 1),
            "kbps": round(total_kbps, 1),
            "nodes_count": len(self._state_machines),
            "total_pixels": self.universe.total_pixels,
            "nodes": node_stats,
            "integrity_status": "healthy",
        }

        if self._loop is not None and not self._loop.is_closed():
            self._loop.create_task(
                self.web_server.broadcast_frame(bytes(universe_frame), telemetry_dict)
            )

    def inject_fixture_colors(self, fixture_colors: dict[str, list[Color]]) -> None:
        """Direct software injection of fixture colors bypassing UDP sockets (for pattern previews)."""
        universe_frame = bytearray()
        for fixture in self.universe.fixtures:
            cols = fixture_colors.get(fixture.id, [])
            for i in range(fixture.pixel_count):
                if i < len(cols):
                    c = cols[i]
                    universe_frame.extend((c.r, c.g, c.b))
                else:
                    universe_frame.extend((0, 0, 0))

        telemetry_dict = {
            "fps": 30.0,
            "pps": 0,
            "kbps": 0.0,
            "nodes_count": len(self._state_machines),
            "total_pixels": self.universe.total_pixels,
            "nodes": {},
            "integrity_status": "direct_injection",
        }

        if self._loop is not None and not self._loop.is_closed():
            self._loop.create_task(
                self.web_server.broadcast_frame(bytes(universe_frame), telemetry_dict)
            )

    async def start(self) -> None:
        """Start HTTP/WS web server and all controller UDP listeners."""
        self._loop = asyncio.get_running_loop()
        self._running = True

        await self.web_server.start()
        for recv in self._receivers:
            await recv.start()

    async def stop(self) -> None:
        """Gracefully shut down all receivers and web server."""
        self._running = False
        for recv in self._receivers:
            recv.stop()
        self._receivers.clear()
        await self.web_server.stop()

    async def run_forever(self) -> None:
        """Run until cancelled (Ctrl+C)."""
        await self.start()
        try:
            while self._running:
                await asyncio.sleep(1.0)
        finally:
            await self.stop()
