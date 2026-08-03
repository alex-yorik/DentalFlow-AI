import tempfile
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite
import pytest
import pytest_asyncio

from src.config.loader import AppConfig, ClientConfig, load_client_config
from src.storage.database import DB_PATH, run_alembic_upgrade

CLIENT_NAME = "demo_dental"


@pytest.fixture(scope="session", autouse=True)
def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_alembic_upgrade(DB_PATH)


@pytest.fixture
def demo_client_config() -> ClientConfig:
    return load_client_config(CLIENT_NAME)


@pytest.fixture
def demo_app_config(demo_client_config: ClientConfig) -> AppConfig:
    return AppConfig(
        telegram_bot_token="test_token",
        openai_api_key="test_key",
        client_name="demo_dental",
        client=demo_client_config,
    )


@pytest_asyncio.fixture
async def db_path() -> AsyncGenerator[Path, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    conn = await aiosqlite.connect(str(path))
    conn.row_factory = aiosqlite.Row
    await conn.commit()
    await conn.close()
    run_alembic_upgrade(path)
    yield path
    path.unlink(missing_ok=True)


@pytest_asyncio.fixture
async def db(db_path: Path, monkeypatch) -> AsyncGenerator[None, None]:
    async def get_connection():
        conn = await aiosqlite.connect(str(db_path))
        conn.row_factory = aiosqlite.Row
        return conn

    monkeypatch.setattr("src.storage.database.get_connection", get_connection)
    yield