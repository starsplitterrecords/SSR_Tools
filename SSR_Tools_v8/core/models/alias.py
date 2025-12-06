# 01_core/models/alias.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Alias:
    """Represents an artist/alias in the SSR ecosystem."""

    codename: str
    display_name: str
    project_name: str | None = None
    visual_style: str | None = None
    notes: str | None = None
    # Additional metadata fields can be added as needed
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "codename": self.codename,
            "display_name": self.display_name,
            "project_name": self.project_name,
            "visual_style": self.visual_style,
            "notes": self.notes,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alias":
        """Construct an Alias from a plain dictionary."""
        return cls(
            codename=data.get("codename", ""),
            display_name=data.get("display_name", ""),
            project_name=data.get("project_name"),
            visual_style=data.get("visual_style"),
            notes=data.get("notes"),
            extra=data.get("extra", {}) or {},
        )
