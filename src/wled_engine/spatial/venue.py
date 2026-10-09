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


def create_concert_hall_venue() -> tuple[SpatialUniverse, PatchTable]:
    """Alias for flagship 20-node Metro Concert Hall & Lounge installation."""
    return create_demo_venue()


def create_warehouse_rave_venue() -> tuple[SpatialUniverse, PatchTable]:
    """Create an industrial underground rave venue with 360-deg central DJ cage and perimeter battens.

    Includes:
    - 16 WLED controllers on Cat6 Ethernet (wled_01 .. wled_16)
    - 4x4m Central DJ square cage (overhead horizontal truss beams & vertical pylons)
    - 4 Corner Strobe Blinders on cage uprights
    - Dual 16x16 Heavy Industrial Wall Video Matrices
    - 4 Vertical Ground Dancefloor Totems
    - 4 Warehouse Perimeter Wall Battens
    - Ceiling diagonal cross-beams and center halo ring
    - DJ booth holographic projector viewport
    """
    universe = SpatialUniverse(name="Warehouse Rave & Boiler Stage")
    patch = PatchTable(name="Warehouse 16-Node DDP Patch")

    # 1. Central 360 DJ Truss Cage (Controllers 01 - 04)
    # Roof horizontal beams
    universe.add_fixture(LinearStripFixture(
        fixture_id="cage_roof_north",
        name="DJ Cage North Roof Beam",
        pixel_count=200,
        waypoints=[Point3D(-2.0, 2.0, 3.8), Point3D(2.0, 2.0, 3.8)],
        group="dj_cage",
        tags=["cage", "roof", "north"],
    ))
    patch.patch_fixture("cage_roof_north", 200, controller_id="wled_01", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="cage_roof_south",
        name="DJ Cage South Roof Beam",
        pixel_count=200,
        waypoints=[Point3D(-2.0, -2.0, 3.8), Point3D(2.0, -2.0, 3.8)],
        group="dj_cage",
        tags=["cage", "roof", "south"],
    ))
    patch.patch_fixture("cage_roof_south", 200, controller_id="wled_01", channel_index=1)

    universe.add_fixture(LinearStripFixture(
        fixture_id="cage_roof_west",
        name="DJ Cage West Roof Beam",
        pixel_count=200,
        waypoints=[Point3D(-2.0, -2.0, 3.8), Point3D(-2.0, 2.0, 3.8)],
        group="dj_cage",
        tags=["cage", "roof", "west"],
    ))
    patch.patch_fixture("cage_roof_west", 200, controller_id="wled_02", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="cage_roof_east",
        name="DJ Cage East Roof Beam",
        pixel_count=200,
        waypoints=[Point3D(2.0, -2.0, 3.8), Point3D(2.0, 2.0, 3.8)],
        group="dj_cage",
        tags=["cage", "roof", "east"],
    ))
    patch.patch_fixture("cage_roof_east", 200, controller_id="wled_02", channel_index=1)

    # Vertical corner pylons
    universe.add_fixture(LinearStripFixture(
        fixture_id="cage_pylon_nw",
        name="DJ Cage NW Corner Pylon",
        pixel_count=150,
        waypoints=[Point3D(-2.0, 2.0, 3.8), Point3D(-2.0, 2.0, 0.0)],
        group="dj_cage",
        tags=["cage", "upright", "nw"],
    ))
    patch.patch_fixture("cage_pylon_nw", 150, controller_id="wled_03", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="cage_pylon_ne",
        name="DJ Cage NE Corner Pylon",
        pixel_count=150,
        waypoints=[Point3D(2.0, 2.0, 3.8), Point3D(2.0, 2.0, 0.0)],
        group="dj_cage",
        tags=["cage", "upright", "ne"],
    ))
    patch.patch_fixture("cage_pylon_ne", 150, controller_id="wled_03", channel_index=1)

    universe.add_fixture(LinearStripFixture(
        fixture_id="cage_pylon_sw",
        name="DJ Cage SW Corner Pylon",
        pixel_count=150,
        waypoints=[Point3D(-2.0, -2.0, 3.8), Point3D(-2.0, -2.0, 0.0)],
        group="dj_cage",
        tags=["cage", "upright", "sw"],
    ))
    patch.patch_fixture("cage_pylon_sw", 150, controller_id="wled_04", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="cage_pylon_se",
        name="DJ Cage SE Corner Pylon",
        pixel_count=150,
        waypoints=[Point3D(2.0, -2.0, 3.8), Point3D(2.0, -2.0, 0.0)],
        group="dj_cage",
        tags=["cage", "upright", "se"],
    ))
    patch.patch_fixture("cage_pylon_se", 150, controller_id="wled_04", channel_index=1)

    # 2. Corner Strobe Blinders on Cage Upright Tops (Controller 05)
    universe.add_fixture(PointFixture("strobe_cage_nw", "NW Cage Strobe Blinder", Point3D(-2.0, 2.0, 4.0), radius=0.4, group="strobes", tags=["strobe", "blinder"]))
    patch.patch_fixture("strobe_cage_nw", 1, controller_id="wled_05", channel_index=0, port_offset=0)

    universe.add_fixture(PointFixture("strobe_cage_ne", "NE Cage Strobe Blinder", Point3D(2.0, 2.0, 4.0), radius=0.4, group="strobes", tags=["strobe", "blinder"]))
    patch.patch_fixture("strobe_cage_ne", 1, controller_id="wled_05", channel_index=0, port_offset=1)

    universe.add_fixture(PointFixture("strobe_cage_sw", "SW Cage Strobe Blinder", Point3D(-2.0, -2.0, 4.0), radius=0.4, group="strobes", tags=["strobe", "blinder"]))
    patch.patch_fixture("strobe_cage_sw", 1, controller_id="wled_05", channel_index=1, port_offset=0)

    universe.add_fixture(PointFixture("strobe_cage_se", "SE Cage Strobe Blinder", Point3D(2.0, -2.0, 4.0), radius=0.4, group="strobes", tags=["strobe", "blinder"]))
    patch.patch_fixture("strobe_cage_se", 1, controller_id="wled_05", channel_index=1, port_offset=1)

    # 3. Dual 16x16 Industrial Wall Video Matrices (Controllers 06 - 07)
    universe.add_fixture(MatrixFixture(
        fixture_id="matrix_north_wall",
        name="North Wall Video Matrix (16x16)",
        rows=16,
        cols=16,
        origin=Point3D(-1.0, 6.5, 1.5),
        width=2.0,
        height=2.0,
        group="matrices",
        tags=["matrix", "wall", "north"],
    ))
    patch.patch_fixture("matrix_north_wall", 256, controller_id="wled_06", channel_index=0)

    universe.add_fixture(MatrixFixture(
        fixture_id="matrix_south_wall",
        name="South Wall Video Matrix (16x16)",
        rows=16,
        cols=16,
        origin=Point3D(-1.0, -6.5, 1.5),
        width=2.0,
        height=2.0,
        group="matrices",
        tags=["matrix", "wall", "south"],
    ))
    patch.patch_fixture("matrix_south_wall", 256, controller_id="wled_07", channel_index=0)

    # 4. Dancefloor Corner Totems (Controllers 08 - 09)
    for idx, (fid, fname, ch_info, (x, y)) in enumerate([
        ("totem_dancefloor_fl", "Front Left Dancefloor Totem", ("wled_08", 0), (-4.5, 4.0)),
        ("totem_dancefloor_fr", "Front Right Dancefloor Totem", ("wled_08", 1), (4.5, 4.0)),
        ("totem_dancefloor_rl", "Rear Left Dancefloor Totem", ("wled_09", 0), (-4.5, -4.0)),
        ("totem_dancefloor_rr", "Rear Right Dancefloor Totem", ("wled_09", 1), (4.5, -4.0)),
    ]):
        universe.add_fixture(LinearStripFixture(
            fixture_id=fid,
            name=fname,
            pixel_count=160,
            waypoints=[Point3D(x, y, 3.2), Point3D(x, y, 0.0)],
            group="totems",
            tags=["totem", "column"],
        ))
        patch.patch_fixture(fid, 160, controller_id=ch_info[0], channel_index=ch_info[1])

    # 5. Perimeter Wall Battens (Controllers 10 - 13)
    wall_configs = [
        ("batten_wall_north", "North Wall Pixel Batten", "wled_10", [Point3D(-6.5, 6.8, 0.2), Point3D(6.5, 6.8, 0.2)]),
        ("batten_wall_south", "South Wall Pixel Batten", "wled_11", [Point3D(-6.5, -6.8, 0.2), Point3D(6.5, -6.8, 0.2)]),
        ("batten_wall_west", "West Wall Pixel Batten", "wled_12", [Point3D(-6.8, -6.5, 0.2), Point3D(-6.8, 6.5, 0.2)]),
        ("batten_wall_east", "East Wall Pixel Batten", "wled_13", [Point3D(6.8, -6.5, 0.2), Point3D(6.8, 6.5, 0.2)]),
    ]
    for fid, fname, cid, pts in wall_configs:
        universe.add_fixture(LinearStripFixture(
            fixture_id=fid,
            name=fname,
            pixel_count=240,
            waypoints=pts,
            group="perimeter",
            tags=["wall", "batten"],
        ))
        patch.patch_fixture(fid, 240, controller_id=cid, channel_index=0)

    # 6. Overhead Diagonal Beams & Center Halo (Controllers 14 - 16)
    universe.add_fixture(LinearStripFixture(
        fixture_id="beam_cross_diag_1",
        name="Overhead Cross Truss Beam A",
        pixel_count=220,
        waypoints=[Point3D(-6.0, -6.0, 4.5), Point3D(6.0, 6.0, 4.5)],
        group="overhead_beams",
        tags=["beam", "overhead"],
    ))
    patch.patch_fixture("beam_cross_diag_1", 220, controller_id="wled_14", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="beam_cross_diag_2",
        name="Overhead Cross Truss Beam B",
        pixel_count=220,
        waypoints=[Point3D(-6.0, 6.0, 4.5), Point3D(6.0, -6.0, 4.5)],
        group="overhead_beams",
        tags=["beam", "overhead"],
    ))
    patch.patch_fixture("beam_cross_diag_2", 220, controller_id="wled_15", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="center_halo_ring",
        name="Center DJ Overhead Square Halo",
        pixel_count=240,
        waypoints=[
            Point3D(-1.5, -1.5, 4.2), Point3D(1.5, -1.5, 4.2),
            Point3D(1.5, 1.5, 4.2), Point3D(-1.5, 1.5, 4.2), Point3D(-1.5, -1.5, 4.2),
        ],
        group="overhead_beams",
        tags=["halo", "center"],
    ))
    patch.patch_fixture("center_halo_ring", 240, controller_id="wled_16", channel_index=0)

    # 7. Virtual Projector Viewport
    universe.add_fixture(ProjectorViewport(
        fixture_id="projector_hologram_booth",
        name="DJ Hologram Projection Field",
        top_left=Point3D(-1.8, 2.0, 3.5),
        bottom_right=Point3D(1.8, -2.0, 0.5),
        group="projectors",
    ))

    return universe, patch


