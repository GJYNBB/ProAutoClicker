from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Any

import requests
from PySide6.QtCore import QObject, Signal


GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/GJYNBB/ProAutoClicker/releases/latest"


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    url: str
    name: str = ""


def _version_parts(version: str) -> tuple[int, ...]:
    text = version.strip().lstrip("vV")
    return tuple(int(part) for part in re.findall(r"\d+", text))


def is_newer_version(latest: str, current: str) -> bool:
    latest_parts = _version_parts(latest)
    current_parts = _version_parts(current)
    width = max(len(latest_parts), len(current_parts))
    latest_parts = latest_parts + (0,) * (width - len(latest_parts))
    current_parts = current_parts + (0,) * (width - len(current_parts))
    return latest_parts > current_parts


def fetch_latest_release(timeout_seconds: float = 5.0) -> ReleaseInfo:
    response = requests.get(
        GITHUB_LATEST_RELEASE_API,
        headers={"Accept": "application/vnd.github+json"},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    return ReleaseInfo(
        version=str(payload.get("tag_name", "")).strip(),
        url=str(payload.get("html_url", "")).strip(),
        name=str(payload.get("name", "")).strip(),
    )


class UpdateChecker(QObject):
    update_available = Signal(str, str, str)
    up_to_date = Signal(str)
    check_failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def check_async(self, current_version: str) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._check, args=(current_version,), daemon=True)
            self._thread.start()

    def _check(self, current_version: str) -> None:
        try:
            release = fetch_latest_release()
            if release.version and is_newer_version(release.version, current_version):
                self.update_available.emit(release.version, release.url, release.name)
                return
            self.up_to_date.emit(release.version or current_version)
        except Exception as exc:  # noqa: BLE001 - UI should surface any network/check failure uniformly.
            self.check_failed.emit(str(exc))
