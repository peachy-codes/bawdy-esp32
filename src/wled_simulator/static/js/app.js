/**
 * Main Application Coordinator
 * Boots modules, registers event listeners, installs ResizeObserver.
 */

import { store, loadSavedFixtures, saveFixtures } from './state.js';
import { screenToWorld, fitToView } from './camera.js';
import {
  FIXTURE_SPAN_WORLD,
  getFixtureAt,
  computeMagneticSnap,
  applyGarageArchPreset,
  applyStackedRowsPreset,
  rotateFixture,
  flipFixture,
} from './fixtures.js';
import { requestStageDraw } from './renderer.js';
import { createTelemetryManager } from './telemetry.js';
import { connectSimulatorWebSocket } from './network.js';

// DOM Elements
const container = document.getElementById('viewport-container');
const canvas = document.getElementById('studio-canvas');
const ctx = canvas.getContext('2d');

const statusDot = document.getElementById('status-indicator');
const deviceNameDisplay = document.getElementById('device-name-display');
const channelMetaDisplay = document.getElementById('channel-meta-display');

const hudFps = document.getElementById('hud-fps');
const hudPps = document.getElementById('hud-pps');
const hudKbps = document.getElementById('hud-kbps');
const hudJitter = document.getElementById('hud-jitter');
const hudIntegrityBadge = document.getElementById('hud-integrity-badge');

const inspectorPanel = document.getElementById('inspector-panel');
const toggleInspectorBtn = document.getElementById('toggle-inspector-btn');
const inspectorCloseBtn = document.getElementById('inspector-close-btn');
const channelListContainer = document.getElementById('channel-list-container');
const selectedControls = document.getElementById('selected-controls');
const selChLabel = document.getElementById('sel-ch-label');
const btnSelRotate = document.getElementById('btn-sel-rotate');
const btnSelFlip = document.getElementById('btn-sel-flip');

const btnPresetGarage = document.getElementById('btn-preset-garage');
const btnPresetStacked = document.getElementById('btn-preset-stacked');
const btnViewFit = document.getElementById('btn-view-fit');
const btnViewReset = document.getElementById('btn-view-reset');

// Initialize State & Storage
loadSavedFixtures();

// Telemetry Manager
const telemetryMgr = createTelemetryManager({
  hudFps,
  hudPps,
  hudKbps,
  hudJitter,
  hudIntegrityBadge,
  statusDot,
});

// Canvas Resizing with DPR Support
function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  const rect = container.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.scale(dpr, dpr);
  requestStageDraw(ctx, container.getBoundingClientRect());
}

// ResizeObserver on Viewport Container (Catches Hero Bar Multi-Layer Wrapping!)
const resizeObserver = new ResizeObserver(() => {
  resizeCanvas();
});
resizeObserver.observe(container);

// Channel Fixtures Initialization
function initChannels(channels, port) {
  store.channels = channels;
  store.totalLeds = channels.reduce((sum, ch) => sum + ch.length, 0);
  store.udpPort = port || 4048;

  channelMetaDisplay.textContent = `DDP Port ${store.udpPort} • ${channels.length} Channels • ${store.totalLeds} LEDs`;

  let hasExisting = true;
  channels.forEach(ch => {
    if (!store.fixtures[ch.channel_id]) {
      hasExisting = false;
    }
  });

  if (!hasExisting || Object.keys(store.fixtures).length === 0) {
    applyGarageArchPreset(container.getBoundingClientRect(), updatePresetButtons);
    fitToView(container.getBoundingClientRect());
  } else {
    fitToView(container.getBoundingClientRect());
  }

  updateInspectorList();
  requestStageDraw(ctx, container.getBoundingClientRect());
}

function updatePresetButtons(activePreset) {
  btnPresetGarage.classList.toggle('active', activePreset === 'garage');
  btnPresetStacked.classList.toggle('active', activePreset === 'stacked');
}

