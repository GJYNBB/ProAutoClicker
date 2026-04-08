from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from autoclicker.i18n import choice_labels, default_preset_name, detect_system_language, normalize_language, tr
from autoclicker.keymaps import MODIFIER_ORDER, key_name_to_vk, normalize_key_name, normalize_modifiers

ACTION_CHOICES = ("mouse", "keyboard")
MOUSE_BUTTON_CHOICES = ("left", "right", "middle")
TARGET_CHOICES = ("capture", "fixed")
HOTKEY_SCOPE_CHOICES = ("global", "application")
HUD_ITEM_CHOICES = ("state", "rate", "count")

LEGACY_MOUSE_ACTIONS = {
    "mouse_left": "left",
    "mouse_right": "right",
    "mouse_middle": "middle",
}


def get_action_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "action", ACTION_CHOICES)


def get_mouse_button_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "mouse_button", MOUSE_BUTTON_CHOICES)


def get_target_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "target", TARGET_CHOICES)


def get_hotkey_scope_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "hotkey_scope", HOTKEY_SCOPE_CHOICES)


def get_hud_item_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "hud_item", HUD_ITEM_CHOICES)


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _coerce_choice(value: Any, allowed: Collection[str], default: str) -> str:
    text = str(value or "")
    if text in allowed:
        return text
    return default


def _normalize_action_fields(action_mode: Any, mouse_button: Any) -> tuple[str, str]:
    normalized_mode = str(action_mode or "")
    normalized_button = str(mouse_button or "")

    if normalized_mode in LEGACY_MOUSE_ACTIONS:
        return "mouse", LEGACY_MOUSE_ACTIONS[normalized_mode]

    if normalized_mode not in ACTION_CHOICES:
        normalized_mode = "mouse"

    if normalized_button not in MOUSE_BUTTON_CHOICES:
        normalized_button = "left"

    return normalized_mode, normalized_button


def _normalize_hud_items(items: Any) -> tuple[str, ...]:
    if not isinstance(items, (list, tuple, set)):
        items = []
    normalized: list[str] = []
    for item in items:
        text = str(item or "")
        if text in HUD_ITEM_CHOICES and text not in normalized:
            normalized.append(text)
    if not normalized:
        normalized.append("state")
    return tuple(normalized[: len(HUD_ITEM_CHOICES)])


@dataclass(frozen=True)
class KeyCombo:
    key: str = ""
    modifiers: tuple[str, ...] = field(default_factory=tuple)

    def normalized(self) -> "KeyCombo":
        return KeyCombo(
            key=normalize_key_name(self.key),
            modifiers=normalize_modifiers(self.modifiers),
        )

    def is_empty(self) -> bool:
        return not self.key

    def display_text(self) -> str:
        combo = self.normalized()
        if combo.is_empty():
            return ""
        parts = [name for name in MODIFIER_ORDER if name in combo.modifiers]
        parts.append(combo.key)
        return "+".join(parts)

    def to_dict(self) -> dict[str, Any]:
        combo = self.normalized()
        return {
            "key": combo.key,
            "modifiers": list(combo.modifiers),
        }

    @staticmethod
    def from_dict(data: dict[str, Any] | None) -> "KeyCombo":
        if not isinstance(data, dict):
            return KeyCombo()
        modifiers = data.get("modifiers", [])
        if not isinstance(modifiers, (list, tuple, set)):
            modifiers = []
        return KeyCombo(
            key=str(data.get("key", "")),
            modifiers=tuple(str(item) for item in modifiers),
        ).normalized()