def create_festival_amphitheater_venue() -> tuple[SpatialUniverse, PatchTable]:
    """Create an expansive outdoor festival amphitheater venue with proscenium arch and lawn festoon canopy.

    Includes:
    - 16 WLED controllers on Cat6 Ethernet (wled_01 .. wled_16)
    - Monumental curved proscenium stage arch & wing headers
    - 6 Swooping overhead festoon bulb strings extending into the lawn
    - Catwalk center runway and downstage lip underglow
    - Dual side 16x16 IMAG video screens
    - 4 Delay speaker towers with vertical pixel columns
    - Front-of-House sound booth perimeter & VIP garden lights
    - Festival mainstage backdrop projector viewport
    """
    universe = SpatialUniverse(name="Outdoor Amphitheater & Lawn")
    patch = PatchTable(name="Festival Amphitheater 16-Node Patch")

    # 1. Proscenium Arch & Wings (Controllers 01 - 03)
    universe.add_fixture(LinearStripFixture(
        fixture_id="arch_proscenium_outer",
        name="Grand Proscenium Outer Arch",
        pixel_count=450,
        waypoints=[
            Point3D(-7.0, 6.0, 0.0), Point3D(-5.5, 6.0, 5.5),
            Point3D(0.0, 6.0, 6.2), Point3D(5.5, 6.0, 5.5), Point3D(7.0, 6.0, 0.0),
        ],
        group="proscenium",
        tags=["arch", "stage"],
    ))
    patch.patch_segment("arch_proscenium_outer", pixel_start=0, pixel_count=225, controller_id="wled_01", channel_index=0)
    patch.patch_segment("arch_proscenium_outer", pixel_start=225, pixel_count=225, controller_id="wled_01", channel_index=1)

    universe.add_fixture(LinearStripFixture(
        fixture_id="arch_proscenium_inner",
        name="Grand Proscenium Inner Arch",
        pixel_count=360,
        waypoints=[
            Point3D(-5.0, 6.5, 0.0), Point3D(-3.5, 6.5, 4.5),
            Point3D(0.0, 6.5, 5.0), Point3D(3.5, 6.5, 4.5), Point3D(5.0, 6.5, 0.0),
        ],
        group="proscenium",
        tags=["arch", "stage"],
    ))
    patch.patch_segment("arch_proscenium_inner", pixel_start=0, pixel_count=180, controller_id="wled_02", channel_index=0)
    patch.patch_segment("arch_proscenium_inner", pixel_start=180, pixel_count=180, controller_id="wled_02", channel_index=1)

    universe.add_fixture(LinearStripFixture(
        fixture_id="arch_wing_left",
        name="Stage Left Truss Wing Header",
        pixel_count=200,
        waypoints=[Point3D(-7.0, 6.0, 0.0), Point3D(-9.0, 4.5, 0.0)],
        group="proscenium",
        tags=["wing", "stage"],
    ))
    patch.patch_fixture("arch_wing_left", 200, controller_id="wled_03", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="arch_wing_right",
        name="Stage Right Truss Wing Header",
        pixel_count=200,
        waypoints=[Point3D(7.0, 6.0, 0.0), Point3D(9.0, 4.5, 0.0)],
        group="proscenium",
        tags=["wing", "stage"],
    ))
    patch.patch_fixture("arch_wing_right", 200, controller_id="wled_03", channel_index=1)

    # 2. Swooping Overhead Festoon Strings (Controllers 04 - 06)
    festoon_specs = [
        ("festoon_swoop_1", "Amphitheater Festoon Swag 1", 48, Point3D(-6.0, 5.5, 5.0), Point3D(-6.5, -4.0, 3.2), "wled_04", 0),
        ("festoon_swoop_2", "Amphitheater Festoon Swag 2", 48, Point3D(-3.5, 5.8, 5.4), Point3D(-3.0, -4.5, 3.2), "wled_04", 1),
        ("festoon_swoop_3", "Amphitheater Festoon Swag 3 (Center L)", 54, Point3D(-1.0, 6.0, 5.6), Point3D(0.0, -5.0, 3.2), "wled_05", 0),
        ("festoon_swoop_4", "Amphitheater Festoon Swag 4 (Center R)", 54, Point3D(1.0, 6.0, 5.6), Point3D(0.0, -5.0, 3.2), "wled_05", 1),
        ("festoon_swoop_5", "Amphitheater Festoon Swag 5", 48, Point3D(3.5, 5.8, 5.4), Point3D(3.0, -4.5, 3.2), "wled_06", 0),
        ("festoon_swoop_6", "Amphitheater Festoon Swag 6", 48, Point3D(6.0, 5.5, 5.0), Point3D(6.5, -4.0, 3.2), "wled_06", 1),
    ]
    for fid, fname, bcount, p1, p2, cid, ch in festoon_specs:
        universe.add_fixture(BulbStringFixture(
            fixture_id=fid,
            name=fname,
            bulb_count=bcount,
            start=p1,
            end=p2,
            sag=0.85,
            sag_axis="z",
            group="canopy",
            tags=["festoon", "canopy"],
        ))
        patch.patch_fixture(fid, bcount, controller_id=cid, channel_index=ch)

    # 3. Stage Catwalk Runway & Lip (Controller 07)
    universe.add_fixture(LinearStripFixture(
        fixture_id="catwalk_runway",
        name="Center Catwalk Runway Strip",
        pixel_count=250,
        waypoints=[Point3D(0.0, 5.5, 0.4), Point3D(0.0, 1.0, 0.4)],
        group="stage_deck",
        tags=["catwalk", "runway"],
    ))
    patch.patch_fixture("catwalk_runway", 250, controller_id="wled_07", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="stage_deck_lip",
        name="Amphitheater Stage Front Lip",
        pixel_count=250,
        waypoints=[Point3D(-4.5, 5.5, 0.2), Point3D(4.5, 5.5, 0.2)],
        group="stage_deck",
        tags=["stage", "lip"],
    ))
    patch.patch_fixture("stage_deck_lip", 250, controller_id="wled_07", channel_index=1)

    # 4. Dual Side IMAG Matrix Screens (Controllers 08 - 09)
    universe.add_fixture(MatrixFixture(
        fixture_id="matrix_imag_left",
        name="Left IMAG Video Wall (16x16)",
        rows=16,
        cols=16,
        origin=Point3D(-8.0, 5.5, 1.8),
        width=2.4,
        height=2.4,
        group="imag_screens",
        tags=["matrix", "imag", "left"],
    ))
    patch.patch_fixture("matrix_imag_left", 256, controller_id="wled_08", channel_index=0)

    universe.add_fixture(MatrixFixture(
        fixture_id="matrix_imag_right",
        name="Right IMAG Video Wall (16x16)",
        rows=16,
        cols=16,
        origin=Point3D(5.6, 5.5, 1.8),
        width=2.4,
        height=2.4,
        group="imag_screens",
        tags=["matrix", "imag", "right"],
    ))
    patch.patch_fixture("matrix_imag_right", 256, controller_id="wled_09", channel_index=0)

    # 5. Delay Sound Towers (Controllers 10 - 13)
    towers = [
        ("delay_tower_fl", "Delay Tower 1 (Front Left)", "wled_10", (-5.0, -0.5)),
        ("delay_tower_fr", "Delay Tower 2 (Front Right)", "wled_11", (5.0, -0.5)),
        ("delay_tower_rl", "Delay Tower 3 (Rear Left)", "wled_12", (-6.0, -5.5)),
        ("delay_tower_rr", "Delay Tower 4 (Rear Right)", "wled_13", (6.0, -5.5)),
    ]
    for fid, fname, cid, (x, y) in towers:
        universe.add_fixture(LinearStripFixture(
            fixture_id=fid,
            name=fname,
            pixel_count=180,
            waypoints=[Point3D(x, y, 4.0), Point3D(x, y, 0.0)],
            group="delay_towers",
            tags=["tower", "delay"],
        ))
        patch.patch_fixture(fid, 180, controller_id=cid, channel_index=0)

    # 6. Front-of-House Booth & VIP Garden (Controllers 14 - 16)
    universe.add_fixture(LinearStripFixture(
        fixture_id="strip_foh_booth",
        name="FOH Mixing Booth Surround",
        pixel_count=200,
        waypoints=[
            Point3D(-2.0, -6.5, 1.0), Point3D(2.0, -6.5, 1.0),
            Point3D(2.0, -7.5, 1.0), Point3D(-2.0, -7.5, 1.0), Point3D(-2.0, -6.5, 1.0),
        ],
        group="foh_booth",
        tags=["foh", "booth"],
    ))
    patch.patch_fixture("strip_foh_booth", 200, controller_id="wled_14", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="strip_vip_lounge_l",
        name="VIP Garden Left Boundary Strip",
        pixel_count=180,
        waypoints=[Point3D(-8.5, 2.0, 0.1), Point3D(-8.5, -4.0, 0.1)],
        group="vip_garden",
        tags=["vip", "garden"],
    ))
    patch.patch_fixture("strip_vip_lounge_l", 180, controller_id="wled_15", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="strip_vip_lounge_r",
        name="VIP Garden Right Boundary Strip",
        pixel_count=180,
        waypoints=[Point3D(8.5, 2.0, 0.1), Point3D(8.5, -4.0, 0.1)],
        group="vip_garden",
        tags=["vip", "garden"],
    ))
    patch.patch_fixture("strip_vip_lounge_r", 180, controller_id="wled_16", channel_index=0)

    universe.add_fixture(PointFixture("lamp_vip_accent_1", "VIP Garden North Lamp", Point3D(-8.0, 0.0, 0.0), radius=0.6, group="vip_garden"))
    patch.patch_fixture("lamp_vip_accent_1", 1, controller_id="wled_15", channel_index=1, port_offset=0)

    universe.add_fixture(PointFixture("lamp_vip_accent_2", "VIP Garden South Lamp", Point3D(8.0, 0.0, 0.0), radius=0.6, group="vip_garden"))
    patch.patch_fixture("lamp_vip_accent_2", 1, controller_id="wled_16", channel_index=1, port_offset=0)

    # 7. Festival Mainstage Projector Viewport
    universe.add_fixture(ProjectorViewport(
        fixture_id="projector_stage_backdrop",
        name="Festival Main Backdrop Screen",
        top_left=Point3D(-4.0, 7.2, 5.0),
        bottom_right=Point3D(4.0, 7.2, 1.2),
        group="projectors",
    ))

    return universe, patch


