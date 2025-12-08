# core/star_scheduler.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 4. DTOs (Data Types)
# ---------------------------------------------------------------------------


@dataclass
class CatalogRecord:
    adv_id: Optional[str] = None
    track: Optional[str] = None
    version: Optional[str] = None
    dna: Optional[str] = None
    status: Optional[str] = None
    folder: Optional[str] = None
    yaml: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "adv_id": self.adv_id,
            "track": self.track,
            "version": self.version,
            "dna": self.dna,
            "status": self.status,
            "folder": self.folder,
            "yaml": self.yaml,
        }
        # extra wins only for unknown keys; known keys stay canonical
        for k, v in (self.extra or {}).items():
            if k not in data:
                data[k] = v
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CatalogRecord":
        data = data or {}
        known = {"adv_id", "track", "version", "dna", "status", "folder", "yaml"}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            adv_id=data.get("adv_id"),
            track=data.get("track"),
            version=data.get("version"),
            dna=data.get("dna"),
            status=data.get("status"),
            folder=data.get("folder"),
            yaml=data.get("yaml"),
            extra=extra or {},
        )


@dataclass
class CatalogIndex:
    records_by_alias: Dict[str, List[CatalogRecord]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aliases": {
                alias: [rec.to_dict() for rec in recs]
                for alias, recs in self.records_by_alias.items()
            }
        }

    @classmethod
    def from_alias_mapping(
        cls, mapping: Dict[str, List[Dict[str, Any]]]
    ) -> "CatalogIndex":
        mapping = mapping or {}
        return cls(
            records_by_alias={
                alias: [CatalogRecord.from_dict(rec) for rec in (records or [])]
                for alias, records in mapping.items()
            }
        )


@dataclass
class CatalogViewOptions:
    ready_only: bool = True


@dataclass
class SchedulerRow:
    date: str
    alias: str
    track: str
    version: str
    dna: str
    locked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "alias": self.alias,
            "track": self.track,
            "version": self.version,
            "dna": self.dna,
            "locked": bool(self.locked),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchedulerRow":
        data = data or {}
        return cls(
            date=(data.get("date") or "").strip(),
            alias=(data.get("alias") or "").strip(),
            track=(data.get("track") or "").strip(),
            version=(data.get("version") or "").strip(),
            dna=(data.get("dna") or "").strip(),
            locked=bool(data.get("locked", False)),
        )


AliasColorMap = Dict[str, str]


@dataclass
class SchedulerSettings:
    min_gap_days: int = 3
    lock_existing_dates: bool = False
    ready_only: bool = True
    catalog_index_path: str = "_data/catalog_index.json"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_gap_days": int(self.min_gap_days),
            "lock_existing_dates": bool(self.lock_existing_dates),
            "ready_only": bool(self.ready_only),
            "catalog_index_path": self.catalog_index_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchedulerSettings":
        data = data or {}
        return cls(
            min_gap_days=int(data.get("min_gap_days", 3)),
            lock_existing_dates=bool(data.get("lock_existing_dates", False)),
            ready_only=bool(data.get("ready_only", True)),
            catalog_index_path=data.get("catalog_index_path", "_data/catalog_index.json"),
        )


@dataclass
class SchedulerState:
    project_root: str
    rows: List[SchedulerRow] = field(default_factory=list)
    colors: AliasColorMap = field(default_factory=dict)
    settings: SchedulerSettings = field(default_factory=SchedulerSettings)
    read_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_root": self.project_root,
            "rows": [r.to_dict() for r in self.rows],
            "colors": dict(self.colors),
            "settings": self.settings.to_dict(),
            "read_only": bool(self.read_only),
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        project_root: Optional[str] = None,
    ) -> "SchedulerState":
        data = data or {}
        rows_data = data.get("rows") or []
        colors_data = data.get("colors") or {}
        settings_data = data.get("settings") or {}

        return cls(
            project_root=project_root or data.get("project_root") or "",
            rows=[SchedulerRow.from_dict(r) for r in rows_data],
            colors={str(k): str(v) for k, v in colors_data.items()},
            settings=SchedulerSettings.from_dict(settings_data),
            read_only=bool(data.get("read_only", False)),
        )


@dataclass
class CatalogMatch:
    alias: str
    track: str
    version: str
    dna: str
    record: Optional[CatalogRecord]


