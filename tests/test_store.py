import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from autoclicker.store import SettingsStore


class SettingsStoreTests(unittest.TestCase):
    def test_load_returns_default_state_for_invalid_saved_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "ProAutoClicker"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "settings.json").write_text(
                json.dumps({"last_settings": {"fixed_x": "abc", "frequency_hz": "bad"}}, ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                store = SettingsStore()
                state = store.load()

            action = state.last_settings.first_action()
            self.assertEqual(action.fixed_x, 0)
            self.assertEqual(action.frequency_hz, 20.0)

    def test_import_presets_rejects_invalid_root_shape_in_english(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            preset_path = Path(temp_dir) / "presets.json"
            preset_path.write_text(json.dumps(["bad", "shape"], ensure_ascii=False), encoding="utf-8")

            store = SettingsStore()
            with self.assertRaisesRegex(ValueError, "The preset file format is invalid."):
                store.import_presets(str(preset_path), "en")


if __name__ == "__main__":
    unittest.main()