def create_art_gallery_venue() -> tuple[SpatialUniverse, PatchTable]:
    """Create a sleek contemporary art gallery with floating hexagonal halos and wall light blades.

    Includes:
    - 12 WLED controllers on Cat6 Ethernet (wled_01 .. wled_12)
    - 3 Concentric floating geometric hexagonal ceiling halos
    - 8 Architectural wall light blades
    - Centerpiece sculpture pedestal with 16x16 video matrix and base halo
    - 4 Recessed floor track runners
    - 4 Museum accent spotlights
    - Digital canvas projection mapping viewport
    """
    import math
    universe = SpatialUniverse(name="Immersive Art Gallery & Studio")
    patch = PatchTable(name="Art Gallery 12-Node Patch")

    # 1. Concentric Hexagonal Ceiling Halos (Controllers 01 - 03)
    def make_hex_waypoints(radius: float, z_height: float) -> list[Point3D]:
        pts = []
        for i in range(7):
            ang = math.radians(60.0 * i)
            pts.append(Point3D(radius * math.cos(ang), radius * math.sin(ang), z_height))
        return pts

    universe.add_fixture(LinearStripFixture(
        fixture_id="halo_hex_outer",
        name="Outer Hexagonal Ceiling Halo",
        pixel_count=300,
        waypoints=make_hex_waypoints(3.5, 3.6),
        group="ceiling_halos",
        tags=["halo", "hex", "outer"],
    ))
    patch.patch_fixture("halo_hex_outer", 300, controller_id="wled_01", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="halo_hex_mid",
        name="Mid Hexagonal Ceiling Halo",
        pixel_count=240,
        waypoints=make_hex_waypoints(2.5, 3.7),
        group="ceiling_halos",
        tags=["halo", "hex", "mid"],
    ))
    patch.patch_fixture("halo_hex_mid", 240, controller_id="wled_02", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="halo_hex_inner",
        name="Inner Hexagonal Ceiling Halo",
        pixel_count=180,
        waypoints=make_hex_waypoints(1.5, 3.8),
        group="ceiling_halos",
        tags=["halo", "hex", "inner"],
    ))
    patch.patch_fixture("halo_hex_inner", 180, controller_id="wled_03", channel_index=0)

    # 2. Architectural Wall Light Blades (Controllers 04 - 06)
    blades = [
        ("blade_wall_l1", "West Wall Light Blade 1", "wled_04", 0, (-4.8, 3.0)),
        ("blade_wall_l2", "West Wall Light Blade 2", "wled_04", 1, (-4.8, 0.0)),
        ("blade_wall_l3", "West Wall Light Blade 3", "wled_04", 2, (-4.8, -3.0)),
        ("blade_wall_r1", "East Wall Light Blade 1", "wled_05", 0, (4.8, 3.0)),
        ("blade_wall_r2", "East Wall Light Blade 2", "wled_05", 1, (4.8, 0.0)),
        ("blade_wall_r3", "East Wall Light Blade 3", "wled_05", 2, (4.8, -3.0)),
        ("blade_wall_n1", "North Wall Light Blade L", "wled_06", 0, (-2.5, 4.8)),
        ("blade_wall_n2", "North Wall Light Blade R", "wled_06", 1, (2.5, 4.8)),
    ]
    for fid, fname, cid, ch, (x, y) in blades:
        universe.add_fixture(LinearStripFixture(
            fixture_id=fid,
            name=fname,
            pixel_count=120,
            waypoints=[Point3D(x, y, 3.2), Point3D(x, y, 0.2)],
            group="wall_blades",
            tags=["blade", "wall"],
        ))
        patch.patch_fixture(fid, 120, controller_id=cid, channel_index=ch)

    # 3. Center Sculpture Pedestal (Controllers 07 - 08)
    universe.add_fixture(MatrixFixture(
        fixture_id="matrix_pedestal_top",
        name="Sculpture Pedestal Matrix Top (16x16)",
        rows=16,
        cols=16,
        origin=Point3D(-0.6, 0.6, 0.9),
        width=1.2,
        height=1.2,
        group="sculpture",
        tags=["matrix", "pedestal", "center"],
    ))
    patch.patch_fixture("matrix_pedestal_top", 256, controller_id="wled_07", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="strip_pedestal_base",
        name="Sculpture Pedestal Base Glow",
        pixel_count=160,
        waypoints=[
            Point3D(-0.8, -0.8, 0.05), Point3D(0.8, -0.8, 0.05),
            Point3D(0.8, 0.8, 0.05), Point3D(-0.8, 0.8, 0.05), Point3D(-0.8, -0.8, 0.05),
        ],
        group="sculpture",
        tags=["pedestal", "base"],
    ))
    patch.patch_fixture("strip_pedestal_base", 160, controller_id="wled_08", channel_index=0)

    # 4. Floor Recessed Track Runners (Controllers 09 - 11)
    universe.add_fixture(LinearStripFixture(
        fixture_id="runner_floor_north",
        name="North Floor Track Runner",
        pixel_count=180,
        waypoints=[Point3D(-4.2, 4.5, 0.02), Point3D(4.2, 4.5, 0.02)],
        group="floor_tracks",
        tags=["floor", "runner"],
    ))
    patch.patch_fixture("runner_floor_north", 180, controller_id="wled_09", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="runner_floor_south",
        name="South Floor Track Runner",
        pixel_count=180,
        waypoints=[Point3D(-4.2, -4.5, 0.02), Point3D(4.2, -4.5, 0.02)],
        group="floor_tracks",
        tags=["floor", "runner"],
    ))
    patch.patch_fixture("runner_floor_south", 180, controller_id="wled_10", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="runner_floor_west",
        name="West Floor Track Runner",
        pixel_count=180,
        waypoints=[Point3D(-4.5, -4.2, 0.02), Point3D(-4.5, 4.2, 0.02)],
        group="floor_tracks",
        tags=["floor", "runner"],
    ))
    patch.patch_fixture("runner_floor_west", 180, controller_id="wled_11", channel_index=0)

    universe.add_fixture(LinearStripFixture(
        fixture_id="runner_floor_east",
        name="East Floor Track Runner",
        pixel_count=180,
        waypoints=[Point3D(4.5, -4.2, 0.02), Point3D(4.5, 4.2, 0.02)],
        group="floor_tracks",
        tags=["floor", "runner"],
    ))
    patch.patch_fixture("runner_floor_east", 180, controller_id="wled_11", channel_index=1)

    # 5. Museum Spotlights (Controller 12)
    universe.add_fixture(PointFixture("spot_entry_l", "Gallery Entry Left Spot", Point3D(-2.0, -4.6, 0.0), radius=0.35, group="museum_spots"))
    patch.patch_fixture("spot_entry_l", 1, controller_id="wled_12", channel_index=0, port_offset=0)

    universe.add_fixture(PointFixture("spot_entry_r", "Gallery Entry Right Spot", Point3D(2.0, -4.6, 0.0), radius=0.35, group="museum_spots"))
    patch.patch_fixture("spot_entry_r", 1, controller_id="wled_12", channel_index=0, port_offset=1)

    universe.add_fixture(PointFixture("spot_sculpture_overhead", "Sculpture Overhead Spot", Point3D(0.0, 0.0, 3.8), radius=0.5, group="museum_spots"))
    patch.patch_fixture("spot_sculpture_overhead", 1, controller_id="wled_12", channel_index=1, port_offset=0)

    universe.add_fixture(PointFixture("spot_north_wall", "North Wall Artwork Spot", Point3D(0.0, 4.6, 0.0), radius=0.35, group="museum_spots"))
    patch.patch_fixture("spot_north_wall", 1, controller_id="wled_12", channel_index=1, port_offset=1)

    # 6. Virtual Projector Viewport
    universe.add_fixture(ProjectorViewport(
        fixture_id="projector_gallery_canvas",
        name="Digital Canvas Projection Viewport",
        top_left=Point3D(-2.0, 4.9, 3.2),
        bottom_right=Point3D(2.0, 4.9, 0.8),
        group="projectors",
    ))

    return universe, patch


