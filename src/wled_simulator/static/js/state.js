/**
 * Central State Store for WLED Digital Twin Studio
 * Follows Unidirectional Data Flow pattern.
 */

export const store = {
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

  // Fixtures: { [channelId]: { x: number, y: number, angle: 0|90|180|270, reversed: boolean } }
  fixtures: {},

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
