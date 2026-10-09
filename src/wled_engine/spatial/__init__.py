"""Spatial lighting modeling package for 2D/3D fixtures, universe coordination, and sampling."""

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
from wled_engine.spatial.sampler import SpatialSampler
from wled_engine.spatial.patterns import (
    spatial_angle_sweep,
    spatial_radial_pulse,
    spatial_linear_gradient,
    spatial_rainbow_cloud,
)

__all__ = [
    "Point2D",
    "Point3D",
    "BoundingBox3D",
    "interpolate_polyline",
    "generate_catenary_curve",
    "Fixture",
    "LinearStripFixture",
    "MatrixFixture",
    "PointFixture",
    "BulbStringFixture",
    "ProjectorViewport",
    "SpatialUniverse",
    "SpatialSampler",
    "spatial_angle_sweep",
    "spatial_radial_pulse",
    "spatial_linear_gradient",
    "spatial_rainbow_cloud",
    "create_demo_venue",
    "save_default_venue_files",
]

from wled_engine.spatial.venue import create_demo_venue, save_default_venue_files

