import logging
from pathlib import Path

import aiosqlite
from alembic.config import Config
from alembic.command import upgrade

DB_PATH = Path("data/database.db")

logger = logging.getLogger(__name__)

_db_connection: aiosqlite.Connection | None = None

_ALEMBIC_CFG_PATH = Path(__file__).resolve().parent / "alembic.ini"


class _SingletonConnection:
    """Proxies all calls to the underlying connection except close(), which is a no-op
    so that callers who habitually close connections do not terminate the singleton."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def close(self) -> None:
        pass

    def __getattr__(self, name: str):
        return getattr(self._conn, name)


class StorageError(Exception):
    pass


def run_alembic_upgrade(db_path: Path) -> None:
    cfg = Config(str(_ALEMBIC_CFG_PATH))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    upgrade(cfg, "head")


async def get_connection() -> aiosqlite.Connection:
    global _db_connection

    if _db_connection is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            raw = await aiosqlite.connect(str(DB_PATH))
            raw.row_factory = aiosqlite.Row
            await raw.execute("PRAGMA journal_mode=WAL")
            await raw.execute("PRAGMA foreign_keys=ON")
            await raw.execute("PRAGMA busy_timeout=5000")
            await raw.commit()
            _db_connection = raw
        except aiosqlite.Error as e:
            logger.error("StorageError: get_connection failed: %s", e)
            raise StorageError(f"get_connection failed: {e}") from e

    return _SingletonConnection(_db_connection)


async def close_connection() -> None:
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None


async def init_db() -> None:
    run_alembic_upgrade(DB_PATH)
    await get_connection()