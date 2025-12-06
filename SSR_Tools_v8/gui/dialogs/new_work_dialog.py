from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

from core.models import Work
from data import work_repo, catalog_repo
from helpers.events import EventBus


class NewWorkDialog(tk.Toplevel):
    """
    Create a new Work entry.
    """

    def __init__(self, parent, eventbus: EventBus | None = None):
        super().__init__(parent)
        self.title("Create New Work")
        self.transient(parent)
        self.grab_set()

        self.eventbus = eventbus

        self.alias_var = tk.StringVar()
        self.uid_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.folder_var = tk.StringVar()

        frame = tk.Frame(self, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Alias Codename").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.alias_var, width=40).grid(
            row=1, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(frame, text="UID (e.g. PWC001)").grid(row=2, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.uid_var, width=40).grid(
            row=3, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(frame, text="Title").grid(row=4, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.title_var, width=40).grid(
            row=5, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(frame, text="Work Folder Path").grid(row=6, column=0, sticky="w")
        folder_row = tk.Frame(frame)
        folder_row.grid(row=7, column=0, sticky="ew", pady=(0, 4))
        tk.Entry(folder_row, textvariable=self.folder_var, width=40).pack(
            side="left", fill="x", expand=True
        )
        tk.Button(folder_row, text="Browse", command=self._browse_folder).pack(
            side="left", padx=4
        )

        btn_row = tk.Frame(frame)
        btn_row.grid(row=8, column=0, sticky="e", pady=(10, 0))
        tk.Button(btn_row, text="Cancel", command=self._cancel).pack(
            side="right", padx=4
        )
        tk.Button(btn_row, text="Create", command=self._create).pack(side="right")

        self.columnconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory(title="Select work folder")
        if path:
            self.folder_var.set(path)

    def _cancel(self) -> None:
        self.destroy()

    def _create(self) -> None:
        alias = self.alias_var.get().strip()
        uid = self.uid_var.get().strip()
        title = self.title_var.get().strip()
        folder = self.folder_var.get().strip()

        if not alias or not uid or not title or not folder:
            messagebox.showwarning("New Work", "All fields are required.")
            return

        w = Work(
            alias=alias,
            uid=uid,
            title=title,
            folder_path=folder,
            created_utc=datetime.utcnow(),
        )
        work_repo.save_work(w)
        catalog_repo.save_work_to_catalog(w)

        if self.eventbus:
            self.eventbus.publish("work_created", w)

        self.destroy()
