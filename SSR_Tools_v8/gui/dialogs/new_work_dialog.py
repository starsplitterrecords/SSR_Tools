from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

from core.models import Work
from data import work_repo, catalog_repo
from helpers.events import EventBus

from gui.dialogs.base_dialog import BaseDialog
from gui import style


class NewWorkDialog(BaseDialog):
    """
    Create a new Work entry.

    Uses BaseDialog for consistent layout and behavior.
    """

    def __init__(self, parent, eventbus: EventBus | None = None):
        self.eventbus = eventbus

        # Form variables
        self.alias_var = tk.StringVar()
        self.uid_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.folder_var = tk.StringVar()

        super().__init__(parent, scrollable=False, title="Create New Work")

    # ------------------------------------------------------------------ hooks

    def _build_body(self, body: tk.Frame) -> None:
        body.columnconfigure(0, weight=1)

        # Alias
        tk.Label(
            body,
            text="Alias Codename",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).grid(row=0, column=0, sticky="w", pady=(0, style.PAD_Y_SMALL))

        tk.Entry(body, textvariable=self.alias_var, width=40).grid(
            row=1, column=0, sticky="ew", pady=(0, style.PAD_Y)
        )

        # UID
        tk.Label(
            body,
            text="UID (e.g. PWC001)",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).grid(row=2, column=0, sticky="w", pady=(0, style.PAD_Y_SMALL))

        tk.Entry(body, textvariable=self.uid_var, width=40).grid(
            row=3, column=0, sticky="ew", pady=(0, style.PAD_Y)
        )

        # Title
        tk.Label(
            body,
            text="Title",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).grid(row=4, column=0, sticky="w", pady=(0, style.PAD_Y_SMALL))

        tk.Entry(body, textvariable=self.title_var, width=40).grid(
            row=5, column=0, sticky="ew", pady=(0, style.PAD_Y)
        )

        # Folder
        tk.Label(
            body,
            text="Work Folder Path",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).grid(row=6, column=0, sticky="w", pady=(0, style.PAD_Y_SMALL))

        folder_row = tk.Frame(body, bg=style.MAIN_BG)
        folder_row.grid(row=7, column=0, sticky="ew", pady=(0, style.PAD_Y))
        folder_row.columnconfigure(0, weight=1)

        tk.Entry(folder_row, textvariable=self.folder_var, width=40).grid(
            row=0, column=0, sticky="ew"
        )
        tk.Button(
            folder_row,
            text="Browse",
            command=self._browse_folder,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).grid(row=0, column=1, padx=4)

    def _on_submit(self) -> bool:
        alias = self.alias_var.get().strip()
        uid = self.uid_var.get().strip()
        title = self.title_var.get().strip()
        folder = self.folder_var.get().strip()

        if not alias or not uid or not title or not folder:
            messagebox.showwarning("New Work", "All fields are required.")
            return False

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

        return True

    # ------------------------------------------------------------------ helpers

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory(title="Select work folder")
        if path:
            self.folder_var.set(path)
