# 01_core/models/__init__.py
"""
Domain models for SSR Tools.

These are pure data structures with light validation and convenience
methods. They do not perform file or database I/O directly.
"""

from .alias import Alias
from .collateral import Collateral
from .source_file import SourceFile
from .work import Work

__all__ = [
    "Alias",
    "Collateral",
    "SourceFile",
    "Work",
]
