# 02_data/config_repo.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml  # type: ignore

from helpers.paths import project_root, ensure_dir


CONFIG_DIR_NAME = "config"
CONFIG_FILE_NAME = "config.yaml"


def _config_path() -> Path:
    root = project_root()
    cfg_dir = ensure_dir(root / CONFIG_DIR_NAME)
    return cfg_dir / CONFIG_FILE_NAME


def load_config() -> Dict[str, Any]:
    """Load application configuration from YAML, or return defaults."""
    path = _config_path()
    if not path.exists():
        return {
            "assets_root_path": "",
            "router_inbox_path": "",
            "preview_mode": True,
            "auto_refresh_router": True,
            "refresh_interval_seconds": 60,
        }

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def save_config(data: Dict[str, Any]) -> None:
    """Persist configuration to YAML."""
    path = _config_path()
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=True)


def get_assets_root_path() -> str:
    cfg = load_config()
    return cfg.get("assets_root_path", "") or ""


def set_assets_root_path(path: str) -> None:
    cfg = load_config()
    cfg["assets_root_path"] = path
    save_config(cfg)
