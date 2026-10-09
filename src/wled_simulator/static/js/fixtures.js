/**
 * Fixture Geometry, Magnetic Snapping & Presets Module
 */

import { store, saveFixtures } from './state.js';

export const FIXTURE_SPAN_WORLD = 560;

export function applyGarageArchPreset(containerRect, onComplete) {
  if (store.channels.length < 3) {
    applyStackedRowsPreset(containerRect, onComplete);
    return;
  }

  // Archway Geometry:
  // CH1: Left Vertical Run (270 LEDs) -> oriented straight up (270 deg)
  // CH2: Top Horizontal Run (270 LEDs) -> left to right (0 deg)
  // CH3: Right Vertical Run (270 LEDs) -> oriented straight down (90 deg)
  const span = 560;
  const height = 560;

  const ch1 = store.channels[0];
  const ch2 = store.channels[1];
  const ch3 = store.channels[2];

  store.fixtures[ch1.channel_id] = {
    x: -span / 2,
    y: height / 2,
    angle: 270,
    reversed: false,
  };

  store.fixtures[ch2.channel_id] = {
    x: -span / 2,
    y: -height / 2,
    angle: 0,
    reversed: false,
  };

  store.fixtures[ch3.channel_id] = {
    x: span / 2,
    y: -height / 2,
    angle: 90,
    reversed: false,
  };

  // Additional channels stacked neatly below
  for (let i = 3; i < store.channels.length; i++) {
    const extra = store.channels[i];
    store.fixtures[extra.channel_id] = {
      x: -span / 2,
      y: height / 2 + 80 + (i - 3) * 60,
      angle: 0,
      reversed: false,
    };
  }

  saveFixtures();
  if (onComplete) onComplete('garage');
}

export function applyStackedRowsPreset(containerRect, onComplete) {
  const startY = -((store.channels.length - 1) * 70) / 2;
  const span = 600;

  store.channels.forEach((ch, idx) => {
    store.fixtures[ch.channel_id] = {
      x: -span / 2,
      y: startY + idx * 70,
      angle: 0,
      reversed: false,
    };
  });

  saveFixtures();
  if (onComplete) onComplete('stacked');
}

export function getFixtureAt(wx, wy) {
  const hitRadius = 24 / store.camera.zoom;
  const hitRadiusSq = hitRadius * hitRadius;

  if (store.isUniverseMode && store.universe && store.universe.fixtures) {
    const METER_SCALE = 65.0;
    for (let i = store.universe.fixtures.length - 1; i >= 0; i--) {
      const f = store.universe.fixtures[i];
      if (!f.points) continue;
      for (let j = 0; j < f.points.length; j++) {
        const pt = f.points[j];
        const px = pt[0] * METER_SCALE;
        const py = -pt[1] * METER_SCALE;
        const d2 = (wx - px) * (wx - px) + (wy - py) * (wy - py);
        if (d2 <= hitRadiusSq) {
          return f.id;
        }
      }
    }
    return null;
  }

  for (let i = store.channels.length - 1; i >= 0; i--) {
    const ch = store.channels[i];
    const fix = store.fixtures[ch.channel_id];
    if (!fix) continue;

    const rad = (fix.angle * Math.PI) / 180;
    const dx = Math.cos(rad);
    const dy = Math.sin(rad);

    const pvx = wx - fix.x;
    const pvy = wy - fix.y;
    const t = Math.max(0, Math.min(FIXTURE_SPAN_WORLD, pvx * dx + pvy * dy));
    const nearX = fix.x + t * dx;
    const nearY = fix.y + t * dy;

    const distSq = (wx - nearX) * (wx - nearX) + (wy - nearY) * (wy - nearY);
    if (distSq <= hitRadius * hitRadius) {
      return ch.channel_id;
    }
  }
  return null;
}

export function computeMagneticSnap(channelId, targetX, targetY) {
  const snapDist = 20 / store.camera.zoom;
  const curFix = store.fixtures[channelId];
  if (!curFix) return { x: targetX, y: targetY };

  const curRad = (curFix.angle * Math.PI) / 180;
  const curEndX = targetX + Math.cos(curRad) * FIXTURE_SPAN_WORLD;
  const curEndY = targetY + Math.sin(curRad) * FIXTURE_SPAN_WORLD;

  for (const otherCh of store.channels) {
    if (otherCh.channel_id === channelId) continue;
    const otherFix = store.fixtures[otherCh.channel_id];
    if (!otherFix) continue;

    const otherRad = (otherFix.angle * Math.PI) / 180;
    const otherEndX = otherFix.x + Math.cos(otherRad) * FIXTURE_SPAN_WORLD;
    const otherEndY = otherFix.y + Math.sin(otherRad) * FIXTURE_SPAN_WORLD;

    const testPoints = [
      { x: otherFix.x, y: otherFix.y },
      { x: otherEndX, y: otherEndY },
    ];

    for (const pt of testPoints) {
      if (Math.hypot(targetX - pt.x, targetY - pt.y) < snapDist) {
        return { x: pt.x, y: pt.y };
      }
      if (Math.hypot(curEndX - pt.x, curEndY - pt.y) < snapDist) {
        return {
          x: pt.x - Math.cos(curRad) * FIXTURE_SPAN_WORLD,
          y: pt.y - Math.sin(curRad) * FIXTURE_SPAN_WORLD,
        };
      }
    }
  }

  return { x: targetX, y: targetY };
}

export function rotateFixture(channelId) {
  const fix = store.fixtures[channelId];
  if (!fix) return;
  fix.angle = (fix.angle + 90) % 360;
  saveFixtures();
}

export function flipFixture(channelId) {
  const fix = store.fixtures[channelId];
  if (!fix) return;
  fix.reversed = !fix.reversed;
  saveFixtures();
}
