from __future__ import annotations

import threading
import time

from PySide6.QtCore import QObject, Signal

from autoclicker.i18n import detect_system_language, normalize_language, tr
from autoclicker.models import AppSettings, format_action_label
from autoclicker.win32_backend import click_mouse, get_cursor_position, send_key_combo


class AutomationController(QObject):
    state_changed = Signal(str)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    position_captured = Signal(int, int)
    action_count_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._state = "idle"
        self._worker: threading.Thread | None = None
        self._stop_event: threading.Event | None = None
        self._lock = threading.Lock()
        self._action_count = 0
        self._language = detect_system_language()

    @property
    def state(self) -> str:
        return self._state

    def set_language(self, language: str | None) -> None:
        self._language = normalize_language(language)

    def start(self, settings: AppSettings, language: str | None = None) -> None:
        locale_key = normalize_language(language)
        self._language = locale_key
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                return
            self._action_count = 0
            self.action_count_changed.emit(0)
            self._stop_event = threading.Event()
            self._worker = threading.Thread(
                target=self._run_session,
                args=(settings, self._stop_event, locale_key),
                daemon=True,
            )
            self._worker.start()

    def pause(self) -> None:
        with self._lock:
            stop_event = self._stop_event
        if stop_event is not None:
            stop_event.set()
        self._set_state("paused", tr(self._language, "controller.paused"))

    def shutdown(self) -> None:
        with self._lock:
            stop_event = self._stop_event
        if stop_event is not None:
            stop_event.set()
        self._set_state("idle", tr(self._language, "status.ready"))

    def toggle(self, settings: AppSettings, language: str | None = None) -> None:
        if self._state in {"running", "countdown"}:
            self.pause()
        else:
            self.start(settings, language)

    def _run_session(self, settings: AppSettings, stop_event: threading.Event, language: str) -> None:
        try:
            target: tuple[int, int] | None = None

            if settings.action_mode == "mouse":
                if settings.target_mode == "capture":
                    self._set_state("countdown", tr(language, "controller.waiting_capture"))
                    capture_result = self._capture_target(settings.capture_delay_seconds, stop_event, language)
                    if capture_result is None:
                        if stop_event.is_set():
                            return
                        self.error_occurred.emit(tr(language, "controller.capture_position_failed"))
                        self._set_state("paused", tr(language, "controller.capture_failed"))
                        return
                    target = capture_result
                    self.position_captured.emit(target[0], target[1])
                    self.status_changed.emit(tr(language, "controller.captured_position", x=target[0], y=target[1]))
                else:
                    target = (settings.fixed_x, settings.fixed_y)

            action_label = format_action_label(settings, language)
            self._set_state("running", tr(language, "controller.running", action=action_label))
            self._execution_loop(settings, stop_event, target, language)
        except OSError as exc:
            self.error_occurred.emit(str(exc))
            self._set_state("paused", tr(language, "controller.execution_error"))
        finally:
            with self._lock:
                self._worker = None
                self._stop_event = None
            if self._state == "running" and not stop_event.is_set():
                self._set_state("idle", tr(language, "status.ready"))

    def _capture_target(self, delay_seconds: float, stop_event: threading.Event, language: str) -> tuple[int, int] | None:
        if delay_seconds > 0:
            remaining = int(delay_seconds)
            while remaining > 0:
                self.status_changed.emit(tr(language, "controller.countdown", seconds=remaining))
                for _ in range(10):
                    if stop_event.is_set():
                        return None
                    time.sleep(0.1)
                remaining -= 1
            fractional = delay_seconds - int(delay_seconds)
            if fractional > 0:
                end_time = time.perf_counter() + fractional
                while time.perf_counter() < end_time:
                    if stop_event.is_set():
                        return None
                    time.sleep(0.02)
        return get_cursor_position()

    def _execution_loop(
        self,
        settings: AppSettings,
        stop_event: threading.Event,
        target: tuple[int, int] | None,
        language: str,
    ) -> None:
        interval = 1.0 / settings.frequency_hz
        next_run = time.perf_counter()
        last_count_emit = 0.0

        while not stop_event.is_set():
            if settings.action_mode == "mouse":
                if target is None:
                    raise OSError(tr(language, "error.mouse_target_required"))
                click_mouse(settings.mouse_button, target[0], target[1])
            else:
                send_key_combo(settings.action_key, language)

            self._action_count += 1
            now = time.perf_counter()
            if now - last_count_emit >= 0.25:
                self.action_count_changed.emit(self._action_count)
                last_count_emit = now

            next_run += interval
            sleep_for = next_run - time.perf_counter()
            if sleep_for > 0:
                time.sleep(min(sleep_for, 0.2))
            else:
                next_run = time.perf_counter()

    def _set_state(self, state: str, status: str) -> None:
        self._state = state
        self.state_changed.emit(state)
        self.status_changed.emit(status)
