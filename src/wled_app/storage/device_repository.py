"""Device Repository for saving and loading DeviceConfig objects to/from JSON."""

from __future__ import annotations
import json
import os
from pathlib import Path

from wled_app.domain.device import DeviceConfig

def _get_default_device_dir() -> Path:
    env_dir = os.environ.get("WLED_DATA_DIR")
    if env_dir:
        return Path(env_dir) / "devices"
    try:
        config_dir = Path.home() / ".config" / "ascii-udp-wled" / "devices"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    except (PermissionError, OSError):
        local_dir = Path.cwd() / "data" / "devices"
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir


class DeviceRepository:
    """Manages file-based JSON persistence of DeviceConfig aggregate roots."""

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        if storage_dir is not None:
            self.storage_dir = Path(storage_dir)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_dir = _get_default_device_dir()

    def _file_path(self, device_id: str) -> Path:
        # Sanitize device_id for safe filesystem path
        safe_id = "".join(c for c in device_id if c.isalnum() or c in ("-", "_"))
        return self.storage_dir / f"{safe_id}.json"

    def save(self, device: DeviceConfig) -> Path:
        """Atomically persist device config to JSON."""
        target_path = self._file_path(device.id)
        tmp_path = target_path.with_suffix(".tmp")

        data = device.to_dict()
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())

        tmp_path.replace(target_path)
        return target_path

    def get(self, device_id: str) -> DeviceConfig | None:
        """Load device by ID."""
        path = self._file_path(device_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DeviceConfig.from_dict(data)
        except Exception:
            return None

    def get_by_name(self, name: str) -> DeviceConfig | None:
        """Find device by case-insensitive name match."""
        target_name = name.strip().lower()
        for dev in self.list_all():
            if dev.name.lower() == target_name:
                return dev
        return None

    def list_all(self) -> list[DeviceConfig]:
        """List all saved devices sorted by name."""
        devices: list[DeviceConfig] = []
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                devices.append(DeviceConfig.from_dict(data))
            except Exception:
                continue
        return sorted(devices, key=lambda d: d.name.lower())

    def delete(self, device_id: str) -> bool:
        """Delete device by ID. Returns True if file was deleted."""
        path = self._file_path(device_id)
        if path.exists():
            path.unlink()
            return True
        return False
