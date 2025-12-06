# 01_core/__init__.py
"""
Core layer (business logic).

This package contains:
- Domain models (Work, Alias, Collateral, SourceFile)
- Engines (video, image, scheduler, prompt)
"""

__all__ = [
    "models",
    "video",
    "image",
    "prompt",
    "scheduler",
]
