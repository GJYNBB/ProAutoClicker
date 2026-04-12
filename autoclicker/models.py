from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from autoclicker.i18n import choice_labels, default_preset_name, detect_system_language, normalize_language, tr
from autoclicker.keymaps import MODIFIER_ORDER, key_name_to_vk, normalize_key_name, normalize_modifiers

ACTION_CHOICES = ("mouse", "keyboard")
MOUSE_BUTTON_CHOICES = ("left", "right", "middle")
MOUSE_INTERACTION_CHOICES = ("single", "double", "triple", "hold")
TARGET_CHOICES = ("capture", "fixed")
HOTKEY_SCOPE_CHOICES = ("global", "application")
HUD_ITEM_CHOICES = ("state", "step", "rate", "count")
THEME_CHOICES = ("light", "dark")
SEQUENCE_MODE_CHOICES = ("once", "loop")
LIMIT_MODE_CHOICES = ("infinite", "count", "duration")

LEGACY_MOUSE_ACTIONS = {
    "mouse_left": "left",
    "mouse_right": "right",
    "mouse_middle": "middle",
}


def get_action_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "action", ACTION_CHOICES)


def get_mouse_button_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "mouse_button", MOUSE_BUTTON_CHOICES)


def get_mouse_interaction_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "mouse_interaction", MOUSE_INTERACTION_CHOICES)


def get_target_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "target", TARGET_CHOICES)


def get_hotkey_scope_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "hotkey_scope", HOTKEY_SCOPE_CHOICES)


def get_hud_item_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "hud_item", HUD_ITEM_CHOICES)


def get_theme_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "theme", THEME_CHOICES)


def get_sequence_mode_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "sequence_mode", SEQUENCE_MODE_CHOICES)


