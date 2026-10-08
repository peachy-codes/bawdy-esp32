/**
 * Live Telemetry & Integrity HUD Updater Module
 */

export function createTelemetryManager(elements) {
  const { hudFps, hudPps, hudKbps, hudJitter, hudIntegrityBadge, statusDot } = elements;

  return {
    setConnected(connected) {
      if (connected) {
        statusDot.classList.add('active');
      } else {
        statusDot.classList.remove('active');
      }
    },

    update(telemetry) {
      if (telemetry.fps !== undefined) hudFps.textContent = telemetry.fps.toFixed(1);
      if (telemetry.pps !== undefined) hudPps.textContent = Math.round(telemetry.pps);
      if (telemetry.kbps !== undefined) hudKbps.textContent = `${telemetry.kbps.toFixed(1)} KB/s`;
      if (telemetry.jitter_us !== undefined) hudJitter.textContent = `${Math.round(telemetry.jitter_us)} µs`;

      if (telemetry.integrity_status) {
        hudIntegrityBadge.className = 'integrity-tag';
        if (telemetry.integrity_status === 'healthy') {
          hudIntegrityBadge.classList.add('tag-healthy');
          hudIntegrityBadge.textContent = '● Healthy';
        } else if (telemetry.integrity_status === 'sequence_gap') {
          hudIntegrityBadge.classList.add('tag-gap');
          hudIntegrityBadge.textContent = '▲ Gap / Out-of-Order';
        } else {
          hudIntegrityBadge.classList.add('tag-torn');
          hudIntegrityBadge.textContent = '✖ Torn Frame';
        }
        hudIntegrityBadge.title = telemetry.integrity_message || "";
      }
    }
  };
}
