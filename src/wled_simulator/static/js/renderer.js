/**
 * Stage Canvas Renderer Module
 * Dedicated 60 FPS drawing loop with zero DOM thrashing.
 * Supports both legacy single-channel controllers and 20-node Spatial Universes.
 */

import { store } from './state.js';
import { worldToScreen, METER_SCALE } from './camera.js';
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

  // 2. Blueprint Architectural Floorplan (if enabled)
  if (store.isUniverseMode && store.blueprint.visible) {
    drawBlueprint(ctx, containerRect);
  }

  // 3. Render Fixtures
  if (store.isUniverseMode && store.universe && store.universe.fixtures) {
    drawUniverseFixtures(ctx, containerRect);
  } else {
    // Single-device fallback mode
    store.channels.forEach(ch => {
      drawSingleChannelFixture(ctx, ch, containerRect);
    });
  }
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

  // Origin Marker
  if (origin.x >= 0 && origin.x <= W && origin.y >= 0 && origin.y <= H) {
    ctx.fillStyle = 'rgba(0, 180, 216, 0.35)';
    ctx.beginPath();
    ctx.arc(origin.x, origin.y, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
    ctx.font = '9px var(--font-mono)';
    ctx.fillText('(0,0)', origin.x + 8, origin.y - 6);
  }
}

function drawBlueprint(ctx, containerRect) {
  const alpha = store.blueprint.opacity || 0.35;
  const zoom = store.camera.zoom;

  ctx.save();

  // If user uploaded a custom blueprint image
  if (store.blueprint.image) {
    ctx.globalAlpha = alpha;
    const origin = worldToScreen(0, 0, containerRect);
    const img = store.blueprint.image;
    const iw = img.width * zoom;
    const ih = img.height * zoom;
    ctx.drawImage(img, origin.x - iw / 2, origin.y - ih / 2, iw, ih);
    ctx.restore();
    return;
  }

  // Built-in Architectural Blueprint CAD Overlay
  const m2w = (m) => m * METER_SCALE;

  const toScr = (mx, my) => worldToScreen(m2w(mx), -m2w(my), containerRect);

  ctx.strokeStyle = `rgba(0, 180, 216, ${alpha * 0.45})`;
  ctx.fillStyle = `rgba(0, 180, 216, ${alpha * 0.05})`;
  ctx.lineWidth = Math.max(1, 1.5 * zoom);

  // Outer Venue Walls (-7m to +7m X, -7m to +8m Y)
  const wallTL = toScr(-7.2, 7.8);
  const wallBR = toScr(7.2, -7.2);
  ctx.beginPath();
  ctx.rect(wallTL.x, wallTL.y, wallBR.x - wallTL.x, wallBR.y - wallTL.y);
  ctx.stroke();
  ctx.fill();

  // Stage Deck (-6.5m to +6.5m X, +2.5m to +7.5m Y)
  const stageTL = toScr(-6.5, 7.5);
  const stageBR = toScr(6.5, 2.5);
  ctx.fillStyle = `rgba(16, 23, 34, ${alpha * 0.7})`;
  ctx.fillRect(stageTL.x, stageTL.y, stageBR.x - stageTL.x, stageBR.y - stageTL.y);

  ctx.strokeStyle = `rgba(245, 158, 11, ${alpha * 0.5})`;
  ctx.lineWidth = Math.max(1.5, 2 * zoom);
  ctx.strokeRect(stageTL.x, stageTL.y, stageBR.x - stageTL.x, stageBR.y - stageTL.y);

  // Stage Front Lip Edge (Thick line at Y = 2.5)
  const lipL = toScr(-6.5, 2.5);
  const lipR = toScr(6.5, 2.5);
  ctx.beginPath();
  ctx.moveTo(lipL.x, lipL.y);
  ctx.lineTo(lipR.x, lipR.y);
  ctx.strokeStyle = `rgba(245, 158, 11, ${alpha * 0.9})`;
  ctx.lineWidth = Math.max(2, 3 * zoom);
  ctx.stroke();

  // DJ Performance Booth / Riser (-1.8m to +1.8m X, +2.8m to +3.6m Y)
  const djTL = toScr(-1.8, 3.6);
  const djBR = toScr(1.8, 2.8);
  ctx.fillStyle = `rgba(30, 41, 59, ${alpha * 0.9})`;
  ctx.fillRect(djTL.x, djTL.y, djBR.x - djTL.x, djBR.y - djTL.y);
  ctx.strokeStyle = `rgba(0, 180, 216, ${alpha * 0.6})`;
  ctx.lineWidth = 1;
  ctx.strokeRect(djTL.x, djTL.y, djBR.x - djTL.x, djBR.y - djTL.y);

  // FOH Audio/Lighting Tech Console Booth (-1.8m to +1.8m X, -3.2m to -4.2m Y)
  const fohTL = toScr(-1.8, -3.2);
  const fohBR = toScr(1.8, -4.2);
  ctx.fillStyle = `rgba(30, 41, 59, ${alpha * 0.8})`;
  ctx.fillRect(fohTL.x, fohTL.y, fohBR.x - fohTL.x, fohBR.y - fohTL.y);
  ctx.strokeStyle = `rgba(148, 163, 184, ${alpha * 0.5})`;
  ctx.strokeRect(fohTL.x, fohTL.y, fohBR.x - fohTL.x, fohBR.y - fohTL.y);

  // Bar Counter (-5.8m to -1.2m X, -4.8m to -5.6m Y)
  const barTL = toScr(-5.8, -4.8);
  const barBR = toScr(-1.2, -5.6);
  ctx.fillStyle = `rgba(30, 41, 59, ${alpha * 0.7})`;
  ctx.fillRect(barTL.x, barTL.y, barBR.x - barTL.x, barBR.y - barTL.y);
  ctx.strokeStyle = `rgba(148, 163, 184, ${alpha * 0.4})`;
  ctx.strokeRect(barTL.x, barTL.y, barBR.x - barTL.x, barBR.y - barTL.y);

  // Architectural Labels
  if (zoom > 0.4) {
    ctx.fillStyle = `rgba(148, 163, 184, ${alpha * 0.8})`;
    ctx.font = `600 ${Math.max(9, 11 * zoom)}px var(--font-mono)`;
    ctx.textAlign = 'center';

    const stageCenter = toScr(0, 5.0);
    ctx.fillText('MAIN PERFORMANCE STAGE', stageCenter.x, stageCenter.y);

    const djCenter = toScr(0, 3.2);
    ctx.fillText('DJ RISER', djCenter.x, djCenter.y);

    const fohCenter = toScr(0, -3.7);
    ctx.fillText('FOH CONSOLE', fohCenter.x, fohCenter.y);

    const barCenter = toScr(-3.5, -5.2);
    ctx.fillText('BAR & LOUNGE', barCenter.x, barCenter.y);
  }

  ctx.restore();
}

