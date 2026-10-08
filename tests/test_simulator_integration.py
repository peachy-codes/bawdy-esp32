"""Integration test: real UDP loopback transmission between sender and simulator."""

import asyncio
import struct
import unittest
from wled_simulator.models import ChannelInfo
from wled_simulator.protocol_parser import ProtocolParser
from wled_simulator.state_machine import WledStateMachine
from wled_simulator.udp_receiver import UdpReceiver


class TestSimulatorUdpLoopback(unittest.IsolatedAsyncioTestCase):
    async def test_real_udp_packet_ingestion(self) -> None:
        channels = [
            ChannelInfo(1, length=10, start_index=0, name="Strip 1"),
            ChannelInfo(2, length=10, start_index=10, name="Strip 2"),
        ]
        rendered_frames: list[bytes] = []

        def on_render(pixels: bytes, telemetry: object) -> None:
            rendered_frames.append(pixels)

        sm = WledStateMachine(channels=channels, on_frame_rendered=on_render)
        receiver = UdpReceiver(state_machine=sm, host="127.0.0.1", port=14048)

        try:
            await receiver.start()
            loop = asyncio.get_running_loop()
            sender_transport, _ = await loop.create_datagram_endpoint(
                asyncio.DatagramProtocol,
                remote_addr=("127.0.0.1", 14048),
            )
        except (PermissionError, OSError):
            raise unittest.SkipTest("Socket operation restricted in sandbox")

        try:
            # Chunk 1: Red (10 LEDs = 30 bytes), PUSH=0
            p1_data = bytes([255, 0, 0] * 10)
            p1 = struct.pack(">BBBB I H", 0x40, 1, 1, 1, 0, len(p1_data)) + p1_data
            sender_transport.sendto(p1)

            await asyncio.sleep(0.05)
            self.assertEqual(len(rendered_frames), 0)

            # Chunk 2: Green (10 LEDs = 30 bytes), PUSH=1
            p2_data = bytes([0, 255, 0] * 10)
            p2 = struct.pack(">BBBB I H", 0x41, 2, 1, 1, 30, len(p2_data)) + p2_data
            sender_transport.sendto(p2)

            await asyncio.sleep(0.05)
            self.assertEqual(len(rendered_frames), 1)

            frame = rendered_frames[0]
            self.assertEqual(frame[:30], p1_data)
            self.assertEqual(frame[30:], p2_data)

            # Check telemetry
            telem = sm.get_telemetry()
            self.assertEqual(telem.total_packets, 2)
            self.assertEqual(telem.total_frames, 1)

        finally:
            sender_transport.close()
            receiver.stop()


if __name__ == "__main__":
    unittest.main()
