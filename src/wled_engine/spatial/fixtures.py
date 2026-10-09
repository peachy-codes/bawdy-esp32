"""Domain models for spatial lighting fixtures (Strips, Matrices, Bulbs, Point Lamps)."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from wled_engine.spatial.coordinates import (
    Point3D,
    interpolate_polyline,
    generate_catenary_curve,
)


class Fixture(ABC):
    """Abstract base class for a physical or virtual lighting element."""

    def __init__(
        self,
        fixture_id: str,
        name: str,
        pixel_count: int,
        group: str = "default",
        color_order: str = "GRB",
        tags: list[str] | set[str] | None = None,
    ) -> None:
        if pixel_count <= 0:
            raise ValueError(f"Fixture '{fixture_id}' must have at least 1 pixel (got {pixel_count})")
        self.id = fixture_id
        self.name = name
        self.pixel_count = pixel_count
        self.group = group
        self.color_order = color_order.upper()
        self.tags = set(tags) if tags else set()

    @abstractmethod
    def get_pixel_coordinates(self) -> list[Point3D]:
        """Compute physical (X, Y, Z) coordinates for every pixel in the fixture."""
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize fixture to JSON dictionary."""
        ...

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Fixture:
        """Factory creating fixture instance from dictionary specification."""
        ftype = data.get("type", "linear_strip").lower()
        if ftype in ("linear_strip", "strip", "polyline"):
            return LinearStripFixture.from_dict(data)
        elif ftype in ("matrix", "panel", "grid"):
            return MatrixFixture.from_dict(data)
        elif ftype in ("point", "lamp", "spot"):
            return PointFixture.from_dict(data)
        elif ftype in ("bulb_string", "festoon", "catenary"):
            return BulbStringFixture.from_dict(data)
        elif ftype in ("projector", "viewport"):
            return ProjectorViewport.from_dict(data)
        else:
            raise ValueError(f"Unknown fixture type: {ftype}")


class LinearStripFixture(Fixture):
    """1D straight strip or continuous polyline interpolated across physical waypoints."""

    def __init__(
        self,
        fixture_id: str,
        name: str,
        pixel_count: int,
        waypoints: list[Point3D],
        reversed: bool = False,
        group: str = "default",
        color_order: str = "GRB",
        tags: list[str] | set[str] | None = None,
    ) -> None:
        super().__init__(fixture_id, name, pixel_count, group, color_order, tags)
        if len(waypoints) < 2:
            raise ValueError("LinearStripFixture requires at least 2 waypoints")
        self.waypoints = list(waypoints)
        self.reversed = reversed

    def get_pixel_coordinates(self) -> list[Point3D]:
        coords = interpolate_polyline(self.waypoints, self.pixel_count)
        return list(reversed(coords)) if self.reversed else coords

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "linear_strip",
            "id": self.id,
            "name": self.name,
            "pixel_count": self.pixel_count,
            "waypoints": [p.to_dict() for p in self.waypoints],
            "reversed": self.reversed,
            "group": self.group,
            "color_order": self.color_order,
            "tags": sorted(list(self.tags)),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LinearStripFixture:
        pts = [Point3D.from_dict(p) for p in data.get("waypoints", [])]
        return cls(
            fixture_id=data["id"],
            name=data.get("name", data["id"]),
            pixel_count=int(data["pixel_count"]),
            waypoints=pts,
            reversed=bool(data.get("reversed", False)),
            group=data.get("group", "default"),
            color_order=data.get("color_order", "GRB"),
            tags=data.get("tags"),
        )


