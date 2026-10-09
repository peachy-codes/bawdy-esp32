/**
 * Network Communication Module
 * Connects to simulator WebSocket for binary pixel frames and JSON telemetry.
 */

import { store } from './state.js';

export function connectSimulatorWebSocket({ onConnected, onDisconnected, onConfig, onTelemetry, onFrame }) {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${proto}//${window.location.host}/ws`;

  let ws = new WebSocket(url);
  ws.binaryType = 'arraybuffer';

  ws.onopen = () => {
    if (onConnected) onConnected();
  };

  ws.onmessage = (event) => {
    if (typeof event.data === 'string') {
      try {
        const msg = JSON.parse(event.data);
        if ((msg.universe || msg.channels) && onConfig) {
          onConfig(msg);
        }
        if (onTelemetry) {
          onTelemetry(msg);
        }
      } catch (e) {
        console.warn('JSON telemetry parse error:', e);
      }
    } else if (event.data instanceof ArrayBuffer) {
      store.pixelData = new Uint8Array(event.data);
      if (onFrame) onFrame();
    }
  };

  ws.onclose = () => {
    if (onDisconnected) onDisconnected();
    setTimeout(() => {
      connectSimulatorWebSocket({ onConnected, onDisconnected, onConfig, onTelemetry, onFrame });
    }, 1500);
  };

  ws.onerror = (err) => {
    console.warn('WebSocket connection error:', err);
  };

  return ws;
}
