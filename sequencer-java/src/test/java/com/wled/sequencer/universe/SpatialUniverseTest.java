package com.wled.sequencer.universe;

import org.junit.jupiter.api.Test;

import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class SpatialUniverseTest {

    @Test
    void testLoadVenueUniverse() throws Exception {
        Path p = Path.of("..", "data", "venue", "universe.json");
        if (!p.toFile().exists()) {
            p = Path.of("data", "venue", "universe.json");
        }
        assertTrue(p.toFile().exists(), "universe.json must exist at " + p);

        SpatialUniverseModel universe = SpatialUniverseModel.loadFromFile(p);
        assertNotNull(universe);
        assertEquals("Metro Concert Hall & Lounge", universe.getName());
        assertEquals(28, universe.getFixtures().size());
        assertEquals(5153, universe.getTotalPixels());

        // Check groups
        List<String> groups = universe.getGroups();
        assertTrue(groups.contains("trusses"));
        assertTrue(groups.contains("festoon"));
        assertTrue(groups.contains("panels"));
        assertTrue(groups.contains("lamps"));
        assertTrue(groups.contains("projectors"));

        // Check first fixture
        FixtureModel f0 = universe.getFixture("truss_roof_front");
        assertNotNull(f0);
        assertEquals("Front Stage Truss Span", f0.getName());
        assertEquals("linear_strip", f0.getType());
        assertEquals(600, f0.getPixelCount());
        assertEquals(600, f0.getPoints().size());

        // Check point fixture (floor lamp)
        FixtureModel fl = universe.getFixture("lamp_stage_fl_l");
        assertNotNull(fl);
        assertEquals("point", fl.getType());
        assertEquals(1, fl.getPixelCount());
        assertEquals(-4.5, fl.getPoints().get(0).getX(), 0.001);

        // Check matrix fixture
        FixtureModel m = universe.getFixture("matrix_stage_left");
        assertNotNull(m);
        assertEquals("matrix", m.getType());
        assertEquals(256, m.getPixelCount());
        assertEquals(256, m.getPoints().size());
    }

    @Test
    void testLoadVenuePatchTable() throws Exception {
        Path p = Path.of("..", "data", "venue", "patch.json");
        if (!p.toFile().exists()) {
            p = Path.of("data", "venue", "patch.json");
        }
        assertTrue(p.toFile().exists(), "patch.json must exist at " + p);

        PatchTableModel patch = PatchTableModel.loadFromFile(p);
        assertNotNull(patch);
        assertEquals(31, patch.getSegments().size());
        assertEquals(5152, patch.getTotalPatchedPixels());

        List<String> controllers = patch.getAllControllers();
        assertEquals(20, controllers.size());
        assertEquals("wled_01", controllers.get(0));
        assertEquals("wled_20", controllers.get(19));

        List<ControllerNodeModel> nodes = patch.generateControllerNodes();
        assertEquals(20, nodes.size());
        assertEquals("wled_01", nodes.get(0).getId());
        assertEquals("10.0.0.101", nodes.get(0).getIp());
        assertEquals(4048, nodes.get(0).getPort());

        // Validate clean patch
        List<String> errors = patch.validate();
        assertTrue(errors.isEmpty(), "Venue patch table should have 0 validation errors");
    }

    @Test
    void testPatchCollisionDetection() {
        PatchTableModel patch = new PatchTableModel();

        PatchSegmentModel s1 = new PatchSegmentModel();
        s1.setControllerId("node_01");
        s1.setChannelIndex(0);
        s1.setFixtureId("fix_A");
        s1.setPortOffset(0);
        s1.setPixelCount(100);

        PatchSegmentModel s2 = new PatchSegmentModel();
        s2.setControllerId("node_01");
        s2.setChannelIndex(0);
        s2.setFixtureId("fix_B");
        s2.setPortOffset(50); // overlaps with fix_A [0..100]
        s2.setPixelCount(100);

        patch.addSegment(s1);
        patch.addSegment(s2);

        List<String> errors = patch.validate();
        assertEquals(1, errors.size());
        assertTrue(errors.get(0).contains("Port Collision on Controller 'node_01' Channel 0"));
    }

    @Test
    void testLoadAllPresetStages() throws Exception {
        String[] presets = {"concert_hall", "warehouse_rave", "festival_amphitheater", "art_gallery"};
        for (String preset : presets) {
            Path uniPath = Path.of("..", "data", "presets", preset, "universe.json");
            if (!uniPath.toFile().exists()) {
                uniPath = Path.of("data", "presets", preset, "universe.json");
            }
            assertTrue(uniPath.toFile().exists(), "Preset universe.json must exist: " + uniPath);
            SpatialUniverseModel universe = SpatialUniverseModel.loadFromFile(uniPath);
            assertNotNull(universe, "Failed to load universe for preset: " + preset);
            assertFalse(universe.getFixtures().isEmpty(), "Fixtures empty for preset: " + preset);
            assertTrue(universe.getTotalPixels() > 0, "Pixel count must be positive for: " + preset);
            assertFalse(universe.getGroups().isEmpty(), "Groups must not be empty for: " + preset);

            Path patchPath = Path.of("..", "data", "presets", preset, "patch.json");
            if (!patchPath.toFile().exists()) {
                patchPath = Path.of("data", "presets", preset, "patch.json");
            }
            assertTrue(patchPath.toFile().exists(), "Preset patch.json must exist: " + patchPath);
            PatchTableModel patch = PatchTableModel.loadFromFile(patchPath);
            assertNotNull(patch, "Failed to load patch for preset: " + preset);
            assertFalse(patch.getSegments().isEmpty(), "Segments empty for preset: " + preset);
            List<String> errors = patch.validate();
            assertTrue(errors.isEmpty(), "Preset patch table must have 0 errors for " + preset + ": " + errors);
        }
    }
}
