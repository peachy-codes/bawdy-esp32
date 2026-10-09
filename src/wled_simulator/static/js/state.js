/**
 * Central State Store for WLED Digital Twin Studio
 * Follows Unidirectional Data Flow pattern.
 */

export const store = {
  // Mode: 'single' (legacy 1 controller) or 'universe' (20+ controllers, spatial canvas)
  isUniverseMode: false,
  universe: null,
  patch: null,
  activeGroupFilter: 'all',
  selectedFixtureId: null,

  channels: [],
  pixelData: null,
  totalLeds: 0,
  udpPort: 4048,
  selectedChannelId: null,

  // Viewport Camera in World Units
  camera: {
    x: 0,
    y: 0,
    zoom: 1.0,
  },

  // Single-channel Fixtures: { [channelId]: { x: number, y: number, angle: 0|90|180|270, reversed: boolean } }
  fixtures: {},

  // Blueprint / Venue Architectural Overlay
  blueprint: {
    visible: true,
    opacity: 0.35,
    image: null,
  },

  // Multi-Node Fleet Telemetry: { [nodeId]: { fps, pps, kbps, status, port } }
  multiNodeStats: {},

  // Interaction State
  draggingFixtureId: null,
  dragOffset: { x: 0, y: 0 },
  isPanning: false,
  panStart: { x: 0, y: 0 },
};

export function loadSavedFixtures() {
  try {
    const raw = localStorage.getItem('wled_studio_fixtures_v2');
    if (raw) store.fixtures = JSON.parse(raw);
  } catch (e) {
    console.warn('LocalStorage access warning:', e);
  }
}

export function saveFixtures() {
  try {
    localStorage.setItem('wled_studio_fixtures_v2', JSON.stringify(studioFixturesCopy()));
  } catch (e) {}
}

function studioFixturesCopy() {
  return JSON.parse(JSON.stringify(store.fixtures));
}
