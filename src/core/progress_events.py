from __future__ import annotations

from typing import Any, Callable, List

PROGRESS_ERROR = -1
PROGRESS_INDETERMINATE = -2


class ProgressEventBus:
    def __init__(self):
        self._progress_listeners: List[Callable[[str, int], None]] = []
        self._log_listeners: List[Callable[[str], None]] = []
        self._done_listeners: List[Callable[[dict], None]] = []

    def on_progress(self, cb: Callable[[str, int], None]):
        self._progress_listeners.append(cb)

    def on_log(self, cb: Callable[[str], None]):
        self._log_listeners.append(cb)

    def on_done(self, cb: Callable[[dict], None]):
        self._done_listeners.append(cb)

    def emit_progress(self, status: str, pct: int):
        for cb in self._progress_listeners:
            cb(status, pct)

    def emit_log(self, message: str):
        for cb in self._log_listeners:
            cb(message)

    def emit_done(self, report: dict):
        for cb in self._done_listeners:
            cb(report)
