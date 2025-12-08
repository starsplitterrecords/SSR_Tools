from __future__ import annotations

import tkinter as tk

from helpers.events import EventBus
from gui import style


class BarSplitterTab(tk.Frame):
    """
    Placeholder Bar Splitter Tab (Tkinter).

    Original Flet version showed a static message:
    "Bar Splitter temporarily disabled."
    This Tkinter version preserves that behavior only.
    """

    def __init__(self, parent, eventbus: EventBus):
        super().__init__(parent, bg=style.MAIN_BG)
        self.eventbus = eventbus

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = tk.Frame(self, bg=style.MAIN_BG)
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        label = tk.Label(
            container,
            text="Bar Splitter temporarily disabled.",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
            font=(style.FONT_FAMILY, style.FONT_SIZE_LARGE, "bold"),
        )
        label.pack(anchor="center", expand=True)
