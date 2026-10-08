"""High-fidelity Terminal ASCII visualizer with Truecolor and 256-color LED emulation.

Accurately reflects real-time addressable LED colors, peak brightness,
and individual channel activities on all terminal emulators (including macOS Terminal.app).
"""

from __future__ import annotations
import os
import shutil
from typing import Sequence

from wled_app.domain.channel import ChannelConfig
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer

# Character ramps for monochrome fallback
_MONOCHROME_RAMP = " .:-=+*#%@"
_ANSI_RESET = "\033[0m"


def _rgb_to_ansi256(r: int, g: int, b: int) -> int:
    """Map 24-bit RGB to the standard xterm 256-color palette index.

    Supported universally by macOS Terminal.app and all standard terminal emulators.
    """
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return round(((r - 8) / 247) * 23) + 232
    r6 = round(r / 255 * 5)
    g6 = round(g / 255 * 5)
    b6 = round(b / 255 * 5)
    return 16 + 36 * r6 + 6 * g6 + b6


def _supports_truecolor() -> bool:
    """Check if the active terminal supports 24-bit Truecolor.

    macOS Terminal.app famously only supports 256 colors and silently ignores 24-bit codes.
    """
    if os.environ.get("TERM_PROGRAM") == "Apple_Terminal":
        return False
    colorterm = os.environ.get("COLORTERM", "").lower()
    if colorterm in ("truecolor", "24bit"):
        return True
    term_program = os.environ.get("TERM_PROGRAM", "")
    if term_program in ("iTerm.app", "vscode", "Alacritty", "kitty", "WezTerm", "ghostty", "Hyper"):
        return True
    return False


def _color_codes(r: int, g: int, b: int) -> tuple[str, str]:
    """Generate ANSI foreground and background escape codes for RGB color."""
    if _supports_truecolor():
        return f"\033[38;2;{r};{g};{b}m", f"\033[48;2;{r};{g};{b}m"
    code = _rgb_to_ansi256(r, g, b)
    return f"\033[38;5;{code}m", f"\033[48;5;{code}m"


class AsciiCanvas:
    """Visualizes device LED channels as realistic Truecolor/256-color LED strips."""

    def __init__(
        self,
        max_strip_width: int = 48,
        use_color: bool = True,
        block_width: int = 2,
    ) -> None:
        self.max_strip_width = max(10, max_strip_width)
        self.use_color = use_color
        self.block_width = block_width  # 2 for square '██', 1 for '█'

    @staticmethod
    def _color_luminance(c: Color) -> float:
        """Compute relative luminance for energy/brightness comparison."""
        return 0.299 * c.r + 0.587 * c.g + 0.114 * c.b

    @classmethod
    def _resample_pixels(cls, pixels: Sequence[Color], target_width: int) -> list[Color]:
        """Peak-preserving downsampling.

        Preserves bright spots and vibrant colors so running chasers,
        sparkles, or pulses are never diluted by adjacent dark LEDs.
        """
        if not pixels:
            return []
        if len(pixels) <= target_width:
            return list(pixels)

        result: list[Color] = []
        n = len(pixels)
        for i in range(target_width):
            start_f = (i * n) / target_width
            end_f = ((i + 1) * n) / target_width
            start_idx = int(start_f)
            end_idx = min(n, int(end_f + 0.999999))

            bucket = pixels[start_idx:end_idx]
            if not bucket:
                bucket = [pixels[min(start_idx, n - 1)]]

            # Pick highest energy pixel to preserve active effects
            peak_pixel = max(bucket, key=cls._color_luminance)
            peak_lum = cls._color_luminance(peak_pixel)

            if peak_lum > 5.0:
                # Active lit LED in this segment
                result.append(peak_pixel)
            else:
                # Completely dark segment
                result.append(Color.black())

        return result

    def render_channel(
        self,
        channel: ChannelConfig,
        pixels: Sequence[Color],
        target_width: int | None = None,
    ) -> str:
        """Render a single channel into a colored LED strip display."""
        if not channel.is_active:
            name_part = f"CH{channel.channel_id}"
            if channel.name.strip():
                name_part += f" ({channel.name.strip()})"
            return f"{name_part:<17} [Disabled]"

        # Determine target display width
        max_cells = target_width or self.max_strip_width
        actual_cells = min(channel.length, max_cells)
        sampled = self._resample_pixels(pixels, actual_cells)

        blocks: list[str] = []
        unit = "██" if self.block_width == 2 else "█"
        off_unit = "··" if self.block_width == 2 else "·"

        for p in sampled:
            if self.use_color:
                if p.is_black() or (p.r < 8 and p.g < 8 and p.b < 8):
                    # Unlit dark diode socket
                    blocks.append(f"\033[90m{off_unit}{_ANSI_RESET}")
                else:
                    fg, bg = _color_codes(p.r, p.g, p.b)
                    # Set both fg and bg to ensure 100% solid, vivid block rendering in any terminal
                    blocks.append(f"{fg}{bg}{unit}{_ANSI_RESET}")
            else:
                lum = int(self._color_luminance(p) / 255 * (len(_MONOCHROME_RAMP) - 1))
                char = _MONOCHROME_RAMP[lum]
                blocks.append(char * self.block_width)

        strip_str = "".join(blocks)
        name_part = f"CH{channel.channel_id}"
        if channel.name.strip():
            name_part += f" ({channel.name.strip()})"
        length_part = f"[{channel.length:>3} LEDs]"

        # Calculate dominant color swatch badge for this channel
        active_pixels = [p for p in pixels if not p.is_black()]
        if active_pixels and self.use_color:
            avg_r = sum(p.r for p in active_pixels) // len(active_pixels)
            avg_g = sum(p.g for p in active_pixels) // len(active_pixels)
            avg_b = sum(p.b for p in active_pixels) // len(active_pixels)
            swatch_fg, _ = _color_codes(avg_r, avg_g, avg_b)
            swatch = f" {swatch_fg}●{_ANSI_RESET} "
        else:
            swatch = " \033[90m○\033[0m "

        return f"{name_part:<17} {length_part:<10} {swatch}|{strip_str}|"

    def render(
        self,
        device: DeviceConfig,
        frame: FrameBuffer,
        title: str = "",
        fps: float | None = None,
    ) -> str:
        """Render complete device state with all active channels."""
        terminal_cols = shutil.get_terminal_size(fallback=(90, 24)).columns
        # Reserve ~34 chars for prefixes: "CH1 (Name)  [ 60 LEDs]  ● |...|"
        available_width = max(10, (terminal_cols - 36) // self.block_width)
        max_cells = min(self.max_strip_width, available_width)

        lines: list[str] = []
        # Header banner
        header = f"=== {device.name} [{device.ip}:{device.port} ({device.protocol.value.upper()})] ==="
        if title:
            header += f" :: {title}"
        if fps is not None:
            header += f" :: {fps:.1f} FPS"

        lines.append(header)
        lines.append("─" * len(header))

        if not device.active_channels:
            lines.append("  (No active channels configured)")
        else:
            for ch in device.channels:
                ch_pixels = frame.get_channel_pixels(ch)
                line = self.render_channel(ch, ch_pixels, target_width=max_cells)
                lines.append(line)

        lines.append("─" * len(header))
        lines.append(f"Active Channels: {len(device.active_channels)} | Total LEDs: {device.total_leds}")
        return "\n".join(lines)
