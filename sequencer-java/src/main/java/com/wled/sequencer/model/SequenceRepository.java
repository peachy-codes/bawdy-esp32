package com.wled.sequencer.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Stream;

/**
 * Repository for persisting and loading JSON lighting sequences from disk using Jackson.
 */
public class SequenceRepository {
    private final Path directory;
    private final ObjectMapper mapper;

    public SequenceRepository(Path directory) {
        this.directory = directory;
        this.mapper = new ObjectMapper();
        this.mapper.enable(SerializationFeature.INDENT_OUTPUT);
        try {
            Files.createDirectories(directory);
        } catch (IOException ignored) {}
    }

    public Path getDirectory() {
        return directory;
    }

    private String safeFilename(String name) {
        String clean = name == null ? "sequence" : name.trim().toLowerCase().replaceAll("[^a-zA-Z0-9\\-_]", "_");
        if (clean.isBlank()) clean = "sequence";
        return clean.endsWith(".json") ? clean : clean + ".json";
    }

    public List<SequenceSummary> listSequences() {
        if (!Files.isDirectory(directory)) {
            return Collections.emptyList();
        }
        List<SequenceSummary> summaries = new ArrayList<>();
        try (Stream<Path> stream = Files.list(directory)) {
            List<Path> files = stream.filter(p -> p.getFileName().toString().endsWith(".json"))
                    .sorted()
                    .toList();
            for (Path file : files) {
                try {
                    SequenceData seq = loadSequence(file.getFileName().toString());
                    if (seq != null) {
                        summaries.add(new SequenceSummary(
                                file.getFileName().toString(),
                                seq.getName(),
                                seq.getDescription(),
                                seq.getSteps().size(),
                                seq.getTotalDuration(),
                                seq.getLoopMode()
                        ));
                    }
                } catch (Exception ignored) {}
            }
        } catch (IOException e) {
            return Collections.emptyList();
        }
        return summaries;
    }

    public SequenceData loadSequence(String filename) {
        if (!filename.endsWith(".json")) {
            filename += ".json";
        }
        Path path = directory.resolve(filename);
        if (!Files.isRegularFile(path)) {
            return null;
        }
        try {
            SequenceData data = mapper.readValue(path.toFile(), SequenceData.class);
            if (data != null) {
                data.normalize();
            }
            return data;
        } catch (Exception e) {
            return null;
        }
    }

    public String saveSequence(SequenceData sequence, String targetFilename) throws IOException {
        String filename = targetFilename != null && !targetFilename.isBlank()
                ? safeFilename(targetFilename)
                : safeFilename(sequence.getName());

        Path path = directory.resolve(filename);
        Files.createDirectories(directory);
        mapper.writeValue(path.toFile(), sequence);
        return filename;
    }

    public boolean deleteSequence(String filename) {
        if (!filename.endsWith(".json")) {
            filename += ".json";
        }
        Path path = directory.resolve(filename);
        try {
            return Files.deleteIfExists(path);
        } catch (IOException e) {
            return false;
        }
    }
}
