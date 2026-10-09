/**
 * Main Application Coordinator
 * Boots modules, registers event listeners, installs ResizeObserver.
 * Seamlessly coordinates both single-device twin mode and 20-node Spatial Universe mode.
 */

import { store, loadSavedFixtures, saveFixtures } from './state.js';
import { screenToWorld, fitToView } from './camera.js';
import {
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
const inspectorTitle = document.getElementById('inspector-title');
const inspectorInstructions = document.getElementById('inspector-instructions');
const channelListContainer = document.getElementById('channel-list-container');
const selectedControls = document.getElementById('selected-controls');
const singleChannelTools = document.getElementById('single-channel-tools');

const selFixName = document.getElementById('sel-fix-name');
const selFixType = document.getElementById('sel-fix-type');
const selFixGroup = document.getElementById('sel-fix-group');
const selFixPixels = document.getElementById('sel-fix-pixels');
const selFixPatch = document.getElementById('sel-fix-patch');

const singlePresetsGroup = document.getElementById('single-presets-group');
const btnPresetGarage = document.getElementById('btn-preset-garage');
const btnPresetStacked = document.getElementById('btn-preset-stacked');
const btnViewFit = document.getElementById('btn-view-fit');
const btnViewReset = document.getElementById('btn-view-reset');

const btnBlueprintToggle = document.getElementById('btn-blueprint-toggle');
const btnNodesToggle = document.getElementById('btn-nodes-toggle');
const groupFilterBar = document.getElementById('group-filter-bar');
const blueprintToolbar = document.getElementById('blueprint-toolbar');
const bpOpacitySlider = document.getElementById('bp-opacity-slider');
const bpOpacityVal = document.getElementById('bp-opacity-val');
const bpFileInput = document.getElementById('bp-file-input');

const nodesDrawerModal = document.getElementById('nodes-drawer-modal');
const nodesModalClose = document.getElementById('nodes-modal-close');
const nodesGridContainer = document.getElementById('nodes-grid-container');
const nodesModalCount = document.getElementById('nodes-modal-count');

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

const resizeObserver = new ResizeObserver(() => {
  resizeCanvas();
});
resizeObserver.observe(container);

// =========================================================================
// Universe Mode Initialization
// =========================================================================
function initUniverse(config) {
  store.isUniverseMode = true;
  store.universe = config.universe;
  store.patch = config.patch;

  deviceNameDisplay.textContent = store.universe.name || 'Metro Concert Hall';
  channelMetaDisplay.textContent = `${store.universe.fixtures.length} Fixtures • ${store.universe.total_pixels} Total LEDs • Cat6 DDP Subnet`;

  if (singlePresetsGroup) singlePresetsGroup.style.display = 'none';
  if (groupFilterBar) groupFilterBar.style.display = 'flex';
  if (blueprintToolbar) blueprintToolbar.style.display = 'flex';
  if (inspectorTitle) inspectorTitle.textContent = 'Venue Fixtures';
  if (inspectorInstructions) inspectorInstructions.textContent = 'Click fixture to view details & patch. Scroll to zoom, drag to pan.';

  renderGroupFilterButtons();
  updateUniverseInspectorList();
  buildNodesModalGrid();

  setTimeout(() => {
    fitToView(container.getBoundingClientRect());
    requestStageDraw(ctx, container.getBoundingClientRect());
  }, 100);
}

function renderGroupFilterButtons() {
  if (!groupFilterBar || !store.universe) return;
  const groups = ['all', ...(store.universe.groups || [])];
  groupFilterBar.innerHTML = '<span class="filter-label">GROUPS:</span>';

  groups.forEach(grp => {
    const btn = document.createElement('button');
    btn.className = `filter-chip ${store.activeGroupFilter === grp ? 'active' : ''}`;
    btn.textContent = grp === 'all' ? 'All' : grp.charAt(0).toUpperCase() + grp.slice(1);
    btn.dataset.group = grp;
    btn.onclick = () => {
      store.activeGroupFilter = grp;
      groupFilterBar.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      updateUniverseInspectorList();
      requestStageDraw(ctx, container.getBoundingClientRect());
    };
    groupFilterBar.appendChild(btn);
  });
}

function updateUniverseInspectorList() {
  channelListContainer.innerHTML = '';
  if (!store.universe) return;

  const fixtures = store.universe.fixtures.filter(f =>
    store.activeGroupFilter === 'all' || f.group === store.activeGroupFilter
  );

  fixtures.forEach(f => {
    const item = document.createElement('div');
    item.className = 'channel-item';
    if (f.id === store.selectedFixtureId) item.classList.add('selected');

    const typeIcons = {
      linear_strip: '📏',
      bulb_string: '💡',
      matrix: '▦',
      point: '🕯️',
      projector: '📽️',
    };
    const icon = typeIcons[f.type] || '⚡';

    item.innerHTML = `
      <div class="channel-info-left">
        <span class="channel-tag">${icon}</span>
        <span class="channel-label">${f.name || f.id}</span>
      </div>
      <span class="channel-count">${f.pixel_count} px</span>
    `;

    item.onclick = () => {
      store.selectedFixtureId = f.id;
      updateUniverseSelection();
      requestStageDraw(ctx, container.getBoundingClientRect());
    };

    channelListContainer.appendChild(item);
  });

  updateUniverseSelection();
}

function updateUniverseSelection() {
  const items = channelListContainer.querySelectorAll('.channel-item');
  const fixtures = (store.universe && store.universe.fixtures) ? store.universe.fixtures.filter(f =>
    store.activeGroupFilter === 'all' || f.group === store.activeGroupFilter
  ) : [];

  items.forEach((it, idx) => {
    const f = fixtures[idx];
    if (f && f.id === store.selectedFixtureId) {
      it.classList.add('selected');
    } else {
      it.classList.remove('selected');
    }
  });

  if (store.selectedFixtureId && store.universe) {
    const fix = store.universe.fixtures.find(f => f.id === store.selectedFixtureId);
    if (fix) {
      selectedControls.style.display = 'block';
      if (singleChannelTools) singleChannelTools.style.display = 'none';

      selFixName.textContent = fix.name || fix.id;
      selFixType.textContent = (fix.type || 'linear_strip').replace('_', ' ').toUpperCase();
      selFixGroup.textContent = fix.group || 'default';
      selFixPixels.textContent = `${fix.pixel_count} LEDs (${fix.color_order || 'GRB'})`;

      // Find patch mapping
      if (store.patch && store.patch.segments) {
        const segs = store.patch.segments.filter(s => s.fixture_id === fix.id);
        if (segs.length > 0) {
          selFixPatch.textContent = segs.map(s => `${s.controller_id}: Ch${s.channel_index} [${s.port_offset}..${s.port_offset + s.pixel_count - 1}]`).join(', ');
        } else {
          selFixPatch.textContent = 'Virtual / Unpatched';
        }
      } else {
        selFixPatch.textContent = 'Auto-Routed';
      }
    }
  } else {
    selectedControls.style.display = 'none';
  }
}

function buildNodesModalGrid() {
  if (!nodesGridContainer) return;
  nodesGridContainer.innerHTML = '';

  const controllers = (store.patch && store.patch.segments)
    ? [...new Set(store.patch.segments.map(s => s.controller_id))].sort()
    : Array.from({ length: 20 }, (_, i) => `wled_${String(i + 1).padStart(2, '0')}`);

  if (nodesModalCount) nodesModalCount.textContent = `${controllers.length} Boards`;

  controllers.forEach((cid, idx) => {
    const card = document.createElement('div');
    card.className = 'node-card';
    card.id = `node-card-${cid}`;

    card.innerHTML = `
      <div class="node-card-header">
        <span>${cid}</span>
        <span class="status-dot active" style="width: 7px; height: 7px;"></span>
      </div>
      <div class="node-card-meta">UDP Port ${4048 + idx} • DDP</div>
      <div class="node-stats">
        <span class="node-fps">30.0 FPS</span>
        <span class="node-pps">30 PPS</span>
      </div>
    `;
    nodesGridContainer.appendChild(card);
  });
}

function updateNodesTelemetry(nodesStats) {
  if (!nodesStats) return;
  Object.entries(nodesStats).forEach(([cid, stat]) => {
    const card = document.getElementById(`node-card-${cid}`);
    if (card) {
      const fpsEl = card.querySelector('.node-fps');
      const ppsEl = card.querySelector('.node-pps');
      if (fpsEl) fpsEl.textContent = `${stat.fps || 0} FPS`;
      if (ppsEl) ppsEl.textContent = `${stat.pps || 0} PPS`;
    }
  });
}

// =========================================================================
// Single Device Channel Mode Initialization
// =========================================================================
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
  }

  fitToView(container.getBoundingClientRect());
  updateInspectorList();
  requestStageDraw(ctx, container.getBoundingClientRect());
}

