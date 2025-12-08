from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog

from core.image.engine import generate_images_for_work
from core.models import Work
from data import catalog_repo, work_repo
from helpers.events import EventBus

from gui import style


class ImageSplitterTab(tk.Frame):
    """
    Image generation UI (Tkinter) — rewritten for A1+B1.

    Layout:
        +----------------------------------------------------------+
        | Header: Image Splitter + Refresh                         |
        +----------------------------------------------------------+
        |   LEFT: Work List   |  MIDDLE: Options  |  RIGHT: Log    |
        +----------------------------------------------------------+
    """

    FORMATS = [
        "Instagram Square",
        "Instagram Carousel (4:5)",
        "Instagram Story",
        "Twitter Card",
        "Grid 2x2",
        "Grid 3x3",
    ]

    def __init__(self, parent, eventbus: EventBus):
        super().__init__(parent, bg=style.MAIN_BG)
        self.eventbus = eventbus

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # ------------------------------------------------------------------
        # HEADER
        # ------------------------------------------------------------------
        header = tk.Frame(self, bg=style.MAIN_BG)
        header.grid(row=0, column=0, sticky="ew", padx=style.PAD_X, pady=style.PAD_Y)

        tk.Label(
            header,
            text="Image Splitter",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
            font=(style.FONT_FAMILY, style.FONT_SIZE_LARGE, "bold"),
        ).pack(side="left")

        tk.Button(
            header,
            text="Refresh Works",
            command=self.refresh,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(side="right")

        # ------------------------------------------------------------------
        # GRID LAYOUT FOR 3-COLUMN ARRANGEMENT
        # ------------------------------------------------------------------
        body = tk.Frame(self, bg=style.MAIN_BG)
        body.grid(row=2, column=0, sticky="nsew", padx=style.PAD_X, pady=(0, style.PAD_Y_LARGE))

        body.columnconfigure(0, weight=0)  # Work list
        body.columnconfigure(1, weight=0)  # Options
        body.columnconfigure(2, weight=1)  # Log
        body.rowconfigure(0, weight=1)

        # ------------------------------------------------------------------
        # LEFT COLUMN — WORK LIST
        # ------------------------------------------------------------------
        left = tk.Frame(body, bg=style.MAIN_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, style.PAD_X_LARGE))

        tk.Label(
            left,
            text="Works",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).pack(anchor="w", pady=(0, style.PAD_Y))

        self.work_list = tk.Listbox(left, height=14)
        self.work_list.pack(fill="both", expand=True)
        self.work_list.bind("<<ListboxSelect>>", self._on_select_work)

        vsb = ttk.Scrollbar(left, orient="vertical", command=self.work_list.yview)
        self.work_list.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # ------------------------------------------------------------------
        # MIDDLE COLUMN — OPTIONS
        # ------------------------------------------------------------------
        mid = tk.Frame(body, bg=style.MAIN_BG)
        mid.grid(row=0, column=1, sticky="n", padx=(0, style.PAD_X_LARGE))

        tk.Label(
            mid,
            text="Output Format",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).pack(anchor="w", pady=(0, style.PAD_Y_SMALL))

        self.format_var = tk.StringVar()
        self.format_cb = ttk.Combobox(
            mid,
            textvariable=self.format_var,
            state="readonly",
            values=self.FORMATS,
            width=28,
        )
        self.format_cb.pack(anchor="w", pady=(0, style.PAD_Y))

        tk.Button(
            mid,
            text="Pick Images",
            command=self._pick_images,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(anchor="w", pady=(0, style.PAD_Y))

        tk.Button(
            mid,
            text="Generate",
            command=self._run_generation,
            bg=style.BUTTON_BG,
            fg=style.BUTTON_FG,
        ).pack(anchor="w", pady=(0, style.PAD_Y))

        # ------------------------------------------------------------------
        # RIGHT COLUMN — LOG PANEL
        # ------------------------------------------------------------------
        right = tk.Frame(body, bg=style.MAIN_BG)
        right.grid(row=0, column=2, sticky="nsew")

        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        tk.Label(
            right,
            text="Log",
            bg=style.MAIN_BG,
            fg=style.MAIN_FG,
        ).grid(row=0, column=0, sticky="w", pady=(0, style.PAD_Y))

        log_container = tk.Frame(right, bg=style.MAIN_BG)
        log_container.grid(row=1, column=0, sticky="nsew")

        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)

        self.log = tk.Text(log_container, height=14)
        self.log.grid(row=0, column=0, sticky="nsew")

        log_vsb = ttk.Scrollbar(log_container, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=log_vsb.set)
        log_vsb.grid(row=0, column=1, sticky="ns")

        # ------------------------------------------------------------------
        # INTERNAL STATE
        # ------------------------------------------------------------------
        self._works: list[Work] = []
        self._file_paths: list[str] = []

        eventbus.subscribe("work_created", lambda w: self.refresh())
        eventbus.subscribe("work_updated", lambda w: self.refresh())

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    def _log(self, msg: str) -> None:
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def _on_select_work(self, event) -> None:
        # Work selection does not need extra logic here
        pass

    def refresh(self) -> None:
        self._works = catalog_repo.list_works()
        self._works.sort(key=lambda w: (w.alias, w.uid))

        self.work_list.delete(0, tk.END)
        for w in self._works:
            self.work_list.insert(tk.END, f"{w.alias} · {w.uid} · {w.title}")

    def _pick_images(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select source images",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"), ("All", "*.*")],
        )
        if not files:
            return

        self._file_paths = list(files)
        self._log(f"Selected {len(self._file_paths)} files")

    # ------------------------------------------------------------------
    # IMAGE GENERATION
    # ------------------------------------------------------------------

    def _run_generation(self) -> None:
        sel = self.work_list.curselection()
        if not sel:
            self._log("No work selected.")
            return

        index = sel[0]
        if index >= len(self._works):
            return

        work = self._works[index]

        if not self._file_paths:
            self._log("No images selected.")
            return

        if not self.format_var.get():
            self._log("Choose an output format.")
            return

        fmt = self.format_var.get()

        def progress(msg: str) -> None:
            self._log(msg)

        # Call core engine
        out = generate_images_for_work(
            work=work,
            source_images=self._file_paths,
            format_str=fmt,
            quality=92,
            count=len(self._file_paths),
            callback=progress,
        )

        self._log(f"Generated {len(out)} file(s)")

        # Persist work changes
        work_repo.save_work(work)
        self.eventbus.publish("work_updated", work)
        self._log("Work saved.")
