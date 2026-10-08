"""Command-line argument parser and CLI dispatch for ASCII UDP WLED."""

from __future__ import annotations
import argparse
import sys
import time

from rich.console import Console

from wled_app.domain.channel import layout_channels
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig, ProtocolType, validate_ip_or_host
from wled_app.engine.runner import AnimationRunner
from wled_app.patterns.base import PatternConfig
from wled_app.patterns.registry import get_pattern, list_patterns
from wled_app.storage.device_repository import DeviceRepository
from wled_app.storage.preset_repository import PresetRepository
from wled_app.ui.interactive import InteractiveApp
from wled_app.visualizer.ascii_canvas import AsciiCanvas


def cmd_list(args: argparse.Namespace, console: Console, repo: DeviceRepository) -> None:
    """List all saved devices."""
    devices = repo.list_all()
    if not devices:
        console.print("[yellow]No devices found. Use 'wled-app create' or run interactive mode.[/yellow]")
        return

    console.print(f"[bold cyan]Configured Devices ({len(devices)}):[/bold cyan]")
    for dev in devices:
        console.print(
            f"  • [bold green]{dev.name}[/bold green] (ID: {dev.id}) "
            f"-> [cyan]{dev.ip}:{dev.port}[/cyan] [{dev.protocol.value.upper()}] "
            f"| {len(dev.active_channels)} channels, {dev.total_leds} LEDs"
        )


def cmd_create(args: argparse.Namespace, console: Console, repo: DeviceRepository) -> None:
    """Create and save a new device via CLI flags."""
    try:
        clean_ip = validate_ip_or_host(args.ip)
    except ValueError as err:
        console.print(f"[bold red]Invalid IP/hostname:[/bold red] {err}")
        sys.exit(1)

    proto = ProtocolType(args.protocol.lower())
    port = args.port or proto.default_port

    channel_lengths: list[int] = [int(l) for l in args.channels]

    device = DeviceConfig.create(
        name=args.name,
        ip=clean_ip,
        channel_lengths=channel_lengths,
        protocol=proto,
        port=port,
        description=args.description or "",
    )

    path = repo.save(device)
    console.print(f"[bold green]Created device '{device.name}' (ID: {device.id})[/bold green]")
    console.print(f"  Target: {device.ip}:{device.port} [{device.protocol.value.upper()}]")
    console.print(f"  Total LEDs: {device.total_leds} across {len(device.active_channels)} active channels")
    console.print(f"  Saved to: {path}")


def cmd_edit(args: argparse.Namespace, console: Console, repo: DeviceRepository) -> None:
    """Edit an existing device configuration via CLI flags."""
    device = repo.get_by_name(args.device) or repo.get(args.device)
    if not device:
        console.print(f"[bold red]Device '{args.device}' not found.[/bold red]")
        sys.exit(1)

    new_name = args.name if args.name is not None else device.name
    new_ip = device.ip
    if args.ip is not None:
        try:
            new_ip = validate_ip_or_host(args.ip)
        except ValueError as err:
            console.print(f"[bold red]Invalid IP/hostname:[/bold red] {err}")
            sys.exit(1)

    new_protocol = ProtocolType(args.protocol.lower()) if args.protocol else device.protocol
    new_port = args.port if args.port is not None else (new_protocol.default_port if args.protocol else device.port)

    if args.channels is not None:
        channel_lengths: list[int] = [int(l) for l in args.channels]
        specs: list[tuple[int, int, str]] = []
        for i, length in enumerate(channel_lengths, start=1):
            existing_ch = device.get_channel(i)
            ch_name = existing_ch.name if (existing_ch and existing_ch.name) else f"Strip {i}"
            specs.append((i, max(0, length), ch_name))
        new_channels = layout_channels(specs)
    else:
        new_channels = device.channels

    new_description = args.description if args.description is not None else device.description

    updated = device.update(
        name=new_name,
        ip=new_ip,
        port=new_port,
        protocol=new_protocol,
        channels=new_channels,
        description=new_description,
    )

    path = repo.save(updated)
    console.print(f"[bold green]Updated device '{updated.name}' (ID: {updated.id})[/bold green]")
    console.print(f"  Target: {updated.ip}:{updated.port} [{updated.protocol.value.upper()}]")
    console.print(f"  Total LEDs: {updated.total_leds} across {len(updated.active_channels)} active channels")
    console.print(f"  Saved to: {path}")


