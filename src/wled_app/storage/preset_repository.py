"""Preset Repository for saving and loading Pattern presets."""

from __future__ import annotations
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

from wled_app.patterns.base import PatternConfig

def _get_default_preset_dir() -> Path:
    env_dir = os.environ.get("WLED_DATA_DIR")
    if env_dir:
        return Path(env_dir) / "presets"
    try:
        config_dir = Path.home() / ".config" / "ascii-udp-wled" / "presets"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    except (PermissionError, OSError):
        local_dir = Path.cwd() / "data" / "presets"
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir


@dataclass(frozen=True, slots=True)
class Preset:
    """Named preset containing pattern ID, parameters, and description."""

    name: str
    pattern_id: str
    config: PatternConfig
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pattern_id": self.pattern_id,
            "config": self.config.to_dict(),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Preset:
        return cls(
            name=str(data["name"]),
            pattern_id=str(data["pattern_id"]),
            config=PatternConfig.from_dict(data.get("config", {})),
            description=str(data.get("description", "")),
        )


class PresetRepository:
    """Manages file-based JSON persistence of pattern presets."""

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        if storage_dir is not None:
            self.storage_dir = Path(storage_dir)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_dir = _get_default_preset_dir()
        self._ensure_default_presets()

    def _file_path(self, name: str) -> Path:
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).lower()
        return self.storage_dir / f"{safe_name}.json"

    def _ensure_default_presets(self) -> None:
        """Seed default presets if directory is empty."""
        if any(self.storage_dir.glob("*.json")):
            return

        defaults = [
            Preset(
                name="Gentle Rainbow",
                pattern_id="rainbow",
                config=PatternConfig(speed=0.8, brightness=0.8, sync_channels=True),
                description="Smooth full-spectrum color flow across all strips",
            ),
            Preset(
                name="Red Police Chase",
                pattern_id="chase",
                config=PatternConfig(speed=1.5, brightness=1.0, sync_channels=True, extra={"tail_length": 6}),
                description="Fast red scanner chase across channels",
            ),
            Preset(
                name="Alternate Channel Pulse",
                pattern_id="blink",
                config=PatternConfig(
                    speed=1.0,
                    brightness=1.0,
                    extra={"mode": "pulse", "alternate_channels": True},
                ),
                description="Alternating smooth breathe between odd and even channels",
            ),
        ]
        for p in defaults:
            self.save(p)

    def save(self, preset: Preset) -> Path:
        """Atomically persist preset to JSON."""
        target_path = self._file_path(preset.name)
        tmp_path = target_path.with_suffix(".tmp")

        data = preset.to_dict()
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())

        tmp_path.replace(target_path)
        return target_path

    def get(self, name: str) -> Preset | None:
        """Load preset by name."""
        path = self._file_path(name)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Preset.from_dict(data)
        except Exception:
            return None

    def list_all(self) -> list[Preset]:
        """List all saved presets sorted by name."""
        presets: list[Preset] = []
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                presets.append(Preset.from_dict(data))
            except Exception:
                continue
        return sorted(presets, key=lambda p: p.name.lower())

    def delete(self, name: str) -> bool:
        """Delete preset by name. Returns True if deleted."""
        path = self._file_path(name)
        if path.exists():
            path.unlink()
            return True
        return False
