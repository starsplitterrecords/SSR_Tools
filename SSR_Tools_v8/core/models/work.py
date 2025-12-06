# 01_core/models/work.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List

from .alias import Alias
from .collateral import Collateral
from .source_file import SourceFile


@dataclass
class Work:
    """
    Represents a single musical work/release.

    This is a pure domain model; it does not know how to read/write YAML
    or touch the filesystem. That is handled by the data layer.
    """

    alias: str          # alias codename
    uid: str            # per-alias work ID, e.g. "PWC001"
    title: str
    folder_path: str

    status: str = "Unrouted"
    created_utc: datetime | None = None
    planned_release_utc: datetime | None = None
    actual_release_utc: datetime | None = None

    # Optional planning / metadata fields used by the UI
    campaign: str | None = None
    router_inbox: str | None = None
    assets_root: str | None = None
    output_folder: str | None = None

    source_files: List[SourceFile] = field(default_factory=list)
    collateral: List[Collateral] = field(default_factory=list)
    notes: str | None = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict suitable for YAML/JSON."""
        return {
            "alias": self.alias,
            "uid": self.uid,
            "title": self.title,
            "folder_path": self.folder_path,
            "status": self.status,
            "created_utc": self.created_utc.isoformat() if self.created_utc else None,
            "planned_release_utc": (
                self.planned_release_utc.isoformat()
                if self.planned_release_utc
                else None
            ),
            "actual_release_utc": (
                self.actual_release_utc.isoformat()
                if self.actual_release_utc
                else None
            ),
            "campaign": self.campaign,
            "router_inbox": self.router_inbox,
            "assets_root": self.assets_root,
            "output_folder": self.output_folder,
            "source_files": [sf.to_dict() for sf in self.source_files],
            "collateral": [c.to_dict() for c in self.collateral],
            "notes": self.notes,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Work":
        """Construct a Work from a dict."""
        def parse_dt(val: Any):
            if not val:
                return None
            return datetime.fromisoformat(val)

        return cls(
            alias=data.get("alias", ""),
            uid=data.get("uid", ""),
            title=data.get("title", ""),
            folder_path=data.get("folder_path", ""),
            status=data.get("status", "Unrouted"),
            created_utc=parse_dt(data.get("created_utc")),
            planned_release_utc=parse_dt(data.get("planned_release_utc")),
            actual_release_utc=parse_dt(data.get("actual_release_utc")),
            campaign=data.get("campaign"),
            router_inbox=data.get("router_inbox"),
            assets_root=data.get("assets_root"),
            output_folder=data.get("output_folder"),
            source_files=[
                SourceFile.from_dict(sf) for sf in data.get("source_files", []) or []
            ],
            collateral=[
                Collateral.from_dict(c) for c in data.get("collateral", []) or []
            ],
            notes=data.get("notes"),
            extra=data.get("extra", {}) or {},
        )