class MatrixFixture(Fixture):
    """2D LED matrix or video panel with serpentine zigzag wiring options."""

    def __init__(
        self,
        fixture_id: str,
        name: str,
        rows: int,
        cols: int,
        origin: Point3D = Point3D(0.0, 0.0, 0.0),
        width: float = 1.0,
        height: float = 1.0,
        serpentine: bool = True,
        vertical: bool = False,
        start_corner: str = "top_left",
        group: str = "default",
        color_order: str = "GRB",
        tags: list[str] | set[str] | None = None,
    ) -> None:
        super().__init__(fixture_id, name, rows * cols, group, color_order, tags)
        if rows <= 0 or cols <= 0:
            raise ValueError(f"Matrix dimensions must be positive (got {rows}x{cols})")
        self.rows = rows
        self.cols = cols
        self.origin = origin
        self.width = width
        self.height = height
        self.serpentine = serpentine
        self.vertical = vertical
        self.start_corner = start_corner.lower()

    def get_pixel_coordinates(self) -> list[Point3D]:
        """Compute pixel coordinates in row/column order matching physical raster order."""
        dx = self.width / (self.cols - 1) if self.cols > 1 else 0.0
        dy = self.height / (self.rows - 1) if self.rows > 1 else 0.0

        coords: list[Point3D] = []

        if not self.vertical:
            # Horizontal raster: row-by-row
            for r in range(self.rows):
                # Check serpentine reversal on odd rows
                row_reversed = self.serpentine and (r % 2 == 1)
                col_range = range(self.cols - 1, -1, -1) if row_reversed else range(self.cols)

                # Vertical direction
                y_val = self.origin.y - (r * dy) if "top" in self.start_corner else self.origin.y + (r * dy)

                for c in col_range:
                    x_val = self.origin.x + (c * dx) if "left" in self.start_corner else self.origin.x - (c * dx)
                    coords.append(Point3D(x_val, y_val, self.origin.z))
        else:
            # Vertical raster: column-by-column
            for c in range(self.cols):
                col_reversed = self.serpentine and (c % 2 == 1)
                row_range = range(self.rows - 1, -1, -1) if col_reversed else range(self.rows)

                x_val = self.origin.x + (c * dx) if "left" in self.start_corner else self.origin.x - (c * dx)

                for r in row_range:
                    y_val = self.origin.y - (r * dy) if "top" in self.start_corner else self.origin.y + (r * dy)
                    coords.append(Point3D(x_val, y_val, self.origin.z))

        return coords

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "matrix",
            "id": self.id,
            "name": self.name,
            "rows": self.rows,
            "cols": self.cols,
            "origin": self.origin.to_dict(),
            "width": self.width,
            "height": self.height,
            "serpentine": self.serpentine,
            "vertical": self.vertical,
            "start_corner": self.start_corner,
            "group": self.group,
            "color_order": self.color_order,
            "tags": sorted(list(self.tags)),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MatrixFixture:
        orig = Point3D.from_dict(data.get("origin", {}))
        return cls(
            fixture_id=data["id"],
            name=data.get("name", data["id"]),
            rows=int(data["rows"]),
            cols=int(data["cols"]),
            origin=orig,
            width=float(data.get("width", 1.0)),
            height=float(data.get("height", 1.0)),
            serpentine=bool(data.get("serpentine", True)),
            vertical=bool(data.get("vertical", False)),
            start_corner=data.get("start_corner", "top_left"),
            group=data.get("group", "default"),
            color_order=data.get("color_order", "GRB"),
            tags=data.get("tags"),
        )


class PointFixture(Fixture):
    """Discrete single-point or cluster fixture (Floor lamp, Spotlight, Orb)."""

    def __init__(
        self,
        fixture_id: str,
        name: str,
        location: Point3D,
        pixel_count: int = 1,
        radius: float = 0.0,
        group: str = "default",
        color_order: str = "GRB",
        tags: list[str] | set[str] | None = None,
    ) -> None:
        super().__init__(fixture_id, name, pixel_count, group, color_order, tags)
        self.location = location
        self.radius = radius

    def get_pixel_coordinates(self) -> list[Point3D]:
        if self.pixel_count == 1 or self.radius <= 1e-6:
            return [self.location] * self.pixel_count

        # Cluster around center location in a ring
        import math
        coords: list[Point3D] = []
        for i in range(self.pixel_count):
            angle = (2.0 * math.pi * i) / self.pixel_count
            px = self.location.x + self.radius * math.cos(angle)
            pz = self.location.z + self.radius * math.sin(angle)
            coords.append(Point3D(px, self.location.y, pz))
        return coords

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "point",
            "id": self.id,
            "name": self.name,
            "location": self.location.to_dict(),
            "pixel_count": self.pixel_count,
            "radius": self.radius,
            "group": self.group,
            "color_order": self.color_order,
            "tags": sorted(list(self.tags)),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PointFixture:
        loc = Point3D.from_dict(data.get("location", {}))
        return cls(
            fixture_id=data["id"],
            name=data.get("name", data["id"]),
            location=loc,
            pixel_count=int(data.get("pixel_count", 1)),
            radius=float(data.get("radius", 0.0)),
            group=data.get("group", "default"),
            color_order=data.get("color_order", "GRB"),
            tags=data.get("tags"),
        )


