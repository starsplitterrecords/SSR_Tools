from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import List, Dict

import tkinter as tk
from tkinter import messagebox

from core.models import Work
from data import config_repo, work_repo, catalog_repo


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _guess_alias_from_name(name: str) -> str:
    base = os.path.basename(name)
    if "-" in base:
        alias = base.split("-", 1)[0].strip()
        return alias
    return ""


def _parse_uid_suffix(uid: str, alias: str) -> int | None:
    if not uid.startswith(alias):
        return None
    suffix = uid[len(alias) :]
    if not suffix.isdigit():
        return None
    return int(suffix)


def _next_uid_for_alias(alias: str) -> str:
    if not alias:
        return ""
    works = catalog_repo.list_works_by_alias(alias)
    max_num = 0
    for w in works:
        n = _parse_uid_suffix(w.uid, alias)
        if n is not None and n > max_num:
            max_num = n
    return f"{alias}{max_num + 1:03d}"


def _copy_inbox_to_work(inbox_path: str, work_folder: str) -> None:
    if not os.path.exists(inbox_path):
        return

    os.makedirs(work_folder, exist_ok=True)

    if os.path.isfile(inbox_path):
        dest = os.path.join(work_folder, os.path.basename(inbox_path))
        shutil.copy2(inbox_path, dest)
    else:
        base_name = os.path.basename(inbox_path.rstrip(os.sep))
        dest_dir = os.path.join(work_folder, base_name)
        os.makedirs(dest_dir, exist_ok=True)
        for root, dirs, files in os.walk(inbox_path):
            rel = os.path.relpath(root, inbox_path)
            target_root = os.path.join(dest_dir, rel) if rel != "." else dest_dir
            os.makedirs(target_root, exist_ok=True)
            for f in files:
                src_f = os.path.join(root, f)
                dst_f = os.path.join(target_root, f)
                shutil.copy2(src_f, dst_f)


# ----------------------------------------------------------------------
# Single-item dialog
# ----------------------------------------------------------------------


class RouterProcessDialog(tk.Toplevel):
    def __init__(self, parent, selected_path: str, on_created=None):
        super().__init__(parent)
        self.title("Process Router Item")
        self.transient(parent)
        self.grab_set()

        self.selected = selected_path
        self.on_created = on_created

        base = os.path.basename(selected_path)
        title_guess = os.path.splitext(base)[0]
        alias_guess = _guess_alias_from_name(base)
        uid_guess = _next_uid_for_alias(alias_guess) if alias_guess else ""

        self.alias_var = tk.StringVar(value=alias_guess)
        self.uid_var = tk.StringVar(value=uid_guess)
        self.title_var = tk.StringVar(value=title_guess)

        frame = tk.Frame(self, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=f"Source: {selected_path}").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )

        tk.Label(frame, text="Alias").grid(row=1, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.alias_var, width=30).grid(
            row=1, column=1, sticky="ew"
        )

        tk.Label(frame, text="UID (ex: PWC001)").grid(row=2, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.uid_var, width=30).grid(
            row=2, column=1, sticky="ew"
        )

        tk.Label(frame, text="Title").grid(row=3, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.title_var, width=30).grid(
            row=3, column=1, sticky="ew"
        )

        btn_row = tk.Frame(frame)
        btn_row.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))
        tk.Button(btn_row, text="Cancel", command=self._cancel).pack(
            side="right", padx=4
        )
        tk.Button(btn_row, text="Create Work", command=self._create).pack(side="right")

        frame.columnconfigure(1, weight=1)

    def _cancel(self) -> None:
        self.destroy()

    def _create(self) -> None:
        alias = self.alias_var.get().strip()
        uid = self.uid_var.get().strip()
        title = self.title_var.get().strip()

        if not alias or not uid or not title:
            messagebox.showwarning("Router", "Alias, UID, and Title are required.")
            return

        cfg = config_repo.load_config()
        assets = cfg.get("assets_root_path", "")

        if not assets or not os.path.isdir(assets):
            messagebox.showerror("Router", "Assets root not set or invalid.")
            return

        work_folder = os.path.join(assets, alias, uid)
        os.makedirs(work_folder, exist_ok=True)

        _copy_inbox_to_work(self.selected, work_folder)

        w = Work(
            alias=alias,
            uid=uid,
            title=title,
            folder_path=work_folder,
            created_utc=datetime.utcnow(),
        )

        work_repo.save_work(w)
        catalog_repo.save_work_to_catalog(w)

        if self.on_created:
            self.on_created(w)

        messagebox.showinfo("Router", "Work created.")
        self.destroy()


