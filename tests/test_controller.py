import threading
import unittest

from autoclicker.controller import AutomationController
from autoclicker.input_backend import InputBackend, UnsupportedHotkeyManager
from autoclicker.models import ActionUnit, KeyCombo


class FakeInputBackend(InputBackend):
    name = "fake"
    supports_global_hotkeys = True

    def __init__(self) -> None:
        self.mouse_clicks: list[tuple[str, int, int]] = []
        self.key_presses: list[str] = []

    def get_cursor_position(self) -> tuple[int, int] | None:
        return (10, 20)

    def click_mouse(self, button: str, x: int, y: int) -> None:
        self.mouse_clicks.append((button, x, y))

    def mouse_down(self, button: str, x: int, y: int) -> None:
        self.mouse_clicks.append((button + "_down", x, y))

    def mouse_up(self, button: str) -> None:
        self.mouse_clicks.append((button + "_up", -1, -1))

    def send_key_combo(self, combo: KeyCombo, language: str | None = None) -> None:
        self.key_presses.append(combo.display_text())

    def key_combo_down(self, combo: KeyCombo, language: str | None = None) -> None:
        self.key_presses.append(combo.display_text() + "_down")

    def key_combo_up(self, combo: KeyCombo, language: str | None = None) -> None:
        self.key_presses.append(combo.display_text() + "_up")

    def create_hotkey_manager(self):
        return UnsupportedHotkeyManager("fake")


class AutomationControllerTests(unittest.TestCase):
    def test_emit_runtime_metrics_reports_average_frequency(self) -> None:
        controller = AutomationController(FakeInputBackend())
        action_counts: list[int] = []
        actual_rates: list[float] = []
        controller.action_count_changed.connect(action_counts.append)
        controller.actual_frequency_changed.connect(actual_rates.append)

        controller._action_count = 12
        controller._run_started_at = 4.0

        controller._emit_runtime_metrics(now=5.0)

        self.assertEqual(action_counts[-1], 12)
        self.assertAlmostEqual(actual_rates[-1], 12.0)

    def test_force_zero_runtime_metrics_preserves_count_and_clears_rate(self) -> None:
        controller = AutomationController(FakeInputBackend())
        action_counts: list[int] = []
        actual_rates: list[float] = []
        controller.action_count_changed.connect(action_counts.append)
        controller.actual_frequency_changed.connect(actual_rates.append)

        controller._action_count = 7
        controller._run_started_at = 2.5

        controller._emit_runtime_metrics(force_zero=True)

        self.assertEqual(action_counts[-1], 7)
        self.assertEqual(actual_rates[-1], 0.0)
        self.assertIsNone(controller._run_started_at)

    def test_action_execution_uses_injected_backend_and_emits_last_action(self) -> None:
        backend = FakeInputBackend()
        controller = AutomationController(backend)
        last_actions: list[str] = []
        controller.last_action_changed.connect(last_actions.append)

        controller._execute_action_unit(
            ActionUnit(action_mode="keyboard", action_key=KeyCombo("F1"), limit_mode="count", limit_count=1),
            0,
            threading.Event(),
            "en",
        )

        self.assertEqual(backend.key_presses, ["F1_down", "F1_up"])
        self.assertIn("#1", last_actions[-1])


if __name__ == "__main__":
    unittest.main()