def get_limit_mode_labels(language: str | None) -> dict[str, str]:
    return choice_labels(language, "limit_mode", LIMIT_MODE_CHOICES)


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
class ActionUnit:
    name: str = ""
    action_mode: str = "mouse"
    mouse_button: str = "left"
    mouse_interaction: str = "single"
    action_key: KeyCombo = field(default_factory=lambda: KeyCombo("A"))
    target_mode: str = "capture"
    fixed_x: int = 0
    fixed_y: int = 0
    capture_delay_seconds: float = 3.0
    frequency_hz: float = 20.0
    random_interval_enabled: bool = False
    interval_min_ms: int = 30
    interval_max_ms: int = 90
    coordinate_jitter_enabled: bool = False
    jitter_x_px: int = 0
    jitter_y_px: int = 0
    hold_duration_ms: int = 200
    random_hold_enabled: bool = False
    hold_min_ms: int = 120
    hold_max_ms: int = 240
    limit_mode: str = "infinite"
    limit_count: int = 10
    limit_duration_seconds: float = 5.0
    post_delay_ms: int = 0

    def normalized(self, index: int = 0) -> "ActionUnit":
        action_mode, mouse_button = _normalize_action_fields(self.action_mode, self.mouse_button)
        return ActionUnit(
            name=self.name.strip(),
            action_mode=action_mode,
            mouse_button=mouse_button,
            mouse_interaction=_coerce_choice(self.mouse_interaction, MOUSE_INTERACTION_CHOICES, "single"),
            action_key=self.action_key.normalized(),
            target_mode=_coerce_choice(self.target_mode, TARGET_CHOICES, "capture"),
            fixed_x=max(int(self.fixed_x), 0),
            fixed_y=max(int(self.fixed_y), 0),
            capture_delay_seconds=max(float(self.capture_delay_seconds), 0.0),
            frequency_hz=max(float(self.frequency_hz), 0.1),
            random_interval_enabled=bool(self.random_interval_enabled),
            interval_min_ms=max(int(self.interval_min_ms), 1),
            interval_max_ms=max(int(self.interval_max_ms), 1),
            coordinate_jitter_enabled=bool(self.coordinate_jitter_enabled),
            jitter_x_px=max(int(self.jitter_x_px), 0),
            jitter_y_px=max(int(self.jitter_y_px), 0),
            hold_duration_ms=max(int(self.hold_duration_ms), 1),
            random_hold_enabled=bool(self.random_hold_enabled),
            hold_min_ms=max(int(self.hold_min_ms), 1),
            hold_max_ms=max(int(self.hold_max_ms), 1),
            limit_mode=_coerce_choice(self.limit_mode, LIMIT_MODE_CHOICES, "infinite" if index == 0 else "count"),
            limit_count=max(int(self.limit_count), 1),
            limit_duration_seconds=max(float(self.limit_duration_seconds), 0.1),
            post_delay_ms=max(int(self.post_delay_ms), 0),
        )

    def to_dict(self) -> dict[str, Any]:
        normalized = self.normalized()
        return {
            "name": normalized.name,
            "action_mode": normalized.action_mode,
            "mouse_button": normalized.mouse_button,
            "mouse_interaction": normalized.mouse_interaction,
            "action_key": normalized.action_key.to_dict(),
            "target_mode": normalized.target_mode,
            "fixed_x": normalized.fixed_x,
            "fixed_y": normalized.fixed_y,
            "capture_delay_seconds": normalized.capture_delay_seconds,
            "frequency_hz": normalized.frequency_hz,
            "random_interval_enabled": normalized.random_interval_enabled,
            "interval_min_ms": normalized.interval_min_ms,
            "interval_max_ms": normalized.interval_max_ms,
            "coordinate_jitter_enabled": normalized.coordinate_jitter_enabled,
            "jitter_x_px": normalized.jitter_x_px,
            "jitter_y_px": normalized.jitter_y_px,
            "hold_duration_ms": normalized.hold_duration_ms,
            "random_hold_enabled": normalized.random_hold_enabled,
            "hold_min_ms": normalized.hold_min_ms,
            "hold_max_ms": normalized.hold_max_ms,
            "limit_mode": normalized.limit_mode,
            "limit_count": normalized.limit_count,
            "limit_duration_seconds": normalized.limit_duration_seconds,
            "post_delay_ms": normalized.post_delay_ms,
        }

    @staticmethod
    def from_dict(data: dict[str, Any] | None, *, index: int = 0) -> "ActionUnit":
        if not isinstance(data, dict):
            return default_action_unit(index)

        action_mode, mouse_button = _normalize_action_fields(
            data.get("action_mode"),
            data.get("mouse_button"),
        )
        return ActionUnit(
            name=str(data.get("name", "")).strip(),
            action_mode=action_mode,
            mouse_button=mouse_button,
            mouse_interaction=_coerce_choice(
                data.get("mouse_interaction"),
                MOUSE_INTERACTION_CHOICES,
                "single",
            ),
            action_key=KeyCombo.from_dict(data.get("action_key")),
            target_mode=_coerce_choice(data.get("target_mode"), TARGET_CHOICES, "capture"),
            fixed_x=max(_coerce_int(data.get("fixed_x", 0), 0), 0),
            fixed_y=max(_coerce_int(data.get("fixed_y", 0), 0), 0),
            capture_delay_seconds=max(_coerce_float(data.get("capture_delay_seconds", 3.0), 3.0), 0.0),
            frequency_hz=max(_coerce_float(data.get("frequency_hz", 20.0), 20.0), 0.1),
            random_interval_enabled=_coerce_bool(data.get("random_interval_enabled", False), False),
            interval_min_ms=max(_coerce_int(data.get("interval_min_ms", 30), 30), 1),
            interval_max_ms=max(_coerce_int(data.get("interval_max_ms", 90), 90), 1),
            coordinate_jitter_enabled=_coerce_bool(data.get("coordinate_jitter_enabled", False), False),
            jitter_x_px=max(_coerce_int(data.get("jitter_x_px", 0), 0), 0),
            jitter_y_px=max(_coerce_int(data.get("jitter_y_px", 0), 0), 0),
            hold_duration_ms=max(_coerce_int(data.get("hold_duration_ms", 200), 200), 1),
            random_hold_enabled=_coerce_bool(data.get("random_hold_enabled", False), False),
            hold_min_ms=max(_coerce_int(data.get("hold_min_ms", 120), 120), 1),
            hold_max_ms=max(_coerce_int(data.get("hold_max_ms", 240), 240), 1),
            limit_mode=_coerce_choice(
                data.get("limit_mode"),
                LIMIT_MODE_CHOICES,
                "infinite" if index == 0 else "count",
            ),
            limit_count=max(_coerce_int(data.get("limit_count", 10), 10), 1),
            limit_duration_seconds=max(_coerce_float(data.get("limit_duration_seconds", 5.0), 5.0), 0.1),
            post_delay_ms=max(_coerce_int(data.get("post_delay_ms", 0), 0), 0),
        ).normalized(index)