function drawUniverseFixtures(ctx, containerRect) {
  const zoom = store.camera.zoom;
  const pData = store.pixelData;
  const filter = store.activeGroupFilter;

  store.universe.fixtures.forEach(fixture => {
    const isSelected = (store.selectedFixtureId === fixture.id);
    const isMuted = (filter !== 'all' && fixture.group !== filter);

    ctx.save();
    if (isMuted) {
      ctx.globalAlpha = 0.22;
    }

    const ftype = fixture.type || 'linear_strip';
    if (ftype === 'matrix') {
      drawMatrixFixture(ctx, fixture, containerRect, isSelected, pData, zoom);
    } else if (ftype === 'bulb_string') {
      drawBulbStringFixture(ctx, fixture, containerRect, isSelected, pData, zoom);
    } else if (ftype === 'point') {
      drawPointFixture(ctx, fixture, containerRect, isSelected, pData, zoom);
    } else if (ftype === 'projector') {
      drawProjectorFixture(ctx, fixture, containerRect, isSelected, zoom);
    } else {
      drawLinearStripFixture(ctx, fixture, containerRect, isSelected, pData, zoom);
    }

    ctx.restore();
  });
}

function drawLinearStripFixture(ctx, fixture, containerRect, isSelected, pData, zoom) {
  if (!fixture.points || fixture.points.length === 0) return;

  const pts = fixture.points.map(p =>
    worldToScreen(p[0] * METER_SCALE, -p[1] * METER_SCALE, containerRect)
  );

  // 1. Aluminum Channel Extrusion Track
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 1; i < pts.length; i++) {
    ctx.lineTo(pts[i].x, pts[i].y);
  }
  ctx.strokeStyle = isSelected ? 'var(--accent)' : '#1e293b';
  ctx.lineWidth = Math.max(3, 5 * zoom);
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke();

  if (isSelected) {
    ctx.strokeStyle = 'rgba(0, 180, 216, 0.4)';
    ctx.lineWidth = Math.max(6, 10 * zoom);
    ctx.stroke();
  }

  // 2. Individual Addressable LED Diodes (Halo Bloom + Emitter Core)
  const pixelOffset = fixture.pixel_offset || 0;
  const diodeRadius = Math.max(1.3, 2.4 * zoom);
  const glowRadius = diodeRadius * 2.5;

  for (let i = 0; i < pts.length; i++) {
    const pt = pts[i];
    const byteOff = (pixelOffset + i) * 3;
    let r = 10, g = 14, b = 20, active = false;

    if (pData && byteOff + 2 < pData.length) {
      const pr = pData[byteOff];
      const pg = pData[byteOff + 1];
      const pb = pData[byteOff + 2];
      if (pr > 5 || pg > 5 || pb > 5) {
        r = pr; g = pg; b = pb;
        active = true;
      }
    }

    if (active) {
      // Bloom Halo
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, glowRadius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.32)`;
      ctx.fill();

      // Saturated Core
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, diodeRadius, 0, Math.PI * 2);
      ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, diodeRadius * 0.7, 0, Math.PI * 2);
      ctx.fillStyle = '#0a0f18';
      ctx.fill();
    }
  }

  // 3. Start Tag Pill
  if (pts.length > 0 && zoom > 0.45) {
    drawTagPill(ctx, pts[0].x, pts[0].y, fixture.name || fixture.id, isSelected);
  }
}

function drawBulbStringFixture(ctx, fixture, containerRect, isSelected, pData, zoom) {
  if (!fixture.points || fixture.points.length === 0) return;

  const pts = fixture.points.map(p =>
    worldToScreen(p[0] * METER_SCALE, -p[1] * METER_SCALE, containerRect)
  );

  // 1. Suspension Cable (Smooth catenary curve)
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 1; i < pts.length; i++) {
    ctx.lineTo(pts[i].x, pts[i].y);
  }
  ctx.strokeStyle = isSelected ? 'var(--accent)' : '#475569';
  ctx.lineWidth = Math.max(1.2, 2 * zoom);
  ctx.stroke();

  // 2. Hanging Festoon Bulbs
  const pixelOffset = fixture.pixel_offset || 0;
  const bulbRadius = Math.max(3.2, 5.5 * zoom);
  const glowRadius = bulbRadius * 2.8;

  for (let i = 0; i < pts.length; i++) {
    const pt = pts[i];
    const byteOff = (pixelOffset + i) * 3;
    let r = 20, g = 18, b = 14, active = false;

    if (pData && byteOff + 2 < pData.length) {
      const pr = pData[byteOff];
      const pg = pData[byteOff + 1];
      const pb = pData[byteOff + 2];
      if (pr > 5 || pg > 5 || pb > 5) {
        r = pr; g = pg; b = pb;
        active = true;
      }
    }

    // Socket Stem
    const dropY = pt.y + 4 * zoom;
    ctx.beginPath();
    ctx.moveTo(pt.x, pt.y);
    ctx.lineTo(pt.x, dropY);
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    const bulbCenterY = dropY + bulbRadius;

    if (active) {
      // Warm Bloom Diffusion
      ctx.beginPath();
      ctx.arc(pt.x, bulbCenterY, glowRadius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.38)`;
      ctx.fill();

      // Translucent Glass Envelope
      ctx.beginPath();
      ctx.arc(pt.x, bulbCenterY, bulbRadius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.85)`;
      ctx.fill();
      ctx.strokeStyle = `rgb(${r}, ${g}, ${b})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Filament Core Highlight
      ctx.beginPath();
      ctx.arc(pt.x, bulbCenterY, bulbRadius * 0.4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
    } else {
      // Unlit Edison Glass Globe
      ctx.beginPath();
      ctx.arc(pt.x, bulbCenterY, bulbRadius, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(22, 32, 46, 0.7)';
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      ctx.fill();
      ctx.stroke();
    }
  }

  if (pts.length > 0 && zoom > 0.45) {
    drawTagPill(ctx, pts[0].x, pts[0].y, fixture.name || fixture.id, isSelected);
  }
}

