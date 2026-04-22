from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SettingsCard(QFrame):
    """Consistent card container with an optional title."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsCard")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)
        self._title_label = QLabel(title, self)
        self._title_label.setObjectName("cardTitle")
        self._layout.addWidget(self._title_label)
        self._content = QWidget(self)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        self._title_label.setVisible(bool(title))
        self._layout.addWidget(self._content)

    def set_title(self, text: str) -> None:
        self._title_label.setText(text)
        self._title_label.setVisible(bool(text))

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout


class CollapsibleSection(QFrame):
    """Expandable/collapsible section with animation."""

    toggled = Signal(bool)

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("collapsibleSection")
        self._expanded = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._toggle_button = QPushButton(self)
        self._toggle_button.setObjectName("collapsibleToggle")
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(False)
        self._toggle_button.clicked.connect(self._on_toggled)
        self._title = title
        self._update_button_text()
        outer.addWidget(self._toggle_button)

        self._content = QWidget(self)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 8, 0, 0)
        self._content_layout.setSpacing(8)
        self._content.setMaximumHeight(0)
        outer.addWidget(self._content)

        self._animation = QPropertyAnimation(self._content, b"maximumHeight", self)
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

    def set_title(self, title: str) -> None:
        self._title = title
        self._update_button_text()

    def _update_button_text(self) -> None:
        arrow = "▼" if self._expanded else "▶"
        self._toggle_button.setText(f"{arrow}  {self._title}")

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def is_expanded(self) -> bool:
        return self._expanded

    def set_expanded(self, expanded: bool) -> None:
        if self._expanded == expanded:
            return
        self._expanded = expanded
        self._toggle_button.setChecked(expanded)
        self._update_button_text()
        self._content.setMaximumHeight(16777215 if expanded else 0)

    def _on_toggled(self, checked: bool) -> None:
        self._expanded = checked
        self._update_button_text()
        content_height = self._content_layout.sizeHint().height() + 16
        self._animation.stop()
        if checked:
            self._animation.setStartValue(0)
            self._animation.setEndValue(content_height)
        else:
            self._animation.setStartValue(self._content.height())
            self._animation.setEndValue(0)
        self._animation.start()
        self.toggled.emit(checked)


class StatusPanel(QFrame):
    """Always-visible right-side panel showing runtime state."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("statusPanel")
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._state_indicator = QLabel(self)
        self._state_indicator.setObjectName("stateIndicator")
        self._state_indicator.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._state_indicator)

        sep = QFrame(self)
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("statusSeparator")
        layout.addWidget(sep)

        self._fields: dict[str, tuple[QLabel, QLabel]] = {}
        field_keys = ["hotkey", "count", "step", "rate", "last"]
        for key in field_keys:
            row = QWidget(self)
            row.setObjectName("statusFieldRow")
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(2)

            label = QLabel(row)
            label.setObjectName("statusFieldLabel")
            value = QLabel(row)
            value.setObjectName("statusFieldValue")
            value.setWordWrap(True)
            row_layout.addWidget(label)
            row_layout.addWidget(value)
            layout.addWidget(row)
            self._fields[key] = (label, value)

        layout.addStretch(1)

    def set_field_label(self, key: str, text: str) -> None:
        if key in self._fields:
            self._fields[key][0].setText(text)

    def set_field_value(self, key: str, text: str) -> None:
        if key in self._fields:
            self._fields[key][1].setText(text)

    def set_state(self, state: str, display_text: str) -> None:
        self._state_indicator.setText(display_text)
        for s in ("idle", "running", "paused", "countdown"):
            self._state_indicator.setProperty(f"state_{s}", s == state)
        self._state_indicator.style().unpolish(self._state_indicator)
        self._state_indicator.style().polish(self._state_indicator)
        self._state_indicator.update()


class ActionBar(QFrame):
    """Fixed bottom bar with start/pause/exit controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("actionBar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(4)

        buttons_row = QWidget(self)
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)

        self.start_button = QPushButton(self)
        self.start_button.setObjectName("primaryButton")
        self.pause_button = QPushButton(self)
        self.exit_button = QPushButton(self)
        self.exit_button.setObjectName("dangerButton")

        buttons_layout.addWidget(self.start_button, 2)
        buttons_layout.addWidget(self.pause_button, 1)
        buttons_layout.addWidget(self.exit_button, 1)

        self.validation_label = QLabel(self)
        self.validation_label.setWordWrap(True)
        self.validation_label.setObjectName("validationLabel")
        self.validation_label.hide()

        layout.addWidget(buttons_row)
        layout.addWidget(self.validation_label)

    def set_validation_message(self, message: str, *, severity: str = "error") -> None:
        self.validation_label.setText(message)
        self.validation_label.setProperty("severity", severity)
        self.validation_label.setVisible(bool(message))
        self.validation_label.style().unpolish(self.validation_label)
        self.validation_label.style().polish(self.validation_label)
        self.validation_label.update()
