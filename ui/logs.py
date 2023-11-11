from __future__ import annotations
from typing import Optional, Type, TYPE_CHECKING
from pathlib import Path
import logging
import traceback
import sys
import os

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPlainTextEdit

if TYPE_CHECKING:
    from .window import MainWindow
    from types import TracebackType


logging.basicConfig(
    filename="twitch-bot.log",
    format="%(levelname)s:%(asctime)s:%(message)s",
    level=logging.ERROR,
)


class Logs(QPlainTextEdit):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window

        action = self.addAction("Hide Logs")
        action.setShortcut("Alt+C")
        action.triggered.connect(
            lambda: self.show() if self.isHidden() else self.hide()
        )

        sys.stdout.write = sys.stderr.write = self.write
        sys.excepthook = self.excepthook

        self.setWindowTitle("Log")
        self.resize(700, 350)

        self.setContentsMargins(0, 0, 0, 0)
        self.setReadOnly(True)

    @property
    def window(self) -> MainWindow:
        return self._window

    def write(self, text: str):
        self.setPlainText(f"{self.toPlainText()}{text}")

    def log(self, text: str, level=logging.ERROR):
        self.write(text)
        logging.log(msg=text, level=level)

    def excepthook(
        self,
        exc_type: Type[BaseException],
        exc_value: Optional[BaseException],
        exc_tb: TracebackType,
    ):
        self.window.close()
        tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
        cwd = Path(os.path.dirname(os.path.dirname(__file__))).absolute()
        try:
            for frame in tb.stack[::-1]:
                file = Path(frame.filename).absolute()
                if file.is_relative_to(cwd):
                    line = frame.lineno
                    break
            logging.error(f"{file.name}({line}) - {exc_type.__name__}: {exc_value}")
        except Exception:
            logging.error(f"{exc_type.__name__}: {exc_value}")
        return sys.__excepthook__(exc_type, exc_value, exc_tb)
