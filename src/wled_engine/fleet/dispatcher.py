"""High-performance multi-node UDP network dispatcher for multi-controller installations."""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any

from wled_app.domain.device import ProtocolType
from wled_app.domain.frame import FrameBuffer
from wled_app.network.udp_client import MockUdpClient, UdpClient, UdpSender
from wled_app.protocols.ddp import DdpEmitter
from wled_app.protocols.registry import get_emitter


@dataclass
class NodeTelemetry:
    """Network transmission telemetry for an individual controller endpoint."""
    node_id: str
    ip: str
    port: int
    frames_sent: int = 0
    packets_sent: int = 0
    bytes_sent: int = 0
    errors: int = 0
    last_sent_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "ip": self.ip,
            "port": self.port,
            "frames_sent": self.frames_sent,
            "packets_sent": self.packets_sent,
            "bytes_sent": self.bytes_sent,
            "errors": self.errors,
            "last_sent_time": round(self.last_sent_time, 3),
        }


@dataclass
class NodeEndpoint:
    """A configured hardware controller node destination on the Cat6 network."""
    node_id: str
    ip: str
    port: int = 4048
    protocol: ProtocolType = ProtocolType.DDP
    telemetry: NodeTelemetry = field(init=False)

    def __post_init__(self) -> None:
        self.telemetry = NodeTelemetry(node_id=self.node_id, ip=self.ip, port=self.port)


class MultiNodeDispatcher:
    """High-throughput multi-controller UDP dispatcher with DDP Broadcast Frame Synchronization."""

    def __init__(
        self,
        broadcast_ip: str = "255.255.255.255",
        sync_port: int = 4048,
        dry_run: bool = False,
        sender: UdpSender | None = None,
    ) -> None:
        self.broadcast_ip = broadcast_ip
        self.sync_port = sync_port
        self.dry_run = dry_run

        self._nodes: dict[str, NodeEndpoint] = {}
        self._emitters: dict[ProtocolType, Any] = {
            ProtocolType.DDP: DdpEmitter(),
        }

        if sender is not None:
            self._sender = sender
            self._owns_sender = False
        else:
            self._sender = MockUdpClient() if dry_run else UdpClient(broadcast=True)
            self._owns_sender = True

        self._frame_seq: int = 1

    def add_node(
        self,
        node_id: str,
        ip: str,
        port: int = 4048,
        protocol: ProtocolType = ProtocolType.DDP,
    ) -> NodeEndpoint:
        """Register a hardware controller target endpoint."""
        endpoint = NodeEndpoint(node_id=node_id, ip=ip, port=port, protocol=protocol)
        self._nodes[node_id] = endpoint
        return endpoint

    def remove_node(self, node_id: str) -> NodeEndpoint | None:
        """Remove a controller target endpoint."""
        return self._nodes.pop(node_id, None)

    def get_node(self, node_id: str) -> NodeEndpoint | None:
        return self._nodes.get(node_id)

    @property
    def nodes(self) -> list[NodeEndpoint]:
        return list(self._nodes.values())

    def dispatch_channel_buffers(
        self,
        controller_buffers: dict[str, list[bytearray]],
        sync: bool = True,
    ) -> int:
        """Encode and transmit packed channel buffers to all registered nodes.

        Args:
            controller_buffers: Map of controller_id -> [chan_0_bytes, chan_1_bytes, ...]
            sync: If True, transmits DDP packets with push=False and emits a single
                  broadcast DDP Sync packet at the end of the frame tick.

        Returns:
            Total bytes transmitted across all nodes.
        """
        now = time.time()
        total_bytes = 0

        for node_id, chan_bufs in controller_buffers.items():
            node = self._nodes.get(node_id)
            if not node:
                continue

            # Concatenate channel bytearrays into contiguous frame buffer
            all_bytes = bytearray()
            for b in chan_bufs:
                all_bytes.extend(b)

            led_count = len(all_bytes) // 3
            if led_count == 0:
                continue

            frame = FrameBuffer.from_rgb_bytes(bytes(all_bytes))
            emitter = self._emitters.get(node.protocol)
            if not emitter:
                emitter = get_emitter(node.protocol)
                self._emitters[node.protocol] = emitter

            # If broadcast sync is active, disable push flag so packets buffer in board RAM
            push_flag = not sync if isinstance(emitter, DdpEmitter) else True
            if isinstance(emitter, DdpEmitter):
                packets = emitter.encode_frame(frame, push=push_flag)
            else:
                packets = emitter.encode_frame(frame)

            try:
                sent = self._sender.send_packets(node.ip, node.port, packets)
                total_bytes += sent
                node.telemetry.frames_sent += 1
                node.telemetry.packets_sent += len(packets)
                node.telemetry.bytes_sent += sent
                node.telemetry.last_sent_time = now
            except Exception:
                node.telemetry.errors += 1

        # Emit broadcast frame sync packet to latch all 20+ controllers simultaneously
        if sync and self._nodes:
            sync_packet = DdpEmitter.encode_sync_packet(seq=self._frame_seq)
            self._frame_seq = (self._frame_seq % 15) + 1
            try:
                sync_sent = self._sender.send_packet(self.broadcast_ip, self.sync_port, sync_packet)
                total_bytes += sync_sent
            except Exception:
                pass

        return total_bytes

    def get_telemetry(self) -> dict[str, dict[str, Any]]:
        """Return real-time transmission statistics across all nodes."""
        return {nid: n.telemetry.to_dict() for nid, n in self._nodes.items()}

    def close(self) -> None:
        """Close socket resources."""
        if self._owns_sender:
            self._sender.close()
        self._nodes.clear()
