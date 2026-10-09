"""Spatial 2D and 3D coordinate geometry for lighting universes."""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Point2D:
    """Immutable 2D coordinate."""
    x: float
    y: float

    def distance_to(self, other: Point2D) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def lerp(self, other: Point2D, t: float) -> Point2D:
        return Point2D(
            x=self.x + (other.x - self.x) * t,
            y=self.y + (other.y - self.y) * t,
        )

    def to_3d(self, z: float = 0.0) -> Point3D:
        return Point3D(x=self.x, y=self.y, z=z)

    def to_dict(self) -> dict[str, float]:
        return {"x": round(self.x, 4), "y": round(self.y, 4)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Point2D:
        return cls(x=float(data.get("x", 0.0)), y=float(data.get("y", 0.0)))


@dataclass(frozen=True, slots=True)
class Point3D:
    """Immutable 3D coordinate."""
    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: Point3D) -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def lerp(self, other: Point3D, t: float) -> Point3D:
        return Point3D(
            x=self.x + (other.x - self.x) * t,
            y=self.y + (other.y - self.y) * t,
            z=self.z + (other.z - self.z) * t,
        )

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def to_dict(self) -> dict[str, float]:
        return {"x": round(self.x, 4), "y": round(self.y, 4), "z": round(self.z, 4)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Point3D:
        return cls(
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            z=float(data.get("z", 0.0)),
        )


@dataclass
class BoundingBox3D:
    """Axis-aligned 3D bounding box for spatial lighting universes."""
    min_x: float = float("inf")
    min_y: float = float("inf")
    min_z: float = float("inf")
    max_x: float = float("-inf")
    max_y: float = float("-inf")
    max_z: float = float("-inf")

    @property
    def width(self) -> float:
        return max(0.0, self.max_x - self.min_x)

    @property
    def height(self) -> float:
        return max(0.0, self.max_y - self.min_y)

    @property
    def depth(self) -> float:
        return max(0.0, self.max_z - self.min_z)

    @property
    def is_valid(self) -> bool:
        return self.min_x <= self.max_x and self.min_y <= self.max_y and self.min_z <= self.max_z

    def expand(self, p: Point3D) -> None:
        """Expand bounds to enclose point p."""
        if p.x < self.min_x: self.min_x = p.x
        if p.x > self.max_x: self.max_x = p.x
        if p.y < self.min_y: self.min_y = p.y
        if p.y > self.max_y: self.max_y = p.y
        if p.z < self.min_z: self.min_z = p.z
        if p.z > self.max_z: self.max_z = p.z

    def normalize(self, p: Point3D) -> Point3D:
        """Normalize coordinate p into [0.0, 1.0] unit box relative to bounds."""
        w = self.width
        h = self.height
        d = self.depth

        nx = (p.x - self.min_x) / w if w > 1e-6 else 0.5
        ny = (p.y - self.min_y) / h if h > 1e-6 else 0.5
        nz = (p.z - self.min_z) / d if d > 1e-6 else 0.5

        return Point3D(
            x=max(0.0, min(1.0, nx)),
            y=max(0.0, min(1.0, ny)),
            z=max(0.0, min(1.0, nz)),
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "min_x": round(self.min_x, 4),
            "min_y": round(self.min_y, 4),
            "min_z": round(self.min_z, 4),
            "max_x": round(self.max_x, 4),
            "max_y": round(self.max_y, 4),
            "max_z": round(self.max_z, 4),
            "width": round(self.width, 4),
            "height": round(self.height, 4),
            "depth": round(self.depth, 4),
        }


def interpolate_polyline(waypoints: list[Point3D], count: int) -> list[Point3D]:
    """Distribute count equidistant pixel coordinates along a 3D polyline."""
    if count <= 0:
        return []
    if not waypoints:
        return [Point3D(0.0, 0.0, 0.0)] * count
    if len(waypoints) == 1 or count == 1:
        return [waypoints[0]] * count

    # Compute cumulative segment lengths
    lengths: list[float] = [0.0]
    total_length = 0.0
    for i in range(len(waypoints) - 1):
        seg_len = waypoints[i].distance_to(waypoints[i + 1])
        total_length += seg_len
        lengths.append(total_length)

    if total_length < 1e-6:
        return [waypoints[0]] * count

    points: list[Point3D] = []
    step = total_length / (count - 1) if count > 1 else 0.0

    current_seg = 0
    for i in range(count):
        target_dist = i * step
        # Advance segment pointer
        while current_seg < len(lengths) - 2 and lengths[current_seg + 1] < target_dist:
            current_seg += 1

        seg_start_dist = lengths[current_seg]
        seg_end_dist = lengths[current_seg + 1]
        seg_len = seg_end_dist - seg_start_dist

        if seg_len < 1e-6:
            t = 0.0
        else:
            t = max(0.0, min(1.0, (target_dist - seg_start_dist) / seg_len))

        p = waypoints[current_seg].lerp(waypoints[current_seg + 1], t)
        points.append(p)

    return points


def generate_catenary_curve(
    start: Point3D,
    end: Point3D,
    sag: float,
    count: int,
    sag_axis: str = "y",
) -> list[Point3D]:
    """Generate count coordinates along a hanging catenary cable curve under gravity.

    sag: The maximum vertical deflection (drop) in middle of the cable.
    sag_axis: Axis of gravitational droop ("y" or "z").
    """
    if count <= 0:
        return []
    if count == 1:
        return [start.lerp(end, 0.5)]

    points: list[Point3D] = []
    for i in range(count):
        t = i / (count - 1)
        base = start.lerp(end, t)
        # Parabolic catenary sag approximation: 4 * sag * t * (1 - t)
        droop = 4.0 * sag * t * (1.0 - t)

        if sag_axis.lower() == "z":
            p = Point3D(x=base.x, y=base.y, z=base.z - droop)
        else:
            p = Point3D(x=base.x, y=base.y - droop, z=base.z)

        points.append(p)

    return points
