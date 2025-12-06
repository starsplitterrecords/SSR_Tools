# app.py
# Entry point for the Flet-based SSR Tools application.

import flet as ft
from gui.main_view import MainView


def main(page: ft.Page) -> None:
    page.title = "SSR Tools"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="blue")

    # 1. Create MainView instance
    app_view = MainView(page)

    # 2. Add its root control (NOT a ft.View in Flet 0.28)
    page.add(app_view.view)

    page.update()

    # 3. Safe to refresh tabs after controls attached
    app_view.initialize()


if __name__ == "__main__":
    ft.app(target=main)