"""Integration tests for SpatialSampler evaluating continuous fields over 20 controllers."""

from __future__ import annotations
import unittest

from wled_app.domain.color import Color
from wled_engine.patch.target import ColorOrder
from wled_engine.patch.patch_table import PatchTable
from wled_engine.spatial.coordinates import Point3D
from wled_engine.spatial.fixtures import (
    LinearStripFixture,
    MatrixFixture,
    PointFixture,
    BulbStringFixture,
    ProjectorViewport,
)
from wled_engine.spatial.universe import SpatialUniverse
from wled_engine.spatial.sampler import SpatialSampler
from wled_engine.spatial.patterns import (
    spatial_angle_sweep,
    spatial_radial_pulse,
    spatial_linear_gradient,
)


class TestSpatialSampler(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = SpatialUniverse("Grand Venue Universe")
        self.patch = PatchTable("Grand Venue 20-Node Patch")

        # 1. 10 Linear strips across facade & perimeter
        for i in range(10):
            fid = f"strip_{i:02d}"
            strip = LinearStripFixture(
                fixture_id=fid,
                name=f"Perimeter Strip {i}",
                pixel_count=100,
                waypoints=[Point3D(i * 2.0, 0.0), Point3D((i + 1) * 2.0, 0.0)],
                group="strips",
            )
            self.universe.add_fixture(strip)
            # Patch each strip to wled_01 .. wled_10 Channel 0
            cid = f"wled_{i + 1:02d}"
            self.patch.patch_fixture(fid, 100, controller_id=cid, channel_index=0, color_order=ColorOrder.GRB)

        # 2. 1 Matrix panel (16x16 = 256 pixels)
        matrix = MatrixFixture(
            fixture_id="stage_matrix",
            name="Stage Backdrop",
            rows=16,
            cols=16,
            origin=Point3D(5.0, 4.0, 0.0),
            width=4.0,
            height=4.0,
            group="panels",
        )
        self.universe.add_fixture(matrix)
        # Patch matrix split across 2 channels on wled_11 (128 pixels on Ch0, 128 on Ch1)
        self.patch.patch_segment("stage_matrix", 0, 128, controller_id="wled_11", channel_index=0)
        self.patch.patch_segment("stage_matrix", 128, 128, controller_id="wled_11", channel_index=1)

        # 3. 4 Festoon lightbulb strings overhead (25 bulbs each)
        for i in range(4):
            bid = f"bulb_string_{i}"
            bulbs = BulbStringFixture(
                fixture_id=bid,
                name=f"Overhead Bulbs {i}",
                bulb_count=25,
                start=Point3D(0.0, 5.0, i * 2.0),
                end=Point3D(20.0, 5.0, i * 2.0),
                sag=0.6,
                group="festoon",
                color_order="RGB",
            )
            self.universe.add_fixture(bulbs)
            # Patch to wled_12 .. wled_15 Channel 0
            cid = f"wled_{12 + i:02d}"
            self.patch.patch_fixture(bid, 25, controller_id=cid, channel_index=0, color_order=ColorOrder.RGB)

        # 4. 4 Floor lamps (PointFixtures)
        for i in range(4):
            lid = f"lamp_{i}"
            lamp = PointFixture(
                fixture_id=lid,
                name=f"Accent Lamp {i}",
                location=Point3D(i * 6.0, 0.0, 5.0),
                pixel_count=1,
                group="lamps",
            )
            self.universe.add_fixture(lamp)
            # Patch all 4 lamps to wled_16 Channel 0 offsets 0..3
            self.patch.patch_fixture(lid, 1, controller_id="wled_16", channel_index=0, port_offset=i)

        # 5. Projector Viewport covering center area
        proj = ProjectorViewport(
            fixture_id="center_projector",
            name="Main Projection Surface",
            top_left=Point3D(5.0, 5.0),
            bottom_right=Point3D(15.0, 0.0),
        )
        self.universe.add_fixture(proj)
        # Projector routed to virtual raster target
        self.patch.patch_fixture("center_projector", 1, controller_id="projector_node", channel_index=0)

        # Setup remaining boards wled_17..wled_20 as extra accent channels
        for i in range(17, 21):
            cid = f"wled_{i:02d}"
            self.patch.patch_fixture(f"extra_accent_{i}", 50, controller_id=cid, channel_index=0)
            self.universe.add_fixture(LinearStripFixture(
                f"extra_accent_{i}", f"Accent {i}", 50,
                [Point3D(0.0, float(i)), Point3D(5.0, float(i))]
            ))

        self.sampler = SpatialSampler(self.universe, self.patch)

    def test_patch_validation(self) -> None:
        errors = self.patch.validate()
        self.assertEqual(errors, [])
        self.assertEqual(len(self.patch.get_controllers()), 21) # 20 WLED boards + 1 projector node

    def test_spatial_angle_sweep_sampling(self) -> None:
        # Create continuous 45-degree angle sweep across the entire space
        sweep = spatial_angle_sweep(angle_deg=45.0, color_a=Color(255, 0, 0), color_b=Color(0, 0, 255))
        buffers = self.sampler.sample_and_route(sweep, master_brightness=1.0)

        # Assert all 20 WLED controllers have non-empty buffers
        for i in range(1, 21):
            cid = f"wled_{i:02d}"
            self.assertIn(cid, buffers)
            ch0 = buffers[cid][0]
            self.assertTrue(len(ch0) > 0)
            # Check that bytes are non-zero
            self.assertTrue(any(b > 0 for b in ch0))

        # Check wled_11 (matrix split over 2 channels)
        self.assertEqual(len(buffers["wled_11"]), 2)
        self.assertEqual(len(buffers["wled_11"][0]), 128 * 3)
        self.assertEqual(len(buffers["wled_11"][1]), 128 * 3)

    def test_spatial_radial_pulse_and_brightness_scaling(self) -> None:
        # Radial pulse from center of space
        pulse = spatial_radial_pulse(center=Point3D(0.5, 0.5, 0.5), color_center=Color(200, 200, 200), color_edge=Color(0, 0, 0))

        # Full brightness
        bufs_full = self.sampler.sample_and_route(pulse, master_brightness=1.0)
        # Half brightness
        bufs_half = self.sampler.sample_and_route(pulse, master_brightness=0.5)

        # First pixel of wled_01 Channel 0
        b_full = bufs_full["wled_01"][0][0]
        b_half = bufs_half["wled_01"][0][0]

        # b_half should be approximately half of b_full
        self.assertAlmostEqual(b_half, b_full // 2, delta=2)

    def test_color_order_permutation_in_packed_buffers(self) -> None:
        # Solid red field: Color(255, 0, 0)
        red_field = lambda p: Color(255, 0, 0)
        buffers = self.sampler.sample_and_route(red_field, master_brightness=1.0)

        # wled_01 was patched as ColorOrder.GRB: Red should be placed at byte index 1 (G=0, R=255, B=0)
        wled_01_ch0 = buffers["wled_01"][0]
        self.assertEqual(wled_01_ch0[0], 0)   # G
        self.assertEqual(wled_01_ch0[1], 255) # R
        self.assertEqual(wled_01_ch0[2], 0)   # B

        # wled_12 (bulb string) was patched as ColorOrder.RGB: Red at byte 0 (R=255, G=0, B=0)
        wled_12_ch0 = buffers["wled_12"][0]
        self.assertEqual(wled_12_ch0[0], 255) # R
        self.assertEqual(wled_12_ch0[1], 0)   # G
        self.assertEqual(wled_12_ch0[2], 0)   # B


if __name__ == "__main__":
    unittest.main()
