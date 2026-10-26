from src.leads.models import Lead, LeadState
from src.leads.repository import create_lead, get_lead_by_chat_id


async def resolve_lead(
    chat_id: int,
    *,
    source: str,
    channel_type: str,
    blocked_reply: str,
) -> tuple[Lead | None, str | None]:
    """Lookup or create a lead for a chat.

    Returns (lead, blocked_msg): if the chat is blocked returns (None, blocked_msg);
    otherwise (lead, None) where lead is either the found lead (CLOSED leads are
    reset and recreated) or a freshly created one.
    """
    lead = await get_lead_by_chat_id(chat_id)
    if lead and lead.state == LeadState.BLOCKED:
        return None, blocked_reply
    if lead and lead.state == LeadState.CLOSED:
        lead = None
    if lead is None:
        lead = await create_lead(chat_id, source=source, channel_type=channel_type)
    return lead, None
