"""Lightweight in-memory metrics registry (uptime, counters)."""

import threading
import time
from datetime import datetime, timezone


class Metrics:
    def __init__(self) -> None:
        self._started = time.monotonic()
        self._started_dt = datetime.now(timezone.utc)
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}

    def inc(self, name: str, by: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + by

    def get(self, name: str) -> int:
        with self._lock:
            return self._counters.get(name, 0)

    def uptime_seconds(self) -> int:
        return int(time.monotonic() - self._started)

    def snapshot(self) -> dict:
        with self._lock:
            counters = dict(self._counters)
        return {
            "uptime_seconds": self.uptime_seconds(),
            "started": self._started_dt.isoformat(),
            "counters": counters,
        }


metrics = Metrics()
