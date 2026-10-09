package com.wled.sequencer.universe;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/**
 * Represents a 3D coordinate point (X, Y, Z) in meters within the venue coordinate space.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class Point3D {
    private double x;
    private double y;
    private double z;

    public Point3D() {
        this(0.0, 0.0, 0.0);
    }

    public Point3D(double x, double y, double z) {
        this.x = x;
        this.y = y;
        this.z = z;
    }

    public double getX() {
        return x;
    }

    public void setX(double x) {
        this.x = x;
    }

    public double getY() {
        return y;
    }

    public void setY(double y) {
        this.y = y;
    }

    public double getZ() {
        return z;
    }

    public void setZ(double z) {
        this.z = z;
    }

    public double distanceTo(Point3D other) {
        if (other == null) return 0.0;
        double dx = this.x - other.x;
        double dy = this.y - other.y;
        double dz = this.z - other.z;
        return Math.sqrt(dx * dx + dy * dy + dz * dz);
    }

    public double distance2D(double ox, double oy) {
        double dx = this.x - ox;
        double dy = this.y - oy;
        return Math.sqrt(dx * dx + dy * dy);
    }

    @Override
    public String toString() {
        return String.format("(%.2f, %.2f, %.2f)", x, y, z);
    }
}
