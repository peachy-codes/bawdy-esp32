package com.wled.sequencer.model;

/**
 * Summary DTO for listing available sequences.
 */
public record SequenceSummary(
        String filename,
        String name,
        String description,
        int stepCount,
        double totalDuration,
        String loopMode
) {}