def default_action_unit(index: int = 0) -> ActionUnit:
    if index == 0:
        return ActionUnit(name="", limit_mode="infinite")
    return ActionUnit(
        name="",
        limit_mode="count",
        limit_count=1,
        capture_delay_seconds=0.0,
        post_delay_ms=150,
    )


def _legacy_action_unit(data: dict[str, Any]) -> ActionUnit:
    action_mode, mouse_button = _normalize_action_fields(
        data.get("action_mode"),
        data.get("mouse_button"),
    )
    return ActionUnit(
        name="",
        action_mode=action_mode,
        mouse_button=mouse_button,
        mouse_interaction="single",
        action_key=KeyCombo.from_dict(data.get("action_key")),
        target_mode=_coerce_choice(data.get("target_mode"), TARGET_CHOICES, "capture"),
        fixed_x=max(_coerce_int(data.get("fixed_x", 0), 0), 0),
        fixed_y=max(_coerce_int(data.get("fixed_y", 0), 0), 0),
        capture_delay_seconds=max(_coerce_float(data.get("capture_delay_seconds", 3.0), 3.0), 0.0),
        frequency_hz=max(_coerce_float(data.get("frequency_hz", 20.0), 20.0), 0.1),
        limit_mode="infinite",
    ).normalized(0)


@dataclass
class AppSettings:
    sequence_mode: str = "once"
    hotkey_scope: str = "global"
    toggle_hotkey: KeyCombo = field(default_factory=lambda: KeyCombo("F2"))
    exit_hotkey: KeyCombo = field(default_factory=lambda: KeyCombo("Esc"))
    minimize_to_tray: bool = True
    actions: list[ActionUnit] = field(default_factory=lambda: [default_action_unit(0)])

    def normalized(self) -> "AppSettings":
        actions = [ActionUnit.from_dict(item.to_dict(), index=index) for index, item in enumerate(self.actions or [])]
        if not actions:
            actions = [default_action_unit(0)]
        return AppSettings(
            sequence_mode=_coerce_choice(self.sequence_mode, SEQUENCE_MODE_CHOICES, "once"),
            hotkey_scope=_coerce_choice(self.hotkey_scope, HOTKEY_SCOPE_CHOICES, "global"),
            toggle_hotkey=self.toggle_hotkey.normalized(),
            exit_hotkey=self.exit_hotkey.normalized(),
            minimize_to_tray=bool(self.minimize_to_tray),
            actions=actions,
        )

    def to_dict(self) -> dict[str, Any]:
        normalized = self.normalized()
        return {
            "sequence_mode": normalized.sequence_mode,
            "hotkey_scope": normalized.hotkey_scope,
            "toggle_hotkey": normalized.toggle_hotkey.to_dict(),
            "exit_hotkey": normalized.exit_hotkey.to_dict(),
            "minimize_to_tray": normalized.minimize_to_tray,
            "actions": [action.to_dict() for action in normalized.actions],
        }

    @staticmethod
    def from_dict(data: dict[str, Any] | None) -> "AppSettings":
        if not isinstance(data, dict):
            return AppSettings()

        raw_actions = data.get("actions")
        actions: list[ActionUnit]
        if isinstance(raw_actions, list) and raw_actions:
            actions = [ActionUnit.from_dict(item, index=index) for index, item in enumerate(raw_actions)]
        else:
            actions = [_legacy_action_unit(data)]

        return AppSettings(
            sequence_mode=_coerce_choice(data.get("sequence_mode"), SEQUENCE_MODE_CHOICES, "once"),
            hotkey_scope=_coerce_choice(data.get("hotkey_scope"), HOTKEY_SCOPE_CHOICES, "global"),
            toggle_hotkey=KeyCombo.from_dict(data.get("toggle_hotkey")),
            exit_hotkey=KeyCombo.from_dict(data.get("exit_hotkey")),
            minimize_to_tray=_coerce_bool(data.get("minimize_to_tray", True), True),
            actions=actions,
        ).normalized()

    def first_action(self) -> ActionUnit:
        if not self.actions:
            self.actions.append(default_action_unit(0))
        return self.actions[0]


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
    hud_items: tuple[str, ...] = field(default_factory=lambda: ("state", "step", "rate", "count"))
    hud_x: int = 24
    hud_y: int = 24
    hud_opacity_percent: int = 85

    def to_dict(self) -> dict[str, Any]:
        return {
            "hud_enabled": self.hud_enabled,
            "hud_items": list(self.hud_items),
            "hud_x": self.hud_x,
            "hud_y": self.hud_y,
            "hud_opacity_percent": self.hud_opacity_percent,
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
            hud_opacity_percent=min(max(_coerce_int(data.get("hud_opacity_percent", 85), 85), 15), 100),
        )