function updatePresetButtons(activePreset) {
  if (btnPresetGarage) btnPresetGarage.classList.toggle('active', activePreset === 'garage');
  if (btnPresetStacked) btnPresetStacked.classList.toggle('active', activePreset === 'stacked');
}

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
    if (singleChannelTools) singleChannelTools.style.display = 'flex';
    const ch = store.channels.find(c => c.channel_id === store.selectedChannelId);
    selFixName.textContent = ch ? `CH${ch.channel_id} (${ch.name})` : `CH${store.selectedChannelId}`;
    selFixType.textContent = 'Linear Strip';
    selFixGroup.textContent = 'Default';
    selFixPixels.textContent = `${ch ? ch.length : 0} LEDs`;
    selFixPatch.textContent = `Local Port ${store.udpPort}`;
  } else {
    selectedControls.style.display = 'none';
  }
}

// =========================================================================
// Interaction Listeners (Pointer Events)
// =========================================================================
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
      if (store.isUniverseMode) {
        store.selectedFixtureId = hitId;
        updateUniverseSelection();
      } else {
        store.selectedChannelId = hitId;
        store.draggingFixtureId = hitId;
        const fix = store.fixtures[hitId];
        if (fix) {
          store.dragOffset = {
            x: worldPos.x - fix.x,
            y: worldPos.y - fix.y,
          };
        }
        updateInspectorSelection();
      }
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

  if (store.draggingFixtureId !== null && !store.isUniverseMode) {
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;
    const worldPos = screenToWorld(sx, sy, rect);

    const rawX = worldPos.x - store.dragOffset.x;
    const rawY = worldPos.y - store.dragOffset.y;

    const snapped = computeMagneticSnap(store.draggingFixtureId, rawX, rawY);
    if (store.fixtures[store.draggingFixtureId]) {
      store.fixtures[store.draggingFixtureId].x = Math.round(snapped.x);
      store.fixtures[store.draggingFixtureId].y = Math.round(snapped.y);
    }

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
  store.camera.zoom = Math.max(0.15, Math.min(store.camera.zoom * zoomFactor, 5.0));

  const afterZoom = screenToWorld(sx, sy, rect);
  store.camera.x += (beforeZoom.x - afterZoom.x);
  store.camera.y += (beforeZoom.y - afterZoom.y);

  requestStageDraw(ctx, rect);
}, { passive: false });

