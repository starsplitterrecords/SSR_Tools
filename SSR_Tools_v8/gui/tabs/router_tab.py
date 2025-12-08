from __future__ import annotations

import os
from typing import List

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from data import config_repo
from helpers.events import EventBus

from gui import style
from gui.dialogs.router_process_dialog import (
    RouterProcessDialog,
    BatchRouterProcessDialog,
)


class RouterTab(tk.Frame):
    """
    Router inbox browser with multi-select batch processing (Tkinter).

    Layout:
        +-----------------------------------------------------------+
        | Header: Router Inbox Folder [entry] [Change] [Refresh]    |
        +-----------------------------------------------------------+
        | Controls: [Process Selected] [Batch Selected] [Batch All] |
        +-----------------------------------------------------------+
        | Inbox List (multi-select)                                 |
        +-----------------------------------------------------------+
    """

    def __init__(self, parent, eventbus: EventBus):
        super().__init__(parent, bg=style.MAIN_BG)
        self.eventbus = eventbus

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        cfg = config_repo.load_config()
        inbox_default = cfg.get("router_inbox_path", "") or ""

        # ------------------------------------------------------------------
        # HEADER ROW
        # ------------------------------------------------------------------
        header = tk.Frame(self, bg=style.MAIN_BG)
        header.grid(row=0, column=0, sticky="ew", padx=style.PAD_X, pady=style.PAD_Y)

        tk.Label(
            header,
            text="Router Inbox Folder",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).pack(side="left")

        self.inbox_var = tk.StringVar(value=inbox_default)
        self.inbox_entry = tk.Entry(header, textvariable=self.inbox_var, width=60)
        self.inbox_entry.pack(side="left", padx=style.PAD_X)

        tk.Button(
            header,
            text="Change",
            command=self._change_inbox,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="left", padx=4)

        tk.Button(
            header,
            text="Refresh",
            command=self._on_refresh_click,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="left", padx=4)

        # ------------------------------------------------------------------
        # CONTROL ROW
        # ------------------------------------------------------------------
        controls = tk.Frame(self, bg=style.MAIN_BG)
        controls.grid(row=1, column=0, sticky="ew", padx=style.PAD_X, pady=(0, style.PAD_Y))

        tk.Button(
            controls,
            text="Process Selected",
            command=self._process_selected_single,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="left", padx=4)

        tk.Button(
            controls,
            text="Batch Selected",
            command=self._process_selected_batch,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="left", padx=4)

        tk.Button(
            controls,
            text="Batch All",
            command=self._process_all_batch,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="left", padx=4)

        # ------------------------------------------------------------------
        # INBOX LIST
        # ------------------------------------------------------------------
        list_frame = tk.Frame(self, bg=style.MAIN_BG)
        list_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=style.PAD_X,
            pady=(0, style.PAD_Y_LARGE),
        )
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode="extended",
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

        self.listbox.bind("<Double-Button-1>", self._on_double_click)

        # paths indexed by listbox index
        self._items: List[str] = []

        # Initial load
        self._load_inbox()

    # ------------------------------------------------------------------
    # REFRESH / LOAD
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Public refresh entry point (called by main_view)."""
        self._load_inbox()

    def _on_refresh_click(self) -> None:
        self._load_inbox()

    def _load_inbox(self) -> None:
        """Populate listbox from the inbox folder."""
        inbox = self.inbox_var.get().strip()
        self._items.clear()
        self.listbox.delete(0, tk.END)

        if not inbox or not os.path.isdir(inbox):
            return

        try:
            entries = sorted(os.listdir(inbox))
        except OSError as exc:
            messagebox.showerror("Router", f"Unable to read inbox: {exc}")
            return

        for name in entries:
            full = os.path.join(inbox, name)
            self._items.append(full)
            self.listbox.insert(tk.END, name)

    # ------------------------------------------------------------------
    # INBOX PATH CHANGE
    # ------------------------------------------------------------------

    def _change_inbox(self) -> None:
        path = filedialog.askdirectory(title="Select router inbox")
        if not path:
            return

        self.inbox_var.set(path)

        cfg = config_repo.load_config()
        cfg["router_inbox_path"] = path
        config_repo.save_config(cfg)

        self._load_inbox()

    # ------------------------------------------------------------------
    # SELECTION HELPERS
    # ------------------------------------------------------------------

    def _selected_paths(self) -> List[str]:
        sel = self.listbox.curselection()
        if not sel:
            return []
        paths: List[str] = []
        for idx in sel:
            if 0 <= idx < len(self._items):
                paths.append(self._items[idx])
        return paths

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _on_double_click(self, event=None) -> None:
        # Double-click processes a single item
        self._process_selected_single()

    def _process_selected_single(self) -> None:
        paths = self._selected_paths()
        if not paths:
            messagebox.showinfo("Router", "No item selected.")
            return

        if len(paths) > 1:
            # If multiple, use batch instead
            self._process_selected_batch()
            return

        selected = paths[0]
        dlg = RouterProcessDialog(self, selected_path=selected, on_created=self._on_work_created)
        self.wait_window(dlg)

    def _process_selected_batch(self) -> None:
        paths = self._selected_paths()
        if not paths:
            messagebox.showinfo("Router", "No items selected.")
            return

        dlg = BatchRouterProcessDialog(self, selected_paths=paths, on_created=self._on_work_created)
        self.wait_window(dlg)

    def _process_all_batch(self) -> None:
        if not self._items:
            messagebox.showinfo("Router", "Inbox is empty.")
            return

        dlg = BatchRouterProcessDialog(self, selected_paths=list(self._items), on_created=self._on_work_created)
        self.wait_window(dlg)

    # ------------------------------------------------------------------
    # CALLBACKS
    # ------------------------------------------------------------------

    def _on_work_created(self, work) -> None:
        # Notify listeners that a new work was created
        if self.eventbus:
            self.eventbus.publish("work_created", work)