@dataclass
class AppSettings:
    action_mode: str = "mouse"
    mouse_button: str = "left"
    action_key: KeyCombo = field(default_factory=lambda: KeyCombo("A"))
    target_mode: str = "capture"
    fixed_x: int = 0
    fixed_y: int = 0
    capture_delay_seconds: float = 3.0
    frequency_hz: float = 20.0
    hotkey_scope: str = "global"
    toggle_hotkey: KeyCombo = field(default_factory=lambda: KeyCombo("F6"))
    exit_hotkey: KeyCombo = field(default_factory=lambda: KeyCombo("Esc"))
    minimize_to_tray: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_mode": self.action_mode,
            "mouse_button": self.mouse_button,
            "action_key": self.action_key.to_dict(),
            "target_mode": self.target_mode,
            "fixed_x": self.fixed_x,
            "fixed_y": self.fixed_y,
            "capture_delay_seconds": self.capture_delay_seconds,
            "frequency_hz": self.frequency_hz,
            "hotkey_scope": self.hotkey_scope,
            "toggle_hotkey": self.toggle_hotkey.to_dict(),
            "exit_hotkey": self.exit_hotkey.to_dict(),
            "minimize_to_tray": self.minimize_to_tray,
        }

    @staticmethod
    def from_dict(data: dict[str, Any] | None) -> "AppSettings":
        if not isinstance(data, dict):
            return AppSettings()

        action_mode, mouse_button = _normalize_action_fields(
            data.get("action_mode"),
            data.get("mouse_button"),
        )
        return AppSettings(
            action_mode=action_mode,
            mouse_button=mouse_button,
            action_key=KeyCombo.from_dict(data.get("action_key")),
            target_mode=_coerce_choice(data.get("target_mode"), TARGET_CHOICES, "capture"),
            fixed_x=_coerce_int(data.get("fixed_x", 0), 0),
            fixed_y=_coerce_int(data.get("fixed_y", 0), 0),
            capture_delay_seconds=_coerce_float(data.get("capture_delay_seconds", 3.0), 3.0),
            frequency_hz=_coerce_float(data.get("frequency_hz", 20.0), 20.0),
            hotkey_scope=_coerce_choice(data.get("hotkey_scope"), HOTKEY_SCOPE_CHOICES, "global"),
            toggle_hotkey=KeyCombo.from_dict(data.get("toggle_hotkey")),
            exit_hotkey=KeyCombo.from_dict(data.get("exit_hotkey")),
            minimize_to_tray=_coerce_bool(data.get("minimize_to_tray", True), True),
        )


@dataclass
class Preset:
    name: str
    settings: AppSettings
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "updated_at": self.updated_at,
            "settings": self.settings.to_dict(),
        }

    @staticmethod
    def from_dict(data: dict[str, Any] | None, *, default_name: str | None = None) -> "Preset":
        fallback_name = default_name or default_preset_name()
        if not isinstance(data, dict):
            return Preset(name=fallback_name, settings=AppSettings())
        return Preset(
            name=str(data.get("name", fallback_name)).strip() or fallback_name,
            updated_at=str(data.get("updated_at", "")).strip() or datetime.now().isoformat(timespec="seconds"),
            settings=AppSettings.from_dict(data.get("settings")),
        )


@dataclass
class OverlaySettings:
    hud_enabled: bool = False
    hud_items: tuple[str, ...] = field(default_factory=lambda: ("state", "rate", "count"))
    hud_x: int = 24
    hud_y: int = 24

    def to_dict(self) -> dict[str, Any]:
        return {
            "hud_enabled": self.hud_enabled,
            "hud_items": list(self.hud_items),
            "hud_x": self.hud_x,
            "hud_y": self.hud_y,
        }

    @staticmethod
    def from_dict(data: dict[str, Any] | None) -> "OverlaySettings":
        if not isinstance(data, dict):
            return OverlaySettings()
        return OverlaySettings(
            hud_enabled=_coerce_bool(data.get("hud_enabled", False), False),
            hud_items=_normalize_hud_items(data.get("hud_items")),
            hud_x=max(_coerce_int(data.get("hud_x", 24), 24), 0),
            hud_y=max(_coerce_int(data.get("hud_y", 24), 24), 0),
        )


