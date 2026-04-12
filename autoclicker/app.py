from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from autoclicker import APP_NAME
from autoclicker.resources import load_app_icon
from autoclicker.theme import apply_theme
from autoclicker.ui.main_window import MainWindow


def run_app() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setWindowIcon(load_app_icon())
    window = MainWindow()
    apply_theme(app, getattr(window, "theme", "light"))
    window.show()
    return app.exec()
