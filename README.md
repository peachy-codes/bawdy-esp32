# ASCII UDP WLED Controller

A modular, extensible terminal application for configuring multi-channel addressable LED controllers (specifically the **Athom Ethernet WLED ESP32 DMX Controller**) and streaming real-time lighting patterns with live ASCII channel monitoring over UDP.

---

## 🌟 Key Features

* **Multi-Channel Hardware Alignment:** Specifically pre-configured for the 4-channel output topology of the Athom Ethernet ESP32 controller, with support for arbitrary numbers of addressable channels.
* **Automatic Address Space Layout:** Automatically calculates contiguous linear start offsets for all configured outputs (`CH1`..`CH4`) to match WLED internal memory mapping.
* **WLED Realtime Protocols:**
  * **DDP (Distributed Display Protocol, Port 4048):** Industry standard high-performance protocol recommended for multi-strip WLED setups.
  * **DRGB (Direct RGB, Port 21324):** High-speed raw RGB streaming.
  * **DNRGB (Direct Numbered RGB, Port 21324):** Large-frame streaming with start offset headers.
  * **WARLS (WLED Audio Reactive LED Strip, Port 21324):** Per-pixel indexed RGB addressing.
* **Live ASCII Channel Visualizer:** Renders real-time strip activity channel-by-channel directly in your terminal using 24-bit Truecolor ANSI blocks (`██`), peak-preserving perceptual brightness, and active channel color swatches (`●`).
* **11 Dynamic Patterns & Color Palettes:**
  1. **Flowing Rainbow:** Smooth continuous HSV color spectrum wave.
  2. **Theater Chase:** High-speed scanner dot with glowing, fading tail.
  3. **Fire & Campfire:** Heat simulation with rising flames and random spark embers.
  4. **Meteor Rain:** Fast shooting star head with decaying sparkling tail.
  5. **Cylon (Knight Rider):** Smooth bouncing scanner eye with glowing tail.
  6. **Twinkle Stars:** Softly breathing and sparkling stars on a dark backdrop.
  7. **Ocean Waves:** Dual harmonic undulating sine ripples simulating water.
  8. **Gradient Drift:** Multi-stop gradient palettes drifting across channels.
  9. **Blink & Pulse:** Multi-channel strobe, breathing sine pulse, and alternating channel flash.
  10. **Color Wipe:** Progressive filling and draining of LED strips.
  11. **Solid Wash & Breathe:** Clean solid color wash with optional breathing pulse.
* **Predefined Palettes:** *Cyberpunk Neon*, *Tropical Sunset*, *Deep Ocean*, *Emerald Forest*, *Fire & Flame*, *Police Strobe*, and *Party Confetti*.
* **Persistence & Presets:** Save and load device configurations and pattern parameter presets as human-readable JSON files.
* **Dry-Run / Preview Mode:** Test and visually inspect patterns directly in your terminal without needing physical hardware connected.

---

## 🚀 Quick Start

### 1. Requirements & Installation

Python 3.10+ is required. Dependencies are minimal (`rich` and `prompt_toolkit`).

```bash
# Clone or navigate to the directory
cd ~/ascii-udp-wled

# Install package in editable development mode
pip install -e .
```

### 2. Interactive Terminal UI

Launch the interactive terminal application:

```bash
python3 -m wled_app
# Or via installed console script:
wled-app
```

The interactive wizard guides you through:
1. **Selecting / Loading** saved devices.
2. **Creating a new device** with IP, UDP port, protocol, and channel strip lengths.
3. **Inspecting channels** and linear address ranges.
4. **Streaming real-time patterns** with live ASCII art and UDP transmission.
5. **Managing pattern presets**.

---

## 💻 Command Line Interface (CLI)

The application also supports fully scriptable non-interactive CLI commands:

### Create a Device
```bash
wled-app create \
  --name "Athom-LivingRoom" \
  --ip 192.168.1.150 \
  --channels 60 30 144 0 \
  --protocol ddp \
  --description "Athom 4-channel ESP32"
```

### List Saved Devices
```bash
wled-app list
```

### Stream Patterns
```bash
# Stream rainbow to device
wled-app play --device "Athom-LivingRoom" --pattern rainbow --fps 30

# Stream chase in red with 1.5x speed
wled-app play --device "Athom-LivingRoom" --pattern chase --color "#FF0000" --speed 1.5

# Test alternating channel blink in preview-only / dry-run mode (no network packets sent)
wled-app play --device "Athom-LivingRoom" --pattern blink --dry-run
```

---

## 🖥️ Simulated UDP Device (Hardware Digital Twin)

For testing and visual verification without needing physical LED hardware powered on, the repository includes a **standalone WLED ESP32 Hardware Digital Twin Simulator** (`sim.py`).

The simulator runs as an independent process that binds to real UDP sockets (`0.0.0.0:4048` for DDP, `0.0.0.0:21324` for DRGB), faithfully processes multi-packet frame assembly and WLED `PUSH` flags through the operating system network stack, and renders physical LED strips on an interactive web canvas.

### 🌟 Simulator Features

