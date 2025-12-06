# 01_core/models/collateral.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any


@dataclass
class Collateral:
    """
    Represents a single collateral asset associated with a Work
    (e.g. 'Audio-Mastered', 'Video-Promo', 'Artwork', etc.).
    """

    file_type: str
    filename: str
    label: str | None = None
    notes: str | None = None
    checksum: str | None = None
    size_bytes: int | None = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_type": self.file_type,
            "filename": self.filename,
            "label": self.label,
            "notes": self.notes,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Collateral":
        return cls(
            file_type=data.get("file_type", ""),
            filename=data.get("filename", ""),
            label=data.get("label"),
            notes=data.get("notes"),
            checksum=data.get("checksum"),
            size_bytes=data.get("size_bytes"),
            extra=data.get("extra", {}) or {},
        )

    def resolved_path(self, work_folder: str | Path) -> Path:
        """Return the full path to this collateral given a work folder."""
        return Path(work_folder) / self.filename
