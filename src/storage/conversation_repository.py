import logging
import uuid
from datetime import UTC, datetime

import aiosqlite

from src.llm.contracts import DialogMessage
from src.storage import database
from src.storage.database import StorageError

logger = logging.getLogger(__name__)

_MAX_PER_CHAT = 20


async def append_message(channel_user_id: int, role: str, text: str) -> None:
    now = datetime.now(UTC)
    try:
        conn = await database.get_connection()
    except StorageError:
        raise
    try:
        await conn.execute(
            """INSERT INTO messages (id, channel_user_id, role, text, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), channel_user_id, role, text, now.isoformat()),
        )
        await conn.execute(
            """DELETE FROM messages WHERE channel_user_id = ? AND id NOT IN (
                   SELECT id FROM messages
                   WHERE channel_user_id = ?
                   ORDER BY created_at DESC, id DESC LIMIT ?
               )""",
            (channel_user_id, channel_user_id, _MAX_PER_CHAT),
        )
        await conn.commit()
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: append_message(chat=%s) failed: %s", channel_user_id, e)
        raise StorageError(f"append_message failed for chat {channel_user_id}: {e}") from e
    finally:
        await conn.close()


async def get_recent_messages(channel_user_id: int, limit: int = 20) -> list[DialogMessage]:
    try:
        conn = await database.get_connection()
    except StorageError:
        return []
    try:
        cursor = await conn.execute(
            """SELECT role, text FROM (
                   SELECT role, text, created_at, id FROM messages
                   WHERE channel_user_id = ?
                   ORDER BY created_at DESC, id DESC LIMIT ?
               ) ORDER BY created_at ASC, id ASC""",
            (channel_user_id, limit),
        )
        rows = await cursor.fetchall()
        return [DialogMessage(role=row["role"], text=row["text"]) for row in rows]
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: get_recent_messages(chat=%s) failed: %s", channel_user_id, e)
        return []
    finally:
        await conn.close()
