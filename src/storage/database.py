import aiosqlite
import logging
from pathlib import Path

DB_PATH = Path("data/database.db")

logger = logging.getLogger(__name__)

_db_connection: aiosqlite.Connection | None = None


class _SingletonConnection:
    """Proxies all calls to the underlying connection except close(), which is a no-op
    so that callers who habitually close connections don't terminate the singleton."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def close(self) -> None:
        pass

    def __getattr__(self, name: str):
        return getattr(self._conn, name)


class StorageError(Exception):
    pass


async def get_connection() -> aiosqlite.Connection:
    global _db_connection

    if _db_connection is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            raw = await aiosqlite.connect(str(DB_PATH))
            raw.row_factory = aiosqlite.Row
            await raw.execute("PRAGMA journal_mode=WAL")
            await raw.execute("PRAGMA foreign_keys=ON")
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
    conn = await get_connection()
    from src.storage.migrations import SCHEMA, MIGRATIONS
    await conn.executescript(SCHEMA)
    for migration in MIGRATIONS:
        try:
            await conn.execute(migration)
        except Exception:
            pass
    await conn.commit()