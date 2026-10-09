package com.wled.sequencer.player;

import java.util.Set;

/**
 * Listener interface for playback events emitted by TimelinePlayer.
 */
public interface PlayerListener {
    void onPlaybackTick(double elapsedSec, double totalDurationSec, int activeCount);
    void onActiveCuesChanged(Set<String> activeCueIds);
    void onPlaybackStateChanged(boolean isPlaying, boolean isPaused);
    default void onLoopIteration(int currentIteration, int maxIterations) {}
}
