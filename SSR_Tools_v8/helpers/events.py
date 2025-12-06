# helpers/events.py
from __future__ import annotations
from typing import Callable, Dict, List


class EventBus:
    """
    Simple pub-sub event system for UI coordination.
    """

    def __init__(self):
        self._subs: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, callback: Callable):
        if event not in self._subs:
            self._subs[event] = []
        self._subs[event].append(callback)

    def publish(self, event: str, *args, **kwargs):
        for cb in self._subs.get(event, []):
            cb(*args, **kwargs)
