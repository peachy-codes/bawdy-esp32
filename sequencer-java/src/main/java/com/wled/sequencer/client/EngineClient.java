package com.wled.sequencer.client;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.wled.sequencer.model.SequenceData;
import com.wled.sequencer.model.SequenceStep;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * High-performance REST Client communicating asynchronously with the
 * WLED Lighting Engine Daemon via Java 17 HttpClient.
 */
public class EngineClient {
    private String baseUrl;
    private final HttpClient httpClient;
    private final ObjectMapper mapper;

    private volatile boolean online = false;
    private volatile double engineFps = 0.0;

    public EngineClient(String baseUrl) {
        this.baseUrl = normalizeUrl(baseUrl);
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofMillis(1500))
                .build();
        this.mapper = new ObjectMapper();
    }

    public EngineClient() {
        this("http://127.0.0.1:8765");
    }

    private static String normalizeUrl(String url) {
        if (url == null || url.isBlank()) return "http://127.0.0.1:8765";
        return url.replaceAll("/+$", "");
    }

    public String getBaseUrl() {
        return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = normalizeUrl(baseUrl);
    }

    public boolean isOnline() {
        return online;
    }

    public double getEngineFps() {
        return engineFps;
    }

    public CompletableFuture<EngineStatus> ping() {
        String url = baseUrl + "/api/status";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofMillis(2000))
                .GET()
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(resp -> {
                    if (resp.statusCode() == 200) {
                        try {
                            EngineStatus status = mapper.readValue(resp.body(), EngineStatus.class);
                            this.online = true;
                            this.engineFps = status.getActualFps();
                            return status;
                        } catch (Exception e) {
                            this.online = true;
                            return new EngineStatus("ok", true, 30.0);
                        }
                    }
                    this.online = false;
                    this.engineFps = 0.0;
                    return new EngineStatus("error", false, 0.0);
                })
                .exceptionally(ex -> {
                    this.online = false;
                    this.engineFps = 0.0;
                    return new EngineStatus("offline", false, 0.0);
                });
    }

    public CompletableFuture<EngineCapabilities> fetchCapabilities() {
        String url = baseUrl + "/api/capabilities";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofMillis(2000))
                .GET()
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(resp -> {
                    if (resp.statusCode() == 200) {
                        try {
                            return mapper.readValue(resp.body(), EngineCapabilities.class);
                        } catch (Exception ignored) {}
                    }
                    return EngineCapabilities.defaults();
                })
                .exceptionally(ex -> EngineCapabilities.defaults());
    }

    public CompletableFuture<Void> playSequence(SequenceData sequence) {
        try {
            String json = mapper.writeValueAsString(sequence);
            @SuppressWarnings("unchecked")
            Map<String, Object> seqMap = mapper.readValue(json, Map.class);
            Map<String, Object> payload = Map.of(
                    "sequence", seqMap,
                    "time_dilation", sequence.getTimeDilation()
            );
            return sendJsonPost("/api/sequence/play", payload);
        } catch (Exception e) {
            return CompletableFuture.completedFuture(null);
        }
    }

    public CompletableFuture<Void> pauseSequence() {
        return sendJsonPost("/api/sequence/pause", Map.of());
    }

    public CompletableFuture<Void> stopSequence() {
        return sendJsonPost("/api/sequence/stop", Map.of());
    }

    public CompletableFuture<Void> seekSequence(double timeSec) {
        return sendJsonPost("/api/sequence/seek", Map.of("time", timeSec));
    }

    public CompletableFuture<SequencePlayStatus> fetchSequenceStatus() {
        String url = baseUrl + "/api/sequence/status";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofMillis(1000))
                .GET()
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(resp -> {
                    if (resp.statusCode() == 200) {
                        try {
                            return mapper.readValue(resp.body(), SequencePlayStatus.class);
                        } catch (Exception ignored) {}
                    }
                    return null;
                })
                .exceptionally(ex -> null);
    }

    public CompletableFuture<Void> applyStep(SequenceStep step, double timeDilation) {
        int layerIdx = step.getTargetLayer();

        if (step.getPatternId() == null || step.getPatternId().equalsIgnoreCase("none")) {
            return clearLayer(layerIdx, 0.0);
        }

        double dilation = Math.max(0.05, timeDilation);
        double effectiveTransition = Math.max(0.0, step.getTransitionSec() / dilation);
        double startOpacity = effectiveTransition > 0.05 ? 0.0 : step.getTargetOpacity();

        Map<String, Object> payload = new HashMap<>();
        payload.put("pattern", step.getPatternId());
        payload.put("color", step.getPrimaryColor());
        payload.put("speed", step.getSpeed());
        payload.put("brightness", step.getBrightness());
        payload.put("blend_mode", step.getBlendMode());
        payload.put("channels", step.getChannels());
        payload.put("opacity", startOpacity);
        payload.put("enabled", true);

        return sendJsonPost("/api/layers/" + layerIdx, payload)
                .thenCompose(v -> {
                    if (effectiveTransition > 0.05) {
                        Map<String, Object> fadePayload = Map.of(
                                "target_opacity", step.getTargetOpacity(),
                                "duration_sec", effectiveTransition
                        );
                        return sendJsonPost("/api/layers/" + layerIdx + "/fade", fadePayload);
                    }
                    return CompletableFuture.completedFuture(null);
                });
    }

    public CompletableFuture<Void> clearLayer(int layerIdx, double fadeOutSec) {
        if (fadeOutSec > 0.05) {
            Map<String, Object> fadePayload = Map.of(
                    "target_opacity", 0.0,
                    "duration_sec", fadeOutSec
            );
            return sendJsonPost("/api/layers/" + layerIdx + "/fade", fadePayload);
        } else {
            Map<String, Object> offPayload = new HashMap<>();
            offPayload.put("pattern", null);
            offPayload.put("enabled", false);
            offPayload.put("opacity", 0.0);
            return sendJsonPost("/api/layers/" + layerIdx, offPayload);
        }
    }

    public CompletableFuture<Void> blackout() {
        return sendJsonPost("/api/blackout", Map.of());
    }

    public CompletableFuture<Void> broadcastSync() {
        return sendJsonPost("/api/sync", Map.of());
    }

    public CompletableFuture<Void> loadUniversePreset(String presetName) {
        return sendJsonPost("/api/universe", Map.of("preset", presetName));
    }

    private CompletableFuture<Void> sendJsonPost(String endpoint, Map<String, Object> data) {
        try {
            String json = mapper.writeValueAsString(data);
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + endpoint))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofMillis(1000))
                    .POST(HttpRequest.BodyPublishers.ofString(json))
                    .build();

            return httpClient.sendAsync(request, HttpResponse.BodyHandlers.discarding())
                    .thenAccept(resp -> {})
                    .exceptionally(ex -> (Void) null);
        } catch (Exception e) {
            return CompletableFuture.completedFuture(null);
        }
    }
}
