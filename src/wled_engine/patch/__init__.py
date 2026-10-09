"""Hardware patch modeling package translating spatial fixtures to physical controller channels."""

from wled_engine.patch.target import (
    OutputProtocol,
    ColorOrder,
    PatchSegment,
    permute_color,
)
from wled_engine.patch.patch_table import PatchTable

__all__ = [
    "OutputProtocol",
    "ColorOrder",
    "PatchSegment",
    "permute_color",
    "PatchTable",
]
