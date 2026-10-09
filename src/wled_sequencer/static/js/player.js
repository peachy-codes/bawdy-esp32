/**
 * High-Precision Concurrent Multi-Layer Timeline Playback Engine
 */

import { engineClient } from "./engine_client.js";
import { state } from "./state.js";

export class SequencerPlayer {
  constructor() {
    this.animFrameId = null;
    this.lastTimestamp = null;
  }

  play() {
    if (!state.sequence.steps || state.sequence.steps.length === 0) return;
    if (state.isPlaying && !state.isPaused) return;

    if (state.isPaused) {
      state.isPaused = false;
      state.isPlaying = true;
      this.lastTimestamp = performance.now();
      this.tick();
      state.notify("playback_resumed");
      return;
    }

    state.isPlaying = true;
    state.isPaused = false;
    state.currentLoopIteration = 1;

    // If starting from stopped at beginning and a step is selected, start from its start time
    if (state.totalElapsed === 0 && state.selectedIndex > 0) {
      const selected = state.sequence.steps[state.selectedIndex];
      if (selected && selected.start_time_sec !== undefined) {
        state.totalElapsed = selected.start_time_sec;
      }
    }

    state.activeStepIds.clear();
    this.evaluateTimeline(true);
    this.lastTimestamp = performance.now();
    this.tick();
    state.notify("playback_started");
  }

  pause() {
    if (!state.isPlaying || state.isPaused) return;
    state.isPaused = true;
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    state.notify("playback_paused");
  }

  stop() {
    state.isPlaying = false;
    state.isPaused = false;
    state.currentPlayingIndex = -1;
    state.totalElapsed = 0;
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }

    // Cleanly clear active layers
    for (let i = 0; i < 10; i++) {
      engineClient.clearLayer(i, 0.2);
    }

