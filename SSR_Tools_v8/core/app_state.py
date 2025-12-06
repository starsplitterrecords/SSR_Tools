# core/app_state.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Callable, List

from core.models import Work, Alias


@dataclass
class AppState:
    """Global application state shared across tabs/dialogs."""

    # currently selected work (catalog or scheduler)
    selected_work: Optional[Work] = None

    # currently selected alias
    selected_alias: Optional[Alias] = None

    # subscribers notified when state changes
    _listeners: List[Callable[[], None]] = field(default_factory=list)

    # -------------------------------------------------------------

    def set_selected_work(self, work: Work | None):
        self.selected_work = work
        self._notify()

    def set_selected_alias(self, alias: Alias | None):
        self.selected_alias = alias
        self._notify()

    # -------------------------------------------------------------
    def subscribe(self, callback: Callable[[], None]):
        """Tabs can subscribe to state changes (auto-refresh)."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify(self):
        for cb in self._listeners:
            cb()
