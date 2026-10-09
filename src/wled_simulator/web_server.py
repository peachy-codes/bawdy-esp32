"""Asynchronous HTTP & WebSocket server for the WLED Digital Twin Web Canvas."""

from __future__ import annotations
import asyncio
import json
from pathlib import Path
from typing import Set

from aiohttp import WSMsgType, web
from wled_simulator.models import ChannelInfo, TelemetryData


class SimulatorWebServer:
    """Hosts the drag-and-drop web UI and streams binary LED frames over WebSockets."""

    def __init__(
        self,
        channels: list[ChannelInfo] | None = None,
        udp_port: int = 4048,
        host: str = "127.0.0.1",
        web_port: int = 8080,
        universe_meta: dict[str, Any] | None = None,
        patch_meta: dict[str, Any] | None = None,
    ) -> None:
        self.channels = channels or []
        self.udp_port = udp_port
        self.host = host
        self.web_port = web_port
        self.universe_meta = universe_meta
        self.patch_meta = patch_meta

        self._app = web.Application()
        self._sockets: Set[web.WebSocketResponse] = set()
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

        self._static_dir = Path(__file__).parent / "static"
        self._setup_routes()

        self._latest_pixels: bytes | None = None
        self._latest_telemetry: Any = None
        self._telemetry_counter = 0

    def _setup_routes(self) -> None:
        self._app.router.add_get("/", self._handle_index)
        self._app.router.add_get("/ws", self._handle_ws)
        self._app.router.add_static("/css/", path=self._static_dir / "css", name="css")
        self._app.router.add_static("/js/", path=self._static_dir / "js", name="js")

    async def _handle_index(self, request: web.Request) -> web.Response:
        """Serve the single-page HTML5 canvas application."""
        index_path = self._static_dir / "index.html"
        if not index_path.exists():
            return web.Response(text="<h1>Simulator UI Not Found</h1>", content_type="text/html", status=404)
        return web.FileResponse(index_path)

    async def _handle_ws(self, request: web.Request) -> web.WebSocketResponse:
        """Handle incoming WebSocket connection from the browser."""
        ws = web.WebSocketResponse(max_msg_size=1024 * 1024)
        await ws.prepare(request)
        self._sockets.add(ws)

        try:
            # Send initial channel or universe layout metadata
            if self.universe_meta is not None:
                init_payload = {
                    "mode": "universe",
                    "universe": self.universe_meta,
                    "patch": self.patch_meta,
                    "port": self.udp_port,
                    "fps": 0.0,
                    "pps": 0.0,
                    "kbps": 0.0,
                    "jitter_us": 0.0,
                    "integrity_status": "healthy",
                }
            else:
                init_payload = {
                    "mode": "single",
                    "channels": [
                        {
                            "channel_id": ch.channel_id,
                            "length": ch.length,
                            "start_index": ch.start_index,
                            "name": ch.name,
                        }
                        for ch in self.channels
                    ],
                    "port": self.udp_port,
                    "fps": 0.0,
                    "pps": 0.0,
                    "kbps": 0.0,
                    "jitter_us": 0.0,
                    "integrity_status": "healthy",
                }
            await ws.send_str(json.dumps(init_payload))

            # Send current frame if one exists
            if self._latest_pixels is not None:
                await ws.send_bytes(self._latest_pixels)

            async for msg in ws:
                if msg.type in (WSMsgType.CLOSE, WSMsgType.ERROR):
                    break
        finally:
            self._sockets.discard(ws)

        return ws

    async def broadcast_frame(self, pixels: bytes, telemetry: Any) -> None:
        """Broadcast updated RGB byte buffer and telemetry to all connected browsers."""
        self._latest_pixels = pixels
        self._latest_telemetry = telemetry

        if not self._sockets:
            return

        dead_sockets: list[web.WebSocketResponse] = []

        # Send binary RGB pixels
        for ws in self._sockets:
            try:
                await ws.send_bytes(pixels)
            except Exception:
                dead_sockets.append(ws)

        # Broadcast telemetry JSON every 2 frames
        self._telemetry_counter += 1
        if self._telemetry_counter % 2 == 0:
            if isinstance(telemetry, dict):
                telemetry_dict = dict(telemetry)
                telemetry_dict.setdefault("port", self.udp_port)
                telemetry_msg = json.dumps(telemetry_dict)
            elif hasattr(telemetry, "fps"):
                telemetry_msg = json.dumps({
                    "fps": telemetry.fps,
                    "pps": telemetry.pps,
                    "kbps": telemetry.kbps,
                    "jitter_us": getattr(telemetry, "jitter_us", 0.0),
                    "integrity_status": telemetry.integrity_status.value if hasattr(telemetry.integrity_status, "value") else str(telemetry.integrity_status),
                    "integrity_message": getattr(telemetry, "integrity_message", "Stream healthy"),
                    "port": self.udp_port,
                })
            else:
                telemetry_msg = json.dumps({"fps": 0.0, "port": self.udp_port})

            for ws in self._sockets:
                try:
                    await ws.send_str(telemetry_msg)
                except Exception:
                    dead_sockets.append(ws)

        for ws in dead_sockets:
            self._sockets.discard(ws)

    async def start(self) -> None:
        """Start aiohttp web server."""
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.web_port)
        await self._site.start()

    async def stop(self) -> None:
        """Gracefully close all WebSockets and stop the web server."""
        for ws in list(self._sockets):
            await ws.close()
        self._sockets.clear()

        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
            self._site = None
