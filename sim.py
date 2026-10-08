#!/usr/bin/env python3
"""Standalone entrypoint for WLED ESP32 Hardware Digital Twin Simulator."""

import sys
from pathlib import Path

# Add src/ to python path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from wled_simulator.cli import main

if __name__ == "__main__":
    main()
