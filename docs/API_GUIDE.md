# WLED Lighting Engine REST API Reference

The headless **WLED Lighting Engine** exposes a high-performance HTTP JSON REST API (via `EngineDaemon`) to inspect and dynamically control real-time multi-layer compositing, layer transitions, global dimming, and event-driven reactive lighting.

---

## 🚀 Server Overview

* **Default Host:** `127.0.0.1` (or `0.0.0.0` for LAN access)
* **Default Port:** `8765`
* **Content-Type:** `application/json`
* **CORS Support:** Full support (`Access-Control-Allow-Origin: *`) for browser-based apps, web dashboards, and automation platforms.

### Starting the Daemon
```bash
# Using a saved hardware device profile:
wled-app daemon --device "Garage Door 3 by 270" --port 8765

# Using ad-hoc loopback targeting the hardware simulator:
python3 run.py daemon --ip 127.0.0.1 --channels 270 270 270 --port 8765
```

---

## 📡 Endpoints Summary

| Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | Engine lifecycle, actual FPS, tick, dimmer, and fleet status |
| `POST` | `/api/start` | Start the real-time frame clock loop |
| `POST` | `/api/stop` | Pause the real-time frame clock loop |
| `GET` | `/api/layers` | List all 10 compositing layers (Layers 0..9) |
| `GET` | `/api/layers/{index}` | Inspect specific layer configuration (`0` to `9`) |
| `POST` / `PUT` | `/api/layers/{index}` | Configure pattern, color, speed, blend mode, and channels |
| `POST` | `/api/layers/{index}/fade` | Trigger non-linear cosine opacity transition |
| `POST` | `/api/blackout` | Immediately reset all layers, stop sequences, and flush black frame to all hardware |
| `POST` | `/api/sequence/play` | Play a sequence timeline (with optional time dilation) |
| `POST` | `/api/sequence/pause` | Pause sequence timeline playback |
| `POST` | `/api/sequence/stop` | Stop sequence playback, reset clock to 0.0, and flush blackout |
| `POST` | `/api/sequence/seek` | Seek sequence timeline to specific timestamp in seconds |
| `POST` | `/api/spatial/pattern` | Trigger continuous 3D spatial field pattern (`angle_sweep`, `radial_pulse`, `rainbow`, `gradient`) |
| `GET` | `/api/fleet` | Retrieve Cat6 telemetry across all registered controller endpoints |
| `POST` | `/api/master_brightness` | Set global dimmer (0.0 to 1.0) |
| `POST` | `/api/cues` | Snapshot all 10 layers as a named cue |
| `POST` | `/api/cues/{name}/transition`| Crossfade all 10 layers to a saved cue |
| `POST` | `/api/events` | Publish an event to the reactive rule engine |

---

## 📖 Endpoint Details

### 1. `GET /api/status`
Returns real-time engine telemetry and registered device controller nodes.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "running": true,
  "target_fps": 30.0,
  "actual_fps": 30.02,
  "tick": 4120,
  "master_brightness": 1.0,
  "devices": [
    {
      "id": "629718dd",
      "name": "Garage Door 3 by 270",
      "ip": "10.10.0.245",
      "port": 4048,
      "protocol": "ddp",
      "channels": 3,
      "total_leds": 810
    }
  ],
  "cues": ["EveningChill", "StrobeAlert"]
}
```

---

### 2. `POST /api/start` & `POST /api/stop`
Control the background animation clock loop.

**Request:** `POST /api/start` (no body required)  
**Response `200 OK`:**
```json
{
  "status": "ok",
  "running": true
}
```

---

### 3. `GET /api/layers`
Returns an array of all 10 indexed layers (`Layer 0` to `Layer 9`), ordered from bottom (0) to top (9).

**Response `200 OK`:**
```json
[
  {
    "index": 0,
    "name": "Layer 0",
    "pattern": "wave",
    "opacity": 1.0,
    "blend_mode": "OVERWRITE",
    "channel_ids": null,
    "enabled": true
  },
  {
    "index": 1,
    "name": "Layer 1",
    "pattern": "chase",
    "opacity": 0.5,
    "blend_mode": "ADDITIVE",
    "channel_ids": [2],
    "enabled": true
  }
]
```

---

### 4. `POST /api/layers/{index}`
Configures an individual layer (index `0` through `9`). Assigning a valid pattern automatically enables the layer.

**URL Parameters:**
* `index` *(int, 0..9)*: The zero-based layer index.

**JSON Request Body Parameters:**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `pattern` | `string \| null` | — | Pattern ID: `"rainbow"`, `"chase"`, `"fire"`, `"meteor"`, `"cylon"`, `"twinkle"`, `"wave"`, `"gradient"`, `"blink"`, `"wipe"`, `"solid"`, or `null` to clear. |
| `opacity` | `float` | Existing | Opacity level between `0.0` (transparent) and `1.0` (opaque). |
| `blend_mode` | `string` | `"OVERWRITE"` | Blend operator: `"OVERWRITE"`, `"ALPHA_BLEND"`, `"ADDITIVE"`, `"MULTIPLY"`, `"MAX"`, `"MASK"`. |
| `channels` | `int[] \| null`| `null` | Channel numbers to isolate (e.g. `[1, 2]`), or `null` for all channels. |
| `speed` | `float` | `1.0` | Animation speed multiplier. |
| `brightness`| `float` | `1.0` | Pattern relative brightness (0.1..1.0). |
| `color` | `string` | `"#FF0000"` | Primary hex color code (e.g. `"#00FFAA"`). |
| `enabled` | `boolean` | `true` | Layer active switch. |

**Example Request:**
```bash
curl -X POST http://127.0.0.1:8765/api/layers/1 \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "chase",
    "color": "#FF2200",
    "speed": 2.5,
    "blend_mode": "ADDITIVE",
    "channels": [2],
    "opacity": 0.8
  }'
