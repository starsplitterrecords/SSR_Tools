# 02_data/work_repo.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml  # type: ignore

from core.models import Work
from helpers.paths import ensure_dir


def work_yaml_path(work_folder: str | Path) -> Path:
    """Return the expected path to work.yaml under a work folder."""
    return Path(work_folder) / "work.yaml"


def load_work(path: str | Path) -> Work:
    """
    Load a Work from a work.yaml file.

    Raises:
        FileNotFoundError if file does not exist.
        ValueError if file contents are invalid.
    """
    p = Path(path)
    if p.is_dir():
        p = work_yaml_path(p)

    if not p.exists():
        raise FileNotFoundError(f"work.yaml not found at {p}")

    with p.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = yaml.safe_load(f) or {}

    return Work.from_dict(data)


def save_work(work: Work) -> Path:
    """
    Save a Work to work.yaml in its folder.

    Returns:
        The path to the written YAML file.
    """
    folder = ensure_dir(work.folder_path)
    p = work_yaml_path(folder)

    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(work.to_dict(), f, sort_keys=False)

    return p
