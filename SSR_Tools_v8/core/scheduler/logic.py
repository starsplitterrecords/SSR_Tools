# core/scheduler/logic.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

from core.models import Work
from data import work_repo, catalog_repo


def get_scheduled_from_catalog() -> List[Work]:
    """
    Return all works with a planned_release_utc, sorted by date, alias, uid.
    """
    works = catalog_repo.list_works()
    scheduled = [
        w
        for w in works
        if getattr(w, "planned_release_utc", None) is not None
    ]
    scheduled.sort(
        key=lambda w: (
            w.planned_release_utc,  # type: ignore[arg-type]
            w.alias,
            w.uid,
        )
    )
    return scheduled


def validate_release_date(date: datetime) -> Tuple[bool, str]:
    """
    Basic validity checks for a release date.

    - reject dates in the past (by date, not exact time)
    - warn if date is more than 2 years in the future
    """
    today = datetime.utcnow().date()

    if date.date() < today:
        return False, "Release date cannot be in the past."

    two_years_out = datetime.utcnow().replace(year=datetime.utcnow().year + 2)
    if date > two_years_out:
        delta_days = (date.date() - today).days
        return True, f"Warning: release date is {delta_days} days away."

    return True, "Valid release date."


def get_release_statistics(scheduled: List[Work]) -> Dict[str, Any]:
    """
    Calculate simple statistics for scheduled releases.
    """
    now = datetime.utcnow()
    today = now.date()

    scheduled = [
        w for w in scheduled if getattr(w, "planned_release_utc", None) is not None
    ]

    total = len(scheduled)
    past = 0
    upcoming = 0
    this_month = 0
    this_quarter = 0

    for w in scheduled:
        d: datetime = w.planned_release_utc  # type: ignore[assignment]
        if d.date() < today:
            past += 1
        else:
            upcoming += 1

        if d.year == now.year and d.month == now.month:
            this_month += 1

        if d.year == now.year and ((d.month - 1) // 3) == ((now.month - 1) // 3):
            this_quarter += 1

    # Next upcoming release
    next_release: Work | None = None
    for w in sorted(
        scheduled,
        key=lambda w: (
            w.planned_release_utc,  # type: ignore[arg-type]
            w.alias,
            w.uid,
        ),
    ):
        d: datetime = w.planned_release_utc  # type: ignore[assignment]
        if d >= now:
            next_release = w
            break

    return {
        "total": total,
        "past": past,
        "upcoming": upcoming,
        "this_month": this_month,
        "this_quarter": this_quarter,
        "next_release": next_release,
    }


def validate_spacing(
    scheduled: List[Work],
    min_gap_days: int = 8,
    min_gap_any_days: int = 3,
) -> List[Dict[str, Any]]:
    """
    Check for spacing violations among scheduled releases.

    - per-alias spacing
    - global spacing between any releases
    """
    items = [
        w for w in scheduled if getattr(w, "planned_release_utc", None) is not None
    ]
    items = sorted(
        items,
        key=lambda w: (
            w.planned_release_utc,  # type: ignore[arg-type]
            w.alias,
            w.uid,
        ),
    )

    violations: List[Dict[str, Any]] = []
    if not items:
        return violations

    # per-alias
    by_alias: Dict[str, List[Work]] = {}
    for w in items:
        by_alias.setdefault(w.alias, []).append(w)

    for alias, works in by_alias.items():
        for i in range(len(works) - 1):
            w1 = works[i]
            w2 = works[i + 1]
            d1: datetime = w1.planned_release_utc  # type: ignore[assignment]
            d2: datetime = w2.planned_release_utc  # type: ignore[assignment]
            gap = (d2.date() - d1.date()).days
            if gap < min_gap_days:
                violations.append(
                    {
                        "type": "per_alias",
                        "alias": alias,
                        "work1": w1,
                        "work2": w2,
                        "gap_days": gap,
                        "required_days": min_gap_days,
                        "message": (
                            f"{alias}: only {gap} days between "
                            f"{w1.uid} and {w2.uid} (need {min_gap_days})"
                        ),
                    }
                )

    # global spacing
    for i in range(len(items) - 1):
        w1 = items[i]
        w2 = items[i + 1]
        if w1.alias == w2.alias:
            continue
        d1 = w1.planned_release_utc  # type: ignore[assignment]
        d2 = w2.planned_release_utc  # type: ignore[assignment]
        gap = (d2.date() - d1.date()).days
        if gap < min_gap_any_days:
            violations.append(
                {
                    "type": "global",
                    "alias1": w1.alias,
                    "alias2": w2.alias,
                    "work1": w1,
                    "work2": w2,
                    "gap_days": gap,
                    "required_days": min_gap_any_days,
                    "message": (
                        f"{w1.alias} → {w2.alias}: only {gap} days between "
                        f"{w1.uid} and {w2.uid} (need {min_gap_any_days})"
                    ),
                }
            )

    return violations


def recalculate_schedule(
    scheduled: List[Work],
    min_gap_days: int = 8,
    min_gap_any_days: int = 3,
) -> Tuple[int, int]:
    """
    Recalculate planned_release_utc for all scheduled works to respect spacing.

    Returns: (total_scheduled, changed_count)
    """
    # Filter to works with a date; keep references
    items = [
        w for w in scheduled if getattr(w, "planned_release_utc", None) is not None
    ]
    items = sorted(
        items,
        key=lambda w: (
            w.planned_release_utc,  # type: ignore[arg-type]
            w.alias,
            w.uid,
        ),
    )

    alias_last: Dict[str, datetime] = {}
    last_any: datetime | None = None
    changed = 0

    for w in items:
        current: datetime = w.planned_release_utc  # type: ignore[assignment]
        target = current

        if w.alias in alias_last:
            alias_min = alias_last[w.alias] + timedelta(days=min_gap_days)
            if alias_min > target:
                target = alias_min

        if last_any is not None:
            global_min = last_any + timedelta(days=min_gap_any_days)
            if global_min > target:
                target = global_min

        if target != current:
            w.planned_release_utc = target
            changed += 1

        alias_last[w.alias] = w.planned_release_utc  # type: ignore[index]
        if last_any is None or w.planned_release_utc > last_any:  # type: ignore[operator]
            last_any = w.planned_release_utc  # type: ignore[assignment]

    # Persist all scheduled works (changed and unchanged; cheap and simple)
    for w in items:
        work_repo.save_work(w)
        catalog_repo.save_work_to_catalog(w)

    return len(items), changed
