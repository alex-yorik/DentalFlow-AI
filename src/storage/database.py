import aiosqlite
import logging
from pathlib import Path

DB_PATH = Path("data/database.db")

logger = logging.getLogger(__name__)


class StorageError(Exception):
    pass


async def get_connection() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = await aiosqlite.connect(str(DB_PATH))
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        return conn
    except aiosqlite.Error as e:
        logger.error("StorageError: get_connection failed: %s", e)
        raise StorageError(f"get_connection failed: {e}") from e


async def init_db() -> None:
    conn = await get_connection()
    try:
        from src.storage.migrations import SCHEMA
        await conn.executescript(SCHEMA)
        await conn.commit()
    finally:
        await conn.close()