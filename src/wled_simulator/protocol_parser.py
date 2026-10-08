"""Binary datagram parsers for WLED protocols (DDP, DRGB, DNRGB)."""

from __future__ import annotations
import struct
from wled_simulator.models import DdpDatagram, DrgbDatagram


class ProtocolParser:
    """Parses raw UDP network packets into typed datagram structures.

    Adheres to 'Parse, don't validate' by converting raw untrusted byte buffers
    at the network boundary into strongly typed, immutable dataclasses.
    """

    @staticmethod
    def parse_ddp(data: bytes) -> DdpDatagram | None:
        """Parse raw UDP bytes as a Distributed Display Protocol (DDP) datagram.

        Returns None if packet is smaller than the 10-byte DDP header.
        """
        if len(data) < 10:
            return None

        # 10-byte DDP Header: >BBBB I H
        flags, seq, data_type, dest_id, offset, length = struct.unpack(">BBBB I H", data[:10])
        payload = data[10 : 10 + length]

        push = bool(flags & 0x01)
        version = (flags >> 6) & 0x03

        return DdpDatagram(
            flags=flags,
            sequence=seq,
            data_type=data_type,
            dest_id=dest_id,
            offset=offset,
            length=len(payload),
            payload=payload,
            push=push,
            version=version,
        )

    @staticmethod
    def parse_drgb(data: bytes) -> DrgbDatagram | None:
        """Parse raw UDP bytes as Direct RGB / DNRGB.

        Returns None if packet is smaller than 2 bytes.
        """
        if len(data) < 2:
            return None

        cmd = data[0]
        timeout = data[1]

        if cmd == 4:  # DNRGB: Direct Numbered RGB
            if len(data) < 4:
                return None
            start_led = (data[2] << 8) | data[3]
            payload = data[4:]
            return DrgbDatagram(command=cmd, timeout=timeout, payload=payload, start_led=start_led)

        elif cmd == 2:  # DRGB: Direct RGB starting at LED 0
            payload = data[2:]
            return DrgbDatagram(command=cmd, timeout=timeout, payload=payload, start_led=0)

        elif cmd == 1:  # WARLS
            payload = data[2:]
            return DrgbDatagram(command=cmd, timeout=timeout, payload=payload, start_led=0)

        return None
