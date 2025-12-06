from __future__ import annotations

from datetime import datetime

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

from core.models import Work
from core.scheduler.engine import schedule_release
from core.scheduler.logic import (
    get_scheduled_from_catalog,
    get_release_statistics,
    validate_spacing,
    recalculate_schedule,
)
from data import catalog_repo, work_repo


class SchedulerTab(tk.Frame):
    """
    Scheduler UI for setting planned release dates (Tkinter).
    """

    def __init__(self, parent, eventbus):
        super().__init__(parent, bg="#1e1e1e")
        self.eventbus = eventbus

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        header = tk.Frame(self, bg="#1e1e1e")
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=4)

        tk.Label(
            header,
            text="Scheduler",
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

        tk.Button(header, text="Refresh", command=self._on_refresh_click).pack(
            side="left", padx=4
        )
        tk.Button(
            header, text="Validate spacing", command=self._on_validate_click
        ).pack(side="left", padx=4)
        tk.Button(header, text="Recalculate", command=self._on_recalc_click).pack(
            side="left", padx=4
        )

        self.stats_label = tk.Label(
            self,
            text="",
            bg="#1e1e1e",
            fg="#ffffff",
        )
        self.stats_label.grid(row=1, column=0, sticky="w", padx=8)

        # Controls
        controls = tk.Frame(self, bg="#1e1e1e")
        controls.grid(row=2, column=0, sticky="ew", padx=8, pady=4)

        tk.Label(
            controls,
            text="Planned Release (UTC)",
            bg="#1e1e1e",
            fg="#ffffff",
        ).pack(side="left")

        self.date_var = tk.StringVar()
        self.date_entry = tk.Entry(controls, textvariable=self.date_var, width=32)
        self.date_entry.pack(side="left", padx=4)

        tk.Button(
            controls, text="Set Date", command=self._open_date_dialog
        ).pack(side="left", padx=4)

        # Work list
        list_frame = tk.Frame(self, bg="#1e1e1e")
        list_frame.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.work_list = tk.Listbox(list_frame)
        self.work_list.grid(row=0, column=0, sticky="nsew")
        self.work_list.bind("<<ListboxSelect>>", self._on_select_work)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.work_list.yview)
        self.work_list.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

        self._works: list[Work] = []
        self.selected_work: Work | None = None

        eventbus.subscribe("work_created", lambda w: self.refresh())
        eventbus.subscribe("work_updated", lambda w: self.refresh())

    # ------------------------------------------------------------------

    def _on_refresh_click(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        self._works = catalog_repo.list_works()
        self._works.sort(
            key=lambda w: (
                getattr(w, "planned_release_utc", None) or datetime.max,
                w.alias,
                w.uid,
            )
        )

        self.work_list.delete(0, tk.END)
        for w in self._works:
            planned = (
                w.planned_release_utc.isoformat()
                if getattr(w, "planned_release_utc", None)
                else ""
            )
            self.work_list.insert(
                tk.END,
                f"{w.alias} · {w.uid} · {planned}",
            )

    def _on_select_work(self, event) -> None:
        sel = self.work_list.curselection()
        if not sel:
            self.selected_work = None
            self.date_var.set("")
            return
        idx = sel[0]
        if idx >= len(self._works):
            return
        w = self._works[idx]
        self.selected_work = w
        self.date_var.set(
            w.planned_release_utc.isoformat()
            if getattr(w, "planned_release_utc", None)
            else ""
        )

    def _open_date_dialog(self) -> None:
        if not self.selected_work:
            messagebox.showinfo("Scheduler", "No work selected.")
            return
        initial = self.date_var.get().strip() or datetime.utcnow().strftime("%Y-%m-%d")
        s = simpledialog.askstring(
            "Set release date",
            "Enter date as YYYY-MM-DD:",
            initialvalue=initial,
            parent=self,
        )
        if not s:
            return
        try:
            d = datetime.strptime(s.strip(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Scheduler", "Invalid date format.")
            return

        self.date_var.set(d.isoformat())
        schedule_release(self.selected_work, d)
        work_repo.save_work(self.selected_work)
        catalog_repo.save_work_to_catalog(self.selected_work)
        self._on_select_work(None)
        self.eventbus.publish("work_updated", self.selected_work)

    def _on_validate_click(self) -> None:
        scheduled = get_scheduled_from_catalog()
        stats = get_release_statistics(scheduled)
        violations = validate_spacing(scheduled)

        msg = (
            f"Total: {stats['total']} | "
            f"Upcoming: {stats['upcoming']} | "
            f"Violations: {len(violations)}"
        )
        self.stats_label.config(text=msg)

        if violations:
            messagebox.showwarning(
                "Scheduler",
                "Spacing violations detected; details printed to console.",
            )
            for v in violations:
                print(v.get("message", ""))
        else:
            messagebox.showinfo("Scheduler", "No spacing violations.")

    def _on_recalc_click(self) -> None:
        scheduled = get_scheduled_from_catalog()
        total, changed = recalculate_schedule(scheduled)
        messagebox.showinfo(
            "Scheduler",
            f"Recalculated {total} scheduled releases; {changed} date(s) adjusted.",
        )
        self.refresh()