# ----------------------------------------------------------------------
# Batch dialog
# ----------------------------------------------------------------------


class BatchRouterProcessDialog(tk.Toplevel):
    def __init__(self, parent, selected_paths: List[str], on_created=None):
        super().__init__(parent)
        self.title("Batch Process Router Items")
        self.transient(parent)
        self.grab_set()

        self.selected_paths = selected_paths
        self.on_created = on_created

        self.items: List[Dict[str, object]] = []

        frame = tk.Frame(self, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(frame)
        canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(
            frame, orient="vertical", command=canvas.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        inner = tk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        # Auto-UID bases
        alias_to_next_num: Dict[str, int] = {}
        for path in selected_paths:
            base = os.path.basename(path)
            alias = _guess_alias_from_name(base)
            if not alias:
                continue
            if alias not in alias_to_next_num:
                works = catalog_repo.list_works_by_alias(alias)
                max_num = 0
                for w in works:
                    n = _parse_uid_suffix(w.uid, alias)
                    if n is not None and n > max_num:
                        max_num = n
                alias_to_next_num[alias] = max_num + 1

        row = 0
        for path in selected_paths:
            base = os.path.basename(path)
            title_guess = os.path.splitext(base)[0]
            alias_guess = _guess_alias_from_name(base)
            uid_guess = ""

            if alias_guess:
                n = alias_to_next_num.get(alias_guess, 1)
                uid_guess = f"{alias_guess}{n:03d}"
                alias_to_next_num[alias_guess] = n + 1

            tk.Label(inner, text=f"Source: {path}").grid(
                row=row, column=0, columnspan=3, sticky="w", pady=(4, 0)
            )
            row += 1

            alias_var = tk.StringVar(value=alias_guess)
            uid_var = tk.StringVar(value=uid_guess)
            title_var = tk.StringVar(value=title_guess)

            tk.Label(inner, text="Alias").grid(row=row, column=0, sticky="w")
            tk.Entry(inner, textvariable=alias_var, width=12).grid(
                row=row, column=1, sticky="w"
            )
            row += 1

            tk.Label(inner, text="UID").grid(row=row, column=0, sticky="w")
            tk.Entry(inner, textvariable=uid_var, width=12).grid(
                row=row, column=1, sticky="w"
            )
            row += 1

            tk.Label(inner, text="Title").grid(row=row, column=0, sticky="w")
            tk.Entry(inner, textvariable=title_var, width=40).grid(
                row=row, column=1, columnspan=2, sticky="ew"
            )
            row += 1

            tk.Label(inner, text="").grid(row=row, column=0)  # spacer
            row += 1

            self.items.append(
                {
                    "path": path,
                    "alias_var": alias_var,
                    "uid_var": uid_var,
                    "title_var": title_var,
                }
            )

        # Buttons
        btn_row = tk.Frame(self)
        btn_row.pack(fill="x", padx=10, pady=(4, 8))
        tk.Button(btn_row, text="Cancel", command=self._cancel).pack(
            side="right", padx=4
        )
        tk.Button(btn_row, text="Create Works", command=self._create_all).pack(
            side="right"
        )

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"), width=event.width)

        inner.bind("<Configure>", _on_configure)

    def _cancel(self) -> None:
        self.destroy()

    def _create_all(self) -> None:
        cfg = config_repo.load_config()
        assets = cfg.get("assets_root_path", "")

        if not assets or not os.path.isdir(assets):
            messagebox.showerror("Router", "Assets root not set or invalid.")
            return

        created_count = 0

        for item in self.items:
            path = item["path"]  # type: ignore[assignment]
            alias_var: tk.StringVar = item["alias_var"]  # type: ignore[assignment]
            uid_var: tk.StringVar = item["uid_var"]  # type: ignore[assignment]
            title_var: tk.StringVar = item["title_var"]  # type: ignore[assignment]

            alias = alias_var.get().strip()
            uid = uid_var.get().strip()
            title = title_var.get().strip()

            if not alias or not uid or not title:
                messagebox.showwarning(
                    "Router", "All rows must have Alias, UID, and Title."
                )
                return

            work_folder = os.path.join(assets, alias, uid)
            os.makedirs(work_folder, exist_ok=True)
            _copy_inbox_to_work(path, work_folder)

            w = Work(
                alias=alias,
                uid=uid,
                title=title,
                folder_path=work_folder,
                created_utc=datetime.utcnow(),
            )

            work_repo.save_work(w)
            catalog_repo.save_work_to_catalog(w)

            if self.on_created:
                self.on_created(w)

            created_count += 1

        messagebox.showinfo("Router", f"Created {created_count} works.")
        self.destroy()
