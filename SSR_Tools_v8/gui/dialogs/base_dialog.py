from __future__ import annotations

"""
BaseDialog: standard SSR-compliant dialog foundation.

All dialogs inherit from this class to ensure:
- consistent padding and spacing
- consistent fonts and colors (via gui.style)
- button row bottom-right
- optional scrollable content area
- transient+grab_set behavior
"""

import tkinter as tk
from tkinter import ttk

from gui import style


class BaseDialog(tk.Toplevel):
    """
    A unified dialog wrapper providing consistent behavior.

    Subclasses must override:
        self._build_body(body_frame)
        self._on_submit()

    Optional:
        self._on_cancel()
    """

    WIDTH = 520
    HEIGHT = 480

    def __init__(self, parent, *, scrollable: bool = False, title: str = ""):
        super().__init__(parent)
        self.parent = parent
        self.scrollable = scrollable

        # Window basics
        self.title(title or "Dialog")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.transient(parent)
        self.grab_set()

        # Root layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # ------------------------------------------------------------------
        # BODY REGION
        # ------------------------------------------------------------------
        if scrollable:
            outer = tk.Frame(self, bg=style.MAIN_BG)
            outer.grid(row=0, column=0, sticky="nsew")

            outer.rowconfigure(0, weight=1)
            outer.columnconfigure(0, weight=1)

            canvas = tk.Canvas(
                outer,
                bg=style.MAIN_BG,
                highlightthickness=0,
                bd=0,
            )
            canvas.grid(row=0, column=0, sticky="nsew")

            scrollbar = ttk.Scrollbar(
                outer, orient="vertical", command=canvas.yview
            )
            scrollbar.grid(row=0, column=1, sticky="ns")
            canvas.configure(yscrollcommand=scrollbar.set)

            body = tk.Frame(canvas, bg=style.MAIN_BG)
            self.body_window = canvas.create_window(
                (0, 0), window=body, anchor="nw"
            )

            def _on_config(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.itemconfig(self.body_window, width=event.width)

            canvas.bind("<Configure>", _on_config)
            self._body = body
        else:
            body = tk.Frame(self, bg=style.MAIN_BG)
            body.grid(row=0, column=0, sticky="nsew")
            self._body = body

        # ------------------------------------------------------------------
        # BUTTON ROW
        # ------------------------------------------------------------------
        btn_row = tk.Frame(self, bg=style.MAIN_BG)
        btn_row.grid(
            row=1,
            column=0,
            sticky="e",
            padx=style.PAD_X,
            pady=(style.PAD_Y, style.PAD_Y_LARGE),
        )

        cancel_btn = tk.Button(
            btn_row, text="Cancel", command=self._cancel_clicked
        )
        cancel_btn.pack(side="right", padx=4)

        submit_btn = tk.Button(
            btn_row, text="OK", command=self._submit_clicked
        )
        submit_btn.pack(side="right", padx=4)

        # ------------------------------------------------------------------
        # BUILD
        # ------------------------------------------------------------------
        self._build_body(self._body)

    # ----------------------------------------------------------------------
    # SUBCLASS HOOKS
    # ----------------------------------------------------------------------

    def _build_body(self, body: tk.Frame) -> None:
        """Override in subclass. Build the actual dialog content."""
        raise NotImplementedError

    def _on_submit(self) -> bool:
        """
        Override in subclass. Return True if dialog can close.
        Return False to keep the dialog open.
        """
        return True

    def _on_cancel(self) -> None:
        """Override in subclass if special logic needed."""
        pass

    # ----------------------------------------------------------------------
    # INTERNAL HANDLERS
    # ----------------------------------------------------------------------

    def _submit_clicked(self) -> None:
        ok = self._on_submit()
        if ok:
            self.destroy()

    def _cancel_clicked(self) -> None:
        self._on_cancel()
        self.destroy()
