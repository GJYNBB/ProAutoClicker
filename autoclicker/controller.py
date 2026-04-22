from __future__ import annotations

import random
import threading
import time
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from autoclicker.input_backend import InputBackend, create_input_backend
from autoclicker.i18n import detect_system_language, normalize_language, tr
from autoclicker.models import AppSettings, ActionUnit, format_action_unit_label


class AutomationController(QObject):
    state_changed = Signal(str)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    position_captured = Signal(int, int)
    action_count_changed = Signal(int)
    actual_frequency_changed = Signal(float)
    current_step_changed = Signal(int, str)
    last_action_changed = Signal(str)

    def __init__(self, backend: InputBackend | None = None) -> None:
        super().__init__()
        self._backend = backend or create_input_backend()
        self._state = "idle"
        self._worker: threading.Thread | None = None
        self._stop_event: threading.Event | None = None
        self._lock = threading.Lock()
        self._action_count = 0
        self._run_started_at: float | None = None
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
            self._run_started_at = None
            self._emit_runtime_metrics(force_zero=True)
            self.current_step_changed.emit(-1, "")
            self.last_action_changed.emit("")
            self._stop_event = threading.Event()
            session_settings = AppSettings.from_dict(settings.to_dict())
            self._worker = threading.Thread(
                target=self._run_session,
                args=(session_settings, self._stop_event, locale_key),
                daemon=True,
            )
            self._worker.start()

    def pause(self) -> None:
        with self._lock:
            stop_event = self._stop_event
        if stop_event is not None:
            stop_event.set()
        self._emit_runtime_metrics(force_zero=True)
        self.current_step_changed.emit(-1, "")
        self._set_state("paused", tr(self._language, "controller.paused"))

    def shutdown(self) -> None:
        with self._lock:
            stop_event = self._stop_event
        if stop_event is not None:
            stop_event.set()
        self._emit_runtime_metrics(force_zero=True)
        self.current_step_changed.emit(-1, "")
        self.last_action_changed.emit("")
        self._set_state("idle", tr(self._language, "status.ready"))

    def toggle(self, settings: AppSettings, language: str | None = None) -> None:
        if self._state in {"running", "countdown"}:
            self.pause()
        else:
            self.start(settings, language)

    def _run_session(self, settings: AppSettings, stop_event: threading.Event, language: str) -> None:
        completed_normally = False
        try:
            self._run_started_at = time.perf_counter()
            self._emit_runtime_metrics()
            total_steps = len(settings.actions)
            if total_steps <= 0:
                raise OSError(tr(language, "validation.action_required"))

            while not stop_event.is_set():
                for index, action in enumerate(settings.actions):
                    if stop_event.is_set():
                        break
                    step_label = action.name or format_action_unit_label(action, language)
                    self.current_step_changed.emit(index, step_label)
                    self.status_changed.emit(
                        tr(
                            language,
                            "controller.sequence_step",
                            index=index + 1,
                            total=total_steps,
                            action=step_label,
                        )
                    )
                    self._set_state("running", tr(language, "controller.running", action=step_label))
                    self._execute_action_unit(
                        action,
                        index,
                        stop_event,
                        language,
                        settings.safety_countdown_seconds,
                    )
                if stop_event.is_set():
                    break
                if settings.sequence_mode == "once":
                    completed_normally = True
                    break
            if not stop_event.is_set() and settings.sequence_mode == "loop":
                completed_normally = False
        except OSError as exc:
            self.error_occurred.emit(str(exc))
            self._set_state("paused", tr(language, "controller.execution_error"))
        finally:
            with self._lock:
                self._worker = None
                self._stop_event = None
            self._emit_runtime_metrics(force_zero=True)
            self.current_step_changed.emit(-1, "")
            if completed_normally and not stop_event.is_set():
                self._set_state("idle", tr(language, "status.ready"))

    def _execute_action_unit(
        self,
        action: ActionUnit,
        index: int,
        stop_event: threading.Event,
        language: str,
        safety_countdown_seconds: float = 0.0,
    ) -> None:
        target: tuple[int, int] | None = None
        if action.action_mode == "mouse":
            target = self._resolve_mouse_target(action, stop_event, language)
            if target is None:
                if stop_event.is_set():
                    return
                raise OSError(tr(language, "error.mouse_target_required"))

        started_at = time.perf_counter()
        executed = 0
        last_metrics_emit = started_at

        while not stop_event.is_set():
            if safety_countdown_seconds > 0 and self._safety_countdown(safety_countdown_seconds, stop_event, language):
                return

            if action.action_mode == "mouse":
                assert target is not None
                x, y = self._apply_jitter(target, action)
                self._perform_mouse_action(action, x, y, stop_event)
            else:
                self._perform_keyboard_action(action, stop_event, language)

            executed += 1
            self._action_count += 1
            self.last_action_changed.emit(
                tr(
                    language,
                    "controller.last_action",
                    time=datetime.now().strftime("%H:%M:%S"),
                    count=self._action_count,
                )
            )
            now = time.perf_counter()
            if now - last_metrics_emit >= 0.25:
                self._emit_runtime_metrics(now=now)
                last_metrics_emit = now

            if action.limit_mode == "count" and executed >= action.limit_count:
                break
            if action.limit_mode == "duration" and (now - started_at) >= action.limit_duration_seconds:
                break

            interval_seconds = self._effective_interval_seconds(action)
            if interval_seconds > 0 and self._wait(interval_seconds, stop_event):
                return

        if not stop_event.is_set() and action.post_delay_ms > 0:
            self._wait(action.post_delay_ms / 1000.0, stop_event)

    def _resolve_mouse_target(
        self,
        action: ActionUnit,
        stop_event: threading.Event,
        language: str,
    ) -> tuple[int, int] | None:
        if action.target_mode == "fixed":
            return action.fixed_x, action.fixed_y

        self._set_state("countdown", tr(language, "controller.waiting_capture"))
        capture_result = self._capture_target(action.capture_delay_seconds, stop_event, language)
        if capture_result is None:
            if stop_event.is_set():
                return None
            self.error_occurred.emit(tr(language, "controller.capture_position_failed"))
            self._set_state("paused", tr(language, "controller.capture_failed"))
            return None

        self.position_captured.emit(capture_result[0], capture_result[1])
        self.status_changed.emit(
            tr(language, "controller.captured_position", x=capture_result[0], y=capture_result[1])
        )
        return capture_result

    def _capture_target(
        self,
        delay_seconds: float,
        stop_event: threading.Event,
        language: str,
    ) -> tuple[int, int] | None:
        if delay_seconds > 0:
            end_time = time.perf_counter() + delay_seconds
            last_announce = None
            while True:
                if stop_event.is_set():
                    return None
                remaining = max(end_time - time.perf_counter(), 0.0)
                remaining_int = int(remaining + 0.999)
                if remaining_int > 0 and remaining_int != last_announce:
                    self.status_changed.emit(tr(language, "controller.countdown", seconds=remaining_int))
                    last_announce = remaining_int
                if remaining <= 0:
                    break
                time.sleep(min(remaining, 0.05))
        return self._backend.get_cursor_position()

    def _perform_mouse_action(
        self,
        action: ActionUnit,
        x: int,
        y: int,
        stop_event: threading.Event,
    ) -> None:
        if action.mouse_interaction == "hold":
            self._backend.mouse_down(action.mouse_button, x, y)
            try:
                self._wait(self._effective_hold_seconds(action), stop_event)
            finally:
                self._backend.mouse_up(action.mouse_button)
            return

        repeat = {"single": 1, "double": 2, "triple": 3}.get(action.mouse_interaction, 1)
        for click_index in range(repeat):
            if stop_event.is_set():
                return
            self._backend.click_mouse(action.mouse_button, x, y)
            if click_index < repeat - 1:
                self._wait(0.04, stop_event)

    def _perform_keyboard_action(
        self,
        action: ActionUnit,
        stop_event: threading.Event,
        language: str,
    ) -> None:
        hold_seconds = self._effective_hold_seconds(action)
        if hold_seconds <= 0.03:
            self._backend.send_key_combo(action.action_key, language)
            return

        self._backend.key_combo_down(action.action_key, language)
        try:
            self._wait(hold_seconds, stop_event)
        finally:
            self._backend.key_combo_up(action.action_key, language)

    def _safety_countdown(self, delay_seconds: float, stop_event: threading.Event, language: str) -> bool:
        end_time = time.perf_counter() + max(delay_seconds, 0.0)
        last_announce = None
        while True:
            if stop_event.is_set():
                return True
            remaining = max(end_time - time.perf_counter(), 0.0)
            remaining_int = int(remaining + 0.999)
            if remaining_int > 0 and remaining_int != last_announce:
                self.status_changed.emit(tr(language, "controller.safety_countdown", seconds=remaining_int))
                last_announce = remaining_int
            if remaining <= 0:
                break
            time.sleep(min(remaining, 0.05))
        return stop_event.is_set()

    def _effective_interval_seconds(self, action: ActionUnit) -> float:
        if action.random_interval_enabled:
            return random.uniform(action.interval_min_ms, action.interval_max_ms) / 1000.0
        return 1.0 / max(action.frequency_hz, 0.1)

    def _effective_hold_seconds(self, action: ActionUnit) -> float:
        if action.random_hold_enabled:
            milliseconds = random.uniform(action.hold_min_ms, action.hold_max_ms)
        else:
            milliseconds = action.hold_duration_ms
        return max(milliseconds, 1.0) / 1000.0

    def _apply_jitter(self, target: tuple[int, int], action: ActionUnit) -> tuple[int, int]:
        if not action.coordinate_jitter_enabled:
            return target
        return (
            max(target[0] + random.randint(-action.jitter_x_px, action.jitter_x_px), 0),
            max(target[1] + random.randint(-action.jitter_y_px, action.jitter_y_px), 0),
        )

    def _wait(self, seconds: float, stop_event: threading.Event) -> bool:
        if seconds <= 0:
            return stop_event.is_set()
        end_time = time.perf_counter() + seconds
        while time.perf_counter() < end_time:
            if stop_event.is_set():
                return True
            time.sleep(min(end_time - time.perf_counter(), 0.02))
        return stop_event.is_set()

    def _emit_runtime_metrics(self, now: float | None = None, *, force_zero: bool = False) -> None:
        self.action_count_changed.emit(self._action_count)
        if force_zero or self._run_started_at is None or self._action_count <= 0:
            if force_zero:
                self._run_started_at = None
            self.actual_frequency_changed.emit(0.0)
            return

        current_time = now if now is not None else time.perf_counter()
        elapsed = max(current_time - self._run_started_at, 1e-9)
        self.actual_frequency_changed.emit(self._action_count / elapsed)

    def _set_state(self, state: str, status: str) -> None:
        self._state = state
        self.state_changed.emit(state)
        self.status_changed.emit(status)