@dataclass
class PersistedState:
    schema_version: int = 5
    language: str = field(default_factory=detect_system_language)
    theme: str = "light"
    selected_preset: str = field(default_factory=default_preset_name)
    last_settings: AppSettings = field(default_factory=AppSettings)
    overlay: OverlaySettings = field(default_factory=OverlaySettings)
    presets: list[Preset] = field(default_factory=lambda: [Preset(name=default_preset_name(), settings=AppSettings())])

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "language": self.language,
            "theme": self.theme,
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
            schema_version=_coerce_int(data.get("schema_version", 5), 5),
            language=language,
            theme=_coerce_choice(data.get("theme"), THEME_CHOICES, "light"),
            selected_preset=str(data.get("selected_preset", fallback_name)).strip() or fallback_name,
            last_settings=AppSettings.from_dict(data.get("last_settings")),
            overlay=OverlaySettings.from_dict(data.get("overlay")),
            presets=presets,
        )


@dataclass
class ValidationResult:
    general_errors: list[str] = field(default_factory=list)
    field_errors: dict[str, list[str]] = field(default_factory=dict)

    def add(self, message: str, field: str | None = None) -> None:
        if field:
            self.field_errors.setdefault(field, []).append(message)
            return
        self.general_errors.append(message)

    @property
    def is_valid(self) -> bool:
        return not self.general_errors and not self.field_errors

    def messages(self) -> list[str]:
        merged = list(self.general_errors)
        for field_messages in self.field_errors.values():
            merged.extend(field_messages)
        seen: set[str] = set()
        ordered: list[str] = []
        for message in merged:
            if message and message not in seen:
                seen.add(message)
                ordered.append(message)
        return ordered

    def first_message_for(self, field: str) -> str | None:
        messages = self.field_errors.get(field)
        if messages:
            return messages[0]
        return None

    def action_errors(self, index: int) -> dict[str, list[str]]:
        prefix = f"actions.{index}."
        result: dict[str, list[str]] = {}
        for field, messages in self.field_errors.items():
            if field.startswith(prefix):
                result[field[len(prefix) :]] = messages
        return result


