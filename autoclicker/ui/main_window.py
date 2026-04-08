from __future__ import annotations

from datetime import datetime

from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStatusBar,
    QStyle,
    QSystemTrayIcon,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from autoclicker import APP_VERSION
from autoclicker.controller import AutomationController
from autoclicker.i18n import app_display_name, build_help_html, default_preset_name, language_items, normalize_language, tr
from autoclicker.models import (
    AppSettings,
    OverlaySettings,
    PersistedState,
    Preset,
    format_action_label,
    get_action_labels,
    get_hud_item_labels,
    get_hotkey_scope_labels,
    get_mouse_button_labels,
    get_target_labels,
    validate_settings,
)
from autoclicker.resources import load_app_icon
from autoclicker.store import SettingsStore
from autoclicker.ui.hotkey_edit import HotkeyLineEdit
from autoclicker.ui.status_hud import StatusHudWindow
from autoclicker.win32_backend import GlobalHotkeyManager, get_cursor_position


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._store = SettingsStore()
        self._controller = AutomationController()
        self._global_hotkeys = GlobalHotkeyManager()
        self._persisted_state = self._store.load()
        self._language = normalize_language(self._persisted_state.language)
        self._controller.set_language(self._language)
        self._presets = {preset.name: preset for preset in self._persisted_state.presets}
        self._overlay_settings = self._persisted_state.overlay
        self._hud_window = StatusHudWindow()
        self._current_target: tuple[int, int] | None = None
        self._action_count = 0
        self._actual_frequency = 0.0
        self._controller_state = self._controller.state
        self._local_shortcuts: list[QShortcut] = []
        self._loading = False
        self._tray_notice_shown = False
        self._force_quit = False

        self.setWindowIcon(load_app_icon())
        self.resize(720, 820)
        self.setMinimumSize(640, 560)

        self._build_ui()
        self._build_menus()
        self._wire_events()
        self._apply_translations()
        self._load_initial_state()
        self._refresh_form_state()

    def _build_ui(self) -> None:
        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("heroTitle")

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("heroSubtitle")
        self.subtitle_label.setWordWrap(True)

        root_layout.addWidget(self.title_label)
        root_layout.addWidget(self.subtitle_label)
        root_layout.addWidget(self._create_scroll_panel(self._build_main_panel()), 1)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar(self))
        self._build_tray()

    def _create_scroll_panel(self, content: QWidget) -> QScrollArea:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(content)
        return scroll_area

    def _build_main_panel(self) -> QWidget:
        container = QWidget()
        self._main_panel_layout = QVBoxLayout(container)
        self._main_panel_layout.setSpacing(16)

        self.action_group = self._build_action_group()
        self.mouse_group = self._build_mouse_group()
        self.timing_group = self._build_timing_group()
        self.hotkey_group = self._build_hotkey_group()
        self.options_group = self._build_options_group()
        self.controls_group = self._build_controls_group()
        self.status_group = self._build_status_group()
        self.help_group = self._build_help_group()
        self.preset_group = self._build_preset_group()

        for group in (
            self.action_group,
            self.mouse_group,
            self.timing_group,
            self.hotkey_group,
            self.options_group,
            self.controls_group,
            self.status_group,
            self.help_group,
            self.preset_group,
        ):
            self._main_panel_layout.addWidget(group)

        self._main_panel_layout.addStretch(1)
        return container

    def _build_action_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QFormLayout(group)

        self.action_mode_label = QLabel()
        self.action_mode_combo = QComboBox()

        self.action_key_label = QLabel()
        self.action_key_edit = HotkeyLineEdit()
        self.action_key_hint = QLabel()
        self.action_key_hint.setWordWrap(True)
        self.action_key_hint.setStyleSheet("color: #5f7285;")

        self.action_key_container = QWidget()
        action_key_layout = QVBoxLayout(self.action_key_container)
        action_key_layout.setContentsMargins(0, 0, 0, 0)
        action_key_layout.setSpacing(6)
        action_key_layout.addWidget(self.action_key_edit)
        action_key_layout.addWidget(self.action_key_hint)

        layout.addRow(self.action_mode_label, self.action_mode_combo)
        layout.addRow(self.action_key_label, self.action_key_container)
        return group

    def _build_mouse_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QFormLayout(group)

        self.mouse_button_label = QLabel()
        self.mouse_button_combo = QComboBox()

        self.target_mode_label = QLabel()
        self.target_mode_combo = QComboBox()

        self.fixed_x_spin = QSpinBox()
        self.fixed_x_spin.setRange(0, 99999)
        self.fixed_y_spin = QSpinBox()
        self.fixed_y_spin.setRange(0, 99999)
        self.use_current_cursor_button = QPushButton()

        coordinate_row = QWidget()
        coordinate_layout = QHBoxLayout(coordinate_row)
        coordinate_layout.setContentsMargins(0, 0, 0, 0)
        coordinate_layout.setSpacing(8)
        coordinate_layout.addWidget(QLabel("X"))
        coordinate_layout.addWidget(self.fixed_x_spin)
        coordinate_layout.addWidget(QLabel("Y"))
        coordinate_layout.addWidget(self.fixed_y_spin)
        coordinate_layout.addWidget(self.use_current_cursor_button)

        self.capture_delay_spin = QDoubleSpinBox()
        self.capture_delay_spin.setDecimals(1)
        self.capture_delay_spin.setRange(0.0, 60.0)
        self.capture_delay_spin.setSingleStep(0.5)

        self.fixed_coordinates_label = QLabel()
        self.capture_delay_label = QLabel()
        self.fixed_coordinates_row = coordinate_row

        layout.addRow(self.mouse_button_label, self.mouse_button_combo)
        layout.addRow(self.target_mode_label, self.target_mode_combo)
        layout.addRow(self.fixed_coordinates_label, self.fixed_coordinates_row)
        layout.addRow(self.capture_delay_label, self.capture_delay_spin)
        return group

    def _build_timing_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QFormLayout(group)

        self.frequency_label = QLabel()
        self.frequency_spin = QDoubleSpinBox()
        self.frequency_spin.setDecimals(1)
        self.frequency_spin.setRange(0.1, 1000.0)
        self.frequency_spin.setSingleStep(1.0)
        self.frequency_spin.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)

        layout.addRow(self.frequency_label, self.frequency_spin)
        return group

    def _build_hotkey_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QFormLayout(group)

        self.hotkey_scope_label = QLabel()
        self.hotkey_scope_combo = QComboBox()

        self.toggle_hotkey_label = QLabel()
        self.toggle_hotkey_edit = HotkeyLineEdit()

        self.exit_hotkey_label = QLabel()
        self.exit_hotkey_edit = HotkeyLineEdit()

        self.hotkey_hint = QLabel()
        self.hotkey_hint.setWordWrap(True)
        self.hotkey_hint.setStyleSheet("color: #5f7285;")

        layout.addRow(self.hotkey_scope_label, self.hotkey_scope_combo)
        layout.addRow(self.toggle_hotkey_label, self.toggle_hotkey_edit)
        layout.addRow(self.exit_hotkey_label, self.exit_hotkey_edit)
        layout.addRow(QLabel(""), self.hotkey_hint)
        return group

    def _build_options_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QVBoxLayout(group)
        self.minimize_to_tray_checkbox = QCheckBox()
        self.enable_hud_checkbox = QCheckBox()
        self.hud_items_label = QLabel()
        self.hud_position_label = QLabel()
        self.hud_hint_label = QLabel()
        self.hud_hint_label.setWordWrap(True)
        self.hud_hint_label.setStyleSheet("color: #5f7285;")
        self.hud_state_checkbox = QCheckBox()
        self.hud_rate_checkbox = QCheckBox()
        self.hud_count_checkbox = QCheckBox()
        self.hud_item_checkboxes = {
            "state": self.hud_state_checkbox,
            "rate": self.hud_rate_checkbox,
            "count": self.hud_count_checkbox,
        }
        hud_items_row = QWidget()
        hud_items_layout = QHBoxLayout(hud_items_row)
        hud_items_layout.setContentsMargins(0, 0, 0, 0)
        hud_items_layout.setSpacing(8)
        for checkbox in self.hud_item_checkboxes.values():
            hud_items_layout.addWidget(checkbox)
        hud_items_layout.addStretch(1)

        self.hud_x_spin = QSpinBox()
        self.hud_x_spin.setRange(0, 99999)
        self.hud_y_spin = QSpinBox()
        self.hud_y_spin.setRange(0, 99999)
        self.hud_position_row = QWidget()
        hud_position_layout = QHBoxLayout(self.hud_position_row)
        hud_position_layout.setContentsMargins(0, 0, 0, 0)
        hud_position_layout.setSpacing(8)
        hud_position_layout.addWidget(QLabel("X"))
        hud_position_layout.addWidget(self.hud_x_spin)
        hud_position_layout.addWidget(QLabel("Y"))
        hud_position_layout.addWidget(self.hud_y_spin)
        hud_position_layout.addStretch(1)

        hud_form = QFormLayout()
        hud_form.setContentsMargins(0, 0, 0, 0)
        hud_form.addRow(self.hud_items_label, hud_items_row)
        hud_form.addRow(self.hud_position_label, self.hud_position_row)

        layout.addWidget(self.minimize_to_tray_checkbox)
        layout.addWidget(self.enable_hud_checkbox)
        layout.addLayout(hud_form)
        layout.addWidget(self.hud_hint_label)
        return group

    def _build_controls_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QVBoxLayout(group)

        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.start_button = QPushButton()
        self.start_button.setObjectName("primaryButton")
        self.pause_button = QPushButton()
        self.exit_button = QPushButton()
        self.exit_button.setObjectName("dangerButton")

        button_layout.addWidget(self.start_button, 2)
        button_layout.addWidget(self.pause_button, 1)
        button_layout.addWidget(self.exit_button, 1)

        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("color: #b42318;")

        layout.addWidget(button_row)
        layout.addWidget(self.validation_label)
        return group

    def _build_status_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QFormLayout(group)

        self.state_label = QLabel()
        self.actual_frequency_label = QLabel()
        self.action_count_label = QLabel()
        self.target_position_label = QLabel()
        self.summary_label = QLabel()

        self.state_value = QLabel("0")
        self.actual_frequency_value = QLabel("0")
        self.action_count_value = QLabel("0")
        self.target_value = QLabel("")
        self.summary_value = QLabel("")
        self.summary_value.setWordWrap(True)
        self.summary_value.setStyleSheet("color: #415466;")

        layout.addRow(self.state_label, self.state_value)
        layout.addRow(self.actual_frequency_label, self.actual_frequency_value)
        layout.addRow(self.action_count_label, self.action_count_value)
        layout.addRow(self.target_position_label, self.target_value)
        layout.addRow(self.summary_label, self.summary_value)
        return group

    def _build_help_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QVBoxLayout(group)

        self.help_browser = QTextBrowser()
        self.help_browser.setOpenExternalLinks(False)
        layout.addWidget(self.help_browser)
        return group

    def _build_preset_group(self) -> QGroupBox:
        group = QGroupBox()
        layout = QGridLayout(group)

        self.current_preset_label = QLabel()
        self.preset_combo = QComboBox()
        self.load_preset_button = QPushButton()
        self.save_preset_button = QPushButton()
        self.save_as_preset_button = QPushButton()
        self.delete_preset_button = QPushButton()
        self.import_presets_button = QPushButton()
        self.export_presets_button = QPushButton()

        layout.addWidget(self.current_preset_label, 0, 0)
        layout.addWidget(self.preset_combo, 0, 1, 1, 2)
        layout.addWidget(self.load_preset_button, 1, 0)
        layout.addWidget(self.save_preset_button, 1, 1)
        layout.addWidget(self.save_as_preset_button, 1, 2)
        layout.addWidget(self.delete_preset_button, 2, 0)
        layout.addWidget(self.import_presets_button, 2, 1)
        layout.addWidget(self.export_presets_button, 2, 2)
        return group

    def _build_menus(self) -> None:
        menubar = self.menuBar()

        self.file_menu = menubar.addMenu("")
        self.import_action = QAction(self)
        self.import_action.triggered.connect(self._import_presets)
        self.file_menu.addAction(self.import_action)

        self.export_action = QAction(self)
        self.export_action.triggered.connect(self._export_presets)
        self.file_menu.addAction(self.export_action)

        self.file_menu.addSeparator()

        self.exit_action = QAction(self)
        self.exit_action.triggered.connect(self._handle_exit)
        self.file_menu.addAction(self.exit_action)

        self.language_menu = menubar.addMenu("")
        self.language_actions: dict[str, QAction] = {}
        for code, label in language_items():
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda _checked=False, value=code: self._set_language(value))
            self.language_menu.addAction(action)
            self.language_actions[code] = action

        self.help_menu = menubar.addMenu("")
        self.help_action = QAction(self)
        self.help_action.triggered.connect(self._show_help_dialog)
        self.help_menu.addAction(self.help_action)

    def _build_tray(self) -> None:
        self.tray_icon = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = load_app_icon()
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu(self)
        self.tray_show_action = QAction(self)
        self.tray_toggle_action = QAction(self)
        self.tray_pause_action = QAction(self)
        self.tray_exit_action = QAction(self)

        tray_menu.addAction(self.tray_show_action)
        tray_menu.addAction(self.tray_toggle_action)
        tray_menu.addAction(self.tray_pause_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.tray_exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _wire_events(self) -> None:
        self.action_mode_combo.currentIndexChanged.connect(self._on_form_changed)
        self.mouse_button_combo.currentIndexChanged.connect(self._on_form_changed)
        self.action_key_edit.hotkey_changed.connect(self._on_form_changed)
        self.target_mode_combo.currentIndexChanged.connect(self._on_form_changed)
        self.fixed_x_spin.valueChanged.connect(self._on_form_changed)
        self.fixed_y_spin.valueChanged.connect(self._on_form_changed)
        self.capture_delay_spin.valueChanged.connect(self._on_form_changed)
        self.frequency_spin.valueChanged.connect(self._on_form_changed)
        self.hotkey_scope_combo.currentIndexChanged.connect(self._on_form_changed)
        self.toggle_hotkey_edit.hotkey_changed.connect(self._on_form_changed)
        self.exit_hotkey_edit.hotkey_changed.connect(self._on_form_changed)
        self.minimize_to_tray_checkbox.stateChanged.connect(self._on_form_changed)
        self.enable_hud_checkbox.stateChanged.connect(self._on_form_changed)
        self.hud_x_spin.valueChanged.connect(self._on_form_changed)
        self.hud_y_spin.valueChanged.connect(self._on_form_changed)
        for checkbox in self.hud_item_checkboxes.values():
            checkbox.stateChanged.connect(self._on_hud_item_changed)

        self.use_current_cursor_button.clicked.connect(self._fill_coordinates_from_cursor)

        self.start_button.clicked.connect(self._handle_start_resume)
        self.pause_button.clicked.connect(self._handle_pause)
        self.exit_button.clicked.connect(self._handle_exit)

        self.load_preset_button.clicked.connect(self._load_selected_preset)
        self.save_preset_button.clicked.connect(self._save_current_preset)
        self.save_as_preset_button.clicked.connect(self._save_preset_as)
        self.delete_preset_button.clicked.connect(self._delete_selected_preset)
        self.import_presets_button.clicked.connect(self._import_presets)
        self.export_presets_button.clicked.connect(self._export_presets)

        self._controller.state_changed.connect(self._on_state_changed)
        self._controller.status_changed.connect(self._on_status_changed)
        self._controller.error_occurred.connect(self._on_controller_error)
        self._controller.position_captured.connect(self._on_position_captured)
        self._controller.action_count_changed.connect(self._on_action_count_changed)
        self._controller.actual_frequency_changed.connect(self._on_actual_frequency_changed)

        self._global_hotkeys.toggle_pressed.connect(self._handle_hotkey_toggle)
        self._global_hotkeys.exit_pressed.connect(self._handle_exit)
        self._global_hotkeys.error_occurred.connect(self._on_controller_error)

        if self.tray_icon is not None:
            self.tray_show_action.triggered.connect(self._show_window)
            self.tray_toggle_action.triggered.connect(self._handle_hotkey_toggle)
            self.tray_pause_action.triggered.connect(self._handle_pause)
            self.tray_exit_action.triggered.connect(self._handle_exit)
            self.tray_icon.activated.connect(self._on_tray_activated)

    def _display_name(self) -> str:
        return app_display_name(self._language)

    def _default_preset_name(self) -> str:
        return default_preset_name(self._language)

    def _set_combo_items(self, combo: QComboBox, items: list[tuple[str, str]], current_data: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        for value, label in items:
            combo.addItem(label, value)
        index = combo.findData(current_data)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def _set_combo_data(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _current_combo_data(self, combo: QComboBox, default: str) -> str:
        data = combo.currentData()
        return data if isinstance(data, str) and data else default

    def _apply_translations(self) -> None:
        action_mode = self._current_combo_data(self.action_mode_combo, "mouse")
        mouse_button = self._current_combo_data(self.mouse_button_combo, "left")
        target_mode = self._current_combo_data(self.target_mode_combo, "capture")
        hotkey_scope = self._current_combo_data(self.hotkey_scope_combo, "global")

        self.setWindowTitle(f"{self._display_name()} {APP_VERSION}")
        self.title_label.setText(self._display_name())
        self.subtitle_label.setText(tr(self._language, "app.hero_subtitle"))
        self.statusBar().showMessage(tr(self._language, "status.ready"))

        self.action_group.setTitle(tr(self._language, "group.action"))
        self.mouse_group.setTitle(tr(self._language, "group.mouse"))
        self.timing_group.setTitle(tr(self._language, "group.timing"))
        self.hotkey_group.setTitle(tr(self._language, "group.hotkey"))
        self.options_group.setTitle(tr(self._language, "group.options"))
        self.controls_group.setTitle(tr(self._language, "group.controls"))
        self.status_group.setTitle(tr(self._language, "group.status"))
        self.help_group.setTitle(tr(self._language, "group.help"))
        self.preset_group.setTitle(tr(self._language, "group.presets"))

        self.action_mode_label.setText(tr(self._language, "field.action_mode"))
        self.action_key_label.setText(tr(self._language, "field.action_key"))
        self.action_key_hint.setText(tr(self._language, "hint.action_key"))
        self.action_key_edit.setPlaceholderText(tr(self._language, "hint.hotkey_input"))

        self.mouse_button_label.setText(tr(self._language, "field.mouse_button"))
        self.target_mode_label.setText(tr(self._language, "field.target_mode"))
        self.fixed_coordinates_label.setText(tr(self._language, "field.fixed_coordinates"))
        self.capture_delay_label.setText(tr(self._language, "field.capture_delay"))
        self.use_current_cursor_button.setText(tr(self._language, "button.read_cursor"))
        self.capture_delay_spin.setSuffix(tr(self._language, "suffix.seconds"))

        self.frequency_label.setText(tr(self._language, "field.frequency"))
        self.frequency_spin.setSuffix(tr(self._language, "suffix.per_second"))

        self.hotkey_scope_label.setText(tr(self._language, "field.hotkey_scope"))
        self.toggle_hotkey_label.setText(tr(self._language, "field.toggle_hotkey"))
        self.exit_hotkey_label.setText(tr(self._language, "field.exit_hotkey"))
        self.hotkey_hint.setText(tr(self._language, "hint.hotkey_scope"))
        self.toggle_hotkey_edit.setPlaceholderText(tr(self._language, "hint.hotkey_input"))
        self.exit_hotkey_edit.setPlaceholderText(tr(self._language, "hint.hotkey_input"))

        self.minimize_to_tray_checkbox.setText(tr(self._language, "option.minimize_to_tray"))
        self.enable_hud_checkbox.setText(tr(self._language, "option.hud_enabled"))
        self.hud_items_label.setText(tr(self._language, "field.hud_items"))
        self.hud_position_label.setText(tr(self._language, "field.hud_position"))
        self.hud_hint_label.setText(tr(self._language, "hint.hud_items"))
        hud_item_labels = get_hud_item_labels(self._language)
        for key, checkbox in self.hud_item_checkboxes.items():
            checkbox.setText(hud_item_labels[key])

        self.start_button.setText(tr(self._language, "button.start_resume"))
        self.pause_button.setText(tr(self._language, "button.pause"))
        self.exit_button.setText(tr(self._language, "button.exit"))

        self.state_label.setText(tr(self._language, "field.current_state"))
        self.actual_frequency_label.setText(tr(self._language, "field.actual_frequency"))
        self.action_count_label.setText(tr(self._language, "field.action_count"))
        self.target_position_label.setText(tr(self._language, "field.target_position"))
        self.summary_label.setText(tr(self._language, "field.current_summary"))
        self._render_actual_frequency()
        self.action_count_value.setText(str(self._action_count))

        self.current_preset_label.setText(tr(self._language, "field.current_preset"))
        self.load_preset_button.setText(tr(self._language, "button.load"))
        self.save_preset_button.setText(tr(self._language, "button.save"))
        self.save_as_preset_button.setText(tr(self._language, "button.save_as"))
        self.delete_preset_button.setText(tr(self._language, "button.delete"))
        self.import_presets_button.setText(tr(self._language, "button.import_json"))
        self.export_presets_button.setText(tr(self._language, "button.export_json"))

        self.help_browser.setHtml(build_help_html(self._language))

        self.file_menu.setTitle(tr(self._language, "menu.file"))
        self.import_action.setText(tr(self._language, "menu.file.import_presets"))
        self.export_action.setText(tr(self._language, "menu.file.export_presets"))
        self.exit_action.setText(tr(self._language, "menu.file.exit"))
        self.language_menu.setTitle(tr(self._language, "menu.language"))
        for code, action in self.language_actions.items():
            action.setChecked(code == self._language)
        self.help_menu.setTitle(tr(self._language, "menu.help"))
        self.help_action.setText(tr(self._language, "menu.help.usage"))

        if self.tray_icon is not None:
            self.tray_show_action.setText(tr(self._language, "tray.show_window"))
            self.tray_toggle_action.setText(tr(self._language, "tray.start_pause"))
            self.tray_pause_action.setText(tr(self._language, "tray.pause"))
            self.tray_exit_action.setText(tr(self._language, "tray.exit"))

        self._set_combo_items(self.action_mode_combo, list(get_action_labels(self._language).items()), action_mode)
        self._set_combo_items(self.mouse_button_combo, list(get_mouse_button_labels(self._language).items()), mouse_button)
        self._set_combo_items(self.target_mode_combo, list(get_target_labels(self._language).items()), target_mode)
        self._set_combo_items(self.hotkey_scope_combo, list(get_hotkey_scope_labels(self._language).items()), hotkey_scope)
        self._sync_observability_views()

    def _load_initial_state(self) -> None:
        self._rebuild_preset_combo(self._persisted_state.selected_preset)
        self._apply_overlay_settings_to_form(self._persisted_state.overlay)
        self._apply_settings_to_form(self._persisted_state.last_settings)

    def _apply_overlay_settings_to_form(self, settings: OverlaySettings) -> None:
        self._loading = True
        try:
            self.enable_hud_checkbox.setChecked(settings.hud_enabled)
            self.hud_x_spin.setValue(settings.hud_x)
            self.hud_y_spin.setValue(settings.hud_y)
            for key, checkbox in self.hud_item_checkboxes.items():
                checkbox.setChecked(key in settings.hud_items)
        finally:
            self._loading = False

    def _apply_settings_to_form(self, settings: AppSettings) -> None:
        self._loading = True
        try:
            self._set_combo_data(self.action_mode_combo, settings.action_mode)
            self._set_combo_data(self.mouse_button_combo, settings.mouse_button)
            self.action_key_edit.set_hotkey(settings.action_key)
            self._set_combo_data(self.target_mode_combo, settings.target_mode)
            self.fixed_x_spin.setValue(settings.fixed_x)
            self.fixed_y_spin.setValue(settings.fixed_y)
            self.capture_delay_spin.setValue(settings.capture_delay_seconds)
            self.frequency_spin.setValue(settings.frequency_hz)
            self._set_combo_data(self.hotkey_scope_combo, settings.hotkey_scope)
            self.toggle_hotkey_edit.set_hotkey(settings.toggle_hotkey)
            self.exit_hotkey_edit.set_hotkey(settings.exit_hotkey)
            self.minimize_to_tray_checkbox.setChecked(settings.minimize_to_tray)
            self._current_target = None
        finally:
            self._loading = False

    def _collect_settings(self) -> AppSettings:
        return AppSettings(
            action_mode=self._current_combo_data(self.action_mode_combo, "mouse"),
            mouse_button=self._current_combo_data(self.mouse_button_combo, "left"),
            action_key=self.action_key_edit.hotkey(),
            target_mode=self._current_combo_data(self.target_mode_combo, "capture"),
            fixed_x=self.fixed_x_spin.value(),
            fixed_y=self.fixed_y_spin.value(),
            capture_delay_seconds=self.capture_delay_spin.value(),
            frequency_hz=self.frequency_spin.value(),
            hotkey_scope=self._current_combo_data(self.hotkey_scope_combo, "global"),
            toggle_hotkey=self.toggle_hotkey_edit.hotkey(),
            exit_hotkey=self.exit_hotkey_edit.hotkey(),
            minimize_to_tray=self.minimize_to_tray_checkbox.isChecked(),
        )

    def _selected_hud_items(self) -> tuple[str, ...]:
        selected = tuple(key for key, checkbox in self.hud_item_checkboxes.items() if checkbox.isChecked())
        return selected or ("state",)

    def _collect_overlay_settings(self) -> OverlaySettings:
        return OverlaySettings(
            hud_enabled=self.enable_hud_checkbox.isChecked(),
            hud_items=self._selected_hud_items(),
            hud_x=self.hud_x_spin.value(),
            hud_y=self.hud_y_spin.value(),
        )

    def _refresh_form_state(self) -> None:
        settings = self._collect_settings()
        self._overlay_settings = self._collect_overlay_settings()
        mouse_mode = settings.action_mode == "mouse"
        capture_mode = settings.target_mode == "capture"
        fixed_mode = settings.target_mode == "fixed"

        self.action_key_label.setVisible(not mouse_mode)
        self.action_key_container.setVisible(not mouse_mode)
        self.mouse_group.setVisible(mouse_mode)
        self.fixed_coordinates_label.setVisible(mouse_mode and fixed_mode)
        self.fixed_coordinates_row.setVisible(mouse_mode and fixed_mode)
        self.capture_delay_label.setVisible(mouse_mode and capture_mode)
        self.capture_delay_spin.setVisible(mouse_mode and capture_mode)

        self.fixed_x_spin.setEnabled(mouse_mode and fixed_mode)
        self.fixed_y_spin.setEnabled(mouse_mode and fixed_mode)
        self.use_current_cursor_button.setEnabled(mouse_mode and fixed_mode)
        self.capture_delay_spin.setEnabled(mouse_mode and capture_mode)
        hud_controls_enabled = self._overlay_settings.hud_enabled
        self.hud_items_label.setEnabled(hud_controls_enabled)
        self.hud_position_label.setEnabled(hud_controls_enabled)
        self.hud_hint_label.setEnabled(hud_controls_enabled)
        self.hud_x_spin.setEnabled(hud_controls_enabled)
        self.hud_y_spin.setEnabled(hud_controls_enabled)
        for checkbox in self.hud_item_checkboxes.values():
            checkbox.setEnabled(hud_controls_enabled)

        errors = validate_settings(settings, self._language)
        self.validation_label.setText("\n".join(errors))
        self._update_summary(settings)
        self._configure_hotkeys(settings, errors)
        self._save_persisted_state()
        self._on_state_changed(self._controller.state)
        self._sync_observability_views()

    def _update_summary(self, settings: AppSettings) -> None:
        target_text = tr(self._language, "summary.target.not_applicable")
        if settings.action_mode == "mouse":
            if settings.target_mode == "capture":
                target_text = tr(self._language, "summary.target.capture", seconds=settings.capture_delay_seconds)
            else:
                target_text = tr(self._language, "summary.target.fixed", x=settings.fixed_x, y=settings.fixed_y)

        action_text = format_action_label(settings, self._language)
        if settings.action_mode == "keyboard":
            action_text = tr(
                self._language,
                "summary.action.keyboard",
                action=action_text,
                combo=settings.action_key.display_text() or tr(self._language, "summary.not_set"),
            )

        scope_text = get_hotkey_scope_labels(self._language).get(settings.hotkey_scope, tr(self._language, "hotkey_scope.global"))
        hotkeys = tr(
            self._language,
            "summary.hotkeys",
            toggle=settings.toggle_hotkey.display_text() or tr(self._language, "summary.not_set"),
            exit=settings.exit_hotkey.display_text() or tr(self._language, "summary.not_set"),
            scope=scope_text,
        )
        self.summary_value.setText(
            tr(
                self._language,
                "summary.full",
                action=action_text,
                frequency=settings.frequency_hz,
                target=target_text,
                hotkeys=hotkeys,
            )
        )

        if settings.action_mode == "keyboard":
            self.target_value.setText(tr(self._language, "target_value.keyboard_mode"))
        elif settings.target_mode == "fixed":
            self.target_value.setText(tr(self._language, "target_value.fixed", x=settings.fixed_x, y=settings.fixed_y))
        elif self._current_target is None:
            self.target_value.setText(tr(self._language, "target_value.capture_pending"))
        else:
            self.target_value.setText(tr(self._language, "target_value.captured", x=self._current_target[0], y=self._current_target[1]))

    def _configure_hotkeys(self, settings: AppSettings, errors: list[str]) -> None:
        self._clear_local_shortcuts()
        self._global_hotkeys.stop()
        if errors:
            return
        if settings.hotkey_scope == "global":
            self._global_hotkeys.configure(settings.toggle_hotkey, settings.exit_hotkey, self._language)
            return

        toggle_shortcut = QShortcut(QKeySequence(settings.toggle_hotkey.display_text()), self)
        toggle_shortcut.activated.connect(self._handle_hotkey_toggle)
        exit_shortcut = QShortcut(QKeySequence(settings.exit_hotkey.display_text()), self)
        exit_shortcut.activated.connect(self._handle_exit)
        self._local_shortcuts = [toggle_shortcut, exit_shortcut]

    def _clear_local_shortcuts(self) -> None:
        for shortcut in self._local_shortcuts:
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        self._local_shortcuts = []

    def _prepare_for_start(self, settings: AppSettings) -> None:
        if settings.action_mode == "mouse" and settings.target_mode == "capture":
            self._current_target = None
            self.target_value.setText(tr(self._language, "target_value.waiting_capture"))

    def _handle_start_resume(self) -> None:
        settings = self._collect_settings()
        errors = validate_settings(settings, self._language)
        if errors:
            QMessageBox.warning(self, self._display_name(), "\n".join(errors))
            return
        self._prepare_for_start(settings)
        self._controller.start(settings, self._language)

    def _handle_pause(self) -> None:
        self._controller.pause()

    def _handle_hotkey_toggle(self) -> None:
        if self._controller.state in {"running", "countdown"}:
            self._controller.pause()
            return

        settings = self._collect_settings()
        errors = validate_settings(settings, self._language)
        if errors:
            self._on_status_changed(tr(self._language, "status.fix_errors_before_hotkey"))
            return
        self._prepare_for_start(settings)
        self._controller.start(settings, self._language)

    def _handle_exit(self) -> None:
        self._force_quit = True
        self._save_persisted_state()
        self._controller.shutdown()
        self._clear_local_shortcuts()
        self._global_hotkeys.stop()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _set_language(self, language: str) -> None:
        if self._loading:
            return
        language = normalize_language(language)
        if language == self._language:
            for code, action in self.language_actions.items():
                action.setChecked(code == self._language)
            return
        self._language = language
        self._controller.set_language(self._language)
        self._apply_translations()
        self._refresh_form_state()

    def _on_form_changed(self, *_args) -> None:
        if self._loading:
            return
        if self._controller.state in {"idle", "paused"}:
            self._current_target = None
        self._refresh_form_state()

    def _on_hud_item_changed(self, *_args) -> None:
        if self._loading:
            return
        if any(checkbox.isChecked() for checkbox in self.hud_item_checkboxes.values()):
            self._on_form_changed()
            return

        self._loading = True
        try:
            self.hud_state_checkbox.setChecked(True)
        finally:
            self._loading = False
        self._on_form_changed()

    def _on_state_changed(self, state: str) -> None:
        self._controller_state = state
        self.state_value.setText(tr(self._language, f"state.{state}"))
        has_errors = bool(self.validation_label.text())
        can_start = not has_errors and state in {"idle", "paused"}
        can_pause = state in {"running", "countdown"}

        self.start_button.setEnabled(can_start)
        self.pause_button.setEnabled(can_pause)

        if self.tray_icon is not None:
            self.tray_toggle_action.setEnabled(can_pause or not has_errors)
            self.tray_pause_action.setEnabled(can_pause)
        self._sync_observability_views()

    def _on_status_changed(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _on_position_captured(self, x: int, y: int) -> None:
        self._current_target = (x, y)
        self.target_value.setText(tr(self._language, "target_value.captured", x=x, y=y))
        self._sync_observability_views()

    def _on_action_count_changed(self, count: int) -> None:
        self._action_count = count
        self.action_count_value.setText(str(count))
        self._sync_observability_views()

    def _on_actual_frequency_changed(self, frequency: float) -> None:
        self._actual_frequency = max(frequency, 0.0)
        self._render_actual_frequency()
        self._sync_observability_views()

    def _render_actual_frequency(self) -> None:
        self.actual_frequency_value.setText(
            tr(self._language, "value.actual_frequency", frequency=self._actual_frequency)
        )

    def _hud_lines(self) -> list[str]:
        lines: list[str] = []
        items = self._overlay_settings.hud_items
        if "state" in items:
            lines.append(f"{tr(self._language, 'field.current_state')}: {tr(self._language, f'state.{self._controller_state}')}")
        if "rate" in items:
            lines.append(f"{tr(self._language, 'field.actual_frequency')}: {tr(self._language, 'value.actual_frequency', frequency=self._actual_frequency)}")
        if "count" in items:
            lines.append(f"{tr(self._language, 'field.action_count')}: {self._action_count}")
        return lines

    def _sync_observability_views(self) -> None:
        overlay = self._overlay_settings
        self._hud_window.update_content(
            lines=self._hud_lines(),
            x=overlay.hud_x,
            y=overlay.hud_y,
            visible=overlay.hud_enabled,
        )

    def _on_controller_error(self, message: str) -> None:
        QMessageBox.warning(self, self._display_name(), message)
        self.statusBar().showMessage(message)

    def _fill_coordinates_from_cursor(self) -> None:
        position = get_cursor_position()
        if position is None:
            QMessageBox.warning(self, self._display_name(), tr(self._language, "dialog.cursor_failed"))
            return
        self.fixed_x_spin.setValue(position[0])
        self.fixed_y_spin.setValue(position[1])

    def _rebuild_preset_combo(self, selected_name: str) -> None:
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        for name in sorted(self._presets):
            self.preset_combo.addItem(name)
        index = self.preset_combo.findText(selected_name)
        if index < 0 and self.preset_combo.count() > 0:
            index = 0
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)
        self.preset_combo.blockSignals(False)

    def _load_selected_preset(self) -> None:
        preset = self._presets.get(self.preset_combo.currentText())
        if preset is None:
            return
        self._apply_settings_to_form(preset.settings)
        self._refresh_form_state()
        self._on_status_changed(tr(self._language, "status.loaded_preset", name=preset.name))

    def _save_current_preset(self) -> None:
        name = self.preset_combo.currentText().strip() or self._default_preset_name()
        self._presets[name] = Preset(
            name=name,
            settings=self._collect_settings(),
            updated_at=datetime.now().isoformat(timespec="seconds"),
        )
        self._rebuild_preset_combo(name)
        self._save_persisted_state()
        self._on_status_changed(tr(self._language, "status.saved_preset", name=name))

    def _save_preset_as(self) -> None:
        name, accepted = QInputDialog.getText(self, self._display_name(), tr(self._language, "dialog.preset_name"))
        name = name.strip()
        if not accepted or not name:
            return
        self._presets[name] = Preset(
            name=name,
            settings=self._collect_settings(),
            updated_at=datetime.now().isoformat(timespec="seconds"),
        )
        self._rebuild_preset_combo(name)
        self._save_persisted_state()
        self._on_status_changed(tr(self._language, "status.saved_preset_as", name=name))

    def _delete_selected_preset(self) -> None:
        name = self.preset_combo.currentText()
        if not name:
            return
        if QMessageBox.question(self, self._display_name(), tr(self._language, "dialog.delete_preset", name=name)) != QMessageBox.Yes:
            return
        self._presets.pop(name, None)
        if not self._presets:
            default_name = self._default_preset_name()
            self._presets[default_name] = Preset(name=default_name, settings=AppSettings())
        next_name = sorted(self._presets)[0]
        self._rebuild_preset_combo(next_name)
        self._save_persisted_state()
        self._on_status_changed(tr(self._language, "status.deleted_preset", name=name))

    def _import_presets(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, self._display_name(), "", tr(self._language, "dialog.json_filter"))
        if not path:
            return
        try:
            imported = self._store.import_presets(path, self._language)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, self._display_name(), tr(self._language, "dialog.import_failed", error=exc))
            return
        for preset in imported:
            self._presets[preset.name] = preset
        selected = self.preset_combo.currentText() or self._default_preset_name()
        self._rebuild_preset_combo(selected)
        self._save_persisted_state()
        self._on_status_changed(tr(self._language, "status.imported_presets", count=len(imported)))

    def _export_presets(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._display_name(),
            tr(self._language, "dialog.presets_file_name"),
            tr(self._language, "dialog.json_filter"),
        )
        if not path:
            return
        try:
            self._store.export_presets(path, list(self._presets.values()))
        except OSError as exc:
            QMessageBox.warning(self, self._display_name(), tr(self._language, "dialog.export_failed", error=exc))
            return
        self._on_status_changed(tr(self._language, "status.exported_presets", path=path))

    def _save_persisted_state(self) -> None:
        if self._loading:
            return
        selected = self.preset_combo.currentText() or self._default_preset_name()
        self._persisted_state = PersistedState(
            language=self._language,
            selected_preset=selected,
            last_settings=self._collect_settings(),
            overlay=self._collect_overlay_settings(),
            presets=list(self._presets.values()),
        )
        try:
            self._store.save(self._persisted_state)
        except OSError as exc:
            self.statusBar().showMessage(tr(self._language, "status.save_config_failed", error=exc))

    def _show_help_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(tr(self._language, "dialog.help_title", app_name=self._display_name()))
        dialog.resize(620, 480)

        layout = QVBoxLayout(dialog)
        browser = QTextBrowser(dialog)
        browser.setOpenExternalLinks(False)
        browser.setHtml(self.help_browser.toHtml())
        layout.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, dialog)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        if ok_button is not None:
            ok_button.setText(tr(self._language, "button.ok"))
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.exec()

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_window()

    def closeEvent(self, event: QCloseEvent) -> None:  # type: ignore[override]
        self._save_persisted_state()
        if not self._force_quit and self.minimize_to_tray_checkbox.isChecked() and self.tray_icon is not None:
            self.hide()
            event.ignore()
            if not self._tray_notice_shown:
                self.tray_icon.showMessage(self._display_name(), tr(self._language, "status.tray_running"))
                self._tray_notice_shown = True
            return
        self._controller.shutdown()
        self._global_hotkeys.stop()
        self._clear_local_shortcuts()
        self._hud_window.hide()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        event.accept()
