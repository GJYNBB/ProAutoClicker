from __future__ import annotations

from PySide6.QtWidgets import QApplication

THEMES = {
    "light": {
        "window": "#edf3fb",
        "card": "#ffffff",
        "card_alt": "#f8fbff",
        "text": "#13263a",
        "muted": "#52667a",
        "border": "#d5dee7",
        "focus": "#f97316",
        "primary": "#f97316",
        "primary_hover": "#ea580c",
        "success": "#16a34a",
        "success_bg": "#dcfce7",
        "warning": "#d97706",
        "warning_bg": "#fef3c7",
        "danger_bg": "#fff1f2",
        "danger_text": "#b42318",
        "danger_border": "#fda4af",
        "disabled_bg": "#eef2f6",
        "disabled_text": "#7b8a9a",
        "status_bg": "#102a43",
        "status_text": "#ffffff",
        "tab_bg": "#ffffff",
        "tab_inactive": "#dbe6f0",
    },
    "dark": {
        "window": "#1c2128",
        "card": "#22272e",
        "card_alt": "#2d333b",
        "text": "#e6edf3",
        "muted": "#9da7b3",
        "border": "#373e47",
        "focus": "#fb923c",
        "primary": "#f97316",
        "primary_hover": "#ea580c",
        "success": "#22c55e",
        "success_bg": "#16351f",
        "warning": "#fbbf24",
        "warning_bg": "#3d2f12",
        "danger_bg": "#38252a",
        "danger_text": "#fecdd3",
        "danger_border": "#6b3039",
        "disabled_bg": "#2a3038",
        "disabled_text": "#7b8694",
        "status_bg": "#171b21",
        "status_text": "#e6edf3",
        "tab_bg": "#22272e",
        "tab_inactive": "#2a3038",
    },
}


