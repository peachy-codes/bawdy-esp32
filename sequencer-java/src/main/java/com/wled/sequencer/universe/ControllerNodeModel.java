package com.wled.sequencer.universe;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.ArrayList;
import java.util.List;

/**
 * Represents a physical or simulated WLED controller node in the Cat6 multi-node network.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class ControllerNodeModel {
    private String id;
    private String name;
    private String ip = "127.0.0.1";
    private int port = 4048;
    private String protocol = "DDP";
    private int totalPixels = 0;
    private List<Integer> channels = new ArrayList<>();
    private List<String> fixtureIds = new ArrayList<>();
    private String status = "Synced (Cat6 0x41)";
    private long packetsSent = 0;
    private double latencyMs = 0.8;

    public ControllerNodeModel() {}

    public ControllerNodeModel(String id, String name, String ip, int port, String protocol) {
        this.id = id;
        this.name = name;
        this.ip = ip;
        this.port = port;
        this.protocol = protocol;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name != null ? name : id;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getIp() {
        return ip;
    }

    public void setIp(String ip) {
        this.ip = ip;
    }

    public int getPort() {
        return port;
    }

    public void setPort(int port) {
        this.port = port;
    }

    public String getProtocol() {
        return protocol;
    }

    public void setProtocol(String protocol) {
        this.protocol = protocol;
    }

    public int getTotalPixels() {
        return totalPixels;
    }

    public void setTotalPixels(int totalPixels) {
        this.totalPixels = totalPixels;
    }

    public List<Integer> getChannels() {
        return channels;
    }

    public void setChannels(List<Integer> channels) {
        this.channels = channels != null ? channels : new ArrayList<>();
    }

    public List<String> getFixtureIds() {
        return fixtureIds;
    }

    public void setFixtureIds(List<String> fixtureIds) {
        this.fixtureIds = fixtureIds != null ? fixtureIds : new ArrayList<>();
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public long getPacketsSent() {
        return packetsSent;
    }

    public void setPacketsSent(long packetsSent) {
        this.packetsSent = packetsSent;
    }

    public double getLatencyMs() {
        return latencyMs;
    }

    public void setLatencyMs(double latencyMs) {
        this.latencyMs = latencyMs;
    }
}
