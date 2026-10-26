import json
import logging
import uuid
from datetime import UTC, datetime

import aiosqlite

from src.leads.models import Lead, LeadState
from src.storage import database
from src.storage.database import StorageError

logger = logging.getLogger(__name__)


def _row_to_lead(row) -> Lead:
    return Lead(
        id=row["id"],
        channel_user_id=row["channel_user_id"],
        state=LeadState(row["state"]),
        name=row["name"],
        phone=row["phone"],
        email=row["email"],
        service_interest=row["service_interest"],
        intent=row["intent"],
        urgency=row["urgency"],
        preferred_time=row["preferred_time"],
        source=row["source"],
        channel_type=row["channel_type"],
        qualification_score=row["qualification_score"],
        conversation_summary=row["conversation_summary"],
        opt_in_consent=bool(row["opt_in_consent"]),
        internal_tags=json.loads(row["internal_tags"]),
        crm_contact_id=row["crm_contact_id"],
        followup_task_id=row["followup_task_id"],
        refusal_count=row["refusal_count"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def create_lead(channel_user_id: int, source: str = "telegram", channel_type: str = "telegram") -> Lead:
    now = datetime.now(UTC)
    lead = Lead(
        id=str(uuid.uuid4()),
        channel_user_id=channel_user_id,
        source=source,
        channel_type=channel_type,
        created_at=now,
        updated_at=now,
    )
    try:
        conn = await database.get_connection()
    except StorageError:
        raise

    try:
        await conn.execute(
            """INSERT INTO leads
               (id, channel_user_id, state, source, channel_type,
                opt_in_consent, internal_tags,
                qualification_score, conversation_summary,
                refusal_count,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lead.id, lead.channel_user_id, lead.state.value, lead.source, lead.channel_type,
                1 if lead.opt_in_consent else 0,
                json.dumps(lead.internal_tags),
                lead.qualification_score, lead.conversation_summary,
                lead.refusal_count,
                lead.created_at.isoformat(), lead.updated_at.isoformat(),
            ),
        )
        await conn.commit()
        return lead
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: create_lead(chat_id=%s) failed: %s", channel_user_id, e)
        raise StorageError(f"create_lead failed for chat {channel_user_id}: {e}") from e
    finally:
        await conn.close()


async def get_lead_by_chat_id(channel_user_id: int) -> Lead | None:
    try:
        conn = await database.get_connection()
    except StorageError:
        return None

    try:
        cursor = await conn.execute(
            "SELECT * FROM leads WHERE channel_user_id = ? ORDER BY created_at DESC LIMIT 1",
            (channel_user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_lead(row)
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: get_lead_by_chat_id(chat_id=%s) failed: %s", channel_user_id, e)
        return None
    finally:
        await conn.close()


async def update_lead(lead: Lead) -> None:
    lead.updated_at = datetime.now(UTC)
    try:
        conn = await database.get_connection()
    except StorageError:
        raise

    try:
        await conn.execute(
            """UPDATE leads SET
               state=?, name=?, phone=?, email=?, service_interest=?,
               intent=?, urgency=?, preferred_time=?, source=?, channel_type=?,
               qualification_score=?, conversation_summary=?,
               opt_in_consent=?, internal_tags=?, crm_contact_id=?,
               followup_task_id=?, refusal_count=?, updated_at=?
               WHERE id=?""",
            (
                lead.state.value, lead.name, lead.phone, lead.email,
                lead.service_interest, lead.intent, lead.urgency,
                lead.preferred_time, lead.source, lead.channel_type,
                lead.qualification_score, lead.conversation_summary,
                1 if lead.opt_in_consent else 0,
                json.dumps(lead.internal_tags),
                lead.crm_contact_id, lead.followup_task_id,
                lead.refusal_count,
                lead.updated_at.isoformat(), lead.id,
            ),
        )
        await conn.commit()
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: update_lead(id=%s, chat_id=%s) failed: %s", lead.id, lead.channel_user_id, e)
        raise StorageError(f"update_lead failed for lead {lead.id}: {e}") from e
    finally:
        await conn.close()


async def lead_exists(channel_user_id: int) -> bool:
    try:
        conn = await database.get_connection()
    except StorageError:
        return False

    try:
        cursor = await conn.execute(
            "SELECT 1 FROM leads WHERE channel_user_id = ? LIMIT 1",
            (channel_user_id,),
        )
        return await cursor.fetchone() is not None
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: lead_exists(chat_id=%s) failed: %s", channel_user_id, e)
        return False
    finally:
        await conn.close()


async def delete_lead(lead_id: str) -> None:
    try:
        conn = await database.get_connection()
    except StorageError:
        raise

    try:
        await conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        await conn.commit()
    except (aiosqlite.Error, StorageError) as e:
        logger.error("StorageError: delete_lead(id=%s) failed: %s", lead_id, e)
        raise StorageError(f"delete_lead failed for lead {lead_id}: {e}") from e
    finally:
        await conn.close()
