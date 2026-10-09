package com.wled.sequencer.player;

import com.wled.sequencer.model.SequenceData;
import com.wled.sequencer.model.SequenceStep;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

class TimelinePlayerTest {

    private TimelinePlayer player;
    private SequenceData show;

    @BeforeEach
    void setUp() {
        // Player without network client for hermetic unit testing
        player = new TimelinePlayer(null);

        show = new SequenceData("Test Concurrent Show");
        SequenceStep s1 = new SequenceStep("step_1", "Ocean Wash", "Intro", 0, 0.0, 10.0, "wave");
        SequenceStep s2 = new SequenceStep("step_2", "Cyan Chase", "Intro", 1, 2.0, 6.0, "chase"); // 2.0 .. 8.0
        SequenceStep s3 = new SequenceStep("step_3", "Header Strobe", "Intro", 2, 4.0, 4.0, "cylon"); // 4.0 .. 8.0
        SequenceStep s4 = new SequenceStep("step_4", "Sunset", "Outro", 0, 10.0, 5.0, "gradient"); // 10.0 .. 15.0

        show.setSteps(List.of(s1, s2, s3, s4));
        player.setSequence(show);
    }

    @Test
    void testConcurrentActiveEvaluation() {
        // At t = 1.0: only step_1 is active
        player.seek(1.0);
        player.evaluateTimeline(true);
        Set<String> active1 = player.getActiveCueIds();
        assertEquals(Set.of("step_1"), active1);

        // At t = 3.0: step_1 and step_2 are BOTH active concurrently
        player.seek(3.0);
        player.evaluateTimeline(true);
        Set<String> active3 = player.getActiveCueIds();
        assertEquals(Set.of("step_1", "step_2"), active3);

        // At t = 5.0: step_1, step_2, and step_3 are ALL 3 active concurrently!
        player.seek(5.0);
        player.evaluateTimeline(true);
        Set<String> active5 = player.getActiveCueIds();
        assertEquals(Set.of("step_1", "step_2", "step_3"), active5);

        // At t = 9.0: step_2 and step_3 ended; only step_1 still active (until 10.0)
        player.seek(9.0);
        player.evaluateTimeline(true);
        Set<String> active9 = player.getActiveCueIds();
        assertEquals(Set.of("step_1"), active9);

        // At t = 11.0: step_4 is active
        player.seek(11.0);
        player.evaluateTimeline(true);
        Set<String> active11 = player.getActiveCueIds();
        assertEquals(Set.of("step_4"), active11);
    }

    @Test
    void testJumpToStepAndSeeking() {
        player.jumpToStep(1); // step_2 starts at 2.0s
        assertEquals(2.0, player.getTotalElapsedSec());

        player.jumpToStep(3); // step_4 starts at 10.0s
        assertEquals(10.0, player.getTotalElapsedSec());

        player.seek(7.5);
        assertEquals(7.5, player.getTotalElapsedSec());

        player.stop();
        assertEquals(0.0, player.getTotalElapsedSec());
        assertTrue(player.getActiveCueIds().isEmpty());
    }

    @Test
    void testPlayerListenerCallbacks() {
        AtomicInteger tickCount = new AtomicInteger(0);
        AtomicInteger activeChanges = new AtomicInteger(0);

        player.addListener(new PlayerListener() {
            @Override
            public void onPlaybackTick(double elapsedSec, double totalDurationSec, int activeCount) {
                tickCount.incrementAndGet();
            }

            @Override
            public void onActiveCuesChanged(Set<String> activeCueIds) {
                activeChanges.incrementAndGet();
            }

            @Override
            public void onPlaybackStateChanged(boolean isPlaying, boolean isPaused) {}
        });

        player.seek(3.0);
        player.evaluateTimeline(true);
        assertTrue(tickCount.get() > 0);
        assertTrue(activeChanges.get() > 0);
    }

    @Test
    void testCapabilitiesAndAtomicControls() {
        var caps = com.wled.sequencer.client.EngineCapabilities.defaults();
        assertNotNull(caps.patterns());
        assertTrue(caps.patterns().contains("wave"));
        assertTrue(caps.palettes().contains("cyberpunk"));
        assertEquals(10, caps.maxLayers());

        player.seek(5.0);
        player.stop();
        assertEquals(0.0, player.getTotalElapsedSec());
        assertFalse(player.isPlaying());
        assertTrue(player.getActiveCueIds().isEmpty());
    }

    @Test
    void testPlayAndClockAdvancement() throws InterruptedException {
        player.play();
        assertTrue(player.isPlaying());
        assertFalse(player.isPaused());

        Thread.sleep(150);

        assertTrue(player.getTotalElapsedSec() > 0.05, "Timeline elapsed should advance: " + player.getTotalElapsedSec());

        player.pause();
        assertTrue(player.isPaused());
        double pausedTime = player.getTotalElapsedSec();

        Thread.sleep(100);
        assertEquals(pausedTime, player.getTotalElapsedSec(), 0.01);

        player.play();
        assertFalse(player.isPaused());
        assertTrue(player.isPlaying());

        player.stop();
        assertFalse(player.isPlaying());
        assertEquals(0.0, player.getTotalElapsedSec());
    }
}
