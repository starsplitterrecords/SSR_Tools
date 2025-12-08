from __future__ import annotations

"""
Shared UI style constants and helpers for the Tkinter GUI.

All GUI modules should import from this file instead of hardcoding
colors, fonts, or padding values.
"""

import tkinter as tk

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

TOPBAR_BG = "#303030"
TOPBAR_FG = "#ffffff"

MAIN_BG = "#1e1e1e"
MAIN_FG = "#ffffff"

PANEL_BG = "#1e1e1e"
PANEL_FG = "#ffffff"

BUTTON_BG = "#3a3a3a"
BUTTON_FG = "#ffffff"

ENTRY_BG = "#1e1e1e"
ENTRY_FG = "#ffffff"

HIGHLIGHT_BG = "#454545"
DISABLED_FG = "#777777"

SEPARATOR_COLOR = "#444444"

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

FONT_FAMILY = "Segoe UI"

FONT_SIZE_SMALL = 9
FONT_SIZE_BASE = 10
FONT_SIZE_LARGE = 12
FONT_SIZE_TITLE = 14

# ---------------------------------------------------------------------------
# Spacing
# ---------------------------------------------------------------------------

PAD_X_SMALL = 4
PAD_Y_SMALL = 2

PAD_X = 8
PAD_Y = 4

PAD_X_LARGE = 12
PAD_Y_LARGE = 8

SECTION_GAP = 10

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def apply_global_style(root: tk.Tk) -> None:
    """
    Apply global Tkinter options for fonts and basic widget styling.
    """
    # Wrap family in {} so Tk treats "Segoe UI" as a single token
    base_font = f"{{{FONT_FAMILY}}} {FONT_SIZE_BASE}"

    root.option_add("*Font", base_font)

    # Labels
    root.option_add("*Label.foreground", MAIN_FG)
    root.option_add("*Label.background", MAIN_BG)

    # Frames
    root.option_add("*Frame.background", MAIN_BG)

    # Buttons
    root.option_add("*Button.background", BUTTON_BG)
    root.option_add("*Button.foreground", BUTTON_FG)
    root.option_add("*Button.activeBackground", HIGHLIGHT_BG)
    root.option_add("*Button.font", base_font)

    # Entries
    root.option_add("*Entry.background", ENTRY_BG)
    root.option_add("*Entry.foreground", ENTRY_FG)
    root.option_add("*Entry.insertBackground", ENTRY_FG)
    root.option_add("*Entry.font", base_font)

    # Text
    root.option_add("*Text.background", ENTRY_BG)
    root.option_add("*Text.foreground", ENTRY_FG)
    root.option_add("*Text.insertBackground", ENTRY_FG)
    root.option_add("*Text.font", base_font)

    # Listbox
    root.option_add("*Listbox.background", ENTRY_BG)
    root.option_add("*Listbox.foreground", ENTRY_FG)
    root.option_add("*Listbox.selectBackground", HIGHLIGHT_BG)
    root.option_add("*Listbox.selectForeground", ENTRY_FG)
    root.option_add("*Listbox.font", base_font)

    # Scrollbar
    root.option_add("*Scrollbar.troughColor", MAIN_BG)