def cmd_play(args: argparse.Namespace, console: Console, repo: DeviceRepository) -> None:
    """Play pattern and stream to device with ASCII visualizer."""
    device: DeviceConfig | None = None
    if args.device:
        device = repo.get_by_name(args.device) or repo.get(args.device)
        if not device:
            console.print(f"[bold red]Device '{args.device}' not found.[/bold red]")
            sys.exit(1)
    else:
        # Default to first available device
        all_devs = repo.list_all()
        if all_devs:
            device = all_devs[0]

    if not device:
        # Create a temporary virtual device if none exist
        console.print("[yellow]No device specified or saved. Using default 4-channel virtual test rig.[/yellow]")
        device = DeviceConfig.create(
            name="Virtual-Athom-ESP32",
            ip="127.0.0.1",
            channel_lengths=[60, 30, 144, 0],
            protocol=ProtocolType.DDP,
        )

    pattern = get_pattern(args.pattern)

    try:
        prim_color = Color.from_hex(args.color) if args.color else Color.red()
    except Exception:
        prim_color = Color.red()

    extra_params: dict[str, object] = {}
    if getattr(args, "palette", None):
        extra_params["palette"] = args.palette

    p_config = PatternConfig(
        speed=args.speed,
        brightness=args.brightness,
        primary_color=prim_color,
        sync_channels=not args.linear,
        extra=extra_params,
    )

    canvas = AsciiCanvas(use_color=not args.no_color)
    runner = AnimationRunner(
        device=device,
        pattern=pattern,
        pattern_config=p_config,
        dry_run=args.dry_run,
        target_fps=args.fps,
    )

    mode = "\033[1;33mDRY-RUN\033[0m" if args.dry_run else f"\033[1;32mLIVE UDP -> {device.ip}:{device.port}\033[0m"
    console.print(f"[bold]Streaming {pattern.name}[/bold]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    frame_count = 0
    max_frames = args.frames

    try:
        while True:
            if max_frames and frame_count >= max_frames:
                break

            runner.step()
            frame_count += 1

            output = canvas.render(
                device=device,
                frame=runner.frame,
                title=f"{pattern.name} ({mode})",
                fps=args.fps,
            )

            sys.stdout.write("\033[H\033[J")
            sys.stdout.write(output + "\n")
            sys.stdout.write(f"Frame {frame_count} | Press Ctrl+C to stop\n")
            sys.stdout.flush()

            time.sleep(1.0 / args.fps)
    except KeyboardInterrupt:
        pass
    finally:
        runner.close()
        console.print("\n[green]Streaming ended.[/green]")


def build_parser() -> argparse.ArgumentParser:
    """Build command-line parser."""
    parser = argparse.ArgumentParser(
        prog="wled-app",
        description="Terminal-based WLED UDP Controller with multi-channel addressing & ASCII monitor.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # List
    subparsers.add_parser("list", help="List saved devices")

    # Create
    p_create = subparsers.add_parser("create", help="Create a new WLED device")
    p_create.add_argument("--name", required=True, help="Device name")
    p_create.add_argument("--ip", required=True, help="Controller IP address")
    p_create.add_argument(
        "--channels",
        nargs="+",
        type=int,
        required=True,
        help="LED lengths for each channel (e.g. 60 30 144 0)",
    )
    p_create.add_argument(
        "--protocol",
        choices=["ddp", "drgb", "dnrgb", "warls"],
        default="ddp",
        help="WLED realtime protocol (default: ddp)",
    )
    p_create.add_argument("--port", type=int, default=None, help="UDP port (default: protocol default)")
    p_create.add_argument("--description", default="", help="Optional notes")

    # Edit
    p_edit = subparsers.add_parser("edit", help="Edit an existing WLED device")
    p_edit.add_argument("--device", required=True, help="Device name or ID to edit")
    p_edit.add_argument("--name", default=None, help="New device name")
    p_edit.add_argument("--ip", default=None, help="New controller IP address")
    p_edit.add_argument(
        "--channels",
        nargs="+",
        type=int,
        default=None,
        help="New LED lengths for channels (e.g. 60 30 144 0)",
    )
    p_edit.add_argument(
        "--protocol",
        choices=["ddp", "drgb", "dnrgb", "warls"],
        default=None,
        help="New realtime protocol",
    )
    p_edit.add_argument("--port", type=int, default=None, help="New UDP port")
    p_edit.add_argument("--description", default=None, help="New notes / description")

    # Play
    p_play = subparsers.add_parser("play", help="Stream an animation pattern to a device")
    p_play.add_argument("--device", help="Device name or ID (defaults to active/first device)")
    p_play.add_argument(
        "--pattern",
        choices=[
            "rainbow",
            "chase",
            "fire",
            "meteor",
            "cylon",
            "twinkle",
            "wave",
            "gradient",
            "blink",
            "wipe",
            "solid",
        ],
        default="rainbow",
        help="Pattern to stream (default: rainbow)",
    )
    p_play.add_argument(
        "--palette",
        choices=["cyberpunk", "sunset", "ocean", "forest", "fire", "police", "party"],
        default=None,
        help="Color palette for gradient/wave patterns",
    )
    p_play.add_argument("--speed", type=float, default=1.0, help="Animation speed multiplier")
    p_play.add_argument("--brightness", type=float, default=1.0, help="Brightness (0.1..1.0)")
    p_play.add_argument("--color", default="#FF0000", help="Primary color hex (e.g. #FF0000)")
    p_play.add_argument("--fps", type=float, default=30.0, help="Target frames per second")
    p_play.add_argument("--frames", type=int, default=None, help="Stop after N frames")
    p_play.add_argument("--linear", action="store_true", help="Flow continuously across channels instead of sync")
    p_play.add_argument("--dry-run", action="store_true", help="Preview only, do not send UDP packets")
    p_play.add_argument("--no-color", action="store_true", help="Disable ANSI color codes")

    # Interactive
    subparsers.add_parser("interactive", help="Launch full interactive menu UI")

    return parser


def main() -> None:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    console = Console()
    device_repo = DeviceRepository()

    if args.command is None or args.command == "interactive":
        # Launch interactive UI
        app = InteractiveApp(device_repo=device_repo, console=console)
        app.run()
    elif args.command == "list":
        cmd_list(args, console, device_repo)
    elif args.command == "create":
        cmd_create(args, console, device_repo)
    elif args.command == "edit":
        cmd_edit(args, console, device_repo)
    elif args.command == "play":
        cmd_play(args, console, device_repo)


if __name__ == "__main__":
    main()
