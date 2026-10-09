"""Standalone CLI launcher for the headless WLED Lighting Engine REST Daemon."""

from __future__ import annotations
import argparse
import sys
import time

from rich.console import Console

from wled_app.domain.device import DeviceConfig, ProtocolType, validate_ip_or_host
from wled_app.storage.device_repository import DeviceRepository
from wled_engine.adapters.rest_daemon import EngineDaemon
from wled_engine.core import LightingEngine


def parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wled-engine-daemon",
        description="Headless HTTP REST Daemon for WLED Lighting Engine.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP API host to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="HTTP API port (default: 8765)",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=30.0,
        help="Target animation engine FPS (default: 30.0)",
    )
    parser.add_argument(
        "--venue",
        action="store_true",
        help="Configure full 20-node multi-controller venue universe",
    )
    parser.add_argument(
        "--preset",
        default=None,
        help="Stage universe preset name (concert_hall, warehouse_rave, festival_amphitheater, art_gallery)",
    )
    parser.add_argument(
        "--universe",
        default=None,
        help="Path to SpatialUniverse JSON file",
    )
    parser.add_argument(
        "--patch",
        default=None,
        help="Path to PatchTable JSON file",
    )
    parser.add_argument(
        "--device",
        help="Name or ID of saved device to register on startup",
    )
    parser.add_argument(
        "--ip",
        help="Hardware controller IP address (if creating ad-hoc device)",
    )
    parser.add_argument(
        "--channels",
        nargs="+",
        type=int,
        help="LED counts per channel for ad-hoc device (e.g. 270 270 270)",
    )
    parser.add_argument(
        "--protocol",
        choices=["ddp", "drgb", "dnrgb", "warls"],
        default="ddp",
        help="Realtime protocol (default: ddp)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not transmit UDP packets across network",
    )
    return parser


def main() -> None:
    parser = parse_args()
    args = parser.parse_args()
    console = Console()

    engine = LightingEngine(target_fps=args.fps, dry_run=args.dry_run)

    # Register universe or device
    if args.venue or args.universe or args.preset:
        from pathlib import Path
        from wled_engine.spatial.universe import SpatialUniverse
        from wled_engine.patch.patch_table import PatchTable
        if args.preset:
            from wled_engine.spatial.venue import get_preset_venue
            universe, patch_table = get_preset_venue(args.preset)
        elif args.venue:
            from wled_engine.spatial.venue import create_demo_venue
            universe, patch_table = create_demo_venue()
        else:
            universe = SpatialUniverse.load_json(args.universe)
            patch_file = args.patch or (Path(args.universe).parent / "patch.json")
            patch_table = PatchTable.load_json(patch_file)

        engine.setup_universe(universe, patch_table, dry_run=args.dry_run)
        console.print(f"[bold green]🌐 Spatial Universe Active:[/bold green] [cyan]{universe.name}[/cyan] ({universe.total_pixels} pixels across {len(patch_table.get_controllers())} Cat6 controller nodes)")
    elif args.device:
        repo = DeviceRepository()
        device = repo.get_by_name(args.device) or repo.get(args.device)
        if not device:
            console.print(f"[bold red]Device not found:[/bold red] {args.device}")
            sys.exit(1)
        engine.add_device(device)
        console.print(f"[green]Registered device from repository:[/green] {device.name} ({device.total_leds} LEDs)")
    elif args.ip and args.channels:
        clean_ip = validate_ip_or_host(args.ip)
        proto = ProtocolType(args.protocol.lower())
        device = DeviceConfig.create(
            name="DaemonTarget",
            ip=clean_ip,
            channel_lengths=args.channels,
            protocol=proto,
        )
        engine.add_device(device)
        console.print(f"[green]Registered ad-hoc device:[/green] {clean_ip} ({device.total_leds} LEDs)")
    else:
        # Check if repository has any devices
        repo = DeviceRepository()
        all_devs = repo.list_all()
        if all_devs:
            device = all_devs[0]
            engine.add_device(device)
            console.print(f"[cyan]Auto-registered default device:[/cyan] {device.name} ({device.total_leds} LEDs)")

    # Start engine clock
    engine.start()

    daemon = EngineDaemon(engine=engine, host=args.host, port=args.port)
    daemon.start()

    console.print(f"[bold green]⚡ WLED Lighting Engine REST Daemon is running![/bold green]")
    console.print(f"  • API URL: [cyan]http://{args.host}:{daemon.port}[/cyan]")
    console.print(f"  • Status:  [cyan]http://{args.host}:{daemon.port}/api/status[/cyan]")
    console.print(f"  • Layers:  [cyan]http://{args.host}:{daemon.port}/api/layers[/cyan]")
    console.print(f"  • Press [bold yellow]Ctrl+C[/bold yellow] to stop daemon.")

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down Lighting Engine Daemon...[/yellow]")
    finally:
        daemon.stop()
        engine.stop()
        console.print("[green]Daemon stopped cleanly.[/green]")


if __name__ == "__main__":
    main()
