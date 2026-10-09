"""Compositor and LayerStack manager for indexed Layers 0-9."""

from __future__ import annotations
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import Pattern, PatternConfig
from wled_engine.blend import BlendMode
from wled_engine.layer import Layer


class LayerStack:
    """Manages an ordered stack of 10 indexed layers (Layer 0 to Layer 9).

    Composited in ascending order: Layer 0 (bottom) up to Layer 9 (top).
    """

    MAX_LAYERS = 10

    def __init__(self) -> None:
        self._layers: list[Layer] = [
            Layer(index=i, enabled=False, opacity=0.0) for i in range(self.MAX_LAYERS)
        ]
        self._scratch_frame = FrameBuffer(0)
        self.master_brightness: float = 1.0

    def get_layer(self, index: int) -> Layer:
        """Retrieve layer by index (0..9)."""
        if not (0 <= index < self.MAX_LAYERS):
            raise IndexError(f"Layer index must be 0..{self.MAX_LAYERS - 1}, got {index}")
        return self._layers[index]

    def __getitem__(self, index: int) -> Layer:
        return self.get_layer(index)

    def set_layer(
        self,
        index: int,
        pattern: Pattern | None = None,
        pattern_config: PatternConfig | None = None,
        opacity: float = 1.0,
        blend_mode: BlendMode = BlendMode.ALPHA_BLEND,
        name: str | None = None,
        channel_ids: set[int] | None = None,
        enabled: bool = True,
    ) -> Layer:
        """Configure and enable an indexed layer."""
        layer = self.get_layer(index)
        layer.pattern = pattern
        if pattern_config is not None:
            layer.pattern_config = pattern_config
        layer.opacity = opacity
        layer.blend_mode = blend_mode
        if name is not None:
            layer.name = name
        layer.channel_ids = channel_ids
        layer.enabled = enabled
        return layer

    def clear_layer(self, index: int) -> None:
        """Disable and reset a layer."""
        layer = self.get_layer(index)
        layer.enabled = False
        layer.opacity = 0.0
        layer.pattern = None
        layer.channel_ids = None

    def clear_all(self) -> None:
        """Reset all layers 0..9."""
        for i in range(self.MAX_LAYERS):
            self.clear_layer(i)

    @property
    def active_layers(self) -> list[Layer]:
        """List of active layers currently contributing to the composite."""
        return [
            layer for layer in self._layers
            if layer.enabled and layer.opacity > 0.0 and layer.pattern is not None
        ]

    def composite(
        self,
        tick: int,
        dt: float,
        device: DeviceConfig,
        out_frame: FrameBuffer,
    ) -> FrameBuffer:
        """Composite all layers from Layer 0 up to Layer 9 into out_frame.

        Args:
            tick: Animation tick index.
            dt: Delta time elapsed since last frame (in seconds).
            device: Target DeviceConfig being rendered.
            out_frame: Destination FrameBuffer to write composite into.

        Returns:
            The composited FrameBuffer.
        """
        total_leds = device.total_leds
        if total_leds == 0:
            return out_frame

        # Ensure destination buffer matches size
        if len(out_frame) != total_leds:
            out_frame.pixels = [Color.black() for _ in range(total_leds)]
        else:
            out_frame.clear()

        # Update layer animations/tweens and composite in ascending order (0 -> 9)
        for layer in self._layers:
            layer.update(dt)
            layer.composite_into(tick, device, out_frame, self._scratch_frame)

        # Apply master brightness dimmer
        mb = max(0.0, min(1.0, self.master_brightness))
        if mb < 1.0:
            for i in range(total_leds):
                out_frame[i] = out_frame[i].dim(mb)

        return out_frame
