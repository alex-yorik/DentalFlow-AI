import json
import uuid
from datetime import datetime, timezone

from src.leads.models import Lead, LeadState
from src.storage import database


def _row_to_lead(row) -> Lead:
    return Lead(
        id=row["id"],
        telegram_chat_id=row["telegram_chat_id"],
        state=LeadState(row["state"]),
        name=row["name"],
        phone=row["phone"],
        email=row["email"],
        service_interest=row["service_interest"],
        intent=row["intent"],
        urgency=row["urgency"],
        preferred_time=row["preferred_time"],
        source=row["source"],
        qualification_score=row["qualification_score"],
        conversation_summary=row["conversation_summary"],
        opt_in_consent=bool(row["opt_in_consent"]),
        internal_tags=json.loads(row["internal_tags"]),
        crm_contact_id=row["crm_contact_id"],
        followup_task_id=row["followup_task_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def create_lead(telegram_chat_id: int, source: str = "telegram") -> Lead:
    now = datetime.now(timezone.utc)
    lead = Lead(
        id=str(uuid.uuid4()),
        telegram_chat_id=telegram_chat_id,
        source=source,
        created_at=now,
        updated_at=now,
    )
    conn = await database.get_connection()
    try:
        await conn.execute(
            """INSERT INTO leads
               (id, telegram_chat_id, state, source,
                opt_in_consent, internal_tags,
                qualification_score, conversation_summary,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lead.id, lead.telegram_chat_id, lead.state.value, lead.source,
                1 if lead.opt_in_consent else 0,
                json.dumps(lead.internal_tags),
                lead.qualification_score, lead.conversation_summary,
                lead.created_at.isoformat(), lead.updated_at.isoformat(),
            ),
        )
        await conn.commit()
        return lead
    finally:
        await conn.close()


async def get_lead_by_chat_id(telegram_chat_id: int) -> Lead | None:
    conn = await database.get_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM leads WHERE telegram_chat_id = ? ORDER BY created_at DESC LIMIT 1",
            (telegram_chat_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_lead(row)
    finally:
        await conn.close()


async def update_lead(lead: Lead) -> None:
    lead.updated_at = datetime.now(timezone.utc)
    conn = await database.get_connection()
    try:
        await conn.execute(
            """UPDATE leads SET
               state=?, name=?, phone=?, email=?, service_interest=?,
               intent=?, urgency=?, preferred_time=?, source=?,
               qualification_score=?, conversation_summary=?,
               opt_in_consent=?, internal_tags=?, crm_contact_id=?,
               followup_task_id=?, updated_at=?
               WHERE id=?""",
            (
                lead.state.value, lead.name, lead.phone, lead.email,
                lead.service_interest, lead.intent, lead.urgency,
                lead.preferred_time, lead.source, lead.qualification_score,
                lead.conversation_summary,
                1 if lead.opt_in_consent else 0,
                json.dumps(lead.internal_tags),
                lead.crm_contact_id, lead.followup_task_id,
                lead.updated_at.isoformat(), lead.id,
            ),
        )
        await conn.commit()
    finally:
        await conn.close()


async def lead_exists(telegram_chat_id: int) -> bool:
    conn = await database.get_connection()
    try:
        cursor = await conn.execute(
            "SELECT 1 FROM leads WHERE telegram_chat_id = ? LIMIT 1",
            (telegram_chat_id,),
        )
        return await cursor.fetchone() is not None
    finally:
        await conn.close()


async def delete_lead(lead_id: str) -> None:
    conn = await database.get_connection()
    try:
        await conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        await conn.commit()
    finally:
        await conn.close()