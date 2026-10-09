/**
 * Pattern Sequencer Application Bootstrap
 */

import { engineClient } from "./engine_client.js";
import { state } from "./state.js";
import { initDialogs } from "./ui_dialogs.js";
import { initGlobalSettings } from "./ui_global.js";
import { initInspector } from "./ui_inspector.js";
import { initStepList } from "./ui_steps.js";
import { initTransport } from "./ui_transport.js";

async function bootstrap() {
  console.log("⚡ Bootstrapping WLED Pattern Sequencer [Windows 95 Edition]...");

  // 1. Initialize UI components
  initStepList();
  initInspector();
  initTransport();
  initGlobalSettings();
  initDialogs();

  // 2. Start engine health check pinger
  engineClient.startHealthCheck(2500);

  // 3. Load initial demo sequence from backend repository
  try {
    const resp = await fetch("/api/sequences/garage_light_show.json");
    if (resp.ok) {
      const data = await resp.json();
      state.setSequence(data, "garage_light_show.json");
      const titleEl = document.getElementById("window-title-text");
      if (titleEl) {
        titleEl.textContent = `WLED Pattern Sequencer - [garage_light_show.json]`;
      }
    }
  } catch (err) {
    console.warn("Could not load default sequence:", err);
  }

  console.log("✅ WLED Pattern Sequencer ready!");
}

document.addEventListener("DOMContentLoaded", bootstrap);
