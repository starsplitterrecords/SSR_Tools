from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from core.models import Alias
from data import alias_repo
from helpers.events import EventBus


class AliasTab(tk.Frame):
    """
    Simple alias manager backed by alias_repo.
    """

    def __init__(self, parent, eventbus: EventBus):
        super().__init__(parent, bg="#1e1e1e")
        self.eventbus = eventbus

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Left list
        left = tk.Frame(self, bg="#1e1e1e")
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        tk.Label(left, text="Aliases", bg="#1e1e1e", fg="#ffffff").pack(
            anchor="w", pady=(0, 4)
        )

        self.listbox = tk.Listbox(left, height=20)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Right form
        right = tk.Frame(self, bg="#1e1e1e")
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        self.codename_var = tk.StringVar()
        self.display_var = tk.StringVar()
        self.project_var = tk.StringVar()
        self.style_var = tk.StringVar()

        tk.Label(right, text="Codename", bg="#1e1e1e", fg="#ffffff").grid(
            row=0, column=0, sticky="w"
        )
        tk.Entry(right, textvariable=self.codename_var).grid(
            row=1, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(right, text="Display Name", bg="#1e1e1e", fg="#ffffff").grid(
            row=2, column=0, sticky="w"
        )
        tk.Entry(right, textvariable=self.display_var).grid(
            row=3, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(right, text="Project Name", bg="#1e1e1e", fg="#ffffff").grid(
            row=4, column=0, sticky="w"
        )
        tk.Entry(right, textvariable=self.project_var).grid(
            row=5, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(right, text="Visual Style", bg="#1e1e1e", fg="#ffffff").grid(
            row=6, column=0, sticky="w"
        )
        tk.Entry(right, textvariable=self.style_var).grid(
            row=7, column=0, sticky="ew", pady=(0, 4)
        )

        tk.Label(right, text="Notes", bg="#1e1e1e", fg="#ffffff").grid(
            row=8, column=0, sticky="w"
        )
        self.notes_text = tk.Text(right, height=6)
        self.notes_text.grid(row=9, column=0, sticky="nsew", pady=(0, 4))

        right.columnconfigure(0, weight=1)
        right.rowconfigure(9, weight=1)

        btn_frame = tk.Frame(right, bg="#1e1e1e")
        btn_frame.grid(row=10, column=0, sticky="ew", pady=(6, 0))
        tk.Button(btn_frame, text="Save", command=self.save_alias).pack(
            side="left", padx=2
        )
        tk.Button(btn_frame, text="Delete", command=self.delete_alias).pack(
            side="left", padx=2
        )

        self.selected_alias: Alias | None = None

    # ------------------------------------------------------------------ external

    def refresh(self) -> None:
        self._refresh_list()

    # ------------------------------------------------------------------ internals

    def _refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        aliases = alias_repo.list_aliases()
        for alias in aliases:
            self.listbox.insert(tk.END, alias.codename)

    def _on_select(self, event) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        index = sel[0]
        codename = self.listbox.get(index)
        alias = alias_repo.get_alias(codename)
        if not alias:
            return

        self.selected_alias = alias
        self.codename_var.set(alias.codename)
        self.display_var.set(alias.display_name or "")
        self.project_var.set(alias.project_name or "")
        self.style_var.set(alias.visual_style or "")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert(tk.END, alias.notes or "")

    def save_alias(self) -> None:
        codename = self.codename_var.get().strip()
        if not codename:
            messagebox.showwarning("Alias", "Codename required.")
            return

        display = self.display_var.get().strip() or codename
        project = self.project_var.get().strip() or None
        style = self.style_var.get().strip() or None
        notes = self.notes_text.get("1.0", tk.END).strip() or None

        if self.selected_alias is None:
            alias = Alias(
                codename=codename,
                display_name=display,
                project_name=project,
                visual_style=style,
                notes=notes,
            )
        else:
            alias = self.selected_alias
            alias.codename = codename
            alias.display_name = display
            alias.project_name = project
            alias.visual_style = style
            alias.notes = notes

        alias_repo.save_alias(alias)
        self.selected_alias = alias
        self._refresh_list()

    def delete_alias(self) -> None:
        if not self.selected_alias:
            return
        alias_repo.delete_alias(self.selected_alias.codename)
        self.selected_alias = None
        self.codename_var.set("")
        self.display_var.set("")
        self.project_var.set("")
        self.style_var.set("")
        self.notes_text.delete("1.0", tk.END)
        self._refresh_list()
