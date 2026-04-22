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
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

HOTKEY_ID_TOGGLE = 1
HOTKEY_ID_EXIT = 2
HOTKEY_ID_EMERGENCY = 3

KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_ABSOLUTE = 0x8000

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

MOUSE_DOWN_FLAGS = {
    "left": MOUSEEVENTF_LEFTDOWN,
    "right": MOUSEEVENTF_RIGHTDOWN,
    "middle": MOUSEEVENTF_MIDDLEDOWN,
}

MOUSE_UP_FLAGS = {
    "left": MOUSEEVENTF_LEFTUP,
    "right": MOUSEEVENTF_RIGHTUP,
    "middle": MOUSEEVENTF_MIDDLEUP,
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


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


LPINPUT = ctypes.POINTER(INPUT)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [wintypes.INT]
user32.GetSystemMetrics.restype = wintypes.INT
user32.SendInput.argtypes = [wintypes.UINT, LPINPUT, ctypes.c_int]
user32.SendInput.restype = wintypes.UINT
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


def _mouse_input(flags: int) -> INPUT:
    event = INPUT(type=INPUT_MOUSE)
    event.mi = MOUSEINPUT(dwFlags=flags)
    return event


def _keyboard_input(vk: int, flags: int = 0) -> INPUT:
    event = INPUT(type=INPUT_KEYBOARD)
    event.ki = KEYBDINPUT(wVk=vk, dwFlags=flags)
    return event


def _get_virtual_screen_metrics() -> tuple[int, int, int, int]:
    left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    width = max(user32.GetSystemMetrics(SM_CXVIRTUALSCREEN), 1)
    height = max(user32.GetSystemMetrics(SM_CYVIRTUALSCREEN), 1)
    return left, top, width, height


def _normalize_absolute_coordinate(value: int, origin: int, span: int) -> int:
    if span <= 1:
        return 0
    normalized = round((value - origin) * 65535 / (span - 1))
    return max(0, min(65535, normalized))


def _build_mouse_move_input(x: int, y: int) -> INPUT:
    left, top, width, height = _get_virtual_screen_metrics()
    event = INPUT(type=INPUT_MOUSE)
    event.mi = MOUSEINPUT(
        dx=_normalize_absolute_coordinate(x, left, width),
        dy=_normalize_absolute_coordinate(y, top, height),
        dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
    )
    return event


def _build_mouse_click_inputs(button: str) -> tuple[INPUT, INPUT]:
    return _mouse_input(MOUSE_DOWN_FLAGS[button]), _mouse_input(MOUSE_UP_FLAGS[button])


def _build_key_combo_inputs(combo: KeyCombo, language: str | None = None) -> tuple[INPUT, ...]:
    locale_key = normalize_language(language)
    normalized = combo.normalized()
    vk = key_name_to_vk(normalized.key)
    if vk is None:
        raise OSError(tr(locale_key, "error.unsupported_keyboard_action"))

    inputs: list[INPUT] = []
    for modifier in normalized.modifiers:
        inputs.append(_keyboard_input(MODIFIER_VK_BY_NAME[modifier]))
    inputs.append(_keyboard_input(vk))
    inputs.append(_keyboard_input(vk, KEYEVENTF_KEYUP))
    for modifier in reversed(normalized.modifiers):
        inputs.append(_keyboard_input(MODIFIER_VK_BY_NAME[modifier], KEYEVENTF_KEYUP))
    return tuple(inputs)


def _build_key_down_inputs(combo: KeyCombo, language: str | None = None) -> tuple[INPUT, ...]:
    locale_key = normalize_language(language)
    normalized = combo.normalized()
    vk = key_name_to_vk(normalized.key)
    if vk is None:
        raise OSError(tr(locale_key, "error.unsupported_keyboard_action"))

    inputs: list[INPUT] = []
    for modifier in normalized.modifiers:
        inputs.append(_keyboard_input(MODIFIER_VK_BY_NAME[modifier]))
    inputs.append(_keyboard_input(vk))
    return tuple(inputs)


def _build_key_up_inputs(combo: KeyCombo, language: str | None = None) -> tuple[INPUT, ...]:
    locale_key = normalize_language(language)
    normalized = combo.normalized()
    vk = key_name_to_vk(normalized.key)
    if vk is None:
        raise OSError(tr(locale_key, "error.unsupported_keyboard_action"))

    inputs: list[INPUT] = [_keyboard_input(vk, KEYEVENTF_KEYUP)]
    for modifier in reversed(normalized.modifiers):
        inputs.append(_keyboard_input(MODIFIER_VK_BY_NAME[modifier], KEYEVENTF_KEYUP))
    return tuple(inputs)


def _send_inputs(*inputs: INPUT) -> None:
    input_count = len(inputs)
    if input_count == 0:
        return

    payload = (INPUT * input_count)(*inputs)
    sent = user32.SendInput(input_count, payload, ctypes.sizeof(INPUT))
    if sent != input_count:
        error = ctypes.get_last_error()
        if error:
            raise ctypes.WinError(error)
        raise OSError("SendInput failed.")


def get_cursor_position() -> tuple[int, int] | None:
    point = POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        return None
    return point.x, point.y


def move_cursor(x: int, y: int) -> None:
    _send_inputs(_build_mouse_move_input(x, y))


def mouse_down(button: str, x: int, y: int) -> None:
    _send_inputs(_build_mouse_move_input(x, y), _mouse_input(MOUSE_DOWN_FLAGS[button]))


def mouse_up(button: str) -> None:
    _send_inputs(_mouse_input(MOUSE_UP_FLAGS[button]))


def click_mouse(button: str, x: int, y: int) -> None:
    _send_inputs(
        _build_mouse_move_input(x, y),
        _mouse_input(MOUSE_DOWN_FLAGS[button]),
        _mouse_input(MOUSE_UP_FLAGS[button]),
    )


def key_combo_down(combo: KeyCombo, language: str | None = None) -> None:
    _send_inputs(*_build_key_down_inputs(combo, language))


def key_combo_up(combo: KeyCombo, language: str | None = None) -> None:
    _send_inputs(*_build_key_up_inputs(combo, language))


def send_key_combo(combo: KeyCombo, language: str | None = None) -> None:
    _send_inputs(*_build_key_combo_inputs(combo, language))


def hotkey_to_win32(combo: KeyCombo, language: str | None = None) -> tuple[int, int]:
    locale_key = normalize_language(language)
    normalized = combo.normalized()
    modifiers = MOD_NOREPEAT
    for modifier in normalized.modifiers:
        modifiers |= MODIFIER_FLAG_BY_NAME[modifier]
    vk = key_name_to_vk(normalized.key)
    if vk is None:
        raise OSError(
            tr(
                locale_key,
                "error.unsupported_hotkey",
                hotkey=combo.display_text() or tr(locale_key, "summary.not_set"),
            )
        )
    return modifiers, vk


class GlobalHotkeyManager(QObject):
    toggle_pressed = Signal()
    exit_pressed = Signal()
    emergency_pressed = Signal()
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._lock = threading.Lock()

    def configure(
        self,
        toggle_hotkey: KeyCombo | None,
        exit_hotkey: KeyCombo | None,
        language: str | None = None,
        *,
        emergency_hotkey: KeyCombo | None = None,
    ) -> None:
        locale_key = normalize_language(language)
        self.stop()
        self._thread = threading.Thread(
            target=self._message_loop,
            args=(
                toggle_hotkey.normalized() if toggle_hotkey is not None else None,
                exit_hotkey.normalized() if exit_hotkey is not None else None,
                emergency_hotkey.normalized() if emergency_hotkey is not None else None,
                locale_key,
            ),
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

    def _message_loop(
        self,
        toggle_hotkey: KeyCombo | None,
        exit_hotkey: KeyCombo | None,
        emergency_hotkey: KeyCombo | None,
        language: str,
    ) -> None:
        thread_id = kernel32.GetCurrentThreadId()
        registered_hotkeys: list[int] = []
        with self._lock:
            self._thread_id = thread_id
        try:
            if toggle_hotkey is not None:
                toggle_modifiers, toggle_vk = hotkey_to_win32(toggle_hotkey, language)
                if not user32.RegisterHotKey(None, HOTKEY_ID_TOGGLE, toggle_modifiers, toggle_vk):
                    raise OSError(tr(language, "error.register_toggle_failed", hotkey=toggle_hotkey.display_text()))
                registered_hotkeys.append(HOTKEY_ID_TOGGLE)
            if exit_hotkey is not None:
                exit_modifiers, exit_vk = hotkey_to_win32(exit_hotkey, language)
                if not user32.RegisterHotKey(None, HOTKEY_ID_EXIT, exit_modifiers, exit_vk):
                    raise OSError(tr(language, "error.register_exit_failed", hotkey=exit_hotkey.display_text()))
                registered_hotkeys.append(HOTKEY_ID_EXIT)
            if emergency_hotkey is not None:
                emergency_modifiers, emergency_vk = hotkey_to_win32(emergency_hotkey, language)
                if not user32.RegisterHotKey(None, HOTKEY_ID_EMERGENCY, emergency_modifiers, emergency_vk):
                    raise OSError(
                        tr(language, "error.register_emergency_failed", hotkey=emergency_hotkey.display_text())
                    )
                registered_hotkeys.append(HOTKEY_ID_EMERGENCY)

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
                    elif msg.wParam == HOTKEY_ID_EMERGENCY:
                        self.emergency_pressed.emit()
        except OSError as exc:
            self.error_occurred.emit(str(exc))
        finally:
            for hotkey_id in registered_hotkeys:
                user32.UnregisterHotKey(None, hotkey_id)
            with self._lock:
                self._thread_id = None
