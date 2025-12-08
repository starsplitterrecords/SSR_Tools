"""
Details Tab

Comprehensive work viewer with complete metadata, workflow tracking,
file listings, and quick actions.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, Dict

import customtkinter as ctk
from tkinter import ttk
import tkinter as tk

from models.work import Work
from atf_utils import classify_atf_group, ATF_GROUP_ORDER


class DetailsTab:
    """
    Details tab for comprehensive work viewing and editing.

    Shows:
    - Complete work information
    - Workflow progress
    - File lists
    - ATF-grouped file view
    - Metadata
    - Quick actions
    """

    def __init__(self, parent_frame, catalog, config_manager, main_window):
        """
        Initialize the details tab.

        Args:
            parent_frame: Parent CTk frame
            catalog: Catalog instance
            config_manager: ConfigManager instance
            main_window: Reference to main window
        """
        self.parent_frame = parent_frame
        self.catalog = catalog
        self.config = config_manager
        self.main_window = main_window

        # Current work
        self.current_work: Optional[Work] = None

        # Checklist vars keyed by task name
        self.checklist_vars: Dict[str, ctk.BooleanVar] = {}

        # Build UI
        self._create_widgets()

    # ---------------------------------------------------------------------
    # UI construction
    # ---------------------------------------------------------------------

    def _create_widgets(self):
        """Create the tab widgets."""
        # Top control bar
        control_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        control_frame.pack(fill="x", padx=8, pady=(8, 4))

        # Work label
        self.work_label = ctk.CTkLabel(
            control_frame,
            text="No work selected",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.work_label.pack(side="left", padx=8)

        # Action buttons
        action_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        action_frame.pack(side="right", padx=4)

        self.save_button = ctk.CTkButton(
            action_frame,
            text="💾 Save",
            command=self.save_work,
            width=80,
            height=28,
            font=ctk.CTkFont(size=12),
            state="disabled",
        )
        self.save_button.pack(side="left", padx=2)

        self.folder_button = ctk.CTkButton(
            action_frame,
            text="📁 Open Folder",
            command=self.open_folder,
            width=100,
            height=28,
            font=ctk.CTkFont(size=12),
            state="disabled",
        )
        self.folder_button.pack(side="left", padx=2)

        self.refresh_button = ctk.CTkButton(
            action_frame,
            text="🔄 Refresh",
            command=self.refresh,
            width=80,
            height=28,
            font=ctk.CTkFont(size=12),
            state="disabled",
        )
        self.refresh_button.pack(side="left", padx=2)

        # Router / tools buttons live under main window, but we keep hooks here
        btn_grid = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        btn_grid.pack(fill="x", padx=8, pady=(0, 4))

        self.bar_splitter_btn = ctk.CTkButton(
            btn_grid,
            text="🎞 Bar Splitter",
            command=self.open_bar_splitter,
            height=32,
            state="disabled",
        )
        self.bar_splitter_btn.pack(side="left", padx=4, fill="x", expand=True)

        self.image_splitter_btn = ctk.CTkButton(
            btn_grid,
            text="🖼 Image Splitter",
            command=self.open_image_splitter,
            height=32,
            state="disabled",
        )
        self.image_splitter_btn.pack(side="left", padx=4, fill="x", expand=True)

        self.router_btn = ctk.CTkButton(
            btn_grid,
            text="📮 Router",
            command=self.open_router,
            height=32,
            state="disabled",
        )
        self.router_btn.pack(side="left", padx=4, fill="x", expand=True)

        # Main content tabs
        self.content_tabs = ctk.CTkTabview(self.parent_frame)
        self.content_tabs.pack(fill="both", expand=True, padx=8, pady=4)

        self.content_tabs.add("Overview")
        self.content_tabs.add("Workflow")
        self.content_tabs.add("Files")
        self.content_tabs.add("Metadata")

        self._create_overview_tab()
        self._create_workflow_tab()
        self._create_files_tab()
        self._create_metadata_tab()

    # ------------------------------------------------------------------
    # Overview tab
    # ------------------------------------------------------------------

    def _create_overview_tab(self):
        """Create the overview tab."""
        overview = self.content_tabs.tab("Overview")

        grid = ctk.CTkFrame(overview, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=8, pady=8)

        # Identity
        identity_frame = ctk.CTkFrame(grid)
        identity_frame.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(
            identity_frame,
            text="Identity",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=4, pady=(4, 2))

        self.overview_identity = ctk.CTkTextbox(identity_frame, height=140)
        self.overview_identity.pack(fill="both", expand=True, padx=4, pady=4)

        # Status
        status_frame = ctk.CTkFrame(grid)
        status_frame.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(
            status_frame,
            text="Status",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=4, pady=(4, 2))

        self.overview_status = ctk.CTkTextbox(status_frame, height=140)
        self.overview_status.pack(fill="both", expand=True, padx=4, pady=4)

        # Files summary
        files_frame = ctk.CTkFrame(overview)
        files_frame.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(
            files_frame,
            text="Files",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=4, pady=(4, 2))

        self.overview_files = ctk.CTkTextbox(files_frame, height=80)
        self.overview_files.pack(fill="x", padx=4, pady=4)

        # Initialize with "no work" state
        self._clear_all_tabs()

    def _populate_overview(self):
        """Populate the overview tab."""
        work = self.current_work
        if not work:
            return

        # Identity
        self.overview_identity.configure(state="normal")
        self.overview_identity.delete("1.0", "end")
        identity_text = (
            f"Alias: {work.alias}\n"
            f"UID: {work.uid}\n"
            f"Title: {work.title}\n"
            f"Status: {work.status}\n"
            f"Created: {work.created_utc}\n"
            f"Folder: {work.folder_path}"
        )
        self.overview_identity.insert("1.0", identity_text)
        self.overview_identity.configure(state="disabled")

        # Status
        progress = work.get_checklist_progress()
        self.overview_status.configure(state="normal")
        self.overview_status.delete("1.0", "end")
        status_text = (
            f"Status: {work.status}\n"
            f"Progress: {progress['percent_complete']}% "
            f"({progress['completed_count']}/{progress['total']} tasks)\n"
            f"Completed: {', '.join(progress['completed'][:3]) if progress['completed'] else 'None'}\n"
            f"Remaining: {len(progress['incomplete'])} tasks"
        )
        self.overview_status.insert("1.0", status_text)
        self.overview_status.configure(state="disabled")

        # Files summary
        source_count = sum(len(files) for files in work.source_files.values())
        collateral_count = len(work.collateral)

        self.overview_files.configure(state="normal")
        self.overview_files.delete("1.0", "end")
        files_text = (
            f"Source Files: {source_count}\n"
            f"Collateral Files: {collateral_count}\n"
            f"Total Files: {source_count + collateral_count + 1}\n"  # +1 for work.yaml
        )
        self.overview_files.insert("1.0", files_text)
        self.overview_files.configure(state="disabled")

    # ------------------------------------------------------------------
    # Workflow tab
    # ------------------------------------------------------------------

    def _create_workflow_tab(self):
        """Create the workflow/checklist tab."""
        workflow = self.content_tabs.tab("Workflow")

        # Progress
        progress_frame = ctk.CTkFrame(workflow, fg_color="transparent")
        progress_frame.pack(fill="x", padx=8, pady=(8, 4))

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Progress: 0%",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.progress_label.pack(anchor="w", padx=4, pady=4)

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=4, pady=4)
        self.progress_bar.set(0)

        # Checklist
        checklist_frame = ctk.CTkFrame(workflow)
        checklist_frame.pack(fill="both", expand=True, padx=8, pady=4)

        ctk.CTkLabel(
            checklist_frame,
            text="Workflow Checklist",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=8, pady=(8, 4))

        self.checklist_scroll = ctk.CTkScrollableFrame(checklist_frame)
        self.checklist_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _populate_workflow(self):
        """Populate the workflow tab."""
        work = self.current_work
        if not work:
            return

        # Progress numbers
        progress = work.get_checklist_progress()
        self.progress_label.configure(
            text=(
                f"Progress: {progress['percent_complete']}% "
                f"({progress['completed_count']}/{progress['total']})"
            )
        )
        self.progress_bar.set(progress["percent_complete"] / 100 if progress["total"] else 0)

        # Checklist UI
        for widget in self.checklist_scroll.winfo_children():
            widget.destroy()
        self.checklist_vars.clear()

        for task_name, is_complete in work.checklist.items():
            task_frame = ctk.CTkFrame(self.checklist_scroll, fg_color="transparent")
            task_frame.pack(fill="x", padx=4, pady=2)

            var = ctk.BooleanVar(value=is_complete)
            self.checklist_vars[task_name] = var

            checkbox = ctk.CTkCheckBox(
                task_frame,
                text=task_name.replace("_", " ").title(),
                variable=var,
                command=lambda t=task_name: self._toggle_task(t),
                font=ctk.CTkFont(size=13),
            )
            checkbox.pack(side="left", padx=4, pady=4)

    # ------------------------------------------------------------------
    # Files tab (including E16 ATF grouping)
    # ------------------------------------------------------------------

    def _create_files_tab(self):
        """Create the files tab."""
        files = self.content_tabs.tab("Files")

        # Sub-tabs
        self.file_tabs = ctk.CTkTabview(files)
        self.file_tabs.pack(fill="both", expand=True, padx=4, pady=4)

        self.file_tabs.add("Collateral")
        self.file_tabs.add("Source Files")
        self.file_tabs.add("All Files")
        self.file_tabs.add("ATF Types")  # E16: ATF grouping

        # Collateral tab
        self.collateral_frame = ctk.CTkScrollableFrame(self.file_tabs.tab("Collateral"))
        self.collateral_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Source files tab
        self.source_files_frame = ctk.CTkScrollableFrame(self.file_tabs.tab("Source Files"))
        self.source_files_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # All files tab
        self.all_files_frame = ctk.CTkScrollableFrame(self.file_tabs.tab("All Files"))
        self.all_files_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # ATF Types tab
        self.atf_types_frame = ctk.CTkScrollableFrame(self.file_tabs.tab("ATF Types"))
        self.atf_types_frame.pack(fill="both", expand=True, padx=4, pady=4)

    def _populate_files(self):
        """Populate the files tab."""
        work = self.current_work
        if not work:
            # Ensure frames are cleared if no work
            for frame in (
                self.collateral_frame,
                self.source_files_frame,
                self.all_files_frame,
                self.atf_types_frame,
            ):
                for widget in frame.winfo_children():
                    widget.destroy()
            return

        # Clear frames
        for widget in self.collateral_frame.winfo_children():
            widget.destroy()
        for widget in self.source_files_frame.winfo_children():
            widget.destroy()
        for widget in self.all_files_frame.winfo_children():
            widget.destroy()
        for widget in self.atf_types_frame.winfo_children():
            widget.destroy()

        # --- Collateral view ---
        if work.collateral:
            for collat in work.collateral:
                item = ctk.CTkFrame(self.collateral_frame)
                item.pack(fill="x", padx=4, pady=2)

                ctk.CTkLabel(
                    item,
                    text=f"{collat.file_type} #{collat.counter:02d}",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    anchor="w",
                ).pack(anchor="w", padx=8, pady=(4, 0))

                ctk.CTkLabel(
                    item,
                    text=collat.filename,
                    font=ctk.CTkFont(size=12),
                    text_color="gray",
                    anchor="w",
                ).pack(anchor="w", padx=8, pady=(0, 4))
        else:
            ctk.CTkLabel(
                self.collateral_frame,
                text="No collateral files",
                text_color="gray",
            ).pack(pady=20)

        # --- Source files view ---
        has_source = False
        for category, files in work.source_files.items():
            if not files:
                continue

            has_source = True
            cat_label = ctk.CTkLabel(
                self.source_files_frame,
                text=category.replace("_", " ").title(),
                font=ctk.CTkFont(size=15, weight="bold"),
            )
            cat_label.pack(anchor="w", padx=8, pady=(8, 4))

            for source in files:
                ctk.CTkLabel(
                    self.source_files_frame,
                    text=f"• {source.filename}",
                    font=ctk.CTkFont(size=12),
                    anchor="w",
                ).pack(anchor="w", padx=16, pady=1)

        if not has_source:
            ctk.CTkLabel(
                self.source_files_frame,
                text="No source files",
                text_color="gray",
            ).pack(pady=20)

        # --- All files view (work.yaml + source + collateral) ---
        all_files = work.get_all_declared_files()
        for filename in all_files:
            ctk.CTkLabel(
                self.all_files_frame,
                text=f"• {filename}",
                font=ctk.CTkFont(size=12),
                anchor="w",
            ).pack(anchor="w", padx=8, pady=1)

        # --- E16: ATF Types grouped view ---
        groups = {name: [] for name in ATF_GROUP_ORDER}

        # Collateral: we have explicit ATF file_type + counter
        for collat in work.collateral:
            group_name = classify_atf_group(collat.filename, getattr(collat, "file_type", None))
            label = f"{collat.file_type} #{collat.counter:02d} — {collat.filename}"
            groups[group_name].append(label)

        # Source files: usually not ATF collateral, but classify by name/ext
        for category, files in work.source_files.items():
            for source in files:
