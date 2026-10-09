package com.wled.sequencer.universe;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Root domain model representing the complete multi-fixture spatial lighting universe.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class SpatialUniverseModel {
    private String name = "Default Universe";

    @JsonProperty("bounding_box")
    private BoundingBox3D boundingBox = new BoundingBox3D();

    @JsonProperty("total_pixels")
    private int totalPixels = 0;

    private List<String> groups = new ArrayList<>();
    private List<FixtureModel> fixtures = new ArrayList<>();

    private transient Path sourcePath;

    public SpatialUniverseModel() {}

    public Path getSourcePath() {
        return sourcePath;
    }

    public void setSourcePath(Path path) {
        this.sourcePath = path;
    }

    public static SpatialUniverseModel loadFromFile(Path path) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        byte[] bytes = Files.readAllBytes(path);
        SpatialUniverseModel model = mapper.readValue(bytes, SpatialUniverseModel.class);
        model.setSourcePath(path);
        model.initialize();
        return model;
    }

    public static SpatialUniverseModel loadFromJson(String json) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        SpatialUniverseModel model = mapper.readValue(json, SpatialUniverseModel.class);
        model.initialize();
        return model;
    }

    public void saveToFile(Path path) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        mapper.writerWithDefaultPrettyPrinter().writeValue(path.toFile(), this);
        this.sourcePath = path;
    }

    public void save() throws IOException {
        if (sourcePath != null) {
            saveToFile(sourcePath);
        }
    }

    public void addFixture(FixtureModel fixture) {
        if (fixture != null) {
            fixtures.add(fixture);
            if (fixture.getGroup() != null && !groups.contains(fixture.getGroup())) {
                groups.add(fixture.getGroup());
            }
            initialize();
        }
    }

    public boolean removeFixture(String fixtureId) {
        if (fixtureId == null) return false;
        boolean removed = fixtures.removeIf(f -> fixtureId.equalsIgnoreCase(f.getId()));
        if (removed) {
            initialize();
        }
        return removed;
    }

    public void initialize() {
        int offset = 0;
        int sumPixels = 0;

        for (FixtureModel f : fixtures) {
            f.ensurePixelPointsGenerated();
            f.setPixelOffset(offset);
            offset += f.getPixelCount();
            sumPixels += f.getPixelCount();
        }

        if (totalPixels <= 0) {
            this.totalPixels = sumPixels;
        }

        if (groups == null || groups.isEmpty()) {
            this.groups = fixtures.stream()
                    .map(FixtureModel::getGroup)
                    .distinct()
                    .sorted()
                    .collect(Collectors.toList());
        }

        // Validate or compute bounding box
        if (boundingBox == null || boundingBox.getWidth() <= 0) {
            double minX = Double.MAX_VALUE, minY = Double.MAX_VALUE, minZ = Double.MAX_VALUE;
            double maxX = -Double.MAX_VALUE, maxY = -Double.MAX_VALUE, maxZ = -Double.MAX_VALUE;

            for (FixtureModel f : fixtures) {
                for (Point3D p : f.getPoints()) {
                    if (p.getX() < minX) minX = p.getX();
                    if (p.getX() > maxX) maxX = p.getX();
                    if (p.getY() < minY) minY = p.getY();
                    if (p.getY() > maxY) maxY = p.getY();
                    if (p.getZ() < minZ) minZ = p.getZ();
                    if (p.getZ() > maxZ) maxZ = p.getZ();
                }
            }
            if (minX <= maxX) {
                this.boundingBox = new BoundingBox3D(minX, minY, minZ, maxX, maxY, maxZ);
            } else {
                this.boundingBox = new BoundingBox3D(-6.5, -6.5, 0.0, 6.5, 7.0, 4.5);
            }
        }
    }

    public FixtureModel getFixture(String id) {
        if (id == null) return null;
        for (FixtureModel f : fixtures) {
            if (id.equalsIgnoreCase(f.getId())) {
                return f;
            }
        }
        return null;
    }

    public List<FixtureModel> getFixturesByGroup(String group) {
        if (group == null || group.equalsIgnoreCase("all")) {
            return new ArrayList<>(fixtures);
        }
        return fixtures.stream()
                .filter(f -> group.equalsIgnoreCase(f.getGroup()))
                .collect(Collectors.toList());
    }

    // Getters and Setters

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public BoundingBox3D getBoundingBox() {
        return boundingBox;
    }

    public void setBoundingBox(BoundingBox3D boundingBox) {
        this.boundingBox = boundingBox;
    }

    public int getTotalPixels() {
        return totalPixels;
    }

    public void setTotalPixels(int totalPixels) {
        this.totalPixels = totalPixels;
    }

    public List<String> getGroups() {
        return groups;
    }

    public void setGroups(List<String> groups) {
        this.groups = groups;
    }

    public List<FixtureModel> getFixtures() {
        return fixtures;
    }

    public void setFixtures(List<FixtureModel> fixtures) {
        this.fixtures = fixtures != null ? fixtures : new ArrayList<>();
    }
}
