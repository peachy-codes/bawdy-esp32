"""Unit tests for spatial coordinate math, fixtures, and SpatialUniverse."""

from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from wled_engine.spatial.coordinates import (
    Point2D,
    Point3D,
    BoundingBox3D,
    interpolate_polyline,
    generate_catenary_curve,
)
from wled_engine.spatial.fixtures import (
    Fixture,
    LinearStripFixture,
    MatrixFixture,
    PointFixture,
    BulbStringFixture,
    ProjectorViewport,
)
from wled_engine.spatial.universe import SpatialUniverse


class TestSpatialCoordinates(unittest.TestCase):
    def test_point2d_and_3d(self) -> None:
        p1 = Point3D(0.0, 0.0, 0.0)
        p2 = Point3D(3.0, 4.0, 0.0)
        self.assertAlmostEqual(p1.distance_to(p2), 5.0)

        mid = p1.lerp(p2, 0.5)
        self.assertAlmostEqual(mid.x, 1.5)
        self.assertAlmostEqual(mid.y, 2.0)
        self.assertAlmostEqual(mid.z, 0.0)

        d = p2.to_dict()
        self.assertEqual(d["x"], 3.0)
        self.assertEqual(Point3D.from_dict(d), p2)

    def test_bounding_box_normalization(self) -> None:
        bbox = BoundingBox3D()
        bbox.expand(Point3D(-10.0, 0.0, 5.0))
        bbox.expand(Point3D(10.0, 50.0, 15.0))

        self.assertEqual(bbox.width, 20.0)
        self.assertEqual(bbox.height, 50.0)
        self.assertEqual(bbox.depth, 10.0)

        # Center point
        center = Point3D(0.0, 25.0, 10.0)
        norm = bbox.normalize(center)
        self.assertAlmostEqual(norm.x, 0.5)
        self.assertAlmostEqual(norm.y, 0.5)
        self.assertAlmostEqual(norm.z, 0.5)

    def test_polyline_interpolation(self) -> None:
        # L-shaped polyline: (0,0) -> (10,0) -> (10,10)
        wps = [Point3D(0.0, 0.0), Point3D(10.0, 0.0), Point3D(10.0, 10.0)]
        pts = interpolate_polyline(wps, count=5)
        self.assertEqual(len(pts), 5)
        # Expected: (0,0), (5,0), (10,0), (10,5), (10,10)
        self.assertAlmostEqual(pts[0].x, 0.0)
        self.assertAlmostEqual(pts[1].x, 5.0)
        self.assertAlmostEqual(pts[2].x, 10.0)
        self.assertAlmostEqual(pts[3].x, 10.0)
        self.assertAlmostEqual(pts[3].y, 5.0)
        self.assertAlmostEqual(pts[4].y, 10.0)

    def test_catenary_curve(self) -> None:
        start = Point3D(0.0, 5.0, 0.0)
        end = Point3D(10.0, 5.0, 0.0)
        curve = generate_catenary_curve(start, end, sag=1.0, count=5, sag_axis="y")
        self.assertEqual(len(curve), 5)
        # Midpoint should have maximum sag (dropped by 1.0 down to y = 4.0)
        self.assertAlmostEqual(curve[2].x, 5.0)
        self.assertAlmostEqual(curve[2].y, 4.0)


