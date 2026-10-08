"""Interactive terminal UI and wizards for WLED controller."""

from __future__ import annotations
import sys
import time
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig, ProtocolType, validate_ip_or_host
from wled_app.engine.runner import AnimationRunner
from wled_app.patterns.base import PatternConfig
from wled_app.patterns.registry import get_pattern, list_patterns
from wled_app.storage.device_repository import DeviceRepository
from wled_app.storage.preset_repository import Preset, PresetRepository
from wled_app.visualizer.ascii_canvas import AsciiCanvas


class InteractiveApp:
    """Main interactive terminal application."""

    def __init__(
        self,
        device_repo: DeviceRepository | None = None,
        preset_repo: PresetRepository | None = None,
        console: Console | None = None,
    ) -> None:
        self.console = console or Console()
        self.device_repo = device_repo or DeviceRepository()
        self.preset_repo = preset_repo or PresetRepository()
        self.current_device: DeviceConfig | None = None
        self.canvas = AsciiCanvas(use_color=True)

        # Attempt to auto-load the first available device
        all_devs = self.device_repo.list_all()
        if all_devs:
            self.current_device = all_devs[0]

    def run(self) -> None:
        """Run the main interactive event loop."""
        while True:
            self.console.clear()
            self._print_header()

            self.console.print("\n[bold cyan]Main Menu:[/bold cyan]")
            self.console.print("  [bold green]1.[/bold green] Select / Load Device")
            self.console.print("  [bold green]2.[/bold green] Create New Device (Athom ESP32 / Multi-channel)")
            self.console.print("  [bold green]3.[/bold green] Edit Existing Device")
            self.console.print("  [bold green]4.[/bold green] Inspect Current Device & ASCII Channel Monitor")
            self.console.print("  [bold green]5.[/bold green] Test / Stream Pattern (11 Dynamic Patterns)")
            self.console.print("  [bold green]6.[/bold green] Manage Saved Pattern Presets")
            self.console.print("  [bold green]7.[/bold green] Delete Current Device")
            self.console.print("  [bold red]0.[/bold red] Exit")

            choice = Prompt.ask("\nChoose an option", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="5")

            if choice == "0":
                self.console.print("[dim]Goodbye![/dim]")
                break
            elif choice == "1":
                self._menu_select_device()
            elif choice == "2":
                self._menu_create_device()
            elif choice == "3":
                self._menu_edit_device()
            elif choice == "4":
                self._menu_inspect_device()
            elif choice == "5":
                self._menu_stream_pattern()
            elif choice == "6":
                self._menu_manage_presets()
            elif choice == "7":
                self._menu_delete_device()

    def _print_header(self) -> None:
        """Display banner and active device overview."""
        title = "[bold magenta]ASCII UDP WLED Controller[/bold magenta] [dim]v0.1.0[/dim]"
        if self.current_device:
            status = (
                f"[bold]Active Device:[/bold] [yellow]{self.current_device.name}[/yellow] "
                f"({self.current_device.ip}:{self.current_device.port} | {self.current_device.protocol.value.upper()})\n"
                f"[bold]Channels:[/bold] {len(self.current_device.active_channels)} active "
                f"| [bold]Total LEDs:[/bold] {self.current_device.total_leds}"
            )
        else:
            status = "[italic yellow]No device selected. Create or load one below.[/italic yellow]"

        panel = Panel(f"{title}\n\n{status}", border_style="cyan")
        self.console.print(panel)

    def _menu_select_device(self) -> None:
        """List and load saved devices."""
        devices = self.device_repo.list_all()
        if not devices:
            self.console.print("[yellow]No saved devices found. Create one first![/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        table = Table(title="Saved Devices")
        table.add_column("#", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("IP:Port", style="cyan")
        table.add_column("Protocol", style="magenta")
        table.add_column("Active Channels", justify="center")
        table.add_column("Total LEDs", justify="right")

        for idx, dev in enumerate(devices, start=1):
            table.add_row(
                str(idx),
                dev.name,
                f"{dev.ip}:{dev.port}",
                dev.protocol.value.upper(),
                str(len(dev.active_channels)),
                str(dev.total_leds),
            )

        self.console.print(table)
        sel = IntPrompt.ask("Select device number (0 to cancel)", default=1)
        if 1 <= sel <= len(devices):
            self.current_device = devices[sel - 1]
            self.console.print(f"[green]Loaded device: {self.current_device.name}[/green]")
            time.sleep(1)

    def _menu_create_device(self) -> None:
        """Wizard to create and save a new device."""
        self.console.print("\n[bold cyan]=== Create New WLED Device ===[/bold cyan]")
        self.console.print("[dim]Configured for Athom Ethernet ESP32 (up to 4 channels) or arbitrary outputs.[/dim]\n")

        name = Prompt.ask("Device Name", default="Athom-ESP32")

        # IP address prompt with validation loop
        while True:
            ip_str = Prompt.ask("Target IP Address", default="192.168.1.150")
            try:
                clean_ip = validate_ip_or_host(ip_str)
                break
            except ValueError as err:
                self.console.print(f"[red]Error: {err}. Please re-enter.[/red]")

        # Protocol selection
        self.console.print("\n[bold]Select Realtime Protocol:[/bold]")
        self.console.print("  [cyan]1. DDP[/cyan]   - Distributed Display Protocol (Port 4048) [green][Recommended for Athom/ESP32][/green]")
        self.console.print("  [cyan]2. DRGB[/cyan]  - Direct RGB (Port 21324)")
        self.console.print("  [cyan]3. DNRGB[/cyan] - Direct Numbered RGB (Port 21324)")
        self.console.print("  [cyan]4. WARLS[/cyan] - WLED Audio-Reactive RGB (Port 21324)")
        proto_choice = Prompt.ask("Protocol", choices=["1", "2", "3", "4"], default="1")
        proto_map = {
            "1": ProtocolType.DDP,
            "2": ProtocolType.DRGB,
            "3": ProtocolType.DNRGB,
            "4": ProtocolType.WARLS,
        }
        protocol = proto_map[proto_choice]
        port = IntPrompt.ask("UDP Port", default=protocol.default_port)

        # Channel lengths (Athom has 4 channels CH1-CH4)
        self.console.print("\n[bold]Configure Channels (Athom ESP32 supports 4 outputs; enter 0 to disable):[/bold]")
        num_channels = IntPrompt.ask("Number of channels to configure", default=4)
        num_channels = max(1, min(16, num_channels))

        channel_lengths: list[tuple[int, int, str]] = []
        for i in range(1, num_channels + 1):
            default_len = 60 if i == 1 else (30 if i == 2 else 0)
            length = IntPrompt.ask(f"  CH{i} LED strip length", default=default_len)
            ch_name = Prompt.ask(f"  CH{i} custom label (optional)", default=f"Strip {i}")
            channel_lengths.append((i, max(0, length), ch_name))

        desc = Prompt.ask("Optional description", default="Athom Ethernet ESP32 WLED Controller")

        new_device = DeviceConfig.create(
            name=name,
            ip=clean_ip,
            channel_lengths=channel_lengths,
            protocol=protocol,
            port=port,
            description=desc,
        )

        self.console.print("\n[bold green]Device Configured Successfully![/bold green]")
        self.console.print(f"Total addressable LEDs: [bold]{new_device.total_leds}[/bold]")
        for ch in new_device.active_channels:
            self.console.print(
                f"  {ch.display_name}: {ch.length} LEDs (Indices {ch.start_index}..{ch.end_index - 1})"
            )

        if Confirm.ask("\nSave this device to disk?", default=True):
            saved_path = self.device_repo.save(new_device)
            self.console.print(f"[green]Saved to {saved_path}[/green]")

        self.current_device = new_device
        Prompt.ask("\nPress Enter to continue")

    def _menu_edit_device(self) -> None:
        """Edit an existing device configuration."""
        devices = self.device_repo.list_all()
        if not devices:
            self.console.print("[yellow]No saved devices found to edit. Create one first![/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        device_to_edit: DeviceConfig | None = self.current_device

        # If a device is already loaded, ask whether to edit it or pick a different one
        if device_to_edit is not None and len(devices) > 1:
            if not Confirm.ask(f"Edit currently active device '{device_to_edit.name}'?", default=True):
                device_to_edit = None

        if device_to_edit is None:
            table = Table(title="Select Device to Edit")
            table.add_column("#", style="dim")
            table.add_column("Name", style="bold green")
            table.add_column("IP:Port", style="cyan")
            table.add_column("Protocol", style="magenta")
            table.add_column("Channels", justify="right")
            for idx, dev in enumerate(devices, start=1):
                table.add_row(
                    str(idx),
                    dev.name,
                    f"{dev.ip}:{dev.port}",
                    dev.protocol.value.upper(),
                    str(len(dev.channels)),
                )
            self.console.print(table)
            sel = IntPrompt.ask("Select device number (0 to cancel)", default=1)
            if not (1 <= sel <= len(devices)):
                return
            device_to_edit = devices[sel - 1]

        self.console.print(f"\n[bold cyan]=== Edit Device: {device_to_edit.name} (ID: {device_to_edit.id}) ===[/bold cyan]")
        self.console.print("[dim]Press Enter on any prompt to retain its current value.[/dim]\n")

        new_name = Prompt.ask("Device Name", default=device_to_edit.name)

        while True:
            ip_str = Prompt.ask("Target IP Address", default=device_to_edit.ip)
            try:
                new_ip = validate_ip_or_host(ip_str)
                break
            except ValueError as err:
                self.console.print(f"[red]Error: {err}. Please re-enter.[/red]")

        # Protocol
        self.console.print(f"\nCurrent Protocol: [cyan]{device_to_edit.protocol.display_name}[/cyan]")
        if Confirm.ask("Change protocol?", default=False):
            self.console.print("  [cyan]1. DDP[/cyan]   - Distributed Display Protocol (Port 4048) [green][Recommended for Athom/ESP32][/green]")
            self.console.print("  [cyan]2. DRGB[/cyan]  - Direct RGB (Port 21324)")
            self.console.print("  [cyan]3. DNRGB[/cyan] - Direct Numbered RGB (Port 21324)")
            self.console.print("  [cyan]4. WARLS[/cyan] - WLED Audio-Reactive RGB (Port 21324)")
            proto_choice = Prompt.ask("Protocol", choices=["1", "2", "3", "4"], default="1")
            proto_map = {
                "1": ProtocolType.DDP,
                "2": ProtocolType.DRGB,
                "3": ProtocolType.DNRGB,
                "4": ProtocolType.WARLS,
            }
            new_protocol = proto_map[proto_choice]
            new_port = IntPrompt.ask("UDP Port", default=new_protocol.default_port)
        else:
            new_protocol = device_to_edit.protocol
            new_port = IntPrompt.ask("UDP Port", default=device_to_edit.port)

        # Channels
        self.console.print("\nCurrent Channels:")
        for ch in device_to_edit.channels:
            status = f"{ch.length} LEDs" if ch.is_active else "Disabled"
            self.console.print(f"  • {ch.display_name}: {status}")

        if Confirm.ask("\nEdit channels & LED strip lengths?", default=False):
            num_channels = IntPrompt.ask("Number of channels", default=max(4, len(device_to_edit.channels)))
            num_channels = max(1, min(16, num_channels))
            specs: list[tuple[int, int, str]] = []
            for i in range(1, num_channels + 1):
                existing_ch = device_to_edit.get_channel(i)
                def_len = existing_ch.length if existing_ch else 0
                def_name = existing_ch.name if (existing_ch and existing_ch.name) else f"Strip {i}"
                ch_len = IntPrompt.ask(f"  CH{i} LED strip length", default=def_len)
                ch_name = Prompt.ask(f"  CH{i} custom label", default=def_name)
                specs.append((i, max(0, ch_len), ch_name))
            new_channels = layout_channels(specs)
        else:
            new_channels = device_to_edit.channels

        new_desc = Prompt.ask("Description / Notes", default=device_to_edit.description)

        updated_device = device_to_edit.update(
            name=new_name,
            ip=new_ip,
            port=new_port,
            protocol=new_protocol,
            channels=new_channels,
            description=new_desc,
        )

        self.console.print("\n[bold green]Updated Configuration Preview:[/bold green]")
        self.console.print(f"  Name: {updated_device.name}")
        self.console.print(f"  Target: {updated_device.ip}:{updated_device.port} [{updated_device.protocol.value.upper()}]")
        self.console.print(f"  Total LEDs: {updated_device.total_leds} across {len(updated_device.active_channels)} active channels")

        if Confirm.ask("\nSave updated device to disk?", default=True):
            saved_path = self.device_repo.save(updated_device)
            self.console.print(f"[green]Saved changes to {saved_path}[/green]")
            self.current_device = updated_device

        Prompt.ask("\nPress Enter to continue")

    def _menu_inspect_device(self) -> None:
        """Display current device channel map and static ASCII preview."""
        if not self.current_device:
            self.console.print("[yellow]No device loaded.[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        table = Table(title=f"Device: {self.current_device.name}")
        table.add_column("Channel", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Length", justify="right")
        table.add_column("WLED Start Index", justify="right")
        table.add_column("WLED End Index", justify="right")

        for ch in self.current_device.channels:
            status = "[green]Active[/green]" if ch.is_active else "[dim]Disabled[/dim]"
            start = str(ch.start_index) if ch.is_active else "-"
            end = str(ch.end_index - 1) if ch.is_active else "-"
            table.add_row(ch.display_name, status, str(ch.length), start, end)

        self.console.print(table)
        self.console.print(f"\n[bold]Total LEDs:[/bold] {self.current_device.total_leds}")
        self.console.print(f"[bold]Target:[/bold] {self.current_device.ip}:{self.current_device.port}")
        self.console.print(f"[bold]Protocol:[/bold] {self.current_device.protocol.display_name}")

        Prompt.ask("\nPress Enter to continue")

    def _menu_stream_pattern(self) -> None:
        """Interactive pattern tester and real-time live ASCII visualizer."""
        if not self.current_device:
            self.console.print("[yellow]Please select or create a device first![/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        self.console.print("\n[bold cyan]=== Select Animation Pattern ===[/bold cyan]")
        patterns = list_patterns()
        for idx, pat in enumerate(patterns, start=1):
            self.console.print(f"  [green]{idx:2d}.[/green] [bold]{pat.name:<32}[/bold] [dim]- {pat.description}[/dim]")

        pat_idx = IntPrompt.ask("\nSelect pattern number", default=1)
        if not (1 <= pat_idx <= len(patterns)):
            return
        selected_pattern = patterns[pat_idx - 1]

        # Extra parameters dictionary
        extra_params: dict[str, Any] = {}

        # Pattern-specific color configuration
        if selected_pattern.id in ("gradient", "wave"):
            self.console.print("\n[bold]Select Color Palette:[/bold]")
            self.console.print("  [cyan]1. Cyberpunk Neon[/cyan] (Electric Cyan / Hot Magenta / Purple)")
            self.console.print("  [cyan]2. Tropical Sunset[/cyan] (Indigo / Purple / Coral / Gold)")
            self.console.print("  [cyan]3. Deep Ocean[/cyan] (Navy / Azure / Aqua Seafoam)")
            self.console.print("  [cyan]4. Emerald Forest[/cyan] (Foliage / Lime / Aurora)")
            self.console.print("  [cyan]5. Fire & Flame[/cyan] (Ember Red / Hot Orange / Amber / White)")
            self.console.print("  [cyan]6. Party Confetti[/cyan] (Red / Gold / Green / Blue / Magenta)")
            pal_choice = Prompt.ask("Choose palette", choices=["1", "2", "3", "4", "5", "6"], default="1")
            pal_map = {
                "1": "cyberpunk",
                "2": "sunset",
                "3": "ocean",
                "4": "forest",
                "5": "fire",
                "6": "party",
            }
            extra_params["palette"] = pal_map[pal_choice]
            prim_color = Color.cyan()
            sec_color = Color.black()
        elif selected_pattern.id == "fire":
            # Fire uses built-in flame palette
            prim_color = Color.red()
            sec_color = Color.black()
        else:
            # Color options for primary color
            self.console.print("\n[bold]Select Primary Color:[/bold]")
            self.console.print("  [red]1. Red[/red]      [green]2. Green[/green]    [blue]3. Blue[/blue]      [cyan]4. Cyan[/cyan]")
            self.console.print("  [yellow]5. Amber[/yellow]    [magenta]6. Magenta[/magenta]  [white]7. White[/white]     [dim]8. Custom Hex[/dim]")
            c_choice = Prompt.ask("Color", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="1")
            color_presets = {
                "1": Color(255, 0, 0),
                "2": Color(0, 255, 0),
                "3": Color(0, 80, 255),
                "4": Color(0, 255, 255),
                "5": Color(255, 140, 0),
                "6": Color(255, 0, 200),
                "7": Color(255, 240, 220),
            }
            if c_choice in color_presets:
                prim_color = color_presets[c_choice]
            else:
                hex_str = Prompt.ask("Enter hex color code", default="#FF0000")
                try:
                    prim_color = Color.from_hex(hex_str)
                except Exception:
                    prim_color = Color.red()

            sec_color = Color.black()

        # Motion speed & brightness
        speed = float(Prompt.ask("Speed multiplier", default="1.0"))
        brightness = float(Prompt.ask("Brightness (0.1 to 1.0)", default="1.0"))
        sync_channels = Confirm.ask("Sync pattern across all channels independently?", default=True)

        config = PatternConfig(
            speed=speed,
            brightness=brightness,
            primary_color=prim_color,
            secondary_color=sec_color,
            sync_channels=sync_channels,
            extra=extra_params,
        )

        # Transmission mode: live UDP or preview-only
        send_live = Confirm.ask(
            f"Send live UDP packets to {self.current_device.ip}:{self.current_device.port}?",
            default=True,
        )
        target_fps = IntPrompt.ask("Target FPS", default=30)

        self.console.print(f"\n[bold yellow]Streaming {selected_pattern.name}...[/bold yellow]")
        self.console.print("[dim]Press Ctrl+C to return to main menu.[/dim]\n")
        time.sleep(0.5)

        self._run_live_visualizer(
            device=self.current_device,
            pattern=selected_pattern,
            pattern_config=config,
            dry_run=not send_live,
            target_fps=float(target_fps),
        )

    def _run_live_visualizer(
        self,
        device: DeviceConfig,
        pattern: Any,
        pattern_config: PatternConfig,
        dry_run: bool,
        target_fps: float,
    ) -> None:
        """Run real-time pattern generator and display live ASCII art."""
        runner = AnimationRunner(
            device=device,
            pattern=pattern,
            pattern_config=pattern_config,
            dry_run=dry_run,
            target_fps=target_fps,
        )

        mode_str = "\033[1;33mDRY-RUN / PREVIEW ONLY\033[0m" if dry_run else f"\033[1;32mLIVE UDP -> {device.ip}:{device.port}\033[0m"
        runner.start_background()

        try:
            # Main terminal render loop
            while runner.is_running:
                # ANSI cursor home or clear
                output = self.canvas.render(
                    device=device,
                    frame=runner.frame,
                    title=f"{pattern.name} | {mode_str}",
                    fps=runner.actual_fps,
                )
                # Print using cursor reset for smooth in-place refresh
                sys.stdout.write("\033[H\033[J")
                sys.stdout.write(output + "\n\n")
                sys.stdout.write("  [Press Ctrl+C to stop animation]\n")
                sys.stdout.flush()
                time.sleep(0.04)
        except KeyboardInterrupt:
            pass
        finally:
            runner.stop()
            self.console.print("\n[green]Pattern stopped.[/green]")
            time.sleep(1)

    def _menu_manage_presets(self) -> None:
        """List and manage pattern presets."""
        presets = self.preset_repo.list_all()
        table = Table(title="Pattern Presets")
        table.add_column("#", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Pattern", style="cyan")
        table.add_column("Speed", justify="right")
        table.add_column("Description", style="dim")

        for idx, p in enumerate(presets, start=1):
            table.add_row(
                str(idx),
                p.name,
                p.pattern_id.capitalize(),
                f"{p.config.speed:.1f}x",
                p.description,
            )

        self.console.print(table)
        Prompt.ask("\nPress Enter to continue")

    def _menu_delete_device(self) -> None:
        """Delete currently selected device."""
        if not self.current_device:
            self.console.print("[yellow]No device selected.[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return

        if Confirm.ask(f"Are you sure you want to delete device '{self.current_device.name}'?", default=False):
            self.device_repo.delete(self.current_device.id)
            self.console.print("[green]Device deleted.[/green]")
            self.current_device = None
            time.sleep(1)
