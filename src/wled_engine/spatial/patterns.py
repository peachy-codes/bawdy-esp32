"""Spatial pattern generators evaluating 2D and 3D visual fields over space and time."""

from __future__ import annotations
import math
from typing import Callable

from wled_app.domain.color import Color
from wled_engine.spatial.coordinates import Point3D


def spatial_angle_sweep(
    angle_deg: float = 0.0,
    speed: float = 1.0,
    time_sec: float = 0.0,
    frequency: float = 2.0,
    color_a: Color = Color(255, 0, 128),
    color_b: Color = Color(0, 200, 255),
) -> Callable[[Point3D], Color]:
    """Create a continuous directional color wave sweeping at angle_deg across space."""
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    def evaluate(p: Point3D) -> Color:
        # Project normalized point along the directional unit vector
        proj = p.x * cos_a + p.y * sin_a
        # Sine wave phase
        phase = (proj * frequency * 2.0 * math.pi) - (time_sec * speed * 2.0 * math.pi)
        # Remap [-1, 1] to [0, 1]
        t = (math.sin(phase) + 1.0) / 2.0
        return color_a.lerp(color_b, t)

    return evaluate


def spatial_radial_pulse(
    center: Point3D = Point3D(0.5, 0.5, 0.0),
    speed: float = 1.0,
    time_sec: float = 0.0,
    frequency: float = 3.0,
    color_center: Color = Color(255, 220, 50),
    color_edge: Color = Color(10, 20, 80),
) -> Callable[[Point3D], Color]:
    """Create a concentric circular or spherical pulse expanding from center."""
    def evaluate(p: Point3D) -> Color:
        dist = center.distance_to(p)
        phase = (dist * frequency * 2.0 * math.pi) - (time_sec * speed * 2.0 * math.pi)
        t = (math.sin(phase) + 1.0) / 2.0
        return color_center.lerp(color_edge, t)

    return evaluate


def spatial_linear_gradient(
    start: Point3D = Point3D(0.0, 0.0, 0.0),
    end: Point3D = Point3D(1.0, 1.0, 0.0),
    color_start: Color = Color(255, 60, 0),
    color_end: Color = Color(120, 0, 255),
) -> Callable[[Point3D], Color]:
    """Create a static or offset linear gradient between two points in space."""
    dx = end.x - start.x
    dy = end.y - start.y
    dz = end.z - start.z
    length_sq = dx * dx + dy * dy + dz * dz

    def evaluate(p: Point3D) -> Color:
        if length_sq < 1e-6:
            return color_start
        # Project vector (p - start) onto (end - start)
        dot = (p.x - start.x) * dx + (p.y - start.y) * dy + (p.z - start.z) * dz
        t = max(0.0, min(1.0, dot / length_sq))
        return color_start.lerp(color_end, t)

    return evaluate


def spatial_rainbow_cloud(
    time_sec: float = 0.0,
    speed: float = 0.5,
    scale: float = 2.0,
) -> Callable[[Point3D], Color]:
    """Procedural multi-frequency color cloud drifting through coordinate space."""
    offset = time_sec * speed

    def evaluate(p: Point3D) -> Color:
        # Pseudo-noise hash combination
        h1 = math.sin(p.x * scale * math.pi + offset)
        h2 = math.cos(p.y * scale * math.pi - offset * 0.7)
        h3 = math.sin((p.x + p.y + p.z) * scale * 1.5 + offset * 1.2)
        combined_hue = ((h1 + h2 + h3) / 3.0 + 1.0) / 2.0
        return Color.from_hsv(combined_hue, 1.0, 1.0)

    return evaluate
