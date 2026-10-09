"""Visualizer Adapters connecting LightingEngine frames to visualizer sinks."""

from __future__ import annotations
from typing import Callable
from dataclasses import dataclass, field

from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.visualizer.ascii_canvas import AsciiCanvas
from wled_engine.core import LightingEngine


@dataclass
class VisualizerSink:
    """Subscriber receiving rendered engine frames for visualization."""
    callback: Callable[[DeviceConfig, FrameBuffer, float, int], None]
    device_id: str | None = None  # None means all devices


class VisualizerAdapter:
    """Manages visualizer sinks and terminal ASCII monitors for a LightingEngine."""

    def __init__(self, engine: LightingEngine) -> None:
        self.engine = engine
        self._sinks: list[VisualizerSink] = []
        self._ascii_canvases: dict[str, AsciiCanvas] = {}

        # Wire engine's on_frame to dispatch through this adapter
        self._previous_on_frame = self.engine.on_frame
        self.engine.on_frame = self._dispatch_frame

    def add_sink(
        self,
        callback: Callable[[DeviceConfig, FrameBuffer, float, int], None],
        device_id: str | None = None,
    ) -> VisualizerSink:
        """Register a callback sink to receive rendered frames."""
        sink = VisualizerSink(callback=callback, device_id=device_id)
        self._sinks.append(sink)
        return sink

    def remove_sink(self, sink: VisualizerSink) -> bool:
        """Unregister a frame callback sink."""
        if sink in self._sinks:
            self._sinks.remove(sink)
            return True
        return False

    def attach_ascii_canvas(
        self,
        device_id: str,
        max_strip_width: int = 48,
        use_color: bool = True,
    ) -> AsciiCanvas:
        """Attach an AsciiCanvas for real-time terminal channel rendering."""
        canvas = AsciiCanvas(max_strip_width=max_strip_width, use_color=use_color)
        self._ascii_canvases[device_id] = canvas
        return canvas

    def render_ascii(self, device: DeviceConfig, frame: FrameBuffer) -> str:
        """Render a single frame as ANSI ASCII art."""
        canvas = self._ascii_canvases.get(device.id)
        if canvas is None:
            canvas = self.attach_ascii_canvas(device.id)
        return canvas.render(device, frame)

    def _dispatch_frame(
        self,
        device: DeviceConfig,
        frame: FrameBuffer,
        fps: float,
        tick: int,
    ) -> None:
        """Internal dispatch of rendered frames to all registered sinks."""
        # 1. Forward to any previous on_frame handler
        if self._previous_on_frame:
            self._previous_on_frame(device, frame, fps, tick)

        # 2. Forward to registered visualizer sinks
        for sink in self._sinks:
            if sink.device_id is None or sink.device_id == device.id:
                sink.callback(device, frame, fps, tick)
