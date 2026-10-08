/**
 * Stage Canvas Renderer Module
 * Dedicated 60 FPS drawing loop with zero DOM thrashing.
 */

import { store } from './state.js';
import { worldToScreen } from './camera.js';
import { FIXTURE_SPAN_WORLD } from './fixtures.js';

let animFramePending = false;

export function requestStageDraw(ctx, containerRect) {
  if (!animFramePending) {
    animFramePending = true;
    requestAnimationFrame(() => {
      animFramePending = false;
      renderStage(ctx, containerRect);
    });
  }
}

export function renderStage(ctx, containerRect) {
  const W = containerRect.width;
  const H = containerRect.height;

  ctx.clearRect(0, 0, W, H);

  // 1. World Grid
  drawGrid(ctx, containerRect);

  // 2. Physical LED Fixtures
  store.channels.forEach(ch => {
    drawFixture(ctx, ch, containerRect);
  });
}

function drawGrid(ctx, containerRect) {
  const W = containerRect.width;
  const H = containerRect.height;
  const zoom = store.camera.zoom;
  const gridSize = 50 * zoom;
  const origin = worldToScreen(0, 0, containerRect);

  const offsetX = ((origin.x % gridSize) + gridSize) % gridSize;
  const offsetY = ((origin.y % gridSize) + gridSize) % gridSize;

  ctx.beginPath();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
  ctx.lineWidth = 1;

  for (let x = offsetX; x < W; x += gridSize) {
    ctx.moveTo(x, 0);
    ctx.lineTo(x, H);
  }
  for (let y = offsetY; y < H; y += gridSize) {
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
  }
  ctx.stroke();

  // Subtle Origin Marker
  if (origin.x >= 0 && origin.x <= W && origin.y >= 0 && origin.y <= H) {
    ctx.fillStyle = 'rgba(0, 180, 216, 0.25)';
    ctx.beginPath();
    ctx.arc(origin.x, origin.y, 3, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawFixture(ctx, channel, containerRect) {
  const fix = store.fixtures[channel.channel_id];
  if (!fix) return;

  const isSelected = (channel.channel_id === store.selectedChannelId);
  const startScreen = worldToScreen(fix.x, fix.y, containerRect);
  const zoom = store.camera.zoom;
  const rad = (fix.angle * Math.PI) / 180;

  ctx.save();
  ctx.translate(startScreen.x, startScreen.y);
  ctx.rotate(rad);

  const fixtureLen = FIXTURE_SPAN_WORLD * zoom;
  const trackThickness = Math.max(16, 22 * zoom);
  const halfThick = trackThickness / 2;

  // A. Aluminum Channel Extrusion Track
  ctx.fillStyle = '#0f1722';
  ctx.strokeStyle = isSelected ? 'var(--accent)' : '#1e293b';
  ctx.lineWidth = isSelected ? 2 : 1;

  ctx.beginPath();
  ctx.roundRect(0, -halfThick, fixtureLen, trackThickness, 4);
  ctx.fill();
  ctx.stroke();

  if (isSelected) {
    ctx.strokeStyle = 'rgba(0, 180, 216, 0.3)';
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.roundRect(-2, -halfThick - 2, fixtureLen + 4, trackThickness + 4, 6);
    ctx.stroke();
  }

  // B. Channel Tag Pill at Fixture Head
  const tagW = Math.max(28, 36 * zoom);
  const tagH = Math.max(12, 16 * zoom);
  ctx.fillStyle = isSelected ? 'var(--accent)' : '#1e293b';
  ctx.beginPath();
  ctx.roundRect(4 * zoom, -tagH / 2, tagW, tagH, 3);
  ctx.fill();

  ctx.fillStyle = isSelected ? '#000' : '#94a3b8';
  ctx.font = `bold ${Math.max(8, 10 * zoom)}px var(--font-mono)`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(`CH${channel.channel_id}`, 4 * zoom + tagW / 2, 0);

  // C. Direction Indicator at Tail
  ctx.fillStyle = '#475569';
  ctx.font = `${Math.max(7, 9 * zoom)}px var(--font-mono)`;
  ctx.textAlign = 'right';
  ctx.fillText(fix.reversed ? '◀ REV' : 'FWD ▶', fixtureLen - 6 * zoom, 0);

  // D. Dual-Pass Addressable LED Diodes (Emitter Core + Bloom Glow)
  const ledCount = channel.length;
  if (ledCount > 0) {
    const startLedOffset = tagW + 10 * zoom;
    const availableLen = fixtureLen - startLedOffset - (16 * zoom);
    const step = availableLen / (ledCount - 1 || 1);
    const diodeRadius = Math.max(1.2, Math.min(step * 0.45, 5.0 * zoom));
    const glowRadius = diodeRadius * 2.4;

    const pData = store.pixelData;
    const startIdx = channel.start_index;

    for (let i = 0; i < ledCount; i++) {
      const logicalIdx = fix.reversed ? (ledCount - 1 - i) : i;
      const byteOffset = (startIdx + logicalIdx) * 3;

      let r = 10, g = 14, b = 20;
      let isActive = false;

      if (pData && (byteOffset + 2 < pData.length)) {
        const pr = pData[byteOffset];
        const pg = pData[byteOffset + 1];
        const pb = pData[byteOffset + 2];
        if (pr > 5 || pg > 5 || pb > 5) {
          r = pr;
          g = pg;
          b = pb;
          isActive = true;
        }
      }

      const diodeX = startLedOffset + i * step;

      if (isActive) {
        // Outer Bloom Halo
        ctx.beginPath();
        ctx.arc(diodeX, 0, glowRadius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.28)`;
        ctx.fill();

        // Inner Saturated Emitter Core
        ctx.beginPath();
        ctx.arc(diodeX, 0, diodeRadius, 0, Math.PI * 2);
        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        ctx.fill();
      } else {
        // Inactive Phosphor Diode
        ctx.beginPath();
        ctx.arc(diodeX, 0, diodeRadius * 0.75, 0, Math.PI * 2);
        ctx.fillStyle = '#0a0f18';
        ctx.fill();
      }
    }
  }

  ctx.restore();
}
