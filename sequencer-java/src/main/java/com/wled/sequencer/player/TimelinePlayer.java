package com.wled.sequencer.player;

import com.wled.sequencer.client.EngineClient;
import com.wled.sequencer.model.SequenceData;
import com.wled.sequencer.model.SequenceStep;

import javax.swing.SwingUtilities;
import java.util.*;
import java.util.concurrent.*;

/**
 * Concurrent Multi-Layer Timeline Playback Engine.
 *
 * Coordinates timeline execution with high-precision timekeeping,
 * event-driven layer dispatch on cue boundaries, continuous opacity interpolation,
 * and decoupling from the Swing Event Dispatch Thread (EDT).
 */
public class TimelinePlayer {
    private final EngineClient engineClient;
    private SequenceData sequence;

    private final ScheduledExecutorService executor;
    private ScheduledFuture<?> playTask;
    private long lastTimestampNanos = 0;

    private volatile boolean isPlaying = false;
    private volatile boolean isPaused = false;
    private volatile double totalElapsedSec = 0.0;
    private volatile int currentLoopIteration = 0;

    private final Set<String> activeCueIds = new CopyOnWriteArraySet<>();
    private final List<PlayerListener> listeners = new CopyOnWriteArrayList<>();

    public TimelinePlayer(EngineClient engineClient) {
        this.engineClient = engineClient;
        this.sequence = new SequenceData("Default Show");

        // Background playback scheduler decoupled from Swing EDT
        this.executor = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "TimelinePlayerClock");
            t.setDaemon(true);
            return t;
        });
    }

    public void addListener(PlayerListener listener) {
        listeners.add(listener);
    }

    public void removeListener(PlayerListener listener) {
        listeners.remove(listener);
    }

    public SequenceData getSequence() {
        return sequence;
    }

    public void setSequence(SequenceData sequence) {
        boolean wasPlaying = this.isPlaying;
        stop();
        this.sequence = sequence != null ? sequence : new SequenceData("Empty Show");
        this.sequence.normalize();
        notifyTick();
        notifyStateChanged();
        if (wasPlaying) {
            play();
        }
    }

    public boolean isPlaying() {
        return isPlaying;
    }

    public boolean isPaused() {
        return isPaused;
    }

    public double getTotalElapsedSec() {
        return totalElapsedSec;
    }

    public double getElapsedSec() {
        return totalElapsedSec;
    }

    public List<SequenceStep> getActiveSteps() {
        List<SequenceStep> result = new ArrayList<>();
        double t = this.totalElapsedSec;
        for (SequenceStep s : sequence.getSteps()) {
            if (t >= s.getStartTimeSec() && t < s.getStopTimeSec()) {
                result.add(s);
            }
        }
        return result;
    }

    public Set<String> getActiveCueIds() {
        return Collections.unmodifiableSet(activeCueIds);
    }

    public synchronized void play() {
        if (sequence.getSteps().isEmpty()) return;
        if (isPlaying && !isPaused) return;

        if (isPaused) {
            isPaused = false;
            isPlaying = true;
            lastTimestampNanos = System.nanoTime();
            startClockTask();
            notifyStateChanged();
            return;
        }

        isPlaying = true;
        isPaused = false;
        currentLoopIteration = 1;
        lastTimestampNanos = System.nanoTime();
        activeCueIds.clear();

        evaluateTimeline(true);
        startClockTask();
        notifyStateChanged();
    }

    public synchronized void pause() {
        if (!isPlaying || isPaused) return;
        isPaused = true;
        stopClockTask();
        notifyStateChanged();
    }

    public synchronized void stop() {
        isPlaying = false;
        isPaused = false;
        stopClockTask();
        totalElapsedSec = 0.0;
        activeCueIds.clear();

        if (engineClient != null && engineClient.isOnline()) {
            engineClient.blackout();
        }

        notifyTick();
        notifyActiveCuesChanged();
        notifyStateChanged();
    }

    public void seek(double timeSec) {
        double maxDur = sequence.getTotalDuration();
        this.totalElapsedSec = Math.max(0.0, Math.min(maxDur, timeSec));
        lastTimestampNanos = System.nanoTime();
        evaluateTimeline(true);
    }

    public void jumpToStep(int stepIndex) {
        if (stepIndex < 0 || stepIndex >= sequence.getSteps().size()) return;
        SequenceStep step = sequence.getSteps().get(stepIndex);
        seek(step.getStartTimeSec());
    }

    public void nextStep() {
        double cur = this.totalElapsedSec;
        double minDiff = Double.MAX_VALUE;
        int nextIdx = -1;
        for (int i = 0; i < sequence.getSteps().size(); i++) {
            SequenceStep s = sequence.getSteps().get(i);
            double diff = s.getStartTimeSec() - cur;
            if (diff > 0.05 && diff < minDiff) {
                minDiff = diff;
                nextIdx = i;
            }
        }
        if (nextIdx != -1) {
            jumpToStep(nextIdx);
        }
    }

    public void prevStep() {
        double cur = this.totalElapsedSec;
        double minDiff = Double.MAX_VALUE;
        int prevIdx = -1;
        for (int i = 0; i < sequence.getSteps().size(); i++) {
            SequenceStep s = sequence.getSteps().get(i);
            double diff = cur - s.getStartTimeSec();
            if (diff > 0.2 && diff < minDiff) {
                minDiff = diff;
                prevIdx = i;
            }
        }
        if (prevIdx != -1) {
            jumpToStep(prevIdx);
        } else {
            seek(0.0);
        }
    }

    /**
     * Evaluates timeline cues and dispatches layer states with continuous opacity interpolation.
     * When online, dispatches layer updates to the engine daemon on cue state transitions.
     */
    public void evaluateTimeline(boolean forceApply) {
        double t = this.totalElapsedSec;
        List<SequenceStep> steps = sequence.getSteps();

        List<SequenceStep> activeSteps = new ArrayList<>();
        Set<String> newActiveIds = new HashSet<>();
        Map<Integer, SequenceStep> layerClaims = new HashMap<>();

        for (SequenceStep s : steps) {
            double start = s.getStartTimeSec();
            double stop = s.getStopTimeSec();
            if (t >= start && t < stop) {
                activeSteps.add(s);
                newActiveIds.add(s.getId());
                layerClaims.put(s.getTargetLayer(), s);
            }
        }

        // Cleanly clear layers only if no active step is claiming them (avoids layer collision cut-offs)
        if (engineClient != null && engineClient.isOnline()) {
            for (String oldId : this.activeCueIds) {
                if (!newActiveIds.contains(oldId)) {
                    SequenceStep oldStep = findStepById(oldId);
                    if (oldStep != null && !layerClaims.containsKey(oldStep.getTargetLayer())) {
                        engineClient.clearLayer(oldStep.getTargetLayer(), oldStep.getFadeOutSec());
                    }
                }
            }

            for (SequenceStep step : activeSteps) {
                if (forceApply || !this.activeCueIds.contains(step.getId())) {
                    engineClient.applyStep(step, sequence.getTimeDilation());
                }
            }
        }

        boolean activeSetChanged = !this.activeCueIds.equals(newActiveIds);
        this.activeCueIds.clear();
        this.activeCueIds.addAll(newActiveIds);

        if (activeSetChanged) {
            notifyActiveCuesChanged();
        }
        notifyTick();
    }

    private synchronized void startClockTask() {
        stopClockTask();
        lastTimestampNanos = System.nanoTime();
        playTask = executor.scheduleAtFixedRate(this::clockTick, 33, 33, TimeUnit.MILLISECONDS);
    }

    private synchronized void stopClockTask() {
        if (playTask != null) {
            playTask.cancel(false);
            playTask = null;
        }
    }

    private void clockTick() {
        if (!isPlaying || isPaused) return;

        long nowNanos = System.nanoTime();
        double dt = (nowNanos - lastTimestampNanos) / 1_000_000_000.0;
        lastTimestampNanos = nowNanos;

        double dilation = Math.max(0.05, sequence.getTimeDilation());
        this.totalElapsedSec += dt * dilation;

        double totalDur = sequence.getTotalDuration();
        if (totalDur > 0 && this.totalElapsedSec >= totalDur) {
            handleSequenceEnd();
            return;
        }

        evaluateTimeline(false);
    }

    private void handleSequenceEnd() {
        String mode = sequence.getLoopMode();
        if ("infinite".equalsIgnoreCase(mode)) {
            this.totalElapsedSec = 0.0;
            lastTimestampNanos = System.nanoTime();
            evaluateTimeline(true);
        } else if ("count".equalsIgnoreCase(mode)) {
            this.currentLoopIteration++;
            if (this.currentLoopIteration <= sequence.getLoopCount()) {
                this.totalElapsedSec = 0.0;
                lastTimestampNanos = System.nanoTime();
                int iter = currentLoopIteration;
                int count = sequence.getLoopCount();
                for (PlayerListener l : listeners) {
                    try {
                        l.onLoopIteration(iter, count);
                    } catch (Exception ignored) {}
                }
                evaluateTimeline(true);
            } else {
                stop();
            }
        } else if ("once_blackout".equalsIgnoreCase(mode)) {
            stop();
        } else {
            // once_hold: stop playback clock but leave current layer visual state intact
            isPlaying = false;
            isPaused = false;
            stopClockTask();
            notifyStateChanged();
        }
    }

    private SequenceStep findStepById(String id) {
        for (SequenceStep s : sequence.getSteps()) {
            if (s.getId().equals(id)) return s;
        }
        return null;
    }

    private void notifyTick() {
        double elapsed = totalElapsedSec;
        double total = sequence.getTotalDuration();
        int activeCount = activeCueIds.size();
        for (PlayerListener l : listeners) {
            try {
                l.onPlaybackTick(elapsed, total, activeCount);
            } catch (Exception ignored) {}
        }
    }

    private void notifyActiveCuesChanged() {
        Set<String> unmodifiable = Collections.unmodifiableSet(new HashSet<>(activeCueIds));
        for (PlayerListener l : listeners) {
            try {
                l.onActiveCuesChanged(unmodifiable);
            } catch (Exception ignored) {}
        }
    }

    private void notifyStateChanged() {
        boolean playing = isPlaying;
        boolean paused = isPaused;
        for (PlayerListener l : listeners) {
            try {
                l.onPlaybackStateChanged(playing, paused);
            } catch (Exception ignored) {}
        }
    }
}
