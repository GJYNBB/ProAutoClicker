from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal

from autoclicker.i18n import normalize_language, tr
from autoclicker.keymaps import key_name_to_vk
from autoclicker.models import KeyCombo

ULONG_PTR = getattr(wintypes, "ULONG_PTR", ctypes.c_size_t)

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

HOTKEY_ID_TOGGLE = 1
HOTKEY_ID_EXIT = 2

KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

MODIFIER_FLAG_BY_NAME = {
    "Alt": MOD_ALT,
    "Ctrl": MOD_CONTROL,
    "Shift": MOD_SHIFT,
    "Win": MOD_WIN,
}

MODIFIER_VK_BY_NAME = {
    "Alt": 0x12,
    "Ctrl": 0x11,
    "Shift": 0x10,
    "Win": 0x5B,
}

MOUSE_FLAGS = {
    "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
    "mouse_left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "mouse_right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "mouse_middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
        ("lPrivate", wintypes.DWORD),
    ]


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.SetCursorPos.argtypes = [wintypes.INT, wintypes.INT]
user32.SetCursorPos.restype = wintypes.BOOL
user32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ULONG_PTR]
user32.mouse_event.restype = None
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ULONG_PTR]
user32.keybd_event.restype = None
user32.RegisterHotKey.argtypes = [wintypes.HWND, wintypes.INT, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, wintypes.INT]
user32.UnregisterHotKey.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.argtypes = []
kernel32.GetCurrentThreadId.restype = wintypes.DWORD


def get_cursor_position() -> tuple[int, int] | None:
    point = POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        return None
    return point.x, point.y


def click_mouse(action_mode: str, x: int, y: int) -> None:
    flags = MOUSE_FLAGS[action_mode]
    user32.SetCursorPos(x, y)
    user32.mouse_event(flags[0], 0, 0, 0, 0)
    user32.mouse_event(flags[1], 0, 0, 0, 0)


def send_key_combo(combo: KeyCombo, language: str | None = None) -> None:
    locale_key = normalize_language(language)
    normalized = combo.normalized()
    vk = key_name_to_vk(normalized.key)
    if vk is None:
        raise OSError(tr(locale_key, "error.unsupported_keyboard_action"))
    for modifier in normalized.modifiers:
        user32.keybd_event(MODIFIER_VK_BY_NAME[modifier], 0, 0, 0)
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    for modifier in reversed(normalized.modifiers):
        user32.keybd_event(MODIFIER_VK_BY_NAME[modifier], 0, KEYEVENTF_KEYUP, 0)


def hotkey_to_win32(combo: KeyCombo, language: str | None = None) -> tuple[int, int]:
    locale_key = normalize_language(language)
    normalized = combo.normalized()
    modifiers = MOD_NOREPEAT
    for modifier in normalized.modifiers:
        modifiers |= MODIFIER_FLAG_BY_NAME[modifier]
    vk = key_name_to_vk(normalized.key)
    if vk is None:
        raise OSError(tr(locale_key, "error.unsupported_hotkey", hotkey=combo.display_text() or tr(locale_key, "summary.not_set")))
    return modifiers, vk


class GlobalHotkeyManager(QObject):
    toggle_pressed = Signal()
    exit_pressed = Signal()
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._lock = threading.Lock()

    def configure(self, toggle_hotkey: KeyCombo, exit_hotkey: KeyCombo, language: str | None = None) -> None:
        locale_key = normalize_language(language)
        self.stop()
        self._thread = threading.Thread(
            target=self._message_loop,
            args=(toggle_hotkey.normalized(), exit_hotkey.normalized(), locale_key),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        with self._lock:
            thread_id = self._thread_id
            thread = self._thread
        if thread_id is not None:
            user32.PostThreadMessageW(thread_id, WM_QUIT, 0, 0)
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)
        with self._lock:
            self._thread = None
            self._thread_id = None

    def _message_loop(self, toggle_hotkey: KeyCombo, exit_hotkey: KeyCombo, language: str) -> None:
        thread_id = kernel32.GetCurrentThreadId()
        registered_toggle = False
        registered_exit = False
        with self._lock:
            self._thread_id = thread_id
        try:
            toggle_modifiers, toggle_vk = hotkey_to_win32(toggle_hotkey, language)
            exit_modifiers, exit_vk = hotkey_to_win32(exit_hotkey, language)
            if not user32.RegisterHotKey(None, HOTKEY_ID_TOGGLE, toggle_modifiers, toggle_vk):
                raise OSError(tr(language, "error.register_toggle_failed", hotkey=toggle_hotkey.display_text()))
            registered_toggle = True
            if not user32.RegisterHotKey(None, HOTKEY_ID_EXIT, exit_modifiers, exit_vk):
                raise OSError(tr(language, "error.register_exit_failed", hotkey=exit_hotkey.display_text()))
            registered_exit = True

            msg = MSG()
            while True:
                result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result == -1:
                    raise ctypes.WinError()
                if result == 0:
                    break
                if msg.message == WM_HOTKEY:
                    if msg.wParam == HOTKEY_ID_TOGGLE:
                        self.toggle_pressed.emit()
                    elif msg.wParam == HOTKEY_ID_EXIT:
                        self.exit_pressed.emit()
        except OSError as exc:
            self.error_occurred.emit(str(exc))
        finally:
            if registered_toggle:
                user32.UnregisterHotKey(None, HOTKEY_ID_TOGGLE)
            if registered_exit:
                user32.UnregisterHotKey(None, HOTKEY_ID_EXIT)
            with self._lock:
                self._thread_id = None
