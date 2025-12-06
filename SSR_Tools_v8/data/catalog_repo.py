# 02_data/catalog_repo.py
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from core.models import Work
from helpers.paths import project_root


def _db_path() -> Path:
    """Return path to the catalog SQLite DB."""
    return project_root() / "catalog.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS works (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            alias                TEXT NOT NULL,
            uid                  TEXT NOT NULL,
            title                TEXT NOT NULL,
            status               TEXT NOT NULL,
            folder_path          TEXT NOT NULL,
            created_utc          TEXT,
            planned_release_utc  TEXT,
            actual_release_utc   TEXT,
            UNIQUE(alias, uid)
        )
        """
    )
    conn.commit()


def _dt_to_str(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _str_to_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    return datetime.fromisoformat(val)


def save_work_to_catalog(work: Work) -> None:
    """
    Insert or update a Work into the catalog DB.

    NOTE: This does NOT write work.yaml; that is handled by data.work_repo.
    """
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO works (alias, uid, title, status, folder_path,
                               created_utc, planned_release_utc, actual_release_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alias, uid) DO UPDATE SET
                title               = excluded.title,
                status              = excluded.status,
                folder_path         = excluded.folder_path,
                created_utc         = excluded.created_utc,
                planned_release_utc = excluded.planned_release_utc,
                actual_release_utc  = excluded.actual_release_utc
            """,
            (
                work.alias,
                work.uid,
                work.title,
                work.status,
                work.folder_path,
                _dt_to_str(work.created_utc),
                _dt_to_str(work.planned_release_utc),
                _dt_to_str(work.actual_release_utc),
            ),
        )


def get_work(alias: str, uid: str) -> Optional[Work]:
    """Fetch a Work by (alias, uid)."""
    conn = _get_connection()
    cur = conn.execute(
        "SELECT * FROM works WHERE alias = ? AND uid = ?",
        (alias, uid),
    )
    row = cur.fetchone()
    if not row:
        return None

    return Work(
        alias=row["alias"],
        uid=row["uid"],
        title=row["title"],
        folder_path=row["folder_path"],
        status=row["status"],
        created_utc=_str_to_dt(row["created_utc"]),
        planned_release_utc=_str_to_dt(row["planned_release_utc"]),
        actual_release_utc=_str_to_dt(row["actual_release_utc"]),
    )


def list_works() -> List[Work]:
    """Return all works from the catalog."""
    conn = _get_connection()
    cur = conn.execute(
        "SELECT * FROM works ORDER BY alias ASC, uid ASC"
    )

    works: List[Work] = []
    for row in cur:
        works.append(
            Work(
                alias=row["alias"],
                uid=row["uid"],
                title=row["title"],
                folder_path=row["folder_path"],
                status=row["status"],
                created_utc=_str_to_dt(row["created_utc"]),
                planned_release_utc=_str_to_dt(row["planned_release_utc"]),
                actual_release_utc=_str_to_dt(row["actual_release_utc"]),
            )
        )
    return works


def list_works_by_alias(alias: str) -> List[Work]:
    """Return all works for a given alias."""
    conn = _get_connection()
    cur = conn.execute(
        "SELECT * FROM works WHERE alias = ? ORDER BY uid ASC",
        (alias,),
    )

    works: List[Work] = []
    for row in cur:
        works.append(
            Work(
                alias=row["alias"],
                uid=row["uid"],
                title=row["title"],
                folder_path=row["folder_path"],
                status=row["status"],
                created_utc=_str_to_dt(row["created_utc"]),
                planned_release_utc=_str_to_dt(row["planned_release_utc"]),
                actual_release_utc=_str_to_dt(row["actual_release_utc"]),
            )
        )
    return works
