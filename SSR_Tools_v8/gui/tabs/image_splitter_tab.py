from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.image.engine import generate_images_for_work
from core.models import Work
from data import catalog_repo, work_repo
from helpers.events import EventBus


class ImageSplitterTab(tk.Frame):
    """
    Image generation UI (Tkinter).
    """

    def __init__(self, parent, eventbus: EventBus):
        super().__init__(parent, bg="#1e1e1e")
        self.eventbus = eventbus

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        header = tk.Frame(self, bg="#1e1e1e")
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=4)

        tk.Label(
            header,
            text="Image Splitter",
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

        tk.Button(header, text="Refresh Works", command=self.refresh).pack(
            side="right"
        )

        # Work list
        work_frame = tk.Frame(self, bg="#1e1e1e")
        work_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))
        work_frame.columnconfigure(0, weight=1)
        work_frame.rowconfigure(1, weight=1)

        tk.Label(
            work_frame,
            text="Works",
            bg="#1e1e1e",
            fg="#ffffff",
        ).grid(row=0, column=0, sticky="w")

        self.work_list = tk.Listbox(work_frame, height=8)
        self.work_list.grid(row=1, column=0, sticky="nsew")
        self.work_list.bind("<<ListboxSelect>>", self._on_select_work)

        vsb = ttk.Scrollbar(work_frame, orient="vertical", command=self.work_list.yview)
        self.work_list.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")

        # Options
        options_frame = tk.Frame(self, bg="#1e1e1e")
        options_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 4))

        tk.Label(
            options_frame,
            text="Output Format",
            bg="#1e1e1e",
            fg="#ffffff",
        ).grid(row=0, column=0, sticky="w")

        self.format_var = tk.StringVar()
        self.format_cb = ttk.Combobox(
            options_frame,
            textvariable=self.format_var,
            state="readonly",
            values=[
                "Instagram Square",
                "Instagram Carousel (4:5)",
                "Instagram Story",
                "Twitter Card",
                "Grid 2x2",
                "Grid 3x3",
            ],
        )
        self.format_cb.grid(row=1, column=0, sticky="w")

        tk.Button(
            options_frame, text="Pick Images", command=self._pick_images
        ).grid(row=1, column=1, padx=6)
        tk.Button(
            options_frame, text="Generate", command=self._run_generation
        ).grid(row=1, column=2, padx=6)

        # Log
        self.log = tk.Text(self, height=10)
        self.log.grid(row=3, column=0, sticky="nsew", padx=8, pady=(4, 8))

        self._works: list[Work] = []
        self._file_paths: list[str] = []

        eventbus.subscribe("work_created", lambda w: self.refresh())
        eventbus.subscribe("work_updated", lambda w: self.refresh())

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        self._works = catalog_repo.list_works()
        self._works.sort(key=lambda w: (w.alias, w.uid))
        self.work_list.delete(0, tk.END)
        for w in self._works:
            self.work_list.insert(tk.END, f"{w.alias} · {w.uid} · {w.title}")

    def _on_select_work(self, event) -> None:
        # selection just sets index; nothing else needed here
        pass

    def _pick_images(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select source images",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"), ("All", "*.*")],
        )
        if not files:
            return
        self._file_paths = list(files)
        self._log(f"Selected {len(self._file_paths)} files")

    def _log(self, msg: str) -> None:
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def _run_generation(self) -> None:
        sel = self.work_list.curselection()
        if not sel:
            self._log("No work selected")
            return
        index = sel[0]
        if index >= len(self._works):
            return
        work = self._works[index]

        if not self._file_paths:
            self._log("No images selected")
            return
        if not self.format_var.get():
            self._log("Choose a format")
            return

        fmt = self.format_var.get()

        def progress(msg: str) -> None:
            self._log(msg)

        out = generate_images_for_work(
            work=work,
            source_images=self._file_paths,
            format_str=fmt,
            quality=92,
            count=len(self._file_paths),
            callback=progress,
        )
        self._log(f"Generated {len(out)} file(s)")
        work_repo.save_work(work)
        self._log("Work saved")
        self.eventbus.publish("work_updated", work)
