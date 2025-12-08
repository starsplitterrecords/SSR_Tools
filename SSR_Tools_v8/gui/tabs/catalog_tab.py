from __future__ import annotations

from datetime import datetime

import tkinter as tk
from tkinter import ttk

from core.models import Work
from data import catalog_repo
from helpers.events import EventBus

from gui import style
from gui.layouts.two_pane import TwoPane
from gui.tabs.details_tab import DetailsTab


class CatalogTab(tk.Frame):
    """
    Catalog + Details displayed using standardized TwoPane layout.

    Left pane: work table
    Right pane: embedded DetailsTab
    """

    def __init__(self, parent, eventbus: EventBus):
        super().__init__(parent, bg=style.MAIN_BG)
        self.eventbus = eventbus

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ------------------------------------------------------------------
        # HEADER
        # ------------------------------------------------------------------
        header = tk.Frame(self, bg=style.MAIN_BG)
        header.grid(row=0, column=0, sticky="ew", padx=style.PAD_X, pady=style.PAD_Y)

        tk.Label(
            header,
            text="Catalog",
            font=(style.FONT_FAMILY, style.FONT_SIZE_LARGE, "bold"),
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).pack(side="left")

        tk.Button(
            header,
            text="Refresh",
            command=self.refresh,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="right")

        # ------------------------------------------------------------------
        # PANE LAYOUT
        # ------------------------------------------------------------------
        pane = TwoPane(
            self,
            left_scroll=False,
            right_scroll=True,
            left_width=380,
        )
        pane.grid(row=1, column=0, sticky="nsew", padx=style.PAD_X, pady=(0, style.PAD_Y))
        self.pane = pane

        # ------------------------------------------------------------------
        # LEFT TABLE
        # ------------------------------------------------------------------
        self._build_table(pane.left)

        # ------------------------------------------------------------------
        # RIGHT DETAILS PANEL
        # ------------------------------------------------------------------
        self.details = DetailsTab(pane.right, self.eventbus)

        # Event subscriptions
        eventbus.subscribe("work_created", lambda w: self.refresh())
        eventbus.subscribe("work_updated", lambda w: self.refresh())

    # ----------------------------------------------------------------------
    # TABLE
    # ----------------------------------------------------------------------

    def _build_table(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        tk.Label(
            parent,
            text="Works",
            fg=style.MAIN_FG,
            bg=style.MAIN_BG,
            font=(style.FONT_FAMILY, style.FONT_SIZE_BASE, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, style.PAD_Y))

        columns = ("alias", "uid", "title", "status", "planned")
        self.table = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=20,
        )

        col_config = {
            "alias": 80,
            "uid": 80,
            "title": 200,
            "status": 120,
            "planned": 160,
        }

        headings = {
            "alias": "Alias",
            "uid": "UID",
            "title": "Title",
            "status": "Status",
            "planned": "Planned Release",
        }

        for col in columns:
            self.table.heading(col, text=headings[col])
            self.table.column(col, width=col_config[col], anchor="w")

        self.table.grid(row=1, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")

        self.table.bind("<<TreeviewSelect>>", self._on_select)

    # ----------------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------------

    @staticmethod
    def _make_id(work: Work) -> str:
        return f"{work.alias}::{work.uid}"

    def _on_select(self, event) -> None:
        sel = self.table.selection()
        if not sel:
            return

        item_id = sel[0]
        alias, uid = item_id.split("::", 1)

        w = catalog_repo.get_work(alias, uid)
        if w:
            self.eventbus.publish("work_selected", w)

    # ----------------------------------------------------------------------
    # DATA REFRESH
    # ----------------------------------------------------------------------

    def refresh(self) -> None:
        # Clear table
        for row in self.table.get_children():
            self.table.delete(row)

        # Load works
        works = catalog_repo.list_works()
        works.sort(
            key=lambda w: (
                getattr(w, "planned_release_utc", None) or datetime.max,
                w.alias,
                w.uid,
            )
        )

        # Populate
        for w in works:
            planned_str = (
                w.planned_release_utc.isoformat()
                if getattr(w, "planned_release_utc", None)
                else ""
            )
            self.table.insert(
                "",
                "end",
                iid=self._make_id(w),
                values=(
                    w.alias,
                    w.uid,
                    w.title,
                    getattr(w, "status", "") or "",
                    planned_str,
                ),
            )
