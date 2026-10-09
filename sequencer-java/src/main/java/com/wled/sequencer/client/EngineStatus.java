package com.wled.sequencer.client;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Telemetry status DTO returned by Lighting Engine REST Daemon /api/status.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class EngineStatus {
    private String status = "offline";
    private boolean running = false;

    @JsonProperty("target_fps")
    private double targetFps = 30.0;

    @JsonProperty("actual_fps")
    private double actualFps = 0.0;

    private long tick = 0;

    @JsonProperty("master_brightness")
    private double masterBrightness = 1.0;

    public EngineStatus() {}

    public EngineStatus(String status, boolean running, double actualFps) {
        this.status = status;
        this.running = running;
        this.actualFps = actualFps;
    }

    public String getStatus() {
        return status;
    }

    public boolean isRunning() {
        return running;
    }

    public double getTargetFps() {
        return targetFps;
    }

    public double getActualFps() {
        return actualFps;
    }

    public long getTick() {
        return tick;
    }

    public double getMasterBrightness() {
        return masterBrightness;
    }
}
