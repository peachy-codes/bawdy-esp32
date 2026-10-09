/**
 * Step Property Inspector Component with Two-Way Start/Stop/Duration Calculations
 */

import { state } from "./state.js";

export function initInspector() {
  // Tabs
  const tabButtons = document.querySelectorAll(".win95-tab");
  const tabContents = document.querySelectorAll(".tab-content");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.style.display = "none");

      btn.classList.add("active");
      const targetId = btn.dataset.tab;
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.style.display = "block";
    });
  });

  // Inputs - Tab 1: General & Layer
  const inpSection = document.getElementById("inp-step-section");
  const selQuickSection = document.getElementById("sel-quick-section");
  const inpName = document.getElementById("inp-step-name");
  const selLayer = document.getElementById("sel-target-layer");
  const selBlend = document.getElementById("sel-blend-mode");
  const chkAll = document.getElementById("chk-ch-all");
  const chkChannels = document.querySelectorAll(".chk-ch");

  // Inputs - Tab 2: Pattern & Color
  const selPattern = document.getElementById("sel-pattern");
  const inpColor = document.getElementById("inp-primary-color");
  const inpColorHex = document.getElementById("inp-color-hex");
  const selQuickColor = document.getElementById("sel-quick-color");
  const selPalette = document.getElementById("sel-palette");
  const inpSpeedRange = document.getElementById("inp-speed-range");
  const inpSpeed = document.getElementById("inp-speed");
  const inpBrightnessRange = document.getElementById("inp-brightness-range");
  const inpBrightness = document.getElementById("inp-brightness");

  // Inputs - Tab 3: Timing & Fade
  const inpStart = document.getElementById("inp-start-sec");
  const inpDuration = document.getElementById("inp-duration-sec");
  const inpStop = document.getElementById("inp-stop-sec");
  const inpTransition = document.getElementById("inp-transition-sec");
  const inpFadeOut = document.getElementById("inp-fadeout-sec");
  const inpOpacityRange = document.getElementById("inp-opacity-range");
  const inpOpacity = document.getElementById("inp-target-opacity");

  let isPopulating = false;

  function loadStepIntoForm() {
    const step = state.selectedStep;
    if (!step) return;

    isPopulating = true;
    if (inpSection) inpSection.value = step.section || "Main";
    inpName.value = step.name || "";
    selLayer.value = String(step.target_layer ?? 0);
    selBlend.value = step.blend_mode || "OVERWRITE";

    // Channels
    if (!step.channels || step.channels.length === 0) {
      chkAll.checked = true;
      chkChannels.forEach(c => c.checked = false);
    } else {
      chkAll.checked = false;
      chkChannels.forEach(c => {
        c.checked = step.channels.includes(parseInt(c.value, 10));
      });
    }

    selPattern.value = step.pattern_id || "none";
    inpColor.value = step.primary_color || "#FF0000";
    inpColorHex.value = step.primary_color || "#FF0000";
    selQuickColor.value = "";
    selPalette.value = step.palette || "";

    inpSpeed.value = step.speed ?? 1.0;
    inpSpeedRange.value = step.speed ?? 1.0;

    inpBrightness.value = step.brightness ?? 1.0;
    inpBrightnessRange.value = step.brightness ?? 1.0;

    const startVal = step.start_time_sec ?? 0.0;
    const durVal = step.duration_sec ?? step.hold_duration_sec ?? 4.0;
    const stopVal = step.stop_time_sec !== undefined ? step.stop_time_sec : (startVal + durVal);

    if (inpStart) inpStart.value = startVal.toFixed(1);
    if (inpDuration) inpDuration.value = durVal.toFixed(1);
    if (inpStop) inpStop.value = Number(stopVal).toFixed(1);

    if (inpTransition) inpTransition.value = (step.transition_sec ?? 1.0).toFixed(1);
    if (inpFadeOut) inpFadeOut.value = (step.fade_out_sec ?? 0.5).toFixed(1);

    inpOpacity.value = step.target_opacity ?? 1.0;
    inpOpacityRange.value = step.target_opacity ?? 1.0;

    isPopulating = false;
  }

  function saveFormIntoStep() {
    if (isPopulating) return;

    // Collect channels
    let channels = null;
    if (!chkAll.checked) {
      const selectedChs = [];
      chkChannels.forEach(c => {
        if (c.checked) selectedChs.push(parseInt(c.value, 10));
      });
      if (selectedChs.length > 0) channels = selectedChs;
    }

    const startVal = Math.max(0.0, parseFloat(inpStart ? inpStart.value : 0.0) || 0.0);
    const durVal = Math.max(0.1, parseFloat(inpDuration ? inpDuration.value : 4.0) || 0.1);

    state.updateSelectedStep({
      section: inpSection ? inpSection.value.trim() || "Main" : "Main",
      name: inpName.value.trim() || "Cue",
      target_layer: parseInt(selLayer.value, 10),
      blend_mode: selBlend.value,
      channels: channels,
      pattern_id: selPattern.value,
      primary_color: inpColorHex.value.trim() || "#FF0000",
      palette: selPalette.value || null,
      speed: parseFloat(inpSpeed.value) || 1.0,
      brightness: parseFloat(inpBrightness.value) || 1.0,
      start_time_sec: startVal,
      duration_sec: durVal,
      transition_sec: Math.max(0.0, parseFloat(inpTransition ? inpTransition.value : 1.0) || 0.0),
      fade_out_sec: Math.max(0.0, parseFloat(inpFadeOut ? inpFadeOut.value : 0.5) || 0.0),
      target_opacity: Math.max(0.0, Math.min(1.0, parseFloat(inpOpacity.value) || 1.0))
    });
  }

  // Two-way calculation handlers for Timing
  if (inpStart) {
    inpStart.addEventListener("input", () => {
      if (isPopulating) return;
      const s = Math.max(0, parseFloat(inpStart.value) || 0);
      const d = Math.max(0.1, parseFloat(inpDuration.value) || 0.1);
      if (inpStop) inpStop.value = (s + d).toFixed(1);
      saveFormIntoStep();
    });
  }

  if (inpDuration) {
    inpDuration.addEventListener("input", () => {
      if (isPopulating) return;
      const s = Math.max(0, parseFloat(inpStart.value) || 0);
      const d = Math.max(0.1, parseFloat(inpDuration.value) || 0.1);
      if (inpStop) inpStop.value = (s + d).toFixed(1);
      saveFormIntoStep();
    });
  }

  if (inpStop) {
    inpStop.addEventListener("input", () => {
      if (isPopulating) return;
      const s = Math.max(0, parseFloat(inpStart.value) || 0);
      let stop = parseFloat(inpStop.value);
      if (isNaN(stop) || stop <= s) {
        stop = s + 0.1;
      }
      const d = Math.max(0.1, Math.round((stop - s) * 10) / 10);
      if (inpDuration) inpDuration.value = d.toFixed(1);
      saveFormIntoStep();
    });
  }

  if (inpTransition) {
    inpTransition.addEventListener("input", saveFormIntoStep);
  }
  if (inpFadeOut) {
    inpFadeOut.addEventListener("input", saveFormIntoStep);
  }

  // Quick section selector
  if (selQuickSection) {
    selQuickSection.addEventListener("change", () => {
      if (selQuickSection.value) {
        if (inpSection) inpSection.value = selQuickSection.value;
        selQuickSection.value = "";
        saveFormIntoStep();
      }
    });
  }

  // Bind change events
  [inpSection, inpName, selLayer, selBlend, selPattern, selPalette].forEach(el => {
    if (!el) return;
    el.addEventListener("change", saveFormIntoStep);
    el.addEventListener("input", saveFormIntoStep);
  });

  // Channel toggles
  chkAll.addEventListener("change", () => {
    if (chkAll.checked) {
      chkChannels.forEach(c => c.checked = false);
    }
    saveFormIntoStep();
  });

  chkChannels.forEach(c => {
    c.addEventListener("change", () => {
      if (c.checked) chkAll.checked = false;
      saveFormIntoStep();
    });
  });

  // Color sync
  inpColor.addEventListener("input", () => {
    inpColorHex.value = inpColor.value.toUpperCase();
    saveFormIntoStep();
  });

  inpColorHex.addEventListener("change", () => {
    let hex = inpColorHex.value.trim();
    if (!hex.startsWith("#")) hex = "#" + hex;
    if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
      inpColor.value = hex;
      inpColorHex.value = hex.toUpperCase();
    }
    saveFormIntoStep();
  });

  selQuickColor.addEventListener("change", () => {
    if (selQuickColor.value) {
      inpColor.value = selQuickColor.value;
      inpColorHex.value = selQuickColor.value;
      saveFormIntoStep();
    }
  });

  // Sliders sync with numeric inputs
  inpSpeedRange.addEventListener("input", () => {
    inpSpeed.value = inpSpeedRange.value;
    saveFormIntoStep();
  });
  inpSpeed.addEventListener("input", () => {
    inpSpeedRange.value = inpSpeed.value;
    saveFormIntoStep();
  });

  inpBrightnessRange.addEventListener("input", () => {
    inpBrightness.value = inpBrightnessRange.value;
    saveFormIntoStep();
  });
  inpBrightness.addEventListener("input", () => {
    inpBrightnessRange.value = inpBrightness.value;
    saveFormIntoStep();
  });

  inpOpacityRange.addEventListener("input", () => {
    inpOpacity.value = inpOpacityRange.value;
    saveFormIntoStep();
  });
  inpOpacity.addEventListener("input", () => {
    inpOpacityRange.value = inpOpacity.value;
    saveFormIntoStep();
  });

  // State Subscriptions
  state.subscribe((event) => {
    if (event === "step_selected" || event === "sequence_loaded" || event === "step_added") {
      loadStepIntoForm();
    }
  });

  loadStepIntoForm();
}
