package com.wled.sequencer.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Represents a single timed visual lighting cue block across layers 0..9.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class SequenceStep implements Cloneable {
    private String id;
    private String name = "Cue";
    private String section = "Main";

    @JsonProperty("target_layer")
    private int targetLayer = 0;

    @JsonProperty("start_time_sec")
    private double startTimeSec = 0.0;

    @JsonProperty("duration_sec")
    private double durationSec = 4.0;

    @JsonProperty("hold_duration_sec")
    private Double legacyHoldDurationSec;

    @JsonProperty("pattern_id")
    private String patternId = "rainbow";

    @JsonProperty("primary_color")
    private String primaryColor = "#FF0000";

    private String palette; // optional null

    private double speed = 1.0;
    private double brightness = 1.0;

    @JsonProperty("blend_mode")
    private String blendMode = "OVERWRITE";

    @JsonProperty("fixture_group")
    private String fixtureGroup = "all";

    private List<Integer> channels; // null = all channels

    @JsonProperty("target_opacity")
    private double targetOpacity = 1.0;

    @JsonProperty("transition_sec")
    private double transitionSec = 1.0;

    @JsonProperty("fade_out_sec")
    private double fadeOutSec = 0.5;

    public SequenceStep() {
        this.id = "step_" + System.currentTimeMillis();
    }

    public SequenceStep(String id, String name, String section, int targetLayer,
                        double startTimeSec, double durationSec, String patternId) {
        this.id = id;
        this.name = name;
        this.section = section;
        setTargetLayer(targetLayer);
        setStartTimeSec(startTimeSec);
        setDurationSec(durationSec);
        this.patternId = patternId;
    }

    /**
     * Called after deserialization to ensure legacy hold_duration_sec is migrated.
     */
    public void normalize() {
        if (legacyHoldDurationSec != null && durationSec == 4.0 && legacyHoldDurationSec > 0) {
            this.durationSec = legacyHoldDurationSec;
        }
        if (section == null || section.isBlank()) {
            this.section = "Main";
        }
    }

    @JsonProperty("stop_time_sec")
    public double getStopTimeSec() {
        return Math.round((startTimeSec + durationSec) * 1000.0) / 1000.0;
    }

    // Getters and Setters with validation

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name != null ? name : "Cue";
    }

    public String getSection() {
        return section;
    }

    public void setSection(String section) {
        this.section = section != null && !section.isBlank() ? section : "Main";
    }

    public int getTargetLayer() {
        return targetLayer;
    }

    public void setTargetLayer(int targetLayer) {
        if (targetLayer < 0 || targetLayer > 9) {
            throw new IllegalArgumentException("Target layer must be between 0 and 9, got: " + targetLayer);
        }
        this.targetLayer = targetLayer;
    }

    public double getStartTimeSec() {
        return startTimeSec;
    }

    public void setStartTimeSec(double startTimeSec) {
        this.startTimeSec = Math.max(0.0, startTimeSec);
    }

    public double getDurationSec() {
        return durationSec;
    }

    public void setDurationSec(double durationSec) {
        this.durationSec = Math.max(0.1, durationSec);
    }

    public void setStopTimeSec(double stopTimeSec) {
        double dur = stopTimeSec - this.startTimeSec;
        this.durationSec = Math.max(0.1, Math.round(dur * 1000.0) / 1000.0);
    }

    public String getPatternId() {
        return patternId;
    }

    public void setPatternId(String patternId) {
        this.patternId = patternId != null ? patternId : "none";
    }

    public String getPrimaryColor() {
        return primaryColor;
    }

    public void setPrimaryColor(String primaryColor) {
        this.primaryColor = primaryColor != null ? primaryColor : "#FF0000";
    }

    public String getPalette() {
        return palette;
    }

    public void setPalette(String palette) {
        this.palette = palette != null && !palette.isBlank() ? palette : null;
    }

    public double getSpeed() {
        return speed;
    }

    public void setSpeed(double speed) {
        this.speed = Math.max(0.1, speed);
    }

    public double getBrightness() {
        return brightness;
    }

    public void setBrightness(double brightness) {
        this.brightness = Math.max(0.0, Math.min(1.0, brightness));
    }

    public String getBlendMode() {
        return blendMode;
    }

    public void setBlendMode(String blendMode) {
        this.blendMode = blendMode != null ? blendMode.toUpperCase() : "OVERWRITE";
    }

    public String getFixtureGroup() {
        return fixtureGroup != null ? fixtureGroup : "all";
    }

    public void setFixtureGroup(String fixtureGroup) {
        this.fixtureGroup = fixtureGroup != null && !fixtureGroup.isBlank() ? fixtureGroup.toLowerCase() : "all";
    }

    public List<Integer> getChannels() {
        return channels;
    }

    public void setChannels(List<Integer> channels) {
        this.channels = channels != null && !channels.isEmpty() ? new ArrayList<>(channels) : null;
    }

    public double getTargetOpacity() {
        return targetOpacity;
    }

    public void setTargetOpacity(double targetOpacity) {
        this.targetOpacity = Math.max(0.0, Math.min(1.0, targetOpacity));
    }

    public double getTransitionSec() {
        return transitionSec;
    }

    public void setTransitionSec(double transitionSec) {
        this.transitionSec = Math.max(0.0, transitionSec);
    }

    public double getFadeOutSec() {
        return fadeOutSec;
    }

    public void setFadeOutSec(double fadeOutSec) {
        this.fadeOutSec = Math.max(0.0, fadeOutSec);
    }

    @Override
    public SequenceStep clone() {
        try {
            SequenceStep copy = (SequenceStep) super.clone();
            copy.id = "step_" + System.currentTimeMillis();
            if (this.channels != null) {
                copy.channels = new ArrayList<>(this.channels);
            }
            return copy;
        } catch (CloneNotSupportedException e) {
            throw new AssertionError(e);
        }
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof SequenceStep that)) return false;
        return targetLayer == that.targetLayer &&
                Double.compare(that.startTimeSec, startTimeSec) == 0 &&
                Double.compare(that.durationSec, durationSec) == 0 &&
                Objects.equals(id, that.id) &&
                Objects.equals(name, that.name) &&
                Objects.equals(section, that.section) &&
                Objects.equals(patternId, that.patternId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name, section, targetLayer, startTimeSec, durationSec, patternId);
    }
}
