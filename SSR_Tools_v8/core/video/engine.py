from __future__ import annotations
import flet as ft


class BarSplitterTab(ft.Container):
    """
    Placeholder Bar Splitter Tab.
    Real processing will be restored later.
    """

    def __init__(self, eventbus):
        super().__init__()
        self.eventbus = eventbus
        self.expand = True
        self.padding = 20

        self.content = ft.Column(
            controls=[
                ft.Text("Bar Splitter temporarily disabled.", size=20),
                ft.Text("Engine function `generate_beat_synced_video` missing."),
                ft.Text("This tab will be restored later."),
            ]
        )