// Interaction Listeners (Pointer Events)
container.addEventListener('pointerdown', (e) => {
  const rect = container.getBoundingClientRect();
  const sx = e.clientX - rect.left;
  const sy = e.clientY - rect.top;
  const worldPos = screenToWorld(sx, sy, rect);

  if (e.button === 1 || e.altKey) {
    store.isPanning = true;
    store.panStart = { x: e.clientX, y: e.clientY };
    container.classList.add('panning');
    container.setPointerCapture(e.pointerId);
    return;
  }

  if (e.button === 0) {
    const hitId = getFixtureAt(worldPos.x, worldPos.y);
    if (hitId !== null) {
      store.selectedChannelId = hitId;
      store.draggingFixtureId = hitId;
      const fix = store.fixtures[hitId];
      store.dragOffset = {
        x: worldPos.x - fix.x,
        y: worldPos.y - fix.y,
      };
      updateInspectorSelection();
      container.setPointerCapture(e.pointerId);
      requestStageDraw(ctx, container.getBoundingClientRect());
    } else {
      store.isPanning = true;
      store.panStart = { x: e.clientX, y: e.clientY };
      container.classList.add('panning');
      container.setPointerCapture(e.pointerId);
    }
  }
});

container.addEventListener('pointermove', (e) => {
  const rect = container.getBoundingClientRect();

  if (store.isPanning) {
    const dx = (e.clientX - store.panStart.x) / store.camera.zoom;
    const dy = (e.clientY - store.panStart.y) / store.camera.zoom;
    store.camera.x -= dx;
    store.camera.y -= dy;
    store.panStart = { x: e.clientX, y: e.clientY };
    requestStageDraw(ctx, rect);
    return;
  }

  if (store.draggingFixtureId !== null) {
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;
    const worldPos = screenToWorld(sx, sy, rect);

    const rawX = worldPos.x - store.dragOffset.x;
    const rawY = worldPos.y - store.dragOffset.y;

    // Magnetic Snapping
    const snapped = computeMagneticSnap(store.draggingFixtureId, rawX, rawY);
    store.fixtures[store.draggingFixtureId].x = Math.round(snapped.x);
    store.fixtures[store.draggingFixtureId].y = Math.round(snapped.y);

    requestStageDraw(ctx, rect);
  }
});

const stopDragging = (e) => {
  if (store.draggingFixtureId !== null) {
    store.draggingFixtureId = null;
    saveFixtures();
  }
  if (store.isPanning) {
    store.isPanning = false;
    container.classList.remove('panning');
  }
};

container.addEventListener('pointerup', stopDragging);
container.addEventListener('pointercancel', stopDragging);

// Zoom via Mouse Wheel
container.addEventListener('wheel', (e) => {
  e.preventDefault();
  const rect = container.getBoundingClientRect();
  const sx = e.clientX - rect.left;
  const sy = e.clientY - rect.top;
  const beforeZoom = screenToWorld(sx, sy, rect);

  const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
  store.camera.zoom = Math.max(0.2, Math.min(store.camera.zoom * zoomFactor, 4.0));

  const afterZoom = screenToWorld(sx, sy, rect);
  store.camera.x += (beforeZoom.x - afterZoom.x);
  store.camera.y += (beforeZoom.y - afterZoom.y);

  requestStageDraw(ctx, rect);
}, { passive: false });

// Keyboard Shortcuts
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === 'r' || e.key === 'R') {
    if (store.selectedChannelId !== null) {
      rotateFixture(store.selectedChannelId);
      requestStageDraw(ctx, container.getBoundingClientRect());
    }
  } else if (e.key === 'f' || e.key === 'F') {
    fitToView(container.getBoundingClientRect());
    requestStageDraw(ctx, container.getBoundingClientRect());
  } else if (e.key === 'g' || e.key === 'G') {
    applyGarageArchPreset(container.getBoundingClientRect(), updatePresetButtons);
    fitToView(container.getBoundingClientRect());
    requestStageDraw(ctx, container.getBoundingClientRect());
  } else if (e.key === 's' || e.key === 'S') {
    applyStackedRowsPreset(container.getBoundingClientRect(), updatePresetButtons);
    fitToView(container.getBoundingClientRect());
    requestStageDraw(ctx, container.getBoundingClientRect());
  }
});

