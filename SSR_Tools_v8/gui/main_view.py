from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from core.app_state import AppState
from helpers.events import EventBus

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
    Main application window (Tkinter).
    """

    def __init__(self, root: tk.Tk):
        self.root = root

        self.state = AppState()
        self.events = EventBus()

        self._build_layout()
        self._init_tabs()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)

        # Top bar
        bar = tk.Frame(self.root, bg="#303030", height=40)
        bar.grid(row=0, column=0, columnspan=2, sticky="nsew")
        bar.grid_propagate(False)

        title_lbl = tk.Label(
            bar,
            text="SSR Tools",
            bg="#303030",
            fg="#ffffff",
            font=("Segoe UI", 14, "bold"),
        )
        title_lbl.pack(side="left", padx=10, pady=5)

        btn_settings = tk.Button(
            bar,
            text="Settings",
            command=self._open_settings,
        )
        btn_settings.pack(side="right", padx=5, pady=5)

        btn_new = tk.Button(
            bar,
            text="New Work",
            command=self._open_new_work,
        )
        btn_new.pack(side="right", padx=5, pady=5)

        # Sidebar
        sidebar = tk.Frame(self.root, bg="#252525", width=200)
        sidebar.grid(row=1, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=0)

        buttons = [
            ("Catalog", "catalog"),
            ("Router", "router"),
            ("Bar Splitter", "bar"),
            ("Image Splitter", "image"),
            ("Scheduler", "scheduler"),
            ("Aliases", "aliases"),
        ]

        self._nav_buttons: dict[str, tk.Button] = {}

        for label, key in buttons:
            btn = tk.Button(
                sidebar,
                text=label,
                anchor="w",
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(fill="x", padx=5, pady=2)
            self._nav_buttons[key] = btn

        # Content area
        self.content = tk.Frame(self.root, bg="#1e1e1e")
        self.content.grid(row=1, column=1, sticky="nsew")

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    def _init_tabs(self) -> None:
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
            old = self.tabs[self.active_tab]
            old.pack_forget()

        self.active_tab = key
        widget = self.tabs[key]
        widget.pack(fill="both", expand=True)

        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(relief="sunken")
            else:
                btn.configure(relief="raised")

        if hasattr(widget, "refresh"):
            widget.refresh()

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    def _open_new_work(self) -> None:
        NewWorkDialog(self.root, self.events)

    def _open_settings(self) -> None:
        SettingsDialog(self.root)
