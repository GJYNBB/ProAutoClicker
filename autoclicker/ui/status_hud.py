from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class StatusHudWindow(QWidget):
    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame(self)
        card.setObjectName("hudCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)

        self._label = QLabel(card)
        self._label.setObjectName("hudLabel")
        self._label.setWordWrap(True)
        card_layout.addWidget(self._label)
        layout.addWidget(card)

        self.setStyleSheet(
            """
            QFrame#hudCard {
                background: rgba(16, 42, 67, 200);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 14px;
            }
            QLabel#hudLabel {
                color: #ffffff;
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
                font-size: 10pt;
                font-weight: 600;
            }
            """
        )
        self.hide()

    def update_content(self, *, lines: list[str], x: int, y: int, visible: bool) -> None:
        self.move(x, y)
        if not visible or not lines:
            self.hide()
            return

        self._label.setText("\n".join(lines))
        self.adjustSize()
        self.show()
