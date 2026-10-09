"""Device Fleet manager for multi-controller orchestration."""

from __future__ import annotations
from dataclasses import dataclass
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.network.udp_client import MockUdpClient, UdpClient, UdpSender
from wled_app.protocols.base import ProtocolEmitter
from wled_app.protocols.registry import get_emitter


@dataclass
class DeviceNode:
    """A managed device endpoint in the fleet."""
    device: DeviceConfig
    emitter: ProtocolEmitter
    sender: UdpSender
    frame: FrameBuffer
    owns_sender: bool = True

    def close(self) -> None:
        if self.owns_sender:
            self.sender.close()


class DeviceFleet:
    """Manages concurrent transmission and framebuffers across multiple physical devices."""

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self._nodes: dict[str, DeviceNode] = {}

    def add_device(
        self,
        device: DeviceConfig,
        emitter: ProtocolEmitter | None = None,
        sender: UdpSender | None = None,
    ) -> DeviceNode:
        """Register a device with the fleet."""
        res_emitter = emitter or get_emitter(device.protocol)
        if sender is not None:
            res_sender = sender
            owns_sender = False
        else:
            res_sender = MockUdpClient() if self.dry_run else UdpClient()
            owns_sender = True

        node = DeviceNode(
            device=device,
            emitter=res_emitter,
            sender=res_sender,
            frame=FrameBuffer(device.total_leds),
            owns_sender=owns_sender,
        )
        self._nodes[device.id] = node
        return node

    def remove_device(self, device_id: str) -> DeviceNode | None:
        """Remove a device from the fleet."""
        node = self._nodes.pop(device_id, None)
        if node:
            node.close()
        return node

    def get_node(self, device_id: str) -> DeviceNode | None:
        """Get device node by ID."""
        return self._nodes.get(device_id)

    @property
    def devices(self) -> list[DeviceConfig]:
        """List of all registered devices."""
        return [node.device for node in self._nodes.values()]

    def transmit_node(self, node: DeviceNode) -> int:
        """Encode and transmit current frame buffer to this device endpoint."""
        if node.device.total_leds == 0:
            return 0
        packets = node.emitter.encode_frame(node.frame)
        return node.sender.send_packets(node.device.ip, node.device.port, packets)

    def close(self) -> None:
        """Close all network clients."""
        for node in self._nodes.values():
            node.close()
        self._nodes.clear()
