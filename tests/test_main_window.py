import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from autoclicker.input_backend import InputBackend
from autoclicker.models import ActionUnit, AppSettings, EMERGENCY_STOP_HOTKEY, KeyCombo
from autoclicker.ui.main_window import MainWindow

APP = QApplication.instance() or QApplication([])


class FakeHotkeyManager(QObject):
    toggle_pressed = Signal()
    exit_pressed = Signal()
    emergency_pressed = Signal()
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.configured: list[tuple[KeyCombo | None, KeyCombo | None, KeyCombo | None]] = []
        self.stop_count = 0

    def configure(
        self,
        toggle_hotkey: KeyCombo | None,
        exit_hotkey: KeyCombo | None,
        language: str | None = None,
        *,
        emergency_hotkey: KeyCombo | None = EMERGENCY_STOP_HOTKEY,
    ) -> None:
        self.configured.append((toggle_hotkey, exit_hotkey, emergency_hotkey))

    def stop(self) -> None:
        self.stop_count += 1


class FakeInputBackend(InputBackend):
    name = "fake"
    supports_global_hotkeys = True

    def __init__(self) -> None:
        self.hotkey_manager = FakeHotkeyManager()

    def get_cursor_position(self) -> tuple[int, int] | None:
        return (100, 200)

    def click_mouse(self, button: str, x: int, y: int) -> None:
        return

    def mouse_down(self, button: str, x: int, y: int) -> None:
        return

    def mouse_up(self, button: str) -> None:
        return

    def send_key_combo(self, combo: KeyCombo, language: str | None = None) -> None:
        return

    def key_combo_down(self, combo: KeyCombo, language: str | None = None) -> None:
        return

    def key_combo_up(self, combo: KeyCombo, language: str | None = None) -> None:
        return

    def create_hotkey_manager(self) -> FakeHotkeyManager:
        return self.hotkey_manager


class MainWindowTests(unittest.TestCase):
    def _create_window(self, temp_dir: str, backend: FakeInputBackend | None = None) -> MainWindow:
        fake_backend = backend or FakeInputBackend()
        patcher = patch("autoclicker.ui.main_window.create_input_backend", return_value=fake_backend)
        patcher.start()
        self.addCleanup(patcher.stop)
        env_patcher = patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False)
        env_patcher.start()
        self.addCleanup(env_patcher.stop)
        window = MainWindow()
        self.addCleanup(lambda: self._close_window(window))
        return window

    @staticmethod
    def _close_window(window: MainWindow) -> None:
        window._force_quit = True
        window.close()

    def test_load_initial_state_prefers_last_used_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "ProAutoClicker"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "settings.json").write_text(
                json.dumps(
                    {
                        "selected_preset": "Mouse Preset",
                        "language": "en",
                        "auto_check_updates": True,
                        "last_settings": {
                            "actions": [
                                {
                                    "action_mode": "keyboard",
                                    "action_key": {"key": "B", "modifiers": []},
                                    "frequency_hz": 12.5,
                                }
                            ]
                        },
                        "presets": [
                            {
                                "name": "Mouse Preset",
                                "settings": {
                                    "actions": [
                                        {
                                            "action_mode": "mouse",
                                            "mouse_button": "right",
                                            "target_mode": "fixed",
                                            "fixed_x": 88,
                                            "fixed_y": 99,
                                        }
                                    ]
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            window = self._create_window(temp_dir)

            self.assertEqual(window.preset_combo.currentText(), "Mouse Preset")
            self.assertEqual(window._language, "en")
            self.assertTrue(window.auto_check_updates_checkbox.isChecked())
            self.assertEqual(window.quick_editor.action_mode_combo.currentData(), "keyboard")
            self.assertEqual(window.quick_editor.action_key_edit.hotkey().display_text(), "B")
            self.assertAlmostEqual(window.quick_editor.frequency_spin.value(), 12.5)
            self.assertEqual(window.start_button.text(), "Start / Resume")

    def test_sequence_list_drag_order_updates_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            window = self._create_window(temp_dir)
            window._apply_settings_to_form(
                AppSettings(
                    actions=[
                        ActionUnit(name="A", limit_mode="count", limit_count=1),
                        ActionUnit(name="B", limit_mode="count", limit_count=1),
                        ActionUnit(name="C", limit_mode="count", limit_count=1),
                    ]
                )
            )
            window._refresh_form_state()

            moved = window.sequence_list.takeItem(2)
            window.sequence_list.insertItem(0, moved)
            window._apply_sequence_order_from_list()

            self.assertEqual([action.name for action in window._settings.actions], ["C", "A", "B"])
            self.assertEqual(window.quick_editor.name_edit.text(), "C")

    def test_batch_copy_and_delete_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            window = self._create_window(temp_dir)
            window._apply_settings_to_form(
                AppSettings(
                    actions=[
                        ActionUnit(name="A", limit_mode="count", limit_count=1),
                        ActionUnit(name="B", limit_mode="count", limit_count=1),
                        ActionUnit(name="C", limit_mode="count", limit_count=1),
                    ]
                )
            )
            window._refresh_form_state()

            window.sequence_list.item(0).setSelected(True)
            window.sequence_list.item(2).setSelected(True)
            window._copy_selected_action()

            self.assertEqual([action.name for action in window._settings.actions], ["A", "B", "C", "A - 副本", "C - 副本"])

            window.sequence_list.clearSelection()
            window.sequence_list.item(1).setSelected(True)
            window.sequence_list.item(3).setSelected(True)
            with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
                window._delete_selected_action()

            self.assertEqual([action.name for action in window._settings.actions], ["A", "C", "C - 副本"])

    def test_hud_preferences_persist_with_last_action_and_opacity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "ProAutoClicker"
            window = self._create_window(temp_dir)

            window.enable_hud_checkbox.setChecked(True)
            window._rebuild_hud_order_list(("last", "state"))
            window.hud_opacity_spin.setValue(70)
            window._refresh_form_state()

            saved = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["overlay"]["hud_items"], ["last", "state"])
            self.assertEqual(saved["overlay"]["hud_opacity_percent"], 70)

    def test_emergency_hotkey_is_configured_globally_in_app_hotkey_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            backend = FakeInputBackend()
            window = self._create_window(temp_dir, backend)
            window.hotkey_scope_combo.setCurrentIndex(window.hotkey_scope_combo.findData("application"))
            window._refresh_form_state()

            self.assertIn((None, None, EMERGENCY_STOP_HOTKEY), backend.hotkey_manager.configured)

    def test_status_panel_shows_last_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            window = self._create_window(temp_dir)
            window._set_language("en")

            window._on_last_action_changed("12:00:00, #4")

            self.assertEqual(window.last_action_label.text(), "Last Action")
            self.assertEqual(window.last_action_value.text(), "12:00:00, #4")


if __name__ == "__main__":
    unittest.main()
