/**
 * REST API Client communicating with WLED Lighting Engine Daemon
 */

import { state } from "./state.js";

export class EngineClient {
  constructor() {
    this.checkTimer = null;
  }

  startHealthCheck(intervalMs = 3000) {
    this.ping();
    this.checkTimer = setInterval(() => this.ping(), intervalMs);
  }

  stopHealthCheck() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
    }
  }

  async ping() {
    const url = `${state.engineUrl.replace(/\/+$/, "")}/api/status`;
    try {
      const resp = await fetch(url, { method: "GET", mode: "cors" });
      if (resp.ok) {
        const data = await resp.json();
        state.engineOnline = true;
        state.engineFps = data.actual_fps || 30.0;
        state.notify("engine_status", { online: true, fps: state.engineFps });
        return true;
      }
    } catch {
      // Offline
    }
    state.engineOnline = false;
    state.engineFps = 0.0;
    state.notify("engine_status", { online: false, fps: 0.0 });
    return false;
  }

  async applyStep(step, timeDilation = 1.0) {
    if (!state.engineOnline) return;
    const base = state.engineUrl.replace(/\/+$/, "");
    const layerIdx = step.target_layer;

    // 1. If pattern is "none" or null, clear layer
    if (!step.pattern_id || step.pattern_id === "none") {
      await this.clearLayer(layerIdx, 0.0);
      return;
    }

    // 2. Prepare layer payload
    const effectiveTransition = Math.max(0, (step.transition_sec || 0) / Math.max(0.05, timeDilation));
    const startOpacity = effectiveTransition > 0.05 ? 0.0 : (step.target_opacity ?? 1.0);

    const payload = {
      pattern: step.pattern_id,
      color: step.primary_color || "#FF0000",
      speed: step.speed || 1.0,
      brightness: step.brightness || 1.0,
      blend_mode: step.blend_mode || "OVERWRITE",
      channels: step.channels || null,
      opacity: startOpacity,
      enabled: true
    };

    try {
      await fetch(`${base}/api/layers/${layerIdx}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      // 3. Trigger fade tween if transition duration specified
      if (effectiveTransition > 0.05) {
        await fetch(`${base}/api/layers/${layerIdx}/fade`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            target_opacity: step.target_opacity ?? 1.0,
            duration_sec: effectiveTransition
          })
        });
      }
    } catch (err) {
      console.warn(`Failed to dispatch step to layer ${layerIdx}:`, err);
    }
  }

  async clearLayer(layerIdx, fadeOutSec = 0.5) {
    if (!state.engineOnline) return;
    const base = state.engineUrl.replace(/\/+$/, "");

    try {
      if (fadeOutSec > 0.05) {
        // Fade out smoothly
        await fetch(`${base}/api/layers/${layerIdx}/fade`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            target_opacity: 0.0,
            duration_sec: fadeOutSec
          })
        });

        // After fade duration, turn off pattern and disabled flag
        setTimeout(async () => {
          try {
            await fetch(`${base}/api/layers/${layerIdx}`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ pattern: null, enabled: false, opacity: 0.0 })
            });
          } catch {}
        }, fadeOutSec * 1000);
      } else {
        await fetch(`${base}/api/layers/${layerIdx}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pattern: null, enabled: false, opacity: 0.0 })
        });
      }
    } catch (err) {
      console.warn(`Failed to clear layer ${layerIdx}:`, err);
    }
  }

  async blackout() {
    if (!state.engineOnline) return;
    const base = state.engineUrl.replace(/\/+$/, "");
    for (let i = 0; i < 10; i++) {
      try {
        await fetch(`${base}/api/layers/${i}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pattern: null, opacity: 0.0, enabled: false })
        });
      } catch {
        // continue
      }
    }
  }
}

export const engineClient = new EngineClient();
