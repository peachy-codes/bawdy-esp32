"""Unit tests for MultiNodeDispatcher and DDP Broadcast Synchronization across 20 nodes."""

from __future__ import annotations
import unittest

from wled_app.network.udp_client import MockUdpClient
from wled_engine.fleet.dispatcher import MultiNodeDispatcher


class TestMultiNodeDispatcher(unittest.TestCase):
    def test_20_node_broadcast_synchronization(self) -> None:
        mock_sender = MockUdpClient()
        dispatcher = MultiNodeDispatcher(
            broadcast_ip="192.168.1.255",
            sync_port=4048,
            dry_run=True,
            sender=mock_sender,
        )

        # Register 20 controllers on Cat6 subnet
        for i in range(1, 21):
            dispatcher.add_node(
                node_id=f"wled_{i:02d}",
                ip=f"192.168.1.{100 + i}",
                port=4048,
            )

        self.assertEqual(len(dispatcher.nodes), 20)

        # Prepare channel buffers for all 20 nodes (100 LEDs each = 300 bytes)
        buffers = {
            f"wled_{i:02d}": [bytearray(b"\xFF\x00\x00" * 100)]
            for i in range(1, 21)
        }

        # Dispatch with broadcast frame sync enabled
        total_bytes = dispatcher.dispatch_channel_buffers(buffers, sync=True)
        self.assertTrue(total_bytes > 0)

        # Total packets sent: 20 node packets + 1 broadcast sync packet = 21 packets
        self.assertEqual(len(mock_sender.sent_packets), 21)

        # Verify all 20 node packets have push flag DISABLED (flags1 = 0x40)
        for i in range(20):
            ip, port, pkt = mock_sender.sent_packets[i]
            self.assertTrue(ip.startswith("192.168.1."))
            self.assertEqual(port, 4048)
            flags1 = pkt[0]
            self.assertEqual(flags1, 0x40, f"Expected push=False (0x40) on node packet {i}")

        # Verify the 21st packet is the Broadcast Sync packet!
        sync_ip, sync_port, sync_pkt = mock_sender.sent_packets[20]
        self.assertEqual(sync_ip, "192.168.1.255")
        self.assertEqual(sync_port, 4048)
        self.assertEqual(len(sync_pkt), 10)  # Exactly 10 bytes header
        self.assertEqual(sync_pkt[0], 0x41)  # Version 1 + PUSH flag set
        # Offset (bytes 4..7) and Length (bytes 8..9) are 0
        self.assertEqual(sync_pkt[8:10], b"\x00\x00")

        # Telemetry verification
        telem = dispatcher.get_telemetry()
        self.assertEqual(len(telem), 20)
        for i in range(1, 21):
            nid = f"wled_{i:02d}"
            self.assertEqual(telem[nid]["frames_sent"], 1)
            self.assertEqual(telem[nid]["packets_sent"], 1)
            self.assertEqual(telem[nid]["errors"], 0)

    def test_dispatch_without_sync(self) -> None:
        mock_sender = MockUdpClient()
        dispatcher = MultiNodeDispatcher(dry_run=True, sender=mock_sender)
        dispatcher.add_node("wled_01", "192.168.1.101", 4048)

        buffers = {"wled_01": [bytearray(b"\x00\xFF\x00" * 50)]}
        dispatcher.dispatch_channel_buffers(buffers, sync=False)

        # Exactly 1 packet sent (no broadcast sync)
        self.assertEqual(len(mock_sender.sent_packets), 1)
        ip, port, pkt = mock_sender.sent_packets[0]
        self.assertEqual(ip, "192.168.1.101")
        # Push flag enabled (0x41) on immediate render
        self.assertEqual(pkt[0], 0x41)


if __name__ == "__main__":
    unittest.main()
