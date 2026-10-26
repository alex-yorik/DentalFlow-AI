import asyncio
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from src.monitoring.heartbeat import HeartbeatWriter, write_heartbeat

HERE = Path(__file__).resolve().parent.parent.parent
WORKER_HC = HERE / "docker" / "worker_healthcheck.py"


@pytest_asyncio.fixture
async def beat_db(db_path):
    conn = await aiosqlite.connect(str(db_path))
    conn.row_factory = aiosqlite.Row

    async def get_connection():
        return conn

    async def _fetch(service: str):
        cur = await conn.execute(
            "SELECT last_beat FROM service_heartbeats WHERE service = ?", (service,)
        )
        row = await cur.fetchone()
        return row["last_beat"] if row else None

    yield {"get_connection": get_connection, "fetch": _fetch}
    await conn.close()


@pytest.mark.asyncio
async def test_write_heartbeat_creates_row(monkeypatch, beat_db):
    monkeypatch.setattr("src.monitoring.heartbeat.get_connection", beat_db["get_connection"])
    now = datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC)
    await write_heartbeat("telegram", now)
    assert await beat_db["fetch"]("telegram") == now.isoformat()


@pytest.mark.asyncio
async def test_write_heartbeat_updates_row(monkeypatch, beat_db):
    monkeypatch.setattr("src.monitoring.heartbeat.get_connection", beat_db["get_connection"])
    await write_heartbeat("telegram", datetime(2026, 8, 3, 12, 0, 0, tzinfo=UTC))
    later = datetime(2026, 8, 3, 12, 1, 0, tzinfo=UTC)
    await write_heartbeat("telegram", later)
    assert await beat_db["fetch"]("telegram") == later.isoformat()


@pytest.mark.asyncio
async def test_heartbeat_writer_loop_writes(monkeypatch, beat_db):
    monkeypatch.setattr("src.monitoring.heartbeat.get_connection", beat_db["get_connection"])
    writer = HeartbeatWriter("followup", interval=1)
    await writer.start()
    await asyncio.sleep(1.5)
    await writer.stop()
    ts = await beat_db["fetch"]("followup")
    assert ts is not None


def _run_worker_hc(db_path, service, interval=30):
    return subprocess.run(
        [sys.executable, str(WORKER_HC)],
        capture_output=True,
        check=False,
        env={
            "DB_PATH": str(db_path),
            "WATCHED_SERVICE": service,
            "HEARTBEAT_INTERVAL": str(interval),
        },
    )


def test_worker_healthcheck_ok_when_fresh(db_path):
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    ts = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    conn.execute(
        "INSERT INTO service_heartbeats (service, last_beat) VALUES (?, ?)",
        ("telegram", ts),
    )
    conn.commit()
    conn.close()
    assert _run_worker_hc(db_path, "telegram").returncode == 0


def test_worker_healthcheck_fails_when_stale(db_path):
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    ts = (datetime.now(UTC) - timedelta(seconds=200)).isoformat()
    conn.execute(
        "INSERT INTO service_heartbeats (service, last_beat) VALUES (?, ?)",
        ("telegram", ts),
    )
    conn.commit()
    conn.close()
    assert _run_worker_hc(db_path, "telegram").returncode == 1


def test_worker_healthcheck_fails_when_missing(db_path):
    assert _run_worker_hc(db_path, "nonexistent").returncode == 1