class BulbStringFixture(Fixture):
    """Overhead festoon / cafe light string hanging along a catenary curve."""

    def __init__(
        self,
        fixture_id: str,
        name: str,
        bulb_count: int,
        start: Point3D,
        end: Point3D,
        sag: float = 0.3,
        sag_axis: str = "y",
        group: str = "default",
        color_order: str = "RGB",
        tags: list[str] | set[str] | None = None,
    ) -> None:
        super().__init__(fixture_id, name, bulb_count, group, color_order, tags)
        self.start = start
        self.end = end
        self.sag = sag
        self.sag_axis = sag_axis

    def get_pixel_coordinates(self) -> list[Point3D]:
        return generate_catenary_curve(
            start=self.start,
            end=self.end,
            sag=self.sag,
            count=self.pixel_count,
            sag_axis=self.sag_axis,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "bulb_string",
            "id": self.id,
            "name": self.name,
            "pixel_count": self.pixel_count,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "sag": self.sag,
            "sag_axis": self.sag_axis,
            "group": self.group,
            "color_order": self.color_order,
            "tags": sorted(list(self.tags)),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BulbStringFixture:
        return cls(
            fixture_id=data["id"],
            name=data.get("name", data["id"]),
            bulb_count=int(data["pixel_count"]),
            start=Point3D.from_dict(data["start"]),
            end=Point3D.from_dict(data["end"]),
            sag=float(data.get("sag", 0.3)),
            sag_axis=data.get("sag_axis", "y"),
            group=data.get("group", "default"),
            color_order=data.get("color_order", "RGB"),
            tags=data.get("tags"),
        )


class ProjectorViewport(Fixture):
    """Virtual 2D projection raster viewport mapping a region of the spatial canvas."""

    def __init__(
        self,
        fixture_id: str,
        name: str,
        top_left: Point3D,
        bottom_right: Point3D,
        resolution_x: int = 1920,
        resolution_y: int = 1080,
        group: str = "projector",
        tags: list[str] | set[str] | None = None,
    ) -> None:
        # A projector fixture has 1 logical frame buffer
        super().__init__(fixture_id, name, 1, group, "RGB", tags)
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.resolution_x = resolution_x
        self.resolution_y = resolution_y

    def get_pixel_coordinates(self) -> list[Point3D]:
        # Represents center of projection surface
        center = self.top_left.lerp(self.bottom_right, 0.5)
        return [center]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "projector",
            "id": self.id,
            "name": self.name,
            "top_left": self.top_left.to_dict(),
            "bottom_right": self.bottom_right.to_dict(),
            "resolution_x": self.resolution_x,
            "resolution_y": self.resolution_y,
            "group": self.group,
            "tags": sorted(list(self.tags)),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectorViewport:
        return cls(
            fixture_id=data["id"],
            name=data.get("name", data["id"]),
            top_left=Point3D.from_dict(data["top_left"]),
            bottom_right=Point3D.from_dict(data["bottom_right"]),
            resolution_x=int(data.get("resolution_x", 1920)),
            resolution_y=int(data.get("resolution_y", 1080)),
            group=data.get("group", "projector"),
            tags=data.get("tags"),
        )
