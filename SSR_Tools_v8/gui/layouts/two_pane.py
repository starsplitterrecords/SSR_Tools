from __future__ import annotations

"""
Reusable two-pane layout container for SSR Tools UI.

Provides a consistent left/right split with optional scrollability.
Tabs should use this layout rather than custom geometry.
"""

import tkinter as tk
from tkinter import ttk

from gui import style


class TwoPane(tk.Frame):
    """
    A standardized two-pane container:

        +-------------------------------+
        |           PARENT              |
        |  +-----------+ +-----------+  |
        |  |  left     | |  right    |  |
        |  |  pane     | |  pane     |  |
        |  +-----------+ +-----------+  |
        +-------------------------------+

    - Left and right panes expand.
    - Optional scrollbars for each pane.
    - Consistent padding, background, and separation line.
    """

    def __init__(
        self,
        parent,
        *,
        left_scroll: bool = False,
        right_scroll: bool = False,
        left_width: int = 300,
        separator: bool = True,
    ):
        super().__init__(parent, bg=style.MAIN_BG)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        # ------------------------------------------------------------------
        # LEFT PANE
        # ------------------------------------------------------------------
        if left_scroll:
            left_container = tk.Frame(self, bg=style.MAIN_BG)
            left_container.grid(row=0, column=0, sticky="nsew")
            left_container.rowconfigure(0, weight=1)
            left_container.columnconfigure(0, weight=1)

            self.left_canvas = tk.Canvas(
                left_container,
                bg=style.MAIN_BG,
                highlightthickness=0,
                bd=0,
            )
            self.left_canvas.grid(row=0, column=0, sticky="nsew")

            yscroll = ttk.Scrollbar(
                left_container, orient="vertical", command=self.left_canvas.yview
            )
            yscroll.grid(row=0, column=1, sticky="ns")

            self.left_canvas.configure(yscrollcommand=yscroll.set)

            self.left_frame = tk.Frame(self.left_canvas, bg=style.MAIN_BG)
            self.left_canvas.create_window((0, 0), window=self.left_frame, anchor="nw")

            def _on_left_config(event):
                self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
                self.left_canvas.itemconfig(self.left_frame_window, width=event.width)

            self.left_frame_window = self.left_canvas.create_window(
                (0, 0), window=self.left_frame, anchor="nw"
            )
            self.left_canvas.bind("<Configure>", _on_left_config)

        else:
            self.left_frame = tk.Frame(self, bg=style.MAIN_BG)
            self.left_frame.grid(row=0, column=0, sticky="nsew")

        # Fix width
        self.left_frame.configure(width=left_width)
        self.grid_columnconfigure(0, minsize=left_width)

        # ------------------------------------------------------------------
        # SEPARATOR
        # ------------------------------------------------------------------
        if separator:
            sep = tk.Frame(self, bg=style.SEPARATOR_COLOR, width=1)
            sep.grid(row=0, column=1, sticky="ns")

        # ------------------------------------------------------------------
        # RIGHT PANE
        # ------------------------------------------------------------------
        if right_scroll:
            right_container = tk.Frame(self, bg=style.MAIN_BG)
            right_container.grid(row=0, column=2, sticky="nsew")
            right_container.rowconfigure(0, weight=1)
            right_container.columnconfigure(0, weight=1)

            self.right_canvas = tk.Canvas(
                right_container,
                bg=style.MAIN_BG,
                highlightthickness=0,
                bd=0,
            )
            self.right_canvas.grid(row=0, column=0, sticky="nsew")

            yscroll = ttk.Scrollbar(
                right_container, orient="vertical", command=self.right_canvas.yview
            )
            yscroll.grid(row=0, column=1, sticky="ns")

            self.right_canvas.configure(yscrollcommand=yscroll.set)

            self.right_frame = tk.Frame(self.right_canvas, bg=style.MAIN_BG)
            self.right_canvas.create_window((0, 0), window=self.right_frame, anchor="nw")

            def _on_right_config(event):
                self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))
                self.right_canvas.itemconfig(
                    self.right_frame_window, width=event.width
                )

            self.right_frame_window = self.right_canvas.create_window(
                (0, 0), window=self.right_frame, anchor="nw"
            )
            self.right_canvas.bind("<Configure>", _on_right_config)

        else:
            self.right_frame = tk.Frame(self, bg=style.MAIN_BG)
            self.right_frame.grid(row=0, column=2, sticky="nsew")

        # ------------------------------------------------------------------
        # Exposed attributes
        # ------------------------------------------------------------------
        self.left = self.left_frame
        self.right = self.right_frame

