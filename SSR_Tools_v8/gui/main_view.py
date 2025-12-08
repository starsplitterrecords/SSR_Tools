from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from core.app_state import AppState
from helpers.events import EventBus

from gui import style
from gui.tabs.catalog_tab import CatalogTab
from gui.tabs.alias_tab import AliasTab
from gui.tabs.router_tab import RouterTab
from gui.tabs.bar_splitter_tab import BarSplitterTab
from gui.tabs.image_splitter_tab import ImageSplitterTab
from gui.tabs.scheduler_tab import SchedulerTab

from gui.dialogs.new_work_dialog import NewWorkDialog
from gui.dialogs.settings_dialog import SettingsDialog


class MainWindow:
    """
    SSR Tools v8 — Main Window (Tkinter)
    Uses a TOP NAVIGATION BAR (A1+B1 spec):
        [Prev]  [Catalog] [Router] [BarSplitter] [Image] [Scheduler] [Aliases]  [Next] ... (right side: New Work, Settings)

    No sidebar. Content area shows the active tab.
    """

    TAB_ORDER = [
        "catalog",
        "router",
        "bar",
        "image",
        "scheduler",
        "aliases",
    ]

    TAB_LABELS = {
        "catalog": "Catalog",
        "router": "Router",
        "bar": "Bar Splitter",
        "image": "Image Splitter",
        "scheduler": "Scheduler",
        "aliases": "Aliases",
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        style.apply_global_style(root)

        self.state = AppState()
        self.events = EventBus()

        self._build_layout()
        self._init_tabs()

    # ----------------------------------------------------------------------
    # LAYOUT
    # ----------------------------------------------------------------------

    def _build_layout(self) -> None:
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # --------------------------------------------------------------
        # TOP NAV BAR
        # --------------------------------------------------------------
        bar = tk.Frame(self.root, bg=style.TOPBAR_BG, height=44)
        bar.grid(row=0, column=0, sticky="nsew")
        bar.grid_propagate(False)

        # Left: Prev
        prev_btn = tk.Button(
            bar,
            text="◀",
            command=self._prev_tab,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
            width=4,
        )
        prev_btn.pack(side="left", padx=style.PAD_X)

        # Center: Tab Buttons
        center = tk.Frame(bar, bg=style.TOPBAR_BG)
        center.pack(side="left", padx=style.PAD_X_LARGE)

        self._tab_buttons: dict[str, tk.Button] = {}

        for key in self.TAB_ORDER:
            btn = tk.Button(
                center,
                text=self.TAB_LABELS[key],
                command=lambda k=key: self._switch_tab(k),
                bg=style.BUTTON_BG,
                fg=style.BUTTON_FG,
            )
            btn.pack(side="left", padx=4, pady=6)
            self._tab_buttons[key] = btn

        # Right: Next + Actions
        right = tk.Frame(bar, bg=style.TOPBAR_BG)
        right.pack(side="right", padx=style.PAD_X)

        next_btn = tk.Button(
            right,
            text="▶",
            command=self._next_tab,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
            width=4,
        )
        next_btn.pack(side="left", padx=style.PAD_X)

        tk.Button(
            right,
            text="New Work",
            command=self._open_new_work,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="left", padx=style.PAD_X)

        tk.Button(
            right,
            text="Settings",
            command=self._open_settings,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="left", padx=style.PAD_X)

        # --------------------------------------------------------------
        # CONTENT AREA
        # --------------------------------------------------------------
        self.content = tk.Frame(self.root, bg=style.MAIN_BG)
        self.content.grid(row=1, column=0, sticky="nsew")

    # ----------------------------------------------------------------------
    # TABS
    # ----------------------------------------------------------------------

    def _init_tabs(self) -> None:
        """Create tab instances but only pack active tab."""
        self.tabs: dict[str, tk.Widget] = {
            "catalog": CatalogTab(self.content, self.events),
            "router": RouterTab(self.content, self.events),
            "bar": BarSplitterTab(self.content, self.events),
            "image": ImageSplitterTab(self.content, self.events),
            "scheduler": SchedulerTab(self.content, self.events),
            "aliases": AliasTab(self.content, self.events),
        }

        self.active_tab: str | None = None
        self._switch_tab("catalog")

    def _switch_tab(self, key: str) -> None:
        if self.active_tab is not None:
            self.tabs[self.active_tab].pack_forget()

        self.active_tab = key
        widget = self.tabs[key]
        widget.pack(fill="both", expand=True)

        # Update tab button highlight
        for k, btn in self._tab_buttons.items():
            if k == key:
                btn.configure(relief="sunken", bg=style.HIGHLIGHT_BG)
            else:
                btn.configure(relief="raised", bg=style.BUTTON_BG)

        # Auto-refresh tab if it has refresh()
        if hasattr(widget, "refresh"):
            widget.refresh()

    # ----------------------------------------------------------------------
    # TAB CYCLING
    # ----------------------------------------------------------------------

    def _prev_tab(self) -> None:
        if not self.active_tab:
            return
        idx = self.TAB_ORDER.index(self.active_tab)
        idx = (idx - 1) % len(self.TAB_ORDER)
        self._switch_tab(self.TAB_ORDER[idx])

    def _next_tab(self) -> None:
        if not self.active_tab:
            return
        idx = self.TAB_ORDER.index(self.active_tab)
        idx = (idx + 1) % len(self.TAB_ORDER)
        self._switch_tab(self.TAB_ORDER[idx])

    # ----------------------------------------------------------------------
    # DIALOGS
    # ----------------------------------------------------------------------

    def _open_new_work(self):
        NewWorkDialog(self.root, self.events)

    def _open_settings(self):
        SettingsDialog(self.root)
