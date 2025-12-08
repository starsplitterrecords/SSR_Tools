# data/star_scheduler_repo.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple

from helpers.paths import ensure_dir, project_root as _current_project_root

from core.star_scheduler import (
    AliasColorMap,
    CatalogIndex,
    CatalogMatch,
    CatalogRecord,
    CatalogViewOptions,
    RecalcResult,
    SchedulerRow,
    SchedulerSettings,
    SchedulerState,
    ValidationReport,
    derive_aliases,
    ensure_alias_colors,
    normalize_row,
    recalculate_dates,
    validate_rows_against_catalog,
    find_catalog_match,
)


DEFAULT_ALIASES: List[str] = ["NMA", "SSB", "PWC", "AVO"]


__all__ = [
    # state / catalog I/O
    "load_state",
    "save_state",
    "load_catalog_index",
    "load_aliases_txt",
    # UI contract
    "init_scheduler_state",
    "init_scheduler_state_for_current_project",
    "add_row_from_catalog_pick",
    "recalculate_and_persist",
    "validate_and_report",
]


# ---------------------------------------------------------------------------
# 6. Storage API – State JSON
# ---------------------------------------------------------------------------


def _data_dir(project_root: str) -> Path:
    root = Path(project_root).expanduser().resolve()
    return ensure_dir(root / "_data")


def _state_path(project_root: str) -> Path:
    return _data_dir(project_root) / "scheduler_state.json"


def _default_settings() -> SchedulerSettings:
    return SchedulerSettings(
        min_gap_days=3,
        lock_existing_dates=False,
        ready_only=True,
        catalog_index_path="_data/catalog_index.json",
    )


def _default_state(project_root: str) -> SchedulerState:
    root_abs = str(Path(project_root).expanduser().resolve())
    return SchedulerState(
        project_root=root_abs,
        rows=[],
        colors={},
        settings=_default_settings(),
        read_only=False,
    )


def load_state(project_root: str) -> SchedulerState:
    """
    Load SchedulerState from _data/scheduler_state.json under project_root.
    Falls back to sensible defaults if missing/invalid, just like the rest
    of the repo’s data layer.
    """
    path = _state_path(project_root)
    if not path.exists():
        return _default_state(project_root)

    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return _default_state(project_root)

    state = SchedulerState.from_dict(
        raw,
        project_root=str(Path(project_root).expanduser().resolve()),
    )
    # Always normalize project_root to current absolute root
    state.project_root = str(Path(project_root).expanduser().resolve())
    return state


def save_state(project_root: str, state: SchedulerState) -> None:
    """
    Atomically persist SchedulerState to _data/scheduler_state.json.
    Mirrors the existing style used elsewhere (tmp + fsync + replace).
    """
    data_dir = _data_dir(project_root)
    final_path = _state_path(project_root)
    tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")

    payload = state.to_dict()

    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp_path, final_path)


# ---------------------------------------------------------------------------
# 6.2 Catalog index JSON
# ---------------------------------------------------------------------------


def _resolve_catalog_path(project_root: str, catalog_index_path: str) -> Path:
    p = Path(catalog_index_path)
    if p.is_absolute():
        return p
    root = Path(project_root).expanduser().resolve()
    return root / catalog_index_path


def load_catalog_index(
    project_root: str,
    catalog_index_path: str,
) -> Optional[CatalogIndex]:
    """
    Load CatalogIndex from JSON with shape:
      { "aliases": { "<ALIAS>": [ {adv_id, track, ...}, ... ] } }
    Returns None if file is missing/invalid; caller handles UI warning.
    """
    path = _resolve_catalog_path(project_root, catalog_index_path)
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return None

    aliases_mapping = (raw or {}).get("aliases") or {}
    if not isinstance(aliases_mapping, dict):
        return None

    return CatalogIndex.from_alias_mapping(aliases_mapping)


# ---------------------------------------------------------------------------
# 6.3 Aliases file
# ---------------------------------------------------------------------------


def load_aliases_txt(project_root: str) -> List[str]:
    """
    Load optional aliases.txt from project root, ignoring comments/blanks.
    This plays nicely with your existing text-based alias lists.
    """
    root = Path(project_root).expanduser().resolve()
    path = root / "aliases.txt"
    if not path.exists():
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []

    aliases: List[str] = []
    for line in text.splitlines():
        s = (line or "").strip()
        if not s or s.startswith("#"):
            continue
        aliases.append(s)
    return aliases


# ---------------------------------------------------------------------------
# 7. UI Integration Hooks (star_scheduler.ui_contract)
# ---------------------------------------------------------------------------


def init_scheduler_state(
    project_root: str,
) -> Tuple[SchedulerState, Optional[CatalogIndex], List[str]]:
    """
    Core entry for any Tk tab:
      - loads persisted state
      - loads catalog_index.json if present
      - merges aliases from catalog + aliases.txt + defaults
      - ensures alias colors are populated
    No dialogs, no Tk imports here.
    """
    state = load_state(project_root)
    catalog = load_catalog_index(project_root, state.settings.catalog_index_path)
    aliases_txt = load_aliases_txt(project_root)

    aliases = derive_aliases(
        catalog=catalog,
        aliases_txt_lines=aliases_txt,
        defaults=DEFAULT_ALIASES,
    )

    state.colors = ensure_alias_colors(aliases, state.colors)

    return state, catalog, aliases


def init_scheduler_state_for_current_project(
    project_root: Optional[str] = None,
) -> Tuple[SchedulerState, Optional[CatalogIndex], List[str]]:
    """
    Convenience wrapper for the existing SSR base:
    uses helpers.paths.project_root() when project_root is not provided.
    This lets a Tk tab call init_scheduler_state_for_current_project()
    without worrying about path plumbing.
    """
    root = project_root or str(_current_project_root())
    return init_scheduler_state(root)


def add_row_from_catalog_pick(
    state: SchedulerState,
    catalog: Optional[CatalogIndex],
    row: SchedulerRow,
    allow_manual: bool,
) -> Tuple[SchedulerState, CatalogMatch, bool]:
    """
    Normalize row, optionally require a catalog match, and append to state.rows.

    Returns:
        state:   possibly-updated state (rows list mutated).
        match:   CatalogMatch object (record may be None).
        added:   False when a match is required but missing (UI should confirm).
    """
    normalized = normalize_row(row)
    if catalog is not None:
        match = find_catalog_match(
            catalog=catalog,
            alias=normalized.alias,
            track=normalized.track,
            version=normalized.version,
            dna=normalized.dna,
        )
    else:
        match = CatalogMatch(
            alias=normalized.alias,
            track=normalized.track,
            version=normalized.version,
            dna=normalized.dna,
            record=None,
        )

    if catalog is not None and not allow_manual and match.record is None:
        # UI should confirm before adding; state unchanged
        return state, match, False

    state.rows.append(normalized)
    return state, match, True


def recalculate_and_persist(
    project_root: str,
    state: SchedulerState,
    today_date: str,
) -> RecalcResult:
    """
    Run recalc (pure core) and persist updated state via JSON.
    Callers (Tk tabs) can then update their table rows from result.state.rows.
    """
    result = recalculate_dates(state=state, today_date=today_date)
    save_state(project_root, result.state)
    return result


def validate_and_report(
    state: SchedulerState,
    catalog: CatalogIndex,
) -> ValidationReport:
    """
    Thin pass-through to core validation, for UI convenience.
    """
    return validate_rows_against_catalog(state=state, catalog=catalog)