def format_action_unit_label(action: ActionUnit, language: str | None = None) -> str:
    locale_key = normalize_language(language)
    normalized = action.normalized()
    if normalized.action_mode == "keyboard":
        combo = normalized.action_key.display_text() or tr(locale_key, "summary.not_set")
        return tr(locale_key, "summary.action.keyboard_short", combo=combo)
    return tr(
        locale_key,
        "summary.action.mouse_short",
        button=tr(locale_key, f"mouse_button.{normalized.mouse_button}"),
        interaction=tr(locale_key, f"mouse_interaction.{normalized.mouse_interaction}"),
    )


def format_action_label(settings: AppSettings, language: str | None = None) -> str:
    return format_action_unit_label(settings.first_action(), language)


def summarize_action_unit(action: ActionUnit, language: str | None = None) -> str:
    locale_key = normalize_language(language)
    normalized = action.normalized()
    label = normalized.name or format_action_unit_label(normalized, locale_key)

    limit_text = tr(locale_key, f"limit_mode.{normalized.limit_mode}")
    if normalized.limit_mode == "count":
        limit_text = tr(locale_key, "summary.limit.count", count=normalized.limit_count)
    elif normalized.limit_mode == "duration":
        limit_text = tr(locale_key, "summary.limit.duration", seconds=normalized.limit_duration_seconds)

    if normalized.random_interval_enabled:
        interval_text = tr(
            locale_key,
            "summary.interval.random",
            minimum=normalized.interval_min_ms,
            maximum=normalized.interval_max_ms,
        )
    else:
        interval_text = tr(locale_key, "summary.interval.fixed", frequency=normalized.frequency_hz)

    target_text = tr(locale_key, "summary.target.not_applicable")
    if normalized.action_mode == "mouse":
        if normalized.target_mode == "capture":
            target_text = tr(locale_key, "summary.target.capture", seconds=normalized.capture_delay_seconds)
        else:
            target_text = tr(locale_key, "summary.target.fixed", x=normalized.fixed_x, y=normalized.fixed_y)

    return tr(
        locale_key,
        "summary.sequence_item",
        label=label,
        interval=interval_text,
        target=target_text,
        limit=limit_text,
        post_delay=normalized.post_delay_ms,
    )


