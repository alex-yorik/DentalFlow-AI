"""Heartbeat writer: workers report liveness to the shared SQLite table."""

import asyncio
import contextlib
import logging
from datetime import UTC, datetime

from src.storage.database import get_connection

logger = logging.getLogger(__name__)


async def write_heartbeat(service: str, now: datetime | None = None) -> None:
    """UPSERT the last_beat timestamp for a worker service."""
    ts = now or datetime.now(UTC)
    conn = await get_connection()
    await conn.execute(
        """
        INSERT INTO service_heartbeats (service, last_beat)
        VALUES (?, ?)
        ON CONFLICT(service) DO UPDATE SET last_beat = excluded.last_beat
        """,
        (service, ts.isoformat()),
    )
    await conn.commit()


class HeartbeatWriter:
    def __init__(self, service: str, interval: int) -> None:
        self._service = service
        self._interval = interval
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        self._stop.clear()
        self._task = asyncio.create_task(self._run(), name=f"heartbeat-{self._service}")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        logger.info("Heartbeat writer started: service=%s interval=%ss", self._service, self._interval)
        while not self._stop.is_set():
            try:
                await write_heartbeat(self._service)
            except Exception as e:  # noqa: BLE001 # heartbeat loop must survive storage errors
                logger.error("Heartbeat write failed for %s: %s", self._service, e)
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
