# 01_core/scheduler/engine.py
from __future__ import annotations

from datetime import datetime
from typing import List, Dict

from core.models import Work


def schedule_release(work: Work, date: datetime) -> None:
    """Assign or update the planned release date."""
    work.planned_release_utc = date
    work.status = "Scheduled"


def get_scheduled(upcoming: List[Work]) -> List[Work]:
    """Return sorted works that have planned release dates."""
    return sorted(
        [w for w in upcoming if w.planned_release_utc],
        key=lambda w: w.planned_release_utc,
    )
