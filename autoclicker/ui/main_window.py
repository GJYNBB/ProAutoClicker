from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStatusBar,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from autoclicker import APP_VERSION
from autoclicker.controller import AutomationController
from autoclicker.input_backend import create_input_backend
from autoclicker.i18n import app_display_name, build_help_html, default_preset_name, language_items, normalize_language, tr
from autoclicker.models import (
    AppSettings,
    EMERGENCY_STOP_HOTKEY,
    PersistedState,
    Preset,
    ValidationResult,
    default_action_unit,
    format_action_unit_label,
    get_hud_item_labels,
    get_hotkey_scope_labels,
    get_sequence_mode_labels,
    get_theme_labels,
    summarize_action_unit,
    validate_settings,
)
from autoclicker.resources import load_app_icon
from autoclicker.store import SettingsStore
from autoclicker.theme import apply_theme
from autoclicker.ui.action_unit_editor import ActionUnitDialog, ActionUnitEditor
from autoclicker.ui.hotkey_edit import HotkeyLineEdit
from autoclicker.ui.status_hud import StatusHudWindow
from autoclicker.update_checker import UpdateChecker


def _set_widget_error(widget: QWidget, message: str | None) -> None:
    widget.setProperty("errorState", bool(message))
    if message:
        widget.setToolTip(message)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._store = SettingsStore()
        self._input_backend = create_input_backend()
        self._controller = AutomationController(self._input_backend)
        self._global_hotkeys = self._input_backend.create_hotkey_manager()
        self._update_checker = UpdateChecker(self)
        self._persisted_state = self._store.load()
        self._language = normalize_language(self._persisted_state.language)
        self.theme = self._persisted_state.theme
        self._controller.set_language(self._language)
        self._presets = {preset.name: preset for preset in self._persisted_state.presets}
        self._settings = AppSettings.from_dict(self._persisted_state.last_settings.to_dict())
        self._overlay = self._persisted_state.overlay
        self._hud_window = StatusHudWindow()
        self._current_target: tuple[int, int] | None = None
        self._action_count = 0
        self._actual_frequency = 0.0
        self._current_step_index = -1
        self._current_step_text = ""
        self._last_action_text = ""
        self._controller_state = self._controller.state
        self._local_shortcuts: list[QShortcut] = []
        self._loading = False
        self._tray_notice_shown = False
        self._force_quit = False
        self._validation = ValidationResult()

        self.setWindowIcon(load_app_icon())
        self.resize(1100, 860)
        self.setMinimumSize(820, 620)

        self._build_ui()
        self._build_menus()
        self._wire_events()
        self._apply_translations()
        self._load_initial_state()
        self._refresh_form_state()
        apply_theme(QApplication.instance(), self.theme)
        if self._persisted_state.auto_check_updates:
            QTimer.singleShot(1000, lambda: self._check_for_updates(manual=False))

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("tabPage")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        self.title_label = QLabel(root)
        self.title_label.setObjectName("heroTitle")
        self.subtitle_label = QLabel(root)
        self.subtitle_label.setObjectName("heroSubtitle")
        self.subtitle_label.setWordWrap(True)

        self.tabs = QTabWidget(root)
        self.quick_tab = self._build_quick_tab()
        self.sequence_tab = self._build_sequence_tab()
        self.runtime_tab = self._build_runtime_tab()
        self.tabs.addTab(self.quick_tab, "")
        self.tabs.addTab(self.sequence_tab, "")
        self.tabs.addTab(self.runtime_tab, "")

        root_layout.addWidget(self.title_label)
        root_layout.addWidget(self.subtitle_label)
        root_layout.addWidget(self.tabs, 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar(self))
        self._build_tray()

    def _create_scroll_panel(self, content: QWidget) -> QScrollArea:
        area = QScrollArea(self)
        area.setObjectName("pageScroll")
        area.viewport().setObjectName("scrollViewport")
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        content.setObjectName("scrollContent")
        area.setWidget(content)
        return area

    def _build_quick_tab(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("tabPage")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget(page)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(14)

        self.quick_hint_label = QLabel(container)
        self.quick_hint_label.setWordWrap(True)
        self.quick_editor = ActionUnitEditor(
            language=self._language,
            allow_infinite=True,
            backend=self._input_backend,
            parent=container,
        )

        self.task_group = QGroupBox(container)
        task_layout = QFormLayout(self.task_group)
        self.sequence_mode_label = QLabel(self.task_group)
        self.sequence_mode_combo = QComboBox(self.task_group)
        self.sequence_note_label = QLabel(self.task_group)
        self.sequence_note_label.setWordWrap(True)
        self.sequence_note_label.setStyleSheet("color: #5f7285;")
        task_layout.addRow(self.sequence_mode_label, self.sequence_mode_combo)
        task_layout.addRow(QLabel(""), self.sequence_note_label)

        self.hotkey_group = QGroupBox(container)
        hotkey_layout = QFormLayout(self.hotkey_group)
        self.hotkey_scope_label = QLabel(self.hotkey_group)
        self.hotkey_scope_combo = QComboBox(self.hotkey_group)
        self.toggle_hotkey_label = QLabel(self.hotkey_group)
        self.toggle_hotkey_edit = HotkeyLineEdit(self.hotkey_group)
        self.exit_hotkey_label = QLabel(self.hotkey_group)
        self.exit_hotkey_edit = HotkeyLineEdit(self.hotkey_group)
        self.hotkey_note_label = QLabel(self.hotkey_group)
        self.hotkey_note_label.setWordWrap(True)
        self.hotkey_note_label.setStyleSheet("color: #5f7285;")
        hotkey_layout.addRow(self.hotkey_scope_label, self.hotkey_scope_combo)
        hotkey_layout.addRow(self.toggle_hotkey_label, self.toggle_hotkey_edit)
        hotkey_layout.addRow(self.exit_hotkey_label, self.exit_hotkey_edit)
        hotkey_layout.addRow(QLabel(""), self.hotkey_note_label)

        self.safety_group = QGroupBox(container)
        safety_layout = QFormLayout(self.safety_group)
        self.confirm_before_start_checkbox = QCheckBox(self.safety_group)
        self.safety_countdown_label = QLabel(self.safety_group)
        self.safety_countdown_spin = QDoubleSpinBox(self.safety_group)
        self.safety_countdown_spin.setDecimals(1)
        self.safety_countdown_spin.setRange(0.0, 30.0)
        self.safety_countdown_spin.setSingleStep(0.5)
        self.emergency_hotkey_label = QLabel(self.safety_group)
        self.emergency_hotkey_value = QLabel(EMERGENCY_STOP_HOTKEY.display_text(), self.safety_group)
        self.safety_note_label = QLabel(self.safety_group)
        self.safety_note_label.setWordWrap(True)
        self.safety_note_label.setStyleSheet("color: #5f7285;")
        safety_layout.addRow(self.confirm_before_start_checkbox)
        safety_layout.addRow(self.safety_countdown_label, self.safety_countdown_spin)
        safety_layout.addRow(self.emergency_hotkey_label, self.emergency_hotkey_value)
        safety_layout.addRow(QLabel(""), self.safety_note_label)

        self.appearance_group = QGroupBox(container)
        appearance_layout = QVBoxLayout(self.appearance_group)
        appearance_form = QFormLayout()
        self.theme_label = QLabel(self.appearance_group)
        self.theme_combo = QComboBox(self.appearance_group)
        appearance_form.addRow(self.theme_label, self.theme_combo)

        self.minimize_to_tray_checkbox = QCheckBox(self.appearance_group)
        self.auto_check_updates_checkbox = QCheckBox(self.appearance_group)
        self.enable_hud_checkbox = QCheckBox(self.appearance_group)
        self.hud_items_label = QLabel(self.appearance_group)
        self.hud_position_label = QLabel(self.appearance_group)
        self.hud_opacity_label = QLabel(self.appearance_group)
        self.hud_note_label = QLabel(self.appearance_group)
        self.hud_note_label.setWordWrap(True)
        self.hud_note_label.setStyleSheet("color: #5f7285;")

        self.hud_order_list = QListWidget(self.appearance_group)
        self.hud_order_list.setObjectName("hudOrderList")
        self.hud_order_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.hud_order_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.hud_order_list.setDragEnabled(True)
        self.hud_order_list.setDropIndicatorShown(True)
        self.hud_order_list.setDefaultDropAction(Qt.MoveAction)
        self.hud_order_list.setAlternatingRowColors(False)
        self.hud_order_list.setMaximumHeight(168)

        self.hud_x_spin = QSpinBox(self.appearance_group)
        self.hud_x_spin.setRange(0, 99999)
        self.hud_y_spin = QSpinBox(self.appearance_group)
        self.hud_y_spin.setRange(0, 99999)
        self.hud_opacity_spin = QSpinBox(self.appearance_group)
        self.hud_opacity_spin.setRange(15, 100)
        self.hud_opacity_spin.setSingleStep(5)
        position_row = QWidget(self.appearance_group)
        position_layout = QHBoxLayout(position_row)
        position_layout.setContentsMargins(0, 0, 0, 0)
        position_layout.setSpacing(8)
        position_layout.addWidget(QLabel("X", position_row))
        position_layout.addWidget(self.hud_x_spin)
        position_layout.addWidget(QLabel("Y", position_row))
        position_layout.addWidget(self.hud_y_spin)
        position_layout.addStretch(1)

        hud_form = QFormLayout()
        hud_form.addRow(self.hud_items_label, self.hud_order_list)
        hud_form.addRow(self.hud_position_label, position_row)
        hud_form.addRow(self.hud_opacity_label, self.hud_opacity_spin)
        appearance_layout.addLayout(appearance_form)
        appearance_layout.addWidget(self.minimize_to_tray_checkbox)
        appearance_layout.addWidget(self.auto_check_updates_checkbox)
        appearance_layout.addWidget(self.enable_hud_checkbox)
        appearance_layout.addLayout(hud_form)
        appearance_layout.addWidget(self.hud_note_label)

        self.controls_group = QGroupBox(container)
        controls_layout = QVBoxLayout(self.controls_group)
        buttons_row = QWidget(self.controls_group)
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        self.start_button = QPushButton(self.controls_group)
        self.start_button.setObjectName("primaryButton")
        self.pause_button = QPushButton(self.controls_group)
        self.exit_button = QPushButton(self.controls_group)
        self.exit_button.setObjectName("dangerButton")
        buttons_layout.addWidget(self.start_button, 2)
        buttons_layout.addWidget(self.pause_button, 1)
        buttons_layout.addWidget(self.exit_button, 1)
        self.validation_label = QLabel(self.controls_group)
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("color: #b42318;")
        controls_layout.addWidget(buttons_row)
        controls_layout.addWidget(self.validation_label)

        for widget in (
            self.quick_hint_label,
            self.quick_editor,
            self.task_group,
            self.hotkey_group,
            self.safety_group,
            self.appearance_group,
            self.controls_group,
        ):
            layout.addWidget(widget)
        layout.addStretch(1)
        page_layout.addWidget(self._create_scroll_panel(container))
        return page

    def _build_sequence_tab(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("tabPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        self.sequence_hint_label = QLabel(page)
        self.sequence_hint_label.setWordWrap(True)

        self.sequence_group = QGroupBox(page)
        group_layout = QVBoxLayout(self.sequence_group)
        self.sequence_list = QListWidget(self.sequence_group)
        self.sequence_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.sequence_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.sequence_list.setDragEnabled(True)
        self.sequence_list.setDropIndicatorShown(True)
        self.sequence_list.setDefaultDropAction(Qt.MoveAction)
        buttons_row = QWidget(self.sequence_group)
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        self.add_action_button = QPushButton(self.sequence_group)
        self.edit_action_button = QPushButton(self.sequence_group)
        self.copy_action_button = QPushButton(self.sequence_group)
        self.delete_action_button = QPushButton(self.sequence_group)
        self.move_up_button = QPushButton(self.sequence_group)
        self.move_down_button = QPushButton(self.sequence_group)
        for button in (
            self.add_action_button,
            self.edit_action_button,
            self.copy_action_button,
            self.delete_action_button,
            self.move_up_button,
            self.move_down_button,
        ):
            buttons_layout.addWidget(button)
        buttons_layout.addStretch(1)
        group_layout.addWidget(self.sequence_list)
        group_layout.addWidget(buttons_row)

        layout.addWidget(self.sequence_hint_label)
        layout.addWidget(self.sequence_group, 1)
        return page

    def _build_runtime_tab(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("tabPage")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        container = QWidget(page)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.status_group = QGroupBox(container)
        status_layout = QFormLayout(self.status_group)
        self.state_label = QLabel(self.status_group)
        self.state_value = QLabel(self.status_group)
        self.current_step_label = QLabel(self.status_group)
        self.current_step_value = QLabel(self.status_group)
        self.actual_frequency_label = QLabel(self.status_group)
        self.actual_frequency_value = QLabel(self.status_group)
        self.action_count_label = QLabel(self.status_group)
        self.action_count_value = QLabel(self.status_group)
        self.last_action_label = QLabel(self.status_group)
        self.last_action_value = QLabel(self.status_group)
        self.target_position_label = QLabel(self.status_group)
        self.target_value = QLabel(self.status_group)
        self.summary_label = QLabel(self.status_group)
        self.summary_value = QLabel(self.status_group)
        self.summary_value.setWordWrap(True)
        status_layout.addRow(self.state_label, self.state_value)
        status_layout.addRow(self.current_step_label, self.current_step_value)
        status_layout.addRow(self.actual_frequency_label, self.actual_frequency_value)
        status_layout.addRow(self.action_count_label, self.action_count_value)
        status_layout.addRow(self.last_action_label, self.last_action_value)
        status_layout.addRow(self.target_position_label, self.target_value)
        status_layout.addRow(self.summary_label, self.summary_value)

        self.preset_group = QGroupBox(container)
        preset_layout = QGridLayout(self.preset_group)
        self.current_preset_label = QLabel(self.preset_group)
        self.preset_combo = QComboBox(self.preset_group)
        self.load_preset_button = QPushButton(self.preset_group)
        self.save_preset_button = QPushButton(self.preset_group)
        self.save_as_preset_button = QPushButton(self.preset_group)
        self.delete_preset_button = QPushButton(self.preset_group)
        self.import_presets_button = QPushButton(self.preset_group)
        self.export_presets_button = QPushButton(self.preset_group)
        preset_layout.addWidget(self.current_preset_label, 0, 0)
        preset_layout.addWidget(self.preset_combo, 0, 1, 1, 2)
        preset_layout.addWidget(self.load_preset_button, 1, 0)
        preset_layout.addWidget(self.save_preset_button, 1, 1)
        preset_layout.addWidget(self.save_as_preset_button, 1, 2)
        preset_layout.addWidget(self.delete_preset_button, 2, 0)
        preset_layout.addWidget(self.import_presets_button, 2, 1)
        preset_layout.addWidget(self.export_presets_button, 2, 2)

        self.help_group = QGroupBox(container)
        help_layout = QVBoxLayout(self.help_group)
        self.help_browser = QTextBrowser(self.help_group)
        self.help_browser.setOpenExternalLinks(False)
        help_layout.addWidget(self.help_browser)

        layout.addWidget(self.status_group)
        layout.addWidget(self.preset_group)
        layout.addWidget(self.help_group, 1)
        layout.addStretch(1)
        page_layout.addWidget(self._create_scroll_panel(container))
        return page

    def _build_menus(self) -> None:
        menubar = self.menuBar()
        self.file_menu = menubar.addMenu("")
        self.import_action = QAction(self)
        self.export_action = QAction(self)
        self.exit_action = QAction(self)
        self.import_action.triggered.connect(self._import_presets)
        self.export_action.triggered.connect(self._export_presets)
        self.exit_action.triggered.connect(self._handle_exit)
        self.file_menu.addAction(self.import_action)
        self.file_menu.addAction(self.export_action)
        self.file_menu.addSeparator()
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
        self.check_updates_action = QAction(self)
        self.feedback_action = QAction(self)
        self.help_action.triggered.connect(self._show_help_dialog)
        self.check_updates_action.triggered.connect(lambda: self._check_for_updates(manual=True))
        self.feedback_action.triggered.connect(self._open_feedback_page)
        self.help_menu.addAction(self.help_action)
        self.help_menu.addAction(self.check_updates_action)
        self.help_menu.addAction(self.feedback_action)

    def _build_tray(self) -> None:
        self.tray_icon = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = load_app_icon()
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        menu = QMenu(self)
        self.tray_show_action = QAction(self)
        self.tray_toggle_action = QAction(self)
        self.tray_pause_action = QAction(self)
        self.tray_exit_action = QAction(self)
        menu.addAction(self.tray_show_action)
        menu.addAction(self.tray_toggle_action)
        menu.addAction(self.tray_pause_action)
        menu.addSeparator()
        menu.addAction(self.tray_exit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def _wire_events(self) -> None:
        self.quick_editor.changed.connect(self._on_form_changed)
        self.quick_editor.cursor_read_failed.connect(self._on_cursor_failed)
        self.sequence_mode_combo.currentIndexChanged.connect(self._on_form_changed)
        self.hotkey_scope_combo.currentIndexChanged.connect(self._on_form_changed)
        self.toggle_hotkey_edit.hotkey_changed.connect(self._on_form_changed)
        self.exit_hotkey_edit.hotkey_changed.connect(self._on_form_changed)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        self.confirm_before_start_checkbox.stateChanged.connect(self._on_form_changed)
        self.safety_countdown_spin.valueChanged.connect(self._on_form_changed)
        self.minimize_to_tray_checkbox.stateChanged.connect(self._on_form_changed)
        self.auto_check_updates_checkbox.stateChanged.connect(self._on_form_changed)
        self.enable_hud_checkbox.stateChanged.connect(self._on_form_changed)
        self.hud_x_spin.valueChanged.connect(self._on_form_changed)
        self.hud_y_spin.valueChanged.connect(self._on_form_changed)
        self.hud_opacity_spin.valueChanged.connect(self._on_form_changed)
        self.hud_order_list.itemChanged.connect(self._on_hud_item_changed)
        self.hud_order_list.model().rowsMoved.connect(lambda *_args: self._on_form_changed())

        self.start_button.clicked.connect(self._handle_start_resume)
        self.pause_button.clicked.connect(self._handle_pause)
        self.exit_button.clicked.connect(self._handle_exit)

        self.add_action_button.clicked.connect(self._add_action)
        self.edit_action_button.clicked.connect(self._edit_selected_action)
        self.copy_action_button.clicked.connect(self._copy_selected_action)
        self.delete_action_button.clicked.connect(self._delete_selected_action)
        self.move_up_button.clicked.connect(lambda: self._move_action(-1))
        self.move_down_button.clicked.connect(lambda: self._move_action(1))
        self.sequence_list.itemDoubleClicked.connect(lambda _item: self._edit_selected_action())
        self.sequence_list.currentRowChanged.connect(lambda _row: self._update_sequence_buttons())
        self.sequence_list.itemSelectionChanged.connect(self._update_sequence_buttons)
        self.sequence_list.model().rowsMoved.connect(lambda *_args: self._apply_sequence_order_from_list())

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
        self._controller.current_step_changed.connect(self._on_current_step_changed)
        self._controller.last_action_changed.connect(self._on_last_action_changed)
        self._global_hotkeys.toggle_pressed.connect(self._handle_hotkey_toggle)
        self._global_hotkeys.exit_pressed.connect(self._handle_exit)
        self._global_hotkeys.emergency_pressed.connect(self._handle_emergency_stop)
        self._global_hotkeys.error_occurred.connect(self._on_controller_error)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.up_to_date.connect(self._on_update_up_to_date)
        self._update_checker.check_failed.connect(self._on_update_check_failed)
        self._hud_window.position_changed.connect(self._on_hud_position_changed)

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
        if index < 0 and combo.count() > 0:
            index = 0
        if index >= 0:
            combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def _current_combo_data(self, combo: QComboBox, default: str) -> str:
        data = combo.currentData()
        return data if isinstance(data, str) and data else default

    def _default_hud_item_order(self) -> tuple[str, ...]:
        return ("state", "step", "rate", "count", "last")

    def _selected_hud_items(self) -> tuple[str, ...]:
        items: list[str] = []
        for index in range(self.hud_order_list.count()):
            item = self.hud_order_list.item(index)
            key = item.data(Qt.UserRole)
            if isinstance(key, str) and item.checkState() == Qt.Checked:
                items.append(key)
        return tuple(items) or ("state",)

    def _rebuild_hud_order_list(self, ordered_items: tuple[str, ...] | list[str]) -> None:
        labels = get_hud_item_labels(self._language)
        seen: list[str] = []
        for key in ordered_items:
            if key in labels and key not in seen:
                seen.append(key)
        for key in self._default_hud_item_order():
            if key not in seen:
                seen.append(key)

        selected = set(ordered_items) if ordered_items else {"state"}
        self.hud_order_list.blockSignals(True)
        self.hud_order_list.clear()
        for key in seen:
            item = QListWidgetItem(labels.get(key, key), self.hud_order_list)
            item.setData(Qt.UserRole, key)
            item.setFlags(
                item.flags()
                | Qt.ItemIsUserCheckable
                | Qt.ItemIsSelectable
                | Qt.ItemIsEnabled
                | Qt.ItemIsDragEnabled
            )
            item.setCheckState(Qt.Checked if key in selected else Qt.Unchecked)
        self.hud_order_list.blockSignals(False)

    def _apply_translations(self) -> None:
        self.setWindowTitle(f"{self._display_name()} {APP_VERSION}")
        self.title_label.setText(self._display_name())
        self.subtitle_label.setText(tr(self._language, "app.hero_subtitle"))
        self.tabs.setTabText(0, tr(self._language, "tab.quick"))
        self.tabs.setTabText(1, tr(self._language, "tab.sequence"))
        self.tabs.setTabText(2, tr(self._language, "tab.runtime"))

        self.quick_hint_label.setText(tr(self._language, "hint.first_action_editor"))
        self.sequence_group.setTitle(tr(self._language, "group.sequence"))
        self.task_group.setTitle(tr(self._language, "group.task"))
        self.hotkey_group.setTitle(tr(self._language, "group.hotkey"))
        self.safety_group.setTitle(tr(self._language, "group.safety"))
        self.appearance_group.setTitle(tr(self._language, "group.appearance"))
        self.controls_group.setTitle(tr(self._language, "group.controls"))
        self.status_group.setTitle(tr(self._language, "group.status"))
        self.preset_group.setTitle(tr(self._language, "group.presets"))
        self.help_group.setTitle(tr(self._language, "group.help"))
        self.sequence_hint_label.setText(tr(self._language, "hint.sequence_tab"))
        self.quick_editor.set_language(self._language)

        self.sequence_mode_label.setText(tr(self._language, "field.sequence_mode"))
        self.sequence_note_label.setText(tr(self._language, "hint.sequence_mode"))
        self.hotkey_scope_label.setText(tr(self._language, "field.hotkey_scope"))
        self.toggle_hotkey_label.setText(tr(self._language, "field.toggle_hotkey"))
        self.exit_hotkey_label.setText(tr(self._language, "field.exit_hotkey"))
        self.hotkey_note_label.setText(tr(self._language, "hint.hotkey_scope"))
        self.toggle_hotkey_edit.setPlaceholderText(tr(self._language, "hint.hotkey_input"))
        self.exit_hotkey_edit.setPlaceholderText(tr(self._language, "hint.hotkey_input"))

        self.confirm_before_start_checkbox.setText(tr(self._language, "field.confirm_before_start"))
        self.safety_countdown_label.setText(tr(self._language, "field.safety_countdown"))
        self.safety_countdown_spin.setSuffix(tr(self._language, "suffix.seconds"))
        self.emergency_hotkey_label.setText(tr(self._language, "field.emergency_hotkey"))
        self.emergency_hotkey_value.setText(EMERGENCY_STOP_HOTKEY.display_text())
        self.safety_note_label.setText(
            f"{tr(self._language, 'hint.safety_countdown')} {tr(self._language, 'hint.emergency_hotkey')}"
        )
        self.confirm_before_start_checkbox.setToolTip(tr(self._language, "hint.confirm_before_start"))
        self.safety_countdown_spin.setToolTip(tr(self._language, "hint.safety_countdown"))

        self.theme_label.setText(tr(self._language, "field.theme"))
        self.minimize_to_tray_checkbox.setText(
            "关闭窗口时最小化到系统托盘，而不是直接退出"
            if self._language == "zh-CN"
            else "Minimize to the system tray when closing the window instead of exiting immediately"
        )
        self.auto_check_updates_checkbox.setText(tr(self._language, "field.auto_check_updates"))
        self.auto_check_updates_checkbox.setToolTip(tr(self._language, "hint.auto_check_updates"))
        self.enable_hud_checkbox.setText("启用 HUD 悬浮窗" if self._language == "zh-CN" else "Enable HUD overlay")
        self.hud_items_label.setText(tr(self._language, "field.hud_items"))
        self.hud_position_label.setText(tr(self._language, "field.hud_position"))
        self.hud_opacity_label.setText(tr(self._language, "field.hud_opacity"))
        self.hud_opacity_spin.setSuffix("%")
        self.hud_note_label.setText(f"{tr(self._language, 'hint.hud_items')} {tr(self._language, 'hint.hud_drag')}")
        self._rebuild_hud_order_list(self._overlay.hud_items)

        self.start_button.setText(tr(self._language, "button.start_resume"))
        self.pause_button.setText(tr(self._language, "button.pause"))
        self.exit_button.setText(tr(self._language, "button.exit"))
        self.add_action_button.setText(tr(self._language, "button.add_action"))
        self.edit_action_button.setText(tr(self._language, "button.edit_action"))
        self.copy_action_button.setText(tr(self._language, "button.copy_action"))
        self.delete_action_button.setText(tr(self._language, "button.delete_action"))
        self.move_up_button.setText(tr(self._language, "button.move_up"))
        self.move_down_button.setText(tr(self._language, "button.move_down"))

        self.state_label.setText(tr(self._language, "field.current_state"))
        self.current_step_label.setText(tr(self._language, "field.current_step"))
        self.actual_frequency_label.setText(tr(self._language, "field.actual_frequency"))
        self.action_count_label.setText(tr(self._language, "field.action_count"))
        self.last_action_label.setText(tr(self._language, "field.last_action"))
        self.last_action_value.setText(self._last_action_text or tr(self._language, "value.no_last_action"))
        self.target_position_label.setText(tr(self._language, "field.target_position"))
        self.summary_label.setText(tr(self._language, "field.current_summary"))

        self.current_preset_label.setText(tr(self._language, "field.current_preset"))
        self.load_preset_button.setText(tr(self._language, "button.load"))
        self.save_preset_button.setText(tr(self._language, "button.save"))
        self.save_as_preset_button.setText(tr(self._language, "button.save_as"))
        self.delete_preset_button.setText("删除预设" if self._language == "zh-CN" else "Delete Preset")
        self.import_presets_button.setText(tr(self._language, "button.import_json"))
        self.export_presets_button.setText(tr(self._language, "button.export_json"))
        self.help_browser.setHtml(build_help_html(self._language))

        self.file_menu.setTitle(tr(self._language, "menu.file"))
        self.import_action.setText(tr(self._language, "menu.file.import_presets"))
        self.export_action.setText(tr(self._language, "menu.file.export_presets"))
        self.exit_action.setText(tr(self._language, "menu.file.exit"))
        self.language_menu.setTitle(tr(self._language, "menu.language"))
        self.help_menu.setTitle(tr(self._language, "menu.help"))
        self.help_action.setText(tr(self._language, "menu.help.usage"))
        self.check_updates_action.setText(tr(self._language, "menu.help.check_updates"))
        self.feedback_action.setText(tr(self._language, "menu.help.feedback"))
        for code, action in self.language_actions.items():
            action.setChecked(code == self._language)
        if self.tray_icon is not None:
            self.tray_show_action.setText(tr(self._language, "tray.show_window"))
            self.tray_toggle_action.setText(tr(self._language, "tray.start_pause"))
            self.tray_pause_action.setText(tr(self._language, "tray.pause"))
            self.tray_exit_action.setText(tr(self._language, "tray.exit"))

        self._set_combo_items(self.sequence_mode_combo, list(get_sequence_mode_labels(self._language).items()), self._settings.sequence_mode)
        self._set_combo_items(self.hotkey_scope_combo, list(get_hotkey_scope_labels(self._language).items()), self._settings.hotkey_scope)
        self._set_combo_items(self.theme_combo, list(get_theme_labels(self._language).items()), self.theme)

    def _load_initial_state(self) -> None:
        if not self._presets:
            name = self._default_preset_name()
            self._presets[name] = Preset(name=name, settings=AppSettings())
        self._rebuild_preset_combo(self._persisted_state.selected_preset or self._default_preset_name())
        self._apply_settings_to_form(self._settings)
        self._apply_overlay_to_form()
        self._loading = True
        try:
            self.auto_check_updates_checkbox.setChecked(self._persisted_state.auto_check_updates)
        finally:
            self._loading = False
        self.statusBar().showMessage(tr(self._language, "status.ready"))

    def _apply_settings_to_form(self, settings: AppSettings) -> None:
        self._loading = True
        try:
            self._settings = AppSettings.from_dict(settings.to_dict())
            self.quick_editor.set_action(self._settings.first_action())
            self._set_combo_items(self.sequence_mode_combo, list(get_sequence_mode_labels(self._language).items()), self._settings.sequence_mode)
            self._set_combo_items(self.hotkey_scope_combo, list(get_hotkey_scope_labels(self._language).items()), self._settings.hotkey_scope)
            self.toggle_hotkey_edit.set_hotkey(self._settings.toggle_hotkey)
            self.exit_hotkey_edit.set_hotkey(self._settings.exit_hotkey)
            self.minimize_to_tray_checkbox.setChecked(self._settings.minimize_to_tray)
            self.confirm_before_start_checkbox.setChecked(self._settings.confirm_before_start)
            self.safety_countdown_spin.setValue(self._settings.safety_countdown_seconds)
        finally:
            self._loading = False
        self._refresh_sequence_list()

    def _apply_overlay_to_form(self) -> None:
        self._loading = True
        try:
            self.enable_hud_checkbox.setChecked(self._overlay.hud_enabled)
            self.hud_x_spin.setValue(self._overlay.hud_x)
            self.hud_y_spin.setValue(self._overlay.hud_y)
            self.hud_opacity_spin.setValue(self._overlay.hud_opacity_percent)
            self._rebuild_hud_order_list(self._overlay.hud_items)
        finally:
            self._loading = False

    def _current_settings(self) -> AppSettings:
        settings = AppSettings.from_dict(self._settings.to_dict())
        settings.sequence_mode = self._current_combo_data(self.sequence_mode_combo, "once")
        settings.hotkey_scope = self._current_combo_data(self.hotkey_scope_combo, "global")
        settings.toggle_hotkey = self.toggle_hotkey_edit.hotkey()
        settings.exit_hotkey = self.exit_hotkey_edit.hotkey()
        settings.minimize_to_tray = self.minimize_to_tray_checkbox.isChecked()
        settings.confirm_before_start = self.confirm_before_start_checkbox.isChecked()
        settings.safety_countdown_seconds = self.safety_countdown_spin.value()
        settings.actions[0] = self.quick_editor.action_unit()
        return settings.normalized()

    def _collect_overlay(self):
        overlay = type(self._overlay).from_dict(
            {
                "hud_enabled": self.enable_hud_checkbox.isChecked(),
                "hud_items": list(self._selected_hud_items()),
                "hud_x": self.hud_x_spin.value(),
                "hud_y": self.hud_y_spin.value(),
                "hud_opacity_percent": self.hud_opacity_spin.value(),
            }
        )
        return overlay

    def _refresh_form_state(self) -> None:
        self._settings = self._current_settings()
        self._overlay = self._collect_overlay()
        self._validation = validate_settings(self._settings, self._language)
        self.quick_editor.set_allow_infinite(len(self._settings.actions) <= 1)
        self.quick_editor.apply_validation(self._validation.action_errors(0))
        _set_widget_error(self.sequence_mode_combo, self._validation.first_message_for("sequence_mode"))
        _set_widget_error(self.hotkey_scope_combo, self._validation.first_message_for("hotkey_scope"))
        _set_widget_error(self.toggle_hotkey_edit, self._validation.first_message_for("toggle_hotkey"))
        _set_widget_error(self.exit_hotkey_edit, self._validation.first_message_for("exit_hotkey"))
        _set_widget_error(self.safety_countdown_spin, self._validation.first_message_for("safety_countdown_seconds"))
        self.validation_label.setText("\n".join(self._validation.messages()))
        self._refresh_sequence_list()
        self._update_summary()
        self._configure_hotkeys()
        self._save_persisted_state()
        self._on_state_changed(self._controller.state)
        self._sync_hud()

    def _refresh_sequence_list(self) -> None:
        selected_indices = set(self._selected_action_indices())
        selected = self.sequence_list.currentRow()
        self.sequence_list.blockSignals(True)
        self.sequence_list.clear()
        for index, action in enumerate(self._settings.actions):
            label = action.name or format_action_unit_label(action, self._language)
            item = QListWidgetItem(f"{index + 1}. {label}\n   {summarize_action_unit(action, self._language)}")
            item.setData(Qt.UserRole, index)
            item.setToolTip(action.name or format_action_unit_label(action, self._language))
            item.setSizeHint(QSize(0, 58))
            self.sequence_list.addItem(item)
            if index in selected_indices:
                item.setSelected(True)
        if self.sequence_list.count() > 0 and not selected_indices:
            self.sequence_list.setCurrentRow(min(max(selected, 0), self.sequence_list.count() - 1))
        self.sequence_list.blockSignals(False)
        self._update_sequence_buttons()

    def _update_summary(self) -> None:
        first = self._settings.first_action()
        scope_text = get_hotkey_scope_labels(self._language).get(self._settings.hotkey_scope, "")
        mode_text = get_sequence_mode_labels(self._language).get(self._settings.sequence_mode, "")
        self.summary_value.setText(
            tr(
                self._language,
                "summary.full",
                mode=mode_text,
                count=len(self._settings.actions),
                toggle=self._settings.toggle_hotkey.display_text() or tr(self._language, "summary.not_set"),
                exit=self._settings.exit_hotkey.display_text() or tr(self._language, "summary.not_set"),
                scope=scope_text,
            )
        )
        if first.action_mode == "keyboard":
            self.target_value.setText(tr(self._language, "target_value.keyboard_mode"))
        elif first.target_mode == "fixed":
            self.target_value.setText(tr(self._language, "target_value.fixed", x=first.fixed_x, y=first.fixed_y))
        elif self._current_target is None:
            self.target_value.setText(tr(self._language, "target_value.capture_pending"))
        else:
            self.target_value.setText(tr(self._language, "target_value.captured", x=self._current_target[0], y=self._current_target[1]))
        if self._current_step_index >= 0:
            step_text = tr(self._language, "value.step_index", index=self._current_step_index + 1, total=len(self._settings.actions))
            if self._current_step_text:
                step_text = f"{step_text} - {self._current_step_text}"
            self.current_step_value.setText(step_text)
        else:
            self.current_step_value.setText(tr(self._language, "value.no_step"))

    def _configure_hotkeys(self) -> None:
        self._clear_local_shortcuts()
        self._global_hotkeys.stop()
        if not self._validation.is_valid:
            self._global_hotkeys.configure(None, None, self._language, emergency_hotkey=EMERGENCY_STOP_HOTKEY)
            return
        if self._settings.hotkey_scope == "global":
            self._global_hotkeys.configure(
                self._settings.toggle_hotkey,
                self._settings.exit_hotkey,
                self._language,
                emergency_hotkey=EMERGENCY_STOP_HOTKEY,
            )
            return
        self._global_hotkeys.configure(None, None, self._language, emergency_hotkey=EMERGENCY_STOP_HOTKEY)
        toggle_shortcut = QShortcut(QKeySequence(self._settings.toggle_hotkey.display_text()), self)
        toggle_shortcut.activated.connect(self._handle_hotkey_toggle)
        exit_shortcut = QShortcut(QKeySequence(self._settings.exit_hotkey.display_text()), self)
        exit_shortcut.activated.connect(self._handle_exit)
        self._local_shortcuts = [toggle_shortcut, exit_shortcut]

    def _clear_local_shortcuts(self) -> None:
        for shortcut in self._local_shortcuts:
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        self._local_shortcuts = []

    def _selected_action_index(self) -> int:
        item = self.sequence_list.currentItem()
        if item is None:
            return -1
        data = item.data(Qt.UserRole)
        return int(data) if isinstance(data, int) else -1

    def _selected_action_indices(self) -> list[int]:
        indices: list[int] = []
        for item in self.sequence_list.selectedItems():
            data = item.data(Qt.UserRole)
            if isinstance(data, int):
                indices.append(data)
        return sorted(set(indices))

    def _sequence_order_from_list(self) -> list[int]:
        order: list[int] = []
        for row in range(self.sequence_list.count()):
            data = self.sequence_list.item(row).data(Qt.UserRole)
            if isinstance(data, int):
                order.append(data)
        return order

    def _apply_sequence_order_from_list(self) -> None:
        if self._loading:
            return
        order = self._sequence_order_from_list()
        if sorted(order) != list(range(len(self._settings.actions))):
            return
        self._settings = self._current_settings()
        self._settings.actions = [self._settings.actions[index] for index in order]
        self.quick_editor.set_action(self._settings.first_action())
        self._refresh_form_state()
        self._on_status_changed(tr(self._language, "status.sequence_updated"))

    def _default_new_action(self, index: int):
        action = default_action_unit(index)
        action.name = ("主动作" if index == 0 else f"步骤 {index + 1}") if self._language == "zh-CN" else ("Primary Action" if index == 0 else f"Step {index + 1}")
        return action

    def _update_sequence_buttons(self) -> None:
        indices = self._selected_action_indices()
        index = indices[0] if len(indices) == 1 else -1
        count = len(self._settings.actions)
        editable = self._controller_state in {"idle", "paused"}
        self.add_action_button.setEnabled(editable)
        self.edit_action_button.setEnabled(editable and len(indices) == 1)
        self.copy_action_button.setEnabled(editable and bool(indices))
        self.delete_action_button.setEnabled(editable and bool(indices))
        self.move_up_button.setEnabled(editable and index > 0)
        self.move_down_button.setEnabled(editable and index >= 0 and index < count - 1)

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

    def _hud_lines(self) -> list[str]:
        lines: list[str] = []
        for key in self._overlay.hud_items:
            if key == "state":
                lines.append(f"{tr(self._language, 'field.current_state')}: {tr(self._language, f'state.{self._controller_state}')}")
            elif key == "step":
                lines.append(f"{tr(self._language, 'field.current_step')}: {self.current_step_value.text()}")
            elif key == "rate":
                lines.append(f"{tr(self._language, 'field.actual_frequency')}: {tr(self._language, 'value.actual_frequency', frequency=self._actual_frequency)}")
            elif key == "count":
                lines.append(f"{tr(self._language, 'field.action_count')}: {self._action_count}")
            elif key == "last":
                lines.append(f"{tr(self._language, 'field.last_action')}: {self._last_action_text or tr(self._language, 'value.no_last_action')}")
        return lines

    def _sync_hud(self) -> None:
        self._hud_window.update_content(
            lines=self._hud_lines(),
            x=self._overlay.hud_x,
            y=self._overlay.hud_y,
            visible=self._overlay.hud_enabled,
            opacity_percent=self._overlay.hud_opacity_percent,
        )

    def _prepare_for_start(self) -> None:
        first = self._settings.first_action()
        if first.action_mode == "mouse" and first.target_mode == "capture":
            self._current_target = None
            self.target_value.setText(tr(self._language, "target_value.waiting_capture"))

    def _confirm_start_if_needed(self) -> bool:
        if not self._settings.confirm_before_start:
            return True
        return (
            QMessageBox.question(
                self,
                tr(self._language, "dialog.start_confirm_title"),
                tr(
                    self._language,
                    "dialog.start_confirm_message",
                    emergency=EMERGENCY_STOP_HOTKEY.display_text(),
                ),
            )
            == QMessageBox.Yes
        )

    def _start_current_settings(self, *, show_error_dialog: bool) -> None:
        self._refresh_form_state()
        if not self._validation.is_valid:
            if show_error_dialog:
                QMessageBox.warning(self, self._display_name(), "\n".join(self._validation.messages()))
            else:
                self._on_status_changed(tr(self._language, "status.fix_errors_before_hotkey"))
            return
        if not self._confirm_start_if_needed():
            self._on_status_changed(tr(self._language, "status.start_cancelled"))
            return
        self._prepare_for_start()
        self._controller.start(self._settings, self._language)

    def _handle_start_resume(self) -> None:
        self._start_current_settings(show_error_dialog=True)

    def _handle_pause(self) -> None:
        self._controller.pause()

    def _handle_hotkey_toggle(self) -> None:
        if self._controller.state in {"running", "countdown"}:
            self._controller.pause()
            return
        self._start_current_settings(show_error_dialog=False)

    def _handle_exit(self) -> None:
        self._force_quit = True
        self._save_persisted_state()
        self._controller.shutdown()
        self._clear_local_shortcuts()
        self._global_hotkeys.stop()
        self._hud_window.hide()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _handle_emergency_stop(self) -> None:
        self.statusBar().showMessage(tr(self._language, "status.emergency_stop", hotkey=EMERGENCY_STOP_HOTKEY.display_text()))
        self._handle_exit()

    def _set_language(self, language: str) -> None:
        if self._loading:
            return
        self._language = normalize_language(language)
        self._controller.set_language(self._language)
        self._apply_translations()
        self._refresh_form_state()

    def _set_theme(self, theme: str) -> None:
        self.theme = theme
        apply_theme(QApplication.instance(), theme)
        self._save_persisted_state()
        self._on_status_changed(tr(self._language, "status.theme_changed"))

    def _on_theme_combo_changed(self, *_args) -> None:
        if self._loading:
            return
        self._set_theme(self._current_combo_data(self.theme_combo, self.theme))
        self._on_form_changed()

    def _on_form_changed(self, *_args) -> None:
        if self._loading:
            return
        if self._controller.state in {"idle", "paused"}:
            self._current_target = None
        self._refresh_form_state()

    def _on_hud_item_changed(self, *_args) -> None:
        if self._loading:
            return
        if self._selected_hud_items():
            self._on_form_changed()
            return
        self._loading = True
        try:
            if self.hud_order_list.count() > 0:
                self.hud_order_list.item(0).setCheckState(Qt.Checked)
        finally:
            self._loading = False
        self._on_form_changed()

    def _on_state_changed(self, state: str) -> None:
        self._controller_state = state
        self.state_value.setText(tr(self._language, f"state.{state}"))
        editable = state in {"idle", "paused"}
        can_start = editable and self._validation.is_valid
        self.start_button.setEnabled(can_start)
        self.pause_button.setEnabled(state in {"running", "countdown"})
        self.quick_editor.setEnabled(editable)
        self.sequence_mode_combo.setEnabled(editable)
        self.hotkey_scope_combo.setEnabled(editable)
        self.toggle_hotkey_edit.setEnabled(editable)
        self.exit_hotkey_edit.setEnabled(editable)
        self.confirm_before_start_checkbox.setEnabled(editable)
        self.safety_countdown_spin.setEnabled(editable)
        self.theme_combo.setEnabled(editable)
        self.minimize_to_tray_checkbox.setEnabled(editable)
        self.auto_check_updates_checkbox.setEnabled(editable)
        self.enable_hud_checkbox.setEnabled(editable)
        self.hud_x_spin.setEnabled(editable and self.enable_hud_checkbox.isChecked())
        self.hud_y_spin.setEnabled(editable and self.enable_hud_checkbox.isChecked())
        self.hud_opacity_spin.setEnabled(editable and self.enable_hud_checkbox.isChecked())
        self.hud_order_list.setEnabled(editable and self.enable_hud_checkbox.isChecked())
        if self.tray_icon is not None:
            self.tray_toggle_action.setEnabled(self._validation.is_valid or state in {"running", "countdown"})
            self.tray_pause_action.setEnabled(state in {"running", "countdown"})
        self._update_sequence_buttons()
        self._sync_hud()

    def _on_status_changed(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _on_position_captured(self, x: int, y: int) -> None:
        self._current_target = (x, y)
        self._update_summary()
        self._sync_hud()

    def _on_action_count_changed(self, count: int) -> None:
        self._action_count = count
        self.action_count_value.setText(str(count))
        self._sync_hud()

    def _on_last_action_changed(self, text: str) -> None:
        self._last_action_text = text
        self.last_action_value.setText(text or tr(self._language, "value.no_last_action"))
        self._sync_hud()

    def _on_actual_frequency_changed(self, frequency: float) -> None:
        self._actual_frequency = max(frequency, 0.0)
        self.actual_frequency_value.setText(tr(self._language, "value.actual_frequency", frequency=self._actual_frequency))
        self._sync_hud()

    def _on_current_step_changed(self, index: int, step_text: str) -> None:
        self._current_step_index = index
        self._current_step_text = step_text
        self._update_summary()
        self._sync_hud()

    def _on_controller_error(self, message: str) -> None:
        QMessageBox.warning(self, self._display_name(), message)
        self.statusBar().showMessage(message)

    def _on_cursor_failed(self) -> None:
        QMessageBox.warning(self, self._display_name(), tr(self._language, "dialog.cursor_failed"))

    def _on_hud_position_changed(self, x: int, y: int) -> None:
        if self._loading:
            return
        self._loading = True
        try:
            self.hud_x_spin.setValue(x)
            self.hud_y_spin.setValue(y)
        finally:
            self._loading = False
        self._on_form_changed()

    def _add_action(self) -> None:
        self._settings = self._current_settings()
        dialog = ActionUnitDialog(
            language=self._language,
            title=tr(self._language, "dialog.add_action"),
            action=self._default_new_action(len(self._settings.actions)),
            allow_infinite=False,
            backend=self._input_backend,
            parent=self,
        )
        if not dialog.exec():
            return
        self._settings.actions.append(dialog.action_unit())
        self._apply_settings_to_form(self._settings)
        self._refresh_form_state()
        self.sequence_list.setCurrentRow(len(self._settings.actions) - 1)

    def _edit_selected_action(self) -> None:
        self._settings = self._current_settings()
        index = self._selected_action_index()
        if index < 0:
            QMessageBox.information(self, self._display_name(), tr(self._language, "dialog.sequence_empty"))
            return
        dialog = ActionUnitDialog(
            language=self._language,
            title=tr(self._language, "dialog.edit_action"),
            action=self._settings.actions[index],
            allow_infinite=index == 0 and len(self._settings.actions) == 1,
            backend=self._input_backend,
            parent=self,
        )
        if not dialog.exec():
            return
        self._settings.actions[index] = dialog.action_unit()
        self._apply_settings_to_form(self._settings)
        self._refresh_form_state()
        self.sequence_list.setCurrentRow(index)

    def _copy_selected_action(self) -> None:
        self._settings = self._current_settings()
        indices = self._selected_action_indices()
        if not indices:
            return
        clones = []
        for index in indices:
            clone = type(self._settings.actions[index]).from_dict(
                self._settings.actions[index].to_dict(),
                index=len(self._settings.actions) + len(clones),
            )
            if clone.limit_mode == "infinite":
                clone.limit_mode = "count"
            if clone.name:
                clone.name = clone.name + tr(self._language, "label.copy_suffix")
            else:
                clone.name = tr(self._language, "label.copied_action")
            clones.append(clone)
        insert_at = indices[-1] + 1
        self._settings.actions[insert_at:insert_at] = clones
        self._apply_settings_to_form(self._settings)
        self._refresh_form_state()
        self.sequence_list.clearSelection()
        for row in range(insert_at, insert_at + len(clones)):
            item = self.sequence_list.item(row)
            if item is not None:
                item.setSelected(True)
        self.sequence_list.setCurrentRow(insert_at)

    def _delete_selected_action(self) -> None:
        self._settings = self._current_settings()
        indices = self._selected_action_indices()
        if not indices:
            return
        if len(indices) == 1:
            name = self._settings.actions[indices[0]].name or format_action_unit_label(
                self._settings.actions[indices[0]],
                self._language,
            )
            message = tr(self._language, "dialog.delete_action", name=name)
        else:
            message = tr(self._language, "dialog.delete_actions", count=len(indices))
        if QMessageBox.question(self, self._display_name(), message) != QMessageBox.Yes:
            return
        for index in reversed(indices):
            self._settings.actions.pop(index)
        if not self._settings.actions:
            self._settings.actions = [default_action_unit(0)]
        self._apply_settings_to_form(self._settings)
        self._refresh_form_state()

    def _move_action(self, delta: int) -> None:
        self._settings = self._current_settings()
        index = self._selected_action_index()
        target = index + delta
        if index < 0 or target < 0 or target >= len(self._settings.actions):
            return
        self._settings.actions[index], self._settings.actions[target] = self._settings.actions[target], self._settings.actions[index]
        self._apply_settings_to_form(self._settings)
        self._refresh_form_state()
        self.sequence_list.setCurrentRow(target)

    def _load_selected_preset(self) -> None:
        preset = self._presets.get(self.preset_combo.currentText())
        if preset is None:
            return
        self._apply_settings_to_form(preset.settings)
        self._refresh_form_state()
        self._on_status_changed(tr(self._language, "status.loaded_preset", name=preset.name))

    def _save_current_preset(self) -> None:
        self._settings = self._current_settings()
        name = self.preset_combo.currentText().strip() or self._default_preset_name()
        self._presets[name] = Preset(name=name, settings=self._settings, updated_at=datetime.now().isoformat(timespec="seconds"))
        self._rebuild_preset_combo(name)
        self._save_persisted_state()
        self._on_status_changed(tr(self._language, "status.saved_preset", name=name))

    def _save_preset_as(self) -> None:
        name, accepted = QInputDialog.getText(self, self._display_name(), tr(self._language, "dialog.preset_name"))
        name = name.strip()
        if not accepted or not name:
            return
        self._settings = self._current_settings()
        self._presets[name] = Preset(name=name, settings=self._settings, updated_at=datetime.now().isoformat(timespec="seconds"))
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
            fallback = self._default_preset_name()
            self._presets[fallback] = Preset(name=fallback, settings=AppSettings())
        next_name = sorted(self._presets)[0]
        self._rebuild_preset_combo(next_name)
        self._save_persisted_state()

    def _import_presets(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, self._display_name(), "", tr(self._language, "dialog.json_filter"))
        if not path:
            return
        try:
            presets = self._store.import_presets(path, self._language)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, self._display_name(), tr(self._language, "dialog.import_failed", error=exc))
            return
        for preset in presets:
            self._presets[preset.name] = preset
        self._rebuild_preset_combo(self.preset_combo.currentText() or self._default_preset_name())
        self._save_persisted_state()

    def _export_presets(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, self._display_name(), tr(self._language, "dialog.presets_file_name"), tr(self._language, "dialog.json_filter"))
        if not path:
            return
        try:
            self._store.export_presets(path, list(self._presets.values()))
        except OSError as exc:
            QMessageBox.warning(self, self._display_name(), tr(self._language, "dialog.export_failed", error=exc))
            return
        self._on_status_changed(tr(self._language, "status.exported_presets", path=path))

    def _check_for_updates(self, *, manual: bool) -> None:
        if manual:
            self._on_status_changed(tr(self._language, "status.update_checking"))
        self._update_checker.check_async(APP_VERSION)

    def _on_update_available(self, version: str, url: str, name: str) -> None:
        self._on_status_changed(tr(self._language, "status.update_available", version=version))
        if not url:
            return
        if (
            QMessageBox.question(
                self,
                tr(self._language, "dialog.update_available_title"),
                tr(self._language, "dialog.update_available_message", version=version, url=url),
            )
            == QMessageBox.Yes
        ):
            QDesktopServices.openUrl(QUrl(url))

    def _on_update_up_to_date(self, version: str) -> None:
        self._on_status_changed(tr(self._language, "status.update_not_available", version=version))

    def _on_update_check_failed(self, error: str) -> None:
        self._on_status_changed(tr(self._language, "status.update_check_failed", error=error))

    def _open_feedback_page(self) -> None:
        QDesktopServices.openUrl(QUrl("https://github.com/GJYNBB/ProAutoClicker/issues"))

    def _save_persisted_state(self) -> None:
        if self._loading:
            return
        self._persisted_state = PersistedState(
            language=self._language,
            theme=self.theme,
            selected_preset=self.preset_combo.currentText() or self._default_preset_name(),
            auto_check_updates=self.auto_check_updates_checkbox.isChecked(),
            last_settings=self._current_settings(),
            overlay=self._collect_overlay(),
            presets=list(self._presets.values()),
        )
        try:
            self._store.save(self._persisted_state)
        except OSError as exc:
            self.statusBar().showMessage(tr(self._language, "status.save_config_failed", error=exc))

    def _show_help_dialog(self) -> None:
        QMessageBox.information(self, tr(self._language, "dialog.help_title", app_name=self._display_name()), self.help_browser.toPlainText())

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
