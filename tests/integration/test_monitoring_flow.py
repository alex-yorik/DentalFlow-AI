from datetime import UTC, datetime, timedelta

import aiosqlite
import pytest
import pytest_asyncio

from src.config.loader import AppConfig, MonitoringConfig, load_client_config
from src.monitoring.heartbeat import write_heartbeat
from src.monitoring.watchdog import Watchdog

_CLIENT = load_client_config("demo_dental")


def _cfg(heartbeat=30) -> AppConfig:
    return AppConfig(
        telegram_bot_token="t",
        openai_api_key="k",
        client_name="demo_dental",
        client=_CLIENT,
        monitoring=MonitoringConfig(heartbeat_interval=heartbeat),
    )


@pytest_asyncio.fixture
async def monitoring_db(db_path):
    conn = await aiosqlite.connect(str(db_path))
    conn.row_factory = aiosqlite.Row

    async def get_connection():
        return conn

    yield get_connection
    await conn.close()


@pytest.mark.asyncio
async def test_worker_healthy_when_heartbeat_fresh(monkeypatch, monitoring_db):
    monkeypatch.setattr("src.monitoring.heartbeat.get_connection", monitoring_db)
    monkeypatch.setattr("src.monitoring.watchdog.get_connection", monitoring_db)

    now = datetime.now(UTC)
    await write_heartbeat("telegram", now)

    watchdog = Watchdog(_cfg(heartbeat=30))
    assert await watchdog._default_probe("telegram", now) is True


@pytest.mark.asyncio
async def test_worker_down_when_heartbeat_stale(monkeypatch, monitoring_db):
    monkeypatch.setattr("src.monitoring.heartbeat.get_connection", monitoring_db)
    monkeypatch.setattr("src.monitoring.watchdog.get_connection", monitoring_db)

    now = datetime.now(UTC)
    await write_heartbeat("telegram", now - timedelta(seconds=200))

    watchdog = Watchdog(_cfg(heartbeat=30))
    assert await watchdog._default_probe("telegram", now) is False


@pytest.mark.asyncio
async def test_worker_down_when_no_heartbeat(monkeypatch, monitoring_db):
    monkeypatch.setattr("src.monitoring.watchdog.get_connection", monitoring_db)
    watchdog = Watchdog(_cfg(heartbeat=30))
    assert await watchdog._default_probe("telegram", datetime.now(UTC)) is False
