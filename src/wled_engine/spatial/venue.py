"""Venue preset generator configuring a full 20-node multi-controller installation."""

from __future__ import annotations
from pathlib import Path

from wled_engine.patch.target import ColorOrder, OutputProtocol
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


def create_demo_venue() -> tuple[SpatialUniverse, PatchTable]:
    """Create a complete production-grade 20-controller venue universe with all fixture modalities.

    Includes:
    - 20 WLED controllers hardwired on Cat6 Ethernet (wled_01 .. wled_20)
    - Structural truss linear strips (Perimeter, Roof, Stage Arch)
    - Overhead hanging festoon bulb strings (Catenary gravitational curves)
    - 2D LED matrix panels (Stage backdrop & DJ booth facade)
    - Floor accent lamps (Point lamps)
    - Projector viewport (Stage backdrop mapping)
    """
    universe = SpatialUniverse(name="Metro Concert Hall & Lounge")
    patch = PatchTable(name="Cat6 20-Node Production Patch")

    # =========================================================================
    # 1. Structural Truss Strips (Controllers 01 - 03)
    # =========================================================================
    # Front Roof Overhead Truss (600 LEDs split across wled_01 Ch0 & Ch1)
    f_roof = LinearStripFixture(
        fixture_id="truss_roof_front",
        name="Front Stage Truss Span",
        pixel_count=600,
        waypoints=[Point3D(-6.0, 4.0, 4.0), Point3D(6.0, 4.0, 4.0)],
        group="trusses",
        tags=["stage", "overhead", "front"],
    )
    universe.add_fixture(f_roof)
    patch.patch_segment("truss_roof_front", pixel_start=0, pixel_count=300, controller_id="wled_01", channel_index=0)
    patch.patch_segment("truss_roof_front", pixel_start=300, pixel_count=300, controller_id="wled_01", channel_index=1)

    # Front Truss Vertical Legs
    leg_left = LinearStripFixture(
        fixture_id="truss_leg_front_left",
        name="Front Left Truss Upright",
        pixel_count=200,
        waypoints=[Point3D(-6.0, 4.0, 4.0), Point3D(-6.0, 4.0, 0.0)],
        group="trusses",
        tags=["stage", "upright", "left"],
    )
    universe.add_fixture(leg_left)
    patch.patch_fixture("truss_leg_front_left", 200, controller_id="wled_01", channel_index=2)

    leg_right = LinearStripFixture(
        fixture_id="truss_leg_front_right",
        name="Front Right Truss Upright",
        pixel_count=200,
        waypoints=[Point3D(6.0, 4.0, 4.0), Point3D(6.0, 4.0, 0.0)],
        group="trusses",
        tags=["stage", "upright", "right"],
    )
    universe.add_fixture(leg_right)
    patch.patch_fixture("truss_leg_front_right", 200, controller_id="wled_02", channel_index=0)

    # Rear Stage Overhead Truss & Legs (wled_02 & wled_03)
    rear_roof = LinearStripFixture(
        fixture_id="truss_roof_rear",
        name="Rear Stage Truss Span",
        pixel_count=500,
        waypoints=[Point3D(-5.0, 7.0, 4.5), Point3D(5.0, 7.0, 4.5)],
        group="trusses",
        tags=["stage", "overhead", "rear"],
    )
    universe.add_fixture(rear_roof)
    patch.patch_segment("truss_roof_rear", pixel_start=0, pixel_count=250, controller_id="wled_02", channel_index=1)
    patch.patch_segment("truss_roof_rear", pixel_start=250, pixel_count=250, controller_id="wled_02", channel_index=2)

    rear_leg_l = LinearStripFixture(
        fixture_id="truss_leg_rear_left",
        name="Rear Left Truss Upright",
        pixel_count=200,
        waypoints=[Point3D(-5.0, 7.0, 4.5), Point3D(-5.0, 7.0, 0.0)],
        group="trusses",
        tags=["stage", "upright", "rear"],
    )
    universe.add_fixture(rear_leg_l)
    patch.patch_fixture("truss_leg_rear_left", 200, controller_id="wled_03", channel_index=0)

    rear_leg_r = LinearStripFixture(
        fixture_id="truss_leg_rear_right",
        name="Rear Right Truss Upright",
        pixel_count=200,
        waypoints=[Point3D(5.0, 7.0, 4.5), Point3D(5.0, 7.0, 0.0)],
        group="trusses",
        tags=["stage", "upright", "rear"],
    )
    universe.add_fixture(rear_leg_r)
    patch.patch_fixture("truss_leg_rear_right", 200, controller_id="wled_03", channel_index=1)

    # =========================================================================
    # 2. Overhead Festoon Bulb Strings with Catenary Sag (Controllers 04 - 05)
    # =========================================================================
    bulb_1 = BulbStringFixture(
        fixture_id="bulb_canopy_left",
        name="Canopy Festoon Left Diagonal",
        bulb_count=36,
        start=Point3D(-6.0, 3.5, 3.8),
        end=Point3D(0.0, -4.0, 3.2),
        sag=0.6,
        sag_axis="z",
        group="festoon",
        tags=["overhead", "canopy", "warm"],
    )
    universe.add_fixture(bulb_1)
    patch.patch_fixture("bulb_canopy_left", 36, controller_id="wled_04", channel_index=0)

    bulb_2 = BulbStringFixture(
        fixture_id="bulb_canopy_right",
        name="Canopy Festoon Right Diagonal",
        bulb_count=36,
        start=Point3D(6.0, 3.5, 3.8),
        end=Point3D(0.0, -4.0, 3.2),
        sag=0.6,
        sag_axis="z",
        group="festoon",
        tags=["overhead", "canopy", "warm"],
    )
    universe.add_fixture(bulb_2)
    patch.patch_fixture("bulb_canopy_right", 36, controller_id="wled_04", channel_index=1)

    bulb_3 = BulbStringFixture(
        fixture_id="bulb_canopy_cross",
        name="Canopy Festoon Cross Transverse",
        bulb_count=48,
        start=Point3D(-5.5, 0.0, 3.6),
        end=Point3D(5.5, 0.0, 3.6),
        sag=0.75,
        sag_axis="z",
        group="festoon",
        tags=["overhead", "canopy", "warm"],
    )
    universe.add_fixture(bulb_3)
    patch.patch_fixture("bulb_canopy_cross", 48, controller_id="wled_04", channel_index=2)

    bulb_4 = BulbStringFixture(
        fixture_id="bulb_lounge_swag",
        name="Lounge Rear Swag Line",
        bulb_count=40,
        start=Point3D(-4.0, -6.0, 3.0),
        end=Point3D(4.0, -6.0, 3.0),
        sag=0.5,
        sag_axis="z",
        group="festoon",
        tags=["overhead", "lounge", "warm"],
    )
    universe.add_fixture(bulb_4)
    patch.patch_fixture("bulb_lounge_swag", 40, controller_id="wled_05", channel_index=0)

    # =========================================================================
    # 3. 2D LED Matrix Panels (Controllers 06 - 07)
    # =========================================================================
    # Stage Backdrop Left (16x16)
    matrix_stage_l = MatrixFixture(
        fixture_id="matrix_stage_left",
        name="Stage Left Matrix Wall",
        rows=16,
        cols=16,
        origin=Point3D(-2.8, 6.8, 1.2),
        width=1.92,
        height=1.92,
        serpentine=True,
        group="panels",
        tags=["stage", "matrix", "left"],
    )
    universe.add_fixture(matrix_stage_l)
    patch.patch_fixture("matrix_stage_left", 256, controller_id="wled_06", channel_index=0)

    # Stage Backdrop Right (16x16)
    matrix_stage_r = MatrixFixture(
        fixture_id="matrix_stage_right",
        name="Stage Right Matrix Wall",
        rows=16,
        cols=16,
        origin=Point3D(0.9, 6.8, 1.2),
        width=1.92,
        height=1.92,
        serpentine=True,
        group="panels",
        tags=["stage", "matrix", "right"],
    )
    universe.add_fixture(matrix_stage_r)
    patch.patch_fixture("matrix_stage_right", 256, controller_id="wled_06", channel_index=1)

    # DJ Booth Facade (8 rows, 32 cols)
    matrix_dj = MatrixFixture(
        fixture_id="matrix_dj_facade",
        name="DJ Booth Front Matrix",
        rows=8,
        cols=32,
        origin=Point3D(-1.6, 3.0, 0.2),
        width=3.2,
        height=0.8,
        serpentine=True,
        group="panels",
        tags=["stage", "dj", "facade"],
    )
    universe.add_fixture(matrix_dj)
    patch.patch_fixture("matrix_dj_facade", 256, controller_id="wled_07", channel_index=0)

    # =========================================================================
    # 4. Floor Accent Point Lamps (Controller 08)
    # =========================================================================
    lamp_1 = PointFixture(
        fixture_id="lamp_stage_fl_l",
        name="Stage Front Left Lamp",
        location=Point3D(-4.5, 3.5, 0.0),
        pixel_count=1,
        radius=0.45,
        group="lamps",
        tags=["floor", "stage", "accent"],
    )
    universe.add_fixture(lamp_1)
    patch.patch_fixture("lamp_stage_fl_l", 1, controller_id="wled_08", channel_index=0, port_offset=0)

    lamp_2 = PointFixture(
        fixture_id="lamp_stage_fl_r",
        name="Stage Front Right Lamp",
        location=Point3D(4.5, 3.5, 0.0),
        pixel_count=1,
        radius=0.45,
        group="lamps",
        tags=["floor", "stage", "accent"],
    )
    universe.add_fixture(lamp_2)
    patch.patch_fixture("lamp_stage_fl_r", 1, controller_id="wled_08", channel_index=0, port_offset=1)

    lamp_3 = PointFixture(
        fixture_id="lamp_lounge_l",
        name="Lounge Left Accent Lamp",
        location=Point3D(-3.5, -4.5, 0.0),
        pixel_count=1,
        radius=0.5,
        group="lamps",
        tags=["floor", "lounge", "accent"],
    )
    universe.add_fixture(lamp_3)
    patch.patch_fixture("lamp_lounge_l", 1, controller_id="wled_08", channel_index=1, port_offset=0)

    lamp_4 = PointFixture(
        fixture_id="lamp_lounge_r",
        name="Lounge Right Accent Lamp",
        location=Point3D(3.5, -4.5, 0.0),
        pixel_count=1,
        radius=0.5,
        group="lamps",
        tags=["floor", "lounge", "accent"],
    )
    universe.add_fixture(lamp_4)
    patch.patch_fixture("lamp_lounge_r", 1, controller_id="wled_08", channel_index=1, port_offset=1)

    # =========================================================================
    # 5. Projector Viewport (Virtual Raster Output)
    # =========================================================================
    proj = ProjectorViewport(
        fixture_id="projector_stage_canvas",
        name="Main Stage Projector Viewport",
        top_left=Point3D(-2.4, 6.9, 3.8),
        bottom_right=Point3D(2.4, 6.9, 1.1),
        resolution_x=1920,
        resolution_y=1080,
        group="projectors",
        tags=["video", "stage", "screen"],
    )
    universe.add_fixture(proj)

    # =========================================================================
    # 6. Additional Architecture, Perimeter & Room Lighting (Controllers 09 - 20)
    # =========================================================================
    # Perimeter Run Left Wall (split across wled_09 & wled_10)
    wall_left = LinearStripFixture(
        fixture_id="strip_wall_left",
        name="Auditorium Left Wall Baseboard",
        pixel_count=450,
        waypoints=[Point3D(-6.5, 4.0, 0.1), Point3D(-6.5, -6.5, 0.1)],
        group="perimeter",
        tags=["wall", "left", "baseboard"],
    )
    universe.add_fixture(wall_left)
    patch.patch_segment("strip_wall_left", pixel_start=0, pixel_count=225, controller_id="wled_09", channel_index=0)
    patch.patch_segment("strip_wall_left", pixel_start=225, pixel_count=225, controller_id="wled_10", channel_index=0)

    # Perimeter Run Right Wall (split across wled_11 & wled_12)
    wall_right = LinearStripFixture(
        fixture_id="strip_wall_right",
        name="Auditorium Right Wall Baseboard",
        pixel_count=450,
        waypoints=[Point3D(6.5, 4.0, 0.1), Point3D(6.5, -6.5, 0.1)],
        group="perimeter",
        tags=["wall", "right", "baseboard"],
    )
    universe.add_fixture(wall_right)
    patch.patch_segment("strip_wall_right", pixel_start=0, pixel_count=225, controller_id="wled_11", channel_index=0)
    patch.patch_segment("strip_wall_right", pixel_start=225, pixel_count=225, controller_id="wled_12", channel_index=0)

    # Stage Lip Under-Glow (wled_13)
    stage_lip = LinearStripFixture(
        fixture_id="strip_stage_lip",
        name="Stage Front Lip Under-Glow",
        pixel_count=240,
        waypoints=[Point3D(-4.0, 2.8, 0.05), Point3D(4.0, 2.8, 0.05)],
        group="stage",
        tags=["stage", "lip", "edge"],
    )
    universe.add_fixture(stage_lip)
    patch.patch_fixture("strip_stage_lip", 240, controller_id="wled_13", channel_index=0)

    # Bar Counter Glow & Shelving (Controllers 14 - 16)
    bar_top = LinearStripFixture(
        fixture_id="strip_bar_counter",
        name="Bar Counter Edge Glow",
        pixel_count=180,
        waypoints=[Point3D(-5.5, -5.0, 1.1), Point3D(-1.5, -5.0, 1.1)],
        group="bar",
        tags=["bar", "counter"],
    )
    universe.add_fixture(bar_top)
    patch.patch_fixture("strip_bar_counter", 180, controller_id="wled_14", channel_index=0)

    bar_under = LinearStripFixture(
        fixture_id="strip_bar_kickplate",
        name="Bar Kickplate Under-Lighting",
        pixel_count=180,
        waypoints=[Point3D(-5.5, -5.0, 0.05), Point3D(-1.5, -5.0, 0.05)],
        group="bar",
        tags=["bar", "kickplate"],
    )
    universe.add_fixture(bar_under)
    patch.patch_fixture("strip_bar_kickplate", 180, controller_id="wled_15", channel_index=0)

    bar_bottles = LinearStripFixture(
        fixture_id="strip_bar_shelf",
        name="Bar Liquor Display Shelf Backlight",
        pixel_count=180,
        waypoints=[Point3D(-5.5, -6.0, 1.8), Point3D(-1.5, -6.0, 1.8)],
        group="bar",
        tags=["bar", "bottles", "accent"],
    )
    universe.add_fixture(bar_bottles)
    patch.patch_fixture("strip_bar_shelf", 180, controller_id="wled_16", channel_index=0)

    # Acoustic Cloud Ceiling Floats (Controllers 17 - 20)
    for idx, (cid, x_pos, y_pos) in enumerate([
        ("wled_17", -3.0, 1.0),
        ("wled_18", 3.0, 1.0),
        ("wled_19", -2.5, -2.5),
        ("wled_20", 2.5, -2.5),
    ], start=1):
        cloud = LinearStripFixture(
            fixture_id=f"strip_ceiling_cloud_{idx}",
            name=f"Ceiling Float Panel {idx} Halo",
            pixel_count=160,
            waypoints=[
                Point3D(x_pos - 1.0, y_pos - 1.0, 3.4),
                Point3D(x_pos + 1.0, y_pos - 1.0, 3.4),
                Point3D(x_pos + 1.0, y_pos + 1.0, 3.4),
                Point3D(x_pos - 1.0, y_pos + 1.0, 3.4),
                Point3D(x_pos - 1.0, y_pos - 1.0, 3.4),
            ],
            group="ceiling",
            tags=["ceiling", "halo", "overhead"],
        )
        universe.add_fixture(cloud)
        patch.patch_fixture(f"strip_ceiling_cloud_{idx}", 160, controller_id=cid, channel_index=0)

    return universe, patch


def save_default_venue_files(dest_dir: str | Path = "data/venue") -> tuple[Path, Path]:
    """Generate and save the default 20-node venue universe and patch files."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    universe, patch = create_demo_venue()

    uni_path = dest / "universe.json"
    patch_path = dest / "patch.json"

    universe.save_json(uni_path)
    patch.save_json(patch_path)

    return uni_path, patch_path
