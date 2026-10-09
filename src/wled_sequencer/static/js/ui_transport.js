/**
 * Transport Controls & Progress Scrub HUD with Timeline Scrubbing
 */

import { player } from "./player.js";
import { state } from "./state.js";

export function initTransport() {
  const btnPlay = document.getElementById("btn-transport-play");
  const btnPause = document.getElementById("btn-transport-pause");
  const btnStop = document.getElementById("btn-transport-stop");
  const btnPrev = document.getElementById("btn-transport-prev");
  const btnNext = document.getElementById("btn-transport-next");

  const tbPlay = document.getElementById("tb-play");
  const tbPause = document.getElementById("tb-pause");
  const tbStop = document.getElementById("tb-stop");
  const tbPrev = document.getElementById("tb-prev");
  const tbNext = document.getElementById("tb-next");

  const timeDisplay = document.getElementById("time-display");
  const progressContainer = document.querySelector(".progress-container");
  const progressBar = document.getElementById("timeline-progress-bar");
  const statusMsg = document.getElementById("status-message");

  function formatTime(sec) {
    const s = Math.max(0, Math.floor(sec));
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    const tenths = Math.floor((sec % 1) * 10);
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}.${tenths}`;
  }

  function updateTransportButtons() {
    const isPlaying = state.isPlaying && !state.isPaused;
    [btnPlay, tbPlay].forEach(b => {
      if (b) b.classList.toggle("active", isPlaying);
    });
    [btnPause, tbPause].forEach(b => {
      if (b) b.classList.toggle("active", state.isPaused);
    });

    if (statusMsg) {
      if (state.isPlaying) {
        if (state.isPaused) {
          statusMsg.textContent = "Playback Paused";
        } else {
          const count = state.activeStepIds ? state.activeStepIds.size : 0;
          statusMsg.textContent = `Playing Sequence (${count} concurrent cue${count === 1 ? '' : 's'} active)`;
        }
      } else {
        statusMsg.textContent = "Stopped (Ready)";
      }
    }
  }

  // Button Listeners
  [btnPlay, tbPlay].forEach(b => {
    if (b) b.addEventListener("click", () => player.play());
  });
  [btnPause, tbPause].forEach(b => {
    if (b) b.addEventListener("click", () => player.pause());
  });
  [btnStop, tbStop].forEach(b => {
    if (b) b.addEventListener("click", () => player.stop());
  });
  [btnPrev, tbPrev].forEach(b => {
    if (b) b.addEventListener("click", () => player.prevStep());
  });
  [btnNext, tbNext].forEach(b => {
    if (b) b.addEventListener("click", () => player.nextStep());
  });

  // Timeline scrubber click to seek
  if (progressContainer) {
    progressContainer.style.cursor = "pointer";
    progressContainer.addEventListener("click", (e) => {
      const rect = progressContainer.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const ratio = Math.max(0, Math.min(1, clickX / rect.width));
      const targetTime = ratio * state.totalSequenceDuration;
      player.seek(targetTime);
    });
  }

  // State Subscriptions
  state.subscribe((event, data) => {
    if (
      event === "playback_started" ||
      event === "playback_paused" ||
      event === "playback_resumed" ||
      event === "playback_stopped"
    ) {
      updateTransportButtons();
      if (!state.isPlaying) {
        if (progressBar) progressBar.style.width = "0%";
        if (timeDisplay) {
          timeDisplay.textContent = `TIME: 00:00.0 / ${formatTime(state.totalSequenceDuration)} | ACTIVE: 0 Cues`;
        }
      }
    } else if (event === "playback_tick" && data) {
      if (timeDisplay) {
        const curTime = formatTime(data.totalElapsed);
        const totDur = formatTime(data.totalDuration);
        const count = data.activeCount ?? (state.activeStepIds ? state.activeStepIds.size : 0);
        timeDisplay.textContent = `TIME: ${curTime} / ${totDur} | ACTIVE: ${count} Cue(s)`;
      }
      if (progressBar && data.totalDuration > 0) {
        const pct = Math.min(100, (data.totalElapsed / data.totalDuration) * 100);
        progressBar.style.width = `${pct.toFixed(1)}%`;
      }
    } else if (event === "sequence_loaded" || event === "step_updated" || event === "step_added" || event === "step_deleted") {
      if (!state.isPlaying && timeDisplay) {
        timeDisplay.textContent = `TIME: 00:00.0 / ${formatTime(state.totalSequenceDuration)} | ACTIVE: 0 Cues`;
      }
    }
  });

  if (timeDisplay) {
    timeDisplay.textContent = `TIME: 00:00.0 / ${formatTime(state.totalSequenceDuration)} | ACTIVE: 0 Cues`;
  }
}
