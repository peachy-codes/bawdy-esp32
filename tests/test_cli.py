"""Unit tests for CLI parser and commands."""

import argparse
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

from wled_app.domain.device import ProtocolType
from wled_app.storage.device_repository import DeviceRepository
from wled_app.ui.cli import build_parser, cmd_create, cmd_edit, cmd_list, cmd_play


class TestCLI(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.device_repo = DeviceRepository(self.temp_dir / "devices")
        self.console = Console(file=io.StringIO(), color_system=None)
        self.parser = build_parser()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parser_create(self) -> None:
        args = self.parser.parse_args([
            "create",
            "--name", "Athom-Desk",
            "--ip", "192.168.1.100",
            "--channels", "60", "30", "0", "0",
            "--protocol", "ddp",
        ])
        self.assertEqual(args.command, "create")
        self.assertEqual(args.name, "Athom-Desk")
        self.assertEqual(args.ip, "192.168.1.100")
        self.assertEqual(args.channels, [60, 30, 0, 0])

    def test_parser_edit(self) -> None:
        args = self.parser.parse_args([
            "edit",
            "--device", "Athom-Desk",
            "--name", "Athom-Studio",
            "--ip", "192.168.1.105",
            "--channels", "120", "60", "0", "0",
            "--protocol", "drgb",
            "--port", "21324",
            "--description", "Updated notes",
        ])
        self.assertEqual(args.command, "edit")
        self.assertEqual(args.device, "Athom-Desk")
        self.assertEqual(args.name, "Athom-Studio")
        self.assertEqual(args.ip, "192.168.1.105")
        self.assertEqual(args.channels, [120, 60, 0, 0])
        self.assertEqual(args.protocol, "drgb")
        self.assertEqual(args.port, 21324)
        self.assertEqual(args.description, "Updated notes")

    def test_cmd_create_and_list(self) -> None:
        args = argparse.Namespace(
            name="LivingRoom-Athom",
            ip="192.168.1.55",
            channels=[60, 30, 144, 0],
            protocol="ddp",
            port=4048,
            description="Ethernet WLED controller",
        )
        cmd_create(args, self.console, self.device_repo)

        devs = self.device_repo.list_all()
        self.assertEqual(len(devs), 1)
        self.assertEqual(devs[0].name, "LivingRoom-Athom")
        self.assertEqual(devs[0].total_leds, 234)

        # Run list command
        list_args = argparse.Namespace()
        cmd_list(list_args, self.console, self.device_repo)
        output = self.console.file.getvalue()  # type: ignore[attr-defined]
        self.assertIn("LivingRoom-Athom", output)

    def test_cmd_edit(self) -> None:
        # Create initial device
        create_args = argparse.Namespace(
            name="Original-Device",
            ip="192.168.1.20",
            channels=[60, 60],
            protocol="ddp",
            port=4048,
            description="Original",
        )
        cmd_create(create_args, self.console, self.device_repo)

        devs = self.device_repo.list_all()
        dev_id = devs[0].id

        # Edit device
        edit_args = argparse.Namespace(
            device="Original-Device",
            name="Renamed-Device",
            ip="192.168.1.25",
            channels=[90, 30, 10],
            protocol="drgb",
            port=21324,
            description="Modified",
        )
        cmd_edit(edit_args, self.console, self.device_repo)

        updated_dev = self.device_repo.get(dev_id)
        self.assertIsNotNone(updated_dev)
        assert updated_dev is not None
        self.assertEqual(updated_dev.id, dev_id)
        self.assertEqual(updated_dev.name, "Renamed-Device")
        self.assertEqual(updated_dev.ip, "192.168.1.25")
        self.assertEqual(updated_dev.protocol, ProtocolType.DRGB)
        self.assertEqual(updated_dev.port, 21324)
        self.assertEqual(updated_dev.total_leds, 130)
        self.assertEqual(updated_dev.description, "Modified")

    def test_cmd_play_dry_run(self) -> None:
        # Create a device
        args = argparse.Namespace(
            name="TestStrip",
            ip="127.0.0.1",
            channels=[10, 10],
            protocol="ddp",
            port=4048,
            description="",
        )
        cmd_create(args, self.console, self.device_repo)

        play_args = argparse.Namespace(
            device="TestStrip",
            pattern="rainbow",
            speed=1.0,
            brightness=1.0,
            color="#00FF00",
            fps=50.0,
            frames=3,
            linear=False,
            dry_run=True,
            no_color=True,
        )

        with patch("sys.stdout", new_callable=io.StringIO):
            cmd_play(play_args, self.console, self.device_repo)


if __name__ == "__main__":
    unittest.main()
