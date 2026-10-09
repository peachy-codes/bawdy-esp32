package com.wled.sequencer.universe;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Patch table mapping universe fixtures and pixel segments to hardware controllers and DDP ports.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class PatchTableModel {
    private String name = "Universe Patch Table";
    private List<PatchSegmentModel> segments = new ArrayList<>();

    private transient Path sourcePath;

    public PatchTableModel() {}

    public Path getSourcePath() {
        return sourcePath;
    }

    public void setSourcePath(Path path) {
        this.sourcePath = path;
    }

    public static PatchTableModel loadFromFile(Path path) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        byte[] bytes = Files.readAllBytes(path);
        PatchTableModel model = mapper.readValue(bytes, PatchTableModel.class);
        model.setSourcePath(path);
        return model;
    }

    public static PatchTableModel loadFromJson(String json) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        return mapper.readValue(json, PatchTableModel.class);
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

    public void addSegment(PatchSegmentModel segment) {
        if (segment != null) {
            segments.add(segment);
        }
    }

    public boolean removeSegment(int index) {
        if (index >= 0 && index < segments.size()) {
            segments.remove(index);
            return true;
        }
        return false;
    }

    public List<PatchSegmentModel> getSegmentsForFixture(String fixtureId) {
        if (fixtureId == null) return Collections.emptyList();
        return segments.stream()
                .filter(s -> fixtureId.equalsIgnoreCase(s.getFixtureId()))
                .collect(Collectors.toList());
    }

    public List<PatchSegmentModel> getSegmentsForController(String controllerId) {
        if (controllerId == null) return Collections.emptyList();
        return segments.stream()
                .filter(s -> controllerId.equalsIgnoreCase(s.getControllerId()))
                .collect(Collectors.toList());
    }

    public List<String> getAllControllers() {
        return segments.stream()
                .map(PatchSegmentModel::getControllerId)
                .filter(Objects::nonNull)
                .distinct()
                .sorted()
                .collect(Collectors.toList());
    }

    public int getTotalPatchedPixels() {
        return segments.stream().mapToInt(PatchSegmentModel::getPixelCount).sum();
    }

    /**
     * Validates the patch table for hardware port collisions and overlapping pixel ranges.
     * @return List of error strings; empty if patch is 100% clean.
     */
    public List<String> validate() {
        List<String> errors = new ArrayList<>();
        Map<String, List<PatchSegmentModel>> portBuckets = new HashMap<>();

        for (PatchSegmentModel s : segments) {
            String key = s.getControllerId() + "#" + s.getChannelIndex();
            portBuckets.computeIfAbsent(key, k -> new ArrayList<>()).add(s);
        }

        for (Map.Entry<String, List<PatchSegmentModel>> entry : portBuckets.entrySet()) {
            List<PatchSegmentModel> segs = entry.getValue();
            for (int i = 0; i < segs.size(); i++) {
                for (int j = i + 1; j < segs.size(); j++) {
                    PatchSegmentModel s1 = segs.get(i);
                    PatchSegmentModel s2 = segs.get(j);
                    int s1End = s1.getPortOffset() + s1.getPixelCount();
                    int s2End = s2.getPortOffset() + s2.getPixelCount();
                    if (Math.max(s1.getPortOffset(), s2.getPortOffset()) < Math.min(s1End, s2End)) {
                        errors.add(String.format("Port Collision on Controller '%s' Channel %d: Fixture '%s' [%d..%d] overlaps with Fixture '%s' [%d..%d]",
                                s1.getControllerId(), s1.getChannelIndex(), s1.getFixtureId(), s1.getPortOffset(), s1End, s2.getFixtureId(), s2.getPortOffset(), s2End));
                    }
                }
            }
        }
        return errors;
    }

    /**
     * Synthesizes 20-node controller fleet metadata from the patch segments.
     */
    public List<ControllerNodeModel> generateControllerNodes() {
        List<String> controllerIds = getAllControllers();
        if (controllerIds.isEmpty()) {
            // Default 20 nodes if patch is empty
            for (int i = 1; i <= 20; i++) {
                controllerIds.add(String.format("wled_%02d", i));
            }
        }

        List<ControllerNodeModel> nodes = new ArrayList<>();
        int index = 1;
        for (String cid : controllerIds) {
            ControllerNodeModel node = new ControllerNodeModel();
            node.setId(cid);
            List<PatchSegmentModel> nodeSegs = getSegmentsForController(cid);
            node.setName(getDescriptiveControllerName(cid, nodeSegs));
            node.setIp(String.format("10.0.0.%d", 100 + index));
            node.setPort(4048 + (index - 1));
            node.setProtocol("DDP (Distributed Display Protocol)");

            int sumPixels = 0;
            Set<Integer> channels = new TreeSet<>();
            Set<String> fixtures = new LinkedHashSet<>();

            for (PatchSegmentModel seg : nodeSegs) {
                sumPixels += seg.getPixelCount();
                channels.add(seg.getChannelIndex());
                if (seg.getFixtureId() != null) {
                    fixtures.add(seg.getFixtureId());
                }
            }

            node.setTotalPixels(sumPixels);
            node.setChannels(new ArrayList<>(channels));
            node.setFixtureIds(new ArrayList<>(fixtures));
            node.setStatus("Synced (0x41 Cat6 Active)");
            node.setPacketsSent(1420L * index);
            node.setLatencyMs(0.6 + (index % 5) * 0.1);

            nodes.add(node);
            index++;
        }

        return nodes;
    }

    private String getDescriptiveControllerName(String cid, List<PatchSegmentModel> nodeSegs) {
        if (nodeSegs != null && !nodeSegs.isEmpty()) {
            List<String> fixNames = nodeSegs.stream()
                    .map(PatchSegmentModel::getFixtureId)
                    .filter(Objects::nonNull)
                    .distinct()
                    .limit(2)
                    .map(this::formatFixtureIdAsRole)
                    .toList();
            if (!fixNames.isEmpty()) {
                return String.join(" + ", fixNames);
            }
        }
        return "Cat6 WLED Node " + cid;
    }

    private String formatFixtureIdAsRole(String fid) {
        return Arrays.stream(fid.replace('_', ' ').split("\\s+"))
                .map(w -> w.isEmpty() ? "" : Character.toUpperCase(w.charAt(0)) + w.substring(1).toLowerCase())
                .collect(Collectors.joining(" "));
    }

    // Getters and Setters

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<PatchSegmentModel> getSegments() {
        return segments;
    }

    public void setSegments(List<PatchSegmentModel> segments) {
        this.segments = segments != null ? segments : new ArrayList<>();
    }
}
