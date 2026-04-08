import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from autoclicker.ui.main_window import MainWindow

APP = QApplication.instance() or QApplication([])


class MainWindowTests(unittest.TestCase):
    def test_load_initial_state_prefers_last_used_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "ProAutoClicker"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "settings.json").write_text(
                json.dumps(
                    {
                        "selected_preset": "Mouse Preset",
                        "language": "en",
                        "last_settings": {
                            "action_mode": "keyboard",
                            "action_key": {"key": "B", "modifiers": []},
                            "frequency_hz": 12.5,
                        },
                        "presets": [
                            {
                                "name": "Mouse Preset",
                                "settings": {
                                    "action_mode": "mouse",
                                    "mouse_button": "right",
                                    "target_mode": "fixed",
                                    "fixed_x": 88,
                                    "fixed_y": 99,
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                window = MainWindow()

            self.assertEqual(window.preset_combo.currentText(), "Mouse Preset")
            self.assertEqual(window._language, "en")
            self.assertEqual(window.language_menu.title(), "Language")
            self.assertTrue(window.language_actions["en"].isChecked())
            self.assertEqual(window.action_mode_combo.currentData(), "keyboard")
            self.assertEqual(window.action_key_edit.hotkey().display_text(), "B")
            self.assertAlmostEqual(window.frequency_spin.value(), 12.5)
            self.assertTrue(window.mouse_group.isHidden())
            self.assertEqual(window.action_group.title(), "Action")
            self.assertEqual(window.start_button.text(), "Start / Resume")

            window._force_quit = True
            window.close()

    def test_keyboard_mode_hides_mouse_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                window = MainWindow()

            self.assertFalse(window.mouse_group.isHidden())
            self.assertGreater(window._main_panel_layout.indexOf(window.preset_group), window._main_panel_layout.indexOf(window.help_group))

            window.action_mode_combo.setCurrentIndex(window.action_mode_combo.findData("keyboard"))
            window._refresh_form_state()

            self.assertTrue(window.mouse_group.isHidden())
            self.assertFalse(window.action_key_container.isHidden())

            window._force_quit = True
            window.close()

    def test_target_mode_toggles_mouse_parameter_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                window = MainWindow()

            window.action_mode_combo.setCurrentIndex(window.action_mode_combo.findData("mouse"))
            window.target_mode_combo.setCurrentIndex(window.target_mode_combo.findData("capture"))
            window._refresh_form_state()

            self.assertTrue(window.capture_delay_label.isVisibleTo(window.mouse_group))
            self.assertTrue(window.capture_delay_spin.isVisibleTo(window.mouse_group))
            self.assertFalse(window.fixed_coordinates_label.isVisibleTo(window.mouse_group))
            self.assertFalse(window.fixed_coordinates_row.isVisibleTo(window.mouse_group))

            window.target_mode_combo.setCurrentIndex(window.target_mode_combo.findData("fixed"))
            window._refresh_form_state()

            self.assertFalse(window.capture_delay_label.isVisibleTo(window.mouse_group))
            self.assertFalse(window.capture_delay_spin.isVisibleTo(window.mouse_group))
            self.assertTrue(window.fixed_coordinates_label.isVisibleTo(window.mouse_group))
            self.assertTrue(window.fixed_coordinates_row.isVisibleTo(window.mouse_group))

            window._force_quit = True
            window.close()

    def test_language_menu_updates_ui_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "ProAutoClicker"
            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                window = MainWindow()
                window.language_actions["zh-TW"].trigger()
                APP.processEvents()

                self.assertEqual(window._language, "zh-TW")
                self.assertEqual(window.language_menu.title(), "語言")
                self.assertTrue(window.language_actions["zh-TW"].isChecked())
                self.assertEqual(window.action_group.title(), "動作設定")
                self.assertEqual(window.start_button.text(), "開始 / 繼續")
                self.assertIn("快速開始", window.help_browser.toPlainText())

                saved = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
                self.assertEqual(saved["language"], "zh-TW")

                window._force_quit = True
                window.close()

    def test_status_panel_shows_runtime_observability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                window = MainWindow()

            window._set_language("en")
            window._on_state_changed("running")
            window._on_actual_frequency_changed(18.5)
            window._on_action_count_changed(42)

            self.assertEqual(window.state_value.text(), "Running")
            self.assertEqual(window.actual_frequency_label.text(), "Actual Rate")
            self.assertEqual(window.actual_frequency_value.text(), "18.5 / s")
            self.assertEqual(window.action_count_value.text(), "42")

            window._force_quit = True
            window.close()

    def test_overlay_preferences_persist_and_keep_at_least_one_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "ProAutoClicker"
            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                window = MainWindow()

            window.enable_hud_checkbox.setChecked(True)
            window.hud_state_checkbox.setChecked(False)
            window.hud_rate_checkbox.setChecked(False)
            window.hud_count_checkbox.setChecked(False)
            APP.processEvents()

            self.assertTrue(window.hud_state_checkbox.isChecked())

            window.hud_rate_checkbox.setChecked(True)
            window.hud_x_spin.setValue(320)
            window.hud_y_spin.setValue(180)
            APP.processEvents()

            saved = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["overlay"]["hud_items"], ["state", "rate"])
            self.assertEqual(saved["overlay"]["hud_x"], 320)
            self.assertEqual(saved["overlay"]["hud_y"], 180)

            window._force_quit = True
            window.close()


if __name__ == "__main__":
    unittest.main()
