from __future__ import annotations

import json
import os
from pathlib import Path

from autoclicker.i18n import default_preset_name, normalize_language, tr
from autoclicker.models import PersistedState, Preset

APP_DIR_NAME = "ProAutoClicker"


class SettingsStore:
    def __init__(self) -> None:
        base_dir = Path(os.environ.get("APPDATA", str(Path.home())))
        self.config_dir = base_dir / APP_DIR_NAME
        self.config_path = self.config_dir / "settings.json"

    def load(self) -> PersistedState:
        if not self.config_path.exists():
            return PersistedState()
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            return PersistedState.from_dict(data)
        except (OSError, TypeError, ValueError):
            return PersistedState()

    def save(self, state: PersistedState) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(state.to_dict(), indent=2, ensure_ascii=False)
        self.config_path.write_text(payload, encoding="utf-8")

    def export_presets(self, path: str, presets: list[Preset]) -> None:
        data = {
            "schema_version": 2,
            "presets": [preset.to_dict() for preset in presets],
        }
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def import_presets(self, path: str, language: str | None = None) -> list[Preset]:
        locale_key = normalize_language(language)
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(tr(locale_key, "error.invalid_preset_root"))

        presets = data.get("presets", [])
        if not isinstance(presets, list):
            raise ValueError(tr(locale_key, "error.invalid_preset_presets"))

        fallback_name = default_preset_name(locale_key)
        return [Preset.from_dict(item, default_name=fallback_name) for item in presets]