function drawMatrixFixture(ctx, fixture, containerRect, isSelected, pData, zoom) {
  if (!fixture.points || fixture.points.length === 0) return;

  const pts = fixture.points.map(p =>
    worldToScreen(p[0] * METER_SCALE, -p[1] * METER_SCALE, containerRect)
  );

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  pts.forEach(p => {
    minX = Math.min(minX, p.x);
    maxX = Math.max(maxX, p.x);
    minY = Math.min(minY, p.y);
    maxY = Math.max(maxY, p.y);
  });

  const pad = 10 * zoom;
  const boxX = minX - pad;
  const boxY = minY - pad;
  const boxW = (maxX - minX) + pad * 2;
  const boxH = (maxY - minY) + pad * 2;

  // 1. Panel Chassis Enclosure
  ctx.fillStyle = '#0a0f18';
  ctx.fillRect(boxX, boxY, boxW, boxH);

  ctx.strokeStyle = isSelected ? 'var(--accent)' : '#1e293b';
  ctx.lineWidth = isSelected ? 2 : 1;
  ctx.strokeRect(boxX, boxY, boxW, boxH);

  if (isSelected) {
    ctx.strokeStyle = 'rgba(0, 180, 216, 0.35)';
    ctx.lineWidth = 6;
    ctx.strokeRect(boxX - 2, boxY - 2, boxW + 4, boxH + 4);
  }

  // 2. Matrix LED Pixels
  const pixelOffset = fixture.pixel_offset || 0;
  const diodeRadius = Math.max(1.2, 2.2 * zoom);
  const glowRadius = diodeRadius * 2.2;

  for (let i = 0; i < pts.length; i++) {
    const pt = pts[i];
    const byteOff = (pixelOffset + i) * 3;
    let r = 10, g = 14, b = 20, active = false;

    if (pData && byteOff + 2 < pData.length) {
      const pr = pData[byteOff];
      const pg = pData[byteOff + 1];
      const pb = pData[byteOff + 2];
      if (pr > 5 || pg > 5 || pb > 5) {
        r = pr; g = pg; b = pb;
        active = true;
      }
    }

    if (active) {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, glowRadius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.28)`;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(pt.x, pt.y, diodeRadius, 0, Math.PI * 2);
      ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, diodeRadius * 0.75, 0, Math.PI * 2);
      ctx.fillStyle = '#101722';
      ctx.fill();
    }
  }

  // 3. Panel Header Label
  if (zoom > 0.4) {
    ctx.fillStyle = isSelected ? 'var(--accent)' : '#94a3b8';
    ctx.font = `bold ${Math.max(8, 10 * zoom)}px var(--font-mono)`;
    ctx.textAlign = 'center';
    ctx.fillText(`${fixture.name || fixture.id} (${fixture.rows}x${fixture.cols})`, boxX + boxW / 2, boxY - 4);
  }
}

function drawPointFixture(ctx, fixture, containerRect, isSelected, pData, zoom) {
  const loc = fixture.location || { x: 0, y: 0, z: 0 };
  const pt = worldToScreen(loc.x * METER_SCALE, -loc.y * METER_SCALE, containerRect);

  const pixelOffset = fixture.pixel_offset || 0;
  const byteOff = pixelOffset * 3;
  let r = 20, g = 20, b = 20, active = false;

  if (pData && byteOff + 2 < pData.length) {
    const pr = pData[byteOff];
    const pg = pData[byteOff + 1];
    const pb = pData[byteOff + 2];
    if (pr > 5 || pg > 5 || pb > 5) {
      r = pr; g = pg; b = pb;
      active = true;
    }
  }

  // 1. Ambient Floor Wash Diffusion (Large radial light pool)
  const washRadius = Math.max(25, 45 * zoom);
  if (active) {
    const grad = ctx.createRadialGradient(pt.x, pt.y, 0, pt.x, pt.y, washRadius);
    grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.45)`);
    grad.addColorStop(0.5, `rgba(${r}, ${g}, ${b}, 0.18)`);
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.beginPath();
    ctx.arc(pt.x, pt.y, washRadius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();
  }

  // 2. Cast Iron Lamp Base
  const baseRadius = Math.max(4, 7 * zoom);
  ctx.beginPath();
  ctx.arc(pt.x, pt.y, baseRadius, 0, Math.PI * 2);
  ctx.fillStyle = '#0f1722';
  ctx.strokeStyle = isSelected ? 'var(--accent)' : '#334155';
  ctx.lineWidth = isSelected ? 2 : 1;
  ctx.fill();
  ctx.stroke();

  // 3. Central Emitter Globe
  const coreRadius = Math.max(2.5, 4.5 * zoom);
  ctx.beginPath();
  ctx.arc(pt.x, pt.y, coreRadius, 0, Math.PI * 2);
  ctx.fillStyle = active ? `rgb(${r}, ${g}, ${b})` : '#1e293b';
  ctx.fill();

  if (zoom > 0.45) {
    drawTagPill(ctx, pt.x, pt.y - baseRadius - 8, fixture.name || fixture.id, isSelected);
  }
}

