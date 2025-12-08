from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import List, Dict

import tkinter as tk
from tkinter import messagebox

from core.models import Work
from data import config_repo, work_repo, catalog_repo

from gui.dialogs.base_dialog import BaseDialog
from gui import style


# ----------------------------------------------------------------------
# INTERNAL HELPERS (unchanged logic)
# ----------------------------------------------------------------------

def _guess_alias_from_name(name: str) -> str:
    base = os.path.basename(name)
    if "-" in base:
        return base.split("-", 1)[0].strip()
    return ""


def _parse_uid_suffix(uid: str, alias: str) -> int | None:
    if not uid.startswith(alias):
        return None
    suffix = uid[len(alias):]
    if suffix.isdigit():
        return int(suffix)
    return None


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
        dst = os.path.join(work_folder, os.path.basename(inbox_path))
        shutil.copy2(inbox_path, dst)
        return

    base = os.path.basename(inbox_path.rstrip(os.sep))
    dest_dir = os.path.join(work_folder, base)
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
# SINGLE ITEM ROUTER DIALOG
# ----------------------------------------------------------------------

class RouterProcessDialog(BaseDialog):
    """
    Dialog for processing a single inbox item into a new Work.

    Uses BaseDialog for consistent styling.
    """

    def __init__(self, parent, selected_path: str, on_created=None):
        self.selected_path = selected_path
        self.on_created = on_created

        # Suggestions
        base = os.path.basename(selected_path)
        title_guess = os.path.splitext(base)[0]
        alias_guess = _guess_alias_from_name(base)
        uid_guess = _next_uid_for_alias(alias_guess) if alias_guess else ""

        # Vars
        self.alias_var = tk.StringVar(value=alias_guess)
        self.uid_var = tk.StringVar(value=uid_guess)
        self.title_var = tk.StringVar(value=title_guess)

        super().__init__(parent, scrollable=False, title="Process Router Item")

    # ------------------------------------------------------------------
    # BUILD BODY
    # ------------------------------------------------------------------

    def _build_body(self, body: tk.Frame) -> None:
        body.columnconfigure(1, weight=1)

        # Source label
        tk.Label(
            body,
            text=f"Source: {self.selected_path}",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).grid(row=0, column=0, columnspan=2, sticky="w",
               pady=(0, style.PAD_Y_LARGE))

        # Alias
        tk.Label(body, text="Alias", bg=style.MAIN_BG, fg=style.MAIN_FG)\
            .grid(row=1, column=0, sticky="w")
        tk.Entry(body, textvariable=self.alias_var)\
            .grid(row=1, column=1, sticky="ew", pady=(0, style.PAD_Y))

        # UID
        tk.Label(body, text="UID (ex: PWC001)", bg=style.MAIN_BG, fg=style.MAIN_FG)\
            .grid(row=2, column=0, sticky="w")
        tk.Entry(body, textvariable=self.uid_var)\
            .grid(row=2, column=1, sticky="ew", pady=(0, style.PAD_Y))

        # Title
        tk.Label(body, text="Title", bg=style.MAIN_BG, fg=style.MAIN_FG)\
            .grid(row=3, column=0, sticky="w")
        tk.Entry(body, textvariable=self.title_var)\
            .grid(row=3, column=1, sticky="ew", pady=(0, style.PAD_Y))

    # ------------------------------------------------------------------
    # SUBMIT
    # ------------------------------------------------------------------

    def _on_submit(self) -> bool:
        alias = self.alias_var.get().strip()
        uid = self.uid_var.get().strip()
        title = self.title_var.get().strip()

        if not alias or not uid or not title:
            messagebox.showwarning("Router", "Alias, UID, and Title are required.")
            return False

        cfg = config_repo.load_config()
        assets = cfg.get("assets_root_path", "")

        if not assets or not os.path.isdir(assets):
            messagebox.showerror("Router", "Assets root not set or invalid.")
            return False

        # Create work folder
        work_folder = os.path.join(assets, alias, uid)
        os.makedirs(work_folder, exist_ok=True)

        _copy_inbox_to_work(self.selected_path, work_folder)

        # Build work
        work = Work(
            alias=alias,
            uid=uid,
            title=title,
            folder_path=work_folder,
            created_utc=datetime.utcnow(),
        )

        work_repo.save_work(work)
        catalog_repo.save_work_to_catalog(work)

        if self.on_created:
            self.on_created(work)

        messagebox.showinfo("Router", "Work created.")
        return True


