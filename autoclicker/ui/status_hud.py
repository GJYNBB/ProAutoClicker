from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class StatusHudWindow(QWidget):
    position_changed = Signal(int, int)

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self._drag_active = False
        self._drag_offset = QPoint()

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
                background: rgba(16, 42, 67, 210);
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

    def update_content(
        self,
        *,
        lines: list[str],
        x: int,
        y: int,
        visible: bool,
        opacity_percent: int = 85,
    ) -> None:
        self.move(x, y)
        if not visible or not lines:
            self.hide()
            return

        self.setWindowOpacity(max(min(opacity_percent, 100), 15) / 100.0)
        self._label.setText("\n".join(lines))
        self.adjustSize()
        self.show()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if self._drag_active and event.buttons() & Qt.LeftButton:
            new_position = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_position)
            self.position_changed.emit(max(new_position.x(), 0), max(new_position.y(), 0))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton and self._drag_active:
            self._drag_active = False
            self.position_changed.emit(max(self.x(), 0), max(self.y(), 0))
            event.accept()
            return
        super().mouseReleaseEvent(event)