@dataclass
class RowValidationIssue:
    row_index: int
    reason: str


@dataclass
class ValidationReport:
    ok: bool
    invalid_indexes: List[int]
    issues: List[RowValidationIssue]


@dataclass
class RecalcChange:
    row_index: int
    old_date: str
    new_date: str


@dataclass
class RecalcResult:
    total_rows: int
    changed_count: int
    changes: List[RecalcChange]
    state: SchedulerState


__all__ = [
    # DTOs
    "CatalogRecord",
    "CatalogIndex",
    "CatalogViewOptions",
    "SchedulerRow",
    "SchedulerSettings",
    "SchedulerState",
    "CatalogMatch",
    "RowValidationIssue",
    "ValidationReport",
    "RecalcChange",
    "RecalcResult",
    "AliasColorMap",
    # APIs
    "derive_aliases",
    "ensure_alias_colors",
    "filter_catalog_for_alias",
    "find_catalog_match",
    "normalize_row",
    "sort_rows_for_processing",
    "recalculate_dates",
    "validate_rows_against_catalog",
]


# ---------------------------------------------------------------------------
# Helpers (pure, no repo coupling)
# ---------------------------------------------------------------------------


def _parse_iso_date(value: str, fallback: str) -> date:
    value = (value or "").strip()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return datetime.strptime(fallback, "%Y-%m-%d").date()


def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def _alias_to_pastel(alias: str) -> str:
    """
    Deterministic pastel color from alias string.
    Compatible with the rest of the codebase: just returns "#RRGGBB".
    """
    h = hash(alias) & 0xFFFFFF
    r = (h >> 16) & 0xFF
    g = (h >> 8) & 0xFF
    b = h & 0xFF

    # mix with white for pastel
    r = (r + 255) // 2
    g = (g + 255) // 2
    b = (b + 255) // 2

    return f"#{r:02X}{g:02X}{b:02X}"


# ---------------------------------------------------------------------------
# 5.1 Alias / Color helpers
# ---------------------------------------------------------------------------


def derive_aliases(
    catalog: Optional[CatalogIndex],
    aliases_txt_lines: Optional[List[str]],
    defaults: List[str],
) -> List[str]:
    """
    Combine aliases from catalog + aliases.txt into a sorted unique list.
    If nothing found, return defaults (e.g. existing SSR aliases).
    """
    aliases_set: set[str] = set()

    if catalog is not None:
        for alias in catalog.records_by_alias.keys():
            alias = (alias or "").strip()
            if alias:
                aliases_set.add(alias)

    if aliases_txt_lines:
        for line in aliases_txt_lines:
            raw = (line or "").strip()
            if not raw or raw.startswith("#"):
                continue
            aliases_set.add(raw)

    if not aliases_set:
        return list(defaults)

    return sorted(aliases_set)


def ensure_alias_colors(
    aliases: List[str],
    existing: AliasColorMap,
) -> AliasColorMap:
    """
    Ensure every alias has a color, reusing existing map where possible.
    Deterministic color generation; safe to persist in _data.
    """
    result: AliasColorMap = dict(existing or {})
    for alias in aliases:
        if alias not in result or not result[alias]:
            result[alias] = _alias_to_pastel(alias)
    return result


# ---------------------------------------------------------------------------
# 5.2 Catalog querying
# ---------------------------------------------------------------------------


def filter_catalog_for_alias(
    catalog: CatalogIndex,
    alias: str,
    view: CatalogViewOptions,
) -> List[CatalogRecord]:
    """
    Return records for alias, optionally filtered to status == 'ready'.
    """
    records = catalog.records_by_alias.get(alias, []) or []
    if not view.ready_only:
        return list(records)

    out: List[CatalogRecord] = []
    for rec in records:
        status = _norm(rec.status)
        if status == "ready":
            out.append(rec)
    return out


