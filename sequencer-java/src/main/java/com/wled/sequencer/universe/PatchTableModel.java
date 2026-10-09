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
            node.setName(getDescriptiveControllerName(cid));
            node.setIp(String.format("10.0.0.%d", 100 + index));
            node.setPort(4048 + (index - 1));
            node.setProtocol("DDP (Distributed Display Protocol)");

            List<PatchSegmentModel> nodeSegs = getSegmentsForController(cid);
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

    private String getDescriptiveControllerName(String cid) {
        return switch (cid.toLowerCase()) {
            case "wled_01" -> "Front Stage Truss Span [Master A]";
            case "wled_02" -> "Front Stage Truss Span [Master B]";
            case "wled_03" -> "Front Left Truss Upright";
            case "wled_04" -> "Front Right Truss Upright";
            case "wled_05" -> "Rear Stage Truss Span [Master A]";
            case "wled_06" -> "Rear Stage Truss Span [Master B]";
            case "wled_07" -> "Rear Left Truss Upright";
            case "wled_08" -> "Rear Right Truss Upright";
            case "wled_09" -> "Left Stage Wing Overhead";
            case "wled_10" -> "Right Stage Wing Overhead";
            case "wled_11" -> "Stage Deck Front Lip Underglow";
            case "wled_12" -> "DJ Riser Front Facade Strip";
            case "wled_13" -> "Stage Left Wall Matrix Panel (16x16)";
            case "wled_14" -> "Stage Right Wall Matrix Panel (16x16)";
            case "wled_15" -> "DJ Booth Front Matrix Panel (16x16)";
            case "wled_16" -> "Canopy Festoon Left Diagonal";
            case "wled_17" -> "Canopy Festoon Right Diagonal";
            case "wled_18" -> "Perimeter Hall Ambient Strip [Left]";
            case "wled_19" -> "Perimeter Hall Ambient Strip [Right]";
            case "wled_20" -> "Floor Lamps & Projector Viewport Bus";
            default -> "WLED Node " + cid;
        };
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
