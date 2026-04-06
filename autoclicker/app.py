from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from autoclicker import APP_NAME
from autoclicker.resources import load_app_icon
from autoclicker.ui.main_window import MainWindow

APP_STYLE = """
QMainWindow {
    background: #edf2f7;
}
QWidget {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
    font-size: 10.5pt;
    color: #142739;
}
QLabel#heroTitle {
    color: #0f2740;
    font-size: 28px;
    font-weight: 700;
}
QLabel#heroSubtitle {
    color: #50667c;
    font-size: 10.5pt;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #d5dee7;
    border-radius: 16px;
    margin-top: 14px;
    font-weight: 600;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #0f2740;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextBrowser {
    background: #fbfcfe;
    border: 1px solid #c8d4e0;
    border-radius: 10px;
    min-height: 22px;
    padding: 6px 10px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextBrowser:focus {
    border: 1px solid #f97316;
}
QPushButton {
    background: #ffffff;
    border: 1px solid #c8d4e0;
    border-radius: 10px;
    min-height: 24px;
    padding: 7px 14px;
    font-weight: 600;
}
QPushButton:hover {
    border-color: #f97316;
}
QPushButton#primaryButton {
    background: #f97316;
    color: #ffffff;
    border-color: #f97316;
}
QPushButton#primaryButton:hover {
    background: #ea580c;
}
QPushButton#dangerButton {
    background: #fff1f2;
    color: #b42318;
    border-color: #fda4af;
}
QPushButton#dangerButton:hover {
    background: #ffe4e6;
}
QPushButton:disabled {
    background: #eef2f6;
    color: #7b8a9a;
    border-color: #d5dee7;
}
QStatusBar {
    background: #102a43;
    color: #ffffff;
}
"""


def run_app() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setStyleSheet(APP_STYLE)
    app.setWindowIcon(load_app_icon())
    window = MainWindow()
    window.show()
    return app.exec()