    state.activeStepIds.clear();
    state.notify("playback_stopped");
  }

  seek(timeSec) {
    const maxDur = state.totalSequenceDuration;
    state.totalElapsed = Math.max(0, Math.min(maxDur, timeSec));
    if (state.isPlaying) {
      this.evaluateTimeline(true);
    }
    state.notify("playback_tick", {
      totalElapsed: state.totalElapsed,
      totalDuration: state.totalSequenceDuration,
      activeCount: state.activeStepIds.size
    });
  }

  jumpToStep(index) {
    if (index < 0 || index >= state.sequence.steps.length) return;
    const step = state.sequence.steps[index];
    state.selectStep(index);
    state.totalElapsed = step.start_time_sec || 0;

    if (state.isPlaying) {
      this.evaluateTimeline(true);
    } else {
      // Preview single step directly on hardware
      engineClient.applyStep(step, state.sequence.time_dilation);
    }
  }

  nextStep() {
    const curTime = state.totalElapsed;
    // Find next step whose start time is strictly greater than current time
    let nextIdx = -1;
    let minDiff = Infinity;
    state.sequence.steps.forEach((s, idx) => {
      const diff = (s.start_time_sec || 0) - curTime;
      if (diff > 0.05 && diff < minDiff) {
        minDiff = diff;
        nextIdx = idx;
      }
    });

    if (nextIdx !== -1) {
      this.jumpToStep(nextIdx);
    } else if (state.selectedIndex + 1 < state.sequence.steps.length) {
      this.jumpToStep(state.selectedIndex + 1);
    }
  }

  prevStep() {
    const curTime = state.totalElapsed;
    // Find step whose start time is closest before current time
    let prevIdx = -1;
    let minDiff = Infinity;
    state.sequence.steps.forEach((s, idx) => {
      const diff = curTime - (s.start_time_sec || 0);
      if (diff > 0.2 && diff < minDiff) {
        minDiff = diff;
        prevIdx = idx;
      }
    });

    if (prevIdx !== -1) {
      this.jumpToStep(prevIdx);
    } else if (state.selectedIndex - 1 >= 0) {
      this.jumpToStep(state.selectedIndex - 1);
    } else {
      this.seek(0);
    }
  }

  evaluateTimeline(forceApply = false) {
    const t = state.totalElapsed;
    const steps = state.sequence.steps || [];

    // 1. Identify which blocks should be active at timeline t
    const activeSteps = steps.filter(s => {
      const start = s.start_time_sec ?? 0;
      const stop = s.stop_time_sec ?? (start + (s.duration_sec ?? 4));
      return t >= start && t < stop;
    });

    const activeIds = new Set(activeSteps.map(s => s.id));

    // 2. Identify blocks that expired and should deactivate their layer
    const activeLayers = new Set(activeSteps.map(s => s.target_layer));

    for (const oldId of state.activeStepIds) {
      if (!activeIds.has(oldId)) {
        const oldStep = steps.find(s => s.id === oldId);
        if (oldStep) {
          // If no remaining active block is driving this layer, clear it
          if (!activeLayers.has(oldStep.target_layer)) {
            engineClient.clearLayer(oldStep.target_layer, oldStep.fade_out_sec ?? 0.5);
          }
        }
      }
    }

    // 3. Dispatch cues for newly entering blocks (or forced refresh)
    for (const step of activeSteps) {
      if (forceApply || !state.activeStepIds.has(step.id)) {
        engineClient.applyStep(step, state.sequence.time_dilation);
      }
    }

    // 4. Update reactive state
    state.activeStepIds = activeIds;

    if (activeSteps.length > 0) {
      // Find the most recently triggered active step for index highlighting
      let latestStep = activeSteps[0];
      for (const s of activeSteps) {
        if ((s.start_time_sec ?? 0) >= (latestStep.start_time_sec ?? 0)) {
          latestStep = s;
        }
      }
      state.currentPlayingIndex = steps.indexOf(latestStep);
    } else {
      state.currentPlayingIndex = -1;
    }
  }

  tick() {
    if (!state.isPlaying || state.isPaused) return;

    const now = performance.now();
    const dt = (now - (this.lastTimestamp || now)) / 1000;
    this.lastTimestamp = now;

    const dilation = Math.max(0.1, state.sequence.time_dilation || 1.0);
    state.totalElapsed += dt * dilation;

    const totalDur = state.totalSequenceDuration;

    // Check if end of sequence timeline has been reached
    if (totalDur > 0 && state.totalElapsed >= totalDur) {
      this.handleSequenceEnd();
      return;
    }

    this.evaluateTimeline();

    state.notify("playback_tick", {
      totalElapsed: state.totalElapsed,
      totalDuration: totalDur,
      activeCount: state.activeStepIds.size
    });

    this.animFrameId = requestAnimationFrame(() => this.tick());
  }

  handleSequenceEnd() {
    const mode = state.sequence.loop_mode;

    if (mode === "infinite") {
      state.totalElapsed = 0;
      this.evaluateTimeline(true);
      state.notify("playback_tick", {
        totalElapsed: state.totalElapsed,
        totalDuration: state.totalSequenceDuration,
        activeCount: state.activeStepIds.size
      });
      this.animFrameId = requestAnimationFrame(() => this.tick());
    } else if (mode === "count") {
      state.currentLoopIteration++;
      if (state.currentLoopIteration <= (state.sequence.loop_count || 1)) {
        state.totalElapsed = 0;
        this.evaluateTimeline(true);
        state.notify("playback_tick", {
          totalElapsed: state.totalElapsed,
          totalDuration: state.totalSequenceDuration,
          activeCount: state.activeStepIds.size
        });
        this.animFrameId = requestAnimationFrame(() => this.tick());
      } else {
        this.stop();
      }
    } else if (mode === "once_blackout") {
      this.stop();
      engineClient.blackout();
    } else {
      // once_hold: keep final visual state
      this.stop();
    }
  }
}

export const player = new SequencerPlayer();