def validate_settings(settings: AppSettings, language: str | None = None) -> ValidationResult:
    locale_key = normalize_language(language)
    normalized = settings.normalized()
    result = ValidationResult()

    if normalized.sequence_mode not in SEQUENCE_MODE_CHOICES:
        result.add(tr(locale_key, "validation.sequence_mode_unsupported"), "sequence_mode")

    if normalized.hotkey_scope not in HOTKEY_SCOPE_CHOICES:
        result.add(tr(locale_key, "validation.hotkey_scope_unsupported"), "hotkey_scope")

    if normalized.toggle_hotkey.is_empty():
        result.add(tr(locale_key, "validation.toggle_hotkey_required"), "toggle_hotkey")
    elif key_name_to_vk(normalized.toggle_hotkey.key) is None:
        result.add(tr(locale_key, "validation.toggle_hotkey_unsupported"), "toggle_hotkey")

    if normalized.exit_hotkey.is_empty():
        result.add(tr(locale_key, "validation.exit_hotkey_required"), "exit_hotkey")
    elif key_name_to_vk(normalized.exit_hotkey.key) is None:
        result.add(tr(locale_key, "validation.exit_hotkey_unsupported"), "exit_hotkey")

    if normalized.toggle_hotkey.normalized() == normalized.exit_hotkey.normalized():
        result.add(tr(locale_key, "validation.hotkeys_must_differ"), "toggle_hotkey")
        result.add(tr(locale_key, "validation.hotkeys_must_differ"), "exit_hotkey")

    if not normalized.actions:
        result.add(tr(locale_key, "validation.action_required"))
        return result

    if len(normalized.actions) > 1 and normalized.actions[0].limit_mode == "infinite":
        result.add(tr(locale_key, "validation.infinite_requires_single_action"), "actions.0.limit_mode")

    for index, action in enumerate(normalized.actions):
        prefix = f"actions.{index}."
        if action.action_mode not in ACTION_CHOICES:
            result.add(tr(locale_key, "validation.action_mode_unsupported"), prefix + "action_mode")

        if action.frequency_hz < 0.1 or action.frequency_hz > 1000.0:
            result.add(tr(locale_key, "validation.frequency_range"), prefix + "frequency_hz")

        if action.random_interval_enabled:
            if action.interval_min_ms < 1 or action.interval_max_ms < 1:
                result.add(tr(locale_key, "validation.interval_range"), prefix + "interval_min_ms")
            if action.interval_min_ms > action.interval_max_ms:
                result.add(tr(locale_key, "validation.interval_order"), prefix + "interval_min_ms")
                result.add(tr(locale_key, "validation.interval_order"), prefix + "interval_max_ms")

        if action.random_hold_enabled:
            if action.hold_min_ms < 1 or action.hold_max_ms < 1:
                result.add(tr(locale_key, "validation.hold_range"), prefix + "hold_min_ms")
            if action.hold_min_ms > action.hold_max_ms:
                result.add(tr(locale_key, "validation.hold_order"), prefix + "hold_min_ms")
                result.add(tr(locale_key, "validation.hold_order"), prefix + "hold_max_ms")

        if action.hold_duration_ms < 1 or action.hold_duration_ms > 600000:
            result.add(tr(locale_key, "validation.hold_range"), prefix + "hold_duration_ms")

        if action.limit_mode not in LIMIT_MODE_CHOICES:
            result.add(tr(locale_key, "validation.limit_mode_unsupported"), prefix + "limit_mode")
        elif action.limit_mode == "count" and action.limit_count < 1:
            result.add(tr(locale_key, "validation.limit_count_range"), prefix + "limit_count")
        elif action.limit_mode == "duration" and action.limit_duration_seconds <= 0:
            result.add(tr(locale_key, "validation.limit_duration_range"), prefix + "limit_duration_seconds")
        elif action.limit_mode == "infinite" and index > 0:
            result.add(tr(locale_key, "validation.infinite_only_first_action"), prefix + "limit_mode")

        if action.post_delay_ms < 0 or action.post_delay_ms > 600000:
            result.add(tr(locale_key, "validation.post_delay_range"), prefix + "post_delay_ms")

        if action.action_mode == "keyboard":
            if action.action_key.is_empty():
                result.add(tr(locale_key, "validation.keyboard_action_required"), prefix + "action_key")
            elif key_name_to_vk(action.action_key.key) is None:
                result.add(tr(locale_key, "validation.keyboard_action_unsupported"), prefix + "action_key")
            if action.action_key.normalized() == normalized.toggle_hotkey.normalized():
                result.add(tr(locale_key, "validation.keyboard_equals_toggle"), prefix + "action_key")
            if action.action_key.normalized() == normalized.exit_hotkey.normalized():
                result.add(tr(locale_key, "validation.keyboard_equals_exit"), prefix + "action_key")

        if action.action_mode == "mouse":
            if action.mouse_button not in MOUSE_BUTTON_CHOICES:
                result.add(tr(locale_key, "validation.mouse_button_unsupported"), prefix + "mouse_button")
            if action.mouse_interaction not in MOUSE_INTERACTION_CHOICES:
                result.add(tr(locale_key, "validation.mouse_interaction_unsupported"), prefix + "mouse_interaction")
            if action.target_mode not in TARGET_CHOICES:
                result.add(tr(locale_key, "validation.target_mode_unsupported"), prefix + "target_mode")
            if action.capture_delay_seconds < 0 or action.capture_delay_seconds > 60:
                result.add(tr(locale_key, "validation.capture_delay_range"), prefix + "capture_delay_seconds")
            if action.target_mode == "fixed" and (action.fixed_x < 0 or action.fixed_y < 0):
                result.add(tr(locale_key, "validation.fixed_coordinates_invalid"), prefix + "fixed_x")
            if action.coordinate_jitter_enabled and (action.jitter_x_px < 0 or action.jitter_y_px < 0):
                result.add(tr(locale_key, "validation.jitter_range"), prefix + "jitter_x_px")

    return result