@dataclass
class PersistedState:
    schema_version: int = 3
    language: str = field(default_factory=detect_system_language)
    selected_preset: str = field(default_factory=default_preset_name)
    last_settings: AppSettings = field(default_factory=AppSettings)
    overlay: OverlaySettings = field(default_factory=OverlaySettings)
    presets: list[Preset] = field(default_factory=lambda: [Preset(name=default_preset_name(), settings=AppSettings())])

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "language": self.language,
            "selected_preset": self.selected_preset,
            "last_settings": self.last_settings.to_dict(),
            "overlay": self.overlay.to_dict(),
            "presets": [preset.to_dict() for preset in self.presets],
        }

    @staticmethod
    def from_dict(data: dict[str, Any] | None) -> "PersistedState":
        if not isinstance(data, dict):
            return PersistedState()

        language = normalize_language(data.get("language")) if "language" in data else detect_system_language()
        fallback_name = default_preset_name(language)
        raw_presets = data.get("presets", [])
        if not isinstance(raw_presets, list):
            raw_presets = []
        presets = [Preset.from_dict(item, default_name=fallback_name) for item in raw_presets]
        if not presets:
            presets = [Preset(name=fallback_name, settings=AppSettings())]
        return PersistedState(
            schema_version=_coerce_int(data.get("schema_version", 3), 3),
            language=language,
            selected_preset=str(data.get("selected_preset", fallback_name)).strip() or fallback_name,
            last_settings=AppSettings.from_dict(data.get("last_settings")),
            overlay=OverlaySettings.from_dict(data.get("overlay")),
            presets=presets,
        )


def format_action_label(settings: AppSettings, language: str | None = None) -> str:
    locale_key = normalize_language(language)
    if settings.action_mode == "keyboard":
        return tr(locale_key, "action.keyboard")
    mouse_label = tr(locale_key, "action.mouse")
    button_label = tr(locale_key, f"mouse_button.{settings.mouse_button}")
    if locale_key == "en":
        return f"{mouse_label} {button_label}"
    return f"{mouse_label}{button_label}"


def validate_settings(settings: AppSettings, language: str | None = None) -> list[str]:
    locale_key = normalize_language(language)
    errors: list[str] = []

    if settings.capture_delay_seconds < 0 or settings.capture_delay_seconds > 60:
        errors.append(tr(locale_key, "validation.capture_delay_range"))

    if settings.frequency_hz < 0.1 or settings.frequency_hz > 1000:
        errors.append(tr(locale_key, "validation.frequency_range"))

    if settings.toggle_hotkey.is_empty():
        errors.append(tr(locale_key, "validation.toggle_hotkey_required"))

    if settings.exit_hotkey.is_empty():
        errors.append(tr(locale_key, "validation.exit_hotkey_required"))

    if settings.toggle_hotkey.normalized() == settings.exit_hotkey.normalized():
        errors.append(tr(locale_key, "validation.hotkeys_must_differ"))

    if key_name_to_vk(settings.toggle_hotkey.key) is None:
        errors.append(tr(locale_key, "validation.toggle_hotkey_unsupported"))

    if key_name_to_vk(settings.exit_hotkey.key) is None:
        errors.append(tr(locale_key, "validation.exit_hotkey_unsupported"))

    if settings.action_mode not in ACTION_CHOICES:
        errors.append(tr(locale_key, "validation.action_mode_unsupported"))

    if settings.action_mode == "mouse" and settings.mouse_button not in MOUSE_BUTTON_CHOICES:
        errors.append(tr(locale_key, "validation.mouse_button_unsupported"))

    if settings.hotkey_scope not in HOTKEY_SCOPE_CHOICES:
        errors.append(tr(locale_key, "validation.hotkey_scope_unsupported"))

    if settings.action_mode == "keyboard":
        if settings.action_key.is_empty():
            errors.append(tr(locale_key, "validation.keyboard_action_required"))
        elif key_name_to_vk(settings.action_key.key) is None:
            errors.append(tr(locale_key, "validation.keyboard_action_unsupported"))
        if settings.action_key.normalized() == settings.toggle_hotkey.normalized():
            errors.append(tr(locale_key, "validation.keyboard_equals_toggle"))
        if settings.action_key.normalized() == settings.exit_hotkey.normalized():
            errors.append(tr(locale_key, "validation.keyboard_equals_exit"))

    if settings.action_mode == "mouse":
        if settings.target_mode not in TARGET_CHOICES:
            errors.append(tr(locale_key, "validation.target_mode_unsupported"))
        if settings.target_mode == "fixed" and (settings.fixed_x < 0 or settings.fixed_y < 0):
            errors.append(tr(locale_key, "validation.fixed_coordinates_invalid"))

    return errors