# ----------------------------------------------------------------------
# BATCH ROUTER DIALOG
# ----------------------------------------------------------------------

class BatchRouterProcessDialog(BaseDialog):
    """
    Batch process multiple inbox items into Works.

    Uses BaseDialog with scrollable=True.
    """

    def __init__(self, parent, selected_paths: List[str], on_created=None):
        self.selected_paths = selected_paths
        self.on_created = on_created

        # Holds { path, alias_var, uid_var, title_var }
        self.items: List[Dict[str, object]] = []

        super().__init__(parent, scrollable=True, title="Batch Process Router Items")

    # ------------------------------------------------------------------
    # BUILD BODY
    # ------------------------------------------------------------------

    def _build_body(self, body: tk.Frame) -> None:
        row = 0

        # Build alias UID counters
        alias_to_next_num: Dict[str, int] = {}
        for path in self.selected_paths:
            base = os.path.basename(path)
            alias = _guess_alias_from_name(base)
            if alias:
                if alias not in alias_to_next_num:
                    works = catalog_repo.list_works_by_alias(alias)
                    max_num = 0
                    for w in works:
                        n = _parse_uid_suffix(w.uid, alias)
                        if n is not None and n > max_num:
                            max_num = n
                    alias_to_next_num[alias] = max_num + 1

        for path in self.selected_paths:
            base = os.path.basename(path)
            alias_guess = _guess_alias_from_name(base)
            title_guess = os.path.splitext(base)[0]

            uid_guess = ""
            if alias_guess:
                n = alias_to_next_num[alias_guess]
                uid_guess = f"{alias_guess}{n:03d}"
                alias_to_next_num[alias_guess] = n + 1

            # Display path
            tk.Label(
                body,
                text=f"Source: {path}",
                bg=style.MAIN_BG,
                fg=style.MAIN_FG,
            ).grid(row=row, column=0, columnspan=3, sticky="w",
                   pady=(style.PAD_Y_SMALL, 0))
            row += 1

            alias_var = tk.StringVar(value=alias_guess)
            uid_var = tk.StringVar(value=uid_guess)
            title_var = tk.StringVar(value=title_guess)

            # Alias field
            tk.Label(body, text="Alias", bg=style.MAIN_BG, fg=style.MAIN_FG)\
                .grid(row=row, column=0, sticky="w")
            tk.Entry(body, textvariable=alias_var, width=14)\
                .grid(row=row, column=1, sticky="w")
            row += 1

            # UID field
            tk.Label(body, text="UID", bg=style.MAIN_BG, fg=style.MAIN_FG)\
                .grid(row=row, column=0, sticky="w")
            tk.Entry(body, textvariable=uid_var, width=14)\
                .grid(row=row, column=1, sticky="w")
            row += 1

            # Title field
            tk.Label(body, text="Title", bg=style.MAIN_BG, fg=style.MAIN_FG)\
                .grid(row=row, column=0, sticky="w")
            tk.Entry(body, textvariable=title_var, width=40)\
                .grid(row=row, column=1, sticky="ew", columnspan=2)
            row += 1

            # Spacer
            tk.Label(body, text="", bg=style.MAIN_BG).grid(row=row, column=0)
            row += 1

            self.items.append(
                {
                    "path": path,
                    "alias_var": alias_var,
                    "uid_var": uid_var,
                    "title_var": title_var,
                }
            )

    # ------------------------------------------------------------------
    # SUBMIT (CREATE ALL)
    # ------------------------------------------------------------------

    def _on_submit(self) -> bool:
        cfg = config_repo.load_config()
        assets = cfg.get("assets_root_path", "")

        if not assets or not os.path.isdir(assets):
            messagebox.showerror("Router", "Assets root not set or invalid.")
            return False

        created_count = 0

        for item in self.items:
            path = item["path"]              # type: ignore
            alias_var = item["alias_var"]    # type: ignore
            uid_var = item["uid_var"]        # type: ignore
            title_var = item["title_var"]    # type: ignore

            alias = alias_var.get().strip()
            uid = uid_var.get().strip()
            title = title_var.get().strip()

            if not alias or not uid or not title:
                messagebox.showwarning(
                    "Router",
                    "All rows must have Alias, UID, and Title."
                )
                return False

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
        return True