class TestSpatialFixtures(unittest.TestCase):
    def test_linear_strip_fixture(self) -> None:
        strip = LinearStripFixture(
            fixture_id="roof_main",
            name="Roof Peak",
            pixel_count=100,
            waypoints=[Point3D(0.0, 5.0), Point3D(10.0, 8.0), Point3D(20.0, 5.0)],
            group="roof",
        )
        self.assertEqual(strip.pixel_count, 100)
        coords = strip.get_pixel_coordinates()
        self.assertEqual(len(coords), 100)
        self.assertAlmostEqual(coords[0].x, 0.0)
        self.assertAlmostEqual(coords[-1].x, 20.0)

        # Reversal test
        strip_rev = LinearStripFixture(
            fixture_id="roof_rev",
            name="Roof Peak Rev",
            pixel_count=100,
            waypoints=[Point3D(0.0, 5.0), Point3D(10.0, 8.0), Point3D(20.0, 5.0)],
            reversed=True,
        )
        coords_rev = strip_rev.get_pixel_coordinates()
        self.assertAlmostEqual(coords_rev[0].x, 20.0)
        self.assertAlmostEqual(coords_rev[-1].x, 0.0)

    def test_matrix_fixture_serpentine(self) -> None:
        # 4 rows x 5 cols matrix
        matrix = MatrixFixture(
            fixture_id="panel_1",
            name="Matrix Display",
            rows=4,
            cols=5,
            origin=Point3D(0.0, 3.0),
            width=4.0,
            height=3.0,
            serpentine=True,
            start_corner="top_left",
        )
        self.assertEqual(matrix.pixel_count, 20)
        coords = matrix.get_pixel_coordinates()
        self.assertEqual(len(coords), 20)

        # Row 0 (cols 0..4 left-to-right): x increases
        self.assertAlmostEqual(coords[0].x, 0.0)
        self.assertAlmostEqual(coords[4].x, 4.0)
        # Row 1 (serpentine reversed: cols 4..0 right-to-left): x decreases
        self.assertAlmostEqual(coords[5].x, 4.0)
        self.assertAlmostEqual(coords[9].x, 0.0)

    def test_point_fixture(self) -> None:
        lamp = PointFixture(
            fixture_id="floor_lamp_1",
            name="Corner Lamp",
            location=Point3D(2.5, 0.0, 4.0),
            pixel_count=1,
            group="lamps",
        )
        coords = lamp.get_pixel_coordinates()
        self.assertEqual(len(coords), 1)
        self.assertEqual(coords[0], Point3D(2.5, 0.0, 4.0))

    def test_bulb_string_fixture(self) -> None:
        festoon = BulbStringFixture(
            fixture_id="cafe_lights",
            name="Patio Bulbs",
            bulb_count=25,
            start=Point3D(0.0, 3.5, 0.0),
            end=Point3D(12.0, 3.5, 5.0),
            sag=0.5,
            group="festoon",
        )
        self.assertEqual(festoon.pixel_count, 25)
        coords = festoon.get_pixel_coordinates()
        self.assertEqual(len(coords), 25)
        self.assertTrue(coords[12].y < 3.5) # Sag below 3.5m

    def test_fixture_polymorphic_deserialization(self) -> None:
        orig = LinearStripFixture("s1", "Strip", 50, [Point3D(0, 0), Point3D(5, 5)])
        d = orig.to_dict()
        restored = Fixture.from_dict(d)
        self.assertIsInstance(restored, LinearStripFixture)
        self.assertEqual(restored.id, "s1")
        self.assertEqual(restored.pixel_count, 50)


class TestSpatialUniverse(unittest.TestCase):
    def test_universe_aggregation_and_bounds(self) -> None:
        uni = SpatialUniverse("Courtyard Installation")
        uni.add_fixture(LinearStripFixture("strip1", "Perimeter", 100, [Point3D(0, 0), Point3D(10, 0)], group="perimeter"))
        uni.add_fixture(MatrixFixture("matrix1", "Sign", 8, 8, origin=Point3D(2, 4), width=2, height=2, group="sign"))
        uni.add_fixture(PointFixture("lamp1", "Torch", Point3D(5, 1, 3), group="lamps"))

        self.assertEqual(len(uni.fixtures), 3)
        self.assertEqual(uni.total_pixels, 100 + 64 + 1)
        self.assertEqual(uni.get_groups(), ["lamps", "perimeter", "sign"])

        bbox = uni.bounding_box
        self.assertAlmostEqual(bbox.min_x, 0.0)
        self.assertAlmostEqual(bbox.max_x, 10.0)
        self.assertAlmostEqual(bbox.min_y, 0.0)
        self.assertAlmostEqual(bbox.max_y, 4.0)

        # Normalized coordinates range between [0, 1]
        norm_coords = uni.get_normalized_coordinates("strip1")
        self.assertEqual(len(norm_coords), 100)
        self.assertAlmostEqual(norm_coords[0].x, 0.0)
        self.assertAlmostEqual(norm_coords[-1].x, 1.0)
        for p in norm_coords:
            self.assertTrue(0.0 <= p.x <= 1.0)
            self.assertTrue(0.0 <= p.y <= 1.0)

    def test_universe_json_persistence(self) -> None:
        uni = SpatialUniverse("Test Venue")
        uni.add_fixture(PointFixture("p1", "Orb", Point3D(1, 2, 3), group="orbs"))
        uni.add_fixture(BulbStringFixture("b1", "String", 10, Point3D(0, 3), Point3D(5, 3), group="overhead"))

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "universe.json"
            uni.save_json(path)
            loaded = SpatialUniverse.load_json(path)

            self.assertEqual(loaded.name, "Test Venue")
            self.assertEqual(len(loaded.fixtures), 2)
            self.assertEqual(loaded.total_pixels, 11)


if __name__ == "__main__":
    unittest.main()