# Preset Registry
VENUE_PRESETS = {
    "concert_hall": create_concert_hall_venue,
    "venue": create_concert_hall_venue,
    "warehouse_rave": create_warehouse_rave_venue,
    "festival_amphitheater": create_festival_amphitheater_venue,
    "art_gallery": create_art_gallery_venue,
}


def get_preset_venue(name: str) -> tuple[SpatialUniverse, PatchTable]:
    """Look up a venue preset by id or friendly name."""
    norm = name.strip().lower().replace("-", "_").replace(" ", "_")
    if norm in VENUE_PRESETS:
        return VENUE_PRESETS[norm]()
    if "warehouse" in norm or "rave" in norm or "boiler" in norm:
        return create_warehouse_rave_venue()
    if "festival" in norm or "amphitheater" in norm or "outdoor" in norm:
        return create_festival_amphitheater_venue()
    if "art" in norm or "gallery" in norm or "museum" in norm or "studio" in norm:
        return create_art_gallery_venue()
    if "concert" in norm or "metro" in norm or "hall" in norm:
        return create_concert_hall_venue()
    raise KeyError(f"Unknown venue preset: {name}. Available: {list(VENUE_PRESETS.keys())}")


def list_preset_names() -> list[dict[str, Any]]:
    """Return catalog of available venue presets with spatial and hardware metadata."""
    presets = [
        ("concert_hall", "Metro Concert Hall & Lounge", create_concert_hall_venue),
        ("warehouse_rave", "Warehouse Rave & Boiler Stage", create_warehouse_rave_venue),
        ("festival_amphitheater", "Outdoor Amphitheater & Lawn", create_festival_amphitheater_venue),
        ("art_gallery", "Immersive Art Gallery & Studio", create_art_gallery_venue),
    ]
    summaries = []
    for pid, pname, factory in presets:
        u, p = factory()
        summaries.append({
            "id": pid,
            "name": pname,
            "fixtures": len(u.fixtures),
            "total_pixels": u.total_pixels,
            "controllers": len(p.get_controllers()),
            "groups": u.groups,
        })
    return summaries


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


def save_all_preset_files(base_dir: str | Path = "data/presets") -> dict[str, tuple[Path, Path]]:
    """Generate and save universe.json and patch.json for all built-in presets."""
    base = Path(base_dir)
    results = {}
    presets = [
        ("concert_hall", create_concert_hall_venue),
        ("warehouse_rave", create_warehouse_rave_venue),
        ("festival_amphitheater", create_festival_amphitheater_venue),
        ("art_gallery", create_art_gallery_venue),
    ]
    for pid, factory in presets:
        pdir = base / pid
        pdir.mkdir(parents=True, exist_ok=True)
        u, p = factory()
        u_path = pdir / "universe.json"
        p_path = pdir / "patch.json"
        u.save_json(u_path)
        p.save_json(p_path)
        results[pid] = (u_path, p_path)

    # Also sync data/venue with concert_hall
    save_default_venue_files()
    return results