// Keyboard Shortcuts
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === 'f' || e.key === 'F') {
    fitToView(container.getBoundingClientRect());
    requestStageDraw(ctx, container.getBoundingClientRect());
  } else if (!store.isUniverseMode) {
    if (e.key === 'r' || e.key === 'R') {
      if (store.selectedChannelId !== null) {
        rotateFixture(store.selectedChannelId);
        requestStageDraw(ctx, container.getBoundingClientRect());
      }
    } else if (e.key === 'g' || e.key === 'G') {
      applyGarageArchPreset(container.getBoundingClientRect(), updatePresetButtons);
      fitToView(container.getBoundingClientRect());
      requestStageDraw(ctx, container.getBoundingClientRect());
    } else if (e.key === 's' || e.key === 'S') {
      applyStackedRowsPreset(container.getBoundingClientRect(), updatePresetButtons);
      fitToView(container.getBoundingClientRect());
      requestStageDraw(ctx, container.getBoundingClientRect());
    }
  }
});

// View Controls
if (btnViewFit) {
  btnViewFit.onclick = () => {
    fitToView(container.getBoundingClientRect());
    requestStageDraw(ctx, container.getBoundingClientRect());
  };
}

if (btnViewReset) {
  btnViewReset.onclick = () => {
    store.camera = { x: 0, y: 0, zoom: 1.0 };
    requestStageDraw(ctx, container.getBoundingClientRect());
  };
}

