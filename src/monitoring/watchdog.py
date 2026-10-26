"""Watchdog: probes service health and manages UP/DOWN state with alert cooldown."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from src.storage.database import get_connection

logger = logging.getLogger(__name__)

SERVICES = ("web", "telegram", "followup")


class ServiceStatus(Enum):
    UP = "up"
    DOWN = "down"


@dataclass(frozen=True)
class WatchdogEvent:
    kind: str  # "down" or "recovered"
    service: str

    @property
    def is_down(self) -> bool:
        return self.kind == "down"


async def _probe_web(url: str, timeout: float = 5.0) -> bool:
    import urllib.request

    def _request() -> bool:
        # URL is an operator-configured health endpoint, not user input.
        with urllib.request.urlopen(url, timeout=timeout) as r:  # nosec B310
            return r.status == 200

    try:
        return await asyncio.to_thread(_request)
    except Exception:  # noqa: BLE001
        return False


async def _probe_worker(service: str, max_age_seconds: int, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    try:
        conn = await get_connection()
        cur = await conn.execute(
            "SELECT last_beat FROM service_heartbeats WHERE service = ?", (service,)
        )
        row = await cur.fetchone()
    except Exception:  # noqa: BLE001
        return False
    if row is None or row[0] is None:
        return False
    last_beat = datetime.fromisoformat(row[0])
    if last_beat.tzinfo is None:
        last_beat = last_beat.replace(tzinfo=timezone.utc)
    return (now - last_beat) <= timedelta(seconds=max_age_seconds)


class Watchdog:
    """Evaluates per-service health and produces down/recovered events.

    state:  initialise to DOWN so a service that is unhealthy at startup
            does not emit a spurious "down" alert (no UP->DOWN transition).
    """

    def __init__(self, config, probe=None, now_provider=None) -> None:
        self._config = config
        self._probe = probe or self._default_probe
        self._now = now_provider or (lambda: datetime.now(timezone.utc))
        self._status: dict[str, ServiceStatus] = {s: ServiceStatus.DOWN for s in SERVICES}
        self._last_down_at: dict[str, datetime] = {}
        self._down_history: set[str] = set()

    async def _default_probe(self, service: str, now: datetime) -> bool:
        if service == "web":
            return await _probe_web(self._config.monitoring.web_health_url)
        max_age = self._config.monitoring.heartbeat_interval * 3
        return await _probe_worker(service, max_age, now)

    async def tick(self) -> list[WatchdogEvent]:
        now = self._now()
        events: list[WatchdogEvent] = []
        cooldown = timedelta(minutes=self._config.monitoring.alert_cooldown_minutes)

        for service in SERVICES:
            is_up = await self._probe(service, now)
            prev = self._status[service]

            if is_up:
                self._status[service] = ServiceStatus.UP
                if prev is ServiceStatus.DOWN and service in self._down_history:
                    events.append(WatchdogEvent("recovered", service))
            else:
                self._status[service] = ServiceStatus.DOWN
                if prev is ServiceStatus.UP:
                    last = self._last_down_at.get(service)
                    if last is None or (now - last) >= cooldown:
                        self._last_down_at[service] = now
                        self._down_history.add(service)
                        events.append(WatchdogEvent("down", service))

        return events

    @property
    def status(self) -> dict[str, str]:
        return {s: self._status[s].value for s in SERVICES}
