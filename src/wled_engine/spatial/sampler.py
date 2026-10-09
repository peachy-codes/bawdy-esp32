"""SpatialSampler: Evaluates continuous spatial color fields and packs physical controller channel buffers."""

from __future__ import annotations
from typing import Callable

from wled_app.domain.color import Color
from wled_engine.patch.target import permute_color, ColorOrder
from wled_engine.patch.patch_table import PatchTable
from wled_engine.spatial.coordinates import Point3D
from wled_engine.spatial.universe import SpatialUniverse


class SpatialSampler:
    """Samples visual color fields in physical/normalized coordinate space

    and routes bytes to hardware controller frame buffers according to the PatchTable.
    """

    def __init__(self, universe: SpatialUniverse, patch_table: PatchTable) -> None:
        self.universe = universe
        self.patch_table = patch_table

    def sample_field_to_fixtures(
        self,
        field_func: Callable[[Point3D], Color],
        use_normalized: bool = True,
    ) -> dict[str, list[Color]]:
        """Evaluate continuous spatial color field for every pixel in every fixture.

        Returns:
            dict mapping fixture_id -> list[Color] (one per pixel).
        """
        result: dict[str, list[Color]] = {}
        for fixture in self.universe.fixtures:
            if use_normalized:
                coords = self.universe.get_normalized_coordinates(fixture.id)
            else:
                coords = self.universe.get_pixel_coordinates(fixture.id)

            pixels = [field_func(p) for p in coords]
            result[fixture.id] = pixels
        return result

    def route_fixture_colors_to_controllers(
        self,
        fixture_colors: dict[str, list[Color]],
        master_brightness: float = 1.0,
    ) -> dict[str, list[bytearray]]:
        """Pack pre-sampled fixture colors into physical controller channel byte buffers.

        Returns:
            dict mapping controller_id -> list[bytearray] (one bytearray per channel).
        """
        # Determine controller channel allocations
        controller_buffers: dict[str, list[bytearray]] = {}

        controllers = self.patch_table.get_controllers()
        for cid in controllers:
            ch_indices = self.patch_table.get_channel_indices(cid)
            max_ch = max(ch_indices) if ch_indices else 0
            # Initialize buffers for channels 0..max_ch
            buffers: list[bytearray] = []
            for ch in range(max_ch + 1):
                length = self.patch_table.get_channel_pixel_length(cid, ch)
                # Default 3 bytes per pixel (RGB/GRB)
                buffers.append(bytearray(length * 3))
            controller_buffers[cid] = buffers

        # Route each patch segment
        for seg in self.patch_table.segments:
            cid = seg.controller_id
            ch = seg.channel_index
            colors = fixture_colors.get(seg.fixture_id)
            if not colors:
                continue

            # Extract slice
            start = seg.pixel_start
            end = min(len(colors), seg.pixel_end)
            if start >= len(colors):
                continue
            slice_colors = colors[start:end]

            if seg.reversed:
                slice_colors = list(reversed(slice_colors))

            # Bytes per pixel based on color order
            bpp = 4 if seg.color_order in (ColorOrder.RGBW, ColorOrder.GRBW) else 3
            buf = controller_buffers[cid][ch]

            # Ensure buffer capacity
            needed_bytes = (seg.port_offset + len(slice_colors)) * bpp
            if len(buf) < needed_bytes:
                buf.extend(b"\x00" * (needed_bytes - len(buf)))

            eff_scale = max(0.0, min(1.0, seg.brightness_scale * master_brightness))

            for i, col in enumerate(slice_colors):
                dest_offset = (seg.port_offset + i) * bpp
                r = int(round(col.r * eff_scale))
                g = int(round(col.g * eff_scale))
                b = int(round(col.b * eff_scale))

                permuted = permute_color(r, g, b, seg.color_order)
                for bi, byte_val in enumerate(permuted):
                    if dest_offset + bi < len(buf):
                        buf[dest_offset + bi] = byte_val

        return controller_buffers

    def sample_and_route(
        self,
        field_func: Callable[[Point3D], Color],
        master_brightness: float = 1.0,
        use_normalized: bool = True,
    ) -> dict[str, list[bytearray]]:
        """Convenience method combining spatial field evaluation and controller byte packing."""
        fixture_colors = self.sample_field_to_fixtures(field_func, use_normalized=use_normalized)
        return self.route_fixture_colors_to_controllers(fixture_colors, master_brightness=master_brightness)
