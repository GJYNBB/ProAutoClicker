import unittest

from autoclicker.models import (
    AppSettings,
    EMERGENCY_STOP_HOTKEY,
    KeyCombo,
    PersistedState,
    validate_settings,
)


class AppSettingsParsingTests(unittest.TestCase):
    def test_from_dict_falls_back_for_invalid_legacy_values(self) -> None:
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
                "confirm_before_start": "true",
                "safety_countdown_seconds": "2.5",
                "toggle_hotkey": {"key": "f6", "modifiers": ["Ctrl", 1, None]},
            }
        )

        action = settings.first_action()
        self.assertEqual(action.action_mode, "mouse")
        self.assertEqual(action.mouse_button, "left")
        self.assertEqual(action.target_mode, "capture")
        self.assertEqual(action.fixed_x, 0)
        self.assertEqual(action.fixed_y, 0)
        self.assertEqual(action.capture_delay_seconds, 3.0)
        self.assertEqual(action.frequency_hz, 20.0)
        self.assertEqual(settings.hotkey_scope, "global")
        self.assertFalse(settings.minimize_to_tray)
        self.assertTrue(settings.confirm_before_start)
        self.assertEqual(settings.safety_countdown_seconds, 2.5)
        self.assertEqual(settings.toggle_hotkey, KeyCombo("F6", ("Ctrl",)))

    def test_from_dict_migrates_legacy_mouse_action_mode(self) -> None:
        settings = AppSettings.from_dict({"action_mode": "mouse_right"})

        action = settings.first_action()
        self.assertEqual(action.action_mode, "mouse")
        self.assertEqual(action.mouse_button, "right")

    def test_validate_settings_supports_english_messages(self) -> None:
        settings = AppSettings.from_dict(
            {
                "actions": [
                    {
                        "random_interval_enabled": True,
                        "interval_min_ms": 200,
                        "interval_max_ms": 100,
                    }
                ]
            }
        )

        errors = validate_settings(settings, "en")

        self.assertIn("The minimum random interval cannot be greater than the maximum.", errors.messages())

    def test_validate_settings_reserves_emergency_hotkey(self) -> None:
        settings = AppSettings(toggle_hotkey=EMERGENCY_STOP_HOTKEY)

        errors = validate_settings(settings, "en")

        self.assertIn("This key combo is reserved for emergency stop. Choose another hotkey.", errors.messages())

    def test_persisted_state_normalizes_overlay_and_update_settings(self) -> None:
        state = PersistedState.from_dict(
            {
                "language": "zh-TW",
                "auto_check_updates": "true",
                "overlay": {
                    "hud_enabled": "true",
                    "hud_items": ["last", "count", "last"],
                    "hud_x": "bad",
                    "hud_y": -10,
                    "hud_opacity_percent": 4,
                },
                "presets": [],
            }
        )

        self.assertEqual(state.language, "zh-CN")
        self.assertTrue(state.auto_check_updates)
        self.assertEqual(state.selected_preset, "默认")
        self.assertEqual(state.presets[0].name, "默认")
        self.assertTrue(state.overlay.hud_enabled)
        self.assertEqual(state.overlay.hud_items, ("last", "count"))
        self.assertEqual(state.overlay.hud_x, 24)
        self.assertEqual(state.overlay.hud_y, 0)
        self.assertEqual(state.overlay.hud_opacity_percent, 15)


if __name__ == "__main__":
    unittest.main()