function drawProjectorFixture(ctx, fixture, containerRect, isSelected, zoom) {
  const tl = fixture.top_left || { x: -2, y: 5, z: 2 };
  const br = fixture.bottom_right || { x: 2, y: 5, z: 0 };

  const p1 = worldToScreen(tl.x * METER_SCALE, -tl.y * METER_SCALE, containerRect);
  const p2 = worldToScreen(br.x * METER_SCALE, -br.y * METER_SCALE, containerRect);

  const x = Math.min(p1.x, p2.x);
  const y = Math.min(p1.y, p2.y);
  const w = Math.abs(p2.x - p1.x);
  const h = Math.abs(p2.y - p1.y);

  ctx.save();
  ctx.setLineDash([4 * zoom, 4 * zoom]);
  ctx.strokeStyle = isSelected ? 'var(--accent)' : 'rgba(0, 180, 216, 0.4)';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(x, y, w, h);

  ctx.fillStyle = 'rgba(0, 180, 216, 0.05)';
  ctx.fillRect(x, y, w, h);

  if (zoom > 0.4) {
    ctx.setLineDash([]);
    ctx.fillStyle = 'rgba(0, 180, 216, 0.8)';
    ctx.font = `bold ${Math.max(8, 10 * zoom)}px var(--font-mono)`;
    ctx.textAlign = 'center';
    ctx.fillText('PROJECTOR CANVAS (1920x1080)', x + w / 2, y + h / 2);
  }
  ctx.restore();
}

