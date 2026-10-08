/**
 * Camera & Coordinate Transformation Module
 */

import { store } from './state.js';

export function worldToScreen(wx, wy, containerRect) {
  const cx = containerRect.width / 2;
  const cy = containerRect.height / 2;
  return {
    x: cx + (wx - store.camera.x) * store.camera.zoom,
    y: cy + (wy - store.camera.y) * store.camera.zoom,
  };
}

export function screenToWorld(sx, sy, containerRect) {
  const cx = containerRect.width / 2;
  const cy = containerRect.height / 2;
  return {
    x: store.camera.x + (sx - cx) / store.camera.zoom,
    y: store.camera.y + (sy - cy) / store.camera.zoom,
  };
}

export function fitToView(containerRect) {
  if (store.channels.length === 0) return;

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  const fixtureSpan = 560;

  store.channels.forEach(ch => {
    const fix = store.fixtures[ch.channel_id];
    if (!fix) return;

    const rad = (fix.angle * Math.PI) / 180;
    const endX = fix.x + Math.cos(rad) * fixtureSpan;
    const endY = fix.y + Math.sin(rad) * fixtureSpan;

    minX = Math.min(minX, fix.x, endX);
    maxX = Math.max(maxX, fix.x, endX);
    minY = Math.min(minY, fix.y, endY);
    maxY = Math.max(maxY, fix.y, endY);
  });

  if (!isFinite(minX)) return;

  const totalW = (maxX - minX) + 160;
  const totalH = (maxY - minY) + 160;

  store.camera.x = (minX + maxX) / 2;
  store.camera.y = (minY + maxY) / 2;

  const scaleX = containerRect.width / totalW;
  const scaleY = containerRect.height / totalH;
  store.camera.zoom = Math.max(0.35, Math.min(Math.min(scaleX, scaleY), 1.8));
}
