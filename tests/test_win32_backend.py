import ctypes
import unittest
from unittest.mock import patch

import autoclicker.win32_backend as backend
from autoclicker.models import KeyCombo


class _FakeUser32:
    def __init__(self, *, send_result: int | None = None) -> None:
        self.send_result = send_result
        self.send_calls: list[tuple[int, list[backend.INPUT], int]] = []

    def SendInput(self, count: int, payload: ctypes.Array[backend.INPUT], size: int) -> int:
        snapshot = [payload[index] for index in range(count)]
        self.send_calls.append((count, snapshot, size))
        if self.send_result is None:
            return count
        return self.send_result


class Win32BackendTests(unittest.TestCase):
    def test_build_mouse_move_input_uses_absolute_virtual_desktop_coordinates(self) -> None:
        with patch.object(backend, "_get_virtual_screen_metrics", return_value=(0, 0, 1920, 1080)):
            move_event = backend._build_mouse_move_input(1919, 1079)

        self.assertEqual(move_event.type, backend.INPUT_MOUSE)
        self.assertEqual(
            move_event.mi.dwFlags,
            backend.MOUSEEVENTF_MOVE | backend.MOUSEEVENTF_ABSOLUTE | backend.MOUSEEVENTF_VIRTUALDESK,
        )
        self.assertEqual(move_event.mi.dx, 65535)
        self.assertEqual(move_event.mi.dy, 65535)

    def test_build_mouse_click_inputs_uses_expected_flags(self) -> None:
        down_event, up_event = backend._build_mouse_click_inputs("right")

        self.assertEqual(down_event.type, backend.INPUT_MOUSE)
        self.assertEqual(down_event.mi.dwFlags, backend.MOUSEEVENTF_RIGHTDOWN)
        self.assertEqual(up_event.type, backend.INPUT_MOUSE)
        self.assertEqual(up_event.mi.dwFlags, backend.MOUSEEVENTF_RIGHTUP)

    def test_build_key_combo_inputs_orders_modifier_and_key_events(self) -> None:
        events = backend._build_key_combo_inputs(KeyCombo("A", ("Shift", "Ctrl")))

        self.assertEqual([event.type for event in events], [backend.INPUT_KEYBOARD] * 6)
        self.assertEqual(events[0].ki.wVk, backend.MODIFIER_VK_BY_NAME["Ctrl"])
        self.assertEqual(events[1].ki.wVk, backend.MODIFIER_VK_BY_NAME["Shift"])
        self.assertEqual(events[2].ki.wVk, ord("A"))
        self.assertEqual(events[2].ki.dwFlags, 0)
        self.assertEqual(events[3].ki.wVk, ord("A"))
        self.assertEqual(events[3].ki.dwFlags, backend.KEYEVENTF_KEYUP)
        self.assertEqual(events[4].ki.wVk, backend.MODIFIER_VK_BY_NAME["Shift"])
        self.assertEqual(events[4].ki.dwFlags, backend.KEYEVENTF_KEYUP)
        self.assertEqual(events[5].ki.wVk, backend.MODIFIER_VK_BY_NAME["Ctrl"])
        self.assertEqual(events[5].ki.dwFlags, backend.KEYEVENTF_KEYUP)

    def test_send_key_combo_uses_sendinput(self) -> None:
        fake_user32 = _FakeUser32()

        with patch.object(backend, "user32", fake_user32):
            backend.send_key_combo(KeyCombo("B", ("Ctrl",)))

        self.assertEqual(len(fake_user32.send_calls), 1)
        sent_count, payload, struct_size = fake_user32.send_calls[0]
        self.assertEqual(sent_count, 4)
        self.assertEqual(struct_size, ctypes.sizeof(backend.INPUT))
        self.assertEqual(payload[0].ki.wVk, backend.MODIFIER_VK_BY_NAME["Ctrl"])
        self.assertEqual(payload[1].ki.wVk, ord("B"))
        self.assertEqual(payload[2].ki.dwFlags, backend.KEYEVENTF_KEYUP)
        self.assertEqual(payload[3].ki.dwFlags, backend.KEYEVENTF_KEYUP)

    def test_click_mouse_moves_cursor_then_uses_sendinput(self) -> None:
        fake_user32 = _FakeUser32()

        with patch.object(backend, "user32", fake_user32), patch.object(
            backend, "_get_virtual_screen_metrics", return_value=(0, 0, 100, 100)
        ):
            backend.click_mouse("middle", 128, 256)

        self.assertEqual(len(fake_user32.send_calls), 1)
        sent_count, payload, struct_size = fake_user32.send_calls[0]
        self.assertEqual(sent_count, 3)
        self.assertEqual(struct_size, ctypes.sizeof(backend.INPUT))
        self.assertEqual(
            payload[0].mi.dwFlags,
            backend.MOUSEEVENTF_MOVE | backend.MOUSEEVENTF_ABSOLUTE | backend.MOUSEEVENTF_VIRTUALDESK,
        )
        self.assertEqual(payload[1].mi.dwFlags, backend.MOUSEEVENTF_MIDDLEDOWN)
        self.assertEqual(payload[2].mi.dwFlags, backend.MOUSEEVENTF_MIDDLEUP)


if __name__ == "__main__":
    unittest.main()