function drawTagPill(ctx, x, y, text, isSelected) {
  ctx.save();
  ctx.font = 'bold 9px var(--font-mono)';
  const metrics = ctx.measureText(text);
  const pw = metrics.width + 10;
  const ph = 14;

  ctx.fillStyle = isSelected ? 'var(--accent)' : 'rgba(15, 23, 34, 0.9)';
  ctx.beginPath();
  ctx.roundRect(x - pw / 2, y - ph / 2, pw, ph, 3);
  ctx.fill();

  ctx.strokeStyle = isSelected ? '#ffffff' : '#334155';
  ctx.lineWidth = 1;
  ctx.stroke();

  ctx.fillStyle = isSelected ? '#000000' : '#cbd5e1';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, x, y);
  ctx.restore();
}

function drawSingleChannelFixture(ctx, channel, containerRect) {
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

  // Extrusion Track
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

  // Channel Tag Pill
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

  // Direction Indicator
  ctx.fillStyle = '#475569';
  ctx.font = `${Math.max(7, 9 * zoom)}px var(--font-mono)`;
  ctx.textAlign = 'right';
  ctx.fillText(fix.reversed ? '◀ REV' : 'FWD ▶', fixtureLen - 6 * zoom, 0);

  // Addressable Diodes
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
          r = pr; g = pg; b = pb;
          isActive = true;
        }
      }

      const diodeX = startLedOffset + i * step;

      if (isActive) {
        ctx.beginPath();
        ctx.arc(diodeX, 0, glowRadius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.28)`;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(diodeX, 0, diodeRadius, 0, Math.PI * 2);
        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        ctx.fill();
      } else {
        ctx.beginPath();
        ctx.arc(diodeX, 0, diodeRadius * 0.75, 0, Math.PI * 2);
        ctx.fillStyle = '#0a0f18';
        ctx.fill();
      }
    }
  }

  ctx.restore();
}
