package com.wled.sequencer.universe;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Represents a 3D Axis-Aligned Bounding Box enclosing physical fixtures in the venue.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class BoundingBox3D {
    @JsonProperty("min_x")
    private double minX = -6.5;

    @JsonProperty("min_y")
    private double minY = -6.5;

    @JsonProperty("min_z")
    private double minZ = 0.0;

    @JsonProperty("max_x")
    private double maxX = 6.5;

    @JsonProperty("max_y")
    private double maxY = 7.0;

    @JsonProperty("max_z")
    private double maxZ = 4.5;

    private double width = 13.0;
    private double height = 13.5;
    private double depth = 4.5;

    public BoundingBox3D() {}

    public BoundingBox3D(double minX, double minY, double minZ, double maxX, double maxY, double maxZ) {
        this.minX = minX;
        this.minY = minY;
        this.minZ = minZ;
        this.maxX = maxX;
        this.maxY = maxY;
        this.maxZ = maxZ;
        this.width = Math.max(0.1, maxX - minX);
        this.height = Math.max(0.1, maxY - minY);
        this.depth = Math.max(0.1, maxZ - minZ);
    }

    public double getMinX() {
        return minX;
    }

    public void setMinX(double minX) {
        this.minX = minX;
    }

    public double getMinY() {
        return minY;
    }

    public void setMinY(double minY) {
        this.minY = minY;
    }

    public double getMinZ() {
        return minZ;
    }

    public void setMinZ(double minZ) {
        this.minZ = minZ;
    }

    public double getMaxX() {
        return maxX;
    }

    public void setMaxX(double maxX) {
        this.maxX = maxX;
    }

    public double getMaxY() {
        return maxY;
    }

    public void setMaxY(double maxY) {
        this.maxY = maxY;
    }

    public double getMaxZ() {
        return maxZ;
    }

    public void setMaxZ(double maxZ) {
        this.maxZ = maxZ;
    }

    public double getWidth() {
        return width > 0 ? width : (maxX - minX);
    }

    public void setWidth(double width) {
        this.width = width;
    }

    public double getHeight() {
        return height > 0 ? height : (maxY - minY);
    }

    public void setHeight(double height) {
        this.height = height;
    }

    public double getDepth() {
        return depth > 0 ? depth : (maxZ - minZ);
    }

    public void setDepth(double depth) {
        this.depth = depth;
    }

    public double getCenterX() {
        return (minX + maxX) / 2.0;
    }

    public double getCenterY() {
        return (minY + maxY) / 2.0;
    }

    public double getCenterZ() {
        return (minZ + maxZ) / 2.0;
    }
}
