import os
import sqlite3
import yaml
from pathlib import Path
from datetime import datetime

# -----------------------
# CONFIG
# -----------------------
ASSETS_ROOT = r"C:\Users\jeffh\Documents\Star Splitter Records\assets"
DB_PATH = "catalog.db"

ASSETS_ROOT = ASSETS_ROOT.rstrip("\\") + "\\"


def parse_iso(dt_val):
    if not dt_val:
        return None
    if isinstance(dt_val, datetime):
        return dt_val.isoformat()
    if isinstance(dt_val, str):
        return dt_val.strip() or None
    return None


# -----------------------
# DB helpers (match existing schema)
# -----------------------

def upsert_work(con: sqlite3.Connection, row: dict):
    alias = row["alias"]
    uid = row["uid"]

    cur = con.cursor()
    cur.execute(
        "SELECT id FROM works WHERE alias=? AND uid=?",
        (alias, uid),
    )
    existing = cur.fetchone()

    title = row.get("title") or ""
    status = row.get("status") or ""
    folder_path = row.get("folder_path") or ""
    created_utc = parse_iso(row.get("created_utc"))
    planned_release_utc = parse_iso(row.get("planned_release_utc"))
    actual_release_utc = parse_iso(row.get("actual_release_utc"))

    if existing:
        work_id = existing[0]
        cur.execute(
            """
            UPDATE works
               SET title=?,
                   status=?,
                   folder_path=?,
                   created_utc=?,
                   planned_release_utc=?,
                   actual_release_utc=?
             WHERE id=?
            """,
            (
                title,
                status,
                folder_path,
                created_utc,
                planned_release_utc,
                actual_release_utc,
                work_id,
            ),
        )
        print(f"UPDATED: {alias}/{uid}")
    else:
        cur.execute(
            """
            INSERT INTO works
                (alias, uid, title, status, folder_path,
                 created_utc, planned_release_utc, actual_release_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alias,
                uid,
                title,
                status,
                folder_path,
                created_utc,
                planned_release_utc,
                actual_release_utc,
            ),
        )
        print(f"INSERTED: {alias}/{uid}")


# -----------------------
# Asset scan
# -----------------------

def scan_assets():
    works = []

    for alias in os.listdir(ASSETS_ROOT):
        alias_dir = os.path.join(ASSETS_ROOT, alias)
        if not os.path.isdir(alias_dir):
            continue

        for uid in os.listdir(alias_dir):
            work_dir = os.path.join(alias_dir, uid)
            if not os.path.isdir(work_dir):
                continue

            yaml_path = os.path.join(work_dir, "work.yaml")
            if not os.path.isfile(yaml_path):
                continue

            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"ERROR reading {yaml_path}: {e}")
                continue

            # Build row dict aligned to DB columns
            row = {}
            row["alias"] = alias
            row["uid"] = uid
            row["title"] = data.get("title") or data.get("name") or ""
            row["status"] = data.get("status") or ""
            row["folder_path"] = work_dir
            row["created_utc"] = data.get("created_utc") or data.get("created")
            row["planned_release_utc"] = (
                data.get("planned_release_utc") or data.get("planned_release")
            )
            row["actual_release_utc"] = (
                data.get("actual_release_utc") or data.get("actual_release")
            )

            works.append(row)

    return works


# -----------------------
# Main
# -----------------------

def main():
    if not Path(DB_PATH).exists():
        print("No catalog.db found at", DB_PATH)
        return

    con = sqlite3.connect(DB_PATH)

    # sanity check
    cols = con.execute("PRAGMA table_info(works)").fetchall()
    col_names = [c[1] for c in cols]
    required = [
        "id",
        "alias",
        "uid",
        "title",
        "status",
        "folder_path",
        "created_utc",
        "planned_release_utc",
        "actual_release_utc",
    ]
    missing = [c for c in required if c not in col_names]
    if missing:
        print("Schema mismatch; missing columns:", missing)
        con.close()
        return

    works = scan_assets()
    print(f"Found {len(works)} works in assets to upsert into catalog.db")

    for row in works:
        upsert_work(con, row)

    con.commit()
    con.close()
    print("Asset scan migration complete.")


if __name__ == "__main__":
    main()
