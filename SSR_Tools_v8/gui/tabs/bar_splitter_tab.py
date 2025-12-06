from __future__ import annotations

import tkinter as tk


class BarSplitterTab(tk.Frame):
    """
    Placeholder Bar Splitter Tab.
    The beat-synced engine can be wired later.
    """

    def __init__(self, parent, eventbus):
        super().__init__(parent, bg="#1e1e1e")
        self.eventbus = eventbus

        label = tk.Label(
            self,
            text="Bar Splitter\n(This feature is currently disabled.)",
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Segoe UI", 12),
            justify="left",
        )
        label.pack(anchor="nw", padx=10, pady=10)