def find_catalog_match(
    catalog: CatalogIndex,
    alias: str,
    track: str,
    version: str,
    dna: str,
) -> CatalogMatch:
    """
    Case-insensitive, trimmed equality on track/version/dna within alias.
    Does not enforce ready_only.
    """
    needle_track = _norm(track)
    needle_version = _norm(version)
    needle_dna = _norm(dna)

    records = catalog.records_by_alias.get(alias, []) or []
    found: Optional[CatalogRecord] = None

    for rec in records:
        if _norm(rec.track) != needle_track:
            continue
        if _norm(rec.version) != needle_version:
            continue
        if _norm(rec.dna) != needle_dna:
            continue
        found = rec
        break

    return CatalogMatch(
        alias=alias,
        track=track,
        version=version,
        dna=dna,
        record=found,
    )


# ---------------------------------------------------------------------------
# 5.3 Row operations
# ---------------------------------------------------------------------------


def normalize_row(row: SchedulerRow) -> SchedulerRow:
    """
    Trim all string fields and normalize the locked flag.
    Returns a new instance to avoid accidental UI-state sharing.
    """
    return SchedulerRow(
        date=(row.date or "").strip(),
        alias=(row.alias or "").strip(),
        track=(row.track or "").strip(),
        version=(row.version or "").strip(),
        dna=(row.dna or "").strip(),
        locked=bool(row.locked),
    )


def sort_rows_for_processing(
    rows: List[SchedulerRow],
    today_date: str,
) -> List[int]:
    """
    Return indexes of rows sorted by (date, alias, track).
    Invalid dates fall back to today_date, which the caller supplies.
    """
    fallback = today_date

    def sort_key(idx: int) -> Tuple[date, str, str]:
        r = rows[idx]
        d = _parse_iso_date(r.date, fallback)
        alias_key = _norm(r.alias)
        track_key = _norm(r.track)
        return d, alias_key, track_key

    indexes = list(range(len(rows)))
    indexes.sort(key=sort_key)
    return indexes


# ---------------------------------------------------------------------------
# 5.4 Recalculate dates
# ---------------------------------------------------------------------------


def recalculate_dates(
    state: SchedulerState,
    today_date: str,
) -> RecalcResult:
    """
    Enforce min-gap per alias on SchedulerState.rows in-place, returning a
    RecalcResult with explicit change list. Compatible with the rest of the
    codebase: caller owns persistence via data layer.
    """
    order = sort_rows_for_processing(state.rows, today_date)
    last_for_alias: Dict[str, date] = {}
    changes: List[RecalcChange] = []

    settings = state.settings
    min_gap_days = int(settings.min_gap_days)

    for idx in order:
        row = state.rows[idx]
        alias_key = _norm(row.alias) or row.alias

        original_date_str = (row.date or "").strip()
        d = _parse_iso_date(original_date_str, today_date)

        if settings.lock_existing_dates and row.locked:
            last_for_alias[alias_key] = d
            continue

        prev = last_for_alias.get(alias_key)
        if prev is not None:
            min_allowed = prev + timedelta(days=min_gap_days)
            if d < min_allowed:
                new_date = min_allowed
                new_iso = new_date.isoformat()
                if new_iso != original_date_str:
                    row.date = new_iso
                    changes.append(
                        RecalcChange(
                            row_index=idx,
                            old_date=original_date_str,
                            new_date=new_iso,
                        )
                    )
                d = new_date

        last_for_alias[alias_key] = d

    return RecalcResult(
        total_rows=len(state.rows),
        changed_count=len(changes),
        changes=changes,
        state=state,
    )


# ---------------------------------------------------------------------------
# 5.5 Validation
# ---------------------------------------------------------------------------


def validate_rows_against_catalog(
    state: SchedulerState,
    catalog: CatalogIndex,
) -> ValidationReport:
    """
    Validate that each row has a matching ADV record.
    Leaves state unchanged; pure report for the UI layer.
    """
    issues: List[RowValidationIssue] = []
    invalid_indexes: List[int] = []

    for idx, row in enumerate(state.rows):
        match = find_catalog_match(
            catalog=catalog,
            alias=row.alias,
            track=row.track,
            version=row.version,
            dna=row.dna,
        )
        if match.record is None:
            reason = (
                f"No ADV match for {row.alias} / {row.track} "
                f"[{row.version}] – {row.dna}."
            )
            issues.append(RowValidationIssue(row_index=idx, reason=reason))
            invalid_indexes.append(idx)

    ok = not issues
    return ValidationReport(
        ok=ok,
        invalid_indexes=invalid_indexes,
        issues=issues,
    )
