import tkinter as tk
from tkinter import ttk
from data import catalog_repo
from gui_tk.tabs.details_tab import DetailsTab

class CatalogTab(tk.Frame):
    def __init__(self, parent, eventbus):
        super().__init__(parent)
        self.eventbus = eventbus

        self.table = ttk.Treeview(self, columns=("alias","uid","title","status","planned"))
        self.table.heading("alias", text="Alias")
        self.table.heading("uid", text="UID")
        self.table.heading("title", text="Title")
        self.table.heading("status", text="Status")
        self.table.heading("planned", text="Planned Release")
        self.table.pack(fill="both", expand=True)

        self.table.bind("<<TreeviewSelect>>", self._on_select)

        eventbus.subscribe("work_created", lambda w: self.refresh())
        eventbus.subscribe("work_updated", lambda w: self.refresh())

    def refresh(self):
        for row in self.table.get_children():
            self.table.delete(row)

        works = catalog_repo.list_works()
        for w in works:
            self.table.insert(
                "", "end", iid=f"{w.alias}:{w.uid}",
                values=(
                    w.alias, w.uid, w.title,
                    getattr(w, "status", ""),
                    (w.planned_release_utc.isoformat()
                        if getattr(w, "planned_release_utc", None)
                        else "")
                )
            )

    def _on_select(self, e):
        item = self.table.focus()
        if not item:
            return
        alias, uid = item.split(":")
        # eventbus dispatch same as Flet version
        from data import catalog_repo
        w = catalog_repo.get_work(alias, uid)
        if w:
            self.eventbus.publish("work_selected", w)
