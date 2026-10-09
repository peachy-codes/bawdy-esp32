package com.wled.sequencer.universe;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;
import java.util.List;

/**
 * Model representing a physical lighting fixture in the spatial universe.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class FixtureModel {
    private String id;
    private String name;
    private String type = "linear_strip";
    private String group = "trusses";
    private List<String> tags = new ArrayList<>();

    @JsonProperty("pixel_count")
    private int pixelCount = 1;

    @JsonProperty("pixel_offset")
    private int pixelOffset = 0;

    @JsonProperty("color_order")
    private String colorOrder = "GRB";

    private boolean reversed = false;

    // Computed or deserialized pixel 3D coordinates
    private List<Point3D> points = new ArrayList<>();

    // Type-specific: linear_strip
    private List<Point3D> waypoints = new ArrayList<>();

    // Type-specific: bulb_string
    private Point3D start;
    private Point3D end;
    private double sag = 0.5;

    @JsonProperty("sag_axis")
    private String sagAxis = "z";

    // Type-specific: matrix
    private int rows = 16;
    private int cols = 16;
    private double width = 1.0;
    private double height = 1.0;
    private Point3D origin;
    private boolean serpentine = true;

    // Type-specific: point (lamp)
    private Point3D location;
    private double radius = 0.45;

    // Type-specific: projector
    @JsonProperty("top_left")
    private Point3D topLeft;

    @JsonProperty("bottom_right")
    private Point3D bottomRight;

    @JsonProperty("resolution_x")
    private int resolutionX = 1920;

    @JsonProperty("resolution_y")
    private int resolutionY = 1080;

    public FixtureModel() {}

    /**
     * Ensures all pixel coordinates are calculated and cached.
     */
    public void ensurePixelPointsGenerated() {
        if (!points.isEmpty()) {
            return;
        }

        points = new ArrayList<>();

        if ("linear_strip".equalsIgnoreCase(type)) {
            if (waypoints != null && waypoints.size() >= 2 && pixelCount > 0) {
                Point3D p0 = waypoints.get(0);
                Point3D p1 = waypoints.get(waypoints.size() - 1);
                for (int i = 0; i < pixelCount; i++) {
                    double t = pixelCount > 1 ? (double) i / (pixelCount - 1) : 0.0;
                    points.add(new Point3D(
                            p0.getX() + t * (p1.getX() - p0.getX()),
                            p0.getY() + t * (p1.getY() - p0.getY()),
                            p0.getZ() + t * (p1.getZ() - p0.getZ())
                    ));
                }
            }
        } else if ("bulb_string".equalsIgnoreCase(type)) {
            if (start != null && end != null && pixelCount > 0) {
                for (int i = 0; i < pixelCount; i++) {
                    double t = pixelCount > 1 ? (double) i / (pixelCount - 1) : 0.0;
                    double linX = start.getX() + t * (end.getX() - start.getX());
                    double linY = start.getY() + t * (end.getY() - start.getY());
                    double linZ = start.getZ() + t * (end.getZ() - start.getZ());
                    // Parabolic catenary sag: 4 * sag * t * (1 - t)
                    double sagOffset = 4.0 * sag * t * (1.0 - t);
                    double z = "z".equalsIgnoreCase(sagAxis) ? linZ - sagOffset : linZ;
                    double y = "y".equalsIgnoreCase(sagAxis) ? linY - sagOffset : linY;
                    points.add(new Point3D(linX, y, z));
                }
            }
        } else if ("matrix".equalsIgnoreCase(type)) {
            Point3D org = origin != null ? origin : new Point3D(0, 0, 0);
            int rCount = rows > 0 ? rows : 16;
            int cCount = cols > 0 ? cols : 16;
            this.pixelCount = rCount * cCount;

            double dx = cCount > 1 ? width / (cCount - 1) : 0;
            double dz = rCount > 1 ? height / (rCount - 1) : 0;

            for (int r = 0; r < rCount; r++) {
                for (int c = 0; c < cCount; c++) {
                    int colIdx = (serpentine && (r % 2 == 1)) ? (cCount - 1 - c) : c;
                    points.add(new Point3D(
                            org.getX() + colIdx * dx,
                            org.getY(),
                            org.getZ() - r * dz
                    ));
                }
            }
        } else if ("point".equalsIgnoreCase(type)) {
            Point3D loc = location != null ? location : new Point3D(0, 0, 0);
            points.add(new Point3D(loc.getX(), loc.getY(), loc.getZ()));
        } else if ("projector".equalsIgnoreCase(type)) {
            Point3D tl = topLeft != null ? topLeft : new Point3D(-2.4, 6.9, 3.8);
            Point3D br = bottomRight != null ? bottomRight : new Point3D(2.4, 6.9, 1.1);
            // Projector center screen reference point
            points.add(new Point3D((tl.getX() + br.getX()) / 2.0, tl.getY(), (tl.getZ() + br.getZ()) / 2.0));
        }

        if (reversed && points.size() > 1) {
            java.util.Collections.reverse(points);
        }
    }

    // Getters and Setters

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

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getGroup() {
        return group != null ? group : "general";
    }

    public void setGroup(String group) {
        this.group = group;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(List<String> tags) {
        this.tags = tags != null ? tags : new ArrayList<>();
    }

    public int getPixelCount() {
        return pixelCount > 0 ? pixelCount : Math.max(1, points.size());
    }

    public void setPixelCount(int pixelCount) {
        this.pixelCount = pixelCount;
    }

    public int getPixelOffset() {
        return pixelOffset;
    }

    public void setPixelOffset(int pixelOffset) {
        this.pixelOffset = pixelOffset;
    }

    public String getColorOrder() {
        return colorOrder;
    }

    public void setColorOrder(String colorOrder) {
        this.colorOrder = colorOrder;
    }

    public boolean isReversed() {
        return reversed;
    }

    public void setReversed(boolean reversed) {
        this.reversed = reversed;
    }

    public List<Point3D> getPoints() {
        return points;
    }

    public void setPoints(List<Point3D> points) {
        this.points = points != null ? points : new ArrayList<>();
    }

    public List<Point3D> getWaypoints() {
        return waypoints;
    }

    public void setWaypoints(List<Point3D> waypoints) {
        this.waypoints = waypoints;
    }

    public Point3D getStart() {
        return start;
    }

    public void setStart(Point3D start) {
        this.start = start;
    }

    public Point3D getEnd() {
        return end;
    }

    public void setEnd(Point3D end) {
        this.end = end;
    }

    public double getSag() {
        return sag;
    }

    public void setSag(double sag) {
        this.sag = sag;
    }

    public String getSagAxis() {
        return sagAxis;
    }

    public void setSagAxis(String sagAxis) {
        this.sagAxis = sagAxis;
    }

    public int getRows() {
        return rows;
    }

    public void setRows(int rows) {
        this.rows = rows;
    }

    public int getCols() {
        return cols;
    }

    public void setCols(int cols) {
        this.cols = cols;
    }

    public double getWidth() {
        return width;
    }

    public void setWidth(double width) {
        this.width = width;
    }

    public double getHeight() {
        return height;
    }

    public void setHeight(double height) {
        this.height = height;
    }

    public Point3D getOrigin() {
        return origin;
    }

    public void setOrigin(Point3D origin) {
        this.origin = origin;
    }

    public boolean isSerpentine() {
        return serpentine;
    }

    public void setSerpentine(boolean serpentine) {
        this.serpentine = serpentine;
    }

    public Point3D getLocation() {
        return location;
    }

    public void setLocation(Point3D location) {
        this.location = location;
    }

    public double getRadius() {
        return radius;
    }

    public void setRadius(double radius) {
        this.radius = radius;
    }

    public Point3D getTopLeft() {
        return topLeft;
    }

    public void setTopLeft(Point3D topLeft) {
        this.topLeft = topLeft;
    }

    public Point3D getBottomRight() {
        return bottomRight;
    }

    public void setBottomRight(Point3D bottomRight) {
        this.bottomRight = bottomRight;
    }

    public int getResolutionX() {
        return resolutionX;
    }

    public void setResolutionX(int resolutionX) {
        this.resolutionX = resolutionX;
    }

    public int getResolutionY() {
        return resolutionY;
    }

    public void setResolutionY(int resolutionY) {
        this.resolutionY = resolutionY;
    }

    @Override
    public String toString() {
        return getName() + " [" + group + " - " + getPixelCount() + " LEDs]";
    }
}
