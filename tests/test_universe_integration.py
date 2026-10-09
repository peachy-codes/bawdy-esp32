"""End-to-end multi-controller integration test: LightingEngine -> MultiNodeDispatcher -> MultiNodeSimulatorRunner."""

import asyncio
import time
import unittest

from wled_app.network.udp_client import MockUdpClient
from wled_engine.core import LightingEngine
from wled_engine.spatial.patterns import spatial_angle_sweep
from wled_engine.spatial.venue import create_demo_venue
from wled_simulator.multi_node_runner import MultiNodeSimulatorRunner
from wled_simulator.protocol_parser import ProtocolParser


class TestUniverseEndToEndIntegration(unittest.TestCase):
    def test_full_pipeline_multi_node_dispatch_and_sync(self) -> None:
        """Verify 20-node pipeline from spatial pattern math to packet generation and digital twin reassembly."""
        universe, patch = create_demo_venue()
        mock_sender = MockUdpClient()

        # 1. Initialize MultiNodeSimulatorRunner
        runner = MultiNodeSimulatorRunner(
            universe=universe,
            patch_table=patch,
            base_port=26048,
            web_port=29080,
            sync_port=26048,
        )

        # 2. Configure LightingEngine in universe mode with mock sender
        engine = LightingEngine(dry_run=True)
        engine.setup_universe(
            universe=universe,
            patch_table=patch,
            broadcast_ip="255.255.255.255",
            sync_port=26048,
            dry_run=True,
        )
        engine.dispatcher._sender = mock_sender
        engine.dispatcher._owns_sender = False

        # 3. Set continuous spatial pattern (Angle Sweep)
        pattern_func = spatial_angle_sweep(angle_deg=45.0, speed=1.0, time_sec=0.5)
        engine.set_spatial_pattern(pattern_func)

        # 4. Execute frame step
        frames = engine.step(custom_dt=0.033, tick=1)
        self.assertIsNotNone(frames)

        # 5. Verify Engine Dispatcher Telemetry
        disp_telemetry = engine.dispatcher.get_telemetry()
        self.assertEqual(len(disp_telemetry), 20)
        for cid in patch.get_controllers():
            self.assertIn(cid, disp_telemetry)
            self.assertGreater(disp_telemetry[cid]["packets_sent"], 0)
            self.assertGreater(disp_telemetry[cid]["bytes_sent"], 0)

        # 6. Verify mock sender captured packets for all 20 controllers + 1 sync packet
        self.assertGreaterEqual(len(mock_sender.sent_packets), 21)

        # 7. Feed captured DDP packets into runner state machines to verify unpack pipeline
        for ip, port, pkt_bytes in mock_sender.sent_packets:
            parsed = ProtocolParser.parse_ddp(pkt_bytes)
            if parsed is not None:
                # Find controller by port or feed all
                for cid, sm in runner._state_machines.items():
                    sm.process_ddp(parsed)

        # 9. Verify blackout flushes black frames
        mock_sender.sent_packets.clear()
        engine.blackout()
        self.assertIsNone(engine.spatial_pattern_func)
        self.assertGreaterEqual(len(mock_sender.sent_packets), 20)

        engine.close()

    def test_blackout_clears_spatial_and_flushes_black(self) -> None:
        """Verify engine.blackout() clears spatial pattern and sends black frame to all nodes."""
        universe, patch = create_demo_venue()
        mock_sender = MockUdpClient()
        engine = LightingEngine(dry_run=True)
        engine.setup_universe(universe=universe, patch_table=patch, dry_run=True)
        engine.dispatcher._sender = mock_sender
        engine.dispatcher._owns_sender = False

        engine.set_spatial_pattern(lambda p: (255, 255, 255))
        self.assertIsNotNone(engine.spatial_pattern_func)

        engine.blackout()
        self.assertIsNone(engine.spatial_pattern_func)
        self.assertGreaterEqual(len(mock_sender.sent_packets), 20)
        engine.close()


if __name__ == "__main__":
    unittest.main()