// Blueprint Controls
if (btnBlueprintToggle) {
  btnBlueprintToggle.onclick = () => {
    store.blueprint.visible = !store.blueprint.visible;
    btnBlueprintToggle.classList.toggle('active', store.blueprint.visible);
    requestStageDraw(ctx, container.getBoundingClientRect());
  };
}

if (bpOpacitySlider) {
  bpOpacitySlider.oninput = (e) => {
    const val = parseInt(e.target.value, 10);
    store.blueprint.opacity = val / 100.0;
    if (bpOpacityVal) bpOpacityVal.textContent = `${val}%`;
    requestStageDraw(ctx, container.getBoundingClientRect());
  };
}

if (bpFileInput) {
  bpFileInput.onchange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (re) => {
        const img = new Image();
        img.onload = () => {
          store.blueprint.image = img;
          store.blueprint.visible = true;
          if (btnBlueprintToggle) btnBlueprintToggle.classList.add('active');
          requestStageDraw(ctx, container.getBoundingClientRect());
        };
        img.src = re.target.result;
      };
      reader.readAsDataURL(file);
    }
  };
}

// Multi-Node Modal Controls
if (btnNodesToggle) {
  btnNodesToggle.onclick = () => {
    if (nodesDrawerModal) nodesDrawerModal.style.display = 'flex';
  };
}

if (nodesModalClose) {
  nodesModalClose.onclick = () => {
    if (nodesDrawerModal) nodesDrawerModal.style.display = 'none';
  };
}

if (nodesDrawerModal) {
  nodesDrawerModal.onclick = (e) => {
    if (e.target === nodesDrawerModal) {
      nodesDrawerModal.style.display = 'none';
    }
  };
}

// Single-Mode Preset Buttons
if (btnPresetGarage) {
  btnPresetGarage.onclick = () => {
    applyGarageArchPreset(container.getBoundingClientRect(), updatePresetButtons);
    fitToView(container.getBoundingClientRect());
    requestStageDraw(ctx, container.getBoundingClientRect());
  };
}

if (btnPresetStacked) {
  btnPresetStacked.onclick = () => {
    applyStackedRowsPreset(container.getBoundingClientRect(), updatePresetButtons);
    fitToView(container.getBoundingClientRect());
    requestStageDraw(ctx, container.getBoundingClientRect());
  };
}

// Inspector Drawer Toggle
if (inspectorCloseBtn) {
  inspectorCloseBtn.onclick = () => {
    inspectorPanel.classList.add('collapsed');
    toggleInspectorBtn.style.display = 'flex';
  };
}

if (toggleInspectorBtn) {
  toggleInspectorBtn.onclick = () => {
    inspectorPanel.classList.remove('collapsed');
    toggleInspectorBtn.style.display = 'none';
  };
}

// Connect Network WebSocket
connectSimulatorWebSocket({
  onConnected: () => telemetryMgr.setConnected(true),
  onDisconnected: () => telemetryMgr.setConnected(false),
  onConfig: (config) => {
    if (config.mode === 'universe' || config.universe) {
      initUniverse(config);
    } else if (config.channels && config.channels.length && store.channels.length === 0) {
      initChannels(config.channels, config.port);
    }
  },
  onTelemetry: (t) => {
    telemetryMgr.update(t);
    if (t.nodes) {
      updateNodesTelemetry(t.nodes);
    }
  },
  onFrame: () => requestStageDraw(ctx, container.getBoundingClientRect()),
});

// Initial Canvas Layout
resizeCanvas();