* **Unified CAD Stage Canvas (`http://localhost:8080`):** Single full-screen hardware-accelerated 2D stage with smooth Pan, Zoom, and Auto-Fit.
* **Interactive Drag & Drop with Magnetic Snapping:** Drag channel strip fixtures freely across the 2D plane. Fixture endpoints magnetically snap together for effortless alignment.
* **Architectural Layout Presets:**
  * **🏛️ Garage Arch Preset:** Instantly aligns fixtures into a connected U-frame: Channel 1 (Left vertical track), Channel 2 (Top horizontal header), and Channel 3 (Right vertical track).
  * **☰ Stacked Rows Preset:** Aligns channels in clean parallel horizontal runs.
* **Orientation Controls:** Rotate any strip in 90° increments or flip sequence direction (`FWD ▶` / `◀ REV`).
* **Multi-Packet Stream Integrity & Telemetry HUD:** Real-time monospace telemetry displaying **FPS**, **Packets/Sec (PPS)**, **Throughput (KB/s)**, **Packet Arrival Jitter (µs)**, and an **Integrity Status Badge** (Healthy 🟢, Sequence Gap 🟡, Torn Frame Push 🔴).
* **Responsive Multi-Layer Hero Bar:** Gracefully wraps text and controls into clean, organized layers on laptop displays or split-screen windows without clipping or scrollbars.
* **Zero Modification to Original App:** The simulator is completely decoupled from `run.py` and operates as an independent network receiver.

### 🚀 Launching the Simulator

#### 1. Start the Simulator in Terminal 1
```bash
# Launch using an existing saved device profile (e.g. 3 channels of 270 LEDs):
python3 sim.py --device "Garage Door 3 by 270"

# Or launch with custom ad-hoc channel counts and custom ports:
python3 sim.py --channels 270 270 270 --port 4048
```
*(Your browser will automatically open `http://localhost:8080` displaying the virtual stage).*

#### 2. Stream Real-Time Patterns from Terminal 2
In a second terminal window, stream live patterns from your controller app over loopback:
```bash
# Stream chase pattern to the simulated controller
python3 run.py play --ip 127.0.0.1 --pattern chase --speed 1.5

# Or stream other patterns:
python3 run.py play --ip 127.0.0.1 --pattern rainbow --speed 2.0
python3 run.py play --ip 127.0.0.1 --pattern fire
python3 run.py play --ip 127.0.0.1 --pattern meteor
```

### ⌨️ Studio Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| <kbd>F</kbd> | **Fit to View:** Automatically scale and center all fixtures to the window |
| <kbd>R</kbd> | **Rotate:** Rotate selected channel fixture 90° clockwise |
| <kbd>G</kbd> | **Garage Arch:** Snap fixtures into the connected Garage Door frame layout |
| <kbd>S</kbd> | **Stacked Rows:** Arrange fixtures in parallel horizontal rows |
| **Scroll Wheel** | Zoom in / out towards mouse cursor |
| **Drag Background** | Pan the viewport camera across the stage |

---

## 🧱 Architecture & Design Patterns

The codebase strictly adheres to the engineering patterns documented in `~/llm-coding-practices`:

* **Locality of Behavior (LoB):** Clear, inspectable modules with minimal magic indirection.
* **Make Illegal States Unrepresentable:** Immutable value objects ([`Color`](src/wled_app/domain/color.py), [`ChannelConfig`](src/wled_app/domain/channel.py), [`DeviceConfig`](src/wled_app/domain/device.py)) guarantee that invalid RGB values, out-of-bounds channels, or malformed protocol states cannot exist.
* **Composition over Inheritance:** Protocols ([`ProtocolEmitter`](src/wled_app/protocols/base.py), [`Pattern`](src/wled_app/patterns/base.py), [`UdpSender`](src/wled_app/network/udp_client.py)) use structural subtyping via `typing.Protocol`.
* **Zero-Allocation Packet Buffers:** Contiguous `bytearray` assembly for fast UDP datagram serialization.
* **Hermetic Testing:** 100% test coverage for protocol encoders and pattern engines using in-memory mock transports.

---

## 🔌 Adding Custom Patterns

Creating a new visual effect requires implementing the `Pattern` protocol:

```python
from wled_app.domain.color import Color
from wled_app.domain.device import DeviceConfig
from wled_app.domain.frame import FrameBuffer
from wled_app.patterns.base import PatternConfig

class SparklePattern:
    @property
    def id(self) -> str:
        return "sparkle"

    @property
    def name(self) -> str:
        return "Random Sparkle"

    @property
    def description(self) -> str:
        return "Random LED sparkle across active channels"

    def render(self, tick: int, device: DeviceConfig, frame: FrameBuffer, config: PatternConfig) -> None:
        frame.clear()
        import random
        for ch in device.active_channels:
            if ch.length > 0:
                random_pixel = random.randint(0, ch.length - 1)
                frame.set_pixel(ch.start_index + random_pixel, config.primary_color)
```

Register it in `src/wled_app/patterns/registry.py` and it immediately becomes available in both the CLI and Interactive TUI!

---

## 🧪 Running Tests

Run the test suite using Python's built-in `unittest`:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py" -v
```