```

**Response `200 OK`:**
```json
{
  "status": "ok",
  "layer": {
    "index": 1,
    "pattern": "chase",
    "opacity": 0.8,
    "blend_mode": "ADDITIVE",
    "channel_ids": [2],
    "enabled": true
  }
}
```

---

### 5. `POST /api/layers/{index}/fade`
Initiates a smooth temporal fade using non-linear cosine ease-in-out curves.

**JSON Request Body:**
```json
{
  "target_opacity": 0.0,
  "duration_sec": 2.5
}
```

**Response `200 OK`:**
```json
{
  "status": "ok",
  "layer": 1,
  "fading": true
}
```

---

### 6. `POST /api/master_brightness`
Dims or brightens all outputs globally without altering individual layer opacity balances.

**JSON Request Body:**
```json
{
  "brightness": 0.4
}
```

**Response `200 OK`:**
```json
{
  "status": "ok",
  "master_brightness": 0.4
}
```

---

### 7. `POST /api/cues` & `POST /api/cues/{name}/transition`
Saves and crossfades complete multi-layer scenes.

#### Save Cue
```bash
curl -X POST http://127.0.0.1:8765/api/cues \
  -H "Content-Type: application/json" \
  -d '{"name": "EveningAmbient"}'
```

#### Crossfade to Cue
```bash
curl -X POST http://127.0.0.1:8765/api/cues/EveningAmbient/transition \
  -H "Content-Type: application/json" \
  -d '{"duration_sec": 3.0}'
```

**Response `200 OK`:**
```json
{
  "status": "ok",
  "cue": "EveningAmbient",
  "transitioning": true
}
```

---

### 8. `POST /api/events`
Publishes an event to the engine's internal `EventBus`. Pre-configured declarative `EventRule`s will execute automatically.

**JSON Request Body:**
```json
{
  "name": "garage_door_opened",
  "data": {
    "target_opacity": 1.0,
    "duration_sec": 0.5
  }
}
```

**Response `200 OK`:**
```json
{
  "status": "ok",
  "event": "garage_door_opened",
  "executed_actions": ["fade_layer"]
}
```

---

### 9. `POST /api/blackout`
Immediately halts sequence playback, clears active 3D spatial continuous patterns, resets all layers (0..9) to 0 opacity, and flushes an all-black RGB frame over UDP to all connected hardware controller nodes with sync.

```bash
curl -X POST http://127.0.0.1:8765/api/blackout
```

**Response `200 OK`:**
```json
{
  "status": "ok",
  "blackout": true
}
```

---

### 10. `POST /api/sequence/play` & Sequence Transport
Controls deterministic timeline sequence playback directly within the engine daemon.

#### Play Sequence
```bash
curl -X POST http://127.0.0.1:8765/api/sequence/play \
  -H "Content-Type: application/json" \
  -d '{"time_dilation": 1.0}'
```

#### Pause Sequence
```bash
curl -X POST http://127.0.0.1:8765/api/sequence/pause
```

#### Stop Sequence (Resets and Flushes Blackout)
```bash
curl -X POST http://127.0.0.1:8765/api/sequence/stop
```

#### Seek Timeline
```bash
curl -X POST http://127.0.0.1:8765/api/sequence/seek \
  -H "Content-Type: application/json" \
  -d '{"time": 12.5}'
```

---

### 11. `POST /api/spatial/pattern`
Triggers continuous 3D mathematical color field evaluators across the spatial universe. The engine samples the 3D field at every fixture LED coordinate and dispatches channel buffers to all controllers.

**Supported Patterns:** `angle_sweep`, `radial_pulse`, `rainbow`, `gradient`, `off`

```bash
curl -X POST http://127.0.0.1:8765/api/spatial/pattern \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "radial_pulse",
    "speed": 1.5,
    "frequency": 2.0,
    "color_center": "#FFD700",
    "color_edge": "#000033"
  }'
```

---

### 12. `GET /api/fleet`
Returns real-time network transmission telemetry (frames sent, packets sent, bytes sent, packet errors, and latency) across all Cat6 controller nodes.

```bash
curl http://127.0.0.1:8765/api/fleet
```

