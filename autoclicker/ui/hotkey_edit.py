from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit

from autoclicker.models import KeyCombo

SPECIAL_KEYS = {
    Qt.Key_Space: "Space",
    Qt.Key_Return: "Enter",
    Qt.Key_Enter: "Enter",
    Qt.Key_Tab: "Tab",
    Qt.Key_Escape: "Esc",
    Qt.Key_Backspace: "Backspace",
    Qt.Key_Delete: "Delete",
    Qt.Key_Insert: "Insert",
    Qt.Key_Home: "Home",
    Qt.Key_End: "End",
    Qt.Key_PageUp: "PageUp",
    Qt.Key_PageDown: "PageDown",
    Qt.Key_Left: "Left",
    Qt.Key_Right: "Right",
    Qt.Key_Up: "Up",
    Qt.Key_Down: "Down",
}


class HotkeyLineEdit(QLineEdit):
    hotkey_changed = Signal(object)

    def __init__(self, parent=None, *, allow_empty: bool = False) -> None:
        super().__init__(parent)
        self._allow_empty = allow_empty
        self._hotkey = KeyCombo()
        self.setReadOnly(True)
        self.setPlaceholderText("")

    def hotkey(self) -> KeyCombo:
        return self._hotkey

    def set_hotkey(self, hotkey: KeyCombo) -> None:
        self._hotkey = hotkey.normalized()
        self.setText(self._hotkey.display_text())
        self.hotkey_changed.emit(self._hotkey)

    def clear_hotkey(self) -> None:
        self._hotkey = KeyCombo()
        self.clear()
        self.hotkey_changed.emit(self._hotkey)

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        key = event.key()
        if key in {Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta}:
            event.accept()
            return

        if key in {Qt.Key_Backspace, Qt.Key_Delete} and self._allow_empty:
            self.clear_hotkey()
            event.accept()
            return

        key_name = self._qt_key_to_name(key)
        if not key_name:
            event.ignore()
            return

        modifiers = []
        qt_modifiers = event.modifiers()
        if qt_modifiers & Qt.ControlModifier:
            modifiers.append("Ctrl")
        if qt_modifiers & Qt.AltModifier:
            modifiers.append("Alt")
        if qt_modifiers & Qt.ShiftModifier:
            modifiers.append("Shift")
        if qt_modifiers & Qt.MetaModifier:
            modifiers.append("Win")

        self.set_hotkey(KeyCombo(key=key_name, modifiers=tuple(modifiers)))
        event.accept()

    def _qt_key_to_name(self, key: int) -> str:
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key)
        if Qt.Key_0 <= key <= Qt.Key_9:
            return chr(key)
        if Qt.Key_F1 <= key <= Qt.Key_F24:
            return f"F{key - Qt.Key_F1 + 1}"
        return SPECIAL_KEYS.get(key, "")
