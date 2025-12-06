# 01_core/models/source_file.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any


@dataclass
class SourceFile:
    """
    Represents a raw input file for a Work (stems, reference mixes,
    source video, artwork PSD, etc.).
    """

    relative_path: str
    label: str | None = None
    notes: str | None = None
    tags: list[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "label": self.label,
            "notes": self.notes,
            "tags": self.tags,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceFile":
        return cls(
            relative_path=data.get("relative_path", ""),
            label=data.get("label"),
            notes=data.get("notes"),
            tags=list(data.get("tags", []) or []),
            extra=data.get("extra", {}) or {},
        )

    def resolved_path(self, work_folder: str | Path) -> Path:
        """Return the absolute path to this file given a work folder."""
        return Path(work_folder) / self.relative_path
