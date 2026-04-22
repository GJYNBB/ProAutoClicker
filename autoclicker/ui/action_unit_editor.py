from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from autoclicker.i18n import normalize_language, tr
from autoclicker.models import (
    AppSettings,
    ActionUnit,
    get_action_labels,
    get_limit_mode_labels,
    get_mouse_button_labels,
    get_mouse_interaction_labels,
    get_target_labels,
    validate_settings,
)
from autoclicker.input_backend import InputBackend, create_input_backend
from autoclicker.ui.hotkey_edit import HotkeyLineEdit


def _set_widget_error(widget: QWidget, message: str | None) -> None:
    widget.setProperty("errorState", bool(message))
    widget.setToolTip(message or widget.toolTip())
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class ActionUnitEditor(QWidget):
    changed = Signal()
    cursor_read_failed = Signal()

    def __init__(
        self,
        *,
        language: str | None = None,
        allow_infinite: bool = True,
        backend: InputBackend | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._language = normalize_language(language)
        self._allow_infinite = allow_infinite
        self._backend = backend or create_input_backend()
        self._loading = False

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(12)

        self.base_group = QGroupBox(self)
        base_layout = QFormLayout(self.base_group)

        self.name_label = QLabel(self.base_group)
        self.name_edit = QLineEdit(self.base_group)

        self.action_mode_label = QLabel(self.base_group)
        self.action_mode_combo = QComboBox(self.base_group)

        self.mouse_button_label = QLabel(self.base_group)
        self.mouse_button_combo = QComboBox(self.base_group)

        self.mouse_interaction_label = QLabel(self.base_group)
        self.mouse_interaction_combo = QComboBox(self.base_group)

        self.action_key_label = QLabel(self.base_group)
        self.action_key_edit = HotkeyLineEdit(self.base_group)

        self.action_key_hint = QLabel(self.base_group)
        self.action_key_hint.setWordWrap(True)
        self.action_key_hint.setStyleSheet("color: #5f7285;")

        self.action_key_container = QWidget(self.base_group)
        action_key_layout = QVBoxLayout(self.action_key_container)
        action_key_layout.setContentsMargins(0, 0, 0, 0)
        action_key_layout.setSpacing(6)
        action_key_layout.addWidget(self.action_key_edit)
        action_key_layout.addWidget(self.action_key_hint)

        base_layout.addRow(self.name_label, self.name_edit)
        base_layout.addRow(self.action_mode_label, self.action_mode_combo)
        base_layout.addRow(self.mouse_button_label, self.mouse_button_combo)
        base_layout.addRow(self.mouse_interaction_label, self.mouse_interaction_combo)
        base_layout.addRow(self.action_key_label, self.action_key_container)

        self.target_group = QGroupBox(self)
        target_layout = QFormLayout(self.target_group)

        self.target_mode_label = QLabel(self.target_group)
        self.target_mode_combo = QComboBox(self.target_group)

        self.fixed_coordinates_label = QLabel(self.target_group)
        self.fixed_x_spin = QSpinBox(self.target_group)
        self.fixed_x_spin.setRange(0, 99999)
        self.fixed_y_spin = QSpinBox(self.target_group)
        self.fixed_y_spin.setRange(0, 99999)
        self.read_cursor_button = QPushButton(self.target_group)

        coordinates_row = QWidget(self.target_group)
        coordinates_layout = QHBoxLayout(coordinates_row)
        coordinates_layout.setContentsMargins(0, 0, 0, 0)
        coordinates_layout.setSpacing(8)
        coordinates_layout.addWidget(QLabel("X", coordinates_row))
        coordinates_layout.addWidget(self.fixed_x_spin)
        coordinates_layout.addWidget(QLabel("Y", coordinates_row))
        coordinates_layout.addWidget(self.fixed_y_spin)
        coordinates_layout.addWidget(self.read_cursor_button)

        self.capture_delay_label = QLabel(self.target_group)
        self.capture_delay_spin = QDoubleSpinBox(self.target_group)
        self.capture_delay_spin.setDecimals(1)
        self.capture_delay_spin.setRange(0.0, 60.0)
        self.capture_delay_spin.setSingleStep(0.5)

        target_layout.addRow(self.target_mode_label, self.target_mode_combo)
        target_layout.addRow(self.fixed_coordinates_label, coordinates_row)
        target_layout.addRow(self.capture_delay_label, self.capture_delay_spin)

        self.random_group = QGroupBox(self)
        random_layout = QGridLayout(self.random_group)

        self.frequency_label = QLabel(self.random_group)
        self.frequency_spin = QDoubleSpinBox(self.random_group)
        self.frequency_spin.setDecimals(1)
        self.frequency_spin.setRange(0.1, 1000.0)
        self.frequency_spin.setSingleStep(1.0)
        self.frequency_spin.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)

        self.random_interval_checkbox = QCheckBox(self.random_group)
        self.interval_min_label = QLabel(self.random_group)
        self.interval_min_spin = QSpinBox(self.random_group)
        self.interval_min_spin.setRange(1, 600000)
        self.interval_max_label = QLabel(self.random_group)
        self.interval_max_spin = QSpinBox(self.random_group)
        self.interval_max_spin.setRange(1, 600000)

        self.coordinate_jitter_checkbox = QCheckBox(self.random_group)
        self.jitter_x_label = QLabel(self.random_group)
        self.jitter_x_spin = QSpinBox(self.random_group)
        self.jitter_x_spin.setRange(0, 9999)
        self.jitter_y_label = QLabel(self.random_group)
        self.jitter_y_spin = QSpinBox(self.random_group)
        self.jitter_y_spin.setRange(0, 9999)

        self.hold_duration_label = QLabel(self.random_group)
        self.hold_duration_spin = QSpinBox(self.random_group)
        self.hold_duration_spin.setRange(1, 600000)
        self.random_hold_checkbox = QCheckBox(self.random_group)
        self.hold_min_label = QLabel(self.random_group)
        self.hold_min_spin = QSpinBox(self.random_group)
        self.hold_min_spin.setRange(1, 600000)
        self.hold_max_label = QLabel(self.random_group)
        self.hold_max_spin = QSpinBox(self.random_group)
        self.hold_max_spin.setRange(1, 600000)

        random_layout.addWidget(self.frequency_label, 0, 0)
        random_layout.addWidget(self.frequency_spin, 0, 1, 1, 3)
        random_layout.addWidget(self.random_interval_checkbox, 1, 0, 1, 2)
        random_layout.addWidget(self.interval_min_label, 2, 0)
        random_layout.addWidget(self.interval_min_spin, 2, 1)
        random_layout.addWidget(self.interval_max_label, 2, 2)
        random_layout.addWidget(self.interval_max_spin, 2, 3)
        random_layout.addWidget(self.coordinate_jitter_checkbox, 3, 0, 1, 2)
        random_layout.addWidget(self.jitter_x_label, 4, 0)
        random_layout.addWidget(self.jitter_x_spin, 4, 1)
        random_layout.addWidget(self.jitter_y_label, 4, 2)
        random_layout.addWidget(self.jitter_y_spin, 4, 3)
        random_layout.addWidget(self.hold_duration_label, 5, 0)
        random_layout.addWidget(self.hold_duration_spin, 5, 1, 1, 3)
        random_layout.addWidget(self.random_hold_checkbox, 6, 0, 1, 2)
        random_layout.addWidget(self.hold_min_label, 7, 0)
        random_layout.addWidget(self.hold_min_spin, 7, 1)
        random_layout.addWidget(self.hold_max_label, 7, 2)
        random_layout.addWidget(self.hold_max_spin, 7, 3)

        self.execution_group = QGroupBox(self)
        execution_layout = QFormLayout(self.execution_group)

        self.limit_mode_label = QLabel(self.execution_group)
        self.limit_mode_combo = QComboBox(self.execution_group)

        self.limit_count_label = QLabel(self.execution_group)
        self.limit_count_spin = QSpinBox(self.execution_group)
        self.limit_count_spin.setRange(1, 1000000)

        self.limit_duration_label = QLabel(self.execution_group)
        self.limit_duration_spin = QDoubleSpinBox(self.execution_group)
        self.limit_duration_spin.setDecimals(1)
        self.limit_duration_spin.setRange(0.1, 86400.0)
        self.limit_duration_spin.setSingleStep(1.0)

        self.post_delay_label = QLabel(self.execution_group)
        self.post_delay_spin = QSpinBox(self.execution_group)
        self.post_delay_spin.setRange(0, 600000)

        execution_layout.addRow(self.limit_mode_label, self.limit_mode_combo)
        execution_layout.addRow(self.limit_count_label, self.limit_count_spin)
        execution_layout.addRow(self.limit_duration_label, self.limit_duration_spin)
        execution_layout.addRow(self.post_delay_label, self.post_delay_spin)

        root_layout.addWidget(self.base_group)
        root_layout.addWidget(self.target_group)
        root_layout.addWidget(self.random_group)
        root_layout.addWidget(self.execution_group)

        self._field_widgets: dict[str, QWidget] = {
            "name": self.name_edit,
            "action_mode": self.action_mode_combo,
            "mouse_button": self.mouse_button_combo,
            "mouse_interaction": self.mouse_interaction_combo,
            "action_key": self.action_key_edit,
            "target_mode": self.target_mode_combo,
            "fixed_x": self.fixed_x_spin,
            "fixed_y": self.fixed_y_spin,
            "capture_delay_seconds": self.capture_delay_spin,
            "frequency_hz": self.frequency_spin,
            "interval_min_ms": self.interval_min_spin,
            "interval_max_ms": self.interval_max_spin,
            "jitter_x_px": self.jitter_x_spin,
            "jitter_y_px": self.jitter_y_spin,
            "hold_duration_ms": self.hold_duration_spin,
            "hold_min_ms": self.hold_min_spin,
            "hold_max_ms": self.hold_max_spin,
            "limit_mode": self.limit_mode_combo,
            "limit_count": self.limit_count_spin,
            "limit_duration_seconds": self.limit_duration_spin,
            "post_delay_ms": self.post_delay_spin,
        }

        self._wire_events()
        self.set_allow_infinite(allow_infinite)
        self.set_language(self._language)
        self.set_action(ActionUnit())

    def _wire_events(self) -> None:
        widgets = [
            self.name_edit,
            self.action_mode_combo,
            self.mouse_button_combo,
            self.mouse_interaction_combo,
            self.target_mode_combo,
            self.frequency_spin,
            self.capture_delay_spin,
            self.fixed_x_spin,
            self.fixed_y_spin,
            self.interval_min_spin,
            self.interval_max_spin,
            self.jitter_x_spin,
            self.jitter_y_spin,
            self.hold_duration_spin,
            self.hold_min_spin,
            self.hold_max_spin,
            self.limit_mode_combo,
            self.limit_count_spin,
            self.limit_duration_spin,
            self.post_delay_spin,
        ]
        for widget in widgets:
            if hasattr(widget, "currentIndexChanged"):
                widget.currentIndexChanged.connect(self._on_value_changed)  # type: ignore[attr-defined]
            elif hasattr(widget, "valueChanged"):
                widget.valueChanged.connect(self._on_value_changed)  # type: ignore[attr-defined]
            elif hasattr(widget, "textChanged"):
                widget.textChanged.connect(self._on_value_changed)  # type: ignore[attr-defined]

        self.action_key_edit.hotkey_changed.connect(self._on_value_changed)
        self.random_interval_checkbox.stateChanged.connect(self._on_value_changed)
        self.coordinate_jitter_checkbox.stateChanged.connect(self._on_value_changed)
        self.random_hold_checkbox.stateChanged.connect(self._on_value_changed)
        self.read_cursor_button.clicked.connect(self._fill_current_cursor)

    def _set_combo_items(self, combo: QComboBox, items: dict[str, str], current_value: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        for value, label in items.items():
            combo.addItem(label, value)
        index = combo.findData(current_value)
        if index < 0 and combo.count() > 0:
            index = 0
        if index >= 0:
            combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def _current_combo_data(self, combo: QComboBox, default: str) -> str:
        data = combo.currentData()
        return data if isinstance(data, str) and data else default

    def set_allow_infinite(self, allow_infinite: bool) -> None:
        self._allow_infinite = allow_infinite
        labels = get_limit_mode_labels(self._language)
        items = dict(labels)
        if not allow_infinite:
            items.pop("infinite", None)
        current_value = self._current_combo_data(self.limit_mode_combo, "count")
        if current_value == "infinite" and not allow_infinite:
            current_value = "count"
        self._set_combo_items(self.limit_mode_combo, items, current_value)

    def set_language(self, language: str | None) -> None:
        self._language = normalize_language(language)
        self.base_group.setTitle(tr(self._language, "group.quick_action"))
        self.target_group.setTitle(tr(self._language, "group.task"))
        self.random_group.setTitle(tr(self._language, "field.random_interval"))
        self.execution_group.setTitle(tr(self._language, "field.limit_mode"))

        self.name_label.setText(tr(self._language, "field.action_name"))
        self.action_mode_label.setText(tr(self._language, "field.action_mode"))
        self.mouse_button_label.setText(tr(self._language, "field.mouse_button"))
        self.mouse_interaction_label.setText(tr(self._language, "field.mouse_interaction"))
        self.action_key_label.setText(tr(self._language, "field.action_key"))
        self.action_key_hint.setText(tr(self._language, "hint.action_key"))
        self.action_key_edit.setPlaceholderText(tr(self._language, "hint.hotkey_input"))

        self.target_mode_label.setText(tr(self._language, "field.target_mode"))
        self.fixed_coordinates_label.setText(tr(self._language, "field.fixed_coordinates"))
        self.capture_delay_label.setText(tr(self._language, "field.capture_delay"))
        self.capture_delay_spin.setSuffix(tr(self._language, "suffix.seconds"))
        self.read_cursor_button.setText(tr(self._language, "button.read_cursor"))

        self.frequency_label.setText(tr(self._language, "field.frequency"))
        self.frequency_spin.setSuffix(tr(self._language, "suffix.per_second"))
        self.random_interval_checkbox.setText(tr(self._language, "field.random_interval"))
        self.interval_min_label.setText(tr(self._language, "field.interval_min"))
        self.interval_max_label.setText(tr(self._language, "field.interval_max"))
        self.interval_min_spin.setSuffix(tr(self._language, "suffix.milliseconds"))
        self.interval_max_spin.setSuffix(tr(self._language, "suffix.milliseconds"))
        self.coordinate_jitter_checkbox.setText(tr(self._language, "field.coordinate_jitter"))
        self.jitter_x_label.setText(tr(self._language, "field.jitter_x"))
        self.jitter_y_label.setText(tr(self._language, "field.jitter_y"))
        self.jitter_x_spin.setSuffix(tr(self._language, "suffix.milliseconds").replace(" ms", " px"))
        self.jitter_y_spin.setSuffix(tr(self._language, "suffix.milliseconds").replace(" ms", " px"))
        self.hold_duration_label.setText(tr(self._language, "field.hold_duration"))
        self.hold_duration_spin.setSuffix(tr(self._language, "suffix.milliseconds"))
        self.random_hold_checkbox.setText(tr(self._language, "field.random_hold"))
        self.hold_min_label.setText(tr(self._language, "field.hold_min"))
        self.hold_max_label.setText(tr(self._language, "field.hold_max"))
        self.hold_min_spin.setSuffix(tr(self._language, "suffix.milliseconds"))
        self.hold_max_spin.setSuffix(tr(self._language, "suffix.milliseconds"))

        self.limit_mode_label.setText(tr(self._language, "field.limit_mode"))
        self.limit_count_label.setText(tr(self._language, "field.limit_count"))
        self.limit_duration_label.setText(tr(self._language, "field.limit_duration"))
        self.limit_duration_spin.setSuffix(tr(self._language, "suffix.seconds"))
        self.post_delay_label.setText(tr(self._language, "field.post_delay"))
        self.post_delay_spin.setSuffix(tr(self._language, "suffix.milliseconds"))

        self.name_edit.setToolTip(tr(self._language, "hint.action_name"))
        self.action_mode_combo.setToolTip(tr(self._language, "field.action_mode"))
        self.mouse_button_combo.setToolTip(tr(self._language, "field.mouse_button"))
        self.mouse_interaction_combo.setToolTip(tr(self._language, "field.mouse_interaction"))
        self.action_key_edit.setToolTip(tr(self._language, "hint.action_key"))
        self.target_mode_combo.setToolTip(tr(self._language, "field.target_mode"))
        self.capture_delay_spin.setToolTip(tr(self._language, "summary.target.capture", seconds=3.0))
        self.frequency_spin.setToolTip(tr(self._language, "field.frequency"))
        self.random_interval_checkbox.setToolTip(tr(self._language, "hint.random_interval"))
        self.coordinate_jitter_checkbox.setToolTip(tr(self._language, "hint.coordinate_jitter"))
        self.random_hold_checkbox.setToolTip(tr(self._language, "hint.random_hold"))
        self.limit_mode_combo.setToolTip(tr(self._language, "hint.limit_mode"))

        current_action_mode = self._current_combo_data(self.action_mode_combo, "mouse")
        current_mouse_button = self._current_combo_data(self.mouse_button_combo, "left")
        current_mouse_interaction = self._current_combo_data(self.mouse_interaction_combo, "single")
        current_target_mode = self._current_combo_data(self.target_mode_combo, "capture")

        self._set_combo_items(self.action_mode_combo, get_action_labels(self._language), current_action_mode)
        self._set_combo_items(self.mouse_button_combo, get_mouse_button_labels(self._language), current_mouse_button)
        self._set_combo_items(
            self.mouse_interaction_combo,
            get_mouse_interaction_labels(self._language),
            current_mouse_interaction,
        )
        self._set_combo_items(self.target_mode_combo, get_target_labels(self._language), current_target_mode)
        self.set_allow_infinite(self._allow_infinite)
        self._refresh_visibility()

    def set_action(self, action: ActionUnit) -> None:
        self._loading = True
        try:
            normalized = action.normalized()
            self.name_edit.setText(normalized.name)
            self._set_combo_items(self.action_mode_combo, get_action_labels(self._language), normalized.action_mode)
            self._set_combo_items(self.mouse_button_combo, get_mouse_button_labels(self._language), normalized.mouse_button)
            self._set_combo_items(
                self.mouse_interaction_combo,
                get_mouse_interaction_labels(self._language),
                normalized.mouse_interaction,
            )
            self.action_key_edit.set_hotkey(normalized.action_key)
            self._set_combo_items(self.target_mode_combo, get_target_labels(self._language), normalized.target_mode)
            self.fixed_x_spin.setValue(normalized.fixed_x)
            self.fixed_y_spin.setValue(normalized.fixed_y)
            self.capture_delay_spin.setValue(normalized.capture_delay_seconds)
            self.frequency_spin.setValue(normalized.frequency_hz)
            self.random_interval_checkbox.setChecked(normalized.random_interval_enabled)
            self.interval_min_spin.setValue(normalized.interval_min_ms)
            self.interval_max_spin.setValue(normalized.interval_max_ms)
            self.coordinate_jitter_checkbox.setChecked(normalized.coordinate_jitter_enabled)
            self.jitter_x_spin.setValue(normalized.jitter_x_px)
            self.jitter_y_spin.setValue(normalized.jitter_y_px)
            self.hold_duration_spin.setValue(normalized.hold_duration_ms)
            self.random_hold_checkbox.setChecked(normalized.random_hold_enabled)
            self.hold_min_spin.setValue(normalized.hold_min_ms)
            self.hold_max_spin.setValue(normalized.hold_max_ms)
            if normalized.limit_mode == "infinite" and not self._allow_infinite:
                normalized.limit_mode = "count"
            self.set_allow_infinite(self._allow_infinite)
            index = self.limit_mode_combo.findData(normalized.limit_mode)
            if index >= 0:
                self.limit_mode_combo.setCurrentIndex(index)
            self.limit_count_spin.setValue(normalized.limit_count)
            self.limit_duration_spin.setValue(normalized.limit_duration_seconds)
            self.post_delay_spin.setValue(normalized.post_delay_ms)
        finally:
            self._loading = False
        self._refresh_visibility()

    def action_unit(self) -> ActionUnit:
        return ActionUnit(
            name=self.name_edit.text().strip(),
            action_mode=self._current_combo_data(self.action_mode_combo, "mouse"),
            mouse_button=self._current_combo_data(self.mouse_button_combo, "left"),
            mouse_interaction=self._current_combo_data(self.mouse_interaction_combo, "single"),
            action_key=self.action_key_edit.hotkey(),
            target_mode=self._current_combo_data(self.target_mode_combo, "capture"),
            fixed_x=self.fixed_x_spin.value(),
            fixed_y=self.fixed_y_spin.value(),
            capture_delay_seconds=self.capture_delay_spin.value(),
            frequency_hz=self.frequency_spin.value(),
            random_interval_enabled=self.random_interval_checkbox.isChecked(),
            interval_min_ms=self.interval_min_spin.value(),
            interval_max_ms=self.interval_max_spin.value(),
            coordinate_jitter_enabled=self.coordinate_jitter_checkbox.isChecked(),
            jitter_x_px=self.jitter_x_spin.value(),
            jitter_y_px=self.jitter_y_spin.value(),
            hold_duration_ms=self.hold_duration_spin.value(),
            random_hold_enabled=self.random_hold_checkbox.isChecked(),
            hold_min_ms=self.hold_min_spin.value(),
            hold_max_ms=self.hold_max_spin.value(),
            limit_mode=self._current_combo_data(
                self.limit_mode_combo,
                "infinite" if self._allow_infinite else "count",
            ),
            limit_count=self.limit_count_spin.value(),
            limit_duration_seconds=self.limit_duration_spin.value(),
            post_delay_ms=self.post_delay_spin.value(),
        )

    def apply_validation(self, errors: dict[str, list[str]] | None) -> None:
        errors = errors or {}
        for field_name, widget in self._field_widgets.items():
            message = None
            field_messages = errors.get(field_name)
            if field_messages:
                message = field_messages[0]
            _set_widget_error(widget, message)

    def _fill_current_cursor(self) -> None:
        try:
            position = self._backend.get_cursor_position()
        except OSError:
            position = None
        if position is None:
            self.cursor_read_failed.emit()
            return
        self.fixed_x_spin.setValue(position[0])
        self.fixed_y_spin.setValue(position[1])

    def _refresh_visibility(self) -> None:
        mouse_mode = self._current_combo_data(self.action_mode_combo, "mouse") == "mouse"
        keyboard_mode = not mouse_mode
        fixed_mode = self._current_combo_data(self.target_mode_combo, "capture") == "fixed"
        hold_mode = keyboard_mode or self._current_combo_data(self.mouse_interaction_combo, "single") == "hold"
        limit_mode = self._current_combo_data(self.limit_mode_combo, "count")

        self.mouse_button_label.setVisible(mouse_mode)
        self.mouse_button_combo.setVisible(mouse_mode)
        self.mouse_interaction_label.setVisible(mouse_mode)
        self.mouse_interaction_combo.setVisible(mouse_mode)
        self.action_key_label.setVisible(keyboard_mode)
        self.action_key_container.setVisible(keyboard_mode)

        self.target_group.setVisible(mouse_mode)
        self.fixed_coordinates_label.setVisible(mouse_mode and fixed_mode)
        self.fixed_x_spin.parentWidget().setVisible(mouse_mode and fixed_mode)
        self.capture_delay_label.setVisible(mouse_mode and not fixed_mode)
        self.capture_delay_spin.setVisible(mouse_mode and not fixed_mode)

        self.coordinate_jitter_checkbox.setVisible(mouse_mode)
        self.jitter_x_label.setVisible(mouse_mode and self.coordinate_jitter_checkbox.isChecked())
        self.jitter_x_spin.setVisible(mouse_mode and self.coordinate_jitter_checkbox.isChecked())
        self.jitter_y_label.setVisible(mouse_mode and self.coordinate_jitter_checkbox.isChecked())
        self.jitter_y_spin.setVisible(mouse_mode and self.coordinate_jitter_checkbox.isChecked())

        self.hold_duration_label.setVisible(hold_mode)
        self.hold_duration_spin.setVisible(hold_mode)
        self.random_hold_checkbox.setVisible(hold_mode)
        show_random_hold = hold_mode and self.random_hold_checkbox.isChecked()
        self.hold_min_label.setVisible(show_random_hold)
        self.hold_min_spin.setVisible(show_random_hold)
        self.hold_max_label.setVisible(show_random_hold)
        self.hold_max_spin.setVisible(show_random_hold)

        show_random_interval = self.random_interval_checkbox.isChecked()
        self.interval_min_label.setVisible(show_random_interval)
        self.interval_min_spin.setVisible(show_random_interval)
        self.interval_max_label.setVisible(show_random_interval)
        self.interval_max_spin.setVisible(show_random_interval)

        self.limit_count_label.setVisible(limit_mode == "count")
        self.limit_count_spin.setVisible(limit_mode == "count")
        self.limit_duration_label.setVisible(limit_mode == "duration")
        self.limit_duration_spin.setVisible(limit_mode == "duration")

    def _on_value_changed(self, *_args) -> None:
        if self._loading:
            return
        self._refresh_visibility()
        self.changed.emit()


class ActionUnitDialog(QDialog):
    def __init__(
        self,
        *,
        language: str | None,
        title: str,
        action: ActionUnit,
        allow_infinite: bool,
        backend: InputBackend | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._language = normalize_language(language)
        self.setWindowTitle(title)
        self.resize(700, 760)

        layout = QVBoxLayout(self)
        self.editor = ActionUnitEditor(language=self._language, allow_infinite=allow_infinite, backend=backend, parent=self)
        self.editor.base_group.setTitle(tr(self._language, "group.quick_action"))
        self.editor.target_group.setTitle(tr(self._language, "field.target_mode"))
        self.editor.random_group.setTitle(tr(self._language, "field.random_interval"))
        self.editor.execution_group.setTitle(tr(self._language, "field.limit_mode"))
        self.editor.set_action(action)
        self.editor.cursor_read_failed.connect(self._on_cursor_failed)
        self.editor.changed.connect(self._refresh_validation)

        self.validation_label = QLabel(self)
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("color: #b42318;")

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        ok_button = self.buttons.button(QDialogButtonBox.Ok)
        if ok_button is not None:
            ok_button.setText(tr(self._language, "button.ok"))
        cancel_button = self.buttons.button(QDialogButtonBox.Cancel)
        if cancel_button is not None:
            cancel_button.setText(tr(self._language, "button.cancel"))
        self.buttons.accepted.connect(self._accept_if_valid)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.editor)
        layout.addWidget(self.validation_label)
        layout.addWidget(self.buttons)
        self._refresh_validation()

    def action_unit(self) -> ActionUnit:
        return self.editor.action_unit()

    def _refresh_validation(self) -> None:
        candidate = self.editor.action_unit()
        dummy_settings = validate_settings(AppSettings(actions=[candidate]), self._language)
        action_errors = dummy_settings.action_errors(0)
        self.editor.apply_validation(action_errors)
        messages = [message for key, values in action_errors.items() for message in values]
        deduped: list[str] = []
        seen: set[str] = set()
        for message in messages:
            if message not in seen:
                seen.add(message)
                deduped.append(message)
        self.validation_label.setText("\n".join(deduped))

    def _accept_if_valid(self) -> None:
        if self.validation_label.text():
            return
        self.accept()

    def _on_cursor_failed(self) -> None:
        QMessageBox.warning(self, self.windowTitle(), tr(self._language, "dialog.cursor_failed"))
