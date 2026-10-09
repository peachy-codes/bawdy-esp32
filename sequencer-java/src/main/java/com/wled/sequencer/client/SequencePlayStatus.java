package com.wled.sequencer.client;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record SequencePlayStatus(
        @JsonProperty("playing") boolean playing,
        @JsonProperty("paused") boolean paused,
        @JsonProperty("elapsed_time") double elapsedTime,
        @JsonProperty("total_duration") double totalDuration,
        @JsonProperty("active_cues") List<String> activeCues,
        @JsonProperty("loop_iteration") int loopIteration,
        @JsonProperty("sequence_name") String sequenceName
) {}
