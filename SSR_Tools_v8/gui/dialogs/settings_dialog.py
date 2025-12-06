from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox

from data import config_repo


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.transient(parent)
        self.grab_set()

        cfg = config_repo.load_config()

        self.assets_var = tk.StringVar(value=cfg.get("assets_root_path", ""))
        self.router_var = tk.StringVar(value=cfg.get("router_inbox_path", ""))
        self.preview_var = tk.BooleanVar(value=cfg.get("preview_mode", False))
        self.refresh_var = tk.BooleanVar(value=cfg.get("auto_refresh_router", False))
        self.interval_var = tk.StringVar(
            value=str(cfg.get("refresh_interval_seconds", 60))
        )

        frame = tk.Frame(self, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        # Assets root
        tk.Label(frame, text="Assets Root Path").grid(row=0, column=0, sticky="w")
        assets_row = tk.Frame(frame)
        assets_row.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        tk.Entry(assets_row, textvariable=self.assets_var, width=50).pack(
            side="left", fill="x", expand=True
        )
        tk.Button(assets_row, text="Browse", command=self._pick_assets).pack(
            side="left", padx=4
        )

        # Router inbox
        tk.Label(frame, text="Router Inbox Path").grid(row=2, column=0, sticky="w")
        router_row = tk.Frame(frame)
        router_row.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        tk.Entry(router_row, textvariable=self.router_var, width=50).pack(
            side="left", fill="x", expand=True
        )
        tk.Button(router_row, text="Browse", command=self._pick_router).pack(
            side="left", padx=4
        )

        # Options
        tk.Checkbutton(
            frame, text="Preview Mode", variable=self.preview_var
        ).grid(row=4, column=0, sticky="w", pady=(4, 0))
        tk.Checkbutton(
            frame, text="Auto Refresh Router", variable=self.refresh_var
        ).grid(row=5, column=0, sticky="w")

        tk.Label(frame, text="Refresh Interval (sec)").grid(
            row=6, column=0, sticky="w"
        )
        tk.Entry(frame, textvariable=self.interval_var, width=10).grid(
            row=7, column=0, sticky="w", pady=(0, 4)
        )

        btn_row = tk.Frame(frame)
        btn_row.grid(row=8, column=0, sticky="e", pady=(10, 0))
        tk.Button(btn_row, text="Cancel", command=self._cancel).pack(
            side="right", padx=4
        )
        tk.Button(btn_row, text="Save", command=self._save).pack(side="right")

        frame.columnconfigure(0, weight=1)

    def _pick_assets(self) -> None:
        path = filedialog.askdirectory(title="Select assets root")
        if path:
            self.assets_var.set(path)

    def _pick_router(self) -> None:
        path = filedialog.askdirectory(title="Select router inbox")
        if path:
            self.router_var.set(path)

    def _cancel(self) -> None:
        self.destroy()

    def _save(self) -> None:
        try:
            interval = int(self.interval_var.get().strip() or "60")
        except ValueError:
            messagebox.showerror("Settings", "Refresh interval must be an integer.")
            return

        cfg = {
            "assets_root_path": self.assets_var.get().strip(),
            "router_inbox_path": self.router_var.get().strip(),
            "preview_mode": self.preview_var.get(),
            "auto_refresh_router": self.refresh_var.get(),
            "refresh_interval_seconds": interval,
        }
        config_repo.save_config(cfg)
        messagebox.showinfo("Settings", "Settings saved.")
        self.destroy()
