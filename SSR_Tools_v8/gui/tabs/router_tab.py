from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from data import config_repo
from gui.dialogs.router_process_dialog import (
    RouterProcessDialog,
    BatchRouterProcessDialog,
)


class RouterTab(tk.Frame):
    """
    Router inbox browser with multi-select batch processing (Tkinter).
    """

    def __init__(self, parent, eventbus):
        super().__init__(parent, bg="#1e1e1e")
        self.eventbus = eventbus

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        cfg = config_repo.load_config()

        # Inbox path field
        top = tk.Frame(self, bg="#1e1e1e")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        tk.Label(
            top,
            text="Router Inbox Folder",
            bg="#1e1e1e",
            fg="#ffffff",
        ).pack(side="left")

        self.inbox_var = tk.StringVar(value=cfg.get("router_inbox_path", "") or "")
        self.inbox_entry = tk.Entry(top, textvariable=self.inbox_var, width=60)
        self.inbox_entry.pack(side="left", padx=5)

        tk.Button(top, text="Change", command=self._change_inbox).pack(side="left")
        tk.Button(top, text="Refresh", command=self._on_refresh_click).pack(
            side="left", padx=3
        )
        tk.Button(
            top, text="Process Selected", command=self._process_selected
        ).pack(side="left", padx=3)

        # File list
        self.file_list = tk.Listbox(self, selectmode=tk.EXTENDED)
        self.file_list.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self._paths: list[str] = []

        # Auto-refresh loop
        self._auto_refresh()

    # ------------------------------------------------------------------

    def _change_inbox(self) -> None:
        path = filedialog.askdirectory(title="Select router inbox folder")
        if not path:
            return
        self._save_inbox_to_config(path)
        self._on_refresh_click()

    def _save_inbox_to_config(self, new_path: str) -> None:
        cfg = config_repo.load_config()
        cfg["router_inbox_path"] = new_path
        config_repo.save_config(cfg)
        self.inbox_var.set(new_path)

    def _on_refresh_click(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        inbox = self.inbox_var.get().strip()
        self.file_list.delete(0, tk.END)
        self._paths.clear()

        if not inbox or not os.path.isdir(inbox):
            self.file_list.insert(tk.END, "Inbox folder not set or does not exist.")
            return

        entries = sorted(os.listdir(inbox))
        if not entries:
            self.file_list.insert(tk.END, "(No files)")
            return

        for name in entries:
            full = os.path.join(inbox, name)
            label = f"[DIR] {name}" if os.path.isdir(full) else name
            self.file_list.insert(tk.END, label)
            self._paths.append(full)

    def _process_selected(self) -> None:
        sel = self.file_list.curselection()
        if not sel:
            messagebox.showinfo("Router", "No items selected.")
            return

        paths = [self._paths[i] for i in sel if i < len(self._paths)]
        if not paths:
            return

        if len(paths) == 1:
            dlg = RouterProcessDialog(
                self.winfo_toplevel(),
                selected_path=paths[0],
                on_created=lambda w: self.eventbus.publish("work_created", w),
            )
            dlg.wait_window()
        else:
            dlg = BatchRouterProcessDialog(
                self.winfo_toplevel(),
                selected_paths=paths,
                on_created=lambda w: self.eventbus.publish("work_created", w),
            )
            dlg.wait_window()

    # ------------------------------------------------------------------
    # Auto-refresh

    def _auto_refresh(self) -> None:
        cfg = config_repo.load_config()
        interval = int(cfg.get("refresh_interval_seconds", 60) or 60)
        if cfg.get("auto_refresh_router", False):
            self.refresh()
        # schedule next check
        self.after(max(5000, interval * 1000), self._auto_refresh)
