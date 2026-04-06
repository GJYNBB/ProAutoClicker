from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(getattr(sys, "_MEIPASS"))
    else:
        base_path = Path(__file__).resolve().parent.parent
    return str(base_path / relative_path)


def load_app_icon() -> QIcon:
    for relative_path in ("assets/app_icon.png", "assets/app_icon.ico"):
        absolute_path = Path(resource_path(relative_path))
        if absolute_path.exists():
            return QIcon(str(absolute_path))
    return QIcon()
