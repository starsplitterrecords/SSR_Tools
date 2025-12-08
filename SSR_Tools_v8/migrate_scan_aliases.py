import os
import sqlite3
from pathlib import Path

# -----------------------
# CONFIG
# -----------------------
ASSETS_ROOT = r"C:\Users\jeffh\Documents\Star Splitter Records\assets"
DB_PATH = "aliases.db"

ASSETS_ROOT = ASSETS_ROOT.rstrip("\\") + "\\"


def get_alias_folders():
    aliases = []
    for name in os.listdir(ASSETS_ROOT):
        full = os.path.join(ASSETS_ROOT, name)
        if os.path.isdir(full):
            aliases.append(name)
    return sorted(set(aliases))


def upsert_alias(con: sqlite3.Connection, codename: str):
    """
    Match your exact table schema:
      codename TEXT PRIMARY KEY
      display_name TEXT NOT NULL
      project_name TEXT NULL
      visual_style TEXT NULL
      notes TEXT NULL
      extra_json TEXT NULL
    """
    cur = con.cursor()

    # Check existing
    cur.execute("SELECT codename FROM aliases WHERE codename = ?", (codename,))
    exists = cur.fetchone()

    if exists:
        print(f"EXISTS: {codename}")
        return

    # We insert minimal valid row
    display_name = codename
    project_name = ""
    visual_style = ""
    notes = ""
    extra_json = ""

    cur.execute(
        """
        INSERT INTO aliases
            (codename, display_name, project_name, visual_style, notes, extra_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            codename,
            display_name,
            project_name,
            visual_style,
            notes,
            extra_json,
        ),
    )
    print(f"INSERTED: {codename}")


def main():
    if not Path(DB_PATH).exists():
        print("No aliases.db found at", DB_PATH)
        return

    con = sqlite3.connect(DB_PATH)

    # sanity check schema
    cols = con.execute("PRAGMA table_info(aliases)").fetchall()
    col_names = [c[1] for c in cols]
    required = ["codename", "display_name"]
    for r in required:
        if r not in col_names:
            print("Invalid aliases table schema. Missing:", r)
            con.close()
            return

    aliases = get_alias_folders()
    print(f"Found {len(aliases)} alias folders.")

    for codename in aliases:
        upsert_alias(con, codename)

    con.commit()
    con.close()
    print("Alias scan migration complete.")


if __name__ == "__main__":
    main()
