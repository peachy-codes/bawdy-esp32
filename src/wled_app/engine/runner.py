"""Animation Runner adapter coordinating pattern generation, UDP transmission, and frame callbacks via LightingEngine."""

from __future__ import annotations
from typing import Callable

from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.network.udp_client import MockUdpClient, UdpClient, UdpSender
from wled_app.patterns.base import Pattern, PatternConfig
from wled_app.protocols.base import ProtocolEmitter
from wled_app.protocols.registry import get_emitter
from wled_engine.blend import BlendMode
from wled_engine.core import LightingEngine


class AnimationRunner:
    """CLI/TUI Adapter over the headless LightingEngine.

    Coordinates real-time rendering, multi-layer compositing, and UDP transmission
    while maintaining 100% backward-compatible API with existing CLI & TUI consumers.
    """

    def __init__(
        self,
        device: DeviceConfig,
        pattern: Pattern,
        pattern_config: PatternConfig | None = None,
        emitter: ProtocolEmitter | None = None,
        sender: UdpSender | None = None,
        target_fps: float = 30.0,
        dry_run: bool = False,
        on_frame: Callable[[FrameBuffer, float, int], None] | None = None,
    ) -> None:
        self.device = device
        self.pattern = pattern
        self.pattern_config = pattern_config or PatternConfig()
        self.emitter = emitter or get_emitter(device.protocol)
        self.dry_run = dry_run
        self.target_fps = max(1.0, min(120.0, target_fps))
        self.on_frame = on_frame

        if sender is not None:
            self.sender = sender
            self._owns_sender = False
        else:
            self.sender = MockUdpClient() if dry_run else UdpClient()
            self._owns_sender = True

        # Initialize underlying headless LightingEngine
        self.engine = LightingEngine(
            target_fps=self.target_fps,
            dry_run=dry_run,
        )

        # Register device with engine fleet
        self.node = self.engine.add_device(
            device=self.device,
            emitter=self.emitter,
            sender=self.sender,
        )

        # Set Layer 0 as the active primary pattern
        self.engine.set_layer_pattern(
            0,
            pattern=self.pattern,
            pattern_config=self.pattern_config,
            opacity=1.0,
            blend_mode=BlendMode.OVERWRITE,
        )

        # Reference to the composited frame buffer for backward compatibility
        self.frame = self.node.frame

    @property
    def is_running(self) -> bool:
        return self.engine.is_running

    @property
    def current_tick(self) -> int:
        return self.engine.current_tick

    @property
    def actual_fps(self) -> float:
        return self.engine.actual_fps

    def step(self, tick: int | None = None) -> FrameBuffer:
        """Execute a single animation frame via the LightingEngine."""
        current_tick = self.engine.current_tick if tick is None else tick
        self.engine.step(
            custom_dt=1.0 / self.target_fps if tick is not None else None,
            tick=tick,
        )

        if self.on_frame:
            self.on_frame(self.frame, self.actual_fps, current_tick)

        return self.frame

    def run(self, max_frames: int | None = None) -> None:
        """Run the animation loop synchronously until stopped or max_frames reached."""
        if self.on_frame:
            def _engine_on_frame(dev: DeviceConfig, fb: FrameBuffer, fps: float, tick: int) -> None:
                if self.on_frame:
                    self.on_frame(fb, fps, tick)
            self.engine.on_frame = _engine_on_frame

        try:
            self.engine.run(max_frames=max_frames)
        finally:
            self.close()

    def start_background(self) -> None:
        """Start animation loop in a background daemon thread."""
        if self.on_frame:
            def _engine_on_frame(dev: DeviceConfig, fb: FrameBuffer, fps: float, tick: int) -> None:
                if self.on_frame:
                    self.on_frame(fb, fps, tick)
            self.engine.on_frame = _engine_on_frame
        self.engine.start()

    def stop(self, timeout: float = 2.0) -> None:
        """Signal the animation loop to stop and wait for completion."""
        self.engine.stop(timeout=timeout)
        self.close()

    def close(self) -> None:
        """Clean up resources."""
        self.engine.close()
        if self._owns_sender:
            self.sender.close()
