"""SpatialUniverse: Aggregate container and spatial index for all physical and virtual fixtures."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from wled_engine.spatial.coordinates import Point3D, BoundingBox3D
from wled_engine.spatial.fixtures import Fixture


class SpatialUniverse:
    """Manages the physical arrangement and spatial coordinate cache of all installation fixtures."""

    def __init__(self, name: str = "Default Universe") -> None:
        self.name = name
        self._fixtures: dict[str, Fixture] = {}
        self._bounds_cache: BoundingBox3D | None = None
        self._coords_cache: dict[str, list[Point3D]] = {}
        self._normalized_cache: dict[str, list[Point3D]] = {}

    def add_fixture(self, fixture: Fixture) -> None:
        """Register a fixture in the spatial universe."""
        self._fixtures[fixture.id] = fixture
        self._invalidate_cache()

    def remove_fixture(self, fixture_id: str) -> Fixture | None:
        """Remove a fixture by ID."""
        f = self._fixtures.pop(fixture_id, None)
        if f is not None:
            self._invalidate_cache()
        return f

    def get_fixture(self, fixture_id: str) -> Fixture | None:
        """Retrieve fixture by ID."""
        return self._fixtures.get(fixture_id)

    @property
    def fixtures(self) -> list[Fixture]:
        """List of all registered fixtures."""
        return list(self._fixtures.values())

    @property
    def total_pixels(self) -> int:
        """Total LED pixel count across all fixtures."""
        return sum(f.pixel_count for f in self._fixtures.values())

    @property
    def groups(self) -> list[str]:
        """List all unique fixture group names."""
        return self.get_groups()

    def get_groups(self) -> list[str]:
        """List all unique fixture group names."""
        return sorted(list({f.group for f in self._fixtures.values()}))

    def get_fixtures_by_group(self, group: str) -> list[Fixture]:
        """Filter fixtures belonging to a specific group."""
        return [f for f in self._fixtures.values() if f.group == group]

    def get_fixtures_by_tag(self, tag: str) -> list[Fixture]:
        """Filter fixtures tagged with a specific tag."""
        return [f for f in self._fixtures.values() if tag in f.tags]

    @property
    def bounding_box(self) -> BoundingBox3D:
        """Compute or return cached 3D axis-aligned bounding box enclosing all pixels."""
        if self._bounds_cache is None:
            self._recompute_spatial_index()
        return self._bounds_cache or BoundingBox3D()

    def get_pixel_coordinates(self, fixture_id: str) -> list[Point3D]:
        """Get physical (X, Y, Z) coordinates for all pixels in a fixture."""
        if fixture_id not in self._coords_cache:
            f = self._fixtures.get(fixture_id)
            if not f:
                return []
            self._coords_cache[fixture_id] = f.get_pixel_coordinates()
        return self._coords_cache[fixture_id]

    def get_normalized_coordinates(self, fixture_id: str) -> list[Point3D]:
        """Get coordinates normalized to [0.0, 1.0]^3 space relative to the universe bounding box."""
        if self._bounds_cache is None:
            self._recompute_spatial_index()

        if fixture_id not in self._normalized_cache:
            raw_coords = self.get_pixel_coordinates(fixture_id)
            bbox = self.bounding_box
            self._normalized_cache[fixture_id] = [bbox.normalize(p) for p in raw_coords]

        return self._normalized_cache[fixture_id]

    def _invalidate_cache(self) -> None:
        self._bounds_cache = None
        self._coords_cache.clear()
        self._normalized_cache.clear()

    def _recompute_spatial_index(self) -> None:
        bbox = BoundingBox3D()
        for f in self._fixtures.values():
            coords = f.get_pixel_coordinates()
            self._coords_cache[f.id] = coords
            for p in coords:
                bbox.expand(p)

        # If empty or single point, give valid default width/height
        if not bbox.is_valid:
            bbox = BoundingBox3D(0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        self._bounds_cache = bbox

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "bounding_box": self.bounding_box.to_dict(),
            "total_pixels": self.total_pixels,
            "fixtures": [f.to_dict() for f in self._fixtures.values()],
        }

    def to_visualizer_dict(self) -> dict[str, Any]:
        """Produce enriched dictionary for Web Visualizer Canvas streaming."""
        offset = 0
        fixtures_meta = []
        for f in self._fixtures.values():
            d = f.to_dict()
            coords = self.get_pixel_coordinates(f.id)
            d["points"] = [[round(p.x, 3), round(p.y, 3), round(p.z, 3)] for p in coords]
            d["pixel_offset"] = offset
            fixtures_meta.append(d)
            offset += f.pixel_count

        return {
            "name": self.name,
            "bounding_box": self.bounding_box.to_dict(),
            "total_pixels": self.total_pixels,
            "groups": self.get_groups(),
            "fixtures": fixtures_meta,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpatialUniverse:
        uni = cls(name=data.get("name", "Default Universe"))
        for f_data in data.get("fixtures", []):
            fixture = Fixture.from_dict(f_data)
            uni.add_fixture(fixture)
        return uni

    def save_json(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: Path | str) -> SpatialUniverse:
        p = Path(path)
        with open(p, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
