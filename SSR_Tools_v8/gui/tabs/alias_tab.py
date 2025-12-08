from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from core.models import Alias
from data import alias_repo
from helpers.events import EventBus

from gui import style


class AliasTab(tk.Frame):
    """
    Alias manager (SSR compliant, A1+B1 UI).

    Layout:
        +----------------------------------------------------------+
        | Header: Aliases                                          |
        +----------------------------------------------------------+
        | LEFT: alias list | RIGHT: alias form (fields + notes)    |
        +----------------------------------------------------------+
    """

    def __init__(self, parent, eventbus: EventBus):
        super().__init__(parent, bg=style.MAIN_BG)
        self.eventbus = eventbus

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # ------------------------------------------------------------------
        # HEADER
        # ------------------------------------------------------------------
        header = tk.Frame(self, bg=style.MAIN_BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew",
                    padx=style.PAD_X, pady=style.PAD_Y)

        tk.Label(
            header,
            text="Aliases",
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
        # LEFT COLUMN — ALIAS LIST
        # ------------------------------------------------------------------
        left = tk.Frame(self, bg=style.MAIN_BG)
        left.grid(row=1, column=0, sticky="nsew", padx=(style.PAD_X, style.PAD_X_LARGE),
                  pady=(0, style.PAD_Y_LARGE))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        tk.Label(
            left,
            text="Alias Codes",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
            font=(style.FONT_FAMILY, style.FONT_SIZE_BASE, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, style.PAD_Y))

        self.listbox = tk.Listbox(left, height=20)
        self.listbox.grid(row=1, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(left, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")

        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # ------------------------------------------------------------------
        # RIGHT COLUMN — FORM
        # ------------------------------------------------------------------
        right = tk.Frame(self, bg=style.MAIN_BG)
        right.grid(row=1, column=1, sticky="nsew",
                   padx=(0, style.PAD_X), pady=(0, style.PAD_Y_LARGE))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(9, weight=1)

        # Form variables
        self.codename_var = tk.StringVar()
        self.display_var = tk.StringVar()
        self.project_var = tk.StringVar()
        self.style_var = tk.StringVar()

        # Helper
        def add_field(label: str, var: tk.StringVar):
            tk.Label(
                right,
                text=label,
                bg=style.MAIN_BG,
                fg=style.MAIN_FG,
            ).pack(anchor="w", pady=(style.PAD_Y_SMALL, 0))

            e = tk.Entry(right, textvariable=var)
            e.pack(fill="x", pady=(0, style.PAD_Y))
            return e

        add_field("Codename", self.codename_var)
        add_field("Display Name", self.display_var)
        add_field("Project Name", self.project_var)
        add_field("Visual Style", self.style_var)

        # Notes (multiline)
        tk.Label(
            right,
            text="Notes",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).pack(anchor="w", pady=(style.PAD_Y_SMALL, 0))

        self.notes_text = tk.Text(right, height=6)
        self.notes_text.pack(fill="x", pady=(0, style.PAD_Y))

        # Buttons
        btn_row = tk.Frame(right, bg=style.MAIN_BG)
        btn_row.pack(anchor="e", pady=(style.PAD_Y, 0))

        tk.Button(
            btn_row,
            text="Save",
            command=self.save_alias,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="left", padx=4)

        tk.Button(
            btn_row,
            text="Delete",
            command=self.delete_alias,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="left", padx=4)

        # Internal state
        self.selected_alias: Alias | None = None

    # ----------------------------------------------------------------------
    # EVENT-HANDLED METHODS
    # ----------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload alias list."""
        self.listbox.delete(0, tk.END)
        aliases = alias_repo.list_aliases()
        for alias in aliases:
            self.listbox.insert(tk.END, alias.codename)

    def _on_select(self, event) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return

        codename = self.listbox.get(sel[0])
        alias = alias_repo.get_alias(codename)
        if not alias:
            return

        self.selected_alias = alias

        self.codename_var.set(alias.codename)
        self.display_var.set(alias.display_name or "")
        self.project_var.set(alias.project_name or "")
        self.style_var.set(alias.visual_style or "")

        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("end", alias.notes or "")

    # ----------------------------------------------------------------------
    # SAVE / DELETE
    # ----------------------------------------------------------------------

    def save_alias(self) -> None:
        codename = self.codename_var.get().strip()
        if not codename:
            messagebox.showwarning("Alias", "Codename is required.")
            return

        display = self.display_var.get().strip() or codename
        project = self.project_var.get().strip() or None
        vstyle = self.style_var.get().strip() or None
        notes = self.notes_text.get("1.0", tk.END).strip() or None

        if self.selected_alias is None:
            alias = Alias(
                codename=codename,
                display_name=display,
                project_name=project,
                visual_style=vstyle,
                notes=notes,
            )
        else:
            alias = self.selected_alias
            alias.codename = codename
            alias.display_name = display
            alias.project_name = project
            alias.visual_style = vstyle
            alias.notes = notes

        alias_repo.save_alias(alias)
        self.selected_alias = alias
        self.refresh()

    def delete_alias(self) -> None:
        if not self.selected_alias:
            return

        alias_repo.delete_alias(self.selected_alias.codename)

        # Clear UI
        self.selected_alias = None
        self.codename_var.set("")
        self.display_var.set("")
        self.project_var.set("")
        self.style_var.set("")
        self.notes_text.delete("1.0", tk.END)

        self.refresh()
