from __future__ import annotations

from datetime import datetime

import tkinter as tk
from tkinter import ttk

from core.models import Work
from data import catalog_repo
from helpers.events import EventBus
from gui.tabs.details_tab import DetailsTab


class CatalogTab(tk.Frame):
    """
    Catalog + Details split pane.
    """

    def __init__(self, parent, eventbus: EventBus):
        super().__init__(parent, bg="#1e1e1e")
        self.eventbus = eventbus

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg="#1e1e1e")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        tk.Label(
            header,
            text="Catalog",
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

        tk.Button(header, text="Refresh", command=self._manual_refresh).pack(
            side="right"
        )

        # Left table
        left = tk.Frame(self, bg="#1e1e1e")
        left.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        columns = ("alias", "uid", "title", "status", "planned")
        self.table = ttk.Treeview(left, columns=columns, show="headings")
        for col, text in zip(
            columns,
            ["Alias", "UID", "Title", "Status", "Planned Release"],
        ):
            self.table.heading(col, text=text)
            self.table.column(col, width=100 if col != "title" else 240, anchor="w")

        self.table.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(left, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

        self.table.bind("<<TreeviewSelect>>", self._on_select)

        # Right: Details
        self.details = DetailsTab(self, eventbus)
        self.details.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)

        eventbus.subscribe("work_created", lambda w: self.refresh())
        eventbus.subscribe("work_updated", lambda w: self.refresh())

    # ------------------------------------------------------------------ helpers

    def _manual_refresh(self) -> None:
        self.refresh()

    def _make_id(self, work: Work) -> str:
        return f"{work.alias}::{work.uid}"

    def _on_select(self, event) -> None:
        sel = self.table.selection()
        if not sel:
            return
        item_id = sel[0]
        alias, uid = item_id.split("::", 1)
        from data import catalog_repo

        w = catalog_repo.get_work(alias, uid)
        if w:
            self.eventbus.publish("work_selected", w)

    # ------------------------------------------------------------------ data

    def refresh(self) -> None:
        for row in self.table.get_children():
            self.table.delete(row)

        works = catalog_repo.list_works()
        works.sort(
            key=lambda w: (
                getattr(w, "planned_release_utc", None) or datetime.max,
                w.alias,
                w.uid,
            )
        )

        for w in works:
            planned = (
                w.planned_release_utc.isoformat()
                if getattr(w, "planned_release_utc", None)
                else ""
            )
            self.table.insert(
                "",
                "end",
                iid=self._make_id(w),
                values=(w.alias, w.uid, w.title, getattr(w, "status", "") or "", planned),
            )
