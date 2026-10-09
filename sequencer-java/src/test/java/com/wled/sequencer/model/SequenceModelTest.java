package com.wled.sequencer.model;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class SequenceModelTest {

    @TempDir
    Path tempDir;

    private SequenceRepository repo;

    @BeforeEach
    void setUp() {
        repo = new SequenceRepository(tempDir);
    }

    @Test
    void testStepTimingCalculations() {
        SequenceStep step = new SequenceStep("s1", "Intro Wave", "Intro", 0, 2.5, 4.0, "wave");
        assertEquals(2.5, step.getStartTimeSec());
        assertEquals(4.0, step.getDurationSec());
        assertEquals(6.5, step.getStopTimeSec());

        // Modifying stop time recalculates duration
        step.setStopTimeSec(10.0);
        assertEquals(7.5, step.getDurationSec());
        assertEquals(10.0, step.getStopTimeSec());

        // Clamping check
        step.setStopTimeSec(1.0); // before start time
        assertEquals(0.1, step.getDurationSec());
        assertEquals(2.6, step.getStopTimeSec());
    }

    @Test
    void testTargetLayerValidation() {
        SequenceStep step = new SequenceStep();
        step.setTargetLayer(0);
        assertEquals(0, step.getTargetLayer());
        step.setTargetLayer(9);
        assertEquals(9, step.getTargetLayer());

        assertThrows(IllegalArgumentException.class, () -> step.setTargetLayer(10));
        assertThrows(IllegalArgumentException.class, () -> step.setTargetLayer(-1));
    }

    @Test
    void testSequenceTotalDuration() {
        SequenceData seq = new SequenceData("Show");
        SequenceStep s1 = new SequenceStep("s1", "Cue 1", "Intro", 0, 0.0, 5.0, "rainbow");
        SequenceStep s2 = new SequenceStep("s2", "Cue 2", "Intro", 1, 2.0, 8.0, "chase"); // stop = 10.0
        SequenceStep s3 = new SequenceStep("s3", "Cue 3", "Outro", 0, 8.0, 4.0, "wave");  // stop = 12.0
        seq.setSteps(List.of(s1, s2, s3));

        assertEquals(12.0, seq.getTotalDuration());
    }

    @Test
    void testRepositorySaveAndLoad() throws IOException {
        SequenceData seq = new SequenceData("My Cyber Show");
        seq.setLoopMode("count");
        seq.setLoopCount(3);
        seq.setTimeDilation(1.5);

        SequenceStep step = new SequenceStep("c1", "Laser", "Main", 1, 0.0, 6.0, "cylon");
        step.setChannels(List.of(2));
        step.setBlendMode("ADDITIVE");
        seq.getSteps().add(step);

        String savedName = repo.saveSequence(seq, null);
        assertTrue(savedName.endsWith(".json"));

        List<SequenceSummary> list = repo.listSequences();
        assertEquals(1, list.size());
        assertEquals("My Cyber Show", list.get(0).name());
        assertEquals(1, list.get(0).stepCount());

        SequenceData loaded = repo.loadSequence(savedName);
        assertNotNull(loaded);
        assertEquals("My Cyber Show", loaded.getName());
        assertEquals(1.5, loaded.getTimeDilation());
        assertEquals("count", loaded.getLoopMode());
        assertEquals(3, loaded.getLoopCount());
        assertEquals(1, loaded.getSteps().size());
        assertEquals("cylon", loaded.getSteps().get(0).getPatternId());
        assertEquals(List.of(2), loaded.getSteps().get(0).getChannels());
        assertEquals("ADDITIVE", loaded.getSteps().get(0).getBlendMode());
    }

    @Test
    void testLoadExistingSequencesDirectory() {
        Path rootSequences = Path.of("..", "sequences");
        if (Files.isDirectory(rootSequences)) {
            SequenceRepository realRepo = new SequenceRepository(rootSequences);
            List<SequenceSummary> list = realRepo.listSequences();
            assertFalse(list.isEmpty());

            SequenceData garage = realRepo.loadSequence("garage_light_show.json");
            assertNotNull(garage);
            assertFalse(garage.getSteps().isEmpty());
            assertTrue(garage.getTotalDuration() > 0);
        }
    }

    @Test
    void testSequenceDocumentDirtyTracking() {
        SequenceData data = new SequenceData("Editor Test");
        SequenceDocument doc = new SequenceDocument(data, "test_doc.json");

        assertFalse(doc.isDirty());
        assertEquals("test_doc.json", doc.getTitle());

        boolean[] notified = {false};
        doc.addListener(d -> notified[0] = true);

        doc.markDirty();
        assertTrue(doc.isDirty());
        assertTrue(notified[0]);
        assertEquals("test_doc.json *", doc.getTitle());

        notified[0] = false;
        doc.markClean();
        assertFalse(doc.isDirty());
        assertTrue(notified[0]);
        assertEquals("test_doc.json", doc.getTitle());

        // Test setData resets dirty flag
        doc.markDirty();
        assertTrue(doc.isDirty());
        notified[0] = false;

        SequenceData nextData = new SequenceData("Brand New Show");
        doc.setData(nextData, "new_show.json");
        assertFalse(doc.isDirty());
        assertTrue(notified[0]);
        assertEquals("new_show.json", doc.getTitle());
    }
}
