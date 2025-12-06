# 02_data/alias_repo.py
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from core.models import Alias
from helpers.paths import project_root


def _db_path() -> Path:
    """Return path to the aliases SQLite DB."""
    return project_root() / "aliases.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS aliases (
            codename      TEXT PRIMARY KEY,
            display_name  TEXT NOT NULL,
            project_name  TEXT,
            visual_style  TEXT,
            notes         TEXT,
            extra_json    TEXT
        )
        """
    )
    conn.commit()


def save_alias(alias: Alias) -> None:
    """
    Insert or update an alias.
    """
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO aliases (codename, display_name, project_name,
                                 visual_style, notes, extra_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(codename) DO UPDATE SET
                display_name  = excluded.display_name,
                project_name  = excluded.project_name,
                visual_style  = excluded.visual_style,
                notes         = excluded.notes,
                extra_json    = excluded.extra_json
            """,
            (
                alias.codename,
                alias.display_name,
                alias.project_name,
                alias.visual_style,
                alias.notes,
                json.dumps(alias.extra or {}),
            ),
        )


def get_alias(codename: str) -> Optional[Alias]:
    """Fetch a single alias by codename."""
    conn = _get_connection()
    cur = conn.execute(
        "SELECT * FROM aliases WHERE codename = ?",
        (codename,),
    )
    row = cur.fetchone()
    if not row:
        return None

    extra = json.loads(row["extra_json"]) if row["extra_json"] else {}
    return Alias(
        codename=row["codename"],
        display_name=row["display_name"],
        project_name=row["project_name"],
        visual_style=row["visual_style"],
        notes=row["notes"],
        extra=extra,
    )


def list_aliases() -> List[Alias]:
    """Return all aliases sorted by codename."""
    conn = _get_connection()
    cur = conn.execute("SELECT * FROM aliases ORDER BY codename ASC")
    aliases: List[Alias] = []
    for row in cur:
        extra = json.loads(row["extra_json"]) if row["extra_json"] else {}
        aliases.append(
            Alias(
                codename=row["codename"],
                display_name=row["display_name"],
                project_name=row["project_name"],
                visual_style=row["visual_style"],
                notes=row["notes"],
                extra=extra,
            )
        )
    return aliases


def delete_alias(codename: str) -> bool:
    """Delete alias; return True if any row was removed."""
    conn = _get_connection()
    with conn:
        cur = conn.execute(
            "DELETE FROM aliases WHERE codename = ?",
            (codename,),
        )
    return cur.rowcount > 0