// Inspector UI Binding
btnSelRotate.onclick = () => {
  if (store.selectedChannelId !== null) {
    rotateFixture(store.selectedChannelId);
    requestStageDraw(ctx, container.getBoundingClientRect());
  }
};

btnSelFlip.onclick = () => {
  if (store.selectedChannelId !== null) {
    flipFixture(store.selectedChannelId);
    requestStageDraw(ctx, container.getBoundingClientRect());
  }
};

btnPresetGarage.onclick = () => {
  applyGarageArchPreset(container.getBoundingClientRect(), updatePresetButtons);
  fitToView(container.getBoundingClientRect());
  requestStageDraw(ctx, container.getBoundingClientRect());
};

btnPresetStacked.onclick = () => {
  applyStackedRowsPreset(container.getBoundingClientRect(), updatePresetButtons);
  fitToView(container.getBoundingClientRect());
  requestStageDraw(ctx, container.getBoundingClientRect());
};

btnViewFit.onclick = () => {
  fitToView(container.getBoundingClientRect());
  requestStageDraw(ctx, container.getBoundingClientRect());
};

btnViewReset.onclick = () => {
  store.camera = { x: 0, y: 0, zoom: 1.0 };
  requestStageDraw(ctx, container.getBoundingClientRect());
};

inspectorCloseBtn.onclick = () => {
  inspectorPanel.classList.add('collapsed');
  toggleInspectorBtn.style.display = 'flex';
};

toggleInspectorBtn.onclick = () => {
  inspectorPanel.classList.remove('collapsed');
  toggleInspectorBtn.style.display = 'none';
};

function updateInspectorList() {
  channelListContainer.innerHTML = '';
  store.channels.forEach(ch => {
    const item = document.createElement('div');
    item.className = 'channel-item';
    if (ch.channel_id === store.selectedChannelId) item.classList.add('selected');

    item.innerHTML = `
      <div class="channel-info-left">
        <span class="channel-tag">CH${ch.channel_id}</span>
        <span class="channel-label">${ch.name || 'Strip ' + ch.channel_id}</span>
      </div>
      <span class="channel-count">${ch.length} LEDs</span>
    `;

    item.onclick = () => {
      store.selectedChannelId = ch.channel_id;
      updateInspectorSelection();
      requestStageDraw(ctx, container.getBoundingClientRect());
    };

    channelListContainer.appendChild(item);
  });
  updateInspectorSelection();
}

function updateInspectorSelection() {
  const items = channelListContainer.querySelectorAll('.channel-item');
  items.forEach((it, idx) => {
    const ch = store.channels[idx];
    if (ch && ch.channel_id === store.selectedChannelId) {
      it.classList.add('selected');
    } else {
      it.classList.remove('selected');
    }
  });

  if (store.selectedChannelId !== null) {
    selectedControls.style.display = 'block';
    const ch = store.channels.find(c => c.channel_id === store.selectedChannelId);
    selChLabel.textContent = ch ? `CH${ch.channel_id} (${ch.name})` : `CH${store.selectedChannelId}`;
  } else {
    selectedControls.style.display = 'none';
  }
}

// Connect Network WebSocket
connectSimulatorWebSocket({
  onConnected: () => telemetryMgr.setConnected(true),
  onDisconnected: () => telemetryMgr.setConnected(false),
  onConfig: (config) => {
    if (config.channels && config.channels.length && store.channels.length === 0) {
      initChannels(config.channels, config.port);
    }
  },
  onTelemetry: (t) => telemetryMgr.update(t),
  onFrame: () => requestStageDraw(ctx, container.getBoundingClientRect()),
});

// Initial Setup
resizeCanvas();
