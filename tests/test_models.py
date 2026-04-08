import unittest

from autoclicker.models import AppSettings, KeyCombo, PersistedState, validate_settings


class AppSettingsParsingTests(unittest.TestCase):
    def test_from_dict_falls_back_for_invalid_values(self) -> None:
        settings = AppSettings.from_dict(
            {
                "action_mode": "unsupported",
                "mouse_button": "bad",
                "target_mode": "bad",
                "fixed_x": "abc",
                "fixed_y": None,
                "capture_delay_seconds": "oops",
                "frequency_hz": "oops",
                "hotkey_scope": "bad",
                "minimize_to_tray": "false",
                "toggle_hotkey": {"key": "f6", "modifiers": ["Ctrl", 1, None]},
            }
        )

        self.assertEqual(settings.action_mode, "mouse")
        self.assertEqual(settings.mouse_button, "left")
        self.assertEqual(settings.target_mode, "capture")
        self.assertEqual(settings.fixed_x, 0)
        self.assertEqual(settings.fixed_y, 0)
        self.assertEqual(settings.capture_delay_seconds, 3.0)
        self.assertEqual(settings.frequency_hz, 20.0)
        self.assertEqual(settings.hotkey_scope, "global")
        self.assertFalse(settings.minimize_to_tray)
        self.assertEqual(settings.toggle_hotkey, KeyCombo("F6", ("Ctrl",)))

    def test_from_dict_migrates_legacy_mouse_action_mode(self) -> None:
        settings = AppSettings.from_dict({"action_mode": "mouse_right"})

        self.assertEqual(settings.action_mode, "mouse")
        self.assertEqual(settings.mouse_button, "right")

    def test_validate_settings_supports_english_messages(self) -> None:
        settings = AppSettings(frequency_hz=0.05)

        errors = validate_settings(settings, "en")

        self.assertIn("Frequency must be between 0.1 and 1000 actions per second.", errors)

    def test_persisted_state_reads_language_and_localized_default_name(self) -> None:
        state = PersistedState.from_dict({"language": "zh-TW", "presets": []})

        self.assertEqual(state.language, "zh-TW")
        self.assertEqual(state.selected_preset, "預設")
        self.assertEqual(state.presets[0].name, "預設")

    def test_persisted_state_normalizes_overlay_settings(self) -> None:
        state = PersistedState.from_dict(
            {
                "overlay": {
                    "hud_enabled": "true",
                    "hud_items": [],
                    "hud_x": "bad",
                    "hud_y": -10,
                }
            }
        )

        self.assertTrue(state.overlay.hud_enabled)
        self.assertEqual(state.overlay.hud_items, ("state",))
        self.assertEqual(state.overlay.hud_x, 24)
        self.assertEqual(state.overlay.hud_y, 0)


if __name__ == "__main__":
    unittest.main()
