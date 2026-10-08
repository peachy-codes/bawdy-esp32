"""Protocol registry and factory for resolving ProtocolEmitter instances."""

from __future__ import annotations

from wled_app.domain.device import ProtocolType
from wled_app.protocols.base import ProtocolEmitter
from wled_app.protocols.ddp import DdpEmitter
from wled_app.protocols.drgb import DnrgbEmitter, DrgbEmitter
from wled_app.protocols.warls import WarlsEmitter

_EMITTER_FACTORIES: dict[ProtocolType, type[ProtocolEmitter]] = {
    ProtocolType.DDP: DdpEmitter,
    ProtocolType.DRGB: DrgbEmitter,
    ProtocolType.DNRGB: DnrgbEmitter,
    ProtocolType.WARLS: WarlsEmitter,
}


def get_emitter(protocol: ProtocolType | str) -> ProtocolEmitter:
    """Retrieve or construct a ProtocolEmitter for the specified protocol.

    Args:
        protocol: ProtocolType enum or case-insensitive string name.

    Returns:
        Configured ProtocolEmitter instance.

    Raises:
        ValueError: If the protocol type is unknown or unsupported.
    """
    if isinstance(protocol, str):
        try:
            proto_enum = ProtocolType(protocol.lower())
        except ValueError as exc:
            raise ValueError(
                f"Unsupported protocol '{protocol}'. Supported: {[p.value for p in ProtocolType]}"
            ) from exc
    else:
        proto_enum = protocol

    emitter_cls = _EMITTER_FACTORIES.get(proto_enum)
    if not emitter_cls:
        raise ValueError(f"No emitter registered for protocol '{proto_enum}'")

    return emitter_cls()
