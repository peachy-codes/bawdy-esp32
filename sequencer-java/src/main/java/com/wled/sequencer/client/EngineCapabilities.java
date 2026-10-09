package com.wled.sequencer.client;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record EngineCapabilities(
        @JsonProperty("status") String status,
        @JsonProperty("patterns") List<String> patterns,
        @JsonProperty("palettes") List<String> palettes,
        @JsonProperty("blend_modes") List<String> blendModes,
        @JsonProperty("max_layers") int maxLayers
) {
    public static EngineCapabilities defaults() {
        return new EngineCapabilities(
                "default",
                List.of("rainbow", "chase", "fire", "meteor", "cylon", "twinkle", "wave", "gradient", "blink", "wipe", "solid", "none"),
                List.of("(None / Solid Primary)", "cyberpunk", "sunset", "ocean", "forest", "fire", "police", "party"),
                List.of("OVERWRITE", "ALPHA_BLEND", "ADDITIVE", "MULTIPLY", "MAX", "MASK"),
                10
        );
    }
}
