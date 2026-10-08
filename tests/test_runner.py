"""Unit tests for Network layer and AnimationRunner engine."""

import unittest
from wled_app.domain.device import DeviceConfig, ProtocolType
from wled_app.domain.frame import FrameBuffer
from wled_app.engine.runner import AnimationRunner
from wled_app.network.udp_client import MockUdpClient
from wled_app.patterns.chase import ChasePattern


class TestAnimationRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.device = DeviceConfig.create(
            name="RunnerTest",
            ip="192.168.1.42",
            channel_lengths=[20, 10],
            protocol=ProtocolType.DDP,
        )
        self.mock_sender = MockUdpClient()
        self.pattern = ChasePattern()

    def test_single_step_transmits_packets(self) -> None:
        runner = AnimationRunner(
            device=self.device,
            pattern=self.pattern,
            sender=self.mock_sender,
        )
        frame = runner.step(tick=0)
        self.assertEqual(len(frame), 30)

        # Should have sent 1 packet to 192.168.1.42:4048
        self.assertEqual(len(self.mock_sender.sent_packets), 1)
        ip, port, data = self.mock_sender.sent_packets[0]
        self.assertEqual(ip, "192.168.1.42")
        self.assertEqual(port, 4048)
        # Header (10) + 30 * 3 (90) = 100 bytes
        self.assertEqual(len(data), 100)

    def test_run_max_frames(self) -> None:
        runner = AnimationRunner(
            device=self.device,
            pattern=self.pattern,
            sender=self.mock_sender,
            target_fps=100.0,
        )
        runner.run(max_frames=5)
        self.assertEqual(len(self.mock_sender.sent_packets), 5)
        self.assertEqual(runner.current_tick, 5)

    def test_callback_invoked(self) -> None:
        callbacks: list[int] = []

        def on_frame(fb: FrameBuffer, fps: float, tick: int) -> None:
            callbacks.append(tick)

        runner = AnimationRunner(
            device=self.device,
            pattern=self.pattern,
            sender=self.mock_sender,
            on_frame=on_frame,
        )
        runner.step()
        runner.step()
        self.assertEqual(callbacks, [0, 1])


if __name__ == "__main__":
    unittest.main()
