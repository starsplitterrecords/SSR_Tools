from __future__ import annotations

from dataclasses import fields as dataclass_fields
from datetime import datetime
from typing import Optional

import tkinter as tk
from tkinter import ttk, messagebox

import yaml  # type: ignore

from core.models import Work
from data import work_repo, catalog_repo
from helpers.events import EventBus


class DetailsTab(tk.Frame):
    """
    Work details + metadata editor (Tkinter).
    """

    def __init__(self, parent, eventbus: EventBus):
        super().__init__(parent, bg="#1e1e1e")
        self.eventbus = eventbus
        self.work: Optional[Work] = None

        eventbus.subscribe("work_selected", self.on_work_selected)
        eventbus.subscribe("work_created", self.on_work_created)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        title_frame = tk.Frame(self, bg="#1e1e1e")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        self.title_label = tk.Label(
            title_frame,
            text="Details",
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
        )
        self.title_label.pack(side="left")

        # Left column
        left = tk.Frame(self, bg="#1e1e1e")
        left.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        left.columnconfigure(0, weight=1)

        self.uid_var = tk.StringVar()
        self.alias_var = tk.StringVar()
        self.created_var = tk.StringVar()
        self.planned_var = tk.StringVar()
        self.campaign_var = tk.StringVar()

        tk.Label(left, text="UID", bg="#1e1e1e", fg="#ffffff").grid(
            row=0, column=0, sticky="w"
        )
        tk.Entry(left, textvariable=self.uid_var, state="readonly").grid(
            row=1, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(left, text="Alias", bg="#1e1e1e", fg="#ffffff").grid(
            row=2, column=0, sticky="w"
        )
        tk.Entry(left, textvariable=self.alias_var, state="readonly").grid(
            row=3, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(left, text="Created (UTC)", bg="#1e1e1e", fg="#ffffff").grid(
            row=4, column=0, sticky="w"
        )
        tk.Entry(left, textvariable=self.created_var, state="readonly").grid(
            row=5, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(
            left,
            text="Planned release (ISO UTC)",
            bg="#1e1e1e",
            fg="#ffffff",
        ).grid(row=6, column=0, sticky="w")
        tk.Entry(left, textvariable=self.planned_var).grid(
            row=7, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(left, text="Campaign", bg="#1e1e1e", fg="#ffffff").grid(
            row=8, column=0, sticky="w"
        )
        tk.Entry(left, textvariable=self.campaign_var).grid(
            row=9, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(left, text="Notes", bg="#1e1e1e", fg="#ffffff").grid(
            row=10, column=0, sticky="w"
        )
        self.notes_text = tk.Text(left, height=5)
        self.notes_text.grid(row=11, column=0, sticky="nsew", pady=(0, 4))

        left.rowconfigure(11, weight=1)

        # Paths (read-only)
        tk.Label(left, text="Router inbox folder", bg="#1e1e1e", fg="#ffffff").grid(
            row=12, column=0, sticky="w"
        )
        self.router_inbox_var = tk.StringVar()
        tk.Entry(left, textvariable=self.router_inbox_var, state="readonly").grid(
            row=13, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(left, text="Assets root folder", bg="#1e1e1e", fg="#ffffff").grid(
            row=14, column=0, sticky="w"
        )
        self.assets_root_var = tk.StringVar()
        tk.Entry(left, textvariable=self.assets_root_var, state="readonly").grid(
            row=15, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(left, text="Output folder", bg="#1e1e1e", fg="#ffffff").grid(
            row=16, column=0, sticky="w"
        )
        self.output_folder_var = tk.StringVar()
        tk.Entry(left, textvariable=self.output_folder_var, state="readonly").grid(
            row=17, column=0, sticky="ew", pady=(0, 4)
        )

        self.save_button = tk.Button(left, text="Save", command=self.on_save_clicked)
        self.save_button.grid(row=18, column=0, sticky="e", pady=(6, 0))

        # Right YAML editor
        right = tk.Frame(self, bg="#1e1e1e")
        right.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        tk.Label(right, text="Work YAML", bg="#1e1e1e", fg="#ffffff").grid(
            row=0, column=0, sticky="w"
        )

        self.yaml_text = tk.Text(right)
        self.yaml_text.grid(row=1, column=0, sticky="nsew")

    # ------------------------------------------------------------------ events

    def on_work_selected(self, work: Work) -> None:
        self.work = work
        self._load_work_into_fields(work)

    def on_work_created(self, work: Work) -> None:
        self.work = work
        self._load_work_into_fields(work)

    # ------------------------------------------------------------------ helpers

    def _load_work_into_fields(self, work: Work) -> None:
        self.title_label.config(text=f"Details: {work.alias} ({work.uid})")

        self.uid_var.set(work.uid)
        self.alias_var.set(work.alias)
        self.created_var.set(work.created_utc.isoformat() if work.created_utc else "")
        planned = getattr(work, "planned_release_utc", None)
        self.planned_var.set(planned.isoformat() if planned else "")

        self.campaign_var.set(getattr(work, "campaign", "") or "")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert(tk.END, getattr(work, "notes", "") or "")

        self.router_inbox_var.set(getattr(work, "router_inbox", "") or "")
        self.assets_root_var.set(getattr(work, "assets_root", "") or "")
        self.output_folder_var.set(getattr(work, "output_folder", "") or "")

        self.yaml_text.delete("1.0", tk.END)
        self.yaml_text.insert(
            tk.END,
            yaml.safe_dump(work.to_dict(), sort_keys=False, allow_unicode=True),
        )

    def _parse_planned_release(self, text: str) -> Optional[datetime]:
        text = (text or "").strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            if self.work and getattr(self.work, "planned_release_utc", None):
                return self.work.planned_release_utc
            return None

    def _apply_form_to_work(self, work: Work) -> None:
        work.campaign = (self.campaign_var.get() or "").strip() or None
        notes = self.notes_text.get("1.0", tk.END).strip()
        work.notes = notes or None
        work.planned_release_utc = self._parse_planned_release(self.planned_var.get())

    def _apply_yaml_to_work(self, work: Work) -> bool:
        text = self.yaml_text.get("1.0", tk.END)
        try:
            raw = yaml.safe_load(text) or {}
            if not isinstance(raw, dict):
                raise ValueError("YAML root must be a mapping/object")

            required = ("alias", "uid", "title", "folder_path")
            missing = [
                key
                for key in required
                if not isinstance(raw.get(key, ""), str) or not raw.get(key, "").strip()
            ]
            if missing:
                raise ValueError(
                    f"Missing required field(s): {', '.join(sorted(missing))}"
                )

            updated = Work.from_dict(raw)
            for f in dataclass_fields(Work):
                setattr(work, f.name, getattr(updated, f.name))

            return True
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("YAML error", str(exc))
            return False

    # ------------------------------------------------------------------ save

    def on_save_clicked(self) -> None:
        if not self.work:
            messagebox.showwarning("Details", "No work selected.")
            return

        self._apply_form_to_work(self.work)

        if not self._apply_yaml_to_work(self.work):
            return

        work_repo.save_work(self.work)
        catalog_repo.save_work_to_catalog(self.work)
        messagebox.showinfo("Details", "Work saved.")
        self.eventbus.publish("work_updated", self.work)