def build_stylesheet(theme: str = "light") -> str:
    palette = THEMES.get(theme, THEMES["light"])
    error_background = "#fff7f7" if theme == "light" else "#33161b"
    return f"""
QMainWindow {{
    background: {palette["window"]};
}}
QWidget {{
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
    font-size: 10.5pt;
    color: {palette["text"]};
}}
QLabel#heroTitle {{
    color: {palette["text"]};
    font-size: 28px;
    font-weight: 700;
}}
QLabel#heroSubtitle {{
    color: {palette["muted"]};
    font-size: 10.5pt;
}}
QTabWidget::pane {{
    border: 1px solid {palette["border"]};
    border-radius: 16px;
    background: {palette["card"]};
    top: -1px;
}}
QWidget#tabPage, QWidget#scrollContent, QWidget#scrollViewport {{
    background: transparent;
}}
QTabBar::tab {{
    background: {palette["tab_inactive"]};
    border: 1px solid {palette["border"]};
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 8px 16px;
    margin-right: 6px;
    color: {palette["muted"]};
}}
QTabBar::tab:selected {{
    background: {palette["tab_bg"]};
    color: {palette["text"]};
}}
QGroupBox {{
    background: {palette["card"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
    margin-top: 18px;
    font-weight: 600;
    padding-top: 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 1px;
    padding: 0 8px;
    color: {palette["text"]};
    background: {palette["window"]};
    border-radius: 8px;
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextBrowser, QListWidget {{
    background: {palette["card_alt"]};
    border: 1px solid {palette["border"]};
    border-radius: 6px;
    min-height: 24px;
    padding: 6px 10px;
    selection-background-color: {palette["focus"]};
    selection-color: #ffffff;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextBrowser:focus, QListWidget:focus {{
    border: 1px solid {palette["focus"]};
}}
QLineEdit[errorState="true"], QComboBox[errorState="true"], QSpinBox[errorState="true"], QDoubleSpinBox[errorState="true"], QListWidget[errorState="true"] {{
    border: 1px solid #ef4444;
    background: {error_background};
}}
QTextBrowser {{
    padding: 12px;
}}
QListWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid {palette["border"]};
}}
QListWidget::item:selected {{
    background: {palette["tab_inactive"]};
    color: {palette["text"]};
}}
QPushButton {{
    background: {palette["card"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
    min-height: 28px;
    padding: 7px 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    border-color: {palette["focus"]};
}}
QPushButton#primaryButton {{
    background: {palette["primary"]};
    color: #ffffff;
    border-color: {palette["primary"]};
}}
QPushButton#primaryButton:hover {{
    background: {palette["primary_hover"]};
}}
QPushButton#dangerButton {{
    background: {palette["danger_bg"]};
    color: {palette["danger_text"]};
    border-color: {palette["danger_border"]};
}}
QPushButton:disabled {{
    background: {palette["disabled_bg"]};
    color: {palette["disabled_text"]};
    border-color: {palette["border"]};
}}
QFrame#settingsCard, QFrame#statusPanel, QFrame#actionBar, QFrame#topBar {{
    background: {palette["card"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
}}
QLabel#cardTitle {{
    font-size: 14pt;
    font-weight: 700;
    color: {palette["text"]};
}}
QFrame#collapsibleSection {{
    background: transparent;
    border: none;
}}
QPushButton#collapsibleToggle {{
    background: {palette["card"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
    padding: 8px 12px;
    text-align: left;
}}
QPushButton#collapsibleToggle:checked {{
    border-color: {palette["focus"]};
}}
QFrame#statusPanel {{
    background: {palette["card_alt"]};
}}
QLabel#stateIndicator {{
    background: {palette["tab_inactive"]};
    border-radius: 8px;
    color: {palette["text"]};
    font-size: 14pt;
    font-weight: 700;
    padding: 10px 12px;
}}
QLabel#stateIndicator[state_idle="true"] {{
    background: {palette["tab_inactive"]};
    color: {palette["text"]};
}}
QLabel#stateIndicator[state_running="true"] {{
    background: {palette["success_bg"]};
    color: {palette["success"]};
    border: 1px solid {palette["success"]};
}}
QLabel#stateIndicator[state_paused="true"] {{
    background: {palette["warning_bg"]};
    color: {palette["warning"]};
    border: 1px solid {palette["warning"]};
}}
QLabel#stateIndicator[state_countdown="true"] {{
    background: {palette["danger_bg"]};
    color: {palette["danger_text"]};
    border: 1px solid {palette["danger_border"]};
}}
QFrame#statusSeparator {{
    color: {palette["border"]};
}}
QLabel#statusFieldLabel {{
    color: {palette["muted"]};
    font-size: 9pt;
}}
QLabel#statusFieldValue {{
    color: {palette["text"]};
    font-weight: 600;
}}
QFrame#actionBar {{
    border-radius: 8px;
}}
QLabel#validationLabel {{
    color: {palette["danger_text"]};
    font-size: 9pt;
}}
QLabel#validationLabel[severity="warning"] {{
    color: {palette["warning"]};
}}
QLabel#validationLabel[severity="success"] {{
    color: {palette["success"]};
}}
QWidget#taskSelector {{
    background: transparent;
}}
QPushButton#taskSegment {{
    background: {palette["tab_inactive"]};
    border: 1px solid {palette["border"]};
    border-radius: 8px;
    color: {palette["muted"]};
    min-height: 36px;
    padding: 8px 14px;
}}
QPushButton#taskSegment:checked {{
    background: {palette["primary"]};
    border-color: {palette["primary"]};
    color: #ffffff;
}}
QPushButton#taskSegment:hover {{
    border-color: {palette["focus"]};
}}
QPushButton#topBarIconButton {{
    min-width: 40px;
}}
QCheckBox {{
    spacing: 8px;
}}
QMenuBar {{
    background: {palette["window"]};
    color: {palette["text"]};
    padding: 4px 8px;
}}
QMenuBar::item {{
    padding: 6px 10px;
    border-radius: 8px;
}}
QMenuBar::item:selected {{
    background: {palette["tab_inactive"]};
}}
QMenu {{
    background: {palette["card"]};
    color: {palette["text"]};
    border: 1px solid {palette["border"]};
}}
QMenu::item:selected {{
    background: {palette["tab_inactive"]};
}}
QStatusBar {{
    background: {palette["status_bg"]};
    color: {palette["status_text"]};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
"""


def apply_theme(app: QApplication | None, theme: str) -> None:
    if app is None:
        return
    app.setStyleSheet(build_stylesheet(theme))
