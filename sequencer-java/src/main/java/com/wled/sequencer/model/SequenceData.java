package com.wled.sequencer.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.List;

/**
 * Top-level sequence document representing a choreographed lighting show.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class SequenceData {
    private String name = "Untitled Sequence";
    private String description = "";
    private String author = "";

    @JsonProperty("loop_mode")
    private String loopMode = "infinite";

    @JsonProperty("loop_count")
    private int loopCount = 1;

    @JsonProperty("time_dilation")
    private double timeDilation = 1.0;

    private List<SequenceStep> steps = new ArrayList<>();

    public SequenceData() {}

    public SequenceData(String name) {
        this.name = name;
    }

    public void normalize() {
        if (steps == null) {
            steps = new ArrayList<>();
        }
        double runningTime = 0.0;
        for (SequenceStep step : steps) {
            step.normalize();
            if (step.getStartTimeSec() == 0.0 && runningTime > 0.0 && steps.indexOf(step) > 0) {
                step.setStartTimeSec(runningTime);
            }
            runningTime = step.getStopTimeSec();
        }
    }

    @JsonProperty("total_duration")
    public double getTotalDuration() {
        if (steps == null || steps.isEmpty()) {
            return 0.0;
        }
        double maxStop = 0.0;
        for (SequenceStep s : steps) {
            double stop = s.getStopTimeSec();
            if (stop > maxStop) {
                maxStop = stop;
            }
        }
        return Math.round(maxStop * 1000.0) / 1000.0;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name != null && !name.isBlank() ? name : "Untitled Sequence";
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description != null ? description : "";
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author != null ? author : "";
    }

    public String getLoopMode() {
        return loopMode;
    }

    public void setLoopMode(String loopMode) {
        this.loopMode = loopMode != null ? loopMode : "infinite";
    }

    public int getLoopCount() {
        return loopCount;
    }

    public void setLoopCount(int loopCount) {
        this.loopCount = Math.max(1, loopCount);
    }

    public double getTimeDilation() {
        return timeDilation;
    }

    public void setTimeDilation(double timeDilation) {
        this.timeDilation = Math.max(0.1, Math.min(10.0, timeDilation));
    }

    public List<SequenceStep> getSteps() {
        if (steps == null) {
            steps = new ArrayList<>();
        }
        return steps;
    }

    public void setSteps(List<SequenceStep> steps) {
        this.steps = steps != null ? new ArrayList<>(steps) : new ArrayList<>();
    }
}
