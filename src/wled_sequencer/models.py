"""Data models and repository for Pattern Sequencer sequences with timeline sections."""

from __future__ import annotations
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SequenceStep:
    """A temporal block/cue within a lighting sequence with start, duration, and stop."""
    id: str
    name: str = "Block"
    section: str = "Main"  # Logical section grouping (e.g. Intro, Verse, Chorus, Outro)
    target_layer: int = 0  # 0..9
    start_time_sec: float = 0.0
    duration_sec: float = 4.0
    pattern_id: str = "rainbow"
    primary_color: str = "#FF0000"
    palette: str | None = None
    speed: float = 1.0
    brightness: float = 1.0
    blend_mode: str = "OVERWRITE"  # OVERWRITE, ALPHA_BLEND, ADDITIVE, MULTIPLY, MAX, MASK
    channels: list[int] | None = None  # None = all channels
    target_opacity: float = 1.0
    transition_sec: float = 1.0  # Fade in duration
    fade_out_sec: float = 0.5    # Fade out duration

    @property
    def stop_time_sec(self) -> float:
        return round(self.start_time_sec + self.duration_sec, 3)

    def __post_init__(self) -> None:
        if not (0 <= self.target_layer <= 9):
            raise ValueError(f"target_layer must be in range 0..9, got {self.target_layer}")
        if self.start_time_sec < 0:
            raise ValueError("start_time_sec must be non-negative")
        if self.duration_sec < 0:
            raise ValueError("duration_sec must be non-negative")
        if self.transition_sec < 0:
            raise ValueError("transition_sec must be non-negative")
        if self.fade_out_sec < 0:
            raise ValueError("fade_out_sec must be non-negative")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SequenceStep:
        # Support both 'duration_sec' and legacy 'hold_duration_sec'
        dur = float(data.get("duration_sec", data.get("hold_duration_sec", 4.0)))
        start = float(data.get("start_time_sec", 0.0))
        return cls(
            id=str(data.get("id", "step_0")),
            name=str(data.get("name", "Step")),
            section=str(data.get("section", "Main")),
            target_layer=int(data.get("target_layer", 0)),
            start_time_sec=start,
            duration_sec=dur,
            pattern_id=str(data.get("pattern_id", "rainbow")),
            primary_color=str(data.get("primary_color", "#FF0000")),
            palette=data.get("palette"),
            speed=float(data.get("speed", 1.0)),
            brightness=float(data.get("brightness", 1.0)),
            blend_mode=str(data.get("blend_mode", "OVERWRITE")).upper(),
            channels=data.get("channels"),
            target_opacity=float(data.get("target_opacity", 1.0)),
            transition_sec=float(data.get("transition_sec", 1.0)),
            fade_out_sec=float(data.get("fade_out_sec", 0.5)),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["stop_time_sec"] = self.stop_time_sec
        return d


@dataclass
class SequenceData:
    """Full sequence document containing metadata and temporal steps."""
    name: str
    description: str = ""
    author: str = ""
    loop_mode: str = "infinite"  # infinite, count, once_hold, once_blackout
    loop_count: int = 1
    time_dilation: float = 1.0
    steps: list[SequenceStep] = field(default_factory=list)

    @property
    def total_duration(self) -> float:
        if not self.steps:
            return 0.0
        return max(s.stop_time_sec for s in self.steps)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SequenceData:
        raw_steps = data.get("steps", [])
        steps = []
        current_time = 0.0
        for s in raw_steps:
            step_obj = SequenceStep.from_dict(s)
            # Automatic migration for legacy files lacking start_time_sec
            if "start_time_sec" not in s and "hold_duration_sec" in s:
                step_obj.start_time_sec = current_time
                current_time = step_obj.stop_time_sec
            steps.append(step_obj)

        return cls(
            name=str(data.get("name", "Untitled Sequence")),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            loop_mode=str(data.get("loop_mode", "infinite")),
            loop_count=int(data.get("loop_count", 1)),
            time_dilation=float(data.get("time_dilation", 1.0)),
            steps=steps,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "loop_mode": self.loop_mode,
            "loop_count": self.loop_count,
            "time_dilation": self.time_dilation,
            "total_duration": self.total_duration,
            "steps": [s.to_dict() for s in self.steps],
        }


class SequenceRepository:
    """Filesystem repository for saving and loading JSON sequence files."""

    def __init__(self, directory: Path | str) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _safe_filename(self, name: str) -> str:
        clean = re.sub(r"[^\w\-_]", "_", name.strip().lower())
        if not clean:
            clean = "sequence"
        return f"{clean}.json"

    def list_sequences(self) -> list[dict[str, Any]]:
        """List summary of all sequence files."""
        summaries = []
        for file in sorted(self.directory.glob("*.json")):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                seq = SequenceData.from_dict(data)
                summaries.append({
                    "filename": file.name,
                    "name": seq.name,
                    "description": seq.description,
                    "step_count": len(seq.steps),
                    "total_duration": seq.total_duration,
                    "loop_mode": seq.loop_mode,
                })
            except Exception:
                continue
        return summaries

    def load_sequence(self, filename: str) -> SequenceData | None:
        """Load a sequence by filename."""
        path = self.directory / filename
        if not path.is_file():
            path = self.directory / f"{filename}.json"
        if not path.is_file():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SequenceData.from_dict(data)

    def save_sequence(self, sequence: SequenceData, filename: str | None = None) -> str:
        """Save sequence to disk and return filename."""
        target_name = filename or self._safe_filename(sequence.name)
        if not target_name.endswith(".json"):
            target_name += ".json"
        path = self.directory / target_name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sequence.to_dict(), f, indent=2)
        return target_name

    def delete_sequence(self, filename: str) -> bool:
        """Delete sequence file."""
        path = self.directory / filename
        if path.is_file():
            path.unlink()
            return True
        return False
