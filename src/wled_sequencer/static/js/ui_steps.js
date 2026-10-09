/**
 * Step / Cue List Table UI Component with Concurrent Timeline Highlighting
 */

import { player } from "./player.js";
import { state } from "./state.js";

export function initStepList() {
  const tbody = document.getElementById("cue-tbody");
  const btnAdd = document.getElementById("btn-add-step");
  const btnDup = document.getElementById("btn-duplicate-step");
  const btnDel = document.getElementById("btn-delete-step");
  const btnUp = document.getElementById("btn-move-up");
  const btnDown = document.getElementById("btn-move-down");

  function renderTable() {
    tbody.innerHTML = "";
    state.sequence.steps.forEach((step, idx) => {
      const tr = document.createElement("tr");
      tr.dataset.index = idx;
      tr.dataset.id = step.id;

      const isSelected = idx === state.selectedIndex;
      const isPlayingNow = state.isPlaying && state.activeStepIds && state.activeStepIds.has(step.id);

      if (isSelected) tr.classList.add("selected");
      if (isPlayingNow) tr.classList.add("playing");

      const channelsText = step.channels && step.channels.length > 0
        ? step.channels.map(c => `CH${c}`).join(",")
        : "ALL";

      const colorOrPalette = step.palette
        ? `<span style="text-transform: capitalize;">🎨 ${step.palette}</span>`
        : `<span style="display: inline-block; width: 10px; height: 10px; background-color: ${step.primary_color || '#FF0000'}; border: 1px solid #000; vertical-align: middle; margin-right: 4px;"></span>${step.primary_color}`;

      const stopVal = step.stop_time_sec !== undefined
        ? step.stop_time_sec
        : ((step.start_time_sec || 0) + (step.duration_sec || 4));

      tr.innerHTML = `
        <td style="text-align: center; font-weight: bold;">${idx + 1}</td>
        <td><span class="section-tag">${escapeHtml(step.section || "Main")}</span></td>
        <td><strong>${escapeHtml(step.name || "Cue")}</strong></td>
        <td style="text-align: center;"><span style="background: #e0e0e0; padding: 1px 3px; border: 1px solid #808080;">L${step.target_layer}</span></td>
        <td style="text-align: right; font-family: var(--win-font-mono);">${(step.start_time_sec || 0).toFixed(1)}s</td>
        <td style="text-align: right; font-family: var(--win-font-mono);">${Number(stopVal).toFixed(1)}s</td>
        <td style="text-align: right; font-family: var(--win-font-mono);">${(step.duration_sec || 0).toFixed(1)}s</td>
        <td>${escapeHtml(step.pattern_id || "none")}</td>
        <td>${colorOrPalette}</td>
        <td style="font-size: 10px;">${escapeHtml(step.blend_mode || "OVERWRITE")}</td>
        <td style="text-align: center; font-size: 10px;">${channelsText}</td>
      `;

      tr.addEventListener("click", () => {
        state.selectStep(idx);
      });

      tr.addEventListener("dblclick", () => {
        player.jumpToStep(idx);
      });

      tbody.appendChild(tr);
    });

    updateButtonsState();
    updateStatusPanels();
  }

  function updateButtonsState() {
    const hasSelection = state.selectedIndex >= 0 && state.selectedIndex < state.sequence.steps.length;
    btnDup.disabled = !hasSelection;
    btnDel.disabled = !hasSelection || state.sequence.steps.length <= 1;
    btnUp.disabled = !hasSelection || state.selectedIndex === 0;
    btnDown.disabled = !hasSelection || state.selectedIndex === state.sequence.steps.length - 1;
  }

  function updateStatusPanels() {
    const statusSteps = document.getElementById("status-steps");
    const statusTotalTime = document.getElementById("status-total-time");
    if (statusSteps) statusSteps.textContent = `Cues: ${state.sequence.steps.length}`;
    if (statusTotalTime) statusTotalTime.textContent = `Total: ${state.totalSequenceDuration.toFixed(1)}s`;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // Button actions
  btnAdd.addEventListener("click", () => state.addStep());
  btnDup.addEventListener("click", () => state.duplicateStep(state.selectedIndex));
  btnDel.addEventListener("click", () => state.deleteStep(state.selectedIndex));
  btnUp.addEventListener("click", () => state.moveStep(state.selectedIndex, -1));
  btnDown.addEventListener("click", () => state.moveStep(state.selectedIndex, 1));

  // State Subscriptions
  state.subscribe((event) => {
    if (
      event === "sequence_loaded" ||
      event === "step_added" ||
      event === "step_deleted" ||
      event === "steps_reordered" ||
      event === "step_updated"
    ) {
      renderTable();
    } else if (
      event === "step_selected" ||
      event === "playback_tick" ||
      event === "playback_started" ||
      event === "playback_resumed" ||
      event === "playback_paused" ||
      event === "playback_stopped"
    ) {
      // Re-highlight active concurrent rows & selected row
      const rows = tbody.querySelectorAll("tr");
      rows.forEach((tr, i) => {
        const step = state.sequence.steps[i];
        const isSelected = i === state.selectedIndex;
        const isPlayingNow = state.isPlaying && step && state.activeStepIds && state.activeStepIds.has(step.id);

        tr.classList.toggle("selected", isSelected);
        tr.classList.toggle("playing", !!isPlayingNow);
      });
      updateButtonsState();
      updateStatusPanels();
    }
  });

  renderTable();
}
