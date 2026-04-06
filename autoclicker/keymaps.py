from __future__ import annotations

MODIFIER_ORDER = ("Ctrl", "Alt", "Shift", "Win")

KEY_NAME_TO_VK = {
    "Backspace": 0x08,
    "Tab": 0x09,
    "Enter": 0x0D,
    "Esc": 0x1B,
    "Space": 0x20,
    "PageUp": 0x21,
    "PageDown": 0x22,
    "End": 0x23,
    "Home": 0x24,
    "Left": 0x25,
    "Up": 0x26,
    "Right": 0x27,
    "Down": 0x28,
    "Insert": 0x2D,
    "Delete": 0x2E,
}

for index in range(10):
    KEY_NAME_TO_VK[str(index)] = 0x30 + index

for index, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    KEY_NAME_TO_VK[letter] = 0x41 + index

for index in range(1, 25):
    KEY_NAME_TO_VK[f"F{index}"] = 0x6F + index

KEY_NAME_ALIASES = {
    "Escape": "Esc",
    "Return": "Enter",
    "PgUp": "PageUp",
    "PgDown": "PageDown",
}


def normalize_key_name(name: str) -> str:
    value = (name or "").strip()
    if not value:
        return ""
    upper = value.upper()
    if len(value) == 1 and upper.isalnum():
        return upper
    title = value[0].upper() + value[1:]
    return KEY_NAME_ALIASES.get(title, title)


def normalize_modifiers(modifiers: tuple[str, ...] | list[str] | set[str]) -> tuple[str, ...]:
    normalized = {modifier for modifier in modifiers if modifier in MODIFIER_ORDER}
    return tuple(name for name in MODIFIER_ORDER if name in normalized)


def key_name_to_vk(name: str) -> int | None:
    return KEY_NAME_TO_VK.get(normalize_key_name(name))
