"""Standalone CLI for WLED ESP32 Hardware Digital Twin."""

from __future__ import annotations
import argparse
import asyncio
import sys
import webbrowser
from rich.console import Console

from wled_simulator.models import ChannelInfo
from wled_simulator.runner import SimulatorRunner


def build_parser() -> argparse.ArgumentParser:
    """Build simulator CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="wled-sim",
        description="Standalone WLED ESP32 Hardware Digital Twin & Interactive LED Canvas Simulator.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Name of saved device profile to simulate (e.g. 'Garage Door Test')",
    )
    parser.add_argument(
        "--channels",
        nargs="+",
        type=int,
        default=None,
        help="LED lengths for each channel (e.g. 270 270 270)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4048,
        help="UDP listening port (default: 4048 for DDP)",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=8080,
        help="Local Web UI port (default: 8080)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open web browser on startup",
    )
    return parser


def resolve_channels(args: argparse.Namespace, console: Console) -> tuple[list[ChannelInfo], int]:
    """Resolve channel configuration from saved device profile or ad-hoc flags."""
    udp_port = args.port

    if args.device:
        try:
            from wled_app.storage.device_repository import DeviceRepository
            repo = DeviceRepository()
            dev = repo.get_by_name(args.device) or repo.get(args.device)
            if dev is not None:
                console.print(f"[bold green]Loaded device profile:[/bold green] [cyan]{dev.name}[/cyan] ({dev.total_leds} LEDs)")
                channels = [
                    ChannelInfo(
                        channel_id=ch.channel_id,
                        length=ch.length,
                        start_index=ch.start_index,
                        name=ch.name or f"Strip {ch.channel_id}",
                    )
                    for ch in dev.active_channels
                ]
                return channels, (dev.port or udp_port)
            else:
                console.print(f"[yellow]Device profile '{args.device}' not found. Falling back to CLI channel flags.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Could not load profile '{args.device}': {e}. Using CLI channel flags.[/yellow]")

    # Fallback to --channels or default 3-channel 270 LED setup (Athom controller profile)
    lengths = args.channels or [270, 270, 270]
    channels: list[ChannelInfo] = []
    current_offset = 0
    for idx, length in enumerate(lengths, start=1):
        channels.append(
            ChannelInfo(
                channel_id=idx,
                length=max(0, length),
                start_index=current_offset,
                name=f"Strip {idx}",
            )
        )
        current_offset += max(0, length)

    return channels, udp_port


def main() -> None:
    """Main CLI entrypoint for standalone WLED simulator."""
    parser = build_parser()
    args = parser.parse_args()

    console = Console()

    channels, udp_port = resolve_channels(args, console)
    total_leds = sum(ch.length for ch in channels)

    console.print()
    console.print("[bold cyan]══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold white]        WLED ESP32 Hardware Digital Twin Simulator            [/bold white]")
    console.print("[bold cyan]══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print(f"  • [bold]UDP Listener:[/bold]   [green]0.0.0.0:{udp_port}[/green] [dim](DDP / DRGB)[/dim]")
    console.print(f"  • [bold]Web Interface:[/bold]  [cyan]http://localhost:{args.web_port}[/cyan]")
    console.print(f"  • [bold]Channels ({len(channels)}):[/bold]   [yellow]{total_leds} total LEDs[/yellow]")
    for ch in channels:
        console.print(f"      CH{ch.channel_id} ({ch.name}): [bold]{ch.length}[/bold] LEDs [dim](Indices {ch.start_index}..{ch.end_index - 1})[/dim]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    url = f"http://localhost:{args.web_port}"
    if not args.no_browser:
        console.print(f"[dim]Opening web browser at {url}...[/dim]")
        webbrowser.open(url)

    runner = SimulatorRunner(
        channels=channels,
        udp_port=udp_port,
        web_port=args.web_port,
    )

    try:
        asyncio.run(runner.run_forever())
    except KeyboardInterrupt:
        console.print("\n[yellow]Simulator stopped.[/yellow]")


if __name__ == "__main__":
    main()
