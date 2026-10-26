import logging
import uuid
from datetime import UTC, datetime

import aiosqlite

from src.leads.models import Lead
from src.storage import database
from src.storage.database import StorageError

logger = logging.getLogger(__name__)

STATUS_SCHEDULED = "scheduled"


async def _find_by_phone(phone: str) -> dict | None:
    try:
        conn = await database.get_connection()
    except StorageError:
        return None
    try:
        cursor = await conn.execute(
            """SELECT * FROM appointments
               WHERE phone = ? AND status = ? ORDER BY created_at DESC LIMIT 1""",
            (phone, STATUS_SCHEDULED),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: appointment by phone failed: %s", e)
        return None
    finally:
        await conn.close()


async def find_existing_appointment(
    name: str | None,
    phone: str | None,
) -> dict | None:
    if not phone:
        return None
    return await _find_by_phone(phone)


async def create_appointment(lead: Lead, appointment_datetime: str | None = None) -> str:
    now = datetime.now(UTC)
    appointment_id = str(uuid.uuid4())
    try:
        conn = await database.get_connection()
    except StorageError:
        raise
    try:
        await conn.execute(
            """INSERT INTO appointments
               (id, lead_id, chat_id, name, phone, service, appointment_datetime, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                appointment_id, lead.id, lead.channel_user_id,
                lead.name, lead.phone, lead.service_interest,
                appointment_datetime or lead.preferred_time,
                STATUS_SCHEDULED, now.isoformat(), now.isoformat(),
            ),
        )
        await conn.commit()
        return appointment_id
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: create_appointment failed for lead %s: %s", lead.id, e)
        raise StorageError(f"create_appointment failed for lead {lead.id}: {e}") from e
    finally:
        await conn.close()


async def update_appointment_datetime(appointment_id: str, appointment_datetime: str) -> None:
    now = datetime.now(UTC)
    try:
        conn = await database.get_connection()
    except StorageError:
        raise
    try:
        await conn.execute(
            "UPDATE appointments SET appointment_datetime=?, updated_at=? WHERE id=?",
            (appointment_datetime, now.isoformat(), appointment_id),
        )
        await conn.commit()
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: update_appointment_datetime(%s) failed: %s", appointment_id, e)
        raise StorageError(f"update_appointment_datetime failed for {appointment_id}: {e}") from e
    finally:
        await conn.close()
