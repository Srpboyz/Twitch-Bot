from __future__ import annotations
from typing import TYPE_CHECKING

from twitch_bot.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QWidget

if TYPE_CHECKING:
    from .window import MainWindow


class Body(QFrame):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(0)
        self.setMidLineWidth(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setLayout(layout)

    def addWidget(self, widget: QWidget, stretch: int):
        self.layout().addWidget(widget, stretch)

    @property
    def window(self) -> MainWindow:
        return self._window
