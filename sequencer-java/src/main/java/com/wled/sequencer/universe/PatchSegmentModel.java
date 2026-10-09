package com.wled.sequencer.universe;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Maps a contiguous segment of fixture pixels to a specific hardware controller and channel.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class PatchSegmentModel {
    @JsonProperty("fixture_id")
    private String fixtureId;

    @JsonProperty("pixel_start")
    private int pixelStart = 0;

    @JsonProperty("pixel_count")
    private int pixelCount = 0;

    @JsonProperty("controller_id")
    private String controllerId;

    @JsonProperty("channel_index")
    private int channelIndex = 0;

    @JsonProperty("port_offset")
    private int portOffset = 0;

    private boolean reversed = false;

    @JsonProperty("color_order")
    private String colorOrder = "GRB";

    private String protocol = "ddp";

    @JsonProperty("brightness_scale")
    private double brightnessScale = 1.0;

    public PatchSegmentModel() {}

    public String getFixtureId() {
        return fixtureId;
    }

    public void setFixtureId(String fixtureId) {
        this.fixtureId = fixtureId;
    }

    public int getPixelStart() {
        return pixelStart;
    }

    public void setPixelStart(int pixelStart) {
        this.pixelStart = pixelStart;
    }

    public int getPixelCount() {
        return pixelCount;
    }

    public void setPixelCount(int pixelCount) {
        this.pixelCount = pixelCount;
    }

    public String getControllerId() {
        return controllerId;
    }

    public void setControllerId(String controllerId) {
        this.controllerId = controllerId;
    }

    public int getChannelIndex() {
        return channelIndex;
    }

    public void setChannelIndex(int channelIndex) {
        this.channelIndex = channelIndex;
    }

    public int getPortOffset() {
        return portOffset;
    }

    public void setPortOffset(int portOffset) {
        this.portOffset = portOffset;
    }

    public boolean isReversed() {
        return reversed;
    }

    public void setReversed(boolean reversed) {
        this.reversed = reversed;
    }

    public String getColorOrder() {
        return colorOrder;
    }

    public void setColorOrder(String colorOrder) {
        this.colorOrder = colorOrder;
    }

    public String getProtocol() {
        return protocol;
    }

    public void setProtocol(String protocol) {
        this.protocol = protocol;
    }

    public double getBrightnessScale() {
        return brightnessScale;
    }

    public void setBrightnessScale(double brightnessScale) {
        this.brightnessScale = brightnessScale;
    }
}
