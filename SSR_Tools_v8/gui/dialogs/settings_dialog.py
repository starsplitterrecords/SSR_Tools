from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox

from data import config_repo

from gui.dialogs.base_dialog import BaseDialog
from gui import style


class SettingsDialog(BaseDialog):
    """
    Application settings (SSR-compliant).
    """

    def __init__(self, parent):
        # Load config first to initialize variables
        cfg = config_repo.load_config()

        self.assets_var = tk.StringVar(value=cfg.get("assets_root_path", ""))
        self.router_var = tk.StringVar(value=cfg.get("router_inbox_path", ""))
        self.preview_var = tk.BooleanVar(value=cfg.get("preview_mode", False))
        self.refresh_var = tk.BooleanVar(value=cfg.get("auto_refresh_router", False))
        self.interval_var = tk.StringVar(
            value=str(cfg.get("refresh_interval_seconds", 60))
        )

        super().__init__(parent, scrollable=False, title="Settings")

    # ------------------------------------------------------------------
    # BUILD
    # ------------------------------------------------------------------

    def _build_body(self, body: tk.Frame) -> None:
        body.columnconfigure(0, weight=1)

        # Assets Root
        tk.Label(body, text="Assets Root Path", bg=style.MAIN_BG, fg=style.MAIN_FG)\
            .grid(row=0, column=0, sticky="w", pady=(0, style.PAD_Y_SMALL))

        assets_row = tk.Frame(body, bg=style.MAIN_BG)
        assets_row.grid(row=1, column=0, sticky="ew", pady=(0, style.PAD_Y))
        assets_row.columnconfigure(0, weight=1)

        tk.Entry(assets_row, textvariable=self.assets_var, width=50)\
            .grid(row=0, column=0, sticky="ew")
        tk.Button(
            assets_row, text="Browse", command=self._pick_assets,
            bg=style.BUTTON_BG, fg=style.BUTTON_FG
        ).grid(row=0, column=1, padx=4)

        # Router Inbox
        tk.Label(body, text="Router Inbox Path", bg=style.MAIN_BG, fg=style.MAIN_FG)\
            .grid(row=2, column=0, sticky="w", pady=(0, style.PAD_Y_SMALL))

        router_row = tk.Frame(body, bg=style.MAIN_BG)
        router_row.grid(row=3, column=0, sticky="ew", pady=(0, style.PAD_Y))
        router_row.columnconfigure(0, weight=1)

        tk.Entry(router_row, textvariable=self.router_var, width=50)\
            .grid(row=0, column=0, sticky="ew")
        tk.Button(
            router_row, text="Browse", command=self._pick_router,
            bg=style.BUTTON_BG, fg=style.BUTTON_FG
        ).grid(row=0, column=1, padx=4)

        # Options
        tk.Checkbutton(
            body, text="Preview Mode",
            variable=self.preview_var,
            bg=style.MAIN_BG, fg=style.MAIN_FG,
            selectcolor=style.MAIN_BG
        ).grid(row=4, column=0, sticky="w", pady=(style.PAD_Y, style.PAD_Y_SMALL))

        tk.Checkbutton(
            body, text="Auto Refresh Router",
            variable=self.refresh_var,
            bg=style.MAIN_BG, fg=style.MAIN_FG,
            selectcolor=style.MAIN_BG
        ).grid(row=5, column=0, sticky="w", pady=(0, style.PAD_Y_SMALL))

        # Interval
        tk.Label(
            body,
            text="Refresh Interval (sec)",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).grid(row=6, column=0, sticky="w", pady=(style.PAD_Y, style.PAD_Y_SMALL))

        tk.Entry(body, textvariable=self.interval_var, width=12)\
            .grid(row=7, column=0, sticky="w", pady=(0, style.PAD_Y))

    # ------------------------------------------------------------------
    # SUBMIT
    # ------------------------------------------------------------------

    def _on_submit(self) -> bool:
        try:
            interval = int(self.interval_var.get().strip() or "60")
        except ValueError:
            messagebox.showerror("Settings", "Refresh interval must be an integer.")
            return False

        cfg = {
            "assets_root_path": self.assets_var.get().strip(),
            "router_inbox_path": self.router_var.get().strip(),
            "preview_mode": self.preview_var.get(),
            "auto_refresh_router": self.refresh_var.get(),
            "refresh_interval_seconds": interval,
        }

        config_repo.save_config(cfg)
        messagebox.showinfo("Settings", "Settings saved.")
        return True

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _pick_assets(self) -> None:
        path = filedialog.askdirectory(title="Select assets root")
        if path:
            self.assets_var.set(path)

    def _pick_router(self) -> None:
        path = filedialog.askdirectory(title="Select router inbox")
        if path:
            self.router_var.set(path)
