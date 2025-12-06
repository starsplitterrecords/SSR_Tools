# 00_helpers/paths.py
"""
Path and filesystem helpers.
"""

from __future__ import annotations

import os
from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if it does not exist and return it as a Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def project_root() -> Path:
    """
    Return the project root directory.

    Assumes this file lives in 00_helpers/ under the project root.
    """
    return Path(__file__).resolve().parent.parent
