# 00_helpers/__init__.py
"""
Helper utilities (lowest layer).

These modules must not import from core, data, or gui.
They provide generic helpers such as path utilities, logging helpers, etc.
"""

__all__ = [
    "paths",
    "events",
]
