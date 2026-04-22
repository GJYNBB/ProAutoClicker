from __future__ import annotations

import sys
from abc import ABC, abstractmethod

from PySide6.QtCore import QObject, Signal

from autoclicker.i18n import normalize_language, tr
from autoclicker.models import EMERGENCY_STOP_HOTKEY, KeyCombo


class HotkeyManager(QObject):
    toggle_pressed = Signal()
    exit_pressed = Signal()
    emergency_pressed = Signal()
    error_occurred = Signal(str)

    def configure(
        self,
        toggle_hotkey: KeyCombo | None,
        exit_hotkey: KeyCombo | None,
        language: str | None = None,
        *,
        emergency_hotkey: KeyCombo | None = EMERGENCY_STOP_HOTKEY,
    ) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class InputBackend(ABC):
    name = "base"
    supports_global_hotkeys = False

    @abstractmethod
    def get_cursor_position(self) -> tuple[int, int] | None:
        raise NotImplementedError

    @abstractmethod
    def click_mouse(self, button: str, x: int, y: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def mouse_down(self, button: str, x: int, y: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def mouse_up(self, button: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_key_combo(self, combo: KeyCombo, language: str | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def key_combo_down(self, combo: KeyCombo, language: str | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def key_combo_up(self, combo: KeyCombo, language: str | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_hotkey_manager(self) -> HotkeyManager:
        raise NotImplementedError


class UnsupportedHotkeyManager(HotkeyManager):
    def __init__(self, platform_name: str) -> None:
        super().__init__()
        self._platform_name = platform_name
        self._reported = False

    def configure(
        self,
        toggle_hotkey: KeyCombo | None,
        exit_hotkey: KeyCombo | None,
        language: str | None = None,
        *,
        emergency_hotkey: KeyCombo | None = EMERGENCY_STOP_HOTKEY,
    ) -> None:
        if self._reported:
            return
        self._reported = True
        locale_key = normalize_language(language)
        self.error_occurred.emit(tr(locale_key, "error.unsupported_platform", platform=self._platform_name))

    def stop(self) -> None:
        return


class UnsupportedInputBackend(InputBackend):
    name = "unsupported"
    supports_global_hotkeys = False

    def __init__(self, platform_name: str | None = None) -> None:
        self.platform_name = platform_name or sys.platform

    def _raise_unsupported(self, language: str | None = None) -> None:
        locale_key = normalize_language(language)
        raise OSError(tr(locale_key, "error.unsupported_platform", platform=self.platform_name))

    def get_cursor_position(self) -> tuple[int, int] | None:
        self._raise_unsupported()
        return None

    def click_mouse(self, button: str, x: int, y: int) -> None:
        self._raise_unsupported()

    def mouse_down(self, button: str, x: int, y: int) -> None:
        self._raise_unsupported()

    def mouse_up(self, button: str) -> None:
        self._raise_unsupported()

    def send_key_combo(self, combo: KeyCombo, language: str | None = None) -> None:
        self._raise_unsupported(language)

    def key_combo_down(self, combo: KeyCombo, language: str | None = None) -> None:
        self._raise_unsupported(language)

    def key_combo_up(self, combo: KeyCombo, language: str | None = None) -> None:
        self._raise_unsupported(language)

    def create_hotkey_manager(self) -> HotkeyManager:
        return UnsupportedHotkeyManager(self.platform_name)


class Win32InputBackend(InputBackend):
    name = "win32"
    supports_global_hotkeys = True

    @staticmethod
    def _backend():
        from autoclicker import win32_backend

        return win32_backend

    def get_cursor_position(self) -> tuple[int, int] | None:
        return self._backend().get_cursor_position()

    def click_mouse(self, button: str, x: int, y: int) -> None:
        self._backend().click_mouse(button, x, y)

    def mouse_down(self, button: str, x: int, y: int) -> None:
        self._backend().mouse_down(button, x, y)

    def mouse_up(self, button: str) -> None:
        self._backend().mouse_up(button)

    def send_key_combo(self, combo: KeyCombo, language: str | None = None) -> None:
        self._backend().send_key_combo(combo, language)

    def key_combo_down(self, combo: KeyCombo, language: str | None = None) -> None:
        self._backend().key_combo_down(combo, language)

    def key_combo_up(self, combo: KeyCombo, language: str | None = None) -> None:
        self._backend().key_combo_up(combo, language)

    def create_hotkey_manager(self) -> HotkeyManager:
        return self._backend().GlobalHotkeyManager()


def create_input_backend(platform_name: str | None = None) -> InputBackend:
    resolved = platform_name or sys.platform
    if resolved == "win32":
        return Win32InputBackend()
    return UnsupportedInputBackend(resolved)
