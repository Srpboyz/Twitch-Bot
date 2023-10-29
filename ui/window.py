from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QCloseEvent
from PyQt6.QtWidgets import QMainWindow

from .body import Body
from .sidebar import Sidebar
from .stack import Stack
from .systemtray import SystemTray
from .logs import Logs
from network import Client

if TYPE_CHECKING:
    from .sidebar import Sidebar
    from .stack import Stack


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowIcon(QIcon("icons/twitch.ico"))
        self.setWindowTitle("Twitch Bot")
        self.client = Client(self)

        self.body = Body(self)
        self.systemTray = SystemTray(self)
        self.sidebar = Sidebar(self)
        self.stack = Stack(self)
        self.logs = Logs(self)

        action = self.addAction("Logs")
        action.setShortcut("Alt+C")
        action.triggered.connect(
            lambda: self.logs.show() if self.logs.isHidden() else self.logs.hide()
        )

        self.body.addWidget(self.sidebar, 3)
        self.body.addWidget(self.stack, 10)

        self.setCentralWidget(self.body)
        self.setStyleSheet(open("styles.qss").read())

        self.stack.cogsPage.addCogs()
        self.client.start()

    def log(self, text: str):
        self.logs.log(text)

    def closeEvent(self, event: QCloseEvent):
        if self.systemTray.isVisible():
            self.hide()
            return event.ignore()
        return super().closeEvent(event)

    def close(self):
        self.systemTray.hide()
        self.client.close()
        self.logs.close()
        self.showMinimized() if self.isHidden() else ...
        return super().close()
